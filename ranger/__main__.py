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

# Most import statements in this module are inside the functions.
# This enables more convenient exception handling in ranger.py
# (ImportError will imply that this module can't be found)
# convenient exception handling in ranger.py (ImportError)

import locale
import os.path
import sys


def load_settings(fm, clean):
	import ranger.shared
	import ranger.api.commands
	import ranger.api.keys
	if not clean:
		allow_access_to_confdir(ranger.arg.confdir, True)

		# Load commands
		comcont = ranger.api.commands.CommandContainer()
		ranger.api.commands.alias = comcont.alias
		try:
			import commands
			comcont.load_commands_from_module(commands)
		except ImportError:
			pass
		from ranger.defaults import commands
		comcont.load_commands_from_module(commands)
		commands = comcont

		# Load apps
		try:
			import apps
		except ImportError:
			from ranger.defaults import apps

		# Load keys
		keymanager = ranger.shared.EnvironmentAware.env.keymanager
		ranger.api.keys.keymanager = keymanager
		from ranger.defaults import keys
		try:
			import keys
		except ImportError:
			pass
		# COMPAT WARNING
		if hasattr(keys, 'initialize_commands'):
			print("Warning: the syntax for ~/.config/ranger/keys.py has changed.")
			print("Your custom keys are not loaded."\
					"  Please update your configuration.")
		allow_access_to_confdir(ranger.arg.confdir, False)
	else:
		comcont = ranger.api.commands.CommandContainer()
		ranger.api.commands.alias = comcont.alias
		from ranger.api import keys
		keymanager = ranger.shared.EnvironmentAware.env.keymanager
		ranger.api.keys.keymanager = keymanager
		from ranger.defaults import commands, keys, apps
		comcont.load_commands_from_module(commands)
		commands = comcont
	fm.commands = commands
	fm.keys = keys
	fm.apps = apps.CustomApplications()


def load_apps(fm, clean):
	import ranger
	if not clean:
		allow_access_to_confdir(ranger.arg.confdir, True)
		try:
			import apps
		except ImportError:
			from ranger.defaults import apps
		allow_access_to_confdir(ranger.arg.confdir, False)
	else:
		from ranger.defaults import apps
	fm.apps = apps.CustomApplications()


def main():
	"""initialize objects and run the filemanager"""
	try:
		import curses
	except ImportError as errormessage:
		print(errormessage)
		print('ranger requires the python curses module. Aborting.')
		sys.exit(1)

	try: locale.setlocale(locale.LC_ALL, '')
	except: print("Warning: Unable to set locale.  Expect encoding problems.")

	if not 'SHELL' in os.environ:
		os.environ['SHELL'] = 'bash'

	# Need to decide whether to write bytecode or not before importing.
	import ranger
	from ranger.ext import curses_interrupt_handler
	from ranger.core.runner import Runner
	from ranger.core.fm import FM
	from ranger.core.environment import Environment
	from ranger.gui.defaultui import DefaultUI as UI
	from ranger.fsobject import File

#	if not arg.debug:
#		curses_interrupt_handler.install_interrupt_handler()

	SettingsAware._setup()

	targets = arg.targets or ['.']
	target = targets[0]
	if arg.targets:
		if target.startswith('file://'):
			target = target[7:]
		if not os.access(target, os.F_OK):
			print("File or directory doesn't exist: %s" % target)
			sys.exit(1)

	crash_traceback = None
	try:
		# Initialize objects
		EnvironmentAware._assign(Environment(target))
		if arg.clean:
			sys.dont_write_bytecode = True
		fm = FM()
		fm.tabs = dict((n+1, os.path.abspath(path)) for n, path \
				in enumerate(targets[:9]))
		FileManagerAware._assign(fm)
		fm.ui = UI()
		fm.run = Runner(ui=fm.ui, logfunc=fm.notify)
		fm.add_commands_from_file(ranger.relpath('core/base_commands.py'))
		fm.run_commands_from_file(ranger.relpath('defaults/config'))

		# Run the file manager
		fm.initialize()
		if fm.env.username == 'root':
			fm.settings.preview_files = False
		fm.ui.initialize()
		fm.loop()
	except Exception:
		import traceback
		crash_traceback = traceback.format_exc()
	except SystemExit as error:
		return error.args[0]
	finally:
		try:
			fm.ui.destroy()
		except (AttributeError, NameError):
			pass
		if crash_traceback:
			print(crash_traceback)
			print("Ranger crashed.  " \
					"Please report this (including the traceback) at:")
			print("http://savannah.nongnu.org/bugs/?group=ranger&func=additem")
			return 1
		return 0
