import curses

class Plugin(object):
	__requires__ = 'ncurses'
	__implements__ = 'key_fetcher'
	def __install__(self):
		fm = self.fm
		fm.signal_bind('base.loop.main', self.getkey)

	def getkey(self):
		win = self.fm.lib.ncurses.win
		key = win.getch()
		self.fm.signal_emit('base.ncurses.getch', key=key)
		if key == ord('d'):
			self.fm.feature_deactivate('ncurses_mouse_handling')
		elif key == ord('f'):
			self.fm.feature_activate('ncurses_mouse_handling')
