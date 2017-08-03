#!/usr/bin/python
# -*- coding: utf-8 -*-

#  Copyright (c) 2017 Citrix Systems
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'metadata_version': '1.0'}


DOCUMENTATION = '''
---
module: netscaler_gslb_vserver
short_description: Configure gslb vserver entities in Netscaler.
description:
    - Configure gslb vserver entities in Netscaler.

version_added: "2.4.0"

author: George Nikolopoulos (@giorgos-nikolopoulos)

options:

    name:
        description:
            - >-
                Name for the GSLB virtual server. Must begin with an ASCII alphanumeric or underscore C(_) character,
                and must contain only ASCII alphanumeric, underscore C(_), hash C(#), period C(.), space, colon C(:), at C(@),
                equals C(=), and hyphen C(-) characters. Can be changed after the virtual server is created.
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
            - 'NNTP'
            - 'ANY'
            - 'SIP_UDP'
            - 'SIP_TCP'
            - 'SIP_SSL'
            - 'RADIUS'
            - 'RDP'
            - 'RTSP'
            - 'MYSQL'
            - 'MSSQL'
            - 'ORACLE'
        description:
            - "Protocol used by services bound to the virtual server."
            - >-

    dnsrecordtype:
        choices:
            - 'A'
            - 'AAAA'
            - 'CNAME'
            - 'NAPTR'
        description:
            - "DNS record type to associate with the GSLB virtual server's domain name."
            - "Default value: A"
            - "Possible values = A, AAAA, CNAME, NAPTR"

    lbmethod:
        choices:
            - 'ROUNDROBIN'
            - 'LEASTCONNECTION'
            - 'LEASTRESPONSETIME'
            - 'SOURCEIPHASH'
            - 'LEASTBANDWIDTH'
            - 'LEASTPACKETS'
            - 'STATICPROXIMITY'
            - 'RTT'
            - 'CUSTOMLOAD'
        description:
            - "Load balancing method for the GSLB virtual server."
            - "Default value: LEASTCONNECTION"
            - >-
                Possible values = ROUNDROBIN, LEASTCONNECTION, LEASTRESPONSETIME, SOURCEIPHASH, LEASTBANDWIDTH,
                LEASTPACKETS, STATICPROXIMITY, RTT, CUSTOMLOAD

    backuplbmethod:
        choices:
            - 'ROUNDROBIN'
            - 'LEASTCONNECTION'
            - 'LEASTRESPONSETIME'
            - 'SOURCEIPHASH'
            - 'LEASTBANDWIDTH'
            - 'LEASTPACKETS'
            - 'STATICPROXIMITY'
            - 'RTT'
            - 'CUSTOMLOAD'
        description:
            - >-
                Backup load balancing method. Becomes operational if the primary load balancing method fails or
                cannot be used. Valid only if the primary method is based on either round-trip time (RTT) or static
                proximity.

    netmask:
        description:
            - "IPv4 network mask for use in the SOURCEIPHASH load balancing method."
            - "Minimum length = 1"

    v6netmasklen:
        description:
            - >-
                Number of bits to consider, in an IPv6 source IP address, for creating the hash that is required by
                the C(SOURCEIPHASH) load balancing method.
            - "Default value: C(128)"
            - "Minimum value = C(1)"
            - "Maximum value = C(128)"

    tolerance:
        description:
            - >-
                Site selection tolerance, in milliseconds, for implementing the RTT load balancing method. If a
                site's RTT deviates from the lowest RTT by more than the specified tolerance, the site is not
                considered when the NetScaler appliance makes a GSLB decision. The appliance implements the round
                robin method of global server load balancing between sites whose RTT values are within the specified
                tolerance. If the tolerance is 0 (zero), the appliance always sends clients the IP address of the
                site with the lowest RTT.
            - "Minimum value = C(0)"
            - "Maximum value = C(100)"

    persistencetype:
        choices:
            - 'SOURCEIP'
            - 'NONE'
        description:
            - "Use source IP address based persistence for the virtual server."
            - >-
                After the load balancing method selects a service for the first packet, the IP address received in
                response to the DNS query is used for subsequent requests from the same client.

    persistenceid:
        description:
            - >-
                The persistence ID for the GSLB virtual server. The ID is a positive integer that enables GSLB sites
                to identify the GSLB virtual server, and is required if source IP address based or spill over based
                persistence is enabled on the virtual server.
            - "Minimum value = C(0)"
            - "Maximum value = C(65535)"

    persistmask:
        description:
            - >-
                The optional IPv4 network mask applied to IPv4 addresses to establish source IP address based
                persistence.
            - "Minimum length = 1"

    v6persistmasklen:
        description:
            - >-
                Number of bits to consider in an IPv6 source IP address when creating source IP address based
                persistence sessions.
            - "Default value: C(128)"
            - "Minimum value = C(1)"
            - "Maximum value = C(128)"

    timeout:
        description:
            - "Idle time, in minutes, after which a persistence entry is cleared."
            - "Default value: C(2)"
            - "Minimum value = C(2)"
            - "Maximum value = C(1440)"

    mir:
        choices:
            - 'ENABLED'
            - 'DISABLED'
        description:
            - "Include multiple IP addresses in the DNS responses sent to clients."

    disableprimaryondown:
        choices:
            - 'ENABLED'
            - 'DISABLED'
        description:
            - >-
                Continue to direct traffic to the backup chain even after the primary GSLB virtual server returns to
                the UP state. Used when spillover is configured for the virtual server.

    dynamicweight:
        choices:
            - 'SERVICECOUNT'
            - 'SERVICEWEIGHT'
            - 'DISABLED'
        description:
            - >-
                Specify if the appliance should consider the service count, service weights, or ignore both when
                using weight-based load balancing methods. The state of the number of services bound to the virtual
                server help the appliance to select the service.

    considereffectivestate:
        choices:
            - 'NONE'
            - 'STATE_ONLY'
        description:
            - >-
                If the primary state of all bound GSLB services is DOWN, consider the effective states of all the
                GSLB services, obtained through the Metrics Exchange Protocol (MEP), when determining the state of
                the GSLB virtual server. To consider the effective state, set the parameter to STATE_ONLY. To
                disregard the effective state, set the parameter to NONE.
            - >-
                The effective state of a GSLB service is the ability of the corresponding virtual server to serve
                traffic. The effective state of the load balancing virtual server, which is transferred to the GSLB
                service, is UP even if only one virtual server in the backup chain of virtual servers is in the UP
                state.

    comment:
        description:
            - "Any comments that you might want to associate with the GSLB virtual server."

    somethod:
        choices:
            - 'CONNECTION'
            - 'DYNAMICCONNECTION'
            - 'BANDWIDTH'
            - 'HEALTH'
            - 'NONE'
        description:
            - "Type of threshold that, when exceeded, triggers spillover. Available settings function as follows:"
            - "* C(CONNECTION) - Spillover occurs when the number of client connections exceeds the threshold."
            - >-
                * C(DYNAMICCONNECTION) - Spillover occurs when the number of client connections at the GSLB virtual
                server exceeds the sum of the maximum client (Max Clients) settings for bound GSLB services. Do not
                specify a spillover threshold for this setting, because the threshold is implied by the Max Clients
                settings of the bound GSLB services.
            - >-
                * C(BANDWIDTH) - Spillover occurs when the bandwidth consumed by the GSLB virtual server's incoming and
                outgoing traffic exceeds the threshold.
            - >-
                * C(HEALTH) - Spillover occurs when the percentage of weights of the GSLB services that are UP drops
                below the threshold. For example, if services gslbSvc1, gslbSvc2, and gslbSvc3 are bound to a virtual
                server, with weights 1, 2, and 3, and the spillover threshold is 50%, spillover occurs if gslbSvc1
                and gslbSvc3 or gslbSvc2 and gslbSvc3 transition to DOWN.
            - "* C(NONE) - Spillover does not occur."

    sopersistence:
        choices:
            - 'ENABLED'
            - 'DISABLED'
        description:
            - >-
                If spillover occurs, maintain source IP address based persistence for both primary and backup GSLB
                virtual servers.

    sopersistencetimeout:
        description:
            - "Timeout for spillover persistence, in minutes."
            - "Default value: C(2)"
            - "Minimum value = C(2)"
            - "Maximum value = C(1440)"

    sothreshold:
        description:
            - >-
                Threshold at which spillover occurs. Specify an integer for the CONNECTION spillover method, a
                bandwidth value in kilobits per second for the BANDWIDTH method (do not enter the units), or a
                percentage for the HEALTH method (do not enter the percentage symbol).
            - "Minimum value = C(1)"
            - "Maximum value = C(4294967287)"

    sobackupaction:
        choices:
            - 'DROP'
            - 'ACCEPT'
            - 'REDIRECT'
        description:
            - >-
                Action to be performed if spillover is to take effect, but no backup chain to spillover is usable or
                exists.

    appflowlog:
        choices:
            - 'ENABLED'
            - 'DISABLED'
        description:
            - "Enable logging appflow flow information."

    domain_bindings:
        description:
            - >-
                List of bindings for domains for this glsb vserver.
        suboptions:
            cookietimeout:
                description:
                    - Timeout, in minutes, for the GSLB site cookie.

            domainname:
                description:
                    - Domain name for which to change the time to live (TTL) and/or backup service IP address.

            ttl:
                description:
                    - Time to live (TTL) for the domain.

            sitedomainttl:
                description:
                    - >-
                        TTL, in seconds, for all internally created site domains (created when a site prefix is
                        configured on a GSLB service) that are associated with this virtual server.
                    - Minimum value = C(1)

    service_bindings:
        description:
            - List of bindings for gslb services bound to this gslb virtual server.
        suboptions:
            servicename:
                description:
                    - Name of the GSLB service for which to change the weight.
            weight:
                description:
                    - Weight to assign to the GSLB service.

    disabled:
        description:
            - When set to C(yes) the GSLB Vserver state will be set to DISABLED.
            - When set to C(no) the GSLB Vserver state will be set to ENABLED.
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
'''

