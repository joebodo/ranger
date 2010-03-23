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

__license__ = 'GPL3'
__version__ = '1.0.4'
__credits__ = 'Roman Zimbelmann'
__author__ = 'Roman Zimbelmann'
__maintainer__ = 'Roman Zimbelmann'
__email__ = 'romanz@lavabit.com'

from ranger import log
from ranger.container import Bookmarks
from ranger import relpath_conf
from ranger.fsobject.directory import Directory

def __install__(fm, signals):
	register = signals.register
	@register('loop_start')
	def update_bookmarks(signal):
		signal.fm.bookmarks.update_if_outdated()

	@register('terminate')
	def save_bookmarks(signal):
		signal.fm.bookmarks.remember(signal.fm.env.cwd)
		signal.fm.bookmarks.save()

	@register('initialize')
	def init_bookmarks(signal):
		if signal.arg.clean:
			bookmarkfile = None
		else:
			bookmarkfile = relpath_conf('bookmarks')
		bm = Bookmarks(
				bookmarkfile=bookmarkfile,
				bookmarktype=Directory,
				autosave=signal.fm.settings.autosave_bookmarks)
		bm.load()
		signal.fm.bookmarks = bm

	@fm.lib.register
	def enter_bookmark(fm, key):
		try:
			destination = fm.bookmarks[key]
			cwd = fm.env.cwd
			if destination.path != cwd.path:
				fm.bookmarks.enter(key)
				fm.bookmarks.remember(cwd)
		except KeyError:
			pass

	@fm.lib.register
	def set_bookmark(fm, key):
		"""Set the bookmark with the name <key> to the current directory"""
		log(fm)
		fm.bookmarks[key] = fm.env.cwd

	@fm.lib.register
	def unset_bookmark(fm, key):
		"""Delete the bookmark with the name <key>"""
		fm.bookmarks.delete(key)
