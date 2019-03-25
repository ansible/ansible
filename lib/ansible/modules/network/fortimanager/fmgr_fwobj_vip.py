#!/usr/bin/python
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.
#

from __future__ import absolute_import, division, print_function

__metaclass__ = type

ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'metadata_version': '1.1'}

DOCUMENTATION = '''
---
module: fmgr_fwobj_vip
version_added: "2.8"
notes:
    - Full Documentation at U(https://ftnt-ansible-docs.readthedocs.io/en/latest/).
author:
    - Luke Weighall (@lweighall)
    - Andrew Welsh (@Ghilli3)
    - Jim Huber (@p4r4n0y1ng)
short_description: Manages Virtual IPs objects in FortiManager
description:
  -  Manages Virtual IP objects in FortiManager for IPv4

options:
  adom:
    description:
      - The ADOM the configuration should belong to.
    required: false
    default: root

  mode:
    description:
      - Sets one of three modes for managing the object.
      - Allows use of soft-adds instead of overwriting existing values
    choices: ['add', 'set', 'delete', 'update']
    required: false
    default: add

  websphere_server:
    description:
      - Enable to add an HTTP header to indicate SSL offloading for a WebSphere server.
      - choice | disable | Do not add HTTP header indicating SSL offload for WebSphere server.
      - choice | enable | Add HTTP header indicating SSL offload for WebSphere server.
    required: false
    choices: ["disable", "enable"]

  weblogic_server:
    description:
      - Enable to add an HTTP header to indicate SSL offloading for a WebLogic server.
      - choice | disable | Do not add HTTP header indicating SSL offload for WebLogic server.
      - choice | enable | Add HTTP header indicating SSL offload for WebLogic server.
    required: false
    choices: ["disable", "enable"]

  type:
    description:
      - Configure a static NAT, load balance, server load balance, DNS translation, or FQDN VIP.
      - choice | static-nat | Static NAT.
      - choice | load-balance | Load balance.
      - choice | server-load-balance | Server load balance.
      - choice | dns-translation | DNS translation.
      - choice | fqdn | FQDN Translation
    required: false
    choices: ["static-nat", "load-balance", "server-load-balance", "dns-translation", "fqdn"]

  ssl_server_session_state_type:
    description:
      - How to expire SSL sessions for the segment of the SSL connection between the server and the FortiGate.
      - choice | disable | Do not keep session states.
      - choice | time | Expire session states after this many minutes.
      - choice | count | Expire session states when this maximum is reached.
      - choice | both | Expire session states based on time or count, whichever occurs first.
    required: false
    choices: ["disable", "time", "count", "both"]

  ssl_server_session_state_timeout:
    description:
      - Number of minutes to keep FortiGate to Server SSL session state.
    required: false

  ssl_server_session_state_max:
    description:
      - Maximum number of FortiGate to Server SSL session states to keep.
    required: false

  ssl_server_min_version:
    description:
      - Lowest SSL/TLS version acceptable from a server. Use the client setting by default.
      - choice | ssl-3.0 | SSL 3.0.
      - choice | tls-1.0 | TLS 1.0.
      - choice | tls-1.1 | TLS 1.1.
      - choice | tls-1.2 | TLS 1.2.
      - choice | client | Use same value as client configuration.
    required: false
    choices: ["ssl-3.0", "tls-1.0", "tls-1.1", "tls-1.2", "client"]

  ssl_server_max_version:
    description:
      - Highest SSL/TLS version acceptable from a server. Use the client setting by default.
      - choice | ssl-3.0 | SSL 3.0.
      - choice | tls-1.0 | TLS 1.0.
      - choice | tls-1.1 | TLS 1.1.
      - choice | tls-1.2 | TLS 1.2.
      - choice | client | Use same value as client configuration.
    required: false
    choices: ["ssl-3.0", "tls-1.0", "tls-1.1", "tls-1.2", "client"]

  ssl_server_algorithm:
    description:
      - Permitted encryption algorithms for the server side of SSL full mode sessions according to encryption strength
      - choice | high | High encryption. Allow only AES and ChaCha.
      - choice | low | Low encryption. Allow AES, ChaCha, 3DES, RC4, and DES.
      - choice | medium | Medium encryption. Allow AES, ChaCha, 3DES, and RC4.
      - choice | custom | Custom encryption. Use ssl-server-cipher-suites to select the cipher suites that are allowed.
      - choice | client | Use the same encryption algorithms for both client and server sessions.
    required: false
    choices: ["high", "low", "medium", "custom", "client"]

  ssl_send_empty_frags:
    description:
      - Enable/disable sending empty fragments to avoid CBC IV attacks (SSL 3.0 &amp; TLS 1.0 only).
      - choice | disable | Do not send empty fragments.
      - choice | enable | Send empty fragments.
    required: false
    choices: ["disable", "enable"]

  ssl_pfs:
    description:
      - Select the cipher suites that can be used for SSL perfect forward secrecy (PFS).
      - choice | require | Allow only Diffie-Hellman cipher-suites, so PFS is applied.
      - choice | deny | Allow only non-Diffie-Hellman cipher-suites, so PFS is not applied.
      - choice | allow | Allow use of any cipher suite so PFS may or may not be used depending on the cipher suite
    required: false
    choices: ["require", "deny", "allow"]

  ssl_mode:
    description:
      - Apply SSL offloading mode
      - choice | half | Client to FortiGate SSL.
      - choice | full | Client to FortiGate and FortiGate to Server SSL.
    required: false
    choices: ["half", "full"]

  ssl_min_version:
    description:
      - Lowest SSL/TLS version acceptable from a client.
      - choice | ssl-3.0 | SSL 3.0.
      - choice | tls-1.0 | TLS 1.0.
      - choice | tls-1.1 | TLS 1.1.
      - choice | tls-1.2 | TLS 1.2.
    required: false
    choices: ["ssl-3.0", "tls-1.0", "tls-1.1", "tls-1.2"]

  ssl_max_version:
    description:
      - Highest SSL/TLS version acceptable from a client.
      - choice | ssl-3.0 | SSL 3.0.
      - choice | tls-1.0 | TLS 1.0.
      - choice | tls-1.1 | TLS 1.1.
      - choice | tls-1.2 | TLS 1.2.
    required: false
    choices: ["ssl-3.0", "tls-1.0", "tls-1.1", "tls-1.2"]

  ssl_http_match_host:
    description:
      - Enable/disable HTTP host matching for location conversion.
      - choice | disable | Do not match HTTP host.
      - choice | enable | Match HTTP host in response header.
    required: false
    choices: ["disable", "enable"]

  ssl_http_location_conversion:
    description:
      - Enable to replace HTTP with HTTPS in the reply's Location HTTP header field.
      - choice | disable | Disable HTTP location conversion.
      - choice | enable | Enable HTTP location conversion.
    required: false
    choices: ["disable", "enable"]

  ssl_hsts_include_subdomains:
    description:
      - Indicate that HSTS header applies to all subdomains.
      - choice | disable | HSTS header does not apply to subdomains.
      - choice | enable | HSTS header applies to subdomains.
    required: false
    choices: ["disable", "enable"]

  ssl_hsts_age:
    description:
      - Number of seconds the client should honour the HSTS setting.
    required: false

  ssl_hsts:
    description:
      - Enable/disable including HSTS header in response.
      - choice | disable | Do not add a HSTS header to each a HTTP response.
      - choice | enable | Add a HSTS header to each HTTP response.
    required: false
    choices: ["disable", "enable"]

  ssl_hpkp_report_uri:
    description:
      - URL to report HPKP violations to.
    required: false

  ssl_hpkp_primary:
    description:
      - Certificate to generate primary HPKP pin from.
    required: false

  ssl_hpkp_include_subdomains:
    description:
      - Indicate that HPKP header applies to all subdomains.
      - choice | disable | HPKP header does not apply to subdomains.
      - choice | enable | HPKP header applies to subdomains.
    required: false
    choices: ["disable", "enable"]

  ssl_hpkp_backup:
    description:
      - Certificate to generate backup HPKP pin from.
    required: false

  ssl_hpkp_age:
    description:
      - Number of seconds the client should honour the HPKP setting.
    required: false

  ssl_hpkp:
    description:
      - Enable/disable including HPKP header in response.
      - choice | disable | Do not add a HPKP header to each HTTP response.
      - choice | enable | Add a HPKP header to each a HTTP response.
      - choice | report-only | Add a HPKP Report-Only header to each HTTP response.
    required: false
    choices: ["disable", "enable", "report-only"]

  ssl_dh_bits:
    description:
      - Number of bits to use in the Diffie-Hellman exchange for RSA encryption of SSL sessions.
      - choice | 768 | 768-bit Diffie-Hellman prime.
      - choice | 1024 | 1024-bit Diffie-Hellman prime.
      - choice | 1536 | 1536-bit Diffie-Hellman prime.
      - choice | 2048 | 2048-bit Diffie-Hellman prime.
      - choice | 3072 | 3072-bit Diffie-Hellman prime.
      - choice | 4096 | 4096-bit Diffie-Hellman prime.
    required: false
    choices: ["768", "1024", "1536", "2048", "3072", "4096"]

  ssl_client_session_state_type:
    description:
      - How to expire SSL sessions for the segment of the SSL connection between the client and the FortiGate.
      - choice | disable | Do not keep session states.
      - choice | time | Expire session states after this many minutes.
      - choice | count | Expire session states when this maximum is reached.
      - choice | both | Expire session states based on time or count, whichever occurs first.
    required: false
    choices: ["disable", "time", "count", "both"]

  ssl_client_session_state_timeout:
    description:
      - Number of minutes to keep client to FortiGate SSL session state.
    required: false

  ssl_client_session_state_max:
    description:
      - Maximum number of client to FortiGate SSL session states to keep.
    required: false

  ssl_client_renegotiation:
    description:
      - Allow, deny, or require secure renegotiation of client sessions to comply with RFC 5746.
      - choice | deny | Abort any client initiated SSL re-negotiation attempt.
      - choice | allow | Allow a SSL client to renegotiate.
      - choice | secure | Abort any client initiated SSL re-negotiation attempt that does not use RFC 5746.
    required: false
    choices: ["deny", "allow", "secure"]

  ssl_client_fallback:
    description:
      - Enable/disable support for preventing Downgrade Attacks on client connections (RFC 7507).
      - choice | disable | Disable.
      - choice | enable | Enable.
    required: false
    choices: ["disable", "enable"]

  ssl_certificate:
    description:
      - The name of the SSL certificate to use for SSL acceleration.
    required: false

  ssl_algorithm:
    description:
      - Permitted encryption algorithms for SSL sessions according to encryption strength.
      - choice | high | High encryption. Allow only AES and ChaCha.
      - choice | medium | Medium encryption. Allow AES, ChaCha, 3DES, and RC4.
      - choice | low | Low encryption. Allow AES, ChaCha, 3DES, RC4, and DES.
      - choice | custom | Custom encryption. Use config ssl-cipher-suites to select the cipher suites that are allowed.
    required: false
    choices: ["high", "medium", "low", "custom"]

  srcintf_filter:
    description:
      - Interfaces to which the VIP applies. Separate the names with spaces.
    required: false

  src_filter:
    description:
      - Source address filter. Each address must be either an IP/subnet (x.x.x.x/n) or a range (x.x.x.x-y.y.y.y).
      - Separate addresses with spaces.
    required: false

  service:
    description:
      - Service name.
    required: false

  server_type:
    description:
      - Protocol to be load balanced by the virtual server (also called the server load balance virtual IP).
      - choice | http | HTTP
      - choice | https | HTTPS
      - choice | ssl | SSL
      - choice | tcp | TCP
      - choice | udp | UDP
      - choice | ip | IP
      - choice | imaps | IMAPS
      - choice | pop3s | POP3S
      - choice | smtps | SMTPS
    required: false
    choices: ["http", "https", "ssl", "tcp", "udp", "ip", "imaps", "pop3s", "smtps"]

  protocol:
    description:
      - Protocol to use when forwarding packets.
      - choice | tcp | TCP.
      - choice | udp | UDP.
      - choice | sctp | SCTP.
      - choice | icmp | ICMP.
    required: false
    choices: ["tcp", "udp", "sctp", "icmp"]

  portmapping_type:
    description:
      - Port mapping type.
      - choice | 1-to-1 | One to one.
      - choice | m-to-n | Many to many.
    required: false
    choices: ["1-to-1", "m-to-n"]

  portforward:
    description:
      - Enable/disable port forwarding.
      - choice | disable | Disable port forward.
      - choice | enable | Enable port forward.
    required: false
    choices: ["disable", "enable"]

  persistence:
    description:
      - Configure how to make sure that clients connect to the same server every time they make a request that is part
      - of the same session.
      - choice | none | None.
      - choice | http-cookie | HTTP cookie.
      - choice | ssl-session-id | SSL session ID.
    required: false
    choices: ["none", "http-cookie", "ssl-session-id"]

  outlook_web_access:
    description:
      - Enable to add the Front-End-Https header for Microsoft Outlook Web Access.
      - choice | disable | Disable Outlook Web Access support.
      - choice | enable | Enable Outlook Web Access support.
    required: false
    choices: ["disable", "enable"]

  nat_source_vip:
    description:
      - Enable to prevent unintended servers from using a virtual IP.
      - Disable to use the actual IP address of the server as the source address.
      - choice | disable | Do not force to NAT as VIP.
      - choice | enable | Force to NAT as VIP.
    required: false
    choices: ["disable", "enable"]

  name:
    description:
      - Virtual IP name.
    required: false

  monitor:
    description:
      - Name of the health check monitor to use when polling to determine a virtual server's connectivity status.
    required: false

  max_embryonic_connections:
    description:
      - Maximum number of incomplete connections.
    required: false

  mappedport:
    description:
      - Port number range on the destination network to which the external port number range is mapped.
    required: false

  mappedip:
    description:
      - IP address or address range on the destination network to which the external IP address is mapped.
    required: false

  mapped_addr:
    description:
      - Mapped FQDN address name.
    required: false

  ldb_method:
    description:
      - Method used to distribute sessions to real servers.
      - choice | static | Distribute to server based on source IP.
      - choice | round-robin | Distribute to server based round robin order.
      - choice | weighted | Distribute to server based on weight.
      - choice | least-session | Distribute to server with lowest session count.
      - choice | least-rtt | Distribute to server with lowest Round-Trip-Time.
      - choice | first-alive | Distribute to the first server that is alive.
      - choice | http-host | Distribute to server based on host field in HTTP header.
    required: false
    choices: ["static", "round-robin", "weighted", "least-session", "least-rtt", "first-alive", "http-host"]

  https_cookie_secure:
    description:
      - Enable/disable verification that inserted HTTPS cookies are secure.
      - choice | disable | Do not mark cookie as secure, allow sharing between an HTTP and HTTPS connection.
      - choice | enable | Mark inserted cookie as secure, cookie can only be used for HTTPS a connection.
    required: false
    choices: ["disable", "enable"]

  http_multiplex:
    description:
      - Enable/disable HTTP multiplexing.
      - choice | disable | Disable HTTP session multiplexing.
      - choice | enable | Enable HTTP session multiplexing.
    required: false
    choices: ["disable", "enable"]

  http_ip_header_name:
    description:
      - For HTTP multiplexing, enter a custom HTTPS header name. The orig client IP address is added to this header.
      - If empty, X-Forwarded-For is used.
    required: false

  http_ip_header:
    description:
      - For HTTP multiplexing, enable to add the original client IP address in the XForwarded-For HTTP header.
      - choice | disable | Disable adding HTTP header.
      - choice | enable | Enable adding HTTP header.
    required: false
    choices: ["disable", "enable"]

  http_cookie_share:
    description:
      - Control sharing of cookies across virtual servers. same-ip means a cookie from one virtual server can be used
      - by another. Disable stops cookie sharing.
      - choice | disable | Only allow HTTP cookie to match this virtual server.
      - choice | same-ip | Allow HTTP cookie to match any virtual server with same IP.
    required: false
    choices: ["disable", "same-ip"]

  http_cookie_path:
    description:
      - Limit HTTP cookie persistence to the specified path.
    required: false

  http_cookie_generation:
    description:
      - Generation of HTTP cookie to be accepted. Changing invalidates all existing cookies.
    required: false

  http_cookie_domain_from_host:
    description:
      - Enable/disable use of HTTP cookie domain from host field in HTTP.
      - choice | disable | Disable use of HTTP cookie domain from host field in HTTP (use http-cooke-domain setting).
      - choice | enable | Enable use of HTTP cookie domain from host field in HTTP.
    required: false
    choices: ["disable", "enable"]

  http_cookie_domain:
    description:
      - Domain that HTTP cookie persistence should apply to.
    required: false

  http_cookie_age:
    description:
      - Time in minutes that client web browsers should keep a cookie. Default is 60 seconds. 0 = no time limit.
    required: false

  gratuitous_arp_interval:
    description:
      - Enable to have the VIP send gratuitous ARPs. 0=disabled. Set from 5 up to 8640000 seconds to enable.
    required: false

  extport:
    description:
      - Incoming port number range that you want to map to a port number range on the destination network.
    required: false

  extip:
    description:
      - IP address or address range on the external interface that you want to map to an address or address range on t
      - he destination network.
    required: false

  extintf:
    description:
      - Interface connected to the source network that receives the packets that will be forwarded to the destination
      - network.
    required: false

  extaddr:
    description:
      - External FQDN address name.
    required: false

  dns_mapping_ttl:
    description:
      - DNS mapping TTL (Set to zero to use TTL in DNS response, default = 0).
    required: false

  comment:
    description:
      - Comment.
    required: false

  color:
    description:
      - Color of icon on the GUI.
    required: false

  arp_reply:
    description:
      - Enable to respond to ARP requests for this virtual IP address. Enabled by default.
      - choice | disable | Disable ARP reply.
      - choice | enable | Enable ARP reply.
    required: false
    choices: ["disable", "enable"]

  dynamic_mapping:
    description:
      - EXPERTS ONLY! KNOWLEDGE OF FMGR JSON API IS REQUIRED!
      - List of multiple child objects to be added. Expects a list of dictionaries.
      - Dictionaries must use FortiManager API parameters, not the ansible ones listed below.
      - If submitted, all other prefixed sub-parameters ARE IGNORED.
      - This object is MUTUALLY EXCLUSIVE with its options.
      - We expect that you know what you are doing with these list parameters, and are leveraging the JSON API Guide.
      - WHEN IN DOUBT, USE THE SUB OPTIONS BELOW INSTEAD TO CREATE OBJECTS WITH MULTIPLE TASKS
    required: false

  dynamic_mapping_arp_reply:
    description:
      - Dynamic Mapping Version of Suffixed Option Name. Sub-Table. Same Descriptions as Parent.
      - choice | disable |
      - choice | enable |
    required: false
    choices: ["disable", "enable"]

  dynamic_mapping_color:
    description:
      - Dynamic Mapping Version of Suffixed Option Name. Sub-Table. Same Descriptions as Parent.
    required: false

  dynamic_mapping_comment:
    description:
      - Dynamic Mapping Version of Suffixed Option Name. Sub-Table. Same Descriptions as Parent.
    required: false

  dynamic_mapping_dns_mapping_ttl:
    description:
      - Dynamic Mapping Version of Suffixed Option Name. Sub-Table. Same Descriptions as Parent.
    required: false

  dynamic_mapping_extaddr:
    description:
      - Dynamic Mapping Version of Suffixed Option Name. Sub-Table. Same Descriptions as Parent.
    required: false

  dynamic_mapping_extintf:
    description:
      - Dynamic Mapping Version of Suffixed Option Name. Sub-Table. Same Descriptions as Parent.
    required: false

  dynamic_mapping_extip:
    description:
      - Dynamic Mapping Version of Suffixed Option Name. Sub-Table. Same Descriptions as Parent.
    required: false

  dynamic_mapping_extport:
    description:
      - Dynamic Mapping Version of Suffixed Option Name. Sub-Table. Same Descriptions as Parent.
    required: false

  dynamic_mapping_gratuitous_arp_interval:
    description:
      - Dynamic Mapping Version of Suffixed Option Name. Sub-Table. Same Descriptions as Parent.
    required: false

  dynamic_mapping_http_cookie_age:
    description:
      - Dynamic Mapping Version of Suffixed Option Name. Sub-Table. Same Descriptions as Parent.
    required: false

  dynamic_mapping_http_cookie_domain:
    description:
      - Dynamic Mapping Version of Suffixed Option Name. Sub-Table. Same Descriptions as Parent.
    required: false

  dynamic_mapping_http_cookie_domain_from_host:
    description:
      - Dynamic Mapping Version of Suffixed Option Name. Sub-Table. Same Descriptions as Parent.
      - choice | disable |
      - choice | enable |
    required: false
    choices: ["disable", "enable"]

  dynamic_mapping_http_cookie_generation:
    description:
      - Dynamic Mapping Version of Suffixed Option Name. Sub-Table. Same Descriptions as Parent.
    required: false

  dynamic_mapping_http_cookie_path:
    description:
      - Dynamic Mapping Version of Suffixed Option Name. Sub-Table. Same Descriptions as Parent.
    required: false

  dynamic_mapping_http_cookie_share:
    description:
      - Dynamic Mapping Version of Suffixed Option Name. Sub-Table. Same Descriptions as Parent.
      - choice | disable |
      - choice | same-ip |
    required: false
    choices: ["disable", "same-ip"]

  dynamic_mapping_http_ip_header:
    description:
      - Dynamic Mapping Version of Suffixed Option Name. Sub-Table. Same Descriptions as Parent.
      - choice | disable |
      - choice | enable |
    required: false
    choices: ["disable", "enable"]

  dynamic_mapping_http_ip_header_name:
    description:
      - Dynamic Mapping Version of Suffixed Option Name. Sub-Table. Same Descriptions as Parent.
    required: false

  dynamic_mapping_http_multiplex:
    description:
      - Dynamic Mapping Version of Suffixed Option Name. Sub-Table. Same Descriptions as Parent.
      - choice | disable |
      - choice | enable |
    required: false
    choices: ["disable", "enable"]

  dynamic_mapping_https_cookie_secure:
    description:
      - Dynamic Mapping Version of Suffixed Option Name. Sub-Table. Same Descriptions as Parent.
      - choice | disable |
      - choice | enable |
    required: false
    choices: ["disable", "enable"]

  dynamic_mapping_ldb_method:
    description:
      - Dynamic Mapping Version of Suffixed Option Name. Sub-Table. Same Descriptions as Parent.
      - choice | static |
      - choice | round-robin |
      - choice | weighted |
      - choice | least-session |
      - choice | least-rtt |
      - choice | first-alive |
      - choice | http-host |
    required: false
    choices: ["static", "round-robin", "weighted", "least-session", "least-rtt", "first-alive", "http-host"]

  dynamic_mapping_mapped_addr:
    description:
      - Dynamic Mapping Version of Suffixed Option Name. Sub-Table. Same Descriptions as Parent.
    required: false

  dynamic_mapping_mappedip:
    description:
      - Dynamic Mapping Version of Suffixed Option Name. Sub-Table. Same Descriptions as Parent.
    required: false

  dynamic_mapping_mappedport:
    description:
      - Dynamic Mapping Version of Suffixed Option Name. Sub-Table. Same Descriptions as Parent.
    required: false

  dynamic_mapping_max_embryonic_connections:
    description:
      - Dynamic Mapping Version of Suffixed Option Name. Sub-Table. Same Descriptions as Parent.
    required: false

  dynamic_mapping_monitor:
    description:
      - Dynamic Mapping Version of Suffixed Option Name. Sub-Table. Same Descriptions as Parent.
    required: false

  dynamic_mapping_nat_source_vip:
    description:
      - Dynamic Mapping Version of Suffixed Option Name. Sub-Table. Same Descriptions as Parent.
      - choice | disable |
      - choice | enable |
    required: false
    choices: ["disable", "enable"]

  dynamic_mapping_outlook_web_access:
    description:
      - Dynamic Mapping Version of Suffixed Option Name. Sub-Table. Same Descriptions as Parent.
      - choice | disable |
      - choice | enable |
    required: false
    choices: ["disable", "enable"]

  dynamic_mapping_persistence:
    description:
      - Dynamic Mapping Version of Suffixed Option Name. Sub-Table. Same Descriptions as Parent.
      - choice | none |
      - choice | http-cookie |
      - choice | ssl-session-id |
    required: false
    choices: ["none", "http-cookie", "ssl-session-id"]

  dynamic_mapping_portforward:
    description:
      - Dynamic Mapping Version of Suffixed Option Name. Sub-Table. Same Descriptions as Parent.
      - choice | disable |
      - choice | enable |
    required: false
    choices: ["disable", "enable"]

  dynamic_mapping_portmapping_type:
    description:
      - Dynamic Mapping Version of Suffixed Option Name. Sub-Table. Same Descriptions as Parent.
      - choice | 1-to-1 |
      - choice | m-to-n |
    required: false
    choices: ["1-to-1", "m-to-n"]

  dynamic_mapping_protocol:
    description:
      - Dynamic Mapping Version of Suffixed Option Name. Sub-Table. Same Descriptions as Parent.
      - choice | tcp |
      - choice | udp |
      - choice | sctp |
      - choice | icmp |
    required: false
    choices: ["tcp", "udp", "sctp", "icmp"]

  dynamic_mapping_server_type:
    description:
      - Dynamic Mapping Version of Suffixed Option Name. Sub-Table. Same Descriptions as Parent.
      - choice | http |
      - choice | https |
      - choice | ssl |
      - choice | tcp |
      - choice | udp |
      - choice | ip |
      - choice | imaps |
      - choice | pop3s |
      - choice | smtps |
    required: false
    choices: ["http", "https", "ssl", "tcp", "udp", "ip", "imaps", "pop3s", "smtps"]

  dynamic_mapping_service:
    description:
      - Dynamic Mapping Version of Suffixed Option Name. Sub-Table. Same Descriptions as Parent.
    required: false

  dynamic_mapping_src_filter:
    description:
      - Dynamic Mapping Version of Suffixed Option Name. Sub-Table. Same Descriptions as Parent.
    required: false

  dynamic_mapping_srcintf_filter:
    description:
      - Dynamic Mapping Version of Suffixed Option Name. Sub-Table. Same Descriptions as Parent.
    required: false

  dynamic_mapping_ssl_algorithm:
    description:
      - Dynamic Mapping Version of Suffixed Option Name. Sub-Table. Same Descriptions as Parent.
      - choice | high |
      - choice | medium |
      - choice | low |
      - choice | custom |
    required: false
    choices: ["high", "medium", "low", "custom"]

  dynamic_mapping_ssl_certificate:
    description:
      - Dynamic Mapping Version of Suffixed Option Name. Sub-Table. Same Descriptions as Parent.
    required: false

  dynamic_mapping_ssl_client_fallback:
    description:
      - Dynamic Mapping Version of Suffixed Option Name. Sub-Table. Same Descriptions as Parent.
      - choice | disable |
      - choice | enable |
    required: false
    choices: ["disable", "enable"]

  dynamic_mapping_ssl_client_renegotiation:
    description:
      - Dynamic Mapping Version of Suffixed Option Name. Sub-Table. Same Descriptions as Parent.
      - choice | deny |
      - choice | allow |
      - choice | secure |
    required: false
    choices: ["deny", "allow", "secure"]

  dynamic_mapping_ssl_client_session_state_max:
    description:
      - Dynamic Mapping Version of Suffixed Option Name. Sub-Table. Same Descriptions as Parent.
    required: false

  dynamic_mapping_ssl_client_session_state_timeout:
    description:
      - Dynamic Mapping Version of Suffixed Option Name. Sub-Table. Same Descriptions as Parent.
    required: false

  dynamic_mapping_ssl_client_session_state_type:
    description:
      - Dynamic Mapping Version of Suffixed Option Name. Sub-Table. Same Descriptions as Parent.
      - choice | disable |
      - choice | time |
      - choice | count |
      - choice | both |
    required: false
    choices: ["disable", "time", "count", "both"]

  dynamic_mapping_ssl_dh_bits:
    description:
      - Dynamic Mapping Version of Suffixed Option Name. Sub-Table. Same Descriptions as Parent.
      - choice | 768 |
      - choice | 1024 |
      - choice | 1536 |
      - choice | 2048 |
      - choice | 3072 |
      - choice | 4096 |
    required: false
    choices: ["768", "1024", "1536", "2048", "3072", "4096"]

  dynamic_mapping_ssl_hpkp:
    description:
      - Dynamic Mapping Version of Suffixed Option Name. Sub-Table. Same Descriptions as Parent.
      - choice | disable |
      - choice | enable |
      - choice | report-only |
    required: false
    choices: ["disable", "enable", "report-only"]

  dynamic_mapping_ssl_hpkp_age:
    description:
      - Dynamic Mapping Version of Suffixed Option Name. Sub-Table. Same Descriptions as Parent.
    required: false

  dynamic_mapping_ssl_hpkp_backup:
    description:
      - Dynamic Mapping Version of Suffixed Option Name. Sub-Table. Same Descriptions as Parent.
    required: false

  dynamic_mapping_ssl_hpkp_include_subdomains:
    description:
      - Dynamic Mapping Version of Suffixed Option Name. Sub-Table. Same Descriptions as Parent.
      - choice | disable |
      - choice | enable |
    required: false
    choices: ["disable", "enable"]

  dynamic_mapping_ssl_hpkp_primary:
    description:
      - Dynamic Mapping Version of Suffixed Option Name. Sub-Table. Same Descriptions as Parent.
    required: false

  dynamic_mapping_ssl_hpkp_report_uri:
    description:
      - Dynamic Mapping Version of Suffixed Option Name. Sub-Table. Same Descriptions as Parent.
    required: false

  dynamic_mapping_ssl_hsts:
    description:
      - Dynamic Mapping Version of Suffixed Option Name. Sub-Table. Same Descriptions as Parent.
      - choice | disable |
      - choice | enable |
    required: false
    choices: ["disable", "enable"]

  dynamic_mapping_ssl_hsts_age:
    description:
      - Dynamic Mapping Version of Suffixed Option Name. Sub-Table. Same Descriptions as Parent.
    required: false

  dynamic_mapping_ssl_hsts_include_subdomains:
    description:
      - Dynamic Mapping Version of Suffixed Option Name. Sub-Table. Same Descriptions as Parent.
      - choice | disable |
      - choice | enable |
    required: false
    choices: ["disable", "enable"]

  dynamic_mapping_ssl_http_location_conversion:
    description:
      - Dynamic Mapping Version of Suffixed Option Name. Sub-Table. Same Descriptions as Parent.
      - choice | disable |
      - choice | enable |
    required: false
    choices: ["disable", "enable"]

  dynamic_mapping_ssl_http_match_host:
    description:
      - Dynamic Mapping Version of Suffixed Option Name. Sub-Table. Same Descriptions as Parent.
      - choice | disable |
      - choice | enable |
    required: false
    choices: ["disable", "enable"]

  dynamic_mapping_ssl_max_version:
    description:
      - Dynamic Mapping Version of Suffixed Option Name. Sub-Table. Same Descriptions as Parent.
      - choice | ssl-3.0 |
      - choice | tls-1.0 |
      - choice | tls-1.1 |
      - choice | tls-1.2 |
    required: false
    choices: ["ssl-3.0", "tls-1.0", "tls-1.1", "tls-1.2"]

  dynamic_mapping_ssl_min_version:
    description:
      - Dynamic Mapping Version of Suffixed Option Name. Sub-Table. Same Descriptions as Parent.
      - choice | ssl-3.0 |
      - choice | tls-1.0 |
      - choice | tls-1.1 |
      - choice | tls-1.2 |
    required: false
    choices: ["ssl-3.0", "tls-1.0", "tls-1.1", "tls-1.2"]

  dynamic_mapping_ssl_mode:
    description:
      - Dynamic Mapping Version of Suffixed Option Name. Sub-Table. Same Descriptions as Parent.
      - choice | half |
      - choice | full |
    required: false
    choices: ["half", "full"]

  dynamic_mapping_ssl_pfs:
    description:
      - Dynamic Mapping Version of Suffixed Option Name. Sub-Table. Same Descriptions as Parent.
      - choice | require |
      - choice | deny |
      - choice | allow |
    required: false
    choices: ["require", "deny", "allow"]

  dynamic_mapping_ssl_send_empty_frags:
    description:
      - Dynamic Mapping Version of Suffixed Option Name. Sub-Table. Same Descriptions as Parent.
      - choice | disable |
      - choice | enable |
    required: false
    choices: ["disable", "enable"]

  dynamic_mapping_ssl_server_algorithm:
    description:
      - Dynamic Mapping Version of Suffixed Option Name. Sub-Table. Same Descriptions as Parent.
      - choice | high |
      - choice | low |
      - choice | medium |
      - choice | custom |
      - choice | client |
    required: false
    choices: ["high", "low", "medium", "custom", "client"]

  dynamic_mapping_ssl_server_max_version:
    description:
      - Dynamic Mapping Version of Suffixed Option Name. Sub-Table. Same Descriptions as Parent.
      - choice | ssl-3.0 |
      - choice | tls-1.0 |
      - choice | tls-1.1 |
      - choice | tls-1.2 |
      - choice | client |
    required: false
    choices: ["ssl-3.0", "tls-1.0", "tls-1.1", "tls-1.2", "client"]

  dynamic_mapping_ssl_server_min_version:
    description:
      - Dynamic Mapping Version of Suffixed Option Name. Sub-Table. Same Descriptions as Parent.
      - choice | ssl-3.0 |
      - choice | tls-1.0 |
      - choice | tls-1.1 |
      - choice | tls-1.2 |
      - choice | client |
    required: false
    choices: ["ssl-3.0", "tls-1.0", "tls-1.1", "tls-1.2", "client"]

  dynamic_mapping_ssl_server_session_state_max:
    description:
      - Dynamic Mapping Version of Suffixed Option Name. Sub-Table. Same Descriptions as Parent.
    required: false

  dynamic_mapping_ssl_server_session_state_timeout:
    description:
      - Dynamic Mapping Version of Suffixed Option Name. Sub-Table. Same Descriptions as Parent.
    required: false

  dynamic_mapping_ssl_server_session_state_type:
    description:
      - Dynamic Mapping Version of Suffixed Option Name. Sub-Table. Same Descriptions as Parent.
      - choice | disable |
      - choice | time |
      - choice | count |
      - choice | both |
    required: false
    choices: ["disable", "time", "count", "both"]

  dynamic_mapping_type:
    description:
      - Dynamic Mapping Version of Suffixed Option Name. Sub-Table. Same Descriptions as Parent.
      - choice | static-nat |
      - choice | load-balance |
      - choice | server-load-balance |
      - choice | dns-translation |
      - choice | fqdn |
    required: false
    choices: ["static-nat", "load-balance", "server-load-balance", "dns-translation", "fqdn"]

  dynamic_mapping_weblogic_server:
    description:
      - Dynamic Mapping Version of Suffixed Option Name. Sub-Table. Same Descriptions as Parent.
      - choice | disable |
      - choice | enable |
    required: false
    choices: ["disable", "enable"]

  dynamic_mapping_websphere_server:
    description:
      - Dynamic Mapping Version of Suffixed Option Name. Sub-Table. Same Descriptions as Parent.
      - choice | disable |
      - choice | enable |
    required: false
    choices: ["disable", "enable"]

  dynamic_mapping_realservers_client_ip:
    description:
      - Dynamic Mapping Version of Suffixed Option Name. Sub-Table. Same Descriptions as Parent.
    required: false

  dynamic_mapping_realservers_healthcheck:
    description:
      - Dynamic Mapping Version of Suffixed Option Name. Sub-Table. Same Descriptions as Parent.
      - choice | disable |
      - choice | enable |
      - choice | vip |
    required: false
    choices: ["disable", "enable", "vip"]

  dynamic_mapping_realservers_holddown_interval:
    description:
      - Dynamic Mapping Version of Suffixed Option Name. Sub-Table. Same Descriptions as Parent.
    required: false

  dynamic_mapping_realservers_http_host:
    description:
      - Dynamic Mapping Version of Suffixed Option Name. Sub-Table. Same Descriptions as Parent.
    required: false

  dynamic_mapping_realservers_ip:
    description:
      - Dynamic Mapping Version of Suffixed Option Name. Sub-Table. Same Descriptions as Parent.
    required: false

  dynamic_mapping_realservers_max_connections:
    description:
      - Dynamic Mapping Version of Suffixed Option Name. Sub-Table. Same Descriptions as Parent.
    required: false

  dynamic_mapping_realservers_monitor:
    description:
      - Dynamic Mapping Version of Suffixed Option Name. Sub-Table. Same Descriptions as Parent.
    required: false

  dynamic_mapping_realservers_port:
    description:
      - Dynamic Mapping Version of Suffixed Option Name. Sub-Table. Same Descriptions as Parent.
    required: false

  dynamic_mapping_realservers_seq:
    description:
      - Dynamic Mapping Version of Suffixed Option Name. Sub-Table. Same Descriptions as Parent.
    required: false

  dynamic_mapping_realservers_status:
    description:
      - Dynamic Mapping Version of Suffixed Option Name. Sub-Table. Same Descriptions as Parent.
      - choice | active |
      - choice | standby |
      - choice | disable |
    required: false
    choices: ["active", "standby", "disable"]

  dynamic_mapping_realservers_weight:
    description:
      - Dynamic Mapping Version of Suffixed Option Name. Sub-Table. Same Descriptions as Parent.
    required: false

  dynamic_mapping_ssl_cipher_suites_cipher:
    description:
      - Dynamic Mapping Version of Suffixed Option Name. Sub-Table. Same Descriptions as Parent.
      - choice | TLS-RSA-WITH-RC4-128-MD5 |
      - choice | TLS-RSA-WITH-RC4-128-SHA |
      - choice | TLS-RSA-WITH-DES-CBC-SHA |
      - choice | TLS-RSA-WITH-3DES-EDE-CBC-SHA |
      - choice | TLS-RSA-WITH-AES-128-CBC-SHA |
      - choice | TLS-RSA-WITH-AES-256-CBC-SHA |
      - choice | TLS-RSA-WITH-AES-128-CBC-SHA256 |
      - choice | TLS-RSA-WITH-AES-256-CBC-SHA256 |
      - choice | TLS-RSA-WITH-CAMELLIA-128-CBC-SHA |
      - choice | TLS-RSA-WITH-CAMELLIA-256-CBC-SHA |
      - choice | TLS-RSA-WITH-CAMELLIA-128-CBC-SHA256 |
      - choice | TLS-RSA-WITH-CAMELLIA-256-CBC-SHA256 |
      - choice | TLS-RSA-WITH-SEED-CBC-SHA |
      - choice | TLS-RSA-WITH-ARIA-128-CBC-SHA256 |
      - choice | TLS-RSA-WITH-ARIA-256-CBC-SHA384 |
      - choice | TLS-DHE-RSA-WITH-DES-CBC-SHA |
      - choice | TLS-DHE-RSA-WITH-3DES-EDE-CBC-SHA |
      - choice | TLS-DHE-RSA-WITH-AES-128-CBC-SHA |
      - choice | TLS-DHE-RSA-WITH-AES-256-CBC-SHA |
      - choice | TLS-DHE-RSA-WITH-AES-128-CBC-SHA256 |
      - choice | TLS-DHE-RSA-WITH-AES-256-CBC-SHA256 |
      - choice | TLS-DHE-RSA-WITH-CAMELLIA-128-CBC-SHA |
      - choice | TLS-DHE-RSA-WITH-CAMELLIA-256-CBC-SHA |
      - choice | TLS-DHE-RSA-WITH-CAMELLIA-128-CBC-SHA256 |
      - choice | TLS-DHE-RSA-WITH-CAMELLIA-256-CBC-SHA256 |
      - choice | TLS-DHE-RSA-WITH-SEED-CBC-SHA |
      - choice | TLS-DHE-RSA-WITH-ARIA-128-CBC-SHA256 |
      - choice | TLS-DHE-RSA-WITH-ARIA-256-CBC-SHA384 |
      - choice | TLS-ECDHE-RSA-WITH-RC4-128-SHA |
      - choice | TLS-ECDHE-RSA-WITH-3DES-EDE-CBC-SHA |
      - choice | TLS-ECDHE-RSA-WITH-AES-128-CBC-SHA |
      - choice | TLS-ECDHE-RSA-WITH-AES-256-CBC-SHA |
      - choice | TLS-ECDHE-RSA-WITH-CHACHA20-POLY1305-SHA256 |
      - choice | TLS-ECDHE-ECDSA-WITH-CHACHA20-POLY1305-SHA256 |
      - choice | TLS-DHE-RSA-WITH-CHACHA20-POLY1305-SHA256 |
      - choice | TLS-DHE-RSA-WITH-AES-128-GCM-SHA256 |
      - choice | TLS-DHE-RSA-WITH-AES-256-GCM-SHA384 |
      - choice | TLS-DHE-DSS-WITH-AES-128-CBC-SHA |
      - choice | TLS-DHE-DSS-WITH-AES-256-CBC-SHA |
      - choice | TLS-DHE-DSS-WITH-AES-128-CBC-SHA256 |
      - choice | TLS-DHE-DSS-WITH-AES-128-GCM-SHA256 |
      - choice | TLS-DHE-DSS-WITH-AES-256-CBC-SHA256 |
      - choice | TLS-DHE-DSS-WITH-AES-256-GCM-SHA384 |
      - choice | TLS-ECDHE-RSA-WITH-AES-128-CBC-SHA256 |
      - choice | TLS-ECDHE-RSA-WITH-AES-128-GCM-SHA256 |
      - choice | TLS-ECDHE-RSA-WITH-AES-256-CBC-SHA384 |
      - choice | TLS-ECDHE-RSA-WITH-AES-256-GCM-SHA384 |
      - choice | TLS-ECDHE-ECDSA-WITH-AES-128-CBC-SHA |
      - choice | TLS-ECDHE-ECDSA-WITH-AES-128-CBC-SHA256 |
      - choice | TLS-ECDHE-ECDSA-WITH-AES-128-GCM-SHA256 |
      - choice | TLS-ECDHE-ECDSA-WITH-AES-256-CBC-SHA384 |
      - choice | TLS-ECDHE-ECDSA-WITH-AES-256-GCM-SHA384 |
      - choice | TLS-RSA-WITH-AES-128-GCM-SHA256 |
      - choice | TLS-RSA-WITH-AES-256-GCM-SHA384 |
      - choice | TLS-DHE-DSS-WITH-CAMELLIA-128-CBC-SHA |
      - choice | TLS-DHE-DSS-WITH-CAMELLIA-256-CBC-SHA |
      - choice | TLS-DHE-DSS-WITH-CAMELLIA-128-CBC-SHA256 |
      - choice | TLS-DHE-DSS-WITH-CAMELLIA-256-CBC-SHA256 |
      - choice | TLS-DHE-DSS-WITH-SEED-CBC-SHA |
      - choice | TLS-DHE-DSS-WITH-ARIA-128-CBC-SHA256 |
      - choice | TLS-DHE-DSS-WITH-ARIA-256-CBC-SHA384 |
      - choice | TLS-ECDHE-RSA-WITH-ARIA-128-CBC-SHA256 |
      - choice | TLS-ECDHE-RSA-WITH-ARIA-256-CBC-SHA384 |
      - choice | TLS-ECDHE-ECDSA-WITH-ARIA-128-CBC-SHA256 |
      - choice | TLS-ECDHE-ECDSA-WITH-ARIA-256-CBC-SHA384 |
      - choice | TLS-DHE-DSS-WITH-3DES-EDE-CBC-SHA |
      - choice | TLS-DHE-DSS-WITH-DES-CBC-SHA |
    required: false
    choices: ["TLS-RSA-WITH-RC4-128-MD5",
                "TLS-RSA-WITH-RC4-128-SHA",
                "TLS-RSA-WITH-DES-CBC-SHA",
                "TLS-RSA-WITH-3DES-EDE-CBC-SHA",
                "TLS-RSA-WITH-AES-128-CBC-SHA",
                "TLS-RSA-WITH-AES-256-CBC-SHA",
                "TLS-RSA-WITH-AES-128-CBC-SHA256",
                "TLS-RSA-WITH-AES-256-CBC-SHA256",
                "TLS-RSA-WITH-CAMELLIA-128-CBC-SHA",
                "TLS-RSA-WITH-CAMELLIA-256-CBC-SHA",
                "TLS-RSA-WITH-CAMELLIA-128-CBC-SHA256",
                "TLS-RSA-WITH-CAMELLIA-256-CBC-SHA256",
                "TLS-RSA-WITH-SEED-CBC-SHA",
                "TLS-RSA-WITH-ARIA-128-CBC-SHA256",
                "TLS-RSA-WITH-ARIA-256-CBC-SHA384",
                "TLS-DHE-RSA-WITH-DES-CBC-SHA",
                "TLS-DHE-RSA-WITH-3DES-EDE-CBC-SHA",
                "TLS-DHE-RSA-WITH-AES-128-CBC-SHA",
                "TLS-DHE-RSA-WITH-AES-256-CBC-SHA",
                "TLS-DHE-RSA-WITH-AES-128-CBC-SHA256",
                "TLS-DHE-RSA-WITH-AES-256-CBC-SHA256",
                "TLS-DHE-RSA-WITH-CAMELLIA-128-CBC-SHA",
                "TLS-DHE-RSA-WITH-CAMELLIA-256-CBC-SHA",
                "TLS-DHE-RSA-WITH-CAMELLIA-128-CBC-SHA256",
                "TLS-DHE-RSA-WITH-CAMELLIA-256-CBC-SHA256",
                "TLS-DHE-RSA-WITH-SEED-CBC-SHA",
                "TLS-DHE-RSA-WITH-ARIA-128-CBC-SHA256",
                "TLS-DHE-RSA-WITH-ARIA-256-CBC-SHA384",
                "TLS-ECDHE-RSA-WITH-RC4-128-SHA",
                "TLS-ECDHE-RSA-WITH-3DES-EDE-CBC-SHA",
                "TLS-ECDHE-RSA-WITH-AES-128-CBC-SHA",
                "TLS-ECDHE-RSA-WITH-AES-256-CBC-SHA",
                "TLS-ECDHE-RSA-WITH-CHACHA20-POLY1305-SHA256",
                "TLS-ECDHE-ECDSA-WITH-CHACHA20-POLY1305-SHA256",
                "TLS-DHE-RSA-WITH-CHACHA20-POLY1305-SHA256",
                "TLS-DHE-RSA-WITH-AES-128-GCM-SHA256",
                "TLS-DHE-RSA-WITH-AES-256-GCM-SHA384",
                "TLS-DHE-DSS-WITH-AES-128-CBC-SHA",
                "TLS-DHE-DSS-WITH-AES-256-CBC-SHA",
                "TLS-DHE-DSS-WITH-AES-128-CBC-SHA256",
                "TLS-DHE-DSS-WITH-AES-128-GCM-SHA256",
                "TLS-DHE-DSS-WITH-AES-256-CBC-SHA256",
                "TLS-DHE-DSS-WITH-AES-256-GCM-SHA384",
                "TLS-ECDHE-RSA-WITH-AES-128-CBC-SHA256",
                "TLS-ECDHE-RSA-WITH-AES-128-GCM-SHA256",
                "TLS-ECDHE-RSA-WITH-AES-256-CBC-SHA384",
                "TLS-ECDHE-RSA-WITH-AES-256-GCM-SHA384",
                "TLS-ECDHE-ECDSA-WITH-AES-128-CBC-SHA",
                "TLS-ECDHE-ECDSA-WITH-AES-128-CBC-SHA256",
                "TLS-ECDHE-ECDSA-WITH-AES-128-GCM-SHA256",
                "TLS-ECDHE-ECDSA-WITH-AES-256-CBC-SHA384",
                "TLS-ECDHE-ECDSA-WITH-AES-256-GCM-SHA384",
                "TLS-RSA-WITH-AES-128-GCM-SHA256",
                "TLS-RSA-WITH-AES-256-GCM-SHA384",
                "TLS-DHE-DSS-WITH-CAMELLIA-128-CBC-SHA",
                "TLS-DHE-DSS-WITH-CAMELLIA-256-CBC-SHA",
                "TLS-DHE-DSS-WITH-CAMELLIA-128-CBC-SHA256",
                "TLS-DHE-DSS-WITH-CAMELLIA-256-CBC-SHA256",
                "TLS-DHE-DSS-WITH-SEED-CBC-SHA",
                "TLS-DHE-DSS-WITH-ARIA-128-CBC-SHA256",
                "TLS-DHE-DSS-WITH-ARIA-256-CBC-SHA384",
                "TLS-ECDHE-RSA-WITH-ARIA-128-CBC-SHA256",
                "TLS-ECDHE-RSA-WITH-ARIA-256-CBC-SHA384",
                "TLS-ECDHE-ECDSA-WITH-ARIA-128-CBC-SHA256",
                "TLS-ECDHE-ECDSA-WITH-ARIA-256-CBC-SHA384",
                "TLS-DHE-DSS-WITH-3DES-EDE-CBC-SHA",
                "TLS-DHE-DSS-WITH-DES-CBC-SHA"]

  dynamic_mapping_ssl_cipher_suites_versions:
    description:
      - Dynamic Mapping Version of Suffixed Option Name. Sub-Table. Same Descriptions as Parent.
      - FLAG Based Options. Specify multiple in list form.
      - flag | ssl-3.0 |
      - flag | tls-1.0 |
      - flag | tls-1.1 |
      - flag | tls-1.2 |
    required: false
    choices: ["ssl-3.0", "tls-1.0", "tls-1.1", "tls-1.2"]

  realservers:
    description:
      - EXPERTS ONLY! KNOWLEDGE OF FMGR JSON API IS REQUIRED!
      - List of multiple child objects to be added. Expects a list of dictionaries.
      - Dictionaries must use FortiManager API parameters, not the ansible ones listed below.
      - If submitted, all other prefixed sub-parameters ARE IGNORED.
      - This object is MUTUALLY EXCLUSIVE with its options.
      - We expect that you know what you are doing with these list parameters, and are leveraging the JSON API Guide.
      - WHEN IN DOUBT, USE THE SUB OPTIONS BELOW INSTEAD TO CREATE OBJECTS WITH MULTIPLE TASKS
    required: false

  realservers_client_ip:
    description:
      - Only clients in this IP range can connect to this real server.
    required: false

  realservers_healthcheck:
    description:
      - Enable to check the responsiveness of the real server before forwarding traffic.
      - choice | disable | Disable per server health check.
      - choice | enable | Enable per server health check.
      - choice | vip | Use health check defined in VIP.
    required: false
    choices: ["disable", "enable", "vip"]

  realservers_holddown_interval:
    description:
      - Time in seconds that the health check monitor monitors an unresponsive server that should be active.
    required: false

  realservers_http_host:
    description:
      - HTTP server domain name in HTTP header.
    required: false

  realservers_ip:
    description:
      - IP address of the real server.
    required: false

  realservers_max_connections:
    description:
      - Max number of active connections that can be directed to the real server. When reached, sessions are sent to
      - their real servers.
    required: false

  realservers_monitor:
    description:
      - Name of the health check monitor to use when polling to determine a virtual server's connectivity status.
    required: false

  realservers_port:
    description:
      - Port for communicating with the real server. Required if port forwarding is enabled.
    required: false

  realservers_seq:
    description:
      - Real Server Sequence Number
    required: false

  realservers_status:
    description:
      - Set the status of the real server to active so that it can accept traffic.
      - Or on standby or disabled so no traffic is sent.
      - choice | active | Server status active.
      - choice | standby | Server status standby.
      - choice | disable | Server status disable.
    required: false
    choices: ["active", "standby", "disable"]

  realservers_weight:
    description:
      - Weight of the real server. If weighted load balancing is enabled, the server with the highest weight gets more
      - connections.
    required: false

  ssl_cipher_suites:
    description:
      - EXPERTS ONLY! KNOWLEDGE OF FMGR JSON API IS REQUIRED!
      - List of multiple child objects to be added. Expects a list of dictionaries.
      - Dictionaries must use FortiManager API parameters, not the ansible ones listed below.
      - If submitted, all other prefixed sub-parameters ARE IGNORED.
      - This object is MUTUALLY EXCLUSIVE with its options.
      - We expect that you know what you are doing with these list parameters, and are leveraging the JSON API Guide.
      - WHEN IN DOUBT, USE THE SUB OPTIONS BELOW INSTEAD TO CREATE OBJECTS WITH MULTIPLE TASKS
    required: false

  ssl_cipher_suites_cipher:
    description:
      - Cipher suite name.
      - choice | TLS-RSA-WITH-RC4-128-MD5 | Cipher suite TLS-RSA-WITH-RC4-128-MD5.
      - choice | TLS-RSA-WITH-RC4-128-SHA | Cipher suite TLS-RSA-WITH-RC4-128-SHA.
      - choice | TLS-RSA-WITH-DES-CBC-SHA | Cipher suite TLS-RSA-WITH-DES-CBC-SHA.
      - choice | TLS-RSA-WITH-3DES-EDE-CBC-SHA | Cipher suite TLS-RSA-WITH-3DES-EDE-CBC-SHA.
      - choice | TLS-RSA-WITH-AES-128-CBC-SHA | Cipher suite TLS-RSA-WITH-AES-128-CBC-SHA.
      - choice | TLS-RSA-WITH-AES-256-CBC-SHA | Cipher suite TLS-RSA-WITH-AES-256-CBC-SHA.
      - choice | TLS-RSA-WITH-AES-128-CBC-SHA256 | Cipher suite TLS-RSA-WITH-AES-128-CBC-SHA256.
      - choice | TLS-RSA-WITH-AES-256-CBC-SHA256 | Cipher suite TLS-RSA-WITH-AES-256-CBC-SHA256.
      - choice | TLS-RSA-WITH-CAMELLIA-128-CBC-SHA | Cipher suite TLS-RSA-WITH-CAMELLIA-128-CBC-SHA.
      - choice | TLS-RSA-WITH-CAMELLIA-256-CBC-SHA | Cipher suite TLS-RSA-WITH-CAMELLIA-256-CBC-SHA.
      - choice | TLS-RSA-WITH-CAMELLIA-128-CBC-SHA256 | Cipher suite TLS-RSA-WITH-CAMELLIA-128-CBC-SHA256.
      - choice | TLS-RSA-WITH-CAMELLIA-256-CBC-SHA256 | Cipher suite TLS-RSA-WITH-CAMELLIA-256-CBC-SHA256.
      - choice | TLS-RSA-WITH-SEED-CBC-SHA | Cipher suite TLS-RSA-WITH-SEED-CBC-SHA.
      - choice | TLS-RSA-WITH-ARIA-128-CBC-SHA256 | Cipher suite TLS-RSA-WITH-ARIA-128-CBC-SHA256.
      - choice | TLS-RSA-WITH-ARIA-256-CBC-SHA384 | Cipher suite TLS-RSA-WITH-ARIA-256-CBC-SHA384.
      - choice | TLS-DHE-RSA-WITH-DES-CBC-SHA | Cipher suite TLS-DHE-RSA-WITH-DES-CBC-SHA.
      - choice | TLS-DHE-RSA-WITH-3DES-EDE-CBC-SHA | Cipher suite TLS-DHE-RSA-WITH-3DES-EDE-CBC-SHA.
      - choice | TLS-DHE-RSA-WITH-AES-128-CBC-SHA | Cipher suite TLS-DHE-RSA-WITH-AES-128-CBC-SHA.
      - choice | TLS-DHE-RSA-WITH-AES-256-CBC-SHA | Cipher suite TLS-DHE-RSA-WITH-AES-256-CBC-SHA.
      - choice | TLS-DHE-RSA-WITH-AES-128-CBC-SHA256 | Cipher suite TLS-DHE-RSA-WITH-AES-128-CBC-SHA256.
      - choice | TLS-DHE-RSA-WITH-AES-256-CBC-SHA256 | Cipher suite TLS-DHE-RSA-WITH-AES-256-CBC-SHA256.
      - choice | TLS-DHE-RSA-WITH-CAMELLIA-128-CBC-SHA | Cipher suite TLS-DHE-RSA-WITH-CAMELLIA-128-CBC-SHA.
      - choice | TLS-DHE-RSA-WITH-CAMELLIA-256-CBC-SHA | Cipher suite TLS-DHE-RSA-WITH-CAMELLIA-256-CBC-SHA.
      - choice | TLS-DHE-RSA-WITH-CAMELLIA-128-CBC-SHA256 | Cipher suite TLS-DHE-RSA-WITH-CAMELLIA-128-CBC-SHA256.
      - choice | TLS-DHE-RSA-WITH-CAMELLIA-256-CBC-SHA256 | Cipher suite TLS-DHE-RSA-WITH-CAMELLIA-256-CBC-SHA256.
      - choice | TLS-DHE-RSA-WITH-SEED-CBC-SHA | Cipher suite TLS-DHE-RSA-WITH-SEED-CBC-SHA.
      - choice | TLS-DHE-RSA-WITH-ARIA-128-CBC-SHA256 | Cipher suite TLS-DHE-RSA-WITH-ARIA-128-CBC-SHA256.
      - choice | TLS-DHE-RSA-WITH-ARIA-256-CBC-SHA384 | Cipher suite TLS-DHE-RSA-WITH-ARIA-256-CBC-SHA384.
      - choice | TLS-ECDHE-RSA-WITH-RC4-128-SHA | Cipher suite TLS-ECDHE-RSA-WITH-RC4-128-SHA.
      - choice | TLS-ECDHE-RSA-WITH-3DES-EDE-CBC-SHA | Cipher suite TLS-ECDHE-RSA-WITH-3DES-EDE-CBC-SHA.
      - choice | TLS-ECDHE-RSA-WITH-AES-128-CBC-SHA | Cipher suite TLS-ECDHE-RSA-WITH-AES-128-CBC-SHA.
      - choice | TLS-ECDHE-RSA-WITH-AES-256-CBC-SHA | Cipher suite TLS-ECDHE-RSA-WITH-AES-256-CBC-SHA.
      - choice | TLS-ECDHE-RSA-WITH-CHACHA20-POLY1305-SHA256 | Cipher suite TLS-ECDHE-RSA-WITH-CHACHA20-POLY1305-SHA256.
      - choice | TLS-ECDHE-ECDSA-WITH-CHACHA20-POLY1305-SHA256 | Cipher suite TLS-ECDHE-ECDSA-WITH-CHACHA20-POLY1305-SHA256.
      - choice | TLS-DHE-RSA-WITH-CHACHA20-POLY1305-SHA256 | Cipher suite TLS-DHE-RSA-WITH-CHACHA20-POLY1305-SHA256.
      - choice | TLS-DHE-RSA-WITH-AES-128-GCM-SHA256 | Cipher suite TLS-DHE-RSA-WITH-AES-128-GCM-SHA256.
      - choice | TLS-DHE-RSA-WITH-AES-256-GCM-SHA384 | Cipher suite TLS-DHE-RSA-WITH-AES-256-GCM-SHA384.
      - choice | TLS-DHE-DSS-WITH-AES-128-CBC-SHA | Cipher suite TLS-DHE-DSS-WITH-AES-128-CBC-SHA.
      - choice | TLS-DHE-DSS-WITH-AES-256-CBC-SHA | Cipher suite TLS-DHE-DSS-WITH-AES-256-CBC-SHA.
      - choice | TLS-DHE-DSS-WITH-AES-128-CBC-SHA256 | Cipher suite TLS-DHE-DSS-WITH-AES-128-CBC-SHA256.
      - choice | TLS-DHE-DSS-WITH-AES-128-GCM-SHA256 | Cipher suite TLS-DHE-DSS-WITH-AES-128-GCM-SHA256.
      - choice | TLS-DHE-DSS-WITH-AES-256-CBC-SHA256 | Cipher suite TLS-DHE-DSS-WITH-AES-256-CBC-SHA256.
      - choice | TLS-DHE-DSS-WITH-AES-256-GCM-SHA384 | Cipher suite TLS-DHE-DSS-WITH-AES-256-GCM-SHA384.
      - choice | TLS-ECDHE-RSA-WITH-AES-128-CBC-SHA256 | Cipher suite TLS-ECDHE-RSA-WITH-AES-128-CBC-SHA256.
      - choice | TLS-ECDHE-RSA-WITH-AES-128-GCM-SHA256 | Cipher suite TLS-ECDHE-RSA-WITH-AES-128-GCM-SHA256.
      - choice | TLS-ECDHE-RSA-WITH-AES-256-CBC-SHA384 | Cipher suite TLS-ECDHE-RSA-WITH-AES-256-CBC-SHA384.
      - choice | TLS-ECDHE-RSA-WITH-AES-256-GCM-SHA384 | Cipher suite TLS-ECDHE-RSA-WITH-AES-256-GCM-SHA384.
      - choice | TLS-ECDHE-ECDSA-WITH-AES-128-CBC-SHA | Cipher suite TLS-ECDHE-ECDSA-WITH-AES-128-CBC-SHA.
      - choice | TLS-ECDHE-ECDSA-WITH-AES-128-CBC-SHA256 | Cipher suite TLS-ECDHE-ECDSA-WITH-AES-128-CBC-SHA256.
      - choice | TLS-ECDHE-ECDSA-WITH-AES-128-GCM-SHA256 | Cipher suite TLS-ECDHE-ECDSA-WITH-AES-128-GCM-SHA256.
      - choice | TLS-ECDHE-ECDSA-WITH-AES-256-CBC-SHA384 | Cipher suite TLS-ECDHE-ECDSA-WITH-AES-256-CBC-SHA384.
      - choice | TLS-ECDHE-ECDSA-WITH-AES-256-GCM-SHA384 | Cipher suite TLS-ECDHE-ECDSA-WITH-AES-256-GCM-SHA384.
      - choice | TLS-RSA-WITH-AES-128-GCM-SHA256 | Cipher suite TLS-RSA-WITH-AES-128-GCM-SHA256.
      - choice | TLS-RSA-WITH-AES-256-GCM-SHA384 | Cipher suite TLS-RSA-WITH-AES-256-GCM-SHA384.
      - choice | TLS-DHE-DSS-WITH-CAMELLIA-128-CBC-SHA | Cipher suite TLS-DSS-RSA-WITH-CAMELLIA-128-CBC-SHA.
      - choice | TLS-DHE-DSS-WITH-CAMELLIA-256-CBC-SHA | Cipher suite TLS-DHE-DSS-WITH-CAMELLIA-256-CBC-SHA.
      - choice | TLS-DHE-DSS-WITH-CAMELLIA-128-CBC-SHA256 | Cipher suite TLS-DHE-DSS-WITH-CAMELLIA-128-CBC-SHA256.
      - choice | TLS-DHE-DSS-WITH-CAMELLIA-256-CBC-SHA256 | Cipher suite TLS-DHE-DSS-WITH-CAMELLIA-256-CBC-SHA256.
      - choice | TLS-DHE-DSS-WITH-SEED-CBC-SHA | Cipher suite TLS-DHE-DSS-WITH-SEED-CBC-SHA.
      - choice | TLS-DHE-DSS-WITH-ARIA-128-CBC-SHA256 | Cipher suite TLS-DHE-DSS-WITH-ARIA-128-CBC-SHA256.
      - choice | TLS-DHE-DSS-WITH-ARIA-256-CBC-SHA384 | Cipher suite TLS-DHE-DSS-WITH-ARIA-256-CBC-SHA384.
      - choice | TLS-ECDHE-RSA-WITH-ARIA-128-CBC-SHA256 | Cipher suite TLS-ECDHE-RSA-WITH-ARIA-128-CBC-SHA256.
      - choice | TLS-ECDHE-RSA-WITH-ARIA-256-CBC-SHA384 | Cipher suite TLS-ECDHE-RSA-WITH-ARIA-256-CBC-SHA384.
      - choice | TLS-ECDHE-ECDSA-WITH-ARIA-128-CBC-SHA256 | Cipher suite TLS-ECDHE-ECDSA-WITH-ARIA-128-CBC_SHA256.
      - choice | TLS-ECDHE-ECDSA-WITH-ARIA-256-CBC-SHA384 | Cipher suite TLS-ECDHE-ECDSA-WITH-ARIA-256-CBC_SHA384.
      - choice | TLS-DHE-DSS-WITH-3DES-EDE-CBC-SHA | Cipher suite TLS-DHE-DSS-WITH-3DES-EDE-CBC-SHA.
      - choice | TLS-DHE-DSS-WITH-DES-CBC-SHA | Cipher suite TLS-DHE-DSS-WITH-DES-CBC-SHA.
    required: false
    choices: ["TLS-RSA-WITH-RC4-128-MD5",
            "TLS-RSA-WITH-RC4-128-SHA",
            "TLS-RSA-WITH-DES-CBC-SHA",
            "TLS-RSA-WITH-3DES-EDE-CBC-SHA",
            "TLS-RSA-WITH-AES-128-CBC-SHA",
            "TLS-RSA-WITH-AES-256-CBC-SHA",
            "TLS-RSA-WITH-AES-128-CBC-SHA256",
            "TLS-RSA-WITH-AES-256-CBC-SHA256",
            "TLS-RSA-WITH-CAMELLIA-128-CBC-SHA",
            "TLS-RSA-WITH-CAMELLIA-256-CBC-SHA",
            "TLS-RSA-WITH-CAMELLIA-128-CBC-SHA256",
            "TLS-RSA-WITH-CAMELLIA-256-CBC-SHA256",
            "TLS-RSA-WITH-SEED-CBC-SHA",
            "TLS-RSA-WITH-ARIA-128-CBC-SHA256",
            "TLS-RSA-WITH-ARIA-256-CBC-SHA384",
            "TLS-DHE-RSA-WITH-DES-CBC-SHA",
            "TLS-DHE-RSA-WITH-3DES-EDE-CBC-SHA",
            "TLS-DHE-RSA-WITH-AES-128-CBC-SHA",
            "TLS-DHE-RSA-WITH-AES-256-CBC-SHA",
            "TLS-DHE-RSA-WITH-AES-128-CBC-SHA256",
            "TLS-DHE-RSA-WITH-AES-256-CBC-SHA256",
            "TLS-DHE-RSA-WITH-CAMELLIA-128-CBC-SHA",
            "TLS-DHE-RSA-WITH-CAMELLIA-256-CBC-SHA",
            "TLS-DHE-RSA-WITH-CAMELLIA-128-CBC-SHA256",
            "TLS-DHE-RSA-WITH-CAMELLIA-256-CBC-SHA256",
            "TLS-DHE-RSA-WITH-SEED-CBC-SHA",
            "TLS-DHE-RSA-WITH-ARIA-128-CBC-SHA256",
            "TLS-DHE-RSA-WITH-ARIA-256-CBC-SHA384",
            "TLS-ECDHE-RSA-WITH-RC4-128-SHA",
            "TLS-ECDHE-RSA-WITH-3DES-EDE-CBC-SHA",
            "TLS-ECDHE-RSA-WITH-AES-128-CBC-SHA",
            "TLS-ECDHE-RSA-WITH-AES-256-CBC-SHA",
            "TLS-ECDHE-RSA-WITH-CHACHA20-POLY1305-SHA256",
            "TLS-ECDHE-ECDSA-WITH-CHACHA20-POLY1305-SHA256",
            "TLS-DHE-RSA-WITH-CHACHA20-POLY1305-SHA256",
            "TLS-DHE-RSA-WITH-AES-128-GCM-SHA256",
            "TLS-DHE-RSA-WITH-AES-256-GCM-SHA384",
            "TLS-DHE-DSS-WITH-AES-128-CBC-SHA",
            "TLS-DHE-DSS-WITH-AES-256-CBC-SHA",
            "TLS-DHE-DSS-WITH-AES-128-CBC-SHA256",
            "TLS-DHE-DSS-WITH-AES-128-GCM-SHA256",
            "TLS-DHE-DSS-WITH-AES-256-CBC-SHA256",
            "TLS-DHE-DSS-WITH-AES-256-GCM-SHA384",
            "TLS-ECDHE-RSA-WITH-AES-128-CBC-SHA256",
            "TLS-ECDHE-RSA-WITH-AES-128-GCM-SHA256",
            "TLS-ECDHE-RSA-WITH-AES-256-CBC-SHA384",
            "TLS-ECDHE-RSA-WITH-AES-256-GCM-SHA384",
            "TLS-ECDHE-ECDSA-WITH-AES-128-CBC-SHA",
            "TLS-ECDHE-ECDSA-WITH-AES-128-CBC-SHA256",
            "TLS-ECDHE-ECDSA-WITH-AES-128-GCM-SHA256",
            "TLS-ECDHE-ECDSA-WITH-AES-256-CBC-SHA384",
            "TLS-ECDHE-ECDSA-WITH-AES-256-GCM-SHA384",
            "TLS-RSA-WITH-AES-128-GCM-SHA256",
            "TLS-RSA-WITH-AES-256-GCM-SHA384",
            "TLS-DHE-DSS-WITH-CAMELLIA-128-CBC-SHA",
            "TLS-DHE-DSS-WITH-CAMELLIA-256-CBC-SHA",
            "TLS-DHE-DSS-WITH-CAMELLIA-128-CBC-SHA256",
            "TLS-DHE-DSS-WITH-CAMELLIA-256-CBC-SHA256",
            "TLS-DHE-DSS-WITH-SEED-CBC-SHA",
            "TLS-DHE-DSS-WITH-ARIA-128-CBC-SHA256",
            "TLS-DHE-DSS-WITH-ARIA-256-CBC-SHA384",
            "TLS-ECDHE-RSA-WITH-ARIA-128-CBC-SHA256",
            "TLS-ECDHE-RSA-WITH-ARIA-256-CBC-SHA384",
            "TLS-ECDHE-ECDSA-WITH-ARIA-128-CBC-SHA256",
            "TLS-ECDHE-ECDSA-WITH-ARIA-256-CBC-SHA384",
            "TLS-DHE-DSS-WITH-3DES-EDE-CBC-SHA",
            "TLS-DHE-DSS-WITH-DES-CBC-SHA"]

  ssl_cipher_suites_versions:
    description:
      - SSL/TLS versions that the cipher suite can be used with.
      - FLAG Based Options. Specify multiple in list form.
      - flag | ssl-3.0 | SSL 3.0.
      - flag | tls-1.0 | TLS 1.0.
      - flag | tls-1.1 | TLS 1.1.
      - flag | tls-1.2 | TLS 1.2.
    required: false
    choices: ["ssl-3.0", "tls-1.0", "tls-1.1", "tls-1.2"]

  ssl_server_cipher_suites:
    description:
      - EXPERTS ONLY! KNOWLEDGE OF FMGR JSON API IS REQUIRED!
      - List of multiple child objects to be added. Expects a list of dictionaries.
      - Dictionaries must use FortiManager API parameters, not the ansible ones listed below.
      - If submitted, all other prefixed sub-parameters ARE IGNORED.
      - This object is MUTUALLY EXCLUSIVE with its options.
      - We expect that you know what you are doing with these list parameters, and are leveraging the JSON API Guide.
      - WHEN IN DOUBT, USE THE SUB OPTIONS BELOW INSTEAD TO CREATE OBJECTS WITH MULTIPLE TASKS
    required: false

  ssl_server_cipher_suites_cipher:
    description:
      - Cipher suite name.
      - choice | TLS-RSA-WITH-RC4-128-MD5 | Cipher suite TLS-RSA-WITH-RC4-128-MD5.
      - choice | TLS-RSA-WITH-RC4-128-SHA | Cipher suite TLS-RSA-WITH-RC4-128-SHA.
      - choice | TLS-RSA-WITH-DES-CBC-SHA | Cipher suite TLS-RSA-WITH-DES-CBC-SHA.
      - choice | TLS-RSA-WITH-3DES-EDE-CBC-SHA | Cipher suite TLS-RSA-WITH-3DES-EDE-CBC-SHA.
      - choice | TLS-RSA-WITH-AES-128-CBC-SHA | Cipher suite TLS-RSA-WITH-AES-128-CBC-SHA.
      - choice | TLS-RSA-WITH-AES-256-CBC-SHA | Cipher suite TLS-RSA-WITH-AES-256-CBC-SHA.
      - choice | TLS-RSA-WITH-AES-128-CBC-SHA256 | Cipher suite TLS-RSA-WITH-AES-128-CBC-SHA256.
      - choice | TLS-RSA-WITH-AES-256-CBC-SHA256 | Cipher suite TLS-RSA-WITH-AES-256-CBC-SHA256.
      - choice | TLS-RSA-WITH-CAMELLIA-128-CBC-SHA | Cipher suite TLS-RSA-WITH-CAMELLIA-128-CBC-SHA.
      - choice | TLS-RSA-WITH-CAMELLIA-256-CBC-SHA | Cipher suite TLS-RSA-WITH-CAMELLIA-256-CBC-SHA.
      - choice | TLS-RSA-WITH-CAMELLIA-128-CBC-SHA256 | Cipher suite TLS-RSA-WITH-CAMELLIA-128-CBC-SHA256.
      - choice | TLS-RSA-WITH-CAMELLIA-256-CBC-SHA256 | Cipher suite TLS-RSA-WITH-CAMELLIA-256-CBC-SHA256.
      - choice | TLS-RSA-WITH-SEED-CBC-SHA | Cipher suite TLS-RSA-WITH-SEED-CBC-SHA.
      - choice | TLS-RSA-WITH-ARIA-128-CBC-SHA256 | Cipher suite TLS-RSA-WITH-ARIA-128-CBC-SHA256.
      - choice | TLS-RSA-WITH-ARIA-256-CBC-SHA384 | Cipher suite TLS-RSA-WITH-ARIA-256-CBC-SHA384.
      - choice | TLS-DHE-RSA-WITH-DES-CBC-SHA | Cipher suite TLS-DHE-RSA-WITH-DES-CBC-SHA.
      - choice | TLS-DHE-RSA-WITH-3DES-EDE-CBC-SHA | Cipher suite TLS-DHE-RSA-WITH-3DES-EDE-CBC-SHA.
      - choice | TLS-DHE-RSA-WITH-AES-128-CBC-SHA | Cipher suite TLS-DHE-RSA-WITH-AES-128-CBC-SHA.
      - choice | TLS-DHE-RSA-WITH-AES-256-CBC-SHA | Cipher suite TLS-DHE-RSA-WITH-AES-256-CBC-SHA.
      - choice | TLS-DHE-RSA-WITH-AES-128-CBC-SHA256 | Cipher suite TLS-DHE-RSA-WITH-AES-128-CBC-SHA256.
      - choice | TLS-DHE-RSA-WITH-AES-256-CBC-SHA256 | Cipher suite TLS-DHE-RSA-WITH-AES-256-CBC-SHA256.
      - choice | TLS-DHE-RSA-WITH-CAMELLIA-128-CBC-SHA | Cipher suite TLS-DHE-RSA-WITH-CAMELLIA-128-CBC-SHA.
      - choice | TLS-DHE-RSA-WITH-CAMELLIA-256-CBC-SHA | Cipher suite TLS-DHE-RSA-WITH-CAMELLIA-256-CBC-SHA.
      - choice | TLS-DHE-RSA-WITH-CAMELLIA-128-CBC-SHA256 | Cipher suite TLS-DHE-RSA-WITH-CAMELLIA-128-CBC-SHA256.
      - choice | TLS-DHE-RSA-WITH-CAMELLIA-256-CBC-SHA256 | Cipher suite TLS-DHE-RSA-WITH-CAMELLIA-256-CBC-SHA256.
      - choice | TLS-DHE-RSA-WITH-SEED-CBC-SHA | Cipher suite TLS-DHE-RSA-WITH-SEED-CBC-SHA.
      - choice | TLS-DHE-RSA-WITH-ARIA-128-CBC-SHA256 | Cipher suite TLS-DHE-RSA-WITH-ARIA-128-CBC-SHA256.
      - choice | TLS-DHE-RSA-WITH-ARIA-256-CBC-SHA384 | Cipher suite TLS-DHE-RSA-WITH-ARIA-256-CBC-SHA384.
      - choice | TLS-ECDHE-RSA-WITH-RC4-128-SHA | Cipher suite TLS-ECDHE-RSA-WITH-RC4-128-SHA.
      - choice | TLS-ECDHE-RSA-WITH-3DES-EDE-CBC-SHA | Cipher suite TLS-ECDHE-RSA-WITH-3DES-EDE-CBC-SHA.
      - choice | TLS-ECDHE-RSA-WITH-AES-128-CBC-SHA | Cipher suite TLS-ECDHE-RSA-WITH-AES-128-CBC-SHA.
      - choice | TLS-ECDHE-RSA-WITH-AES-256-CBC-SHA | Cipher suite TLS-ECDHE-RSA-WITH-AES-256-CBC-SHA.
      - choice | TLS-ECDHE-RSA-WITH-CHACHA20-POLY1305-SHA256 | Cipher suite TLS-ECDHE-RSA-WITH-CHACHA20-POLY1305-SHA256.
      - choice | TLS-ECDHE-ECDSA-WITH-CHACHA20-POLY1305-SHA256 | Suite TLS-ECDHE-ECDSA-WITH-CHACHA20-POLY1305-SHA256.
      - choice | TLS-DHE-RSA-WITH-CHACHA20-POLY1305-SHA256 | Cipher suite TLS-DHE-RSA-WITH-CHACHA20-POLY1305-SHA256.
      - choice | TLS-DHE-RSA-WITH-AES-128-GCM-SHA256 | Cipher suite TLS-DHE-RSA-WITH-AES-128-GCM-SHA256.
      - choice | TLS-DHE-RSA-WITH-AES-256-GCM-SHA384 | Cipher suite TLS-DHE-RSA-WITH-AES-256-GCM-SHA384.
      - choice | TLS-DHE-DSS-WITH-AES-128-CBC-SHA | Cipher suite TLS-DHE-DSS-WITH-AES-128-CBC-SHA.
      - choice | TLS-DHE-DSS-WITH-AES-256-CBC-SHA | Cipher suite TLS-DHE-DSS-WITH-AES-256-CBC-SHA.
      - choice | TLS-DHE-DSS-WITH-AES-128-CBC-SHA256 | Cipher suite TLS-DHE-DSS-WITH-AES-128-CBC-SHA256.
      - choice | TLS-DHE-DSS-WITH-AES-128-GCM-SHA256 | Cipher suite TLS-DHE-DSS-WITH-AES-128-GCM-SHA256.
      - choice | TLS-DHE-DSS-WITH-AES-256-CBC-SHA256 | Cipher suite TLS-DHE-DSS-WITH-AES-256-CBC-SHA256.
      - choice | TLS-DHE-DSS-WITH-AES-256-GCM-SHA384 | Cipher suite TLS-DHE-DSS-WITH-AES-256-GCM-SHA384.
      - choice | TLS-ECDHE-RSA-WITH-AES-128-CBC-SHA256 | Cipher suite TLS-ECDHE-RSA-WITH-AES-128-CBC-SHA256.
      - choice | TLS-ECDHE-RSA-WITH-AES-128-GCM-SHA256 | Cipher suite TLS-ECDHE-RSA-WITH-AES-128-GCM-SHA256.
      - choice | TLS-ECDHE-RSA-WITH-AES-256-CBC-SHA384 | Cipher suite TLS-ECDHE-RSA-WITH-AES-256-CBC-SHA384.
      - choice | TLS-ECDHE-RSA-WITH-AES-256-GCM-SHA384 | Cipher suite TLS-ECDHE-RSA-WITH-AES-256-GCM-SHA384.
      - choice | TLS-ECDHE-ECDSA-WITH-AES-128-CBC-SHA | Cipher suite TLS-ECDHE-ECDSA-WITH-AES-128-CBC-SHA.
      - choice | TLS-ECDHE-ECDSA-WITH-AES-128-CBC-SHA256 | Cipher suite TLS-ECDHE-ECDSA-WITH-AES-128-CBC-SHA256.
      - choice | TLS-ECDHE-ECDSA-WITH-AES-128-GCM-SHA256 | Cipher suite TLS-ECDHE-ECDSA-WITH-AES-128-GCM-SHA256.
      - choice | TLS-ECDHE-ECDSA-WITH-AES-256-CBC-SHA384 | Cipher suite TLS-ECDHE-ECDSA-WITH-AES-256-CBC-SHA384.
      - choice | TLS-ECDHE-ECDSA-WITH-AES-256-GCM-SHA384 | Cipher suite TLS-ECDHE-ECDSA-WITH-AES-256-GCM-SHA384.
      - choice | TLS-RSA-WITH-AES-128-GCM-SHA256 | Cipher suite TLS-RSA-WITH-AES-128-GCM-SHA256.
      - choice | TLS-RSA-WITH-AES-256-GCM-SHA384 | Cipher suite TLS-RSA-WITH-AES-256-GCM-SHA384.
      - choice | TLS-DHE-DSS-WITH-CAMELLIA-128-CBC-SHA | Cipher suite TLS-DSS-RSA-WITH-CAMELLIA-128-CBC-SHA.
      - choice | TLS-DHE-DSS-WITH-CAMELLIA-256-CBC-SHA | Cipher suite TLS-DHE-DSS-WITH-CAMELLIA-256-CBC-SHA.
      - choice | TLS-DHE-DSS-WITH-CAMELLIA-128-CBC-SHA256 | Cipher suite TLS-DHE-DSS-WITH-CAMELLIA-128-CBC-SHA256.
      - choice | TLS-DHE-DSS-WITH-CAMELLIA-256-CBC-SHA256 | Cipher suite TLS-DHE-DSS-WITH-CAMELLIA-256-CBC-SHA256.
      - choice | TLS-DHE-DSS-WITH-SEED-CBC-SHA | Cipher suite TLS-DHE-DSS-WITH-SEED-CBC-SHA.
      - choice | TLS-DHE-DSS-WITH-ARIA-128-CBC-SHA256 | Cipher suite TLS-DHE-DSS-WITH-ARIA-128-CBC-SHA256.
      - choice | TLS-DHE-DSS-WITH-ARIA-256-CBC-SHA384 | Cipher suite TLS-DHE-DSS-WITH-ARIA-256-CBC-SHA384.
      - choice | TLS-ECDHE-RSA-WITH-ARIA-128-CBC-SHA256 | Cipher suite TLS-ECDHE-RSA-WITH-ARIA-128-CBC-SHA256.
      - choice | TLS-ECDHE-RSA-WITH-ARIA-256-CBC-SHA384 | Cipher suite TLS-ECDHE-RSA-WITH-ARIA-256-CBC-SHA384.
      - choice | TLS-ECDHE-ECDSA-WITH-ARIA-128-CBC-SHA256 | Cipher suite TLS-ECDHE-ECDSA-WITH-ARIA-128-CBC_SHA256.
      - choice | TLS-ECDHE-ECDSA-WITH-ARIA-256-CBC-SHA384 | Cipher suite TLS-ECDHE-ECDSA-WITH-ARIA-256-CBC_SHA384.
      - choice | TLS-DHE-DSS-WITH-3DES-EDE-CBC-SHA | Cipher suite TLS-DHE-DSS-WITH-3DES-EDE-CBC-SHA.
      - choice | TLS-DHE-DSS-WITH-DES-CBC-SHA | Cipher suite TLS-DHE-DSS-WITH-DES-CBC-SHA.
    required: false
    choices: ["TLS-RSA-WITH-RC4-128-MD5",
            "TLS-RSA-WITH-RC4-128-SHA",
            "TLS-RSA-WITH-DES-CBC-SHA",
            "TLS-RSA-WITH-3DES-EDE-CBC-SHA",
            "TLS-RSA-WITH-AES-128-CBC-SHA",
            "TLS-RSA-WITH-AES-256-CBC-SHA",
            "TLS-RSA-WITH-AES-128-CBC-SHA256",
            "TLS-RSA-WITH-AES-256-CBC-SHA256",
            "TLS-RSA-WITH-CAMELLIA-128-CBC-SHA",
            "TLS-RSA-WITH-CAMELLIA-256-CBC-SHA",
            "TLS-RSA-WITH-CAMELLIA-128-CBC-SHA256",
            "TLS-RSA-WITH-CAMELLIA-256-CBC-SHA256",
            "TLS-RSA-WITH-SEED-CBC-SHA",
            "TLS-RSA-WITH-ARIA-128-CBC-SHA256",
            "TLS-RSA-WITH-ARIA-256-CBC-SHA384",
            "TLS-DHE-RSA-WITH-DES-CBC-SHA",
            "TLS-DHE-RSA-WITH-3DES-EDE-CBC-SHA",
            "TLS-DHE-RSA-WITH-AES-128-CBC-SHA",
            "TLS-DHE-RSA-WITH-AES-256-CBC-SHA",
            "TLS-DHE-RSA-WITH-AES-128-CBC-SHA256",
            "TLS-DHE-RSA-WITH-AES-256-CBC-SHA256",
            "TLS-DHE-RSA-WITH-CAMELLIA-128-CBC-SHA",
            "TLS-DHE-RSA-WITH-CAMELLIA-256-CBC-SHA",
            "TLS-DHE-RSA-WITH-CAMELLIA-128-CBC-SHA256",
            "TLS-DHE-RSA-WITH-CAMELLIA-256-CBC-SHA256",
            "TLS-DHE-RSA-WITH-SEED-CBC-SHA",
            "TLS-DHE-RSA-WITH-ARIA-128-CBC-SHA256",
            "TLS-DHE-RSA-WITH-ARIA-256-CBC-SHA384",
            "TLS-ECDHE-RSA-WITH-RC4-128-SHA",
            "TLS-ECDHE-RSA-WITH-3DES-EDE-CBC-SHA",
            "TLS-ECDHE-RSA-WITH-AES-128-CBC-SHA",
            "TLS-ECDHE-RSA-WITH-AES-256-CBC-SHA",
            "TLS-ECDHE-RSA-WITH-CHACHA20-POLY1305-SHA256",
            "TLS-ECDHE-ECDSA-WITH-CHACHA20-POLY1305-SHA256",
            "TLS-DHE-RSA-WITH-CHACHA20-POLY1305-SHA256",
            "TLS-DHE-RSA-WITH-AES-128-GCM-SHA256",
            "TLS-DHE-RSA-WITH-AES-256-GCM-SHA384",
            "TLS-DHE-DSS-WITH-AES-128-CBC-SHA",
            "TLS-DHE-DSS-WITH-AES-256-CBC-SHA",
            "TLS-DHE-DSS-WITH-AES-128-CBC-SHA256",
            "TLS-DHE-DSS-WITH-AES-128-GCM-SHA256",
            "TLS-DHE-DSS-WITH-AES-256-CBC-SHA256",
            "TLS-DHE-DSS-WITH-AES-256-GCM-SHA384",
            "TLS-ECDHE-RSA-WITH-AES-128-CBC-SHA256",
            "TLS-ECDHE-RSA-WITH-AES-128-GCM-SHA256",
            "TLS-ECDHE-RSA-WITH-AES-256-CBC-SHA384",
            "TLS-ECDHE-RSA-WITH-AES-256-GCM-SHA384",
            "TLS-ECDHE-ECDSA-WITH-AES-128-CBC-SHA",
            "TLS-ECDHE-ECDSA-WITH-AES-128-CBC-SHA256",
            "TLS-ECDHE-ECDSA-WITH-AES-128-GCM-SHA256",
            "TLS-ECDHE-ECDSA-WITH-AES-256-CBC-SHA384",
            "TLS-ECDHE-ECDSA-WITH-AES-256-GCM-SHA384",
            "TLS-RSA-WITH-AES-128-GCM-SHA256",
            "TLS-RSA-WITH-AES-256-GCM-SHA384",
            "TLS-DHE-DSS-WITH-CAMELLIA-128-CBC-SHA",
            "TLS-DHE-DSS-WITH-CAMELLIA-256-CBC-SHA",
            "TLS-DHE-DSS-WITH-CAMELLIA-128-CBC-SHA256",
            "TLS-DHE-DSS-WITH-CAMELLIA-256-CBC-SHA256",
            "TLS-DHE-DSS-WITH-SEED-CBC-SHA",
            "TLS-DHE-DSS-WITH-ARIA-128-CBC-SHA256",
            "TLS-DHE-DSS-WITH-ARIA-256-CBC-SHA384",
            "TLS-ECDHE-RSA-WITH-ARIA-128-CBC-SHA256",
            "TLS-ECDHE-RSA-WITH-ARIA-256-CBC-SHA384",
            "TLS-ECDHE-ECDSA-WITH-ARIA-128-CBC-SHA256",
            "TLS-ECDHE-ECDSA-WITH-ARIA-256-CBC-SHA384",
            "TLS-DHE-DSS-WITH-3DES-EDE-CBC-SHA",
            "TLS-DHE-DSS-WITH-DES-CBC-SHA"]

  ssl_server_cipher_suites_priority:
    description:
      - SSL/TLS cipher suites priority.
    required: false

  ssl_server_cipher_suites_versions:
    description:
      - SSL/TLS versions that the cipher suite can be used with.
      - FLAG Based Options. Specify multiple in list form.
      - flag | ssl-3.0 | SSL 3.0.
      - flag | tls-1.0 | TLS 1.0.
      - flag | tls-1.1 | TLS 1.1.
      - flag | tls-1.2 | TLS 1.2.
    required: false
    choices: ["ssl-3.0", "tls-1.0", "tls-1.1", "tls-1.2"]


'''

