#!/usr/bin/python
# (c) 2017, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# most of it copied from AWX's scan_packages module

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
module: package_facts
short_description: package information as facts
description:
  - Return information about installed packages as facts
options:
  manager:
    description:
      - The package manager used by the system so we can query the package information.
      - Since 2.8 this is a list and can support multiple package managers per system.
      - The 'portage', 'pkg' and 'pip' options were added in version 2.8.
    default: ['auto']
    choices: ["auto", "rpm", "apt", "portage", "pkg", "pip"]
    required: False
    type: list
  strategy:
    description:
      - How to query the package managers on the system
    choices: ['first', 'all']
    default: 'first'
    version_added: "2.8"
version_added: "2.5"
requirements:
    - For 'portage' support it requires the `qlist` utility, which is part of the 'portage-utils' package.
author:
  - Matthew Jones (@matburt)
  - Brian Coca (@bcoca)
  - Adam Miller (@maxamillion)
'''

EXAMPLES = '''
- name: get the rpm package facts
  package_facts:
    manager: "auto"

- name: show them
  debug: var=ansible_facts.packages

'''

RETURN = '''
ansible_facts:
  description: facts to add to ansible_facts
  returned: always
  type: complex
  contains:
    packages:
      description: list of dicts with package information
      returned: when operating system level package manager is specified or auto detected manager
      type: dict
      sample_rpm:
        {
          "packages": {
            "kernel": [
              {
                "arch": "x86_64",
                "epoch": null,
                "name": "kernel",
                "release": "514.26.2.el7",
                "source": "rpm",
                "version": "3.10.0"
              },
              {
                "arch": "x86_64",
                "epoch": null,
                "name": "kernel",
                "release": "514.16.1.el7",
                "source": "rpm",
                "version": "3.10.0"
              },
              {
                "arch": "x86_64",
                "epoch": null,
                "name": "kernel",
                "release": "514.10.2.el7",
                "source": "rpm",
                "version": "3.10.0"
              },
              {
                "arch": "x86_64",
                "epoch": null,
                "name": "kernel",
                "release": "514.21.1.el7",
                "source": "rpm",
                "version": "3.10.0"
              },
              {
                "arch": "x86_64",
                "epoch": null,
                "name": "kernel",
                "release": "693.2.2.el7",
                "source": "rpm",
                "version": "3.10.0"
              }
            ],
            "kernel-tools": [
              {
                "arch": "x86_64",
                "epoch": null,
                "name": "kernel-tools",
                "release": "693.2.2.el7",
                "source": "rpm",
                "version": "3.10.0"
              }
            ],
            "kernel-tools-libs": [
              {
                "arch": "x86_64",
                "epoch": null,
                "name": "kernel-tools-libs",
                "release": "693.2.2.el7",
                "source": "rpm",
                "version": "3.10.0"
              }
            ],
          }
        }
      sample_deb:
        {
          "packages": {
            "libbz2-1.0": [
              {
                "version": "1.0.6-5",
                "source": "apt",
                "arch": "amd64",
                "name": "libbz2-1.0"
              }
            ],
            "patch": [
              {
                "version": "2.7.1-4ubuntu1",
                "source": "apt",
                "arch": "amd64",
                "name": "patch"
              }
            ],
          }
        }
