# (c) 2019 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# CAUTION: This implementation of the collection loader is used by ansible-test.
#          Because of this, it must be compatible with all Python versions supported on the controller or remote.

from __future__ import annotations

import itertools
import os
import os.path
import pathlib
import re
import sys

from contextlib import contextmanager
from importlib import import_module, reload as reload_module
from importlib.machinery import FileFinder
from importlib.util import find_spec, spec_from_loader
from keyword import iskeyword
from types import ModuleType

# DO NOT add new non-stdlib import deps here, this loader is used by external tools (eg ansible-test import sanity)
# that only allow stdlib and module_utils
from . import _to_bytes, _to_text
from ._collection_config import AnsibleCollectionConfig

try:
    # Available on Python >= 3.11
    # We ignore the import error that will trigger when running mypy with
    # older Python versions.
    from importlib.resources.abc import TraversableResources  # type: ignore[import]
except ImportError:
    # Used with Python 3.9 and 3.10 only
    # This member is still available as an alias up until Python 3.14 but
    # is deprecated as of Python 3.12.
    # deprecated: description='TraversableResources move' python_version='3.10'
    from importlib.abc import TraversableResources  # type: ignore[assignment,no-redef]

# NB: this supports import sanity test providing a different impl
try:
    from ._collection_meta import _meta_yml_to_dict
except ImportError:
    _meta_yml_to_dict = None

PB_EXTENSIONS = ('.yml', '.yaml')
SYNTHETIC_PACKAGE_NAME = '<ansible_synthetic_collection_package>'


class _AnsibleNSTraversable:
    """Class that implements the ``importlib.resources.abc.Traversable``
    interface for the following ``ansible_collections`` namespace packages::

    * ``ansible_collections``
    * ``ansible_collections.<namespace>``

    These namespace packages operate differently from a normal Python
    namespace package, in that the same namespace can be distributed across
    multiple directories on the filesystem and still function as a single
    namespace, such as::

    * ``/usr/share/ansible/collections/ansible_collections/ansible/posix/``
    * ``/home/user/.ansible/collections/ansible_collections/ansible/windows/``

    This class will mimic the behavior of various ``pathlib.Path`` methods,
    by combining the results of multiple root paths into the output.

    This class does not do anything to remove duplicate collections from the
    list, so when traversing either namespace patterns supported by this class,
    it is possible to have the same collection located in multiple root paths,
    but precedence rules only use one. When iterating or traversing these
    package roots, there is the potential to see the same collection in
    multiple places without indication of which would be used. In such a
    circumstance, it is best to then call ``importlib.resources.files`` for an
    individual collection package rather than continuing to traverse from the
    namespace package.

    Several methods will raise ``NotImplementedError`` as they do not make
    sense for these namespace packages.
    """
    def __init__(self, *paths):
        self._paths = [pathlib.Path(p) for p in paths]

    def __repr__(self):
        return "_AnsibleNSTraversable('%s')" % "', '".join(map(_to_text, self._paths))

    def iterdir(self):
        return itertools.chain.from_iterable(p.iterdir() for p in self._paths if p.is_dir())

    def is_dir(self):
        return any(p.is_dir() for p in self._paths)

    def is_file(self):
        return False

    def glob(self, pattern):
        return itertools.chain.from_iterable(p.glob(pattern) for p in self._paths if p.is_dir())

    def _not_implemented(self, *args, **kwargs):
        raise NotImplementedError('not usable on namespaces')

    joinpath = __truediv__ = read_bytes = read_text = _not_implemented


