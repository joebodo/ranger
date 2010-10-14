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
An object that contains information about the environment
and methods for manipulating it.
"""

from __future__ import print_function
from ranger.ext.openstruct import OpenStruct
import locale
import ranger
import re
import os.path
import sys

_VERSION_RE = re.compile("(\d+)\.(\d+)\.(\d+)(.*)$")

class Unknown:
	"""
	Used to identify situations where information is unknown

	Can be instantiated with a boolean value and can be used as one. 
	"""
	def __init__(self, boolvalue=True):
		self.boolvalue = bool(boolvalue)

	def __bool__(self):
		return self.boolvalue

	def __repr__(self):
		return "Unknown (assumed %s)" % str(self.boolvalue)

	__nonzero__ = __bool__

class Info(object):
	logfile = '/tmp/errorlog'
	name = 'ranger'
	rangerdir = os.path.dirname(os.path.dirname(__file__))
	Unknown = Unknown

	def __init__(self):
		# Directories
		if 'XDG_CONFIG_HOME' in os.environ and os.environ['XDG_CONFIG_HOME']:
			self.confdir = os.environ['XDG_CONFIG_HOME'] + '/ranger'
		else:
			self.confdir = os.path.expanduser('~/.config/ranger')
		if 'XDG_CACHE_HOME' in os.environ and os.environ['XDG_CACHE_HOME']:
			self.cachedir = os.environ['XDG_CACHE_HOME'] + '/ranger'
		else:
			self.cachedir = os.path.expanduser('~/.cache/ranger')

		# Status
		self.debug = Unknown(False)
		self.clean = Unknown(False)
		self.pid = os.getpid()
		self.python_version = sys.version_info
		self.py3 = self.python_version >= (3, )
		self.ui = None
		self.commands = None

		# Default/Dummy arguments
		self.args_loaded = False
		self.arg = OpenStruct(debug=self.debug, clean=self.clean,
				confdir=self.confdir, mode=0, flags="", fail_unless_cd=False,
				copy_config=False)

		# Version
		self.version = ranger.__version__
		match = _VERSION_RE.match(self.version)
		if match:
			self.vmajor        = int(match.group(1))
			self.vminor        = int(match.group(2))
			self.vrevision     = int(match.group(3))
			self.vsuffix       = match.group(4)
			self.version_tuple = \
					(self.vmajor, self.vminor, self.vrevision, self.vsuffix)
		else:
			self.vmajor, self.vminor, self.vrevision, self.vsuffix = \
					self.version_tuple = (0, 0, 0, "")

	def setup_environment(self):
		"""
		Create a ranger-friendly environment.

		It should be enough to call this function once, even if you
		run multiple ranger instances.
		"""
		try:
			locale.setlocale(locale.LC_ALL, '')
		except:
			pass
		if not 'SHELL' in os.environ:
			os.environ['SHELL'] = 'bash'

	@property
	def encoding(self):
		return locale.getlocale()[1]

	@property
	def ui_runs(self):
		return self.ui and self.ui.runs

	def relpath(self, *paths):
		"""returns the path relative to rangers library directory"""
		return os.path.join(self.rangerdir, *paths)

	def confpath(self, *paths):
		"""returns the path relative to rangers configuration directory"""
		if self.clean:
			assert 0, "Should not access confpath in clean mode!"
		else:
			return os.path.join(self.confdir, *paths)

	def cachepath(self, *paths):
		"""returns the path relative to rangers configuration directory"""
		if self.clean:
			assert 0, "Should not access cachepath in clean mode!"
		else:
			return os.path.join(self.cachedir, *paths)

	def copy_config_files(self, which):
		if self.clean:
			self.err("refusing to copy config files in clean mode\n")
			return
		import stat
		import shutil
		def copy(_from, to):
			if os.path.exists(self.confpath(to)):
				self.err("already exists: %s" % self.confpath(to))
			else:
				self.err("creating: %s" % self.confpath(to))
				try:
					shutil.copy(self.relpath(_from), self.confpath(to))
				except Exception as e:
					self.err("  ERROR: %s" % str(e))
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
			os.chmod(self.confpath('scope.sh'),
				os.stat(self.confpath('scope.sh')).st_mode | stat.S_IXUSR)
		if which not in \
				('all', 'apps', 'scope', 'commands', 'keys', 'options'):
			self.err("unknown config file `%s'" % which)

	def log(self, *args, **keywords):
		if not self.clean:
			if 'file' not in keywords:
				keywords['file'] = open(self.logfile, 'a')
			print(*args, **keywords)

	def log_traceback(self):
		if not self.clean:
			import traceback
			traceback.print_stack(file=open(self.logfile, 'a'))

	def err(self, *args):
		if self.ui_runs:
			self.ui.notify(*args, bad=True)
		else:
			print(*args, file=sys.stderr)

	def write(self, string):
		if self.ui_runs:
			self.ui.notify(string)
		else:
			print(string)

	def create_directories(self):
		if not self.clean:
			for directory in (self.confdir, self.cachedir):
				try:
					os.makedirs(directory)
				except OSError as err:
					if err.errno != 17:  # 17 means it already exists
						self.err("This directory could not be created:")
						self.err(directory)
						raise SystemExit()

	def allow_importing_from(self, directory, allow=True):
		if allow:
			if not directory in sys.path:
				sys.path[0:0] = [directory]
		else:
			while directory in sys.path:
				sys.path.remove(directory)

	def parse_arguments(self):
		"""Parse the program arguments"""
		from optparse import OptionParser, SUPPRESS_HELP

		# Some setup
		usage = '%prog [options] [path/filename]'
		version_tag = ' (stable)' if int(self.vminor) % 2 == 0 \
				else ' (testing)'
		version_string = 'ranger ' + self.version + ' (stable)' \
				if self.vminor % 2 == 0 else ' (testing)'
		parser = OptionParser(usage=usage, version=version_string)

		# Define options
		parser.add_option('-d', '--debug', action='store_true',
				help="activate debug mode")
		parser.add_option('-c', '--clean', action='store_true',
				help="don't touch/require any config files. ")
		parser.add_option('--copy-config', type='string', metavar='which',
				help="copy the default configs to the local config directory."
				" Possible values: all, apps, commands, keys, options, scope")
		parser.add_option('--fail-unless-cd', action='store_true',
				help="return the exit code 1 if ranger is used to run a "
					"file (with `ranger filename`)")
		parser.add_option('-r', '--confdir', type='string',
				metavar='dir', default=self.confdir,
				help="the configuration directory. (%default)")
		parser.add_option('-m', '--mode', type='int', default=0, metavar='n',
				help="if a filename is supplied, run it with this mode")
		parser.add_option('-f', '--flags', type='string', default='',
				metavar='string',
				help="if a filename is supplied, run it with these flags.")

		# Parsing and post processing
		options, positional = parser.parse_args()
		arg = OpenStruct(options.__dict__, targets=positional)
		self.confdir = os.path.expanduser(arg.confdir)
		self.debug = arg.debug
		self.clean = arg.clean
		self.arg = arg
		self.args_loaded = True

		return arg

	def load_commands(self):
		import ranger.defaults.commands
		import ranger.api.commands
		container = ranger.api.commands.CommandContainer()
		container.load_commands_from_module(ranger.defaults.commands)
		if not self.clean:
			self.allow_importing_from(self.confdir, True)
			ranger.api.commands.alias = container.alias
			try:
				import commands
			except ImportError:
				pass
			else:
				container.load_commands_from_module(commands)
			self.allow_importing_from(self.confdir, False)
		self.commands = container
		return container

	def load_config(self):
		try:
			myconfig = open(self.confpath('config'), 'r').read()
		except:
			self.source_cmdlist(self.relpath('defaults/config'))
		else:
			lines = myconfig.split("\n")
			if 'nodefaults' not in lines:
				self.source_cmdlist(self.relpath('defaults/config'))
			for line in lines:
				self.cmd_secure(line.rstrip("\r\n"))

	def source_cmdlist(self, filename):
		for line in open(filename, 'r'):
			self.cmd_secure(line.rstrip("\r\n"))

	def load_plugin(self, filename):
		import ranger

		# Get the filename and its content
		content = None
		if '/' not in filename:
			if filename[-3:] != '.py':
				real_filename = self.confpath('plugins', filename+'.py')
			else:
				real_filename = self.confpath('plugins', filename)
			try:
				content = open(real_filename).read()
			except:
				pass
		if not content:
			real_filename = filename
			try:
				content = open(filename).read()
			except:
				return False

		# Set up the environment
		remove_ranger_fm = hasattr(ranger, 'fm')
		ranger.fm = self

		# Compile and execute the code
		code = compile(content, real_filename, 'exec')
		exec(code)

		# Clean up
		if remove_ranger_fm and hasattr(ranger, 'fm'):
			del ranger.fm

	def cmd_secure(self, line, lineno=None, n=None):
		try:
			self.cmd(line, n=n)
		except Exception as e:
			self.err(e)

	def cmd(self, line, n=None):
		if line == 'nodefaults':
			return
		line = line.lstrip()
		if not line or line[0] == '"' or line[0] == '#':
			return
		command_name = line.split(' ', 1)[0]
		try:
			command_entry = self.commands.get_command(command_name)
		except Exception as e:
			self.err(str(e))
			return
		if command_entry:
			command = command_entry(line, n=n)
			command.execute()
		else:
			raise Exception("No such command: " + command_name)