RETURN = '''
'''


import copy

try:
    from nssrc.com.citrix.netscaler.nitro.resource.config.gslb.gslbvserver import gslbvserver
    from nssrc.com.citrix.netscaler.nitro.resource.config.gslb.gslbvserver_gslbservice_binding import gslbvserver_gslbservice_binding
    from nssrc.com.citrix.netscaler.nitro.resource.config.gslb.gslbvserver_domain_binding import gslbvserver_domain_binding
    from nssrc.com.citrix.netscaler.nitro.exception.nitro_exception import nitro_exception
    PYTHON_SDK_IMPORTED = True
except ImportError as e:
    PYTHON_SDK_IMPORTED = False

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.netscaler import (
    ConfigProxy,
    get_nitro_client,
    netscaler_common_arguments,
    log,
    loglines,
    ensure_feature_is_enabled,
    get_immutables_intersection,
    complete_missing_attributes
)


gslbvserver_domain_binding_rw_attrs = [
    'name',
    'domainname',
    'backupipflag',
    'cookietimeout',
    'backupip',
    'ttl',
    'sitedomainttl',
    'cookie_domainflag',
]

gslbvserver_gslbservice_binding_rw_attrs = [
    'name',
    'servicename',
    'weight',
]


def get_actual_domain_bindings(client, module):
    log('get_actual_domain_bindings')
    # Get actual domain bindings and index them by domainname
    actual_domain_bindings = {}
    if gslbvserver_domain_binding.count(client, name=module.params['name']) != 0:
        # Get all domain bindings associated with the named gslb vserver
        fetched_domain_bindings = gslbvserver_domain_binding.get(client, name=module.params['name'])
        # index by domainname
        for binding in fetched_domain_bindings:
            complete_missing_attributes(binding, gslbvserver_domain_binding_rw_attrs, fill_value=None)
            actual_domain_bindings[binding.domainname] = binding
    return actual_domain_bindings


