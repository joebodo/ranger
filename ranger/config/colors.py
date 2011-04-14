import ranger
import stat
from ranger.ext.curses_colors import *

fm = ranger.get_fm()

def is_selected(sig):
	return sig.target.pointed_obj == sig.file

def is_executable(sig):
	return sig.file.stat.st_mode & stat.S_IXUSR

@fm.signal_wrapper('color')
def foo(sig):
#	if hasattr(sig.file, 'cached_color'):
#		sig.colors[:] = sig.file.cached_color
#		return
	fg, bg, attr = -1, -1, 0
	if 'in_browser' in sig.context:
		if sig.file.is_directory:
			fg = blue
			attr = bold
		elif is_executable(sig):
			fg = green
			attr = bold
		if is_selected(sig):
			attr |= reverse
		if sig.file.marked:
			fg = yellow
			attr = bold
#			attr = reverse
		if sig.file.media:
			fg = magenta

#	sig.file.cached_color = [fg, bg, attr]
	sig.colors[:] = [fg, bg, attr]
