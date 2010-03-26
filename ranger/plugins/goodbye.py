def say_goodbye(s):
	print("Good bye!")

class Plugin(object):
	def __install__(self, fm):
		fm.signal_bind('core.quit', say_goodbye)
