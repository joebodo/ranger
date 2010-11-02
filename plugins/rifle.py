#!/usr/bin/python
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
rifle - A simple pythonic file launcher

This is a file launcher designed to work as a ranger plugin as
well as a standalone application.

As a standalone program, you can pass arguments to it on the command
line and by looking at the files, rifle decides how to start them.

As a ranger plugin, it will replace the :execute command and add an
:open_with command which allow you to interface with rifle.


----------------------------------------------------------------
Configuration is done the python files ~/.riflerc (standalone)
or ~/.config/ranger/riflerc.py (when used as a ranger plugin).
To use the same config file in standalone, you can either create a symlink:
    ln -s .config/ranger/riflerc.py ~/.riflerc
or run rifle with the -r option:
    rifle -r ~/.config/ranger/riflerc.py
or simply edit the default path for the conig file in the code.


If you want to open a file named movie.avi with mplayer, run:
    rifle --with=mplayer movie.avi

You can tell rifle what you mean with mplayer by adding this to your conf file:
    app('mplayer', 'mplayer -fs %s')
Now "rifle --with=mplayer movie.avi" would execute "mplayer -fs movie.avi".

To detach mplayer from the console to continue working there, you can
use "flags".  The flag for detaching is d.
    app('mplayer', 'mplayer -fs %s', flags='d')

Without the "--with" option, rifle executes the app "default".  So if you
want to run all files with "vim" by default, you can write:
  app('default', 'vim %s')

But rifle allows you to write a python function that automatically detects
the filetype and runs the right program:

  def default_handler(context):
    if isvideo(context.file):
      return "mplayer %s"
    elif isaudio(context.file):
      context.flags = "d"
      return "mplayer -fs %s"
    elif isimage(context.file):
      return "feh %s"
    elif context.file.endswith(".html") or context.file.endswith(".swf"):
      return "firefox %s"
    elif iscontainer(context.file):
      return "atool --extract %s"
    elif mimetype(context.file).startswith("text"):
      return "vim %s"
  app('default', fnc=default_handler)

The function takes a context-object as the single argument and returns
the command to be run (either a string or a list of arguments)

When calling app(), it returns such a function which can be used later on, eg:
  handler = app("mplayer", "mplayer %s")
  app("mplayer_detached", fnc=handler, flags="d")

If you're unexperienced with python, try this quick tutorial:
  http://www.korokithakis.net/tutorials/python


----------------------------------------------------------------
Reference:

"context" is a dictionary-like object that contains parameters for rifle.
context.app is the --with parameter,
context.files is a list of file paths that have been passed to rifle,
context.file is the first file path of context.files,
context.mode is the --mode parameter
context.flags is the --flags parameter
context.fm is the fm instance of ranger if it runs, otherwise None.

"app" can be used like:
app("name", "command")
app("name", cmd="command")
app("name", cmd="command", flags="xyz", mode=123)

Aliases can be done like this:
function = app("name", "command")
app("other_name", fnc=function)

"flags" are single characters that influence how programs are run:
d = detach from terminal
w = wait for enter press after execution
p = pipe into pager (app "pager")
q = discard output

"modes" are simply numbers which are passed to rifle to distinguish
different ways of running the same file.  The default mode is 0.
For example, if the config looks like this:
app("mplayer", cmd="mplayer %s")
app("mplayer", cmd="mplayer -fs %s", mode=1)
Then:
"rifle --with=mplayer --mode=0 foo.avi"   runs   "mplayer foo.avi"
"rifle --with=mplayer --mode=1 foo.avi"   runs   "mplayer -fs foo.avi"

"macros" are special words that you can use in return values of app functions:
%s   => All passed filenames
%f   => The first passed filename
%d   => The dirname of %f
%b   => The basename of %f

