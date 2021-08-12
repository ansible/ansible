# (c) 2019 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# CAUTION: There are two implementations of the collection loader.
#          They must be kept functionally identical, although their implementations may differ.
#
# 1) The controller implementation resides in the "lib/ansible/utils/collection_loader/" directory.
#    It must function on all Python versions supported on the controller.
# 2) The ansible-test implementation resides in the "test/lib/ansible_test/_util/target/legacy_collection_loader/" directory.
#    It must function on all Python versions supported on managed hosts which are not supported by the controller.

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
import os.path
import pkgutil
import re
import sys
from keyword import iskeyword
from tokenize import Name as _VALID_IDENTIFIER_REGEX


# DO NOT add new non-stdlib import deps here, this loader is used by external tools (eg ansible-test import sanity)
# that only allow stdlib and module_utils
from ansible.module_utils.common.text.converters import to_native, to_text, to_bytes
from ansible.module_utils.six import string_types, PY3
from ._collection_config import AnsibleCollectionConfig

from contextlib import contextmanager
from types import ModuleType

try:
    from importlib import import_module
except ImportError:
    def import_module(name):
        __import__(name)
        return sys.modules[name]

try:
    from importlib import reload as reload_module
except ImportError:
    # 2.7 has a global reload function instead...
    reload_module = reload  # pylint:disable=undefined-variable

# NB: this supports import sanity test providing a different impl
try:
    from ._collection_meta import _meta_yml_to_dict
except ImportError:
    _meta_yml_to_dict = None


if not hasattr(__builtins__, 'ModuleNotFoundError'):
    # this was introduced in Python 3.6
    ModuleNotFoundError = ImportError


_VALID_IDENTIFIER_STRING_REGEX = re.compile(
    ''.join((_VALID_IDENTIFIER_REGEX, r'\Z')),
)


try:  # NOTE: py3/py2 compat
    # py2 mypy can't deal with try/excepts
    is_python_identifier = str.isidentifier  # type: ignore[attr-defined]
except AttributeError:  # Python 2
    def is_python_identifier(tested_str):  # type: (str) -> bool
        """Determine whether the given string is a Python identifier."""
        # Ref: https://stackoverflow.com/a/55802320/595220
        return bool(re.match(_VALID_IDENTIFIER_STRING_REGEX, tested_str))


PB_EXTENSIONS = ('.yml', '.yaml')


