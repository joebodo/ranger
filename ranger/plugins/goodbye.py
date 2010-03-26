def __install__(self, fm):
	def say_goodbye(s):
		print("Good bye!")
	fm.signal_bind('core.quit', say_goodbye)
