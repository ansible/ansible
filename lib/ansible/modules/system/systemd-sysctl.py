#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2018, Susant Sahani <susant@redhat.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['stableinterface'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: systemd-sysctl
short_description:  automates systemd-sysctl configuration.
description:
    - Allows you to generate systemd-sysctl configuration files.
version_added: "2.8"
options:
    conf_path:
        description:
            - Specifies the path where to write the configuration files.
        default: "/etc/sysctl.d"
        choices: [ "/etc/sysctl.d", "/run/sysctl.d", "/usr/lib/sysctl.d" ]
    file_name:
        description:
            - This configuration file name where the configurations will be written. Note the file name will be
              automatically have the extension .conf.
    variables:
        description:
            - Space separated list of sysctl variables.
    action:
        description:
            - Whether configuration files should be added or removed.
        choices: [ "create", "remove" ]
author: "Susant Sahani (@ssahani) <susant@redhat.com>"
'''

EXAMPLES = '''
# Create config file
- systemd-sysctl:
       file_name: my_sysctl
       variables: "net.netfilter.nf_conntrack_max=131072 net.ipv4.ip_forward=1 net.ipv4.conf.eth0.forwading=1"
       action: create

# Remove config file
- systemd-sysctl:
       file_name: my_sysctl
       action: remove
'''

RETURN = r'''
'''

import os
from ansible.module_utils.basic import get_platform, AnsibleModule

UNIT_PATH_SYSTEMD_SYSCTL = '/usr/lib/sysctl.d'
UNIT_PATH_SYSTEMD_SYSCTL_SYSTEM = '/etc/sysctl.d'
UNIT_PATH_SYSTEMD_SYSCTL_RUN = '/run/sysctl.d'


class SystemdVariablesLoad(object):

    def __init__(self, module):
        self.module = module
        self.args = self.module.params
        self.conf_path = module.params['conf_path']
        self.file_name = module.params['file_name']
        self.variables = module.params['variables']
        self.action = module.params['action']
        self.changed = False

    def remove_files(self):
        paths = [UNIT_PATH_SYSTEMD_SYSCTL_RUN, UNIT_PATH_SYSTEMD_SYSCTL_SYSTEM, UNIT_PATH_SYSTEMD_SYSCTL]
        rc = False

        list_conf_files = self.file_name.split(' ')
        for conf_file in list_conf_files:
            conf_file += '.conf'
            if os.path.exists(os.path.join(self.conf_path, conf_file)):
                os.remove(os.path.join(self.conf_path, conf_file))
                rc = True

        return rc

    def write_configs_to_file(self):
        rc = False

        if not os.path.exists(self.conf_path):
            os.makedirs(self.conf_path, exist_ok=True)

        self.file_name += '.conf'
        with open(os.path.join(self.conf_path, self.file_name), "w") as f:
            variables_list = self.variables.split(' ')
            for variable in variables_list:
                f.write(variable + '\n')
                rc = True

        return rc

    def configure_systemd_sysctl(self):
        rc = False

        if self.action == 'create':
            rc = self.write_configs_to_file()
        elif self.action == 'remove':
            rc = self.remove_files()

        return rc


def main():
    module = AnsibleModule(
        argument_spec=dict(
            conf_path=dict(default=UNIT_PATH_SYSTEMD_SYSCTL_SYSTEM, type='str',
                           choices=[UNIT_PATH_SYSTEMD_SYSCTL, UNIT_PATH_SYSTEMD_SYSCTL_RUN, UNIT_PATH_SYSTEMD_SYSCTL_SYSTEM]),
            file_name=dict(default=None, type='str'),
            variables=dict(required=False, default=None, type='str'),
            action=dict(choices=['create', 'remove'], required=True),
        ),
        supports_check_mode=True
    )

    conf_path = module.params['conf_path']
    file_name = module.params['file_name']
    variables = module.params['variables']
    action = module.params['action']

    if file_name is None:
        module.fail_json(msg='file_name cannot be None')

    if action == 'create' and variables is None:
        module.fail_json(msg='variables cannot be None when action is create')

    variables_load = SystemdVariablesLoad(module)
    result = variables_load.configure_systemd_sysctl()

    module.exit_json(changed=result)


if __name__ == '__main__':
    main()
