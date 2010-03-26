import os
import curses

__implements__ = 'ncurses'

class Plugin(object):
	def initialize(self):
		os.environ['ESCDELAY'] = '25'   # don't know a cleaner way
		self.win = curses.initscr()
		self.fm.lib.register_subdirectory('ncurses')
		self.fm.lib.ncurses.win = self.win
		self.__activate__()

	def __activate__(self):
		self.win.leaveok(0)
		self.win.keypad(1)
		curses.cbreak()
		curses.noecho()
		curses.halfdelay(20)
		try:
			curses.curs_set(int(bool(self.fm.settings.show_cursor)))
		except:
			pass
		curses.start_color()
		curses.use_default_colors()

		self.fm.signal_emit('base.ncurses.activate')

	def __deactivate__(self):
		self.win.keypad(0)
		curses.nocbreak()
		curses.echo()
		try:
			curses.curs_set(1)
		except:
			pass
		self.fm.signal_emit('base.ncurses.deactivate')
		curses.endwin()

	def __install__(self):
		fm = self.fm
		fm.setting_add('show_cursor', True, bool)
		fm.signal_bind('core.init', self.initialize)
		fm.signal_bind('core.quit', self.__deactivate__)
