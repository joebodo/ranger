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

'''
This is the default file for command definitions.

Each command is a subclass of `Command'.  Several methods are defined
to interface with the console:
	execute: call this method when the command is executed.
	tab: call this method when tab is pressed.
	quick: call this method after each keypress.

The return values for tab() can be either:
	None: There is no tab completion
	A string: Change the console to this string
	A list/tuple/generator: cycle through every item in it
The return value for quick() can be:
	False: Nothing happens
	True: Execute the command afterwards
The return value for execute() doesn't matter.

If you want to add custom commands, you can create a file
~/.config/ranger/commands.py, add the line:
	from ranger.api.commands import *

and write some command definitions, for example:

	class tabnew(Command):
		def execute(self):
			self.fm.tab_new()

	class tabgo(Command):
		"""
		:tabgo <n>

		Go to the nth tab.
		"""
		def execute(self):
			num = self.line.split()[1]
			self.fm.tab_open(int(num))

For a list of all actions, check /ranger/core/actions.py.
'''

import ranger
fm = ranger.get_fm()


from ranger.api.commands import *
from ranger.ext.get_executables import get_executables
from ranger.runner import ALLOWED_FLAGS
import re


aliases = {
	'e': 'edit',
	'q': 'quit',
	'q!': 'quitall',
	'qall': 'quitall'
}

@fm.register_command
class cd(Command):
	"""
	:cd <dirname>

	The cd command changes the directory.
	The command 'cd -' is equivalent to typing ``.
	"""

	def execute(self):
		if self.arg(1) == '-r':
			import os.path
			self.shift()
			destination = os.path.realpath(self.rest(1))
		else:
			destination = self.rest(1)

		if not destination:
			destination = '~'

		if destination == '-':
			self.fm.enter_bookmark('`')
		else:
			self.fm.cd(destination)

	def tab(self):
		from os.path import dirname, basename, expanduser, join, isdir

		line = parse(self.line)
		cwd = self.fm.env.cwd.path

		try:
			rel_dest = line.rest(1)
		except IndexError:
			rel_dest = ''

		bookmarks = [v.path for v in self.fm.bookmarks.dct.values()
				if rel_dest in v.path ]

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
			dirnames = bookmarks + dirnames

			# no results, return None
			if len(dirnames) == 0:
				return

			# one result. since it must be a directory, append a slash.
			if len(dirnames) == 1:
				return line.start(1) + join(rel_dirname, dirnames[0]) + '/'

			# more than one result. append no slash, so the user can
			# manually type in the slash to advance into that directory
			return (line.start(1) + join(rel_dirname, dirname) for dirname in dirnames)

@fm.register_command
class enter_bookmark(Command):
	""":enter_bookmark <key>
	Enter the given bookmark."""
	def execute(self):
		self.fm.enter_bookmark(self.arg(1))

@fm.register_command
class unset_bookmark(Command):
	""":enter_bookmark <key>
	Delete the given bookmark."""
	def execute(self):
		self.fm.unset_bookmark(self.arg(1))

@fm.register_command
class set_bookmark(Command):
	""":enter_bookmark <key>
	Set the given bookmark to the current directory."""
	def execute(self):
		self.fm.set_bookmark(self.arg(1))

@fm.register_command
class search(Command):
	def execute(self):
		self.fm.search_file(self.rest(1), regexp=True)

@fm.register_command
class load_(Command):
	""":load <file/plugin>
	Loads a plugin or python file."""
	name = 'load'
	def execute(self):
		self.fm.load_plugin(self.rest(1))

@fm.register_command
class search_inc(Command):
	def quick(self):
		self.fm.search_file(parse(self.line).rest(1), regexp=True, offset=0)


