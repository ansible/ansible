# (c) 2019 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
import os.path
import re
import sys

from types import ModuleType

from ansible.module_utils._text import to_bytes, to_native, to_text
from ansible.module_utils.compat.importlib import import_module
from ansible.module_utils.six import iteritems, string_types, with_metaclass
from ansible.utils.path import cs_open
from ansible.utils.singleton import Singleton

_SYNTHETIC_PACKAGES = {
    # these provide fallback package definitions when there are no on-disk paths
    'ansible_collections': dict(type='pkg_only', allow_external_subpackages=True),
    'ansible_collections.ansible': dict(type='pkg_only', allow_external_subpackages=True),
    # these implement the ansible.builtin synthetic collection mapped to the packages inside the ansible distribution
    'ansible_collections.ansible.builtin': dict(type='pkg_only'),
    'ansible_collections.ansible.builtin.plugins': dict(type='map', map='ansible.plugins'),
    'ansible_collections.ansible.builtin.plugins.module_utils': dict(type='map', map='ansible.module_utils', graft=True),
    'ansible_collections.ansible.builtin.plugins.modules': dict(type='flatmap', flatmap='ansible.modules', graft=True),
}


# FIXME: exception handling/error logging
class AnsibleCollectionLoader(with_metaclass(Singleton, object)):
    def __init__(self, config=None):
        if config:
            self._n_configured_paths = config.get_config_value('COLLECTIONS_PATHS')
        else:
            self._n_configured_paths = os.environ.get('ANSIBLE_COLLECTIONS_PATHS', '').split(os.pathsep)

        if isinstance(self._n_configured_paths, string_types):
            self._n_configured_paths = [self._n_configured_paths]
        elif self._n_configured_paths is None:
            self._n_configured_paths = []

        # expand any placeholders in configured paths
        self._n_configured_paths = [to_native(os.path.expanduser(p), errors='surrogate_or_strict') for p in self._n_configured_paths]

        self._n_playbook_paths = []
        self._default_collection = None
        # pre-inject grafted package maps so we can force them to use the right loader instead of potentially delegating to a "normal" loader
        for syn_pkg_def in (p for p in iteritems(_SYNTHETIC_PACKAGES) if p[1].get('graft')):
            pkg_name = syn_pkg_def[0]
            pkg_def = syn_pkg_def[1]

            newmod = ModuleType(pkg_name)
            newmod.__package__ = pkg_name
            newmod.__file__ = '<ansible_synthetic_collection_package>'
            pkg_type = pkg_def.get('type')

            # TODO: need to rethink map style so we can just delegate all the loading

            if pkg_type == 'flatmap':
                newmod.__loader__ = AnsibleFlatMapLoader(import_module(pkg_def['flatmap']))
            newmod.__path__ = []

            sys.modules[pkg_name] = newmod

    @property
    def n_collection_paths(self):
        return self._n_playbook_paths + self._n_configured_paths

    def get_collection_path(self, collection_name):
        if not AnsibleCollectionRef.is_valid_collection_name(collection_name):
            raise ValueError('{0} is not a valid collection name'.format(to_native(collection_name)))

        m = import_module('ansible_collections.{0}'.format(collection_name))

        return m.__file__

    def set_playbook_paths(self, b_playbook_paths):
        if isinstance(b_playbook_paths, string_types):
            b_playbook_paths = [b_playbook_paths]

        # track visited paths; we have to preserve the dir order as-passed in case there are duplicate collections (first one wins)
        added_paths = set()

        # de-dupe and ensure the paths are native strings (Python seems to do this for package paths etc, so assume it's safe)
        self._n_playbook_paths = [os.path.join(to_native(p), 'collections') for p in b_playbook_paths if not (p in added_paths or added_paths.add(p))]
        # FIXME: only allow setting this once, or handle any necessary cache/package path invalidations internally?

    # FIXME: is there a better place to store this?
    # FIXME: only allow setting this once
    def set_default_collection(self, collection_name):
        self._default_collection = collection_name

    @property
    def default_collection(self):
        return self._default_collection

    def find_module(self, fullname, path=None):
        if self._find_module(fullname, path, load=False)[0]:
            return self

        return None

    def load_module(self, fullname):
        mod = self._find_module(fullname, None, load=True)[1]

        if not mod:
            raise ImportError('module {0} not found'.format(fullname))

        return mod

    def _find_module(self, fullname, path, load):
        # this loader is only concerned with items under the Ansible Collections namespace hierarchy, ignore others
        if not fullname.startswith('ansible_collections.') and fullname != 'ansible_collections':
            return False, None

        if sys.modules.get(fullname):
            if not load:
                return True, None

            return True, sys.modules[fullname]

        newmod = None

        # this loader implements key functionality for Ansible collections
        # * implicit distributed namespace packages for the root Ansible namespace (no pkgutil.extend_path hackery reqd)
        # * implicit package support for Python 2.7 (no need for __init__.py in collections, except to use standard Py2.7 tooling)
        # * preventing controller-side code injection during collection loading
        # * (default loader would execute arbitrary package code from all __init__.py's)

        parent_pkg_name = '.'.join(fullname.split('.')[:-1])

        parent_pkg = sys.modules.get(parent_pkg_name)

        if parent_pkg_name and not parent_pkg:
            raise ImportError('parent package {0} not found'.format(parent_pkg_name))

        # are we at or below the collection level? eg a.mynamespace.mycollection.something.else
        # if so, we don't want distributed namespace behavior; first mynamespace.mycollection on the path is where
        # we'll load everything from (ie, don't fall back to another mynamespace.mycollection lower on the path)
        sub_collection = fullname.count('.') > 1

        synpkg_def = _SYNTHETIC_PACKAGES.get(fullname)
        synpkg_remainder = ''

        if not synpkg_def:
            # if the parent is a grafted package, we have some special work to do, otherwise just look for stuff on disk
            parent_synpkg_def = _SYNTHETIC_PACKAGES.get(parent_pkg_name)
            if parent_synpkg_def and parent_synpkg_def.get('graft'):
                synpkg_def = parent_synpkg_def
                synpkg_remainder = '.' + fullname.rpartition('.')[2]

        # FUTURE: collapse as much of this back to on-demand as possible (maybe stub packages that get replaced when actually loaded?)
        if synpkg_def:
            pkg_type = synpkg_def.get('type')
            if not pkg_type:
                raise KeyError('invalid synthetic package type (no package "type" specified)')
            if pkg_type == 'map':
                map_package = synpkg_def.get('map')

                if not map_package:
                    raise KeyError('invalid synthetic map package definition (no target "map" defined)')

                if not load:
                    return True, None

                mod = import_module(map_package + synpkg_remainder)

                sys.modules[fullname] = mod

                return True, mod
            elif pkg_type == 'flatmap':
                raise NotImplementedError()
            elif pkg_type == 'pkg_only':
                if not load:
                    return True, None

                newmod = ModuleType(fullname)
                newmod.__package__ = fullname
                newmod.__file__ = '<ansible_synthetic_collection_package>'
                newmod.__loader__ = self
                newmod.__path__ = []

                if not synpkg_def.get('allow_external_subpackages'):
                    # if external subpackages are NOT allowed, we're done
                    sys.modules[fullname] = newmod
                    return True, newmod

                # if external subpackages ARE allowed, check for on-disk implementations and return a normal
                # package if we find one, otherwise return the one we created here

        if not parent_pkg:  # top-level package, look for NS subpackages on all collection paths
            package_paths = [self._extend_path_with_ns(p, fullname) for p in self.n_collection_paths]
        else:  # subpackage; search in all subpaths (we'll limit later inside a collection)
            package_paths = [self._extend_path_with_ns(p, fullname) for p in parent_pkg.__path__]

        for candidate_child_path in package_paths:
            code_object = None
            is_package = True
            location = None
            # check for implicit sub-package first
            if os.path.isdir(to_bytes(candidate_child_path)):
                # Py3.x implicit namespace packages don't have a file location, so they don't support get_data
                # (which assumes the parent dir or that the loader has an internal mapping); so we have to provide
                # a bogus leaf file on the __file__ attribute for pkgutil.get_data to strip off
                location = os.path.join(candidate_child_path, '__synthetic__')
            else:
                for source_path in [os.path.join(candidate_child_path, '__init__.py'),
                                    candidate_child_path + '.py']:
                    if not os.path.isfile(to_bytes(source_path)):
                        continue

                    if not load:
                        return True, None

                    with open(to_bytes(source_path), 'rb') as fd:
                        source = fd.read()

                    code_object = compile(source=source, filename=source_path, mode='exec', flags=0, dont_inherit=True)
                    location = source_path
                    is_package = source_path.endswith('__init__.py')
                    break

                if not location:
                    continue

            newmod = ModuleType(fullname)
            newmod.__file__ = location
            newmod.__loader__ = self

            if is_package:
                if sub_collection:  # we never want to search multiple instances of the same collection; use first found
                    newmod.__path__ = [candidate_child_path]
                else:
                    newmod.__path__ = package_paths

                newmod.__package__ = fullname
            else:
                newmod.__package__ = parent_pkg_name

            sys.modules[fullname] = newmod

            if code_object:
                # FIXME: decide cases where we don't actually want to exec the code?
                exec(code_object, newmod.__dict__)

            return True, newmod

        # even if we didn't find one on disk, fall back to a synthetic package if we have one...
        if newmod:
            sys.modules[fullname] = newmod
            return True, newmod

        # FIXME: need to handle the "no dirs present" case for at least the root and synthetic internal collections like ansible.builtin

        return False, None

    @staticmethod
    def _extend_path_with_ns(path, ns):
        ns_path_add = ns.rsplit('.', 1)[-1]

        return os.path.join(path, ns_path_add)

    def get_data(self, filename):
        with cs_open(filename, 'rb') as fd:
            return fd.read()


