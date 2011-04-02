"""
The configuration of ranger consists of two parts:
rc.conf, a file containing ranger commands. Each line will be typed in for you
	in the console when ranger starts.
startup.py, a python file that is imported very early on startup. It allows you
	to wreak havoc in any thinkable way. See the pydoc for a python API.

They can be placed in either ranger/config/ (of rangers library path) or
$HOME/.config/ranger/ (the XDG standard directory for config files). The latter
takes precedence.

Also, ranger is capable of using plugins, all of which may have their own
configuration files.
"""
