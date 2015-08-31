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
module: cs_securitygroup
short_description: Manages security groups on Apache CloudStack based clouds.
description:
    - Create and remove security groups.
version_added: '2.0'
author: "René Moser (@resmo)"
options:
  name:
    description:
      - Name of the security group.
    required: true
  description:
    description:
      - Description of the security group.
    required: false
    default: null
  state:
    description:
      - State of the security group.
    required: false
    default: 'present'
    choices: [ 'present', 'absent' ]
  project:
    description:
      - Name of the project the security group to be created in.
    required: false
    default: null
extends_documentation_fragment: cloudstack
'''

EXAMPLES = '''
# Create a security group
- local_action:
    module: cs_securitygroup
    name: default
    description: default security group

# Remove a security group
- local_action:
    module: cs_securitygroup
    name: default
    state: absent
'''

RETURN = '''
---
id:
  description: UUID of the security group.
  returned: success
  type: string
  sample: a6f7a5fc-43f8-11e5-a151-feff819cdc9f
name:
  description: Name of security group.
  returned: success
  type: string
  sample: app
description:
  description: Description of security group.
  returned: success
  type: string
  sample: application security group
'''

try:
    from cs import CloudStack, CloudStackException, read_config
    has_lib_cs = True
except ImportError:
    has_lib_cs = False

# import cloudstack common
from ansible.module_utils.cloudstack import *


class AnsibleCloudStackSecurityGroup(AnsibleCloudStack):

    def __init__(self, module):
        super(AnsibleCloudStackSecurityGroup, self).__init__(module)
        self.security_group = None


    def get_security_group(self):
        if not self.security_group:
            sg_name = self.module.params.get('name')
            args = {}
            args['projectid'] = self.get_project('id')
            sgs = self.cs.listSecurityGroups(**args)
            if sgs:
                for s in sgs['securitygroup']:
                    if s['name'] == sg_name:
                        self.security_group = s
                        break
        return self.security_group


    def create_security_group(self):
        security_group = self.get_security_group()
        if not security_group:
            self.result['changed'] = True

            args = {}
            args['name'] = self.module.params.get('name')
            args['projectid'] = self.get_project('id')
            args['description'] = self.module.params.get('description')

            if not self.module.check_mode:
                res = self.cs.createSecurityGroup(**args)
                if 'errortext' in res:
                    self.module.fail_json(msg="Failed: '%s'" % res['errortext'])
                security_group = res['securitygroup']

        return security_group


    def remove_security_group(self):
        security_group = self.get_security_group()
        if security_group:
            self.result['changed'] = True

            args = {}
            args['name'] = self.module.params.get('name')
            args['projectid'] = self.get_project('id')

            if not self.module.check_mode:
                res = self.cs.deleteSecurityGroup(**args)
                if 'errortext' in res:
                    self.module.fail_json(msg="Failed: '%s'" % res['errortext'])

        return security_group



def main():
    module = AnsibleModule(
        argument_spec = dict(
            name = dict(required=True),
            description = dict(default=None),
            state = dict(choices=['present', 'absent'], default='present'),
            project = dict(default=None),
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
        acs_sg = AnsibleCloudStackSecurityGroup(module)

        state = module.params.get('state')
        if state in ['absent']:
            sg = acs_sg.remove_security_group()
        else:
            sg = acs_sg.create_security_group()

        result = acs_sg.get_result(sg)

    except CloudStackException, e:
        module.fail_json(msg='CloudStackException: %s' % str(e))

    module.exit_json(**result)

# import module snippets
from ansible.module_utils.basic import *
if __name__ == '__main__':
    main()