EXAMPLES = '''
# BASIC FULL STATIC NAT MAPPING
- name: EDIT FMGR_FIREWALL_VIP SNAT
  fmgr_fwobj_vip:
    name: "Basic StaticNAT Map"
    mode: "set"
    adom: "ansible"
    type: "static-nat"
    extip: "82.72.192.185"
    extintf: "any"
    mappedip: "10.7.220.25"
    comment: "Created by Ansible"
    color: "17"

# BASIC PORT PNAT MAPPING
- name: EDIT FMGR_FIREWALL_VIP PNAT
  fmgr_fwobj_vip:
    name: "Basic PNAT Map Port 10443"
    mode: "set"
    adom: "ansible"
    type: "static-nat"
    extip: "82.72.192.185"
    extport: "10443"
    extintf: "any"
    portforward: "enable"
    protocol: "tcp"
    mappedip: "10.7.220.25"
    mappedport: "443"
    comment: "Created by Ansible"
    color: "17"

# BASIC DNS TRANSLATION NAT
- name: EDIT FMGR_FIREWALL_DNST
  fmgr_fwobj_vip:
    name: "Basic DNS Translation"
    mode: "set"
    adom: "ansible"
    type: "dns-translation"
    extip: "192.168.0.1-192.168.0.100"
    extintf: "dmz"
    mappedip: "3.3.3.0/24, 4.0.0.0/24"
    comment: "Created by Ansible"
    color: "12"

# BASIC FQDN NAT
- name: EDIT FMGR_FIREWALL_FQDN
  fmgr_fwobj_vip:
    name: "Basic FQDN Translation"
    mode: "set"
    adom: "ansible"
    type: "fqdn"
    mapped_addr: "google-play"
    comment: "Created by Ansible"
    color: "5"

# DELETE AN ENTRY
- name: DELETE FMGR_FIREWALL_VIP PNAT
  fmgr_fwobj_vip:
    name: "Basic PNAT Map Port 10443"
    mode: "delete"
    adom: "ansible"
'''

