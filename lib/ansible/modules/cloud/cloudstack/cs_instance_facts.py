#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# (c) 2016, René Moser <mail@renemoser.net>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['stableinterface'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: cs_instance_facts
short_description: Gathering facts from the API of instances from Apache CloudStack based clouds.
description:
    - Gathering facts from the API of an instance.
version_added: "2.1"
author: "René Moser (@resmo)"
options:
  name:
    description:
      - Name or display name of the instance.
    required: true
  domain:
    description:
      - Domain the instance is related to.
  account:
    description:
      - Account the instance is related to.
  project:
    description:
      - Project the instance is related to.
extends_documentation_fragment: cloudstack
'''

EXAMPLES = '''
- name: gather instance facts
  cs_instance_facts:
    name: web-vm-1
  delegate_to: localhost
  register: vm

- debug:
    var: cloudstack_instance

- debug:
    var: vm
'''

RETURN = '''
---
id:
  description: UUID of the instance.
  returned: success
  type: string
  sample: 04589590-ac63-4ffc-93f5-b698b8ac38b6
name:
  description: Name of the instance.
  returned: success
  type: string
  sample: web-01
display_name:
  description: Display name of the instance.
  returned: success
  type: string
  sample: web-01
group:
  description: Group name of the instance is related.
  returned: success
  type: string
  sample: web
created:
  description: Date of the instance was created.
  returned: success
  type: string
  sample: 2014-12-01T14:57:57+0100
password_enabled:
  description: True if password setting is enabled.
  returned: success
  type: boolean
  sample: true
password:
  description: The password of the instance if exists.
  returned: success
  type: string
  sample: Ge2oe7Do
ssh_key:
  description: Name of SSH key deployed to instance.
  returned: success
  type: string
  sample: key@work
domain:
  description: Domain the instance is related to.
  returned: success
  type: string
  sample: example domain
account:
  description: Account the instance is related to.
  returned: success
  type: string
  sample: example account
project:
  description: Name of project the instance is related to.
  returned: success
  type: string
  sample: Production
default_ip:
  description: Default IP address of the instance.
  returned: success
  type: string
  sample: 10.23.37.42
public_ip:
  description: Public IP address with instance via static NAT rule.
  returned: success
  type: string
  sample: 1.2.3.4
iso:
  description: Name of ISO the instance was deployed with.
  returned: success
  type: string
  sample: Debian-8-64bit
template:
  description: Name of template the instance was deployed with.
  returned: success
  type: string
  sample: Debian-8-64bit
service_offering:
  description: Name of the service offering the instance has.
  returned: success
  type: string
  sample: 2cpu_2gb
zone:
  description: Name of zone the instance is in.
  returned: success
  type: string
  sample: ch-gva-2
state:
  description: State of the instance.
  returned: success
  type: string
  sample: Running
security_groups:
  description: Security groups the instance is in.
  returned: success
  type: list
  sample: '[ "default" ]'
affinity_groups:
  description: Affinity groups the instance is in.
  returned: success
  type: list
  sample: '[ "webservers" ]'
tags:
  description: List of resource tags associated with the instance.
  returned: success
  type: dict
  sample: '[ { "key": "foo", "value": "bar" } ]'
hypervisor:
  description: Hypervisor related to this instance.
  returned: success
  type: string
  sample: KVM
host:
  description: Host the instance is running on.
  returned: success and instance is running
  type: string
  sample: host01.example.com
  version_added: '2.6'
instance_name:
  description: Internal name of the instance (ROOT admin only).
  returned: success
  type: string
  sample: i-44-3992-VM
volumes:
  description: List of dictionaries of the volumes attached to the instance.
  returned: success
  type: list
  sample: '[ { name: "ROOT-1369", type: "ROOT", size: 10737418240 }, { name: "data01, type: "DATADISK", size: 10737418240 } ]'
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.cloudstack import AnsibleCloudStack, cs_argument_spec


class AnsibleCloudStackInstanceFacts(AnsibleCloudStack):

    def __init__(self, module):
        super(AnsibleCloudStackInstanceFacts, self).__init__(module)
        self.instance = None
        self.returns = {
            'group': 'group',
            'hypervisor': 'hypervisor',
            'instancename': 'instance_name',
            'publicip': 'public_ip',
            'passwordenabled': 'password_enabled',
            'password': 'password',
            'serviceofferingname': 'service_offering',
            'isoname': 'iso',
            'templatename': 'template',
            'keypair': 'ssh_key',
            'hostname': 'host',
        }
        self.facts = {
            'cloudstack_instance': None,
        }

    def get_instance(self):
        instance = self.instance
        if not instance:
            instance_name = self.module.params.get('name')

            args = {
                'account': self.get_account(key='name'),
                'domainid': self.get_domain(key='id'),
                'projectid': self.get_project(key='id'),
                'fetch_list': True,
            }
            # Do not pass zoneid, as the instance name must be unique across zones.
            instances = self.query_api('listVirtualMachines', **args)
            if instances:
                for v in instances:
                    if instance_name.lower() in [v['name'].lower(), v['displayname'].lower(), v['id']]:
                        self.instance = v
                        break
        return self.instance

    def get_volumes(self, instance):
        volume_details = []
        if instance:
            args = {
                'account': self.get_account(key='name'),
                'domainid': self.get_domain(key='id'),
                'projectid': self.get_project(key='id'),
                'virtualmachineid': instance['id'],
                'fetch_list': True,
            }

            volumes = self.query_api('listVolumes', **args)
            if volumes:
                for vol in volumes:
                    volume_details.append({'size': vol['size'], 'type': vol['type'], 'name': vol['name']})
        return volume_details

    def run(self):
        instance = self.get_instance()
        if not instance:
            self.module.fail_json(msg="Instance not found: %s" % self.module.params.get('name'))
        return instance

    def get_result(self, instance):
        super(AnsibleCloudStackInstanceFacts, self).get_result(instance)
        if instance:
            if 'securitygroup' in instance:
                security_groups = []
                for securitygroup in instance['securitygroup']:
                    security_groups.append(securitygroup['name'])
                self.result['security_groups'] = security_groups
            if 'affinitygroup' in instance:
                affinity_groups = []
                for affinitygroup in instance['affinitygroup']:
                    affinity_groups.append(affinitygroup['name'])
                self.result['affinity_groups'] = affinity_groups
            if 'nic' in instance:
                for nic in instance['nic']:
                    if nic['isdefault'] and 'ipaddress' in nic:
                        self.result['default_ip'] = nic['ipaddress']
            volumes = self.get_volumes(instance)
            if volumes:
                self.result['volumes'] = volumes
        return self.result


def main():
    argument_spec = cs_argument_spec()
    argument_spec.update(dict(
        name=dict(required=True),
        domain=dict(),
        account=dict(),
        project=dict(),
    ))

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )
    acs_instance_facts = AnsibleCloudStackInstanceFacts(module=module)
    cs_instance_facts = acs_instance_facts.get_result_and_facts(
        facts_name='cloudstack_instance',
        resource=acs_instance_facts.run()
    )
    module.exit_json(**cs_instance_facts)


if __name__ == '__main__':
    main()
