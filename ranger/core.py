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
from types import MethodType
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
		self.prio = min(0, max(1, self.prio))
		self.signal_name = signal_name
		self.function = function

	def remove(self):
		self.fm.signal_unbind(self)


class Plugin(dict):
	def __init__(self, fm, name, module):
#		dict.__init__(self, attributes)
#		self.__dict__ = self
		self.fm = fm
		self.name = name
		for attr in PLUGIN_ATTR_ALL:
			try: value = getattr(module, '__'+attr+'__')
			except: value = None
			if attr in PLUGIN_ATTR_SETS:
				if value is None:
					value = set()
				elif isinstance(value, str):
					value = set([value])
				elif isinstance(value, (set, list, tuple)):
					value = set(value)
			elif attr in PLUGIN_ATTR_METHODS:
				if hasattr(value, '__call__'):
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


class SettingWrapper(object):
	def __init__(self, fm):
		self._fm = fm
		self._settings = fm._settings

	def __setattr__(self, name, value):
		if name[0] == '_':
			self.__dict__[name] = value
		else:
			assert name in self._settings, "No such setting: {0}!".format(name)
			signal = ranger.signal.emit(SETTING_CHANGE_SIGNAL, \
				setting=name, value=value, previous=self._settings[name])

	def __getattr__(self, name):
		assert name in self._settings, "No such setting: {0}!".format(name)
		return self._settings[name]

	__getitem__ = __getattr__
	__setitem__ = __setattr__

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
BAD_SETTING_NAMES = ('register', )
BAD_SETTING_STARTS = tuple('0123456789_')
SETTING_CHANGE_SIGNAL = 'core.settingchange'

def DummyFM():
	fm = FM()
	fm.args = OpenStruct(cd_after_exit=False,
			debug=False, clean=True, confdir=DEFAULT_CONFDIR,
			mode=0, flags='', targets=[])

def main():
	from locale import getdefaultlocale, setlocale, LC_ALL
	from ranger.__main__ import parse_arguments

	# Ensure that a utf8 locale is set.
	if getdefaultlocale()[1] not in ('utf8', 'UTF-8'):
		for locale in ('en_US.utf8', 'en_US.UTF-8'):
			try: setlocale(LC_ALL, locale)
			except: pass
			else: break
		else: setlocale(LC_ALL, '')
	else: setlocale(LC_ALL, '')

	# initialize stuff
	fm = FM()

	args = parse_arguments()
	fm.args = args

	fm._setting_structs = []
	try:
		from ranger.defaults import options as default_options
		fm._setting_structs.append(default_options)
	except ImportError:
		pass
	try:
		import options as custom_options
		fm._setting_structs.append(custom_options)
	except ImportError:
		pass

	# load plugins
	fm.settings = SettingWrapper(fm)
	fm.setting_add('plugins', ['base'], (list, tuple))
	for name in fm.settings.plugins:
		assert isinstance(name, str), "Plugin names must be strings!"
		if name[0] == '!':
			fm.plugin_forbid(name[1:])
			continue
		if name[0] == '~':
			fm.feature_forbid(name[1:])
			continue
		try:
			fm.plugin_install(name)
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

	# run the shit
	fm.signal_emit('core.all_plugins_loaded')
	try:
		fm.signal_emit('core.run')
	finally:
		fm.signal_emit('core.quit')


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
		self._setting_structs = list()
		self._settings = dict()
		self._setting_types = dict()

		self.signal_bind(SETTING_CHANGE_SIGNAL,
				self._setting_set_raw_signal, prio=0.1)

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

	def _is_valid_setting_name(self, string):
		return string not in BAD_SETTING_NAMES \
				and string[0] not in BAD_SETTING_STARTS

	def setting_add(self, name, default, type=None):
		assert self._is_valid_setting_name(name), \
			'{0} is no valid setting name!'.format(name)
		value = default
		for struct in self._setting_structs:
			try:
				value = getattr(struct, name)
			except AttributeError:
				pass
		if type is not None:
			self._setting_types[name] = type
#			assert self._check_setting_type(name, type, value)
		self._settings[name] = value

	def _setting_set_raw(self, name, value):
		self._settings[name] = value

	def _check_setting_type(self, name, typ, value):
		if isfunction(typ):
			assert typ(value), \
				"The option `" + name + "' has an incorrect type!"
		else:
			assert isinstance(value, typ), \
				"The option `" + name + "' has an incorrect type!"\
				" Got " + str(type(value)) + ", expected " + str(typ) + "!"
		return True

	def _setting_set_raw_signal(self, signal):
		self._settings[signal.setting] = signal.value

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
			entry = (False, entry[1])
		handler = SignalHandler(self, signal_name, function, rules)
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
			handlers = self._signal_sort(handlers)
			entry = (True, handlers)

		signal = Signal(self, signal_name, handlers, kw)
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
		assert isinstance(name, str), 'Plugin names must be strings!'
		assert '.' not in name, 'Specify plugin names without the extension!'
		if os.path.exists(self.confpath('plugins', name + '.py')):
			modulepath = 'plugins'
		elif os.path.exists(self.relpath('plugins', name + '.py')):
			modulepath = 'ranger.plugins'
		else:
			raise Exception('Plugin not found: ' + name)

		module = getattr(__import__(modulepath, fromlist=[name]), name)
		return Plugin(self, name, module)

	def plugin_find(self, name):
		try:
			return self._plugin_cache[name]
		except KeyError:
			plg = self._name_to_plugin(name)
			self._plugin_cache[name] = plg
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

		if plg.install: plg.install(self)
		for feature in plg.implements:
			self.feature_implement(feature, plg, force=force)
		self._loaded_plugins.append(name)
		self._plugin_load_stack.pop()