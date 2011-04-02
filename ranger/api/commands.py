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

import os
from collections import deque
from ranger.api import *
from ranger.core.shared import FileManagerAware
from ranger.ext.lazy_property import lazy_property
import string

class VarTemplate(string.Template):
	"""A template for substituting variables in commands"""
	delimiter = '%'

class CommandHandler(object):
	def __init__(self):
		self._commands = {}
		self._command_aliases = {}

	def register_command(self, command):
		classdict = command.__mro__[0].__dict__
		if 'name' in classdict and classdict['name']:
			self._commands[classdict['name']] = command
		else:
			self._commands[command.__name__] = command

	def get_command(self, name, abbrev=True):
		if abbrev:
			lst = [cls for cmd, cls in self._commands.items() \
					if cls.allow_abbrev and cmd.startswith(name) \
					or cmd == name]
			if len(lst) == 0:
				raise KeyError
			if len(lst) == 1:
				return lst[0]
			if self._commands[name] in lst:
				return self._commands[name]
			raise ValueError("Ambiguous command")
		else:
			try:
				return self._commands[name]
			except KeyError:
				return None

	def alias_command(self, new, old):
		if old in self._commands:
			self._commands[new] = self._commands[old]
			self._command_aliases[new] = old

	def command_generator(self, start):
		return (cmd + ' ' for cmd in self._commands if cmd.startswith(start))

	def cmd(self, line, n=None, any=[]):
		line = line.lstrip()
		if not line or line[0] == '#':
			return
		command_name = line.split(' ', 1)[0]
		ok = self.signal_emit('command.pre', line=line,
				command_name=command_name)
		if not ok:
			return
		try:
			command_entry = self._commands.get_command(command_name)
		except KeyError:
			if ranger.DEBUG:
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
			if command.resolve_variables and self.VarTemplate.delimiter in line:
				line = self.substitute_variables(line, any=any)
			command.setargs(line, n=n)
			command.execute()

	def cmd_secure(self, line, lineno=None, n=None):
		try:
			self.cmd(line, n=n)
		except Exception as e:
			if ranger.DEBUG:
				raise
			else:
				self.err('Error in line `%s\':\n  %s' % (line, str(e)))

	def substitute_variables(self, string, any=[]):
		return self.VarTemplate(string).safe_substitute(
				self._get_variables(any=any))

	def _get_variables(self, any=[]):
		variables = {}

		variables['version'] = self.version
		variables['confdir'] = self.confdir
		variables['rangerdir'] = self.rangerdir
		variables['cachedir'] = self.cachedir

		for i in range(0, 10):
			if i < len(any):
				variables['any' + str(i+1)] = construct_keybinding([any[i]])
			else:
				variables['any' + str(i+1)] = ""
		if any:
			variables['any'] = construct_keybinding([any[0]])
		else:
			variables['any'] = ""

		if self.env.cf:
			variables['f']  = shell_quote(self.env.cf.basename)
			variables['ff'] = self.env.cf.basename
		else:
			variables['f']  = ''
			variables['ff'] = ''

		variables['s'] = ' '.join(shell_quote(fl.basename) \
				for fl in self.env.get_selection())

		variables['c'] = ' '.join(shell_quote(fl.path)
				for fl in self.env.copy)

		if self.ui:
			variables['height'], variables['width'] = self.env.termsize
		else:
			variables['height'], variables['width'] = 24, 80

		if self.env.cwd:
			variables['d'] = shell_quote(self.env.cwd.path)
			variables['t'] = ' '.join(shell_quote(fl.basename)
					for fl in self.env.cwd.files
					if fl.realpath in self.tags)
		else:
			variables['d'] = '.'
			variables['t'] = ''

		for key in ALLOWED_SETTINGS:
			variables[key] = repr(self.settings[key])

		# define d/f/s variables for each tab
		for i in range(1,10):
			try:
				tab_dir_path = self.tabs[i]
			except:
				continue
			tab_dir = self.env.get_directory(tab_dir_path)
			i = str(i)
			if tab_dir and tab_dir.pointed_obj:
				variables[i + 'd'] = shell_quote(tab_dir_path)
				variables[i + 'f'] = shell_quote(tab_dir.pointed_obj.path)
				variables[i + 's'] = ' '.join(shell_quote(fl.path)
					for fl in tab_dir.get_selection())
			else:
				variables[i + 'd'] = ""
				variables[i + 'f'] = ""
				variables[i + 's'] = ""

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
			variables['D'] = shell_quote(next_tab)
			variables['F'] = shell_quote(next_tab.pointed_obj.path)
			variables['S'] = ' '.join(shell_quote(fl.path)
				for fl in next_tab.get_selection())
		else:
			variables['D'] = ''
			variables['F'] = ''
			variables['S'] = ''
		variables.update(self.variables)

		return variables


