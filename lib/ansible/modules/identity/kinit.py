#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'supported_by': 'community',
    'status': ['preview']
}

DOCUMENTATION = '''
---
module: kinit
version_added: "2.5"
author: "Ali (@bincyber)"
short_description: Obtain a Kerberos ticket-granting ticket.
description:
  - "This module is a wrapper around kinit to obtain a short-lived Kerberos ticket-granting ticket (TGT).
  The M(expect) or M(shell) module could be used instead, however to ensure the principal's password is not logged,
  the I(no_log: True) task attribute must be set resulting in hidden error messages and the loss of an audit trail.
  By default, this module prevents the password for the authenticating principal from being shown or logged while
  still displaying error messages and enabling the task to be logged for auditing purposes. The default location
  of the Kerberos 5 credentials cache is used."
options:
  principal:
    description:
      - The principal to obtain a Kerberos ticket for. The principal can include the primary, instance, and realm. eg. primary/instance@REALM
    required: yes
    default: null
  password:
    description:
      - The password used to authenticate to the Kerberos server.
    required: yes
    default: null
  lifetime:
    description:
      - The lifetime of the Kerberos ticket.
    required: false
    default: 60
  state:
    description:
      - The state of the Kerberos ticket. If set to C(absent), I(kdestroy) is executed to remove all existing Kerberos tickets for the principal.
    required: false
    default: "present"
    choices: [ "present", "absent" ]
requirements:
  - kinit
  - klist
  - kdestroy
notes:
  - "This module requires Kerberos 5 I(kinit), I(klist), and I(kdestroy) installed on all target systems."
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

# destroy all existing Kerberos tickets for the principal
- kinit:
    principal: johndoe
    state: absent
'''

RETURN = '''
msg:
    description: the status message describing what occurred
    returned: always
    type: string
    sample: "Obtained a short-lived Kerberos ticket"

rc:
    description: the return code after executing klist, kinit, or kdestroy
    returned: always
    type: int
    sample: 0

err:
    description: the error message after executing klist, kinit, or kdestroy
    returned: failure
    type: string
    sample: "kinit: Password incorrect while getting initial credentials"
'''

from ansible.module_utils.basic import AnsibleModule
import shlex
import datetime
import time


class KerberosTicket(object):
    def __init__(self, module):
        self.module = module
        self.principal = module.params['principal']
        self.password = module.params['password']
        self.lifetime = module.params.get('lifetime', 60)
        self.state = module.params['state']

    @property
    def klist(self):
        return self.module.get_bin_path("klist", required=True)

    @property
    def kinit(self):
        return self.module.get_bin_path("kinit", required=True)

    @property
    def kdestroy(self):
        return self.module.get_bin_path("kdestroy", required=True)

    @property
    def max_ticket_expiry_datetime(self):
        return datetime.datetime.fromtimestamp(time.time() + self.lifetime)

    def get_existing_tickets(self):
        return self.module.run_command([self.klist])

    def generate_new_ticket(self):
        cmd = shlex.split('{0} {1} -l {2}'.format(self.kinit, self.principal, self.lifetime))

        rc, out, err = self.module.run_command(cmd, data=self.password, binary_data=False)
        if rc:
            self.module.fail_json(msg="Failed to obtain a Kerberos ticket", rc=rc, err=err)
        else:
            self.module.exit_json(changed=True, msg='Obtained a short-lived Kerberos ticket', rc=rc)

    def destroy_existing_tickets(self):
        rc, out, err = self.module.run_command([self.kdestroy, '-q'])
        if rc:
            self.module.fail_json(msg="Failed to destroy existing Kerberos tickets", rc=rc, err=err)
        else:
            self.module.exit_json(changed=True, msg='Destroyed existing Kerberos tickets', rc=rc)


def main():

    module = AnsibleModule(
        argument_spec=dict(
            principal=dict(required=True, type='str'),
            password=dict(required=False, type='str', no_log=True),
            lifetime=dict(required=False, type='int', default=60),
            state=dict(default='present', choices=['present', 'absent'])
        ),
        required_if=[
            ['state', 'present', ['principal', 'password']]
        ],
        supports_check_mode=True,
    )

    kerberos_ticket = KerberosTicket(module)

    rc, out, err = kerberos_ticket.get_existing_tickets()

    # when rc != 0, klist returns stderr message that there are no existing tickets for the principal
    if rc:
        if kerberos_ticket.state == 'present':
            if module.check_mode:
                module.exit_json(changed=True)

            kerberos_ticket.generate_new_ticket()

        elif kerberos_ticket.state == 'absent':
            module.exit_json(changed=False, msg='No existing Kerberos tickets to destroy')

    if kerberos_ticket.state == 'absent':
        if module.check_mode:
            module.exit_json(changed=True)

        kerberos_ticket.destroy_existing_tickets()

    klist_output = filter(None, out.split('\n'))

    # info on tickets within the keytab starts from the 4th element in the list
    for ticket in klist_output[3:]:

        # we're only concerned with ticket-granting tickets (TGT)
        if 'krbtgt/' not in ticket:
            continue

        ticket_expiry_datetime = datetime.datetime.strptime(' '.join(ticket.split()[2:4]), '%m/%d/%Y %H:%M:%S')

        if kerberos_ticket.max_ticket_expiry_datetime > ticket_expiry_datetime:
            if module.check_mode:
                module.exit_json(changed=True)

            kerberos_ticket.generate_new_ticket()

        else:
            module.exit_json(changed=False, msg='An existing ticket has yet to expire', ticket=ticket)

if __name__ == '__main__':
    main()