RETURN = """
api_result:
  description: full API response, includes status code and message
  returned: always
  type: str
"""

from ansible.module_utils.basic import AnsibleModule, env_fallback
from ansible.module_utils.connection import Connection
from ansible.module_utils.network.fortimanager.fortimanager import FortiManagerHandler
from ansible.module_utils.network.fortimanager.common import FMGBaseException
from ansible.module_utils.network.fortimanager.common import FMGRCommon
from ansible.module_utils.network.fortimanager.common import FMGRMethods
from ansible.module_utils.network.fortimanager.common import DEFAULT_RESULT_OBJ
from ansible.module_utils.network.fortimanager.common import FAIL_SOCKET_MSG
from ansible.module_utils.network.fortimanager.common import prepare_dict
from ansible.module_utils.network.fortimanager.common import scrub_dict


def fmgr_firewall_vip_modify(fmgr, paramgram):
    """
    :param fmgr: The fmgr object instance from fortimanager.py
    :type fmgr: class object
    :param paramgram: The formatted dictionary of options to process
    :type paramgram: dict
    :return: The response from the FortiManager
    :rtype: dict
    """

    mode = paramgram["mode"]
    adom = paramgram["adom"]
    # INIT A BASIC OBJECTS
    response = DEFAULT_RESULT_OBJ
    url = ""
    datagram = {}

    # EVAL THE MODE PARAMETER FOR SET OR ADD
    if mode in ['set', 'add', 'update']:
        url = '/pm/config/adom/{adom}/obj/firewall/vip'.format(adom=adom)
        datagram = scrub_dict(prepare_dict(paramgram))

    # EVAL THE MODE PARAMETER FOR DELETE
    elif mode == "delete":
        # SET THE CORRECT URL FOR DELETE
        url = '/pm/config/adom/{adom}/obj/firewall/vip/{name}'.format(adom=adom, name=paramgram["name"])
        datagram = {}

    response = fmgr.process_request(url, datagram, paramgram["mode"])
    return response


