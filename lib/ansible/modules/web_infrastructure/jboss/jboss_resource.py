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
module: jboss_resource
short_description: Manage JBoss configuration (datasources, queues, https, etc)
description:
    - Manages JBoss configuration/resources (i.e. Management Model) through Management API.
    - Locally or remote, ensuring resource state matches specified attributes.
author: "Jairo Junior (@jairojunior)"
version_added: 2.6
options:
    name:
      description: Name of the configuration resource using JBoss-CLI path expression.
      required: true
      aliases: [path]
    state:
      description: Whether the resource should be present or absent.
      required: false
      default: present
      choices: [present, absent]
    attributes:
      description: Attributes defining the state of configuration resource.
      required: false
extends_documentation_fragment: jboss
'''

EXAMPLES = '''
# Configure a datasource
- jboss_resource:
    name: "/subsystem=datasources/data-source=DemoDS"
    state: present
    attributes:
    driver-name: h2
    connection-url: "jdbc:h2:mem:demo;DB_CLOSE_DELAY=-1;DB_CLOSE_ON_EXIT=FALSE"
    jndi-name: "java:jboss/datasources/DemoDS"
    user-name: sa
    password: sa
    min-pool-size: 20
    max-pool-size: 40

# TLSRealm
- jboss_resource:
    name: "/core-service=management/security-realm=TLSRealm"

# Server identity
- jboss_resource:
    name: "/core-service=management/security-realm=TLSRealm/server-identity=ssl"
    attributes:
    keystore-path: jboss.jks
    keystore-relative-to: /etc/pki/java
    keystore-password: changeit
    alias: demo
    key-password: changeit

# HTTPS Listener
- jboss_resource:
    name: "/subsystem=undertow/server=default-server/https-listener=https"
    attributes:
    socket-binding: https
    security-realm: TLSRealm
    enabled: true
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


def diff(current, desired):
    attributes_diff = {}

    for key, value in desired.items():
        if not current[key] == value:
            attributes_diff[key] = value

    return attributes_diff


def present(module, client, path, desired_attributes, exists, current_attributes):
    if exists:
        changed_attributes = diff(current_attributes, desired_attributes)

        if not changed_attributes:
            module.exit_json(changed=False,
                             msg='{0} exists with {1}'.format(path, current_attributes))

        if not module.check_mode:
            module.exit_json(changed=True,
                             msg='Updated {0} of {1}'.format(changed_attributes, path),
                             meta=client.update(path, changed_attributes))

        module.exit_json(changed=True,
                         diff=dict(before=current_attributes, after=desired_attributes))

    if not module.check_mode:
        module.exit_json(changed=True,
                         meta=client.add(path, desired_attributes),
                         msg='Added {0} with {1}'.format(path, desired_attributes))

    module.exit_json(changed=True,
                     diff=dict(before=current_attributes, after=desired_attributes))


def absent(module, client, path, exists):
    if exists:
        if not module.check_mode:
            module.exit_json(changed=True,
                             msg='Removed ' + path,
                             meta=client.remove(path))

        module.exit_json(changed=True, msg='Resouce exists')

    module.exit_json(changed=False, msg=path + ' is absent')


def main():
    module = JBossAnsibleModule(
        argument_spec=dict(
            name=dict(aliases=['path'], required=True, type='str'),
            state=dict(choices=['present', 'absent'], default='present'),
            attributes=dict(required=False, type='dict', default=dict()),
        ),
        supports_check_mode=True
    )

    if not HAS_JBOSS_PY:
        module.fail_json(msg='jboss-py required for this module')

    client = Client.from_config(module.params)

    try:
        path = module.params['name']
        attributes = module.params['attributes']
        state = module.params['state']

        exists, current_attributes = client.read(path)

        if state == 'present':
            present(module, client, path, attributes, exists, current_attributes)
        else:
            absent(module, client, path, exists)
    except (AuthError, OperationError) as err:
        module.fail_json(msg=str(err))


if __name__ == '__main__':
    main()
