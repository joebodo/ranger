"""
This plugin is responsible for launching files. As a bonus, it can also
be executed as a standalone program.
"""

if __name__ == '__main__':
  pass
else:
  import ranger
  fm = ranger.get_fm()
  fm.optparser.add_option('-m', '--mode', type='int', default=ranger.RUNMODE,
      metavar='n', help="if a filename is supplied, run it with this mode")
  fm.optparser.add_option('-f', '--flags', type='string', default=ranger.RUNFLAGS,
      metavar='string',
      help="if a filename is supplied, run it with these flags.")
