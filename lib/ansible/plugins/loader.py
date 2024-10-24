# (c) 2012, Daniel Hokka Zakrisson <daniel@hozac.com>
# (c) 2012-2014, Michael DeHaan <michael.dehaan@gmail.com> and others
# (c) 2017, Toshio Kuratomi <tkuratomi@ansible.com>
# (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import glob
import os
import os.path
import pkgutil
import sys
import warnings

from collections import defaultdict, namedtuple
from importlib import import_module
from traceback import format_exc

import ansible.module_utils.compat.typing as t

from .filter import AnsibleJinja2Filter
from .test import AnsibleJinja2Test

from ansible import __version__ as ansible_version
from ansible import constants as C
from ansible.errors import AnsibleError, AnsiblePluginCircularRedirect, AnsiblePluginRemovedError, AnsibleCollectionUnsupportedVersionError
from ansible.module_utils.common.text.converters import to_bytes, to_text, to_native
from ansible.module_utils.six import string_types
from ansible.parsing.utils.yaml import from_yaml
from ansible.parsing.yaml.loader import AnsibleLoader
from ansible.plugins import get_plugin_class, MODULE_CACHE, PATH_CACHE, PLUGIN_PATH_CACHE, PY_FILES
from ansible.utils.collection_loader import AnsibleCollectionConfig, AnsibleCollectionRef
from ansible.utils.collection_loader._collection_finder import _AnsibleCollectionFinder, _get_collection_metadata
from ansible.utils.display import Display
from ansible.utils.plugin_docs import add_fragments

# TODO: take the packaging dep, or vendor SpecifierSet?

try:
    from packaging.specifiers import SpecifierSet
    from packaging.version import Version
except ImportError:
    SpecifierSet = None  # type: ignore[misc]
    Version = None  # type: ignore[misc]

import importlib.util

_PLUGIN_FILTERS = defaultdict(frozenset)  # type: t.DefaultDict[str, frozenset]
display = Display()

get_with_context_result = namedtuple('get_with_context_result', ['object', 'plugin_load_context'])


def get_all_plugin_loaders():
    return [(name, obj) for (name, obj) in globals().items() if isinstance(obj, PluginLoader)]


def add_all_plugin_dirs(path):
    """ add any existing plugin dirs in the path provided """
    b_path = os.path.expanduser(to_bytes(path, errors='surrogate_or_strict'))
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


class PluginPathContext(object):
    def __init__(self, path, internal):
        self.path = path
        self.internal = internal


class PluginLoadContext(object):
    def __init__(self):
        self.original_name = None
        self.redirect_list = []
        self.error_list = []
        self.import_error_list = []
        self.load_attempts = []
        self.pending_redirect = None
        self.exit_reason = None
        self.plugin_resolved_path = None
        self.plugin_resolved_name = None
        self.plugin_resolved_collection = None  # empty string for resolved plugins from user-supplied paths
        self.deprecated = False
        self.removal_date = None
        self.removal_version = None
        self.deprecation_warnings = []
        self.resolved = False
        self._resolved_fqcn = None
        self.action_plugin = None

    @property
    def resolved_fqcn(self):
        if not self.resolved:
            return

        if not self._resolved_fqcn:
            final_plugin = self.redirect_list[-1]
            if AnsibleCollectionRef.is_valid_fqcr(final_plugin) and final_plugin.startswith('ansible.legacy.'):
                final_plugin = final_plugin.split('ansible.legacy.')[-1]
            if self.plugin_resolved_collection and not AnsibleCollectionRef.is_valid_fqcr(final_plugin):
                final_plugin = self.plugin_resolved_collection + '.' + final_plugin
            self._resolved_fqcn = final_plugin

        return self._resolved_fqcn

    def record_deprecation(self, name, deprecation, collection_name):
        if not deprecation:
            return self

        # The `or ''` instead of using `.get(..., '')` makes sure that even if the user explicitly
        # sets `warning_text` to `~` (None) or `false`, we still get an empty string.
        warning_text = deprecation.get('warning_text', None) or ''
        removal_date = deprecation.get('removal_date', None)
        removal_version = deprecation.get('removal_version', None)
        # If both removal_date and removal_version are specified, use removal_date
        if removal_date is not None:
            removal_version = None
        warning_text = '{0} has been deprecated.{1}{2}'.format(name, ' ' if warning_text else '', warning_text)

        display.deprecated(warning_text, date=removal_date, version=removal_version, collection_name=collection_name)

        self.deprecated = True
        if removal_date:
            self.removal_date = removal_date
        if removal_version:
            self.removal_version = removal_version
        self.deprecation_warnings.append(warning_text)
        return self

    def resolve(self, resolved_name, resolved_path, resolved_collection, exit_reason, action_plugin):
        self.pending_redirect = None
        self.plugin_resolved_name = resolved_name
        self.plugin_resolved_path = resolved_path
        self.plugin_resolved_collection = resolved_collection
        self.exit_reason = exit_reason
        self.resolved = True
        self.action_plugin = action_plugin
        return self

    def redirect(self, redirect_name):
        self.pending_redirect = redirect_name
        self.exit_reason = 'pending redirect resolution from {0} to {1}'.format(self.original_name, redirect_name)
        self.resolved = False
        return self

    def nope(self, exit_reason):
        self.pending_redirect = None
        self.exit_reason = exit_reason
        self.resolved = False
        return self


