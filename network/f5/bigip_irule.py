#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2016 F5 Networks Inc.
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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

DOCUMENTATION = '''
---
module: bigip_irule
short_description: Manage iRules across different modules on a BIG-IP.
description:
  - Manage iRules across different modules on a BIG-IP.
version_added: "2.2"
options:
  content:
    description:
      - When used instead of 'src', sets the contents of an iRule directly to
        the specified value. This is for simple values, but can be used with
        lookup plugins for anything complex or with formatting. Either one
        of C(src) or C(content) must be provided.
  module:
    description:
      - The BIG-IP module to add the iRule to.
    required: true
    choices:
      - ltm
      - gtm
  partition:
    description:
      - The partition to create the iRule on.
    required: false
    default: Common
  name:
    description:
      - The name of the iRule.
    required: true
  src:
    description:
      - The iRule file to interpret and upload to the BIG-IP. Either one
        of C(src) or C(content) must be provided.
    required: true
  state:
    description:
      - Whether the iRule should exist or not.
    required: false
    default: present
    choices:
      - present
      - absent
notes:
  - Requires the f5-sdk Python package on the host. This is as easy as
    pip install f5-sdk.
extends_documentation_fragment: f5
requirements:
  - f5-sdk
author:
  - Tim Rupp (@caphrim007)
'''

EXAMPLES = '''
- name: Add the iRule contained in templated irule.tcl to the LTM module
  bigip_irule:
      content: "{{ lookup('template', 'irule-template.tcl') }}"
      module: "ltm"
      name: "MyiRule"
      password: "secret"
      server: "lb.mydomain.com"
      state: "present"
      user: "admin"
  delegate_to: localhost

- name: Add the iRule contained in static file irule.tcl to the LTM module
  bigip_irule:
      module: "ltm"
      name: "MyiRule"
      password: "secret"
      server: "lb.mydomain.com"
      src: "irule-static.tcl"
      state: "present"
      user: "admin"
  delegate_to: localhost
'''

RETURN = '''
module:
    description: The module that the iRule was added to
    returned: changed and success
    type: string
    sample: "gtm"
src:
    description: The filename that included the iRule source
    returned: changed and success, when provided
    type: string
    sample: "/opt/src/irules/example1.tcl"
name:
    description: The name of the iRule that was managed
    returned: changed and success
    type: string
    sample: "my-irule"
content:
    description: The content of the iRule that was managed
    returned: changed and success
    type: string
    sample: "when LB_FAILED { set wipHost [LB::server addr] }"
partition:
    description: The partition in which the iRule was managed
    returned: changed and success
    type: string
    sample: "Common"
'''

try:
    from f5.bigip import ManagementRoot
    from icontrol.session import iControlUnexpectedHTTPError
    HAS_F5SDK = True
except ImportError:
    HAS_F5SDK = False

MODULES = ['gtm', 'ltm']