@fm.register_command
class shell(Command):
	def execute(self):
		if self.arg(1) and self.arg(1)[0] == '-':
			flags = self.arg(1)[1:]
			command = self.rest(2)
		else:
			flags = ''
			command = self.rest(1)

		if not command and 'p' in flags:
			command = 'cat %f'
		if command:
			self.fm.execute_command(command, flags=flags)

	def tab(self):
		if self.arg(1) and self.arg(1)[0] == '-':
			flags = self.arg(1)[1:]
			command = self.rest(2)
		else:
			flags = ''
			command = self.rest(1)
		start = self.line[0:len(self.line) - len(command)]

		try:
			position_of_last_space = command.rindex(" ")
		except ValueError:
			return (start + program + ' ' for program \
					in get_executables() if program.startswith(command))
		if position_of_last_space == len(command) - 1:
			return self.line + '%s '
		else:
			before_word, start_of_word = self.line.rsplit(' ', 1)
			return (before_word + ' ' + file.shell_escaped_basename \
					for file in self.fm.env.cwd.files \
					if file.shell_escaped_basename.startswith(start_of_word))

@fm.register_command
class map_(Command):
	""":map <keysequence> <command>
	Maps a command to a keysequence in the "browser" context.

	Example:
	map j move down
	map J move down 10
	"""
	name = 'map'
	context = 'browser'
	resolve_macros = False
	def execute(self):
		command = self.rest(2)
		self.fm.env.keymanager.map(self.context, self.arg(1),
			func=(lambda arg: arg.fm.cmd(command, n=arg.n, any=arg.matches)),
			help=command)

@fm.register_command
class pass_(Command):
	""":pass
	Null command, does nothing."""
	name = 'pass'

@fm.register_command
class cmap(map_):
	""":cmap <keysequence> <command>
	Maps a command to a keysequence in the "console" context.

	Example:
	map <ESC> console_close
	map <C-x> console_type test
	"""
	context = 'console'

@fm.register_command
class tmap(map_):
	""":tmap <keysequence> <command>
	Maps a command to a keysequence in the "taskview" context.

	Example:
	map <ESC> console_close
	map <C-x> console_type test
	"""
	context = 'taskview'

@fm.register_command
class console_type(Command):
	""":console_type <text>
	Type the given text into the console"""
	def execute(self):
		self.fm.ui.console.type_key(self.rest(1))

@fm.register_command
class next_(Command):
	""":next [<method>]
	Go to the next object with a given method.
	With no method, move to the next object with the previously used method.
	Methods are: tag, ctime, mimetype, size, text
	"""
	name = 'next'
	forward = True
	def execute(self):
		method = self.arg(1)
		if not method:
			self.fm.search(forward=self.forward)
		elif method in ('tag', 'ctime', 'mimetype', 'size', 'text'):
			self.fm.search(order=method, forward=self.forward)
		else:
			self.fm.err("No such search method: `%s'" % method)

@fm.register_command
class previous(next_):
	forward = False

@fm.register_command
class hint(Command):
	""":hint [<method> [<text>]]
	Display information to help the user.
	":hint" displays all keys which can follow with this key combination.
	":hint bookmarks" displays all bookmarks
	":hint text <text>" displays the given text in the statusbar.
	"""
	def execute(self):
		if self.arg(1) == 'bookmarks':
			self.fm.ui.browser.draw_bookmarks = True
		elif self.arg(1) == 'text':
			self.fm.ui.hint(self.rest(2))
		else:
			self.fm.ui.browser.draw_hints = True

@fm.register_command
class chain(Command):
	""":chain <command1>; <command2>; ...
	Calls multiple commands at once, separated by semicolons.
	"""
	def execute(self):
		for command in self.rest(1).split(";"):
			self.fm.cmd(command)

@fm.register_command
class tab(Command):
	""":tab <path>
	Open a new tab and move to the given path"""
	def execute(self):
		self.fm.tab_new(path=self.rest(1) or None)

@fm.register_command
class tabnext(Command):
	""":tabnext
	Move to the next tab"""
	def execute(self):
		self.fm.tab_move(1)

@fm.register_command
class tabprevious(Command):
	""":tabprevious
	Move to the previous tab"""
	def execute(self):
		self.fm.tab_move(-1)

