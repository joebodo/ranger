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
An OpenStruct is a dict that lets you access its items like attributes.

This means, ostruct['foo'] is equivalent to ostruct.foo.
"""

class OpenStruct(dict):
	"""
	An OpenStruct is a dict that lets you access its items like attributes.

	This means, ostruct['foo'] is equivalent to ostruct.foo.

	>>> ostruct = OpenStruct(foo='hello', bar='world', **{'a':1, 'b':2})
	>>> assert ostruct.a == 1
	>>> assert ostruct.b == 2
	>>> assert ostruct.foo == ostruct['foo']
	>>> 'bar' in ostruct
	True
	"""

	# prepend __ to arguments because one might use "args"
	# or "keywords" as a keyword argument.
	def __init__(self, *__args, **__keywords):
		dict.__init__(self, *__args, **__keywords)
		self.__dict__ = self

if __name__ == '__main__':
	import doctest
	doctest.testmod()
