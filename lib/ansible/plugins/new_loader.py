# (c) 2012, Daniel Hokka Zakrisson <daniel@hozac.com>
# (c) 2012-2014, Michael DeHaan <michael.dehaan@gmail.com> and others
# (c) 2017, Toshio Kuratomi <tkuratomi@ansible.com>
# (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
import os.path
import sys
import time
import warnings

from ansible import constants as C
from ansible.errors import AnsibleError
from ansible.module_utils._text import to_bytes, to_text, to_native
from ansible.module_utils.six import string_types
from ansible.parsing.utils.yaml import from_yaml
from ansible.parsing.yaml.loader import AnsibleLoader
from ansible.plugins import get_plugin_class
from ansible.utils.collection_loader import AnsibleCollectionLoader, AnsibleFlatMapLoader, AnsibleCollectionRef
from ansible.utils.display import Display
from ansible.utils.plugin_docs import add_fragments


try:
    import importlib.util
    imp = None
except ImportError:
    import imp

# HACK: keep Python 2.6 controller tests happy in CI until they're properly split
try:
    from importlib import import_module
except ImportError:
    import_module = __import__

display = Display()


def get_all_plugin_loaders():
    return [(name, obj) for (name, obj) in globals().items() if isinstance(obj, PluginLoader)]


def add_all_plugin_dirs(path):
    ''' add any existing plugin dirs in the path provided '''
    b_path = to_bytes(path, errors='surrogate_or_strict')
    if os.path.isdir(b_path):
        for name, obj in get_all_plugin_loaders():
            if obj.subdir:
                plugin_path = os.path.join(b_path, to_bytes(obj.subdir))
                if os.path.isdir(plugin_path):
                    obj.add_directory(to_text(plugin_path))
    else:
        display.warning("Ignoring invalid path provided to plugin path: '%s' is not a directory" % to_text(path))


