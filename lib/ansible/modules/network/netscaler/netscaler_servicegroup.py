#!/usr/bin/python
# -*- coding: utf-8 -*-

#  Copyright (c) 2017 Citrix Systems
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: netscaler_servicegroup
short_description: Manage service group configuration in Netscaler
description:
    - Manage service group configuration in Netscaler.
    - This module is intended to run either on the ansible  control node or a bastion (jumpserver) with access to the actual netscaler instance.

version_added: "2.4"

author: George Nikolopoulos (@giorgos-nikolopoulos)

options:
    servicegroupname:
        description:
            - >-
                Name of the service group. Must begin with an ASCII alphabetic or underscore C(_) character, and must
                contain only ASCII alphanumeric, underscore C(_), hash C(#), period C(.), space C( ), colon C(:), at C(@), equals
                C(=), and hyphen C(-) characters. Can be changed after the name is created.
            - "Minimum length = 1"

    servicetype:
        choices:
            - 'HTTP'
            - 'FTP'
            - 'TCP'
            - 'UDP'
            - 'SSL'
            - 'SSL_BRIDGE'
            - 'SSL_TCP'
            - 'DTLS'
            - 'NNTP'
            - 'RPCSVR'
            - 'DNS'
            - 'ADNS'
            - 'SNMP'
            - 'RTSP'
            - 'DHCPRA'
            - 'ANY'
            - 'SIP_UDP'
            - 'SIP_TCP'
            - 'SIP_SSL'
            - 'DNS_TCP'
            - 'ADNS_TCP'
            - 'MYSQL'
            - 'MSSQL'
            - 'ORACLE'
            - 'RADIUS'
            - 'RADIUSListener'
            - 'RDP'
            - 'DIAMETER'
            - 'SSL_DIAMETER'
            - 'TFTP'
            - 'SMPP'
            - 'PPTP'
            - 'GRE'
            - 'SYSLOGTCP'
            - 'SYSLOGUDP'
            - 'FIX'
            - 'SSL_FIX'
        description:
            - "Protocol used to exchange data with the service."

    cachetype:
        choices:
            - 'TRANSPARENT'
            - 'REVERSE'
            - 'FORWARD'
        description:
            - "Cache type supported by the cache server."

    maxclient:
        description:
            - "Maximum number of simultaneous open connections for the service group."
            - "Minimum value = C(0)"
            - "Maximum value = C(4294967294)"

    maxreq:
        description:
            - "Maximum number of requests that can be sent on a persistent connection to the service group."
            - "Note: Connection requests beyond this value are rejected."
            - "Minimum value = C(0)"
            - "Maximum value = C(65535)"

    cacheable:
        description:
            - "Use the transparent cache redirection virtual server to forward the request to the cache server."
            - "Note: Do not set this parameter if you set the Cache Type."
        type: bool

    cip:
        choices:
            - 'enabled'
            - 'disabled'
        description:
            - "Insert the Client IP header in requests forwarded to the service."

    cipheader:
        description:
            - >-
                Name of the HTTP header whose value must be set to the IP address of the client. Used with the Client
                IP parameter. If client IP insertion is enabled, and the client IP header is not specified, the value
                of Client IP Header parameter or the value set by the set ns config command is used as client's IP
                header name.
            - "Minimum length = 1"

    usip:
        description:
            - >-
                Use client's IP address as the source IP address when initiating connection to the server. With the
                NO setting, which is the default, a mapped IP (MIP) address or subnet IP (SNIP) address is used as
                the source IP address to initiate server side connections.
        type: bool

    pathmonitor:
        description:
            - "Path monitoring for clustering."
        type: bool

    pathmonitorindv:
        description:
            - "Individual Path monitoring decisions."
        type: bool

    useproxyport:
        description:
            - >-
                Use the proxy port as the source port when initiating connections with the server. With the NO
                setting, the client-side connection port is used as the source port for the server-side connection.
            - "Note: This parameter is available only when the Use Source IP C(usip) parameter is set to C(yes)."
        type: bool

    healthmonitor:
        description:
            - "Monitor the health of this service. Available settings function as follows:"
            - "C(yes) - Send probes to check the health of the service."
            - >-
                C(no) - Do not send probes to check the health of the service. With the NO option, the appliance shows
                the service as UP at all times.
        type: bool

    sp:
        description:
            - "Enable surge protection for the service group."
        type: bool

    rtspsessionidremap:
        description:
            - "Enable RTSP session ID mapping for the service group."
        type: bool

    clttimeout:
        description:
            - "Time, in seconds, after which to terminate an idle client connection."
            - "Minimum value = C(0)"
            - "Maximum value = C(31536000)"

    svrtimeout:
        description:
            - "Time, in seconds, after which to terminate an idle server connection."
            - "Minimum value = C(0)"
            - "Maximum value = C(31536000)"

    cka:
        description:
            - "Enable client keep-alive for the service group."
        type: bool

    tcpb:
        description:
            - "Enable TCP buffering for the service group."
        type: bool

    cmp:
        description:
            - "Enable compression for the specified service."
        type: bool

    maxbandwidth:
        description:
            - "Maximum bandwidth, in Kbps, allocated for all the services in the service group."
            - "Minimum value = C(0)"
            - "Maximum value = C(4294967287)"

    monthreshold:
        description:
            - >-
                Minimum sum of weights of the monitors that are bound to this service. Used to determine whether to
                mark a service as UP or DOWN.
            - "Minimum value = C(0)"
            - "Maximum value = C(65535)"

    downstateflush:
        choices:
            - 'enabled'
            - 'disabled'
        description:
            - >-
                Flush all active transactions associated with all the services in the service group whose state
                transitions from UP to DOWN. Do not enable this option for applications that must complete their
                transactions.

    tcpprofilename:
        description:
            - "Name of the TCP profile that contains TCP configuration settings for the service group."
            - "Minimum length = 1"
            - "Maximum length = 127"

    httpprofilename:
        description:
            - "Name of the HTTP profile that contains HTTP configuration settings for the service group."
            - "Minimum length = 1"
            - "Maximum length = 127"

    comment:
        description:
            - "Any information about the service group."

    appflowlog:
        choices:
            - 'enabled'
            - 'disabled'
        description:
            - "Enable logging of AppFlow information for the specified service group."

    netprofile:
        description:
            - "Network profile for the service group."
            - "Minimum length = 1"
            - "Maximum length = 127"

    autoscale:
        choices:
            - 'DISABLED'
            - 'DNS'
            - 'POLICY'
        description:
            - "Auto scale option for a servicegroup."

    memberport:
        description:
            - "member port."

    graceful:
        description:
            - "Wait for all existing connections to the service to terminate before shutting down the service."
        type: bool

    servicemembers:
        description:
            - A list of dictionaries describing each service member of the service group.
        suboptions:
            ip:
                description:
                    - IP address of the service. Must not overlap with an existing server entity defined by name.

            port:
                description:
                    - Server port number.
                    - Range C(1) - C(65535)
                    - "* in CLI is represented as 65535 in NITRO API"
            state:
                choices:
                    - 'enabled'
                    - 'disabled'
                description:
                    - Initial state of the service after binding.
            hashid:
                description:
                    - The hash identifier for the service.
                    - This must be unique for each service.
                    - This parameter is used by hash based load balancing methods.
                    - Minimum value = C(1)

            serverid:
                description:
                    - The identifier for the service.
                    - This is used when the persistency type is set to Custom Server ID.

            servername:
                description:
                    - Name of the server to which to bind the service group.
                    - The server must already be configured as a named server.
                    - Minimum length = 1

            customserverid:
                description:
                    - The identifier for this IP:Port pair.
                    - Used when the persistency type is set to Custom Server ID.

            weight:
                description:
                    - Weight to assign to the servers in the service group.
                    - Specifies the capacity of the servers relative to the other servers in the load balancing configuration.
                    - The higher the weight, the higher the percentage of requests sent to the service.
                    - Minimum value = C(1)
                    - Maximum value = C(100)

    monitorbindings:
        description:
            - A list of monitornames to bind to this service
            - Note that the monitors must have already been setup possibly using the M(netscaler_lb_monitor) module or some other method
        suboptions:
            monitorname:
                description:
                    - The monitor name to bind to this servicegroup.
            weight:
                description:
                    - Weight to assign to the binding between the monitor and servicegroup.

    disabled:
        description:
            - When set to C(yes) the service group state will be set to DISABLED.
            - When set to C(no) the service group state will be set to ENABLED.
            - >-
                Note that due to limitations of the underlying NITRO API a C(disabled) state change alone
                does not cause the module result to report a changed status.
        type: bool
        default: false


extends_documentation_fragment: netscaler
requirements:
    - nitro python sdk
'''

EXAMPLES = '''
# The LB Monitors monitor-1 and monitor-2 must already exist
# Service members defined by C(ip) must not redefine an existing server's ip address.
# Service members defined by C(servername) must already exist.

- name: Setup http service with ip members
  delegate_to: localhost
  netscaler_servicegroup:
    nsip: 172.18.0.2
    nitro_user: nsroot
    nitro_pass: nsroot

    state: present

    servicegroupname: service-group-1
    servicetype: HTTP
    servicemembers:
      - ip: 10.78.78.78
        port: 80
        weight: 50
      - ip: 10.79.79.79
        port: 80
        weight: 40
      - servername: server-1
        port: 80
        weight: 10

    monitorbindings:
      - monitorname: monitor-1
        weight: 50
      - monitorname: monitor-2
        weight: 50

'''

RETURN = '''
loglines:
    description: list of logged messages by the module
    returned: always
    type: list
    sample: ['message 1', 'message 2']

msg:
    description: Message detailing the failure reason
    returned: failure
    type: str
    sample: "Action does not exist"

diff:
    description: List of differences between the actual configured object and the configuration specified in the module
    returned: failure
    type: dict
    sample: { 'clttimeout': 'difference. ours: (float) 10.0 other: (float) 20.0' }
'''

from ansible.module_utils.basic import AnsibleModule
import copy

from ansible.module_utils.network.netscaler.netscaler import ConfigProxy, get_nitro_client, netscaler_common_arguments, log, \
    loglines, get_immutables_intersection
try:
    from nssrc.com.citrix.netscaler.nitro.resource.config.basic.servicegroup import servicegroup
    from nssrc.com.citrix.netscaler.nitro.resource.config.basic.servicegroup_servicegroupmember_binding import servicegroup_servicegroupmember_binding
    from nssrc.com.citrix.netscaler.nitro.exception.nitro_exception import nitro_exception

    from nssrc.com.citrix.netscaler.nitro.resource.config.basic.servicegroup_lbmonitor_binding import servicegroup_lbmonitor_binding
    from nssrc.com.citrix.netscaler.nitro.resource.config.lb.lbmonitor_servicegroup_binding import lbmonitor_servicegroup_binding
    PYTHON_SDK_IMPORTED = True
except ImportError as e:
    PYTHON_SDK_IMPORTED = False


def servicegroup_exists(client, module):
    log('Checking if service group exists')
    count = servicegroup.count_filtered(client, 'servicegroupname:%s' % module.params['servicegroupname'])
    log('count is %s' % count)
    if count > 0:
        return True
    else:
        return False


def servicegroup_identical(client, module, servicegroup_proxy):
    log('Checking if service group is identical')
    servicegroups = servicegroup.get_filtered(client, 'servicegroupname:%s' % module.params['servicegroupname'])
    if servicegroup_proxy.has_equal_attributes(servicegroups[0]):
        return True
    else:
        return False


def get_configured_service_members(client, module):
    log('get_configured_service_members')
    readwrite_attrs = [
        'servicegroupname',
        'ip',
        'port',
        'state',
        'hashid',
        'serverid',
        'servername',
        'customserverid',
        'weight'
    ]
    readonly_attrs = [
        'delay',
        'statechangetimesec',
        'svrstate',
        'tickssincelaststatechange',
        'graceful',
    ]

    members = []
    if module.params['servicemembers'] is None:
        return members

    for config in module.params['servicemembers']:
        # Make a copy to update
        config = copy.deepcopy(config)
        config['servicegroupname'] = module.params['servicegroupname']
        member_proxy = ConfigProxy(
            actual=servicegroup_servicegroupmember_binding(),
            client=client,
            attribute_values_dict=config,
            readwrite_attrs=readwrite_attrs,
            readonly_attrs=readonly_attrs
        )
        members.append(member_proxy)
    return members


def get_actual_service_members(client, module):
    try:
        # count() raises nitro exception instead of returning 0
        count = servicegroup_servicegroupmember_binding.count(client, module.params['servicegroupname'])
        if count > 0:
            servicegroup_members = servicegroup_servicegroupmember_binding.get(client, module.params['servicegroupname'])
        else:
            servicegroup_members = []
    except nitro_exception as e:
        if e.errorcode == 258:
            servicegroup_members = []
        else:
            raise
    return servicegroup_members


def servicemembers_identical(client, module):
    log('servicemembers_identical')

    servicegroup_members = get_actual_service_members(client, module)
    log('servicemembers %s' % servicegroup_members)
    module_servicegroups = get_configured_service_members(client, module)
    log('Number of service group members %s' % len(servicegroup_members))
    if len(servicegroup_members) != len(module_servicegroups):
        return False

    # Fallthrough to member evaluation
    identical_count = 0
    for actual_member in servicegroup_members:
        for member in module_servicegroups:
            if member.has_equal_attributes(actual_member):
                identical_count += 1
                break
    if identical_count != len(servicegroup_members):
        return False

    # Fallthrough to success
    return True


def sync_service_members(client, module):
    log('sync_service_members')
    configured_service_members = get_configured_service_members(client, module)
    actual_service_members = get_actual_service_members(client, module)
    skip_add = []
    skip_delete = []

    # Find positions of identical service members
    for (configured_index, configured_service) in enumerate(configured_service_members):
        for (actual_index, actual_service) in enumerate(actual_service_members):
            if configured_service.has_equal_attributes(actual_service):
                skip_add.append(configured_index)
                skip_delete.append(actual_index)

    # Delete actual that are not identical to any configured
    for (actual_index, actual_service) in enumerate(actual_service_members):
        # Skip identical
        if actual_index in skip_delete:
            log('Skipping actual delete at index %s' % actual_index)
            continue

        # Fallthrouth to deletion
        if all([
            hasattr(actual_service, 'ip'),
            actual_service.ip is not None,
            hasattr(actual_service, 'servername'),
            actual_service.servername is not None,
        ]):
            actual_service.ip = None

        actual_service.servicegroupname = module.params['servicegroupname']
        servicegroup_servicegroupmember_binding.delete(client, actual_service)

    # Add configured that are not already present in actual
    for (configured_index, configured_service) in enumerate(configured_service_members):

        # Skip identical
        if configured_index in skip_add:
            log('Skipping configured add at index %s' % configured_index)
            continue

        # Fallthrough to addition
        configured_service.add()


def monitor_binding_equal(configured, actual):
    if any([configured.monitorname != actual.monitor_name,
            configured.servicegroupname != actual.servicegroupname,
            configured.weight != float(actual.weight)]):
        return False
    return True


def get_configured_monitor_bindings(client, module):
    log('Entering get_configured_monitor_bindings')
    bindings = {}
    if 'monitorbindings' in module.params and module.params['monitorbindings'] is not None:
        for binding in module.params['monitorbindings']:
            readwrite_attrs = [
                'monitorname',
                'servicegroupname',
                'weight',
            ]
            readonly_attrs = []
            attribute_values_dict = copy.deepcopy(binding)
            attribute_values_dict['servicegroupname'] = module.params['servicegroupname']
            binding_proxy = ConfigProxy(
                actual=lbmonitor_servicegroup_binding(),
                client=client,
                attribute_values_dict=attribute_values_dict,
                readwrite_attrs=readwrite_attrs,
                readonly_attrs=readonly_attrs,
            )
            key = attribute_values_dict['monitorname']
            bindings[key] = binding_proxy
    return bindings


def get_actual_monitor_bindings(client, module):
    log('Entering get_actual_monitor_bindings')
    bindings = {}
    try:
        # count() raises nitro exception instead of returning 0
        count = servicegroup_lbmonitor_binding.count(client, module.params['servicegroupname'])
    except nitro_exception as e:
        if e.errorcode == 258:
            return bindings
        else:
            raise

    if count == 0:
        return bindings

    # Fallthrough to rest of execution
    for binding in servicegroup_lbmonitor_binding.get(client, module.params['servicegroupname']):
        log('Gettign actual monitor with name %s' % binding.monitor_name)
        key = binding.monitor_name
        bindings[key] = binding

    return bindings


def monitor_bindings_identical(client, module):
    log('Entering monitor_bindings_identical')
    configured_bindings = get_configured_monitor_bindings(client, module)
    actual_bindings = get_actual_monitor_bindings(client, module)

    configured_key_set = set(configured_bindings.keys())
    actual_key_set = set(actual_bindings.keys())
    symmetrical_diff = configured_key_set ^ actual_key_set
    for default_monitor in ('tcp-default', 'ping-default'):
        if default_monitor in symmetrical_diff:
            log('Excluding %s monitor from key comparison' % default_monitor)
            symmetrical_diff.remove(default_monitor)
    if len(symmetrical_diff) > 0:
        return False

    # Compare key to key
    for key in configured_key_set:
        configured_proxy = configured_bindings[key]

        # Follow nscli convention for missing weight value
        if not hasattr(configured_proxy, 'weight'):
            configured_proxy.weight = 1
        log('configured_proxy %s' % [configured_proxy.monitorname, configured_proxy.servicegroupname, configured_proxy.weight])
        log('actual_bindings %s' % [actual_bindings[key].monitor_name, actual_bindings[key].servicegroupname, actual_bindings[key].weight])
        if not monitor_binding_equal(configured_proxy, actual_bindings[key]):
            return False

    # Fallthrought to success
    return True


def sync_monitor_bindings(client, module):
    log('Entering sync_monitor_bindings')

    actual_bindings = get_actual_monitor_bindings(client, module)

    # Exclude default monitors from deletion
    for monitorname in ('tcp-default', 'ping-default'):
        if monitorname in actual_bindings:
            del actual_bindings[monitorname]

    configured_bindings = get_configured_monitor_bindings(client, module)

    to_remove = list(set(actual_bindings.keys()) - set(configured_bindings.keys()))
    to_add = list(set(configured_bindings.keys()) - set(actual_bindings.keys()))
    to_modify = list(set(configured_bindings.keys()) & set(actual_bindings.keys()))

    # Delete existing and modifiable bindings
    for key in to_remove + to_modify:
        binding = actual_bindings[key]
        b = lbmonitor_servicegroup_binding()
        b.monitorname = binding.monitor_name
        b.servicegroupname = module.params['servicegroupname']
        # Cannot remove default monitor bindings
        if b.monitorname in ('tcp-default', 'ping-default'):
            continue
        lbmonitor_servicegroup_binding.delete(client, b)

    # Add new and modified bindings
    for key in to_add + to_modify:
        binding = configured_bindings[key]
        log('Adding %s' % binding.monitorname)
        binding.add()


def diff(client, module, servicegroup_proxy):
    servicegroup_list = servicegroup.get_filtered(client, 'servicegroupname:%s' % module.params['servicegroupname'])
    diff_object = servicegroup_proxy.diff_object(servicegroup_list[0])
    return diff_object


def do_state_change(client, module, servicegroup_proxy):
    if module.params['disabled']:
        log('Disabling service')
        result = servicegroup.disable(client, servicegroup_proxy.actual)
    else:
        log('Enabling service')
        result = servicegroup.enable(client, servicegroup_proxy.actual)
    return result


def main():

    module_specific_arguments = dict(
        servicegroupname=dict(type='str'),
        servicetype=dict(
            type='str',
            choices=[
                'HTTP',
                'FTP',
                'TCP',
                'UDP',
                'SSL',
                'SSL_BRIDGE',
                'SSL_TCP',
                'DTLS',
                'NNTP',
                'RPCSVR',
                'DNS',
                'ADNS',
                'SNMP',
                'RTSP',
                'DHCPRA',
                'ANY',
                'SIP_UDP',
                'SIP_TCP',
                'SIP_SSL',
                'DNS_TCP',
                'ADNS_TCP',
                'MYSQL',
                'MSSQL',
                'ORACLE',
                'RADIUS',
                'RADIUSListener',
                'RDP',
                'DIAMETER',
                'SSL_DIAMETER',
                'TFTP',
                'SMPP',
                'PPTP',
                'GRE',
                'SYSLOGTCP',
                'SYSLOGUDP',
                'FIX',
                'SSL_FIX',
            ]
        ),
        cachetype=dict(
            type='str',
            choices=[
                'TRANSPARENT',
                'REVERSE',
                'FORWARD',
            ]
        ),
        maxclient=dict(type='float'),
        maxreq=dict(type='float'),
        cacheable=dict(type='bool'),
        cip=dict(
            type='str',
            choices=[
                'enabled',
                'disabled',
            ]
        ),
        cipheader=dict(type='str'),
        usip=dict(type='bool'),
        pathmonitor=dict(type='bool'),
        pathmonitorindv=dict(type='bool'),
        useproxyport=dict(type='bool'),
        healthmonitor=dict(type='bool'),
        sp=dict(type='bool'),
        rtspsessionidremap=dict(type='bool'),
        clttimeout=dict(type='float'),
        svrtimeout=dict(type='float'),
        cka=dict(type='bool'),
        tcpb=dict(type='bool'),
        cmp=dict(type='bool'),
        maxbandwidth=dict(type='float'),
        monthreshold=dict(type='float'),
        downstateflush=dict(
            type='str',
            choices=[
                'enabled',
                'disabled',
            ]
        ),
        tcpprofilename=dict(type='str'),
        httpprofilename=dict(type='str'),
        comment=dict(type='str'),
        appflowlog=dict(
            type='str',
            choices=[
                'enabled',
                'disabled',
            ]
        ),
        netprofile=dict(type='str'),
        autoscale=dict(
            type='str',
            choices=[
                'DISABLED',
                'DNS',
                'POLICY',
            ]
        ),
        memberport=dict(type='int'),
        graceful=dict(type='bool'),
    )

    hand_inserted_arguments = dict(
        servicemembers=dict(type='list'),
        monitorbindings=dict(type='list'),
        disabled=dict(
            type='bool',
            default=False,
        ),
    )

    argument_spec = dict()

    argument_spec.update(netscaler_common_arguments)
    argument_spec.update(module_specific_arguments)
    argument_spec.update(hand_inserted_arguments)

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )
    module_result = dict(
        changed=False,
        failed=False,
        loglines=loglines,
    )

    # Fail the module if imports failed
    if not PYTHON_SDK_IMPORTED:
        module.fail_json(msg='Could not load nitro python sdk')

    # Fallthrough to rest of execution
    client = get_nitro_client(module)

    try:
        client.login()
    except nitro_exception as e:
        msg = "nitro exception during login. errorcode=%s, message=%s" % (str(e.errorcode), e.message)
        module.fail_json(msg=msg)
    except Exception as e:
        if str(type(e)) == "<class 'requests.exceptions.ConnectionError'>":
            module.fail_json(msg='Connection error %s' % str(e))
        elif str(type(e)) == "<class 'requests.exceptions.SSLError'>":
            module.fail_json(msg='SSL Error %s' % str(e))
        else:
            module.fail_json(msg='Unexpected error during login %s' % str(e))

    # Instantiate service group configuration object
    readwrite_attrs = [
        'servicegroupname',
        'servicetype',
        'cachetype',
        'maxclient',
        'maxreq',
        'cacheable',
        'cip',
        'cipheader',
        'usip',
        'pathmonitor',
        'pathmonitorindv',
        'useproxyport',
        'healthmonitor',
        'sp',
        'rtspsessionidremap',
        'clttimeout',
        'svrtimeout',
        'cka',
        'tcpb',
        'cmp',
        'maxbandwidth',
        'monthreshold',
        'downstateflush',
        'tcpprofilename',
        'httpprofilename',
        'comment',
        'appflowlog',
        'netprofile',
        'autoscale',
        'memberport',
        'graceful',
    ]

    readonly_attrs = [
        'numofconnections',
        'serviceconftype',
        'value',
        'svrstate',
        'ip',
        'monstatcode',
        'monstatparam1',
        'monstatparam2',
        'monstatparam3',
        'statechangetimemsec',
        'stateupdatereason',
        'clmonowner',
        'clmonview',
        'groupcount',
        'riseapbrstatsmsgcode2',
        'serviceipstr',
        'servicegroupeffectivestate'
    ]

    immutable_attrs = [
        'servicegroupname',
        'servicetype',
        'cachetype',
        'td',
        'cipheader',
        'state',
        'autoscale',
        'memberport',
        'servername',
        'port',
        'serverid',
        'monitor_name_svc',
        'dup_weight',
        'riseapbrstatsmsgcode',
        'delay',
        'graceful',
        'includemembers',
        'newname',
    ]

    transforms = {
        'pathmonitorindv': ['bool_yes_no'],
        'cacheable': ['bool_yes_no'],
        'cka': ['bool_yes_no'],
        'pathmonitor': ['bool_yes_no'],
        'tcpb': ['bool_yes_no'],
        'sp': ['bool_on_off'],
        'usip': ['bool_yes_no'],
        'healthmonitor': ['bool_yes_no'],
        'useproxyport': ['bool_yes_no'],
        'rtspsessionidremap': ['bool_on_off'],
        'graceful': ['bool_yes_no'],
        'cmp': ['bool_yes_no'],
        'cip': [lambda v: v.upper()],
        'downstateflush': [lambda v: v.upper()],
        'appflowlog': [lambda v: v.upper()],
    }

    # Instantiate config proxy
    servicegroup_proxy = ConfigProxy(
        actual=servicegroup(),
        client=client,
        attribute_values_dict=module.params,
        readwrite_attrs=readwrite_attrs,
        readonly_attrs=readonly_attrs,
        immutable_attrs=immutable_attrs,
        transforms=transforms,
    )

    try:
        if module.params['state'] == 'present':
            log('Applying actions for state present')
            if not servicegroup_exists(client, module):
                if not module.check_mode:
                    log('Adding service group')
                    servicegroup_proxy.add()
                    if module.params['save_config']:
                        client.save_config()
                module_result['changed'] = True
            elif not servicegroup_identical(client, module, servicegroup_proxy):

                # Check if we try to change value of immutable attributes
                diff_dict = diff(client, module, servicegroup_proxy)
                immutables_changed = get_immutables_intersection(servicegroup_proxy, diff_dict.keys())
                if immutables_changed != []:
                    msg = 'Cannot update immutable attributes %s. Must delete and recreate entity.' % (immutables_changed,)
                    module.fail_json(msg=msg, diff=diff_dict, **module_result)

                if not module.check_mode:
                    servicegroup_proxy.update()
                    if module.params['save_config']:
                        client.save_config()
                module_result['changed'] = True
            else:
                module_result['changed'] = False

            # Check bindings
            if not monitor_bindings_identical(client, module):
                if not module.check_mode:
                    sync_monitor_bindings(client, module)
                    if module.params['save_config']:
                        client.save_config()
                module_result['changed'] = True

            if not servicemembers_identical(client, module):
                if not module.check_mode:
                    sync_service_members(client, module)
                    if module.params['save_config']:
                        client.save_config()
                module_result['changed'] = True

            if not module.check_mode:
                res = do_state_change(client, module, servicegroup_proxy)
                if res.errorcode != 0:
                    msg = 'Error when setting disabled state. errorcode: %s message: %s' % (res.errorcode, res.message)
                    module.fail_json(msg=msg, **module_result)

            # Sanity check for state
            if not module.check_mode:
                log('Sanity checks for state present')
                if not servicegroup_exists(client, module):
                    module.fail_json(msg='Service group is not present', **module_result)
                if not servicegroup_identical(client, module, servicegroup_proxy):
                    module.fail_json(
                        msg='Service group is not identical to configuration',
                        diff=diff(client, module, servicegroup_proxy),
                        **module_result
                    )
                if not servicemembers_identical(client, module):
                    module.fail_json(msg='Service group members differ from configuration', **module_result)
                if not monitor_bindings_identical(client, module):
                    module.fail_json(msg='Monitor bindings are not identical', **module_result)

        elif module.params['state'] == 'absent':
            log('Applying actions for state absent')
            if servicegroup_exists(client, module):
                if not module.check_mode:
                    servicegroup_proxy.delete()
                    if module.params['save_config']:
                        client.save_config()
                module_result['changed'] = True
            else:
                module_result['changed'] = False

            # Sanity check for state
            if not module.check_mode:
                log('Sanity checks for state absent')
                if servicegroup_exists(client, module):
                    module.fail_json(msg='Service group is present', **module_result)

    except nitro_exception as e:
        msg = "nitro exception errorcode=" + str(e.errorcode) + ",message=" + e.message
        module.fail_json(msg=msg, **module_result)

    client.logout()
    module.exit_json(**module_result)


if __name__ == "__main__":
    main()
