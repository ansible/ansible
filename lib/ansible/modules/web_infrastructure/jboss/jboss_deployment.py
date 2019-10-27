#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2017, Ansible by Red Hat, inc
#
# This file is part of Ansible by Red Hat
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

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'metadata_version': '1.1'}

DOCUMENTATION = '''
---
module: jboss_deployment
short_description: Manage JBoss deployments
description:
    - Manages JBoss deployments through Management API, using local or remote artifacts and ensuring deployed content checksum matches source file checksum.
author:
  - Jairo Junior (@jairojunior)
version_added: 2.10
options:
    name:
      description: Name of deployment unit.
      required: true
      type: str
    state:
      description: Whether the deployment should be present or absent.
      required: false
      default: present
      choices: [present, absent]
      type: str
    src:
      description: Local or remote path of deployment file.
      required: false
      type: str
    server_group:
      description: Target server group. (Domain mode only)
      required: false
      type: str
extends_documentation_fragment: jboss
'''

EXAMPLES = '''
# Undeploy hawt.io
- jboss_deployment:
    name: hawtio.war
    state: absent
  environment:
    JBOSS_MANAGEMENT_USER: admin
    JBOSS_MANAGEMENT_PASSWORD: admin

# Deploy hawt.io (uploads src from local)
- jboss_deployment:
    username: admin
    password: admin
    name: hawtio.war
    src: /opt/hawtio-web-1.5.10.war
    state: present

# Update hawt.io (uploads src from local)
- jboss_deployment:
    username: admin
    password: admin
    name: hawtio.war
    src: /opt/hawtio-web-1.5.11.war
    state: present
'''

RETURN = '''
---
meta:
    description: Management API response
    returned: success
    type: dict
    sample: "{'outcome': 'success', 'response-headers': {'process-state': 'reload-required'}}"
'''

from ansible.module_utils.jboss.common import Client
from ansible.module_utils.jboss.common import OperationError
from ansible.module_utils.jboss.common import JBossAnsibleModule
from ansible.module_utils._text import to_native, to_text
from binascii import hexlify, a2b_base64


def read_deployment(client, name):
    exists, result = client.read('/deployment=' + name)

    # Example of content=[{"hash" => bytes { 0x1b, 0x85, 0x57, 0x73, 0x19, 0x13, 0xf7, 0x3a, 0xa2, 0x63,
    # 0x21, 0xaf, 0xdb, 0xbd, 0xc4, 0x83, 0x06, 0x7d, 0xa7, 0xa2 }}].
    # Convert content to string 1b8557731913f73aa26321afdbbdc483067da7a2
    if exists:
        bytes_value = result['content'][0]['hash']['BYTES_VALUE']
        result = to_text(hexlify(a2b_base64(bytes_value)))

    return exists, result


def present(module, client, name, exists, current_checksum):
    src = module.params['src']
    checksum_src = module.sha1(src)
    server_group = module.params['server_group']

    output = {}
    output.update(module_name=name)
    output.update(checksum_src=checksum_src)
    output.update(current_checksum=current_checksum)
    output.update(url_management=client.url)
    output.update(check_mode=module.check_mode)
    output.update(server_group=server_group)

    if exists:
        if current_checksum == checksum_src:
            module.exit_json(changed=False,
                             meta=output,
                             msg='Deployment {0} exists with {1}'.format(name, current_checksum))

        if not module.check_mode:
            output.update(client.update_deploy(name, src, server_group))
            module.exit_json(changed=True,
                             meta=output,
                             msg='Update deployment {0} content with {1}. Previous content checksum {2}'.format(name,
                                                                                                                checksum_src,
                                                                                                                current_checksum))

        module.exit_json(changed=True,
                         meta=output,
                         diff=dict(before=current_checksum, after=checksum_src))

    if not module.check_mode:
        output.update(client.deploy(name, src, server_group))
        module.exit_json(changed=True, meta=output, msg='Deployed {0}'.format(name))

    module.exit_json(changed=True, meta=output, diff=dict(before='', after=checksum_src))


def absent(module, client, name, exists):
    server_group = module.params['server_group']

    output = {}
    output.update(module_name=name)
    output.update(url_management=client.url)
    output.update(check_mode=module.check_mode)
    output.update(server_group=server_group)

    if exists:
        if not module.check_mode:
            output.update(client.undeploy(name, server_group))
            module.exit_json(changed=True,
                             meta=output,
                             msg='Undeployed {0}'.format(name))

        module.exit_json(changed=True,
                         meta=output,
                         msg='Deployment exists')

    module.exit_json(changed=False,
                     meta=output,
                     msg='Deployment {0} is absent'.format(name))


def main():
    module = JBossAnsibleModule(
        argument_spec=dict(
            name=dict(required=True, type='str'),
            state=dict(choices=['present', 'absent'], default='present', type='str'),
            src=dict(required=False, type='str'),
            server_group=dict(required=False, type='str'),
        ),
        required_if=[
            ('state', 'present', ['src']),
        ],
        supports_check_mode=True
    )

    client = Client.from_config(module.params)

    try:
        name = module.params['name']
        state = module.params['state']

        exists, current_checksum = read_deployment(client, name)

        if state == 'present':
            present(module, client, name, exists, current_checksum)
        else:
            absent(module, client, name, exists)
    except OperationError as err:
        module.fail_json(msg=to_native(err))


if __name__ == '__main__':
    main()
