# A proof-of-concept plugin which implements control flow commands
# that support nesting: if, else, endif, while, endwhile.
# if and while take python expressions as arguments and use their
# boolean value to determine the flow.
#
# Example:
# let foo = 5
# while %foo
#     echo %foo
#     let foo -= 1
# endwhile
# echo finished!
#
# put this file at ~/.config/ranger/plugins/flow.py
# and add the command "load flow" in your ~/.config/ranger/config

from ranger import fm
from ranger.api.commands import *
import collections

register = fm.commands.register
command_flow_stack = collections.deque()

@register
class if_(Command):
	name = 'if'
	def execute(self):
		result = self.fm.eval(self.rest(1))
		command_flow_stack.append(
			['if', bool(result), 'endif', 'else'])

@register
class else_(Command):
	name = 'else'

@register
class endif(Command):
	pass

@register
class while_(Command):
	resolve_macros = False
	name = 'while'
	def execute(self):
		global command_flow_stack
		command_flow_stack.append(['while', self.rest(1), 'endwhile', 0])

@register
class endwhile(Command):
	pass

ENABLE = CODE = 1
END = 2
ELSE = 3
COMMANDS = 4

def cmdhook(signal):
	global command_flow_stack, fm
	if command_flow_stack:
		top = command_flow_stack[-1]
		if top[0] == 'if':
			if signal.command_name == top[END]:
				command_flow_stack.pop()
			elif signal.command_name == top[ELSE]:
				top[ENABLE] = not top[ENABLE]
			elif not top[ENABLE]:
				signal.stop()
		elif top[0] == 'while':
			if signal.command_name == top[END]:
				command_flow_stack.pop()
				while fm.eval(fm.substitute_macros(top[CODE])):
					for line in top[COMMANDS:]:
						fm.cmd(line)
			elif top[3] == 0:
				top.append(signal.line)
				signal.stop()

fm.signal_bind('command.pre', cmdhook)
