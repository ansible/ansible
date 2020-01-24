#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright: (c) 2019, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: ovirt_event_info
short_description: This module can be used to retrieve information about one or more oVirt/RHV events
author: "Chris Keller (@nasx)"
version_added: "2.8"
description:
    - "Retrieve information about one or more oVirt/RHV events."
    - This module was called C(ovirt_event_facts) before Ansible 2.9, returning C(ansible_facts).
      Note that the M(ovirt_event_info) module no longer returns C(ansible_facts)!
options:
    case_sensitive:
        description:
            - "Indicates if the search performed using the search parameter should be performed taking case
               into account. The default value is true, which means that case is taken into account. If you
               want to search ignoring case set it to false."
        required: false
        default: true
        type: bool

    from_:
        description:
            - "Indicates the event index after which events should be returned. The indexes of events are
               strictly increasing, so when this parameter is used only the events with greater indexes
               will be returned."
        required: false
        type: int

    max:
        description:
            - "Sets the maximum number of events to return. If not specified all the events are returned."
        required: false
        type: int

    search:
        description:
            - "Search term which is accepted by the oVirt/RHV API."
            - "For example to search for events of severity alert use the following pattern: severity=alert"
        required: false
        type: str

    headers:
        description:
            - "Additional HTTP headers."
        required: false
        type: str

    query:
        description:
            - "Additional URL query parameters."
        required: false
        type: str

    wait:
        description:
            - "If True wait for the response."
        required: false
        default: true
        type: bool
extends_documentation_fragment: ovirt_info
'''

EXAMPLES = '''
# Examples don't contain the auth parameter for simplicity,
# look at the ovirt_auth module to see how to reuse authentication.

- name: Return all events
  ovirt_event_info:
  register: result

- name: Return the last 10 events
  ovirt_event_info:
    max: 10
  register: result

- name: Return all events of type alert
  ovirt_event_info:
    search: "severity=alert"
  register: result
- debug:
    msg: "{{ result.ovirt_events }}"
'''

RETURN = '''
ovirt_events:
    description: "List of dictionaries describing the events. Event attributes are mapped to dictionary keys.
                  All event attributes can be found at the following url:
                  http://ovirt.github.io/ovirt-engine-api-model/master/#types/event"
    returned: On success."
    type: list
'''

import traceback

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ovirt import (
    check_sdk,
    create_connection,
    get_dict_of_struct,
    ovirt_info_full_argument_spec,
)


def main():
    argument_spec = ovirt_info_full_argument_spec(
        case_sensitive=dict(default=True, type='bool', required=False),
        from_=dict(default=None, type='int', required=False),
        max=dict(default=None, type='int', required=False),
        search=dict(default='', required=False),
        headers=dict(default='', required=False),
        query=dict(default='', required=False),
        wait=dict(default=True, type='bool', required=False)
    )
    module = AnsibleModule(argument_spec)
    is_old_facts = module._name == 'ovirt_event_facts'
    if is_old_facts:
        module.deprecate("The 'ovirt_event_facts' module has been renamed to 'ovirt_event_info', "
                         "and the renamed one no longer returns ansible_facts", version='2.13')

    check_sdk(module)

    try:
        auth = module.params.pop('auth')
        connection = create_connection(auth)
        events_service = connection.system_service().events_service()
        events = events_service.list(
            case_sensitive=module.params['case_sensitive'],
            from_=module.params['from_'],
            max=module.params['max'],
            search=module.params['search'],
            headers=module.params['headers'],
            query=module.params['query'],
            wait=module.params['wait']
        )

        result = dict(
            ovirt_events=[
                get_dict_of_struct(
                    struct=c,
                    connection=connection,
                    fetch_nested=module.params.get('fetch_nested'),
                    attributes=module.params.get('nested_attributes'),
                ) for c in events
            ],
        )
        if is_old_facts:
            module.exit_json(changed=False, ansible_facts=result)
        else:
            module.exit_json(changed=False, **result)
    except Exception as e:
        module.fail_json(msg=str(e), exception=traceback.format_exc())
    finally:
        connection.close(logout=auth.get('token') is None)


if __name__ == '__main__':
    main()
