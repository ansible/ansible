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
module: cs_instance_info
short_description: Gathering information from the API of instances from Apache CloudStack based clouds.
description:
    - Gathering information from the API of an instance.
    - This module was called C(cs_instance_facts) before Ansible 2.9, returning C(ansible_facts) with key C(cloudstack_instance).
      Since Ansible 2.6, the module also returned registerable results.
      Note that the M(cs_instance_info) module no longer returns C(ansible_facts)!
version_added: '2.1'
author: René Moser (@resmo)
options:
  name:
    description:
      - Name or display name of the instance.
    type: str
    required: true
  domain:
    description:
      - Domain the instance is related to.
    type: str
  account:
    description:
      - Account the instance is related to.
    type: str
  project:
    description:
      - Project the instance is related to.
    type: str
extends_documentation_fragment: cloudstack
'''

EXAMPLES = '''
- name: gather instance information
  cs_instance_info:
    name: web-vm-1
  delegate_to: localhost
  register: vm

- name: Show the returned results of the registered variable
  debug:
    var: vm

# When the module is called as cs_instance_facts, return values are also
# published in ansible_facts['cloudstack_instance'] and can be used as
# follows. Note that this is deprecated and will stop working in
# Ansible 2.13.
- name: gather instance information
  cs_instance_facts:
    name: web-vm-1
  delegate_to: localhost

- name: Show the facts by the ansible_facts key cloudstack_instance
  debug:
    var: cloudstack_instance
'''

RETURN = '''
---
id:
  description: UUID of the instance.
  returned: success
  type: str
  sample: 04589590-ac63-4ffc-93f5-b698b8ac38b6
name:
  description: Name of the instance.
  returned: success
  type: str
  sample: web-01
display_name:
  description: Display name of the instance.
  returned: success
  type: str
  sample: web-01
group:
  description: Group name of the instance is related.
  returned: success
  type: str
  sample: web
created:
  description: Date of the instance was created.
  returned: success
  type: str
  sample: 2014-12-01T14:57:57+0100
password_enabled:
  description: True if password setting is enabled.
  returned: success
  type: bool
  sample: true
password:
  description: The password of the instance if exists.
  returned: success
  type: str
  sample: Ge2oe7Do
ssh_key:
  description: Name of SSH key deployed to instance.
  returned: success
  type: str
  sample: key@work
domain:
  description: Domain the instance is related to.
  returned: success
  type: str
  sample: example domain
account:
  description: Account the instance is related to.
  returned: success
  type: str
  sample: example account
project:
  description: Name of project the instance is related to.
  returned: success
  type: str
  sample: Production
default_ip:
  description: Default IP address of the instance.
  returned: success
  type: str
  sample: 10.23.37.42
public_ip:
  description: Public IP address with instance via static NAT rule.
  returned: success
  type: str
  sample: 1.2.3.4
iso:
  description: Name of ISO the instance was deployed with.
  returned: success
  type: str
  sample: Debian-8-64bit
template:
  description: Name of template the instance was deployed with.
  returned: success
  type: str
  sample: Debian-8-64bit
service_offering:
  description: Name of the service offering the instance has.
  returned: success
  type: str
  sample: 2cpu_2gb
zone:
  description: Name of zone the instance is in.
  returned: success
  type: str
  sample: ch-gva-2
state:
  description: State of the instance.
  returned: success
  type: str
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
  type: list
  sample: '[ { "key": "foo", "value": "bar" } ]'
hypervisor:
  description: Hypervisor related to this instance.
  returned: success
  type: str
  sample: KVM
host:
  description: Host the instance is running on.
  returned: success and instance is running
  type: str
  sample: host01.example.com
  version_added: '2.6'
instance_name:
  description: Internal name of the instance (ROOT admin only).
  returned: success
  type: str
  sample: i-44-3992-VM
volumes:
  description: List of dictionaries of the volumes attached to the instance.
  returned: success
  type: list
  sample: '[ { name: "ROOT-1369", type: "ROOT", size: 10737418240 }, { name: "data01, type: "DATADISK", size: 10737418240 } ]'
nic:
  description: List of dictionaries of the instance nics.
  returned: success
  type: complex
  version_added: '2.8'
  contains:
    broadcasturi:
      description: The broadcast uri of the nic.
      returned: success
      type: str
      sample: vlan://2250
    gateway:
      description: The gateway of the nic.
      returned: success
      type: str
      sample: 10.1.2.1
    id:
      description: The ID of the nic.
      returned: success
      type: str
      sample: 5dc74fa3-2ec3-48a0-9e0d-6f43365336a9
    ipaddress:
      description: The ip address of the nic.
      returned: success
      type: str
      sample: 10.1.2.3
    isdefault:
      description: True if nic is default, false otherwise.
      returned: success
      type: bool
      sample: true
    isolationuri:
      description: The isolation uri of the nic.
      returned: success
      type: str
      sample: vlan://2250
    macaddress:
      description: The mac address of the nic.
      returned: success
      type: str
      sample: 06:a2:03:00:08:12
    netmask:
      description: The netmask of the nic.
      returned: success
      type: str
      sample: 255.255.255.0
    networkid:
      description: The ID of the corresponding network.
      returned: success
      type: str
      sample: 432ce27b-c2bb-4e12-a88c-a919cd3a3017
    networkname:
      description: The name of the corresponding network.
      returned: success
      type: str
      sample: network1
    traffictype:
      description: The traffic type of the nic.
      returned: success
      type: str
      sample: Guest
    type:
      description: The type of the network.
      returned: success
      type: str
      sample: Shared
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.cloudstack import AnsibleCloudStack, cs_argument_spec


class AnsibleCloudStackInstanceInfo(AnsibleCloudStack):

    def __init__(self, module):
        super(AnsibleCloudStackInstanceInfo, self).__init__(module)
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
        self.info = {
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
        super(AnsibleCloudStackInstanceInfo, self).get_result(instance)
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
                self.result['nic'] = instance['nic']
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
    is_old_facts = module._name == 'cs_instance_facts'
    if is_old_facts:
        module.deprecate("The 'cs_instance_facts' module has been renamed to 'cs_instance_info', "
                         "and the renamed one no longer returns ansible_facts", version='2.13')

    acs_instance_info = AnsibleCloudStackInstanceInfo(module=module)
    if is_old_facts:
        cs_instance_info = acs_instance_info.get_result_and_facts(
            facts_name='cloudstack_instance',
            resource=acs_instance_info.run()
        )
        module.exit_json(**cs_instance_info)
    else:
        cs_instance_info = acs_instance_info.get_result(acs_instance_info.run())
        module.exit_json(**cs_instance_info)


if __name__ == '__main__':
    main()