def get_configured_domain_bindings_proxys(client, module):
    log('get_configured_domain_bindings_proxys')
    configured_domain_proxys = {}
    # Get configured domain bindings and index them by domainname
    if module.params['domain_bindings'] is not None:
        for configured_domain_binding in module.params['domain_bindings']:
            binding_values = copy.deepcopy(configured_domain_binding)
            binding_values['name'] = module.params['name']
            gslbvserver_domain_binding_proxy = ConfigProxy(
                actual=gslbvserver_domain_binding(),
                client=client,
                attribute_values_dict=binding_values,
                readwrite_attrs=gslbvserver_domain_binding_rw_attrs,
                readonly_attrs=[],
            )
            configured_domain_proxys[configured_domain_binding['domainname']] = gslbvserver_domain_binding_proxy
    return configured_domain_proxys


def sync_domain_bindings(client, module):
    log('sync_domain_bindings')

    actual_domain_bindings = get_actual_domain_bindings(client, module)
    configured_domain_proxys = get_configured_domain_bindings_proxys(client, module)

    # Delete actual bindings not in configured bindings
    for domainname, actual_domain_binding in actual_domain_bindings.items():
        if domainname not in configured_domain_proxys.keys():
            log('Deleting absent binding for domain %s' % domainname)
            gslbvserver_domain_binding.delete(client, actual_domain_binding)

    # Delete actual bindings that differ from configured
    for proxy_key, binding_proxy in configured_domain_proxys.items():
        if proxy_key in actual_domain_bindings:
            actual_binding = actual_domain_bindings[proxy_key]
            if not binding_proxy.has_equal_attributes(actual_binding):
                log('Deleting differing binding for domain %s' % binding_proxy.domainname)
                gslbvserver_domain_binding.delete(client, actual_binding)
                log('Adding anew binding for domain %s' % binding_proxy.domainname)
                binding_proxy.add()

    # Add configured domains that are missing from actual
    for proxy_key, binding_proxy in configured_domain_proxys.items():
        if proxy_key not in actual_domain_bindings.keys():
            log('Adding domain binding for domain %s' % binding_proxy.domainname)
            binding_proxy.add()


