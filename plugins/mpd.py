"""
A plugin that adds a few commands that integrate mpd into ranger.

Commands:
   :goto_current_song

Options:
   mpd_root_dir = /var/lib/mpd/music
"""

from ranger import fm
from ranger.api.commands import *
from ranger.ext.spawn import spawn

fm.register_plugin(name='mpd', version='1', help=__doc__)
fm.cmd('let mpd_root_dir = /var/lib/mpd/music')

@fm.commands.register
class goto_current_song(Command):
	""":goto_current_song
	Selects the currently playing song of MPD in ranger."""
	def execute(self):
		from os.path import dirname, basename, join
		newpath = join(fm.macros['mpd_root_dir'],
			spawn(['mpc', '-f', '%file%', 'current']).strip())
		basename = basename(newpath)

		fm.enter_dir(dirname(newpath))
		fm.env.cwd.load_content(schedule=False)

		for i, f in enumerate(fm.env.cwd.files):
			if f.basename == basename:
				fm.env.cwd.move(to=i)
				break
