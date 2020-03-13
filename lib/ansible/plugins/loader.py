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
import warnings

from collections import defaultdict

from ansible import constants as C
from ansible.errors import AnsibleError
from ansible.module_utils._text import to_bytes, to_text, to_native
from ansible.module_utils.compat.importlib import import_module
from ansible.module_utils.six import string_types
from ansible.parsing.utils.yaml import from_yaml
from ansible.parsing.yaml.loader import AnsibleLoader
from ansible.plugins import get_plugin_class, MODULE_CACHE, PATH_CACHE, PLUGIN_PATH_CACHE
from ansible.utils.collection_loader import AnsibleCollectionLoader, AnsibleFlatMapLoader, AnsibleCollectionRef
from ansible.utils.display import Display
from ansible.utils.plugin_docs import add_fragments

try:
    import importlib.util
    imp = None
except ImportError:
    import imp

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


def get_shell_plugin(shell_type=None, executable=None):

    if not shell_type:
        # default to sh
        shell_type = 'sh'

        # mostly for backwards compat
        if executable:
            if isinstance(executable, string_types):
                shell_filename = os.path.basename(executable)
                try:
                    shell = shell_loader.get(shell_filename)
                except Exception:
                    shell = None

                if shell is None:
                    for shell in shell_loader.all():
                        if shell_filename in shell.COMPATIBLE_SHELLS:
                            shell_type = shell.SHELL_FAMILY
                            break
        else:
            raise AnsibleError("Either a shell type or a shell executable must be provided ")

    shell = shell_loader.get(shell_type)
    if not shell:
        raise AnsibleError("Could not find the shell plugin required (%s)." % shell_type)

    if executable:
        setattr(shell, 'executable', executable)

    return shell


def add_dirs_to_loader(which_loader, paths):

    loader = getattr(sys.modules[__name__], '%s_loader' % which_loader)
    for path in paths:
        loader.add_directory(path, with_subdir=True)