#############
# END METHODS
#############


def main():
    argument_spec = dict(
        adom=dict(type="str", default="root"),
        mode=dict(choices=["add", "set", "delete", "update"], type="str", default="add"),

        websphere_server=dict(required=False, type="str", choices=["disable", "enable"]),
        weblogic_server=dict(required=False, type="str", choices=["disable", "enable"]),
        type=dict(required=False, type="str",
                  choices=["static-nat", "load-balance", "server-load-balance", "dns-translation", "fqdn"]),
        ssl_server_session_state_type=dict(required=False, type="str", choices=["disable", "time", "count", "both"]),
        ssl_server_session_state_timeout=dict(required=False, type="int"),
        ssl_server_session_state_max=dict(required=False, type="int"),
        ssl_server_min_version=dict(required=False, type="str",
                                    choices=["ssl-3.0", "tls-1.0", "tls-1.1", "tls-1.2", "client"]),
        ssl_server_max_version=dict(required=False, type="str",
                                    choices=["ssl-3.0", "tls-1.0", "tls-1.1", "tls-1.2", "client"]),
        ssl_server_algorithm=dict(required=False, type="str", choices=["high", "low", "medium", "custom", "client"]),
        ssl_send_empty_frags=dict(required=False, type="str", choices=["disable", "enable"]),
        ssl_pfs=dict(required=False, type="str", choices=["require", "deny", "allow"]),
        ssl_mode=dict(required=False, type="str", choices=["half", "full"]),
        ssl_min_version=dict(required=False, type="str", choices=["ssl-3.0", "tls-1.0", "tls-1.1", "tls-1.2"]),
        ssl_max_version=dict(required=False, type="str", choices=["ssl-3.0", "tls-1.0", "tls-1.1", "tls-1.2"]),
        ssl_http_match_host=dict(required=False, type="str", choices=["disable", "enable"]),
        ssl_http_location_conversion=dict(required=False, type="str", choices=["disable", "enable"]),
        ssl_hsts_include_subdomains=dict(required=False, type="str", choices=["disable", "enable"]),
        ssl_hsts_age=dict(required=False, type="int"),
        ssl_hsts=dict(required=False, type="str", choices=["disable", "enable"]),
        ssl_hpkp_report_uri=dict(required=False, type="str"),
        ssl_hpkp_primary=dict(required=False, type="str"),
        ssl_hpkp_include_subdomains=dict(required=False, type="str", choices=["disable", "enable"]),
        ssl_hpkp_backup=dict(required=False, type="str"),
        ssl_hpkp_age=dict(required=False, type="int"),
        ssl_hpkp=dict(required=False, type="str", choices=["disable", "enable", "report-only"]),
        ssl_dh_bits=dict(required=False, type="str", choices=["768", "1024", "1536", "2048", "3072", "4096"]),
        ssl_client_session_state_type=dict(required=False, type="str", choices=["disable", "time", "count", "both"]),
        ssl_client_session_state_timeout=dict(required=False, type="int"),
        ssl_client_session_state_max=dict(required=False, type="int"),
        ssl_client_renegotiation=dict(required=False, type="str", choices=["deny", "allow", "secure"]),
        ssl_client_fallback=dict(required=False, type="str", choices=["disable", "enable"]),
        ssl_certificate=dict(required=False, type="str"),
        ssl_algorithm=dict(required=False, type="str", choices=["high", "medium", "low", "custom"]),
        srcintf_filter=dict(required=False, type="str"),
        src_filter=dict(required=False, type="str"),
        service=dict(required=False, type="str"),
        server_type=dict(required=False, type="str",
                         choices=["http", "https", "ssl", "tcp", "udp", "ip", "imaps", "pop3s", "smtps"]),
        protocol=dict(required=False, type="str", choices=["tcp", "udp", "sctp", "icmp"]),
        portmapping_type=dict(required=False, type="str", choices=["1-to-1", "m-to-n"]),
        portforward=dict(required=False, type="str", choices=["disable", "enable"]),
        persistence=dict(required=False, type="str", choices=["none", "http-cookie", "ssl-session-id"]),
        outlook_web_access=dict(required=False, type="str", choices=["disable", "enable"]),
        nat_source_vip=dict(required=False, type="str", choices=["disable", "enable"]),
        name=dict(required=False, type="str"),
        monitor=dict(required=False, type="str"),
        max_embryonic_connections=dict(required=False, type="int"),
        mappedport=dict(required=False, type="str"),
        mappedip=dict(required=False, type="str"),
        mapped_addr=dict(required=False, type="str"),
        ldb_method=dict(required=False, type="str",
                        choices=["static", "round-robin", "weighted", "least-session", "least-rtt", "first-alive",
                                 "http-host"]),
        https_cookie_secure=dict(required=False, type="str", choices=["disable", "enable"]),
        http_multiplex=dict(required=False, type="str", choices=["disable", "enable"]),
        http_ip_header_name=dict(required=False, type="str"),
        http_ip_header=dict(required=False, type="str", choices=["disable", "enable"]),
        http_cookie_share=dict(required=False, type="str", choices=["disable", "same-ip"]),
        http_cookie_path=dict(required=False, type="str"),
        http_cookie_generation=dict(required=False, type="int"),
        http_cookie_domain_from_host=dict(required=False, type="str", choices=["disable", "enable"]),
        http_cookie_domain=dict(required=False, type="str"),
        http_cookie_age=dict(required=False, type="int"),
        gratuitous_arp_interval=dict(required=False, type="int"),
        extport=dict(required=False, type="str"),
        extip=dict(required=False, type="str"),
        extintf=dict(required=False, type="str"),
        extaddr=dict(required=False, type="str"),
        dns_mapping_ttl=dict(required=False, type="int"),
        comment=dict(required=False, type="str"),
        color=dict(required=False, type="int"),
        arp_reply=dict(required=False, type="str", choices=["disable", "enable"]),
        dynamic_mapping=dict(required=False, type="list"),
        dynamic_mapping_arp_reply=dict(required=False, type="str", choices=["disable", "enable"]),
        dynamic_mapping_color=dict(required=False, type="int"),
        dynamic_mapping_comment=dict(required=False, type="str"),
        dynamic_mapping_dns_mapping_ttl=dict(required=False, type="int"),
        dynamic_mapping_extaddr=dict(required=False, type="str"),
        dynamic_mapping_extintf=dict(required=False, type="str"),
        dynamic_mapping_extip=dict(required=False, type="str"),
        dynamic_mapping_extport=dict(required=False, type="str"),
        dynamic_mapping_gratuitous_arp_interval=dict(required=False, type="int"),
        dynamic_mapping_http_cookie_age=dict(required=False, type="int"),
        dynamic_mapping_http_cookie_domain=dict(required=False, type="str"),
        dynamic_mapping_http_cookie_domain_from_host=dict(required=False, type="str", choices=["disable", "enable"]),
        dynamic_mapping_http_cookie_generation=dict(required=False, type="int"),
        dynamic_mapping_http_cookie_path=dict(required=False, type="str"),
        dynamic_mapping_http_cookie_share=dict(required=False, type="str", choices=["disable", "same-ip"]),
        dynamic_mapping_http_ip_header=dict(required=False, type="str", choices=["disable", "enable"]),
        dynamic_mapping_http_ip_header_name=dict(required=False, type="str"),
        dynamic_mapping_http_multiplex=dict(required=False, type="str", choices=["disable", "enable"]),
        dynamic_mapping_https_cookie_secure=dict(required=False, type="str", choices=["disable", "enable"]),
        dynamic_mapping_ldb_method=dict(required=False, type="str", choices=["static",
                                                                             "round-robin",
                                                                             "weighted",
                                                                             "least-session",
                                                                             "least-rtt",
                                                                             "first-alive",
                                                                             "http-host"]),
        dynamic_mapping_mapped_addr=dict(required=False, type="str"),
        dynamic_mapping_mappedip=dict(required=False, type="str"),
        dynamic_mapping_mappedport=dict(required=False, type="str"),
        dynamic_mapping_max_embryonic_connections=dict(required=False, type="int"),
        dynamic_mapping_monitor=dict(required=False, type="str"),
        dynamic_mapping_nat_source_vip=dict(required=False, type="str", choices=["disable", "enable"]),
        dynamic_mapping_outlook_web_access=dict(required=False, type="str", choices=["disable", "enable"]),
        dynamic_mapping_persistence=dict(required=False, type="str", choices=["none", "http-cookie", "ssl-session-id"]),
        dynamic_mapping_portforward=dict(required=False, type="str", choices=["disable", "enable"]),
        dynamic_mapping_portmapping_type=dict(required=False, type="str", choices=["1-to-1", "m-to-n"]),
        dynamic_mapping_protocol=dict(required=False, type="str", choices=["tcp", "udp", "sctp", "icmp"]),
        dynamic_mapping_server_type=dict(required=False, type="str",
                                         choices=["http", "https", "ssl", "tcp", "udp", "ip", "imaps", "pop3s",
                                                  "smtps"]),
        dynamic_mapping_service=dict(required=False, type="str"),
        dynamic_mapping_src_filter=dict(required=False, type="str"),
        dynamic_mapping_srcintf_filter=dict(required=False, type="str"),
        dynamic_mapping_ssl_algorithm=dict(required=False, type="str", choices=["high", "medium", "low", "custom"]),
        dynamic_mapping_ssl_certificate=dict(required=False, type="str"),
        dynamic_mapping_ssl_client_fallback=dict(required=False, type="str", choices=["disable", "enable"]),
        dynamic_mapping_ssl_client_renegotiation=dict(required=False, type="str", choices=["deny", "allow", "secure"]),
        dynamic_mapping_ssl_client_session_state_max=dict(required=False, type="int"),
        dynamic_mapping_ssl_client_session_state_timeout=dict(required=False, type="int"),
        dynamic_mapping_ssl_client_session_state_type=dict(required=False, type="str",
                                                           choices=["disable", "time", "count", "both"]),
        dynamic_mapping_ssl_dh_bits=dict(required=False, type="str",
                                         choices=["768", "1024", "1536", "2048", "3072", "4096"]),
        dynamic_mapping_ssl_hpkp=dict(required=False, type="str", choices=["disable", "enable", "report-only"]),
        dynamic_mapping_ssl_hpkp_age=dict(required=False, type="int"),
        dynamic_mapping_ssl_hpkp_backup=dict(required=False, type="str"),
        dynamic_mapping_ssl_hpkp_include_subdomains=dict(required=False, type="str", choices=["disable", "enable"]),
        dynamic_mapping_ssl_hpkp_primary=dict(required=False, type="str"),
        dynamic_mapping_ssl_hpkp_report_uri=dict(required=False, type="str"),
        dynamic_mapping_ssl_hsts=dict(required=False, type="str", choices=["disable", "enable"]),
        dynamic_mapping_ssl_hsts_age=dict(required=False, type="int"),
        dynamic_mapping_ssl_hsts_include_subdomains=dict(required=False, type="str", choices=["disable", "enable"]),
        dynamic_mapping_ssl_http_location_conversion=dict(required=False, type="str", choices=["disable", "enable"]),
        dynamic_mapping_ssl_http_match_host=dict(required=False, type="str", choices=["disable", "enable"]),
        dynamic_mapping_ssl_max_version=dict(required=False, type="str",
                                             choices=["ssl-3.0", "tls-1.0", "tls-1.1", "tls-1.2"]),
        dynamic_mapping_ssl_min_version=dict(required=False, type="str",
                                             choices=["ssl-3.0", "tls-1.0", "tls-1.1", "tls-1.2"]),
        dynamic_mapping_ssl_mode=dict(required=False, type="str", choices=["half", "full"]),
        dynamic_mapping_ssl_pfs=dict(required=False, type="str", choices=["require", "deny", "allow"]),
        dynamic_mapping_ssl_send_empty_frags=dict(required=False, type="str", choices=["disable", "enable"]),
        dynamic_mapping_ssl_server_algorithm=dict(required=False, type="str",
                                                  choices=["high", "low", "medium", "custom", "client"]),
        dynamic_mapping_ssl_server_max_version=dict(required=False, type="str",
                                                    choices=["ssl-3.0", "tls-1.0", "tls-1.1", "tls-1.2", "client"]),
        dynamic_mapping_ssl_server_min_version=dict(required=False, type="str",
                                                    choices=["ssl-3.0", "tls-1.0", "tls-1.1", "tls-1.2", "client"]),
        dynamic_mapping_ssl_server_session_state_max=dict(required=False, type="int"),
        dynamic_mapping_ssl_server_session_state_timeout=dict(required=False, type="int"),
        dynamic_mapping_ssl_server_session_state_type=dict(required=False, type="str",
                                                           choices=["disable", "time", "count", "both"]),
        dynamic_mapping_type=dict(required=False, type="str",
                                  choices=["static-nat", "load-balance", "server-load-balance", "dns-translation",
                                           "fqdn"]),
        dynamic_mapping_weblogic_server=dict(required=False, type="str", choices=["disable", "enable"]),
        dynamic_mapping_websphere_server=dict(required=False, type="str", choices=["disable", "enable"]),

        dynamic_mapping_realservers_client_ip=dict(required=False, type="str"),
        dynamic_mapping_realservers_healthcheck=dict(required=False, type="str", choices=["disable", "enable", "vip"]),
        dynamic_mapping_realservers_holddown_interval=dict(required=False, type="int"),
        dynamic_mapping_realservers_http_host=dict(required=False, type="str"),
        dynamic_mapping_realservers_ip=dict(required=False, type="str"),
        dynamic_mapping_realservers_max_connections=dict(required=False, type="int"),
        dynamic_mapping_realservers_monitor=dict(required=False, type="str"),
        dynamic_mapping_realservers_port=dict(required=False, type="int"),
        dynamic_mapping_realservers_seq=dict(required=False, type="str"),
        dynamic_mapping_realservers_status=dict(required=False, type="str", choices=["active", "standby", "disable"]),
        dynamic_mapping_realservers_weight=dict(required=False, type="int"),

        dynamic_mapping_ssl_cipher_suites_cipher=dict(required=False,
                                                      type="str",
                                                      choices=["TLS-RSA-WITH-RC4-128-MD5",
                                                               "TLS-RSA-WITH-RC4-128-SHA",
                                                               "TLS-RSA-WITH-DES-CBC-SHA",
                                                               "TLS-RSA-WITH-3DES-EDE-CBC-SHA",
                                                               "TLS-RSA-WITH-AES-128-CBC-SHA",
                                                               "TLS-RSA-WITH-AES-256-CBC-SHA",
                                                               "TLS-RSA-WITH-AES-128-CBC-SHA256",
                                                               "TLS-RSA-WITH-AES-256-CBC-SHA256",
                                                               "TLS-RSA-WITH-CAMELLIA-128-CBC-SHA",
                                                               "TLS-RSA-WITH-CAMELLIA-256-CBC-SHA",
                                                               "TLS-RSA-WITH-CAMELLIA-128-CBC-SHA256",
                                                               "TLS-RSA-WITH-CAMELLIA-256-CBC-SHA256",
                                                               "TLS-RSA-WITH-SEED-CBC-SHA",
                                                               "TLS-RSA-WITH-ARIA-128-CBC-SHA256",
                                                               "TLS-RSA-WITH-ARIA-256-CBC-SHA384",
                                                               "TLS-DHE-RSA-WITH-DES-CBC-SHA",
                                                               "TLS-DHE-RSA-WITH-3DES-EDE-CBC-SHA",
                                                               "TLS-DHE-RSA-WITH-AES-128-CBC-SHA",
                                                               "TLS-DHE-RSA-WITH-AES-256-CBC-SHA",
                                                               "TLS-DHE-RSA-WITH-AES-128-CBC-SHA256",
                                                               "TLS-DHE-RSA-WITH-AES-256-CBC-SHA256",
                                                               "TLS-DHE-RSA-WITH-CAMELLIA-128-CBC-SHA",
                                                               "TLS-DHE-RSA-WITH-CAMELLIA-256-CBC-SHA",
                                                               "TLS-DHE-RSA-WITH-CAMELLIA-128-CBC-SHA256",
                                                               "TLS-DHE-RSA-WITH-CAMELLIA-256-CBC-SHA256",
                                                               "TLS-DHE-RSA-WITH-SEED-CBC-SHA",
                                                               "TLS-DHE-RSA-WITH-ARIA-128-CBC-SHA256",
                                                               "TLS-DHE-RSA-WITH-ARIA-256-CBC-SHA384",
                                                               "TLS-ECDHE-RSA-WITH-RC4-128-SHA",
                                                               "TLS-ECDHE-RSA-WITH-3DES-EDE-CBC-SHA",
                                                               "TLS-ECDHE-RSA-WITH-AES-128-CBC-SHA",
                                                               "TLS-ECDHE-RSA-WITH-AES-256-CBC-SHA",
                                                               "TLS-ECDHE-RSA-WITH-CHACHA20-POLY1305-SHA256",
                                                               "TLS-ECDHE-ECDSA-WITH-CHACHA20-POLY1305-SHA256",
                                                               "TLS-DHE-RSA-WITH-CHACHA20-POLY1305-SHA256",
                                                               "TLS-DHE-RSA-WITH-AES-128-GCM-SHA256",
                                                               "TLS-DHE-RSA-WITH-AES-256-GCM-SHA384",
                                                               "TLS-DHE-DSS-WITH-AES-128-CBC-SHA",
                                                               "TLS-DHE-DSS-WITH-AES-256-CBC-SHA",
                                                               "TLS-DHE-DSS-WITH-AES-128-CBC-SHA256",
                                                               "TLS-DHE-DSS-WITH-AES-128-GCM-SHA256",
                                                               "TLS-DHE-DSS-WITH-AES-256-CBC-SHA256",
                                                               "TLS-DHE-DSS-WITH-AES-256-GCM-SHA384",
                                                               "TLS-ECDHE-RSA-WITH-AES-128-CBC-SHA256",
                                                               "TLS-ECDHE-RSA-WITH-AES-128-GCM-SHA256",
                                                               "TLS-ECDHE-RSA-WITH-AES-256-CBC-SHA384",
                                                               "TLS-ECDHE-RSA-WITH-AES-256-GCM-SHA384",
                                                               "TLS-ECDHE-ECDSA-WITH-AES-128-CBC-SHA",
                                                               "TLS-ECDHE-ECDSA-WITH-AES-128-CBC-SHA256",
                                                               "TLS-ECDHE-ECDSA-WITH-AES-128-GCM-SHA256",
                                                               "TLS-ECDHE-ECDSA-WITH-AES-256-CBC-SHA384",
                                                               "TLS-ECDHE-ECDSA-WITH-AES-256-GCM-SHA384",
                                                               "TLS-RSA-WITH-AES-128-GCM-SHA256",
                                                               "TLS-RSA-WITH-AES-256-GCM-SHA384",
                                                               "TLS-DHE-DSS-WITH-CAMELLIA-128-CBC-SHA",
                                                               "TLS-DHE-DSS-WITH-CAMELLIA-256-CBC-SHA",
                                                               "TLS-DHE-DSS-WITH-CAMELLIA-128-CBC-SHA256",
                                                               "TLS-DHE-DSS-WITH-CAMELLIA-256-CBC-SHA256",
                                                               "TLS-DHE-DSS-WITH-SEED-CBC-SHA",
                                                               "TLS-DHE-DSS-WITH-ARIA-128-CBC-SHA256",
                                                               "TLS-DHE-DSS-WITH-ARIA-256-CBC-SHA384",
                                                               "TLS-ECDHE-RSA-WITH-ARIA-128-CBC-SHA256",
                                                               "TLS-ECDHE-RSA-WITH-ARIA-256-CBC-SHA384",
                                                               "TLS-ECDHE-ECDSA-WITH-ARIA-128-CBC-SHA256",
                                                               "TLS-ECDHE-ECDSA-WITH-ARIA-256-CBC-SHA384",
                                                               "TLS-DHE-DSS-WITH-3DES-EDE-CBC-SHA",
                                                               "TLS-DHE-DSS-WITH-DES-CBC-SHA"]),
        dynamic_mapping_ssl_cipher_suites_versions=dict(required=False, type="str",
                                                        choices=["ssl-3.0", "tls-1.0", "tls-1.1", "tls-1.2"]),
        realservers=dict(required=False, type="list"),
        realservers_client_ip=dict(required=False, type="str"),
        realservers_healthcheck=dict(required=False, type="str", choices=["disable", "enable", "vip"]),
        realservers_holddown_interval=dict(required=False, type="int"),
        realservers_http_host=dict(required=False, type="str"),
        realservers_ip=dict(required=False, type="str"),
        realservers_max_connections=dict(required=False, type="int"),
        realservers_monitor=dict(required=False, type="str"),
        realservers_port=dict(required=False, type="int"),
        realservers_seq=dict(required=False, type="str"),
        realservers_status=dict(required=False, type="str", choices=["active", "standby", "disable"]),
        realservers_weight=dict(required=False, type="int"),
        ssl_cipher_suites=dict(required=False, type="list"),
        ssl_cipher_suites_cipher=dict(required=False,
                                      type="str",
                                      choices=["TLS-RSA-WITH-RC4-128-MD5",
                                               "TLS-RSA-WITH-RC4-128-SHA",
                                               "TLS-RSA-WITH-DES-CBC-SHA",
                                               "TLS-RSA-WITH-3DES-EDE-CBC-SHA",
                                               "TLS-RSA-WITH-AES-128-CBC-SHA",
                                               "TLS-RSA-WITH-AES-256-CBC-SHA",
                                               "TLS-RSA-WITH-AES-128-CBC-SHA256",
                                               "TLS-RSA-WITH-AES-256-CBC-SHA256",
                                               "TLS-RSA-WITH-CAMELLIA-128-CBC-SHA",
                                               "TLS-RSA-WITH-CAMELLIA-256-CBC-SHA",
                                               "TLS-RSA-WITH-CAMELLIA-128-CBC-SHA256",
                                               "TLS-RSA-WITH-CAMELLIA-256-CBC-SHA256",
                                               "TLS-RSA-WITH-SEED-CBC-SHA",
                                               "TLS-RSA-WITH-ARIA-128-CBC-SHA256",
                                               "TLS-RSA-WITH-ARIA-256-CBC-SHA384",
                                               "TLS-DHE-RSA-WITH-DES-CBC-SHA",
                                               "TLS-DHE-RSA-WITH-3DES-EDE-CBC-SHA",
                                               "TLS-DHE-RSA-WITH-AES-128-CBC-SHA",
                                               "TLS-DHE-RSA-WITH-AES-256-CBC-SHA",
                                               "TLS-DHE-RSA-WITH-AES-128-CBC-SHA256",
                                               "TLS-DHE-RSA-WITH-AES-256-CBC-SHA256",
                                               "TLS-DHE-RSA-WITH-CAMELLIA-128-CBC-SHA",
                                               "TLS-DHE-RSA-WITH-CAMELLIA-256-CBC-SHA",
                                               "TLS-DHE-RSA-WITH-CAMELLIA-128-CBC-SHA256",
                                               "TLS-DHE-RSA-WITH-CAMELLIA-256-CBC-SHA256",
                                               "TLS-DHE-RSA-WITH-SEED-CBC-SHA",
                                               "TLS-DHE-RSA-WITH-ARIA-128-CBC-SHA256",
                                               "TLS-DHE-RSA-WITH-ARIA-256-CBC-SHA384",
                                               "TLS-ECDHE-RSA-WITH-RC4-128-SHA",
                                               "TLS-ECDHE-RSA-WITH-3DES-EDE-CBC-SHA",
                                               "TLS-ECDHE-RSA-WITH-AES-128-CBC-SHA",
                                               "TLS-ECDHE-RSA-WITH-AES-256-CBC-SHA",
                                               "TLS-ECDHE-RSA-WITH-CHACHA20-POLY1305-SHA256",
                                               "TLS-ECDHE-ECDSA-WITH-CHACHA20-POLY1305-SHA256",
                                               "TLS-DHE-RSA-WITH-CHACHA20-POLY1305-SHA256",
                                               "TLS-DHE-RSA-WITH-AES-128-GCM-SHA256",
                                               "TLS-DHE-RSA-WITH-AES-256-GCM-SHA384",
                                               "TLS-DHE-DSS-WITH-AES-128-CBC-SHA",
                                               "TLS-DHE-DSS-WITH-AES-256-CBC-SHA",
                                               "TLS-DHE-DSS-WITH-AES-128-CBC-SHA256",
                                               "TLS-DHE-DSS-WITH-AES-128-GCM-SHA256",
                                               "TLS-DHE-DSS-WITH-AES-256-CBC-SHA256",
                                               "TLS-DHE-DSS-WITH-AES-256-GCM-SHA384",
                                               "TLS-ECDHE-RSA-WITH-AES-128-CBC-SHA256",
                                               "TLS-ECDHE-RSA-WITH-AES-128-GCM-SHA256",
                                               "TLS-ECDHE-RSA-WITH-AES-256-CBC-SHA384",
                                               "TLS-ECDHE-RSA-WITH-AES-256-GCM-SHA384",
                                               "TLS-ECDHE-ECDSA-WITH-AES-128-CBC-SHA",
                                               "TLS-ECDHE-ECDSA-WITH-AES-128-CBC-SHA256",
                                               "TLS-ECDHE-ECDSA-WITH-AES-128-GCM-SHA256",
                                               "TLS-ECDHE-ECDSA-WITH-AES-256-CBC-SHA384",
                                               "TLS-ECDHE-ECDSA-WITH-AES-256-GCM-SHA384",
                                               "TLS-RSA-WITH-AES-128-GCM-SHA256",
                                               "TLS-RSA-WITH-AES-256-GCM-SHA384",
                                               "TLS-DHE-DSS-WITH-CAMELLIA-128-CBC-SHA",
                                               "TLS-DHE-DSS-WITH-CAMELLIA-256-CBC-SHA",
                                               "TLS-DHE-DSS-WITH-CAMELLIA-128-CBC-SHA256",
                                               "TLS-DHE-DSS-WITH-CAMELLIA-256-CBC-SHA256",
                                               "TLS-DHE-DSS-WITH-SEED-CBC-SHA",
                                               "TLS-DHE-DSS-WITH-ARIA-128-CBC-SHA256",
                                               "TLS-DHE-DSS-WITH-ARIA-256-CBC-SHA384",
                                               "TLS-ECDHE-RSA-WITH-ARIA-128-CBC-SHA256",
                                               "TLS-ECDHE-RSA-WITH-ARIA-256-CBC-SHA384",
                                               "TLS-ECDHE-ECDSA-WITH-ARIA-128-CBC-SHA256",
                                               "TLS-ECDHE-ECDSA-WITH-ARIA-256-CBC-SHA384",
                                               "TLS-DHE-DSS-WITH-3DES-EDE-CBC-SHA",
                                               "TLS-DHE-DSS-WITH-DES-CBC-SHA"]),
        ssl_cipher_suites_versions=dict(required=False, type="str",
                                        choices=["ssl-3.0", "tls-1.0", "tls-1.1", "tls-1.2"]),
        ssl_server_cipher_suites=dict(required=False, type="list"),
        ssl_server_cipher_suites_cipher=dict(required=False,
                                             type="str",
                                             choices=["TLS-RSA-WITH-RC4-128-MD5",
                                                      "TLS-RSA-WITH-RC4-128-SHA",
                                                      "TLS-RSA-WITH-DES-CBC-SHA",
                                                      "TLS-RSA-WITH-3DES-EDE-CBC-SHA",
                                                      "TLS-RSA-WITH-AES-128-CBC-SHA",
                                                      "TLS-RSA-WITH-AES-256-CBC-SHA",
                                                      "TLS-RSA-WITH-AES-128-CBC-SHA256",
                                                      "TLS-RSA-WITH-AES-256-CBC-SHA256",
                                                      "TLS-RSA-WITH-CAMELLIA-128-CBC-SHA",
                                                      "TLS-RSA-WITH-CAMELLIA-256-CBC-SHA",
                                                      "TLS-RSA-WITH-CAMELLIA-128-CBC-SHA256",
                                                      "TLS-RSA-WITH-CAMELLIA-256-CBC-SHA256",
                                                      "TLS-RSA-WITH-SEED-CBC-SHA",
                                                      "TLS-RSA-WITH-ARIA-128-CBC-SHA256",
                                                      "TLS-RSA-WITH-ARIA-256-CBC-SHA384",
                                                      "TLS-DHE-RSA-WITH-DES-CBC-SHA",
                                                      "TLS-DHE-RSA-WITH-3DES-EDE-CBC-SHA",
                                                      "TLS-DHE-RSA-WITH-AES-128-CBC-SHA",
                                                      "TLS-DHE-RSA-WITH-AES-256-CBC-SHA",
                                                      "TLS-DHE-RSA-WITH-AES-128-CBC-SHA256",
                                                      "TLS-DHE-RSA-WITH-AES-256-CBC-SHA256",
                                                      "TLS-DHE-RSA-WITH-CAMELLIA-128-CBC-SHA",
                                                      "TLS-DHE-RSA-WITH-CAMELLIA-256-CBC-SHA",
                                                      "TLS-DHE-RSA-WITH-CAMELLIA-128-CBC-SHA256",
                                                      "TLS-DHE-RSA-WITH-CAMELLIA-256-CBC-SHA256",
                                                      "TLS-DHE-RSA-WITH-SEED-CBC-SHA",
                                                      "TLS-DHE-RSA-WITH-ARIA-128-CBC-SHA256",
                                                      "TLS-DHE-RSA-WITH-ARIA-256-CBC-SHA384",
                                                      "TLS-ECDHE-RSA-WITH-RC4-128-SHA",
                                                      "TLS-ECDHE-RSA-WITH-3DES-EDE-CBC-SHA",
                                                      "TLS-ECDHE-RSA-WITH-AES-128-CBC-SHA",
                                                      "TLS-ECDHE-RSA-WITH-AES-256-CBC-SHA",
                                                      "TLS-ECDHE-RSA-WITH-CHACHA20-POLY1305-SHA256",
                                                      "TLS-ECDHE-ECDSA-WITH-CHACHA20-POLY1305-SHA256",
                                                      "TLS-DHE-RSA-WITH-CHACHA20-POLY1305-SHA256",
                                                      "TLS-DHE-RSA-WITH-AES-128-GCM-SHA256",
                                                      "TLS-DHE-RSA-WITH-AES-256-GCM-SHA384",
                                                      "TLS-DHE-DSS-WITH-AES-128-CBC-SHA",
                                                      "TLS-DHE-DSS-WITH-AES-256-CBC-SHA",
                                                      "TLS-DHE-DSS-WITH-AES-128-CBC-SHA256",
                                                      "TLS-DHE-DSS-WITH-AES-128-GCM-SHA256",
                                                      "TLS-DHE-DSS-WITH-AES-256-CBC-SHA256",
                                                      "TLS-DHE-DSS-WITH-AES-256-GCM-SHA384",
                                                      "TLS-ECDHE-RSA-WITH-AES-128-CBC-SHA256",
                                                      "TLS-ECDHE-RSA-WITH-AES-128-GCM-SHA256",
                                                      "TLS-ECDHE-RSA-WITH-AES-256-CBC-SHA384",
                                                      "TLS-ECDHE-RSA-WITH-AES-256-GCM-SHA384",
                                                      "TLS-ECDHE-ECDSA-WITH-AES-128-CBC-SHA",
                                                      "TLS-ECDHE-ECDSA-WITH-AES-128-CBC-SHA256",
                                                      "TLS-ECDHE-ECDSA-WITH-AES-128-GCM-SHA256",
                                                      "TLS-ECDHE-ECDSA-WITH-AES-256-CBC-SHA384",
                                                      "TLS-ECDHE-ECDSA-WITH-AES-256-GCM-SHA384",
                                                      "TLS-RSA-WITH-AES-128-GCM-SHA256",
                                                      "TLS-RSA-WITH-AES-256-GCM-SHA384",
                                                      "TLS-DHE-DSS-WITH-CAMELLIA-128-CBC-SHA",
                                                      "TLS-DHE-DSS-WITH-CAMELLIA-256-CBC-SHA",
                                                      "TLS-DHE-DSS-WITH-CAMELLIA-128-CBC-SHA256",
                                                      "TLS-DHE-DSS-WITH-CAMELLIA-256-CBC-SHA256",
                                                      "TLS-DHE-DSS-WITH-SEED-CBC-SHA",
                                                      "TLS-DHE-DSS-WITH-ARIA-128-CBC-SHA256",
                                                      "TLS-DHE-DSS-WITH-ARIA-256-CBC-SHA384",
                                                      "TLS-ECDHE-RSA-WITH-ARIA-128-CBC-SHA256",
                                                      "TLS-ECDHE-RSA-WITH-ARIA-256-CBC-SHA384",
                                                      "TLS-ECDHE-ECDSA-WITH-ARIA-128-CBC-SHA256",
                                                      "TLS-ECDHE-ECDSA-WITH-ARIA-256-CBC-SHA384",
                                                      "TLS-DHE-DSS-WITH-3DES-EDE-CBC-SHA",
                                                      "TLS-DHE-DSS-WITH-DES-CBC-SHA"]),
        ssl_server_cipher_suites_priority=dict(required=False, type="str"),
        ssl_server_cipher_suites_versions=dict(required=False, type="str",
                                               choices=["ssl-3.0", "tls-1.0", "tls-1.1", "tls-1.2"]),

    )

    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=False, )
    # MODULE PARAMGRAM
    paramgram = {
        "mode": module.params["mode"],
        "adom": module.params["adom"],
        "websphere-server": module.params["websphere_server"],
        "weblogic-server": module.params["weblogic_server"],
        "type": module.params["type"],
        "ssl-server-session-state-type": module.params["ssl_server_session_state_type"],
        "ssl-server-session-state-timeout": module.params["ssl_server_session_state_timeout"],
        "ssl-server-session-state-max": module.params["ssl_server_session_state_max"],
        "ssl-server-min-version": module.params["ssl_server_min_version"],
        "ssl-server-max-version": module.params["ssl_server_max_version"],
        "ssl-server-algorithm": module.params["ssl_server_algorithm"],
        "ssl-send-empty-frags": module.params["ssl_send_empty_frags"],
        "ssl-pfs": module.params["ssl_pfs"],
        "ssl-mode": module.params["ssl_mode"],
        "ssl-min-version": module.params["ssl_min_version"],
        "ssl-max-version": module.params["ssl_max_version"],
        "ssl-http-match-host": module.params["ssl_http_match_host"],
        "ssl-http-location-conversion": module.params["ssl_http_location_conversion"],
        "ssl-hsts-include-subdomains": module.params["ssl_hsts_include_subdomains"],
        "ssl-hsts-age": module.params["ssl_hsts_age"],
        "ssl-hsts": module.params["ssl_hsts"],
        "ssl-hpkp-report-uri": module.params["ssl_hpkp_report_uri"],
        "ssl-hpkp-primary": module.params["ssl_hpkp_primary"],
        "ssl-hpkp-include-subdomains": module.params["ssl_hpkp_include_subdomains"],
        "ssl-hpkp-backup": module.params["ssl_hpkp_backup"],
        "ssl-hpkp-age": module.params["ssl_hpkp_age"],
        "ssl-hpkp": module.params["ssl_hpkp"],
        "ssl-dh-bits": module.params["ssl_dh_bits"],
        "ssl-client-session-state-type": module.params["ssl_client_session_state_type"],
        "ssl-client-session-state-timeout": module.params["ssl_client_session_state_timeout"],
        "ssl-client-session-state-max": module.params["ssl_client_session_state_max"],
        "ssl-client-renegotiation": module.params["ssl_client_renegotiation"],
        "ssl-client-fallback": module.params["ssl_client_fallback"],
        "ssl-certificate": module.params["ssl_certificate"],
        "ssl-algorithm": module.params["ssl_algorithm"],
        "srcintf-filter": module.params["srcintf_filter"],
        "src-filter": module.params["src_filter"],
        "service": module.params["service"],
        "server-type": module.params["server_type"],
        "protocol": module.params["protocol"],
        "portmapping-type": module.params["portmapping_type"],
        "portforward": module.params["portforward"],
        "persistence": module.params["persistence"],
        "outlook-web-access": module.params["outlook_web_access"],
        "nat-source-vip": module.params["nat_source_vip"],
        "name": module.params["name"],
        "monitor": module.params["monitor"],
        "max-embryonic-connections": module.params["max_embryonic_connections"],
        "mappedport": module.params["mappedport"],
        "mappedip": module.params["mappedip"],
        "mapped-addr": module.params["mapped_addr"],
        "ldb-method": module.params["ldb_method"],
        "https-cookie-secure": module.params["https_cookie_secure"],
        "http-multiplex": module.params["http_multiplex"],
        "http-ip-header-name": module.params["http_ip_header_name"],
        "http-ip-header": module.params["http_ip_header"],
        "http-cookie-share": module.params["http_cookie_share"],
        "http-cookie-path": module.params["http_cookie_path"],
        "http-cookie-generation": module.params["http_cookie_generation"],
        "http-cookie-domain-from-host": module.params["http_cookie_domain_from_host"],
        "http-cookie-domain": module.params["http_cookie_domain"],
        "http-cookie-age": module.params["http_cookie_age"],
        "gratuitous-arp-interval": module.params["gratuitous_arp_interval"],
        "extport": module.params["extport"],
        "extip": module.params["extip"],
        "extintf": module.params["extintf"],
        "extaddr": module.params["extaddr"],
        "dns-mapping-ttl": module.params["dns_mapping_ttl"],
        "comment": module.params["comment"],
        "color": module.params["color"],
        "arp-reply": module.params["arp_reply"],
        "dynamic_mapping": {
            "arp-reply": module.params["dynamic_mapping_arp_reply"],
            "color": module.params["dynamic_mapping_color"],
            "comment": module.params["dynamic_mapping_comment"],
            "dns-mapping-ttl": module.params["dynamic_mapping_dns_mapping_ttl"],
            "extaddr": module.params["dynamic_mapping_extaddr"],
            "extintf": module.params["dynamic_mapping_extintf"],
            "extip": module.params["dynamic_mapping_extip"],
            "extport": module.params["dynamic_mapping_extport"],
            "gratuitous-arp-interval": module.params["dynamic_mapping_gratuitous_arp_interval"],
            "http-cookie-age": module.params["dynamic_mapping_http_cookie_age"],
            "http-cookie-domain": module.params["dynamic_mapping_http_cookie_domain"],
            "http-cookie-domain-from-host": module.params["dynamic_mapping_http_cookie_domain_from_host"],
            "http-cookie-generation": module.params["dynamic_mapping_http_cookie_generation"],
            "http-cookie-path": module.params["dynamic_mapping_http_cookie_path"],
            "http-cookie-share": module.params["dynamic_mapping_http_cookie_share"],
            "http-ip-header": module.params["dynamic_mapping_http_ip_header"],
            "http-ip-header-name": module.params["dynamic_mapping_http_ip_header_name"],
            "http-multiplex": module.params["dynamic_mapping_http_multiplex"],
            "https-cookie-secure": module.params["dynamic_mapping_https_cookie_secure"],
            "ldb-method": module.params["dynamic_mapping_ldb_method"],
            "mapped-addr": module.params["dynamic_mapping_mapped_addr"],
            "mappedip": module.params["dynamic_mapping_mappedip"],
            "mappedport": module.params["dynamic_mapping_mappedport"],
            "max-embryonic-connections": module.params["dynamic_mapping_max_embryonic_connections"],
            "monitor": module.params["dynamic_mapping_monitor"],
            "nat-source-vip": module.params["dynamic_mapping_nat_source_vip"],
            "outlook-web-access": module.params["dynamic_mapping_outlook_web_access"],
            "persistence": module.params["dynamic_mapping_persistence"],
            "portforward": module.params["dynamic_mapping_portforward"],
            "portmapping-type": module.params["dynamic_mapping_portmapping_type"],
            "protocol": module.params["dynamic_mapping_protocol"],
            "server-type": module.params["dynamic_mapping_server_type"],
            "service": module.params["dynamic_mapping_service"],
            "src-filter": module.params["dynamic_mapping_src_filter"],
            "srcintf-filter": module.params["dynamic_mapping_srcintf_filter"],
            "ssl-algorithm": module.params["dynamic_mapping_ssl_algorithm"],
            "ssl-certificate": module.params["dynamic_mapping_ssl_certificate"],
            "ssl-client-fallback": module.params["dynamic_mapping_ssl_client_fallback"],
            "ssl-client-renegotiation": module.params["dynamic_mapping_ssl_client_renegotiation"],
            "ssl-client-session-state-max": module.params["dynamic_mapping_ssl_client_session_state_max"],
            "ssl-client-session-state-timeout": module.params["dynamic_mapping_ssl_client_session_state_timeout"],
            "ssl-client-session-state-type": module.params["dynamic_mapping_ssl_client_session_state_type"],
            "ssl-dh-bits": module.params["dynamic_mapping_ssl_dh_bits"],
            "ssl-hpkp": module.params["dynamic_mapping_ssl_hpkp"],
            "ssl-hpkp-age": module.params["dynamic_mapping_ssl_hpkp_age"],
            "ssl-hpkp-backup": module.params["dynamic_mapping_ssl_hpkp_backup"],
            "ssl-hpkp-include-subdomains": module.params["dynamic_mapping_ssl_hpkp_include_subdomains"],
            "ssl-hpkp-primary": module.params["dynamic_mapping_ssl_hpkp_primary"],
            "ssl-hpkp-report-uri": module.params["dynamic_mapping_ssl_hpkp_report_uri"],
            "ssl-hsts": module.params["dynamic_mapping_ssl_hsts"],
            "ssl-hsts-age": module.params["dynamic_mapping_ssl_hsts_age"],
            "ssl-hsts-include-subdomains": module.params["dynamic_mapping_ssl_hsts_include_subdomains"],
            "ssl-http-location-conversion": module.params["dynamic_mapping_ssl_http_location_conversion"],
            "ssl-http-match-host": module.params["dynamic_mapping_ssl_http_match_host"],
            "ssl-max-version": module.params["dynamic_mapping_ssl_max_version"],
            "ssl-min-version": module.params["dynamic_mapping_ssl_min_version"],
            "ssl-mode": module.params["dynamic_mapping_ssl_mode"],
            "ssl-pfs": module.params["dynamic_mapping_ssl_pfs"],
            "ssl-send-empty-frags": module.params["dynamic_mapping_ssl_send_empty_frags"],
            "ssl-server-algorithm": module.params["dynamic_mapping_ssl_server_algorithm"],
            "ssl-server-max-version": module.params["dynamic_mapping_ssl_server_max_version"],
            "ssl-server-min-version": module.params["dynamic_mapping_ssl_server_min_version"],
            "ssl-server-session-state-max": module.params["dynamic_mapping_ssl_server_session_state_max"],
            "ssl-server-session-state-timeout": module.params["dynamic_mapping_ssl_server_session_state_timeout"],
            "ssl-server-session-state-type": module.params["dynamic_mapping_ssl_server_session_state_type"],
            "type": module.params["dynamic_mapping_type"],
            "weblogic-server": module.params["dynamic_mapping_weblogic_server"],
            "websphere-server": module.params["dynamic_mapping_websphere_server"],
            "realservers": {
                "client-ip": module.params["dynamic_mapping_realservers_client_ip"],
                "healthcheck": module.params["dynamic_mapping_realservers_healthcheck"],
                "holddown-interval": module.params["dynamic_mapping_realservers_holddown_interval"],
                "http-host": module.params["dynamic_mapping_realservers_http_host"],
                "ip": module.params["dynamic_mapping_realservers_ip"],
                "max-connections": module.params["dynamic_mapping_realservers_max_connections"],
                "monitor": module.params["dynamic_mapping_realservers_monitor"],
                "port": module.params["dynamic_mapping_realservers_port"],
                "seq": module.params["dynamic_mapping_realservers_seq"],
                "status": module.params["dynamic_mapping_realservers_status"],
                "weight": module.params["dynamic_mapping_realservers_weight"],
            },
            "ssl-cipher-suites": {
                "cipher": module.params["dynamic_mapping_ssl_cipher_suites_cipher"],
                "versions": module.params["dynamic_mapping_ssl_cipher_suites_versions"],
            },
        },
        "realservers": {
            "client-ip": module.params["realservers_client_ip"],
            "healthcheck": module.params["realservers_healthcheck"],
            "holddown-interval": module.params["realservers_holddown_interval"],
            "http-host": module.params["realservers_http_host"],
            "ip": module.params["realservers_ip"],
            "max-connections": module.params["realservers_max_connections"],
            "monitor": module.params["realservers_monitor"],
            "port": module.params["realservers_port"],
            "seq": module.params["realservers_seq"],
            "status": module.params["realservers_status"],
            "weight": module.params["realservers_weight"],
        },
        "ssl-cipher-suites": {
            "cipher": module.params["ssl_cipher_suites_cipher"],
            "versions": module.params["ssl_cipher_suites_versions"],
        },
        "ssl-server-cipher-suites": {
            "cipher": module.params["ssl_server_cipher_suites_cipher"],
            "priority": module.params["ssl_server_cipher_suites_priority"],
            "versions": module.params["ssl_server_cipher_suites_versions"],
        }
    }
    module.paramgram = paramgram
    fmgr = None
    if module._socket_path:
        connection = Connection(module._socket_path)
        fmgr = FortiManagerHandler(connection, module)
        fmgr.tools = FMGRCommon()
    else:
        module.fail_json(**FAIL_SOCKET_MSG)

    list_overrides = ['dynamic_mapping', 'realservers', 'ssl-cipher-suites', 'ssl-server-cipher-suites']
    paramgram = fmgr.tools.paramgram_child_list_override(list_overrides=list_overrides,
                                                         paramgram=paramgram, module=module)

    results = DEFAULT_RESULT_OBJ
    try:
        results = fmgr_firewall_vip_modify(fmgr, paramgram)
        fmgr.govern_response(module=module, results=results,
                             ansible_facts=fmgr.construct_ansible_facts(results, module.params, paramgram))

    except Exception as err:
        raise FMGBaseException(err)

    return module.exit_json(**results[1])


if __name__ == "__main__":
    main()
