#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# (c) 2018, Gregor Riepl <onitake@gmail.com>
# based on cs_sshkeypair (c) 2015, René Moser <mail@renemoser.net>
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible. If not, see <http://www.gnu.org/licenses/>.

DOCUMENTATION = '''
---
module: cs_rootpassword
short_description: Allows resetting VM root passwords on Apache CloudStack based clouds.
description:
    - Reset the root password on a virtual machine.
    - Requires cloud-init installed in the virtual machine.
version_added: '2.8'
author: "Gregor Riepl (@onitake)"
options:
  vm:
    description:
      - Name of the virtual machine to reset the root password on.
    required: true
  domain:
    description:
      - Name of the domain the virtual machine belongs to.
  account:
    description:
      - Account the virtual machine belongs to.
  project:
    description:
      - Name of the project the virtual machine belongs to.
  poll_async:
    description:
      - Poll async jobs until job has finished.
    default: yes
    type: bool
extends_documentation_fragment: cloudstack
'''

EXAMPLES = '''
# reset and get the root password
- local_action:
    cs_rootpassword:
      name: myvirtualmachine
  register: root
- debug:
    msg: "new root password is {{ root.password }}"
# reboot the virtual machine to activate the new password
- local_action:
    cs_instance:
      name: myvirtualmachine
      state: restarted
  when: root is changed
'''

RETURN = '''
---
id:
  description: ID of the virtual machine.
  returned: success
  type: string
  sample: a6f7a5fc-43f8-11e5-a151-feff819cdc9f
password:
  description: The new root password.
  returned: success
  type: string
  sample: ahQu5nuNge3keesh
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.cloudstack import (
    AnsibleCloudStack,
    CloudStackException,
    cs_required_together,
    cs_argument_spec
)

class AnsibleCloudStackPasswordReset(AnsibleCloudStack):

    def __init__(self, module):
        super(AnsibleCloudStackPasswordReset, self).__init__(module)
        self.returns = {
            'password':     'password',
        }
        self.password = None


    def reset_password(self):
        args                = {}
        args['domainid']    = self.get_domain('id')
        args['account']     = self.get_account('name')
        args['projectid']   = self.get_project('id')
        args['id']          = self.get_vm('id')

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
        vm = dict(required=True),
        domain = dict(default=None),
        account = dict(default=None),
        project = dict(default=None),
        poll_async=dict(type='bool', default=True),
    ))

    module = AnsibleModule(
        argument_spec=argument_spec,
        required_together=cs_required_together(),
        supports_check_mode=True
    )

    try:
        acs_password = AnsibleCloudStackPasswordReset(module)
        password = acs_password.reset_password()
        result = acs_password.get_result({'password':password})

    except CloudStackException as e:
        module.fail_json(msg='CloudStackException: %s' % str(e))

    module.exit_json(**result)

if __name__ == '__main__':
    main()
