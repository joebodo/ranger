def register(cls):
	fm._commands[name] = cls

def register_function(fnc):
	import types
	from ranger.api.commands import Command
	name = fnc.__name__
	cls = type(name, (Command, ), {})
	cls.execute = fnc
#	cls.execute = types.UnboundMethodType(fnc, cls)
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
	position = 0
	if self.arg(1)[0:2] == '-p':
		self.shift()
		if len(self.arg(0)) > 2:
			position = int(self.arg(0)[2:])
		else:
			self.shift()
			position = int(self.arg(0))
	fm.ui.open_console(self.rest(1))

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
		fm.settings[key] = value

@register_function
def cd(self):
	fm.enter_dir(self.arg(1))

@register_function
def map(self):
	fm.env.keymanager.get_context('browser')(self.arg(1),
			lambda arg: fm.cmd(self.rest(2)))

@register_function
def cmap(self):
	pass

@register_function
def move(self):
	direction = self.arg(1)
	if direction == 'down':
		fm.move(down=1)
	elif direction == 'up':
		fm.move(up=1)
	elif direction == 'left':
		fm.cmd("cd ..")
	elif direction == 'home':
		fm.move(down=0, absolute=True)
	elif direction == 'end':
		fm.move(down=-1, absolute=True)

@register_function
def execute(self):
	selection = fm.env.get_selection()
	cf = fm.env.cf
	if cf.is_directory:
		fm.cmd("cd " + cf.path)
	else:
		fm.cmd("console open_with ")
