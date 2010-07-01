#!/usr/bin/python
# Copyright (C) 2010  Roman Zimbelmann <romanz@lavabit.com>
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

"""Rifle - Ranger's File Launcher"""

import optparse
import os.path
import sys
import string
import subprocess

__version__    = '0.1'
__author__     = 'Roman Zimbelmann'
USAGE          = '%prog [options] [filename1 [filename 2...]]'
DEFAULT_CONFIG = '~/.riflerc'

# Mini-library {{{
class OpenStruct(dict):
	"""The fusion of dict and struct"""
	def __init__(self, *__args, **__keywords):
		dict.__init__(self, *__args, **__keywords)
		self.__dict__ = self

def waitpid_no_intr(pid):
	"""catch interrupts which occur while using os.waitpid"""
	while True:
		try:
			return os.waitpid(pid, 0)
		except (KeyboardInterrupt, OSError):
			continue

def spawn(*args):
	"""Runs a program, waits for its termination and returns its stdout"""
	if len(args) == 1:
		popen_arguments = args[0]
	else:
		popen_arguments = args
	process = subprocess.Popen(popen_arguments, stdout=subprocess.PIPE)
	stdout, stderr = process.communicate()
	return stdout.decode('utf-8')

def shell_quote(string):
	"""Escapes by quoting"""
	return "'" + str(string).replace("'", "'\\''") + "'"

class CustomTemplate(string.Template):
	delimiter = '%'
	idpattern = '[a-z]'

def is_installed(program):
	for path in os.environ['PATH'].split(":"):
		if os.path.exists(os.path.join(path, program)):
			return True
	return False

def shell_escape(string):
	return "'" + str(string).replace("'", "'\\''") + "'"
#}}}

# Helper functions for .riflerc #{{{
def extension(filename):
	return os.path.splitext(filename)[1][1:]

def mimetype(filename):
	return spawn('file', '-Lb', '--mime-type', filename)

def is_image(filename):
	return mimetype(filename).startswith('image')

def is_video(filename):
	return mimetype(filename).startswith('video')

def is_audio(filename):
	return mimetype(filename).startswith('audio')

CONTAINER_EXTENSIONS = ('7z', 'ace', 'ar', 'arc', 'bz', 'bz2', 'cab', 'cpio',
	'cpt', 'dgc', 'dmg', 'gz', 'iso', 'jar', 'msi', 'pkg', 'rar', 'shar',
	'tar', 'tbz', 'tgz', 'xar', 'xz', 'zip')

def is_container(filename):
	return extension(filename) in CONTAINER_EXTENSIONS
#}}}

class Runner(object): #{{{
	def __init__(self, apps):
		self.apps = apps

	def _find_app(self, app, context):
		if not app:
			app = 'default'
		if app in self.apps:
			return self.apps[app](context)
		else:
			return (app, ) + tuple(context.files)

	def _squash_flags(self, context):
		for flag in context.flags:
			if ord(flag) <= 90:
				bad = flag + flag.lower()
				context.flags = ''.join(c for c in context.flags \
						if c not in bad)

	def __call__(self, action=None, try_app_first=False, app='default',
			files=None, mode=0, flags='', **popen_kws):
		# Find an action if none was supplied by
		# creating a Context object and passing it to
		# an Application object.
		context = OpenStruct(app=app, files=files, mode=mode,
				flags=flags, popen_kws=popen_kws,
				file=files and files[0] or None)
		if files:
			context.allfiles = ' '.join(shell_quote(fl) for fl in files)
		else:
			context.allfiles = ''

		if self.apps:
			if try_app_first and action is not None:
				test = self._find_app(app, context)
				if test:
					action = test
			if action is None:
				action = self._find_app(app, context)
				if action is None:
					sys.stderr.write("No action found!\n")
					return False

		if action is None:
			sys.stderr.write("No way of determining the action!\n")
			return False

		# Preconditions
		self._squash_flags(context)
		popen_kws = context.popen_kws  # shortcut

		pipe_output    = False
		wait_for_enter = False
		wait_for_exit  = True

		popen_kws['args'] = action
		if 'shell' not in popen_kws:
			popen_kws['shell'] = isinstance(action, str)

		# Evaluate the flags to determine keywords
		# for Popen() and other variables
		if 'p' in context.flags:
			popen_kws['stdout'] = subprocess.PIPE
			popen_kws['stderr'] = subprocess.PIPE
			pipe_output = True
			wait_for_exit = False
		if 'q' in context.flags or 'd' in context.flags:
			for key in ('stdout', 'stderr', 'stdin'):
				popen_kws[key] = open(os.devnull, 'a')
		if 'd' in context.flags:
			wait_for_exit = False
		if 'w' in context.flags:
			wait_for_enter = True

		# Finally, run it
		try:
			process = None
			try:
				process = subprocess.Popen(**popen_kws)
			except:
				sys.stderr.write("Failed to run: " + str(action) + "\n")
			else:
				if wait_for_exit:
					waitpid_no_intr(process.pid)
		finally:
			if process:
				if pipe_output:
					return self(app='pager', stdin=process.stdout,
							flags=context.flags+'PQ')
				elif wait_for_enter:
					print("Press ENTER to continue...")
					try: raw_input()
					except:  input()
			return process #}}}