class AnsibleFlatMapLoader(object):
    _extension_blacklist = ['.pyc', '.pyo']

    def __init__(self, root_package):
        self._root_package = root_package
        self._dirtree = None

    def _init_dirtree(self):
        # FIXME: thread safety
        root_path = os.path.dirname(self._root_package.__file__)
        flat_files = []
        # FIXME: make this a dict of filename->dir for faster direct lookup?
        # FIXME: deal with _ prefixed deprecated files (or require another method for collections?)
        # FIXME: fix overloaded filenames (eg, rename Windows setup to win_setup)
        for root, dirs, files in os.walk(root_path):
            # add all files in this dir that don't have a blacklisted extension
            flat_files.extend(((root, f) for f in files if not any((f.endswith(ext) for ext in self._extension_blacklist))))

        # HACK: Put Windows modules at the end of the list. This makes collection_loader behave
        # the same way as plugin loader, preventing '.ps1' from modules being selected before '.py'
        # modules simply because '.ps1' files may be above '.py' files in the flat_files list.
        #
        # The expected sort order is paths in the order they were in 'flat_files'
        # with paths ending in '/windows' at the end, also in the original order they were
        # in 'flat_files'. The .sort() method is guaranteed to be stable, so original order is preserved.
        flat_files.sort(key=lambda p: p[0].endswith('/windows'))
        self._dirtree = flat_files

    def find_file(self, filename):
        # FIXME: thread safety
        if not self._dirtree:
            self._init_dirtree()

        if '.' not in filename:  # no extension specified, use extension regex to filter
            extensionless_re = re.compile(r'^{0}(\..+)?$'.format(re.escape(filename)))
            # why doesn't Python have first()?
            try:
                # FIXME: store extensionless in a separate direct lookup?
                filepath = next(os.path.join(r, f) for r, f in self._dirtree if extensionless_re.match(f))
            except StopIteration:
                raise IOError("couldn't find {0}".format(filename))
        else:  # actual filename, just look it up
            # FIXME: this case sucks; make it a lookup
            try:
                filepath = next(os.path.join(r, f) for r, f in self._dirtree if f == filename)
            except StopIteration:
                raise IOError("couldn't find {0}".format(filename))

        return filepath

    def get_data(self, filename):
        found_file = self.find_file(filename)

        with open(found_file, 'rb') as fd:
            return fd.read()


