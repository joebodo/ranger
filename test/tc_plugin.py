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

if __name__ == '__main__': from __init__ import init; init()

import unittest
import inspect

class DummyPlugin(object):
	pass

class base(DummyPlugin):
	__dependencies__ = ['ncurses_base_console', 'loader_parallel']
class ncurses_base_console(DummyPlugin):
	__implements__ = ['console']
class loader_parallel(DummyPlugin):
	__implements__ = ['data_loader']
class cool_commands(DummyPlugin):
	__required_features__ = ['console']
class loop1(DummyPlugin):
	__dependencies__ = 'loop2'
class loop2(DummyPlugin):
	__dependencies__ = 'loop1'
class loop3(DummyPlugin):
	def __install__(self):
		plugin.raw_install('loop2')
class cycle1(DummyPlugin):
	__implements__ = ['x']
	__dependencies__ = ['cycle2']
class cycle2(DummyPlugin):
	__required_features__ = ['x']

plugins = {}
for name, obj in vars().copy().items():
	if inspect.isclass(obj) and issubclass(obj, DummyPlugin) \
			and obj is not DummyPlugin:
		plugins[name] = obj()

def patched_name_to_module(name):
	return plugins[name]

import ranger.core.plugin
ranger.core.plugin._name_to_module = patched_name_to_module
import ranger.core.init

from ranger import plugin
from ranger.core.plugin import MissingFeature, DependencyCycle

class Test(unittest.TestCase):
	def tearDown(self):
		plugin.reset()

	def test_dependencies(self):
		self.assertRaises(MissingFeature, plugin.raw_install, 'cool_commands')
		plugin.raw_install('base')
		deps = set(base.__dependencies__)
		self.assert_(deps.issubset(plugin.plugins))
		plugin.raw_install('cool_commands') # works now since console is installed

	def test_cycle_detection(self):
		self.assertRaises(DependencyCycle, plugin.raw_install, 'loop1')
		self.assertRaises(DependencyCycle, plugin.raw_install, 'loop2')
		self.assertRaises(DependencyCycle, plugin.raw_install, 'loop3')

		self.assertRaises(MissingFeature, plugin.raw_install, 'cycle1')

if __name__ == '__main__':
	unittest.main()

