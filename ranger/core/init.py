"""
Import this module to initialize the core.

This is NOT inside the ranger.core.__init__ to allow modifications
of the components before they are initialized.
"""

import ranger

from .signal import SignalManager
from .settings import Settings
from .plugin import PluginManager

ranger.signal = SignalManager()
ranger.settings = Settings()
ranger.plugin = PluginManager()
