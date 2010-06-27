# This is the configuration file for ranger.
#
# To customize ranger, either 1. create an empty file ~/.config/ranger/rc.py
# and add only the lines you need to change (recommended), or 2. copy this
# file as a whole to ~/.config/ranger/rc.py and edit it there.
#
# Though approach 2 may be easier for starters, it might break the
# configuration when you upgrade ranger.
#
# This file is python code and will be executed at the start of ranger.
# Feel free to hack into any part of ranger from here and/or wreak havoc.
#
# Table of contents:
# 1. Settings
# 2. Key Bindings
# 3. Command Definitions

# ===================================================================
# == 1. Settings  {{{
# ===================================================================

# Which files should be hidden?  Toggle this by typing `zh' or
# changing the setting `show_hidden'
import re
settings.hidden_filter = re.compile(
	r'^\.|\.(?:pyc|pyo|bak|swp)$|~$|lost\+found')
settings.show_hidden = False

# Show dotfiles in the bookmark preview box?
settings.show_hidden_bookmarks = True

# Which colorscheme to use?  These colorschemes are available by default:
# default, default88, texas, jungle, snow
# Snow is monochrome, texas and default88 use 88 colors.
settings.colorscheme = 'default'

# Preview files on the rightmost column?
# And collapse (shrink) the last column if there is nothing to preview?
settings.preview_files = True
settings.preview_directories = True
settings.collapse_preview = True

# Save the console history on exit?
settings.save_console_history = True

# Draw borders around columns?
settings.draw_borders = False
settings.draw_bookmark_borders = True

# Display the directory name in tabs?
settings.dirname_in_tabs = False

# How many columns are there, and what are their relative widths?
settings.column_ratios = (1, 1, 4, 3)

# Enable the mouse support?
settings.mouse_enabled = True

# Display the file size in the main column or status bar?
settings.display_size_in_main_column = True
settings.display_size_in_status_bar = False

# Set a title for the window?
settings.update_title = True

# Shorten the title if it gets long?  The number defines how many
# directories are displayed at once, False turns off this feature.
settings.shorten_title = 3

# Abbreviate $HOME with ~ in the titlebar (first line) of ranger?
settings.tilde_in_titlebar = True

# How many directory-changes or console-commands should be kept in history?
settings.max_history_size = 20
settings.max_console_history_size = 20

# Try to keep so much space between the top/bottom border when scrolling:
settings.scroll_offset = 8

# Flush the input after each key hit?  (Noticable when ranger lags)
settings.flushinput = True

# Save bookmarks (used with mX and `X) instantly?
# This helps to synchronize bookmarks between multiple ranger
# instances but leads to *slight* performance loss.
# When false, bookmarks are saved when ranger is exited.
settings.autosave_bookmarks = True

# Makes sense for screen readers:
settings.show_cursor = False

# One of: size, basename, mtime, type
settings.sort = 'basename'
settings.sort_reverse = False
settings.sort_case_insensitive = False
settings.sort_directories_first = True

# Enable this if key combinations with the Alt Key don't work for you.
# (Especially on xterm)
settings.xterm_alt_key = False


# }}}
# ===================================================================
# == 2. Key Bindings  {{{
# ===================================================================

# There are different keys for different contexts:
#   browser, console, taskview, pager
# To map a key to one context, you can use:
#   keys.map('browser', 'x', function_x)

bmap = lambda *args: keys.map('browser', *args)
cmap = lambda *args: keys.map('console', *args)

bmap('Q', fm.exit)
bmap('<C-L>', fm.redraw_window)

bmap('t', fm.tag_toggle)
bmap('T', fm.tag_remove)

bmap(' ',  lambda: fm.mark(toggle=True))
bmap('v',  lambda: fm.mark(all=True, toggle=True))
bmap('uv', lambda: fm.mark(all=True, val=False))

from ranger.gui.widgets import console_mode as cmode
bmap(':', lambda: fm.open_console(cmode.COMMAND))


cmap('<Esc>', lambda: fm.focused.close())
cmap('<backspace>', lambda: fm.focused.delete())

cmap('<any>', lambda arg: arg.wdg.type_key(arg.match))

# and many more boring keybindings
# ... ... ...
# ... ... ...
# ... ... ...

# == Set up keys with directions ==

from ranger.ext.direction import Direction
directions = {
	'h':          Direction(left=1),
	'j':          Direction(down=1),
	'k':          Direction(up=1),
	'l':          Direction(right=1),
	'gg':         Direction(down=0, absolute=True),
	'G':          Direction(down=-1, absolute=True),
	'K':          Direction(up=0.5, pages=True),
	'J':          Direction(down=0.5, pages=True),
	'%':          Direction(down=50, percentage=True, absolute=True),
	'<left>':     Direction(left=1),
	'<down>':     Direction(down=1),
	'<up>':       Direction(up=1),
	'<right>':    Direction(right=1),
	'<C-B>':      Direction(up=1, pages=True),
	'<C-F>':      Direction(down=1, pages=True),
	'<C-U>':      Direction(up=0.5, pages=True),
	'<C-D>':      Direction(down=0.5, pages=True),
	'<home>':     Direction(down=0, absolute=True),
	'<end>':      Direction(down=-1, absolute=True),
	'<pageup>':   Direction(up=1, pages=True),
	'<pagedown>': Direction(down=1, pages=True),
}

def commands_with_directions(key, drct):
	bmap(key, lambda: fm.move(**drct))
	bmap('d' + key, lambda: fm.cut(dirarg=drct))
	bmap('y' + key, lambda: fm.copy(dirarg=drct))
	bmap('<C-V>' + key,
			lambda: fm.mark_in_direction(val=True, dirarg=drct))
	bmap('u<C-V>' + key,
			lambda: fm.mark_in_direction(val=False, dirarg=drct))

for key, drct in directions.items():
	commands_with_directions(key, drct)

# }}}
# ===================================================================
# == 3. Command Definitions  {{{
# ===================================================================

# }}}
# ===================================================================
