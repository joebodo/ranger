# Copyright (C) 2009, 2010  Roman Zimbelmann <romanz@lavabit.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
The File Manager, putting the pieces together
"""

from time import time
from collections import deque
from os.path import exists, abspath
import mimetypes
import os
import stat
import socket
import string
import sys

import ranger
from ranger import *
from ranger.core.tab import Tab
#from ranger.core.actions import Actions
#from ranger.core.pluginsystem import PluginSystem
#from ranger.api.commands import CommandHandler
from ranger.gui.ui import UI
from ranger.core.directory import Directory
from ranger.ext.lazy_property import lazy_property
from ranger.ext.signals import SignalDispatcher
from ranger.ext.shell_escape import shell_quote
from ranger.ext.keybinding_parser import construct_keybinding
from ranger.core.settings import Settings
from ranger.core.keybuffer import KeyBuffer
from ranger.core.keymap import KeyManager
from ranger.core.history import History

TICKS_BEFORE_COLLECTING_GARBAGE = 100
TIME_BEFORE_FILE_BECOMES_GARBAGE = 1200

ALLOWED_CONTEXTS = ('browser', 'pager', 'embedded_pager', 'taskview',
		'console')

#class FM(Actions, PluginSystem, CommandHandler, Cache, SignalDispatcher):
class FM(SignalDispatcher):
	# -=- Initialization -=-
	def __init__(self, infoinit=True):
		"""Initialize FM."""
#		Actions.__init__(self)
		SignalDispatcher.__init__(self)
#		PluginSystem.__init__(self)
#		CommandHandler.__init__(self)

		self.variables = VariableContainer(self)
		self.log = deque(maxlen=20)
		self.dircache = {}
		self.tabs = {}
		self.tab = None
		self.previews = {}
		self.current_tab = 1
		self.copy = set()
		self.settings = Settings(self)
		self.keybuffer = KeyBuffer(None, None)
		self.keymanager = KeyManager(self.keybuffer, ALLOWED_CONTEXTS)
		self.termsize = None
		self.last_search = None

		try:
			self.username = pwd.getpwuid(os.geteuid()).pw_name
		except:
			self.username = 'uid:' + str(os.geteuid())
		self.hostname = socket.gethostname()
		self.home_path = os.path.expanduser('~')

	def initialize(self, targets=[]):
		"""If ui/bookmarks are None, they will be initialized here."""
		from ranger.core.bookmarks import Bookmarks
		from ranger.core.runner import Runner
		from ranger.core.directory import Directory
		from ranger.core.loader import Loader
		import ranger

		self.log.append('Ranger {0} started! Process ID is {1}.' \
				.format(ranger.__version__, os.getpid()))
		self.log.append('Running on Python ' + sys.version.split('\n')[0])

		configfile         = ranger.confpath('startup.py')
		default_configfile = ranger.relpath('config', 'startup.py')
		commandlistfile    = ranger.confpath('rc.conf')

		try:
			locale.setlocale(locale.LC_ALL, '')
		except:
			pass
		if not 'SHELL' in os.environ:
			os.environ['SHELL'] = 'bash'

		# -=- Load Config File -=-
		while True:
			if not CLEAN:
				if os.access(configfile, os.R_OK):
					execfile(configfile)
					break
			if os.access(default_configfile, os.R_OK):
				execfile(default_configfile)
			break

		self.loader = Loader()

		self.tabs = dict((n+1, Tab(path)) for n, path \
				in enumerate(ranger.RUNTARGETS[:9]))
		self.tab = self.tabs[1]

		if CLEAN:
			self.tags = {}
		else:
			from ranger.core.tags import Tags
			self.tags = Tags(ranger.confpath('tagged'))

		self.ui = UI()
		self.ui.initialize()
		self.run = Runner(ui=self.ui, logfunc=ranger.ERR)
		self.run = Runner(logfunc=ERR)

#		self.tag.signal_bind('cd', self._update_current_tab)
		self.signal_bind('setvar', lambda sig: dict.__setitem__(
			self.variablecontainer, sig.name, sig.value), priority=0.2)

		if CLEAN:
			bookmarkfile = None
		else:
			bookmarkfile = ranger.confpath('bookmarks')
		self.bookmarks = Bookmarks(
				bookmarkfile=bookmarkfile,
				bookmarktype=Directory,
				autosave=self.settings.autosave_bookmarks)
		self.bookmarks.load()

		mimetypes.knownfiles.append(os.path.expanduser('~/.mime.types'))
		mimetypes.knownfiles.append(ranger.relpath('data/mime.types'))
		self.mimetypes = mimetypes.MimeTypes()

		if not ranger.DEBUG:
			import ranger.ext.curses_interrupt_handler
			ranger.ext.curses_interrupt_handler.install_interrupt_handler()

		# -=- Load Command List -=-
		if not CLEAN and os.access(commandlistfile, os.R_OK):
			execfile(commandlistfile)

	def loop(self):
		"""
		The main loop consists of:
		1. reloading bookmarks if outdated
		2. letting the loader work
		3. drawing and finalizing ui
		4. reading and handling user input
		5. after X loops: collecting unused directory objects
		"""

		self.tab.enter_dir(self.tab.path)

		gc_tick = 0

		# for faster lookup:
		ui = self.ui
		throbber = ui.throbber
		loader = self.loader
		has_throbber = hasattr(ui, 'throbber')

		try:
			while True:
				loader.work()
				if has_throbber:
					if loader.has_work():
						throbber(loader.status)
					else:
						throbber(remove=True)

				ui.redraw()

				ui.set_load_mode(loader.has_work())

				ui.handle_input()

				gc_tick += 1
				if gc_tick > TICKS_BEFORE_COLLECTING_GARBAGE:
					gc_tick = 0
					self.garbage_collect(TIME_BEFORE_FILE_BECOMES_GARBAGE)

		except KeyboardInterrupt:
			# this only happens in --debug mode. By default, interrupts
			# are caught in curses_interrupt_handler
			raise SystemExit

		finally:
			if ranger.CHOOSEDIR and self.tag.cwd and self.tag.cwd.path:
				open(ranger.CHOOSEDIR, 'w').write(self.tag.cwd.path)
			self.bookmarks.remember(tag.cwd)
			self.bookmarks.save()

	def get_directory(self, path):
		"""Get the directory object at the given path"""
		path = abspath(path)
		try:
			return self.dircache[path]
		except KeyError:
			obj = Directory(path)
			self.dircache[path] = obj
			return obj

	def garbage_collect(self, age):
		"""Delete unused directory objects"""
		for key in tuple(self.dircache):
			value = self.dircache[key]
			if age == -1 or \
					(value.is_older_than(age) and not value in self.pathway):
				del self.dircache[key]
				if value.is_directory:
					value.files = None
		self.settings.signal_garbage_collect()
		self.signal_garbage_collect()

	# -=- Random Functions -=-
	def get_free_space(self, path):
		stat = os.statvfs(path)
		return stat.f_bavail * stat.f_bsize

	def key_append(self, key):
		"""Append a key to the keybuffer"""

		# special keys:
		if key == curses.KEY_RESIZE:
			self.keybuffer.clear()

		self.keybuffer.add(key)

	def key_clear(self):
		"""Clear the keybuffer"""
		self.keybuffer.clear()

	def destroy(self):
		if self.ui:
			try:
				self.ui.destroy()
			except:
				if ranger.DEBUG:
					raise
		if self.loader:
			try:
				self.loader.destroy()
			except:
				if ranger.DEBUG:
					raise

	def compile_command_list(self):
		from inspect import cleandoc
		sorted_cmds = list(sorted(self.commands.commands.items(),
			key=lambda item: item[0]))

		if self.settings.syntax_highlighting:
			header = "[4mList of currently available commands:[0m\n\n"
			seperator = "[0m\n   "
			blockstart = "[1m"
			blockend = "\n\n\n"
			nodescr = "[1m:%s[0m\n   No description.\n\n\n"
		else:
			header = "List of currently available commands:\n\n"
			seperator = "\n   "
			blockstart = ""
			blockend = "\n\n\n"
			nodescr = ":%s\n   No description.\n\n\n"

		content = header
		for name, cmd in sorted_cmds:
			if name in self.commands.aliases:
				continue
			if cmd.__doc__:
				doc = cleandoc(cmd.__doc__).split("\n")
				if doc[1] == "":
					del doc[1]
				for i in range(1, len(doc)):
					doc[i] = doc[i]
				content += blockstart + seperator.join(doc) + blockend
			else:
				content += nodescr % name
		return content

	def compile_plugin_list(self):
		return "List of loaded plugins:\n" + "\n".join(self.plugins)

	def source_cmdlist(self, filename):
		for line in open(filename, 'r'):
			self.cmd_secure(line.rstrip("\r\n"))

	def eval(self, code):
		fm = self
		try:
			return eval(code)
		except Exception as ex:
			self.err(ex)
			return None

class VariableContainer(dict):
	def __init__(self, signal_dispatcher):
		dict.__init__(self)
		self._signal_dispatcher = signal_dispatcher

	def __setitem__(self, key, value):
		self._signal_dispatcher.signal_emit('setvar', previous=self[key],
				name=key, value=value)
