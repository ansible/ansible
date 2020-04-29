# (c) 2012, Daniel Hokka Zakrisson <daniel@hozac.com>
# (c) 2012-2014, Michael DeHaan <michael.dehaan@gmail.com> and others
# (c) 2017, Toshio Kuratomi <tkuratomi@ansible.com>
# (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import glob
import os
import os.path
import sys
import time
import types
import warnings

from collections import namedtuple

from ansible import constants as C
from ansible.errors import AnsibleError
from ansible.module_utils._text import to_bytes, to_text, to_native
from ansible.module_utils.six import string_types
from ansible.parsing.utils.yaml import from_yaml
from ansible.parsing.yaml.loader import AnsibleLoader
from ansible.plugins import get_plugin_class
from ansible.utils.collection_loader import AnsibleCollectionLoader, AnsibleFlatMapLoader, AnsibleCollectionRef, get_collection_name_from_path
from ansible.utils.display import Display
from ansible.utils.plugin_docs import add_fragments


try:
    import importlib.util
    from importlib.abc import PathEntryFinder
    imp = None
except ImportError:
    import imp

# HACK: keep Python 2.6 controller tests happy in CI until they're properly split
try:
    from importlib import import_module
except ImportError:
    import_module = __import__

display = Display()

GENERAL_CACHE_ENTRY_FIELDS = ['obj', 'deprecated', 'aliases']

PathCacheEntry = namedtuple('PathCacheEntry', ['name', 'extension'] + GENERAL_CACHE_ENTRY_FIELDS)
PluginCacheEntry = namedtuple('PluginCacheEntry', ['path'] + GENERAL_CACHE_ENTRY_FIELDS)


def get_all_plugin_loaders():
    return [(name, obj) for (name, obj) in globals().items() if isinstance(obj, PluginFinder)]


def add_all_plugin_dirs(path):
    ''' add any existing plugin dirs in the path provided '''
    b_path = to_bytes(path, errors='surrogate_or_strict')
    if os.path.isdir(b_path):
        for name, obj in get_all_plugin_loaders():
            if obj.subdir:
                plugin_path = os.path.join(b_path, to_bytes(obj.subdir))
                if os.path.isdir(plugin_path):
                    obj.add_directories([to_text(plugin_path)], recursive=True)
    else:
        display.warning("Ignoring invalid path provided to plugin path: '%s' is not a directory" % to_text(path))


