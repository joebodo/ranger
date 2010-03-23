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

class Settings(object):
	def __init__(self, fm):
		try:
			from ranger.defaults import options as defaultoptions
			self._defaultoptions = defaultoptions
		except ImportError:
			self._defaultoptions = None

		try:
			import options as customoptions
			self._customoptions = customoptions
		except ImportError:
			self._customoptions = None

		self._fm = fm
		self._data = {}
		for name, type in ALLOWED_SETTINGS.items():
			self.register(name=name, type=type)
		self._allowed_settings = ALLOWED_SETTINGS.copy()
		from ranger.gui.colorscheme import ColorScheme
		self.colorscheme = ColorScheme()

		try: import apps
		except ImportError: from ranger.defaults import apps
		self.register(name='apps', default=apps)
		try: import keys
		except ImportError: from ranger.defaults import keys
		self.register(name='keys', default=keys)

	def register(self, name, type=Ellipsis, default=Ellipsis):
		assert is_valid_setting_name(name), \
			'{0} is no valid setting name!'.format(name)
		try:
			value = getattr(self._customoptions, name)
		except AttributeError:
			try:
				value = getattr(self._defaultoptions, name)
			except AttributeError:
				if default is Ellipsis:
					raise Exception("No default value for option `{0}' "\
							"was specified!".format(name))
				else:
					value = default
		assert _check_type(name, type, value) if type != Ellipsis else 1
		self._data[name] = value

	def __getattr__(self, name):
		assert name in self._data, "No such setting: {0}!".format(name)
		return self._data[name]

	def __setattr__(self, name, value):
		if name[0] == '_':
			self.__dict__[name] = value
		else:
			assert name in self._data, "No such setting: {0}!".format(name)
			self._fm.emit('change_setting', \
				setting=name, value=value, previous=self._data[name])
			self._data[name] = value

	__getitem__ = __getattr__
	__setitem__ = __setattr__

BAD_SETTING_NAMES = ('register', )
BAD_SETTING_STARTS = '0123456789_'
ALLOWED_SETTINGS = {
	'plugins': (tuple, list),
	'show_hidden': bool,
	'show_cursor': bool,
	'collapse_preview': bool,
	'draw_borders': bool,
	'sort': str,
	'reverse': bool,
	'directories_first': bool,
	'update_title': bool,
	'shorten_title': int,
	'max_filesize_for_preview': (int, type(None)),
	'max_history_size': (int, type(None)),
	'scroll_offset': int,
	'preview_files': bool,
	'preview_directories': bool,
	'flushinput': bool,
	'colorscheme': str,
	'hidden_filter': lambda obj: hasattr(obj, 'match'),
}

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