class _AnsibleCollectionFinder:
    def __init__(self, paths=None, scan_sys_paths=True):
        # TODO: accept metadata loader override
        self._ansible_pkg_path = to_native(os.path.dirname(to_bytes(sys.modules['ansible'].__file__)))

        if isinstance(paths, string_types):
            paths = [paths]
        elif paths is None:
            paths = []

        # expand any placeholders in configured paths
        paths = [os.path.expanduser(to_native(p, errors='surrogate_or_strict')) for p in paths]

        # add syspaths if needed
        if scan_sys_paths:
            paths.extend(sys.path)

        good_paths = []
        # expand any placeholders in configured paths
        for p in paths:

            # ensure we always have ansible_collections
            if os.path.basename(p) == 'ansible_collections':
                p = os.path.dirname(p)

            if p not in good_paths and os.path.isdir(to_bytes(os.path.join(p, 'ansible_collections'), errors='surrogate_or_strict')):
                good_paths.append(p)

        self._n_configured_paths = good_paths
        self._n_cached_collection_paths = None
        self._n_cached_collection_qualified_paths = None

        self._n_playbook_paths = []

    @classmethod
    def _remove(cls):
        for mps in sys.meta_path:
            if isinstance(mps, _AnsibleCollectionFinder):
                sys.meta_path.remove(mps)

        # remove any path hooks that look like ours
        for ph in sys.path_hooks:
            if hasattr(ph, '__self__') and isinstance(ph.__self__, _AnsibleCollectionFinder):
                sys.path_hooks.remove(ph)

        # zap any cached path importer cache entries that might refer to us
        sys.path_importer_cache.clear()

        AnsibleCollectionConfig._collection_finder = None

        # validate via the public property that we really killed it
        if AnsibleCollectionConfig.collection_finder is not None:
            raise AssertionError('_AnsibleCollectionFinder remove did not reset AnsibleCollectionConfig.collection_finder')

    def _install(self):
        self._remove()
        sys.meta_path.insert(0, self)

        sys.path_hooks.insert(0, self._ansible_collection_path_hook)

        AnsibleCollectionConfig.collection_finder = self

    def _ansible_collection_path_hook(self, path):
        path = to_native(path)
        interesting_paths = self._n_cached_collection_qualified_paths
        if not interesting_paths:
            interesting_paths = []
            for p in self._n_collection_paths:
                if os.path.basename(p) != 'ansible_collections':
                    p = os.path.join(p, 'ansible_collections')

                if p not in interesting_paths:
                    interesting_paths.append(p)

            interesting_paths.insert(0, self._ansible_pkg_path)
            self._n_cached_collection_qualified_paths = interesting_paths

        if any(path.startswith(p) for p in interesting_paths):
            return _AnsiblePathHookFinder(self, path)

        raise ImportError('not interested')

    @property
    def _n_collection_paths(self):
        paths = self._n_cached_collection_paths
        if not paths:
            self._n_cached_collection_paths = paths = self._n_playbook_paths + self._n_configured_paths
        return paths

    def set_playbook_paths(self, playbook_paths):
        if isinstance(playbook_paths, string_types):
            playbook_paths = [playbook_paths]

        # track visited paths; we have to preserve the dir order as-passed in case there are duplicate collections (first one wins)
        added_paths = set()

        # de-dupe
        self._n_playbook_paths = [os.path.join(to_native(p), 'collections') for p in playbook_paths if not (p in added_paths or added_paths.add(p))]
        self._n_cached_collection_paths = None
        # HACK: playbook CLI sets this relatively late, so we've already loaded some packages whose paths might depend on this. Fix those up.
        # NB: this should NOT be used for late additions; ideally we'd fix the playbook dir setup earlier in Ansible init
        # to prevent this from occurring
        for pkg in ['ansible_collections', 'ansible_collections.ansible']:
            self._reload_hack(pkg)

    def _reload_hack(self, fullname):
        m = sys.modules.get(fullname)
        if not m:
            return
        reload_module(m)

    def find_module(self, fullname, path=None):
        # Figure out what's being asked for, and delegate to a special-purpose loader

        split_name = fullname.split('.')
        toplevel_pkg = split_name[0]
        module_to_find = split_name[-1]
        part_count = len(split_name)

        if toplevel_pkg not in ['ansible', 'ansible_collections']:
            # not interested in anything other than ansible_collections (and limited cases under ansible)
            return None

        # sanity check what we're getting from import, canonicalize path values
        if part_count == 1:
            if path:
                raise ValueError('path should not be specified for top-level packages (trying to find {0})'.format(fullname))
            else:
                # seed the path to the configured collection roots
                path = self._n_collection_paths

        if part_count > 1 and path is None:
            raise ValueError('path must be specified for subpackages (trying to find {0})'.format(fullname))

        # NB: actual "find"ing is delegated to the constructors on the various loaders; they'll ImportError if not found
        try:
            if toplevel_pkg == 'ansible':
                # something under the ansible package, delegate to our internal loader in case of redirections
                return _AnsibleInternalRedirectLoader(fullname=fullname, path_list=path)
            if part_count == 1:
                return _AnsibleCollectionRootPkgLoader(fullname=fullname, path_list=path)
            if part_count == 2:  # ns pkg eg, ansible_collections, ansible_collections.somens
                return _AnsibleCollectionNSPkgLoader(fullname=fullname, path_list=path)
            elif part_count == 3:  # collection pkg eg, ansible_collections.somens.somecoll
                return _AnsibleCollectionPkgLoader(fullname=fullname, path_list=path)
            # anything below the collection
            return _AnsibleCollectionLoader(fullname=fullname, path_list=path)
        except ImportError:
            # TODO: log attempt to load context
            return None


