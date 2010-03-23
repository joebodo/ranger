import ranger
from ranger import relpath, relpath_conf, log
from os.path import exists
from types import MethodType
from inspect import getargspec

def _find_plugin(name):
	assert isinstance(name, str), 'Plugin names must be strings!'
	assert '.' not in name, 'Specify plugin names without the extension!'
	if exists(relpath_conf('plugins', name + '.py')):
		return 'plugins'
	elif exists(relpath('plugins', name + '.py')):
		return 'ranger.plugins'
	raise Exception('Plugin not found!')

plugins = ['throbber', 'bookmarks']

def install_plugins(**keywords):
	for plugin in plugins:
		path = _find_plugin(plugin)
		module = __import__(path, fromlist=[plugin])
		installfunc = getattr(module, plugin).__install__
		install_keywords = dict(
				[arg, keywords[arg] if arg in keywords else None] \
				for arg in getargspec(installfunc).args)
		installfunc(**install_keywords)

class Library(object):
	def __init__(self, fm):
		self.fm = fm

	def register(self, function, name=None):
		if name is None:
			name = function.__name__
			assert name != '<lambda>'
		self.__dict__[name] = MethodType(function, self.fm)

