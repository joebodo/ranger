# Copyright (C) 2009, 2010  Roman Zimbelmann <romanz@lavabit.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

'''
Every file that ends with .py in your configuration directory (normally
~/.config/ranger/) will be loaded and evaluated as python code. They
may contain any code. But to be recognized as plugins, they should look like
this sample plugin:

	from ranger.pluginsystem import Plugin
	from inspect import cleandoc

	def hello_world():
		fm.display("Hello World")

	@fm.register_plugin_class
	class MyPlugin(Plugin):
		"""This plugin prints "hello world" whenever you press a key."""
		name = 'Hello World'
		version = '1.3.37'
		author = 'foo bar'
		help = cleandoc(__doc__)
		handler = None

		def on_load(self):
			self.handler = self.fm.signal_bind('key.press', hello_world)

		def on_unload(self):
			self.fm.signal_unbind(self.handler)

'''

import ranger
import os
import sys
from ranger.ext.openstruct import OpenStruct as Plugin

class PluginSystem(object):
	def __init__(self):
		self._plugins = {}

	def register_plugin(self, **kw):
		self.register_plugin_class(Plugin(**kw))

	def register_plugin_class(self, cls):
		if hasattr(cls, 'name'):
			self.plugins[cls.name] = cls
		else:
			ranger.ERR('Need a name for the plugin!')

	def load_plugins(self):
		# TODO: deal with errors in plugins
		override_path = self.confpath('plugins')
		default_path  = self.relpath('config')
		overrides = [] if self.arg.clean else os.listdir(override_path)
		defaults = [f for f in os.listdir(default_path) if f not in overrides]
		for fname in defaults:
			if fname.endswith('.py'):
				try:
					__import__('ranger.config.' + fname[:-3])
				except:
					pass
		if overrides and os.path.exists(override_path):
			if not os.path.exists(override_path + '/__init__.py'):
				open(override_path + '/__init__.py', 'a').close()
			sys.path[0:0] = [self.confpath()]
			for fname in overrides:
				if fname.endswith('.py'):
					try:
						__import__('plugins.' + fname[:-3])
					except:
						pass
			del sys.path[0]
