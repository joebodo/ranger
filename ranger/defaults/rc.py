# ===================================================================
# == This is the configuration file for ranger.
# ===================================================================
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
# 1. Variable Definitions
# 2. Settings
# 3. Key Bindings
# 4. Command Definitions

# ===================================================================
# == 1. Variable Definitions {{{
# ===================================================================
# These variables are no real settings, they rather influence how
# the configuration is constructed later on.  Try searching for the
# variables in this file to see what they actually do.

ALLOW_DELETE_COMMAND = True
DELETE_WARNING = "delete seriously? "

# Direction keys, later used in key bindings:
from ranger.ext.direction import Direction
DIRECTIONS = {
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

# }}}
# ===================================================================
# == 2. Settings  {{{
# ===================================================================

# Preview files on the rightmost column?
# And collapse (shrink) the last column if there is nothing to preview?
settings.preview_files = True
settings.preview_directories = True
settings.collapse_preview = True

# Which program should be responsible for launching files?
settings.launch_script = '$libpath/data/rifle.py' + \
	' --config=$confpath/riflerc.py -f "$flags" -m "$mode" $files'
# Ranger ships with the file launcher "Rifle".
# Alternatives include:  (uncomment to use)
#launch_script = "gnome-open $files"  # The GNOME file launcher
#launch_script = "exo-open $files"    # The file launcher of Thunar

# Show dotfiles in the bookmark preview box?
settings.show_hidden_bookmarks = True

# Which colorscheme to use?  These colorschemes are available by default:
# default, default88, texas, jungle, snow
# Snow is monochrome, texas and default88 use 88 colors.
settings.colorscheme = 'default'

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

# Which files should be hidden?  Toggle this by typing `zh' or
# changing the setting `show_hidden'
import re
settings.hidden_filter = re.compile(
	r'^\.|\.(?:pyc|pyo|bak|swp)$|~$|lost\+found')
settings.show_hidden = False


# }}}
# ===================================================================
# == 3. Key Bindings  {{{
# ===================================================================
# There are different keys for different contexts:
#   browser, console, taskview, pager
# To map a key to one context, you can use:
#   keys.map('browser', 'x', function_x)

# Apply currying for shorter functions:
bmap = lambda *args: keys.map('browser', *args)
cmap = lambda *args: keys.map('console', *args)
tmap = lambda *args: keys.map('taskview', *args)
pmap = lambda *args: keys.map('pager', *args)
def allmap(*args):
	keys.map('browser', *args)
	keys.map('console', *args)
	keys.map('taskview', *args)
	keys.map('pager', *args)
def for_each(dictionary):
	def decorator(function):
		for items in dictionary:
			function(*items)
		return function
	return decorator


# == Global Keys ==
allmap("?", fm.display_help)
allmap('Q',     fm.exit)
allmap('<C-L>', fm.redraw_window)

# == Keys in the "browser" Context ==

# Movement:
# (Note: h/j/k/l keys are defined in the section for direction keys)
bmap('<C-D>', 'J', lambda: fm.move(down=0.5, pages=True))
bmap('<C-U>', 'K', lambda: fm.move(up=0.5, pages=True))
bmap(']',          lambda: fm.move_parent(1))
bmap('[',          lambda: fm.move_parent(-1))
bmap('}',          lambda: fm.traverse())
bmap('{',          lambda: fm.history_go(-1))
bmap('H',          lambda: fm.history_go(-1))
bmap('L',          lambda: fm.history_go(1))
bmap("<enter>",    lambda: fm.move(right=0))  # run with mode 0

# Tagging:
bmap('t', fm.tag_toggle)
bmap('T', fm.tag_remove)

# Marking:
bmap(' ',  lambda: fm.mark(toggle=True))
bmap('v',  lambda: fm.mark(all=True, toggle=True))
bmap('uv', lambda: fm.mark(all=True, val=False))

# File System Operations:
bmap('pp', fm.paste)
bmap('po', lambda: fm.paste(overwrite=True))
bmap('pl', fm.paste_symlink)
bmap('ud', 'uy', fm.uncut)

# Toggle Options:
bmap('zc', lambda: fm.toggle_boolean_option('collapse_preview'))
bmap('zd', lambda: fm.toggle_boolean_option('sort_directories_first'))
bmap('zf', lambda: fm.open_console(cmode.COMMAND, 'filter '))
bmap('zh', '<C-h>', lambda: fm.toggle_boolean_option('show_hidden'))
bmap('zi', lambda: fm.toggle_boolean_option('flushinput'))
bmap('zm', lambda: fm.toggle_boolean_option('mouse_enabled'))
bmap('zp', lambda: fm.toggle_boolean_option('preview_files'))
bmap('zP', lambda: fm.toggle_boolean_option('preview_directories'))
bmap('zs', lambda: fm.toggle_boolean_option('sort_case_insensitive'))

# Run Programs
bmap('S',  lambda: fm.execute_command(os.environ['SHELL']))
bmap('E',  lambda: fm.edit_file())
bmap('du', lambda: fm.execute_command('du --max-depth=1 -h | less'))

# Console Shortcuts
def append_to_filename(arg):
	command = 'rename ' + fm.env.cf.basename
	fm.open_console(cmode.COMMAND, command)
bmap("A", append_to_filename)

def insert_before_filename(arg):
	append_to_filename(arg)
	fm.ui.console.move(right=len('rename '), absolute=True)
bmap("I", insert_before_filename)

bmap('cw', lambda: fm.open_console(cmode.COMMAND, 'rename '))
bmap('cd', lambda: fm.open_console(cmode.COMMAND, 'cd '))
bmap('f',  lambda: fm.open_console(cmode.COMMAND_QUICK, 'find '))
bmap('@',  lambda: fm.open_console(cmode.OPEN, '@'))
bmap('#',  lambda: fm.open_console(cmode.OPEN, 'p!'))

# Jump to Directories:
bmap('gd', lambda: fm.cd('/dev'))
bmap('ge', lambda: fm.cd('/etc'))
bmap('gh', lambda: fm.cd('~'))
bmap('gl', lambda: fm.cd('/lib'))
bmap('gm', lambda: fm.cd('/media'))
bmap('gM', lambda: fm.cd('/mnt'))
bmap('go', lambda: fm.cd('/opt'))
bmap('gr', 'g/', lambda: fm.cd('/'))
bmap('gs', lambda: fm.cd('/srv'))
bmap('gu', lambda: fm.cd('/usr'))
bmap('gv', lambda: fm.cd('/var'))

from ranger import RANGERDIR
bmap('gR', lambda: fm.cd(RANGERDIR))

# Tabs:
bmap('gc', '<C-W>',   fm.tab_close)
bmap('gt', '<TAB>',   lambda: fm.tab_move(1))
bmap('gT', '<S-TAB>', lambda: fm.tab_move(-1))

def newtab_and_gohome(arg):
	arg.fm.tab_new()
	arg.fm.cd('~')   # To return to the original directory, type ``
bmap('gn', '<C-N>', newtab_and_gohome)

for n in range(1, 10):
	bmap('g' + str(n),         lambda: fm.tab_open(n))
	bmap('<A-' + str(n) + '>', lambda: fm.tab_open(n))

# Searching:
bmap('/',  lambda: fm.open_console(cmode.SEARCH))
bmap('n',  lambda: fm.search())
bmap('N',  lambda: fm.search(forward=False))
bmap('ct', lambda: fm.search(order='tag'))
bmap('cc', lambda: fm.search(order='ctime'))
bmap('cm', lambda: fm.search(order='mimetype'))
bmap('cs', lambda: fm.search(order='size'))

# Bookmarks:
from ranger.container.bookmarks import ALLOWED_KEYS
@for_each(ALLOWED_KEYS)
def assign_bookmark_keys(key):
	bmap("`" + key, "'" + key, lambda: fm.enter_bookmark(key))
	bmap("m" + key,            lambda: fm.set_bookmark(key))
	bmap("um" + key,           lambda: fm.unset_bookmark(key))
bmap("`<bg>", "'<bg>", "m<bg>", lambda: fm.draw_bookmarks())

# Change Views:
bmap('i', fm.display_file)
bmap('W', fm.display_log)
bmap('w', lambda: fm.ui.open_taskview())

# System Functions:
bmap("ZZ", "ZQ", fm.exit)
bmap("<C-R>",    fm.reset)
bmap("R",        fm.reload_cwd)

def ctrl_c():
	try:
		item = fm.loader.queue[0]
	except:
		fm.notify("Type Q or :quit<Enter> to exit Ranger")
	else:
		fm.notify("Aborting: " + item.get_description())
		fm.loader.remove(index=0)
bmap("<C-C>", ctrl_c)

bmap(':', ';', lambda: fm.open_console(cmode.COMMAND))
bmap('>',      lambda: fm.open_console(cmode.COMMAND_QUICK))
bmap('!',      lambda: fm.open_console(cmode.OPEN, prompt='!'))
bmap('s',      lambda: fm.open_console(cmode.OPEN, prompt='$'))
bmap('r',      lambda: fm.open_console(cmode.OPEN_QUICK))

# Sorting:
SORTING = {
	'b': 'basename',
	'm': 'mtime',
	'n': 'basename',
	's': 'size',
	't': 'type',
}
@for_each(SORTING.items())
def bind_sort_keys(key, val):
	for key, is_capital in ((key, False), (key.upper(), True)):
		# reverse if any of the two letters is capital
		bmap('o' + key, lambda: fm.sort(func=val, reverse=is_capital))
		bmap('O' + key, lambda: fm.sort(func=val, reverse=True))
bmap('or', 'Or', 'oR', 'OR', lambda:
	fm.sort(reverse=not fm.settings.sort_reverse))

# Midnight Commander shortcuts:
bmap('<F1>',  lambda arg: fm.display_help(narg=arg.n))
bmap('<F3>',  lambda: fm.display_file())
bmap('<F4>',  lambda: fm.edit_file())
bmap('<F5>',  lambda: fm.copy())
bmap('<F6>',  lambda: fm.cut())
bmap('<F7>',  lambda: fm.open_console(cmode.COMMAND, 'mkdir '))
bmap('<F10>', lambda: fm.exit())
if ALLOW_DELETE_COMMAND:
	bmap('<F8>', lambda: fm.open_console(cmode.COMMAND, DELETE_WARNING))

from ranger.gui.widgets import console_mode as cmode
bmap(':', lambda: fm.open_console(cmode.COMMAND))

# == Keys in the "taskview" Context ==
tmap("K",  lambda: fm.focused.task_move(0))
tmap("J",  lambda: fm.focused.task_move(-1))
tmap("dd", lambda: fm.focused.task_remove())
tmap("w", "q", "<ESC>", lambda: fm.ui.close_taskview())

# == Set up keys with directions ==
@for_each(DIRECTIONS.items())
def commands_with_directions(key, drct):
	bmap(key,       lambda arg: fm.move(narg=arg.n, **drct))
	tmap(key,       lambda arg: fm.focused.move(narg=arg.n, **drct))
	pmap(key,       lambda arg: fm.focused.move(narg=arg.n, **drct))
	bmap('d' + key, lambda: fm.cut(dirarg=drct))  # TODO: d3j
	bmap('y' + key, lambda: fm.copy(dirarg=drct))
	bmap('<C-V>' + key,
			lambda: fm.mark_in_direction(val=True, dirarg=drct))
	bmap('u<C-V>' + key,
			lambda: fm.mark_in_direction(val=False, dirarg=drct))

	if key[0] == '<' and key[-1] == '>':
		cmap(key, lambda arg: fm.focused.move(narg=arg.n, **drct))

# Hints:
# Try to keep them short! (~80 characters)
HINTS = {
	"c": "*c*time *m*imetype *s*ize *t*ag *w*:rename",
	"d": "d*u* (disk usage)  d*d* (cut)",
	"o": "*s*ize, *b*ase*n*ame *m*time *t*ype *r*everse",
	"p": "press *p* to confirm pasting, *o* to overwrite or *l* to " \
			"create symlinks",
	"u": "un*y*ank, unbook*m*ark, unselect:*v*",
	'um': "delete which bookmark?",
	"z": "[*cdfhimpPs*] show_*h*idden *p*review_files *P*review_dirs " \
			"*f*ilter flush*i*nput *m*ouse",
}
HINTS["O"] = HINTS["o"]

@for_each(HINTS.items())
def bind_hint_keys(key, text):
	bmap(key + "<bg>", lambda: fm.hint(text))

# == Pager Keys ==
pmap('<space>',      lambda arg: fm.focused.move(down=0.8, pages=True))
pmap('<cr>',         lambda arg: wdg.move(down=1))
pmap('<left>',  'h', lambda arg: fm.focused.move(left=4, narg=arg.n))
pmap('<right>', 'l', lambda arg: fm.focused.move(right=4, narg=arg.n))
pmap('d', lambda arg: fm.focused.move(down=0.5, pages=True, narg=arg.n))
pmap('u', lambda arg: fm.focused.move(up=0.5,   pages=True, narg=arg.n))
pmap('f', lambda arg: fm.focused.move(down=1,   pages=True, narg=arg.n))
pmap('b', lambda arg: fm.focused.move(up=1,     pages=True, narg=arg.n))
# (Other direction keys are already defined above)

pmap('E', fm.edit_file())
pmap('?', fm.display_help())
def close_pager():
	if fm.focused == fm.ui.pager:
		fm.ui.close_pager()
	else:
		fm.ui.close_embedded_pager()
pmap('q', 'i', '<ESC>', '<F3>', close_pager)

# == Console Keys ==
cmap('<Esc>', "<C-C>",       lambda: fm.focused.close())
cmap('<Enter>', "<c-j>",     lambda: fm.focused.execute())
cmap('<backspace>', "<C-H>", lambda: fm.focused.delete(-1))
cmap('<delete>', "<C-D>",    lambda: fm.focused.delete(-1))
cmap("<TAB>",                lambda: fm.focused.tab())
cmap("<S-TAB>",              lambda: fm.focused.tab(-1))

cmap("<C-W>", lambda: fm.focused.delete_word())
cmap("<C-K>", lambda: fm.focused.delete_rest(1))
cmap("<C-U>", lambda: fm.focused.delete_rest(-1))
cmap("<C-Y>", lambda: fm.focused.delete_rest(-1))

cmap("<up>",   "<C-P>", lambda: fm.focused.history_move(-1))
cmap("<down>", "<C-N>", lambda: fm.focused.history_move(1))
cmap("<home>", "<C-A>", lambda: fm.focused.move(right=0, absolute=True))
cmap("<end>",  "<C-E>", lambda: fm.focused.move(right=-1, absolute=True))

cmap('<any>', lambda arg: fm.focused.type_key(arg.match))

# }}}
# ===================================================================
# == 4. Command Definitions  {{{
# ===================================================================


# }}}
# ===================================================================