class Command(FileManagerAware):
	"""Abstract command class"""
	name = None
	resolve_variables = True
	allow_abbrev = True
	_shifted = 0

	def setargs(self, line, pos=None, n=None):
		self.line = line
		self.args = line.split()
		self.n = n
		if pos is None:
			self.pos = len(line)
		else:
			self.pos = pos
		return self

	def execute(self):
		"""Override this"""

	def tab(self):
		"""Override this"""

	def quick(self):
		"""Override this"""

	# Easy ways to get information
	def arg(self, n):
		"""Returns the nth space separated word"""
		try:
			return self.args[n]
		except IndexError:
			return ""

	def rest(self, n):
		"""Returns everything from and after arg(n)"""
		got_space = False
		word_count = 0
		for i in range(len(self.line)):
			if self.line[i] == " ":
				if not got_space:
					got_space = True
					word_count += 1
			elif got_space:
				got_space = False
				if word_count == n + self._shifted:
					return self.line[i:]
		return ""

	def start(self, n):
		"""Returns everything until (inclusively) arg(n)"""
		return ' '.join(self.args[:n]) + " " # XXX

	def shift(self):
		del self.args[0]
		self._shifted += 1

	def tabinsert(self, word):
		return ''.join([self._tabinsert_left, word, self._tabinsert_right])

	@lazy_property
	def _tabinsert_left(self):
		try:
			return self.line[:self.line[0:self.pos].rindex(' ') + 1]
		except ValueError:
			return ''

	@lazy_property
	def _tabinsert_right(self):
		return self.line[self.pos:]

	# Tab stuff
	# COMPAT: this is still used in old commands.py configs
	def _tab_only_directories(self):
		from os.path import dirname, basename, expanduser, join, isdir

		cwd = self.fm.env.cwd.path

		try:
			rel_dest = self.rest(1)
		except IndexError:
			rel_dest = ''

		# expand the tilde into the user directory
		if rel_dest.startswith('~'):
			rel_dest = expanduser(rel_dest)

		# define some shortcuts
		abs_dest = join(cwd, rel_dest)
		abs_dirname = dirname(abs_dest)
		rel_basename = basename(rel_dest)
		rel_dirname = dirname(rel_dest)

		try:
			# are we at the end of a directory?
			if rel_dest.endswith('/') or rel_dest == '':
				_, dirnames, _ = next(os.walk(abs_dest))

			# are we in the middle of the filename?
			else:
				_, dirnames, _ = next(os.walk(abs_dirname))
				dirnames = [dn for dn in dirnames \
						if dn.startswith(rel_basename)]
		except (OSError, StopIteration):
			# os.walk found nothing
			pass
		else:
			dirnames.sort()

			# no results, return None
			if len(dirnames) == 0:
				return

			# one result. since it must be a directory, append a slash.
			if len(dirnames) == 1:
				return self.start(1) + join(rel_dirname, dirnames[0]) + '/'

			# more than one result. append no slash, so the user can
			# manually type in the slash to advance into that directory
			return (self.start(1) + join(rel_dirname, dirname) \
				for dirname in dirnames)

	def _tab_directory_content(self):
		from os.path import dirname, basename, expanduser, join, isdir

		cwd = self.fm.env.cwd.path

		try:
			rel_dest = self.rest(1)
		except IndexError:
			rel_dest = ''

		# expand the tilde into the user directory
		if rel_dest.startswith('~'):
			rel_dest = expanduser(rel_dest)

		# define some shortcuts
		abs_dest = join(cwd, rel_dest)
		abs_dirname = dirname(abs_dest)
		rel_basename = basename(rel_dest)
		rel_dirname = dirname(rel_dest)

		try:
			# are we at the end of a directory?
			if rel_dest.endswith('/') or rel_dest == '':
				_, dirnames, filenames = next(os.walk(abs_dest))
				names = dirnames + filenames

			# are we in the middle of the filename?
			else:
				_, dirnames, filenames = next(os.walk(abs_dirname))
				names = [name for name in (dirnames + filenames) \
						if name.startswith(rel_basename)]
		except (OSError, StopIteration):
			# os.walk found nothing
			pass
		else:
			names.sort()

			# no results, return None
			if len(names) == 0:
				return

			# one result. since it must be a directory, append a slash.
			if len(names) == 1:
				return self.start(1) + join(rel_dirname, names[0]) + '/'

			# more than one result. append no slash, so the user can
			# manually type in the slash to advance into that directory
			return (self.start(1) + join(rel_dirname, name) for name in names)