class _AnsibleTraversableResources(TraversableResources):
    """Implements ``importlib.resources.abc.TraversableResources`` for the
    collection Python loaders.

    The result of ``files`` will depend on whether a particular collection, or
    a sub package of a collection was referenced, as opposed to
    ``ansible_collections`` or a particular namespace. For a collection and
    its subpackages, a ``pathlib.Path`` instance will be returned, whereas
    for the higher level namespace packages, ``_AnsibleNSTraversable``
    will be returned.
    """
    def __init__(self, package, loader):
        self._package = package
        self._loader = loader

    def _get_name(self, package):
        try:
            # spec
            return package.name
        except AttributeError:
            # module
            return package.__name__

    def _get_package(self, package):
        try:
            # spec
            return package.__parent__
        except AttributeError:
            # module
            return package.__package__

    def _get_path(self, package):
        try:
            # spec
            return package.origin
        except AttributeError:
            # module
            return package.__file__

    def _is_ansible_ns_package(self, package):
        origin = getattr(package, 'origin', None)
        if not origin:
            return False

        if origin == SYNTHETIC_PACKAGE_NAME:
            return True

        module_filename = os.path.basename(origin)
        return module_filename in {'__synthetic__', '__init__.py'}

    def _ensure_package(self, package):
        if self._is_ansible_ns_package(package):
            # Short circuit our loaders
            return
        if self._get_package(package) != package.__name__:
            raise TypeError('%r is not a package' % package.__name__)

    def files(self):
        package = self._package
        parts = package.split('.')
        is_ns = parts[0] == 'ansible_collections' and len(parts) < 3

        if isinstance(package, str):
            if is_ns:
                # Don't use ``spec_from_loader`` here, because that will point
                # to exactly 1 location for a namespace. Use ``find_spec``
                # to get a list of all locations for the namespace
                package = find_spec(package)
            else:
                package = spec_from_loader(package, self._loader)
        elif not isinstance(package, ModuleType):
            raise TypeError('Expected string or module, got %r' % package.__class__.__name__)

        self._ensure_package(package)
        if is_ns:
            return _AnsibleNSTraversable(*package.submodule_search_locations)
        return pathlib.Path(self._get_path(package)).parent


class _AnsibleCollectionFinder:
    def __init__(self, paths=None, scan_sys_paths=True, internal_collections=None):
        # TODO: accept metadata loader override
        self._ansible_pkg_path = _to_text(os.path.dirname(_to_bytes(sys.modules['ansible'].__file__)))

        if isinstance(paths, str):
            paths = [paths]
        elif paths is None:
            paths = []

        # expand any placeholders in configured paths
        paths = [os.path.expanduser(_to_text(p)) for p in paths]

        # add syspaths if needed
        if scan_sys_paths:
            paths.extend(sys.path)

        good_paths = []
        # expand any placeholders in configured paths
        for p in paths:

            # ensure we always have ansible_collections
            if os.path.basename(p) == 'ansible_collections':
                p = os.path.dirname(p)

            if p not in good_paths and os.path.isdir(_to_bytes(os.path.join(p, 'ansible_collections'))):
                good_paths.append(p)

        self._internal_collections = internal_collections
        self._n_configured_paths = good_paths
        self._n_cached_collection_paths = None
        self._n_cached_collection_qualified_paths = None

        self._n_playbook_paths = []

    @classmethod
    def _find_existing_finder(cls) -> _AnsibleCollectionFinder | None:
        for finder in sys.meta_path:
            if isinstance(finder, _AnsibleCollectionFinder):
                return finder

        return None

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
        path = _to_text(path)
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
        if isinstance(playbook_paths, str):
            playbook_paths = [playbook_paths]

        # track visited paths; we have to preserve the dir order as-passed in case there are duplicate collections (first one wins)
        added_paths = set()

        # de-dupe
        self._n_playbook_paths = [os.path.join(_to_text(p), 'collections') for p in playbook_paths if not (p in added_paths or added_paths.add(p))]
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

    def _get_loader(self, fullname, path=None):
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

        if toplevel_pkg == 'ansible':
            # something under the ansible package, delegate to our internal loader in case of redirections
            initialize_loader = _AnsibleInternalRedirectLoader
        elif part_count == 1:
            initialize_loader = _AnsibleCollectionRootPkgLoader
        elif part_count == 2:  # ns pkg eg, ansible_collections, ansible_collections.somens
            initialize_loader = _AnsibleCollectionNSPkgLoader
        elif part_count == 3:  # collection pkg eg, ansible_collections.somens.somecoll
            initialize_loader = _AnsibleCollectionPkgLoader
        else:
            # anything below the collection
            initialize_loader = _AnsibleCollectionLoader

        # NB: actual "find"ing is delegated to the constructors on the various loaders; they'll ImportError if not found
        try:
            return initialize_loader(fullname=fullname, path_list=path)
        except ImportError:
            # TODO: log attempt to load context
            return None

    def find_module(self, fullname, path=None):
        # Figure out what's being asked for, and delegate to a special-purpose loader
        return self._get_loader(fullname, path)

    def find_spec(self, fullname, path, target=None):
        loader = self._get_loader(fullname, path)

        if loader is None:
            return None

        spec = spec_from_loader(fullname, loader)
        if spec is not None and hasattr(loader, '_subpackage_search_paths'):
            spec.submodule_search_locations = loader._subpackage_search_paths
        return spec