class Rifle(object): #{{{
	def __init__(self, argv):
		self.apps = {}
		self.runner = Runner(self.apps)
		self.parse_arguments(argv)

		# Setup defaults
		self.app('default', cmd='cat %s', flags='p')
		self.app('pager', cmd='less')

		try:
			self.load_conf(os.path.expanduser(self.args.config))
		except IOError:
			self.load_conf()

	def load_conf(self, rcname=None):
		if rcname is None:
			rcname = os.path.join(os.path.dirname(os.path.realpath(__file__)), "riflerc.py")
		rcstream = open(rcname, 'r')  # expected IOError if file doesnt exist

		# setup artificial environment:
		global app, appdef, get_app, find_app
		app = self.app
		appdef = self.appdef
		get_app = self.get_app
		find_app = self.find_app

		exec(rcstream.read())
		return True

	def parse_arguments(self, argv):
		parser = optparse.OptionParser(usage=USAGE,
				version='rifle ' + __version__)
		parser.add_option('-r', '--config', type='string',
				metavar='path', default=DEFAULT_CONFIG,
				help="the configuration path. (%default)")
		parser.add_option('-w', '--with', type='string', default='default',
				help="what program to run the file(s) with?", metavar='app')
		parser.add_option('-m', '--mode', type='int', default=0, metavar='n',
				help="if a filename is supplied, run it with this mode")
		parser.add_option('-f', '--flags', type='string', default='',
				metavar='string',
				help="if a filename is supplied, run it with these flags.")
		named, positional = parser.parse_args(argv)
		self.args = OpenStruct(named.__dict__, targets=positional)

	def app(self, name, fnc=None, cmd=None, flags=None):
		"""The method to define new applications"""
		if cmd is None:
			cmd = name + " %s"

#		if fnc:
#			print(fnc(OpenStruct(file='info',mode=0)))
		def function(context):
			if flags is not None:
				context.flags = flags
			if fnc:
				cmd = fnc(context)
			if '%' not in cmd:
				return cmd
			macros = dict(f=context.file, s=context.allfiles,
					d=os.path.dirname(context.file))
			return CustomTemplate(cmd).substitute(macros)
		self.apps[name] = function

	def appdef(self, function):
		self.app(function.__name__, fnc=function)
		return function

	def find_app(self, context, name, *apps):
		if not apps:
			return self.get_app(context, name)
		for app in (name, ) + tuple(apps):
			if not app in self.apps:
				if is_installed(app):
					return self.get_app(context, app)
			else:
				context_copy = OpenStruct(context)
				result = self.get_app(context_copy, app)
				result_split = result.split()
				if is_installed(result_split[0]):
					return result
		raise Exception("No appropriate program found!")

	def get_app(self, context, name):
		try:
			return self.apps[name](context)
		except KeyError:
			return name + " %s"

	def execute(self):
		if self.args.targets:
			return self.runner(app=self.args['with'], flags=self.args.flags,
					mode=self.args.mode, files=self.args.targets)
		sys.stderr.write("No targets specified!\n") #}}}

if __name__ == '__main__':
	Rifle(sys.argv[1:]).execute()
