# (c) 2018, Ansible Project
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

from abc import ABCMeta, abstractmethod

from ansible.module_utils.six import with_metaclass
from ansible.module_utils.common.process import get_bin_path
from ansible.module_utils.common._utils import get_all_subclasses


def get_all_pkg_managers():

    return dict([(obj.__name__.lower(), obj) for obj in get_all_subclasses(PkgMgr) if obj not in (CLIMgr, LibMgr)])


class PkgMgr(with_metaclass(ABCMeta, object)):

    @abstractmethod
    def is_available(self):
        # This method is supposed to return True/False if the package manager is currently installed/usable
        # It can also 'prep' the required systems in the process of detecting availability
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

    LIB = None

    def __init__(self):

        self._lib = None
        super(LibMgr, self).__init__()

    def is_available(self):
        found = False
        try:
            self._lib = __import__(self.LIB)
            found = True
        except ImportError:
            pass
        return found


class CLIMgr(PkgMgr):

    CLI = None

    def __init__(self):

        self._cli = None
        super(CLIMgr, self).__init__()

    def is_available(self):
        try:
            self._cli = get_bin_path(self.CLI)
        except ValueError:
            return False
        return True
