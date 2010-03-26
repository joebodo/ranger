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

from ranger.ext.openstruct import OpenStruct
from ranger.core import *

class TestSignal(unittest.TestCase):
	def setUp(self):
		self.fm = DummyFM()

	def test_signal_register_emit(self):
		fm = self.fm
		def poo(sig):
			self.assert_('works' in sig)
			self.assertEqual('yes', sig.works)
		handler = fm.signal_bind('x', poo)

		fm.signal_emit('x', works='yes')
		handler.remove()
		fm.signal_emit('x')

	def test_signal_order(self):
		fm = self.fm
		lst = []
		def addn(n):
			return lambda _: lst.append(n)

		fm.signal_bind('x', addn(6))
		fm.signal_bind('x', addn(3), prio=1)
		fm.signal_bind('x', addn(2), prio=1)
		fm.signal_bind('x', addn(9), prio=0)
		fm.signal_bind('x', addn(1337), prio=0.7)
		fm.signal_emit('x')

		self.assert_(lst.index(3) < lst.index(6))
		self.assert_(lst.index(2) < lst.index(6))
		self.assert_(lst.index(6) < lst.index(9))
		self.assert_(lst.index(1337) < lst.index(6))
		self.assert_(lst.index(1337) < lst.index(9))
		self.assert_(lst.index(1337) > lst.index(2))

	def test_modifying_arguments(self):
		fm = self.fm
		lst = []
		def modify(s):
			s.number = 5
		def set_number(s):
			lst.append(s.number)
		def stopit(s):
			s.stop()

		fm.signal_bind('setnumber', set_number)
		fm.signal_emit('setnumber', number=100)
		self.assertEqual(100, lst[-1])

		fm.signal_bind('setnumber', modify, prio=1)
		fm.signal_emit('setnumber', number=100)
		self.assertEqual(5, lst[-1])

		lst.append(None)
		fm.signal_bind('setnumber', stopit, prio=1)
		fm.signal_emit('setnumber', number=100)
		self.assertEqual(None, lst[-1])

class TestSettings(unittest.TestCase):
	def setUp(self):
		self.fm = DummyFM()
		self.fm._setting_structs = [
			OpenStruct(plugins=['x']),
			OpenStruct(plugins=['a','b','c']) ]
		self.fm.setting_add('plugins', [], list)

	def test_settings(self):
		fm = self.fm
		self.assertEqual(['x'], fm.settings.plugins)
		fm.settings.plugins = 'a', 'b', 'c'

	def test_signal_emission(self):
		fm = self.fm
		lst = []
		def fooo(signal):
			lst.append("something")

		fm.signal_bind(SETTING_CHANGE_SIGNAL, fooo)
		fm.settings.plugins = ['xyz']

		self.assertEqual(1, len(lst))

	def test_setting_postprocessing(self):
		"""
		When specifying a new colorscheme, one might want to keep the
		actual colorscheme object in sync with the setting.
		"""
		fm = self.fm

		fm.setting_add('colorscheme', type=str, default='')
		self.assertEqual('', fm.settings.colorscheme)

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

		fm.signal_bind(SETTING_CHANGE_SIGNAL, update_colorscheme)
		fm.settings.colorscheme = 'default'
		self.assertEqual('default', fm.settings.colorscheme)
		self.assertEqual(string2colorscheme('default'), my.colorscheme)

		bad = 'a colorscheme with spaces'
		fm.settings.colorscheme = bad
		self.assertNotEqual(bad, fm.settings.colorscheme)

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
		def __install__(self):
			self.fm.plugin_install('loop2')
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
		def __install__(self):
			try:
				self.fm.feature_implement('throbber', self)
			except:
				self.throbber_code_executed = False
			else:
				self.throbber_code_executed = True

class TestPlugins(unittest.TestCase):
	def setUp(self):
		self.fm = DummyFM()
		def name2plugin(self, name):
			class Foo(object):  # emulate a module
				Plugin = DummyPlugins.__dict__[name]
			return self._module_to_plugin(Foo, name)
		self.fm._name_to_plugin = MethodType(name2plugin, self.fm)

	def test_dependencies(self):
		fm = self.fm
		self.assertRaises(MissingFeature, fm.plugin_install, 'cool_commands')
		fm.plugin_install('base')  # implicitly installs console
		deps = set(DummyPlugins.base.__dependencies__)
		self.assert_(deps.issubset(fm._loaded_plugins))
		fm.plugin_install('cool_commands') # works now since console is installed

	def test_cycle_detection(self):
		fm = self.fm
		self.assertRaises(DependencyCycle, fm.plugin_install, 'loop1')
		self.assertRaises(DependencyCycle, fm.plugin_install, 'loop2')
		self.assertRaises(DependencyCycle, fm.plugin_install, 'loop3')

		# cycle1 implements feature x and depends on cycle2
		# cycle2 requires feature x. since cycle2 is installed before cycle1
		# as a dependency, the feature x will not be available yet.
		self.assertRaises(MissingFeature, fm.plugin_install, 'cycle1')

	def test_replace_features(self):
		fm = self.fm
		fm.plugin_install('myconsole')
		fm.plugin_install('base')
		self.assertFalse('ncurses_base_console' in fm._loaded_plugins)

		fm.plugin_install('myloader')  # nothing happens
		self.assertFalse('myloader' in fm._loaded_plugins)
		fm.plugin_install('myloader', force=True)
		self.assertTrue('myloader' in fm._loaded_plugins)
		self.assertTrue(fm.plugin_find('myloader').throbber_code_executed)

		self.assertTrue('throbber' in fm._loaded_features)
		self.assertRaises(FeatureAlreadyExists, fm.feature_implement,
				'throbber', None)
		self.assertEqual(fm.plugin_find('myloader'),
				fm._loaded_features['throbber'])

	def test_exclude_features(self):
		fm = self.fm
		name, feature = 'myconsole', 'console'
		fm.plugin_forbid(name)
		fm.plugin_install(name)
		self.assertFalse(name in fm._loaded_plugins)
		self.assertFalse(feature in fm._loaded_features)
		fm.plugin_allow(name)
		fm.plugin_install(name)
		self.assertTrue(name in fm._loaded_plugins)
		self.assertTrue(feature in fm._loaded_features)

		name, feature = 'mybookmarks', 'bookmarks'
		fm.feature_forbid(feature)
		fm.plugin_install(name)
		self.assertFalse(name in fm._loaded_plugins)
		self.assertFalse(feature in fm._loaded_features)
		fm.feature_allow(feature)
		fm.plugin_install(name)
		self.assertTrue(name in fm._loaded_plugins)
		self.assertTrue(feature in fm._loaded_features)

if __name__ == '__main__':
	unittest.main()