@fm.register_command
class tabclose(Command):
	""":tabclose
	Close the current tab."""
	def execute(self):
		self.fm.tab_close()

@fm.register_command
class tabopen(Command):
	""":tabopen <name>
	Open the tab with the given name"""
	def execute(self):
		name = self.arg(1)
		if name.isdigit():
			name = int(name)
		self.fm.tab_open(name=name)

@fm.register_command
class tag(Command):
	""":tag
	Toggle whether a file is tagged or not.
	Tagged files will have a * sign left of them.  The meaning of tagged files
	is up to you.  Use it to tag unread papers, unheared songs,...
	"""
	def execute(self):
		self.fm.tag_toggle()

@fm.register_command
class untag(Command):
	""":untag
	Remove the tag-status of a file.
	"""
	def execute(self):
		self.fm.tag_remove()

@fm.register_command
class move(Command):
	""":move <direction>
	move inside the current column."""
	def execute(self):
		direction = self.arg(1)
		n = self.n
		kw = {}
		try:
			mult = float(self.arg(2))
		except:
			mult = 1
		if 'pages' in self.args:
			kw['pages'] = True
		if direction == 'down':
			self.fm.move(down=(1 if n is None else n) * mult, **kw)
		elif direction == 'up':
			self.fm.move(up=(1 if n is None else n) * mult, **kw)
		elif direction == 'left':
			self.fm.enter_dir("..")
		elif direction == 'right':
			self.fm.cmd("execute")
		elif direction == 'home':
			self.fm.move(down=(0 if n is None else n) * mult,
					absolute=True, **kw)
		elif direction == 'end':
			self.fm.move(down=(-1 if n is None else n) * mult,
					absolute=True, **kw)

@fm.register_command
class move_in_column(Command):
	""":move_in_column <column> <direction>
	move inside the given column.
	column 0 is the current column, -1 is the parent column"""
	def execute(self):
		col = int(self.arg(1))
		n = self.n
		if col == 0:
			self.fm.cmd("move %s" % self.rest(2))
		elif col == -1:
			try:
				mult = float(self.arg(3))
			except:
				mult = 1
			if self.arg(2) == 'down':
				self.fm.move_parent((1 if n is None else n) * mult)
			elif self.arg(2) == 'up':
				self.fm.move_parent(-(1 if n is None else n) * mult)

@fm.register_command
class execute(Command):
	""":execute
	Start the files with the program defined in %file_launcher.
	"""
	def execute(self):
		cf = self.fm.env.cf
		selection = self.fm.env.get_selection()
		if self.fm.env.enter_dir(cf):
			return
		elif selection:
			self.fm.cmd("shell %file_launcher %s")

@fm.register_command
class find(Command):
	"""
	:find <string>

	The find command will attempt to find a partial, case insensitive
	match in the filenames of the current directory and execute the
	file automatically.
	"""

	count = 0
	tab = Command._tab_directory_content

	def execute(self):
		if self.count == 1:
			self.fm.move(right=1)
			self.fm.block_input(0.5)
		else:
			self.fm.cd(self.rest(1))

	def quick(self):
		self.count = 0
		cwd = self.fm.env.cwd
		try:
			arg = self.rest(1)
		except IndexError:
			return False

		if arg == '.':
			return False
		if arg == '..':
			return True

		deq = deque(cwd.files)
		deq.rotate(-cwd.pointer)
		i = 0
		case_insensitive = arg.lower() == arg
		for fsobj in deq:
			if case_insensitive:
				filename = fsobj.basename_lower
			else:
				filename = fsobj.basename
			if arg in filename:
				self.count += 1
				if self.count == 1:
					cwd.move(to=(cwd.pointer + i) % len(cwd.files))
					self.fm.env.cf = cwd.pointed_obj
			if self.count > 1:
				return False
			i += 1

		return self.count == 1


