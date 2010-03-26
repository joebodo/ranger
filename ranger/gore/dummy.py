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
Create a clean FM object without any interaction with the outside world.

This is useful for unit tests.
"""


def DummyFM():
	from ranger.core.fm import FM
	from ranger.core.settings import Settings
	from ranger.core.signal import SignalManager
	from ranger.core.plugin import PluginManager
	import ranger

	fm = FM()

#	fm.settings = Settings(fm)
	fm.plugins = PluginManager(fm)
#	fm.signals = SignalManager()
#	fm.env = Environment()

	ranger.debug = True
	ranger.clean = True
	ranger.cd_after_exit = False
	ranger.fm = fm

	return fm
