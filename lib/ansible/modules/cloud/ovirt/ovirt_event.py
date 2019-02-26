#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright: (c) 2019, Ansible Project
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
module: ovirt_event
short_description: Create or delete an event in oVirt/RHV
author: "Chris Keller (@nasx)"
version_added: "2.8"
description:
    - "This module can be used to create or delete an event in oVirt/RHV."
options:
    state:
        description:
            - "Should the event be present/absent."
            - "The C(wait) option must be set to false when state is absent."
        choices: ['present', 'absent']
        type: str
        default: present

    description:
        description:
            - "Message for the event."
            - "Required when state is present."
         type: str

    severity:
        description:
            - "Severity of the event."
            - "Required when state is present."
        choices: ['error', 'normal', 'warning']
        default: normal

    origin:
        description:
            - "Originator of the event."
            - "Required when state is present."

    custom_id:
        description:
            - "Custom ID for the event. This ID must be unique for each event."
            - "Required when state is present."
        type: int

    id:
        description:
            - "The event ID in the oVirt/RHV audit_log table. This ID is not the same as custom_id and is only used when state is absent."
            - "Required when state is absent."

    cluster:
        description:
            - "The id of the cluster associated with this event."

    data_center:
        description:
            - "The id of the data center associated with this event."

    host:
        description:
            - "The id of the host associated with this event."

    storage_domain:
        description:
            - "The id of the storage domain associated with this event."

    template:
        description:
            - "The id of the template associated with this event."

    user:
        description:
            - "The id of the user associated with this event."

    vm:
        description:
            - "The id of the VM associated with this event."
extends_documentation_fragment: ovirt
'''

EXAMPLES = '''
# Examples don't contain the auth parameter for simplicity,
# look at the ovirt_auth module to see how to reuse authentication.

- name: Create an event
  ovirt_event:
- ovirt_event:
    state: present
    description: "The file system /home on host xyz is almost full!"
    origin: "mymonitor"
    custom_id: 123456789
    severity: warning

- name: Create an event and link it to a specific object
  ovirt_event:
- ovirt_event:
    state: present
    description: "The file system /home is almost full!"
    origin: "mymonitor"
    custom_id: 123456789
    severity: warning
    vm: "c79db183-46ef-44d1-95f9-1a368c516c19"

# Remove an event
- ovirt_event:
    state: absent
    id: 123456789
    wait: false
'''

RETURN = '''
id:
    description: "ID of the event that was created."
    returned: "On success."
    type: str
event:
    description: "Dictionary of all the Event attributes. All event attributes can be found at the following url:
                  http://ovirt.github.io/ovirt-engine-api-model/master/#types/event"
    returned: "On success."
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
    check_params,
    create_connection,
    equal,
    get_dict_of_struct,
    ovirt_full_argument_spec,
)


class EventsModule(BaseModule):

    def build_entity(self):
        return otypes.Event(
            description=self._module.params['description'],
            severity=otypes.LogSeverity(self._module.params['severity']),
            origin=self._module.params['origin'],
            custom_id=self._module.params['custom_id'],
            id=self._module.params['id'],
            cluster=otypes.Cluster(
                id=self._module.params['cluster']
            ) if self._module.params['cluster'] is not None else None,
            data_center=otypes.DataCenter(
                id=self._module.params['data_center']
            ) if self._module.params['data_center'] is not None else None,
            host=otypes.Host(
                id=self._module.params['host']
            ) if self._module.params['host'] is not None else None,
            storage_domain=otypes.StorageDomain(
                id=self._module.params['storage_domain']
            ) if self._module.params['storage_domain'] is not None else None,
            template=otypes.Template(
                id=self._module.params['template']
            ) if self._module.params['template'] is not None else None,
            user=otypes.User(
                id=self._module.params['user']
            ) if self._module.params['user'] is not None else None,
            vm=otypes.Vm(
                id=self._module.params['vm']
            ) if self._module.params['vm'] is not None else None,
        )


def main():
    argument_spec = ovirt_full_argument_spec(
        state=dict(
            choices=['present', 'absent'],
            default='present',
        ),
        description=dict(default=None),
        severity=dict(
            choices=['error', 'normal', 'warning'],
            default='normal',
        ),
        origin=dict(default=None),
        custom_id=dict(default=None, type='int'),
        id=dict(default=None),
        cluster=dict(default=None),
        data_center=dict(default=None),
        host=dict(default=None),
        storage_domain=dict(default=None),
        template=dict(default=None),
        user=dict(default=None),
        vm=dict(default=None),
    )
    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True
    )

    check_sdk(module)

    # Wait must be set to false if state == absent

    if module.params['state'] == 'absent' and module.params['wait'] is not False:
        module.fail_json(msg='When "state" is absent, "wait" must be set to false.')

    try:
        auth = module.params.pop('auth')
        connection = create_connection(auth)
        events_service = connection.system_service().events_service()
        events_module = EventsModule(
            connection=connection,
            module=module,
            service=events_service,
        )

        state = module.params['state']
        if state == 'present':
            ret = events_module.create()
        elif state == 'absent':
            ret = events_module.remove()

        module.exit_json(**ret)
    except Exception as e:
        module.fail_json(msg=str(e), exception=traceback.format_exc())
    finally:
        connection.close(logout=auth.get('token') is None)


if __name__ == "__main__":
    main()