# Implements a path_hook finder for iter_modules (since it's only path based). This finder does not need to actually
# function as a finder in most cases, since our meta_path finder is consulted first for *almost* everything, except
# pkgutil.iter_modules, and under py2, pkgutil.get_data if the parent package passed has not been loaded yet.
class _AnsiblePathHookFinder:
    def __init__(self, collection_finder, pathctx):
        # when called from a path_hook, find_module doesn't usually get the path arg, so this provides our context
        self._pathctx = _to_text(pathctx)
        self._collection_finder = collection_finder
        # cache the native FileFinder (take advantage of its filesystem cache for future find/load requests)
        self._file_finder = None

    # class init is fun- this method has a self arg that won't get used
    def _get_filefinder_path_hook(self=None):
        _file_finder_hook = None
        # try to find the FileFinder hook to call for fallback path-based imports in Py3
        _file_finder_hook = [ph for ph in sys.path_hooks if 'FileFinder' in repr(ph)]
        if len(_file_finder_hook) != 1:
            raise Exception('need exactly one FileFinder import hook (found {0})'.format(len(_file_finder_hook)))
        _file_finder_hook = _file_finder_hook[0]

        return _file_finder_hook

    _filefinder_path_hook = _get_filefinder_path_hook()

    def _get_finder(self, fullname):
        split_name = fullname.split('.')
        toplevel_pkg = split_name[0]

        if toplevel_pkg == 'ansible_collections':
            # collections content? delegate to the collection finder
            return self._collection_finder
        else:
            # Something else; we'd normally restrict this to `ansible` descendent modules so that any weird loader
            # behavior that arbitrary Python modules have can be serviced by those loaders. In some dev/test
            # scenarios (eg a venv under a collection) our path_hook signs us up to load non-Ansible things, and
            # it's too late by the time we've reached this point, but also too expensive for the path_hook to figure
            # out what we *shouldn't* be loading with the limited info it has. So we'll just delegate to the
            # normal path-based loader as best we can to service it. This also allows us to take advantage of Python's
            # built-in FS caching and byte-compilation for most things.
            # create or consult our cached file finder for this path
            if not self._file_finder:
                try:
                    self._file_finder = _AnsiblePathHookFinder._filefinder_path_hook(self._pathctx)
                except ImportError:
                    # FUTURE: log at a high logging level? This is normal for things like python36.zip on the path, but
                    # might not be in some other situation...
                    return None

            return self._file_finder

    def find_module(self, fullname, path=None):
        # we ignore the passed in path here- use what we got from the path hook init
        finder = self._get_finder(fullname)

        if finder is None:
            return None
        elif isinstance(finder, FileFinder):
            # this codepath is erroneously used under some cases in py3,
            # and the find_module method on FileFinder does not accept the path arg
            # see https://github.com/pypa/setuptools/pull/2918
            return finder.find_module(fullname)
        else:
            return finder.find_module(fullname, path=[self._pathctx])

    def find_spec(self, fullname, target=None):
        split_name = fullname.split('.')
        toplevel_pkg = split_name[0]

        finder = self._get_finder(fullname)

        if finder is None:
            return None
        elif toplevel_pkg == 'ansible_collections':
            return finder.find_spec(fullname, path=[self._pathctx])
        else:
            return finder.find_spec(fullname)

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

        self._candidate_paths = self._get_candidate_paths([_to_text(p) for p in path_list])
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
        return [p for p in candidate_paths if os.path.isdir(_to_bytes(p))]

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
        package_path = os.path.join(_to_text(path), _to_text(leaf_name))
        module_path = None

        # if the submodule is a package, assemble valid submodule paths, but stop looking for a module
        if os.path.isdir(_to_bytes(package_path)):
            # is there a package init?
            module_path = os.path.join(package_path, '__init__.py')
            if not os.path.isfile(_to_bytes(module_path)):
                module_path = os.path.join(package_path, '__synthetic__')
                has_code = False
        else:
            module_path = package_path + '.py'
            package_path = None
            if not os.path.isfile(_to_bytes(module_path)):
                raise ImportError('{0} not found at {1}'.format(leaf_name, path))

        return module_path, has_code, package_path

    def get_resource_reader(self, fullname):
        return _AnsibleTraversableResources(fullname, self)

    def exec_module(self, module):
        # short-circuit redirect; avoid reinitializing existing modules
        if self._redirect_module:
            return

        # execute the module's code in its namespace
        code_obj = self.get_code(self._fullname)
        if code_obj is not None:  # things like NS packages that can't have code on disk will return None
            exec(code_obj, module.__dict__)

    def create_module(self, spec):
        # short-circuit redirect; we've already imported the redirected module, so just alias it and return it
        if self._redirect_module:
            return self._redirect_module
        else:
            return None

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
            b_path = _to_bytes(p)
            if os.path.isfile(b_path):
                with open(b_path, 'rb') as fd:
                    return fd.read()
            # HACK: if caller asks for __init__.py and the parent dir exists, return empty string (this keep consistency
            # with "collection subpackages don't require __init__.py" working everywhere with get_data
            elif b_path.endswith(b'__init__.py') and os.path.isdir(os.path.dirname(b_path)):
                return ''

        return None

    def _synthetic_filename(self, fullname):
        return SYNTHETIC_PACKAGE_NAME

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

    def _load_module(self, module):
        if not _meta_yml_to_dict:
            raise ValueError('ansible.utils.collection_loader._meta_yml_to_dict is not set')

        module._collection_meta = {}
        # TODO: load collection metadata, cache in __loader__ state

        collection_name = '.'.join(self._split_name[1:3])

        if collection_name == 'ansible.builtin':
            # ansible.builtin is a synthetic collection, get its routing config from the Ansible distro
            ansible_pkg_path = os.path.dirname(import_module('ansible').__file__)
            metadata_path = os.path.join(ansible_pkg_path, 'config/ansible_builtin_runtime.yml')
            with open(_to_bytes(metadata_path), 'rb') as fd:
                raw_routing = fd.read()
        else:
            b_routing_meta_path = _to_bytes(os.path.join(module.__path__[0], 'meta/runtime.yml'))
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
            raise ValueError(f'error parsing collection metadata: {ex}')

        AnsibleCollectionConfig.on_collection_load.fire(collection_name=collection_name, collection_path=os.path.dirname(module.__file__))

        return module

    def exec_module(self, module):
        super(_AnsibleCollectionPkgLoader, self).exec_module(module)
        self._load_module(module)

    def create_module(self, spec):
        return None

    def load_module(self, fullname):
        module = super(_AnsibleCollectionPkgLoader, self).load_module(fullname)
        return self._load_module(module)

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
    _redirected_package_map = {}  # type: dict[str, str]
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

    def get_resource_reader(self, fullname):
        return _AnsibleTraversableResources(fullname, self)

    def exec_module(self, module):
        # should never see this
        if not self._redirect:
            raise ValueError('no redirect found for {0}'.format(module.__spec__.name))

        # Replace the module with the redirect
        sys.modules[module.__spec__.name] = import_module(self._redirect)

    def create_module(self, spec):
        return None

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
    VALID_REF_TYPES = frozenset(_to_text(r) for r in ['action', 'become', 'cache', 'callback', 'cliconf', 'connection',
                                                      'doc_fragments', 'filter', 'httpapi', 'inventory', 'lookup',
                                                      'module_utils', 'modules', 'netconf', 'role', 'shell', 'strategy',
                                                      'terminal', 'test', 'vars', 'playbook'])

    # FIXME: tighten this up to match Python identifier reqs, etc
    VALID_SUBDIRS_RE = re.compile(_to_text(r'^\w+(\.\w+)*$'))
    VALID_FQCR_RE = re.compile(_to_text(r'^\w+(\.\w+){2,}$'))  # can have 0-N included subdirs as well

    def __init__(self, collection_name, subdirs, resource, ref_type):
        """
        Create an AnsibleCollectionRef from components
        :param collection_name: a collection name of the form 'namespace.collectionname'
        :param subdirs: optional subdir segments to be appended below the plugin type (eg, 'subdir1.subdir2')
        :param resource: the name of the resource being references (eg, 'mymodule', 'someaction', 'a_role')
        :param ref_type: the type of the reference, eg 'module', 'role', 'doc_fragment'
        """
        collection_name = _to_text(collection_name, strict=True)
        if subdirs is not None:
            subdirs = _to_text(subdirs, strict=True)
        resource = _to_text(resource, strict=True)
        ref_type = _to_text(ref_type, strict=True)

        if not self.is_valid_collection_name(collection_name):
            raise ValueError('invalid collection name (must be of the form namespace.collection): {0}'.format(_to_text(collection_name)))

        if ref_type not in self.VALID_REF_TYPES:
            raise ValueError('invalid collection ref_type: {0}'.format(ref_type))

        self.collection = collection_name
        if subdirs:
            if not re.match(self.VALID_SUBDIRS_RE, subdirs):
                raise ValueError('invalid subdirs entry: {0} (must be empty/None or of the form subdir1.subdir2)'.format(_to_text(subdirs)))
            self.subdirs = subdirs
        else:
            self.subdirs = u''

        self.resource = resource
        self.ref_type = ref_type

        package_components = [u'ansible_collections', self.collection]
        fqcr_components = [self.collection]

        self.n_python_collection_package_name = _to_text('.'.join(package_components))

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

        self.n_python_package_name = _to_text('.'.join(package_components))
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
            raise ValueError('{0} is not a valid collection reference'.format(_to_text(ref)))

        ref = _to_text(ref, strict=True)
        ref_type = _to_text(ref_type, strict=True)
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
        if legacy_plugin_dir_name is None:
            plugin_type = None
        else:
            legacy_plugin_dir_name = _to_text(legacy_plugin_dir_name)

            plugin_type = legacy_plugin_dir_name.removesuffix(u'_plugins')

        if plugin_type == u'library':
            plugin_type = u'modules'

        if plugin_type not in AnsibleCollectionRef.VALID_REF_TYPES:
            raise ValueError(f'{legacy_plugin_dir_name!r} cannot be mapped to a valid collection ref type')

        return plugin_type

    @staticmethod
    def is_valid_fqcr(ref, ref_type=None):
        """
        Validates if is string is a well-formed fully-qualified collection reference (does not look up the collection itself)
        :param ref: candidate collection reference to validate (a valid ref is of the form 'ns.coll.resource' or 'ns.coll.subdir1.subdir2.resource')
        :param ref_type: optional reference type to enable deeper validation, eg 'module', 'role', 'doc_fragment'
        :return: True if the collection ref passed is well-formed, False otherwise
        """

        ref = _to_text(ref)

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

        collection_name = _to_text(collection_name)

        if collection_name.count(u'.') != 1:
            return False

        return all(
            # NOTE: keywords and identifiers are different in different Pythons
            not iskeyword(ns_or_name) and ns_or_name.isidentifier()
            for ns_or_name in collection_name.split(u'.')
        )


