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
Console-based visual file manager.

Ranger is a file manager with an ncurses frontend written in Python.
It is designed to give you a broader overview of the file system by
displaying previews and backviews, dividing the screen into columns.

The keybindings are similar to those of other console programs like
vim, mutt or ncmpcpp so the usage will be intuitive and efficient.
"""

import os.path, sys
from os.path import join as _join

# -=- General Information -=-
VERSION = (1, 5, 0, "")
__license__ = 'GPL3'
__version__ = '%d.%d.%d%s' % VERSION
__maintainer__ = 'Roman Zimbelmann'
__author__ = __maintainer__ = 'Roman Zimbelmann'
__email__ = 'romanz@lavabit.com'

# -=- Runtime Information -=-
PID = os.getpid()
INSTANCE = None

# -=- Files and Directories -=-
RANGERDIR = os.path.dirname(__file__)
LOGFILE = '/tmp/ranger_debug_log'

if 'XDG_CONFIG_HOME' in os.environ and os.environ['XDG_CONFIG_HOME']:
	DEFAULT_CONFDIR = os.environ['XDG_CONFIG_HOME'] + '/ranger'
else:
	DEFAULT_CONFDIR = os.path.expanduser('~/.config/ranger')
if 'XDG_CACHE_HOME' in os.environ and os.environ['XDG_CACHE_HOME']:
	DEFAULT_CACHEDIR = os.environ['XDG_CACHE_HOME'] + '/ranger'
else:
	DEFAULT_CACHEDIR = os.path.expanduser('~/.cache/ranger')

# -=- Main Function -=-
def main():
	"""initializes objects, runs the filemanager and returns the exit code"""
	import locale
	import sys
	import os.path
	import ranger.fm

	fm = ranger.get_fm()
	crash_traceback = None
	try:
		fm.initialize()
		fm.loop()
	except Exception:
		import traceback
		crash_traceback = traceback.format_exc()
	except SystemExit as error:
		if error.args:
			return error.args[0]
		return 1
	finally:
		if crash_traceback:
			try:
				filepath = fm.tab.cf.path
			except:
				filepath = "None"
		fm.destroy()
		if crash_traceback:
			print("Ranger version: %s, executed with python %s" %
					(ranger.__version__, sys.version.split()[0]))
			print("Locale: %s" % '.'.join(str(s) for s in locale.getlocale()))
			print("Current file: %s" % filepath)
			print(crash_traceback)
			print("Ranger crashed.  " \
				"Please report this traceback at:")
			print("http://savannah.nongnu.org/bugs/?group=ranger&func=additem")
			return 1
		return 0

# -=- Basic Functions -=-
def LOG(*objects):
	"""Write objects to LOGFILE for the purpose of debugging"""
	if not get_fm().arg.clean:
		f = open(LOGFILE, 'a')
		f.write(' '.join(str(obj) for obj in objects) + '\n')
		f.close()

def LOG_TRACEBACK():
	"""Write a traceback to LOGFILE for the purpose of debugging"""
	if not get_fm().arg.clean:
		import traceback
		f = open(LOGFILE, 'a')
		traceback.print_stack(file=f)
		f.close()

def DISPLAY(*objects):
	"""Display text on the screen.  Adapts to the situation."""
	if INSTANCE:
		INSTANCE.display(*objects)
		if INSTANCE.arg.debug:
			LOG('\n'.join(str(o) for o in objects) + '\n')
	else:
		print('\n'.join(str(o) for o in objects))

def ERR(*objects):
	"""Display text as an error on the screen.  Adapts to the situation."""
	if INSTANCE:
		INSTANCE.err(*objects)
		if INSTANCE.arg.debug:
			LOG('\n'.join(str(o) for o in objects) + '\n')
	else:
		sys.stderr.write('\n'.join(str(o) for o in objects) + '\n')


def get_fm():
	"""returns the global ranger.fm.FM (FileManager) instance"""
	global INSTANCE
	if not INSTANCE:
		import ranger.fm
		INSTANCE = ranger.fm.FM()
	return INSTANCE

del os, sys
