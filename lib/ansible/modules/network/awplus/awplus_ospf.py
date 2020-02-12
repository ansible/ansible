#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2020, Allied Telesis Ltd.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'network',
}


DOCUMENTATION = """
---
module: awplus_ospf
version_added: "2.10"
short_description: Manages OSPF configuration.
description:
    - Manages OSPF configurations on AlliedWare Plus switches.
author:
    - Isaac Daly (@dalyIsaac)
notes:
    - C(state=present) is the default for all state options.
options:
    area:
        description:
            - This option allows the configuration of OSPF areas on an AlliedWare
                Plus device.
        suboptions:
            state:
                description:
                    - C(state=absent) removes the given C(area_id)
                choices: ['present', 'absent']
            area_id:
                description:
                    - Specifies the given area to configure. Valid values are integers in
                        in the range 0-4294967295 or IPv4 addresses expressed as A.B.C.D.
                required: true
            default_cost:
                description:
                    - This option allows the configuration of the default cost for the
                        default summary route sent into a stub of NSSA area.
                suboptions:
                    state:
                        description:
                             - C(state=absent) resets the default cost for this OSPF area to
                                 1.
                        choices: ['present', 'absent']
                    cost_value:
                        description:
                            - The new default cost for this OSPF area.
            authentication:
                description:
                    - This option allows the configuration for authentication for an OSPF
                        area. Specifying the area authentication sets the authentication to
                        Type 1 authentication or the Simple Text password authentication
                        (defailts in RFC 2328).
                suboptions:
                    state:
                        description:
                            - C(state=absent) removes the authentication specification for an
                                area.
                        choices: ['present', 'absent']
                    message_digest:
                        description:
                            - Enables MD5 authentication in the OSPF area.
                        type: bool
            filter_list:
                description:
                    - This option configures filters to advertise summary routes on Area
                        Border Routers (ABR). This option can be used to suppress
                        particular intra-area routes from/to an area to/from the other
                        areas.
                suboptions:
                    state:
                        description:
                            - C(state=absent) removes the filter configuration for the area.
                        choices: ['present', 'absent']
                    prefix_list:
                        description:
                            - The name of a prefix list.
                    direction:
                        description:
                            - In: Filter routes from the other areas to this area.
                            - Out: Filter routes from this area to other areas.
            nssa:
                description:
                    - This option configures an area as a Not-So-Stubby-Area (NSSA). By
                        default, no NSSA area is defined.
                suboptions:
                    state:
                        description:
                            - C(state=absent) removes the designation of this area as a NSSA.
                        choices: ['present', 'absent']
                    default_information_originate:
                        description:
                            - If true, this option will originate Type-7 default LSA into
                                NSSA. If C(state=present) then
                                C(default_information_originate_metric_type) and
                                C(default_information_originate_metric) is required with this
                                command.
                        type: bool
                    default_information_originate_metric_type:
                        description:
                            - The external metric type.
                        choices: [1, 2]
                    default_information_originate_metric:
                        description:
                            - The metric value for the Type-7 default LSA.
                    no_redistribution:
                        description:
                            - If true, then do not redistribute external routes into NSSA.
                        type: bool
                    no_summary:
                        description:
                            - If true, then do not inject inter-area routes into NSSA.
                        type: bool
                    translator_role:
                        description:
                            - If true and C(state=present), then this enables the
                                configuration of translator_role_type (the NSSA-ABR
                                translator-role).
                        type: bool
                    translator_role_type:
                        description:
                            - The NSSA-ABR translator-role type.
                        choices: ['always', 'candidate', 'never']
            range:
                description:
                    - This option is used to summarize OSPF routes at an area boundary,
                        configuring an IPv4 address range which consolidates OSPF routes.
                state:
                    description:
                        - C(state=absent) removes the OSPF routes summarization.
                    choices: ['present', 'absent']
                suboptions:
                    ip_addr:
                        description:
                            - The IP address and prefix-length to be used for
                              consolidation.
                    advertise:
                        description:
                            - Advertise this range as a summary route into other areas.
                        type: bool
            stub:
                description:
                    - This option defines an OSPF area as a stub area.
                suboptions:
                    state:
                        description:
                            - C(state=absent) removes the configuration of this area as a
                                stub.
                        choices: ['present', 'absent']
                    no_summary:
                        description:
                            - Stops an ABR from sending summary links into the stub area.
                        type: bool
            virtual_link:
                description:
                    - Configures a link between two backbone areas that are physically
                        separated through other non-backbone areas.
                suboptions:
                    state:
                        description:
                            - C(state=absent) removes the virtual link.
                        choices: ['present', 'absent']
                    ip_addr:
                        description:
                            - The OSPF router ID of the virtual link neighbour.
                        required: true
                    auth_key:
                        description:
                            - The password used for this virtual link. This option is
                                mutually exclusive with C(msg_key_id) and C(msg_key_password).
                                The password is 8 characters.
                    msg_key_id:
                        description:
                            - The key ID for the message digest key using the MD5 encryption
                                algorithm. The key ID should be an integer in the range 1-255.
                                This must be used in conjunction with C(msg_key_password).
                    msg_key_pasword:
                        description:
                            - The message digest authentication password of 16 characters.
                    authentication_type:
                        description:
                            - Specifies whether to use message-digest authentication, or
                                null authentication to override password or message digest.
                        choices: ['message-digest', 'null']
                    authentication:
                        description:
                            - Enables authentication on this virtual link.
                        type: bool
                    dead_interval:
                        description:
                            - Allows the configuration of the dead-interval.
                        type: bool
                    dead_interval_value:
                        description:
                            - The value of the dead-interval. If no packets are received from
                                a particular neighbour for C(dead_interval_value) seconds,
                                the router considers that neighboring router as being off-line.
                    hello_interval:
                        description:
                            - Allows the configuration of the hello-interval.
                        type: bool
                    hello_interval_value:
                        description:
                            - The value for the hello-interval. The hello-interval is the
                                interval the router waits before it sends a hello packet.
                    retransmit_interval:
                        description:
                            - Allows the retransmit-interval to be configured.
                        type: bool
                    retransmit_interval_value:
                        description:
                            - The value for the retransmit-interval. The retransmit-interval
                                is the interval the router waits before it retransmits a
                                packet.
                    transmit_delay:
                        description:
                            - Allows the configuration of the transmit-delay.
                        type: bool
                    transmit_delay_value:
                        description:
                            - The value for the transmit-delay. The transmit-delay is the
                                interval the router waits before it transmits a packet.
    router:
        description:
            - This configures the router to use OSPF.
        suboptions:
            state:
                description:
                    - C(state=absent) is used to terminate and delete a specific OSPF
                        routing process.
                choices: ['present', 'absent']
            process_id:
                description:
                    - A positive integer in the range 1 to 65535 used to define a routing
                        process.
            vrf_instance:
                description:
                    - The VRF isntance to be associated with the OSPF routing process.
        required: True
    network_area:
        description:
            - Used to enable OSPF routing with a specified Area ID on any interfaces
                which match the specified network address.
        suboptions:
            state:
                description:
                    - C(state=absent) is used to disable OSPF routing on the interfaces.
                choices: ['present', 'absent']
            network_address:
                description:
                    - IP address of the network, entered in the form of either
                        A.B.C.D/mask or A.B.C.D mask.
                required: true
            area_id:
                description:
                    - The area ID to use on the specified network address. This should be
                        in the format of either an IPv4 address of A.B.C.D or a 4 octets
                        unsigned integer value.
                required: true
    ospf_router_id:
        description:
            - This option is used to specific a router ID for the OSPF process.
        suboptions:
            state:
                description:
                    - C(state=absent) removes the router ID for the given OSPF process.
            ip_addr:
                description:
                    - The router ID in IPv4 address format.
    passive_interface:
        description:
            - This option is used to suppress the sending of Hello packets on all
                interfaces, or on a specified interface. If no interface name is
                specified, then all interfaces are put into passive mode.
        suboptions:
            state:
                description:
                    - C(state=absent) allows the sending of Hello packets on all
                        interfaces, or the specified interface.
            name:
                description:
                    - The name of the interface.
            ip_addr:
                description:
                    - The IP address of the interface, entered in the form A.B.C.D.
    redistribute:
        description:
            - This option is used to redistribute routes from other routing
                protocols, static routes, and connected routes into an OSPF routing
                table.
        suboptions:
            state:
                description:
                    - C(state=absent) is used to turn off redistribution.
            static:
                description:
                    - When true, specifies that this applies to the redistribution of
                        static routes.
                type: bool
            metric:
                description:
                    - Specifies the external metric value.
            metric_type:
                description:
                    - Specifies the metric type. The type must be a string.
                choices: ['1', '2']
            route_map_name:
                description:
                    - Specifies the name of the route map.
            tag:
                description:
                    - Specifies the external route tag.
    summary_address:
        description:
            - This option is used to summarize, or possibly suppres, external routes
                that have the specified address range.
        suboptions:
            state:
                description:
                    - C(state=absent) stops summarizing or suppressing external routes
                        that have the specified address range.
            ip_addr:
                description:
                    - IPv4 range of addresses, expressed as A.B.C.D/prefix-length
                required: True
            not_advertise:
                description:
                    - Specifies whether you want OSPF to advertise the summary address or
                        the individual networks within the range of the summary address.
                type: bool
            tag:
                description:
                    - The tag value that OSPF places in the AS external LSAs created as a
                        result of redistributing the summary route. The tag overrides tags
                        set by the original route.
notes:
    - Check mode is supported.
"""


