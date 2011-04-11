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
		if not ranger.NODEFAULTS:
			self._load_plugins_from(ranger.relpath('config'))
		if not self.arg.clean:
			self._load_plugins_from(ranger.confpath())

	def _load_plugins_from(self, directory):
		for _, _, filenames in os.walk(directory):
			for fname in filenames:
				fname = os.sep.join([directory, fname])
				if fname.endswith('.py') and os.access(fname, os.R_OK):
					try:
						execfile(fname)
					except:
						# TODO: deal with errors in plugins
						pass
			break
