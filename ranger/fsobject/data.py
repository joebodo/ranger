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

import os

class FileData(dict):
	def __init__(self, path):
		dict.__init__(self)
		self.__dict__ = self
		path = os.path.abspath(path)
		self.path = path
		self.basename = os.path.basename(path)
		self.dirname = os.path.dirname(path)
		try:
			self.extension = self.basename[ \
					self.basename.rindex('.') + 1:].lower()
		except ValueError:
			self.extension = None
		self.reset()

	def reset(self):
		self.is_file = False
		self.is_directory = False
		self.exists = False
		self.accessible = False
		self.executable = False
		self.is_link = False
		self.stat = None
		self.size = None
		self.files = None
		self.permissions = None
		self.link_destination = None
		self._shell_escaped_basename = None
		self._filetype = None