@fm.register_command
class let(Command):
	""":let <name> <operator> <value>
	Change the value of a macro.  Macros are words that start with a % sign.
	When used in commands, they are replaced with their value.
	Operators are: =, +=, -=, .=

	Example:
	:let foo = hello
	:let foo .= _world
	:echo %foo
	=> hello_world
	"""
	def execute(self):
		macros = self.fm.macros
		newval = self.rest(3)
		op = self.arg(2)
		if self.arg(1) == '-e':
			self.shift()
			newval = self.fm.eval(self.rest(3))

		try:
			var = macros[self.arg(1)]
		except:
			var = 0
		if op == '=':
			macros[self.arg(1)] = newval
		elif op == '+=':
			macros[self.arg(1)] = str(int(var) + int(newval))
		elif op == '-=':
			macros[self.arg(1)] = str(int(var) - int(newval))
		elif op == '.=':
			macros[self.arg(1)] = str(var) + str(newval)
		else:
			self.fm.err("unknown operation `%s'" % op)

@fm.register_command
class set_(Command):
	"""
	:set <option name>=<python expression>

	Gives an option a new value.
	"""
	name = 'set'  # don't override the builtin set class
	listre = re.compile('[, ]+')
	def execute(self):
		if not len(self.args) >= 3:
			return
		from ranger.container.settings import DEFAULT_SETTINGS
		key = self.arg(1)
		op = self.arg(2)
		value = self.rest(3)
		try:
			typ = ALLOWED_SETTINGS[key][0]
		except:
			raise
		else:
			if type(typ) == tuple:
				typ = typ[0]
			if typ == bool:
				value = value not in ('false', 'False', '0')
			elif typ == int:
				value = int(value)
			elif typ == list:
				value = list(int(i) for i in self.listre.split(value))
			elif typ == tuple:
				value = tuple(int(i) for i in self.listre.split(value))
			elif typ == type(re.compile("")):
				value = re.compile(value, re.I)
			if op == '=':
				self.fm.settings[key] = value
			elif op == '^=' and typ == bool:
				self.fm.settings[key] ^= bool(value)

	def tab(self):
		name = self.arg(1)
		name_done = ' ' in self.rest(1)
		value = self.rest(2)
		settings = self.fm.settings
		if not name:
			return (self.tabinsert(setting) for setting in settings)
		if not value and not name_done:
			return (self.tabinsert(setting) for setting in settings \
					if setting.startswith(name))
		if not value:
			return self.tabinsert(repr(settings[name]))
		if bool in settings.types_of(name):
			if 'true'.startswith(value.lower()):
				return self.tabinsert('True')
			if 'false'.startswith(value.lower()):
				return self.tabinsert('False')

@fm.register_command
class toggle(Command):
	""":toggle <option>
	Toggles the value of a boolean option."""
	def execute(self):
		from ranger.container.settings import DEFAULT_SETTINGS
		key = self.arg(1)
		try:
			typ = ALLOWED_SETTINGS[key][0]
		except:
			return self.fm.err("No such setting: `%s'" % key)
		if typ != bool:
			return self.fm.err("Trying to toggle non-boolean setting `%s'" \
					% key)
		self.fm.settings[key] = not self.fm.settings[key]

@fm.register_command
class quit(Command):
	"""
	:quit

	Closes the current tab.  If there is only one tab, quit the program.
	"""

	def execute(self):
		if len(self.fm.tabs) <= 1:
			self.fm.exit()
		self.fm.tab_close()


@fm.register_command
class quitall(Command):
	"""
	:quitall

	Quits the program immediately.
	"""

	def execute(self):
		self.fm.exit()


@fm.register_command
class quit_bang(quitall):
	"""
	:quit!

	Quits the program immediately.
	"""
	name = 'quit!'
	allow_abbrev = False


@fm.register_command
class terminal(Command):
	"""
	:terminal

	Spawns an "x-terminal-emulator" starting in the current directory.
	"""
	def execute(self):
		self.fm.run('x-terminal-emulator', flags='d')