def _get_collection_path(collection_name):
    collection_name = _to_text(collection_name)
    if not collection_name or not isinstance(collection_name, str) or len(collection_name.split('.')) != 2:
        raise ValueError('collection_name must be a non-empty string of the form namespace.collection')
    try:
        collection_pkg = import_module('ansible_collections.' + collection_name)
    except ImportError:
        raise ValueError('unable to locate collection {0}'.format(collection_name))

    return _to_text(os.path.dirname(_to_bytes(collection_pkg.__file__)))


def _get_collection_playbook_path(playbook):

    acr = AnsibleCollectionRef.try_parse_fqcr(playbook, u'playbook')
    if acr:
        try:
            # get_collection_path
            pkg = import_module(acr.n_python_collection_package_name)
        except (OSError, ModuleNotFoundError) as ex:
            # leaving ex as debug target, even though not used in normal code
            pkg = None

        if pkg:
            cpath = os.path.join(sys.modules[acr.n_python_collection_package_name].__file__.replace('__synthetic__', 'playbooks'))

            if acr.subdirs:
                paths = [_to_text(x) for x in acr.subdirs.split(u'.')]
                paths.insert(0, cpath)
                cpath = os.path.join(*paths)

            path = os.path.join(cpath, _to_text(acr.resource))
            if os.path.exists(_to_bytes(path)):
                return acr.resource, path, acr.collection
            elif not acr.resource.endswith(PB_EXTENSIONS):
                for ext in PB_EXTENSIONS:
                    path = os.path.join(cpath, _to_text(acr.resource + ext))
                    if os.path.exists(_to_bytes(path)):
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
                path = os.path.dirname(_to_bytes(sys.modules[acr.n_python_package_name].__file__))
                return resource, _to_text(path), collection_name

        except (OSError, ModuleNotFoundError) as ex:
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
    path = _to_text(os.path.abspath(_to_bytes(path)))

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
        imported_pkg_path = _to_text(os.path.dirname(_to_bytes(import_module('ansible_collections.' + candidate_collection_name).__file__)))
    except ImportError:
        return None

    # reassemble the original path prefix up the collection name, and it should match what we just imported. If not
    # this is probably a collection root that's not configured.

    original_path_prefix = os.path.join('/', *path_parts[0:ac_pos + 3])

    imported_pkg_path = _to_text(os.path.abspath(_to_bytes(imported_pkg_path)))
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
        prefix = _to_text(prefix)
    # yield (module_loader, name, ispkg) for each module/pkg under path
    # TODO: implement ignore/silent catch for unreadable?
    for b_path in map(_to_bytes, paths):
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
                yield prefix + _to_text(b_basename), True
            else:
                # FIXME: match builtin ordering for package/dir/file, support compiled?
                if b_basename.endswith(b'.py') and b_basename != b'__init__.py':
                    yield prefix + _to_text(os.path.splitext(b_basename)[0]), False


def _get_collection_metadata(collection_name):
    collection_name = _to_text(collection_name)
    if not collection_name or not isinstance(collection_name, str) or len(collection_name.split('.')) != 2:
        raise ValueError('collection_name must be a non-empty string of the form namespace.collection')

    try:
        collection_pkg = import_module('ansible_collections.' + collection_name)
    except ImportError as ex:
        raise ValueError('unable to locate collection {0}'.format(collection_name)) from ex

    _collection_meta = getattr(collection_pkg, '_collection_meta', None)

    if _collection_meta is None:
        raise ValueError('collection metadata was not loaded for collection {0}'.format(collection_name))

    return _collection_meta
