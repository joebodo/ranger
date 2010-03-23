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
Specification for plugins:

fm.functions: semi global functions which can be registered from
inside your plugin so they are accessible outside, for example so you
can assign keybindings to them or call them from other modules.
Avoid dependencies though!


fm.signals: 
"""

import ranger
from ranger import relpath, relpath_conf
from os.path import exists
from inspect import getargspec

def _find_plugin(name):
	assert isinstance(name, str), 'Plugin names must be strings!'
	assert '.' not in name, 'Specify plugin names without the extension!'
	if exists(relpath_conf('plugins', name + '.py')):
		return 'plugins'
	elif exists(relpath('plugins', name + '.py')):
		return 'ranger.plugins'
	raise Exception('Plugin not found!')

def install_plugins(plugins, **keywords):
	for plugin in plugins:
		path = _find_plugin(plugin)
		module = __import__(path, fromlist=[plugin])
		installfunc = getattr(module, plugin).__install__
		install_keywords = dict(
				(arg, keywords[arg] if arg in keywords else None) \
				for arg in getargspec(installfunc).args)
		installfunc(**install_keywords)
