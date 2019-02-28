#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# (c) 2018, Gregor Riepl <onitake@gmail.com>
# based on cs_sshkeypair (c) 2015, René Moser <mail@renemoser.net>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: cs_instance_password_reset
short_description: Allows resetting VM the default passwords on Apache CloudStack based clouds.
description:
    - Resets the default user account's password on an instance.
    - Requires cloud-init to be installed in the virtual machine.
    - The passwordenabled flag must be set on the template associated with the VM.
version_added: '2.8'
author: Gregor Riepl (@onitake)
options:
  vm:
    description:
      - Name of the virtual machine to reset the password on.
    type: str
    required: true
  domain:
    description:
      - Name of the domain the virtual machine belongs to.
    type: str
  account:
    description:
      - Account the virtual machine belongs to.
    type: str
  project:
    description:
      - Name of the project the virtual machine belongs to.
    type: str
  zone:
    description:
      - Name of the zone in which the instance is deployed.
      - If not set, the default zone is used.
    type: str
  poll_async:
    description:
      - Poll async jobs until job has finished.
    type: bool
    default: yes
extends_documentation_fragment: cloudstack
'''

EXAMPLES = '''
- name: stop the virtual machine before resetting the password
  cs_instance:
    name: myvirtualmachine
    state: stopped
  delegate_to: localhost

- name: reset and get new default password
  cs_instance_password_reset:
    vm: myvirtualmachine
  register: root
  delegate_to: localhost
- debug:
    msg: "new default password is {{ root.password }}"

- name: boot the virtual machine to activate the new password
  cs_instance:
    name: myvirtualmachine
    state: started
  delegate_to: localhost
  when: root is changed
'''

RETURN = '''
---
id:
  description: ID of the virtual machine.
  returned: success
  type: str
  sample: a6f7a5fc-43f8-11e5-a151-feff819cdc9f
password:
  description: The new default password.
  returned: success
  type: str
  sample: ahQu5nuNge3keesh
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.cloudstack import (
    AnsibleCloudStack,
    cs_required_together,
    cs_argument_spec
)


class AnsibleCloudStackPasswordReset(AnsibleCloudStack):

    def __init__(self, module):
        super(AnsibleCloudStackPasswordReset, self).__init__(module)
        self.returns = {
            'password': 'password',
        }
        self.password = None

    def reset_password(self):
        args = {
            'id': self.get_vm(key='id'),
        }

        res = None
        self.result['changed'] = True
        if not self.module.check_mode:
            res = self.query_api('resetPasswordForVirtualMachine', **args)

            poll_async = self.module.params.get('poll_async')
            if res and poll_async:
                res = self.poll_job(res, 'virtualmachine')

        if res and 'password' in res:
            self.password = res['password']

        return self.password


def main():
    argument_spec = cs_argument_spec()
    argument_spec.update(dict(
        vm=dict(required=True),
        domain=dict(),
        account=dict(),
        project=dict(),
        zone=dict(),
        poll_async=dict(type='bool', default=True),
    ))

    module = AnsibleModule(
        argument_spec=argument_spec,
        required_together=cs_required_together(),
        supports_check_mode=True
    )

    acs_password = AnsibleCloudStackPasswordReset(module)
    password = acs_password.reset_password()
    result = acs_password.get_result({'password': password})

    module.exit_json(**result)


if __name__ == '__main__':
    main()