class BigIpiRule(object):
    def __init__(self, *args, **kwargs):
        if not HAS_F5SDK:
            raise F5ModuleError("The python f5-sdk module is required")

        if kwargs['state'] != 'absent':
            if not kwargs['content'] and not kwargs['src']:
                raise F5ModuleError(
                    "Either 'content' or 'src' must be provided"
                )

        source = kwargs['src']
        if source:
            with open(source) as f:
                kwargs['content'] = f.read()

        # The params that change in the module
        self.cparams = dict()

        # Stores the params that are sent to the module
        self.params = kwargs
        self.api = ManagementRoot(kwargs['server'],
                                  kwargs['user'],
                                  kwargs['password'],
                                  port=kwargs['server_port'])

    def flush(self):
        result = dict()
        state = self.params['state']

        try:
            if state == "present":
                changed = self.present()
            elif state == "absent":
                changed = self.absent()
        except iControlUnexpectedHTTPError as e:
            raise F5ModuleError(str(e))

        result.update(**self.cparams)
        result.update(dict(changed=changed))
        return result

    def read(self):
        """Read information and transform it

        The values that are returned by BIG-IP in the f5-sdk can have encoding
        attached to them as well as be completely missing in some cases.

        Therefore, this method will transform the data from the BIG-IP into a
        format that is more easily consumable by the rest of the class and the
        parameters that are supported by the module.
        """
        p = dict()
        name = self.params['name']
        partition = self.params['partition']
        module = self.params['module']

        if module == 'ltm':
            r = self.api.tm.ltm.rules.rule.load(
                name=name,
                partition=partition
            )
        elif module == 'gtm':
            r = self.api.tm.gtm.rules.rule.load(
                name=name,
                partition=partition
            )

        if hasattr(r, 'apiAnonymous'):
            p['content'] = str(r.apiAnonymous.strip())
        p['name'] = name
        return p

    def delete(self):
        params = dict()
        check_mode = self.params['check_mode']
        module = self.params['module']

        params['name'] = self.params['name']
        params['partition'] = self.params['partition']

        self.cparams = camel_dict_to_snake_dict(params)
        if check_mode:
            return True

        if module == 'ltm':
            r = self.api.tm.ltm.rules.rule.load(**params)
            r.delete()
        elif module == 'gtm':
            r = self.api.tm.gtm.rules.rule.load(**params)
            r.delete()

        if self.exists():
            raise F5ModuleError("Failed to delete the iRule")
        return True

    def exists(self):
        name = self.params['name']
        partition = self.params['partition']
        module = self.params['module']

        if module == 'ltm':
            return self.api.tm.ltm.rules.rule.exists(
                name=name,
                partition=partition
            )
        elif module == 'gtm':
            return self.api.tm.gtm.rules.rule.exists(
                name=name,
                partition=partition
            )

    def present(self):
        if self.exists():
            return self.update()
        else:
            return self.create()

    def update(self):
        params = dict()
        current = self.read()
        changed = False

        check_mode = self.params['check_mode']
        content = self.params['content']
        name = self.params['name']
        partition = self.params['partition']
        module = self.params['module']

        if content is not None:
            content = content.strip()
            if 'content' in current:
                if content != current['content']:
                    params['apiAnonymous'] = content
            else:
                params['apiAnonymous'] = content

        if params:
            changed = True
            params['name'] = name
            params['partition'] = partition
            self.cparams = camel_dict_to_snake_dict(params)
            if 'api_anonymous' in self.cparams:
                self.cparams['content'] = self.cparams.pop('api_anonymous')
            if self.params['src']:
                self.cparams['src'] = self.params['src']

            if check_mode:
                return changed
        else:
            return changed

        if module == 'ltm':
            d = self.api.tm.ltm.rules.rule.load(
                name=name,
                partition=partition
            )
            d.update(**params)
            d.refresh()
        elif module == 'gtm':
            d = self.api.tm.gtm.rules.rule.load(
                name=name,
                partition=partition
            )
            d.update(**params)
            d.refresh()

        return True

    def create(self):
        params = dict()

        check_mode = self.params['check_mode']
        content = self.params['content']
        name = self.params['name']
        partition = self.params['partition']
        module = self.params['module']

        if check_mode:
            return True

        if content is not None:
            params['apiAnonymous'] = content.strip()

        params['name'] = name
        params['partition'] = partition

        self.cparams = camel_dict_to_snake_dict(params)
        if 'api_anonymous' in self.cparams:
            self.cparams['content'] = self.cparams.pop('api_anonymous')
        if self.params['src']:
            self.cparams['src'] = self.params['src']

        if check_mode:
            return True

        if module == 'ltm':
            d = self.api.tm.ltm.rules.rule
            d.create(**params)
        elif module == 'gtm':
            d = self.api.tm.gtm.rules.rule
            d.create(**params)

        if not self.exists():
            raise F5ModuleError("Failed to create the iRule")
        return True

    def absent(self):
        changed = False

        if self.exists():
            changed = self.delete()

        return changed


def main():
    argument_spec = f5_argument_spec()

    meta_args = dict(
        content=dict(required=False, default=None),
        src=dict(required=False, default=None),
        name=dict(required=True),
        module=dict(required=True, choices=MODULES)
    )
    argument_spec.update(meta_args)

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        mutually_exclusive=[
            ['content', 'src']
        ]
    )

    try:
        obj = BigIpiRule(check_mode=module.check_mode, **module.params)
        result = obj.flush()

        module.exit_json(**result)
    except F5ModuleError as e:
        module.fail_json(msg=str(e))

from ansible.module_utils.basic import *
from ansible.module_utils.ec2 import camel_dict_to_snake_dict
from ansible.module_utils.f5 import *

if __name__ == '__main__':
    main()
