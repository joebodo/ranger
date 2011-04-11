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
from ranger.ext.signals import SignalDispatcher
import re

_LIST_RE = re.compile('[, ]+')

# -=- Functions to Parse Options -=-
def _bool(string):
	return string not in ('false', 'False', '0')

def _int(string):
	return int(string)

def _re(string):
	return re.compile(string)

def _re_I(string):
	return re.compile(string, re.I)

def _colorscheme(string):
	pass

def _tuple_int(string):
	return tuple(int(i) for i in _LIST_RE.split(string))

# -=- Initial Database -=-
# Format: setting_name => (converter_function, raw_default_value)
# The initial value of a setting will be converter_function(raw_default_value)
DEFAULT_SETTINGS = {
	'autosave_bookmarks': (_bool, 'True'),
	'collapse_preview': (_bool, 'True'),
	'colorscheme': (_colorscheme, 'default'),
	'column_ratios': (_tuple_int, '1, 1, 4, 3'),
	'dirname_in_tabs': (_bool, 'False'),
	'display_size_in_main_column': (_bool, 'True'),
	'display_size_in_status_bar': (_bool, 'False'),
	'draw_bookmark_borders': (_bool, 'True'),
	'draw_borders': (_bool, 'False'),
	'file_launcher': (str, 'vim'),
	'flushinput': (_bool, 'True'),
	'hidden_filter': (_re, r"^\.|(pyc|pyo|bak|swp)$|^lost\+found$|^__cache__$"),
	'max_console_history_size': (_int, '200'),
	'max_history_size': (_int, '40'),
	'mouse_enabled': (_bool, 'True'),
	'padding_right': (_bool, 'True'),
	'preview_directories': (_bool, 'True'),
	'preview_files': (_bool, 'True'),
	'preview_script': (str, ''),
	'save_console_history': (_bool, 'True'),
	'scroll_offset': (_int, '8'),
	'shorten_title': (_int, '3'),
	'show_cursor': (_bool, 'False'),
	'show_hidden_bookmarks': (_bool, 'True'),
	'show_hidden': (_bool, 'False'),
	'sort_case_insensitive': (_bool, 'False'),
	'sort_directories_first': (_bool, 'True'),
	'sort_reverse': (_bool, 'False'),
	'sort': (str, 'basename'),
	'syntax_highlighting': (_bool, 'True'),
	'tilde_in_titlebar': (_bool, 'True'),
	'update_title': (_bool, 'True'),
	'unicode_ellipsis': (_bool, 'False'),
	'use_preview_script': (_bool, 'True'),
	'xterm_alt_key': (_bool, 'False'),
}

# -=- Setting Container -=-
class Settings(object):
	"""
	Read-only proxy for fm.variables that converts setting-variables
	to a directly usable format
	"""
	def __init__(self, signal_dispatcher):
		self.__dict__['_data'] = {}
		for key, data in DEFAULT_SETTINGS.items():
			self.__dict__['_data'][key] = data[0](data[1])
		for name in DEFAULT_SETTINGS:
			signal_dispatcher.signal_bind('setopt.'+name,
					self._raw_set_with_signal, priority=0.2)

	def _raw_set(self, name, value):
		self.__dict__['_data'][name] = value

	def _raw_set_with_signal(self, signal):
		self.__dict__['_data'][signal.key] = signal.value

	def __getattr__(self, name):
		return self.__dict__['_data'][name]
	__getitem__ = __getattr__

	def __setattr__(self, name, value):
		raise ValueError("Settings are readonly! Change the "
			"underlying variable instead!")

	def _signal_handler(self, sig):
		try:
			previous = self.__dict__['_data'][sig.key]
			try:
				value = DEFAULT_SETTINGS[sig.key][0](sig.value)
			except:
				# Invalid value for this setting!  Set back to previous value.
				raise
				sig.value = sig.previous
			else:
				import ranger
				sig.origin.signal_emit('setopt.'+sig.key, key=sig.key,
						value=value, previous=previous)
#				ranger.LOG('Setting %s to %s' % (sig.key, self.__dict__['_data'][sig.key]))
		except KeyError:
			pass
