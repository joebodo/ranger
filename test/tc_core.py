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

# monkey-patch some of the core parts for easier testing

class OpenStruct(dict):
	def __init__(self, **kw):
		dict.__init__(self, kw)
		self.__dict__ = self

def patched_name_to_module(name):
	return DummyPlugins.__dict__[name]()

def patched_get_config_files():
	default = OpenStruct(plugins=['a','b','c'])
	custom = OpenStruct(plugins=['x'])
	return default, custom

import ranger.core.settings
ranger.core.settings._get_config_files = patched_get_config_files
import ranger.core.plugin
ranger.core.plugin._name_to_module = patched_name_to_module

import ranger.core.init

from ranger.core.plugin import MissingFeature, DependencyCycle
from ranger import *


class TestSettings(unittest.TestCase):
	def setUp(self):
		signal.clear()
	tearDown = setUp

	def test_settings(self):
		self.assertEqual(['x'], settings.plugins)

		settings.plugins = 'a', 'b', 'c'

	def test_signal_emission(self):
		lst = []
		def fooo(signal):
			lst.append("something")

		signal.register(settings.CHANGE, fooo)
		settings.plugins = ['xyz']

		self.assertEqual(1, len(lst))

	def test_setting_postprocessing(self):
		"""
		When specifying a new colorscheme, one might want to keep the
		actual colorscheme object in sync with the setting.
		"""

		settings.register('colorscheme', type=str, default='')
		self.assertEqual('', settings.colorscheme)

		my = OpenStruct()
		my.colorscheme = None

		def scheme_invalid(string):
			# don't allow spaces in colorscheme names!
			return ' ' in string

		def string2colorscheme(string):
			return 'colorscheme:' + string

		def update_colorscheme(signal):
			if scheme_invalid(signal.value):
				signal.value = signal.previous
			my.colorscheme = string2colorscheme(signal.value)

		signal.register(settings.CHANGE, update_colorscheme)
		settings.colorscheme = 'default'
		self.assertEqual('default', settings.colorscheme)
		self.assertEqual(string2colorscheme('default'), my.colorscheme)

		bad = 'a colorscheme with spaces'
		settings.colorscheme = bad
		self.assertNotEqual(bad, settings.colorscheme)


class TestSignal(unittest.TestCase):
	def setUp(self):
		signal.clear()
	tearDown = setUp

	def test_signal_register_emit(self):
		def poo(sig):
			self.assert_('works' in sig)
			self.assertEqual('yes', sig.works)
		handler = signal.register('x', poo)

		signal.emit('x', works='yes')

		signal.base_signal_keywords = {'works': 'yes'}
		signal.emit('x')
		signal.base_signal_keywords = None
		handler.remove()
		signal.emit('x')

	def test_signal_order(self):
		lst = []
		def addn(n):
			return lambda _: lst.append(n)

		signal.register('x', addn(6))
		signal.register('x', addn(3), prio=1)
		signal.register('x', addn(2), prio=1)
		signal.register('x', addn(9), prio=0)
		signal.register('x', addn(1337), prio=0.7)
		signal.emit('x')

		self.assert_(lst.index(3) < lst.index(6))
		self.assert_(lst.index(2) < lst.index(6))
		self.assert_(lst.index(6) < lst.index(9))
		self.assert_(lst.index(1337) < lst.index(6))
		self.assert_(lst.index(1337) < lst.index(9))
		self.assert_(lst.index(1337) > lst.index(2))

	def test_modifying_arguments(self):
		lst = []
		def modify(s):
			s.number = 5
		def set_number(s):
			lst.append(s.number)
		def stopit(s):
			s.stop()

		signal.register('setnumber', set_number)
		signal.emit('setnumber', number=100)
		self.assertEqual(100, lst[-1])

		signal.register('setnumber', modify, prio=1)
		signal.emit('setnumber', number=100)
		self.assertEqual(5, lst[-1])

		lst.append(None)
		signal.register('setnumber', stopit, prio=1)
		signal.emit('setnumber', number=100)
		self.assertEqual(None, lst[-1])


class DummyPlugins(object):
	"""Imagine this is your plugin directory"""
	class base(object):
		__dependencies__ = ['ncurses_base_console', 'loader_parallel']
	class ncurses_base_console(object):
		__implements__ = ['console']
	class loader_parallel(object):
		__implements__ = ['data_loader']
	class cool_commands(object):
		__required_features__ = ['console']
	class loop1(object):
		__dependencies__ = 'loop2'
	class loop2(object):
		__dependencies__ = 'loop1'
	class loop3(object):
		def __install__(self):
			plugin.raw_install('loop2')
	class cycle1(object):
		__implements__ = ['x']
		__dependencies__ = ['cycle2']
	class cycle2(object):
		__required_features__ = ['x']


class TestPlugin(unittest.TestCase):
	def tearDown(self):
		plugin.reset()

	def test_dependencies(self):
		self.assertRaises(MissingFeature, plugin.raw_install, 'cool_commands')
		plugin.raw_install('base')
		deps = set(DummyPlugins.base.__dependencies__)
		self.assert_(deps.issubset(plugin.plugins))
		plugin.raw_install('cool_commands') # works now since console is installed

	def test_cycle_detection(self):
		self.assertRaises(DependencyCycle, plugin.raw_install, 'loop1')
		self.assertRaises(DependencyCycle, plugin.raw_install, 'loop2')
		self.assertRaises(DependencyCycle, plugin.raw_install, 'loop3')

		self.assertRaises(MissingFeature, plugin.raw_install, 'cycle1')


if __name__ == '__main__':
	unittest.main()
