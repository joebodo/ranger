def __install__(self, fm):
	fm.signal_bind('core.run', exit, prio=True)