# Implements a path_hook finder for iter_modules (since it's only path based). This finder does not need to actually
# function as a finder in most cases, since our meta_path finder is consulted first for *almost* everything, except
# pkgutil.iter_modules, and under py2, pkgutil.get_data if the parent package passed has not been loaded yet.
class _AnsiblePathHookFinder:
    def __init__(self, collection_finder, pathctx):
        # when called from a path_hook, find_module doesn't usually get the path arg, so this provides our context
        self._pathctx = to_native(pathctx)
        self._collection_finder = collection_finder
        if PY3:
            # cache the native FileFinder (take advantage of its filesystem cache for future find/load requests)
            self._file_finder = None

    # class init is fun- this method has a self arg that won't get used
    def _get_filefinder_path_hook(self=None):
        _file_finder_hook = None
        if PY3:
            # try to find the FileFinder hook to call for fallback path-based imports in Py3
            _file_finder_hook = [ph for ph in sys.path_hooks if 'FileFinder' in repr(ph)]
            if len(_file_finder_hook) != 1:
                raise Exception('need exactly one FileFinder import hook (found {0})'.format(len(_file_finder_hook)))
            _file_finder_hook = _file_finder_hook[0]

        return _file_finder_hook

    _filefinder_path_hook = _get_filefinder_path_hook()

    def find_module(self, fullname, path=None):
        # we ignore the passed in path here- use what we got from the path hook init
        split_name = fullname.split('.')
        toplevel_pkg = split_name[0]

        if toplevel_pkg == 'ansible_collections':
            # collections content? delegate to the collection finder
            return self._collection_finder.find_module(fullname, path=[self._pathctx])
        else:
            # Something else; we'd normally restrict this to `ansible` descendent modules so that any weird loader
            # behavior that arbitrary Python modules have can be serviced by those loaders. In some dev/test
            # scenarios (eg a venv under a collection) our path_hook signs us up to load non-Ansible things, and
            # it's too late by the time we've reached this point, but also too expensive for the path_hook to figure
            # out what we *shouldn't* be loading with the limited info it has. So we'll just delegate to the
            # normal path-based loader as best we can to service it. This also allows us to take advantage of Python's
            # built-in FS caching and byte-compilation for most things.
            if PY3:
                # create or consult our cached file finder for this path
                if not self._file_finder:
                    try:
                        self._file_finder = _AnsiblePathHookFinder._filefinder_path_hook(self._pathctx)
                    except ImportError:
                        # FUTURE: log at a high logging level? This is normal for things like python36.zip on the path, but
                        # might not be in some other situation...
                        return None

                spec = self._file_finder.find_spec(fullname)
                if not spec:
                    return None
                return spec.loader
            else:
                # call py2's internal loader
                return pkgutil.ImpImporter(self._pathctx).find_module(fullname)

    def iter_modules(self, prefix):
        # NB: this currently represents only what's on disk, and does not handle package redirection
        return _iter_modules_impl([self._pathctx], prefix)

    def __repr__(self):
        return "{0}(path='{1}')".format(self.__class__.__name__, self._pathctx)


