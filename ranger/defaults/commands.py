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

from ranger.api.commands import *
from ranger.ext.get_executables import get_executables
from ranger.core.runner import ALLOWED_FLAGS
import re

aliases = {
	'e': 'edit',
	'q': 'quit',
	'q!': 'quitall',
	'qall': 'quitall'
}

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
		return self._tab_only_directories()

class enter_bookmark(Command):
	def execute(self):
		self.fm.enter_bookmark(self.arg(1))

class unset_bookmark(Command):
	def execute(self):
		self.fm.unset_bookmark(self.arg(1))

class set_bookmark(Command):
	def execute(self):
		self.fm.set_bookmark(self.arg(1))

class search(Command):
	def execute(self):
		self.fm.search_file(self.rest(1), regexp=True)


class load_(Command):
	name = 'load'
	def execute(self):
		self.fm.load_plugin(self.rest(1))


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

class map_(Command):
	name = 'map'
	context = 'browser'
	resolve_macros = False
	def execute(self):
		command = self.rest(2)
		self.fm.env.keymanager.get_context(self.context)(self.arg(1),
			func=(lambda arg: arg.fm.cmd(command, n=arg.n, any=arg.matches)),
			help=command)

class pass_(Command):
	name = 'pass'

class cmap(map_):
	context = 'console'

class tmap(map_):
	context = 'taskview'

class console_type(Command):
	def execute(self):
		self.fm.ui.console.type_key(self.rest(1))

class next_(Command):
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

class previous(next_):
	forward = False

class hint(Command):
	def execute(self):
		if self.arg(1) == 'bookmarks':
			self.fm.ui.browser.draw_bookmarks = True
		elif self.arg(1) == 'text':
			self.fm.ui.hint(self.rest(2))
		else:
			self.fm.ui.browser.draw_hints = True

class chain(Command):
	def execute(self):
		for command in self.rest(1).split(";"):
			self.fm.cmd(command)

class tab(Command):
	def execute(self):
		self.fm.tab_new(path=self.rest(1) or None)

class tabnext(Command):
	def execute(self):
		self.fm.tab_move(1)

class tabprevious(Command):
	def execute(self):
		self.fm.tab_move(-1)

class tabclose(Command):
	def execute(self):
		self.fm.tab_close()

class tabopen(Command):
	def execute(self):
		name = self.arg(1)
		if name.isdigit():
			name = int(name)
		self.fm.tab_open(name=name)

class tag(Command):
	def execute(self):
		self.fm.tag_toggle()

class untag(Command):
	def execute(self):
		self.fm.tag_remove()

class move(Command):
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
			self.fm.cmd("cd ..")
		elif direction == 'right':
			self.fm.cmd("execute")
		elif direction == 'home':
			self.fm.move(down=(0 if n is None else n) * mult,
					absolute=True, **kw)
		elif direction == 'end':
			self.fm.move(down=(-1 if n is None else n) * mult,
					absolute=True, **kw)

class move_in_column(Command):
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

class execute(Command):
	def execute(self):
		cf = self.fm.env.cf
		selection = self.fm.env.get_selection()
		if self.fm.env.enter_dir(cf):
			return
		elif selection:
			self.fm.execute_command(self.fm.substitute_macros(
				"%file_launcher %s"))

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


class let(Command):
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
		from ranger.container.settingobject import ALLOWED_SETTINGS
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

class toggle(Command):
	def execute(self):
		from ranger.container.settingobject import ALLOWED_SETTINGS
		key = self.arg(1)
		try:
			typ = ALLOWED_SETTINGS[key][0]
		except:
			return self.fm.err("No such setting: `%s'" % key)
		if typ != bool:
			return self.fm.err("Trying to toggle non-boolean setting `%s'" \
					% key)
		self.fm.settings[key] = not self.fm.settings[key]

class quit(Command):
	"""
	:quit

	Closes the current tab.  If there is only one tab, quit the program.
	"""

	def execute(self):
		if len(self.fm.tabs) <= 1:
			self.fm.exit()
		self.fm.tab_close()


class quitall(Command):
	"""
	:quitall

	Quits the program immediately.
	"""

	def execute(self):
		self.fm.exit()


