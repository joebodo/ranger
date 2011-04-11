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
from optparse import OptionParser
import mimetypes
import os
import pwd
import stat
import socket
import string
import sys
import curses

import ranger
from ranger.tab import Tab
from ranger.api.actions import Actions
from ranger.pluginsystem import PluginSystem
from ranger.api.commands import CommandHandler
from ranger.gui.ui import UI
from ranger.directory import Directory
from ranger.ext.lazy_property import lazy_property
from ranger.ext.signals import SignalDispatcher
from ranger.ext.shell_escape import shell_quote
from ranger.ext.keybinding_parser import construct_keybinding
from ranger.ext.openstruct import OpenStruct
from ranger.settings import Settings
from ranger.keybuffer import KeyBuffer
from ranger.keymap import KeyManager
from ranger.history import History

TICKS_BEFORE_COLLECTING_GARBAGE = 100
TIME_BEFORE_FILE_BECOMES_GARBAGE = 1200

ALLOWED_CONTEXTS = ('browser', 'taskview', 'console')

#class FM(Actions, PluginSystem, CommandHandler, Cache, SignalDispatcher):
class FM(Actions, PluginSystem, SignalDispatcher):
	# -=- Initialization -=-
	def __init__(self, infoinit=True):
		"""
		After creating the FM object, it will contain simple, configuration-
		independent default values which can be used for unit testing or
		similar things, without actually starting up a full ranger instance.
		"""
		SignalDispatcher.__init__(self)
		PluginSystem.__init__(self)
		#CommandHandler.__init__(self)

		self.variables = VariableContainer(self)
		self.log = deque(maxlen=20)
		self.dircache = {}
		self.tabs = {}
		self.arg = OpenStruct(clean=False, debug=False,
				confdir=ranger.DEFAULT_CONFDIR)
		self.tab = None
		self.previews = {}
		self.current_tab_index = 1
		self.copy = set()
		self.ui = None
		self.settings = Settings(self)
		self.keybuffer = KeyBuffer(None, None)
		self.keymanager = KeyManager(self.keybuffer, ALLOWED_CONTEXTS)
		self.termsize = (24, 80)
		self.last_search = None
		self.hostname = socket.gethostname()
		self.loader = None
		self.home_path = os.path.expanduser('~')
		try:
			self.username = pwd.getpwuid(os.geteuid()).pw_name
		except:
			self.username = 'uid:' + str(os.geteuid())

		self.optparser = OptionParser(usage='%prog [options] [path/filename]',
				version='ranger %s (%s)' % (ranger.__version__,
					ranger.VERSION[2] % 2 and 'stable' or 'testing'))
		self.optparser.add_option('-d', '--debug', action='store_true',
			help="activate debug mode")
		self.optparser.add_option('-c', '--clean', action='store_true',
			help="don't touch/require any config files")
		self.optparser.add_option('-r', '--confdir', type='string',
			metavar='dir', default=self.arg.confdir,
			help="the configuration directory (%default)")
		self.optparser.add_option('--choosefile', type='string', metavar='TARGET',
			help="Makes ranger act like a file chooser. When opening "
			"a file, it will quit and write the name of the selected "
			"file to TARGET.")
		self.optparser.add_option('--choosedir', type='string', metavar='TARGET',
			help="Makes ranger act like a directory chooser. When ranger quits"
			", it will write the name of the last visited directory to TARGET")

	def initialize(self, args=None):
		"""
		This method will initialize ranger, i.e. load configs, parse arguments,
		and initialize the curses user interface.
		Call the method fm.loop() after this to enter the input loop.
		"""
		from ranger.bookmarks import Bookmarks
		from ranger.runner import Runner
		from ranger.directory import Directory
		from ranger.loader import Loader
		import sys
		import ranger

		if args is None:
			args = sys.argv[1:]
		try:
			locale.setlocale(locale.LC_ALL, '')
		except:
			pass
		if not 'SHELL' in os.environ:
			os.environ['SHELL'] = 'bash'

		# There will be two passes of option parsing:
		# 1. before plugins are loaded, to determine the plugin directory
		# and whether or not to load custom plugins (--clean option)
		# 2. after plugins are loaded, to give plugins the chance to add their
		# own parsing options.

		# First pass:
		parser = OptionParser()
		parser.add_option('-c', '--clean', action='store_true')
		parser.add_option('-r', '--confdir', type='string',
				default=self.arg.confdir)
		parser.remove_option('--help')
		filtered_args = [arg for arg in args if not arg or not arg[0] == '-' or \
				arg in ('-c', '-r', '--clean') or arg[0:9] == '--confdir']
		options, _       = parser.parse_args(args=filtered_args)
		self.arg.clean   = options.clean
		self.arg.confdir = options.confdir

		# Load plugins
		self.load_plugins()

		# Second pass of argument parsing:
		options, positional = self.optparser.parse_args(args=args)
		self.arg = OpenStruct(options.__dict__, targets=positional)

		self.log.append('Ranger {0} started! Process ID is {1}.' \
				.format(ranger.__version__, os.getpid()))
		self.log.append('Running on Python ' + sys.version.split('\n')[0])

		configfile         = self.confpath('startup.py')
		default_configfile = self.relpath('config', 'startup.py')
		commandlistfile    = self.confpath('rc.conf')

		self.loader = Loader()
		if self.arg.targets:
			self.tabs = dict((n+1, Tab(path)) for n, path \
					in enumerate(self.arg.targets[:9]))
		else:
			self.tabs = {1: Tab('.')}
		self.tab = self.tabs[1]

		if self.arg.clean:
			self.tags = {}
		else:
			from ranger.tags import Tags
			self.tags = Tags(self.confpath('tagged'))

		self.ui = UI()
		self.ui.initialize()
		self.run = Runner(ui=self.ui, logfunc=ranger.ERR)
		self.run = Runner(logfunc=ranger.ERR)

		#self.tag.signal_bind('cd', self._update_current_tab)
		self.signal_bind('setvar', lambda sig: dict.__setitem__(
			self.variablecontainer, sig.name, sig.value), priority=0.2)

		if self.arg.clean:
			bookmarkfile = None
		else:
			bookmarkfile = self.confpath('bookmarks')
		self.bookmarks = Bookmarks(
				bookmarkfile=bookmarkfile,
				bookmarktype=Directory,
				autosave=self.settings.autosave_bookmarks)
		self.bookmarks.load()

		mimetypes.knownfiles.append(os.path.expanduser('~/.mime.types'))
		mimetypes.knownfiles.append(self.relpath('data/mime.types'))
		self.mimetypes = mimetypes.MimeTypes()

		if not self.arg.debug:
			import ranger.ext.curses_interrupt_handler
			ranger.ext.curses_interrupt_handler.install_interrupt_handler()

		# -=- Load Command List -=-
		if not self.arg.clean and os.access(commandlistfile, os.R_OK):
			execfile(commandlistfile)

	def loop(self):
		"""
		The input loop will run until the user terminates the program.

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
			if self.arg.choosedir and self.tab.cwd and self.tab.cwd.path:
				open(self.arg.choosedir, 'w').write(self.tab.cwd.path)
			self.bookmarks.remember(self.tab.cwd)
			self.bookmarks.save()

	# -=- Tabs -=-
	def tab_open(self, name, path=None):
		do_emit_signal = name != self.tab
		self.tab = name
		if path or (name in self.tabs):
			self.fm.visual = None
			self.enter_dir(path or self.tabs[name])
		else:
			self._update_current_tab()
		if do_emit_signal:
			self.signal_emit('tab.change')

	def tab_close(self, name=None):
		if name is None:
			name = self.tab
		if name == self.tab:
			direction = -1 if name == self._get_tab_list()[-1] else 1
			previous = self.tab
			self.tab_move(direction)
			if previous == self.tab:
				return  # can't close last tab
		if name in self.tabs:
			del self.tabs[name]

	def tab_move(self, offset):
		assert isinstance(offset, int)
		tablist = self._get_tab_list()
		current_index = tablist.index(self.tab)
		newtab = tablist[(current_index + offset) % len(tablist)]
		if newtab != self.tab:
			self.tab_open(newtab)

	def tab_new(self, path=None):
		for i in range(1, 10):
			if not i in self.tabs:
				self.tab_open(i, path)
				break

	def _get_tab_list(self):
		assert len(self.tabs) > 0, "There must be >=1 tabs at all times"
		return sorted(self.tabs)

	def _update_current_tab(self):
		self.tabs[self.tab] = self.env.cwd.path

	def display(self, *msg):
		if self.ui:
			self.ui.display(*msg)
		else:
			print('\n'.join(msg))

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
	def confpath(self, *paths):
		"""returns the path relative to rangers configuration directory"""
		if self.arg.clean:
			assert 0, "Should not access confpath in clean mode!"
		else:
			return os.path.join(self.arg.confdir, *paths)

	def cachepath(self, *paths):
		"""returns the path relative to rangers configuration directory"""
		if self.arg.clean:
			assert 0, "Should not access cachepath in clean mode!"
		else:
			return os.path.join(self.cachedir, *paths)

	def relpath(self, *paths):
		"""returns the path relative to rangers library directory"""
		return os.path.join(ranger.RANGERDIR, *paths)

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
				if self.arg.debug:
					raise
		if self.loader:
			try:
				self.loader.destroy()
			except:
				if self.arg.debug:
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
