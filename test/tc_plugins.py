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

from ranger.core import plug
from ranger.ext.openstruct import OpenStruct

import unittest
import os
import time

class TestPlugins(unittest.TestCase):
	def test_topological_dependency_sort(self):
		table = {
			'motivation': [],
			'shoes': ['socks', 'jeans'],
			'take_off_pajamas': ['motivation', 'get_out_of_bed'],
			't-shirt': ['undershirt'],
			'shirt': ['t-shirt', 'undershirt'],
			'jeans': ['underpants', 'socks'],
			'underpants': ['get_out_of_bed', 'take_off_pajamas'],
			'undershirt': ['get_out_of_bed', 'take_off_pajamas'],
			'get_out_of_bed': ['motivation'],
			'ready_to_go!': ['sunglasses', 'bag', 'mantle', 'shoes'],
			'bag': ['mantle', 'jeans'],
			'shave': ['motivation', 'underpants', 'get_out_of_bed'],
			'socks': ['get_out_of_bed'],
			'mantle': ['shirt', 'jeans', 'shoes'],
			'scarf': ['mantle'],
			'sunglasses': ['scarf', 'underpants'],
		}
		install_order = []
		def install(name):
			return lambda *__, **_: install_order.append(name)
		def name_to_module(name):
			return OpenStruct(__dependencies__=table[name],
					__install__=install(name), name=name)
		plug._name_to_module = name_to_module
		plug.install_plugins(['t-shirt', 'shave', 'ready_to_go!'], debug=True)

		# print(' -> '.join(install_order))
		for name, deps in table.items():
			for dep in deps:
				try:
					self.assert_(install_order.index(dep) < \
							install_order.index(name))
				except ValueError:
					raise KeyError(dep, name)

if __name__ == '__main__':
	unittest.main()
