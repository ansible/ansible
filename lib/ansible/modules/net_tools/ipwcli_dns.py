#!/usr/bin/python

# Copyright: (c) 2020, Christian Wollinger <cwollinger@web.de>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: ipwcli_dns

short_description: Manage DNS Records for Ericsson IPWorks via ipwcli

version_added: "2.10"

description:
    - "Manage DNS records for the Ericsson IPWorks DNS server. The module will use the ipwcli to deploy the DNS records."

requirements:
   - ipwcli (installed on Ericsson IPWorks)

notes:
    - To make the DNS record changes effective, you need to run C(update dnsserver) on the ipwcli.

options:
    dnsname:
        description:
            - Name of the record.
        required: true
        type: str
    type:
        description:
            - Type of the record.
        required: true
        type: str
        choices: [ NAPTR, SRV, A, AAAA ]
    container:
        description:
            - Sets the container zone for the record.
        required: true
        type: str
    address:
        description:
            - The IP address for the A or AAAA record.
            - Required for C(type=A) or C(type=AAAA)
        type: str
    ttl:
        description:
            - Sets the TTL of the record.
        type: int
        default: 3600
    state:
        description:
            - Whether the record should exist or not.
        type: str
        choices: [ absent, present ]
        default: present
    priority:
        description:
            - Sets the priority of the SRV record.
        type: int
        default: 10
    weight:
        description:
            - Sets the weight of the SRV record.
        type: int
        default: 10
    port:
        description:
            - Sets the port of the SRV record.
            - Required for C(type=SRV)
        type: int
    target:
        description:
            - Sets the target of the SRV record.
            - Required for C(type=SRV)
        type: str
    order:
        description:
            - Sets the order of the NAPTR record.
            - Required for C(type=NAPTR)
        type: int
    preference:
        description:
            - Sets the preference of the NAPTR record.
            - Required for C(type=NAPTR)
        type: int
    flags:
        description:
            - Sets one of the possible flags of NAPTR record.
            - Required for C(type=NAPTR)
        type: str
        choices: ['S', 'A', 'U', 'P']
    service:
        description:
            - Sets the service of the NAPTR record.
            - Required for C(type=NAPTR)
        type: str
    replacement:
        description:
            - Sets the replacement of the NAPTR record.
            - Required for C(type=NAPTR)
        type: str
    username:
        description:
            - Username to login on ipwcli.
        type: str
        required: true
    password:
        description:
            - Password to login on ipwcli.
        type: str
        required: true

author:
    - Christian Wollinger (@cwollinger)
'''

EXAMPLES = '''
- name: Create A record
  ipwcli_dns:
    dnsname: example.com
    type: A
    container: ZoneOne
    address: 127.0.0.1

- name: Remove SRV record if exists
  ipwcli_dns:
    dnsname: _sip._tcp.test.example.com
    type: SRV
    container: ZoneOne
    ttl: 100
    state: absent
    target: example.com
    port: 5060

- name: Create NAPTR record
  ipwcli_dns:
    dnsname: test.example.com
    type: NAPTR
    preference: 10
    container: ZoneOne
    ttl: 100
    order: 10
    service: 'SIP+D2T'
    replacement: '_sip._tcp.test.example.com.'
    flags: S
'''

RETURN = '''
record:
    description: The created record from the input params
    type: str
    returned: always
