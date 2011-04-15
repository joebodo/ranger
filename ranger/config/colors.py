import ranger
import stat
from ranger.ext.curses_colors import *

fm = ranger.get_fm()

def is_selected(sig):
	return sig.target.pointed_obj == sig.file

@fm.signal_wrapper('color.file')
def foo(sig):
	text = sig.file.basename
	sig.data[:] = []

	if hasattr(sig.file, '_cached_color'):
		fg, bg, attr = sig.file._cached_color
	else:
		fg, bg, attr = -1, -1, 0

		if sig.file.is_directory:
			fg = blue
			attr = bold
		elif sig.file.executable:
			fg = green
			attr = bold
		if sig.file.media:
			fg = magenta
		if sig.file.marked:
			fg = yellow
			attr |= bold
		sig.file._cached_color = [fg, bg, attr]

	if is_selected(sig):
		attr |= reverse

	if sig.column.level == 0:
		if sig.file.realpath in fm.tags:
			sig.data.append(["*", fg if attr & reverse else red, bg, attr])
		else:
			sig.data.append([" ", fg, bg, attr])


	if sig.column.display_infostring and sig.file.infostring \
			and fm.settings.display_size_in_main_column:
		info = str(sig.file.infostring) + "  "
	else:
		info = ""

	max_width = sig.column.wid - 1 - len(info)
	if len(text) + 1 > max_width:
		text = text[:max_width] + '~'
	text += " " * (sig.column.wid - len(text) - len(info)) + info

	sig.data.append([text, fg, bg, attr])