class PluginLoader:
    '''
    PluginLoader loads plugins from the configured plugin directories.

    It searches for plugins by iterating through the combined list of play basedirs, configured
    paths, and the python path.  The first match is used.
    '''

    def __init__(self, class_name, package, config, subdir, aliases=None, required_base_class=None):
        aliases = {} if aliases is None else aliases

        self.class_name = class_name
        self.base_class = required_base_class
        self.package = package
        self.subdir = subdir

        # FIXME: remove alias dict in favor of alias by symlink?
        self.aliases = aliases

        if config and not isinstance(config, list):
            config = [config]
        elif not config:
            config = []

        self.config = config

        if class_name not in MODULE_CACHE:
            MODULE_CACHE[class_name] = {}
        if class_name not in PATH_CACHE:
            PATH_CACHE[class_name] = None
        if class_name not in PLUGIN_PATH_CACHE:
            PLUGIN_PATH_CACHE[class_name] = defaultdict(dict)

        # hold dirs added at runtime outside of config
        self._extra_dirs = []

        # caches
        self._module_cache = MODULE_CACHE[class_name]
        self._paths = PATH_CACHE[class_name]
        self._plugin_path_cache = PLUGIN_PATH_CACHE[class_name]

        self._searched_paths = set()

    def _clear_caches(self):

        if C.OLD_PLUGIN_CACHE_CLEARING:
            self._paths = None
        else:
            # reset global caches
            MODULE_CACHE[self.class_name] = {}
            PATH_CACHE[self.class_name] = None
            PLUGIN_PATH_CACHE[self.class_name] = defaultdict(dict)

            # reset internal caches
            self._module_cache = MODULE_CACHE[self.class_name]
            self._paths = PATH_CACHE[self.class_name]
            self._plugin_path_cache = PLUGIN_PATH_CACHE[self.class_name]
            self._searched_paths = set()

    def __setstate__(self, data):
        '''
        Deserializer.
        '''

        class_name = data.get('class_name')
        package = data.get('package')
        config = data.get('config')
        subdir = data.get('subdir')
        aliases = data.get('aliases')
        base_class = data.get('base_class')

        PATH_CACHE[class_name] = data.get('PATH_CACHE')
        PLUGIN_PATH_CACHE[class_name] = data.get('PLUGIN_PATH_CACHE')

        self.__init__(class_name, package, config, subdir, aliases, base_class)
        self._extra_dirs = data.get('_extra_dirs', [])
        self._searched_paths = data.get('_searched_paths', set())

    def __getstate__(self):
        '''
        Serializer.
        '''

        return dict(
            class_name=self.class_name,
            base_class=self.base_class,
            package=self.package,
            config=self.config,
            subdir=self.subdir,
            aliases=self.aliases,
            _extra_dirs=self._extra_dirs,
            _searched_paths=self._searched_paths,
            PATH_CACHE=PATH_CACHE[self.class_name],
            PLUGIN_PATH_CACHE=PLUGIN_PATH_CACHE[self.class_name],
        )

    def format_paths(self, paths):
        ''' Returns a string suitable for printing of the search path '''

        # Uses a list to get the order right
        ret = []
        for i in paths:
            if i not in ret:
                ret.append(i)
        return os.pathsep.join(ret)

    def print_paths(self):
        return self.format_paths(self._get_paths(subdirs=False))

    def _all_directories(self, dir):
        results = []
        results.append(dir)
        for root, subdirs, files in os.walk(dir, followlinks=True):
            if '__init__.py' in files:
                for x in subdirs:
                    results.append(os.path.join(root, x))
        return results

    def _get_package_paths(self, subdirs=True):
        ''' Gets the path of a Python package '''

        if not self.package:
            return []
        if not hasattr(self, 'package_path'):
            m = __import__(self.package)
            parts = self.package.split('.')[1:]
            for parent_mod in parts:
                m = getattr(m, parent_mod)
            self.package_path = os.path.dirname(m.__file__)
        if subdirs:
            return self._all_directories(self.package_path)
        return [self.package_path]

    def _get_paths(self, subdirs=True):
        ''' Return a list of paths to search for plugins in '''

        # FIXME: This is potentially buggy if subdirs is sometimes True and sometimes False.
        # In current usage, everything calls this with subdirs=True except for module_utils_loader and ansible-doc
        # which always calls it with subdirs=False. So there currently isn't a problem with this caching.
        if self._paths is not None:
            return self._paths

        ret = self._extra_dirs[:]

        # look in any configured plugin paths, allow one level deep for subcategories
        if self.config is not None:
            for path in self.config:
                path = os.path.realpath(os.path.expanduser(path))
                if subdirs:
                    contents = glob.glob("%s/*" % path) + glob.glob("%s/*/*" % path)
                    for c in contents:
                        if os.path.isdir(c) and c not in ret:
                            ret.append(c)
                if path not in ret:
                    ret.append(path)

        # look for any plugins installed in the package subtree
        # Note package path always gets added last so that every other type of
        # path is searched before it.
        ret.extend(self._get_package_paths(subdirs=subdirs))

        # HACK: because powershell modules are in the same directory
        # hierarchy as other modules we have to process them last.  This is
        # because powershell only works on windows but the other modules work
        # anywhere (possibly including windows if the correct language
        # interpreter is installed).  the non-powershell modules can have any
        # file extension and thus powershell modules are picked up in that.
        # The non-hack way to fix this is to have powershell modules be
        # a different PluginLoader/ModuleLoader.  But that requires changing
        # other things too (known thing to change would be PATHS_CACHE,
        # PLUGIN_PATHS_CACHE, and MODULE_CACHE.  Since those three dicts key
        # on the class_name and neither regular modules nor powershell modules
        # would have class_names, they would not work as written.
        #
        # The expected sort order is paths in the order in 'ret' with paths ending in '/windows' at the end,
        # also in the original order they were found in 'ret'.
        # The .sort() method is guaranteed to be stable, so original order is preserved.
        ret.sort(key=lambda p: p.endswith('/windows'))

        # cache and return the result
        self._paths = ret
        return ret

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

    def add_directory(self, directory, with_subdir=False):
        ''' Adds an additional directory to the search path '''

        directory = os.path.realpath(directory)

        if directory is not None:
            if with_subdir:
                directory = os.path.join(directory, self.subdir)
            if directory not in self._extra_dirs:
                # append the directory and invalidate the path cache
                self._extra_dirs.append(directory)
                self._clear_caches()
                display.debug('Added %s to loader search path' % (directory))

    def _find_fq_plugin(self, fq_name, extension):
        """Search builtin paths to find a plugin. No external paths are searched,
        meaning plugins inside roles inside collections will be ignored.
        """

        plugin_type = AnsibleCollectionRef.legacy_plugin_dir_to_plugin_type(self.subdir)

        acr = AnsibleCollectionRef.from_fqcr(fq_name, plugin_type)

        n_resource = to_native(acr.resource, errors='strict')
        # we want this before the extension is added
        full_name = '{0}.{1}'.format(acr.n_python_package_name, n_resource)

        if extension:
            n_resource += extension

        pkg = sys.modules.get(acr.n_python_package_name)
        if not pkg:
            # FIXME: there must be cheaper/safer way to do this
            pkg = import_module(acr.n_python_package_name)

        # if the package is one of our flatmaps, we need to consult its loader to find the path, since the file could be
        # anywhere in the tree
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
        ext_blacklist = ['.pyc', '.pyo']
        found_files = [f for f in glob.iglob(os.path.join(pkg_path, n_resource) + '.*') if os.path.isfile(f) and os.path.splitext(f)[1] not in ext_blacklist]

        if not found_files:
            return None, None

        if len(found_files) > 1:
            # TODO: warn?
            pass

        return full_name, to_text(found_files[0])

    def find_plugin(self, name, mod_type='', ignore_deprecated=False, check_aliases=False, collection_list=None):
        ''' Find a plugin named name '''
        return self.find_plugin_with_name(name, mod_type, ignore_deprecated, check_aliases, collection_list)[1]

    def find_plugin_with_name(self, name, mod_type='', ignore_deprecated=False, check_aliases=False, collection_list=None):
        ''' Find a plugin named name '''

        global _PLUGIN_FILTERS
        if name in _PLUGIN_FILTERS[self.package]:
            return None, None

        if mod_type:
            suffix = mod_type
        elif self.class_name:
            # Ansible plugins that run in the controller process (most plugins)
            suffix = '.py'
        else:
            # Only Ansible Modules.  Ansible modules can be any executable so
            # they can have any suffix
            suffix = ''

        # FIXME: need this right now so we can still load shipped PS module_utils- come up with a more robust solution
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
                        # 'ansible.legacy' refers to the plugin finding behavior used before collections existed.
                        # They need to search 'library' and the various '*_plugins' directories in order to find the file.
                        full_name = name
                        p = self._find_plugin_legacy(name.replace('ansible.legacy.', '', 1), ignore_deprecated, check_aliases, suffix)
                    else:
                        # 'ansible.builtin' should be handled here. This means only internal, or builtin, paths are searched.
                        full_name, p = self._find_fq_plugin(candidate_name, suffix)
                    if p:
                        return full_name, p
                except Exception as ex:
                    errors.append(to_native(ex))

            if errors:
                display.debug(msg='plugin lookup for {0} failed; errors: {1}'.format(name, '; '.join(errors)))

            return None, None

        # if we got here, there's no collection list and it's not an FQ name, so do legacy lookup

        return name, self._find_plugin_legacy(name, ignore_deprecated, check_aliases, suffix)

    def _find_plugin_legacy(self, name, ignore_deprecated=False, check_aliases=False, suffix=None):
        """Search library and various *_plugins paths in order to find the file.
        This was behavior prior to the existence of collections.
        """

        if check_aliases:
            name = self.aliases.get(name, name)

        # The particular cache to look for modules within.  This matches the
        # requested mod_type
        pull_cache = self._plugin_path_cache[suffix]
        try:
            return pull_cache[name]
        except KeyError:
            # Cache miss.  Now let's find the plugin
            pass

        # TODO: Instead of using the self._paths cache (PATH_CACHE) and
        #       self._searched_paths we could use an iterator.  Before enabling that
        #       we need to make sure we don't want to add additional directories
        #       (add_directory()) once we start using the iterator.  Currently, it
        #       looks like _get_paths() never forces a cache refresh so if we expect
        #       additional directories to be added later, it is buggy.
        for path in (p for p in self._get_paths() if p not in self._searched_paths and os.path.isdir(p)):
            display.debug('trying %s' % path)
            try:
                full_paths = (os.path.join(path, f) for f in os.listdir(path))
            except OSError as e:
                display.warning("Error accessing plugin paths: %s" % to_text(e))

            for full_path in (f for f in full_paths if os.path.isfile(f) and not f.endswith('__init__.py')):
                full_name = os.path.basename(full_path)

                # HACK: We have no way of executing python byte compiled files as ansible modules so specifically exclude them
                # FIXME: I believe this is only correct for modules and module_utils.
                # For all other plugins we want .pyc and .pyo should be valid
                if any(full_path.endswith(x) for x in C.BLACKLIST_EXTS):
                    continue

                splitname = os.path.splitext(full_name)
                base_name = splitname[0]
                try:
                    extension = splitname[1]
                except IndexError:
                    extension = ''

                # Module found, now enter it into the caches that match this file
                if base_name not in self._plugin_path_cache['']:
                    self._plugin_path_cache[''][base_name] = full_path

                if full_name not in self._plugin_path_cache['']:
                    self._plugin_path_cache[''][full_name] = full_path

                if base_name not in self._plugin_path_cache[extension]:
                    self._plugin_path_cache[extension][base_name] = full_path

                if full_name not in self._plugin_path_cache[extension]:
                    self._plugin_path_cache[extension][full_name] = full_path

            self._searched_paths.add(path)
            try:
                return pull_cache[name]
            except KeyError:
                # Didn't find the plugin in this directory. Load modules from the next one
                pass

        # if nothing is found, try finding alias/deprecated
        if not name.startswith('_'):
            alias_name = '_' + name
            # We've already cached all the paths at this point
            if alias_name in pull_cache:
                if not ignore_deprecated and not os.path.islink(pull_cache[alias_name]):
                    # FIXME: this is not always the case, some are just aliases
                    display.deprecated('%s is kept for backwards compatibility but usage is discouraged. '  # pylint: disable=ansible-deprecated-no-version
                                       'The module documentation details page may explain more about this rationale.' % name.lstrip('_'))
                return pull_cache[alias_name]

        return None

    def has_plugin(self, name, collection_list=None):
        ''' Checks if a plugin named name exists '''

        try:
            return self.find_plugin(name, collection_list=collection_list) is not None
        except Exception as ex:
            if isinstance(ex, AnsibleError):
                raise
            # log and continue, likely an innocuous type/package loading failure in collections import
            display.debug('has_plugin error: {0}'.format(to_text(ex)))

    __contains__ = has_plugin

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

    def _update_object(self, obj, name, path):

        # set extra info on the module, in case we want it later
        setattr(obj, '_original_path', path)
        setattr(obj, '_load_name', name)

    def get(self, name, *args, **kwargs):
        ''' instantiates a plugin of the given name using arguments '''

        found_in_cache = True
        class_only = kwargs.pop('class_only', False)
        collection_list = kwargs.pop('collection_list', None)
        if name in self.aliases:
            name = self.aliases[name]
        name, path = self.find_plugin_with_name(name, collection_list=collection_list)
        if path is None:
            return None

        if path not in self._module_cache:
            self._module_cache[path] = self._load_module_source(name, path)
            self._load_config_defs(name, self._module_cache[path], path)
            found_in_cache = False

        obj = getattr(self._module_cache[path], self.class_name)
        if self.base_class:
            # The import path is hardcoded and should be the right place,
            # so we are not expecting an ImportError.
            module = __import__(self.package, fromlist=[self.base_class])
            # Check whether this obj has the required base class.
            try:
                plugin_class = getattr(module, self.base_class)
            except AttributeError:
                return None
            if not issubclass(obj, plugin_class):
                return None

        self._display_plugin_load(self.class_name, name, self._searched_paths, path, found_in_cache=found_in_cache, class_only=class_only)

        if not class_only:
            try:
                obj = obj(*args, **kwargs)
            except TypeError as e:
                if "abstract" in e.args[0]:
                    # Abstract Base Class.  The found plugin file does not
                    # fully implement the defined interface.
                    return None
                raise

        self._update_object(obj, name, path)
        return obj

    def _display_plugin_load(self, class_name, name, searched_paths, path, found_in_cache=None, class_only=None):
        ''' formats data to display debug info for plugin loading, also avoids processing unless really needed '''
        if C.DEFAULT_DEBUG:
            msg = 'Loading %s \'%s\' from %s' % (class_name, os.path.basename(name), path)

            if len(searched_paths) > 1:
                msg = '%s (searched paths: %s)' % (msg, self.format_paths(searched_paths))

            if found_in_cache or class_only:
                msg = '%s (found_in_cache=%s, class_only=%s)' % (msg, found_in_cache, class_only)

            display.debug(msg)

    def all(self, *args, **kwargs):
        '''
        Iterate through all plugins of this type

        A plugin loader is initialized with a specific type.  This function is an iterator returning
        all of the plugins of that type to the caller.

        :kwarg path_only: If this is set to True, then we return the paths to where the plugins reside
            instead of an instance of the plugin.  This conflicts with class_only and both should
            not be set.
        :kwarg class_only: If this is set to True then we return the python class which implements
            a plugin rather than an instance of the plugin.  This conflicts with path_only and both
            should not be set.
        :kwarg _dedupe: By default, we only return one plugin per plugin name.  Deduplication happens
            in the same way as the :meth:`get` and :meth:`find_plugin` methods resolve which plugin
            should take precedence.  If this is set to False, then we return all of the plugins
            found, including those with duplicate names.  In the case of duplicates, the order in
            which they are returned is the one that would take precedence first, followed by the
            others  in decreasing precedence order.  This should only be used by subclasses which
            want to manage their own deduplication of the plugins.
        :*args: Any extra arguments are passed to each plugin when it is instantiated.
        :**kwargs: Any extra keyword arguments are passed to each plugin when it is instantiated.
        '''
        # TODO: Change the signature of this method to:
        # def all(return_type='instance', args=None, kwargs=None):
        #     if args is None: args = []
        #     if kwargs is None: kwargs = {}
        #     return_type can be instance, class, or path.
        #     These changes will mean that plugin parameters won't conflict with our params and
        #     will also make it impossible to request both a path and a class at the same time.
        #
        #     Move _dedupe to be a class attribute, CUSTOM_DEDUPE, with subclasses for filters and
        #     tests setting it to True

        global _PLUGIN_FILTERS

        dedupe = kwargs.pop('_dedupe', True)
        path_only = kwargs.pop('path_only', False)
        class_only = kwargs.pop('class_only', False)
        # Having both path_only and class_only is a coding bug
        if path_only and class_only:
            raise AnsibleError('Do not set both path_only and class_only when calling PluginLoader.all()')

        all_matches = []
        found_in_cache = True

        for i in self._get_paths():
            all_matches.extend(glob.glob(os.path.join(i, "*.py")))

        loaded_modules = set()
        for path in sorted(all_matches, key=os.path.basename):
            name = os.path.splitext(path)[0]
            basename = os.path.basename(name)

            if basename == '__init__' or basename in _PLUGIN_FILTERS[self.package]:
                continue

            if dedupe and basename in loaded_modules:
                continue
            loaded_modules.add(basename)

            if path_only:
                yield path
                continue

            if path not in self._module_cache:
                try:
                    if self.subdir in ('filter_plugins', 'test_plugins'):
                        # filter and test plugin files can contain multiple plugins
                        # they must have a unique python module name to prevent them from shadowing each other
                        full_name = '{0}_{1}'.format(abs(hash(path)), basename)
                    else:
                        full_name = basename
                    module = self._load_module_source(full_name, path)
                    self._load_config_defs(basename, module, path)
                except Exception as e:
                    display.warning("Skipping plugin (%s) as it seems to be invalid: %s" % (path, to_text(e)))
                    continue
                self._module_cache[path] = module
                found_in_cache = False

            try:
                obj = getattr(self._module_cache[path], self.class_name)
            except AttributeError as e:
                display.warning("Skipping plugin (%s) as it seems to be invalid: %s" % (path, to_text(e)))
                continue

            if self.base_class:
                # The import path is hardcoded and should be the right place,
                # so we are not expecting an ImportError.
                module = __import__(self.package, fromlist=[self.base_class])
                # Check whether this obj has the required base class.
                try:
                    plugin_class = getattr(module, self.base_class)
                except AttributeError:
                    continue
                if not issubclass(obj, plugin_class):
                    continue

            self._display_plugin_load(self.class_name, basename, self._searched_paths, path, found_in_cache=found_in_cache, class_only=class_only)

            if not class_only:
                try:
                    obj = obj(*args, **kwargs)
                except TypeError as e:
                    display.warning("Skipping plugin (%s) as it seems to be incomplete: %s" % (path, to_text(e)))

            self._update_object(obj, basename, path)
            yield obj


