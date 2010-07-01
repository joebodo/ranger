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
Shared objects contain singleton variables which can be
inherited, essentially acting like global variables.
"""

import mimetypes
import ranger
import sys
from ranger import relpath
from ranger.ext.openstruct import OpenStruct


class Awareness(object):
	"""Base class for shared objects"""


class EnvironmentAware(Awareness):
	env = None
	@staticmethod
	def _assign(instance):
		EnvironmentAware.env = instance


class FileManagerAware(Awareness):
	fm = None
	@staticmethod
	def _assign(instance):
		FileManagerAware.fm = instance


class MimeTypeAware(Awareness):
	mimetypes = {}
	def __init__(self):
		MimeTypeAware.__init__ = lambda _: None  # refuse multiple inits
		MimeTypeAware.mimetypes = mimetypes.MimeTypes()
		MimeTypeAware.mimetypes.read(relpath('data/mime.types'))

class SettingsAware(Awareness):
	settings = OpenStruct()
	@staticmethod
	def _setup():
		from ranger.gui.colorscheme import _colorscheme_name_to_class
		from ranger.container.settings import SettingObject
		settings = SettingObject()
		settings.signal_bind('setopt.colorscheme',
				_colorscheme_name_to_class, priority=1)
		SettingsAware.settings = settings