EXAMPLES = """
commands:
    - name: Configure OSPF router process id
        awplus_ospf:
            router:
                process_id: 100
            area:
                area_id: "1"
                default_cost:
                    cost_value: 5
                authentication:
                    message_digest: true
"""


RETURN = """
commands:
    description: The list of commands to send to the device
    returned: always
    type: list
    sample: ['router ospf 100', 'area 1 stub']
"""

from ansible.module_utils.network.awplus.utils.complex_constructor import (
    PRESENT,
    STATE,
    ABSENT,
    get_commands,
    construct_from_list,
    get_param,
)
from ansible.module_utils.network.awplus.awplus import (
    get_config,
    load_config,
    awplus_argument_spec,
)
from ansible.module_utils.basic import AnsibleModule


def _append(cmd, state, val):
    if state == PRESENT and val is not None:
        return cmd + ' {}'.format(val)
    return cmd


NSSA_MAP = {
    'default_information_originate': {
        PRESENT: [
            'area',
            'area.area_id',
            'nssa default-information-originate',
            '',
            'metric',
            'default_information_originate_metric',
            'metric-type',
            'default_information_originate_metric_type',
        ],
        ABSENT: [
            'no area',
            'area.area_id',
            'nssa default-information-originate',
        ],
    },
    'no_redistribution': {
        PRESENT: ['area', 'area.area_id', 'nssa', 'no_redistribution'],
        ABSENT: ['no area', 'area.area_id', 'nssa', 'no_redistribution'],
    },
    'no_summary': {
        PRESENT: ['area', 'area.area_id', 'nssa', 'no_summary'],
        ABSENT: ['no area', 'area.area_id', 'nssa', 'no_summary'],
    },
    'translator_role': {
        PRESENT: [
            'area',
            'area.area_id',
            'nssa',
            'translator_role',
            '',
            'translator_role_type',
        ],
        ABSENT: ['no area', 'area.area_id', 'nssa', 'translator_role'],
    },
}


