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
DEBUG = False
CLEAN = False
CONFDIR = DEFAULT_CONFDIR

# Get some valid arguments before actually parsing them in main()
arg = OpenStruct(debug=DEBUG, clean=CLEAN, confdir=CONFDIR,
		mode=0, flags='', targets=[])

# Debugging features.  These will be activated when run with --debug.
# Example usage in the code:
# import ranger; ranger.log("hello world")
def log(*objects, **keywords):
	"""
	Writes objects to a logfile (for the purpose of debugging only.)
	Has the same arguments as print() in python3.
	"""
	if LOGFILE is None or not DEBUG or CLEAN: return
	start = 'start' in keywords and keywords['start'] or 'ranger:'
	sep   =   'sep' in keywords and keywords['sep']   or ' '
	_file =  'file' in keywords and keywords['file']  or open(LOGFILE, 'a')
	end   =   'end' in keywords and keywords['end']   or '\n'
	_file.write(sep.join(map(str, (start, ) + objects)) + end)

def log_traceback():
	if LOGFILE is None or not DEBUG or CLEAN: return
	import traceback
	traceback.print_stack(file=open(LOGFILE, 'a'))

# Handy functions
def relpath_conf(*paths):
	"""returns the path relative to rangers configuration directory"""
	if arg.clean:
		assert 0, "Should not access relpath_conf in clean mode!"
	else:
		return _join(arg.confdir, *paths)

confpath = relpath_conf

def relpath(*paths):
	"""returns the path relative to rangers library directory"""
	return _join(RANGERDIR, *paths)

# A basic argument parser which can be run before 
# We need certain command line arguments before we start anything else.
# These arguments are --debug, --clean and --confdir.  They will also
# be globally available (from ranger import DEBUG, ...)
def parse_basic_arguments(argv):
	if argv is None:
		from sys import argv
	if not argv:
		return
	global DEBUG, CLEAN, CONFDIR
	try:
		argv = argv[0:argv.index("--")]
	except:
		pass
	DEBUG = '-d' in argv or '--debug' in argv
	CLEAN = '-c' in argv or '--clean' in argv
	try:
		dash_r = argv.index('-r')
	except ValueError:
		for arg in argv:
			if arg[:10] == '--confdir=' and len(arg) > 10:
				CONFDIR = arg[10:]
	else:
		if len(argv) >= dash_r:
			CONFDIR = argv[dash_r + 1]

# The main function which is called from inside the main executable.
# It creates a FM object, starts it and catches errors.
def main(argv=None):
	"""initialize environment and run the filemanager"""
	parse_basic_arguments(argv)
	from ranger.core import FM
	fm = FM()
	crash_traceback = None
	try:
		fm.setup_environment()
		fm.initialize()
		fm.loop()
	except Exception:
		import traceback
		crash_traceback = traceback.format_exc()
	except SystemExit as error:
		return error.args[0]
	finally:
		fm.clean_up()
		if crash_traceback:
			print(crash_traceback)
			print("Ranger crashed.  " \
					"Please report this (including the traceback) at:")
			print("http://savannah.nongnu.org/bugs/?group=ranger&func=additem")
			return 1
		return 0

# Clean up
del environ, OpenStruct