class _AnsibleCollectionPkgLoaderBase:
    _allows_package_code = False

    def __init__(self, fullname, path_list=None):
        self._fullname = fullname
        self._redirect_module = None
        self._split_name = fullname.split('.')
        self._rpart_name = fullname.rpartition('.')
        self._parent_package_name = self._rpart_name[0]  # eg ansible_collections for ansible_collections.somens, '' for toplevel
        self._package_to_load = self._rpart_name[2]  # eg somens for ansible_collections.somens

        self._source_code_path = None
        self._decoded_source = None
        self._compiled_code = None

        self._validate_args()

        self._candidate_paths = self._get_candidate_paths([to_native(p) for p in path_list])
        self._subpackage_search_paths = self._get_subpackage_search_paths(self._candidate_paths)

        self._validate_final()

    # allow subclasses to validate args and sniff split values before we start digging around
    def _validate_args(self):
        if self._split_name[0] != 'ansible_collections':
            raise ImportError('this loader can only load packages from the ansible_collections package, not {0}'.format(self._fullname))

    # allow subclasses to customize candidate path filtering
    def _get_candidate_paths(self, path_list):
        return [os.path.join(p, self._package_to_load) for p in path_list]

    # allow subclasses to customize finding paths
    def _get_subpackage_search_paths(self, candidate_paths):
        # filter candidate paths for existence (NB: silently ignoring package init code and same-named modules)
        return [p for p in candidate_paths if os.path.isdir(to_bytes(p))]

    # allow subclasses to customize state validation/manipulation before we return the loader instance
    def _validate_final(self):
        return

    @staticmethod
    @contextmanager
    def _new_or_existing_module(name, **kwargs):
        # handle all-or-nothing sys.modules creation/use-existing/delete-on-exception-if-created behavior
        created_module = False
        module = sys.modules.get(name)
        try:
            if not module:
                module = ModuleType(name)
                created_module = True
                sys.modules[name] = module
            # always override the values passed, except name (allow reference aliasing)
            for attr, value in kwargs.items():
                setattr(module, attr, value)
            yield module
        except Exception:
            if created_module:
                if sys.modules.get(name):
                    sys.modules.pop(name)
            raise

    # basic module/package location support
    # NB: this does not support distributed packages!
    @staticmethod
    def _module_file_from_path(leaf_name, path):
        has_code = True
        package_path = os.path.join(to_native(path), to_native(leaf_name))
        module_path = None

        # if the submodule is a package, assemble valid submodule paths, but stop looking for a module
        if os.path.isdir(to_bytes(package_path)):
            # is there a package init?
            module_path = os.path.join(package_path, '__init__.py')
            if not os.path.isfile(to_bytes(module_path)):
                module_path = os.path.join(package_path, '__synthetic__')
                has_code = False
        else:
            module_path = package_path + '.py'
            package_path = None
            if not os.path.isfile(to_bytes(module_path)):
                raise ImportError('{0} not found at {1}'.format(leaf_name, path))

        return module_path, has_code, package_path

    def load_module(self, fullname):
        # short-circuit redirect; we've already imported the redirected module, so just alias it and return it
        if self._redirect_module:
            sys.modules[self._fullname] = self._redirect_module
            return self._redirect_module

        # we're actually loading a module/package
        module_attrs = dict(
            __loader__=self,
            __file__=self.get_filename(fullname),
            __package__=self._parent_package_name  # sane default for non-packages
        )

        # eg, I am a package
        if self._subpackage_search_paths is not None:  # empty is legal
            module_attrs['__path__'] = self._subpackage_search_paths
            module_attrs['__package__'] = fullname  # per PEP366

        with self._new_or_existing_module(fullname, **module_attrs) as module:
            # execute the module's code in its namespace
            code_obj = self.get_code(fullname)
            if code_obj is not None:  # things like NS packages that can't have code on disk will return None
                exec(code_obj, module.__dict__)

            return module

    def is_package(self, fullname):
        if fullname != self._fullname:
            raise ValueError('this loader cannot answer is_package for {0}, only {1}'.format(fullname, self._fullname))
        return self._subpackage_search_paths is not None

    def get_source(self, fullname):
        if self._decoded_source:
            return self._decoded_source
        if fullname != self._fullname:
            raise ValueError('this loader cannot load source for {0}, only {1}'.format(fullname, self._fullname))
        if not self._source_code_path:
            return None
        # FIXME: what do we want encoding/newline requirements to be?
        self._decoded_source = self.get_data(self._source_code_path)
        return self._decoded_source

    def get_data(self, path):
        if not path:
            raise ValueError('a path must be specified')

        # TODO: ensure we're being asked for a path below something we own
        # TODO: try to handle redirects internally?

        if not path[0] == '/':
            # relative to current package, search package paths if possible (this may not be necessary)
            # candidate_paths = [os.path.join(ssp, path) for ssp in self._subpackage_search_paths]
            raise ValueError('relative resource paths not supported')
        else:
            candidate_paths = [path]

        for p in candidate_paths:
            b_path = to_bytes(p)
            if os.path.isfile(b_path):
                with open(b_path, 'rb') as fd:
                    return fd.read()
            # HACK: if caller asks for __init__.py and the parent dir exists, return empty string (this keep consistency
            # with "collection subpackages don't require __init__.py" working everywhere with get_data
            elif b_path.endswith(b'__init__.py') and os.path.isdir(os.path.dirname(b_path)):
                return ''

        return None

    def _synthetic_filename(self, fullname):
        return '<ansible_synthetic_collection_package>'

    def get_filename(self, fullname):
        if fullname != self._fullname:
            raise ValueError('this loader cannot find files for {0}, only {1}'.format(fullname, self._fullname))

        filename = self._source_code_path

        if not filename and self.is_package(fullname):
            if len(self._subpackage_search_paths) == 1:
                filename = os.path.join(self._subpackage_search_paths[0], '__synthetic__')
            else:
                filename = self._synthetic_filename(fullname)

        return filename

    def get_code(self, fullname):
        if self._compiled_code:
            return self._compiled_code

        # this may or may not be an actual filename, but it's the value we'll use for __file__
        filename = self.get_filename(fullname)
        if not filename:
            filename = '<string>'

        source_code = self.get_source(fullname)

        # for things like synthetic modules that really have no source on disk, don't return a code object at all
        # vs things like an empty package init (which has an empty string source on disk)
        if source_code is None:
            return None

        self._compiled_code = compile(source=source_code, filename=filename, mode='exec', flags=0, dont_inherit=True)

        return self._compiled_code

    def iter_modules(self, prefix):
        return _iter_modules_impl(self._subpackage_search_paths, prefix)

    def __repr__(self):
        return '{0}(path={1})'.format(self.__class__.__name__, self._subpackage_search_paths or self._source_code_path)


