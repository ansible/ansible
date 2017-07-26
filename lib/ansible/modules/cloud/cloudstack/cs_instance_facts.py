#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# (c) 2016, René Moser <mail@renemoser.net>
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

ANSIBLE_METADATA = {'metadata_version': '1.0',
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
    required: false
    default: null
  account:
    description:
      - Account the instance is related to.
    required: false
    default: null
  project:
    description:
      - Project the instance is related to.
    required: false
    default: null
extends_documentation_fragment: cloudstack
'''

EXAMPLES = '''
- cs_instance_facts:
    name: web-vm-1
  delegate_to: localhost

- debug:
    var: cloudstack_instance
'''

RETURN = '''
---
cloudstack_instance.id:
  description: UUID of the instance.
  returned: success
  type: string
  sample: 04589590-ac63-4ffc-93f5-b698b8ac38b6
cloudstack_instance.name:
  description: Name of the instance.
  returned: success
  type: string
  sample: web-01
cloudstack_instance.display_name:
  description: Display name of the instance.
  returned: success
  type: string
  sample: web-01
cloudstack_instance.group:
  description: Group name of the instance is related.
  returned: success
  type: string
  sample: web
created:
  description: Date of the instance was created.
  returned: success
  type: string
  sample: 2014-12-01T14:57:57+0100
cloudstack_instance.password_enabled:
  description: True if password setting is enabled.
  returned: success
  type: boolean
  sample: true
cloudstack_instance.password:
  description: The password of the instance if exists.
  returned: success
  type: string
  sample: Ge2oe7Do
cloudstack_instance.ssh_key:
  description: Name of SSH key deployed to instance.
  returned: success
  type: string
  sample: key@work
cloudstack_instance.domain:
  description: Domain the instance is related to.
  returned: success
  type: string
  sample: example domain
cloudstack_instance.account:
  description: Account the instance is related to.
  returned: success
  type: string
  sample: example account
cloudstack_instance.project:
  description: Name of project the instance is related to.
  returned: success
  type: string
  sample: Production
cloudstack_instance.default_ip:
  description: Default IP address of the instance.
  returned: success
  type: string
  sample: 10.23.37.42
cloudstack_instance.public_ip:
  description: Public IP address with instance via static NAT rule.
  returned: success
  type: string
  sample: 1.2.3.4
cloudstack_instance.iso:
  description: Name of ISO the instance was deployed with.
  returned: success
  type: string
  sample: Debian-8-64bit
cloudstack_instance.template:
  description: Name of template the instance was deployed with.
  returned: success
  type: string
  sample: Debian-8-64bit
cloudstack_instance.service_offering:
  description: Name of the service offering the instance has.
  returned: success
  type: string
  sample: 2cpu_2gb
cloudstack_instance.zone:
  description: Name of zone the instance is in.
  returned: success
  type: string
  sample: ch-gva-2
cloudstack_instance.state:
  description: State of the instance.
  returned: success
  type: string
  sample: Running
cloudstack_instance.security_groups:
  description: Security groups the instance is in.
  returned: success
  type: list
  sample: '[ "default" ]'
cloudstack_instance.affinity_groups:
  description: Affinity groups the instance is in.
  returned: success
  type: list
  sample: '[ "webservers" ]'
cloudstack_instance.tags:
  description: List of resource tags associated with the instance.
  returned: success
  type: dict
  sample: '[ { "key": "foo", "value": "bar" } ]'
cloudstack_instance.hypervisor:
  description: Hypervisor related to this instance.
  returned: success
  type: string
  sample: KVM
cloudstack_instance.instance_name:
  description: Internal name of the instance (ROOT admin only).
  returned: success
  type: string
  sample: i-44-3992-VM
cloudstack_instance.volumes:
  description: List of dictionaries of the volumes attached to the instance.
  returned: success
  type: list
  sample: '[ { name: "ROOT-1369", type: "ROOT", size: 10737418240 }, { name: "data01, type: "DATADISK", size: 10737418240 } ]'
'''

import base64

# import cloudstack common
from ansible.module_utils.cloudstack import *

class AnsibleCloudStackInstanceFacts(AnsibleCloudStack):

    def __init__(self, module):
        super(AnsibleCloudStackInstanceFacts, self).__init__(module)
        self.instance = None
        self.returns = {
            'group':                'group',
            'hypervisor':           'hypervisor',
            'instancename':         'instance_name',
            'publicip':             'public_ip',
            'passwordenabled':      'password_enabled',
            'password':             'password',
            'serviceofferingname':  'service_offering',
            'isoname':              'iso',
            'templatename':         'template',
            'keypair':              'ssh_key',
        }
        self.facts = {
            'cloudstack_instance': None,
        }


    def get_instance(self):
        instance = self.instance
        if not instance:
            instance_name = self.module.params.get('name')

            args                = {}
            args['account']     = self.get_account(key='name')
            args['domainid']    = self.get_domain(key='id')
            args['projectid']   = self.get_project(key='id')
            # Do not pass zoneid, as the instance name must be unique across zones.
            instances = self.cs.listVirtualMachines(**args)
            if instances:
                for v in instances['virtualmachine']:
                    if instance_name.lower() in [ v['name'].lower(), v['displayname'].lower(), v['id'] ]:
                        self.instance = v
                        break
        return self.instance

    def get_volumes(self, instance):
        volume_details = []
        if instance:
            args                = {}
            args['account']     = instance.get('account')
            args['domainid']    = instance.get('domainid')
            args['projectid']   = instance.get('projectid')
            args['virtualmachineid'] = instance['id']

            volumes = self.cs.listVolumes(**args)
            if volumes:
                for vol in volumes['volume']:
                    volume_details.append({'size': vol['size'], 'type': vol['type'], 'name': vol['name']})
        return volume_details

    def run(self):
        instance = self.get_instance()
        if not instance:
            self.module.fail_json(msg="Instance not found: %s" % self.module.params.get('name'))
        self.facts['cloudstack_instance'] = self.get_result(instance)
        return self.facts


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
        name = dict(required=True),
        domain = dict(default=None),
        account = dict(default=None),
        project = dict(default=None),
    ))

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    cs_instance_facts = AnsibleCloudStackInstanceFacts(module=module).run()
    cs_facts_result = dict(changed=False, ansible_facts=cs_instance_facts)
    module.exit_json(**cs_facts_result)

from ansible.module_utils.basic import *
if __name__ == '__main__':
    main()
