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
from ranger.core.actions import Actions
from ranger.core.info import Info
from ranger.container.settingobject import ALLOWED_SETTINGS
from ranger.ext.signals import SignalDispatcher
from ranger.ext.shell_escape import shell_quote
from ranger.ext.keybinding_parser import construct_keybinding

TICKS_BEFORE_COLLECTING_GARBAGE = 100
TIME_BEFORE_FILE_BECOMES_GARBAGE = 1200

class FM(Actions, Info, SignalDispatcher):
	def __init__(self, infoinit=True):
		"""Initialize FM."""
		Actions.__init__(self)
		SignalDispatcher.__init__(self)
		if infoinit:
			Info.__init__(self)
		self.commands = None
		self.macros = {}
		self.log = deque(maxlen=20)
		self.tabs = {}
		self.previews = {}
		self.current_tab = 1

		self.log.append('Ranger {0} started! Process ID is {1}.' \
				.format(self.version, self.pid))
		self.log.append('Running on Python ' + sys.version.split('\n')[0])

	def initialize(self):
		"""If ui/bookmarks are None, they will be initialized here."""
		from ranger.container import Bookmarks
		from ranger.core.runner import Runner
		from ranger.fsobject import Directory
		from ranger.core.loader import Loader
		from ranger.gui.defaultui import DefaultUI

		self.loader = Loader()

		if self.clean:
			bookmarkfile = None
		else:
			bookmarkfile = self.confpath('bookmarks')
		self.bookmarks = Bookmarks(
				bookmarkfile=bookmarkfile,
				bookmarktype=Directory,
				autosave=self.settings.autosave_bookmarks)
		self.bookmarks.load()

		if not self.clean:
			from ranger.container.tags import Tags
			self.tags = Tags(self.confpath('tagged'))
		else:
			self.tags = {}

		self.ui = DefaultUI()
		self.ui.initialize()
		self.run = Runner(ui=self.ui, logfunc=self.err)

		self.env.signal_bind('cd', self._update_current_tab)

		mimetypes.knownfiles.append(os.path.expanduser('~/.mime.types'))
		mimetypes.knownfiles.append(self.relpath('data/mime.types'))
		self.mimetypes = mimetypes.MimeTypes()

	def destroy(self):
		debug = ranger.arg.debug
		if self.ui:
			try:
				self.ui.destroy()
			except:
				if debug:
					raise
		if self.loader:
			try:
				self.loader.destroy()
			except:
				if debug:
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
			self.bookmarks.remember(env.cwd)
			self.bookmarks.save()


	# Command Evaluation
	class MacroTemplate(string.Template):
		"""A template for substituting macros in commands"""
		delimiter = '%'

	class SettingMacroTemplate(string.Template):
		"""A template for substituting macros in commands"""
		delimiter = '&'

	def load_commands(self):
		import ranger.defaults.commands
		import ranger.api.commands
		container = ranger.api.commands.CommandContainer()
		container.load_commands_from_module(ranger.defaults.commands)
		if not self.clean and (exists(self.confpath('commands.py')) or
				exists(self.confpath('commands.pyo')) or
				exists(self.confpath('commands.pyc'))):
			self.allow_importing_from(self.confdir, True)
			try:
				import commands
			except ImportError:
				pass
			else:
				container.load_commands_from_module(commands)
			self.allow_importing_from(self.confdir, False)
		self.commands = container
		return container

	def compile_command_list(self):
		from inspect import cleandoc
		sorted_cmds = list(sorted(self.commands.commands.items(),
			key=lambda (a,b): a))

		content = "List of currently available commands:\n\n"
		for name, cmd in sorted_cmds:
			if cmd.__doc__:
				doc = cleandoc(cmd.__doc__).split("\n")
				if doc[1] == "":
					del doc[1]
				for i in range(1, len(doc)):
					doc[i] = "   " + doc[i]
				content += "\n".join(doc) + "\n\n\n"
			else:
				content += ":%s\n   no description.\n\n\n" % name
		return content

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

	def load_plugin(self, filename):
		import ranger

		# Get the filename and its content
		content = None
		if '/' not in filename:
			if filename[-3:] != '.py':
				real_filename = self.confpath('plugins', filename+'.py')
			else:
				real_filename = self.confpath('plugins', filename)
			try:
				content = open(real_filename).read()
			except:
				pass
		if not content:
			real_filename = filename
			try:
				content = open(filename).read()
			except:
				return False

		# Set up the environment
		remove_ranger_fm = hasattr(ranger, 'fm')
		ranger.fm = self

		# Compile and execute the code
		code = compile(content, real_filename, 'exec')
		exec(code)

		# Clean up
		if remove_ranger_fm and hasattr(ranger, 'fm'):
			del ranger.fm

	def eval(self, code):
		fm = self
		try:
			return eval(code)
		except Exception as ex:
			self.err(ex)
			return None

	def cmd_secure(self, line, lineno=None, n=None):
		try:
			self.cmd(line, n=n)
		except Exception as e:
			if self.debug:
				raise
			else:
				self.err('Error in line `%s\':\n  %s' % (line, str(e)))

	def cmd(self, line, n=None, any=[]):
		if line == 'nodefaults':
			return
		line = line.lstrip()
		if not line or line[0] == '"' or line[0] == '#':
			return
		command_name = line.split(' ', 1)[0]
		ok = self.signal_emit('command.pre', line=line,
				command_name=command_name)
		if not ok:
			return
		try:
			command_entry = self.commands.get_command(command_name)
		except KeyError:
			if self.debug:
				raise Exception("Command `%s' not found!" % command_name)
			elif self.ui_runs:
				self.err("Command `%s' not found! Press ? for help." \
						% command_name)
			else:
				self.err('Error in line `%s\':\n  %s' % \
						(line, 'Invalid Command'))
			return
		except Exception as e:
			self.err(str(e))
			return
		if command_entry:
			command = command_entry()
			if command.resolve_macros and self.MacroTemplate.delimiter in line:
				line = self.substitute_macros(line, any=any)
			command.setargs(line, n=n)
			command.execute()

	def substitute_macros(self, string, any=[]):
		return self.MacroTemplate(string).safe_substitute(
				self._get_macros(any=any))

	def _get_macros(self, any=[]):
		macros = {}

		macros['version'] = self.version
		macros['confdir'] = self.confdir
		macros['rangerdir'] = self.rangerdir
		macros['cachedir'] = self.cachedir

		for i in range(0, 10):
			if i < len(any):
				macros['any' + str(i+1)] = construct_keybinding([any[i]])
			else:
				macros['any' + str(i+1)] = ""
		if any:
			macros['any'] = construct_keybinding([any[0]])
		else:
			macros['any'] = ""

		if self.env.cf:
			macros['f']  = shell_quote(self.env.cf.basename)
			macros['ff'] = self.env.cf.basename
		else:
			macros['f']  = ''
			macros['ff'] = ''

		macros['s'] = ' '.join(shell_quote(fl.basename) \
				for fl in self.env.get_selection())

		macros['c'] = ' '.join(shell_quote(fl.path)
				for fl in self.env.copy)

		if self.ui:
			macros['height'], macros['width'] = self.env.termsize
		else:
			macros['height'], macros['width'] = 24, 80

		if self.env.cwd:
			macros['d'] = shell_quote(self.env.cwd.path)
			macros['t'] = ' '.join(shell_quote(fl.basename)
					for fl in self.env.cwd.files
					if fl.realpath in self.tags)
		else:
			macros['d'] = '.'
			macros['t'] = ''

		for key in ALLOWED_SETTINGS:
			macros[key] = repr(self.settings[key])

		# define d/f/s macros for each tab
		for i in range(1,10):
			try:
				tab_dir_path = self.tabs[i]
			except:
				continue
			tab_dir = self.env.get_directory(tab_dir_path)
			i = str(i)
			if tab_dir and tab_dir.pointed_obj:
				macros[i + 'd'] = shell_quote(tab_dir_path)
				macros[i + 'f'] = shell_quote(tab_dir.pointed_obj.path)
				macros[i + 's'] = ' '.join(shell_quote(fl.path)
					for fl in tab_dir.get_selection())
			else:
				macros[i + 'd'] = ""
				macros[i + 'f'] = ""
				macros[i + 's'] = ""

		# define D/F/S for the next tab
		found_current_tab = False
		next_tab_path = None
		first_tab = None
		for tab in self.tabs:
			if not first_tab:
				first_tab = tab
			if found_current_tab:
				next_tab_path = self.tabs[tab]
				break
			if self.current_tab == tab:
				found_current_tab = True
		if found_current_tab and not next_tab_path:
			next_tab_path = self.tabs[first_tab]
		next_tab = self.env.get_directory(next_tab_path)

		if next_tab and next_tab.pointed_obj:
			macros['D'] = shell_quote(next_tab)
			macros['F'] = shell_quote(next_tab.pointed_obj.path)
			macros['S'] = ' '.join(shell_quote(fl.path)
				for fl in next_tab.get_selection())
		else:
			macros['D'] = ''
			macros['F'] = ''
			macros['S'] = ''
		macros.update(self.macros)

		return macros