class _AnsibleCollectionRootPkgLoader(_AnsibleCollectionPkgLoaderBase):
    def _validate_args(self):
        super(_AnsibleCollectionRootPkgLoader, self)._validate_args()
        if len(self._split_name) != 1:
            raise ImportError('this loader can only load the ansible_collections toplevel package, not {0}'.format(self._fullname))


# Implements Ansible's custom namespace package support.
# The ansible_collections package and one level down (collections namespaces) are Python namespace packages
# that search across all configured collection roots. The collection package (two levels down) is the first one found
# on the configured collection root path, and Python namespace package aggregation is not allowed at or below
# the collection. Implements implicit package (package dir) support for both Py2/3. Package init code is ignored
# by this loader.
class _AnsibleCollectionNSPkgLoader(_AnsibleCollectionPkgLoaderBase):
    def _validate_args(self):
        super(_AnsibleCollectionNSPkgLoader, self)._validate_args()
        if len(self._split_name) != 2:
            raise ImportError('this loader can only load collections namespace packages, not {0}'.format(self._fullname))

    def _validate_final(self):
        # special-case the `ansible` namespace, since `ansible.builtin` is magical
        if not self._subpackage_search_paths and self._package_to_load != 'ansible':
            raise ImportError('no {0} found in {1}'.format(self._package_to_load, self._candidate_paths))


# handles locating the actual collection package and associated metadata
class _AnsibleCollectionPkgLoader(_AnsibleCollectionPkgLoaderBase):
    def _validate_args(self):
        super(_AnsibleCollectionPkgLoader, self)._validate_args()
        if len(self._split_name) != 3:
            raise ImportError('this loader can only load collection packages, not {0}'.format(self._fullname))

    def _validate_final(self):
        if self._split_name[1:3] == ['ansible', 'builtin']:
            # we don't want to allow this one to have on-disk search capability
            self._subpackage_search_paths = []
        elif not self._subpackage_search_paths:
            raise ImportError('no {0} found in {1}'.format(self._package_to_load, self._candidate_paths))
        else:
            # only search within the first collection we found
            self._subpackage_search_paths = [self._subpackage_search_paths[0]]

    def load_module(self, fullname):
        if not _meta_yml_to_dict:
            raise ValueError('ansible.utils.collection_loader._meta_yml_to_dict is not set')

        module = super(_AnsibleCollectionPkgLoader, self).load_module(fullname)

        module._collection_meta = {}
        # TODO: load collection metadata, cache in __loader__ state

        collection_name = '.'.join(self._split_name[1:3])

        if collection_name == 'ansible.builtin':
            # ansible.builtin is a synthetic collection, get its routing config from the Ansible distro
            ansible_pkg_path = os.path.dirname(import_module('ansible').__file__)
            metadata_path = os.path.join(ansible_pkg_path, 'config/ansible_builtin_runtime.yml')
            with open(to_bytes(metadata_path), 'rb') as fd:
                raw_routing = fd.read()
        else:
            b_routing_meta_path = to_bytes(os.path.join(module.__path__[0], 'meta/runtime.yml'))
            if os.path.isfile(b_routing_meta_path):
                with open(b_routing_meta_path, 'rb') as fd:
                    raw_routing = fd.read()
            else:
                raw_routing = ''
        try:
            if raw_routing:
                routing_dict = _meta_yml_to_dict(raw_routing, (collection_name, 'runtime.yml'))
                module._collection_meta = self._canonicalize_meta(routing_dict)
        except Exception as ex:
            raise ValueError('error parsing collection metadata: {0}'.format(to_native(ex)))

        AnsibleCollectionConfig.on_collection_load.fire(collection_name=collection_name, collection_path=os.path.dirname(module.__file__))

        return module

    def _canonicalize_meta(self, meta_dict):
        # TODO: rewrite import keys and all redirect targets that start with .. (current namespace) and . (current collection)
        # OR we could do it all on the fly?
        # if not meta_dict:
        #     return {}
        #
        # ns_name = '.'.join(self._split_name[0:2])
        # collection_name = '.'.join(self._split_name[0:3])
        #
        # #
        # for routing_type, routing_type_dict in iteritems(meta_dict.get('plugin_routing', {})):
        #     for plugin_key, plugin_dict in iteritems(routing_type_dict):
        #         redirect = plugin_dict.get('redirect', '')
        #         if redirect.startswith('..'):
        #             redirect =  redirect[2:]

        return meta_dict


