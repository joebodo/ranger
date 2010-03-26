def say_goodbye(s):
	print("Good bye!")

class Plugin(object):
	def __install__(self):
		self.fm.signal_bind('core.quit', say_goodbye)