# TODO: implement these for easier inline debugging?
#    def get_source(self, fullname):
#    def get_code(self, fullname):
#    def is_package(self, fullname):


class AnsibleCollectionRef:
    # FUTURE: introspect plugin loaders to get these dynamically?
    VALID_REF_TYPES = frozenset(to_text(r) for r in ['action', 'become', 'cache', 'callback', 'cliconf', 'connection',
                                                     'doc_fragments', 'filter', 'httpapi', 'inventory', 'lookup',
                                                     'module_utils', 'modules', 'netconf', 'role', 'shell', 'strategy',
                                                     'terminal', 'test', 'vars'])

    # FIXME: tighten this up to match Python identifier reqs, etc
    VALID_COLLECTION_NAME_RE = re.compile(to_text(r'^(\w+)\.(\w+)$'))
    VALID_SUBDIRS_RE = re.compile(to_text(r'^\w+(\.\w+)*$'))
    VALID_FQCR_RE = re.compile(to_text(r'^\w+\.\w+\.\w+(\.\w+)*$'))  # can have 0-N included subdirs as well

    def __init__(self, collection_name, subdirs, resource, ref_type):
        """
        Create an AnsibleCollectionRef from components
        :param collection_name: a collection name of the form 'namespace.collectionname'
        :param subdirs: optional subdir segments to be appended below the plugin type (eg, 'subdir1.subdir2')
        :param resource: the name of the resource being references (eg, 'mymodule', 'someaction', 'a_role')
        :param ref_type: the type of the reference, eg 'module', 'role', 'doc_fragment'
        """
        collection_name = to_text(collection_name, errors='strict')
        if subdirs is not None:
            subdirs = to_text(subdirs, errors='strict')
        resource = to_text(resource, errors='strict')
        ref_type = to_text(ref_type, errors='strict')

        if not self.is_valid_collection_name(collection_name):
            raise ValueError('invalid collection name (must be of the form namespace.collection): {0}'.format(to_native(collection_name)))

        if ref_type not in self.VALID_REF_TYPES:
            raise ValueError('invalid collection ref_type: {0}'.format(ref_type))

        self.collection = collection_name
        if subdirs:
            if not re.match(self.VALID_SUBDIRS_RE, subdirs):
                raise ValueError('invalid subdirs entry: {0} (must be empty/None or of the form subdir1.subdir2)'.format(to_native(subdirs)))
            self.subdirs = subdirs
        else:
            self.subdirs = u''

        self.resource = resource
        self.ref_type = ref_type

        package_components = [u'ansible_collections', self.collection]

        if self.ref_type == u'role':
            package_components.append(u'roles')
        else:
            # we assume it's a plugin
            package_components += [u'plugins', self.ref_type]

        if self.subdirs:
            package_components.append(self.subdirs)

        if self.ref_type == u'role':
            # roles are their own resource
            package_components.append(self.resource)

        self.n_python_package_name = to_native('.'.join(package_components))

    @staticmethod
    def from_fqcr(ref, ref_type):
        """
        Parse a string as a fully-qualified collection reference, raises ValueError if invalid
        :param ref: collection reference to parse (a valid ref is of the form 'ns.coll.resource' or 'ns.coll.subdir1.subdir2.resource')
        :param ref_type: the type of the reference, eg 'module', 'role', 'doc_fragment'
        :return: a populated AnsibleCollectionRef object
        """
        # assuming the fq_name is of the form (ns).(coll).(optional_subdir_N).(resource_name),
        # we split the resource name off the right, split ns and coll off the left, and we're left with any optional
        # subdirs that need to be added back below the plugin-specific subdir we'll add. So:
        # ns.coll.resource -> ansible_collections.ns.coll.plugins.(plugintype).resource
        # ns.coll.subdir1.resource -> ansible_collections.ns.coll.plugins.subdir1.(plugintype).resource
        # ns.coll.rolename -> ansible_collections.ns.coll.roles.rolename
        if not AnsibleCollectionRef.is_valid_fqcr(ref):
            raise ValueError('{0} is not a valid collection reference'.format(to_native(ref)))

        ref = to_text(ref, errors='strict')
        ref_type = to_text(ref_type, errors='strict')

        resource_splitname = ref.rsplit(u'.', 1)
        package_remnant = resource_splitname[0]
        resource = resource_splitname[1]

        # split the left two components of the collection package name off, anything remaining is plugin-type
        # specific subdirs to be added back on below the plugin type
        package_splitname = package_remnant.split(u'.', 2)
        if len(package_splitname) == 3:
            subdirs = package_splitname[2]
        else:
            subdirs = u''

        collection_name = u'.'.join(package_splitname[0:2])

        return AnsibleCollectionRef(collection_name, subdirs, resource, ref_type)

    @staticmethod
    def try_parse_fqcr(ref, ref_type):
        """
        Attempt to parse a string as a fully-qualified collection reference, returning None on failure (instead of raising an error)
        :param ref: collection reference to parse (a valid ref is of the form 'ns.coll.resource' or 'ns.coll.subdir1.subdir2.resource')
        :param ref_type: the type of the reference, eg 'module', 'role', 'doc_fragment'
        :return: a populated AnsibleCollectionRef object on successful parsing, else None
        """
        try:
            return AnsibleCollectionRef.from_fqcr(ref, ref_type)
        except ValueError:
            pass

    @staticmethod
    def legacy_plugin_dir_to_plugin_type(legacy_plugin_dir_name):
        """
        Utility method to convert from a PluginLoader dir name to a plugin ref_type
        :param legacy_plugin_dir_name: PluginLoader dir name (eg, 'action_plugins', 'library')
        :return: the corresponding plugin ref_type (eg, 'action', 'role')
        """
        legacy_plugin_dir_name = to_text(legacy_plugin_dir_name)

        plugin_type = legacy_plugin_dir_name.replace(u'_plugins', u'')

        if plugin_type == u'library':
            plugin_type = u'modules'

        if plugin_type not in AnsibleCollectionRef.VALID_REF_TYPES:
            raise ValueError('{0} cannot be mapped to a valid collection ref type'.format(to_native(legacy_plugin_dir_name)))

        return plugin_type

    @staticmethod
    def is_valid_fqcr(ref, ref_type=None):
        """
        Validates if is string is a well-formed fully-qualified collection reference (does not look up the collection itself)
        :param ref: candidate collection reference to validate (a valid ref is of the form 'ns.coll.resource' or 'ns.coll.subdir1.subdir2.resource')
        :param ref_type: optional reference type to enable deeper validation, eg 'module', 'role', 'doc_fragment'
        :return: True if the collection ref passed is well-formed, False otherwise
        """

        ref = to_text(ref)

        if not ref_type:
            return bool(re.match(AnsibleCollectionRef.VALID_FQCR_RE, ref))

        return bool(AnsibleCollectionRef.try_parse_fqcr(ref, ref_type))

    @staticmethod
    def is_valid_collection_name(collection_name):
        """
        Validates if the given string is a well-formed collection name (does not look up the collection itself)
        :param collection_name: candidate collection name to validate (a valid name is of the form 'ns.collname')
        :return: True if the collection name passed is well-formed, False otherwise
        """

        collection_name = to_text(collection_name)

        return bool(re.match(AnsibleCollectionRef.VALID_COLLECTION_NAME_RE, collection_name))