@fm.register_command
class delete(Command):
	"""
	:delete

	Tries to delete the selection.

	"Selection" is defined as all the "marked files" (by default, you
	can mark files with space or v). If there are no marked files,
	use the "current file" (where the cursor is)

	When attempting to delete non-empty directories or multiple
	marked files, it will require a confirmation: The last word in
	the line has to start with a 'y'.  This may look like:
	:delete yes
	:delete seriously? yeah!
	"""

	allow_abbrev = False

	def execute(self):
		lastword = self.arg(-1)

		if lastword.startswith('y'):
			# user confirmed deletion!
			self.fm.visual_end()
			return self.fm.delete()
		elif self.line.startswith(DELETE_WARNING):
			# user did not confirm deletion
			return

		cwd = self.fm.env.cwd
		cf = self.fm.env.cf

		if cwd.marked_items or (cf.is_directory and not cf.is_link \
				and len(os.listdir(cf.path)) > 0):
			# better ask for a confirmation, when attempting to
			# delete multiple files or a non-empty directory.
			return self.fm.open_console(DELETE_WARNING)

		# no need for a confirmation, just delete
		self.fm.delete()


@fm.register_command
class console(Command):
	""":console [-p <position>] <text>
	Opens the console and inserts the given text.
	If -p is used, the cursor position is set to the given number."""
	def execute(self):
		position = None
		if self.arg(1)[0:2] == '-p':
			self.shift()
			if len(self.arg(0)) > 2:
				position = int(self.arg(0)[2:])
			else:
				self.shift()
				position = int(self.arg(0))
		elif self.arg(1) == '-x':
			return self.fm.cmd(self.rest(2))
		self.fm.ui.open_console(self.rest(1), position=position)

@fm.register_command
class console_execute(Command):
	""":console_execute
	Execute the command in the console."""
	def execute(self):
		self.fm.ui.console.execute()

@fm.register_command
class console_close(Command):
	""":console_close
	Close the console"""
	def execute(self):
		self.fm.ui.console.close()

@fm.register_command
class eval_macros(Command):
	""":eval_macros <command>
	Run the given command with macros evaluated.

	Example:
	:let foo = macro evaluated!
	:echo %%foo
	:eval_macros echo %%foo"""
	def execute(self):
		return self.fm.cmd(self.rest(1))

@fm.register_command
class history(Command):
	""":history <offset>
	Move in the history by the given offset.  -1 for back, 1 for forward."""
	def execute(self):
		self.fm.history_go(int(self.arg(1)))

@fm.register_command
class copy(Command):
	""":copy <direction> <mode>
	Operates on the files in the given direction and either sets, adds or removes
	those files to/from the copy buffer.
	mode is one of set, add, remove
	direction is one of up, down, home, end, selection, clear
	"""
	method = 'copy'
	def execute(self):
		from ranger.ext.direction import Direction
		fnc = getattr(self.fm, self.method)
		arg1 = self.arg(1)
		if arg1 == 'selection' or not arg1:
			mode = self.arg(2) in ('set', 'add', 'remove') \
					and self.arg(2) or 'set'
			fnc(narg=self.n, mode=mode)
		elif arg1 == 'down':
			fnc(dirarg=Direction(down=1), narg=self.n)
		elif arg1 == 'up':
			fnc(dirarg=Direction(up=1), narg=self.n)
		elif arg1 == 'home':
			fnc(dirarg=Direction(down=0, absolute=True), narg=self.n)
		elif arg1 == 'end':
			fnc(dirarg=Direction(down=-1, absolute=True), narg=self.n)
		elif arg1 == 'clear':
			self.fm.uncut()

@fm.register_command
class cut(copy):
	""":cut <direction> <mode>
	Operates on the files in the given direction and either sets, adds or removes
	those files to/from the copy buffer.
	The difference to :copy is: the files are moved instead of copied.
	mode is one of set, add, remove
	direction is one of up, down, home, end, selection, clear
	"""
	method = 'cut'

