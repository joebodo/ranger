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
from ranger.fsobject.data import FileData

class Plugin(object):
	__implements__ = 'loader'
	def __install__(self):
		self.fm.lib.register_method('load_path', load_path)

def load_path(self, path, force=False):
	files = os.listdir(path)
	f = FileData(path)
	load_file(f)
	self.signal_emit('loader.update_path', path=path, content=content)

def load_file(self):
	try:
		self.stat = os.lstat(self.path)
	except OSError:
		self.stat = None
		self.islink = False
		self.accessible = False
	else:
		self.islink = stat.S_ISLNK(self.stat.st_mode)
		self.accessible = True

	if self.accessible and os.access(self.path, os.F_OK):
		self.exists = True
		self.accessible = True

		if os.path.isdir(self.path):
			self.type = T_DIRECTORY
			try:
				self.size = len(os.listdir(self.path))
				self.infostring = ' %d' % self.size
				self.runnable = True
			except OSError:
				self.infostring = BAD_INFO
				self.runnable = False
				self.accessible = False
		elif os.path.isfile(self.path):
			self.type = T_FILE
			self.size = self.stat.st_size
			self.infostring = ' ' + human_readable(self.stat.st_size)
		else:
			self.type = T_UNKNOWN
			self.infostring = None

	else:
		if self.islink:
			self.infostring = '->'
		else:
			self.infostring = None
		self.type = T_NONEXISTANT
		self.exists = False
		self.runnable = False

	if self.islink:
		self.readlink = os.readlink(self.path)
