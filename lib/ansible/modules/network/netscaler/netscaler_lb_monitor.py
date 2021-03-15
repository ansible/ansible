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
module: netscaler_lb_monitor
short_description: Manage load balancing monitors
description:
    - Manage load balancing monitors.
    - This module is intended to run either on the ansible  control node or a bastion (jumpserver) with access to the actual netscaler instance.

version_added: "2.4"

author: George Nikolopoulos (@giorgos-nikolopoulos)

options:

    monitorname:
        description:
            - >-
                Name for the monitor. Must begin with an ASCII alphanumeric or underscore C(_) character, and must
                contain only ASCII alphanumeric, underscore, hash C(#), period C(.), space C( ), colon C(:), at C(@), equals
                C(=), and hyphen C(-) characters.
            - "Minimum length = 1"

    type:
        choices:
            - 'PING'
            - 'TCP'
            - 'HTTP'
            - 'TCP-ECV'
            - 'HTTP-ECV'
            - 'UDP-ECV'
            - 'DNS'
            - 'FTP'
            - 'LDNS-PING'
            - 'LDNS-TCP'
            - 'LDNS-DNS'
            - 'RADIUS'
            - 'USER'
            - 'HTTP-INLINE'
            - 'SIP-UDP'
            - 'SIP-TCP'
            - 'LOAD'
            - 'FTP-EXTENDED'
            - 'SMTP'
            - 'SNMP'
            - 'NNTP'
            - 'MYSQL'
            - 'MYSQL-ECV'
            - 'MSSQL-ECV'
            - 'ORACLE-ECV'
            - 'LDAP'
            - 'POP3'
            - 'CITRIX-XML-SERVICE'
            - 'CITRIX-WEB-INTERFACE'
            - 'DNS-TCP'
            - 'RTSP'
            - 'ARP'
            - 'CITRIX-AG'
            - 'CITRIX-AAC-LOGINPAGE'
            - 'CITRIX-AAC-LAS'
            - 'CITRIX-XD-DDC'
            - 'ND6'
            - 'CITRIX-WI-EXTENDED'
            - 'DIAMETER'
            - 'RADIUS_ACCOUNTING'
            - 'STOREFRONT'
            - 'APPC'
            - 'SMPP'
            - 'CITRIX-XNC-ECV'
            - 'CITRIX-XDM'
            - 'CITRIX-STA-SERVICE'
            - 'CITRIX-STA-SERVICE-NHOP'
        description:
            - "Type of monitor that you want to create."

    action:
        choices:
            - 'NONE'
            - 'LOG'
            - 'DOWN'
        description:
            - >-
                Action to perform when the response to an inline monitor (a monitor of type C(HTTP-INLINE)) indicates
                that the service is down. A service monitored by an inline monitor is considered C(DOWN) if the response
                code is not one of the codes that have been specified for the Response Code parameter.
            - "Available settings function as follows:"
            - >-
                * C(NONE) - Do not take any action. However, the show service command and the show lb monitor command
                indicate the total number of responses that were checked and the number of consecutive error
                responses received after the last successful probe.
            - "* C(LOG) - Log the event in NSLOG or SYSLOG."
            - >-
                * C(DOWN) - Mark the service as being down, and then do not direct any traffic to the service until the
                configured down time has expired. Persistent connections to the service are terminated as soon as the
                service is marked as C(DOWN). Also, log the event in NSLOG or SYSLOG.

    respcode:
        description:
            - >-
                Response codes for which to mark the service as UP. For any other response code, the action performed
                depends on the monitor type. C(HTTP) monitors and C(RADIUS) monitors mark the service as C(DOWN), while
                C(HTTP-INLINE) monitors perform the action indicated by the Action parameter.

    httprequest:
        description:
            - "HTTP request to send to the server (for example, C(\\"HEAD /file.html\\"))."

    rtsprequest:
        description:
            - "RTSP request to send to the server (for example, C(\\"OPTIONS *\\"))."

    customheaders:
        description:
            - "Custom header string to include in the monitoring probes."

    maxforwards:
        description:
            - >-
                Maximum number of hops that the SIP request used for monitoring can traverse to reach the server.
                Applicable only to monitors of type C(SIP-UDP).
            - "Minimum value = C(0)"
            - "Maximum value = C(255)"

    sipmethod:
        choices:
            - 'OPTIONS'
            - 'INVITE'
            - 'REGISTER'
        description:
            - "SIP method to use for the query. Applicable only to monitors of type C(SIP-UDP)."

    sipuri:
        description:
            - >-
                SIP URI string to send to the service (for example, C(sip:sip.test)). Applicable only to monitors of
                type C(SIP-UDP).
            - "Minimum length = 1"

    sipreguri:
        description:
            - >-
                SIP user to be registered. Applicable only if the monitor is of type C(SIP-UDP) and the SIP Method
                parameter is set to C(REGISTER).
            - "Minimum length = 1"

    send:
        description:
            - "String to send to the service. Applicable to C(TCP-ECV), C(HTTP-ECV), and C(UDP-ECV) monitors."

    recv:
        description:
            - >-
                String expected from the server for the service to be marked as UP. Applicable to C(TCP-ECV), C(HTTP-ECV),
                and C(UDP-ECV) monitors.

    query:
        description:
            - "Domain name to resolve as part of monitoring the DNS service (for example, C(example.com))."

    querytype:
        choices:
            - 'Address'
            - 'Zone'
            - 'AAAA'
        description:
            - >-
                Type of DNS record for which to send monitoring queries. Set to C(Address) for querying A records, C(AAAA)
                for querying AAAA records, and C(Zone) for querying the SOA record.

    scriptname:
        description:
            - >-
                Path and name of the script to execute. The script must be available on the NetScaler appliance, in
                the /nsconfig/monitors/ directory.
            - "Minimum length = 1"

    scriptargs:
        description:
            - "String of arguments for the script. The string is copied verbatim into the request."

    dispatcherip:
        description:
            - "IP address of the dispatcher to which to send the probe."

    dispatcherport:
        description:
            - "Port number on which the dispatcher listens for the monitoring probe."

    username:
        description:
            - >-
                User name with which to probe the C(RADIUS), C(NNTP), C(FTP), C(FTP-EXTENDED), C(MYSQL), C(MSSQL), C(POP3), C(CITRIX-AG),
                C(CITRIX-XD-DDC), C(CITRIX-WI-EXTENDED), C(CITRIX-XNC) or C(CITRIX-XDM) server.
            - "Minimum length = 1"

    password:
        description:
            - >-
                Password that is required for logging on to the C(RADIUS), C(NNTP), C(FTP), C(FTP-EXTENDED), C(MYSQL), C(MSSQL), C(POP3),
                C(CITRIX-AG), C(CITRIX-XD-DDC), C(CITRIX-WI-EXTENDED), C(CITRIX-XNC-ECV) or C(CITRIX-XDM) server. Used in
                conjunction with the user name specified for the C(username) parameter.
            - "Minimum length = 1"

    secondarypassword:
        description:
            - >-
                Secondary password that users might have to provide to log on to the Access Gateway server.
                Applicable to C(CITRIX-AG) monitors.

    logonpointname:
        description:
            - >-
                Name of the logon point that is configured for the Citrix Access Gateway Advanced Access Control
                software. Required if you want to monitor the associated login page or Logon Agent. Applicable to
                C(CITRIX-AAC-LAS) and C(CITRIX-AAC-LOGINPAGE) monitors.

    lasversion:
        description:
            - >-
                Version number of the Citrix Advanced Access Control Logon Agent. Required by the C(CITRIX-AAC-LAS)
                monitor.

    radkey:
        description:
            - >-
                Authentication key (shared secret text string) for RADIUS clients and servers to exchange. Applicable
                to monitors of type C(RADIUS) and C(RADIUS_ACCOUNTING).
            - "Minimum length = 1"

    radnasid:
        description:
            - "NAS-Identifier to send in the Access-Request packet. Applicable to monitors of type C(RADIUS)."
            - "Minimum length = 1"

    radnasip:
        description:
            - >-
                Network Access Server (NAS) IP address to use as the source IP address when monitoring a RADIUS
                server. Applicable to monitors of type C(RADIUS) and C(RADIUS_ACCOUNTING).

    radaccounttype:
        description:
            - "Account Type to be used in Account Request Packet. Applicable to monitors of type C(RADIUS_ACCOUNTING)."
            - "Minimum value = 0"
            - "Maximum value = 15"

    radframedip:
        description:
            - "Source ip with which the packet will go out . Applicable to monitors of type C(RADIUS_ACCOUNTING)."

    radapn:
        description:
            - >-
                Called Station Id to be used in Account Request Packet. Applicable to monitors of type
                C(RADIUS_ACCOUNTING).
            - "Minimum length = 1"

    radmsisdn:
        description:
            - >-
                Calling Stations Id to be used in Account Request Packet. Applicable to monitors of type
                C(RADIUS_ACCOUNTING).
            - "Minimum length = 1"

    radaccountsession:
        description:
            - >-
                Account Session ID to be used in Account Request Packet. Applicable to monitors of type
                C(RADIUS_ACCOUNTING).
            - "Minimum length = 1"

    lrtm:
        choices:
            - 'enabled'
            - 'disabled'
        description:
            - >-
                Calculate the least response times for bound services. If this parameter is not enabled, the
                appliance does not learn the response times of the bound services. Also used for LRTM load balancing.

    deviation:
        description:
            - >-
                Time value added to the learned average response time in dynamic response time monitoring (DRTM).
                When a deviation is specified, the appliance learns the average response time of bound services and
                adds the deviation to the average. The final value is then continually adjusted to accommodate
                response time variations over time. Specified in milliseconds, seconds, or minutes.
            - "Minimum value = C(0)"
            - "Maximum value = C(20939)"

    units1:
        choices:
            - 'SEC'
            - 'MSEC'
            - 'MIN'
        description:
            - "Unit of measurement for the Deviation parameter. Cannot be changed after the monitor is created."

    interval:
        description:
            - "Time interval between two successive probes. Must be greater than the value of Response Time-out."
            - "Minimum value = C(1)"
            - "Maximum value = C(20940)"

    units3:
        choices:
            - 'SEC'
            - 'MSEC'
            - 'MIN'
        description:
            - "monitor interval units."

    resptimeout:
        description:
            - >-
                Amount of time for which the appliance must wait before it marks a probe as FAILED. Must be less than
                the value specified for the Interval parameter.
            - >-
                Note: For C(UDP-ECV) monitors for which a receive string is not configured, response timeout does not
                apply. For C(UDP-ECV) monitors with no receive string, probe failure is indicated by an ICMP port
                unreachable error received from the service.
            - "Minimum value = C(1)"
            - "Maximum value = C(20939)"

    units4:
        choices:
            - 'SEC'
            - 'MSEC'
            - 'MIN'
        description:
            - "monitor response timeout units."

    resptimeoutthresh:
        description:
            - >-
                Response time threshold, specified as a percentage of the Response Time-out parameter. If the
                response to a monitor probe has not arrived when the threshold is reached, the appliance generates an
                SNMP trap called monRespTimeoutAboveThresh. After the response time returns to a value below the
                threshold, the appliance generates a monRespTimeoutBelowThresh SNMP trap. For the traps to be
                generated, the "MONITOR-RTO-THRESHOLD" alarm must also be enabled.
            - "Minimum value = C(0)"
            - "Maximum value = C(100)"

    retries:
        description:
            - >-
                Maximum number of probes to send to establish the state of a service for which a monitoring probe
                failed.
            - "Minimum value = C(1)"
            - "Maximum value = C(127)"

    failureretries:
        description:
            - >-
                Number of retries that must fail, out of the number specified for the Retries parameter, for a
                service to be marked as DOWN. For example, if the Retries parameter is set to 10 and the Failure
                Retries parameter is set to 6, out of the ten probes sent, at least six probes must fail if the
                service is to be marked as DOWN. The default value of 0 means that all the retries must fail if the
                service is to be marked as DOWN.
            - "Minimum value = C(0)"
            - "Maximum value = C(32)"

    alertretries:
        description:
            - >-
                Number of consecutive probe failures after which the appliance generates an SNMP trap called
                monProbeFailed.
            - "Minimum value = C(0)"
            - "Maximum value = C(32)"

    successretries:
        description:
            - "Number of consecutive successful probes required to transition a service's state from DOWN to UP."
            - "Minimum value = C(1)"
            - "Maximum value = C(32)"

    downtime:
        description:
            - >-
                Time duration for which to wait before probing a service that has been marked as DOWN. Expressed in
                milliseconds, seconds, or minutes.
            - "Minimum value = C(1)"
            - "Maximum value = C(20939)"

    units2:
        choices:
            - 'SEC'
            - 'MSEC'
            - 'MIN'
        description:
            - "Unit of measurement for the Down Time parameter. Cannot be changed after the monitor is created."

    destip:
        description:
            - >-
                IP address of the service to which to send probes. If the parameter is set to 0, the IP address of
                the server to which the monitor is bound is considered the destination IP address.

    destport:
        description:
            - >-
                TCP or UDP port to which to send the probe. If the parameter is set to 0, the port number of the
                service to which the monitor is bound is considered the destination port. For a monitor of type C(USER),
                however, the destination port is the port number that is included in the HTTP request sent to the
                dispatcher. Does not apply to monitors of type C(PING).

    state:
        choices:
            - 'enabled'
            - 'disabled'
        description:
            - >-
                State of the monitor. The C(disabled) setting disables not only the monitor being configured, but all
                monitors of the same type, until the parameter is set to C(enabled). If the monitor is bound to a
                service, the state of the monitor is not taken into account when the state of the service is
                determined.

    reverse:
        description:
            - >-
                Mark a service as DOWN, instead of UP, when probe criteria are satisfied, and as UP instead of DOWN
                when probe criteria are not satisfied.
        type: bool

    transparent:
        description:
            - >-
                The monitor is bound to a transparent device such as a firewall or router. The state of a transparent
                device depends on the responsiveness of the services behind it. If a transparent device is being
                monitored, a destination IP address must be specified. The probe is sent to the specified IP address
                by using the MAC address of the transparent device.
        type: bool

    iptunnel:
        description:
            - >-
                Send the monitoring probe to the service through an IP tunnel. A destination IP address must be
                specified.
        type: bool

    tos:
        description:
            - "Probe the service by encoding the destination IP address in the IP TOS (6) bits."
        type: bool

    tosid:
        description:
            - "The TOS ID of the specified destination IP. Applicable only when the TOS parameter is set."
            - "Minimum value = C(1)"
            - "Maximum value = C(63)"

    secure:
        description:
            - >-
                Use a secure SSL connection when monitoring a service. Applicable only to TCP based monitors. The
                secure option cannot be used with a C(CITRIX-AG) monitor, because a CITRIX-AG monitor uses a secure
                connection by default.
        type: bool

    validatecred:
        description:
            - >-
                Validate the credentials of the Xen Desktop DDC server user. Applicable to monitors of type
                C(CITRIX-XD-DDC).
        type: bool

    domain:
        description:
            - >-
                Domain in which the XenDesktop Desktop Delivery Controller (DDC) servers or Web Interface servers are
                present. Required by C(CITRIX-XD-DDC) and C(CITRIX-WI-EXTENDED) monitors for logging on to the DDC servers
                and Web Interface servers, respectively.

    ipaddress:
        description:
            - >-
                Set of IP addresses expected in the monitoring response from the DNS server, if the record type is A
                or AAAA. Applicable to C(DNS) monitors.
            - "Minimum length = 1"

    group:
        description:
            - >-
                Name of a newsgroup available on the NNTP service that is to be monitored. The appliance periodically
                generates an NNTP query for the name of the newsgroup and evaluates the response. If the newsgroup is
                found on the server, the service is marked as UP. If the newsgroup does not exist or if the search
                fails, the service is marked as DOWN. Applicable to NNTP monitors.
            - "Minimum length = 1"

    filename:
        description:
            - >-
                Name of a file on the FTP server. The appliance monitors the FTP service by periodically checking the
                existence of the file on the server. Applicable to C(FTP-EXTENDED) monitors.
            - "Minimum length = 1"

    basedn:
        description:
            - >-
                The base distinguished name of the LDAP service, from where the LDAP server can begin the search for
                the attributes in the monitoring query. Required for C(LDAP) service monitoring.
            - "Minimum length = 1"

    binddn:
        description:
            - >-
                The distinguished name with which an LDAP monitor can perform the Bind operation on the LDAP server.
                Optional. Applicable to C(LDAP) monitors.
            - "Minimum length = 1"

    filter:
        description:
            - "Filter criteria for the LDAP query. Optional."
            - "Minimum length = 1"

    attribute:
        description:
            - >-
                Attribute to evaluate when the LDAP server responds to the query. Success or failure of the
                monitoring probe depends on whether the attribute exists in the response. Optional.
            - "Minimum length = 1"

    database:
        description:
            - "Name of the database to connect to during authentication."
            - "Minimum length = 1"

    oraclesid:
        description:
            - "Name of the service identifier that is used to connect to the Oracle database during authentication."
            - "Minimum length = 1"

    sqlquery:
        description:
            - >-
                SQL query for a C(MYSQL-ECV) or C(MSSQL-ECV) monitor. Sent to the database server after the server
                authenticates the connection.
            - "Minimum length = 1"

    evalrule:
        description:
            - >-
                Default syntax expression that evaluates the database server's response to a MYSQL-ECV or MSSQL-ECV
                monitoring query. Must produce a Boolean result. The result determines the state of the server. If
                the expression returns TRUE, the probe succeeds.
            - >-
                For example, if you want the appliance to evaluate the error message to determine the state of the
                server, use the rule C(MYSQL.RES.ROW(10) .TEXT_ELEM(2).EQ("MySQL")).

    mssqlprotocolversion:
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
            - "Version of MSSQL server that is to be monitored."

    Snmpoid:
        description:
            - "SNMP OID for C(SNMP) monitors."
            - "Minimum length = 1"

    snmpcommunity:
        description:
            - "Community name for C(SNMP) monitors."
            - "Minimum length = 1"

    snmpthreshold:
        description:
            - "Threshold for C(SNMP) monitors."
            - "Minimum length = 1"

    snmpversion:
        choices:
            - 'V1'
            - 'V2'
        description:
            - "SNMP version to be used for C(SNMP) monitors."

    metrictable:
        description:
            - "Metric table to which to bind metrics."
            - "Minimum length = 1"
            - "Maximum length = 99"

    application:
        description:
            - >-
                Name of the application used to determine the state of the service. Applicable to monitors of type
                C(CITRIX-XML-SERVICE).
            - "Minimum length = 1"

    sitepath:
        description:
            - >-
                URL of the logon page. For monitors of type C(CITRIX-WEB-INTERFACE), to monitor a dynamic page under the
                site path, terminate the site path with a slash C(/). Applicable to C(CITRIX-WEB-INTERFACE),
                C(CITRIX-WI-EXTENDED) and C(CITRIX-XDM) monitors.
            - "Minimum length = 1"

    storename:
        description:
            - >-
                Store Name. For monitors of type C(STOREFRONT), C(storename) is an optional argument defining storefront
                service store name. Applicable to C(STOREFRONT) monitors.
            - "Minimum length = 1"

    storefrontacctservice:
        description:
            - >-
                Enable/Disable probing for Account Service. Applicable only to Store Front monitors. For
                multi-tenancy configuration users my skip account service.
        type: bool

    hostname:
        description:
            - "Hostname in the FQDN format (Example: C(porche.cars.org)). Applicable to C(STOREFRONT) monitors."
            - "Minimum length = 1"

    netprofile:
        description:
            - "Name of the network profile."
            - "Minimum length = 1"
            - "Maximum length = 127"

    originhost:
        description:
            - >-
                Origin-Host value for the Capabilities-Exchange-Request (CER) message to use for monitoring Diameter
                servers.
            - "Minimum length = 1"

    originrealm:
        description:
            - >-
                Origin-Realm value for the Capabilities-Exchange-Request (CER) message to use for monitoring Diameter
                servers.
            - "Minimum length = 1"

    hostipaddress:
        description:
            - >-
                Host-IP-Address value for the Capabilities-Exchange-Request (CER) message to use for monitoring
                Diameter servers. If Host-IP-Address is not specified, the appliance inserts the mapped IP (MIP)
                address or subnet IP (SNIP) address from which the CER request (the monitoring probe) is sent.
            - "Minimum length = 1"

    vendorid:
        description:
            - >-
                Vendor-Id value for the Capabilities-Exchange-Request (CER) message to use for monitoring Diameter
                servers.

    productname:
        description:
            - >-
                Product-Name value for the Capabilities-Exchange-Request (CER) message to use for monitoring Diameter
                servers.
            - "Minimum length = 1"

    firmwarerevision:
        description:
            - >-
                Firmware-Revision value for the Capabilities-Exchange-Request (CER) message to use for monitoring
                Diameter servers.

    authapplicationid:
        description:
            - >-
                List of Auth-Application-Id attribute value pairs (AVPs) for the Capabilities-Exchange-Request (CER)
                message to use for monitoring Diameter servers. A maximum of eight of these AVPs are supported in a
                monitoring CER message.
            - "Minimum value = C(0)"
            - "Maximum value = C(4294967295)"

    acctapplicationid:
        description:
            - >-
                List of Acct-Application-Id attribute value pairs (AVPs) for the Capabilities-Exchange-Request (CER)
                message to use for monitoring Diameter servers. A maximum of eight of these AVPs are supported in a
                monitoring message.
            - "Minimum value = C(0)"
            - "Maximum value = C(4294967295)"

    inbandsecurityid:
        choices:
            - 'NO_INBAND_SECURITY'
            - 'TLS'
        description:
            - >-
                Inband-Security-Id for the Capabilities-Exchange-Request (CER) message to use for monitoring Diameter
                servers.

    supportedvendorids:
        description:
            - >-
                List of Supported-Vendor-Id attribute value pairs (AVPs) for the Capabilities-Exchange-Request (CER)
                message to use for monitoring Diameter servers. A maximum eight of these AVPs are supported in a
                monitoring message.
            - "Minimum value = C(1)"
            - "Maximum value = C(4294967295)"

    vendorspecificvendorid:
        description:
            - >-
                Vendor-Id to use in the Vendor-Specific-Application-Id grouped attribute-value pair (AVP) in the
                monitoring CER message. To specify Auth-Application-Id or Acct-Application-Id in
                Vendor-Specific-Application-Id, use vendorSpecificAuthApplicationIds or
                vendorSpecificAcctApplicationIds, respectively. Only one Vendor-Id is supported for all the
                Vendor-Specific-Application-Id AVPs in a CER monitoring message.
            - "Minimum value = 1"

    vendorspecificauthapplicationids:
        description:
            - >-
                List of Vendor-Specific-Auth-Application-Id attribute value pairs (AVPs) for the
                Capabilities-Exchange-Request (CER) message to use for monitoring Diameter servers. A maximum of
                eight of these AVPs are supported in a monitoring message. The specified value is combined with the
                value of vendorSpecificVendorId to obtain the Vendor-Specific-Application-Id AVP in the CER
                monitoring message.
            - "Minimum value = C(0)"
            - "Maximum value = C(4294967295)"

    vendorspecificacctapplicationids:
        description:
            - >-
                List of Vendor-Specific-Acct-Application-Id attribute value pairs (AVPs) to use for monitoring
                Diameter servers. A maximum of eight of these AVPs are supported in a monitoring message. The
                specified value is combined with the value of vendorSpecificVendorId to obtain the
                Vendor-Specific-Application-Id AVP in the CER monitoring message.
            - "Minimum value = C(0)"
            - "Maximum value = C(4294967295)"

    kcdaccount:
        description:
            - "KCD Account used by C(MSSQL) monitor."
            - "Minimum length = 1"
            - "Maximum length = 32"

    storedb:
        choices:
            - 'enabled'
            - 'disabled'
        description:
            - >-
                Store the database list populated with the responses to monitor probes. Used in database specific
                load balancing if C(MSSQL-ECV)/C(MYSQL-ECV) monitor is configured.

    storefrontcheckbackendservices:
        description:
            - >-
                This option will enable monitoring of services running on storefront server. Storefront services are
                monitored by probing to a Windows service that runs on the Storefront server and exposes details of
                which storefront services are running.
        type: bool

    trofscode:
        description:
            - "Code expected when the server is under maintenance."

    trofsstring:
        description:
            - >-
                String expected from the server for the service to be marked as trofs. Applicable to HTTP-ECV/TCP-ECV
                monitors.

extends_documentation_fragment: netscaler
requirements:
    - nitro python sdk
'''

EXAMPLES = '''
- name: Set lb monitor
  local_action:
    nsip: 172.18.0.2
    nitro_user: nsroot
    nitro_pass: nsroot
    validate_certs: no


    module: netscaler_lb_monitor
    state: present

    monitorname: monitor_1
    type: HTTP-INLINE
    action: DOWN
    respcode: ['400']
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
    sample: { 'targetlbvserver': 'difference. ours: (str) server1 other: (str) server2' }
'''

from ansible.module_utils.basic import AnsibleModule

from ansible.module_utils.network.netscaler.netscaler import (
    ConfigProxy,
    get_nitro_client,
    netscaler_common_arguments,
    log,
    loglines,
    ensure_feature_is_enabled,
    get_immutables_intersection
)

try:
    from nssrc.com.citrix.netscaler.nitro.resource.config.lb.lbmonitor import lbmonitor
    from nssrc.com.citrix.netscaler.nitro.exception.nitro_exception import nitro_exception
    PYTHON_SDK_IMPORTED = True
except ImportError as e:
    PYTHON_SDK_IMPORTED = False


def lbmonitor_exists(client, module):
    log('Checking if monitor exists')
    if lbmonitor.count_filtered(client, 'monitorname:%s' % module.params['monitorname']) > 0:
        return True
    else:
        return False


def lbmonitor_identical(client, module, lbmonitor_proxy):
    log('Checking if monitor is identical')

    count = lbmonitor.count_filtered(client, 'monitorname:%s' % module.params['monitorname'])
    if count == 0:
        return False

    lbmonitor_list = lbmonitor.get_filtered(client, 'monitorname:%s' % module.params['monitorname'])
    diff_dict = lbmonitor_proxy.diff_object(lbmonitor_list[0])

    # Skipping hashed fields since the cannot be compared directly
    hashed_fields = [
        'password',
        'secondarypassword',
        'radkey',
    ]
    for key in hashed_fields:
        if key in diff_dict:
            del diff_dict[key]

    if diff_dict == {}:
        return True
    else:
        return False


def diff_list(client, module, lbmonitor_proxy):
    monitor_list = lbmonitor.get_filtered(client, 'monitorname:%s' % module.params['monitorname'])
    return lbmonitor_proxy.diff_object(monitor_list[0])


def main():

    module_specific_arguments = dict(

        monitorname=dict(type='str'),

        type=dict(
            type='str',
            choices=[
                'PING',
                'TCP',
                'HTTP',
                'TCP-ECV',
                'HTTP-ECV',
                'UDP-ECV',
                'DNS',
                'FTP',
                'LDNS-PING',
                'LDNS-TCP',
                'LDNS-DNS',
                'RADIUS',
                'USER',
                'HTTP-INLINE',
                'SIP-UDP',
                'SIP-TCP',
                'LOAD',
                'FTP-EXTENDED',
                'SMTP',
                'SNMP',
                'NNTP',
                'MYSQL',
                'MYSQL-ECV',
                'MSSQL-ECV',
                'ORACLE-ECV',
                'LDAP',
                'POP3',
                'CITRIX-XML-SERVICE',
                'CITRIX-WEB-INTERFACE',
                'DNS-TCP',
                'RTSP',
                'ARP',
                'CITRIX-AG',
                'CITRIX-AAC-LOGINPAGE',
                'CITRIX-AAC-LAS',
                'CITRIX-XD-DDC',
                'ND6',
                'CITRIX-WI-EXTENDED',
                'DIAMETER',
                'RADIUS_ACCOUNTING',
                'STOREFRONT',
                'APPC',
                'SMPP',
                'CITRIX-XNC-ECV',
                'CITRIX-XDM',
                'CITRIX-STA-SERVICE',
                'CITRIX-STA-SERVICE-NHOP',
            ]
        ),

        action=dict(
            type='str',
            choices=[
                'NONE',
                'LOG',
                'DOWN',
            ]
        ),
        respcode=dict(type='list'),
        httprequest=dict(type='str'),
        rtsprequest=dict(type='str'),
        customheaders=dict(type='str'),
        maxforwards=dict(type='float'),
        sipmethod=dict(
            type='str',
            choices=[
                'OPTIONS',
                'INVITE',
                'REGISTER',
            ]
        ),
        sipuri=dict(type='str'),
        sipreguri=dict(type='str'),
        send=dict(type='str'),
        recv=dict(type='str'),
        query=dict(type='str'),
        querytype=dict(
            type='str',
            choices=[
                'Address',
                'Zone',
                'AAAA',
            ]
        ),
        scriptname=dict(type='str'),
        scriptargs=dict(type='str'),
        dispatcherip=dict(type='str'),
        dispatcherport=dict(type='int'),
        username=dict(type='str'),
        password=dict(type='str', no_log=True),
        secondarypassword=dict(type='str', no_log=True),
        logonpointname=dict(type='str'),
        lasversion=dict(type='str'),
        radkey=dict(type='str', no_log=True),
        radnasid=dict(type='str'),
        radnasip=dict(type='str'),
        radaccounttype=dict(type='float'),
        radframedip=dict(type='str'),
        radapn=dict(type='str'),
        radmsisdn=dict(type='str'),
        radaccountsession=dict(type='str'),
        lrtm=dict(
            type='str',
            choices=[
                'enabled',
                'disabled',
            ]
        ),
        deviation=dict(type='float'),
        units1=dict(
            type='str',
            choices=[
                'SEC',
                'MSEC',
                'MIN',
            ]
        ),
        interval=dict(type='int'),
        units3=dict(
            type='str',
            choices=[
                'SEC',
                'MSEC',
                'MIN',
            ]
        ),
        resptimeout=dict(type='int'),
        units4=dict(
            type='str',
            choices=[
                'SEC',
                'MSEC',
                'MIN',
            ]
        ),
        resptimeoutthresh=dict(type='float'),
        retries=dict(type='int'),
        failureretries=dict(type='int'),
        alertretries=dict(type='int'),
        successretries=dict(type='int'),
        downtime=dict(type='int'),
        units2=dict(
            type='str',
            choices=[
                'SEC',
                'MSEC',
                'MIN',
            ]
        ),
        destip=dict(type='str'),
        destport=dict(type='int'),
        reverse=dict(type='bool'),
        transparent=dict(type='bool'),
        iptunnel=dict(type='bool'),
        tos=dict(type='bool'),
        tosid=dict(type='float'),
        secure=dict(type='bool'),
        validatecred=dict(type='bool'),
        domain=dict(type='str'),
        ipaddress=dict(type='list'),
        group=dict(type='str'),
        filename=dict(type='str'),
        basedn=dict(type='str'),
        binddn=dict(type='str'),
        filter=dict(type='str'),
        attribute=dict(type='str'),
        database=dict(type='str'),
        oraclesid=dict(type='str'),
        sqlquery=dict(type='str'),
        evalrule=dict(type='str'),
        mssqlprotocolversion=dict(
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
        Snmpoid=dict(type='str'),
        snmpcommunity=dict(type='str'),
        snmpthreshold=dict(type='str'),
        snmpversion=dict(
            type='str',
            choices=[
                'V1',
                'V2',
            ]
        ),
        application=dict(type='str'),
        sitepath=dict(type='str'),
        storename=dict(type='str'),
        storefrontacctservice=dict(type='bool'),
        hostname=dict(type='str'),
        netprofile=dict(type='str'),
        originhost=dict(type='str'),
        originrealm=dict(type='str'),
        hostipaddress=dict(type='str'),
        vendorid=dict(type='float'),
        productname=dict(type='str'),
        firmwarerevision=dict(type='float'),
        authapplicationid=dict(type='list'),
        acctapplicationid=dict(type='list'),
        inbandsecurityid=dict(
            type='str',
            choices=[
                'NO_INBAND_SECURITY',
                'TLS',
            ]
        ),
        supportedvendorids=dict(type='list'),
        vendorspecificvendorid=dict(type='float'),
        vendorspecificauthapplicationids=dict(type='list'),
        vendorspecificacctapplicationids=dict(type='list'),
        storedb=dict(
            type='str',
            choices=[
                'enabled',
                'disabled',
            ]
        ),
        storefrontcheckbackendservices=dict(type='bool'),
        trofscode=dict(type='float'),
        trofsstring=dict(type='str'),
    )

    hand_inserted_arguments = dict()

    argument_spec = dict()
    argument_spec.update(module_specific_arguments)
    argument_spec.update(netscaler_common_arguments)
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
        module.fail_json(msg='Could not load nitro python sdk', **module_result)

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

    # Instantiate lb monitor object
    readwrite_attrs = [
        'monitorname',
        'type',
        'action',
        'respcode',
        'httprequest',
        'rtsprequest',
        'customheaders',
        'maxforwards',
        'sipmethod',
        'sipuri',
        'sipreguri',
        'send',
        'recv',
        'query',
        'querytype',
        'scriptname',
        'scriptargs',
        'dispatcherip',
        'dispatcherport',
        'username',
        'password',
        'secondarypassword',
        'logonpointname',
        'lasversion',
        'radkey',
        'radnasid',
        'radnasip',
        'radaccounttype',
        'radframedip',
        'radapn',
        'radmsisdn',
        'radaccountsession',
        'lrtm',
        'deviation',
        'units1',
        'interval',
        'units3',
        'resptimeout',
        'units4',
        'resptimeoutthresh',
        'retries',
        'failureretries',
        'alertretries',
        'successretries',
        'downtime',
        'units2',
        'destip',
        'destport',
        'reverse',
        'transparent',
        'iptunnel',
        'tos',
        'tosid',
        'secure',
        'validatecred',
        'domain',
        'ipaddress',
        'group',
        'filename',
        'basedn',
        'binddn',
        'filter',
        'attribute',
        'database',
        'oraclesid',
        'sqlquery',
        'evalrule',
        'mssqlprotocolversion',
        'Snmpoid',
        'snmpcommunity',
        'snmpthreshold',
        'snmpversion',
        'application',
        'sitepath',
        'storename',
        'storefrontacctservice',
        'netprofile',
        'originhost',
        'originrealm',
        'hostipaddress',
        'vendorid',
        'productname',
        'firmwarerevision',
        'authapplicationid',
        'acctapplicationid',
        'inbandsecurityid',
        'supportedvendorids',
        'vendorspecificvendorid',
        'vendorspecificauthapplicationids',
        'vendorspecificacctapplicationids',
        'storedb',
        'storefrontcheckbackendservices',
        'trofscode',
        'trofsstring',
    ]

    readonly_attrs = [
        'lrtmconf',
        'lrtmconfstr',
        'dynamicresponsetimeout',
        'dynamicinterval',
        'multimetrictable',
        'dup_state',
        'dup_weight',
        'weight',
    ]

    immutable_attrs = [
        'monitorname',
        'type',
        'units1',
        'units3',
        'units4',
        'units2',
        'Snmpoid',
        'hostname',
        'servicename',
        'servicegroupname',
    ]

    transforms = {
        'storefrontcheckbackendservices': ['bool_yes_no'],
        'secure': ['bool_yes_no'],
        'tos': ['bool_yes_no'],
        'validatecred': ['bool_yes_no'],
        'storefrontacctservice': ['bool_yes_no'],
        'iptunnel': ['bool_yes_no'],
        'transparent': ['bool_yes_no'],
        'reverse': ['bool_yes_no'],
        'lrtm': [lambda v: v.upper()],
        'storedb': [lambda v: v.upper()],
    }

    lbmonitor_proxy = ConfigProxy(
        actual=lbmonitor(),
        client=client,
        attribute_values_dict=module.params,
        readwrite_attrs=readwrite_attrs,
        readonly_attrs=readonly_attrs,
        immutable_attrs=immutable_attrs,
        transforms=transforms,
    )

    try:
        ensure_feature_is_enabled(client, 'LB')

        if module.params['state'] == 'present':
            log('Applying actions for state present')
            if not lbmonitor_exists(client, module):
                if not module.check_mode:
                    log('Adding monitor')
                    lbmonitor_proxy.add()
                    if module.params['save_config']:
                        client.save_config()
                module_result['changed'] = True
            elif not lbmonitor_identical(client, module, lbmonitor_proxy):

                # Check if we try to change value of immutable attributes
                immutables_changed = get_immutables_intersection(lbmonitor_proxy, diff_list(client, module, lbmonitor_proxy).keys())
                if immutables_changed != []:
                    diff = diff_list(client, module, lbmonitor_proxy)
                    msg = 'Cannot update immutable attributes %s' % (immutables_changed,)
                    module.fail_json(msg=msg, diff=diff, **module_result)

                if not module.check_mode:
                    log('Updating monitor')
                    lbmonitor_proxy.update()
                    if module.params['save_config']:
                        client.save_config()
                module_result['changed'] = True
            else:
                log('Doing nothing for monitor')
                module_result['changed'] = False

            # Sanity check for result
            log('Sanity checks for state present')
            if not module.check_mode:
                if not lbmonitor_exists(client, module):
                    module.fail_json(msg='lb monitor does not exist', **module_result)
                if not lbmonitor_identical(client, module, lbmonitor_proxy):
                    module.fail_json(
                        msg='lb monitor is not configured correctly',
                        diff=diff_list(client, module, lbmonitor_proxy),
                        **module_result
                    )

        elif module.params['state'] == 'absent':
            log('Applying actions for state absent')
            if lbmonitor_exists(client, module):
                if not module.check_mode:
                    lbmonitor_proxy.delete()
                    if module.params['save_config']:
                        client.save_config()
                module_result['changed'] = True
            else:
                module_result['changed'] = False

            # Sanity check for result
            log('Sanity checks for state absent')
            if not module.check_mode:
                if lbmonitor_exists(client, module):
                    module.fail_json(msg='lb monitor still exists', **module_result)

        module_result['actual_attributes'] = lbmonitor_proxy.get_actual_rw_attributes(filter='monitorname')
    except nitro_exception as e:
        msg = "nitro exception errorcode=%s, message=%s" % (str(e.errorcode), e.message)
        module.fail_json(msg=msg, **module_result)

    client.logout()

    module.exit_json(**module_result)


if __name__ == "__main__":
    main()
