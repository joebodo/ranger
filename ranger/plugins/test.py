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

class Plugin(object):
	__dependencies__ = 'base_env'
	def __install__(self):
		self.fm.signal_bind('base.ncurses.getch', self.printkey)

	def printkey(self, sig):
		lib = self.fm.lib
		win = lib.ncurses.win

		self.fm.lib.ncurses.win.addch(sig.key)

		win.addstr(str(lib.env.cwd) + '\n')
