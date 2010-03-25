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

"""
Specification for plugins:

fm.functions: semi global functions which can be registered from
inside your plugin so they are accessible outside, for example so you
can assign keybindings to them or call them from other modules.
Avoid dependencies though!


fm.signals: 
"""

import ranger
from ranger import relpath, relpath_conf
from os.path import exists
from inspect import getargspec

DEPENDENCIES = '__dependencies__'
REQ_FEATURES = '__required_features__'
IMP_FEATURES = '__implements__'


def _find_plugin(name):
	assert isinstance(name, str), 'Plugin names must be strings!'
	assert '.' not in name, 'Specify plugin names without the extension!'
	if exists(relpath_conf('plugins', name + '.py')):
		return 'plugins'
	elif exists(relpath('plugins', name + '.py')):
		return 'ranger.plugins'
	raise Exception('Plugin not found!')

def _name_to_module(name):
	return getattr(__import__(_find_plugin(name), fromlist=[name]), name)

def _get_safely(module, name):
	try:
		value = getattr(module, name)
	except:
		return set()
	if isinstance(value, (set, list, tuple)):
		return set(value)
	else:
		return set([value])

class MissingFeature(Exception):
	pass

class DependencyCycle(Exception):
	pass

class PluginManager(object):
	_install_keywords = {}

	def __init__(self):
		self.plugins = []
		self.features = set()
		self.load_order = []
		self.excluded_plugins = set()
		self.excluded_features = set()

	def install(self, *names):
		for name in names:
			assert isinstance(name, str), "Plugin names must be strings!"
			if name[0] == '!':
				self.excluded_plugins.add(name[1:])
				continue
			if name[0] == '~':
				self.excluded_features.add(name[1:])
				continue
			try:
				self.raw_install(name)
			except MissingFeature as e:
				print("Error: The plugin `{0}' requires the " \
					"features: {1}.\nPlease edit your configuration" \
					" file and add a plugin that\nimplements this " \
					"feature!\nStack: {2}" \
					.format(e[0], ', '.join(e[1]), ' -> '.join(e[2])))
				raise SystemExit
			except DependencyCycle as e:
				print("Error: Dependency cycle encountered!\nStack: {0}" \
						.format(' -> '.join(e[0])))
				raise SystemExit

	def reset(self):
		self.__init__()

	def exclude_plugins(self, *names):
		self.excluded_plugins.update(set(names))

	def exclude_features(self, *names):
		self.excluded_features.update(set(names))

	def raw_install(self, name):
		name = name.replace('.', '_')
		if name in self.plugins:
			return  # already installed
		if name in self.load_order:
			load_order, self.load_order = self.load_order, []
			raise DependencyCycle(load_order + [name])
		self.load_order.append(name)
		kw = self._install_keywords
		module = _name_to_module(name)
		deps = _get_safely(module, DEPENDENCIES)
		reqs = _get_safely(module, REQ_FEATURES)
		for dep in deps:
			if dep not in self.plugins:
				self.raw_install(dep)
		missing_features = reqs - self.features
		if missing_features:
			load_order, self.load_order = self.load_order, []
			raise MissingFeature(name, missing_features, load_order)
		try:
			installfunc = module.__install__
		except:
			pass
		else:
#			required_keywords = dict(  # only pass on the keywords it needs
#					(arg, kw[arg] if arg in kw else None) \
#					for arg in getargspec(installfunc).args)
			installfunc()
		self.features |= _get_safely(module, IMP_FEATURES)
		self.plugins.append(name)
		self.load_order.pop()
