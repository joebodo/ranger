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
from os.path import exists
import mimetypes
import os
import stat
import string
import sys

import ranger
from ranger import *
from ranger.core.actions import Actions
from ranger.core.info import Info
from ranger.core.pluginsystem import PluginSystem
from ranger.api.commands import CommandHandler
from ranger.container.settingobject import ALLOWED_SETTINGS
from ranger.ext.signals import SignalDispatcher
from ranger.ext.shell_escape import shell_quote
from ranger.ext.keybinding_parser import construct_keybinding

TICKS_BEFORE_COLLECTING_GARBAGE = 100
TIME_BEFORE_FILE_BECOMES_GARBAGE = 1200

class FM(Actions, PluginSystem, CommandHandler, SignalDispatcher):
	def __init__(self, infoinit=True):
		"""Initialize FM."""
		Actions.__init__(self)
		SignalDispatcher.__init__(self)
		PluginSystem.__init__(self)
		self.commands = None
		self.variables = {}
		self.log = deque(maxlen=20)
		fm.tabs = dict((n+1, os.path.abspath(path)) for n, path \
				in enumerate(ranger.RUNTARGETS[:9]))
		self.py3 = sys.version_info >= (3, )
		self.previews = {}
		self.current_tab = 1

		self.log.append('Ranger {0} started! Process ID is {1}.' \
				.format(ranger.__version__, PID))
		self.log.append('Running on Python ' + sys.version.split('\n')[0])

	def initialize(self, targets=[]):
		"""If ui/bookmarks are None, they will be initialized here."""
		from ranger.container import Bookmarks
		from ranger.core.runner import Runner
		from ranger.fsobject import Directory
		from ranger.core.loader import Loader
		from ranger.gui.defaultui import DefaultUI

		try:
			locale.setlocale(locale.LC_ALL, '')
		except:
			pass
		if not 'SHELL' in os.environ:
			os.environ['SHELL'] = 'bash'

		self.loader = Loader()

		if CLEAN:
			bookmarkfile = None
		else:
			bookmarkfile = CONFPATH('bookmarks')
		self.bookmarks = Bookmarks(
				bookmarkfile=bookmarkfile,
				bookmarktype=Directory,
				autosave=self.settings.autosave_bookmarks)
		self.bookmarks.load()

		if not CLEAN:
			from ranger.container.tags import Tags
			self.tags = Tags(CONFPATH('tagged'))
		else:
			self.tags = {}

		self.ui = DefaultUI()
		self.ui.initialize()
		self.run = Runner(ui=self.ui, logfunc=self.err)

		self.env.signal_bind('cd', self._update_current_tab)

		mimetypes.knownfiles.append(os.path.expanduser('~/.mime.types'))
		mimetypes.knownfiles.append(self.relpath('data/mime.types'))
		self.mimetypes = mimetypes.MimeTypes()

		from ranger.core.environment import Environment
		EnvironmentAware.env = Environment(target and targets[0] or '.')

		if not ranger.DEBUG:
			import ranger.ext.curses_interrupt_handler
			ranger.ext.curses_interrupt_handler.install_interrupt_handler()

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

	def loop(self):
		"""
		The main loop consists of:
		1. reloading bookmarks if outdated
		2. letting the loader work
		3. drawing and finalizing ui
		4. reading and handling user input
		5. after X loops: collecting unused directory objects
		"""

		self.env.enter_dir(self.env.path)

		gc_tick = 0

		# for faster lookup:
		ui = self.ui
		throbber = ui.throbber
		loader = self.loader
		env = self.env
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
					env.garbage_collect(TIME_BEFORE_FILE_BECOMES_GARBAGE)

		except KeyboardInterrupt:
			# this only happens in --debug mode. By default, interrupts
			# are caught in curses_interrupt_handler
			raise SystemExit

		finally:
			if ranger.CHOOSEDIR and self.env.cwd and self.env.cwd.path:
				open(ranger.CHOOSEDIR, 'w').write(self.env.cwd.path)
			self.bookmarks.remember(env.cwd)
			self.bookmarks.save()

	def load_commands(self):
		import ranger.defaults.commands
		import ranger.api.commands
		container = ranger.api.commands.CommandContainer()
		container.load_commands_from_module(ranger.defaults.commands)
		if not CLEAN and (exists(confpath('commands.py')) or
				exists(confpath('commands.pyo')) or
				exists(confpath('commands.pyc'))):
			self.allow_importing_from(CONFDIR, True)
			try:
				import commands
			except ImportError:
				pass
			else:
				container.load_commands_from_module(commands)
			self.allow_importing_from(CONFDIR, False)
		self.commands = container
		return container

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

	def load_config(self):
		try:
			myconfig = open(self.confpath('config'), 'r').read()
		except:
			self.source_cmdlist(self.relpath('defaults/config'))
		else:
			lines = myconfig.split("\n")
			if 'nodefaults' not in lines:
				self.source_cmdlist(self.relpath('defaults/config'))
			for line in lines:
				self.cmd_secure(line.rstrip("\r\n"))

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

