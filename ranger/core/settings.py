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

from inspect import isfunction
import ranger

BAD_SETTING_NAMES = ('register', )
BAD_SETTING_STARTS = '0123456789_'
ALLOWED_SETTINGS = {
	'plugins': (tuple, list),
}

class Undefined(object):
	pass

def is_valid_setting_name(string):
	return string not in BAD_SETTING_NAMES \
			and string[0] not in BAD_SETTING_STARTS

def _check_type(name, typ, value):
	if isfunction(typ):
		assert typ(value), \
			"The option `" + name + "' has an incorrect type!"
	else:
		assert isinstance(value, typ), \
			"The option `" + name + "' has an incorrect type!"\
			" Got " + str(type(value)) + ", expected " + str(typ) + "!"
	return True

def _get_config_files():
	try:
		from ranger.defaults import options as default
	except ImportError:
		default = None
	try:
		import options as custom
	except ImportError:
		custom = None
	return default, custom

class Settings(object):
	CHANGE = 'core.settings.change'

	def __init__(self, config_files=None):
		self._default, self._custom = config_files or _get_config_files()
		self._data = {}
		self._types = {}
		for name, type in ALLOWED_SETTINGS.items():
			self.register(name=name, type=type)
		self._allowed_settings = ALLOWED_SETTINGS.copy()

	def register(self, name, type=Undefined, default=Undefined):
		assert is_valid_setting_name(name), \
			'{0} is no valid setting name!'.format(name)
		try:
			value = getattr(self._custom, name)
		except AttributeError:
			try:
				value = getattr(self._default, name)
			except AttributeError:
				if default is Undefined:
					raise Exception("No default value for option `{0}' "\
							"was specified!".format(name))
				else:
					value = default
		if type is not Undefined:
			self._types[name] = type
			assert _check_type(name, type, value)
		self._data[name] = value
		ranger.signal.register(Settings.CHANGE, self._raw_update_setting,
				prio=0.1)

	def __getattr__(self, name):
		assert name in self._data, "No such setting: {0}!".format(name)
		return self._data[name]

	def _raw_update_setting(self, signal):
		self._data[signal.setting] = signal.value

	def __setattr__(self, name, value):
		if name[0] == '_':
			self.__dict__[name] = value
		else:
			assert name in self._data, "No such setting: {0}!".format(name)
			signal = ranger.signal.emit(Settings.CHANGE, \
				setting=name, value=value, previous=self._data[name])

	__getitem__ = __getattr__
	__setitem__ = __setattr__
