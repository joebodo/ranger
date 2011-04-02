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

#import curses
#import os
#import pwd
#from os.path import abspath, normpath, join, expanduser, isdir

#from ranger.fsobject import Directory
#from ranger.ext.signals import SignalDispatcher
#from ranger.core.shared import SettingsAware


#class Environment(SettingsAware, SignalDispatcher):
	#"""
	#A collection of data which is relevant for more than one class.
	#"""

	#def __init__(self, path):
		#self.signal_bind('move', self._set_cf_from_signal, priority=0.1,
				#weak=True)

	#def _set_cf_from_signal(self, signal):
		#self._cf = signal.new

	#def _set_cf(self, value):
		#if value is not self._cf:
			#previous = self._cf
			#self.signal_emit('move', previous=previous, new=value)

	#def _get_cf(self):
		#return self._cf

	#cf = property(_get_cf, _set_cf)