class PluginLoader:
    """
    PluginLoader loads plugins from the configured plugin directories.

    It searches for plugins by iterating through the combined list of play basedirs, configured
    paths, and the python path.  The first match is used.
    """

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
        if class_name not in PY_FILES:
            PY_FILES[class_name] = {}

        # hold dirs added at runtime outside of config
        self._extra_dirs = []

        # caches
        self._module_cache = MODULE_CACHE[class_name]
        self._paths = PATH_CACHE[class_name]
        self._py_files = PY_FILES[class_name]
        self._plugin_path_cache = PLUGIN_PATH_CACHE[class_name]
        self._plugin_instance_cache = {} if self.subdir == 'vars_plugins' else None

        self._searched_paths = set()

    @property
    def type(self):
        return AnsibleCollectionRef.legacy_plugin_dir_to_plugin_type(self.subdir)

    def __repr__(self):
        return 'PluginLoader(type={0})'.format(self.type)

    def _clear_caches(self):

        if C.OLD_PLUGIN_CACHE_CLEARING:
            self._paths = None
        else:
            # reset global caches
            MODULE_CACHE[self.class_name] = {}
            PATH_CACHE[self.class_name] = None
            PLUGIN_PATH_CACHE[self.class_name] = defaultdict(dict)
            PY_FILES[self.class_name] = {}

            # reset internal caches
            self._module_cache = MODULE_CACHE[self.class_name]
            self._paths = PATH_CACHE[self.class_name]
            self._plugin_path_cache = PLUGIN_PATH_CACHE[self.class_name]
            self._plugin_instance_cache = {} if self.subdir == 'vars_plugins' else None
            self._py_files = PY_FILES[self.class_name]
            self._searched_paths = set()

    def __setstate__(self, data):
        """
        Deserializer.
        """

        class_name = data.get('class_name')
        package = data.get('package')
        config = data.get('config')
        subdir = data.get('subdir')
        aliases = data.get('aliases')
        base_class = data.get('base_class')

        PATH_CACHE[class_name] = data.get('PATH_CACHE')
        PLUGIN_PATH_CACHE[class_name] = data.get('PLUGIN_PATH_CACHE')
        PY_FILES[class_name] = data.get('PY_FILES')

        self.__init__(class_name, package, config, subdir, aliases, base_class)
        self._extra_dirs = data.get('_extra_dirs', [])
        self._searched_paths = data.get('_searched_paths', set())

    def __getstate__(self):
        """
        Serializer.
        """

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
            PY_FILES=PY_FILES[self.class_name],
        )

    def format_paths(self, paths):
        """ Returns a string suitable for printing of the search path """

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
        """ Gets the path of a Python package """

        if not self.package:
            return []
        if not hasattr(self, 'package_path'):
            m = __import__(self.package)
            parts = self.package.split('.')[1:]
            for parent_mod in parts:
                m = getattr(m, parent_mod)
            self.package_path = to_text(os.path.dirname(m.__file__), errors='surrogate_or_strict')
        if subdirs:
            return self._all_directories(self.package_path)
        return [self.package_path]

    def _get_paths_with_context(self, subdirs=True):
        """ Return a list of PluginPathContext objects to search for plugins in """

        # FIXME: This is potentially buggy if subdirs is sometimes True and sometimes False.
        # In current usage, everything calls this with subdirs=True except for module_utils_loader and ansible-doc
        # which always calls it with subdirs=False. So there currently isn't a problem with this caching.
        if self._paths is not None:
            return self._paths

        ret = [PluginPathContext(p, False) for p in self._extra_dirs]

        # look in any configured plugin paths, allow one level deep for subcategories
        if self.config is not None:
            for path in self.config:
                path = os.path.abspath(os.path.expanduser(path))
                if subdirs:
                    contents = glob.glob("%s/*" % path) + glob.glob("%s/*/*" % path)
                    for c in contents:
                        c = to_text(c, errors='surrogate_or_strict')
                        if os.path.isdir(c) and c not in ret:
                            ret.append(PluginPathContext(c, False))

                path = to_text(path, errors='surrogate_or_strict')
                if path not in ret:
                    ret.append(PluginPathContext(path, False))

        # look for any plugins installed in the package subtree
        # Note package path always gets added last so that every other type of
        # path is searched before it.
        ret.extend([PluginPathContext(p, True) for p in self._get_package_paths(subdirs=subdirs)])

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
        ret.sort(key=lambda p: p.path.endswith('/windows'))

        # cache and return the result
        self._paths = ret
        return ret

    def _get_paths(self, subdirs=True):
        """ Return a list of paths to search for plugins in """

        paths_with_context = self._get_paths_with_context(subdirs=subdirs)
        return [path_with_context.path for path_with_context in paths_with_context]

    def _load_config_defs(self, name, module, path):
        """ Reads plugin docs to find configuration setting definitions, to push to config manager for later use """

        # plugins w/o class name don't support config
        if self.class_name:
            type_name = get_plugin_class(self.class_name)

            # if type name != 'module_doc_fragment':
            if type_name in C.CONFIGURABLE_PLUGINS and not C.config.has_configuration_definition(type_name, name):
                dstring = AnsibleLoader(getattr(module, 'DOCUMENTATION', ''), file_name=path).get_single_data()

                # TODO: allow configurable plugins to use sidecar
                # if not dstring:
                #     filename, cn = find_plugin_docfile( name, type_name, self, [os.path.dirname(path)], C.YAML_DOC_EXTENSIONS)
                #     # TODO: dstring = AnsibleLoader(, file_name=path).get_single_data()

                if dstring:
                    add_fragments(dstring, path, fragment_loader=fragment_loader, is_module=(type_name == 'module'))

                    if 'options' in dstring and isinstance(dstring['options'], dict):
                        C.config.initialize_plugin_configuration_definitions(type_name, name, dstring['options'])
                        display.debug('Loaded config def from plugin (%s/%s)' % (type_name, name))

    def add_directory(self, directory, with_subdir=False):
        """ Adds an additional directory to the search path """

        directory = os.path.realpath(directory)

        if directory is not None:
            if with_subdir:
                directory = os.path.join(directory, self.subdir)
            if directory not in self._extra_dirs:
                # append the directory and invalidate the path cache
                self._extra_dirs.append(directory)
                self._clear_caches()
                display.debug('Added %s to loader search path' % (directory))

    def _query_collection_routing_meta(self, acr, plugin_type, extension=None):
        collection_pkg = import_module(acr.n_python_collection_package_name)
        if not collection_pkg:
            return None

        # FIXME: shouldn't need this...
        try:
            # force any type-specific metadata postprocessing to occur
            import_module(acr.n_python_collection_package_name + '.plugins.{0}'.format(plugin_type))
        except ImportError:
            pass

        # this will be created by the collection PEP302 loader
        collection_meta = getattr(collection_pkg, '_collection_meta', None)

        if not collection_meta:
            return None

        # TODO: add subdirs support
        # check for extension-specific entry first (eg 'setup.ps1')
        # TODO: str/bytes on extension/name munging
        if acr.subdirs:
            subdir_qualified_resource = '.'.join([acr.subdirs, acr.resource])
        else:
            subdir_qualified_resource = acr.resource
        entry = collection_meta.get('plugin_routing', {}).get(plugin_type, {}).get(subdir_qualified_resource + extension, None)
        if not entry:
            # try for extension-agnostic entry
            entry = collection_meta.get('plugin_routing', {}).get(plugin_type, {}).get(subdir_qualified_resource, None)
        return entry

    def _find_fq_plugin(self, fq_name, extension, plugin_load_context, ignore_deprecated=False):
        """Search builtin paths to find a plugin. No external paths are searched,
        meaning plugins inside roles inside collections will be ignored.
        """

        plugin_load_context.resolved = False

        plugin_type = AnsibleCollectionRef.legacy_plugin_dir_to_plugin_type(self.subdir)

        acr = AnsibleCollectionRef.from_fqcr(fq_name, plugin_type)

        # check collection metadata to see if any special handling is required for this plugin
        routing_metadata = self._query_collection_routing_meta(acr, plugin_type, extension=extension)

        action_plugin = None
        # TODO: factor this into a wrapper method
        if routing_metadata:
            deprecation = routing_metadata.get('deprecation', None)

            # this will no-op if there's no deprecation metadata for this plugin
            if not ignore_deprecated:
                plugin_load_context.record_deprecation(fq_name, deprecation, acr.collection)

            tombstone = routing_metadata.get('tombstone', None)

            # FIXME: clean up text gen
            if tombstone:
                removal_date = tombstone.get('removal_date')
                removal_version = tombstone.get('removal_version')
                warning_text = tombstone.get('warning_text') or ''
                warning_text = '{0} has been removed.{1}{2}'.format(fq_name, ' ' if warning_text else '', warning_text)
                removed_msg = display.get_deprecation_message(msg=warning_text, version=removal_version,
                                                              date=removal_date, removed=True,
                                                              collection_name=acr.collection)
                plugin_load_context.removal_date = removal_date
                plugin_load_context.removal_version = removal_version
                plugin_load_context.resolved = True
                plugin_load_context.exit_reason = removed_msg
                raise AnsiblePluginRemovedError(removed_msg, plugin_load_context=plugin_load_context)

            redirect = routing_metadata.get('redirect', None)

            if redirect:
                # Prevent mystery redirects that would be determined by the collections keyword
                if not AnsibleCollectionRef.is_valid_fqcr(redirect):
                    raise AnsibleError(
                        f"Collection {acr.collection} contains invalid redirect for {fq_name}: {redirect}. "
                        "Redirects must use fully qualified collection names."
                    )

                # FIXME: remove once this is covered in debug or whatever
                display.vv("redirecting (type: {0}) {1} to {2}".format(plugin_type, fq_name, redirect))

                # The name doing the redirection is added at the beginning of _resolve_plugin_step,
                # but if the unqualified name is used in conjunction with the collections keyword, only
                # the unqualified name is in the redirect list.
                if fq_name not in plugin_load_context.redirect_list:
                    plugin_load_context.redirect_list.append(fq_name)
                return plugin_load_context.redirect(redirect)
                # TODO: non-FQCN case, do we support `.` prefix for current collection, assume it with no dots, require it for subdirs in current, or ?

            if self.type == 'modules':
                action_plugin = routing_metadata.get('action_plugin')

        n_resource = to_native(acr.resource, errors='strict')
        # we want this before the extension is added
        full_name = '{0}.{1}'.format(acr.n_python_package_name, n_resource)

        if extension:
            n_resource += extension

        pkg = sys.modules.get(acr.n_python_package_name)
        if not pkg:
            # FIXME: there must be cheaper/safer way to do this
            try:
                pkg = import_module(acr.n_python_package_name)
            except ImportError:
                return plugin_load_context.nope('Python package {0} not found'.format(acr.n_python_package_name))

        pkg_path = os.path.dirname(pkg.__file__)

        n_resource_path = os.path.join(pkg_path, n_resource)

        # FIXME: and is file or file link or ...
        if os.path.exists(n_resource_path):
            return plugin_load_context.resolve(
                full_name, to_text(n_resource_path), acr.collection, 'found exact match for {0} in {1}'.format(full_name, acr.collection), action_plugin)

        if extension:
            # the request was extension-specific, don't try for an extensionless match
            return plugin_load_context.nope('no match for {0} in {1}'.format(to_text(n_resource), acr.collection))

        # look for any matching extension in the package location (sans filter)
        found_files = [f
                       for f in glob.iglob(os.path.join(pkg_path, n_resource) + '.*')
                       if os.path.isfile(f) and not f.endswith(C.MODULE_IGNORE_EXTS)]

        if not found_files:
            return plugin_load_context.nope('failed fuzzy extension match for {0} in {1}'.format(full_name, acr.collection))

        found_files = sorted(found_files)  # sort to ensure deterministic results, with the shortest match first

        if len(found_files) > 1:
            display.debug('Found several possible candidates for the plugin but using first: %s' % ','.join(found_files))

        return plugin_load_context.resolve(
            full_name, to_text(found_files[0]), acr.collection,
            'found fuzzy extension match for {0} in {1}'.format(full_name, acr.collection), action_plugin)

    def find_plugin(self, name, mod_type='', ignore_deprecated=False, check_aliases=False, collection_list=None):
        """ Find a plugin named name """
        result = self.find_plugin_with_context(name, mod_type, ignore_deprecated, check_aliases, collection_list)
        if result.resolved and result.plugin_resolved_path:
            return result.plugin_resolved_path

        return None

    def find_plugin_with_context(self, name, mod_type='', ignore_deprecated=False, check_aliases=False, collection_list=None):
        """ Find a plugin named name, returning contextual info about the load, recursively resolving redirection """
        plugin_load_context = PluginLoadContext()
        plugin_load_context.original_name = name
        while True:
            result = self._resolve_plugin_step(name, mod_type, ignore_deprecated, check_aliases, collection_list, plugin_load_context=plugin_load_context)
            if result.pending_redirect:
                if result.pending_redirect in result.redirect_list:
                    raise AnsiblePluginCircularRedirect('plugin redirect loop resolving {0} (path: {1})'.format(result.original_name, result.redirect_list))
                name = result.pending_redirect
                result.pending_redirect = None
                plugin_load_context = result
            else:
                break

        # TODO: smuggle these to the controller when we're in a worker, reduce noise from normal things like missing plugin packages during collection search
        if plugin_load_context.error_list:
            display.warning("errors were encountered during the plugin load for {0}:\n{1}".format(name, plugin_load_context.error_list))

        # TODO: display/return import_error_list? Only useful for forensics...

        # FIXME: store structured deprecation data in PluginLoadContext and use display.deprecate
        # if plugin_load_context.deprecated and C.config.get_config_value('DEPRECATION_WARNINGS'):
        #     for dw in plugin_load_context.deprecation_warnings:
        #         # TODO: need to smuggle these to the controller if we're in a worker context
        #         display.warning('[DEPRECATION WARNING] ' + dw)

        return plugin_load_context

    # FIXME: name bikeshed
    def _resolve_plugin_step(self, name, mod_type='', ignore_deprecated=False,
                             check_aliases=False, collection_list=None, plugin_load_context=PluginLoadContext()):
        if not plugin_load_context:
            raise ValueError('A PluginLoadContext is required')

        plugin_load_context.redirect_list.append(name)
        plugin_load_context.resolved = False

        if name in _PLUGIN_FILTERS[self.package]:
            plugin_load_context.exit_reason = '{0} matched a defined plugin filter'.format(name)
            return plugin_load_context

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

            for candidate_name in candidates:
                try:
                    plugin_load_context.load_attempts.append(candidate_name)
                    # HACK: refactor this properly
                    if candidate_name.startswith('ansible.legacy'):
                        # 'ansible.legacy' refers to the plugin finding behavior used before collections existed.
                        # They need to search 'library' and the various '*_plugins' directories in order to find the file.
                        plugin_load_context = self._find_plugin_legacy(name.removeprefix('ansible.legacy.'),
                                                                       plugin_load_context, ignore_deprecated, check_aliases, suffix)
                    else:
                        # 'ansible.builtin' should be handled here. This means only internal, or builtin, paths are searched.
                        plugin_load_context = self._find_fq_plugin(candidate_name, suffix, plugin_load_context=plugin_load_context,
                                                                   ignore_deprecated=ignore_deprecated)

                        # Pending redirects are added to the redirect_list at the beginning of _resolve_plugin_step.
                        # Once redirects are resolved, ensure the final FQCN is added here.
                        # e.g. 'ns.coll.module' is included rather than only 'module' if a collections list is provided:
                        # - module:
                        #   collections: ['ns.coll']
                        if plugin_load_context.resolved and candidate_name not in plugin_load_context.redirect_list:
                            plugin_load_context.redirect_list.append(candidate_name)

                    if plugin_load_context.resolved or plugin_load_context.pending_redirect:  # if we got an answer or need to chase down a redirect, return
                        return plugin_load_context
                except (AnsiblePluginRemovedError, AnsiblePluginCircularRedirect, AnsibleCollectionUnsupportedVersionError):
                    # these are generally fatal, let them fly
                    raise
                except ImportError as ie:
                    plugin_load_context.import_error_list.append(ie)
                except Exception as ex:
                    # FIXME: keep actual errors, not just assembled messages
                    plugin_load_context.error_list.append(to_native(ex))

            if plugin_load_context.error_list:
                display.debug(msg='plugin lookup for {0} failed; errors: {1}'.format(name, '; '.join(plugin_load_context.error_list)))

            plugin_load_context.exit_reason = 'no matches found for {0}'.format(name)

            return plugin_load_context

        # if we got here, there's no collection list and it's not an FQ name, so do legacy lookup

        return self._find_plugin_legacy(name, plugin_load_context, ignore_deprecated, check_aliases, suffix)

    def _find_plugin_legacy(self, name, plugin_load_context, ignore_deprecated=False, check_aliases=False, suffix=None):
        """Search library and various *_plugins paths in order to find the file.
        This was behavior prior to the existence of collections.
        """
        plugin_load_context.resolved = False

        if check_aliases:
            name = self.aliases.get(name, name)

        # The particular cache to look for modules within.  This matches the
        # requested mod_type
        pull_cache = self._plugin_path_cache[suffix]
        try:
            path_with_context = pull_cache[name]
            plugin_load_context.plugin_resolved_path = path_with_context.path
            plugin_load_context.plugin_resolved_name = name
            plugin_load_context.plugin_resolved_collection = 'ansible.builtin' if path_with_context.internal else ''
            plugin_load_context._resolved_fqcn = ('ansible.builtin.' + name if path_with_context.internal else name)
            plugin_load_context.resolved = True
            return plugin_load_context
        except KeyError:
            # Cache miss.  Now let's find the plugin
            pass

        # TODO: Instead of using the self._paths cache (PATH_CACHE) and
        #       self._searched_paths we could use an iterator.  Before enabling that
        #       we need to make sure we don't want to add additional directories
        #       (add_directory()) once we start using the iterator.
        #       We can use _get_paths_with_context() since add_directory() forces a cache refresh.
        for path_with_context in (p for p in self._get_paths_with_context() if p.path not in self._searched_paths and os.path.isdir(to_bytes(p.path))):
            path = path_with_context.path
            b_path = to_bytes(path)
            display.debug('trying %s' % path)
            plugin_load_context.load_attempts.append(path)
            internal = path_with_context.internal
            try:
                full_paths = (os.path.join(b_path, f) for f in os.listdir(b_path))
            except OSError as e:
                display.warning("Error accessing plugin paths: %s" % to_text(e))

            for full_path in (to_native(f) for f in full_paths if os.path.isfile(f) and not f.endswith(b'__init__.py')):
                full_name = os.path.basename(full_path)

                # HACK: We have no way of executing python byte compiled files as ansible modules so specifically exclude them
                # FIXME: I believe this is only correct for modules and module_utils.
                # For all other plugins we want .pyc and .pyo should be valid
                if any(full_path.endswith(x) for x in C.MODULE_IGNORE_EXTS):
                    continue
                splitname = os.path.splitext(full_name)
                base_name = splitname[0]
                try:
                    extension = splitname[1]
                except IndexError:
                    extension = ''

                # everything downstream expects unicode
                full_path = to_text(full_path, errors='surrogate_or_strict')
                # Module found, now enter it into the caches that match this file
                if base_name not in self._plugin_path_cache['']:
                    self._plugin_path_cache[''][base_name] = PluginPathContext(full_path, internal)

                if full_name not in self._plugin_path_cache['']:
                    self._plugin_path_cache[''][full_name] = PluginPathContext(full_path, internal)

                if base_name not in self._plugin_path_cache[extension]:
                    self._plugin_path_cache[extension][base_name] = PluginPathContext(full_path, internal)

                if full_name not in self._plugin_path_cache[extension]:
                    self._plugin_path_cache[extension][full_name] = PluginPathContext(full_path, internal)

            self._searched_paths.add(path)
            try:
                path_with_context = pull_cache[name]
                plugin_load_context.plugin_resolved_path = path_with_context.path
                plugin_load_context.plugin_resolved_name = name
                plugin_load_context.plugin_resolved_collection = 'ansible.builtin' if path_with_context.internal else ''
                plugin_load_context._resolved_fqcn = 'ansible.builtin.' + name if path_with_context.internal else name
                plugin_load_context.resolved = True
                return plugin_load_context
            except KeyError:
                # Didn't find the plugin in this directory. Load modules from the next one
                pass

        # if nothing is found, try finding alias/deprecated
        if not name.startswith('_'):
            alias_name = '_' + name
            # We've already cached all the paths at this point
            if alias_name in pull_cache:
                path_with_context = pull_cache[alias_name]
                if not ignore_deprecated and not os.path.islink(path_with_context.path):
                    # FIXME: this is not always the case, some are just aliases
                    display.deprecated('%s is kept for backwards compatibility but usage is discouraged. '  # pylint: disable=ansible-deprecated-no-version
                                       'The module documentation details page may explain more about this rationale.' % name.lstrip('_'))
                plugin_load_context.plugin_resolved_path = path_with_context.path
                plugin_load_context.plugin_resolved_name = alias_name
                plugin_load_context.plugin_resolved_collection = 'ansible.builtin' if path_with_context.internal else ''
                plugin_load_context._resolved_fqcn = 'ansible.builtin.' + alias_name if path_with_context.internal else alias_name
                plugin_load_context.resolved = True
                return plugin_load_context

        # last ditch, if it's something that can be redirected, look for a builtin redirect before giving up
        candidate_fqcr = 'ansible.builtin.{0}'.format(name)
        if '.' not in name and AnsibleCollectionRef.is_valid_fqcr(candidate_fqcr):
            return self._find_fq_plugin(fq_name=candidate_fqcr, extension=suffix, plugin_load_context=plugin_load_context, ignore_deprecated=ignore_deprecated)

        return plugin_load_context.nope('{0} is not eligible for last-chance resolution'.format(name))

    def has_plugin(self, name, collection_list=None):
        """ Checks if a plugin named name exists """

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
            # FIXME: this still has issues if the module was previously imported but not "cached",
            #  we should bypass this entire codepath for things that are directly importable
            warnings.simplefilter("ignore", RuntimeWarning)
            spec = importlib.util.spec_from_file_location(to_native(full_name), to_native(path))
            module = importlib.util.module_from_spec(spec)

            # mimic import machinery; make the module-being-loaded available in sys.modules during import
            # and remove if there's a failure...
            sys.modules[full_name] = module

            try:
                spec.loader.exec_module(module)
            except Exception:
                del sys.modules[full_name]
                raise

        return module

    def _update_object(self, obj, name, path, redirected_names=None, resolved=None):

        # set extra info on the module, in case we want it later
        setattr(obj, '_original_path', path)
        setattr(obj, '_load_name', name)
        setattr(obj, '_redirected_names', redirected_names or [])

        names = []
        if resolved:
            names.append(resolved)
        if redirected_names:
            # reverse list so best name comes first
            names.extend(redirected_names[::-1])
        if not names:
            raise AnsibleError(f"Missing FQCN for plugin source {name}")

        setattr(obj, 'ansible_aliases', names)
        setattr(obj, 'ansible_name', names[0])

    def get(self, name, *args, **kwargs):
        return self.get_with_context(name, *args, **kwargs).object

    def get_with_context(self, name, *args, **kwargs):
        """ instantiates a plugin of the given name using arguments """

        found_in_cache = True
        class_only = kwargs.pop('class_only', False)
        collection_list = kwargs.pop('collection_list', None)
        if name in self.aliases:
            name = self.aliases[name]

        if (cached_result := (self._plugin_instance_cache or {}).get(name)) and cached_result[1].resolved:
            # Resolving the FQCN is slow, even if we've passed in the resolved FQCN.
            # Short-circuit here if we've previously resolved this name.
            # This will need to be restricted if non-vars plugins start using the cache, since
            # some non-fqcn plugin need to be resolved again with the collections list.
            return get_with_context_result(*cached_result)

        plugin_load_context = self.find_plugin_with_context(name, collection_list=collection_list)
        if not plugin_load_context.resolved or not plugin_load_context.plugin_resolved_path:
            # FIXME: this is probably an error (eg removed plugin)
            return get_with_context_result(None, plugin_load_context)

        fq_name = plugin_load_context.resolved_fqcn
        if '.' not in fq_name and plugin_load_context.plugin_resolved_collection:
            fq_name = '.'.join((plugin_load_context.plugin_resolved_collection, fq_name))
        resolved_type_name = plugin_load_context.plugin_resolved_name
        path = plugin_load_context.plugin_resolved_path
        if (cached_result := (self._plugin_instance_cache or {}).get(fq_name)) and cached_result[1].resolved:
            # This is unused by vars plugins, but it's here in case the instance cache expands to other plugin types.
            # We get here if we've seen this plugin before, but it wasn't called with the resolved FQCN.
            return get_with_context_result(*cached_result)
        redirected_names = plugin_load_context.redirect_list or []

        if path not in self._module_cache:
            self._module_cache[path] = self._load_module_source(resolved_type_name, path)
            found_in_cache = False

        self._load_config_defs(resolved_type_name, self._module_cache[path], path)

        obj = getattr(self._module_cache[path], self.class_name)

        if self.base_class:
            # The import path is hardcoded and should be the right place,
            # so we are not expecting an ImportError.
            module = __import__(self.package, fromlist=[self.base_class])
            # Check whether this obj has the required base class.
            try:
                plugin_class = getattr(module, self.base_class)
            except AttributeError:
                return get_with_context_result(None, plugin_load_context)
            if not issubclass(obj, plugin_class):
                return get_with_context_result(None, plugin_load_context)

        # FIXME: update this to use the load context
        self._display_plugin_load(self.class_name, resolved_type_name, self._searched_paths, path, found_in_cache=found_in_cache, class_only=class_only)

        if not class_only:
            try:
                # A plugin may need to use its _load_name in __init__ (for example, to set
                # or get options from config), so update the object before using the constructor
                instance = object.__new__(obj)
                self._update_object(instance, resolved_type_name, path, redirected_names, fq_name)
                obj.__init__(instance, *args, **kwargs)  # pylint: disable=unnecessary-dunder-call
                obj = instance
            except TypeError as e:
                if "abstract" in e.args[0]:
                    # Abstract Base Class or incomplete plugin, don't load
                    display.v('Returning not found on "%s" as it has unimplemented abstract methods; %s' % (resolved_type_name, to_native(e)))
                    return get_with_context_result(None, plugin_load_context)
                raise

        self._update_object(obj, resolved_type_name, path, redirected_names, fq_name)
        if self._plugin_instance_cache is not None and getattr(obj, 'is_stateless', False):
            self._plugin_instance_cache[fq_name] = (obj, plugin_load_context)
        elif self._plugin_instance_cache is not None:
            # The cache doubles as the load order, so record the FQCN even if the plugin hasn't set is_stateless = True
            self._plugin_instance_cache[fq_name] = (None, PluginLoadContext())
        return get_with_context_result(obj, plugin_load_context)

    def _display_plugin_load(self, class_name, name, searched_paths, path, found_in_cache=None, class_only=None):
        """ formats data to display debug info for plugin loading, also avoids processing unless really needed """
        if C.DEFAULT_DEBUG:
            msg = 'Loading %s \'%s\' from %s' % (class_name, os.path.basename(name), path)

            if len(searched_paths) > 1:
                msg = '%s (searched paths: %s)' % (msg, self.format_paths(searched_paths))

            if found_in_cache or class_only:
                msg = '%s (found_in_cache=%s, class_only=%s)' % (msg, found_in_cache, class_only)

            display.debug(msg)

    def _get_py_files(self, path):
        if path not in self._py_files:
            self._py_files[path] = glob.glob(to_native(os.path.join(path, "*.py")))
        return self._py_files[path]

    def all(self, *args, **kwargs):
        """
        Iterate through all plugins of this type, in configured paths (no collections)

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
        """
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

        dedupe = kwargs.pop('_dedupe', True)
        path_only = kwargs.pop('path_only', False)
        class_only = kwargs.pop('class_only', False)
        # Having both path_only and class_only is a coding bug
        if path_only and class_only:
            raise AnsibleError('Do not set both path_only and class_only when calling PluginLoader.all()')

        all_matches = []
        found_in_cache = True

        legacy_excluding_builtin = set()
        for path_with_context in self._get_paths_with_context():
            matches = self._get_py_files(path_with_context.path)
            if not path_with_context.internal:
                legacy_excluding_builtin.update(matches)
            # we sort within each path, but keep path precedence from config
            all_matches.extend(sorted(matches, key=os.path.basename))

        loaded_modules = set()
        for path in all_matches:

            name = os.path.splitext(path)[0]
            basename = os.path.basename(name)
            is_j2 = isinstance(self, Jinja2Loader)

            if is_j2:
                ref_name = path
            else:
                ref_name = basename

            if not is_j2 and basename in _PLUGIN_FILTERS[self.package]:
                # j2 plugins get processed in own class, here they would just be container files
                display.debug("'%s' skipped due to a defined plugin filter" % basename)
                continue

            if basename == '__init__' or (basename == 'base' and self.package == 'ansible.plugins.cache'):
                # cache has legacy 'base.py' file, which is wrapper for __init__.py
                display.debug("'%s' skipped due to reserved name" % name)
                continue

            if dedupe and ref_name in loaded_modules:
                # for j2 this is 'same file', other plugins it is basename
                display.debug("'%s' skipped as duplicate" % ref_name)
                continue

            loaded_modules.add(ref_name)

            if path_only:
                yield path
                continue

            if path in legacy_excluding_builtin:
                fqcn = basename
            else:
                fqcn = f"ansible.builtin.{basename}"

            if (cached_result := (self._plugin_instance_cache or {}).get(fqcn)) and cached_result[1].resolved:
                # Here just in case, but we don't call all() multiple times for vars plugins, so this should not be used.
                yield cached_result[0]
                continue

            if path not in self._module_cache:
                if self.type in ('filter', 'test'):
                    # filter and test plugin files can contain multiple plugins
                    # they must have a unique python module name to prevent them from shadowing each other
                    full_name = '{0}_{1}'.format(abs(hash(path)), basename)
                else:
                    full_name = basename

                try:
                    module = self._load_module_source(full_name, path)
                except Exception as e:
                    display.warning("Skipping plugin (%s), cannot load: %s" % (path, to_text(e)))
                    continue

                self._module_cache[path] = module
                found_in_cache = False
            else:
                module = self._module_cache[path]

            self._load_config_defs(basename, module, path)

            try:
                obj = getattr(module, self.class_name)
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

            self._update_object(obj, basename, path, resolved=fqcn)

            if self._plugin_instance_cache is not None:
                needs_enabled = False
                if hasattr(obj, 'REQUIRES_ENABLED'):
                    needs_enabled = obj.REQUIRES_ENABLED
                if not needs_enabled:
                    # Use get_with_context to cache the plugin the first time we see it.
                    self.get_with_context(fqcn)[0]

            yield obj


