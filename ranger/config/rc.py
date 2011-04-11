"""
This plugin loads rc.conf and executes its content as commands.
There are two locations for rc.conf:
	1. ~/.config/ranger/rc.conf
	2. ranger/config/rc.conf
"""

import ranger
import os
fm = ranger.get_fm()

load_default_config = True

def load_config(signal):
	global load_default_config
	if not fm.arg.clean:
		conf = fm.confpath('rc.conf')
		if os.access(conf, os.R_OK):
			fm.source_cmdlist(conf)
	if load_default_config:
		conf = fm.relpath('config', 'rc.conf')
		if os.access(conf, os.R_OK):
			fm.source_cmdlist(conf)

fm.signal_bind('initialize', load_config)
