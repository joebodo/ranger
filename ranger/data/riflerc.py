# This is the configuration of "rifle", Ranger's File Launcher.
#
# It's composed of python code with a couple of helper functions.
# The examples in this sample file should give you an idea.
# Type "pydoc path/to/rifle.py" for a full specification.


pdf_readers = "evince", "zathura", "apvlv"
image_viewers = "feh", "eog", "mirage"
web_browsers = "firefox", "opera"
editors = "vim", "emacs", "vi", "nano", "pico", "ee"


# Auto-detection of the filetype:
@appdef
def default(context):
	global editors, pdf_readers, image_viewers, web_browsers
	filename = context.file

	if filename.lower() == "makefile":
		return get_app(context, "make")

	ext = extension(filename)
	if ext:
		if ext == "pdf":
			context.flags += "d"  # run detached!
			return find_app(context, *pdf_readers)
		if ext == "xml":
			return find_app(context, *editors)
		if ext in ["html", "html", "xhtml"]:
			return find_app(context, *web_browsers)

	if is_container(filename):
		context.flags += "w"  # wait for ENTER after execution!
		return "aunpack %f"   # "aunpack" is a part of "atool"

	if is_audio(filename):
		return "mplayer %s"

	if is_video(filename):
		context.flags += "d"  # run detached!
		return "mplayer %s"

	if is_image(filename):
		return find_app(context, *image_viewers)

	mime = mimetype(filename)
	if mime:
		mime2 = mime[mime.find("/") + 1:]
		if mime2 in ["x-perl", "x-python", "x-ruby", "x-sh"]:
			if context.mode == 0:
				return find_app(context, *editors)
			if context.mode == 1:
				return get_app(context, "self")  # "self" executes the file

	if mime.startswith("text"):
		return find_app(context, *editors)


# Ranger requires you to define the applications "editor" and "pager":
@appdef
def editor(context):
	global editors
	return find_app(context, *editors)

@appdef
def pager(context):
	return "less %s"


# Examples for definitions which use "modes":
@appdef
def make(context):
	if context.mode == 0:
		return "make"
	elif context.mode == 1:
		return "make install"
	elif context.mode == 2:
		return "make clean"

@appdef
def feh(context):
	if context.mode == 1:
		return "feh --bg-scale %f"
	elif context.mode == 2:
		return "feh --bg-tile %f"
	elif context.mode == 3:
		return "feh --bg-center %f"
	elif context.mode == 11:
		return "feh --start-at ./%f ."
	else:
		return "feh %s"


# A more complex definition; Java needs the filename without the extension:
@appdef
def java(context):
	import os.path
	def _without_extension(filename):
		return os.path.splitext(filename)[0]
	return "java " + shell_escape(_without_extension(context.file))


# Define some applications which always run detached (with flag "d")
app("opera", flags="d")
app("firefox", flags="d")
app("gimp", flags="d")
app("mirage", flags="d")
app("eog", flags="d")
app("evince", flags="d")
app("zathura", flags="d")
app("mplayer", flags="d")

app("self", cmd="%f")  # just execute the file itself