def area_nssa_map(module):
    nssa = module.params['area']['nssa']

    map_key = None
    if nssa.get('default_information_originate'):
        map_key = 'default_information_originate'
    elif nssa.get('no_redistribution'):
        map_key = 'no_redistribution'
    elif nssa.get('no_summary'):
        map_key = 'no_summary'
    elif nssa.get('translator_role'):
        map_key = 'translator_role'

    if map_key:
        return construct_from_list(NSSA_MAP[map_key], module, nssa)
    return ''


def area_range_map(module):
    range_params = module.params['area']['range']
    state = range_params[STATE]
    area_id = module.params['area']['area_id']
    ip_addr = range_params['ip_addr']
    advertise = range_params.get('advertise')
    cmd = 'area {} range {}'.format(area_id, ip_addr)
    if state == 'absent':
        return 'no ' + cmd
    if advertise:
        cmd += ' advertise'
    elif advertise is False:
        cmd += ' not-advertise'
    return cmd


def _add_auth_msg_key(cmd, state, auth_key, msg_key, msg_key_id):
    if auth_key:
        cmd += ' authentication-key'
        if state == 'present':
            cmd += ' {}'.format(auth_key)
    elif msg_key and msg_key_id is not None and msg_key:
        cmd += ' message-digest-key {}'.format(msg_key_id)
        if state == 'present':
            cmd += ' md5 {}'.format(msg_key)
    return cmd


