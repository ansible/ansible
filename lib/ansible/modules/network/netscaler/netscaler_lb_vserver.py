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
module: netscaler_lb_vserver
short_description: Manage load balancing vserver configuration
description:
    - Manage load balancing vserver configuration
    - This module is intended to run either on the ansible  control node or a bastion (jumpserver) with access to the actual netscaler instance

version_added: "2.4"

author: George Nikolopoulos (@giorgos-nikolopoulos)

options:

    name:
        description:
            - >-
                Name for the virtual server. Must begin with an ASCII alphanumeric or underscore C(_) character, and
                must contain only ASCII alphanumeric, underscore, hash C(#), period C(.), space C( ), colon C(:), at sign
                C(@), equal sign C(=), and hyphen C(-) characters. Can be changed after the virtual server is created.
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
            - 'DNS'
            - 'DHCPRA'
            - 'ANY'
            - 'SIP_UDP'
            - 'SIP_TCP'
            - 'SIP_SSL'
            - 'DNS_TCP'
            - 'RTSP'
            - 'PUSH'
            - 'SSL_PUSH'
            - 'RADIUS'
            - 'RDP'
            - 'MYSQL'
            - 'MSSQL'
            - 'DIAMETER'
            - 'SSL_DIAMETER'
            - 'TFTP'
            - 'ORACLE'
            - 'SMPP'
            - 'SYSLOGTCP'
            - 'SYSLOGUDP'
            - 'FIX'
            - 'SSL_FIX'
        description:
            - "Protocol used by the service (also called the service type)."

    ipv46:
        description:
            - "IPv4 or IPv6 address to assign to the virtual server."

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
                from C(198.51.96.1) to C(198.51.111.254). You can also use a pattern such as C(0.0.2.2) and a mask such as
                C(0.0.255.255) (a reverse mask).
            - >-
                If a destination IP address matches more than one IP pattern, the pattern with the longest match is
                selected, and the associated virtual server processes the request. For example, if virtual servers
                C(vs1) and C(vs2) have the same IP pattern, C(0.0.100.128), but different IP masks of C(0.0.255.255) and
                C(0.0.224.255), a destination IP address of C(198.51.100.128) has the longest match with the IP pattern of
                vs1. If a destination IP address matches two or more virtual servers to the same extent, the request
                is processed by the virtual server whose port number matches the port number in the request.

    ipmask:
        description:
            - >-
                IP mask, in dotted decimal notation, for the IP Pattern parameter. Can have leading or trailing
                non-zero octets (for example, C(255.255.240.0) or C(0.0.255.255)). Accordingly, the mask specifies whether
                the first n bits or the last n bits of the destination IP address in a client request are to be
                matched with the corresponding bits in the IP pattern. The former is called a forward mask. The
                latter is called a reverse mask.

    port:
        description:
            - "Port number for the virtual server."
            - "Range C(1) - C(65535)"
            - "* in CLI is represented as C(65535) in NITRO API"

    range:
        description:
            - >-
                Number of IP addresses that the appliance must generate and assign to the virtual server. The virtual
                server then functions as a network virtual server, accepting traffic on any of the generated IP
                addresses. The IP addresses are generated automatically, as follows:
            - >-
                * For a range of n, the last octet of the address specified by the IP Address parameter increments
                n-1 times.
            - "* If the last octet exceeds 255, it rolls over to 0 and the third octet increments by 1."
            - >-
                Note: The Range parameter assigns multiple IP addresses to one virtual server. To generate an array
                of virtual servers, each of which owns only one IP address, use brackets in the IP Address and Name
                parameters to specify the range. For example:
            - "add lb vserver my_vserver[1-3] HTTP 192.0.2.[1-3] 80."
            - "Minimum value = C(1)"
            - "Maximum value = C(254)"

    persistencetype:
        choices:
            - 'SOURCEIP'
            - 'COOKIEINSERT'
            - 'SSLSESSION'
            - 'RULE'
            - 'URLPASSIVE'
            - 'CUSTOMSERVERID'
            - 'DESTIP'
            - 'SRCIPDESTIP'
            - 'CALLID'
            - 'RTSPSID'
            - 'DIAMETER'
            - 'FIXSESSION'
            - 'NONE'
        description:
            - "Type of persistence for the virtual server. Available settings function as follows:"
            - "* C(SOURCEIP) - Connections from the same client IP address belong to the same persistence session."
            - >-
                * C(COOKIEINSERT) - Connections that have the same HTTP Cookie, inserted by a Set-Cookie directive from
                a server, belong to the same persistence session.
            - "* C(SSLSESSION) - Connections that have the same SSL Session ID belong to the same persistence session."
            - >-
                * C(CUSTOMSERVERID) - Connections with the same server ID form part of the same session. For this
                persistence type, set the Server ID (CustomServerID) parameter for each service and configure the
                Rule parameter to identify the server ID in a request.
            - "* C(RULE) - All connections that match a user defined rule belong to the same persistence session."
            - >-
                * C(URLPASSIVE) - Requests that have the same server ID in the URL query belong to the same persistence
                session. The server ID is the hexadecimal representation of the IP address and port of the service to
                which the request must be forwarded. This persistence type requires a rule to identify the server ID
                in the request.
            - "* C(DESTIP) - Connections to the same destination IP address belong to the same persistence session."
            - >-
                * C(SRCIPDESTIP) - Connections that have the same source IP address and destination IP address belong to
                the same persistence session.
            - "* C(CALLID) - Connections that have the same CALL-ID SIP header belong to the same persistence session."
            - "* C(RTSPSID) - Connections that have the same RTSP Session ID belong to the same persistence session."
            - >-
                * FIXSESSION - Connections that have the same SenderCompID and TargetCompID values belong to the same
                persistence session.

    timeout:
        description:
            - "Time period for which a persistence session is in effect."
            - "Minimum value = C(0)"
            - "Maximum value = C(1440)"

    persistencebackup:
        choices:
            - 'SOURCEIP'
            - 'NONE'
        description:
            - >-
                Backup persistence type for the virtual server. Becomes operational if the primary persistence
                mechanism fails.

    backuppersistencetimeout:
        description:
            - "Time period for which backup persistence is in effect."
            - "Minimum value = C(2)"
            - "Maximum value = C(1440)"

    lbmethod:
        choices:
            - 'ROUNDROBIN'
            - 'LEASTCONNECTION'
            - 'LEASTRESPONSETIME'
            - 'URLHASH'
            - 'DOMAINHASH'
            - 'DESTINATIONIPHASH'
            - 'SOURCEIPHASH'
            - 'SRCIPDESTIPHASH'
            - 'LEASTBANDWIDTH'
            - 'LEASTPACKETS'
            - 'TOKEN'
            - 'SRCIPSRCPORTHASH'
            - 'LRTM'
            - 'CALLIDHASH'
            - 'CUSTOMLOAD'
            - 'LEASTREQUEST'
            - 'AUDITLOGHASH'
            - 'STATICPROXIMITY'
        description:
            - "Load balancing method. The available settings function as follows:"
            - >-
                * C(ROUNDROBIN) - Distribute requests in rotation, regardless of the load. Weights can be assigned to
                services to enforce weighted round robin distribution.
            - "* C(LEASTCONNECTION) (default) - Select the service with the fewest connections."
            - "* C(LEASTRESPONSETIME) - Select the service with the lowest average response time."
            - "* C(LEASTBANDWIDTH) - Select the service currently handling the least traffic."
            - "* C(LEASTPACKETS) - Select the service currently serving the lowest number of packets per second."
            - "* C(CUSTOMLOAD) - Base service selection on the SNMP metrics obtained by custom load monitors."
            - >-
                * C(LRTM) - Select the service with the lowest response time. Response times are learned through
                monitoring probes. This method also takes the number of active connections into account.
            - >-
                Also available are a number of hashing methods, in which the appliance extracts a predetermined
                portion of the request, creates a hash of the portion, and then checks whether any previous requests
                had the same hash value. If it finds a match, it forwards the request to the service that served
                those previous requests. Following are the hashing methods:
            - "* C(URLHASH) - Create a hash of the request URL (or part of the URL)."
            - >-
                * C(DOMAINHASH) - Create a hash of the domain name in the request (or part of the domain name). The
                domain name is taken from either the URL or the Host header. If the domain name appears in both
                locations, the URL is preferred. If the request does not contain a domain name, the load balancing
                method defaults to C(LEASTCONNECTION).
            - "* C(DESTINATIONIPHASH) - Create a hash of the destination IP address in the IP header."
            - "* C(SOURCEIPHASH) - Create a hash of the source IP address in the IP header."
            - >-
                * C(TOKEN) - Extract a token from the request, create a hash of the token, and then select the service
                to which any previous requests with the same token hash value were sent.
            - >-
                * C(SRCIPDESTIPHASH) - Create a hash of the string obtained by concatenating the source IP address and
                destination IP address in the IP header.
            - "* C(SRCIPSRCPORTHASH) - Create a hash of the source IP address and source port in the IP header."
            - "* C(CALLIDHASH) - Create a hash of the SIP Call-ID header."

    hashlength:
        description:
            - >-
                Number of bytes to consider for the hash value used in the URLHASH and DOMAINHASH load balancing
                methods.
            - "Minimum value = C(1)"
            - "Maximum value = C(4096)"

    netmask:
        description:
            - >-
                IPv4 subnet mask to apply to the destination IP address or source IP address when the load balancing
                method is C(DESTINATIONIPHASH) or C(SOURCEIPHASH).
            - "Minimum length = 1"

    v6netmasklen:
        description:
            - >-
                Number of bits to consider in an IPv6 destination or source IP address, for creating the hash that is
                required by the C(DESTINATIONIPHASH) and C(SOURCEIPHASH) load balancing methods.
            - "Minimum value = C(1)"
            - "Maximum value = C(128)"

    backuplbmethod:
        choices:
            - 'ROUNDROBIN'
            - 'LEASTCONNECTION'
            - 'LEASTRESPONSETIME'
            - 'SOURCEIPHASH'
            - 'LEASTBANDWIDTH'
            - 'LEASTPACKETS'
            - 'CUSTOMLOAD'
        description:
            - "Backup load balancing method. Becomes operational if the primary load balancing me"
            - "thod fails or cannot be used."
            - "Valid only if the primary method is based on static proximity."

    cookiename:
        description:
            - >-
                Use this parameter to specify the cookie name for C(COOKIE) peristence type. It specifies the name of
                cookie with a maximum of 32 characters. If not specified, cookie name is internally generated.


    listenpolicy:
        description:
            - >-
                Default syntax expression identifying traffic accepted by the virtual server. Can be either an
                expression (for example, C(CLIENT.IP.DST.IN_SUBNET(192.0.2.0/24)) or the name of a named expression. In
                the above example, the virtual server accepts all requests whose destination IP address is in the
                192.0.2.0/24 subnet.

    listenpriority:
        description:
            - >-
                Integer specifying the priority of the listen policy. A higher number specifies a lower priority. If
                a request matches the listen policies of more than one virtual server the virtual server whose listen
                policy has the highest priority (the lowest priority number) accepts the request.
            - "Minimum value = C(0)"
            - "Maximum value = C(101)"

    resrule:
        description:
            - >-
                Default syntax expression specifying which part of a server's response to use for creating rule based
                persistence sessions (persistence type RULE). Can be either an expression or the name of a named
                expression.
            - "Example:"
            - "C(HTTP.RES.HEADER(\\"setcookie\\").VALUE(0).TYPECAST_NVLIST_T('=',';').VALUE(\\"server1\\"))."

    persistmask:
        description:
            - "Persistence mask for IP based persistence types, for IPv4 virtual servers."
            - "Minimum length = 1"

    v6persistmasklen:
        description:
            - "Persistence mask for IP based persistence types, for IPv6 virtual servers."
            - "Minimum value = C(1)"
            - "Maximum value = C(128)"

    rtspnat:
        description:
            - "Use network address translation (NAT) for RTSP data connections."
        type: bool

    m:
        choices:
            - 'IP'
            - 'MAC'
            - 'IPTUNNEL'
            - 'TOS'
        description:
            - "Redirection mode for load balancing. Available settings function as follows:"
            - >-
                * C(IP) - Before forwarding a request to a server, change the destination IP address to the server's IP
                address.
            - >-
                * C(MAC) - Before forwarding a request to a server, change the destination MAC address to the server's
                MAC address. The destination IP address is not changed. MAC-based redirection mode is used mostly in
                firewall load balancing deployments.
            - >-
                * C(IPTUNNEL) - Perform IP-in-IP encapsulation for client IP packets. In the outer IP headers, set the
                destination IP address to the IP address of the server and the source IP address to the subnet IP
                (SNIP). The client IP packets are not modified. Applicable to both IPv4 and IPv6 packets.
            - "* C(TOS) - Encode the virtual server's TOS ID in the TOS field of the IP header."
            - "You can use either the C(IPTUNNEL) or the C(TOS) option to implement Direct Server Return (DSR)."

    tosid:
        description:
            - >-
                TOS ID of the virtual server. Applicable only when the load balancing redirection mode is set to TOS.
            - "Minimum value = C(1)"
            - "Maximum value = C(63)"

    datalength:
        description:
            - >-
                Length of the token to be extracted from the data segment of an incoming packet, for use in the token
                method of load balancing. The length of the token, specified in bytes, must not be greater than 24
                KB. Applicable to virtual servers of type TCP.
            - "Minimum value = C(1)"
            - "Maximum value = C(100)"

    dataoffset:
        description:
            - >-
                Offset to be considered when extracting a token from the TCP payload. Applicable to virtual servers,
                of type TCP, using the token method of load balancing. Must be within the first 24 KB of the TCP
                payload.
            - "Minimum value = C(0)"
            - "Maximum value = C(25400)"

    sessionless:
        choices:
            - 'enabled'
            - 'disabled'
        description:
            - >-
                Perform load balancing on a per-packet basis, without establishing sessions. Recommended for load
                balancing of intrusion detection system (IDS) servers and scenarios involving direct server return
                (DSR), where session information is unnecessary.

    connfailover:
        choices:
            - 'DISABLED'
            - 'STATEFUL'
            - 'STATELESS'
        description:
            - >-
                Mode in which the connection failover feature must operate for the virtual server. After a failover,
                established TCP connections and UDP packet flows are kept active and resumed on the secondary
                appliance. Clients remain connected to the same servers. Available settings function as follows:
            - >-
                * C(STATEFUL) - The primary appliance shares state information with the secondary appliance, in real
                time, resulting in some runtime processing overhead.
            - >-
                * C(STATELESS) - State information is not shared, and the new primary appliance tries to re-create the
                packet flow on the basis of the information contained in the packets it receives.
            - "* C(DISABLED) - Connection failover does not occur."

    redirurl:
        description:
            - "URL to which to redirect traffic if the virtual server becomes unavailable."
            - >-
                WARNING! Make sure that the domain in the URL does not match the domain specified for a content
                switching policy. If it does, requests are continuously redirected to the unavailable virtual server.
            - "Minimum length = 1"

    cacheable:
        description:
            - >-
                Route cacheable requests to a cache redirection virtual server. The load balancing virtual server can
                forward requests only to a transparent cache redirection virtual server that has an IP address and
                port combination of *:80, so such a cache redirection virtual server must be configured on the
                appliance.
        type: bool

    clttimeout:
        description:
            - "Idle time, in seconds, after which a client connection is terminated."
            - "Minimum value = C(0)"
            - "Maximum value = C(31536000)"

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
                * DYNAMICCONNECTION - Spillover occurs when the number of client connections at the virtual server
                exceeds the sum of the maximum client (Max Clients) settings for bound services. Do not specify a
                spillover threshold for this setting, because the threshold is implied by the Max Clients settings of
                bound services.
            - >-
                * C(BANDWIDTH) - Spillover occurs when the bandwidth consumed by the virtual server's incoming and
                outgoing traffic exceeds the threshold.
            - >-
                * C(HEALTH) - Spillover occurs when the percentage of weights of the services that are UP drops below
                the threshold. For example, if services svc1, svc2, and svc3 are bound to a virtual server, with
                weights 1, 2, and 3, and the spillover threshold is 50%, spillover occurs if svc1 and svc3 or svc2
                and svc3 transition to DOWN.
            - "* C(NONE) - Spillover does not occur."

    sopersistence:
        choices:
            - 'enabled'
            - 'disabled'
        description:
            - >-
                If spillover occurs, maintain source IP address based persistence for both primary and backup virtual
                servers.

    sopersistencetimeout:
        description:
            - "Timeout for spillover persistence, in minutes."
            - "Minimum value = C(2)"
            - "Maximum value = C(1440)"

    healththreshold:
        description:
            - >-
                Threshold in percent of active services below which vserver state is made down. If this threshold is
                0, vserver state will be up even if one bound service is up.
            - "Minimum value = C(0)"
            - "Maximum value = C(100)"

    sothreshold:
        description:
            - >-
                Threshold at which spillover occurs. Specify an integer for the C(CONNECTION) spillover method, a
                bandwidth value in kilobits per second for the C(BANDWIDTH) method (do not enter the units), or a
                percentage for the C(HEALTH) method (do not enter the percentage symbol).
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
            - 'enabled'
            - 'disabled'
        description:
            - "Rewrite the port and change the protocol to ensure successful HTTP redirects from services."

    downstateflush:
        choices:
            - 'enabled'
            - 'disabled'
        description:
            - >-
                Flush all active transactions associated with a virtual server whose state transitions from UP to
                DOWN. Do not enable this option for applications that must complete their transactions.

    disableprimaryondown:
        choices:
            - 'enabled'
            - 'disabled'
        description:
            - >-
                If the primary virtual server goes down, do not allow it to return to primary status until manually
                enabled.

    insertvserveripport:
        choices:
            - 'OFF'
            - 'VIPADDR'
            - 'V6TOV4MAPPING'
        description:
            - >-
                Insert an HTTP header, whose value is the IP address and port number of the virtual server, before
                forwarding a request to the server. The format of the header is <vipHeader>: <virtual server IP
                address>_<port number >, where vipHeader is the name that you specify for the header. If the virtual
                server has an IPv6 address, the address in the header is enclosed in brackets ([ and ]) to separate
                it from the port number. If you have mapped an IPv4 address to a virtual server's IPv6 address, the
                value of this parameter determines which IP address is inserted in the header, as follows:
            - >-
                * C(VIPADDR) - Insert the IP address of the virtual server in the HTTP header regardless of whether the
                virtual server has an IPv4 address or an IPv6 address. A mapped IPv4 address, if configured, is
                ignored.
            - >-
                * C(V6TOV4MAPPING) - Insert the IPv4 address that is mapped to the virtual server's IPv6 address. If a
                mapped IPv4 address is not configured, insert the IPv6 address.
            - "* C(OFF) - Disable header insertion."

    vipheader:
        description:
            - "Name for the inserted header. The default name is vip-header."
            - "Minimum length = 1"

    authenticationhost:
        description:
            - >-
                Fully qualified domain name (FQDN) of the authentication virtual server to which the user must be
                redirected for authentication. Make sure that the Authentication parameter is set to C(yes).
            - "Minimum length = 3"
            - "Maximum length = 252"

    authentication:
        description:
            - "Enable or disable user authentication."
        type: bool

    authn401:
        description:
            - "Enable or disable user authentication with HTTP 401 responses."
        type: bool

    authnvsname:
        description:
            - "Name of an authentication virtual server with which to authenticate users."
            - "Minimum length = 1"
            - "Maximum length = 252"

    push:
        choices:
            - 'enabled'
            - 'disabled'
        description:
            - "Process traffic with the push virtual server that is bound to this load balancing virtual server."

    pushvserver:
        description:
            - >-
                Name of the load balancing virtual server, of type PUSH or SSL_PUSH, to which the server pushes
                updates received on the load balancing virtual server that you are configuring.
            - "Minimum length = 1"

    pushlabel:
        description:
            - >-
                Expression for extracting a label from the server's response. Can be either an expression or the name
                of a named expression.

    pushmulticlients:
        description:
            - >-
                Allow multiple Web 2.0 connections from the same client to connect to the virtual server and expect
                updates.
        type: bool

    tcpprofilename:
        description:
            - "Name of the TCP profile whose settings are to be applied to the virtual server."
            - "Minimum length = 1"
            - "Maximum length = 127"

    httpprofilename:
        description:
            - "Name of the HTTP profile whose settings are to be applied to the virtual server."
            - "Minimum length = 1"
            - "Maximum length = 127"

    dbprofilename:
        description:
            - "Name of the DB profile whose settings are to be applied to the virtual server."
            - "Minimum length = 1"
            - "Maximum length = 127"

    comment:
        description:
            - "Any comments that you might want to associate with the virtual server."

    l2conn:
        description:
            - >-
                Use Layer 2 parameters (channel number, MAC address, and VLAN ID) in addition to the 4-tuple (<source
                IP>:<source port>::<destination IP>:<destination port>) that is used to identify a connection. Allows
                multiple TCP and non-TCP connections with the same 4-tuple to co-exist on the NetScaler appliance.
        type: bool

    oracleserverversion:
        choices:
            - '10G'
            - '11G'
        description:
            - "Oracle server version."

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
            - >-
                For a load balancing virtual server of type C(MSSQL), the Microsoft SQL Server version. Set this
                parameter if you expect some clients to run a version different from the version of the database.
                This setting provides compatibility between the client-side and server-side connections by ensuring
                that all communication conforms to the server's version.

    mysqlprotocolversion:
        description:
            - "MySQL protocol version that the virtual server advertises to clients."

    mysqlserverversion:
        description:
            - "MySQL server version string that the virtual server advertises to clients."
            - "Minimum length = 1"
            - "Maximum length = 31"

    mysqlcharacterset:
        description:
            - "Character set that the virtual server advertises to clients."

    mysqlservercapabilities:
        description:
            - "Server capabilities that the virtual server advertises to clients."

    appflowlog:
        choices:
            - 'enabled'
            - 'disabled'
        description:
            - "Apply AppFlow logging to the virtual server."

    netprofile:
        description:
            - >-
                Name of the network profile to associate with the virtual server. If you set this parameter, the
                virtual server uses only the IP addresses in the network profile as source IP addresses when
                initiating connections with servers.
            - "Minimum length = 1"
            - "Maximum length = 127"

    icmpvsrresponse:
        choices:
            - 'PASSIVE'
            - 'ACTIVE'
        description:
            - >-
                How the NetScaler appliance responds to ping requests received for an IP address that is common to
                one or more virtual servers. Available settings function as follows:
            - >-
                * If set to C(PASSIVE) on all the virtual servers that share the IP address, the appliance always
                responds to the ping requests.
            - >-
                * If set to C(ACTIVE) on all the virtual servers that share the IP address, the appliance responds to
                the ping requests if at least one of the virtual servers is UP. Otherwise, the appliance does not
                respond.
            - >-
                * If set to C(ACTIVE) on some virtual servers and PASSIVE on the others, the appliance responds if at
                least one virtual server with the ACTIVE setting is UP. Otherwise, the appliance does not respond.
            - >-
                Note: This parameter is available at the virtual server level. A similar parameter, ICMP Response, is
                available at the IP address level, for IPv4 addresses of type VIP. To set that parameter, use the add
                ip command in the CLI or the Create IP dialog box in the GUI.

    rhistate:
        choices:
            - 'PASSIVE'
            - 'ACTIVE'
        description:
            - >-
                Route Health Injection (RHI) functionality of the NetSaler appliance for advertising the route of the
                VIP address associated with the virtual server. When Vserver RHI Level (RHI) parameter is set to
                VSVR_CNTRLD, the following are different RHI behaviors for the VIP address on the basis of RHIstate
                (RHI STATE) settings on the virtual servers associated with the VIP address:
            - >-
                * If you set C(rhistate) to C(PASSIVE) on all virtual servers, the NetScaler ADC always advertises the
                route for the VIP address.
            - >-
                * If you set C(rhistate) to C(ACTIVE) on all virtual servers, the NetScaler ADC advertises the route for
                the VIP address if at least one of the associated virtual servers is in UP state.
            - >-
                * If you set C(rhistate) to C(ACTIVE) on some and PASSIVE on others, the NetScaler ADC advertises the
                route for the VIP address if at least one of the associated virtual servers, whose C(rhistate) set to
                C(ACTIVE), is in UP state.

    newservicerequest:
        description:
            - >-
                Number of requests, or percentage of the load on existing services, by which to increase the load on
                a new service at each interval in slow-start mode. A non-zero value indicates that slow-start is
                applicable. A zero value indicates that the global RR startup parameter is applied. Changing the
                value to zero will cause services currently in slow start to take the full traffic as determined by
                the LB method. Subsequently, any new services added will use the global RR factor.

    newservicerequestunit:
        choices:
            - 'PER_SECOND'
            - 'PERCENT'
        description:
            - "Units in which to increment load at each interval in slow-start mode."

    newservicerequestincrementinterval:
        description:
            - >-
                Interval, in seconds, between successive increments in the load on a new service or a service whose
                state has just changed from DOWN to UP. A value of 0 (zero) specifies manual slow start.
            - "Minimum value = C(0)"
            - "Maximum value = C(3600)"

    minautoscalemembers:
        description:
            - "Minimum number of members expected to be present when vserver is used in Autoscale."
            - "Minimum value = C(0)"
            - "Maximum value = C(5000)"

    maxautoscalemembers:
        description:
            - "Maximum number of members expected to be present when vserver is used in Autoscale."
            - "Minimum value = C(0)"
            - "Maximum value = C(5000)"

    persistavpno:
        description:
            - "Persist AVP number for Diameter Persistency."
            - "In case this AVP is not defined in Base RFC 3588 and it is nested inside a Grouped AVP,"
            - "define a sequence of AVP numbers (max 3) in order of parent to child. So say persist AVP number X"
            - "is nested inside AVP Y which is nested in Z, then define the list as Z Y X."
            - "Minimum value = C(1)"

    skippersistency:
        choices:
            - 'Bypass'
            - 'ReLb'
            - 'None'
        description:
            - >-
                This argument decides the behavior incase the service which is selected from an existing persistence
                session has reached threshold.

    td:
        description:
            - >-
                Integer value that uniquely identifies the traffic domain in which you want to configure the entity.
                If you do not specify an ID, the entity becomes part of the default traffic domain, which has an ID
                of 0.
            - "Minimum value = C(0)"
            - "Maximum value = C(4094)"

    authnprofile:
        description:
            - "Name of the authentication profile to be used when authentication is turned on."

    macmoderetainvlan:
        choices:
            - 'enabled'
            - 'disabled'
        description:
            - "This option is used to retain vlan information of incoming packet when macmode is enabled."

    dbslb:
        choices:
            - 'enabled'
            - 'disabled'
        description:
            - "Enable database specific load balancing for MySQL and MSSQL service types."

    dns64:
        choices:
            - 'enabled'
            - 'disabled'
        description:
            - "This argument is for enabling/disabling the C(dns64) on lbvserver."

    bypassaaaa:
        description:
            - >-
                If this option is enabled while resolving DNS64 query AAAA queries are not sent to back end dns
                server.
        type: bool

    recursionavailable:
        description:
            - >-
                When set to YES, this option causes the DNS replies from this vserver to have the RA bit turned on.
                Typically one would set this option to YES, when the vserver is load balancing a set of DNS servers
                thatsupport recursive queries.
        type: bool

    processlocal:
        choices:
            - 'enabled'
            - 'disabled'
        description:
            - >-
                By turning on this option packets destined to a vserver in a cluster will not under go any steering.
                Turn this option for single packet request response mode or when the upstream device is performing a
                proper RSS for connection based distribution.

    dnsprofilename:
        description:
            - >-
                Name of the DNS profile to be associated with the VServer. DNS profile properties will be applied to
                the transactions processed by a VServer. This parameter is valid only for DNS and DNS-TCP VServers.
            - "Minimum length = 1"
            - "Maximum length = 127"

    servicebindings:
        description:
            - List of services along with the weights that are load balanced.
            - The following suboptions are available.
        suboptions:
            servicename:
                description:
                    - "Service to bind to the virtual server."
                    - "Minimum length = 1"
            weight:
                description:
                    - "Weight to assign to the specified service."
                    - "Minimum value = C(1)"
                    - "Maximum value = C(100)"

    servicegroupbindings:
        description:
            - List of service groups along with the weights that are load balanced.
            - The following suboptions are available.
        suboptions:
            servicegroupname:
                description:
                    - "The service group name bound to the selected load balancing virtual server."
            weight:
                description:
                    - >-
                        Integer specifying the weight of the service. A larger number specifies a greater weight. Defines the
                        capacity of the service relative to the other services in the load balancing configuration.
                        Determines the priority given to the service in load balancing decisions.
                    - "Minimum value = C(1)"
                    - "Maximum value = C(100)"

    ssl_certkey:
        description:
            - The name of the ssl certificate that is bound to this service.
            - The ssl certificate must already exist.
            - Creating the certificate can be done with the M(netscaler_ssl_certkey) module.
            - This option is only applicable only when C(servicetype) is C(SSL).

    disabled:
        description:
            - When set to C(yes) the lb vserver will be disabled.
            - When set to C(no) the lb vserver will be enabled.
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
# Netscaler services service-http-1, service-http-2 must have been already created with the netscaler_service module

- name: Create a load balancing vserver bound to services
  delegate_to: localhost
  netscaler_lb_vserver:
    nsip: 172.18.0.2
    nitro_user: nsroot
    nitro_pass: nsroot
    validate_certs: no

    state: present

    name: lb_vserver_1
    servicetype: HTTP
    timeout: 12
    ipv46: 6.93.3.3
    port: 80
    servicebindings:
        - servicename: service-http-1
          weight: 80
        - servicename: service-http-2
          weight: 20

# Service group service-group-1 must have been already created with the netscaler_servicegroup module

- name: Create load balancing vserver bound to servicegroup
  delegate_to: localhost
  netscaler_lb_vserver:
    nsip: 172.18.0.2
    nitro_user: nsroot
    nitro_pass: nsroot
    validate_certs: no
    state: present

    name: lb_vserver_2
    servicetype: HTTP
    ipv46: 6.92.2.2
    port: 80
    timeout: 10
    servicegroupbindings:
        - servicegroupname: service-group-1
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
from ansible.module_utils.network.netscaler.netscaler import (
    ConfigProxy,
    get_nitro_client,
    netscaler_common_arguments,
    log,
    loglines,
    get_immutables_intersection,
    ensure_feature_is_enabled
)
import copy

try:
    from nssrc.com.citrix.netscaler.nitro.resource.config.lb.lbvserver import lbvserver
    from nssrc.com.citrix.netscaler.nitro.resource.config.lb.lbvserver_servicegroup_binding import lbvserver_servicegroup_binding
    from nssrc.com.citrix.netscaler.nitro.resource.config.lb.lbvserver_service_binding import lbvserver_service_binding
    from nssrc.com.citrix.netscaler.nitro.resource.config.ssl.sslvserver_sslcertkey_binding import sslvserver_sslcertkey_binding
    from nssrc.com.citrix.netscaler.nitro.exception.nitro_exception import nitro_exception

    PYTHON_SDK_IMPORTED = True
except ImportError as e:
    IMPORT_ERROR = str(e)
    PYTHON_SDK_IMPORTED = False


def lb_vserver_exists(client, module):
    log('Checking if lb vserver exists')
    if lbvserver.count_filtered(client, 'name:%s' % module.params['name']) > 0:
        return True
    else:
        return False


def lb_vserver_identical(client, module, lbvserver_proxy):
    log('Checking if configured lb vserver is identical')
    lbvserver_list = lbvserver.get_filtered(client, 'name:%s' % module.params['name'])
    if lbvserver_proxy.has_equal_attributes(lbvserver_list[0]):
        return True
    else:
        return False


def lb_vserver_diff(client, module, lbvserver_proxy):
    lbvserver_list = lbvserver.get_filtered(client, 'name:%s' % module.params['name'])
    return lbvserver_proxy.diff_object(lbvserver_list[0])


def get_configured_service_bindings(client, module):
    log('Getting configured service bindings')

    readwrite_attrs = [
        'weight',
        'name',
        'servicename',
        'servicegroupname'
    ]
    readonly_attrs = [
        'preferredlocation',
        'vserverid',
        'vsvrbindsvcip',
        'servicetype',
        'cookieipport',
        'port',
        'vsvrbindsvcport',
        'curstate',
        'ipv46',
        'dynamicweight',
    ]

    configured_bindings = {}
    if 'servicebindings' in module.params and module.params['servicebindings'] is not None:
        for binding in module.params['servicebindings']:
            attribute_values_dict = copy.deepcopy(binding)
            attribute_values_dict['name'] = module.params['name']
            key = binding['servicename'].strip()
            configured_bindings[key] = ConfigProxy(
                actual=lbvserver_service_binding(),
                client=client,
                attribute_values_dict=attribute_values_dict,
                readwrite_attrs=readwrite_attrs,
                readonly_attrs=readonly_attrs,
            )
    return configured_bindings


def get_configured_servicegroup_bindings(client, module):
    log('Getting configured service group bindings')
    readwrite_attrs = [
        'weight',
        'name',
        'servicename',
        'servicegroupname',
    ]
    readonly_attrs = []

    configured_bindings = {}

    if 'servicegroupbindings' in module.params and module.params['servicegroupbindings'] is not None:
        for binding in module.params['servicegroupbindings']:
            attribute_values_dict = copy.deepcopy(binding)
            attribute_values_dict['name'] = module.params['name']
            key = binding['servicegroupname'].strip()
            configured_bindings[key] = ConfigProxy(
                actual=lbvserver_servicegroup_binding(),
                client=client,
                attribute_values_dict=attribute_values_dict,
                readwrite_attrs=readwrite_attrs,
                readonly_attrs=readonly_attrs,
            )

    return configured_bindings


def get_actual_service_bindings(client, module):
    log('Getting actual service bindings')
    bindings = {}
    try:
        if lbvserver_service_binding.count(client, module.params['name']) == 0:
            return bindings
    except nitro_exception as e:
        if e.errorcode == 258:
            return bindings
        else:
            raise

    bindigs_list = lbvserver_service_binding.get(client, module.params['name'])

    for item in bindigs_list:
        key = item.servicename
        bindings[key] = item

    return bindings


def get_actual_servicegroup_bindings(client, module):
    log('Getting actual service group bindings')
    bindings = {}

    try:
        if lbvserver_servicegroup_binding.count(client, module.params['name']) == 0:
            return bindings
    except nitro_exception as e:
        if e.errorcode == 258:
            return bindings
        else:
            raise

    bindigs_list = lbvserver_servicegroup_binding.get(client, module.params['name'])

    for item in bindigs_list:
        key = item.servicegroupname
        bindings[key] = item

    return bindings


def service_bindings_identical(client, module):
    log('service_bindings_identical')

    # Compare service keysets
    configured_service_bindings = get_configured_service_bindings(client, module)
    service_bindings = get_actual_service_bindings(client, module)
    configured_keyset = set(configured_service_bindings.keys())
    service_keyset = set(service_bindings.keys())
    if len(configured_keyset ^ service_keyset) > 0:
        return False

    # Compare service item to item
    for key in configured_service_bindings.keys():
        conf = configured_service_bindings[key]
        serv = service_bindings[key]
        log('s diff %s' % conf.diff_object(serv))
        if not conf.has_equal_attributes(serv):
            return False

    # Fallthrough to success
    return True


def servicegroup_bindings_identical(client, module):
    log('servicegroup_bindings_identical')

    # Compare servicegroup keysets
    configured_servicegroup_bindings = get_configured_servicegroup_bindings(client, module)
    servicegroup_bindings = get_actual_servicegroup_bindings(client, module)
    configured_keyset = set(configured_servicegroup_bindings.keys())
    service_keyset = set(servicegroup_bindings.keys())
    log('len %s' % len(configured_keyset ^ service_keyset))
    if len(configured_keyset ^ service_keyset) > 0:
        return False

    # Compare servicegroup item to item
    for key in configured_servicegroup_bindings.keys():
        conf = configured_servicegroup_bindings[key]
        serv = servicegroup_bindings[key]
        log('sg diff %s' % conf.diff_object(serv))
        if not conf.has_equal_attributes(serv):
            return False

    # Fallthrough to success
    return True


def sync_service_bindings(client, module):
    log('sync_service_bindings')

    actual_bindings = get_actual_service_bindings(client, module)
    configured_bindigns = get_configured_service_bindings(client, module)

    # Delete actual but not configured
    delete_keys = list(set(actual_bindings.keys()) - set(configured_bindigns.keys()))
    for key in delete_keys:
        log('Deleting service binding %s' % key)
        actual_bindings[key].servicegroupname = ''
        actual_bindings[key].delete(client, actual_bindings[key])

    # Add configured but not in actual
    add_keys = list(set(configured_bindigns.keys()) - set(actual_bindings.keys()))
    for key in add_keys:
        log('Adding service binding %s' % key)
        configured_bindigns[key].add()

    # Update existing if changed
    modify_keys = list(set(configured_bindigns.keys()) & set(actual_bindings.keys()))
    for key in modify_keys:
        if not configured_bindigns[key].has_equal_attributes(actual_bindings[key]):
            log('Updating service binding %s' % key)
            actual_bindings[key].servicegroupname = ''
            actual_bindings[key].delete(client, actual_bindings[key])
            configured_bindigns[key].add()


def sync_servicegroup_bindings(client, module):
    log('sync_servicegroup_bindings')

    actual_bindings = get_actual_servicegroup_bindings(client, module)
    configured_bindigns = get_configured_servicegroup_bindings(client, module)

    # Delete actual but not configured
    delete_keys = list(set(actual_bindings.keys()) - set(configured_bindigns.keys()))
    for key in delete_keys:
        log('Deleting servicegroup binding %s' % key)
        actual_bindings[key].servicename = None
        actual_bindings[key].delete(client, actual_bindings[key])

    # Add configured but not in actual
    add_keys = list(set(configured_bindigns.keys()) - set(actual_bindings.keys()))
    for key in add_keys:
        log('Adding servicegroup binding %s' % key)
        configured_bindigns[key].add()

    # Update existing if changed
    modify_keys = list(set(configured_bindigns.keys()) & set(actual_bindings.keys()))
    for key in modify_keys:
        if not configured_bindigns[key].has_equal_attributes(actual_bindings[key]):
            log('Updating servicegroup binding %s' % key)
            actual_bindings[key].servicename = None
            actual_bindings[key].delete(client, actual_bindings[key])
            configured_bindigns[key].add()


def ssl_certkey_bindings_identical(client, module):
    log('Entering ssl_certkey_bindings_identical')
    vservername = module.params['name']

    if sslvserver_sslcertkey_binding.count(client, vservername) == 0:
        bindings = []
    else:
        bindings = sslvserver_sslcertkey_binding.get(client, vservername)

    log('Existing certs %s' % bindings)

    if module.params['ssl_certkey'] is None:
        if len(bindings) == 0:
            return True
        else:
            return False
    else:
        certificate_list = [item.certkeyname for item in bindings]
        log('certificate_list %s' % certificate_list)
        if certificate_list == [module.params['ssl_certkey']]:
            return True
        else:
            return False


def ssl_certkey_bindings_sync(client, module):
    log('Syncing ssl certificates')
    vservername = module.params['name']
    if sslvserver_sslcertkey_binding.count(client, vservername) == 0:
        bindings = []
    else:
        bindings = sslvserver_sslcertkey_binding.get(client, vservername)
    log('bindings len is %s' % len(bindings))

    # Delete existing bindings
    for binding in bindings:
        sslvserver_sslcertkey_binding.delete(client, binding)

    # Add binding if appropriate
    if module.params['ssl_certkey'] is not None:
        binding = sslvserver_sslcertkey_binding()
        binding.vservername = module.params['name']
        binding.certkeyname = module.params['ssl_certkey']
        sslvserver_sslcertkey_binding.add(client, binding)


def do_state_change(client, module, lbvserver_proxy):
    if module.params['disabled']:
        log('Disabling lb server')
        result = lbvserver.disable(client, lbvserver_proxy.actual)
    else:
        log('Enabling lb server')
        result = lbvserver.enable(client, lbvserver_proxy.actual)
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
                'DTLS',
                'NNTP',
                'DNS',
                'DHCPRA',
                'ANY',
                'SIP_UDP',
                'SIP_TCP',
                'SIP_SSL',
                'DNS_TCP',
                'RTSP',
                'PUSH',
                'SSL_PUSH',
                'RADIUS',
                'RDP',
                'MYSQL',
                'MSSQL',
                'DIAMETER',
                'SSL_DIAMETER',
                'TFTP',
                'ORACLE',
                'SMPP',
                'SYSLOGTCP',
                'SYSLOGUDP',
                'FIX',
                'SSL_FIX',
            ]
        ),
        ipv46=dict(type='str'),
        ippattern=dict(type='str'),
        ipmask=dict(type='str'),
        port=dict(type='int'),
        range=dict(type='float'),
        persistencetype=dict(
            type='str',
            choices=[
                'SOURCEIP',
                'COOKIEINSERT',
                'SSLSESSION',
                'RULE',
                'URLPASSIVE',
                'CUSTOMSERVERID',
                'DESTIP',
                'SRCIPDESTIP',
                'CALLID',
                'RTSPSID',
                'DIAMETER',
                'FIXSESSION',
                'NONE',
            ]
        ),
        timeout=dict(type='float'),
        persistencebackup=dict(
            type='str',
            choices=[
                'SOURCEIP',
                'NONE',
            ]
        ),
        backuppersistencetimeout=dict(type='float'),
        lbmethod=dict(
            type='str',
            choices=[
                'ROUNDROBIN',
                'LEASTCONNECTION',
                'LEASTRESPONSETIME',
                'URLHASH',
                'DOMAINHASH',
                'DESTINATIONIPHASH',
                'SOURCEIPHASH',
                'SRCIPDESTIPHASH',
                'LEASTBANDWIDTH',
                'LEASTPACKETS',
                'TOKEN',
                'SRCIPSRCPORTHASH',
                'LRTM',
                'CALLIDHASH',
                'CUSTOMLOAD',
                'LEASTREQUEST',
                'AUDITLOGHASH',
                'STATICPROXIMITY',
            ]
        ),
        hashlength=dict(type='float'),
        netmask=dict(type='str'),
        v6netmasklen=dict(type='float'),
        backuplbmethod=dict(
            type='str',
            choices=[
                'ROUNDROBIN',
                'LEASTCONNECTION',
                'LEASTRESPONSETIME',
                'SOURCEIPHASH',
                'LEASTBANDWIDTH',
                'LEASTPACKETS',
                'CUSTOMLOAD',
            ]
        ),
        cookiename=dict(type='str'),
        listenpolicy=dict(type='str'),
        listenpriority=dict(type='float'),
        persistmask=dict(type='str'),
        v6persistmasklen=dict(type='float'),
        rtspnat=dict(type='bool'),
        m=dict(
            type='str',
            choices=[
                'IP',
                'MAC',
                'IPTUNNEL',
                'TOS',
            ]
        ),
        tosid=dict(type='float'),
        datalength=dict(type='float'),
        dataoffset=dict(type='float'),
        sessionless=dict(
            type='str',
            choices=[
                'enabled',
                'disabled',
            ]
        ),
        connfailover=dict(
            type='str',
            choices=[
                'DISABLED',
                'STATEFUL',
                'STATELESS',
            ]
        ),
        redirurl=dict(type='str'),
        cacheable=dict(type='bool'),
        clttimeout=dict(type='float'),
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
                'enabled',
                'disabled',
            ]
        ),
        sopersistencetimeout=dict(type='float'),
        healththreshold=dict(type='float'),
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
                'enabled',
                'disabled',
            ]
        ),
        downstateflush=dict(
            type='str',
            choices=[
                'enabled',
                'disabled',
            ]
        ),
        disableprimaryondown=dict(
            type='str',
            choices=[
                'enabled',
                'disabled',
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
        authenticationhost=dict(type='str'),
        authentication=dict(type='bool'),
        authn401=dict(type='bool'),
        authnvsname=dict(type='str'),
        push=dict(
            type='str',
            choices=[
                'enabled',
                'disabled',
            ]
        ),
        pushvserver=dict(type='str'),
        pushlabel=dict(type='str'),
        pushmulticlients=dict(type='bool'),
        tcpprofilename=dict(type='str'),
        httpprofilename=dict(type='str'),
        dbprofilename=dict(type='str'),
        comment=dict(type='str'),
        l2conn=dict(type='bool'),
        oracleserverversion=dict(
            type='str',
            choices=[
                '10G',
                '11G',
            ]
        ),
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
        mysqlprotocolversion=dict(type='float'),
        mysqlserverversion=dict(type='str'),
        mysqlcharacterset=dict(type='float'),
        mysqlservercapabilities=dict(type='float'),
        appflowlog=dict(
            type='str',
            choices=[
                'enabled',
                'disabled',
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
        newservicerequest=dict(type='float'),
        newservicerequestunit=dict(
            type='str',
            choices=[
                'PER_SECOND',
                'PERCENT',
            ]
        ),
        newservicerequestincrementinterval=dict(type='float'),
        minautoscalemembers=dict(type='float'),
        maxautoscalemembers=dict(type='float'),
        skippersistency=dict(
            type='str',
            choices=[
                'Bypass',
                'ReLb',
                'None',
            ]
        ),
        authnprofile=dict(type='str'),
        macmoderetainvlan=dict(
            type='str',
            choices=[
                'enabled',
                'disabled',
            ]
        ),
        dbslb=dict(
            type='str',
            choices=[
                'enabled',
                'disabled',
            ]
        ),
        dns64=dict(
            type='str',
            choices=[
                'enabled',
                'disabled',
            ]
        ),
        bypassaaaa=dict(type='bool'),
        recursionavailable=dict(type='bool'),
        processlocal=dict(
            type='str',
            choices=[
                'enabled',
                'disabled',
            ]
        ),
        dnsprofilename=dict(type='str'),
    )

    hand_inserted_arguments = dict(
        servicebindings=dict(type='list'),
        servicegroupbindings=dict(type='list'),
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
        'servicetype',
        'ipv46',
        'ippattern',
        'ipmask',
        'port',
        'range',
        'persistencetype',
        'timeout',
        'persistencebackup',
        'backuppersistencetimeout',
        'lbmethod',
        'hashlength',
        'netmask',
        'v6netmasklen',
        'backuplbmethod',
        'cookiename',
        'listenpolicy',
        'listenpriority',
        'persistmask',
        'v6persistmasklen',
        'rtspnat',
        'm',
        'tosid',
        'datalength',
        'dataoffset',
        'sessionless',
        'connfailover',
        'redirurl',
        'cacheable',
        'clttimeout',
        'somethod',
        'sopersistence',
        'sopersistencetimeout',
        'healththreshold',
        'sothreshold',
        'sobackupaction',
        'redirectportrewrite',
        'downstateflush',
        'disableprimaryondown',
        'insertvserveripport',
        'vipheader',
        'authenticationhost',
        'authentication',
        'authn401',
        'authnvsname',
        'push',
        'pushvserver',
        'pushlabel',
        'pushmulticlients',
        'tcpprofilename',
        'httpprofilename',
        'dbprofilename',
        'comment',
        'l2conn',
        'oracleserverversion',
        'mssqlserverversion',
        'mysqlprotocolversion',
        'mysqlserverversion',
        'mysqlcharacterset',
        'mysqlservercapabilities',
        'appflowlog',
        'netprofile',
        'icmpvsrresponse',
        'rhistate',
        'newservicerequest',
        'newservicerequestunit',
        'newservicerequestincrementinterval',
        'minautoscalemembers',
        'maxautoscalemembers',
        'skippersistency',
        'authnprofile',
        'macmoderetainvlan',
        'dbslb',
        'dns64',
        'bypassaaaa',
        'recursionavailable',
        'processlocal',
        'dnsprofilename',
    ]

    readonly_attrs = [
        'value',
        'ipmapping',
        'ngname',
        'type',
        'curstate',
        'effectivestate',
        'status',
        'lbrrreason',
        'redirect',
        'precedence',
        'homepage',
        'dnsvservername',
        'domain',
        'policyname',
        'cachevserver',
        'health',
        'gotopriorityexpression',
        'ruletype',
        'groupname',
        'cookiedomain',
        'map',
        'gt2gb',
        'consolidatedlconn',
        'consolidatedlconngbl',
        'thresholdvalue',
        'bindpoint',
        'invoke',
        'labeltype',
        'labelname',
        'version',
        'totalservices',
        'activeservices',
        'statechangetimesec',
        'statechangetimeseconds',
        'statechangetimemsec',
        'tickssincelaststatechange',
        'isgslb',
        'vsvrdynconnsothreshold',
        'backupvserverstatus',
        '__count',
    ]

    immutable_attrs = [
        'name',
        'servicetype',
        'ipv46',
        'port',
        'range',
        'state',
        'redirurl',
        'vipheader',
        'newservicerequestunit',
        'td',
    ]

    transforms = {
        'rtspnat': ['bool_on_off'],
        'authn401': ['bool_on_off'],
        'bypassaaaa': ['bool_yes_no'],
        'authentication': ['bool_on_off'],
        'cacheable': ['bool_yes_no'],
        'l2conn': ['bool_on_off'],
        'pushmulticlients': ['bool_yes_no'],
        'recursionavailable': ['bool_yes_no'],
        'sessionless': [lambda v: v.upper()],
        'sopersistence': [lambda v: v.upper()],
        'redirectportrewrite': [lambda v: v.upper()],
        'downstateflush': [lambda v: v.upper()],
        'disableprimaryondown': [lambda v: v.upper()],
        'push': [lambda v: v.upper()],
        'appflowlog': [lambda v: v.upper()],
        'macmoderetainvlan': [lambda v: v.upper()],
        'dbslb': [lambda v: v.upper()],
        'dns64': [lambda v: v.upper()],
        'processlocal': [lambda v: v.upper()],
    }

    lbvserver_proxy = ConfigProxy(
        actual=lbvserver(),
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

            if not lb_vserver_exists(client, module):
                log('Add lb vserver')
                if not module.check_mode:
                    lbvserver_proxy.add()
                    if module.params['save_config']:
                        client.save_config()
                module_result['changed'] = True
            elif not lb_vserver_identical(client, module, lbvserver_proxy):

                # Check if we try to change value of immutable attributes
                diff_dict = lb_vserver_diff(client, module, lbvserver_proxy)
                immutables_changed = get_immutables_intersection(lbvserver_proxy, diff_dict.keys())
                if immutables_changed != []:
                    msg = 'Cannot update immutable attributes %s. Must delete and recreate entity.' % (immutables_changed,)
                    module.fail_json(msg=msg, diff=diff_dict, **module_result)

                log('Update lb vserver')
                if not module.check_mode:
                    lbvserver_proxy.update()
                    if module.params['save_config']:
                        client.save_config()
                module_result['changed'] = True
            else:
                log('Present noop')

            if not service_bindings_identical(client, module):
                if not module.check_mode:
                    sync_service_bindings(client, module)
                    if module.params['save_config']:
                        client.save_config()
                module_result['changed'] = True

            if not servicegroup_bindings_identical(client, module):
                if not module.check_mode:
                    sync_servicegroup_bindings(client, module)
                    if module.params['save_config']:
                        client.save_config()
                module_result['changed'] = True

            if module.params['servicetype'] != 'SSL' and module.params['ssl_certkey'] is not None:
                module.fail_json(msg='ssl_certkey is applicable only to SSL vservers', **module_result)

            # Check if SSL certkey is sane
            if module.params['servicetype'] == 'SSL':
                if not ssl_certkey_bindings_identical(client, module):
                    if not module.check_mode:
                        ssl_certkey_bindings_sync(client, module)

                    module_result['changed'] = True

            if not module.check_mode:
                res = do_state_change(client, module, lbvserver_proxy)
                if res.errorcode != 0:
                    msg = 'Error when setting disabled state. errorcode: %s message: %s' % (res.errorcode, res.message)
                    module.fail_json(msg=msg, **module_result)

            # Sanity check
            log('Sanity checks for state present')
            if not module.check_mode:
                if not lb_vserver_exists(client, module):
                    module.fail_json(msg='Did not create lb vserver', **module_result)

                if not lb_vserver_identical(client, module, lbvserver_proxy):
                    msg = 'lb vserver is not configured correctly'
                    module.fail_json(msg=msg, diff=lb_vserver_diff(client, module, lbvserver_proxy), **module_result)

                if not service_bindings_identical(client, module):
                    module.fail_json(msg='service bindings are not identical', **module_result)

                if not servicegroup_bindings_identical(client, module):
                    module.fail_json(msg='servicegroup bindings are not identical', **module_result)

                if module.params['servicetype'] == 'SSL':
                    if not ssl_certkey_bindings_identical(client, module):
                        module.fail_json(msg='sll certkey bindings not identical', **module_result)

        elif module.params['state'] == 'absent':
            log('Applying actions for state absent')
            if lb_vserver_exists(client, module):
                if not module.check_mode:
                    log('Delete lb vserver')
                    lbvserver_proxy.delete()
                    if module.params['save_config']:
                        client.save_config()
                module_result['changed'] = True
            else:
                log('Absent noop')
                module_result['changed'] = False

            # Sanity check
            log('Sanity checks for state absent')
            if not module.check_mode:
                if lb_vserver_exists(client, module):
                    module.fail_json(msg='lb vserver still exists', **module_result)

    except nitro_exception as e:
        msg = "nitro exception errorcode=%s, message=%s" % (str(e.errorcode), e.message)
        module.fail_json(msg=msg, **module_result)

    client.logout()
    module.exit_json(**module_result)


if __name__ == "__main__":
    main()
