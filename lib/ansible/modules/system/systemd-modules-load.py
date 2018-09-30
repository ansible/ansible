#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2018, Susant Sahani <ssahani@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['stableinterface'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: systemd-modules-load
short_description:  systemd-modules-load
description:
    - Allows you to  generate systemd-modules-load configuration files.
version_added: "2.8"
options:
    conf_path:
        description:
            - Specifies the path where to write the configuration files.
        default: "/etc/modules-load.d"
        choices: [ "/etc/modules-load.d", "/run/modules-load.d", "/usr/lib/modules-load.d" ]
    file_name:
        description:
            - This configuration file name where the configurations will be written. Note the file name will be
              automatically have the extension .conf.
    modules:
        description:
            - List of module names.
    state:
        description:
            - Whether configuration files should be added or absentd.
        choices: [ "present", "absent" ]
author: "Susant Sahani (@ssahani) <ssahani@gmail.com>"
'''

EXAMPLES = '''

- name: Create config file
  systemd-modules-load:
    file_name: my_tunnel
    modules:
      - ipip
      - sit
      - vti
    state: absent

- name: Remove config file
  systemd-modules-load:
    file_name: ipip
    state: absent
'''

RETURN = r'''
'''

import os
import tempfile
from ansible.module_utils.basic import get_platform, AnsibleModule

UNIT_PATH_MODULES_LOAD = '/usr/lib/modules-load.d'
UNIT_PATH_MODULES_LOAD_SYSTEM = '/etc/modules-load.d'
UNIT_PATH_MODULES_LOAD_RUN = '/run/modules-load.d'


class SystemdModulesLoad(object):

    def __init__(self, module):
        self.module = module
        self.args = self.module.params
        self.conf_path = module.params['conf_path']
        self.file_name = module.params['file_name']
        self.modules = module.params['modules']
        self.state = module.params['state']
        self.changed = False
        self.result = {}

    def remove_files(self):
        paths = [UNIT_PATH_MODULES_LOAD_RUN, UNIT_PATH_MODULES_LOAD_SYSTEM, UNIT_PATH_MODULES_LOAD]
        rc = False

        list_conf_files = self.file_name.split(' ')
        for conf_file in list_conf_files:
            conf_file += '.conf'
            if os.path.exists(os.path.join(self.conf_path, conf_file)):
                os.remove(os.path.join(self.conf_path, conf_file))
                self.changed = True
                rc = True

        return rc

    def write_configs_to_file(self):
        file_modules = []
        conf_file = os.path.join(self.conf_path, self.file_name) + '.conf'

        if not os.path.exists(self.conf_path):
            os.makedirs(self.conf_path, exist_ok=True)
            self.changed = True

        if os.path.exists(conf_file):
            with open(conf_file) as f:
                for line in f:
                    line = line.rstrip("\n")
                    file_modules.append(line)

                    if set(file_modules) == set(self.modules):
                        return True

        tmpfd, tmpfile = tempfile.mkstemp()

        with open(tmpfile, "w") as f:
            for kmod in self.modules:
                f.write(kmod + '\n')

        self.module.atomic_move(tmpfile, conf_file)
        self.changed = True

        return True

    def configure_modules_load(self):
        rc = False

        if self.state == 'present':
            rc = self.write_configs_to_file()
        elif self.state == 'absent':
            rc = self.remove_files()

        self.result['changed'] = self.changed
        self.result['result'] = rc

        return self.result


def main():
    module = AnsibleModule(
        argument_spec=dict(
            conf_path=dict(default=UNIT_PATH_MODULES_LOAD_SYSTEM, type='path', choices=[UNIT_PATH_MODULES_LOAD, UNIT_PATH_MODULES_LOAD_RUN,
                                                                                        UNIT_PATH_MODULES_LOAD_SYSTEM]),
            file_name=dict(default=None, type='path'),
            modules=dict(required=False, default=None, type=list),
            state=dict(choices=['present', 'absent'], required=True),
        ),
        supports_check_mode=True
    )

    conf_path = module.params['conf_path']
    file_name = module.params['file_name']
    modules = module.params['modules']
    state = module.params['state']

    if file_name is None:
        module.fail_json(msg='file_name cannot be None')

    if state == 'present' and modules is None:
        module.fail_json(msg='modules cannot be None when state is present')

    modules_load = SystemdModulesLoad(module)
    result = modules_load.configure_modules_load()

    module.exit_json(**result)


if __name__ == '__main__':
    main()