def area_virtual_link_map(module):
    params = module.params['area']['virtual_link']
    area_id = get_param('area.area_id', module, module.params)
    ip_addr = params['ip_addr']

    cmd = 'area {} virtual-link {}'.format(area_id, ip_addr)

    auth_key = params.get('auth_key')
    msg_key = params.get('msg_key_password')
    msg_key_id = params.get('msg_key_id')
    authentication_type = params.get('authentication_type')
    authentication = params.get('authentication')
    dead_interval = params.get('dead_interval')
    dead_interval_value = params.get('dead_interval_value')
    hello_interval = params.get('hello_interval')
    hello_interval_value = params.get('hello_interval_value')
    retransmit_interval = params.get('retransmit_interval')
    transmit_delay = params.get('transmit_delay')
    retransmit_interval_value = params.get('retransmit_interval_value')
    transmit_delay = params.get('transmit_delay')
    transmit_delay_value = params.get('transmit_delay_value')

    state = params[STATE]

    if (
        dead_interval
        or hello_interval
        or retransmit_interval
        or transmit_delay
    ):
        if authentication:
            cmd += ' authentication'
        if dead_interval:
            cmd += ' dead-interval'
            cmd = _append(cmd, state, dead_interval_value)
        if hello_interval:
            cmd += ' hello-interval'
            cmd = _append(cmd, state, hello_interval_value)
        if retransmit_interval:
            cmd += ' retransmit-interval'
            cmd = _append(cmd, state, retransmit_interval_value)
        if transmit_delay:
            cmd += ' transmit-delay'
            cmd = _append(cmd, state, transmit_delay_value)
    elif authentication:
        cmd += ' authentication'
        if authentication_type and state == 'present':
            cmd += ' {}'.format(authentication_type)
        cmd = _add_auth_msg_key(cmd, state, auth_key, msg_key, msg_key_id)
    elif auth_key or (msg_key and msg_key_id is not None and msg_key):
        cmd = _add_auth_msg_key(cmd, state, auth_key, msg_key, msg_key_id)

    if state == ABSENT:
        cmd = 'no ' + cmd

    return cmd


def router_ospf_map(module, commands):
    params = module.params['router']
    cmd = 'router ospf'
    state = params[STATE]

    process_id = params.get('process_id')
    vrf_instance = params.get('vrf_instance')

    if process_id:
        cmd += ' {}'.format(process_id)
    if state == ABSENT and len(commands) == 0:
        return 'no ' + cmd
    elif vrf_instance:
        cmd += ' {}'.format(vrf_instance)
    return cmd


def passive_interface_map(module):
    params = module.params['passive_interface']
    cmd = 'passive-interface'
    state = params[STATE]

    interface_name = params.get('name')
    ip_addr = params.get('ip_addr')

    if interface_name is not None:
        cmd += ' {}'.format(interface_name)
    if ip_addr is not None:
        cmd += ' {}'.format(ip_addr)

    if state == ABSENT:
        cmd = 'no ' + cmd

    return cmd


def summary_address_map(module):
    params = module.params['summary_address']
    ip_addr = params['ip_addr']
    not_advertise = params.get('not_advertise')
    tag = params.get('tag')

    cmd = 'summary-address {}'.format(ip_addr)

    if not_advertise is True:
        cmd += ' not-advertise'
    elif tag is not None:
        cmd += ' tag {}'.format(tag)

    state = params[STATE]
    if state == ABSENT:
        cmd = 'no ' + cmd

    return cmd


