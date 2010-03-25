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
from inspect import getargspec, isfunction, ismethod
from types import MethodType

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

class MissingFeature(Exception):
	pass

class DependencyCycle(Exception):
	pass

class FeatureAlreadyExists(Exception):
	pass

class Plugin(object):
	_strings = ('version', 'author', 'credits', 'license', 'maintainer',
			'copyright', 'email', 'maintainer')
	_fncs = ('install', 'activate', 'deactivate')
	_sets = ('dependencies', 'requires', 'implements')
	_attrs = _strings + _fncs + _sets

	def __init__(self, name, module, plugin_manager):
		self.name = name
		self._plugin_manager = plugin_manager
		for attr in Plugin._attrs:
			try: value = getattr(module, '__'+attr+'__')
			except: value = None
			if attr in Plugin._sets:
				if value is None:
					value = set()
				elif isinstance(value, str):
					value = set([value])
				elif isinstance(value, (set, list, tuple)):
					value = set(value)
			elif attr in Plugin._fncs:
				if isfunction(value):
					value = MethodType(value, self)
				else:
					value = None # XXX
			else:  # must be in _strings now...
				if value is None:
					value = ""
				elif not isinstance(value, str):
					try: value = str(value)
					except: value = None
			self.__dict__[attr] = value

	def implement_feature(self, name, force=False):
		self._plugin_manager.implement_feature(name, self, force=force)


class PluginManager(object):
	def __init__(self):
		self._plugins_cache = dict()
		self.plugins = []
		self.features = dict()
		self.load_order = []
		self.excluded_plugins = set()
		self.excluded_features = set()

	def __getitem__(self, name):
		try:
			return self._plugins_cache[name]
		except KeyError:
			plg = Plugin(name, _name_to_module(name), self)
			self._plugins_cache[name] = plg
			return plg

#	def multi_install(self, *names):
#		for name in names:
#			assert isinstance(name, str), "Plugin names must be strings!"
#			if name[0] == '!':
#				self.excluded_plugins.add(name[1:])
#				continue
#			if name[0] == '~':
#				self.excluded_features.add(name[1:])
#				continue
#			try:
#				self.install(name)
#			except MissingFeature as e:
#				print("Error: The plugin `{0}' requires the " \
#					"features: {1}.\nPlease edit your configuration" \
#					" file and add a plugin that\nimplements this " \
#					"feature!\nStack: {2}" \
#					.format(e[0], ', '.join(e[1]), ' -> '.join(e[2])))
#				raise SystemExit
#			except DependencyCycle as e:
#				print("Error: Dependency cycle encountered!\nStack: {0}" \
#						.format(' -> '.join(e[0])))
#				raise SystemExit

	def reset(self):
		self.__init__()

	def exclude_plugins(self, *names):
		self.excluded_plugins.update(set(names))

	def exclude_features(self, *names):
		self.excluded_features.update(set(names))

	def implement_feature(self, name, plugin, force=False):
		if not force and name in self.features:
			raise FeatureAlreadyExists(name)
		self.features[name] = plugin

	def install(self, name, force=False):
		if name in self.plugins:
			return  # already installed
		if not force and name in self.excluded_plugins:
			return  # this plugin is excluded
		plg = self[name]
		if not force and plg.implements & set(self.features):
			return  # this plugin implements already existing features

		if name in self.load_order:  # detect dependency cycles
			load_order, self.load_order = self.load_order, []
			raise DependencyCycle(load_order + [name])

		self.load_order.append(name)

		for dep in plg.dependencies:  # install dependencies
			if dep not in self.plugins:
				self.install(dep)

		missing_features = plg.requires - set(self.features)
		if missing_features:  # check if there are missing features
			load_order, self.load_order = self.load_order, []
			raise MissingFeature(name, missing_features, load_order)

		if plg.install: plg.install()
		for feature in plg.implements:
			self.implement_feature(feature, plg, force=force)
		self.plugins.append(name)
		self.load_order.pop()
