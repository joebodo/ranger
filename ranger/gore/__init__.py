"""Core components"""

def init():
	import ranger

	from .signal import SignalManager
	from .settings import Settings
	from .plugin import PluginManager

	ranger.signal = SignalManager()
	ranger.settings = Settings()
	ranger.plugin = PluginManager()
