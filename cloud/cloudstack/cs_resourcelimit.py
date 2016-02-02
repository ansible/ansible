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

DOCUMENTATION = '''
---
module: cs_resourcelimit
short_description: Manages resource limits on Apache CloudStack based clouds.
description:
    - Manage limits of resources for domains, accounts and projects.
version_added: "2.1"
author: "René Moser (@resmo)"
options:
  resource_type:
    description:
      - Type of the resource.
    required: true
    choices:
      - instance
      - ip_address
      - volume
      - snapshot
      - template
      - network
      - vpc
      - cpu
      - memory
      - primary_storage
      - secondary_storage
    aliases: [ 'type' ]
  limit:
    description:
      - Maximum number of the resource.
      - Default is unlimited C(-1).
    required: false
    default: -1
    aliases: [ 'max' ]
  domain:
    description:
      - Domain the resource is related to.
    required: false
    default: null
  account:
    description:
      - Account the resource is related to.
    required: false
    default: null
  project:
    description:
      - Name of the project the resource is related to.
    required: false
    default: null
extends_documentation_fragment: cloudstack
'''

EXAMPLES = '''
# Update a resource limit for instances of a domain
local_action:
  module: cs_resourcelimit
  type: instance
  limit: 10
  domain: customers

# Update a resource limit for instances of an account
local_action:
  module: cs_resourcelimit
  type: instance
  limit: 12
  account: moserre
  domain: customers
'''

RETURN = '''
---
recource_type:
  description: Type of the resource
  returned: success
  type: string
  sample: instance
limit:
  description: Maximum number of the resource.
  returned: success
  type: int
  sample: -1
domain:
  description: Domain the resource is related to.
  returned: success
  type: string
  sample: example domain
account:
  description: Account the resource is related to.
  returned: success
  type: string
  sample: example account
project:
  description: Project the resource is related to.
  returned: success
  type: string
  sample: example project
'''

try:
    from cs import CloudStack, CloudStackException, read_config
    has_lib_cs = True
except ImportError:
    has_lib_cs = False

# import cloudstack common
from ansible.module_utils.cloudstack import *

RESOURCE_TYPES = {
    'instance':             0,
    'ip_address':           1,
    'volume':               2,
    'snapshot':             3,
    'template':             4,
    'network':              6,
    'vpc':                  7,
    'cpu':                  8,
    'memory':               9,
    'primary_storage':      10,
    'secondary_storage':    11,
}

class AnsibleCloudStackResourceLimit(AnsibleCloudStack):

    def __init__(self, module):
        super(AnsibleCloudStackResourceLimit, self).__init__(module)
        self.returns = {
            'max': 'limit',
        }


    def get_resource_type(self):
        resource_type = self.module.params.get('resource_type')
        return RESOURCE_TYPES.get(resource_type)


    def get_resource_limit(self):
        args                 = {}
        args['account']      = self.get_account(key='name')
        args['domainid']     = self.get_domain(key='id')
        args['projectid']    = self.get_project(key='id')
        args['resourcetype'] = self.get_resource_type()
        resource_limit = self.cs.listResourceLimits(**args)
        if resource_limit:
            return resource_limit['resourcelimit'][0]
        self.module.fail_json(msg="Resource limit type '%s' not found." % self.module.params.get('resource_type'))


    def update_resource_limit(self):
        resource_limit = self.get_resource_limit()

        args                 = {}
        args['account']      = self.get_account(key='name')
        args['domainid']     = self.get_domain(key='id')
        args['projectid']    = self.get_project(key='id')
        args['resourcetype'] = self.get_resource_type()
        args['max']          = self.module.params.get('limit', -1)

        if self.has_changed(args, resource_limit):
            self.result['changed'] = True
            if not self.module.check_mode:
                res = self.cs.updateResourceLimit(**args)
                if 'errortext' in res:
                    self.module.fail_json(msg="Failed: '%s'" % res['errortext'])
                resource_limit = res['resourcelimit']
        return resource_limit


    def get_result(self, resource_limit):
        self.result = super(AnsibleCloudStackResourceLimit, self).get_result(resource_limit)
        self.result['resource_type'] = self.module.params.get('resource_type')
        return self.result


def main():
    argument_spec = cs_argument_spec()
    argument_spec.update(dict(
        resource_type = dict(required=True, choices=RESOURCE_TYPES.keys(), aliases=['type']),
        limit = dict(default=-1, aliases=['max']),
        domain = dict(default=None),
        account = dict(default=None),
        project = dict(default=None),
    ))

    module = AnsibleModule(
        argument_spec=argument_spec,
        required_together=cs_required_together(),
        supports_check_mode=True
    )

    if not has_lib_cs:
        module.fail_json(msg="python library cs required: pip install cs")

    try:
        acs_resource_limit = AnsibleCloudStackResourceLimit(module)
        resource_limit = acs_resource_limit.update_resource_limit()
        result = acs_resource_limit.get_result(resource_limit)

    except CloudStackException as e:
        module.fail_json(msg='CloudStackException: %s' % str(e))

    module.exit_json(**result)

# import module snippets
from ansible.module_utils.basic import *
if __name__ == '__main__':
    main()
