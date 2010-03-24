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

from ranger import signal
import unittest

class TestDisplayable(unittest.TestCase):
	def setUp(self):
		signal.clear()
	tearDown = setUp

	def test_signal_register_emit(self):
		@signal.register('x')
		def poo(sig):
			self.assert_('works' in sig)
			self.assertEqual('yes', sig.works)

		signal.emit('x', works='yes')

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

if __name__ == '__main__':
	unittest.main()
