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
from types import MethodType

#def patched_name_to_module(name):
#	return DummyPlugins.__dict__[name]()
#
#import ranger.core.plugin
#ranger.core.plugin._name_to_module = patched_name_to_module

#ranger.core.init()

from ranger.core.plugin import MissingFeature, DependencyCycle, \
		FeatureAlreadyExists
from ranger import *


class DummyPlugins(object):
	"""Imagine this is your plugin directory"""
	class base(object):
		__dependencies__ = ['ncurses_base_console', 'loader_parallel']
	class ncurses_base_console(object):
		__implements__ = ['console']
	class loader_parallel(object):
		__implements__ = ['data_loader']
	class cool_commands(object):
		__requires__ = ['console']
	class loop1(object):
		__dependencies__ = 'loop2'
	class loop2(object):
		__dependencies__ = 'loop1'
	class loop3(object):
		@staticmethod
		def __install__(self):
			self.fm.plugins.install('loop2')
	class cycle1(object):
		__implements__ = ['x']
		__dependencies__ = ['cycle2']
	class cycle2(object):
		__requires__ = ['x']
	class myconsole(object):
		__implements__ = ['console']
	class mybookmarks(object):
		__implements__ = ['bookmarks']
	class myloader(object):
		__implements__ = 'data_loader'
		@staticmethod
		def __install__(self):
			try:
				self.implement_feature('throbber')
			except:
				self.throbber_code_executed = False
			else:
				self.throbber_code_executed = True

class TestPlugin(unittest.TestCase):
	def setUp(self):
		from ranger.core.dummy import DummyFM
		from ranger.core.plugin import Plugin
		fm = DummyFM()
		fm.plugins.name_to_plugin = MethodType(lambda s,n: Plugin(n, DummyPlugins.__dict__[n](),s), fm)
		self.plugin = fm.plugins

	def test_dependencies(self):
		plugin = self.plugin
		self.assertRaises(MissingFeature, plugin.install, 'cool_commands')
		plugin.install('base')
		deps = set(DummyPlugins.base.__dependencies__)
		self.assert_(deps.issubset(plugin.plugins))
		plugin.install('cool_commands') # works now since console is installed

	def test_cycle_detection(self):
		plugin = self.plugin
		self.assertRaises(DependencyCycle, plugin.install, 'loop1')
		self.assertRaises(DependencyCycle, plugin.install, 'loop2')
		self.assertRaises(DependencyCycle, plugin.install, 'loop3')

		# cycle1 implements feature x and depends on cycle2
		# cycle2 requires feature x. since cycle2 is installed before cycle1
		# as a dependency, the feature x will not be available yet.
		self.assertRaises(MissingFeature, plugin.install, 'cycle1')

	def test_replace_features(self):
		plugin = self.plugin
		plugin.install('myconsole')
		plugin.install('base')
		self.assertFalse('ncurses_base_console' in plugin.plugins)

		plugin.install('myloader')  # nothing happens
		self.assertFalse('myloader' in plugin.plugins)
		plugin.install('myloader', force=True)
		self.assertTrue('myloader' in plugin.plugins)
		self.assertTrue(plugin.find('myloader').throbber_code_executed)

		self.assertTrue('throbber' in plugin.features)
		self.assertRaises(FeatureAlreadyExists, plugin.implement_feature,
				'throbber', None)
		self.assertEqual(plugin.find('myloader'), plugin.features['throbber'])

	def test_exclude_features(self):
		plugin = self.plugin
		name, feature = 'myconsole', 'console'
		plugin.exclude_plugins(name)
		plugin.install(name)
		self.assertFalse(name in plugin.plugins)
		self.assertFalse(feature in plugin.features)
		plugin.allow_plugins(name)
		plugin.install(name)
		self.assertTrue(name in plugin.plugins)
		self.assertTrue(feature in plugin.features)

		name, feature = 'mybookmarks', 'bookmarks'
		plugin.exclude_features(feature)
		plugin.install(name)
		self.assertFalse(name in plugin.plugins)
		self.assertFalse(feature in plugin.features)
		plugin.allow_features(feature)
		plugin.install(name)
		self.assertTrue(name in plugin.plugins)
		self.assertTrue(feature in plugin.features)

if __name__ == '__main__':
	unittest.main()
