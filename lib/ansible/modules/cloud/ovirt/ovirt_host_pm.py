#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2016 Red Hat, Inc.
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
#

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: ovirt_host_pm
short_description: Module to manage power management of hosts in oVirt/RHV
version_added: "2.3"
author: "Ondra Machacek (@machacekondra)"
description:
    - "Module to manage power management of hosts in oVirt/RHV."
options:
    name:
        description:
            - "Name of the host to manage."
        required: true
        aliases: ['host']
    state:
        description:
            - "Should the host be present/absent."
        choices: ['present', 'absent']
        default: present
    address:
        description:
            - "Address of the power management interface."
    username:
        description:
            - "Username to be used to connect to power management interface."
    password:
        description:
            - "Password of the user specified in C(username) parameter."
    type:
        description:
            - "Type of the power management. oVirt/RHV predefined values are I(drac5), I(ipmilan), I(rsa),
               I(bladecenter), I(alom), I(apc), I(apc_snmp), I(eps), I(wti), I(rsb), I(cisco_ucs),
               I(drac7), I(hpblade), I(ilo), I(ilo2), I(ilo3), I(ilo4), I(ilo_ssh),
               but user can have defined custom type."
    port:
        description:
            - "Power management interface port."
    slot:
        description:
            - "Power management slot."
    options:
        description:
            - "Dictionary of additional fence agent options."
            - "Additional information about options can be found at U(https://fedorahosted.org/cluster/wiki/FenceArguments)."
    encrypt_options:
        description:
            - "If (true) options will be encrypted when send to agent."
        aliases: ['encrypt']
    order:
        description:
            - "Integer value specifying, by default it's added at the end."
        version_added: "2.5"
extends_documentation_fragment: ovirt
'''

EXAMPLES = '''
# Examples don't contain auth parameter for simplicity,
# look at ovirt_auth module to see how to reuse authentication:

# Add fence agent to host 'myhost'
- ovirt_host_pm:
    name: myhost
    address: 1.2.3.4
    options:
      myoption1: x
      myoption2: y
    username: admin
    password: admin
    port: 3333
    type: ipmilan

# Remove ipmilan fence agent with address 1.2.3.4 on host 'myhost'
- ovirt_host_pm:
    state: absent
    name: myhost
    address: 1.2.3.4
    type: ipmilan
'''

RETURN = '''
id:
    description: ID of the agent which is managed
    returned: On success if agent is found.
    type: str
    sample: 7de90f31-222c-436c-a1ca-7e655bd5b60c
agent:
    description: "Dictionary of all the agent attributes. Agent attributes can be found on your oVirt/RHV instance
                  at following url: http://ovirt.github.io/ovirt-engine-api-model/master/#types/agent."
    returned: On success if agent is found.
    type: dict
'''

import traceback

try:
    import ovirtsdk4.types as otypes
except ImportError:
    pass

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ovirt import (
    BaseModule,
    check_sdk,
    create_connection,
    equal,
    ovirt_full_argument_spec,
    search_by_name,
)


class HostModule(BaseModule):
    def build_entity(self):
        return otypes.Host(
            power_management=otypes.PowerManagement(
                enabled=True,
            ),
        )

    def update_check(self, entity):
        return equal(True, entity.power_management.enabled)


class HostPmModule(BaseModule):

    def build_entity(self):
        return otypes.Agent(
            address=self._module.params['address'],
            encrypt_options=self._module.params['encrypt_options'],
            options=[
                otypes.Option(
                    name=name,
                    value=value,
                ) for name, value in self._module.params['options'].items()
            ] if self._module.params['options'] else None,
            password=self._module.params['password'],
            port=self._module.params['port'],
            type=self._module.params['type'],
            username=self._module.params['username'],
            order=self._module.params.get('order', 100),
        )

    def update_check(self, entity):
        return (
            equal(self._module.params.get('address'), entity.address) and
            equal(self._module.params.get('encrypt_options'), entity.encrypt_options) and
            equal(self._module.params.get('password'), entity.password) and
            equal(self._module.params.get('username'), entity.username) and
            equal(self._module.params.get('port'), entity.port) and
            equal(self._module.params.get('type'), entity.type) and
            equal(self._module.params.get('order'), entity.order)
        )


def main():
    argument_spec = ovirt_full_argument_spec(
        state=dict(
            choices=['present', 'absent'],
            default='present',
        ),
        name=dict(default=None, required=True, aliases=['host']),
        address=dict(default=None),
        username=dict(default=None),
        password=dict(default=None, no_log=True),
        type=dict(default=None),
        port=dict(default=None, type='int'),
        order=dict(default=None, type='int'),
        slot=dict(default=None),
        options=dict(default=None, type='dict'),
        encrypt_options=dict(default=None, type='bool', aliases=['encrypt']),
    )
    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )
    check_sdk(module)

    try:
        auth = module.params.pop('auth')
        connection = create_connection(auth)
        hosts_service = connection.system_service().hosts_service()
        host = search_by_name(hosts_service, module.params['name'])
        fence_agents_service = hosts_service.host_service(host.id).fence_agents_service()

        host_pm_module = HostPmModule(
            connection=connection,
            module=module,
            service=fence_agents_service,
        )
        host_module = HostModule(
            connection=connection,
            module=module,
            service=hosts_service,
        )

        state = module.params['state']
        if state == 'present':
            agent = host_pm_module.search_entity(
                search_params={
                    'address': module.params['address'],
                    'type': module.params['type'],
                }
            )
            ret = host_pm_module.create(entity=agent)

            # Enable Power Management, if it's not enabled:
            host_module.create(entity=host)
        elif state == 'absent':
            agent = host_pm_module.search_entity(
                search_params={
                    'address': module.params['address'],
                    'type': module.params['type'],
                }
            )
            ret = host_pm_module.remove(entity=agent)

        module.exit_json(**ret)
    except Exception as e:
        module.fail_json(msg=str(e), exception=traceback.format_exc())
    finally:
        connection.close(logout=auth.get('token') is None)


if __name__ == "__main__":
    main()