def domain_bindings_identical(client, module):
    log('domain_bindings_identical')
    actual_domain_bindings = get_actual_domain_bindings(client, module)
    configured_domain_proxys = get_configured_domain_bindings_proxys(client, module)

    actual_keyset = set(actual_domain_bindings.keys())
    configured_keyset = set(configured_domain_proxys.keys())

    symmetric_difference = actual_keyset ^ configured_keyset

    log('symmetric difference %s' % symmetric_difference)
    if len(symmetric_difference) != 0:
        return False

    # Item for item equality test
    for key, proxy in configured_domain_proxys.items():
        diff = proxy.diff_object(actual_domain_bindings[key])
        if 'backupipflag' in diff:
            del diff['backupipflag']
        if not len(diff) == 0:
            return False
    # Fallthrough to True result
    return True


def get_actual_service_bindings(client, module):
    log('get_actual_service_bindings')
    # Get actual domain bindings and index them by domainname
    actual_bindings = {}
    if gslbvserver_gslbservice_binding.count(client, name=module.params['name']) != 0:
        # Get all service bindings associated with the named gslb vserver
        fetched_bindings = gslbvserver_gslbservice_binding.get(client, name=module.params['name'])
        # index by servicename
        for binding in fetched_bindings:
            complete_missing_attributes(binding, gslbvserver_gslbservice_binding_rw_attrs, fill_value=None)
            actual_bindings[binding.servicename] = binding

    return actual_bindings


