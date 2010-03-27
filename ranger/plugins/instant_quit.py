"""
This plugin will quit ranger as soon as the core.run signal is emitted.

Useful for testing purposes.
"""
class Plugin(object):
	def __install__(self):
		self.fm.signal_bind('base.loop.end', lambda: quit(), prio=True)
		def stats():
			print("Loaded plugins: {0}".format(
				', '.join(self.fm._loaded_plugins)))
		self.fm.signal_bind('core.quit', stats)