# loads everything under a collection, including handling redirections defined by the collection
class _AnsibleCollectionLoader(_AnsibleCollectionPkgLoaderBase):
    # HACK: stash this in a better place
    _redirected_package_map = {}
    _allows_package_code = True

    def _validate_args(self):
        super(_AnsibleCollectionLoader, self)._validate_args()
        if len(self._split_name) < 4:
            raise ValueError('this loader is only for sub-collection modules/packages, not {0}'.format(self._fullname))

    def _get_candidate_paths(self, path_list):
        if len(path_list) != 1 and self._split_name[1:3] != ['ansible', 'builtin']:
            raise ValueError('this loader requires exactly one path to search')

        return path_list

    def _get_subpackage_search_paths(self, candidate_paths):
        collection_name = '.'.join(self._split_name[1:3])
        collection_meta = _get_collection_metadata(collection_name)

        # check for explicit redirection, as well as ancestor package-level redirection (only load the actual code once!)
        redirect = None
        explicit_redirect = False

        routing_entry = _nested_dict_get(collection_meta, ['import_redirection', self._fullname])
        if routing_entry:
            redirect = routing_entry.get('redirect')

        if redirect:
            explicit_redirect = True
        else:
            redirect = _get_ancestor_redirect(self._redirected_package_map, self._fullname)

        # NB: package level redirection requires hooking all future imports beneath the redirected source package
        # in order to ensure sanity on future relative imports. We always import everything under its "real" name,
        # then add a sys.modules entry with the redirected name using the same module instance. If we naively imported
        # the source for each redirection, most submodules would import OK, but we'd have N runtime copies of the module
        # (one for each name), and relative imports that ascend above the redirected package would break (since they'd
        # see the redirected ancestor package contents instead of the package where they actually live).
        if redirect:
            # FIXME: wrap this so we can be explicit about a failed redirection
            self._redirect_module = import_module(redirect)
            if explicit_redirect and hasattr(self._redirect_module, '__path__') and self._redirect_module.__path__:
                # if the import target looks like a package, store its name so we can rewrite future descendent loads
                self._redirected_package_map[self._fullname] = redirect

            # if we redirected, don't do any further custom package logic
            return None

        # we're not doing a redirect- try to find what we need to actually load a module/package

        # this will raise ImportError if we can't find the requested module/package at all
        if not candidate_paths:
            # noplace to look, just ImportError
            raise ImportError('package has no paths')

        found_path, has_code, package_path = self._module_file_from_path(self._package_to_load, candidate_paths[0])

        # still here? we found something to load...
        if has_code:
            self._source_code_path = found_path

        if package_path:
            return [package_path]  # always needs to be a list

        return None


# This loader only answers for intercepted Ansible Python modules. Normal imports will fail here and be picked up later
# by our path_hook importer (which proxies the built-in import mechanisms, allowing normal caching etc to occur)
class _AnsibleInternalRedirectLoader:
    def __init__(self, fullname, path_list):
        self._redirect = None

        split_name = fullname.split('.')
        toplevel_pkg = split_name[0]
        module_to_load = split_name[-1]

        if toplevel_pkg != 'ansible':
            raise ImportError('not interested')

        builtin_meta = _get_collection_metadata('ansible.builtin')

        routing_entry = _nested_dict_get(builtin_meta, ['import_redirection', fullname])
        if routing_entry:
            self._redirect = routing_entry.get('redirect')

        if not self._redirect:
            raise ImportError('not redirected, go ask path_hook')

    def load_module(self, fullname):
        # since we're delegating to other loaders, this should only be called for internal redirects where we answered
        # find_module with this loader, in which case we'll just directly import the redirection target, insert it into
        # sys.modules under the name it was requested by, and return the original module.

        # should never see this
        if not self._redirect:
            raise ValueError('no redirect found for {0}'.format(fullname))

        # FIXME: smuggle redirection context, provide warning/error that we tried and failed to redirect
        mod = import_module(self._redirect)
        sys.modules[fullname] = mod
        return mod


