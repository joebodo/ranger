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

class PluginSystem(object):
	def __init__(self):
		self._plugins = {}

	def register_plugin(self, name, version, help):
		from inspect import cleandoc
		self.plugins[name] = {'version': version, 'help': cleandoc(help)}

	def load_plugin(self, filename):
		import ranger

		# Get the filename and its content
		content = None
		if '/' not in filename:
			if filename[-3:] != '.py':
				real_filename = self.confpath('plugins', filename+'.py')
			else:
				real_filename = self.confpath('plugins', filename)
			try:
				content = open(real_filename).read()
			except:
				pass
		if not content:
			real_filename = filename
			try:
				content = open(filename).read()
			except:
				return False

		# Set up the environment
		remove_ranger_fm = hasattr(ranger, 'fm')
		ranger.fm = self

		# Compile and execute the code
		code = compile(content, real_filename, 'exec')
		exec(code)

		# Clean up
		if remove_ranger_fm and hasattr(ranger, 'fm'):
			del ranger.fm
