def register(cls):
	name = cls.name if cls.name is not None else cls.__name__
	fm._commands[name] = cls

from ranger.api.commands import Command
def register_function(fnc):
	import types
	name = fnc.__name__
	cls = type(name, (Command, ), {})
	cls.execute = fnc
	fm._commands[name] = cls
	return cls

@register_function
def quit(self):
	raise SystemExit()

@register_function
def reset(self):
	old_path = fm.env.cwd.path
	fm.env.garbage_collect(-1)
	cmd("cd " + old_path)

@register_function
def reload_cwd(self):
	try:
		cwd = fm.env.cwd
	except:
		pass
	else:
		cwd.unload()
		cwd.load_content()

@register_function
def echo(self):
	fm.notify(self.rest(1))

@register_function
def redraw_window(self):
	fm.ui.redraw_window()

@register_function
def console(self):
	position = None
	if self.arg(1)[0:2] == '-p':
		self.shift()
		if len(self.arg(0)) > 2:
			position = int(self.arg(0)[2:])
		else:
			self.shift()
			position = int(self.arg(0))
	elif self.arg(1) == '-x':
		return fm.cmd(self.rest(2))
	fm.ui.open_console(self.rest(1), position=position)

@register_function
def command(self):
	cmd(self.rest(1))

@register_function
def source(self):
	fm.run_commands_from_file(self.rest(1))

@register_function
def set(self):
	if not len(self.args) >= 3:
		return
	from ranger.shared.settings import ALLOWED_SETTINGS
	key = self.arg(1)
	value = self.rest(2)
	try:
		typ = ALLOWED_SETTINGS[key]
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
			value = list(int(i) for i in value.split())
		elif typ == tuple:
			value = tuple(int(i) for i in value.split())
		elif typ == type(re.compile("")):
			value = re.compile(value, re.I)
		fm.settings[key] = value

@register_function
def cd(self):
	fm.enter_dir(self.arg(1))

@register_function
def map(self):
	fm.env.keymanager.get_context('browser')(self.arg(1),
			lambda arg: fm.cmd(self.rest(2), n=arg.n))

@register_function
def cmap(self):
	fm.env.keymanager.get_context('console')(self.arg(1),
			lambda arg: fm.cmd(self.rest(2), n=arg.n))

@register_function
def move(self):
	direction = self.arg(1)
	n = self.n
	if direction == 'down':
		fm.move(down=1 if n is None else n)
	elif direction == 'up':
		fm.move(up=1 if n is None else n)
	elif direction == 'left':
		fm.cmd("cd ..")
	elif direction == 'home':
		fm.move(down=0 if n is None else n, absolute=True)
	elif direction == 'end':
		fm.move(down=-1 if n is None else n, absolute=True)

@register_function
def execute(self):
	selection = fm.env.get_selection()
	cf = fm.env.cf
	if cf.is_directory:
		fm.cmd("cd " + cf.path)
	else:
		fm.cmd("console open_with ")

@register_function
def tag(self):
	argument = self.arg(1)
	if argument == 'toggle':
		fm.tag_toggle()
	pass

@register_function
def console_execute(self):
	fm.ui.console.execute()

@register_function
def console_close(self):
	fm.ui.console.close()

@register_function
def console_delete(self):
	if self.arg(1) == 'here':
		fm.ui.console.delete(-1)
	else:
		fm.ui.console.delete(1)

@register_function
def help(self):
	from ranger.help import get_help, get_help_by_index

	scroll_to_line = 0
	if self.n is not None:
		chapter, subchapter = int(str(self.n)[0]), str(self.n)[1:]
		help_text = get_help_by_index(chapter)
		lines = help_text.split('\n')
		if chapter:
			chapternumber = str(chapter) + '.' + subchapter + '. '
			skip_to_content = True
			for line_number, line in enumerate(lines):
				if skip_to_content:
					if line[:10] == '==========':
						skip_to_content = False
				else:
					if line.startswith(chapternumber):
						scroll_to_line = line_number
	else:
		help_text = get_help('index')
		lines = help_text.split('\n')

	pager = fm.ui.open_pager()
	pager.markup = 'help'
	pager.set_source(lines)
	pager.move(down=scroll_to_line)

@register
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
			fm.execute_command(command, flags=flags)

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

@register_function
def eval_macros(self):
	command = self.rest(1)
	if '%' in self.line:
		command = fm.substitute_macros(command)
	return fm.cmd(command)

@register_function
def defmacro(self):
	fm._custom_macros[self.arg(1)] = self.rest(2)

@register_function
def undefmacro(self):
	try:
		del fm._custom_macros[self.arg(1)]
	except:
		fm.notify("No such macro: " + self.arg(1))