class Jinja2Loader(PluginLoader):
    """
    PluginLoader optimized for Jinja2 plugins

    The filter and test plugins are Jinja2 plugins encapsulated inside of our plugin format.
    The way the calling code is setup, we need to do a few things differently in the all() method
    """
    def find_plugin(self, name, collection_list=None):
        # Nothing using Jinja2Loader use this method.  We can't use the base class version because
        # we deduplicate differently than the base class
        if '.' in name:
            return super(Jinja2Loader, self).find_plugin(name, collection_list=collection_list)

        raise AnsibleError('No code should call find_plugin for Jinja2Loaders (Not implemented)')

    def get(self, name, *args, **kwargs):
        # Nothing using Jinja2Loader use this method.  We can't use the base class version because
        # we deduplicate differently than the base class
        if '.' in name:
            return super(Jinja2Loader, self).get(name, *args, **kwargs)

        raise AnsibleError('No code should call find_plugin for Jinja2Loaders (Not implemented)')

    def all(self, *args, **kwargs):
        """
        Differences with :meth:`PluginLoader.all`:

        * We do not deduplicate ansible plugin names.  This is because we don't care about our
          plugin names, here.  We care about the names of the actual jinja2 plugins which are inside
          of our plugins.
        * We reverse the order of the list of plugins compared to other PluginLoaders.  This is
          because of how calling code chooses to sync the plugins from the list.  It adds all the
          Jinja2 plugins from one of our Ansible plugins into a dict.  Then it adds the Jinja2
          plugins from the next Ansible plugin, overwriting any Jinja2 plugins that had the same
          name.  This is an encapsulation violation (the PluginLoader should not know about what
          calling code does with the data) but we're pushing the common code here.  We'll fix
          this in the future by moving more of the common code into this PluginLoader.
        * We return a list.  We could iterate the list instead but that's extra work for no gain because
          the API receiving this doesn't care.  It just needs an iterable
        """
        # We don't deduplicate ansible plugin names.  Instead, calling code deduplicates jinja2
        # plugin names.
        kwargs['_dedupe'] = False

        # We have to instantiate a list of all plugins so that we can reverse it.  We reverse it so
        # that calling code will deduplicate this correctly.
        plugins = [p for p in super(Jinja2Loader, self).all(*args, **kwargs)]
        plugins.reverse()

        return plugins


