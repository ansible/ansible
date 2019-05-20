#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: ipmi_facts
short_description: Facts collection for ipmi BMC devices
description:
  - Use this module for querying ipmi informations
version_added: "2.9"
notes:
    - "This module creates a new top-level C(ipmi_facts) fact,
      which contains IPMI powerstate and boot informations"
options:
  name:
    description:
      - Hostname or ip address of the BMC.
    required: true
  port:
    description:
      - Remote RMCP port.
    default: 623
  user:
    description:
      - Username to use to connect to the BMC.
    required: true
  password:
    description:
      - Password to connect to the BMC.
    required: true
  timeout:
    description:
      - Maximum number of seconds before interrupt request.
    default: 300
requirements:
  - "python >= 2.6"
  - pyghmi
author: "Luca Lorenzetto (@remixtj) <lorenzetto.luca@gmail.com>"
'''

RETURN = '''
bootdev:
    description: The boot device name which will be used for the next boot (and beyond if persistent).
    returned: success
    type: str
    sample: default
bootdev_persistent:
    description: If True, system firmware will use the specified device beyond next boot.
    returned: success
    type: bool
    sample: false
uefimode:
    description: If True, system firmware will use UEFI boot explicitly.
    returned: success
    type: bool
    sample: false
powerstate:
    description: The current power state of the machine.
    returned: success
    type: str
    sample: on
'''

EXAMPLES = '''
# Ensure machine is powered on.
- ipmi_facts:
    name: test.testdomain.com
    user: admin
    password: password
- debug:
    var: ipmi_facts
'''

import traceback

PYGHMI_IMP_ERR = None
try:
    from pyghmi.ipmi import command
except ImportError:
    PYGHMI_IMP_ERR = traceback.format_exc()
    command = None

from ansible.module_utils.basic import AnsibleModule, missing_required_lib


def main():
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(required=True),
            port=dict(default=623, type='int'),
            user=dict(required=True),
            password=dict(required=True, no_log=True),
            timeout=dict(default=300, type='int'),
        ),
        supports_check_mode=True,
    )

    if command is None:
        module.fail_json(msg=missing_required_lib('pyghmi'), exception=PYGHMI_IMP_ERR)

    name = module.params['name']
    port = module.params['port']
    user = module.params['user']
    password = module.params['password']
    timeout = module.params['timeout']

    # --- run command ---
    try:
        ipmi_cmd = command.Command(
            bmc=name, userid=user, password=password, port=port
        )
        module.debug('ipmi instantiated - name: "%s"' % name)

        current_powerstate = ipmi_cmd.get_power()
        current_bootdev = ipmi_cmd.get_bootdev()
        current_bootdev['bootdev_persistent'] = current_bootdev.pop('persistent')
        response = current_powerstate.copy()
        response.update(current_bootdev)
        changed = False

        if 'error' in response:
            module.fail_json(msg=response['error'])

        module.exit_json(changed=changed,
                         ansible_facts=dict(ipmi_facts=response))
    except Exception as e:
        module.fail_json(msg=str(e))


if __name__ == '__main__':
    main()
