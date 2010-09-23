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

"""Ranger - file browser for the unix terminal"""

from os import path, environ
from os.path import join as _join
from ranger.ext.openstruct import OpenStruct
from sys import argv

# Information
__license__ = 'GPL3'
__version__ = '1.3.0'
__author__ = __maintainer__ = 'Roman Zimbelmann'
__email__ = 'romanz@lavabit.com'

# Constants
USAGE = '%prog [options] [path/filename]'
RANGERDIR = path.dirname(__file__)
LOGFILE = '/tmp/errorlog'
if 'XDG_CONFIG_HOME' in environ and environ['XDG_CONFIG_HOME']:
	DEFAULT_CONFDIR = environ['XDG_CONFIG_HOME'] + '/ranger'
else:
	DEFAULT_CONFDIR = '~/.config/ranger'
DEBUG = ('-d' in argv or '--debug' in argv) and ('--' not in argv or
	(('-d' in argv and argv.index('-d') < argv.index('--')) or
	('--debug' in argv and argv.index('--debug') < argv.index('--'))))

# Get some valid arguments before actually parsing them in main()
arg = OpenStruct(debug=DEBUG, clean=False, confdir=DEFAULT_CONFDIR,
		mode=0, flags='', targets=[])

# Debugging features.  These will be activated when run with --debug.
# Example usage in the code:
# import ranger; ranger.log("hello world")
def log(*objects, **keywords):
	"""
	Writes objects to a logfile (for the purpose of debugging only.)
	Has the same arguments as print() in python3.
	"""
	if LOGFILE is None or not arg.debug or arg.clean: return
	start = 'start' in keywords and keywords['start'] or 'ranger:'
	sep   =   'sep' in keywords and keywords['sep']   or ' '
	_file =  'file' in keywords and keywords['file']  or open(LOGFILE, 'a')
	end   =   'end' in keywords and keywords['end']   or '\n'
	_file.write(sep.join(map(str, (start, ) + objects)) + end)

def log_traceback():
	if LOGFILE is None or not arg.debug or arg.clean: return
	import traceback
	traceback.print_stack(file=open(LOGFILE, 'a'))

# Handy functions
def relpath_conf(*paths):
	"""returns the path relative to rangers configuration directory"""
	if arg.clean:
		assert 0, "Should not access relpath_conf in clean mode!"
	else:
		return _join(arg.confdir, *paths)

def relpath(*paths):
	"""returns the path relative to rangers library directory"""
	return _join(RANGERDIR, *paths)

# The main function
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

	arg = parse_arguments()
	if arg.clean:
		sys.dont_write_bytecode = True

	# Need to decide whether to write bytecode or not before importing.
	import ranger
	from ranger.ext import curses_interrupt_handler
	from ranger.core.runner import Runner
	from ranger.core.fm import FM
	from ranger.core.environment import Environment
	from ranger.gui.defaultui import DefaultUI as UI
	from ranger.fsobject import File
	from ranger.shared import (EnvironmentAware, FileManagerAware,
			SettingsAware)

#	if not arg.debug:
#		curses_interrupt_handler.install_interrupt_handler()
	ranger.arg = arg

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

# Clean up
del environ, OpenStruct, argv
