#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2018, Florian Paul Hoberg <florian.hoberg@credativ.de>
# Written by Florian Paul Hoberg <florian.hoberg@credativ.de>

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: cran
version_added: 2.7
short_description: (Un)installs packages for Microsoft R Open (CRAN)
description:
     - This module (un)installs packages for Microsoft R Open (CRAN).
options:
  package:
    description:
      - Package names(s) like C(vioplot), multiple values separated by space.
  state:
    description:
      - Whether to lock C(present) or unlock C(absent) package(s).
    choices: [ present, absent ]
    default: present
# informational: requirements for nodes
requirements:
- Microsoft R Open
author:
    - '"Florian Paul Hoberg (@florianpaulhoberg)" <florian.hoberg@credativ.de>'
'''

EXAMPLES = '''
- name: Install "vioplot" from CRAN
  cran:
    state: present
    package: vioplot
- name: Install multiple packages from CRAN
  cran:
    state: present
    package: vioplot A3
- name: Install "foobar" from custom CRAN repo
  cran:
    state: present
    package: foobar
    repo: https://cran.hoberg.ch
'''

RETURN = '''
package:
    description: name of used package
    returned: everytime
    type: string
    sample: vioplot
state:
    description: state of used package
    returned: everytime
    type: string
    sample: present
'''

from ansible.module_utils.basic import AnsibleModule


def get_rscript_path(module):
    """ Get path to Rscript """
    rscript_binary = module.get_bin_path('Rscript')
    if rscript_binary.endswith('Rscript'):
        return rscript_binary
    else:
        module.fail_json(msg='Error: Could not find path to Rscript binary.')


def list_package_cran(module, rscript_binary, package):
    """ List package from cran """
    rc_code, out, err = module.run_command("%s --slave -e \
                                           'p <- installed.packages(); cat(p[p[,1] == \"%s\",1])'"
                                           % (rscript_binary, package))
    if rc_code != 0:
        module.fail_json(msg='Error: ' + str(err) + str(out))
    if out == package:
        return True


def add_package_cran(module, rscript_binary, package, repository):
    """ Add package from cran """
    rc_code, out, err = module.run_command("%s --slave -e \
                                           'install.packages(pkgs=\"%s\", repos=\"%s\")'"
                                           % (rscript_binary, package, repository))
    # Check for string because on an error exit_code will be 0
    if 'DONE ('+package+')' in err:
        changed = True
        return changed
    else:
        module.fail_json(msg='Error: ' + str(err) + str(out) + str(rc_code))


def remove_package_cran(module, rscript_binary, package):
    """ Remove package from cran """
    rc_code, out, err = module.run_command("%s --slave -e \
                                           'remove.packages(pkgs=\"%s\")'"
                                           % (rscript_binary, package))
    if rc_code == 0:
        changed = True
        return changed
    else:
        module.fail_json(msg='Error: ' + str(err) + str(out))


def main():
    """ Start main program to add/remove a package from cran """
    module = AnsibleModule(
        argument_spec=dict(
            state=dict(default='present', choices=['present', 'absent']),
            package=dict(required=True, type='str'),
            repository=dict(required=False, type='str', default='https://cran.rstudio.com/'),
        ),
        supports_check_mode=True
    )

    state = module.params['state']
    package = module.params['package']
    repository = module.params['repository']
    changed = False

    # Get path of RScript
    rscript_binary = get_rscript_path(module)

    # Support for multiple packages from string
    packages = package.split()

    # Loop for every single package in packages list
    for single_package in packages:

        # Check if package is already installed
        cran_package = list_package_cran(module, rscript_binary, single_package)

        # Add a package from CRAN
        if state == "present":
            if not cran_package:
                change_state = add_package_cran(module, rscript_binary, single_package, repository)
                if changed is not True:
                    changed = change_state

        # Remove a package from CRAN
        if state == "absent":
            if cran_package:
                change_state = remove_package_cran(module, rscript_binary, single_package)
                if changed is not True:
                    changed = change_state

    # Create Ansible meta output
    response = {'package': package, 'state': state}
    module.exit_json(changed=changed, meta=response)


if __name__ == '__main__':
    main()