class PluginFinder:

    def __init__(self, class_name, package, config, subdir, aliases=None, required_base_class=None):
        self.class_name = class_name
        self.package = package
        self.subdir = subdir
        self.aliases = {} if aliases is None else aliases
        self.base_class = required_base_class
        self.last_modified = None

        if config and not isinstance(config, list):
            config = [config]
        elif not config:
            config = []

        self.config = config

        # paths we've scanned, using a dict for O(1) lookups
        self._scanned_paths = {}
        # plugin_cache -> (key:value)=(name:(path, class object|None))
        self._plugin_cache = {}
        # path_cache -> (key:value)=(path:(name, class object|None))
        self._path_cache = {}

        # now we add the initial directories
        initial_dirs = [os.path.realpath(os.path.expanduser(path)) for path in self.config] + self._get_package_paths()
        self.add_directories(initial_dirs, recursive=True)

    def add_directories(self, paths, recursive=False, force_rescan=False):
        if isinstance(paths, string_types):
            paths = [paths]

        modified = False
        for path in paths:
            if path not in self._scanned_paths or force_rescan:
                modified = True
                self._scan_path(path, recursive=recursive)

        if modified:
            self.last_modified = time.time()

    def _scan_path(self, path, recursive=False):
        self._scanned_paths[path] = True
        for root, subdirs, files in os.walk(path, followlinks=True):
            if '__init__.py' in files:
                for candidate in files:
                    candidate_path = os.path.join(root, candidate)
                    if os.path.isfile(candidate_path) and not candidate.endswith('__init__.py'):
                        candidate_name = os.path.basename(candidate)
                        if any(candidate_name.endswith(x) for x in C.BLACKLIST_EXTS):
                            continue

                        splitname = os.path.splitext(candidate_name)
                        base_name = splitname[0]
                        try:
                            extension = splitname[1]
                        except IndexError:
                            extension = ''

                        if base_name not in self._plugin_cache:
                            self._plugin_cache[base_name] = (candidate_path, None)
                            self._path_cache[candidate_path] = (base_name, None)
            if recursive:
                for x in subdirs:
                    subdir_path = os.path.join(root, x)
                    self._scan_path(subdir_path)

    def _get_package_paths(self):
        ''' Gets the path of a Python package '''
        if not self.package:
            return []
        if not hasattr(self, 'package_path'):
            m = __import__(self.package)
            parts = self.package.split('.')[1:]
            for parent_mod in parts:
                m = getattr(m, parent_mod)
            self.package_path = os.path.dirname(m.__file__)
        return [self.package_path]

    def __contains__(self, name):
        return name in self._plugin_cache

    def get(self, name):
        path, obj_class = self._plugin_cache[name]
        if obj_class is None:
            obj_class = self._load_plugin_class(name, path)
            self._plugin_cache[name] = (path, obj_class)
        return obj_class

    def all(self):
        for name in self._plugin_cache.keys():
            try:
                path, obj_class = self._plugin_cache[name]
                if obj_class is None:
                    obj_class = self._load_plugin_class(name, path)
                    self._plugin_cache[name] = (path, obj_class)
                yield obj_class
            except GeneratorExit:
                break

    def load_plugin(self, name):
        try:
            if name in self.aliases:
                name = self.aliases[name]

            path, obj_class = self._plugin_cache[name]
            if obj_class is None:
                obj_class = self._load_plugin_class(name, path)
                self._plugin_cache[name] = (path, obj_class)

            if self.base_class:
                # The import path is hardcoded and should be the right place,
                # so we are not expecting an ImportError.
                module = __import__(self.package, fromlist=[self.base_class])
                # Check whether this obj has the required base class.
                try:
                    plugin_class = getattr(module, self.base_class)
                except AttributeError:
                    return None
                if not issubclass(obj_class, plugin_class):
                    return None

            self._display_plugin_load(
                self.class_name,
                name,
                self._scanned_paths.keys(),
                path,
            )

            return obj_class
        except KeyError:
            return None

    def _load_plugin_class(self, name, path):
        module_source = self._load_module_source(name, path)
        obj_class = getattr(module_source, self.class_name)
        self._load_config_defs(name, obj_class, path)
        self._update_object(obj_class, name, path)
        return obj_class

    def _load_module_source(self, name, path):
        # avoid collisions across plugins
        if name.startswith('ansible_collections.'):
            full_name = name
        else:
            full_name = '.'.join([self.package, name])

        if full_name in sys.modules:
            # Avoids double loading, See https://github.com/ansible/ansible/issues/13110
            return sys.modules[full_name]

        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)
            if imp is None:
                spec = importlib.util.spec_from_file_location(to_native(full_name), to_native(path))
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                sys.modules[full_name] = module
            else:
                with open(to_bytes(path), 'rb') as module_file:
                    # to_native is used here because imp.load_source's path is for tracebacks and python's traceback formatting uses native strings
                    module = imp.load_source(to_native(full_name), to_native(path), module_file)
        return module

    def _load_config_defs(self, name, module, path):
        ''' Reads plugin docs to find configuration setting definitions, to push to config manager for later use '''
        # plugins w/o class name don't support config
        if self.class_name:
            type_name = get_plugin_class(self.class_name)
            # if type name != 'module_doc_fragment':
            if type_name in C.CONFIGURABLE_PLUGINS:
                dstring = AnsibleLoader(getattr(module, 'DOCUMENTATION', ''), file_name=path).get_single_data()
                if dstring:
                    add_fragments(dstring, path, fragment_loader=fragment_loader)
                if dstring and 'options' in dstring and isinstance(dstring['options'], dict):
                    C.config.initialize_plugin_configuration_definitions(type_name, name, dstring['options'])
                    display.debug('Loaded config def from plugin (%s/%s)' % (type_name, name))

    def _update_object(self, obj, name, path):
        # set extra info on the module, in case we want it later
        setattr(obj, '_original_path', path)
        setattr(obj, '_load_name', name)

    def _display_plugin_load(self, class_name, name, searched_paths, path):
        ''' formats data to display debug info for plugin loading, also avoids processing unless really needed '''
        if C.DEFAULT_DEBUG:
            msg = 'Loading %s \'%s\' from %s' % (class_name, os.path.basename(name), path)
            if len(searched_paths) > 1:
                msg = '%s (searched paths: %s)' % (msg, ", ".join(searched_paths))
            display.debug(msg)


connection_loader = PluginFinder(
    'Connection',
    'ansible.plugins.connection',
    C.DEFAULT_CONNECTION_PLUGIN_PATH,
    'connection_plugins',
    aliases={'paramiko': 'paramiko_ssh'},
    required_base_class='ConnectionBase',
)

filter_loader = PluginFinder(
    'FilterModule',
    'ansible.plugins.filter',
    C.DEFAULT_FILTER_PLUGIN_PATH,
    'filter_plugins',
)

lookup_loader = PluginFinder(
    'LookupModule',
    'ansible.plugins.lookup',
    C.DEFAULT_LOOKUP_PLUGIN_PATH,
    'lookup_plugins',
    required_base_class='LookupBase',
)

test_loader = PluginFinder(
    'TestModule',
    'ansible.plugins.test',
    C.DEFAULT_TEST_PLUGIN_PATH,
    'test_plugins'
)

vars_loader = PluginFinder(
    'VarsModule',
    'ansible.plugins.vars',
    C.DEFAULT_VARS_PLUGIN_PATH,
    'vars_plugins',
)
