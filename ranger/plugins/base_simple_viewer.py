import curses

class Plugin(object):
	__requires__ = 'ncurses'

	def __install__(self):
		self.fm.signal_bind('base.loop.main', self.draw)
		self.fm.signal_bind('core.init', self.initialize)

	def initialize(self):
		self.cwd = '.'

	def draw(self):
		win = self.fm.lib.ncurses.win
		env = self.fm.lib.env
		dr = env.get_directory(self.cwd)

		win.addstr('x')
		if dr is None:
			win.addstr("dr is none :/")

		for path in dr:
			try:
				win.addstr(str(path) + '\n')
			except:
				break
