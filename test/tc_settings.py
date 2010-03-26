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

class OpenStruct(dict):
	def __init__(self, **kw):
		dict.__init__(self, kw)
		self.__dict__ = self

def patched_get_config_files():
	default = OpenStruct(plugins=['a','b','c'])
	custom = OpenStruct(plugins=['x'])
	return default, custom

import ranger.core.settings
ranger.core.settings._get_config_files = patched_get_config_files
ranger.core.init()
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


if __name__ == '__main__':
	unittest.main()