def get_shell_plugin(shell_type=None, executable=None):
    if not shell_type:
        # default to sh
        shell_type = 'sh'
        # mostly for backwards compat
        if executable:
            if isinstance(executable, string_types):
                shell_filename = os.path.basename(executable)
                try:
                    shell = shell_loader.get(shell_filename)()
                except Exception:
                    shell = None

                if shell is None:
                    for shell in shell_loader.all():
                        if shell_filename in shell.COMPATIBLE_SHELLS:
                            shell_type = shell.SHELL_FAMILY
                            break
        else:
            raise AnsibleError("Either a shell type or a shell executable must be provided ")
    else:
        shell = shell_loader.get(shell_type)()

    if not shell:
        raise AnsibleError("Could not find the shell plugin required (%s)." % shell_type)

    if executable:
        setattr(shell, 'executable', executable)

    return shell


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
        # plugin_cache -> (k=name, v=PluginCacheEntry)
        self._plugin_cache = {}
        # path_cache -> (k=path, v=PathCacheEntry)
        self._path_cache = {}

        # now we add the initial directories
        initial_dirs = [os.path.realpath(os.path.expanduser(path)) for path in self.config]
        package_path = self._get_package_path()
        if package_path:
            initial_dirs.append(package_path)

        self.add_directories(initial_dirs, recursive=True)

    # methods for discovering plugins

    def add_directory(self, path, recursive=False, force_rescan=False):
        target_path = path
        if self.subdir:
            target_path = os.path.join(path, self.subdir)
        self.add_directories([target_path], recursive=recursive, force_rescan=force_rescan)

    def add_directories(self, paths, recursive=False, force_rescan=False):
        if isinstance(paths, string_types):
            paths = [paths]

        modified = False
        for path in paths:
            if os.path.exists(path) and (path not in self._scanned_paths or force_rescan):
                modified = True
                self._scan_path(path, recursive=recursive)

        if modified:
            self.last_modified = time.time()

    def _scan_path(self, path, recursive=False):
        self._scanned_paths[path] = True
        for root, subdirs, files in os.walk(path, followlinks=True):
            for candidate in files:
                candidate_path = os.path.join(root, candidate)
                if os.path.isfile(candidate_path) and not candidate.endswith('__init__.py'):
                    candidate_name = os.path.basename(candidate)
                    if any(candidate_name.endswith(x) for x in C.BLACKLIST_EXTS):
                        continue

                    splitname = os.path.splitext(candidate_name)
                    base_name = splitname[0]
                    try:
                        extension = splitname[1].replace('.', '')
                    except IndexError:
                        extension = ''

                    if (base_name, extension) not in self._plugin_cache:
                        self._path_cache[candidate_path] = PathCacheEntry(base_name, extension, None, False, [])
                        self._plugin_cache[(base_name, extension)] = PluginCacheEntry(candidate_path, None, False, [])

            if recursive:
                for x in subdirs:
                    subdir_path = os.path.join(root, x)
                    self._scan_path(subdir_path)

    def _get_package_path(self):
        ''' Gets the path of a Python package '''
        if not self.package:
            return None
        if not hasattr(self, 'package_path'):
            ansible, rest = self.package.split('.', 1)
            parts = rest.split('.')
            if parts[0] == 'plugins':
                path = os.path.join(os.path.dirname(__file__), *parts[1:])
            else:
                # we go up one dir and join the path to all the parts we have
                path = os.path.join(os.path.realpath(os.path.join(os.path.dirname(__file__), '..')), *parts)
            if not os.path.exists(path):
                raise AnsibleError("could not find package path for plugin %s" % (self.package,))
            self.package_path = path
        return self.package_path

    def __contains__(self, name, collection_list=None):
        return self.find_plugin(name, collection_list=collection_list)[1] is not None

    # methods for finding plugins

    has_plugin = __contains__

    def _find_legacy_plugin(self, name, extension):
        '''
        used to find "legacy" plugins, which ship with Ansible and
        are located in the python library directory under plugins/
        '''
        try:
            return self._plugin_cache[(name, extension)]
        except KeyError:
            # if the extension was blank, we default to using python
            # modules so check to see if there's a matching using py
            if extension == '':
                return self._plugin_cache[(name, 'py')]
            # otherwise re-raise the KeyError
            raise

    def _find_fq_plugin(self, fq_name, extension):
        '''
        used to find fully-qualified plugins, which are those that
        ship inside a collection package
        '''

        plugin_type = AnsibleCollectionRef.legacy_plugin_dir_to_plugin_type(self.subdir)
        acr = AnsibleCollectionRef.from_fqcr(fq_name, plugin_type)

        n_resource = to_native(acr.resource, errors='strict')
        # we want this before the extension is added
        full_name = '{0}.{1}'.format(acr.n_python_package_name, n_resource)
        if extension:
            n_resource += "." + extension

        pkg = sys.modules.get(acr.n_python_package_name)
        if not pkg:
            # FIXME: there must be cheaper/safer way to do this
            pkg = import_module(acr.n_python_package_name)

        # if the package is one of our flatmaps, we need to consult its loader
        # to find the path, since the file could be anywhere in the tree
        if hasattr(pkg, '__loader__') and isinstance(pkg.__loader__, AnsibleFlatMapLoader):
            try:
                file_path = pkg.__loader__.find_file(n_resource)
                return full_name, to_text(file_path)
            except IOError:
                # this loader already takes care of extensionless files, so if we didn't find it, just bail
                return None, None

        pkg_path = os.path.dirname(pkg.__file__)
        n_resource_path = os.path.join(pkg_path, n_resource)

        # FIXME: and is file or file link or ...
        if os.path.exists(n_resource_path):
            return full_name, to_text(n_resource_path)

        # look for any matching extension in the package location (sans filter)
        found_files = [f
                       for f in glob.iglob(os.path.join(pkg_path, n_resource) + '.*')
                       if os.path.isfile(f) and not f.endswith(C.MODULE_IGNORE_EXTS)]

        if not found_files:
            return None, None
        elif len(found_files) > 1:
            display.warning("multiple plugins found matching '{0}'".format(fq_name))

        return full_name, to_text(found_files[0])

    def find_plugin(self, name, mod_type='', ignore_deprecated=False, check_aliases=False, collection_list=None):
        # FIXME: implement aliases/deprecated names
        # FIXME: implement plugin filters
        # global _PLUGIN_FILTERS
        # if name in _PLUGIN_FILTERS[self.package]:
        #     return None, None

        if mod_type:
            suffix = mod_type
        else:
            # Only Ansible Modules.  Ansible modules can be any executable so
            # they can have any suffix
            suffix = ''

        # FIXME: need this right now so we can still load shipped PS module_utils- come up with a more robust solution
        return_path = None
        if (AnsibleCollectionRef.is_valid_fqcr(name) or collection_list) and not name.startswith('Ansible'):
            if '.' in name or not collection_list:
                candidates = [name]
            else:
                candidates = ['{0}.{1}'.format(c, name) for c in collection_list]
            # TODO: keep actual errors, not just assembled messages
            errors = []
            for candidate_name in candidates:
                try:
                    # HACK: refactor this properly
                    if candidate_name.startswith('ansible.legacy'):
                        # just pass the raw name to the old lookup function to check in all the usual locations
                        full_name = name
                        # p = self._find_plugin_legacy(name.replace('ansible.legacy.', '', 1), ignore_deprecated, check_aliases, suffix)
                        entry = self._find_legacy_plugin(name.replace('ansible.legacy.', '', 1), suffix)
                        if entry:
                            return_path = entry.path
                    else:
                        full_name, return_path = self._find_fq_plugin(candidate_name, suffix)
                    if return_path:
                        return full_name, return_path
                except Exception as ex:
                    errors.append(to_native(ex))

            if errors:
                display.debug(msg='plugin lookup for {0} failed; errors: {1}'.format(name, '; '.join(errors)))

            return None, None

        # if we got here, there's no collection list and it's not an FQ name, so do legacy lookup
        try:
            entry = self._find_legacy_plugin(name, suffix)
            if entry:
                return_path = entry.path
        except KeyError:
            pass
        return name, return_path

    # methods for loading plugins

    def get(self, name, ext='', collection_list=None):
        name, path = self.find_plugin(name, ext, collection_list=collection_list)
        if not path:
            return None
        if AnsibleCollectionRef.is_valid_fqcr(name):
            return self._load_plugin_class(name, path)
        else:
            return self._load_legacy_plugin(name, ext)

    def _load_legacy_plugin(self, name, ext, *args, **kwargs):
        if not self.class_name:
            return None
        try:
            entry = self._find_legacy_plugin(name, ext)
            if entry.obj is None:
                entry = entry._replace(obj=self.load_plugin(name, ext, entry=entry))
                self._plugin_cache[(name, ext)] = entry
            return entry.obj
        except KeyError:
            return None

    def all(self):
        for name, ext in self._plugin_cache.keys():
            try:
                entry = self._plugin_cache[(name, ext)]
                if entry.obj is None:
                    entry = entry._replace(obj=self.load_plugin(name, ext, entry=entry))
                    self._plugin_cache[(name, ext)] = entry
                yield entry.obj
            except GeneratorExit:
                break

    def load_plugin(self, name, ext='', entry=None):
        try:
            if name in self.aliases:
                name = self.aliases[name]

            if not entry:
                entry = self._plugin_cache[(name, ext)]
            if entry.obj:
                return entry.obj

            obj_class = self._load_plugin_class(name, entry.path)
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
                entry.path,
            )

            return obj_class
        except KeyError:
            return None

    def _load_plugin_class(self, name, path):
        # FIXME: doubtful any other types will do this, but should this
        #        be something that's set in the class instead of hard-
        #        coding it this way?
        # filter and test plugins can can contain multiple plugins
        # they must have a unique python module name to prevent them
        # from shadowing each other
        if self.subdir in ('filter_plugins', 'test_plugins') and '.' not in name:
            name = '{0}_{1}'.format(abs(hash(path)), name)
        module_source = self._load_module_source(name, path)
        self._load_config_defs(name, module_source, path)
        obj_class = getattr(module_source, self.class_name)
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


