#!/usr/bin/python
# -*- coding: utf-8 -*-

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: aci_filter_entry
short_description: Manage filter entries on Cisco ACI fabrics (vz:Entry)
description:
- Manage filter entries for a filter on Cisco ACI fabrics.
- More information from the internal APIC class
  I(vz:Entry) at U(https://developer.cisco.com/media/mim-ref/MO-vzEntry.html).
author:
- Swetha Chunduri (@schunduri)
- Dag Wieers (@dagwieers)
- Jacob McGill (@jmcgill298)
version_added: '2.4'
requirements:
- Tested with ACI Fabric 1.0(3f)+
notes:
- The C(tenant) and C(filter) used must exist before using this module in your playbook.
  The M(aci_tenant) and M(aci_filter) modules can be used for this.
options:
  arp_flag:
    description:
    - The arp flag to use when the ether_type is arp.
    - The APIC defaults new Filter Entries to C(unspecified).
    choices: [ arp_reply, arp_request, unspecified ]
    default: unspecified
  description:
    description:
    - Description for the Filter Entry.
    aliases: [ descr ]
  dst_port:
    description:
    - Used to set both destination start and end ports to the same value when ip_protocol is tcp or udp.
    - The APIC defaults new Filter Entries to C(unspecified).
    choices: [ Valid TCP/UDP Port Ranges]
    default: unspecified
  dst_port_end:
    description:
    - Used to set the destination end port when ip_protocol is tcp or udp.
    - The APIC defaults new Filter Entries to C(unspecified).
    choices: [ Valid TCP/UDP Port Ranges]
    default: unspecified
  dst_port_start:
    description:
    - Used to set the destination start port when ip_protocol is tcp or udp.
    - The APIC defaults new Filter Entries to C(unspecified).
    choices: [ Valid TCP/UDP Port Ranges]
    default: unspecified
  entry:
    description:
    - Then name of the Filter Entry.
    aliases: [ entry_name, filter_entry, name ]
  ether_type:
    description:
    - The Ethernet type.
    - The APIC defaults new Filter Entries to C(unspecified).
    choices: [ arp, fcoe, ip, mac_security, mpls_ucast, trill, unspecified ]
    default: unspecified
  filter:
    description:
      The name of Filter that the entry should belong to.
    aliases: [ filter_name ]
  icmp_msg_type:
    description:
    - ICMPv4 message type; used when ip_protocol is icmp.
    - The APIC defaults new Filter Entries to C(unspecified).
    choices: [ dst_unreachable, echo, echo_reply, src_quench, time_exceeded, unspecified ]
    default: unspecified
  icmp6_msg_type:
    description:
    - ICMPv6 message type; used when ip_protocol is icmpv6.
    - The APIC defaults new Filter Entries to C(unspecified).
    choices: [ dst_unreachable, echo_request, echo_reply, neighbor_advertisement, neighbor_solicitation, redirect, time_exceeded, unspecified ]
    default: unspecified
  ip_protocol:
    description:
    - The IP Protocol type when ether_type is ip.
    - The APIC defaults new Filter Entries to C(unspecified).
    choices: [ eigrp, egp, icmp, icmpv6, igmp, igp, l2tp, ospfigp, pim, tcp, udp, unspecified ]
    default: unspecified
  state:
    description:
    - present, absent, query
    default: present
    choices: [ absent, present, query ]
  stateful:
    description:
    - Determines the statefulness of the filter entry.
  tenant:
    description:
    - The name of the tenant.
    aliases: [ tenant_name ]
extends_documentation_fragment: aci
'''

EXAMPLES = r'''
- aci_filter_entry:
    action: "{{ action }}"
    entry: "{{ entry }}"
    tenant: "{{ tenant }}"
    ether_name: "{{  ether_name }}"
    icmp_msg_type: "{{ icmp_msg_type }}"
    filter: "{{ filter }}"
    descr: "{{ descr }}"
    host: "{{ inventory_hostname }}"
    username: "{{ user }}"
    password: "{{ pass }}"
    protocol: "{{ protocol }}"
'''

RETURN = ''' # '''

from ansible.module_utils.network.aci.aci import ACIModule, aci_argument_spec
from ansible.module_utils.basic import AnsibleModule

VALID_ARP_FLAGS = ['arp_reply', 'arp_request', 'unspecified']
VALID_ETHER_TYPES = ['arp', 'fcoe', 'ip', 'mac_security', 'mpls_ucast', 'trill', 'unspecified']
VALID_ICMP_TYPES = ['dst_unreachable', 'echo', 'echo_reply', 'src_quench', 'time_exceeded',
                    'unspecified', 'echo-rep', 'dst-unreach']
VALID_ICMP6_TYPES = ['dst_unreachable', 'echo_request', 'echo_reply', 'neighbor_advertisement',
                     'neighbor_solicitation', 'redirect', 'time_exceeded', 'unspecified']
VALID_IP_PROTOCOLS = ['eigrp', 'egp', 'icmp', 'icmpv6', 'igmp', 'igp', 'l2tp', 'ospfigp', 'pim', 'tcp', 'udp', 'unspecified']

# mapping dicts are used to normalize the proposed data to what the APIC expects, which will keep diffs accurate
ARP_FLAG_MAPPING = dict(arp_reply='reply', arp_request='req', unspecified=None)
FILTER_PORT_MAPPING = {'443': 'https', '25': 'smtp', '80': 'http', '20': 'ftpData', '53': 'dns', '110': 'pop3', '554': 'rtsp'}
ICMP_MAPPING = {'dst_unreachable': 'dst-unreach', 'echo': 'echo', 'echo_reply': 'echo-rep', 'src_quench': 'src-quench',
                'time_exceeded': 'time-exceeded', 'unspecified': 'unspecified', 'echo-rep': 'echo-rep', 'dst-unreach': 'dst-unreach'}
ICMP6_MAPPING = dict(dst_unreachable='dst-unreach', echo_request='echo-req', echo_reply='echo-rep', neighbor_advertisement='nbr-advert',
                     neighbor_solicitation='nbr-solicit', redirect='redirect', time_exceeded='time-exceeded', unspecified='unspecified')


def main():
    argument_spec = aci_argument_spec
    argument_spec.update(
        arp_flag=dict(type='str', choices=VALID_ARP_FLAGS),
        description=dict(type='str'),
        dst_port=dict(type='str'),
        dst_port_end=dict(type='str'),
        dst_port_start=dict(type='str'),
        entry=dict(type='str', aliases=['entry_name', 'filter_entry', 'name']),
        ether_type=dict(choices=VALID_ETHER_TYPES, type='str'),
        filter=dict(type='str', aliases=['filter_name']),
        icmp_msg_type=dict(type='str', choices=VALID_ICMP_TYPES),
        icmp6_msg_type=dict(type='str', choices=VALID_ICMP6_TYPES),
        ip_protocol=dict(choices=VALID_IP_PROTOCOLS, type='str'),
        state=dict(type='str', default='present', choices=['absent', 'present', 'query']),
        stateful=dict(type='str', choices=['no', 'yes']),
        tenant=dict(type="str", aliases=['tenant_name']),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=[
            ['state', 'absent', ['entry', 'filter', 'tenant']],
            ['state', 'present', ['entry', 'filter', 'tenant']],
        ],
    )

    arp_flag = module.params['arp_flag']
    if arp_flag is not None:
        arp_flag = ARP_FLAG_MAPPING[arp_flag]
    description = module.params['description']
    dst_port = module.params['dst_port']
    if dst_port in FILTER_PORT_MAPPING.keys():
        dst_port = FILTER_PORT_MAPPING[dst_port]
    dst_end = module.params['dst_port_end']
    if dst_end in FILTER_PORT_MAPPING.keys():
        dst_end = FILTER_PORT_MAPPING[dst_end]
    dst_start = module.params['dst_port_start']
    if dst_start in FILTER_PORT_MAPPING.keys():
        dst_start = FILTER_PORT_MAPPING[dst_start]
    entry = module.params['entry']
    ether_type = module.params['ether_type']
    filter_name = module.params['filter']
    icmp_msg_type = module.params['icmp_msg_type']
    if icmp_msg_type is not None:
        icmp_msg_type = ICMP_MAPPING[icmp_msg_type]
    icmp6_msg_type = module.params['icmp6_msg_type']
    if icmp6_msg_type is not None:
        icmp6_msg_type = ICMP6_MAPPING[icmp6_msg_type]
    ip_protocol = module.params['ip_protocol']
    state = module.params['state']
    stateful = module.params['stateful']
    tenant = module.params['tenant']

    # validate that dst_port is not passed with dst_start or dst_end
    if dst_port is not None and (dst_end is not None or dst_start is not None):
        module.fail_json(msg="Parameter 'dst_port' cannot be used with 'dst_end' and 'dst_start'")
    elif dst_port is not None:
        dst_end = dst_port
        dst_start = dst_port

    aci = ACIModule(module)
    aci.construct_url(
        root_class=dict(
            aci_class='fvTenant',
            aci_rn='tn-{}'.format(tenant),
            filter_target='eq(fvTenant.name, "{}")'.format(tenant),
            module_object=tenant,
        ),
        subclass_1=dict(
            aci_class='vzFilter',
            aci_rn='flt-{}'.format(filter_name),
            filter_target='eq(vzFilter.name, "{}")'.format(filter_name),
            module_object=filter_name,
        ),
        subclass_2=dict(
            aci_class='vzEntry',
            aci_rn='e-{}'.format(entry),
            filter_target='eq(vzEntry.name, "{}")'.format(entry),
            module_object=entry
        ),
    )

    aci.get_existing()

    if state == 'present':
        # Filter out module params with null values
        aci.payload(
            aci_class='vzEntry',
            class_config=dict(
                arpOpc=arp_flag,
                descr=description,
                dFromPort=dst_start,
                dToPort=dst_end,
                etherT=ether_type,
                icmpv4T=icmp_msg_type,
                icmpv6T=icmp6_msg_type,
                name=entry,
                prot=ip_protocol,
                stateful=stateful,
            ),
        )

        # generate config diff which will be used as POST request body
        aci.get_diff(aci_class='vzEntry')

        # submit changes if module not in check_mode and the proposed is different than existing
        aci.post_config()

    elif state == 'absent':
        aci.delete_config()

    module.exit_json(**aci.result)


if __name__ == "__main__":
    main()
