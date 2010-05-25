#!/usr/bin/python
"""Give some debugging info for installing the caca extension"""

try:
	import Image
except ImportError:
	print("PIL seems not to be installed.")
	print("Try to add the package \"python-imaging\".")
	print("")
	print("Original errormessage:")
	raise

try:
	from ranger.ext import caca
except (ImportError, OSError):
	print("Libcaca seems not to be installed.")
	print("Try to add the package \"libcaca\", in debian \"libcaca-dev\".")
	print("")
	print("Original errormessage:")
	raise

print("The caca extension should be working!")
