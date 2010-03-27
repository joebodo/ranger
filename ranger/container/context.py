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

class ViewContext(object):
	def __init__(self, fm):
		self.cwd = None
		self.cf = None
		self.pathway = None
		self.pointers = {}
		self.fm = fm

	def enter_dir(self, path):
		"""Enter given path"""
		if path is None: return
		path = str(path)

		# get the absolute path
		path = normpath(join(self.path, expanduser(path)))

		if not isdir(path):
			return

		try:
			new_cwd = self.fm.lib.env.get_directory(path)
		except NoDirectoryGiven:
			return False

		self.path = path
		self.cwd = new_cwd
		os.chdir(path)

#		self.cwd.load_content_if_outdated()

		# build the pathway, a tuple of directory objects which lie
		# on the path to the current directory.
		if path == '/':
			self.pathway = (self.get_directory('/'), )
		else:
			pathway = []
			currentpath = '/'
			for dir in path.split('/'):
				currentpath = join(currentpath, dir)
				pathway.append(self.get_directory(currentpath))
			self.pathway = tuple(pathway)

		self.assign_cursor_positions_for_subdirs()

		# set the current file.
#		self.cwd.sort_if_outdated()
		self.cf = self.pointers[self.cwd]

		if history:
			self.history.add(new_cwd)

		return True