@fm.register_command
class paste(Command):
	""":paste [<method>]
	Pastes the copied or cut files.
	Methods: overwrite, symlink, relative_symlink
	"""
	def execute(self):
		overwrite = 'overwrite' in self.args
		if 'symlink' in self.args:
			self.fm.paste_symlink(relative=False)
		elif 'relative_symlink' in self.args:
			self.fm.paste_symlink(relative=True)
		else:
			self.fm.paste(overwrite=overwrite)

@fm.register_command
class mark(Command):
	do_mark = True
	def execute(self):
		subcommand = self.arg(1)
		if subcommand == 'toggle':
			self.fm.mark(toggle=True, all=self.arg(2) == 'all',
					val=self.do_mark)
		elif subcommand == 'all':
			self.fm.mark(all=True, val=self.do_mark)
		elif subcommand == 'regexp':
			import re
			cwd = self.fm.env.cwd
			input = self.rest(2)
			searchflags = re.UNICODE
			if input.lower() == input: # "smartcase"
				searchflags |= re.IGNORECASE
			pattern = re.compile(input, searchflags)
			for fileobj in cwd.files:
				if pattern.search(fileobj.basename):
					cwd.mark_item(fileobj, val=self.do_mark)
			self.fm.ui.status.need_redraw = True
			self.fm.ui.need_redraw = True

@fm.register_command
class unmark(mark):
	do_mark = False

@fm.register_command
class visual(Command):
	""":visual [reverse]
	Enable the visual mode: All movement will select every file between the starting
	point and the end point of the movement.
	If the first argument is "reverse", the files are unselected instead.
	Use :escape to return to the normal mode."""
	def execute(self):
		self.fm.visual_start(self.arg(1) != 'reverse')

@fm.register_command
class escape(Command):
	""":escape
	Escape to the normal mode, if you have changed it to e.g. the visual mode."""
	def execute(self):
		self.fm.visual_end()

@fm.register_command
class break_(Command):
	""":break
	executed when pressing Ctrl+C, aborts loading/copying/..."""
	name = 'break'
	def execute(self):
		try:
			item = self.fm.loader.queue[0]
		except:
			self.fm.write("Type Q or :quit<Enter> to exit Ranger")
		else:
			self.fm.write("Aborting: " + item.get_description())
			self.fm.loader.remove(index=0)

@fm.register_command
class load_copy_buffer(Command):
	"""
	:load_copy_buffer

	Load the copy buffer from confdir/copy_buffer
	"""
	copy_buffer_filename = 'copy_buffer'
	def execute(self):
		from ranger.fsobject import File
		from os.path import exists
		try:
			f = open(self.fm.confpath(self.copy_buffer_filename), 'r')
		except:
			return self.fm.notify("Cannot open file %s" % fname, bad=True)
		self.fm.env.copy = set(File(g) \
			for g in f.read().split("\n") if exists(g))
		f.close()
		self.fm.ui.redraw_main_column()

@fm.register_command
class save_copy_buffer(Command):
	"""
	:save_copy_buffer

	Save the copy buffer to confdir/copy_buffer
	"""
	copy_buffer_filename = 'copy_buffer'
	def execute(self):
		try:
			f = open(self.fm.confpath(self.copy_buffer_filename), 'w')
		except:
			return self.fm.notify("Cannot open file %s" % fname, bad=True)
		f.write("\n".join(f.path for f in self.fm.env.copy))
		f.close()

@fm.register_command
class help(Command):
	""":help
	Displays the help text in the pager."""
	def execute(self):
		if self.arg(1):
			try:
				data = self.fm.plugins[self.arg(1)]['help']
			except:
				self.fm.err("No data available on a plugin named `%s'" \
						% self.arg(1))
			else:
				self.fm.display_in_pager(data)
		else:
			from ranger.help import get_help_by_index
			index = self.n or 0
			if index == 8:
				self.fm.display_in_pager(self.fm.compile_plugin_list())
			elif index == 9:
				self.fm.display_in_pager(self.fm.compile_command_list())
			else:
				self.fm.display_in_pager(get_help_by_index(index))

