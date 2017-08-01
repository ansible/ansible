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
module: netscaler_cs_vserver
short_description: Manage content switching vserver
description:
    - Manage content switching vserver
    - This module is intended to run either on the ansible  control node or a bastion (jumpserver) with access to the actual netscaler instance

version_added: "2.4"

author: George Nikolopoulos (@giorgos-nikolopoulos)

options:

    name:
        description:
            - >-
                Name for the content switching virtual server. Must begin with an ASCII alphanumeric or underscore
                C(_) character, and must contain only ASCII alphanumeric, underscore C(_), hash C(#), period C(.), space,
                colon C(:), at sign C(@), equal sign C(=), and hyphen C(-) characters.
            - "Cannot be changed after the CS virtual server is created."
            - "Minimum length = 1"

    td:
        description:
            - >-
                Integer value that uniquely identifies the traffic domain in which you want to configure the entity.
                If you do not specify an ID, the entity becomes part of the default traffic domain, which has an ID
                of 0.
            - "Minimum value = 0"
            - "Maximum value = 4094"

    servicetype:
        choices:
            - 'HTTP'
            - 'SSL'
            - 'TCP'
            - 'FTP'
            - 'RTSP'
            - 'SSL_TCP'
            - 'UDP'
            - 'DNS'
            - 'SIP_UDP'
            - 'SIP_TCP'
            - 'SIP_SSL'
            - 'ANY'
            - 'RADIUS'
            - 'RDP'
            - 'MYSQL'
            - 'MSSQL'
            - 'DIAMETER'
            - 'SSL_DIAMETER'
            - 'DNS_TCP'
            - 'ORACLE'
            - 'SMPP'
        description:
            - "Protocol used by the virtual server."

    ipv46:
        description:
            - "IP address of the content switching virtual server."
            - "Minimum length = 1"

    targettype:
        choices:
            - 'GSLB'
        description:
            - "Virtual server target type."

    ippattern:
        description:
            - >-
                IP address pattern, in dotted decimal notation, for identifying packets to be accepted by the virtual
                server. The IP Mask parameter specifies which part of the destination IP address is matched against
                the pattern. Mutually exclusive with the IP Address parameter.
            - >-
                For example, if the IP pattern assigned to the virtual server is C(198.51.100.0) and the IP mask is
                C(255.255.240.0) (a forward mask), the first 20 bits in the destination IP addresses are matched with
                the first 20 bits in the pattern. The virtual server accepts requests with IP addresses that range
                from 198.51.96.1 to 198.51.111.254. You can also use a pattern such as C(0.0.2.2) and a mask such as
                C(0.0.255.255) (a reverse mask).
            - >-
                If a destination IP address matches more than one IP pattern, the pattern with the longest match is
                selected, and the associated virtual server processes the request. For example, if the virtual
                servers, C(vs1) and C(vs2), have the same IP pattern, C(0.0.100.128), but different IP masks of C(0.0.255.255)
                and C(0.0.224.255), a destination IP address of 198.51.100.128 has the longest match with the IP pattern
                of C(vs1). If a destination IP address matches two or more virtual servers to the same extent, the
                request is processed by the virtual server whose port number matches the port number in the request.

    ipmask:
        description:
            - >-
                IP mask, in dotted decimal notation, for the IP Pattern parameter. Can have leading or trailing
                non-zero octets (for example, C(255.255.240.0) or C(0.0.255.255)). Accordingly, the mask specifies whether
                the first n bits or the last n bits of the destination IP address in a client request are to be
                matched with the corresponding bits in the IP pattern. The former is called a forward mask. The
                latter is called a reverse mask.

    range:
        description:
            - >-
                Number of consecutive IP addresses, starting with the address specified by the IP Address parameter,
                to include in a range of addresses assigned to this virtual server.
            - "Minimum value = C(1)"
            - "Maximum value = C(254)"

    port:
        description:
            - "Port number for content switching virtual server."
            - "Minimum value = 1"
            - "Range C(1) - C(65535)"
            - "* in CLI is represented as 65535 in NITRO API"

    stateupdate:
        choices:
            - 'ENABLED'
            - 'DISABLED'
        description:
            - >-
                Enable state updates for a specific content switching virtual server. By default, the Content
                Switching virtual server is always UP, regardless of the state of the Load Balancing virtual servers
                bound to it. This parameter interacts with the global setting as follows:
            - "Global Level | Vserver Level | Result"
            - "ENABLED ENABLED ENABLED"
            - "ENABLED DISABLED ENABLED"
            - "DISABLED ENABLED ENABLED"
            - "DISABLED DISABLED DISABLED"
            - >-
                If you want to enable state updates for only some content switching virtual servers, be sure to
                disable the state update parameter.

    cacheable:
        description:
            - >-
                Use this option to specify whether a virtual server, used for load balancing or content switching,
                routes requests to the cache redirection virtual server before sending it to the configured servers.
        type: bool

    redirecturl:
        description:
            - >-
                URL to which traffic is redirected if the virtual server becomes unavailable. The service type of the
                virtual server should be either C(HTTP) or C(SSL).
            - >-
                Caution: Make sure that the domain in the URL does not match the domain specified for a content
                switching policy. If it does, requests are continuously redirected to the unavailable virtual server.
            - "Minimum length = 1"

    clttimeout:
        description:
            - "Idle time, in seconds, after which the client connection is terminated. The default values are:"
            - "Minimum value = C(0)"
            - "Maximum value = C(31536000)"

    precedence:
        choices:
            - 'RULE'
            - 'URL'
        description:
            - >-
                Type of precedence to use for both RULE-based and URL-based policies on the content switching virtual
                server. With the default C(RULE) setting, incoming requests are evaluated against the rule-based
                content switching policies. If none of the rules match, the URL in the request is evaluated against
                the URL-based content switching policies.

    casesensitive:
        description:
            - >-
                Consider case in URLs (for policies that use URLs instead of RULES). For example, with the C(on)
                setting, the URLs /a/1.html and /A/1.HTML are treated differently and can have different targets (set
                by content switching policies). With the C(off) setting, /a/1.html and /A/1.HTML are switched to the
                same target.
        type: bool

    somethod:
        choices:
            - 'CONNECTION'
            - 'DYNAMICCONNECTION'
            - 'BANDWIDTH'
            - 'HEALTH'
            - 'NONE'
        description:
            - >-
                Type of spillover used to divert traffic to the backup virtual server when the primary virtual server
                reaches the spillover threshold. Connection spillover is based on the number of connections.
                Bandwidth spillover is based on the total Kbps of incoming and outgoing traffic.

    sopersistence:
        choices:
            - 'ENABLED'
            - 'DISABLED'
        description:
            - "Maintain source-IP based persistence on primary and backup virtual servers."

    sopersistencetimeout:
        description:
            - "Time-out value, in minutes, for spillover persistence."
            - "Minimum value = C(2)"
            - "Maximum value = C(1440)"

    sothreshold:
        description:
            - >-
                Depending on the spillover method, the maximum number of connections or the maximum total bandwidth
                (Kbps) that a virtual server can handle before spillover occurs.
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

    redirectportrewrite:
        choices:
            - 'ENABLED'
            - 'DISABLED'
        description:
            - "State of port rewrite while performing HTTP redirect."

    downstateflush:
        choices:
            - 'ENABLED'
            - 'DISABLED'
        description:
            - >-
                Flush all active transactions associated with a virtual server whose state transitions from UP to
                DOWN. Do not enable this option for applications that must complete their transactions.

    backupvserver:
        description:
            - >-
                Name of the backup virtual server that you are configuring. Must begin with an ASCII alphanumeric or
                underscore C(_) character, and must contain only ASCII alphanumeric, underscore C(_), hash C(#), period C(.),
                space C( ), colon C(:), at sign C(@), equal sign C(=), and hyphen C(-) characters. Can be changed after the
                backup virtual server is created. You can assign a different backup virtual server or rename the
                existing virtual server.
            - "Minimum length = 1"

    disableprimaryondown:
        choices:
            - 'ENABLED'
            - 'DISABLED'
        description:
            - >-
                Continue forwarding the traffic to backup virtual server even after the primary server comes UP from
                the DOWN state.

    insertvserveripport:
        choices:
            - 'OFF'
            - 'VIPADDR'
            - 'V6TOV4MAPPING'
        description:
            - >-
                Insert the virtual server's VIP address and port number in the request header. Available values
                function as follows:
            - "C(VIPADDR) - Header contains the vserver's IP address and port number without any translation."
            - "C(OFF) - The virtual IP and port header insertion option is disabled."
            - >-
                C(V6TOV4MAPPING) - Header contains the mapped IPv4 address corresponding to the IPv6 address of the
                vserver and the port number. An IPv6 address can be mapped to a user-specified IPv4 address using the
                set ns ip6 command.

    vipheader:
        description:
            - "Name of virtual server IP and port header, for use with the VServer IP Port Insertion parameter."
            - "Minimum length = 1"

    rtspnat:
        description:
            - "Enable network address translation (NAT) for real-time streaming protocol (RTSP) connections."
        type: bool

    authenticationhost:
        description:
            - >-
                FQDN of the authentication virtual server. The service type of the virtual server should be either
                C(HTTP) or C(SSL).
            - "Minimum length = 3"
            - "Maximum length = 252"

    authentication:
        description:
            - "Authenticate users who request a connection to the content switching virtual server."
        type: bool

    listenpolicy:
        description:
            - >-
                String specifying the listen policy for the content switching virtual server. Can be either the name
                of an existing expression or an in-line expression.

    authn401:
        description:
            - "Enable HTTP 401-response based authentication."
        type: bool

    authnvsname:
        description:
            - >-
                Name of authentication virtual server that authenticates the incoming user requests to this content
                switching virtual server. .
            - "Minimum length = 1"
            - "Maximum length = 252"

    push:
        choices:
            - 'ENABLED'
            - 'DISABLED'
        description:
            - >-
                Process traffic with the push virtual server that is bound to this content switching virtual server
                (specified by the Push VServer parameter). The service type of the push virtual server should be
                either C(HTTP) or C(SSL).

    pushvserver:
        description:
            - >-
                Name of the load balancing virtual server, of type C(PUSH) or C(SSL_PUSH), to which the server pushes
                updates received on the client-facing load balancing virtual server.
            - "Minimum length = 1"

    pushlabel:
        description:
            - >-
                Expression for extracting the label from the response received from server. This string can be either
                an existing rule name or an inline expression. The service type of the virtual server should be
                either C(HTTP) or C(SSL).

    pushmulticlients:
        description:
            - >-
                Allow multiple Web 2.0 connections from the same client to connect to the virtual server and expect
                updates.
        type: bool

    tcpprofilename:
        description:
            - "Name of the TCP profile containing TCP configuration settings for the virtual server."
            - "Minimum length = 1"
            - "Maximum length = 127"

    httpprofilename:
        description:
            - >-
                Name of the HTTP profile containing HTTP configuration settings for the virtual server. The service
                type of the virtual server should be either C(HTTP) or C(SSL).
            - "Minimum length = 1"
            - "Maximum length = 127"

    dbprofilename:
        description:
            - "Name of the DB profile."
            - "Minimum length = 1"
            - "Maximum length = 127"

    oracleserverversion:
        choices:
            - '10G'
            - '11G'
        description:
            - "Oracle server version."

    comment:
        description:
            - "Information about this virtual server."

    mssqlserverversion:
        choices:
            - '70'
            - '2000'
            - '2000SP1'
            - '2005'
            - '2008'
            - '2008R2'
            - '2012'
            - '2014'
        description:
            - "The version of the MSSQL server."

    l2conn:
        description:
            - "Use L2 Parameters to identify a connection."

    mysqlprotocolversion:
        description:
            - "The protocol version returned by the mysql vserver."

    mysqlserverversion:
        description:
            - "The server version string returned by the mysql vserver."
            - "Minimum length = 1"
            - "Maximum length = 31"

    mysqlcharacterset:
        description:
            - "The character set returned by the mysql vserver."

    mysqlservercapabilities:
        description:
            - "The server capabilities returned by the mysql vserver."

    appflowlog:
        choices:
            - 'ENABLED'
            - 'DISABLED'
        description:
            - "Enable logging appflow flow information."

    netprofile:
        description:
            - "The name of the network profile."
            - "Minimum length = 1"
            - "Maximum length = 127"

    icmpvsrresponse:
        choices:
            - 'PASSIVE'
            - 'ACTIVE'
        description:
            - "Can be active or passive."

    rhistate:
        choices:
            - 'PASSIVE'
            - 'ACTIVE'
        description:
            - "A host route is injected according to the setting on the virtual servers"
            - >-
                * If set to C(PASSIVE) on all the virtual servers that share the IP address, the appliance always
                injects the hostroute.
            - >-
                * If set to C(ACTIVE) on all the virtual servers that share the IP address, the appliance injects even
                if one virtual server is UP.
            - >-
                * If set to C(ACTIVE) on some virtual servers and C(PASSIVE) on the others, the appliance, injects even if
                one virtual server set to C(ACTIVE) is UP.

    authnprofile:
        description:
            - "Name of the authentication profile to be used when authentication is turned on."

    dnsprofilename:
        description:
            - >-
                Name of the DNS profile to be associated with the VServer. DNS profile properties will applied to the
                transactions processed by a VServer. This parameter is valid only for DNS and DNS-TCP VServers.
            - "Minimum length = 1"
            - "Maximum length = 127"

    domainname:
        description:
            - "Domain name for which to change the time to live (TTL) and/or backup service IP address."
            - "Minimum length = 1"

    ttl:
        description:
            - "."
            - "Minimum value = C(1)"

    backupip:
        description:
            - "."
            - "Minimum length = 1"

    cookiedomain:
        description:
            - "."
            - "Minimum length = 1"

    cookietimeout:
        description:
            - "."
            - "Minimum value = C(0)"
            - "Maximum value = C(1440)"

    sitedomainttl:
        description:
            - "."
            - "Minimum value = C(1)"

    disabled:
        description:
            - When set to C(yes) the cs vserver will be disabled.
            - When set to C(no) the cs vserver will be enabled.
            - >-
                Note that due to limitations of the underlying NITRO API a C(disabled) state change alone
                does not cause the module result to report a changed status.
        type: bool
        default: 'no'

extends_documentation_fragment: netscaler
requirements:
    - nitro python sdk
'''

EXAMPLES = '''
# policy_1 must have been already created with the netscaler_cs_policy module
# lbvserver_1 must have been already created with the netscaler_lb_vserver module

- name: Setup content switching vserver
  delegate_to: localhost
  netscaler_cs_vserver:
    nsip: 172.18.0.2
    nitro_user: nsroot
    nitro_pass: nsroot

    state: present

    name: cs_vserver_1
    ipv46: 192.168.1.1
    port: 80
    servicetype: HTTP

    policybindings:
      - policyname: policy_1
        targetlbvserver: lbvserver_1
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
    sample: { 'clttimeout': 'difference. ours: (float) 100.0 other: (float) 60.0' }
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.netscaler import (
    ConfigProxy,
    get_nitro_client,
    netscaler_common_arguments,
    log,
    loglines,
    ensure_feature_is_enabled,
    get_immutables_intersection
)
try:
    from nssrc.com.citrix.netscaler.nitro.resource.config.cs.csvserver import csvserver
    from nssrc.com.citrix.netscaler.nitro.resource.config.cs.csvserver_cspolicy_binding import csvserver_cspolicy_binding
    from nssrc.com.citrix.netscaler.nitro.resource.config.ssl.sslvserver_sslcertkey_binding import sslvserver_sslcertkey_binding
    from nssrc.com.citrix.netscaler.nitro.exception.nitro_exception import nitro_exception
    PYTHON_SDK_IMPORTED = True
except ImportError as e:
    PYTHON_SDK_IMPORTED = False


def cs_vserver_exists(client, module):
    if csvserver.count_filtered(client, 'name:%s' % module.params['name']) > 0:
        return True
    else:
        return False


def cs_vserver_identical(client, module, csvserver_proxy):
    csvserver_list = csvserver.get_filtered(client, 'name:%s' % module.params['name'])
    diff_dict = csvserver_proxy.diff_object(csvserver_list[0])
    if len(diff_dict) == 0:
        return True
    else:
        return False


def get_configured_policybindings(client, module):
    log('Getting configured policy bindigs')
    bindings = {}
    if module.params['policybindings'] is None:
        return bindings

    for binding in module.params['policybindings']:
        binding['name'] = module.params['name']
        key = binding['policyname']
        binding_proxy = ConfigProxy(
            actual=csvserver_cspolicy_binding(),
            client=client,
            readwrite_attrs=[
                'priority',
                'bindpoint',
                'policyname',
                'labelname',
                'gotopriorityexpression',
                'targetlbvserver',
                'name',
                'invoke',
                'labeltype',
            ],
            readonly_attrs=[],
            attribute_values_dict=binding
        )
        bindings[key] = binding_proxy
    return bindings


def get_actual_policybindings(client, module):
    log('Getting actual policy bindigs')
    bindings = {}
    try:
        count = csvserver_cspolicy_binding.count(client, name=module.params['name'])
        if count == 0:
            return bindings
    except nitro_exception as e:
        if e.errorcode == 258:
            return bindings
        else:
            raise

    for binding in csvserver_cspolicy_binding.get(client, name=module.params['name']):
        key = binding.policyname
        bindings[key] = binding

    return bindings


def cs_policybindings_identical(client, module):
    log('Checking policy bindings identical')
    actual_bindings = get_actual_policybindings(client, module)
    configured_bindings = get_configured_policybindings(client, module)

    actual_keyset = set(actual_bindings.keys())
    configured_keyset = set(configured_bindings.keys())
    if len(actual_keyset ^ configured_keyset) > 0:
        return False

    # Compare item to item
    for key in actual_bindings.keys():
        configured_binding_proxy = configured_bindings[key]
        actual_binding_object = actual_bindings[key]
        if not configured_binding_proxy.has_equal_attributes(actual_binding_object):
            return False

    # Fallthrough to success
    return True


def sync_cs_policybindings(client, module):
    log('Syncing cs policybindings')

    # Delete all actual bindings
    for binding in get_actual_policybindings(client, module).values():
        log('Deleting binding for policy %s' % binding.policyname)
        csvserver_cspolicy_binding.delete(client, binding)

    # Add all configured bindings

    for binding in get_configured_policybindings(client, module).values():
        log('Adding binding for policy %s' % binding.policyname)
        binding.add()


def ssl_certkey_bindings_identical(client, module):
    log('Checking if ssl cert key bindings are identical')
    vservername = module.params['name']
    if sslvserver_sslcertkey_binding.count(client, vservername) == 0:
        bindings = []
    else:
        bindings = sslvserver_sslcertkey_binding.get(client, vservername)

    if module.params['ssl_certkey'] is None:
        if len(bindings) == 0:
            return True
        else:
            return False
    else:
        certificate_list = [item.certkeyname for item in bindings]
        if certificate_list == [module.params['ssl_certkey']]:
            return True
        else:
            return False


def ssl_certkey_bindings_sync(client, module):
    log('Syncing certkey bindings')
    vservername = module.params['name']
    if sslvserver_sslcertkey_binding.count(client, vservername) == 0:
        bindings = []
    else:
        bindings = sslvserver_sslcertkey_binding.get(client, vservername)

    # Delete existing bindings
    for binding in bindings:
        log('Deleting existing binding for certkey %s' % binding.certkeyname)
        sslvserver_sslcertkey_binding.delete(client, binding)

    # Add binding if appropriate
    if module.params['ssl_certkey'] is not None:
        log('Adding binding for certkey %s' % module.params['ssl_certkey'])
        binding = sslvserver_sslcertkey_binding()
        binding.vservername = module.params['name']
        binding.certkeyname = module.params['ssl_certkey']
        sslvserver_sslcertkey_binding.add(client, binding)


def diff_list(client, module, csvserver_proxy):
    csvserver_list = csvserver.get_filtered(client, 'name:%s' % module.params['name'])
    return csvserver_proxy.diff_object(csvserver_list[0])


def do_state_change(client, module, csvserver_proxy):
    if module.params['disabled']:
        log('Disabling cs vserver')
        result = csvserver.disable(client, csvserver_proxy.actual)
    else:
        log('Enabling cs vserver')
        result = csvserver.enable(client, csvserver_proxy.actual)
    return result


def main():

    module_specific_arguments = dict(

        name=dict(type='str'),
        td=dict(type='float'),
        servicetype=dict(
            type='str',
            choices=[
                'HTTP',
                'SSL',
                'TCP',
                'FTP',
                'RTSP',
                'SSL_TCP',
                'UDP',
                'DNS',
                'SIP_UDP',
                'SIP_TCP',
                'SIP_SSL',
                'ANY',
                'RADIUS',
                'RDP',
                'MYSQL',
                'MSSQL',
                'DIAMETER',
                'SSL_DIAMETER',
                'DNS_TCP',
                'ORACLE',
                'SMPP'
            ]
        ),

        ipv46=dict(type='str'),
        dnsrecordtype=dict(
            type='str',
            choices=[
                'A',
                'AAAA',
                'CNAME',
                'NAPTR',
            ]
        ),
        ippattern=dict(type='str'),
        ipmask=dict(type='str'),
        range=dict(type='float'),
        port=dict(type='int'),
        stateupdate=dict(
            type='str',
            choices=[
                'ENABLED',
                'DISABLED',
            ]
        ),
        cacheable=dict(type='bool'),
        redirecturl=dict(type='str'),
        clttimeout=dict(type='float'),
        precedence=dict(
            type='str',
            choices=[
                'RULE',
                'URL',
            ]
        ),
        casesensitive=dict(type='bool'),
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
        redirectportrewrite=dict(
            type='str',
            choices=[
                'ENABLED',
                'DISABLED',
            ]
        ),
        downstateflush=dict(
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
        insertvserveripport=dict(
            type='str',
            choices=[
                'OFF',
                'VIPADDR',
                'V6TOV4MAPPING',
            ]
        ),
        vipheader=dict(type='str'),
        rtspnat=dict(type='bool'),
        authenticationhost=dict(type='str'),
        authentication=dict(type='bool'),
        listenpolicy=dict(type='str'),
        authn401=dict(type='bool'),
        authnvsname=dict(type='str'),
        push=dict(
            type='str',
            choices=[
                'ENABLED',
                'DISABLED',
            ]
        ),
        pushvserver=dict(type='str'),
        pushlabel=dict(type='str'),
        pushmulticlients=dict(type='bool'),
        tcpprofilename=dict(type='str'),
        httpprofilename=dict(type='str'),
        dbprofilename=dict(type='str'),
        oracleserverversion=dict(
            type='str',
            choices=[
                '10G',
                '11G',
            ]
        ),
        comment=dict(type='str'),
        mssqlserverversion=dict(
            type='str',
            choices=[
                '70',
                '2000',
                '2000SP1',
                '2005',
                '2008',
                '2008R2',
                '2012',
                '2014',
            ]
        ),
        l2conn=dict(type='bool'),
        mysqlprotocolversion=dict(type='float'),
        mysqlserverversion=dict(type='str'),
        mysqlcharacterset=dict(type='float'),
        mysqlservercapabilities=dict(type='float'),
        appflowlog=dict(
            type='str',
            choices=[
                'ENABLED',
                'DISABLED',
            ]
        ),
        netprofile=dict(type='str'),
        icmpvsrresponse=dict(
            type='str',
            choices=[
                'PASSIVE',
                'ACTIVE',
            ]
        ),
        rhistate=dict(
            type='str',
            choices=[
                'PASSIVE',
                'ACTIVE',
            ]
        ),
        authnprofile=dict(type='str'),
        dnsprofilename=dict(type='str'),
    )

    hand_inserted_arguments = dict(
        policybindings=dict(type='list'),
        ssl_certkey=dict(type='str'),
        disabled=dict(
            type='bool',
            default=False
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
        'td',
        'servicetype',
        'ipv46',
        'dnsrecordtype',
        'ippattern',
        'ipmask',
        'range',
        'port',
        'stateupdate',
        'cacheable',
        'redirecturl',
        'clttimeout',
        'precedence',
        'casesensitive',
        'somethod',
        'sopersistence',
        'sopersistencetimeout',
        'sothreshold',
        'sobackupaction',
        'redirectportrewrite',
        'downstateflush',
        'disableprimaryondown',
        'insertvserveripport',
        'vipheader',
        'rtspnat',
        'authenticationhost',
        'authentication',
        'listenpolicy',
        'authn401',
        'authnvsname',
        'push',
        'pushvserver',
        'pushlabel',
        'pushmulticlients',
        'tcpprofilename',
        'httpprofilename',
        'dbprofilename',
        'oracleserverversion',
        'comment',
        'mssqlserverversion',
        'l2conn',
        'mysqlprotocolversion',
        'mysqlserverversion',
        'mysqlcharacterset',
        'mysqlservercapabilities',
        'appflowlog',
        'netprofile',
        'icmpvsrresponse',
        'rhistate',
        'authnprofile',
        'dnsprofilename',
    ]

    readonly_attrs = [
        'ip',
        'value',
        'ngname',
        'type',
        'curstate',
        'sc',
        'status',
        'cachetype',
        'redirect',
        'homepage',
        'dnsvservername',
        'domain',
        'policyname',
        'servicename',
        'weight',
        'cachevserver',
        'targetvserver',
        'priority',
        'url',
        'gotopriorityexpression',
        'bindpoint',
        'invoke',
        'labeltype',
        'labelname',
        'gt2gb',
        'statechangetimesec',
        'statechangetimemsec',
        'tickssincelaststatechange',
        'ruletype',
        'lbvserver',
        'targetlbvserver',
    ]

    immutable_attrs = [
        'name',
        'td',
        'servicetype',
        'ipv46',
        'targettype',
        'range',
        'port',
        'state',
        'vipheader',
        'newname',
    ]

    transforms = {
        'cacheable': ['bool_yes_no'],
        'rtspnat': ['bool_on_off'],
        'authn401': ['bool_on_off'],
        'casesensitive': ['bool_on_off'],
        'authentication': ['bool_on_off'],
        'l2conn': ['bool_on_off'],
        'pushmulticlients': ['bool_yes_no'],
    }

    # Instantiate config proxy
    csvserver_proxy = ConfigProxy(
        actual=csvserver(),
        client=client,
        attribute_values_dict=module.params,
        readwrite_attrs=readwrite_attrs,
        readonly_attrs=readonly_attrs,
        immutable_attrs=immutable_attrs,
        transforms=transforms,
    )

    try:
        ensure_feature_is_enabled(client, 'CS')

        # Apply appropriate state
        if module.params['state'] == 'present':
            log('Applying actions for state present')
            if not cs_vserver_exists(client, module):
                if not module.check_mode:
                    csvserver_proxy.add()
                    if module.params['save_config']:
                        client.save_config()
                module_result['changed'] = True
            elif not cs_vserver_identical(client, module, csvserver_proxy):

                # Check if we try to change value of immutable attributes
                immutables_changed = get_immutables_intersection(csvserver_proxy, diff_list(client, module, csvserver_proxy).keys())
                if immutables_changed != []:
                    module.fail_json(
                        msg='Cannot update immutable attributes %s' % (immutables_changed,),
                        diff=diff_list(client, module, csvserver_proxy),
                        **module_result
                    )

                if not module.check_mode:
                    csvserver_proxy.update()
                    if module.params['save_config']:
                        client.save_config()
                module_result['changed'] = True
            else:
                module_result['changed'] = False

            # Check policybindings
            if not cs_policybindings_identical(client, module):
                if not module.check_mode:
                    sync_cs_policybindings(client, module)
                    if module.params['save_config']:
                        client.save_config()
                module_result['changed'] = True

            if module.params['servicetype'] != 'SSL' and module.params['ssl_certkey'] is not None:
                module.fail_json(msg='ssl_certkey is applicable only to SSL vservers', **module_result)

            # Check ssl certkey bindings
            if module.params['servicetype'] == 'SSL':
                if not ssl_certkey_bindings_identical(client, module):
                    if not module.check_mode:
                        ssl_certkey_bindings_sync(client, module)

                    module_result['changed'] = True

            if not module.check_mode:
                res = do_state_change(client, module, csvserver_proxy)
                if res.errorcode != 0:
                    msg = 'Error when setting disabled state. errorcode: %s message: %s' % (res.errorcode, res.message)
                    module.fail_json(msg=msg, **module_result)

            # Sanity check for state
            if not module.check_mode:
                log('Sanity checks for state present')
                if not cs_vserver_exists(client, module):
                    module.fail_json(msg='CS vserver does not exist', **module_result)
                if not cs_vserver_identical(client, module, csvserver_proxy):
                    module.fail_json(msg='CS vserver differs from configured', diff=diff_list(client, module, csvserver_proxy), **module_result)
                if not cs_policybindings_identical(client, module):
                    module.fail_json(msg='Policy bindings differ')

                if module.params['servicetype'] == 'SSL':
                    if not ssl_certkey_bindings_identical(client, module):
                        module.fail_json(msg='sll certkey bindings not identical', **module_result)

        elif module.params['state'] == 'absent':
            log('Applying actions for state absent')
            if cs_vserver_exists(client, module):
                if not module.check_mode:
                    csvserver_proxy.delete()
                    if module.params['save_config']:
                        client.save_config()
                module_result['changed'] = True
            else:
                module_result['changed'] = False

            # Sanity check for state
            if not module.check_mode:
                log('Sanity checks for state absent')
                if cs_vserver_exists(client, module):
                    module.fail_json(msg='CS vserver still exists', **module_result)

    except nitro_exception as e:
        msg = "nitro exception errorcode=%s, message=%s" % (str(e.errorcode), e.message)
        module.fail_json(msg=msg, **module_result)

    client.logout()
    module.exit_json(**module_result)


if __name__ == "__main__":
    main()
