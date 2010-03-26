import curses

from ranger.gui.mouse_event import MouseEvent

__requires__ = ['ncurses']
__implements__ = ['ncurses_mouse_handling']

MOUSEMASK = curses.ALL_MOUSE_EVENTS | curses.REPORT_MOUSE_POSITION

class Plugin(object):
	def __activate__(self):
		curses.mousemask(MOUSEMASK)
		curses.mouseinterval(0)

		## this line solves this problem:
		## If an action, following a mouse click, includes the
		## suspension and re-initializion of the ui (e.g. running a
		## file by clicking on its preview) and the next key is another
		## mouse click, the bstate of this mouse event will be invalid.
		## (atm, invalid bstates are recognized as scroll-down)
		curses.ungetmouse(0,0,0,0,0)
		self.listener.active = True

	def __deactivate__(self):
		curses.mousemask(0)
		self.listener.active = False

	def dostuff(self, signal):
		if signal.key != curses.KEY_MOUSE:
			return

		event = MouseEvent(curses.getmouse())
		self.fm.lib.ncurses.win.addstr(str(event.bstate))
		signal.stop()

	def update(self, signal):
		if signal.value:
			self.__activate__()
		else:
			self.__deactivate__()

	def __install__(self):
		fm = self.fm
		fm.signal_bind('base.ncurses.activate', self.__activate__)
		fm.signal_bind('base.ncurses.deactivate', self.__deactivate__)
		fm.setting_add('mouse', True, bool)
		fm.signal_bind('core.setting.mouse.change', self.update)

		self.listener = fm.signal_bind('base.ncurses.getch',
				self.dostuff, prio=0.6)