def _load_plugin_filter():
    filters = defaultdict(frozenset)
    user_set = False
    if C.PLUGIN_FILTERS_CFG is None:
        filter_cfg = '/etc/ansible/plugin_filters.yml'
    else:
        filter_cfg = C.PLUGIN_FILTERS_CFG
        user_set = True

    if os.path.exists(filter_cfg):
        with open(filter_cfg, 'rb') as f:
            try:
                filter_data = from_yaml(f.read())
            except Exception as e:
                display.warning(u'The plugin filter file, {0} was not parsable.'
                                u' Skipping: {1}'.format(filter_cfg, to_text(e)))
                return filters

        try:
            version = filter_data['filter_version']
        except KeyError:
            display.warning(u'The plugin filter file, {0} was invalid.'
                            u' Skipping.'.format(filter_cfg))
            return filters

        # Try to convert for people specifying version as a float instead of string
        version = to_text(version)
        version = version.strip()

        if version == u'1.0':
            # Modules and action plugins share the same blacklist since the difference between the
            # two isn't visible to the users
            try:
                filters['ansible.modules'] = frozenset(filter_data['module_blacklist'])
            except TypeError:
                display.warning(u'Unable to parse the plugin filter file {0} as'
                                u' module_blacklist is not a list.'
                                u' Skipping.'.format(filter_cfg))
                return filters
            filters['ansible.plugins.action'] = filters['ansible.modules']
        else:
            display.warning(u'The plugin filter file, {0} was a version not recognized by this'
                            u' version of Ansible. Skipping.'.format(filter_cfg))
    else:
        if user_set:
            display.warning(u'The plugin filter file, {0} does not exist.'
                            u' Skipping.'.format(filter_cfg))

    # Specialcase the stat module as Ansible can run very few things if stat is blacklisted.
    if 'stat' in filters['ansible.modules']:
        raise AnsibleError('The stat module was specified in the module blacklist file, {0}, but'
                           ' Ansible will not function without the stat module.  Please remove stat'
                           ' from the blacklist.'.format(to_native(filter_cfg)))
    return filters


