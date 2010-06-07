#!/usr/bin/python -O
# -*- coding: utf-8 -*-
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
Ranger-run: Configurable file-opener
"""

from ranger.core.runner import Runner
from string import Template
from os.path import dirname, expanduser

__version__ = '0.0'
USAGE = '%prog [options] [filename1 [filename 2...]]'
DEFAULT_CONFIG = '~/.pyrunrc'
apps = {}

class OpenStruct(dict): #{{{
	"""The fusion of dict and struct"""
	def __init__(self, *__args, **__keywords):
		dict.__init__(self, *__args, **__keywords)
		self.__dict__ = self #}}}

class AppsWrapper(object): #{{{
	def __init__(self, apps):
		self.apps = apps

	def apply(self, app, context):
		if not app or app not in self.apps:
			app = 'default'
		try:
			handler = self.apps[app]
		except KeyError:
			return False
		return handler(context) #}}}

def shell_quote(string): #{{{
	"""Escapes by quoting"""
	return "'" + str(string).replace("'", "'\\''") + "'" #}}}

def parse_arguments(): #{{{
	from optparse import OptionParser 
	parser = OptionParser(usage=USAGE, version='pyrun ' + __version__)

	parser.add_option('-r', '--config', type='string',
			metavar='path', default=DEFAULT_CONFIG,
			help="the configuration path. (%default)")
	parser.add_option('-m', '--mode', type='int', default=0, metavar='n',
			help="if a filename is supplied, run it with this mode")
	parser.add_option('-f', '--flags', type='string', default='',
			metavar='string',
			help="if a filename is supplied, run it with these flags.")

	named, positional = parser.parse_args()
	args = OpenStruct(named.__dict__, targets=positional)
	return args #}}}

def substitute_macros(cmd, context): #{{{
	class _CustomTemplate(Template):
		delimiter = '%'
		idpattern = '[a-z]'
	if '%' not in cmd:
		return cmd
	macros = {}
	macros['f'] = context.file
	macros['s'] = ' '.join(shell_quote(fl) for fl in context.files)
	macros['d'] = dirname(context.file)
	return _CustomTemplate(cmd).safe_substitute(macros) #}}}

def app(name, fnc=None, cmd=None, flags=None): #{{{
	global apps
	if fnc:
		if flags is not None:
			def result(context):
				context.flags = flags
				return fnc(context)
		else:
			result = fnc
	elif cmd:
		if flags is not None:
			def result(context):
				context.flags = flags
				return substitute_macros(cmd, context)
		else:
			def result(context):
				return substitute_macros(cmd, context)
	else:
		raise Exception('define a function or a command!')
	apps[name] = result #}}}

# Defaults:
app('default', cmd='cat %s')
app('pager', cmd='less')

args = parse_arguments()
if args.targets:
	config = open(expanduser(args.config), 'r')
	exec(config)

	runner = Runner(apps=AppsWrapper(apps))
	runner(files=args.targets, flags=args.flags, mode=args.mode)