def get_collection_role_path(role_name, collection_list=None):
    acr = AnsibleCollectionRef.try_parse_fqcr(role_name, 'role')

    if acr:
        # looks like a valid qualified collection ref; skip the collection_list
        role = acr.resource
        collection_list = [acr.collection]
        subdirs = acr.subdirs
        resource = acr.resource
    elif not collection_list:
        return None  # not a FQ role and no collection search list spec'd, nothing to do
    else:
        resource = role_name  # treat as unqualified, loop through the collection search list to try and resolve
        subdirs = ''

    for collection_name in collection_list:
        try:
            acr = AnsibleCollectionRef(collection_name=collection_name, subdirs=subdirs, resource=resource, ref_type='role')
            # FIXME: error handling/logging; need to catch any import failures and move along

            # FIXME: this line shouldn't be necessary, but py2 pkgutil.get_data is delegating back to built-in loader when it shouldn't
            pkg = import_module(acr.n_python_package_name)

            if pkg is not None:
                # the package is now loaded, get the collection's package and ask where it lives
                path = os.path.dirname(to_bytes(sys.modules[acr.n_python_package_name].__file__, errors='surrogate_or_strict'))
                return resource, to_text(path, errors='surrogate_or_strict'), collection_name

        except IOError:
            continue
        except Exception as ex:
            # FIXME: pick out typical import errors first, then error logging
            continue

    return None


