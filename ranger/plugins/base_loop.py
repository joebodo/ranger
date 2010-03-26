

def main_loop(signal):
	emit = signal.fm.signal_emit

	try:
		while True:
			emit('base.loop.start')
			emit('base.loop.middle')
			emit('base.loop.end')
	except KeyboardInterrupt:
		pass

def __install__(self, fm):
	fm.signal_bind('core.run', main_loop)