# define and run the method to configure the collection loader object

def _configure_collection_loader():
    if not any((isinstance(l, AnsibleCollectionLoader) for l in sys.meta_path)):
        sys.meta_path.insert(0, AnsibleCollectionLoader(C.config))


_configure_collection_loader()


# All PluginFinder instances follow here

fragment_loader = PluginFinder(
    'ModuleDocFragment',
    'ansible.plugins.doc_fragments',
    C.DOC_FRAGMENT_PLUGIN_PATH,
    'doc_fragments',
)

action_loader = PluginFinder(
    'ActionModule',
    'ansible.plugins.action',
    C.DEFAULT_ACTION_PLUGIN_PATH,
    'action_plugins',
    required_base_class='ActionBase',
)

become_loader = PluginFinder(
    'BecomeModule',
    'ansible.plugins.become',
    C.BECOME_PLUGIN_PATH,
    'become_plugins'
)

cache_loader = PluginFinder(
    'CacheModule',
    'ansible.plugins.cache',
    C.DEFAULT_CACHE_PLUGIN_PATH,
    'cache_plugins',
)

callback_loader = PluginFinder(
    'CallbackModule',
    'ansible.plugins.callback',
    C.DEFAULT_CALLBACK_PLUGIN_PATH,
    'callback_plugins',
)