def _configure_collection_loader():
    if not any((isinstance(l, AnsibleCollectionLoader) for l in sys.meta_path)):
        sys.meta_path.insert(0, AnsibleCollectionLoader(C.config))


# TODO: All of the following is initialization code   It should be moved inside of an initialization
# function which is called at some point early in the ansible and ansible-playbook CLI startup.

_PLUGIN_FILTERS = _load_plugin_filter()

_configure_collection_loader()

# doc fragments first
fragment_loader = PluginLoader(
    'ModuleDocFragment',
    'ansible.plugins.doc_fragments',
    C.DOC_FRAGMENT_PLUGIN_PATH,
    'doc_fragments',
)

action_loader = PluginLoader(
    'ActionModule',
    'ansible.plugins.action',
    C.DEFAULT_ACTION_PLUGIN_PATH,
    'action_plugins',
    required_base_class='ActionBase',
)

cache_loader = PluginLoader(
    'CacheModule',
    'ansible.plugins.cache',
    C.DEFAULT_CACHE_PLUGIN_PATH,
    'cache_plugins',
)

callback_loader = PluginLoader(
    'CallbackModule',
    'ansible.plugins.callback',
    C.DEFAULT_CALLBACK_PLUGIN_PATH,
    'callback_plugins',
)

connection_loader = PluginLoader(
    'Connection',
    'ansible.plugins.connection',
    C.DEFAULT_CONNECTION_PLUGIN_PATH,
    'connection_plugins',
    aliases={'paramiko': 'paramiko_ssh'},
    required_base_class='ConnectionBase',
)

