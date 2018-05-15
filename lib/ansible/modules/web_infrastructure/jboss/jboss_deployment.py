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
author: "Jairo Junior (@jairojunior)"
version_added: 2.6
options:
    name:
      description: Name of deployment unit.
      required: true
    state:
      description: Whether the deployment should be present or absent.
      required: false
      default: present
      choices: [present, absent]
    src:
      description: Local or remote path of deployment file.
      required: false
    server_group:
      description: Target server group. (Domain mode only)
      required: false
extends_documentation_fragment: jboss
'''

EXAMPLES = '''
# Undeploy hawt.io
- jboss_deployment:
    name: hawtio.war
    state: absent

# Deploy hawt.io (uploads src from local)
- jboss_deployment:
    name: hawtio.war
    src: /opt/hawtio.war
    state: present

# Deploy app.jar (already present in remote host)
- jboss_deployment:
    name: app.jar
    state: present
    src: /tmp/app.jar
'''

RETURN = '''
---
meta:
    description: Management API response
    returned: success
    type: dict
    sample: "{'outcome': 'success', 'response-headers': {'process-state': 'reload-required'}}"
'''


try:
    from jboss.client import Client
    from jboss.exceptions import AuthError
    from jboss.exceptions import OperationError
    HAS_JBOSS_PY = True
except ImportError:
    HAS_JBOSS_PY = False

from ansible.module_utils.jboss import JBossAnsibleModule


def read_deployment(client, name):
    exists, result = client.read('/deployment=' + name)

    if exists:
        bytes_value = result['content'][0]['hash']['BYTES_VALUE']
        result = bytes_value.decode('base64').encode('hex')

    return exists, result


def present(module, client, name, exists, current_checksum):
    src = module.params['src']
    checksum_src = module.sha1(src)
    server_group = module.params['server_group']

    if exists:
        if current_checksum == checksum_src:
            module.exit_json(changed=False,
                             meta='Deployment {0} exists with {1}'.format(name, current_checksum))

        if not module.check_mode:
            module.exit_json(changed=True,
                             meta=client.update_deploy(name, src, server_group),
                             msg='Update deployment {0} content with {1}. Previous content checksum {2}'.format(name, checksum_src, current_checksum))

        module.exit_json(changed=True, diff=dict(before=current_checksum, after=checksum_src))

    if not module.check_mode:
        module.exit_json(changed=True,
                         meta=client.deploy(name, src, server_group),
                         msg='Deployed {0}'.format(name))

    module.exit_json(changed=True, diff=dict(before='', after=checksum_src))


def absent(module, client, name, exists):
    server_group = module.params['server_group']

    if exists:
        if not module.check_mode:
            module.exit_json(changed=True,
                             meta=client.undeploy(name, server_group),
                             msg='Undeployed {0}'.format(name))

        module.exit_json(changed=True, msg='Deployment exists')

    module.exit_json(changed=False, msg='Deployment {0} is absent'.format(name))


def main():
    module = JBossAnsibleModule(
        argument_spec=dict(
            name=dict(required=True, type='str'),
            state=dict(choices=['present', 'absent'], default='present'),
            src=dict(required=False, type='str'),
            server_group=dict(required=False, type='str'),
        ),
        supports_check_mode=True
    )

    if not HAS_JBOSS_PY:
        module.fail_json(msg='jboss-py required for this module')

    client = Client.from_config(module.params)

    try:
        name = module.params['name']
        state = module.params['state']

        exists, current_checksum = read_deployment(client, name)

        if state == 'present':
            present(module, client, name, exists, current_checksum)
        else:
            absent(module, client, name, exists)
    except (AuthError, OperationError) as err:
        module.fail_json(msg=str(err))


if __name__ == '__main__':
    main()