'''

from ansible.module_utils.basic import AnsibleModule
import os


class ResourceRecord(object):

    def __init__(self, module):
        self.module = module
        self.dnsname = module.params['dnsname']
        self.dnstype = module.params['type']
        self.container = module.params['container']
        self.address = module.params['address']
        self.ttl = module.params['ttl']
        self.state = module.params['state']
        self.priority = module.params['priority']
        self.weight = module.params['weight']
        self.port = module.params['port']
        self.target = module.params['target']
        self.order = module.params['order']
        self.preference = module.params['preference']
        self.flags = module.params['flags']
        self.service = module.params['service']
        self.replacement = module.params['replacement']
        self.user = module.params['username']
        self.password = module.params['password']

    def create_naptrrecord(self):
        # create NAPTR record with the given params
        if not self.preference:
            self.module.fail_json(msg='missing required arguments for NAPTR record: preference')

        if not self.order:
            self.module.fail_json(msg='missing required arguments for NAPTR record: order')

        if not self.service:
            self.module.fail_json(msg='missing required arguments for NAPTR record: service')

        if not self.replacement:
            self.module.fail_json(msg='missing required arguments for NAPTR record: replacement')

        record = ('naptrrecord %s -set ttl=%s;container=%s;order=%s;preference=%s;flags="%s";service="%s";replacement="%s"'
                  % (self.dnsname, self.ttl, self.container, self.order, self.preference, self.flags, self.service, self.replacement))
        return record

    def create_srvrecord(self):
        # create SRV record with the given params
        if not self.port:
            self.module.fail_json(msg='missing required arguments for SRV record: port')

        if not self.target:
            self.module.fail_json(msg='missing required arguments for SRV record: target')

        record = ('srvrecord %s -set ttl=%s;container=%s;priority=%s;weight=%s;port=%s;target=%s'
                  % (self.dnsname, self.ttl, self.container, self.priority, self.weight, self.port, self.target))
        return record

    def create_arecord(self):
        # create A record with the given params
        if not self.address:
            self.module.fail_json(msg='missing required arguments for A record: address')

        if self.dnstype == 'AAAA':
            record = 'aaaarecord %s %s -set ttl=%s;container=%s' % (self.dnsname, self.address, self.ttl, self.container)
        else:
            record = 'arecord %s %s -set ttl=%s;container=%s' % (self.dnsname, self.address, self.ttl, self.container)

        return record

    def list_record(self, record):
        # check if the record exists via list on ipwcli
        search = 'list %s' % (record.replace(';', '&&').replace('set', 'where'))
        cmd = [self.module.get_bin_path('ipwcli', True)]
        cmd.append('-user=%s' % (self.user))
        cmd.append('-password=%s' % (self.password))
        rc, out, err = self.module.run_command(cmd, data=search)

        if 'Invalid username or password' in out:
            self.module.fail_json(msg='access denied at ipwcli login: Invalid username or password')

        if (('ARecord %s' % self.dnsname in out and rc == 0) or ('SRVRecord %s' % self.dnsname in out and rc == 0) or
                ('NAPTRRecord %s' % self.dnsname in out and rc == 0)):
            return True, rc, out, err

        return False, rc, out, err

    def deploy_record(self, record):
        # check what happens if create fails on ipworks
        stdin = 'create %s' % (record)
        cmd = [self.module.get_bin_path('ipwcli', True)]
        cmd.append('-user=%s' % (self.user))
        cmd.append('-password=%s' % (self.password))
        rc, out, err = self.module.run_command(cmd, data=stdin)

        if 'Invalid username or password' in out:
            self.module.fail_json(msg='access denied at ipwcli login: Invalid username or password')

        if '1 object(s) created.' in out:
            return rc, out, err
        else:
            self.module.fail_json(msg='record creation failed', stderr=out)

    def delete_record(self, record):
        # check what happens if create fails on ipworks
        stdin = 'delete %s' % (record.replace(';', '&&').replace('set', 'where'))
        cmd = [self.module.get_bin_path('ipwcli', True)]
        cmd.append('-user=%s' % (self.user))
        cmd.append('-password=%s' % (self.password))
        rc, out, err = self.module.run_command(cmd, data=stdin)

        if 'Invalid username or password' in out:
            self.module.fail_json(msg='access denied at ipwcli login: Invalid username or password')

        if '1 object(s) were updated.' in out:
            return rc, out, err
        else:
            self.module.fail_json(msg='record deletion failed', stderr=out)


def run_module():
    # define available arguments/parameters a user can pass to the module
    module_args = dict(
        dnsname=dict(type='str', required=True),
        type=dict(type='str', required=True, choices=['A', 'AAAA', 'SRV', 'NAPTR']),
        container=dict(type='str', required=True),
        address=dict(type='str', required=False),
        ttl=dict(type='int', required=False, default=3600),
        state=dict(type='str', default='present', choices=['absent', 'present']),
        priority=dict(type='int', required=False, default=10),
        weight=dict(type='int', required=False, default=10),
        port=dict(type='int', required=False),
        target=dict(type='str', required=False),
        order=dict(type='int', required=False),
        preference=dict(type='int', required=False),
        flags=dict(type='str', required=False, choices=['S', 'A', 'U', 'P']),
        service=dict(type='str', required=False),
        replacement=dict(type='str', required=False),
        username=dict(type='str', required=True),
        password=dict(type='str', required=True, no_log=True)
    )

    # define result
    result = dict(
        changed=False,
        stdout='',
        stderr='',
        rc=0,
        record=''
    )

    # supports check mode
    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    user = ResourceRecord(module)

    if user.dnstype == 'NAPTR':
        record = user.create_naptrrecord()
    elif user.dnstype == 'SRV':
        record = user.create_srvrecord()
    elif user.dnstype == 'A' or user.dnstype == 'AAAA':
        record = user.create_arecord()

    found, rc, out, err = user.list_record(record)

    if found and user.state == 'absent':
        if module.check_mode:
            module.exit_json(changed=True)
        rc, out, err = user.delete_record(record)
        result['changed'] = True
        result['record'] = record
        result['rc'] = rc
        result['stdout'] = out
        result['stderr'] = err
    elif not found and user.state == 'present':
        if module.check_mode:
            module.exit_json(changed=True)
        rc, out, err = user.deploy_record(record)
        result['changed'] = True
        result['record'] = record
        result['rc'] = rc
        result['stdout'] = out
        result['stderr'] = err
    else:
        result['changed'] = False
        result['record'] = record
        result['rc'] = rc
        result['stdout'] = out
        result['stderr'] = err

    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
