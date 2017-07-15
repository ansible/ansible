#!/usr/bin/python
# -*- coding: utf-8 -*-
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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

ANSIBLE_METADATA = {
    'metadata_version': '1.0',
    'supported_by': 'community',
    'status': ['preview']
}

DOCUMENTATION = '''
---
module: kinit
version_added: "2.4"
author: "Ali (@bincyber)"
short_description: Obtain a Kerberos ticket-granting ticket
description:
  - "This module is a wrapper around kinit to obtain a short-lived Kerberos ticket-granting ticket (TGT)."
options:
  principal:
    description:
      - The principal to obtain a Kerberos ticket-granting ticket for. The principal can include the primary, instance, and realm. eg. primary/instance@REALM
    required: yes
    default: null
  password:
    description:
      - The password used to authenticate to the KDC.
    required: yes
    default: null
  lifetime:
    description:
      - The lifetime of the Kerberos ticket-granting ticket.
    required: false
    default: 60
requirements:
   - kinit
'''

EXAMPLES = '''
# obtain a Kerberos ticket with a lifetime of 30 seconds
- kinit:
    principal: johndoe
    password: supersecretpassword
    lifetime: 30

# obtain a Kerberos ticket for a principal that includes the realm
- kinit:
    principal: johndoe@REALM.EXAMPLE.COM
    password: supersecretpassword
'''

RETURN = '''
msg:
    description: the status message describing what occurred
    returned: always
    type: string
    sample: "Successfully obtained Kerberos ticket"

rc:
    description: the return code after executing kinit
    returned: always
    type: int
    sample: 0
'''

from ansible.module_utils.basic import AnsibleModule
from distutils.spawn import find_executable
import shlex


def main():

    module = AnsibleModule(
        argument_spec=dict(
            principal=dict(required=True, type='str'),
            password=dict(required=True, type='str', no_log=True),
            lifetime=dict(required=False, type='int', default=60)
        ),
        required_together=[
            ['principal', 'password']
        ],
        supports_check_mode=False,
    )

    principal = module.params['principal']
    password = module.params['password']
    lifetime = module.params.get('lifetime', 60)

    kinit = find_executable('kinit')
    if kinit is None:
        module.fail_json(msg="kinit is required")

    cmd = shlex.split('{0} {1} -l {2}'.format(kinit, principal, lifetime))

    (rc, out, err) = module.run_command(cmd, data=password, binary_data=False)
    if rc:
        module.fail_json(msg=err, rc=rc)
    else:
        module.exit_json(changed=True, msg='Successfully obtained Kerberos ticket', rc=rc)

if __name__ == '__main__':
    main()
