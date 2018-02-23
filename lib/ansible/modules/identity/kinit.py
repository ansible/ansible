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
  still displaying error messages and enabling the task to be logged for auditing purposes.
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
      - The lifetime of the Kerberos ticket in seconds.
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
    password: 'supersecretpassword'
    lifetime: 30

# obtain a Kerberos ticket for a principal that includes the realm
- kinit:
    principal: johndoe@REALM.EXAMPLE.COM
    password: 'supersecretpassword'

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
    sample: "Obtained a Kerberos ticket"

rc:
    description: the return code after executing klist, kinit, or kdestroy
    returned: failure
    type: int
    sample: 1

cache_name:
    description: the name of the Kerberos cache
    returned:  on success
    type: string
    sample: "KEYRING:persistent:1049221:krb_ccache_y8jzb2l"

err:
    description: the error message after executing klist, kinit, or kdestroy
    returned: failure
    type: string
    sample: "kinit: Password incorrect while getting initial credentials"
'''

from ansible.module_utils.basic import AnsibleModule
import datetime
import re
import shlex
import time


class KerberosTicket(object):
    def __init__(self, module):
        self.module = module
        self.principal = module.params['principal']
        self.password = module.params['password']
        self.lifetime = module.params.get('lifetime', 60)
        self.state = module.params['state']

        self.cache_name = None
        self.ticket = None

    @property
    def klist(self):
        return self.module.get_bin_path('klist', required=True)

    @property
    def kinit(self):
        return self.module.get_bin_path('kinit', required=True)

    @property
    def kdestroy(self):
        return self.module.get_bin_path('kdestroy', required=True)

    @property
    def max_ticket_expiry_datetime(self):
        return datetime.datetime.fromtimestamp(time.time() + self.lifetime)

    @property
    def ticket_expiry_datetime(self):
        return datetime.datetime.strptime(' '.join(self.ticket.split()[2:4]), '%m/%d/%Y %H:%M:%S')

    def get_existing_ticket(self):
        rc, out, err = self.module.run_command([self.klist, '-A'])

        if rc == 0:
            # extract existing ticket
            regexp = 'Ticket cache:\s'
            res = re.split(regexp, out)
            ticket_caches = filter(None, res)
            indexes = [ i for i, s in enumerate(ticket_caches) if self.principal in s ]

            for i in indexes:
                cache = ticket_caches[i].strip().split('\n')

                self.cache_name = cache[0]

                for ticket in cache[3:]:
                    if 'krbtgt/' not in ticket:
                        continue
                    else:
                        self.ticket = ticket
                        break

        return self.cache_name, self.ticket

    def renew_ticket(self):
        if self.max_ticket_expiry_datetime > self.ticket_expiry_datetime:
            rc, err = self.generate_new_ticket()
        else:
            rc = -1
            err = 'An existing ticket has yet to expire'
        return rc, err

    def generate_new_ticket(self):
        cmd = shlex.split('{0} {1} -l {2}'.format(self.kinit, self.principal, self.lifetime))

        rc, _, err = self.module.run_command(cmd, data=self.password, binary_data=False)
        return rc, err

    def destroy_tickets(self):
        cmd = shlex.split('{} -q'.format(self.kdestroy))

        if self.cache_name is not None:
            cmd.extend(shlex.split('-c {}'.format(self.cache_name)))

        rc, _, err = self.module.run_command(cmd)

        self.cache_name = None
        self.ticket = None

        return rc, err


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

    cache_name, ticket = kerberos_ticket.get_existing_ticket()

    if ticket is None:
        if kerberos_ticket.state == 'present':
            if module.check_mode:
                module.exit_json(changed=True)

            rc, err = kerberos_ticket.generate_new_ticket()

            if rc != 0:
                module.fail_json(msg='Failed to obtain a Kerberos ticket', rc=rc, err=err)
            else:
                module.exit_json(changed=True, msg='Obtained a Kerberos ticket', cache_name=cache_name)

        elif kerberos_ticket.state == 'absent':
            if module.check_mode:
                module.exit_json(changed=False)

            module.exit_json(changed=False, msg='No existing Kerberos tickets to destroy', cache_name=cache_name)

    else:
        if kerberos_ticket.state == 'present':
            if module.check_mode:
                if kerberos_ticket.max_ticket_expiry_datetime > kerberos_ticket.ticket_expiry_datetime:
                    module.exit_json(changed=True)
                else:
                    module.exit_json(changed=False)

            rc, err = kerberos_ticket.renew_ticket()

            if rc == -1:
                module.exit_json(changed=False, msg='An existing Kerberos ticket has yet to expire', cache_name=cache_name)
            elif rc != 0:
                module.fail_json(msg='Failed to obtain a Kerberos ticket', rc=rc, err=err)
            else:
                module.exit_json(changed=True, msg='Renewed an existing Kerberos ticket', cache_name=cache_name)

        elif kerberos_ticket.state == 'absent':
            if module.check_mode:
                module.exit_json(changed=True)

            kerberos_ticket.destroy_tickets()

            module.exit_json(changed=True, msg='Kerberos tickets destroyed', cache_name=cache_name)


if __name__ == '__main__':
    main()
