# The first available one will be used:
pdf_readers = "evince", "zathura", "apvlv"
image_viewers = "feh", "eog", "mirage"
editors = "vim", "emacs", "vi", "nano", "pico", "ee"

@appdef
def default(context):
	global editors, pdf_readers, image_viewers
	filename = context.file

	if filename.lower() == "makefile":
		return get_app(context, "make")

	ext = extension(filename)
	if ext:
		if ext == "pdf":
			context.flags += "d"  # run detached!
			return get_app(context, *pdf_readers)
		if ext == "xml":
			return get_app(context, *editors)
		if ext in ["html", "html", "xhtml"]:
			return get_app(context, "firefox", "opera")

	if is_container(filename):
		return "aunpack %f"

	if is_audio(filename):
		return "mplayer %s"

	if is_video(filename):
		context.flags += "d"  # run videos detached
		return "mplayer %s"

	if is_image(filename):
		return get_app(context, *image_viewers)

	mime = mimetype(filename)
	if mime:
		mime2 = mime[mime.find("/") + 1:]
		if mime2 in ["x-perl", "x-python", "x-ruby", "x-sh"]:
			if context.mode == 0:
				return get_app("editor", context)
			if context.mode == 1:
				return "%f"  # execute it!

	if mime.startswith("text"):
		return get_app(context, *editors)


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


@appdef
def make(context):
	if context.mode == 0:
		return "make"
	elif context.mode == 1:
		return "make install"
	elif context.mode == 2:
		return "make clean"

# Define some applications which always run detached (with flag "d")
app("opera", flags="d")
app("firefox", flags="d")
app("gimp", flags="d")
app("mirage", flags="d")
app("eog", flags="d")
app("evince", flags="d")
app("zathura", flags="d")
app("mplayer", flags="d")
app("mplayer_fullscreen", cmd="mplayer -fs %s", flags="d")
