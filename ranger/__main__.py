#!/usr/bin/python
# coding=utf-8
#
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

import os
import sys


def parse_arguments():
	"""Parse the program arguments"""

	from optparse import OptionParser, SUPPRESS_HELP
	from ranger.ext.openstruct import OpenStruct
	from ranger import __version__, USAGE, DEFAULT_CONFDIR

	parser = OptionParser(usage=USAGE, version='ranger ' + __version__)

	# Instead of using this directly, use the embedded
	# shell script by running ranger with:
	# source /path/to/ranger /path/to/ranger
	parser.add_option('--cd-after-exit',
			action='store_true',
			help=SUPPRESS_HELP)

	parser.add_option('-d', '--debug', action='store_true',
			help="activate debug mode")

	parser.add_option('-c', '--clean', action='store_true',
			help="don't touch/require any config files. ")

	parser.add_option('-r', '--confdir', dest='confdir', type='string',
			default=DEFAULT_CONFDIR,
			help="the configuration directory. (%default)")

	parser.add_option('-m', '--mode', type='int', dest='mode', default=0,
			help="if a filename is supplied, run it with this mode")

	parser.add_option('-f', '--flags', type='string', dest='flags', default='',
			help="if a filename is supplied, run it with these flags.")

	options, positional = parser.parse_args()

	arg = OpenStruct(options.__dict__, targets=positional)

	arg.confdir = os.path.expanduser(arg.confdir)

	if arg.cd_after_exit:
		sys.stderr = sys.__stdout__

	if not arg.clean:
		try:
			os.makedirs(arg.confdir)
		except OSError as err:
			if err.errno != 17:  # 17 means it already exists
				print("This configuration directory could not be created:")
				print(arg.confdir)
				print("To run ranger without the need for configuration files")
				print("use the --clean option.")
				raise SystemExit()

		sys.path.append(arg.confdir)

	return arg


def main():
	from locale import getdefaultlocale, setlocale, LC_ALL
	from ranger.core import FM, SettingWrapper, \
			MissingFeature, DependencyCycle

	# Ensure that a utf8 locale is set.
	if getdefaultlocale()[1] not in ('utf8', 'UTF-8'):
		for locale in ('en_US.utf8', 'en_US.UTF-8'):
			try: setlocale(LC_ALL, locale)
			except: pass
			else: break
		else: setlocale(LC_ALL, '')
	else: setlocale(LC_ALL, '')

	# initialize stuff
	fm = FM()

	args = parse_arguments()
	fm.args = args

	fm._setting_structs = []
	try:
		import options as custom_options
		fm._setting_structs.append(custom_options)
	except ImportError:
		pass
	try:
		from ranger.defaults import options as default_options
		fm._setting_structs.append(default_options)
	except ImportError:
		pass

	# load plugins
	fm.setting_add('plugins', ['base'], (list, tuple))
	for name in fm.settings.plugins:
		assert isinstance(name, str), "Plugin names must be strings!"
		if name[0] == '!':
			fm.plugin_forbid(name[1:])
			continue
		if name[0] == '~':
			fm.feature_forbid(name[1:])
			continue
		try:
			fm.plugin_install(name)
		except MissingFeature as e:
			print("Error: The plugin `{0}' requires the " \
				"features: {1}.\nPlease edit your configuration" \
				" file and add a plugin that\nimplements this " \
				"feature!\nStack: {2}" \
				.format(e[0], ', '.join(e[1]), ' -> '.join(e[2])))
			raise SystemExit
		except DependencyCycle as e:
			print("Error: Dependency cycle encountered!\nStack: {0}" \
					.format(' -> '.join(e[0])))
			raise SystemExit

	# run the shit
	fm.signal_emit('core.all_plugins_loaded')
	fm.signal_emit('core.init', vital=True)
	try:
		fm.signal_emit('core.run')
	finally:
		fm.signal_emit('core.quit')

if __name__ == '__main__':
	top_dir = os.path.dirname(sys.path[0])
	sys.path.insert(0, top_dir)
	main()
