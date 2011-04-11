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

"""Shared objects contain singleton variables which can be
inherited, essentially acting like global variables."""

import os.path

#class SettingsAware(Awareness):
	## This creates an instance implicitly, mainly for unit tests
	#@lazy_property
	#def settings(self):
		#from ranger.ext.openstruct import OpenStruct
		#return OpenStruct()

	#@staticmethod
	#def _setup(clean=True):
		#from ranger.container.settingobject import SettingObject, \
				#ALLOWED_SETTINGS
		#import ranger
		#import sys
		#settings = SettingObject()

		#from ranger.gui.colorscheme import _colorscheme_name_to_class
		#settings.signal_bind('setopt.colorscheme',
				#_colorscheme_name_to_class, priority=1)

		#def after_setting_preview_script(signal):
			#if isinstance(signal.value, str):
				#signal.value = os.path.expanduser(signal.value)
				#if not os.path.exists(signal.value):
					#signal.value = None
		#settings.signal_bind('setopt.preview_script',
				#after_setting_preview_script, priority=1)
		#def after_setting_use_preview_script(signal):
			#if signal.fm.settings.preview_script is None and signal.value:
				#signal.fm.notify("Preview script undefined or not found!",
						#bad=True)
		#settings.signal_bind('setopt.use_preview_script',
				#after_setting_use_preview_script, priority=1)

		#SettingsAware.settings = settings