@fm.register_command
class display_log(Command):
	""":display_log
	Displays the current log of ranger in the pager."""
	def execute(self):
		self.fm.display_in_pager("\n".join(reversed(self.fm.log)))

@fm.register_command
class mkdir(Command):
	"""
	:mkdir <dirname>

	Creates a directory with the name <dirname>.
	"""

	def execute(self):
		from os.path import join, expanduser, lexists
		from os import mkdir

		dirname = join(self.fm.env.cwd.path, expanduser(self.rest(1)))
		if not lexists(dirname):
			mkdir(dirname)
		else:
			self.fm.notify("file/directory exists!", bad=True)

@fm.register_command
class touch(Command):
	"""
	:touch <fname>

	Creates a file with the name <fname>.
	"""

	def execute(self):
		from os.path import join, expanduser, lexists
		from os import mkdir

		fname = join(self.fm.env.cwd.path, expanduser(self.rest(1)))
		if not lexists(fname):
			open(fname, 'a')
		else:
			self.fm.notify("file/directory exists!", bad=True)

@fm.register_command
class edit(Command):
	"""
	:edit <filename>
	Opens the specified file in vim
	"""

	def execute(self):
		if not self.arg(1):
			self.fm.edit_file(self.fm.env.cf.path)
		else:
			self.fm.edit_file(self.rest(1))

	def tab(self):
		return self._tab_directory_content()

@fm.register_command
class eval_(Command):
	"""
	:eval <python code>

	Evaluates the python code.
	`fm' is a reference to the FM instance.
	To display text, use the function `p'.

	Examples:
	:eval fm
	:eval len(fm.env.directories)
	:eval p("Hello World!")
	"""
	name = 'eval'

	def execute(self):
		if self.arg(1) == '-q':
			code = self.rest(2)
			quiet = True
		else:
			code = self.rest(1)
			quiet = False
		fm = self.fm
		p = fm.notify
		try:
			try:
				result = eval(code)
			except SyntaxError:
				exec(code)
			else:
				if result and not quiet:
					p(result)
		except Exception as err:
			if not quiet:
				p(err)

@fm.register_command
class echo(Command):
	""":echo <text>
	Displays the given text in the statusbar."""
	def execute(self):
		self.fm.write(self.rest(1))

@fm.register_command
class rename(Command):
	"""
	:rename <newname>

	Changes the name of the currently highlighted file to <newname>
	"""

	def execute(self):
		from ranger.fsobject import File
		if not self.rest(1):
			return self.fm.notify('Syntax: rename <newname>', bad=True)
		self.fm.rename(self.fm.env.cf, self.rest(1))
		f = File(self.rest(1))
		self.fm.env.cwd.pointed_obj = f
		self.fm.env.cf = f

	def tab(self):
		return self._tab_directory_content()

@fm.register_command
class filter(Command):
	"""
	:filter <string>

	Displays only the files which contain <string> in their basename.
	"""

	def execute(self):
		self.fm.set_filter(self.rest(1))
		self.fm.reload_cwd()

@fm.register_command
class reload(Command):
	""":reload
	Reload the current directory"""
	def execute(self):
		self.fm.reload_cwd()

@fm.register_command
class reset(Command):
	""":reset
	Reset the file manager, clearing caches.  Usually mapped to <C-R>"""
	def execute(self):
		self.fm.reset()

@fm.register_command
class redraw(Command):
	""":redraw
	Redraw the window.  Usually mapped to <C-L>"""
	def execute(self):
		self.fm.redraw_window()

@fm.register_command
class grep(Command):
	"""
	:grep <string>

	Looks for a string in all marked files or directories
	"""

	def execute(self):
		if self.rest(1):
			action = ['grep', '--color=always', '--line-number']
			action.extend(['-e', self.rest(1), '-r'])
			action.extend(f.path for f in self.fm.env.get_selection())
			self.fm.execute_command(action, flags='p')