class AnsibleCollectionRef:
    # FUTURE: introspect plugin loaders to get these dynamically?
    VALID_REF_TYPES = frozenset(to_text(r) for r in ['action', 'become', 'cache', 'callback', 'cliconf', 'connection',
                                                     'doc_fragments', 'filter', 'httpapi', 'inventory', 'lookup',
                                                     'module_utils', 'modules', 'netconf', 'role', 'shell', 'strategy',
                                                     'terminal', 'test', 'vars', 'playbook'])

    # FIXME: tighten this up to match Python identifier reqs, etc
    VALID_SUBDIRS_RE = re.compile(to_text(r'^\w+(\.\w+)*$'))
    VALID_FQCR_RE = re.compile(to_text(r'^\w+(\.\w+){2,}$'))  # can have 0-N included subdirs as well

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
        fqcr_components = [self.collection]

        self.n_python_collection_package_name = to_native('.'.join(package_components))

        if self.ref_type == u'role':
            package_components.append(u'roles')
        elif self.ref_type == u'playbook':
            package_components.append(u'playbooks')
        else:
            # we assume it's a plugin
            package_components += [u'plugins', self.ref_type]

        if self.subdirs:
            package_components.append(self.subdirs)
            fqcr_components.append(self.subdirs)

        if self.ref_type in (u'role', u'playbook'):
            # playbooks and roles are their own resource
            package_components.append(self.resource)

        fqcr_components.append(self.resource)

        self.n_python_package_name = to_native('.'.join(package_components))
        self._fqcr = u'.'.join(fqcr_components)

    def __repr__(self):
        return 'AnsibleCollectionRef(collection={0!r}, subdirs={1!r}, resource={2!r})'.format(self.collection, self.subdirs, self.resource)

    @property
    def fqcr(self):
        return self._fqcr

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
        ext = ''

        if ref_type == u'playbook' and ref.endswith(PB_EXTENSIONS):
            resource_splitname = ref.rsplit(u'.', 2)
            package_remnant = resource_splitname[0]
            resource = resource_splitname[1]
            ext = '.' + resource_splitname[2]
        else:
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

        return AnsibleCollectionRef(collection_name, subdirs, resource + ext, ref_type)

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

        if collection_name.count(u'.') != 1:
            return False

        return all(
            # NOTE: keywords and identifiers are different in differnt Pythons
            not iskeyword(ns_or_name) and is_python_identifier(ns_or_name)
            for ns_or_name in collection_name.split(u'.')
        )


def _get_collection_playbook_path(playbook):

    acr = AnsibleCollectionRef.try_parse_fqcr(playbook, u'playbook')
    if acr:
        try:
            # get_collection_path
            pkg = import_module(acr.n_python_collection_package_name)
        except (IOError, ModuleNotFoundError) as e:
            # leaving e as debug target, even though not used in normal code
            pkg = None

        if pkg:
            cpath = os.path.join(sys.modules[acr.n_python_collection_package_name].__file__.replace('__synthetic__', 'playbooks'))

            if acr.subdirs:
                paths = [to_native(x) for x in acr.subdirs.split(u'.')]
                paths.insert(0, cpath)
                cpath = os.path.join(*paths)

            path = os.path.join(cpath, to_native(acr.resource))
            if os.path.exists(to_bytes(path)):
                return acr.resource, path, acr.collection
            elif not acr.resource.endswith(PB_EXTENSIONS):
                for ext in PB_EXTENSIONS:
                    path = os.path.join(cpath, to_native(acr.resource + ext))
                    if os.path.exists(to_bytes(path)):
                        return acr.resource, path, acr.collection
    return None


def _get_collection_role_path(role_name, collection_list=None):
    return _get_collection_resource_path(role_name, u'role', collection_list)


def _get_collection_resource_path(name, ref_type, collection_list=None):

    if ref_type == u'playbook':
        # they are handled a bit diff due to 'extension variance' and no collection_list
        return _get_collection_playbook_path(name)

    acr = AnsibleCollectionRef.try_parse_fqcr(name, ref_type)
    if acr:
        # looks like a valid qualified collection ref; skip the collection_list
        collection_list = [acr.collection]
        subdirs = acr.subdirs
        resource = acr.resource
    elif not collection_list:
        return None  # not a FQ and no collection search list spec'd, nothing to do
    else:
        resource = name  # treat as unqualified, loop through the collection search list to try and resolve
        subdirs = ''

    for collection_name in collection_list:
        try:
            acr = AnsibleCollectionRef(collection_name=collection_name, subdirs=subdirs, resource=resource, ref_type=ref_type)
            # FIXME: error handling/logging; need to catch any import failures and move along
            pkg = import_module(acr.n_python_package_name)

            if pkg is not None:
                # the package is now loaded, get the collection's package and ask where it lives
                path = os.path.dirname(to_bytes(sys.modules[acr.n_python_package_name].__file__, errors='surrogate_or_strict'))
                return resource, to_text(path, errors='surrogate_or_strict'), collection_name

        except (IOError, ModuleNotFoundError) as e:
            continue
        except Exception as ex:
            # FIXME: pick out typical import errors first, then error logging
            continue

    return None


