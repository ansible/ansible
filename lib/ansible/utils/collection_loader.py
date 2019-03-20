# (c) 2019 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os.path
import pkgutil
import re
import sys

from importlib import import_module
from types import ModuleType

from ansible import constants as C
from ansible.module_utils._text import to_native
from ansible.module_utils.six import iteritems, string_types

_SYNTHETIC_PACKAGES = {
    'ansible_collections.ansible': dict(type='pkg_only'),
    'ansible_collections.ansible.core': dict(type='pkg_only'),
    'ansible_collections.ansible.core.plugins': dict(type='map', map='ansible.plugins'),
    'ansible_collections.ansible.core.plugins.module_utils': dict(type='map', map='ansible.module_utils', graft=True),
    'ansible_collections.ansible.core.plugins.modules': dict(type='flatmap', flatmap='ansible.modules', graft=True),
}

# TODO: tighten this up to subset Python identifier requirements
_collection_role_name_re = re.compile(r'^(\w+)\.(\w+)\.(\w+)$')


# FIXME: exception handling/error logging
class AnsibleCollectionLoader(object):
    def __init__(self):
        self._configured_paths = C.config.get_config_value('INSTALLED_CONTENT_ROOTS')

        if isinstance(self._configured_paths, string_types):
            self._configured_paths = [self._configured_paths]
        elif self._configured_paths is None:
            self._configured_paths = []

        # expand any placeholders in configured paths
        self._configured_paths = [os.path.expanduser(p) for p in self._configured_paths]

        self._playbook_paths = []
        # pre-inject grafted package maps so we can force them to use the right loader instead of potentially delegating to a "normal" loader
        for p in (p for p in iteritems(_SYNTHETIC_PACKAGES) if p[1].get('graft')):
            pkg_name = p[0]
            pkg_def = p[1]

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
    def _collection_paths(self):
        return self._playbook_paths + self._configured_paths

    def set_playbook_paths(self, playbook_paths):
        if isinstance(playbook_paths, string_types):
            playbook_paths = [playbook_paths]

        added_paths = set()

        # de-dupe and ensure the paths are native strings (Python seems to do this for package paths etc, so assume it's safe)
        self._playbook_paths = [to_native(p) for p in playbook_paths if not (p in added_paths or added_paths.add(p))]
        # FIXME: only allow setting this once, or handle any necessary cache/package path invalidations internally?

    def find_module(self, fullname, path=None):
        # this loader is only concerned with items under the Ansible Collections namespace hierarchy, ignore others
        if fullname.startswith('ansible_collections.') or fullname == 'ansible_collections':
            return self

        return None

    def load_module(self, fullname):
        if sys.modules.get(fullname):
            return sys.modules[fullname]

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

        # FIXME: collapse as much of this back to on-demand as possible (maybe stub packages that get replaced when actually loaded?)
        if synpkg_def:
            pkg_type = synpkg_def.get('type')
            if not pkg_type:
                raise KeyError('invalid synthetic package type (no package "type" specified)')
            if pkg_type == 'map':
                map_package = synpkg_def.get('map')

                if not map_package:
                    raise KeyError('invalid synthetic map package definition (no target "map" defined)')
                mod = import_module(map_package)

                sys.modules[fullname] = mod

                return mod
            elif pkg_type == 'flatmap':
                raise NotImplementedError()
            elif pkg_type == 'pkg_only':
                newmod = ModuleType(fullname)
                newmod.__package__ = fullname
                newmod.__file__ = '<ansible_synthetic_collection_package>'
                newmod.__loader__ = self
                newmod.__path__ = []

                sys.modules[fullname] = newmod

                return newmod

        if not parent_pkg:  # top-level package, look for NS subpackages on all collection paths
            package_paths = [self._extend_path_with_ns(p, fullname) for p in self._collection_paths]
        else:  # subpackage; search in all subpaths (we'll limit later inside a collection)
            package_paths = [self._extend_path_with_ns(p, fullname) for p in parent_pkg.__path__]

        for candidate_child_path in package_paths:
            source = None
            is_package = True
            location = None
            # check for implicit sub-package first
            if os.path.isdir(candidate_child_path):
                # Py3.x implicit namespace packages don't have a file location, so they don't support get_data
                # (which assumes the parent dir or that the loader has an internal mapping); so we have to provide
                # a bogus leaf file on the __file__ attribute for pkgutil.get_data to strip off
                location = os.path.join(candidate_child_path, '__synthetic__')
            else:
                for source_path in [os.path.join(candidate_child_path, '__init__.py'),
                                    candidate_child_path + '.py']:
                    if os.path.isfile(source_path):
                        with open(source_path, 'rb') as fd:
                            source = fd.read()
                        location = source_path
                        is_package = source_path.endswith('__init__.py')
                        break
                if not location:
                    continue

            newmod = ModuleType(fullname)
            newmod.__package__ = fullname
            newmod.__file__ = location
            newmod.__loader__ = self

            if is_package:
                if sub_collection:  # we never want to search multiple instances of the same collection; use first found
                    newmod.__path__ = [candidate_child_path]
                else:
                    newmod.__path__ = package_paths

            if source:
                # FIXME: decide cases where we don't actually want to exec the code?
                exec(source, newmod.__dict__)

            sys.modules[fullname] = newmod

            return newmod

        # FIXME: need to handle the "no dirs present" case for at least the root and synthetic internal collections like ansible.core

        return None

    @staticmethod
    def _extend_path_with_ns(path, ns):
        ns_path_add = ns.rsplit('.', 1)[-1]

        return os.path.join(path, ns_path_add)

    def get_data(self, filename):
        with open(filename, 'rb') as fd:
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
            data = fd.read()

        return data


# TODO: implement these for easier inline debugging?
#    def get_source(self, fullname):
#    def get_code(self, fullname):
#    def is_package(self, fullname):


def is_collection_qualified_role_name(candidate_name):
    """
    Returns true if a name looks like a collection-qualified name (eg, ns.collection.rolename)
    """
    if _collection_role_name_re.match(candidate_name):
        return True

    return False


def get_collection_role_path(role_name, collection_list=None):
    match = _collection_role_name_re.match(role_name)

    if match:
        grps = match.groups()
        collection_list = ['.'.join([grps[0], grps[1]])]
        role = grps[2]
    elif not collection_list:
        return None  # not a FQ role and no collection search list spec'd, nothing to do
    else:
        role = role_name

    for collection_name in collection_list:
        try:
            role_package = 'ansible_collections.{0}.roles.{1}'.format(collection_name, role)

            # FIXME: we need to be able to enumerate/query collections here without the risk of loading arbitrary module init code along the way
            # should we just ask the collections loader directly now?
            # FIXME: roles don't have to have tasks/main.y?ml anymore, just load the package itself?
            # FIXME: error handling; need to catch any import failures and move along
            tasks_file = pkgutil.get_data(role_package + '.tasks', 'main.yml')

            if tasks_file is not None:
                # the package is now loaded, get the collection's package and ask where it lives
                path = os.path.dirname(sys.modules[role_package].__file__)
                return role, path, collection_name

        except IOError:
            continue
        except Exception as ex:
            # FIXME: pick out typical import errors first, then error logging
            continue

    return None


def set_collection_playbook_paths(playbook_paths):
    # set for any/all AnsibleCollectionLoader instance(s) on meta_path
    for l in (l for l in sys.meta_path if isinstance(l, AnsibleCollectionLoader)):
        l.set_playbook_paths(playbook_paths)
