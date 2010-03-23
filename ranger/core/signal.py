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
		for function in self.propagation_order:
			function(self)
			if self.stop:
				return False
		return True

	def stop_propagation(self):
		self.stop = True
#		self.propagation_order = []

class SignalContainer(object):
	def __init__(self):
		self.signals = {}

	def register(self, name, function=None):
		if function is None:
			if inspect.isfunction(name):
				function = name
				name = function.__name__
			else:
				def moo(fnc):
					self.register(name, fnc)
					return fnc
				return moo
		try:
			lst = self.signals[name]
		except:
			lst = []
			self.signals[name] = lst
		lst.append(function)

	def emit(self, name, *__args, **__kws):
		try:
			lst = self.signals[name]
		except:
			return
		signal = Signal(name, *__args, **__kws)
		signal.propagation_order = lst
		try:
			return signal.propagate()
		except:
			return False