class Jinja2Loader(PluginLoader):
    """
    PluginLoader optimized for Jinja2 plugins

    The filter and test plugins are Jinja2 plugins encapsulated inside of our plugin format.
    We need to do a few things differently in the base class because of file == plugin
    assumptions and dedupe logic.
    """
    def __init__(self, class_name, package, config, subdir, plugin_wrapper_type, aliases=None, required_base_class=None):
        super(Jinja2Loader, self).__init__(class_name, package, config, subdir, aliases=aliases, required_base_class=required_base_class)
        self._plugin_wrapper_type = plugin_wrapper_type
        self._cached_non_collection_wrappers = {}

    def _clear_caches(self):
        super(Jinja2Loader, self)._clear_caches()
        self._cached_non_collection_wrappers = {}

    def find_plugin(self, name, mod_type='', ignore_deprecated=False, check_aliases=False, collection_list=None):
        raise NotImplementedError('find_plugin is not supported on Jinja2Loader')

    @property
    def method_map_name(self):
        return get_plugin_class(self.class_name) + 's'

    def get_contained_plugins(self, collection, plugin_path, name):

        plugins = []

        full_name = '.'.join(['ansible_collections', collection, 'plugins', self.type, name])
        try:
            # use 'parent' loader class to find files, but cannot return this as it can contain multiple plugins per file
            if plugin_path not in self._module_cache:
                self._module_cache[plugin_path] = self._load_module_source(full_name, plugin_path)
            module = self._module_cache[plugin_path]
            obj = getattr(module, self.class_name)
        except Exception as e:
            raise KeyError('Failed to load %s for %s: %s' % (plugin_path, collection, to_native(e)))

        plugin_impl = obj()
        if plugin_impl is None:
            raise KeyError('Could not find %s.%s' % (collection, name))

        try:
            method_map = getattr(plugin_impl, self.method_map_name)
            plugin_map = method_map().items()
        except Exception as e:
            display.warning("Ignoring %s plugins in '%s' as it seems to be invalid: %r" % (self.type, to_text(plugin_path), e))
            return plugins

        for func_name, func in plugin_map:
            fq_name = '.'.join((collection, func_name))
            full = '.'.join((full_name, func_name))
            plugin = self._plugin_wrapper_type(func)
            if plugin in plugins:
                continue
            self._update_object(plugin, full, plugin_path, resolved=fq_name)
            plugins.append(plugin)

        return plugins

    # FUTURE: now that the resulting plugins are closer, refactor base class method with some extra
    # hooks so we can avoid all the duplicated plugin metadata logic, and also cache the collection results properly here
    def get_with_context(self, name, *args, **kwargs):
        # pop N/A kwargs to avoid passthrough to parent methods
        kwargs.pop('class_only', False)
        kwargs.pop('collection_list', None)

        context = PluginLoadContext()

        # avoid collection path for legacy
        name = name.removeprefix('ansible.legacy.')

        self._ensure_non_collection_wrappers(*args, **kwargs)

        # check for stuff loaded via legacy/builtin paths first
        if known_plugin := self._cached_non_collection_wrappers.get(name):
            context.resolved = True
            context.plugin_resolved_name = name
            context.plugin_resolved_path = known_plugin._original_path
            context.plugin_resolved_collection = 'ansible.builtin' if known_plugin.ansible_name.startswith('ansible.builtin.') else ''
            context._resolved_fqcn = known_plugin.ansible_name
            return get_with_context_result(known_plugin, context)

        plugin = None
        key, leaf_key = get_fqcr_and_name(name)
        seen = set()

        # follow the meta!
        while True:

            if key in seen:
                raise AnsibleError('recursive collection redirect found for %r' % name, 0)
            seen.add(key)

            acr = AnsibleCollectionRef.try_parse_fqcr(key, self.type)
            if not acr:
                raise KeyError('invalid plugin name: {0}'.format(key))

            try:
                ts = _get_collection_metadata(acr.collection)
            except ValueError as e:
                # no collection
                raise KeyError('Invalid plugin FQCN ({0}): {1}'.format(key, to_native(e)))

            # TODO: implement cycle detection (unified across collection redir as well)
            routing_entry = ts.get('plugin_routing', {}).get(self.type, {}).get(leaf_key, {})

            # check deprecations
            deprecation_entry = routing_entry.get('deprecation')
            if deprecation_entry:
                warning_text = deprecation_entry.get('warning_text') or ''
                removal_date = deprecation_entry.get('removal_date')
                removal_version = deprecation_entry.get('removal_version')

                warning_text = f'{self.type.title()} "{key}" has been deprecated.{" " if warning_text else ""}{warning_text}'

                display.deprecated(warning_text, version=removal_version, date=removal_date, collection_name=acr.collection)

            # check removal
            tombstone_entry = routing_entry.get('tombstone')
            if tombstone_entry:
                warning_text = tombstone_entry.get('warning_text') or ''
                removal_date = tombstone_entry.get('removal_date')
                removal_version = tombstone_entry.get('removal_version')

                warning_text = f'{self.type.title()} "{key}" has been removed.{" " if warning_text else ""}{warning_text}'

                exc_msg = display.get_deprecation_message(warning_text, version=removal_version, date=removal_date,
                                                          collection_name=acr.collection, removed=True)

                raise AnsiblePluginRemovedError(exc_msg)

            # check redirects
            redirect = routing_entry.get('redirect', None)
            if redirect:
                if not AnsibleCollectionRef.is_valid_fqcr(redirect):
                    raise AnsibleError(
                        f"Collection {acr.collection} contains invalid redirect for {acr.collection}.{acr.resource}: {redirect}. "
                        "Redirects must use fully qualified collection names."
                    )

                next_key, leaf_key = get_fqcr_and_name(redirect, collection=acr.collection)
                display.vvv('redirecting (type: {0}) {1}.{2} to {3}'.format(self.type, acr.collection, acr.resource, next_key))
                key = next_key
            else:
                break

        try:
            pkg = import_module(acr.n_python_package_name)
        except ImportError as e:
            raise KeyError(to_native(e))

        parent_prefix = acr.collection
        if acr.subdirs:
            parent_prefix = '{0}.{1}'.format(parent_prefix, acr.subdirs)

        try:
            for dummy, module_name, ispkg in pkgutil.iter_modules(pkg.__path__, prefix=parent_prefix + '.'):
                if ispkg:
                    continue

                try:
                    # use 'parent' loader class to find files, but cannot return this as it can contain
                    # multiple plugins per file
                    plugin_impl = super(Jinja2Loader, self).get_with_context(module_name, *args, **kwargs)
                    method_map = getattr(plugin_impl.object, self.method_map_name)
                    plugin_map = method_map().items()
                except Exception as e:
                    display.warning(f"Skipping {self.type} plugins in {module_name}'; an error occurred while loading: {e}")
                    continue

                for func_name, func in plugin_map:
                    fq_name = '.'.join((parent_prefix, func_name))
                    src_name = f"ansible_collections.{acr.collection}.plugins.{self.type}.{acr.subdirs}.{func_name}"
                    # TODO: load  anyways into CACHE so we only match each at end of loop
                    #       the files themselves should already be cached by base class caching of modules(python)
                    if key in (func_name, fq_name):
                        plugin = self._plugin_wrapper_type(func)
                        if plugin:
                            context = plugin_impl.plugin_load_context
                            self._update_object(plugin, src_name, plugin_impl.object._original_path, resolved=fq_name)
                            # context will have filename, which for tests/filters might not be correct
                            context._resolved_fqcn = plugin.ansible_name
                            # FIXME: once we start caching these results, we'll be missing functions that would have loaded later
                            break  # go to next file as it can override if dupe (dont break both loops)

        except AnsiblePluginRemovedError as apre:
            raise AnsibleError(to_native(apre), 0, orig_exc=apre)
        except (AnsibleError, KeyError):
            raise
        except Exception as ex:
            display.warning('An unexpected error occurred during Jinja2 plugin loading: {0}'.format(to_native(ex)))
            display.vvv('Unexpected error during Jinja2 plugin loading: {0}'.format(format_exc()))
            raise AnsibleError(to_native(ex), 0, orig_exc=ex)

        return get_with_context_result(plugin, context)

    def all(self, *args, **kwargs):
        kwargs.pop('_dedupe', None)
        path_only = kwargs.pop('path_only', False)
        class_only = kwargs.pop('class_only', False)  # basically ignored for test/filters since they are functions

        # Having both path_only and class_only is a coding bug
        if path_only and class_only:
            raise AnsibleError('Do not set both path_only and class_only when calling PluginLoader.all()')

        self._ensure_non_collection_wrappers(*args, **kwargs)
        if path_only:
            yield from (w._original_path for w in self._cached_non_collection_wrappers.values())
        else:
            yield from (w for w in self._cached_non_collection_wrappers.values())

    def _ensure_non_collection_wrappers(self, *args, **kwargs):
        if self._cached_non_collection_wrappers:
            return

        # get plugins from files in configured paths (multiple in each)
        for p_map in super(Jinja2Loader, self).all(*args, **kwargs):
            is_builtin = p_map.ansible_name.startswith('ansible.builtin.')

            # p_map is really object from file with class that holds multiple plugins
            plugins_list = getattr(p_map, self.method_map_name)
            try:
                plugins = plugins_list()
            except Exception as e:
                display.vvvv("Skipping %s plugins in '%s' as it seems to be invalid: %r" % (self.type, to_text(p_map._original_path), e))
                continue

            for plugin_name in plugins.keys():
                if '.' in plugin_name:
                    display.debug(f'{plugin_name} skipped in {p_map._original_path}; Jinja plugin short names may not contain "."')
                    continue

                if plugin_name in _PLUGIN_FILTERS[self.package]:
                    display.debug("%s skipped due to a defined plugin filter" % plugin_name)
                    continue

                # the plugin class returned by the loader may host multiple Jinja plugins, but we wrap each plugin in
                # its own surrogate wrapper instance here to ease the bookkeeping...
                wrapper = self._plugin_wrapper_type(plugins[plugin_name])
                fqcn = plugin_name
                collection = '.'.join(p_map.ansible_name.split('.')[:2]) if p_map.ansible_name.count('.') >= 2 else ''
                if not plugin_name.startswith(collection):
                    fqcn = f"{collection}.{plugin_name}"

                self._update_object(wrapper, plugin_name, p_map._original_path, resolved=fqcn)

                target_names = {plugin_name, fqcn}
                if is_builtin:
                    target_names.add(f'ansible.builtin.{plugin_name}')

                for target_name in target_names:
                    if existing_plugin := self._cached_non_collection_wrappers.get(target_name):
                        display.debug(f'Jinja plugin {target_name} from {p_map._original_path} skipped; '
                                      f'shadowed by plugin from {existing_plugin._original_path})')
                        continue

                    self._cached_non_collection_wrappers[target_name] = wrapper


