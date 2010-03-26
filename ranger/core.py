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
The core of ranger
"""

import os
import sys
from collections import deque
from ranger.ext.openstruct import OpenStruct
from ranger import *

# ---------------------------
# --- Exceptions
# ---------------------------

class MissingFeature(Exception): pass
class DependencyCycle(Exception): pass
class FeatureAlreadyExists(Exception): pass


# ---------------------------
# --- Helper Classes
# ---------------------------

class Signal(dict):
	def __init__(self, fm, name, handlers, keywords):
		dict.__init__(self, keywords)
		self.__dict__ = keywords
		self.propagation_order = handlers
		self.fm = fm
		self.name = name
		self.stopped = False

	def propagate(self):
		for handler in self.propagation_order:
			handler.function(self)
			if self.stopped:
				break

	def stop(self):
		self.stopped = True


class SignalHandler(dict):
	prio = 0.5
	def __init__(self, fm, signal_name, function, rules):
		dict.__init__(self, rules)
		self.__dict__ = rules
		self.fm = fm
		if self.prio < 0: self.prio = 0
		elif self.prio > 1: self.prio = 1
		self.signal_name = signal_name
		self.function = function

	def remove(self):
		self.fm.signal_unbind(self)


class Plugin(dict):
	def __init__(self, fm, name, attributes):
		dict.__init__(self, attributes)
		self.__dict__ = self
		self.fm = fm
		self.name = name
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

	def implement_feature(self, name, force=False):  #wrapper
		self.fm.plugins.implement_feature(name, self, force=force)


# ---------------------------
# --- Constants
# ---------------------------

RANGERDIR = os.path.dirname(__file__)
PLUGIN_ATTR_STRINGS = ('version', 'author', 'credits', 'license', 'maintainer',
		'copyright', 'email', 'maintainer')
PLUGIN_ATTR_METHODS = ('install', 'activate', 'deactivate')
PLUGIN_ATTR_SETS = ('dependencies', 'requires', 'implements')
PLUGIN_ATTR_ALL = PLUGIN_ATTR_STRINGS + PLUGIN_ATTR_METHODS + PLUGIN_ATTR_SETS
SIGNALS_SORTED = 0
SIGNAL_HANDLERS = 1

def DummyFM():
	fm = FM()
	fm.args = OpenStruct(cd_after_exit=False,
			debug=False, clean=True, confdir=DEFAULT_CONFDIR,
			mode=0, flags='', targets=[])

# ---------------------------
# --- File Manager Class
# ---------------------------


class FM(object):
	def __init__(self):
		self._signals = dict()
		self._plugin_cache = dict()
		self._plugin_load_stack = list()
		self._loaded_plugins = list()
		self._loaded_features = dict()
		self._excluded_plugins = set()
		self._excluded_features = set()
		self._log = deque(maxlen=50)

	def log(self, obj):
		self._log.append(obj)

	def relpath(self, *paths):
		"""returns the path relative to rangers library directory"""
		return os.path.join(RANGERDIR, *paths)

	def confpath(self, *paths):
		if self.args.clean:
			assert 0, "Should not access relpath_conf in clean mode!"
		else:
			return os.path.join(self.args.confdir, *paths)

	# --------------------------------
	# --- Settings stuff
	# --------------------------------

	# --------------------------------
	# --- Signal stuff
	# --------------------------------

	def emit_signal(self):
		pass

	def _signal_sort(self, handlers):
		return sorted(handlers, key=lambda handler: -handler.prio)

	def signal_clear(self):
		self._signals = dict()

	def signal_bind(self, signal_name, function, **rules):
		assert isinstance(signal_name, str)
		try:
			entry = self._signals[signal_name]
		except:
			entry = (False, [])
			self._signals[signal_name] = entry
		else:
			entry[SIGNALS_SORTED] = False
		handler = SignalHandler(fm, signal_name, function, rules)
		entry[SIGNAL_HANDLERS].append(handler)
		return handler

	def signal_unbind(self, signal_handler):
		try:
			handlers = self._signals[signal_handler.signal_name][1]
		except KeyError:
			pass

	def signal_emit(self, signal_name, vital=False, **kw):
		assert isinstance(signal_name, str)
		assert isinstance(vital, bool)
		try:
			entry = self._signals[signal_name]
		except:
			return
		handlers = entry[SIGNAL_HANDLERS]
		if not handlers:
			return

		if not entry[SIGNALS_SORTED]:
			handlers = self._sort(handlers)
			entry[SIGNAL_HANDLERS] = handlers
			entry[SIGNALS_SORTED] = True

		signal = Signal(fm, signal_name, handlers, kw)
		try:
			signal.propagate()
		except Exception as e:
			if vital:
				raise
			else:
				self.log(e)

	# --------------------------------
	# --- Plugin stuff
	# --------------------------------

	def _name_to_plugin(self, name):
		from ranger import relpath, relpath_conf
		assert isinstance(name, str), 'Plugin names must be strings!'
		assert '.' not in name, 'Specify plugin names without the extension!'
		if exists(relpath_conf('plugins', name + '.py')):
			modulepath = 'plugins'
		elif exists(relpath('plugins', name + '.py')):
			modulepath = 'ranger.plugins'
		raise Exception('Plugin not found!')

		module = getattr(__import__(_find_plugin(name), fromlist=[name]), name)
		return Plugin(name, module, self)

	def plugin_find(self, name):
		try:
			return self._plugins_cache[name]
		except KeyError:
			plg = self._name_to_plugin(name)
			self._plugins_cache[name] = plg
			return plg

	def plugin_allow(self, *names):
		self._excluded_plugins.difference_update(names)

	def plugin_forbid(self, *names):
		self._excluded_plugins.update(names)

	def feature_allow(self, *names):
		self._excluded_features.difference_update(names)

	def feature_forbid(self, *names):
		self._excluded_features.update(names)

	def feature_implement(self, name, plugin, force=False):
		if not force and name in self._loaded_features \
				or name in self._excluded_features:
			raise FeatureAlreadyExists(name)
		self._loaded_features[name] = plugin

	def plugin_install(self, name, force=False):
		if name in self._loaded_plugins:
			return  # already installed
		if force:
			plg = self.plugin_find(name)
		else:
			if name in self._excluded_plugins:
				return  # this plugin is excluded
			plg = self.plugin_find(name)
			if plg.implements.intersection(self._loaded_features):
				return  # this plugin implements existing features
			if plg.implements & self._excluded_features:
				return  # this plugin implements excluded features

		if name in self._plugin_load_stack:  # detect dependency cycles
			err, self._plugin_load_stack = self._plugin_load_stack, []
			raise DependencyCycle(err + [name])

		self._plugin_load_stack.append(name)

		for dep in plg.dependencies:  # install dependencies
			if dep not in self._loaded_plugins:
				self.plugin_install(dep)

		missing_features = plg.requires.difference(self._loaded_features)
		if missing_features:  # check if there are missing features
			stack, self._plugin_load_stack = self._plugin_load_stack, []
			raise MissingFeature(name, missing_features, stack)

		if plg.install: plg.install()
		for feature in plg.implements:
			self.feature_implement(feature, plg, force=force)
		self._loaded_plugins.append(name)
		self._plugin_load_stack.pop()
