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
      - The package manager used by the system so we can query the package information
    default: auto
    choices: ["auto", "rpm", "apt"]
    required: False
version_added: "2.5"
author:
  - Matthew Jones
  - Brian Coca
  - Adam Miller
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

import sys

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_text


def rpm_package_list():

    try:
        import rpm
    except ImportError:
        module.fail_json(msg='Unable to use the rpm python bindings, please ensure they are installed under the python the module runs under')

    trans_set = rpm.TransactionSet()
    installed_packages = {}
    for package in trans_set.dbMatch():
        package_details = dict(name=package[rpm.RPMTAG_NAME],
                               version=package[rpm.RPMTAG_VERSION],
                               release=package[rpm.RPMTAG_RELEASE],
                               epoch=package[rpm.RPMTAG_EPOCH],
                               arch=package[rpm.RPMTAG_ARCH],
                               source='rpm')
        if package_details['name'] not in installed_packages:
            installed_packages[package_details['name']] = [package_details]
        else:
            installed_packages[package_details['name']].append(package_details)
    return installed_packages


def apt_package_list():

    try:
        import apt
    except ImportError:
        module.fail_json(msg='Unable to use the apt python bindings, please ensure they are installed under the python the module runs under')

    apt_cache = apt.Cache()
    installed_packages = {}
    apt_installed_packages = [pk for pk in apt_cache.keys() if apt_cache[pk].is_installed]
    for package in apt_installed_packages:
        ac_pkg = apt_cache[package].installed
        package_details = dict(name=package, version=ac_pkg.version, arch=ac_pkg.architecture, source='apt')
        if package_details['name'] not in installed_packages:
            installed_packages[package_details['name']] = [package_details]
        else:
            installed_packages[package_details['name']].append(package_details)
    return installed_packages


# FIXME: add more listing methods
def main():
    global module
    module = AnsibleModule(argument_spec=dict(manager=dict()), supports_check_mode=True)
    manager = module.params['manager']
    packages = {}
    results = {}

    if manager is None or manager == 'auto':

        # detect!
        for manager_lib in ('rpm', 'apt'):
            try:
                dummy = __import__(manager_lib)
                manager = manager_lib
                break
            except ImportError:
                pass

        # FIXME: add more detection methods
    try:
        if manager == "rpm":
            packages = rpm_package_list()
        elif manager == "apt":
            packages = apt_package_list()
        else:
            if manager:
                results['msg'] = 'Unsupported package manager: %s' % manager
                results['skipped'] = True
            else:
                module.fail_json(msg='Could not detect supported package manager')
    except Exception as e:
        from traceback import format_tb
        module.fail_json(msg='Failed to retrieve packages: %s' % to_text(e), exception=format_tb(sys.exc_info()[2]))

    results['ansible_facts'] = {}
    # Set the facts, this will override the facts in ansible_facts that might
    # exist from previous runs when using operating system level or distribution
    # package managers
    results['ansible_facts']['packages'] = packages

    module.exit_json(**results)


if __name__ == '__main__':
    main()
