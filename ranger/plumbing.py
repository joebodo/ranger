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
This package provides functions that do the dirty work.

Functions here are too general to be methods of the FileManager class and
too ranger-specific to be part of a library. Most of them manage rangers
runtime environment or help starting up.
"""

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
				filepath = fm.env.cf.path
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

def parse_arguments(args=None):
	"""Parse the program arguments"""
	import ranger
	import os.path
	from optparse import OptionParser, SUPPRESS_HELP

	# Some setup
	parser = OptionParser(usage='%prog [options] [path/filename]',
		version='ranger %s (%s)' % (ranger.__version__,
				ranger.VERSION[2] % 2 and 'stable' or 'testing'))

	# Define options
	parser.add_option('--copy-config', type='string', metavar='which',
		help="copy the default configs to the local config directory."
			" Possible values: all, apps, commands, keys, options, scope")
	parser.add_option('-m', '--mode', type='int', default=ranger.RUNMODE,
		metavar='n', help="if a filename is supplied, run it with this mode")
	parser.add_option('-f', '--flags', type='string', default=ranger.RUNFLAGS,
		metavar='string',
		help="if a filename is supplied, run it with these flags.")

	# Parsing and post processing
	options, positional   = parser.parse_args(args=args)
	ranger.CONFDIR        = os.path.expanduser(options.confdir)
	ranger.DEBUG          = options.debug
	ranger.CLEAN          = options.clean
	ranger.CHOOSEFILE     = options.choosefile
	ranger.CHOOSEDIR      = options.choosedir
	ranger.RUNMODE        = options.mode
	ranger.RUNFLAGS       = options.flags
	ranger.COPY_CONFIG    = options.copy_config
	ranger.FAIL_UNLESS_CD = options.fail_unless_cd
	ranger.RUNTARGETS     = positional
	if not ranger.RUNTARGETS:
		ranger.RUNTARGETS = ['.']

def copy_config_files(which=None):
	if CLEAN:
		ERR("refusing to copy config files in clean mode\n")
		return
	import stat
	import shutil
	def copy(_from, to):
		if os.path.exists(confpath(to)):
			ERR("already exists: %s" % confpath(to))
		else:
			ERR("creating: %s" % confpath(to))
			try:
				shutil.copy(relpath(_from), confpath(to))
			except Exception as e:
				ERR("  ERROR: %s" % str(e))
	if which == 'apps' or which == 'all':
		copy('defaults/apps.py', 'apps.py')
	if which == 'commands' or which == 'all':
		copy('defaults/commands.py', 'commands.py')
	if which == 'keys' or which == 'all':
		copy('defaults/keys.py', 'keys.py')
	if which == 'options' or which == 'all':
		copy('defaults/options.py', 'options.py')
	if which == 'scope' or which == 'all':
		copy('data/scope.sh', 'scope.sh')
		os.chmod(confpath('scope.sh'),
			os.stat(confpath('scope.sh')).st_mode | stat.S_IXUSR)
	if which not in \
			('all', 'apps', 'scope', 'commands', 'keys', 'options'):
		ERR("unknown config file `%s'" % which)

def create_directories():
	if not CLEAN:
		for directory in (CONFDIR, CACHEDIR):
			try:
				os.makedirs(directory)
			except OSError as err:
				if err.errno != 17:  # 17 means it already exists
					ERR("This directory could not be created:")
					ERR(directory)
					raise SystemExit()
