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
The File Manager, putting the pieces together
"""

class FM():
	"""
	Bare file manager object.
	"""
	def __init__(self):
		"""
		Constructor.

		Please set this attributes externally:
		fm.settings - a Settings object
		fm.plugins - a PluginManager object
		fm.signals - a SignalManager object
		fm.env - an Environment object
		"""

	def emit(self, name, **kw):
		return self.signals.emit(name, fm=self, target=None, **kw)
