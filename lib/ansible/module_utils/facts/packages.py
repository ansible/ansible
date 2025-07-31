# (c) 2018, Ansible Project
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

from __future__ import annotations

import ansible.module_utils.compat.typing as t

from abc import ABCMeta, abstractmethod

from ansible.module_utils._internal import _no_six
from ansible.module_utils.basic import missing_required_lib
from ansible.module_utils.common.process import get_bin_path
from ansible.module_utils.common.respawn import has_respawned, probe_interpreters_for_module, respawn_module
from ansible.module_utils.common._utils import get_all_subclasses


def get_all_pkg_managers():

    return {obj.__name__.lower(): obj for obj in get_all_subclasses(PkgMgr) if obj not in (CLIMgr, LibMgr, RespawningLibMgr)}


class PkgMgr(metaclass=ABCMeta):

    @abstractmethod
    def is_available(self, handle_exceptions):
        # This method is supposed to return True/False if the package manager is currently installed/usable
        # It can also 'prep' the required systems in the process of detecting availability
        # If handle_exceptions is false it should raise exceptions related to manager discovery instead of handling them.
        pass

    @abstractmethod
    def list_installed(self):
        # This method should return a list of installed packages, each list item will be passed to get_package_details
        pass

    @abstractmethod
    def get_package_details(self, package):
        # This takes a 'package' item and returns a dictionary with the package information, name and version are minimal requirements
        pass

    def get_packages(self):
        # Take all of the above and return a dictionary of lists of dictionaries (package = list of installed versions)

        installed_packages = {}
        for package in self.list_installed():
            package_details = self.get_package_details(package)
            if 'source' not in package_details:
                package_details['source'] = self.__class__.__name__.lower()
            name = package_details['name']
            if name not in installed_packages:
                installed_packages[name] = [package_details]
            else:
                installed_packages[name].append(package_details)
        return installed_packages


class LibMgr(PkgMgr):

    LIB = None  # type: str | None

    def __init__(self):

        self._lib = None
        super(LibMgr, self).__init__()

    def is_available(self, handle_exceptions=True):
        found = False
        try:
            self._lib = __import__(self.LIB)
            found = True
        except ImportError:
            if not handle_exceptions:
                raise Exception(missing_required_lib(self.LIB))
        return found


class RespawningLibMgr(LibMgr):

    CLI_BINARIES = []   # type: t.List[str]
    INTERPRETERS = ['/usr/bin/python3']

    def is_available(self, handle_exceptions=True):
        if super(RespawningLibMgr, self).is_available():
            return True

        for binary in self.CLI_BINARIES:
            try:
                bin_path = get_bin_path(binary)
            except ValueError:
                # Not an interesting exception to raise, just a speculative probe
                continue
            else:
                # It looks like this package manager is installed
                if not has_respawned():
                    # See if respawning will help
                    interpreter_path = probe_interpreters_for_module(self.INTERPRETERS, self.LIB)
                    if interpreter_path:
                        respawn_module(interpreter_path)
                        # The module will exit when the respawned copy completes

                if not handle_exceptions:
                    raise Exception(f'Found executable at {bin_path}. {missing_required_lib(self.LIB)}')

        if not handle_exceptions:
            raise Exception(missing_required_lib(self.LIB))

        return False


class CLIMgr(PkgMgr):

    CLI = None  # type: str | None

    def __init__(self):

        self._cli = None
        super(CLIMgr, self).__init__()

    def is_available(self, handle_exceptions=True):
        found = False
        try:
            self._cli = get_bin_path(self.CLI)
            found = True
        except ValueError:
            if not handle_exceptions:
                raise
        return found


def __getattr__(importable_name):
    return _no_six.deprecate(importable_name, __name__, "with_metaclass")
