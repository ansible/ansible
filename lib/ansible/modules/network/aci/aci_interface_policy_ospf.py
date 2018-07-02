#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2018, Dag Wieers (dagwieers) <dag@wieers.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: aci_interface_policy_ospf
short_description: Manage OSPF interface policies (ospf:IfPol)
description:
- Manage OSPF interface policies on Cisco ACI fabrics.
notes:
- More information about the internal APIC class B(ospf:IfPol) from
  L(the APIC Management Information Model reference,https://developer.cisco.com/docs/apic-mim-ref/).
author:
- Dag Wieers (@dagwieers)
version_added: '2.7'
options:
  tenant:
    description:
    - The name of the Tenant the OSPF interface policy should belong to.
    required: yes
    aliases: [ tenant_name ]
  ospf:
    description:
    - The OSPF interface policy name.
    - This name can be between 1 and 64 alphanumeric characters.
    - Note that you cannot change this name after the object has been saved.
    required: yes
    aliases: [ ospf_interface, name ]
  description:
    description:
    - The description for the OSPF interface.
    aliases: [ descr ]
  network_type:
    description:
    - The OSPF interface policy network type.
    - OSPF supports broadcast and point-to-point.
    choices: [ bcast, p2p ]
  priority:
    description:
    - The priority for the OSPF interface profile.
  cost:
    description:
    - The OSPF cost of the interface.
    - The cost (also called metric) of an interface in OSPF is an indication of
      the overhead required to send packets across a certain interface. The
      cost of an interface is inversely proportional to the bandwidth of that
      interface. A higher bandwidth indicates a lower cost. There is more
      overhead (higher cost) and time delays involved in crossing a 56k serial
      line than crossing a 10M ethernet line. The formula used to calculate the
      cost is C(cost= 10000 0000/bandwith in bps) For example, it will cost
      10 EXP8/10 EXP7 = 10 to cross a 10M Ethernet line and will cost
      10 EXP8/1544000 = 64 to cross a T1 line.
    - By default, the cost of an interface is calculated based on the bandwidth;
      you can force the cost of an interface with the ip ospf cost value
      interface subconfiguration mode command.
  controls:
    description:
    - The interface policy controls.
    choices: [ advert-subnet, bfd, mtu-ignore, passive ]
  dead_interval:
    description:
    - The interval between hello packets from a neighbor before the router
      declares the neighbor as down.
    - This value must be the same for all networking devices on a specific network.
    - Specifying a smaller dead interval (seconds) will give faster detection
      of a neighbor being down and improve convergence, but might cause more
      routing instability.
  hello_interval:
    description:
    - The interval between hello packets that OSPF sends on the interface.
    - Note that the smaller the hello interval, the faster topological changes will be detected, but more routing traffic will ensue.
    - This value must be the same for all routers and access servers on a specific network.
  retransmit_interval:
    description:
    - The interval between LSA retransmissions.
    - The retransmit interval occurs while the router is waiting for an acknowledgement from the neighbor router that it received the LSA.
    - If no acknowlegment is received at the end of the interval, then the LSA is resent.
  transmit_delay:
    description:
    - The delay time needed to send an LSA update packet.
    - OSPF increments the LSA age time by the transmit delay amount before transmitting the LSA update.
    - You should take into account the transmission and propagation delays for the interface when you set this value.
  state:
    description:
    - Use C(present) or C(absent) for adding or removing.
    - Use C(query) for listing an object or multiple objects.
    choices: [ absent, present, query ]
    default: present
extends_documentation_fragment: aci
'''

# FIXME: Add more, better examples
EXAMPLES = r'''
- aci_interface_policy_ospf:
    host: '{{ hostname }}'
    username: '{{ username }}'
    password: '{{ password }}'
    ospf: '{{ ospf }}'
    description: '{{ descr }}'
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
  type: string
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
  type: string
  sample: ?rsp-prop-include=config-only
method:
  description: The HTTP method used for the request to the APIC
  returned: failure or debug
  type: string
  sample: POST
response:
  description: The HTTP response from the APIC
  returned: failure or debug
  type: string
  sample: OK (30 bytes)
status:
  description: The HTTP status from the APIC
  returned: failure or debug
  type: int
  sample: 200
url:
  description: The HTTP url used for the request to the APIC
  returned: failure or debug
  type: string
  sample: https://10.11.12.13/api/mo/uni/tn-production.json
'''

from ansible.module_utils.network.aci.aci import ACIModule, aci_argument_spec
from ansible.module_utils.basic import AnsibleModule


def main():
    argument_spec = aci_argument_spec()
    argument_spec.update(
        tenant=dict(type='str', required=False, aliases=['tenant_name']),  # Not required for querying all objects
        ospf=dict(type='str', required=False, aliases=['ospf_interface', 'name']),  # Not required for querying all objects
        description=dict(type='str', aliases=['descr']),
        network_type=dict(type='str', choices=['bcast', 'p2p']),
        priority=dict(type='int'),
        cost=dict(type='int'),
        controls=dict(type='list', choices=['advert-subnet', 'bfd', 'mtu-ignore', 'passive']),
        hello_interval=dict(type='int'),
        dead_interval=dict(type='int'),
        retransmit_interval=dict(type='int'),
        transmit_delay=dict(type='int'),
        state=dict(type='str', default='present', choices=['absent', 'present', 'query']),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=[
            ['state', 'absent', ['ospf', 'tenant']],
            ['state', 'present', ['ospf', 'tenant']],
        ],
    )

    aci = ACIModule(module)

    tenant = module.params['tenant']
    ospf = module.params['ospf']
    description = module.params['description']
    if module.params['controls'] is None:
        controls = None
    else:
        controls = ','.join(module.params['controls'])
    cost = module.params['cost']
    dead_interval = module.params['dead_interval']
    hello_interval = module.params['hello_interval']
    network_type = module.params['network_type']
    priority = module.params['priority']
    retransmit_interval = module.params['retransmit_interval']
    transmit_delay = module.params['transmit_delay']
    state = module.params['state']

    aci.construct_url(
        root_class=dict(
            aci_class='ospfIfPol',
            aci_rn='tn-{0}/ospfIfPol-{1}'.format(tenant, ospf),
            filter_target='eq(ospfIfPol.name, "{0}")'.format(ospf),
            module_object=ospf,
        ),
    )

    aci.get_existing()

    if state == 'present':
        aci.payload(
            aci_class='ospfIfPol',
            class_config=dict(
                name=ospf,
                descr=description,
                cost=cost,
                ctrl=controls,
                deadIntvl=dead_interval,
                helloIntvl=hello_interval,
                nwT=network_type,
                prio=priority,
                rexmitIntvl=retransmit_interval,
                xmitDelay=transmit_delay,
            ),
        )

        aci.get_diff(aci_class='ospfIfPol')

        aci.post_config()

    elif state == 'absent':
        aci.delete_config()

    aci.exit_json()


if __name__ == "__main__":
    main()