def get_fqcr_and_name(resource, collection='ansible.builtin'):
    if '.' not in resource:
        name = resource
        fqcr = collection + '.' + resource
    else:
        name = resource.split('.')[-1]
        fqcr = resource

    return fqcr, name


def _load_plugin_filter():
    filters = _PLUGIN_FILTERS
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

        # Modules and action plugins share the same reject list since the difference between the
        # two isn't visible to the users
        if version == u'1.0':
            try:
                filters['ansible.modules'] = frozenset(filter_data['module_rejectlist'])
            except TypeError:
                display.warning(u'Unable to parse the plugin filter file {0} as'
                                u' module_rejectlist is not a list.'
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

    # Special case: the stat module as Ansible can run very few things if stat is rejected
    if 'stat' in filters['ansible.modules']:
        raise AnsibleError('The stat module was specified in the module reject list file, {0}, but'
                           ' Ansible will not function without the stat module.  Please remove stat'
                           ' from the reject list.'.format(to_native(filter_cfg)))
    return filters


# since we don't want the actual collection loader understanding metadata, we'll do it in an event handler
def _on_collection_load_handler(collection_name, collection_path):
    display.vvvv(to_text('Loading collection {0} from {1}'.format(collection_name, collection_path)))

    collection_meta = _get_collection_metadata(collection_name)

    try:
        if not _does_collection_support_ansible_version(collection_meta.get('requires_ansible', ''), ansible_version):
            mismatch_behavior = C.config.get_config_value('COLLECTIONS_ON_ANSIBLE_VERSION_MISMATCH')
            message = 'Collection {0} does not support Ansible version {1}'.format(collection_name, ansible_version)
            if mismatch_behavior == 'warning':
                display.warning(message)
            elif mismatch_behavior == 'error':
                raise AnsibleCollectionUnsupportedVersionError(message)
    except AnsibleError:
        raise
    except Exception as ex:
        display.warning('Error parsing collection metadata requires_ansible value from collection {0}: {1}'.format(collection_name, ex))


def _does_collection_support_ansible_version(requirement_string, ansible_version):
    if not requirement_string:
        return True

    if not SpecifierSet:
        display.warning('packaging Python module unavailable; unable to validate collection Ansible version requirements')
        return True

    ss = SpecifierSet(requirement_string)

    # ignore prerelease/postrelease/beta/dev flags for simplicity
    base_ansible_version = Version(ansible_version).base_version

    return ss.contains(base_ansible_version)


def _configure_collection_loader(prefix_collections_path=None):
    if AnsibleCollectionConfig.collection_finder:
        # this must be a Python warning so that it can be filtered out by the import sanity test
        warnings.warn('AnsibleCollectionFinder has already been configured')
        return

    if prefix_collections_path is None:
        prefix_collections_path = []

    paths = list(prefix_collections_path) + C.COLLECTIONS_PATHS
    finder = _AnsibleCollectionFinder(paths, C.COLLECTIONS_SCAN_SYS_PATH)
    finder._install()

    # this should succeed now
    AnsibleCollectionConfig.on_collection_load += _on_collection_load_handler


def init_plugin_loader(prefix_collections_path=None):
    """Initialize the plugin filters and the collection loaders

    This method must be called to configure and insert the collection python loaders
    into ``sys.meta_path`` and ``sys.path_hooks``.

    This method is only called in ``CLI.run`` after CLI args have been parsed, so that
    instantiation of the collection finder can utilize parsed CLI args, and to not cause
    side effects.
    """
    _load_plugin_filter()
    _configure_collection_loader(prefix_collections_path)


# TODO: Evaluate making these class instantiations lazy, but keep them in the global scope

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
    AnsibleJinja2Filter
)

test_loader = Jinja2Loader(
    'TestModule',
    'ansible.plugins.test',
    C.DEFAULT_TEST_PLUGIN_PATH,
    'test_plugins',
    AnsibleJinja2Test
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
