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
The pager displays text and allows you to scroll inside it.
"""
import re
from . import Widget
from ranger.ext.direction import Direction
from ranger.container.keymap import CommandArgs
from ranger.gui.color import get_color
from ranger.gui import ansi

BAR_REGEXP = re.compile(r'\|\d+\?\|')
QUOTES_REGEXP = re.compile(r'"[^"]+?"')
SPECIAL_CHARS_REGEXP = re.compile(r'<\w+>|\^[A-Z]')
TITLE_REGEXP = re.compile(r'^\d+\.')

def is_pil_image(obj):
	try:
		import Image
	except ImportError:
		return False
	else:
		return isinstance(obj, Image.Image)

class Pager(Widget):
	source = None
	source_is_stream = False

	old_source = None
	old_scroll_begin = 0
	old_startx = 0
	old_im_source = None
	old_size = None
	def __init__(self, win, embedded=False):
		Widget.__init__(self, win)
		self.embedded = embedded
		self.scroll_begin = 0
		self.startx = 0
		self.markup = None
		self.lines = []

	def open(self):
		self.scroll_begin = 0
		self.markup = None
		self.startx = 0
		self.need_redraw = True

	def close(self):
		if self.source and self.source_is_stream:
			self.source.close()

	def finalize(self):
		self.fm.ui.win.move(self.y, self.x)

	def draw(self):
		if self.old_source != self.source:
			self.old_source = self.source
			self.need_redraw = True

		if self.old_scroll_begin != self.scroll_begin or \
				self.old_startx != self.startx:
			self.old_startx = self.startx
			self.old_scroll_begin = self.scroll_begin
		self.need_redraw = True

		if self.need_redraw:
			self.win.erase()
			cant_draw = False
			if is_pil_image(self.source):
				cant_draw = (self._generate_image(self.source) == False)
			if cant_draw:
				self.close()
			else:
				line_gen = self._generate_lines(
						starty=self.scroll_begin, startx=self.startx)

				for line, i in zip(line_gen, range(self.hei)):
					self._draw_line(i, line)
			self.need_redraw = False

	def _draw_line(self, i, line):
		if self.markup is None:
			self.addstr(i, 0, line)
		elif self.markup is 'help':
			self.addstr(i, 0, line)

			baseclr = ('in_pager', 'help_markup')

			if line.startswith('===='):
				self.color_at(i, 0, len(line), 'seperator', *baseclr)
				return

			if line.startswith('        ') and \
				len(line) >= 16 and line[15] == ' ':
				self.color_at(i, 0, 16, 'key', *baseclr)

			for m in BAR_REGEXP.finditer(line):
				start, length = m.start(), m.end() - m.start()
				self.color_at(i, start, length, 'bars', *baseclr)
				self.color_at(i, start + 1, length - 2, 'link', *baseclr)

			for m in QUOTES_REGEXP.finditer(line):
				start, length = m.start(), m.end() - m.start()
				self.color_at(i, start, length, 'quotes', *baseclr)
				self.color_at(i, start + 1, length - 2, 'text', *baseclr)

			for m in SPECIAL_CHARS_REGEXP.finditer(line):
				start, length = m.start(), m.end() - m.start()
				self.color_at(i, start, length, 'special', *baseclr)

			if TITLE_REGEXP.match(line):
				self.color_at(i, 0, -1, 'title', *baseclr)
		elif self.markup is 'ansi':
			self.addstr(i, 0, "")		# set start position
			for chunk in ansi.text_with_fg_bg(line):
				if isinstance(chunk, tuple):
					fg, bg = chunk
					self.fg_bg_color(fg, bg)
				else:
					self.addstr(chunk)

	def move(self, narg=None, **kw):
		direction = Direction(kw)
		if direction.horizontal():
			self.startx = direction.move(
					direction=direction.right(),
					override=narg,
					maximum=self._get_max_width(),
					current=self.startx,
					pagesize=self.wid,
					offset=-self.wid + 1)
		if direction.vertical():
			if self.source_is_stream:
				self._get_line(self.scroll_begin + self.hei * 2)
			self.scroll_begin = direction.move(
					direction=direction.down(),
					override=narg,
					maximum=len(self.lines),
					current=self.scroll_begin,
					pagesize=self.hei,
					offset=-self.hei + 1)

	def press(self, key):
		self.env.keymanager.use_context(self.embedded and 'embedded_pager' or 'pager')
		self.env.key_append(key)
		kbuf = self.env.keybuffer
		cmd = kbuf.command

		if kbuf.failure:
			kbuf.clear()
			return
		elif not cmd:
			return

		self.env.cmd = cmd

		if cmd.function:
			try:
				cmd.function(CommandArgs.from_widget(self))
			except Exception as error:
				self.fm.notify(error)
			if kbuf.done:
				kbuf.clear()
		else:
			kbuf.clear()

	def set_source(self, source, strip=False):
		if self.source and self.source_is_stream:
			self.source.close()

		if isinstance(source, str):
			self.source_is_stream = False
			self.lines = source.splitlines()
		elif hasattr(source, '__getitem__'):
			self.source_is_stream = False
			self.lines = source
		elif hasattr(source, 'readline'):
			self.source_is_stream = True
			self.lines = []
		elif is_pil_image(source):
			self.source_is_stream = False
			self.lines = []
		else:
			self.source = None
			self.source_is_stream = False
			return False

		if not self.source_is_stream and strip:
			self.lines = map(lambda x: x.strip(), self.lines)

		self.source = source
		return True

	def click(self, event):
		n = event.ctrl() and 1 or 3
		direction = event.mouse_wheel_direction()
		if direction:
			self.move(down=direction * n)
		return True

	def _get_line(self, n, attempt_to_read=True):
		assert isinstance(n, int), n
		try:
			return self.lines[n]
		except (KeyError, IndexError):
			if attempt_to_read and self.source_is_stream:
				try:
					for l in self.source:
						self.lines.append(l)
						if len(self.lines) > n:
							break
				except UnicodeError:
					pass
				return self._get_line(n, attempt_to_read=False)
			return ""

	def _generate_image(self, img):
		if (self.wid, self.hei) == self.old_size \
				and self.source == self.old_im_source:
			return True
		self.old_size = (self.wid, self.hei)
		self.old_im_source = self.source
		try:
			from ranger.ext import caca
		except (ImportError, OSError):
			return False
		the_canvas = caca.canvas.Canvas.create(self.wid, self.hei)
		the_canvas.set_color_ansi(caca.Colors.BLACK, caca.Colors.WHITE)
		w, h = img.size
		ww, wh = the_canvas.get_width(), the_canvas.get_height()
		scale = min(float(ww)/w, float(wh*2)/h)
		the_canvas.put_pil_image(0, 0, int(w*scale), int(h*scale/2), img)
		self.lines = the_canvas.export("ansi").splitlines()
		self.markup = 'ansi'
		return True

	def _generate_lines(self, starty, startx):
		i = starty
		if not self.source:
			raise StopIteration
		while True:
			try:
				line = self._get_line(i).expandtabs(4)
				if self.markup is 'ansi':
					line = ansi.char_slice(line, startx, self.wid + startx) + '\x1b[0m'
				else:
					line = line[startx:self.wid + startx]
				line = line.rstrip()
				yield line
			except IndexError:
				raise StopIteration
			i += 1

	def _get_max_width(self):
		return max(len(line) for line in self.lines)
