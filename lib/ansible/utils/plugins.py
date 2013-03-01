# (c) 2012, Daniel Hokka Zakrisson <daniel@hozac.com>
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

import os
import sys
import glob
import imp
import ansible.constants as C
from ansible import errors

_basedirs = []

def push_basedir(basedir):
    _basedirs.insert(0, basedir)

class PluginLoader(object):
    """PluginLoader loads plugins from the best source

    It searches for plugins by iterating through the combined list of
    play basedirs, configured paths, and the installed package directory.
    The first match is used.
    """
    def __init__(self, class_name, package, config, subdir, aliases={}):
        """Create a new PluginLoader"""
        self.class_name = class_name
        self.package = package
        self.config = config
        self.subdir = subdir
        self.aliases = aliases
        self._module_cache = {}
        self._extra_dirs = []

    def _get_package_path(self):
        """Gets the path of a Python package"""
        if not self.package:
            return []
        if not hasattr(self, 'package_path'):
            m = __import__(self.package)
            parts = self.package.split('.')[1:]
            self.package_path = os.path.join(os.path.dirname(m.__file__), *parts)
        return [self.package_path]

    def _get_paths(self):
        """Return a list of paths to search for plugins in

        The list is searched in order."""
        ret = []
        ret += self._extra_dirs
        for basedir in _basedirs:
            fullpath = os.path.join(basedir, self.subdir)
            if fullpath not in ret:
                ret.append(fullpath)
        ret += self.config.split(os.pathsep)
        ret += self._get_package_path()
        return ret

    def add_directory(self, directory, with_subdir=False):
        """Adds an additional directory to the search path"""
        if directory is not None:
            if with_subdir:
                directory = os.path.join(directory, self.subdir)
            self._extra_dirs.append(directory)

    def print_paths(self):
        """Returns a string suitable for printing of the search path"""
        # Uses a list to get the order right
        ret = []
        for i in self._get_paths():
            if i not in ret:
                ret.append(i)
        return os.pathsep.join(ret)

    def find_plugin(self, name):
        """Find a plugin named name"""
        suffix = ".py"
        if not self.class_name:
            suffix = ""
        for i in self._get_paths():
            path = os.path.join(i, "%s%s" % (name, suffix))
            if os.path.exists(path):
                return path
        return None

    def has_plugin(self, name):
        """Checks if a plugin named name exists"""
        return self.find_plugin(name) is not None
    __contains__ = has_plugin

    def get(self, name, *args, **kwargs):
        if name in self.aliases:
            name = self.aliases[name]
        path = self.find_plugin(name)
        if path is None:
            return None
        if path not in self._module_cache:
            self._module_cache[path] = imp.load_source('.'.join([self.package, name]), path)
        return getattr(self._module_cache[path], self.class_name)(*args, **kwargs)

    def all(self, *args, **kwargs):
        for i in self._get_paths():
            for path in glob.glob(os.path.join(i, "*.py")):
                name, ext = os.path.splitext(os.path.basename(path))
                if name.startswith("_"):
                    continue
                if path not in self._module_cache:
                    self._module_cache[path] = imp.load_source('.'.join([self.package, name]), path)
                yield getattr(self._module_cache[path], self.class_name)(*args, **kwargs)

action_loader     = PluginLoader('ActionModule',   'ansible.runner.action_plugins',     C.DEFAULT_ACTION_PLUGIN_PATH,     'action_plugins')
callback_loader   = PluginLoader('CallbackModule', 'ansible.callback_plugins',          C.DEFAULT_CALLBACK_PLUGIN_PATH,   'callback_plugins')
connection_loader = PluginLoader('Connection',     'ansible.runner.connection_plugins', C.DEFAULT_CONNECTION_PLUGIN_PATH, 'connection_plugins', aliases={'paramiko': 'paramiko_ssh'})
module_finder     = PluginLoader('',               '',                                  C.DEFAULT_MODULE_PATH,            'library')
lookup_loader     = PluginLoader('LookupModule',   'ansible.runner.lookup_plugins',     C.DEFAULT_LOOKUP_PLUGIN_PATH,     'lookup_plugins')
vars_loader       = PluginLoader('VarsModule',     'ansible.inventory.vars_plugins',    C.DEFAULT_VARS_PLUGIN_PATH,       'vars_plugins')
filter_loader     = PluginLoader('FilterModule',   'ansible.runner.filter_plugins',     C.DEFAULT_FILTER_PLUGIN_PATH,     'filter_plugins')
