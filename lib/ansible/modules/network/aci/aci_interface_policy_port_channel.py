#!/usr/bin/python
# -*- coding: utf-8 -*-

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'certified'}

DOCUMENTATION = r'''
---
module: aci_interface_policy_port_channel
short_description: Manage port channel interface policies (lacp:LagPol)
description:
- Manage port channel interface policies on Cisco ACI fabrics.
version_added: '2.4'
options:
  port_channel:
    description:
    - Name of the port channel.
    type: str
    required: yes
    aliases: [ name ]
  description:
    description:
    - The description for the port channel.
    type: str
    aliases: [ descr ]
  max_links:
    description:
    - Maximum links.
    - Accepted values range between 1 and 16.
    - The APIC defaults to C(16) when unset during creation.
    type: int
  min_links:
    description:
    - Minimum links.
    - Accepted values range between 1 and 16.
    - The APIC defaults to C(1) when unset during creation.
    type: int
  mode:
    description:
    - Port channel interface policy mode.
    - Determines the LACP method to use for forming port-channels.
    - The APIC defaults to C(off) when unset during creation.
    type: str
    choices: [ active, mac-pin, mac-pin-nicload, 'off', passive ]
  fast_select:
    description:
    - Determines if Fast Select is enabled for Hot Standby Ports.
    - This makes up the LACP Policy Control Policy; if one setting is defined, then all other Control Properties
      left undefined or set to false will not exist after the task is ran.
    - The APIC defaults to C(yes) when unset during creation.
    type: bool
  graceful_convergence:
    description:
    - Determines if Graceful Convergence is enabled.
    - This makes up the LACP Policy Control Policy; if one setting is defined, then all other Control Properties
      left undefined or set to false will not exist after the task is ran.
    - The APIC defaults to C(yes) when unset during creation.
    type: bool
  load_defer:
    description:
    - Determines if Load Defer is enabled.
    - This makes up the LACP Policy Control Policy; if one setting is defined, then all other Control Properties
      left undefined or set to false will not exist after the task is ran.
    - The APIC defaults to C(no) when unset during creation.
    type: bool
  suspend_individual:
    description:
    - Determines if Suspend Individual is enabled.
    - This makes up the LACP Policy Control Policy; if one setting is defined, then all other Control Properties
      left undefined or set to false will not exist after the task is ran.
    - The APIC defaults to C(yes) when unset during creation.
    type: bool
  symmetric_hash:
    description:
    - Determines if Symmetric Hashing is enabled.
    - This makes up the LACP Policy Control Policy; if one setting is defined, then all other Control Properties
      left undefined or set to false will not exist after the task is ran.
    - The APIC defaults to C(no) when unset during creation.
    type: bool
  state:
    description:
    - Use C(present) or C(absent) for adding or removing.
    - Use C(query) for listing an object or multiple objects.
    type: str
    choices: [ absent, present, query ]
    default: present
extends_documentation_fragment: aci
seealso:
- name: APIC Management Information Model reference
  description: More information about the internal APIC class B(lacp:LagPol).
  link: https://developer.cisco.com/docs/apic-mim-ref/
author:
- Dag Wieers (@dagwieers)
'''

EXAMPLES = r'''
- aci_interface_policy_port_channel:
    host: '{{ inventory_hostname }}'
    username: '{{ username }}'
    password: '{{ password }}'
    port_channel: '{{ port_channel }}'
    description: '{{ description }}'
    min_links: '{{ min_links }}'
    max_links: '{{ max_links }}'
    mode: '{{ mode }}'
  delegate_to: localhost
'''

