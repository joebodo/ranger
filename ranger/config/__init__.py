"""
Ranger is customized with plugins and has no inherent configuration file.
However, the default plugin "rc" will read your ~/.config/ranger/rc.conf
and execute each line as a command, so you can change options and keybindings
there.  Check ranger/config/rc.conf for a template.

Each file at ~/.config/ranger/plugins/*.py will be used as a plugin.
A plugin can contain arbitrary python code and will be executed early on when
ranger starts.

Default plugins are in ranger/config/*.py. To disable default plugins, override
them by creating an empty file with the same name in your own plugin directory.
For example, to disable the "rifle" plugin, create an empty file at
"~/.config/ranger/plugins/rifle.py".

If you use libraries in your plugin, add the package to e.g.
"~/.config/ranger/plugins/name" and import them with "import plugins.name"
"""
