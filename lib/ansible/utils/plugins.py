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
import os.path
import sys
import glob
import imp
import ansible.constants as C
from ansible import errors

_basedirs = []

def push_basedir(basedir):
    if basedir not in _basedirs:
        _basedirs.insert(0, basedir)

class BaseLoader(object):

    '''
    BaseLoader is the base class for plug-in and module loaders in this module.

    It searches for files (plug-ins or modules) by iterating through
    the combined list of play basedirs and configured
    paths. Subclasses may add additional paths by overriding the
    _get_default_paths method.

    The first file found is used.

    '''

    def __init__(self, config, subdir, file_suffix="", aliases={}):

        self.config             = config
        self.subdir             = subdir
        self.file_suffix        = file_suffix
        self.aliases            = aliases

        self._paths = None
        self._found_cache = {}

        self._extra_dirs = []

    def print_paths(self):
        ''' Returns a string suitable for printing of the search path '''

        # Uses a list to get the order right
        ret = []
        for i in self._get_paths():
            if i not in ret:
                ret.append(i)
        return os.pathsep.join(ret)

    def _get_default_paths(self):
        ''' Subclasses may override this method to append search paths '''
        return []

    def _get_paths(self):
        ''' Return a list of paths to search for plugins in '''

        if self._paths is not None:
            return self._paths

        ret = []
        ret += self._extra_dirs
        for basedir in _basedirs:
            fullpath = os.path.join(basedir, self.subdir)
            if os.path.isdir(fullpath):
                files = glob.glob("%s/*" % fullpath)
                for file in files:
                    if os.path.isdir(file) and file not in ret:
                        ret.append(file)
                if fullpath not in ret:
                    ret.append(fullpath)

        # look in any configured paths, allow one level deep for subcategories
        configured_paths = self.config.split(os.pathsep)
        # search default paths, such as the standard plug-ins, last
        configured_paths.extend(self._get_default_paths())
        for path in configured_paths:
            path = os.path.expanduser(path)
            contents = glob.glob("%s/*" % path)
            for c in contents:
                if os.path.isdir(c):
                    ret.append(c)       
            ret.append(path)

        self._paths = ret

        return ret


    def add_directory(self, directory, with_subdir=False):
        ''' Adds an additional directory to the search path '''

        self._paths = None

        if directory is not None:
            if with_subdir:
                directory = os.path.join(directory, self.subdir)
            self._extra_dirs.append(directory)

    def find(self, name):
        ''' Find a file named with the given name and file_suffix '''

        if name in self._found_cache:
            return self._found_cache[name]

        for i in self._get_paths():
            path = os.path.join(i, "%s%s" % (name, self.file_suffix))
            if os.path.exists(path):
                self._found_cache[name] = path
                return path

        return None

    def __contains__(self, name):
        ''' Checks if we can find a file named name '''

        return self.find(name) is not None

class PluginLoader (BaseLoader):

    '''
    Loads Ansible plug-ins.

    Plug-ins may be loaded from the play basedirs, configured paths,
    or from the default ansible packages found on Python's path.  The
    first plug-in found is used.

    '''

    def __init__(self, class_name, package, config, subdir, aliases={}):
        BaseLoader.__init__(self, config, subdir, file_suffix=".py",
                            aliases=aliases)
        self.class_name = class_name
        self.package = package
        self._module_cache = {}

    def _get_default_paths(self):
        ''' return the path to the appropriate standard plug-ins '''

        if not hasattr(self, 'package_path'):
            m = __import__(self.package)
            parts = self.package.split('.')[1:]
            self.package_path = os.path.join(os.path.dirname(m.__file__), *parts)
        return [ self.package_path ]

    def get(self, name, *args, **kwargs):
        ''' instantiates a plugin of the given name using arguments '''

        if name in self.aliases:
            name = self.aliases[name]
        path = self.find(name)
        if path is None:
            return None
        if path not in self._module_cache:
            self._module_cache[path] = imp.load_source('.'.join([self.package, name]), path)
        return getattr(self._module_cache[path], self.class_name)(*args, **kwargs)

    def all(self, *args, **kwargs):
        ''' instantiates all plugins with the same arguments '''       

        for i in self._get_paths():
            for path in glob.glob(os.path.join(i, "*.py")):
                name, ext = os.path.splitext(os.path.basename(path))
                if name.startswith("_"):
                    continue
                if path not in self._module_cache:
                    self._module_cache[path] = imp.load_source('.'.join([self.package, name]), path)
                yield getattr(self._module_cache[path], self.class_name)(*args, **kwargs)

class ModuleLoader (BaseLoader):
    '''
    Loads Ansible modules.

    Modules may be loaded from the play basedirs, configured paths, or
    from the default Ansible modules.  The first module found is used.

    '''
    def _get_default_paths(self):
        ''' returns the path to the standard Ansible modules '''
        return [C.DIST_MODULE_PATH]

action_loader = PluginLoader(
    'ActionModule',   
    'ansible.runner.action_plugins',
    C.DEFAULT_ACTION_PLUGIN_PATH,
    'action_plugins'
)

callback_loader = PluginLoader(
    'CallbackModule', 
    'ansible.callback_plugins', 
    C.DEFAULT_CALLBACK_PLUGIN_PATH, 
    'callback_plugins'
)

connection_loader = PluginLoader(
    'Connection', 
    'ansible.runner.connection_plugins', 
    C.DEFAULT_CONNECTION_PLUGIN_PATH, 
    'connection_plugins', 
    aliases={'paramiko': 'paramiko_ssh'}
)

lookup_loader = PluginLoader(
    'LookupModule',   
    'ansible.runner.lookup_plugins', 
    C.DEFAULT_LOOKUP_PLUGIN_PATH, 
    'lookup_plugins'
)

vars_loader = PluginLoader(
    'VarsModule', 
    'ansible.inventory.vars_plugins', 
    C.DEFAULT_VARS_PLUGIN_PATH, 
    'vars_plugins'
)

filter_loader = PluginLoader(
    'FilterModule', 
    'ansible.runner.filter_plugins', 
    C.DEFAULT_FILTER_PLUGIN_PATH, 
    'filter_plugins'
)

module_finder = ModuleLoader(
    C.DEFAULT_MODULE_PATH,
    'library'
)
