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
import curses
import _curses

import ranger
from ranger.gui.displayable import DisplayableContainer
from ranger.gui.curses_shortcuts import ascii_only
from ranger.gui.mouse_event import MouseEvent
from ranger.gui.widgets.browserview import BrowserView
from ranger.gui.widgets.titlebar import TitleBar
from ranger.gui.widgets.console import Console
from ranger.gui.widgets.statusbar import StatusBar
from ranger.gui.widgets.taskview import TaskView
from ranger.gui.widgets.pager import Pager
from ranger.models.keymap import CommandArgs

TERMINALS_WITH_TITLE = ("xterm", "xterm-256color", "rxvt",
		"rxvt-256color", "rxvt-unicode", "aterm", "Eterm",
		"screen", "screen-256color")

MOUSEMASK = curses.ALL_MOUSE_EVENTS | curses.REPORT_MOUSE_POSITION

def _setup_mouse(signal):
	if signal['value']:
		curses.mousemask(MOUSEMASK)
		curses.mouseinterval(0)

		## this line solves this problem:
		## If an action, following a mouse click, includes the
		## suspension and re-initializion of the ui (e.g. running a
		## file by clicking on its preview) and the next key is another
		## mouse click, the bstate of this mouse event will be invalid.
		## (atm, invalid bstates are recognized as scroll-down)
		curses.ungetmouse(0,0,0,0,0)
	else:
		curses.mousemask(0)

class UI(DisplayableContainer):
	is_set_up = False
	load_mode = False
	runs = False
	def __init__(self):
		self.fm = ranger.get_fm()
		self._draw_title = os.environ["TERM"] in TERMINALS_WITH_TITLE
		os.environ['ESCDELAY'] = '25'   # don't know a cleaner way

		self.win = curses.initscr()
		self.fm.keymanager.use_context('browser')
		self.fm.keybuffer.clear()
		DisplayableContainer.__init__(self, None)

	def initialize(self):
		"""initialize curses, then call setup (at the first time) and resize."""
		self.runs = True
		self.win.leaveok(0)
		self.win.keypad(1)
		self.load_mode = False

		curses.cbreak()
		curses.noecho()
		curses.halfdelay(20)
#		raise Exception(self.fm.settings.show_cursor)
		try:
			curses.curs_set(int(self.fm.settings.show_cursor))
		except:
			raise
			pass
		curses.start_color()
		curses.use_default_colors()

		self.fm.signal_bind('setopt.mouse_enabled', _setup_mouse)
		_setup_mouse(dict(value=self.fm.settings.mouse_enabled))

		if not self.is_set_up:
			self.is_set_up = True
			self.setup()
		self.update_size()

	def suspend(self):
		"""Turn off curses"""
		self.runs = False
		self.win.keypad(0)
		curses.nocbreak()
		curses.echo()
		try:
			curses.curs_set(1)
		except:
			pass
		try:
			mouse_enabled = self.fm.settings.mouse_enabled
		except:
			pass
		else:
			if mouse_enabled:
				_setup_mouse(dict(value=False))
		curses.endwin()

	def set_load_mode(self, boolean):
		boolean = bool(boolean)
		if boolean != self.load_mode:
			self.load_mode = boolean

			if boolean:
				# don't wait for key presses in the load mode
				curses.cbreak()
				self.win.nodelay(1)
			else:
				self.win.nodelay(0)
				curses.halfdelay(20)

	def destroy(self):
		"""Destroy all widgets and turn off curses"""
		self.suspend()
		try:
			DisplayableContainer.destroy(self)
		except:
			pass

	def handle_mouse(self):
		"""Handles mouse input"""
		try:
			event = MouseEvent(curses.getmouse())
		except _curses.error:
			return
		if not self.console.visible:
			DisplayableContainer.click(self, event)

	def handle_key(self, key):
		"""Handles key input"""

		if hasattr(self, 'hint'):
			self.hint()

		if key < 0:
			self.fm.keybuffer.clear()
			return

		if DisplayableContainer.press(self, key):
			return

		self.status.clear_message()

		self.fm.keymanager.use_context('browser')
		self.fm.key_append(key)
		kbuf = self.fm.keybuffer
		cmd = kbuf.command

		self.browser.draw_hints = False
		self.browser.draw_bookmarks = False

		if kbuf.failure:
			kbuf.clear()
			return
		elif not cmd:
			return

