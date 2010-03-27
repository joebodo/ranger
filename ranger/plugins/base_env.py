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
An object which contains data that has global relevance

Such as:
username
hostname
directories
copy, cut
"""

import socket
import pwd
import os

from ranger.fsobject.data import FileData

class Plugin(object):
	__implements__ = 'environment'
	__requires__ = 'loader'

	def __install__(self):
		self.fm.lib.env = self
		self.fm.signal_bind('core.init', self.initialize)
		self.fm.signal_bind('loader.update_path', self.update_path)

	def initialize(self):
		try:
			self.username = pwd.getpwuid(os.geteuid()).pw_name
		except:
			self.username = 'uid:' + str(os.geteuid())
		self.hostname = socket.gethostname()
		self.home_path = os.path.expanduser('~')
		self.directories = {}
		self.copy = set()
		self.cut = False

	def get_free_space(self, path):
		from os import statvfs
		stat = statvfs(path)
		return stat.f_bavail * stat.f_bsize

	def get_directory(self, path):
		path = os.path.abspath(path)
		try:
			return self.directories[path]
		except:
			self.fm.lib.load_path(path)
			try:
				return self.directories[path]
			except:
				return FileData(path)

	def update_path(self, signal):
		self.directories[signal.path] = signal.content
