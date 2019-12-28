#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# (c) 2019, Lorenz Schori <lo@znerol.ch>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: exo_rdns_record
short_description: Manages reverse DNS records for Exoscale compute instances.
description:
    - Set and unset reverse DNS record on Exoscale instance.
version_added: "2.10"
author: "Lorenz Schori (@znerol)"
options:
  name:
    description:
      - Name of the compute instance
    required: true
    type: str
  content:
    aliases: [ 'value' ]
    description:
      - Reverse DSN name for the cs instance. Required if state=present.
    type: str
  state:
    description:
      - State of the record.
    default: present
    choices: [ 'present', 'absent' ]
    type: str
extends_documentation_fragment: cloudstack
'''

EXAMPLES = '''
- name: Set the reverse DNS for a virtual machine
  local_action:
    name: web-vm-1
    content: www.example.com

- name: Delete the reverse DNS for a virtual machine
  local_action:
    name: web-vm-1
    state: absent
'''

RETURN = '''
---
exo_rdns_domain:
  description: Reverse DSN name for the cs instance
  returned: success
  type: str
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_bytes, to_text
from ansible.module_utils.cloudstack import (
    AnsibleCloudStack,
    cs_argument_spec,
    cs_required_together
)


class ExoRdnsRecord(AnsibleCloudStack):

    def __init__(self, module):
        super(ExoRdnsRecord, self).__init__(module)

        self.name = self.module.params.get('name')
        self.content = self.module.params.get('content')

        self.returns = {
            'domain': 'domain'
        }

        self.instance = None

    def get_instance(self):
        instance = self.instance
        if not instance:
            args = {
                'account': self.get_account(key='name'),
                'domainid': self.get_domain(key='id'),
                'projectid': self.get_project(key='id'),
                'fetch_list': True,
            }
            # Do not pass zoneid, as the instance name must be unique across
            # zones.
            instances = self.query_api('listVirtualMachines', **args)
            if instances:
                for v in instances:
                    if self.name.lower() in [v['name'].lower(), v['displayname'].lower(), v['id']]:
                        self.instance = v
                        break

        return self.instance

    def get_record(self, instance):
        result = {}

        res = self.query_api('queryReverseDnsForVirtualMachine',
                             id=instance['id'])
        nics = res['virtualmachine'].get('nic', [])

        defaultnics = [nic for nic in nics if nic.get('isdefault', False)]

        if len(defaultnics) > 0:
            domains = [record['domainname'] for record
                       in defaultnics[0].get('reversedns', [])
                       if 'domainname' in record]

            if len(domains) > 0:
                result = {
                    'domainname': domains[0],
                }

        return result

    def present_record(self):
        instance = self.get_instance()

        if not instance:
            self.module.fail_json(
                msg="No virtual machine with name=%s found. " % self.name)

        data = {
            'domainname': self.content,
        }
        record = self.get_record(instance)
        if self.has_changed(data, record):
            self.result['changed'] = True
            self.result['diff']['before'] = record
            self.result['diff']['after'] = data
            if not self.module.check_mode:
                self.query_api('updateReverseDnsForVirtualMachine',
                               id=instance['id'],
                               domainname=data['domainname'])

        return data

    def absent_record(self):
        instance = self.get_instance()

        if instance:
            record = self.get_record(instance)
            if record:
                self.result['diff']['before'] = record
                self.result['changed'] = True
                if not self.module.check_mode:
                    self.query_api('deleteReverseDnsFromVirtualMachine',
                                   id=instance['id'])

            return record

    def get_result(self, record):
        self.result['exo_rdns_domain'] = record
        return self.result


def main():
    argument_spec = cs_argument_spec()
    argument_spec.update(dict(
        name=dict(required=True),
        content=dict(aliases=['value']),
        state=dict(choices=['present', 'absent'], default='present'),
    ))

    module = AnsibleModule(
        argument_spec=argument_spec,
        required_together=cs_required_together(),
        required_if=[
            ('state', 'present', ['content']),
        ],
        supports_check_mode=True,
    )

    exo_rdns_record = ExoRdnsRecord(module)
    if module.params.get('state') == "present":
        record = exo_rdns_record.present_record()
    else:
        record = exo_rdns_record.absent_record()

    result = exo_rdns_record.get_result(record)
    module.exit_json(**result)


if __name__ == '__main__':
    main()