shell_loader = PluginLoader(
    'ShellModule',
    'ansible.plugins.shell',
    'shell_plugins',
    'shell_plugins',
)

module_loader = PluginLoader(
    '',
    'ansible.modules',
    C.DEFAULT_MODULE_PATH,
    'library',
)

module_utils_loader = PluginLoader(
    '',
    'ansible.module_utils',
    C.DEFAULT_MODULE_UTILS_PATH,
    'module_utils',
)

# NB: dedicated loader is currently necessary because PS module_utils expects "with subdir" lookup where
# regular module_utils doesn't. This can be revisited once we have more granular loaders.
ps_module_utils_loader = PluginLoader(
    '',
    'ansible.module_utils',
    C.DEFAULT_MODULE_UTILS_PATH,
    'module_utils',
)

lookup_loader = PluginLoader(
    'LookupModule',
    'ansible.plugins.lookup',
    C.DEFAULT_LOOKUP_PLUGIN_PATH,
    'lookup_plugins',
    required_base_class='LookupBase',
)

filter_loader = Jinja2Loader(
    'FilterModule',
    'ansible.plugins.filter',
    C.DEFAULT_FILTER_PLUGIN_PATH,
    'filter_plugins',
)

test_loader = Jinja2Loader(
    'TestModule',
    'ansible.plugins.test',
    C.DEFAULT_TEST_PLUGIN_PATH,
    'test_plugins'
)

