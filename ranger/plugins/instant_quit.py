"""
This plugin will quit ranger as soon as the core.run signal is emitted.

Useful for testing purposes.
"""
class Plugin(object):
	def __install__(self, fm):
		fm.signal_bind('base.loop.end', lambda _: exit(), prio=True)
