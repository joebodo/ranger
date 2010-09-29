#!/usr/bin/python -O
# -*- coding: utf-8 -*-
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

# Embed a script which allows you to change the directory of the parent shell
# after you exit ranger.  Run it with the command: source ranger ranger
"""":
if [ $1 ]; then
	$@ --fail-unless-cd &&
	if [ -z "$XDG_CONFIG_HOME" ]; then
		cd "$(grep \^\' ~/.config/ranger/bookmarks | cut -b3-)"
	else
		cd "$(grep \^\' "$XDG_CONFIG_HOME"/ranger/bookmarks | cut -b3-)"
	fi
else
	echo "usage: source path/to/ranger.py path/to/ranger.py"
fi
return 1
"""

# When using the --clean option, nothing should be written to the disk,
# not even python byte code.  We need to find out if the clean-option
# is used before we do any importing. (import sys is ok)
import sys
argv = sys.argv
if ('-c' in argv or '--clean' in argv) and ('--' not in argv or
		(('-c' in argv and argv.index('-c') < argv.index('--')) or
		('--clean' in argv and argv.index('--clean') < argv.index('--')))):
	sys.dont_write_bytecode = True

# Set the actual docstring
__doc__ = """Ranger - file browser for the unix terminal"""

# Start ranger
import ranger
sys.exit(ranger.main())
