# Copyright (C) 2009, 2010  Roman Zimbelmann <romanz@lavabit.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import inspect

class Signal(dict):
	propagation_order = []
	_stop = False

	def __init__(self, name, *args, **__keywords):
		dict.__init__(self, **__keywords)
		self.__dict__ = self
		self._stop = False
		self.name = name

	def propagate(self):
		for handler in self.propagation_order:
			handler.function(self)
			if self._stop:
				return True
		return False

	def stop_propagation(self):
		self._stop = True

class Handler(dict):
	def __init__(self, dct):
		self.__dict__ = dct

class SignalContainer(object):
	# Rules are:
	#     run_before: Try to run this handler before the given handler
	#     run_after: Try to run it after that one.
	#     name: Identifier for "run_before" and "run_after" rules
	# special names: everything
	def __init__(self, logfunc=None):
		self._logfunc = logfunc
		self._signals = {}

	def register(self, signal, function=None, **rules):
		if function is None:
			if inspect.isfunction(signal):
				function = signal
				signal = function.__name__
			else:
				def moo(fnc):
					self.register(signal, fnc, **rules)
					return fnc
				return moo
		try:
			dct = self._signals[signal]
		except:
			lst = []
			dct = {'sorted':False, 'handlers': lst}
			self._signals[signal] = dct
		else:
			dct['sorted'] = False
			lst = dct['handlers']

		handler = Handler(dict(rules, function=function))
		lst.append(handler)

	def _sort(self, lst):
		# TODO: sort the signals by topology
		return lst

	def emit(self, signal_name, vital=False, *__args, **__kws):
		try:
			signal_data = self._signals[signal_name]
		except:
			return
		lst = signal_data['handlers']
		if not lst:
			return

		if not signal_data['sorted']:
			signal_data['handlers'] = self._sort(signal_data['handlers'])
			signal_data['sorted'] = True

		signal = Signal(signal_name, *__args, **__kws)
		signal.propagation_order = lst
		try:
			return signal.propagate()
		except BaseException as e:
			if vital:
				raise
			else:
				if self._logfunc:
					self._logfunc(e)
				return False
