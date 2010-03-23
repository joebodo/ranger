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

	def __init__(self, name, *args, **__keywords):
		dict.__init__(self, **__keywords)
		self.__dict__ = self
		self.stop = False
		self.name = name

	def propagate(self):
		for function, rules in self.propagation_order:
			function(self)
			if self.stop:
				return False
		return True

	def stop_propagation(self):
		self.stop = True
#		self.propagation_order = []

class Handler(dict):
	def __init__(self, dct):
		self.__dict__ = dct

class SignalContainer(object):
	# self.signals = {
	#     'loop_start': {
	#         'sorted': True,
	#         'handlers': [
	#             (function1, rules1),
	#             (function2, rules2)
	#         ]
	#     }
	# }
	#
	# Rules are:
	#     run_before: Try to run this handler before the given handler
	#     run_after: Try to run it after that one.
	#     name: Identifier for "run_before" and "run_after" rules
	# special names: everything
	def __init__(self):
		self.signals = {}

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
			dct = self.signals[signal]
		except:
			lst = []
			dct = {'sorted':False, 'handlers': lst}
			self.signals[signal] = dct
		else:
			lst = dct['handlers']

		lst.append((function, rules))

	def emit(self, signal_name, *__args, **__kws):
		try:
			signal_data = self.signals[signal_name]
		except:
			return
		lst = signal_data['handlers']

		if not signal_data['sorted']:
			# TODO: sort the signals by topology
			signal_data['sorted'] = True

		signal = Signal(signal_name, *__args, **__kws)
		signal.propagation_order = lst
		try:
			return signal.propagate()
		except:
			return False
