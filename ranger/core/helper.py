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

"""Helper functions"""

import os.path
import sys
from ranger import *

def load_settings(fm, clean):
	import ranger.core.shared
	import ranger.api.commands
	import ranger.api.keys
	if not clean:
		allow_access_to_confdir(ranger.arg.confdir, True)

		# Load commands
		comcont = ranger.api.commands.CommandContainer()
		ranger.api.commands.alias = comcont.alias
		try:
			import commands
			comcont.load_commands_from_module(commands)
		except ImportError:
			pass
		from ranger.defaults import commands
		comcont.load_commands_from_module(commands)
		commands = comcont

		# Load apps
		try:
			import apps
		except ImportError:
			from ranger.defaults import apps

		# Load keys
		keymanager = ranger.core.shared.EnvironmentAware.env.keymanager
		ranger.api.keys.keymanager = keymanager
		from ranger.defaults import keys
		try:
			import keys
		except ImportError:
			pass
		allow_access_to_confdir(ranger.arg.confdir, False)
	else:
		comcont = ranger.api.commands.CommandContainer()
		ranger.api.commands.alias = comcont.alias
		from ranger.api import keys
		keymanager = ranger.core.shared.EnvironmentAware.env.keymanager
		ranger.api.keys.keymanager = keymanager
		from ranger.defaults import commands, keys, apps
		comcont.load_commands_from_module(commands)
		commands = comcont
	fm.commands = commands
	fm.keys = keys
	fm.apps = apps.CustomApplications()


def load_apps(fm, clean):
	import ranger
	if not clean:
		allow_access_to_confdir(ranger.arg.confdir, True)
		try:
			import apps
		except ImportError:
			from ranger.defaults import apps
		allow_access_to_confdir(ranger.arg.confdir, False)
	else:
		from ranger.defaults import apps
	fm.apps = apps.CustomApplications()