_N_COLLECTION_PATH_RE = re.compile(r'/ansible_collections/([^/]+)/([^/]+)')


def get_collection_name_from_path(path):
    """
    Return the containing collection name for a given path, or None if the path is not below a configured collection, or
    the collection cannot be loaded (eg, the collection is masked by another of the same name higher in the configured
    collection roots).
    :param n_path: native-string path to evaluate for collection containment
    :return: collection name or None
    """
    n_collection_paths = [to_native(os.path.realpath(to_bytes(p))) for p in AnsibleCollectionLoader().n_collection_paths]

    b_path = os.path.realpath(to_bytes(path))
    n_path = to_native(b_path)

    for coll_path in n_collection_paths:
        common_prefix = to_native(os.path.commonprefix([b_path, to_bytes(coll_path)]))
        if common_prefix == coll_path:
            # strip off the common prefix (handle weird testing cases of nested collection roots, eg)
            collection_remnant = n_path[len(coll_path):]
            # commonprefix may include the trailing /, prepend to the remnant if necessary (eg trailing / on root)
            if collection_remnant and collection_remnant[0] != '/':
                collection_remnant = '/' + collection_remnant
            # the path lives under this collection root, see if it maps to a collection
            found_collection = _N_COLLECTION_PATH_RE.search(collection_remnant)
            if not found_collection:
                continue
            n_collection_name = '{0}.{1}'.format(*found_collection.groups())

            loaded_collection_path = AnsibleCollectionLoader().get_collection_path(n_collection_name)

            if not loaded_collection_path:
                return None

            # ensure we're using the canonical real path, with the bogus __synthetic__ stripped off
            b_loaded_collection_path = os.path.dirname(os.path.realpath(to_bytes(loaded_collection_path)))

            # if the collection path prefix matches the path prefix we were passed, it's the same collection that's loaded
            if os.path.commonprefix([b_path, b_loaded_collection_path]) == b_loaded_collection_path:
                return n_collection_name

            return None  # if not, it's a collection, but not the same collection the loader sees, so ignore it


def set_collection_playbook_paths(b_playbook_paths):
    AnsibleCollectionLoader().set_playbook_paths(b_playbook_paths)
