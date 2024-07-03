# (c) 2017, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# most of it copied from AWX's scan_packages module

from __future__ import annotations


DOCUMENTATION = '''
module: package_facts
short_description: Package information as facts
description:
  - Return information about installed packages as facts.
options:
  manager:
    description:
      - The package manager(s) used by the system so we can query the package information.
        This is a list and can support multiple package managers per system, since version 2.8.
      - The V(portage) and V(pkg) options were added in version 2.8.
      - The V(apk) option was added in version 2.11.
      - The V(pkg_info)' option was added in version 2.13.
      - Aliases were added in 2.18, to support using C(manager={{ansible_facts['pkg_mgr']}})
    default: ['auto']
    choices:
        auto: Depending on O(strategy), will match the first or all package managers provided, in order
        rpm: For RPM based distros, requires RPM Python bindings, not installed by default on Suse (python3-rpm)
        yum: Alias to rpm
        dnf: Alias to rpm
        dnf5: Alias to rpm
        zypper: Alias to rpm
        apt: For DEB based distros, C(python-apt) package must be installed on targeted hosts
        portage: Handles ebuild packages, it requires the C(qlist) utility, which is part of 'app-portage/portage-utils'
        pkg: libpkg front end (FreeBSD)
        pkg5: Alias to pkg
        pkgng: Alias to pkg
        pacman: Archlinux package manager/builder
        apk: Alpine Linux package manager
        pkg_info: OpenBSD package manager
        openbsd_pkg: Alias to pkg_info
    type: list
    elements: str
  strategy:
    description:
      - This option controls how the module queries the package managers on the system.
    choices:
        first: returns only information for the first supported package manager available.
        all: returns information for all supported and available package managers on the system.
    default: 'first'
    type: str
    version_added: "2.8"
version_added: "2.5"
requirements:
    - See details per package manager in the O(manager) option.
author:
  - Matthew Jones (@matburt)
  - Brian Coca (@bcoca)
  - Adam Miller (@maxamillion)
extends_documentation_fragment:
  -  action_common_attributes
  -  action_common_attributes.facts
attributes:
    check_mode:
        support: full
    diff_mode:
        support: none
    facts:
        support: full
    platform:
        platforms: posix
'''

EXAMPLES = '''
- name: Gather the package facts
  ansible.builtin.package_facts:
    manager: auto

- name: Print the package facts
  ansible.builtin.debug:
    var: ansible_facts.packages

- name: Check whether a package called foobar is installed
  ansible.builtin.debug:
    msg: "{{ ansible_facts.packages['foobar'] | length }} versions of foobar are installed!"
  when: "'foobar' in ansible_facts.packages"

'''

RETURN = '''
ansible_facts:
  description: Facts to add to ansible_facts.
  returned: always
  type: complex
  contains:
    packages:
      description:
        - Maps the package name to a non-empty list of dicts with package information.
        - Every dict in the list corresponds to one installed version of the package.
        - The fields described below are present for all package managers. Depending on the
          package manager, there might be more fields for a package.
      returned: when operating system level package manager is specified or auto detected manager
      type: dict
      contains:
        name:
          description: The package's name.
          returned: always
          type: str
        version:
          description: The package's version.
          returned: always
          type: str
        source:
          description: Where information on the package came from.
          returned: always
          type: str
      sample: |-
        {
          "packages": {
            "kernel": [
              {
                "name": "kernel",
                "source": "rpm",
                "version": "3.10.0",
                ...
              },
              {
                "name": "kernel",
                "source": "rpm",
                "version": "3.10.0",
                ...
              },
              ...
            ],
            "kernel-tools": [
              {
                "name": "kernel-tools",
                "source": "rpm",
                "version": "3.10.0",
                ...
              }
            ],
            ...
          }
        }
        # Sample rpm
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
        # Sample deb
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
        # Sample pkg_info
        {
          "packages": {
            "curl": [
              {
                  "name": "curl",
                  "source": "pkg_info",
                  "version": "7.79.0"
              }
            ],
            "intel-firmware": [
              {
                  "name": "intel-firmware",
                  "source": "pkg_info",
                  "version": "20210608v0"
              }
            ],
          }
        }
'''