#		self.fm.cmd = cmd

		if cmd.function:
			try:
				cmd.function(CommandArgs.from_widget(self.fm))
			except Exception as error:
				if self.fm.arg.debug:
					raise
				else:
					self.notify(error)
			if kbuf.done:
				kbuf.clear()
		else:
			kbuf.clear()

	def handle_keys(self, *keys):
		for key in keys:
			self.handle_key(key)

	def handle_input(self):
		key = self.win.getch()
		if key is 27 or key >= 128 and key < 256:
			# Handle special keys like ALT+X or unicode here:
			keys = [key]
			previous_load_mode = self.load_mode
			self.set_load_mode(True)
			for n in range(4):
				getkey = self.win.getch()
				if getkey is not -1:
					keys.append(getkey)
			if len(keys) == 1:
				keys.append(-1)
			if self.fm.settings.xterm_alt_key:
				if len(keys) == 2 and keys[1] in range(127, 256):
					keys = [27, keys[1] - 128]
			self.handle_keys(*keys)
			self.set_load_mode(previous_load_mode)
			if self.fm.settings.flushinput and not self.console.visible:
				curses.flushinp()
		else:
			# Handle simple key presses, CTRL+X, etc here:
			if key > 0:
				if self.fm.settings.flushinput and not self.console.visible:
					curses.flushinp()
				if key == curses.KEY_MOUSE:
					self.handle_mouse()
				elif key == curses.KEY_RESIZE:
					self.update_size()
				else:
					if not self.fm.input_is_blocked():
						self.handle_key(key)

	def setup(self):
		"""Build up the UI by initializing widgets."""
		# Create a title bar
		self.titlebar = TitleBar(self.win)
		self.add_child(self.titlebar)

		# Create the browser view
		self.browser = BrowserView(self.win, self.fm.settings.column_ratios)
		self.fm.signal_bind('setopt.column_ratios',
				self.browser.change_ratios)
		self.add_child(self.browser)

		# Create the process manager
		self.taskview = TaskView(self.win)
		self.taskview.visible = False
		self.add_child(self.taskview)

		# Create the status bar
		self.status = StatusBar(self.win, self.browser.main_column)
		self.add_child(self.status)

		# Create the console
		self.console = Console(self.win)
		self.add_child(self.console)
		self.console.visible = False

		# Create the pager
		self.pager = Pager(self.win)
		self.pager.visible = False
		self.add_child(self.pager)

		self.fm.signal_emit('ui.setup')

	def redraw(self):
		"""Redraw all widgets"""
		self.poke()
		self.draw()
		self.finalize()

	def redraw_window(self):
		"""Redraw the window. This only calls self.win.redrawwin()."""
		self.win.erase()
		self.win.redrawwin()
		self.win.refresh()
		self.win.redrawwin()
		self.need_redraw = True

	def notify(self, *a, **k):
		try:
			return self.status.notify(*a, **k)
		except AttributeError:
			raise Exception(' | '.join(repr(b) for b in a))

	def update_size(self):
		"""resize all widgets"""
		y, x = self.win.getmaxyx()
		self.fm.termsize = y, x

		self.browser.resize(1, 0, y - 2, x)
		self.taskview.resize(1, 0, y - 2, x)
		self.pager.resize(1, 0, y - 2, x)
		self.titlebar.resize(0, 0, 1, x)
		self.status.resize(y - 1, 0, 1, x)
		self.console.resize(y - 1, 0, 1, x)

	def draw(self):
		"""Draw all objects in the container"""
		self.win.touchwin()
		DisplayableContainer.draw(self)
		if self._draw_title and self.fm.settings.update_title:
			cwd = self.fm.tab.cwd.path
			if cwd.startswith(self.fm.home_path):
				cwd = '~' + cwd[len(self.fm.home_path):]
			if self.fm.settings.shorten_title:
				split = cwd.rsplit(os.sep, self.fm.settings.shorten_title)
				if os.sep in split[0]:
					cwd = os.sep.join(split[1:])
			try:
				sys.stdout.write("\033]2;ranger:" + cwd + "\007")
			except UnicodeEncodeError:
				sys.stdout.write("\033]2;ranger:" + ascii_only(cwd) + "\007")
		self.win.refresh()

	def finalize(self):
		"""Finalize every object in container and refresh the window"""
		DisplayableContainer.finalize(self)
		self.win.refresh()


	def close_pager(self):
		if self.console.visible:
			self.console.focused = True
		self.pager.close()
		self.pager.visible = False
		self.pager.focused = False
		self.browser.visible = True

	def open_pager(self):
		if self.console.focused:
			self.console.focused = False
		self.pager.open()
		self.pager.visible = True
		self.pager.focused = True
		self.browser.visible = False
		return self.pager

	def open_embedded_pager(self):
		self.browser.open_pager()
		return self.browser.pager

	def close_embedded_pager(self):
		self.browser.close_pager()

	def open_console(self, string='', prompt=None, position=None):
		if self.console.open(string, prompt=prompt, position=position):
			self.status.msg = None
			self.console.on_close = self.close_console
			self.console.visible = True
			self.status.visible = False

	def close_console(self):
		self.console.visible = False
		self.status.visible = True
		self.close_pager()

	def open_taskview(self):
		self.pager.close()
		self.pager.visible = False
		self.pager.focused = False
		self.console.visible = False
		self.browser.visible = False
		self.taskview.visible = True
		self.taskview.focused = True

	def redraw_main_column(self):
		self.browser.main_column.need_redraw = True

	def close_taskview(self):
		self.taskview.visible = False
		self.browser.visible = True
		self.taskview.focused = False

	def scroll(self, relative):
		if self.browser and self.browser.main_column:
			self.browser.main_column.scroll(relative)

	def throbber(self, string='.', remove=False):
		if remove:
			self.titlebar.throbber = type(self.titlebar).throbber
		else:
			self.titlebar.throbber = string

	def hint(self, text=None):
		self.status.hint = text