def get_configured_service_bindings(client, module):
    log('get_configured_service_bindings_proxys')
    configured_proxys = {}
    # Get configured domain bindings and index them by domainname
    if module.params['service_bindings'] is not None:
        for configured_binding in module.params['service_bindings']:
            binding_values = copy.deepcopy(configured_binding)
            binding_values['name'] = module.params['name']
            gslbvserver_service_binding_proxy = ConfigProxy(
                actual=gslbvserver_gslbservice_binding(),
                client=client,
                attribute_values_dict=binding_values,
                readwrite_attrs=gslbvserver_gslbservice_binding_rw_attrs,
                readonly_attrs=[],
            )
            configured_proxys[configured_binding['servicename']] = gslbvserver_service_binding_proxy
    return configured_proxys


def sync_service_bindings(client, module):
    actual = get_actual_service_bindings(client, module)
    configured = get_configured_service_bindings(client, module)

    # Delete extraneous
    extraneous_service_bindings = list(set(actual.keys()) - set(configured.keys()))
    for servicename in extraneous_service_bindings:
        log('Deleting missing binding from service %s' % servicename)
        binding = actual[servicename]
        binding.name = module.params['name']
        gslbvserver_gslbservice_binding.delete(client, binding)

    # Recreate different
    common_service_bindings = list(set(actual.keys()) & set(configured.keys()))
    for servicename in common_service_bindings:
        proxy = configured[servicename]
        binding = actual[servicename]
        if not proxy.has_equal_attributes(actual):
            log('Recreating differing service binding %s' % servicename)
            gslbvserver_gslbservice_binding.delete(client, binding)
            proxy.add()

    # Add missing
    missing_service_bindings = list(set(configured.keys()) - set(actual.keys()))
    for servicename in missing_service_bindings:
        proxy = configured[servicename]
        log('Adding missing service binding %s' % servicename)
        proxy.add()


def service_bindings_identical(client, module):
    actual_bindings = get_actual_service_bindings(client, module)
    configured_proxys = get_configured_service_bindings(client, module)

    actual_keyset = set(actual_bindings.keys())
    configured_keyset = set(configured_proxys.keys())

    symmetric_difference = actual_keyset ^ configured_keyset
    if len(symmetric_difference) != 0:
        return False

    # Item for item equality test
    for key, proxy in configured_proxys.items():
        if key in actual_bindings.keys():
            if not proxy.has_equal_attributes(actual_bindings[key]):
                return False

    # Fallthrough to True result
    return True


def gslb_vserver_exists(client, module):
    if gslbvserver.count_filtered(client, 'name:%s' % module.params['name']) > 0:
        return True
    else:
        return False


def gslb_vserver_identical(client, module, gslb_vserver_proxy):
    gslb_vserver_list = gslbvserver.get_filtered(client, 'name:%s' % module.params['name'])
    diff_dict = gslb_vserver_proxy.diff_object(gslb_vserver_list[0])
    if len(diff_dict) != 0:
        return False
    else:
        return True


def all_identical(client, module, gslb_vserver_proxy):
    return (
        gslb_vserver_identical(client, module, gslb_vserver_proxy) and
        domain_bindings_identical(client, module) and
        service_bindings_identical(client, module)
    )


def diff_list(client, module, gslb_vserver_proxy):
    gslb_vserver_list = gslbvserver.get_filtered(client, 'name:%s' % module.params['name'])
    return gslb_vserver_proxy.diff_object(gslb_vserver_list[0])


def do_state_change(client, module, gslb_vserver_proxy):
    if module.params['disabled']:
        log('Disabling glsb_vserver')
        result = gslbvserver.disable(client, gslb_vserver_proxy.actual)
    else:
        log('Enabling gslbvserver')
        result = gslbvserver.enable(client, gslb_vserver_proxy.actual)
    return result


