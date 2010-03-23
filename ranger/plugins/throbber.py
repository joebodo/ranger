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

__license__ = 'GPL3'
__version__ = '1.0.4'
__credits__ = 'Roman Zimbelmann'
__author__ = 'Roman Zimbelmann'
__maintainer__ = 'Roman Zimbelmann'
__email__ = 'romanz@lavabit.com'

def __install__(fm, signals):
	@signals.register('loop_start')
	def throbber_function(signal):
		if hasattr(signal.fm.ui, 'throbber'):
			if signal.fm.loader.has_work():
				signal.fm.ui.throbber(signal.fm.loader.status)
			else:
				signal.fm.ui.throbber(remove=True)
