#!/usr/bin/python
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

import optparse
from sys import *

__version__    = '1.0'
__author__     = 'Roman Zimbelmann'
USAGE          = '%prog [options] [filename1 [filename 2...]]'

class OpenStruct(dict):
	"""The fusion of dict and struct"""
	def __init__(self, *__args, **__keywords):
		dict.__init__(self, *__args, **__keywords)
		self.__dict__ = self

def main():
	parser = optparse.OptionParser(usage=USAGE,
			version='lasso ' + __version__)
	parser.add_option('-f', '--overwrite', action='store_true',
			help="overwrite existing files")
	parser.add_option('-m', '--move', action='store_true',
			help="move the files instead of copying")
	parser.add_option('-c', '--copy', action='store_true',
			help="copy the files")
	parser.add_option('-s', '--symlink', action='store_true',
			help="create symlinks with absolute destinations")
	parser.add_option('-l', '--hardlink', action='store_true',
			help="create hardlinks")
	parser.add_option('-L', '--relative-symlink', action='store_true',
			help="create symlinks with relative destinations")
	parser.add_option('-t', '--to', type='string', default='.',
			help="where to put the file(s)", metavar='place')
	named, positional = parser.parse_args(argv)
	args = OpenStruct(named.__dict__, targets=positional)

if __name__ == '__main__':
	main()