def redistribute_map(module):
    params = module.params['redistribute']
    state = params[STATE]
    connected = params.get('connected')
    static = params.get('static')
    metric = params.get('metric')
    metric_type = params.get('metric_type')
    route_map_name = params.get('route_map_name')
    tag = params.get('tag')

    cmd = 'redistribute'

    if connected:
        cmd += ' connected'
    elif static:
        cmd += ' static'

    if not any([metric, metric_type, route_map_name, tag]):
        module.fail_json(
            {
                'errors': [
                    'One of metric, metric_type, route_map_name, tag must be '
                    'present.'
                ]
            }
        )
    if metric:
        cmd += ' metric'
        if state == PRESENT:
            cmd += ' {}'.format(metric)
    if metric_type:
        cmd += ' metric-type'
        if state == PRESENT:
            cmd += ' {}'.format(metric_type)
    if route_map_name:
        cmd += ' route-map'
        if state == PRESENT:
            cmd += ' {}'.format(route_map_name)
    if tag:
        cmd += ' tag'
        if state == PRESENT:
            cmd += ' {}'.format(tag)

    if state == ABSENT:
        return 'no ' + cmd
    return cmd


KEY_TO_COMMAND_MAP = {
    'area': {
        'default_cost': {
            PRESENT: ['area', 'area.area_id', 'default-cost', 'cost_value'],
            ABSENT: ['no area', 'area.area_id', 'default-cost'],
        },
        'authentication': {
            PRESENT: [
                'area',
                'area.area_id',
                'authentication',
                'message_digest',
            ],
            ABSENT: ['no area', 'area.area_id', 'authentication'],
        },
        'filter_list': {
            PRESENT: [
                'area',
                'area.area_id',
                'filter-list prefix',
                'prefix_list',
                '',
                'direction',
            ],
            ABSENT: [
                'no area',
                'area.area_id',
                'filter-list prefix',
                'prefix_list',
                '',
                'direction',
            ],
        },
        'nssa': area_nssa_map,
        'range': area_range_map,
        'stub': {
            PRESENT: ['area', 'area.area_id', 'stub', 'no_summary'],
            ABSENT: ['no area', 'area.area_id', 'stub', 'no_summary'],
        },
        'virtual_link': area_virtual_link_map,
    },
    'network_area': {
        PRESENT: ['network', 'network_address', 'area', 'area_id'],
        ABSENT: ['no network', 'network_address', 'area', 'area_id'],
    },
    'ospf_router_id': {
        PRESENT: ['ospf router-id', 'ip_addr'],
        ABSENT: ['no ospf router-id'],
    },
    'passive_interface': passive_interface_map,
    'redistribute': redistribute_map,
    'summary_address': summary_address_map,
}


def get_existing_config(module):
    config = (get_config(module, flags=[' router ospf']),)

    existing_config = set()
    ospf = None
    for item in config:
        for line in item.splitlines():
            s = line.strip()
            existing_config.add(s)
            if 'router ospf' in s:
                ospf = s

    return ospf, existing_config