import re

from ansible.module_utils.common.text.converters import to_native, to_text
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.common.locale import get_best_parsable_locale
from ansible.module_utils.facts.packages import CLIMgr, RespawningLibMgr, get_all_pkg_managers


ALIASES = {
    'rpm': ['dnf', 'dnf5', 'yum' , 'zypper'],
    'pkg': ['pkg5', 'pkgng'],
    'pkg_info': ['openbsd_pkg'],
}


class RPM(RespawningLibMgr):

    LIB = 'rpm'
    CLI_BINARIES = ['rpm']
    INTERPRETERS = [
        '/usr/libexec/platform-python',
        '/usr/bin/python3',
    ]

    def list_installed(self):
        return self._lib.TransactionSet().dbMatch()

    def get_package_details(self, package):
        return dict(name=package[self._lib.RPMTAG_NAME],
                    version=package[self._lib.RPMTAG_VERSION],
                    release=package[self._lib.RPMTAG_RELEASE],
                    epoch=package[self._lib.RPMTAG_EPOCH],
                    arch=package[self._lib.RPMTAG_ARCH],)


class APT(RespawningLibMgr):

    LIB = 'apt'
    CLI_BINARIES = ['apt', 'apt-get', 'aptitude']

    def __init__(self):
        self._cache = None
        super(APT, self).__init__()

    @property
    def pkg_cache(self):
        if self._cache is not None:
            return self._cache

        self._cache = self._lib.Cache()
        return self._cache

    def list_installed(self):
        # Store the cache to avoid running pkg_cache() for each item in the comprehension, which is very slow
        cache = self.pkg_cache
        return [pk for pk in cache.keys() if cache[pk].is_installed]

    def get_package_details(self, package):
        ac_pkg = self.pkg_cache[package].installed
        return dict(name=package, version=ac_pkg.version, arch=ac_pkg.architecture, category=ac_pkg.section, origin=ac_pkg.origins[0].origin)


class PACMAN(CLIMgr):

    CLI = 'pacman'

    def list_installed(self):
        locale = get_best_parsable_locale(module)
        rc, out, err = module.run_command([self._cli, '-Qi'], environ_update=dict(LC_ALL=locale))
        if rc != 0 or err:
            raise Exception("Unable to list packages rc=%s : %s" % (rc, err))
        return out.split("\n\n")[:-1]

    def get_package_details(self, package):
        # parse values of details that might extend over several lines
        raw_pkg_details = {}
        last_detail = None
        for line in package.splitlines():
            m = re.match(r"([\w ]*[\w]) +: (.*)", line)
            if m:
                last_detail = m.group(1)
                raw_pkg_details[last_detail] = m.group(2)
            else:
                # append value to previous detail
                raw_pkg_details[last_detail] = raw_pkg_details[last_detail] + "  " + line.lstrip()

        provides = None
        if raw_pkg_details['Provides'] != 'None':
            provides = [
                p.split('=')[0]
                for p in raw_pkg_details['Provides'].split('  ')
            ]

        return {
            'name': raw_pkg_details['Name'],
            'version': raw_pkg_details['Version'],
            'arch': raw_pkg_details['Architecture'],
            'provides': provides,
        }


class PKG(CLIMgr):

    CLI = 'pkg'
    atoms = ['name', 'version', 'origin', 'installed', 'automatic', 'arch', 'category', 'prefix', 'vital']

    def list_installed(self):
        rc, out, err = module.run_command([self._cli, 'query', "%%%s" % '\t%'.join(['n', 'v', 'R', 't', 'a', 'q', 'o', 'p', 'V'])])
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
            pkg['automatic'] = bool(int(pkg['automatic']))

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
                pkg['revision'] = '0'

        if 'vital' in pkg:
            pkg['vital'] = bool(int(pkg['vital']))

        return pkg