cliconf_loader = PluginFinder(
    'Cliconf',
    'ansible.plugins.cliconf',
    C.DEFAULT_CLICONF_PLUGIN_PATH,
    'cliconf_plugins',
    required_base_class='CliconfBase'
)

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

httpapi_loader = PluginFinder(
    'HttpApi',
    'ansible.plugins.httpapi',
    C.DEFAULT_HTTPAPI_PLUGIN_PATH,
    'httpapi_plugins',
    required_base_class='HttpApiBase',
)

inventory_loader = PluginFinder(
    'InventoryModule',
    'ansible.plugins.inventory',
    C.DEFAULT_INVENTORY_PLUGIN_PATH,
    'inventory_plugins'
)

lookup_loader = PluginFinder(
    'LookupModule',
    'ansible.plugins.lookup',
    C.DEFAULT_LOOKUP_PLUGIN_PATH,
    'lookup_plugins',
    required_base_class='LookupBase',
)

module_loader = PluginFinder(
    '',
    'ansible.modules',
    C.DEFAULT_MODULE_PATH,
    'library',
)

module_utils_loader = PluginFinder(
    '',
    'ansible.module_utils',
    C.DEFAULT_MODULE_UTILS_PATH,
    'module_utils',
)

netconf_loader = PluginFinder(
    'Netconf',
    'ansible.plugins.netconf',
    C.DEFAULT_NETCONF_PLUGIN_PATH,
    'netconf_plugins',
    required_base_class='NetconfBase'
)

# NB: dedicated loader is currently necessary because PS module_utils expects "with subdir" lookup where
# regular module_utils doesn't. This can be revisited once we have more granular loaders.
ps_module_utils_loader = PluginFinder(
    '',
    'ansible.module_utils',
    C.DEFAULT_MODULE_UTILS_PATH,
    'module_utils',
)

shell_loader = PluginFinder(
    'ShellModule',
    'ansible.plugins.shell',
    'shell_plugins',
    'shell_plugins',
)

strategy_loader = PluginFinder(
    'StrategyModule',
    'ansible.plugins.strategy',
    C.DEFAULT_STRATEGY_PLUGIN_PATH,
    'strategy_plugins',
    required_base_class='StrategyBase',
)

terminal_loader = PluginFinder(
    'TerminalModule',
    'ansible.plugins.terminal',
    C.DEFAULT_TERMINAL_PLUGIN_PATH,
    'terminal_plugins',
    required_base_class='TerminalBase'
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
