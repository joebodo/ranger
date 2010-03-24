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

__implements__ = ['bookmarks']

from ranger.container import Bookmarks
from ranger import relpath_conf
from ranger.fsobject.directory import Directory
from ranger.gui.widgets.browserview import BrowserView

def loop_start(signal):
	signal.fm.bookmarks.update_if_outdated()

def terminate(signal):
	signal.fm.bookmarks.remember(signal.fm.env.cwd)
	signal.fm.bookmarks.save()

def draw(sig):
	try:
		sig.fm.env.cmd.show_obj.draw_bookmarks
	except AttributeError:
		return

	sig.stop_propagation()

	self = sig.target
	self.need_clear = True

	sorted_bookmarks = sorted(item for item in self.fm.bookmarks \
			if '/.' not in item[1].path)

	def generator():
		return zip(range(self.hei), sorted_bookmarks)

	try:
		maxlen = max(len(item[1].path) for i, item in generator())
	except ValueError:
		return
	maxlen = min(maxlen + 5, self.wid)

	for line, items in generator():
		key, mark = items
		string = " " + key + ": " + mark.path
		self.addnstr(line, 0, string.ljust(maxlen), self.wid)

def initialize(signal):
	if signal.fm.arg.clean:
		bookmarkfile = None
	else:
		bookmarkfile = relpath_conf('bookmarks')
	bm = Bookmarks(
			bookmarkfile=bookmarkfile,
			bookmarktype=Directory,
			autosave=signal.fm.settings.autosave_bookmarks)
	bm.load()
	signal.fm.bookmarks = bm

def enter_bookmark(fm, key):
	try:
		destination = fm.bookmarks[key]
		cwd = fm.env.cwd
		if destination.path != cwd.path:
			fm.bookmarks.enter(key)
			fm.bookmarks.remember(cwd)
	except KeyError:
		pass

def unset_bookmark(fm, key):
	"""Delete the bookmark with the name <key>"""
	fm.bookmarks.delete(key)

def set_bookmark(fm, key):
	"""Set the bookmark with the name <key> to the current directory"""
	fm.bookmarks[key] = fm.env.cwd

def __install__(fm):
	def combine(d1, **d2):
		result = d1.copy()
		result.update(d2)
		return result

	rules = {'name': 'bookmarks'}
	fm.signals.register(loop_start, **rules)
	fm.signals.register(terminate, **rules)
	fm.signals.register(initialize, **rules)
	fm.signals.register(draw, **rules)

	fm.functions.register(enter_bookmark)
	fm.functions.register(set_bookmark)
	fm.functions.register(unset_bookmark)

	fm.settings.register('autosave_bookmarks', default=True, type=bool)