class quit_bang(quitall):
	"""
	:quit!

	Quits the program immediately.
	"""
	name = 'quit!'
	allow_abbrev = False


class terminal(Command):
	"""
	:terminal

	Spawns an "x-terminal-emulator" starting in the current directory.
	"""
	def execute(self):
		self.fm.run('x-terminal-emulator', flags='d')


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


class console(Command):
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

class console_execute(Command):
	def execute(self):
		self.fm.ui.console.execute()

class console_delete(Command):
	def execute(self):
		if self.arg(1) == 'here':
			self.fm.ui.console.delete(-1)
		else:
			self.fm.ui.console.delete(1)

class console_close(Command):
	def execute(self):
		self.fm.ui.console.close()

class eval_macros(Command):
	def execute(self):
		return self.fm.cmd(self.rest(1))

class history(Command):
	def execute(self):
		self.fm.history_go(int(self.arg(1)))

class console_history(Command):
	def execute(self):
		self.fm.ui.console.history_move(int(self.arg(1)))

class console_move(Command):
	def execute(self):
		arg1 = self.arg(1)
		if arg1 == 'left':
			self.fm.ui.console.move(left=1)
		elif arg1 == 'right':
			self.fm.ui.console.move(right=1)
		elif arg1 == 'home':
			self.fm.ui.console.move(right=0, absolute=True)
		elif arg1 == 'end':
			self.fm.ui.console.move(right=-1, absolute=True)

class copy(Command):
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

class cut(copy):
	method = 'cut'

class paste(Command):
	def execute(self):
		overwrite = 'overwrite' in self.args
		if 'symlink' in self.args:
			self.fm.paste_symlink(relative=False)
		elif 'relative_symlink' in self.args:
			self.fm.paste_symlink(relative=True)
		else:
			self.fm.paste(overwrite=overwrite)

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

class unmark(mark):
	do_mark = False

class visual(Command):
	def execute(self):
		value = self.arg(1) != 'reverse'
		self.fm.visual = value
		self.fm.mark(val=value, movedown=False)

class escape(Command):
	def execute(self):
		self.fm.visual = None

class break_(Command):
	name = 'break'
	def execute(self):
		try:
			item = self.fm.loader.queue[0]
		except:
			self.fm.write("Type Q or :quit<Enter> to exit Ranger")
		else:
			self.fm.write("Aborting: " + item.get_description())
			self.fm.loader.remove(index=0)

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

class console_tab(Command):
	def execute(self):
		self.fm.ui.console.tab(int(self.arg(1) or 1))

class display_help(Command):
	def execute(self):
		from ranger.help import get_help_by_index
		self.fm.display_in_pager(get_help_by_index(self.n or 0))

class display_log(Command):
	def execute(self):
		self.fm.display_in_pager("\n".join(reversed(self.fm.log)))

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

class echo(Command):
	def execute(self):
		self.fm.write(self.rest(1))

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


class chmod(Command):
	"""
	:chmod <octal number>

	Sets the permissions of the selection to the octal number.

	The octal number is between 0 and 777. The digits specify the
	permissions for the user, the group and others.

	A 1 permits execution, a 2 permits writing, a 4 permits reading.
	Add those numbers to combine them. So a 7 permits everything.
	"""

	def execute(self):
		mode = self.rest(1)

		try:
			mode = int(mode, 8)
			if mode < 0 or mode > 0o777:
				raise ValueError
		except ValueError:
			self.fm.notify("Need an octal number between 0 and 777!", bad=True)
			return

		for file in self.fm.env.get_selection():
			try:
				os.chmod(file.path, mode)
			except Exception as ex:
				self.fm.notify(ex)

		try:
			# reloading directory.  maybe its better to reload the selected
			# files only.
			self.fm.env.cwd.load_content()
		except:
			pass


class filter(Command):
	"""
	:filter <string>

	Displays only the files which contain <string> in their basename.
	"""

	def execute(self):
		self.fm.set_filter(self.rest(1))
		self.fm.reload_cwd()

class reload(Command):
	def execute(self):
		self.fm.reload_cwd()

class reset(Command):
	def execute(self):
		self.fm.reset()

class redraw(Command):
	def execute(self):
		self.fm.redraw_window()

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
