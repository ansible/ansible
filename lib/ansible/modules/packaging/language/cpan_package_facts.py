#!/usr/bin/python
# (c) 2018, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# started out with AWX's scan_packages module

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
module: cpan_package_facts
short_description: Perl's cpan package information
description:
  - Return information about installed pip packages as facts
version_added: "2.8"
requirements:
    - cpan must be installed on the target and configured for use by the user executing the mdoule.
author:
  - Matthew Jones (@matburt)
  - Brian Coca (@bcoca)
  - Adam Miller (@maxamillion)
'''

EXAMPLES = '''
- name: Just get the list from cpan, using remote user
  cpan_package_info:

- name: get the cpan packagelist for root
  cpan_package_info:
  become: yes

'''

RETURN = '''
packages:
  description: a dictionary of installed package data
  returned: always
  type: dict
  contains:
    perl:
      description: A dictionary a list of dicts with Perl package information
      returned: always
      type: dict
      sample:
        "packages": {
        }
'''

from ansible.module_utils._text import to_text
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.facts.packages import CLIMgr


class CPAN(CLIMgr):

    CLI = 'perldoc'

    def is_available(self):

        found = super(CPAN, self).is_available()
        if found:
            # perldoc is always present, but perllocal topic is only available if cpan(m) is in use.
            rc, out, err = self.m.run_command([self._cli, 'perllocal'])
            if rc != 0 or err == 'No documentation found for "perllocal"':
                found = False
        return found

    def list_installed(self):
        pass

    def get_package_details(self, package):
        pass


def main():

    # start work
    global module
    module = AnsibleModule({}, supports_check_mode=True)
    packages = {}
    results = {'packages': {}}

    found = 0
    try:
        cpan = CPAN()
        if cpan.is_available():
            found += 1
            packages = cpan.get_packages()
    except Exception as e:
        module.warn('Failed to retrieve packages with %s: %s' % (cpan._cli, to_text(e)))

    if found == 0:
        module.fail_json(msg='Unable to find a usable cpan')

    # return info
    results['packages'] = packages
    module.exit_json(**results)


if __name__ == '__main__':
    main()