strategy_loader = PluginLoader(
    'StrategyModule',
    'ansible.plugins.strategy',
    C.DEFAULT_STRATEGY_PLUGIN_PATH,
    'strategy_plugins',
    required_base_class='StrategyBase',
)

terminal_loader = PluginLoader(
    'TerminalModule',
    'ansible.plugins.terminal',
    C.DEFAULT_TERMINAL_PLUGIN_PATH,
    'terminal_plugins',
    required_base_class='TerminalBase'
)

vars_loader = PluginLoader(
    'VarsModule',
    'ansible.plugins.vars',
    C.DEFAULT_VARS_PLUGIN_PATH,
    'vars_plugins',
)

cliconf_loader = PluginLoader(
    'Cliconf',
    'ansible.plugins.cliconf',
    C.DEFAULT_CLICONF_PLUGIN_PATH,
    'cliconf_plugins',
    required_base_class='CliconfBase'
)

netconf_loader = PluginLoader(
    'Netconf',
    'ansible.plugins.netconf',
    C.DEFAULT_NETCONF_PLUGIN_PATH,
    'netconf_plugins',
    required_base_class='NetconfBase'
)

inventory_loader = PluginLoader(
    'InventoryModule',
    'ansible.plugins.inventory',
    C.DEFAULT_INVENTORY_PLUGIN_PATH,
    'inventory_plugins'
)

httpapi_loader = PluginLoader(
    'HttpApi',
    'ansible.plugins.httpapi',
    C.DEFAULT_HTTPAPI_PLUGIN_PATH,
    'httpapi_plugins',
    required_base_class='HttpApiBase',
)

become_loader = PluginLoader(
    'BecomeModule',
    'ansible.plugins.become',
    C.BECOME_PLUGIN_PATH,
    'become_plugins'
)
