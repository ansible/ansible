#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# (c) 2015, René Moser <mail@renemoser.net>
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
module: cs_affinitygroup
short_description: Manages affinity groups on Apache CloudStack based clouds.
description:
    - Create and remove affinity groups.
version_added: '2.0'
author: "René Moser (@resmo)"
options:
  name:
    description:
      - Name of the affinity group.
    required: true
  affinty_type:
    description:
      - Type of the affinity group. If not specified, first found affinity type is used.
    required: false
    default: null
  description:
    description:
      - Description of the affinity group.
    required: false
    default: null
  state:
    description:
      - State of the affinity group.
    required: false
    default: 'present'
    choices: [ 'present', 'absent' ]
  domain:
    description:
      - Domain the affinity group is related to.
    required: false
    default: null
  account:
    description:
      - Account the affinity group is related to.
    required: false
    default: null
  poll_async:
    description:
      - Poll async jobs until job has finished.
    required: false
    default: true
extends_documentation_fragment: cloudstack
'''

EXAMPLES = '''
# Create a affinity group
- local_action:
    module: cs_affinitygroup
    name: haproxy
    affinty_type: host anti-affinity

# Remove a affinity group
- local_action:
    module: cs_affinitygroup
    name: haproxy
    state: absent
'''

RETURN = '''
---
id:
  description: UUID of the affinity group.
  returned: success
  type: string
  sample: 87b1e0ce-4e01-11e4-bb66-0050569e64b8
name:
  description: Name of affinity group.
  returned: success
  type: string
  sample: app
description:
  description: Description of affinity group.
  returned: success
  type: string
  sample: application affinity group
affinity_type:
  description: Type of affinity group.
  returned: success
  type: string
  sample: host anti-affinity
'''

try:
    from cs import CloudStack, CloudStackException, read_config
    has_lib_cs = True
except ImportError:
    has_lib_cs = False

# import cloudstack common
from ansible.module_utils.cloudstack import *


class AnsibleCloudStackAffinityGroup(AnsibleCloudStack):

    def __init__(self, module):
        super(AnsibleCloudStackAffinityGroup, self).__init__(module)
        self.returns = {
            'type': 'affinity_type',
        }
        self.affinity_group = None


    def get_affinity_group(self):
        if not self.affinity_group:
            affinity_group = self.module.params.get('name')

            args                = {}
            args['account']     = self.get_account('name')
            args['domainid']    = self.get_domain('id')

            affinity_groups = self.cs.listAffinityGroups(**args)
            if affinity_groups:
                for a in affinity_groups['affinitygroup']:
                    if affinity_group in [ a['name'], a['id'] ]:
                        self.affinity_group = a
                        break
        return self.affinity_group


    def get_affinity_type(self):
        affinity_type = self.module.params.get('affinty_type')

        affinity_types = self.cs.listAffinityGroupTypes()
        if affinity_types:
            if not affinity_type:
                return affinity_types['affinityGroupType'][0]['type']

            for a in affinity_types['affinityGroupType']:
                if a['type'] == affinity_type:
                    return a['type']
        self.module.fail_json(msg="affinity group type '%s' not found" % affinity_type)


    def create_affinity_group(self):
        affinity_group = self.get_affinity_group()
        if not affinity_group:
            self.result['changed'] = True

            args                = {}
            args['name']        = self.module.params.get('name')
            args['type']        = self.get_affinity_type()
            args['description'] = self.module.params.get('description')
            args['account']     = self.get_account('name')
            args['domainid']    = self.get_domain('id')

            if not self.module.check_mode:
                res = self.cs.createAffinityGroup(**args)

                if 'errortext' in res:
                    self.module.fail_json(msg="Failed: '%s'" % res['errortext'])

                poll_async = self.module.params.get('poll_async')
                if res and poll_async:
                    affinity_group = self._poll_job(res, 'affinitygroup')
        return affinity_group


    def remove_affinity_group(self):
        affinity_group = self.get_affinity_group()
        if affinity_group:
            self.result['changed'] = True

            args                = {}
            args['name']        = self.module.params.get('name')
            args['account']     = self.get_account('name')
            args['domainid']    = self.get_domain('id')

            if not self.module.check_mode:
                res = self.cs.deleteAffinityGroup(**args)

                if 'errortext' in res:
                    self.module.fail_json(msg="Failed: '%s'" % res['errortext'])

                poll_async = self.module.params.get('poll_async')
                if res and poll_async:
                    res = self._poll_job(res, 'affinitygroup')
        return affinity_group


def main():
    module = AnsibleModule(
        argument_spec = dict(
            name = dict(required=True),
            affinty_type = dict(default=None),
            description = dict(default=None),
            state = dict(choices=['present', 'absent'], default='present'),
            domain = dict(default=None),
            account = dict(default=None),
            poll_async = dict(choices=BOOLEANS, default=True),
            api_key = dict(default=None),
            api_secret = dict(default=None, no_log=True),
            api_url = dict(default=None),
            api_http_method = dict(choices=['get', 'post'], default='get'),
            api_timeout = dict(type='int', default=10),
            api_region = dict(default='cloudstack'),
        ),
        required_together = (
            ['api_key', 'api_secret', 'api_url'],
        ),
        supports_check_mode=True
    )

    if not has_lib_cs:
        module.fail_json(msg="python library cs required: pip install cs")

    try:
        acs_ag = AnsibleCloudStackAffinityGroup(module)

        state = module.params.get('state')
        if state in ['absent']:
            affinity_group = acs_ag.remove_affinity_group()
        else:
            affinity_group = acs_ag.create_affinity_group()

        result = acs_ag.get_result(affinity_group)

    except CloudStackException, e:
        module.fail_json(msg='CloudStackException: %s' % str(e))

    module.exit_json(**result)

# import module snippets
from ansible.module_utils.basic import *
if __name__ == '__main__':
    main()