def main():

    module_specific_arguments = dict(
        name=dict(type='str'),
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
                'NNTP',
                'ANY',
                'SIP_UDP',
                'SIP_TCP',
                'SIP_SSL',
                'RADIUS',
                'RDP',
                'RTSP',
                'MYSQL',
                'MSSQL',
                'ORACLE',
            ]
        ),
        dnsrecordtype=dict(
            type='str',
            choices=[
                'A',
                'AAAA',
                'CNAME',
                'NAPTR',
            ]
        ),
        lbmethod=dict(
            type='str',
            choices=[
                'ROUNDROBIN',
                'LEASTCONNECTION',
                'LEASTRESPONSETIME',
                'SOURCEIPHASH',
                'LEASTBANDWIDTH',
                'LEASTPACKETS',
                'STATICPROXIMITY',
                'RTT',
                'CUSTOMLOAD',
            ]
        ),
        backuplbmethod=dict(
            type='str',
            choices=[
                'ROUNDROBIN',
                'LEASTCONNECTION',
                'LEASTRESPONSETIME',
                'SOURCEIPHASH',
                'LEASTBANDWIDTH',
                'LEASTPACKETS',
                'STATICPROXIMITY',
                'RTT',
                'CUSTOMLOAD',
            ]
        ),
        netmask=dict(type='str'),
        v6netmasklen=dict(type='float'),
        tolerance=dict(type='float'),
        persistencetype=dict(
            type='str',
            choices=[
                'SOURCEIP',
                'NONE',
            ]
        ),
        persistenceid=dict(type='float'),
        persistmask=dict(type='str'),
        v6persistmasklen=dict(type='float'),
        timeout=dict(type='float'),
        mir=dict(
            type='str',
            choices=[
                'ENABLED',
                'DISABLED',
            ]
        ),
        disableprimaryondown=dict(
            type='str',
            choices=[
                'ENABLED',
                'DISABLED',
            ]
        ),
        dynamicweight=dict(
            type='str',
            choices=[
                'SERVICECOUNT',
                'SERVICEWEIGHT',
                'DISABLED',
            ]
        ),
        considereffectivestate=dict(
            type='str',
            choices=[
                'NONE',
                'STATE_ONLY',
            ]
        ),
        comment=dict(type='str'),
        somethod=dict(
            type='str',
            choices=[
                'CONNECTION',
                'DYNAMICCONNECTION',
                'BANDWIDTH',
                'HEALTH',
                'NONE',
            ]
        ),
        sopersistence=dict(
            type='str',
            choices=[
                'ENABLED',
                'DISABLED',
            ]
        ),
        sopersistencetimeout=dict(type='float'),
        sothreshold=dict(type='float'),
        sobackupaction=dict(
            type='str',
            choices=[
                'DROP',
                'ACCEPT',
                'REDIRECT',
            ]
        ),
        appflowlog=dict(
            type='str',
            choices=[
                'ENABLED',
                'DISABLED',
            ]
        ),
        domainname=dict(type='str'),
        cookie_domain=dict(type='str'),
    )

    hand_inserted_arguments = dict(
        domain_bindings=dict(type='list'),
        service_bindings=dict(type='list'),
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

    readwrite_attrs = [
        'name',
        'servicetype',
        'dnsrecordtype',
        'lbmethod',
        'backuplbmethod',
        'netmask',
        'v6netmasklen',
        'tolerance',
        'persistencetype',
        'persistenceid',
        'persistmask',
        'v6persistmasklen',
        'timeout',
        'mir',
        'disableprimaryondown',
        'dynamicweight',
        'considereffectivestate',
        'comment',
        'somethod',
        'sopersistence',
        'sopersistencetimeout',
        'sothreshold',
        'sobackupaction',
        'appflowlog',
        'cookie_domain',
    ]

    readonly_attrs = [
        'curstate',
        'status',
        'lbrrreason',
        'iscname',
        'sitepersistence',
        'totalservices',
        'activeservices',
        'statechangetimesec',
        'statechangetimemsec',
        'tickssincelaststatechange',
        'health',
        'policyname',
        'priority',
        'gotopriorityexpression',
        'type',
        'vsvrbindsvcip',
        'vsvrbindsvcport',
        '__count',
    ]

    immutable_attrs = [
        'name',
        'servicetype',
    ]

    # Instantiate config proxy
    gslb_vserver_proxy = ConfigProxy(
        actual=gslbvserver(),
        client=client,
        attribute_values_dict=module.params,
        readwrite_attrs=readwrite_attrs,
        readonly_attrs=readonly_attrs,
        immutable_attrs=immutable_attrs,
    )

    try:
        ensure_feature_is_enabled(client, 'GSLB')
        # Apply appropriate state
        if module.params['state'] == 'present':
            log('Applying state present')
            if not gslb_vserver_exists(client, module):
                log('Creating object')
                if not module.check_mode:
                    gslb_vserver_proxy.add()
                    sync_domain_bindings(client, module)
                    sync_service_bindings(client, module)
                    if module.params['save_config']:
                        client.save_config()
                module_result['changed'] = True
            elif not all_identical(client, module, gslb_vserver_proxy):
                log('Entering update actions')

                # Check if we try to change value of immutable attributes
                if not gslb_vserver_identical(client, module, gslb_vserver_proxy):
                    log('Updating gslb vserver')
                    immutables_changed = get_immutables_intersection(gslb_vserver_proxy, diff_list(client, module, gslb_vserver_proxy).keys())
                    if immutables_changed != []:
                        module.fail_json(
                            msg='Cannot update immutable attributes %s' % (immutables_changed,),
                            diff=diff_list(client, module, gslb_vserver_proxy),
                            **module_result
                        )
                    if not module.check_mode:
                        gslb_vserver_proxy.update()

                # Update domain bindings
                if not domain_bindings_identical(client, module):
                    if not module.check_mode:
                        sync_domain_bindings(client, module)

                # Update service bindings
                if not service_bindings_identical(client, module):
                    if not module.check_mode:
                        sync_service_bindings(client, module)

                module_result['changed'] = True
                if not module.check_mode:
                    if module.params['save_config']:
                        client.save_config()
            else:
                module_result['changed'] = False

            if not module.check_mode:
                res = do_state_change(client, module, gslb_vserver_proxy)
                if res.errorcode != 0:
                    msg = 'Error when setting disabled state. errorcode: %s message: %s' % (res.errorcode, res.message)
                    module.fail_json(msg=msg, **module_result)

            # Sanity check for state
            if not module.check_mode:
                if not gslb_vserver_exists(client, module):
                    module.fail_json(msg='GSLB Vserver does not exist', **module_result)
                if not gslb_vserver_identical(client, module, gslb_vserver_proxy):
                    module.fail_json(msg='GSLB Vserver differs from configured', diff=diff_list(client, module, gslb_vserver_proxy), **module_result)
                if not domain_bindings_identical(client, module):
                    module.fail_json(msg='Domain bindings differ from configured', diff=diff_list(client, module, gslb_vserver_proxy), **module_result)
                if not service_bindings_identical(client, module):
                    module.fail_json(msg='Service bindings differ from configured', diff=diff_list(client, module, gslb_vserver_proxy), **module_result)

        elif module.params['state'] == 'absent':

            if gslb_vserver_exists(client, module):
                if not module.check_mode:
                    gslb_vserver_proxy.delete()
                    if module.params['save_config']:
                        client.save_config()
                module_result['changed'] = True
            else:
                module_result['changed'] = False

            # Sanity check for state
            if not module.check_mode:
                if gslb_vserver_exists(client, module):
                    module.fail_json(msg='GSLB Vserver still exists', **module_result)

    except nitro_exception as e:
        msg = "nitro exception errorcode=%s, message=%s" % (str(e.errorcode), e.message)
        module.fail_json(msg=msg, **module_result)

    client.logout()
    module.exit_json(**module_result)


if __name__ == "__main__":
    main()
