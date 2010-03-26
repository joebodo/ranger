__implements__ = 'mainloop'

def main_loop(signal):
	emit = signal.fm.signal_emit

	try:
		while True:
			emit('base.loop.start')
			emit('base.loop.main')
			emit('base.loop.end')
	except KeyboardInterrupt:
		pass

class Plugin(object):
	def __install__(self):
		self.fm.signal_bind('core.run', main_loop)
