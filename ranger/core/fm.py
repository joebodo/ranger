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
The File Manager, putting the pieces together
"""

from ranger import CLEAN, DEBUG, confpath

from time import time
from collections import deque
import os
import sys

from ranger.core.actions import Actions
from ranger.container import History
from ranger.container.tags import Tags
from ranger.gui.defaultui import DefaultUI
from ranger.container import Bookmarks
from ranger.core.runner import Runner
from ranger.ext.get_executables import get_executables
from ranger.fsobject import Directory
from ranger.ext.signal_dispatcher import SignalDispatcher
from ranger import __version__
from ranger.core.loader import Loader
from ranger.shared import (EnvironmentAware, FileManagerAware,
			SettingsAware)

TICKS_BEFORE_COLLECTING_GARBAGE = 100
TIME_BEFORE_FILE_BECOMES_GARBAGE = 1200

class FM(Actions, SignalDispatcher):
	input_blocked = False
	input_blocked_until = 0
	def __init__(self):
		"""Initialize FM."""
		Actions.__init__(self)
		SignalDispatcher.__init__(self)
		self.log = deque(maxlen=20)
		self.log.append('Ranger {0} started! Process ID is {1}.' \
				.format(__version__, os.getpid()))
		self.log.append('Running on Python ' + sys.version.replace('\n',''))

		self.tabs = {}
		self.current_tab = 1
		self.loader = Loader()

	def setup_environment(self):
		"""
		Create a ranger-friendly environment.

		It should be enough to call this function once, even if you
		run multiple ranger instances.
		"""
		try:
			locale.setlocale(locale.LC_ALL, '')
		except:
			pass
		if not 'SHELL' in os.environ:
			os.environ['SHELL'] = 'bash'

	def initialize(self):
		"""If ui/bookmarks are None, they will be initialized here."""
		SettingsAware._setup()
		if CLEAN:
			bookmarkfile = None
		else:
			bookmarkfile = confpath('bookmarks')
		self.bookmarks = Bookmarks(
				bookmarkfile=bookmarkfile,
				bookmarktype=Directory,
				autosave=False)#self.settings.autosave_bookmarks)
		self.bookmarks.load()

		if not CLEAN:
			self.tags = Tags(confpath('tagged'))

		if self.ui is None:
			self.ui = DefaultUI()
			self.ui.initialize()

		def mylogfunc(text):
			self.notify(text, bad=True)

		self.env.history = History(10, #self.settings.max_history_size,
				unique=False)
		self.env.signal_bind('cd', self._update_current_tab)

	def block_input(self, sec=0):
		self.input_blocked = sec != 0
		self.input_blocked_until = time() + sec

	def input_is_blocked(self):
		if self.input_blocked and time() > self.input_blocked_until:
			self.input_blocked = False
		return self.input_blocked

	def loop(self):
		"""
		The main loop consists of:
		1. reloading bookmarks if outdated
		2. letting the loader work
		3. drawing and finalizing ui
		4. reading and handling user input
		5. after X loops: collecting unused directory objects
		"""

		self.env.enter_dir(self.env.path)

		gc_tick = 0

		# for faster lookup:
		ui = self.ui
		throbber = ui.throbber
		bookmarks = self.bookmarks
		loader = self.loader
		env = self.env
		has_throbber = hasattr(ui, 'throbber')

		try:
			while True:
				bookmarks.update_if_outdated()
				loader.work()
				if has_throbber:
					if loader.has_work():
						throbber(loader.status)
					else:
						throbber(remove=True)

				ui.redraw()

				ui.set_load_mode(loader.has_work())

				ui.handle_input()

				gc_tick += 1
				if gc_tick > TICKS_BEFORE_COLLECTING_GARBAGE:
					gc_tick = 0
					env.garbage_collect(TIME_BEFORE_FILE_BECOMES_GARBAGE)

		except KeyboardInterrupt:
			# this only happens in --debug mode. By default, interrupts
			# are caught in curses_interrupt_handler
			raise SystemExit

		finally:
			bookmarks.remember(env.cwd)
			bookmarks.save()

	def clean_up(self):
		pass
