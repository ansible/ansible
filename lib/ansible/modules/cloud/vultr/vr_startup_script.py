#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2018, René Moser <mail@renemoser.net>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: vr_startup_script
short_description: Manages startup scripts on Vultr.
description:
  - Create, update and remove startup scripts.
version_added: "2.5"
author: "René Moser (@resmo)"
options:
  name:
    description:
      - The script name.
    required: true
  script_type:
    description:
      - The script type, can not be changed once created.
    default: boot
    choices: [ boot, pxe ]
    aliases: [ type ]
  script:
    description:
      - The script source code.
      - Required if (state=present).
  state:
    description:
      - State of the script.
    default: present
    choices: [ present, absent ]
extends_documentation_fragment: vultr
'''

EXAMPLES = r'''
- name: ensure a pxe script exists, source from a file
  local_action:
    module: vr_startup_script
    name: my_web_script
    script_type: pxe
    script: "{{ lookup('file', 'path/to/script') }}"

- name: ensure a boot script exists
  local_action:
    module: vr_startup_script
    name: vr_startup_script
    script: "#!/bin/bash\necho Hello World > /root/hello"

- name: ensure a script is absent
  local_action:
    module: vr_startup_script
    name: my_web_script
    state: absent
'''

RETURN = r'''
---
vultr_api:
  description: Response from Vultr API with a few additions/modification
  returned: success
  type: complex
  contains:
    api_account:
      description: Account used in the ini file to select the key
      returned: success
      type: string
      sample: default
    api_timeout:
      description: Timeout used for the API requests
      returned: success
      type: int
      sample: 60
    api_retries:
      description: Amount of max retries for the API requests
      returned: success
      type: int
      sample: 5
    api_endpoint:
      description: Endpoint used for the API requests
      returned: success
      type: string
      sample: "https://api.vultr.com"
vultr_startup_script:
  description: Response from Vultr API
  returned: success
  type: complex
  contains:
    id:
      description: ID of the startup script.
      returned: success
      type: string
      sample: 249395
    name:
      description: Name of the startup script.
      returned: success
      type: string
      sample: my startup script
    script:
      description: The source code of the startup script.
      returned: success
      type: string
      sample: "#!/bin/bash\necho Hello World > /root/hello"
    script_type:
      description: The type of the startup script.
      returned: success
      type: string
      sample: pxe
    date_created:
      description: Date the startup script was created.
      returned: success
      type: string
      sample: "2017-08-26 12:47:48"
    date_modified:
      description: Date the startup script was modified.
      returned: success
      type: string
      sample: "2017-08-26 12:47:48"
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.vultr import (
    Vultr,
    vultr_argument_spec,
)


class AnsibleVultrStartupScript(Vultr):

    def __init__(self, module):
        super(AnsibleVultrStartupScript, self).__init__(module, "vultr_startup_script")

        self.returns = {
            'SCRIPTID': dict(key='id'),
            'type': dict(key='script_type'),
            'name': dict(key='name'),
            'script': dict(),
            'date_created': dict(),
            'date_modified': dict(),
        }

    def get_script(self):
        scripts = self.api_query(path="/v1/startupscript/list")
        name = self.module.params.get('name')
        if scripts:
            for script_id, script_data in scripts.items():
                if script_data.get('name') == name:
                    return script_data
        return {}

    def present_script(self):
        script = self.get_script()
        if not script:
            script = self._create_script(script)
        else:
            script = self._update_script(script)
        return script

    def _create_script(self, script):
        self.result['changed'] = True

        data = {
            'name': self.module.params.get('name'),
            'script': self.module.params.get('script'),
            'type': self.module.params.get('script_type'),
        }

        self.result['diff']['before'] = {}
        self.result['diff']['after'] = data

        if not self.module.check_mode:
            self.api_query(
                path="/v1/startupscript/create",
                method="POST",
                data=data
            )
            script = self.get_script()
        return script

    def _update_script(self, script):
        if script['script'] != self.module.params.get('script'):
            self.result['changed'] = True

            data = {
                'SCRIPTID': script['SCRIPTID'],
                'script': self.module.params.get('script'),
            }

            self.result['diff']['before'] = script
            self.result['diff']['after'] = script.copy()
            self.result['diff']['after'].update(data)

            if not self.module.check_mode:
                self.api_query(
                    path="/v1/startupscript/update",
                    method="POST",
                    data=data
                )
                script = self.get_script()
        return script

    def absent_script(self):
        script = self.get_script()
        if script:
            self.result['changed'] = True

            data = {
                'SCRIPTID': script['SCRIPTID'],
            }

            self.result['diff']['before'] = script
            self.result['diff']['after'] = {}

            if not self.module.check_mode:
                self.api_query(
                    path="/v1/startupscript/destroy",
                    method="POST",
                    data=data
                )
        return script


def main():
    argument_spec = vultr_argument_spec()
    argument_spec.update(dict(
        name=dict(required=True),
        script=dict(),
        script_type=dict(default='boot', choices=['boot', 'pxe'], aliases=['type']),
        state=dict(choices=['present', 'absent'], default='present'),
    ))

    module = AnsibleModule(
        argument_spec=argument_spec,
        required_if=[
            ('state', 'present', ['script']),
        ],
        supports_check_mode=True,
    )

    vr_script = AnsibleVultrStartupScript(module)
    if module.params.get('state') == "absent":
        script = vr_script.absent_script()
    else:
        script = vr_script.present_script()

    result = vr_script.get_result(script)
    module.exit_json(**result)


if __name__ == '__main__':
    main()
