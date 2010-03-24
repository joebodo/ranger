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

"""
The module responsible for signals aka events aka hooks.
"""

import inspect

_signals = {}
base_signal_keywords = None

def clear():
	_signals.clear()


def logfunc(x):
	print(x)


class Signal(dict):
	def __init__(self, name, handlers, keywords):
		dict.__init__(self, keywords)
		self.__dict__ = keywords
		self.propagation_order = handlers
		self.name = name
		self._stop = False

	def propagate(self):
		for handler in self.propagation_order:
			handler.function(self)
			if self._stop:
				return True
		return False

	def stop(self):
		self._stop = True


class Handler(dict):
	prio = 0.5
	def __init__(self, signal_name, function, dct):
		dict.__init__(self, dct)
		self.__dict__ = dct
		if self.prio < 0: self.prio = 0
		elif self.prio > 1: self.prio = 1
		self.signal_name = signal_name
		self.function = function

	def remove(self):
		try:
			handlers = _signals[self.signal_name]['handlers']
			handlers.remove(self)
		except KeyError:
			pass


def register(signal_name, function=None, **rules):
	assert isinstance(signal_name, str)
	if function is None:
		if inspect.isfunction(signal_name):
			function = signal_name
			signal_name = functin.__name__
		else:
			def decorator(func):
				register(signal_name, func, **rules)
				return func
			return decorator

	try:
		dct = _signals[signal_name]
	except:
		lst = []
		dct = {'sorted': False, 'handlers': lst}
		_signals[signal_name] = dct
	else:
		dct['sorted'] = False
		lst = dct['handlers']

	handler = Handler(signal_name, function, rules)
	lst.append(handler)
	return handler


def emit(signal_name, vital=False, **kw):
	assert isinstance(signal_name, str)
	assert isinstance(vital, bool)
	try:
		signal_data = _signals[signal_name]
	except:
		return
	handlers = signal_data['handlers']
	if not handlers:
		return

	if not signal_data['sorted']:
		handlers = _topsort(handlers)
		signal_data['handlers'] = handlers
		signal_data['sorted'] = True

	if base_signal_keywords:
		assert isinstance(base_signal_keywords, dict)
		new_kw = base_signal_keywords.copy()
		new_kw.update(kw)
		kw = new_kw
	signal = Signal(signal_name, handlers, kw)
	try:
		return signal.propagate()
	except AssertionError:
		raise
	except BaseException as e:
		if vital:
			raise
		else:
			logfunc(e)
			return False


# ---- Helper Functions

def _topsort_key_fnc(handler):
	return -handler.prio


def _topsort(handlers):
	return sorted(handlers, key=_topsort_key_fnc)
