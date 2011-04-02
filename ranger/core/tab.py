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

import ranger

from os.path import abspath, expanduser, normpath, join, isdir
from ranger.core.history import History

class Tab(object):
	def __init__(self, path):
#		SignalDispatcher.__init__(self)
		self.fm = ranger.get_fm()
		self.path = abspath(expanduser(path))
		self._cf = None
		self.cwd = None
		self.history = None
		self.pathway = ()
#		self.history = History(self.settings.max_history_size, unique=False)
		self.history = History(20, unique=False)
		self.path = abspath(expanduser(path))

	def ensure_correct_pointer(self):
		if self.cwd:
			self.cwd.correct_pointer()

	def get_selection(self):
		if self.cwd:
			return self.cwd.get_selection()
		return []

	def history_go(self, relative):
		"""Move relative in history"""
		if self.history:
			self.history.move(relative).go(history=False)

	def assign_cursor_positions_for_subdirs(self):
		"""Assign correct cursor positions for subdirectories"""
		last_path = None
		for path in reversed(self.pathway):
			if last_path is None:
				last_path = path
				continue

			path.move_to_obj(last_path)
			last_path = path

	def at_level(self, level):
		"""
		Returns the FileSystemObject at the given level.
		level >0 => previews
		level 0 => current file/directory
		level <0 => parent directories
		"""
		if level <= 0:
			try:
				return self.pathway[level - 1]
			except IndexError:
				return None
		else:
			directory = self.cf
			for i in range(level - 1):
				if directory is None:
					return None
				if directory.is_directory:
					directory = directory.pointed_obj
				else:
					return None
			try:
				return self.directories[directory.path]
			except AttributeError:
				return None
			except KeyError:
				return directory

	def enter_dir(self, path, history = True):
		"""Enter given path"""
		if path is None: return
		path = str(path)

		previous = self.cwd

		# get the absolute path
		path = normpath(join(self.path, expanduser(path)))

		if not isdir(path):
			return False
		new_cwd = self.fm.get_directory(path)

		try:
			os.chdir(path)
		except:
			return True
		self.path = path
		self.cwd = new_cwd

		self.cwd.load_content_if_outdated()

		# build the pathway, a tuple of directory objects which lie
		# on the path to the current directory.
		if path == '/':
			self.pathway = (self.fm.get_directory('/'), )
		else:
			pathway = []
			currentpath = '/'
			for dir in path.split('/'):
				currentpath = join(currentpath, dir)
				pathway.append(self.get_directory(currentpath))
			self.pathway = tuple(pathway)

		self.assign_cursor_positions_for_subdirs()

		# set the current file.
		self.cwd.sort_directories_first = self.settings.sort_directories_first
		self.cwd.sort_reverse = self.settings.sort_reverse
		self.cwd.sort_if_outdated()
		self.cf = self.cwd.pointed_obj

		if history:
			self.history.add(new_cwd)

		self.signal_emit('cd', previous=previous, new=self.cwd)

		return True