def main():
    area_default_cost_spec = {
        'state': {'choices': [PRESENT, ABSENT], 'default': PRESENT},
        'cost_value': {'type': 'int'},
    }

    area_authentication_spec = {
        'state': {'choices': [PRESENT, ABSENT], 'default': PRESENT},
        'message_digest': {'type': 'bool', 'default': False},
    }

    area_filter_list_spec = {
        'state': {'choices': [PRESENT, ABSENT], 'default': PRESENT},
        'prefix_list': {'type': 'str', 'required': True},
        'direction': {'choices': ['in', 'out']},
    }

    area_nssa_spec = {
        'state': {'choices': [PRESENT, ABSENT], 'default': PRESENT},
        'default_information_originate': {'type': 'bool', 'default': False},
        'default_information_originate_metric_type': {
            'type': 'int',
            'choices': [1, 2],
        },
        'default_information_originate_metric': {'type': 'int'},
        'no_redistribution': {'type': 'bool', 'default': False},
        'no_summary': {'type': 'bool', 'default': False},
        'translator_role': {'type': 'bool', 'default': False},
        'translator_role_type': {'choices': ['always', 'candidate', 'never']},
    }

    area_range_spec = {
        'state': {'choices': [PRESENT, ABSENT], 'default': PRESENT},
        'ip_addr': {'type': 'str', 'required': True},
        'advertise': {'type': 'bool', 'default': None},
    }

    area_stub_spec = {
        'state': {'choices': [PRESENT, ABSENT], 'default': PRESENT},
        'no_summary': {'type': 'bool', 'default': False},
    }

    area_virtual_link_spec = {
        'state': {'choices': [PRESENT, ABSENT], 'default': PRESENT},
        'ip_addr': {'type': 'str', 'required': True},
        'auth_key': {'type': 'str'},
        'msg_key_id': {'type': 'int'},
        'msg_key_password': {'type': 'str'},
        'authentication_type': {'choices': ['message-digest', 'null']},
        'authentication': {'type': 'bool', 'default': False},
        'dead_interval': {'type': 'bool', 'default': False},
        'dead_interval_value': {'type': 'int'},
        'hello_interval': {'type': 'bool', 'default': False},
        'hello_interval_value': {'type': 'int'},
        'retransmit_interval': {'type': 'bool', 'default': False},
        'retransmit_interval_value': {'type': 'int'},
        'transmit_delay': {'type': 'bool', 'default': False},
        'transmit_delay_value': {'type': 'int'},
    }

    area_spec = {
        'state': {'choices': [PRESENT, ABSENT], 'default': PRESENT},
        'area_id': {'type': 'str', 'required': True},
        'default_cost': {'type': 'dict', 'options': area_default_cost_spec},
        'authentication': {
            'type': 'dict',
            'options': area_authentication_spec,
        },
        'filter_list': {'type': 'dict', 'options': area_filter_list_spec},
        'nssa': {'type': 'dict', 'options': area_nssa_spec},
        'range': {'type': 'dict', 'options': area_range_spec},
        'stub': {'type': 'dict', 'options': area_stub_spec},
        'virtual_link': {'type': 'dict', 'options': area_virtual_link_spec},
    }

    router_spec = {
        'state': {'choices': [PRESENT, ABSENT], 'default': PRESENT},
        'process_id': {'type': 'int'},
        'vrf_instance': {'type': 'str'},
    }

    network_area_spec = {
        'state': {'choices': [PRESENT, ABSENT], 'default': PRESENT},
        'network_address': {'type': 'str', 'required': True},
        'area_id': {'type': 'str', 'required': True},
    }

    ospf_router_id_spec = {
        'state': {'choices': [PRESENT, ABSENT], 'default': PRESENT},
        'ip_addr': {'type': 'str'},
    }

    passive_interface_spec = {
        'state': {'choices': [PRESENT, ABSENT], 'default': PRESENT},
        'name': {'type': 'str'},
        'ip_addr': {'type': 'str'},
    }

    redistribute_spec = {
        'state': {'choices': [PRESENT, ABSENT], 'default': PRESENT},
        'connected': {'type': 'bool', 'default': False},
        'static': {'type': 'bool', 'default': False},
        'metric': {'type': 'int'},
        'metric_type': {'choices': ['1', '2']},
        'route_map_name': {'type': 'str'},
        'tag': {'type': 'int'},
    }

    summary_address_spec = {
        'state': {'choices': [PRESENT, ABSENT], 'default': PRESENT},
        'ip_addr': {'type': 'str', 'required': True},
        'not_advertise': {'type': 'bool', 'default': False},
        'tag': {'type': 'int'},
    }

    argument_spec = {
        'area': {'type': 'dict', 'options': area_spec},
        'router': {'type': 'dict', 'options': router_spec, 'required': True},
        'network_area': {'type': 'dict', 'options': network_area_spec},
        'ospf_router_id': {'type': 'dict', 'options': ospf_router_id_spec},
        'passive_interface': {
            'type': 'dict',
            'options': passive_interface_spec,
        },
        'redistribute': {'type': 'dict', 'options': redistribute_spec},
        'summary_address': {'type': 'dict', 'options': summary_address_spec},
    }

    argument_spec.update(awplus_argument_spec)

    module = AnsibleModule(
        argument_spec=argument_spec, supports_check_mode=True
    )

    warnings = []
    result = {'changed': False, 'warnings': warnings}

    ospf, existing_config = get_existing_config(module)
    commands = get_commands(
        module, KEY_TO_COMMAND_MAP, router_ospf_map, ospf, existing_config
    )
    result['commands'] = commands

    if commands:
        if not module.check_mode:
            load_config(module, commands)
        result['changed'] = True

    module.exit_json(**result)


if __name__ == '__main__':
    main()