'''
import json

from abc import ABCMeta, abstractmethod

from ansible.module_utils.basic import AnsibleModule, get_all_subclasses
from ansible.module_utils._text import to_native, to_text


class TestFailed(Exception):
    pass


class PkgMgr(object):

    __metaclass__ = ABCMeta

    def __init__(self):

        if not self.test():
            raise TestFailed("Test failed to pass")

    @abstractmethod
    def test(self):
        ''' This method is supposed to return True/False if the package manager is installed/usable by this module '''
        pass

    @abstractmethod
    def list_installed(self):
        ''' This method should return a list of installed packages, each list item will be passed to get_package_details '''
        pass

    @abstractmethod
    def get_package_details(self, package):
        ''' This takes a 'package' item and returns a dictionary with the package information, name and version are minimal requirements '''
        pass

    def get_packages(self):
        ''' Take all of the above and return a dictionary of lists of dictionaries (package = list of installed versions) '''

        installed_packages = {}
        for package in self.list_installed():
            package_details = self.get_package_details(package)
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

        self.lib = None
        super(LibMgr, self).__init__()

    def test(self):
        found = False
        try:
            self.lib = __import__(self.LIB)
            found = True
        except ImportError:
            pass
        return found


class CLIMgr(PkgMgr):

    CLI = None

    def __init__(self):

        self.cli = None
        super(CLIMgr, self).__init__()

    def test(self):
        global module
        self.cli = module.get_bin_path(self.CLI, False)
        return bool(self.cli)


class RPM(LibMgr):

    LIB = 'rpm'

    def list_installed(self):
        return self.lib.TransactionSet().dbMatch()

    def get_package_details(self, package):
        return dict(name=package[self.lib.RPMTAG_NAME],
                    version=package[self.lib.RPMTAG_VERSION],
                    release=package[self.lib.RPMTAG_RELEASE],
                    epoch=package[self.lib.RPMTAG_EPOCH],
                    arch=package[self.lib.RPMTAG_ARCH],)


class APT(LibMgr):

    LIB = 'apt'

    @property
    def pkg_cache(self):
        if self._cache:
            return self._cache

        self._cache = self.lib.Cache()
        return self._cache

    def list_installed(self):
        return [pk for pk in self.pkg_cache.keys() if self.pkg_cache[pk].is_installed]

    def get_package_details(self, package):
        ac_pkg = self.pkg_cache[package].installed
        return dict(name=package, version=ac_pkg.version, arch=ac_pkg.architecture, category=ac_pkg.section, origin=ac_pkg.origins[0].origin)


class PKG(CLIMgr):

    CLI = 'pkg'
    atoms = ['name', 'version', 'origin', 'installed', 'automatic', 'arch', 'category', 'prefix', 'vital']

    def list_installed(self):
        rc, out, err = module.run_command([self.cli, 'query', "%%%s" % '\t%'.join(['n', 'v', 'R', 't', 'a', 'q', 'o', 'p', 'V'])])
        if rc != 0 or err:
            raise Exception("Unable to list packages rc=%s : %s" % (rc, err))
        return out.splitlines()

    def get_package_details(self, package):

        pkg = dict(zip(self.atoms, package.split('\t')))

        if 'arch' in pkg:
            try:
                pkg['arch'] = pkg['arch'].split(':')[2]
            except IndexError:
                pass

        if 'automatic' in pkg:
            pkg['automatic'] = bool(pkg['automatic'])

        if 'category' in pkg:
            pkg['category'] = pkg['category'].split('/', 1)[0]

        if 'version' in pkg:
            if ',' in pkg['version']:
                pkg['version'], pkg['port_epoch'] = pkg['version'].split(',', 1)
            else:
                pkg['port_epoch'] = 0

            if '_' in pkg['version']:
                pkg['version'], pkg['revision'] = pkg['version'].split('_', 1)
            else:
                pkg['revision'] = 0

        if 'vital' in pkg:
            pkg['vital'] = bool(pkg['vital'])

        return pkg


class PORTAGE(CLIMgr):

    CLI = 'qlist'
    atoms = ['category', 'name', 'version', 'ebuild_revision', 'slots', 'prefixes', 'sufixes']

    def list_installed(self):
        rc, out, err = module.run_command(' '.join([self.cli, '-Iv', '|', 'xargs', '-n', '1024', 'qatom']), use_unsafe_shell=True)
        if rc != 0 or err:
            raise RuntimeError("Unable to list packages rc=%s : %s" % (rc, to_native(err)))
        return out.splitlines()

    def get_package_details(self, package):
        return dict(zip(self.atoms, package.split()))


class PIP(CLIMgr):

    CLI = 'pip'

    def list_installed(self):
        global module
        rc, out, err = module.run_command([self.cli, 'list', '-l', '--format=json'])
        if rc != 0:
            raise Exception("Unable to list packages rc=%s : %s" % (rc, err))
        return json.loads(out)

    def get_package_details(self, package):
        return package


def main():

    # get supported pkg managers
    PKG_MANAGERS = dict([(obj.__name__.lower(), obj) for obj in get_all_subclasses(PkgMgr) if obj not in(CLIMgr, LibMgr)])

    # start work
    global module
    module = AnsibleModule(argument_spec=dict(manager={'type': 'list', 'default': ['auto']}), supports_check_mode=True)
    packages = {}
    results = {'warnings': []}
    managers = module.params['manager']
    strategy = module.params['strategy']

    if 'auto' in managers:
        # keep order from user, we do dedupe below
        managers.extend(PKG_MANAGERS.keys())
        managers.remove('auto')

    unsupported = set(managers).difference(set(PKG_MANAGERS.keys()))
    if unsupported:
        module.fail_json(msg='Unsupported package managers requested: %s' % (', '.join(unsupported)))

    found = 0
    seen = set()
    for pkgmgr in managers:

        if found and strategy == 'first':
            break

        # dedupe as per above
        if pkgmgr in seen:
            continue
        seen.add(pkgmgr)
        try:
            try:
                # manager throws TestFailed exception on init (calls self.test) if not usable.
                manager = PKG_MANAGERS[pkgmgr]
                found += 1
                packages.update(manager().get_packages())
            except TestFailed:
                if pkgmgr in module.params['manager']:
                    module.warn('Requested package manager %s was not usable by this module' % pkgmgr)
                continue

        except Exception as e:
            if pkgmgr in module.params['manager']:
                module.warn('Failed to retrieve packages with %s: %s' % (pkgmgr, to_text(e)))

    if found == 0:
        module.fail_json(msg='Could not detect a supported package manager from the following list: %s' % managers)

    results['ansible_facts'] = {}
    # Set the facts, this will override the facts in ansible_facts that might exist from previous runs
    # when using operating system level or distribution package managers
    results['ansible_facts']['packages'] = packages

    module.exit_json(**results)


if __name__ == '__main__':
    main()