def _get_collection_name_from_path(path):
    """
    Return the containing collection name for a given path, or None if the path is not below a configured collection, or
    the collection cannot be loaded (eg, the collection is masked by another of the same name higher in the configured
    collection roots).
    :param path: path to evaluate for collection containment
    :return: collection name or None
    """

    # ensure we compare full paths since pkg path will be abspath
    path = to_native(os.path.abspath(to_bytes(path)))

    path_parts = path.split('/')
    if path_parts.count('ansible_collections') != 1:
        return None

    ac_pos = path_parts.index('ansible_collections')

    # make sure it's followed by at least a namespace and collection name
    if len(path_parts) < ac_pos + 3:
        return None

    candidate_collection_name = '.'.join(path_parts[ac_pos + 1:ac_pos + 3])

    try:
        # we've got a name for it, now see if the path prefix matches what the loader sees
        imported_pkg_path = to_native(os.path.dirname(to_bytes(import_module('ansible_collections.' + candidate_collection_name).__file__)))
    except ImportError:
        return None

    # reassemble the original path prefix up the collection name, and it should match what we just imported. If not
    # this is probably a collection root that's not configured.

    original_path_prefix = os.path.join('/', *path_parts[0:ac_pos + 3])

    imported_pkg_path = to_native(os.path.abspath(to_bytes(imported_pkg_path)))
    if original_path_prefix != imported_pkg_path:
        return None

    return candidate_collection_name


def _get_import_redirect(collection_meta_dict, fullname):
    if not collection_meta_dict:
        return None

    return _nested_dict_get(collection_meta_dict, ['import_redirection', fullname, 'redirect'])


def _get_ancestor_redirect(redirected_package_map, fullname):
    # walk the requested module's ancestor packages to see if any have been previously redirected
    cur_pkg = fullname
    while cur_pkg:
        cur_pkg = cur_pkg.rpartition('.')[0]
        ancestor_redirect = redirected_package_map.get(cur_pkg)
        if ancestor_redirect:
            # rewrite the prefix on fullname so we import the target first, then alias it
            redirect = ancestor_redirect + fullname[len(cur_pkg):]
            return redirect
    return None


def _nested_dict_get(root_dict, key_list):
    cur_value = root_dict
    for key in key_list:
        cur_value = cur_value.get(key)
        if not cur_value:
            return None

    return cur_value


def _iter_modules_impl(paths, prefix=''):
    # NB: this currently only iterates what's on disk- redirected modules are not considered
    if not prefix:
        prefix = ''
    else:
        prefix = to_native(prefix)
    # yield (module_loader, name, ispkg) for each module/pkg under path
    # TODO: implement ignore/silent catch for unreadable?
    for b_path in map(to_bytes, paths):
        if not os.path.isdir(b_path):
            continue
        for b_basename in sorted(os.listdir(b_path)):
            b_candidate_module_path = os.path.join(b_path, b_basename)
            if os.path.isdir(b_candidate_module_path):
                # exclude things that obviously aren't Python package dirs
                # FIXME: this dir is adjustable in py3.8+, check for it
                if b'.' in b_basename or b_basename == b'__pycache__':
                    continue

                # TODO: proper string handling?
                yield prefix + to_native(b_basename), True
            else:
                # FIXME: match builtin ordering for package/dir/file, support compiled?
                if b_basename.endswith(b'.py') and b_basename != b'__init__.py':
                    yield prefix + to_native(os.path.splitext(b_basename)[0]), False


def _get_collection_metadata(collection_name):
    collection_name = to_native(collection_name)
    if not collection_name or not isinstance(collection_name, string_types) or len(collection_name.split('.')) != 2:
        raise ValueError('collection_name must be a non-empty string of the form namespace.collection')

    try:
        collection_pkg = import_module('ansible_collections.' + collection_name)
    except ImportError:
        raise ValueError('unable to locate collection {0}'.format(collection_name))

    _collection_meta = getattr(collection_pkg, '_collection_meta', None)

    if _collection_meta is None:
        raise ValueError('collection metadata was not loaded for collection {0}'.format(collection_name))

    return _collection_meta