RETURN = r'''
current:
  description: The existing configuration from the APIC after the module has finished
  returned: success
  type: list
  sample:
    [
        {
            "fvTenant": {
                "attributes": {
                    "descr": "Production environment",
                    "dn": "uni/tn-production",
                    "name": "production",
                    "nameAlias": "",
                    "ownerKey": "",
                    "ownerTag": ""
                }
            }
        }
    ]
error:
  description: The error information as returned from the APIC
  returned: failure
  type: dict
  sample:
    {
        "code": "122",
        "text": "unknown managed object class foo"
    }
raw:
  description: The raw output returned by the APIC REST API (xml or json)
  returned: parse error
  type: str
  sample: '<?xml version="1.0" encoding="UTF-8"?><imdata totalCount="1"><error code="122" text="unknown managed object class foo"/></imdata>'
sent:
  description: The actual/minimal configuration pushed to the APIC
  returned: info
  type: list
  sample:
    {
        "fvTenant": {
            "attributes": {
                "descr": "Production environment"
            }
        }
    }
previous:
  description: The original configuration from the APIC before the module has started
  returned: info
  type: list
  sample:
    [
        {
            "fvTenant": {
                "attributes": {
                    "descr": "Production",
                    "dn": "uni/tn-production",
                    "name": "production",
                    "nameAlias": "",
                    "ownerKey": "",
                    "ownerTag": ""
                }
            }
        }
    ]
proposed:
  description: The assembled configuration from the user-provided parameters
  returned: info
  type: dict
  sample:
    {
        "fvTenant": {
            "attributes": {
                "descr": "Production environment",
                "name": "production"
            }
        }
    }
filter_string:
  description: The filter string used for the request
  returned: failure or debug
  type: str
  sample: ?rsp-prop-include=config-only
method:
  description: The HTTP method used for the request to the APIC
  returned: failure or debug
  type: str
  sample: POST
response:
  description: The HTTP response from the APIC
  returned: failure or debug
  type: str
  sample: OK (30 bytes)
status:
  description: The HTTP status from the APIC
  returned: failure or debug
  type: int
  sample: 200
url:
  description: The HTTP url used for the request to the APIC
  returned: failure or debug
  type: str
  sample: https://10.11.12.13/api/mo/uni/tn-production.json
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.aci.aci import ACIModule, aci_argument_spec


def main():
    argument_spec = aci_argument_spec()
    argument_spec.update(
        port_channel=dict(type='str', aliases=['name']),  # Not required for querying all objects
        description=dict(type='str', aliases=['descr']),
        min_links=dict(type='int'),
        max_links=dict(type='int'),
        mode=dict(type='str', choices=['active', 'mac-pin', 'mac-pin-nicload', 'off', 'passive']),
        fast_select=dict(type='bool'),
        graceful_convergence=dict(type='bool'),
        load_defer=dict(type='bool'),
        suspend_individual=dict(type='bool'),
        symmetric_hash=dict(type='bool'),
        state=dict(type='str', default='present', choices=['absent', 'present', 'query']),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=[
            ['state', 'absent', ['port_channel']],
            ['state', 'present', ['port_channel']],
        ],
    )

    port_channel = module.params['port_channel']
    description = module.params['description']
    min_links = module.params['min_links']
    if min_links is not None and min_links not in range(1, 17):
        module.fail_json(msg='The "min_links" must be a value between 1 and 16')
    max_links = module.params['max_links']
    if max_links is not None and max_links not in range(1, 17):
        module.fail_json(msg='The "max_links" must be a value between 1 and 16')
    mode = module.params['mode']
    state = module.params['state']

    # Build ctrl value for request
    ctrl = []
    if module.params['fast_select'] is True:
        ctrl.append('fast-sel-hot-stdby')
    if module.params['graceful_convergence'] is True:
        ctrl.append('graceful-conv')
    if module.params['load_defer'] is True:
        ctrl.append('load-defer')
    if module.params['suspend_individual'] is True:
        ctrl.append('susp-individual')
    if module.params['symmetric_hash'] is True:
        ctrl.append('symmetric-hash')
    if not ctrl:
        ctrl = None
    else:
        ctrl = ",".join(ctrl)

    aci = ACIModule(module)
    aci.construct_url(
        root_class=dict(
            aci_class='lacpLagPol',
            aci_rn='infra/lacplagp-{0}'.format(port_channel),
            module_object=port_channel,
            target_filter={'name': port_channel},
        ),
    )

    aci.get_existing()

    if state == 'present':
        aci.payload(
            aci_class='lacpLagPol',
            class_config=dict(
                name=port_channel,
                ctrl=ctrl,
                descr=description,
                minLinks=min_links,
                maxLinks=max_links,
                mode=mode,
            ),
        )

        aci.get_diff(aci_class='lacpLagPol')

        aci.post_config()

    elif state == 'absent':
        aci.delete_config()

    aci.exit_json()


if __name__ == "__main__":
    main()