Helper functions:
extension(filename)    returns the extension of filename
mimetype(filename)     returns the mimetype of filename
isvideo(filename)      does the mimetype of filename start with "video"?
isaudio(filename)      does the mimetype of filename start with "audio"?
isimage(filename)      does the mimetype of filename start with "image"?
iscontainer(filename)  does filename have the extension of a container type?
"""

from __future__ import print_function
import optparse
import os.path
import sys
import string
import subprocess

__version__    = '1.0'
__author__     = 'Roman Zimbelmann'
USAGE          = '%prog [options] [filename1 [filename 2...]]'
DEFAULT_CONFIG = '~/.riflerc'
DEFAULT_PAGER  = {'cmd': 'less'}
DEFAULT_ACTION = {'cmd': 'vim %s'}

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
#}}}

# Helper functions for .riflerc #{{{
def extension(filename):
	return os.path.splitext(filename)[1][1:]

def mimetype(filename):
	return spawn('file', '-Lb', '--mime-type', filename)

def isimage(filename):
	return mimetype(filename).startswith('image')

def isvideo(filename):
	return mimetype(filename).startswith('video')

def isaudio(filename):
	return mimetype(filename).startswith('audio')

CONTAINER_EXTENSIONS = ('7z', 'ace', 'ar', 'arc', 'bz', 'bz2', 'cab', 'cpio',
	'cpt', 'dgc', 'dmg', 'gz', 'iso', 'jar', 'msi', 'pkg', 'rar', 'shar',
	'tar', 'tbz', 'tgz', 'xar', 'xz', 'zip')

def iscontainer(filename):
	return extension(filename) in CONTAINER_EXTENSIONS
#}}}

class Runner(object): #{{{
	def __init__(self, apps, fm, printfunc):
		self.apps = apps
		self.fm = fm
		self.printfunc = printfunc

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
			files=None, mode=0, flags='', verbose=False, **popen_kws):
		# Find an action if none was supplied by creating a Context object
		# and passing it to the app.
		context = OpenStruct(app=app, files=files, mode=mode,
				flags=flags, popen_kws=popen_kws, fm=self.fm,
				file=(files and files[0] or None))

		if self.apps:
			if try_app_first and action is not None:
				test = self._find_app(app, context)
				if test:
					action = test
			if action is None:
				action = self._find_app(app, context)
				if action is None:
					self.printfunc("No action found!\n")
					return False

		if action is None:
			self.printfunc("No way of determining the action!\n")
			return False

		# Preconditions
		self._squash_flags(context)
		popen_kws = context.popen_kws  # shortcut

		toggle_ui      = self.fm is not None
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
			toggle_ui = False
		if 'w' in context.flags:
			wait_for_enter = True

		# Finally, run it
		try:
			process = None
			if toggle_ui:
				self.fm.ui.suspend()
			try:
				if verbose:
					self.printfunc(popen_kws['args'])
				process = subprocess.Popen(**popen_kws)
			except:
				self.printfunc("Failed to run: " + str(action) + "\n")
			else:
				if wait_for_exit:
					waitpid_no_intr(process.pid)
		finally:
			if process:
				if pipe_output:
					if toggle_ui:
						self.fm.ui.initialize()
					return self(app='pager', stdin=process.stdout,
							flags=context.flags+'PQ')
				elif wait_for_enter:
					print("Press ENTER to continue...")
					try: raw_input()
					except:  input()
			if toggle_ui:
				self.fm.ui.initialize()
			return process #}}}

class Rifle(object): #{{{
	def __init__(self, argv, printfunc=None, fm=None):
		self.printfunc = printfunc or sys.stderr.write
		self.apps = {}
		self.runner = Runner(self.apps, fm, printfunc)
		self.parse_arguments(argv)

		# Setup defaults
		global app
		app = self.app
		app('default', **DEFAULT_ACTION)
		app('pager', **DEFAULT_PAGER)

		# Load config file
		try:
			rc_file = os.path.expanduser(self.args.config)
			config = open(rc_file, 'r').read()
		except IOError:
			pass
		else:
			exec(compile(config, rc_file, 'exec'), globals())

	def parse_arguments(self, argv):
		parser = optparse.OptionParser(usage=USAGE,
				version='rifle ' + __version__)
		parser.add_option('-v', '--verbose', action='store_true',
				help="display additional information")
		parser.add_option('-r', '--config', type='string',
				metavar='path', default=DEFAULT_CONFIG,
				help="the configuration path. (default = %default)")
		parser.add_option('-w', '--with', type='string', default='default',
				help="what program to run the file(s) with?", metavar='app')
		parser.add_option('-m', '--mode', type='int', default=0, metavar='n',
				help="run the files with this mode")
		parser.add_option('-f', '--flags', type='string', default='',
				metavar='string',
				help="run the files with these flags")
		named, positional = parser.parse_args(argv)
		self.args = OpenStruct(named.__dict__, targets=positional)

	def app(self, name, cmd=None, fnc=None, mode=None, flags=None):
		"""The method to define new applications"""
		def function(context):
			if flags is not None:
				context.flags = flags
			if fnc:
				newcmd = fnc(context)
			elif cmd:
				newcmd = cmd
			else:
				raise Exception('define a function or a command!')
			if not newcmd:
				return False
			if '%' in newcmd:
				macros = dict(f=shell_quote(context.file),
						s=' '.join(shell_quote(fl) for fl in context.files),
						b=shell_quote(os.path.basename(context.file)),
						d=shell_quote(os.path.dirname(os.path.abspath(
							context.file))))
				return CustomTemplate(newcmd).safe_substitute(macros)
			else:
				return newcmd
		self.apps[name] = function
		return function

	def execute(self):
		if self.args.targets:
			return self.runner(app=self.args['with'], flags=self.args.flags,
					mode=self.args.mode, files=self.args.targets,
					verbose=self.args.verbose)
		self.printfunc("No targets specified!\n")
		return False #}}}

if __name__ == '__main__':
	Rifle(sys.argv[1:], printfunc=print).execute()
else:
	# Ranger integration {{{
	try:
		from ranger import fm
	except:
		pass
	else:
		fm.register_plugin(name='rifle', version=__version__, help=__doc__)
		from ranger.api.commands import Command
		from ranger.ext.shell_escape import shell_escape
		register = fm.commands.register
		fm.cmd('map r console open_with ')

		def run_files(cmd, sel, with_=None, mode=None, flags=None):
			sel = [str(f) for f in sel]
			args = ['-r', self.fm.confpath('riflerc.py')]
			if with_:
				args.extend(['--with', with_])
			if mode is not None:
				args.extend(['--mode', str(mode)])
			if flags is not None:
				args.extend(['--flags', flags])
			if cmd.fm.debug:
				args.append('--verbose')
			rifle = Rifle(args + sel, fm=cmd.fm, printfunc=self.fm.notify)
			return rifle.execute()

		# This is evil. Got another idea?
		globals().update(locals())

		@register
		class open_with(Command):
			def execute(self):
				run_files(self, self.fm.env.get_selection(),
						with_=self.rest(1) or None)

		@register
		class execute(Command):
			def execute(self):
				cf = self.fm.env.cf
				selection = self.fm.env.get_selection()
				if self.fm.env.enter_dir(cf):
					return
				elif selection:
					result = run_files(self, selection, mode=self.n)
					if not result:
						self.fm.cmd('console open_with ') #}}}
