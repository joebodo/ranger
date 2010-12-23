"""
Global variables and functions to be imported in any major module
by adding the line:

from ranger.base import *
"""

import os as _os
import sys as _sys

__all__ = ['__version__', '__author__', 'fm', 'debug', 'clean', 'log',
		'write', 'error', 'confpath', 'cachepath']

version_major    = 1
version_minor    = 5
version_revision = 0
version_suffix   = ''
version_info = (version_major, version_minor, version_revision, version_suffix)

__email__ = 'romanz@lavabit.com'
__author__ = __maintainer__ = 'Roman Zimbelmann'
__license__ = 'GPL3'
__version__ = '%d.%d.%d%s' % version_info

fm        = None
debug     = False
clean     = False
logfile   = '/tmp/ranger_debug_log'
RANGERDIR = _os.path.dirname(_os.path.dirname(__file__))
RANGERPID = _os.getpid()
PY3       = _sys.version_info >= (3, )

if 'XDG_CONFIG_HOME' in _os.environ and _os.environ['XDG_CONFIG_HOME']:
	CONFDIR = _os.environ['XDG_CONFIG_HOME'] + '/ranger'
else:
	CONFDIR = _os.path.expanduser('~/.config/ranger')
if 'XDG_CACHE_HOME' in _os.environ and _os.environ['XDG_CACHE_HOME']:
	CACHEDIR = _os.environ['XDG_CACHE_HOME'] + '/ranger'
else:
	CACHEDIR = _os.path.expanduser('~/.cache/ranger')

def log(*objects):
	"""Writes data to the logfile for debugging purposes"""
	global logfile
	open(logfile, 'a').write(" ".join(str(object)
		for object in objects) + "\n")

def log_traceback():
	global logfile
	import traceback
	traceback.print_stack(file=open(logfile, 'a'))

def write(*objects):
	"""Writes data to the currently active output stream"""
	if fm is None:
		_sys.stdout.write(" ".join(str(object) for object in objects) + "\n")
	else:
		fm.notify(*objects)

def error(*objects):
	"""Writes data to the currently active error stream"""
	if fm is None:
		_sys.stdout.write(" ".join(str(object) for object in objects) + "\n")
	else:
		fm.notify(*objects, bad=True)

def confpath(self, *paths):
	"""returns the path relative to rangers configuration directory"""
	global clean, CONFDIR
	if clean:
		assert 0, "Should not access confpath in clean mode!"
	return _os.path.join(CONFDIR, *paths)

def cachepath(self, *paths):
	"""returns the path relative to rangers configuration directory"""
	global clean, CACHEDIR
	if clean:
		assert 0, "Should not access cachepath in clean mode!"
	return _os.path.join(CACHEDIR, *paths)

del _os, _sys
