#!/usr/bin/python
# -*- coding: utf-8 -*-

#  Copyright (c) 2017 Citrix Systems
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: netscaler_service
short_description: Manage service configuration in Netscaler
description:
    - Manage service configuration in Netscaler.
    - This module allows the creation, deletion and modification of Netscaler services.
    - This module is intended to run either on the ansible  control node or a bastion (jumpserver) with access to the actual netscaler instance.
    - This module supports check mode.

version_added: "2.4.0"

author: George Nikolopoulos (@giorgos-nikolopoulos)

options:

    name:
        description:
            - >-
                Name for the service. Must begin with an ASCII alphabetic or underscore C(_) character, and must
                contain only ASCII alphanumeric, underscore C(_), hash C(#), period C(.), space C( ), colon C(:), at C(@), equals
                C(=), and hyphen C(-) characters. Cannot be changed after the service has been created.
            - "Minimum length = 1"

    ip:
        description:
            - "IP to assign to the service."
            - "Minimum length = 1"

    servername:
        description:
            - "Name of the server that hosts the service."
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
            - "Protocol in which data is exchanged with the service."

    port:
        description:
            - "Port number of the service."
            - "Range 1 - 65535"
            - "* in CLI is represented as 65535 in NITRO API"

    cleartextport:
        description:
            - >-
                Port to which clear text data must be sent after the appliance decrypts incoming SSL traffic.
                Applicable to transparent SSL services.
            - "Minimum value = 1"

    cachetype:
        choices:
            - 'TRANSPARENT'
            - 'REVERSE'
            - 'FORWARD'
        description:
            - "Cache type supported by the cache server."

    maxclient:
        description:
            - "Maximum number of simultaneous open connections to the service."
            - "Minimum value = 0"
            - "Maximum value = 4294967294"

    healthmonitor:
        description:
            - "Monitor the health of this service"
        default: yes

    maxreq:
        description:
            - "Maximum number of requests that can be sent on a persistent connection to the service."
            - "Note: Connection requests beyond this value are rejected."
            - "Minimum value = 0"
            - "Maximum value = 65535"

    cacheable:
        description:
            - "Use the transparent cache redirection virtual server to forward requests to the cache server."
            - "Note: Do not specify this parameter if you set the Cache Type parameter."
        default: no

    cip:
        choices:
            - 'ENABLED'
            - 'DISABLED'
        description:
            - >-
                Before forwarding a request to the service, insert an HTTP header with the client's IPv4 or IPv6
                address as its value. Used if the server needs the client's IP address for security, accounting, or
                other purposes, and setting the Use Source IP parameter is not a viable option.

    cipheader:
        description:
            - >-
                Name for the HTTP header whose value must be set to the IP address of the client. Used with the
                Client IP parameter. If you set the Client IP parameter, and you do not specify a name for the
                header, the appliance uses the header name specified for the global Client IP Header parameter (the
                cipHeader parameter in the set ns param CLI command or the Client IP Header parameter in the
                Configure HTTP Parameters dialog box at System > Settings > Change HTTP parameters). If the global
                Client IP Header parameter is not specified, the appliance inserts a header with the name
                "client-ip.".
            - "Minimum length = 1"

    usip:
        description:
            - >-
                Use the client's IP address as the source IP address when initiating a connection to the server. When
                creating a service, if you do not set this parameter, the service inherits the global Use Source IP
                setting (available in the enable ns mode and disable ns mode CLI commands, or in the System >
                Settings > Configure modes > Configure Modes dialog box). However, you can override this setting
                after you create the service.

    pathmonitor:
        description:
            - "Path monitoring for clustering."

    pathmonitorindv:
        description:
            - "Individual Path monitoring decisions."

    useproxyport:
        description:
            - >-
                Use the proxy port as the source port when initiating connections with the server. With the NO
                setting, the client-side connection port is used as the source port for the server-side connection.
            - "Note: This parameter is available only when the Use Source IP (USIP) parameter is set to YES."

    sc:
        description:
            - "State of SureConnect for the service."
        default: off

    sp:
        description:
            - "Enable surge protection for the service."

    rtspsessionidremap:
        description:
            - "Enable RTSP session ID mapping for the service."
        default: off

    clttimeout:
        description:
            - "Time, in seconds, after which to terminate an idle client connection."
            - "Minimum value = 0"
            - "Maximum value = 31536000"

    svrtimeout:
        description:
            - "Time, in seconds, after which to terminate an idle server connection."
            - "Minimum value = 0"
            - "Maximum value = 31536000"

    customserverid:
        description:
            - >-
                Unique identifier for the service. Used when the persistency type for the virtual server is set to
                Custom Server ID.
        default: 'None'

    serverid:
        description:
            - "The identifier for the service. This is used when the persistency type is set to Custom Server ID."

    cka:
        description:
            - "Enable client keep-alive for the service."

    tcpb:
        description:
            - "Enable TCP buffering for the service."

    cmp:
        description:
            - "Enable compression for the service."

    maxbandwidth:
        description:
            - "Maximum bandwidth, in Kbps, allocated to the service."
            - "Minimum value = 0"
            - "Maximum value = 4294967287"

    accessdown:
        description:
            - >-
                Use Layer 2 mode to bridge the packets sent to this service if it is marked as DOWN. If the service
                is DOWN, and this parameter is disabled, the packets are dropped.
        default: no

    monthreshold:
        description:
            - >-
                Minimum sum of weights of the monitors that are bound to this service. Used to determine whether to
                mark a service as UP or DOWN.
            - "Minimum value = 0"
            - "Maximum value = 65535"

    downstateflush:
        choices:
            - 'ENABLED'
            - 'DISABLED'
        description:
            - >-
                Flush all active transactions associated with a service whose state transitions from UP to DOWN. Do
                not enable this option for applications that must complete their transactions.
        default: ENABLED

    tcpprofilename:
        description:
            - "Name of the TCP profile that contains TCP configuration settings for the service."
            - "Minimum length = 1"
            - "Maximum length = 127"

    httpprofilename:
        description:
            - "Name of the HTTP profile that contains HTTP configuration settings for the service."
            - "Minimum length = 1"
            - "Maximum length = 127"

    hashid:
        description:
            - >-
                A numerical identifier that can be used by hash based load balancing methods. Must be unique for each
                service.
            - "Minimum value = 1"

    comment:
        description:
            - "Any information about the service."

    appflowlog:
        choices:
            - 'ENABLED'
            - 'DISABLED'
        description:
            - "Enable logging of AppFlow information."
        default: ENABLED

    netprofile:
        description:
            - "Network profile to use for the service."
            - "Minimum length = 1"
            - "Maximum length = 127"

    td:
        description:
            - >-
                Integer value that uniquely identifies the traffic domain in which you want to configure the entity.
                If you do not specify an ID, the entity becomes part of the default traffic domain, which has an ID
                of 0.
            - "Minimum value = 0"
            - "Maximum value = 4094"

    processlocal:
        choices:
            - 'ENABLED'
            - 'DISABLED'
        description:
            - >-
                By turning on this option packets destined to a service in a cluster will not under go any steering.
                Turn this option for single packet request response mode or when the upstream device is performing a
                proper RSS for connection based distribution.
        default: DISABLED

    dnsprofilename:
        description:
            - >-
                Name of the DNS profile to be associated with the service. DNS profile properties will applied to the
                transactions processed by a service. This parameter is valid only for ADNS and ADNS-TCP services.
            - "Minimum length = 1"
            - "Maximum length = 127"

    ipaddress:
        description:
            - "The new IP address of the service."

    graceful:
        description:
            - >-
                Shut down gracefully, not accepting any new connections, and disabling the service when all of its
                connections are closed.
        default: no

    monitor_bindings:
        description:
            - A list of load balancing monitors to bind to this service.
            - Each monitor entry is a dictionary which may contain the following options.
            - Note that if not using the built in monitors they must first be setup.
        suboptions:
            monitorname:
                description:
                    - Name of the monitor.
            weight:
                description:
                    - Weight to assign to the binding between the monitor and service.
            dup_state:
                choices:
                    - 'ENABLED'
                    - 'DISABLED'
                description:
                    - State of the monitor.
                    - The state setting for a monitor of a given type affects all monitors of that type.
                    - For example, if an HTTP monitor is enabled, all HTTP monitors on the appliance are (or remain) enabled.
                    - If an HTTP monitor is disabled, all HTTP monitors on the appliance are disabled.
            dup_weight:
                description:
                    - Weight to assign to the binding between the monitor and service.

extends_documentation_fragment: netscaler
requirements:
    - nitro python sdk
'''

EXAMPLES = '''
# Monitor monitor-1 must have been already setup

- name: Setup http service
  gather_facts: False
  delegate_to: localhost
  netscaler_service:
    nsip: 172.18.0.2
    nitro_user: nsroot
    nitro_pass: nsroot

    state: present

    name: service-http-1
    servicetype: HTTP
    ipaddress: 10.78.0.1
    port: 80

    monitor_bindings:
      - monitor-1
'''

RETURN = '''
loglines:
    description: list of logged messages by the module
    returned: always
    type: list
    sample: "['message 1', 'message 2']"

diff:
    description: A dictionary with a list of differences between the actual configured object and the configuration specified in the module
    returned: failure
    type: dict
    sample: "{ 'clttimeout': 'difference. ours: (float) 10.0 other: (float) 20.0' }"
'''

import copy

try:
    from nssrc.com.citrix.netscaler.nitro.resource.config.basic.service import service
    from nssrc.com.citrix.netscaler.nitro.resource.config.basic.service_lbmonitor_binding import service_lbmonitor_binding
    from nssrc.com.citrix.netscaler.nitro.resource.config.lb.lbmonitor_service_binding import lbmonitor_service_binding
    from nssrc.com.citrix.netscaler.nitro.exception.nitro_exception import nitro_exception
    PYTHON_SDK_IMPORTED = True
except ImportError as e:
    PYTHON_SDK_IMPORTED = False

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.netscaler import (ConfigProxy, get_nitro_client, netscaler_common_arguments,
                                            log, loglines, get_immutables_intersection)


def service_exists(client, module):
    if service.count_filtered(client, 'name:%s' % module.params['name']) > 0:
        return True
    else:
        return False


def service_identical(client, module, service_proxy):
    service_list = service.get_filtered(client, 'name:%s' % module.params['name'])
    diff_dict = service_proxy.diff_object(service_list[0])
    # the actual ip address is stored in the ipaddress attribute
    # of the retrieved object
    if 'ip' in diff_dict:
        del diff_dict['ip']
    if len(diff_dict) == 0:
        return True
    else:
        return False


def diff(client, module, service_proxy):
    service_list = service.get_filtered(client, 'name:%s' % module.params['name'])
    diff_object = service_proxy.diff_object(service_list[0])
    if 'ip' in diff_object:
        del diff_object['ip']
    return diff_object


def get_configured_monitor_bindings(client, module, monitor_bindings_rw_attrs):
    bindings = {}
    if module.params['monitor_bindings'] is not None:
        for binding in module.params['monitor_bindings']:
            attribute_values_dict = copy.deepcopy(binding)
            # attribute_values_dict['servicename'] = module.params['name']
            attribute_values_dict['servicegroupname'] = module.params['name']
            binding_proxy = ConfigProxy(
                actual=lbmonitor_service_binding(),
                client=client,
                attribute_values_dict=attribute_values_dict,
                readwrite_attrs=monitor_bindings_rw_attrs,
            )
            key = binding_proxy.monitorname
            bindings[key] = binding_proxy
    return bindings


def get_actual_monitor_bindings(client, module):
    bindings = {}
    if service_lbmonitor_binding.count(client, module.params['name']) == 0:
        return bindings

    # Fallthrough to rest of execution
    for binding in service_lbmonitor_binding.get(client, module.params['name']):
        # Excluding default monitors since we cannot operate on them
        if binding.monitor_name in ('tcp-default', 'ping-default'):
            continue
        key = binding.monitor_name
        actual = lbmonitor_service_binding()
        actual.weight = binding.weight
        actual.monitorname = binding.monitor_name
        actual.dup_weight = binding.dup_weight
        actual.servicename = module.params['name']
        bindings[key] = actual

    return bindings


def monitor_bindings_identical(client, module, monitor_bindings_rw_attrs):
    configured_proxys = get_configured_monitor_bindings(client, module, monitor_bindings_rw_attrs)
    actual_bindings = get_actual_monitor_bindings(client, module)

    configured_key_set = set(configured_proxys.keys())
    actual_key_set = set(actual_bindings.keys())
    symmetrical_diff = configured_key_set ^ actual_key_set
    if len(symmetrical_diff) > 0:
        return False

    # Compare key to key
    for monitor_name in configured_key_set:
        proxy = configured_proxys[monitor_name]
        actual = actual_bindings[monitor_name]
        diff_dict = proxy.diff_object(actual)
        if 'servicegroupname' in diff_dict:
            if proxy.servicegroupname == actual.servicename:
                del diff_dict['servicegroupname']
        if len(diff_dict) > 0:
            return False

    # Fallthrought to success
    return True


def sync_monitor_bindings(client, module, monitor_bindings_rw_attrs):
    configured_proxys = get_configured_monitor_bindings(client, module, monitor_bindings_rw_attrs)
    actual_bindings = get_actual_monitor_bindings(client, module)
    configured_keyset = set(configured_proxys.keys())
    actual_keyset = set(actual_bindings.keys())

    # Delete extra
    delete_keys = list(actual_keyset - configured_keyset)
    for monitor_name in delete_keys:
        log('Deleting binding for monitor %s' % monitor_name)
        lbmonitor_service_binding.delete(client, actual_bindings[monitor_name])

    # Delete and re-add modified
    common_keyset = list(configured_keyset & actual_keyset)
    for monitor_name in common_keyset:
        proxy = configured_proxys[monitor_name]
        actual = actual_bindings[monitor_name]
        if not proxy.has_equal_attributes(actual):
            log('Deleting and re adding binding for monitor %s' % monitor_name)
            lbmonitor_service_binding.delete(client, actual)
            proxy.add()

    # Add new
    new_keys = list(configured_keyset - actual_keyset)
    for monitor_name in new_keys:
        log('Adding binding for monitor %s' % monitor_name)
        configured_proxys[monitor_name].add()


def all_identical(client, module, service_proxy, monitor_bindings_rw_attrs):
    return service_identical(client, module, service_proxy) and monitor_bindings_identical(client, module, monitor_bindings_rw_attrs)


def main():

    module_specific_arguments = dict(
        name=dict(type='str'),
        ip=dict(type='str'),
        servername=dict(type='str'),
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
                'SSL_FIX'
            ]
        ),
        port=dict(type='int'),
        cleartextport=dict(type='int'),
        cachetype=dict(
            type='str',
            choices=[
                'TRANSPARENT',
                'REVERSE',
                'FORWARD',
            ]
        ),
        maxclient=dict(type='float'),
        healthmonitor=dict(
            type='bool',
            default=True,
        ),
        maxreq=dict(type='float'),
        cacheable=dict(
            type='bool',
            default=False,
        ),
        cip=dict(
            type='str',
            choices=[
                'ENABLED',
                'DISABLED',
            ]
        ),
        cipheader=dict(type='str'),
        usip=dict(type='bool'),
        useproxyport=dict(type='bool'),
        sc=dict(
            type='bool',
            default=False,
        ),
        sp=dict(type='bool'),
        rtspsessionidremap=dict(
            type='bool',
            default=False,
        ),
        clttimeout=dict(type='float'),
        svrtimeout=dict(type='float'),
        customserverid=dict(
            type='str',
            default='None',
        ),
        cka=dict(type='bool'),
        tcpb=dict(type='bool'),
        cmp=dict(type='bool'),
        maxbandwidth=dict(type='float'),
        accessdown=dict(
            type='bool',
            default=False
        ),
        monthreshold=dict(type='float'),
        downstateflush=dict(
            type='str',
            choices=[
                'ENABLED',
                'DISABLED',
            ],
            default='ENABLED',
        ),
        tcpprofilename=dict(type='str'),
        httpprofilename=dict(type='str'),
        hashid=dict(type='float'),
        comment=dict(type='str'),
        appflowlog=dict(
            type='str',
            choices=[
                'ENABLED',
                'DISABLED',
            ],
            default='ENABLED',
        ),
        netprofile=dict(type='str'),
        processlocal=dict(
            type='str',
            choices=[
                'ENABLED',
                'DISABLED',
            ],
            default='DISABLED',
        ),
        dnsprofilename=dict(type='str'),
        ipaddress=dict(type='str'),
        graceful=dict(
            type='bool',
            default=False,
        ),
    )

    hand_inserted_arguments = dict(
        monitor_bindings=dict(type='list'),
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

    # Fallthrough to rest of execution

    # Instantiate Service Config object
    readwrite_attrs = [
        'name',
        'ip',
        'servername',
        'servicetype',
        'port',
        'cleartextport',
        'cachetype',
        'maxclient',
        'healthmonitor',
        'maxreq',
        'cacheable',
        'cip',
        'cipheader',
        'usip',
        'useproxyport',
        'sc',
        'sp',
        'rtspsessionidremap',
        'clttimeout',
        'svrtimeout',
        'customserverid',
        'cka',
        'tcpb',
        'cmp',
        'maxbandwidth',
        'accessdown',
        'monthreshold',
        'downstateflush',
        'tcpprofilename',
        'httpprofilename',
        'hashid',
        'comment',
        'appflowlog',
        'netprofile',
        'processlocal',
        'dnsprofilename',
        'ipaddress',
        'graceful',
    ]

    readonly_attrs = [
        'numofconnections',
        'policyname',
        'serviceconftype',
        'serviceconftype2',
        'value',
        'gslb',
        'dup_state',
        'publicip',
        'publicport',
        'svrstate',
        'monitor_state',
        'monstatcode',
        'lastresponse',
        'responsetime',
        'riseapbrstatsmsgcode2',
        'monstatparam1',
        'monstatparam2',
        'monstatparam3',
        'statechangetimesec',
        'statechangetimemsec',
        'tickssincelaststatechange',
        'stateupdatereason',
        'clmonowner',
        'clmonview',
        'serviceipstr',
        'oracleserverversion',
    ]

    immutable_attrs = [
        'name',
        'ip',
        'servername',
        'servicetype',
        'port',
        'cleartextport',
        'cachetype',
        'cipheader',
        'serverid',
        'state',
        'td',
        'monitor_name_svc',
        'riseapbrstatsmsgcode',
        'graceful',
        'all',
        'Internal',
        'newname',
    ]

    transforms = {
        'pathmonitorindv': ['bool_yes_no'],
        'cacheable': ['bool_yes_no'],
        'cka': ['bool_yes_no'],
        'pathmonitor': ['bool_yes_no'],
        'tcpb': ['bool_yes_no'],
        'sp': ['bool_on_off'],
        'graceful': ['bool_yes_no'],
        'usip': ['bool_yes_no'],
        'healthmonitor': ['bool_yes_no'],
        'useproxyport': ['bool_yes_no'],
        'rtspsessionidremap': ['bool_on_off'],
        'sc': ['bool_on_off'],
        'accessdown': ['bool_yes_no'],
        'cmp': ['bool_yes_no'],
    }

    monitor_bindings_rw_attrs = [
        'servicename',
        'servicegroupname',
        'dup_state',
        'dup_weight',
        'monitorname',
        'weight',
    ]

    # Translate module arguments to correspondign config oject attributes
    if module.params['ip'] is None:
        module.params['ip'] = module.params['ipaddress']

    service_proxy = ConfigProxy(
        actual=service(),
        client=client,
        attribute_values_dict=module.params,
        readwrite_attrs=readwrite_attrs,
        readonly_attrs=readonly_attrs,
        immutable_attrs=immutable_attrs,
        transforms=transforms,
    )

    try:

        # Apply appropriate state
        if module.params['state'] == 'present':
            log('Applying actions for state present')
            if not service_exists(client, module):
                if not module.check_mode:
                    service_proxy.add()
                    sync_monitor_bindings(client, module, monitor_bindings_rw_attrs)
                    if module.params['save_config']:
                        client.save_config()
                module_result['changed'] = True
            elif not all_identical(client, module, service_proxy, monitor_bindings_rw_attrs):

                # Check if we try to change value of immutable attributes
                diff_dict = diff(client, module, service_proxy)
                immutables_changed = get_immutables_intersection(service_proxy, diff_dict.keys())
                if immutables_changed != []:
                    msg = 'Cannot update immutable attributes %s. Must delete and recreate entity.' % (immutables_changed,)
                    module.fail_json(msg=msg, diff=diff_dict, **module_result)

                # Service sync
                if not service_identical(client, module, service_proxy):
                    if not module.check_mode:
                        service_proxy.update()

                # Monitor bindings sync
                if not monitor_bindings_identical(client, module, monitor_bindings_rw_attrs):
                    if not module.check_mode:
                        sync_monitor_bindings(client, module, monitor_bindings_rw_attrs)

                module_result['changed'] = True
                if not module.check_mode:
                    if module.params['save_config']:
                        client.save_config()
            else:
                module_result['changed'] = False

            # Sanity check for state
            if not module.check_mode:
                log('Sanity checks for state present')
                if not service_exists(client, module):
                    module.fail_json(msg='Service does not exist', **module_result)

                if not service_identical(client, module, service_proxy):
                    module.fail_json(msg='Service differs from configured', diff=diff(client, module, service_proxy), **module_result)

                if not monitor_bindings_identical(client, module, monitor_bindings_rw_attrs):
                    module.fail_json(msg='Monitor bindings are not identical', **module_result)

        elif module.params['state'] == 'absent':
            log('Applying actions for state absent')
            if service_exists(client, module):
                if not module.check_mode:
                    service_proxy.delete()
                    if module.params['save_config']:
                        client.save_config()
                module_result['changed'] = True
            else:
                module_result['changed'] = False

            # Sanity check for state
            if not module.check_mode:
                log('Sanity checks for state absent')
                if service_exists(client, module):
                    module.fail_json(msg='Service still exists', **module_result)

    except nitro_exception as e:
        msg = "nitro exception errorcode=%s, message=%s" % (str(e.errorcode), e.message)
        module.fail_json(msg=msg, **module_result)

    client.logout()
    module.exit_json(**module_result)


if __name__ == "__main__":
    main()
