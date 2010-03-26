import os
import curses

__implements__ = 'ncurses'
__requires__ = 'mainloop'

MOUSEMASK = curses.ALL_MOUSE_EVENTS | curses.REPORT_MOUSE_POSITION

class Plugin(object):
	def initialize(self):
		os.environ['ESCDELAY'] = '25'   # don't know a cleaner way
		self.win = curses.initscr()
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

		curses.mousemask(MOUSEMASK)
		curses.mouseinterval(0)

		## this line solves this problem:
		## If an action, following a mouse click, includes the
		## suspension and re-initializion of the ui (e.g. running a
		## file by clicking on its preview) and the next key is another
		## mouse click, the bstate of this mouse event will be invalid.
		## (atm, invalid bstates are recognized as scroll-down)
		curses.ungetmouse(0,0,0,0,0)

		#	if not self.is_set_up:
		#		self.is_set_up = True
		#		self.setup()
		#	self.update_size()

	def __deactivate__(self):
		self.win.keypad(0)
		curses.nocbreak()
		curses.echo()
		try:
			curses.curs_set(1)
		except:
			pass
		curses.mousemask(0)
		curses.endwin()

	def do_something(self, signal):
		self.win.addstr('a')
		self.win.refresh()

	def __install__(self):
		fm = self.fm
		fm.setting_add('show_cursor', True, bool)
		fm.signal_bind('core.init', self.initialize)
		fm.signal_bind('core.quit', self.__deactivate__)
		fm.signal_bind('base.loop.main', self.do_something)
