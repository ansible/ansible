# (c) 2019 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import sys
import os.path

from importlib import import_module
from types import ModuleType

from ansible import constants as C
from ansible.module_utils.six import string_types

_SYNTHETIC_PACKAGES = {
    'a.ansible': dict(type='pkg_only'),
    'a.ansible.core': dict(type='pkg_only'),
    'a.ansible.core.plugins': dict(type='map', map='ansible.plugins'),
    'a.ansible.core.plugins.module_utils': dict(type='map', map='ansible.module_utils'),
    'a.ansible.core.plugins.modules': dict(type='flatmap', flatmap='ansible.modules'),
}


class AnsibleCollectionLoader(object):
    def __init__(self):
        self._configured_paths = C.config.get_config_value('INSTALLED_CONTENT_ROOTS')
        self._playbook_paths = []

    @property
    def _collection_paths(self):
        return self._playbook_paths + self._configured_paths

    def set_playbook_paths(self, playbook_paths):
        if isinstance(playbook_paths, string_types):
            playbook_paths = [playbook_paths]

        added_paths = set()

        # de-dupe
        self._playbook_paths = [p for p in playbook_paths if not (p in added_paths or added_paths.add(p))]
        # FIXME: only allow setting this once, or handle any necessary cache/package path invalidations internally?

    def find_module(self, fullname, path=None):
        # this loader is only concerned with items under the Ansible Collections namespace hierarchy, ignore others
        if fullname.startswith('a.') or fullname == 'a':
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
                exec (source, newmod.__dict__)

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

# TODO: implement these for easier inline debugging?
#    def get_source(self, fullname):
#    def get_code(self, fullname):
#    def is_package(self, fullname):


def set_collection_playbook_paths(playbook_paths):
    # set for any/all AnsibleCollectionLoader instance(s) on meta_path
    for l in (l for l in sys.meta_path if isinstance(l, AnsibleCollectionLoader)):
        l.set_playbook_paths(playbook_paths)