class PORTAGE(CLIMgr):

    CLI = 'qlist'
    atoms = ['category', 'name', 'version', 'ebuild_revision', 'slots', 'prefixes', 'sufixes']

    def list_installed(self):
        rc, out, err = module.run_command(' '.join([self._cli, '-Iv', '|', 'xargs', '-n', '1024', 'qatom']), use_unsafe_shell=True)
        if rc != 0:
            raise RuntimeError("Unable to list packages rc=%s : %s" % (rc, to_native(err)))
        return out.splitlines()

    def get_package_details(self, package):
        return dict(zip(self.atoms, package.split()))


class APK(CLIMgr):

    CLI = 'apk'

    def list_installed(self):
        rc, out, err = module.run_command([self._cli, 'info', '-v'])
        if rc != 0:
            raise Exception("Unable to list packages rc=%s : %s" % (rc, err))
        return out.splitlines()

    def get_package_details(self, package):
        raw_pkg_details = {'name': package, 'version': '', 'release': ''}
        nvr = package.rsplit('-', 2)
        try:
            return {
                'name': nvr[0],
                'version': nvr[1],
                'release': nvr[2],
            }
        except IndexError:
            return raw_pkg_details


class PKG_INFO(CLIMgr):

    CLI = 'pkg_info'

    def list_installed(self):
        rc, out, err = module.run_command([self._cli, '-a'])
        if rc != 0 or err:
            raise Exception("Unable to list packages rc=%s : %s" % (rc, err))
        return out.splitlines()

    def get_package_details(self, package):
        raw_pkg_details = {'name': package, 'version': ''}
        details = package.split(maxsplit=1)[0].rsplit('-', maxsplit=1)

        try:
            return {
                'name': details[0],
                'version': details[1],
            }
        except IndexError:
            return raw_pkg_details


def main():

    # get supported pkg managers
    PKG_MANAGERS = get_all_pkg_managers()
    PKG_MANAGER_NAMES = [x.lower() for x in PKG_MANAGERS.keys()]
    # add aliases
    PKG_MANAGER_NAMES.extend([alias for alist in ALIASES.values() for alias in alist])

    # start work
    global module

    # choices are not set for 'manager' as they are computed dynamically and validated below instead of in argspec
    module = AnsibleModule(argument_spec=dict(manager={'type': 'list', 'elements': 'str', 'default': ['auto']},
                                              strategy={'choices': ['first', 'all'], 'default': 'first'}),
                           supports_check_mode=True)
    packages = {}
    results = {'ansible_facts': {}}
    managers = [x.lower() for x in module.params['manager']]
    strategy = module.params['strategy']

    if 'auto' in managers:
        # keep order from user, we do dedupe below
        managers.extend(PKG_MANAGER_NAMES)
        managers.remove('auto')

    unsupported = set(managers).difference(PKG_MANAGER_NAMES)
    if unsupported:
        if 'auto' in module.params['manager']:
            msg = 'Could not auto detect a usable package manager, check warnings for details.'
        else:
            msg = 'Unsupported package managers requested: %s' % (', '.join(unsupported))
        module.fail_json(msg=msg)

    found = 0
    seen = set()
    for pkgmgr in managers:

        if strategy == 'first' and found:
            break

        # substitute aliases for aliased
        for aliased in ALIASES.keys():
            if pkgmgr in ALIASES[aliased]:
                pkgmgr = aliased
                break

        # dedupe as per above
        if pkgmgr in seen:
            continue

        seen.add(pkgmgr)

        manager = PKG_MANAGERS[pkgmgr]()
        try:
            if manager.is_available(handle_exceptions=False):
                found += 1
                try:
                    packages.update(manager.get_packages())
                except Exception as e:
                    module.warn('Failed to retrieve packages with %s: %s' % (pkgmgr, to_text(e)))
        except Exception as e:
            if pkgmgr in module.params['manager']:
                module.warn('Requested package manager %s was not usable by this module: %s' % (pkgmgr, to_text(e)))

    if found == 0:
        msg = ('Could not detect a supported package manager from the following list: %s, '
               'or the required Python library is not installed. Check warnings for details.' % managers)
        module.fail_json(msg=msg)

    # Set the facts, this will override the facts in ansible_facts that might exist from previous runs
    # when using operating system level or distribution package managers
    results['ansible_facts']['packages'] = packages

    module.exit_json(**results)


if __name__ == '__main__':
    main()
