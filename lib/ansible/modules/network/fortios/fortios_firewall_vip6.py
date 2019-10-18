#!/usr/bin/python
from __future__ import (absolute_import, division, print_function)
# Copyright 2019 Fortinet, Inc.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

__metaclass__ = type

ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'metadata_version': '1.1'}

DOCUMENTATION = '''
---
module: fortios_firewall_vip6
short_description: Configure virtual IP for IPv6 in Fortinet's FortiOS and FortiGate.
description:
    - This module is able to configure a FortiGate or FortiOS (FOS) device by allowing the
      user to set and modify firewall feature and vip6 category.
      Examples include all parameters and values need to be adjusted to datasources before usage.
      Tested with FOS v6.0.5
version_added: "2.8"
author:
    - Miguel Angel Munoz (@mamunozgonzalez)
    - Nicolas Thomas (@thomnico)
notes:
    - Requires fortiosapi library developed by Fortinet
    - Run as a local_action in your playbook
requirements:
    - fortiosapi>=0.9.8
options:
    host:
        description:
            - FortiOS or FortiGate IP address.
        type: str
        required: false
    username:
        description:
            - FortiOS or FortiGate username.
        type: str
        required: false
    password:
        description:
            - FortiOS or FortiGate password.
        type: str
        default: ""
    vdom:
        description:
            - Virtual domain, among those defined previously. A vdom is a
              virtual instance of the FortiGate that can be configured and
              used as a different unit.
        type: str
        default: root
    https:
        description:
            - Indicates if the requests towards FortiGate must use HTTPS protocol.
        type: bool
        default: true
    ssl_verify:
        description:
            - Ensures FortiGate certificate must be verified by a proper CA.
        type: bool
        default: true
        version_added: 2.9
    state:
        description:
            - Indicates whether to create or remove the object.
              This attribute was present already in previous version in a deeper level.
              It has been moved out to this outer level.
        type: str
        required: false
        choices:
            - present
            - absent
        version_added: 2.9
    firewall_vip6:
        description:
            - Configure virtual IP for IPv6.
        default: null
        type: dict
        suboptions:
            state:
                description:
                    - B(Deprecated)
                    - Starting with Ansible 2.9 we recommend using the top-level 'state' parameter.
                    - HORIZONTALLINE
                    - Indicates whether to create or remove the object.
                type: str
                required: false
                choices:
                    - present
                    - absent
            arp_reply:
                description:
                    - Enable to respond to ARP requests for this virtual IP address. Enabled by default.
                type: str
                choices:
                    - disable
                    - enable
            color:
                description:
                    - Color of icon on the GUI.
                type: int
            comment:
                description:
                    - Comment.
                type: str
            extip:
                description:
                    - IP address or address range on the external interface that you want to map to an address or address range on the destination network.
                type: str
            extport:
                description:
                    - Incoming port number range that you want to map to a port number range on the destination network.
                type: str
            http_cookie_age:
                description:
                    - Time in minutes that client web browsers should keep a cookie. Default is 60 seconds. 0 = no time limit.
                type: int
            http_cookie_domain:
                description:
                    - Domain that HTTP cookie persistence should apply to.
                type: str
            http_cookie_domain_from_host:
                description:
                    - Enable/disable use of HTTP cookie domain from host field in HTTP.
                type: str
                choices:
                    - disable
                    - enable
            http_cookie_generation:
                description:
                    - Generation of HTTP cookie to be accepted. Changing invalidates all existing cookies.
                type: int
            http_cookie_path:
                description:
                    - Limit HTTP cookie persistence to the specified path.
                type: str
            http_cookie_share:
                description:
                    - Control sharing of cookies across virtual servers. same-ip means a cookie from one virtual server can be used by another. Disable stops
                       cookie sharing.
                type: str
                choices:
                    - disable
                    - same-ip
            http_ip_header:
                description:
                    - For HTTP multiplexing, enable to add the original client IP address in the XForwarded-For HTTP header.
                type: str
                choices:
                    - enable
                    - disable
            http_ip_header_name:
                description:
                    - For HTTP multiplexing, enter a custom HTTPS header name. The original client IP address is added to this header. If empty,
                       X-Forwarded-For is used.
                type: str
            http_multiplex:
                description:
                    - Enable/disable HTTP multiplexing.
                type: str
                choices:
                    - enable
                    - disable
            https_cookie_secure:
                description:
                    - Enable/disable verification that inserted HTTPS cookies are secure.
                type: str
                choices:
                    - disable
                    - enable
            id:
                description:
                    - Custom defined ID.
                type: int
            ldb_method:
                description:
                    - Method used to distribute sessions to real servers.
                type: str
                choices:
                    - static
                    - round-robin
                    - weighted
                    - least-session
                    - least-rtt
                    - first-alive
                    - http-host
            mappedip:
                description:
                    - Mapped IP address range in the format startIP-endIP.
                type: str
            mappedport:
                description:
                    - Port number range on the destination network to which the external port number range is mapped.
                type: str
            max_embryonic_connections:
                description:
                    - Maximum number of incomplete connections.
                type: int
            monitor:
                description:
                    - Name of the health check monitor to use when polling to determine a virtual server's connectivity status.
                type: list
                suboptions:
                    name:
                        description:
                            - Health monitor name. Source firewall.ldb-monitor.name.
                        required: true
                        type: str
            name:
                description:
                    - Virtual ip6 name.
                required: true
                type: str
            outlook_web_access:
                description:
                    - Enable to add the Front-End-Https header for Microsoft Outlook Web Access.
                type: str
                choices:
                    - disable
                    - enable
            persistence:
                description:
                    - Configure how to make sure that clients connect to the same server every time they make a request that is part of the same session.
                type: str
                choices:
                    - none
                    - http-cookie
                    - ssl-session-id
            portforward:
                description:
                    - Enable port forwarding.
                type: str
                choices:
                    - disable
                    - enable
            protocol:
                description:
                    - Protocol to use when forwarding packets.
                type: str
                choices:
                    - tcp
                    - udp
                    - sctp
            realservers:
                description:
                    - Select the real servers that this server load balancing VIP will distribute traffic to.
                type: list
                suboptions:
                    client_ip:
                        description:
                            - Only clients in this IP range can connect to this real server.
                        type: str
                    healthcheck:
                        description:
                            - Enable to check the responsiveness of the real server before forwarding traffic.
                        type: str
                        choices:
                            - disable
                            - enable
                            - vip
                    holddown_interval:
                        description:
                            - Time in seconds that the health check monitor continues to monitor an unresponsive server that should be active.
                        type: int
                    http_host:
                        description:
                            - HTTP server domain name in HTTP header.
                        type: str
                    id:
                        description:
                            - Real server ID.
                        required: true
                        type: int
                    ip:
                        description:
                            - IPv6 address of the real server.
                        type: str
                    max_connections:
                        description:
                            - Max number of active connections that can directed to the real server. When reached, sessions are sent to other real servers.
                        type: int
                    monitor:
                        description:
                            - Name of the health check monitor to use when polling to determine a virtual server's connectivity status. Source firewall
                              .ldb-monitor.name.
                        type: str
                    port:
                        description:
                            - Port for communicating with the real server. Required if port forwarding is enabled.
                        type: int
                    status:
                        description:
                            - Set the status of the real server to active so that it can accept traffic, or on standby or disabled so no traffic is sent.
                        type: str
                        choices:
                            - active
                            - standby
                            - disable
                    weight:
                        description:
                            - Weight of the real server. If weighted load balancing is enabled, the server with the highest weight gets more connections.
                        type: int
            server_type:
                description:
                    - Protocol to be load balanced by the virtual server (also called the server load balance virtual IP).
                type: str
                choices:
                    - http
                    - https
                    - imaps
                    - pop3s
                    - smtps
                    - ssl
                    - tcp
                    - udp
                    - ip
            src_filter:
                description:
                    - "Source IP6 filter (x:x:x:x:x:x:x:x/x). Separate addresses with spaces."
                type: list
                suboptions:
                    range:
                        description:
                            - Source-filter range.
                        required: true
                        type: str
            ssl_algorithm:
                description:
                    - Permitted encryption algorithms for SSL sessions according to encryption strength.
                type: str
                choices:
                    - high
                    - medium
                    - low
                    - custom
            ssl_certificate:
                description:
                    - The name of the SSL certificate to use for SSL acceleration. Source vpn.certificate.local.name.
                type: str
            ssl_cipher_suites:
                description:
                    - SSL/TLS cipher suites acceptable from a client, ordered by priority.
                type: list
                suboptions:
                    cipher:
                        description:
                            - Cipher suite name.
                        type: str
                        choices:
                            - TLS-RSA-WITH-3DES-EDE-CBC-SHA
                            - TLS-DHE-RSA-WITH-DES-CBC-SHA
                            - TLS-DHE-DSS-WITH-DES-CBC-SHA
                    priority:
                        description:
                            - SSL/TLS cipher suites priority.
                        required: true
                        type: int
                    versions:
                        description:
                            - SSL/TLS versions that the cipher suite can be used with.
                        type: str
                        choices:
                            - ssl-3.0
                            - tls-1.0
                            - tls-1.1
                            - tls-1.2
            ssl_client_fallback:
                description:
                    - Enable/disable support for preventing Downgrade Attacks on client connections (RFC 7507).
                type: str
                choices:
                    - disable
                    - enable
            ssl_client_renegotiation:
                description:
                    - Allow, deny, or require secure renegotiation of client sessions to comply with RFC 5746.
                type: str
                choices:
                    - allow
                    - deny
                    - secure
            ssl_client_session_state_max:
                description:
                    - Maximum number of client to FortiGate SSL session states to keep.
                type: int
            ssl_client_session_state_timeout:
                description:
                    - Number of minutes to keep client to FortiGate SSL session state.
                type: int
            ssl_client_session_state_type:
                description:
                    - How to expire SSL sessions for the segment of the SSL connection between the client and the FortiGate.
                type: str
                choices:
                    - disable
                    - time
                    - count
                    - both
            ssl_dh_bits:
                description:
                    - Number of bits to use in the Diffie-Hellman exchange for RSA encryption of SSL sessions.
                type: str
                choices:
                    - 768
                    - 1024
                    - 1536
                    - 2048
                    - 3072
                    - 4096
            ssl_hpkp:
                description:
                    - Enable/disable including HPKP header in response.
                type: str
                choices:
                    - disable
                    - enable
                    - report-only
            ssl_hpkp_age:
                description:
                    - Number of minutes the web browser should keep HPKP.
                type: int
            ssl_hpkp_backup:
                description:
                    - Certificate to generate backup HPKP pin from. Source vpn.certificate.local.name vpn.certificate.ca.name.
                type: str
            ssl_hpkp_include_subdomains:
                description:
                    - Indicate that HPKP header applies to all subdomains.
                type: str
                choices:
                    - disable
                    - enable
            ssl_hpkp_primary:
                description:
                    - Certificate to generate primary HPKP pin from. Source vpn.certificate.local.name vpn.certificate.ca.name.
                type: str
            ssl_hpkp_report_uri:
                description:
                    - URL to report HPKP violations to.
                type: str
            ssl_hsts:
                description:
                    - Enable/disable including HSTS header in response.
                type: str
                choices:
                    - disable
                    - enable
            ssl_hsts_age:
                description:
                    - Number of seconds the client should honour the HSTS setting.
                type: int
            ssl_hsts_include_subdomains:
                description:
                    - Indicate that HSTS header applies to all subdomains.
                type: str
                choices:
                    - disable
                    - enable
            ssl_http_location_conversion:
                description:
                    - Enable to replace HTTP with HTTPS in the reply's Location HTTP header field.
                type: str
                choices:
                    - enable
                    - disable
            ssl_http_match_host:
                description:
                    - Enable/disable HTTP host matching for location conversion.
                type: str
                choices:
                    - enable
                    - disable
            ssl_max_version:
                description:
                    - Highest SSL/TLS version acceptable from a client.
                type: str
                choices:
                    - ssl-3.0
                    - tls-1.0
                    - tls-1.1
                    - tls-1.2
            ssl_min_version:
                description:
                    - Lowest SSL/TLS version acceptable from a client.
                type: str
                choices:
                    - ssl-3.0
                    - tls-1.0
                    - tls-1.1
                    - tls-1.2
            ssl_mode:
                description:
                    - Apply SSL offloading between the client and the FortiGate (half) or from the client to the FortiGate and from the FortiGate to the
                       server (full).
                type: str
                choices:
                    - half
                    - full
            ssl_pfs:
                description:
                    - Select the cipher suites that can be used for SSL perfect forward secrecy (PFS). Applies to both client and server sessions.
                type: str
                choices:
                    - require
                    - deny
                    - allow
            ssl_send_empty_frags:
                description:
                    - Enable/disable sending empty fragments to avoid CBC IV attacks (SSL 3.0 & TLS 1.0 only). May need to be disabled for compatibility with
                       older systems.
                type: str
                choices:
                    - enable
                    - disable
            ssl_server_algorithm:
                description:
                    - Permitted encryption algorithms for the server side of SSL full mode sessions according to encryption strength.
                type: str
                choices:
                    - high
                    - medium
                    - low
                    - custom
                    - client
            ssl_server_cipher_suites:
                description:
                    - SSL/TLS cipher suites to offer to a server, ordered by priority.
                type: list
                suboptions:
                    cipher:
                        description:
                            - Cipher suite name.
                        type: str
                        choices:
                            - TLS-RSA-WITH-3DES-EDE-CBC-SHA
                            - TLS-DHE-RSA-WITH-DES-CBC-SHA
                            - TLS-DHE-DSS-WITH-DES-CBC-SHA
                    priority:
                        description:
                            - SSL/TLS cipher suites priority.
                        required: true
                        type: int
                    versions:
                        description:
                            - SSL/TLS versions that the cipher suite can be used with.
                        type: str
                        choices:
                            - ssl-3.0
                            - tls-1.0
                            - tls-1.1
                            - tls-1.2
            ssl_server_max_version:
                description:
                    - Highest SSL/TLS version acceptable from a server. Use the client setting by default.
                type: str
                choices:
                    - ssl-3.0
                    - tls-1.0
                    - tls-1.1
                    - tls-1.2
                    - client
            ssl_server_min_version:
                description:
                    - Lowest SSL/TLS version acceptable from a server. Use the client setting by default.
                type: str
                choices:
                    - ssl-3.0
                    - tls-1.0
                    - tls-1.1
                    - tls-1.2
                    - client
            ssl_server_session_state_max:
                description:
                    - Maximum number of FortiGate to Server SSL session states to keep.
                type: int
            ssl_server_session_state_timeout:
                description:
                    - Number of minutes to keep FortiGate to Server SSL session state.
                type: int
            ssl_server_session_state_type:
                description:
                    - How to expire SSL sessions for the segment of the SSL connection between the server and the FortiGate.
                type: str
                choices:
                    - disable
                    - time
                    - count
                    - both
            type:
                description:
                    - Configure a static NAT or server load balance VIP.
                type: str
                choices:
                    - static-nat
                    - server-load-balance
            uuid:
                description:
                    - Universally Unique Identifier (UUID; automatically assigned but can be manually reset).
                type: str
            weblogic_server:
                description:
                    - Enable to add an HTTP header to indicate SSL offloading for a WebLogic server.
                type: str
                choices:
                    - disable
                    - enable
            websphere_server:
                description:
                    - Enable to add an HTTP header to indicate SSL offloading for a WebSphere server.
                type: str
                choices:
                    - disable
                    - enable
'''

EXAMPLES = '''
- hosts: localhost
  vars:
   host: "192.168.122.40"
   username: "admin"
   password: ""
   vdom: "root"
   ssl_verify: "False"
  tasks:
  - name: Configure virtual IP for IPv6.
    fortios_firewall_vip6:
      host:  "{{ host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{ vdom }}"
      https: "False"
      state: "present"
      firewall_vip6:
        arp_reply: "disable"
        color: "4"
        comment: "Comment."
        extip: "<your_own_value>"
        extport: "<your_own_value>"
        http_cookie_age: "8"
        http_cookie_domain: "<your_own_value>"
        http_cookie_domain_from_host: "disable"
        http_cookie_generation: "11"
        http_cookie_path: "<your_own_value>"
        http_cookie_share: "disable"
        http_ip_header: "enable"
        http_ip_header_name: "<your_own_value>"
        http_multiplex: "enable"
        https_cookie_secure: "disable"
        id:  "18"
        ldb_method: "static"
        mappedip: "<your_own_value>"
        mappedport: "<your_own_value>"
        max_embryonic_connections: "22"
        monitor:
         -
            name: "default_name_24 (source firewall.ldb-monitor.name)"
        name: "default_name_25"
        outlook_web_access: "disable"
        persistence: "none"
        portforward: "disable"
        protocol: "tcp"
        realservers:
         -
            client_ip: "<your_own_value>"
            healthcheck: "disable"
            holddown_interval: "33"
            http_host: "myhostname"
            id:  "35"
            ip: "<your_own_value>"
            max_connections: "37"
            monitor: "<your_own_value> (source firewall.ldb-monitor.name)"
            port: "39"
            status: "active"
            weight: "41"
        server_type: "http"
        src_filter:
         -
            range: "<your_own_value>"
        ssl_algorithm: "high"
        ssl_certificate: "<your_own_value> (source vpn.certificate.local.name)"
        ssl_cipher_suites:
         -
            cipher: "TLS-RSA-WITH-3DES-EDE-CBC-SHA"
            priority: "49"
            versions: "ssl-3.0"
        ssl_client_fallback: "disable"
        ssl_client_renegotiation: "allow"
        ssl_client_session_state_max: "53"
        ssl_client_session_state_timeout: "54"
        ssl_client_session_state_type: "disable"
        ssl_dh_bits: "768"
        ssl_hpkp: "disable"
        ssl_hpkp_age: "58"
        ssl_hpkp_backup: "<your_own_value> (source vpn.certificate.local.name vpn.certificate.ca.name)"
        ssl_hpkp_include_subdomains: "disable"
        ssl_hpkp_primary: "<your_own_value> (source vpn.certificate.local.name vpn.certificate.ca.name)"
        ssl_hpkp_report_uri: "<your_own_value>"
        ssl_hsts: "disable"
        ssl_hsts_age: "64"
        ssl_hsts_include_subdomains: "disable"
        ssl_http_location_conversion: "enable"
        ssl_http_match_host: "enable"
        ssl_max_version: "ssl-3.0"
        ssl_min_version: "ssl-3.0"
        ssl_mode: "half"
        ssl_pfs: "require"
        ssl_send_empty_frags: "enable"
        ssl_server_algorithm: "high"
        ssl_server_cipher_suites:
         -
            cipher: "TLS-RSA-WITH-3DES-EDE-CBC-SHA"
            priority: "76"
            versions: "ssl-3.0"
        ssl_server_max_version: "ssl-3.0"
        ssl_server_min_version: "ssl-3.0"
        ssl_server_session_state_max: "80"
        ssl_server_session_state_timeout: "81"
        ssl_server_session_state_type: "disable"
        type: "static-nat"
        uuid: "<your_own_value>"
        weblogic_server: "disable"
        websphere_server: "disable"
'''

RETURN = '''
build:
  description: Build number of the fortigate image
  returned: always
  type: str
  sample: '1547'
http_method:
  description: Last method used to provision the content into FortiGate
  returned: always
  type: str
  sample: 'PUT'
http_status:
  description: Last result given by FortiGate on last operation applied
  returned: always
  type: str
  sample: "200"
mkey:
  description: Master key (id) used in the last call to FortiGate
  returned: success
  type: str
  sample: "id"
name:
  description: Name of the table used to fulfill the request
  returned: always
  type: str
  sample: "urlfilter"
path:
  description: Path of the table used to fulfill the request
  returned: always
  type: str
  sample: "webfilter"
revision:
  description: Internal revision number
  returned: always
  type: str
  sample: "17.0.2.10658"
serial:
  description: Serial number of the unit
  returned: always
  type: str
  sample: "FGVMEVYYQT3AB5352"
status:
  description: Indication of the operation's result
  returned: always
  type: str
  sample: "success"
vdom:
  description: Virtual domain used
  returned: always
  type: str
  sample: "root"
version:
  description: Version of the FortiGate
  returned: always
  type: str
  sample: "v5.6.3"

'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.connection import Connection
from ansible.module_utils.network.fortios.fortios import FortiOSHandler
from ansible.module_utils.network.fortimanager.common import FAIL_SOCKET_MSG


def login(data, fos):
    host = data['host']
    username = data['username']
    password = data['password']
    ssl_verify = data['ssl_verify']

    fos.debug('on')
    if 'https' in data and not data['https']:
        fos.https('off')
    else:
        fos.https('on')

    fos.login(host, username, password, verify=ssl_verify)


def filter_firewall_vip6_data(json):
    option_list = ['arp_reply', 'color', 'comment',
                   'extip', 'extport', 'http_cookie_age',
                   'http_cookie_domain', 'http_cookie_domain_from_host', 'http_cookie_generation',
                   'http_cookie_path', 'http_cookie_share', 'http_ip_header',
                   'http_ip_header_name', 'http_multiplex', 'https_cookie_secure',
                   'id', 'ldb_method', 'mappedip',
                   'mappedport', 'max_embryonic_connections', 'monitor',
                   'name', 'outlook_web_access', 'persistence',
                   'portforward', 'protocol', 'realservers',
                   'server_type', 'src_filter', 'ssl_algorithm',
                   'ssl_certificate', 'ssl_cipher_suites', 'ssl_client_fallback',
                   'ssl_client_renegotiation', 'ssl_client_session_state_max', 'ssl_client_session_state_timeout',
                   'ssl_client_session_state_type', 'ssl_dh_bits', 'ssl_hpkp',
                   'ssl_hpkp_age', 'ssl_hpkp_backup', 'ssl_hpkp_include_subdomains',
                   'ssl_hpkp_primary', 'ssl_hpkp_report_uri', 'ssl_hsts',
                   'ssl_hsts_age', 'ssl_hsts_include_subdomains', 'ssl_http_location_conversion',
                   'ssl_http_match_host', 'ssl_max_version', 'ssl_min_version',
                   'ssl_mode', 'ssl_pfs', 'ssl_send_empty_frags',
                   'ssl_server_algorithm', 'ssl_server_cipher_suites', 'ssl_server_max_version',
                   'ssl_server_min_version', 'ssl_server_session_state_max', 'ssl_server_session_state_timeout',
                   'ssl_server_session_state_type', 'type', 'uuid',
                   'weblogic_server', 'websphere_server']
    dictionary = {}

    for attribute in option_list:
        if attribute in json and json[attribute] is not None:
            dictionary[attribute] = json[attribute]

    return dictionary


def underscore_to_hyphen(data):
    if isinstance(data, list):
        for elem in data:
            elem = underscore_to_hyphen(elem)
    elif isinstance(data, dict):
        new_data = {}
        for k, v in data.items():
            new_data[k.replace('_', '-')] = underscore_to_hyphen(v)
        data = new_data

    return data


def firewall_vip6(data, fos):
    vdom = data['vdom']
    if 'state' in data and data['state']:
        state = data['state']
    elif 'state' in data['firewall_vip6'] and data['firewall_vip6']:
        state = data['firewall_vip6']['state']
    else:
        state = True
    firewall_vip6_data = data['firewall_vip6']
    filtered_data = underscore_to_hyphen(filter_firewall_vip6_data(firewall_vip6_data))

    if state == "present":
        return fos.set('firewall',
                       'vip6',
                       data=filtered_data,
                       vdom=vdom)

    elif state == "absent":
        return fos.delete('firewall',
                          'vip6',
                          mkey=filtered_data['name'],
                          vdom=vdom)


def is_successful_status(status):
    return status['status'] == "success" or \
        status['http_method'] == "DELETE" and status['http_status'] == 404


def fortios_firewall(data, fos):

    if data['firewall_vip6']:
        resp = firewall_vip6(data, fos)

    return not is_successful_status(resp), \
        resp['status'] == "success", \
        resp


def main():
    fields = {
        "host": {"required": False, "type": "str"},
        "username": {"required": False, "type": "str"},
        "password": {"required": False, "type": "str", "default": "", "no_log": True},
        "vdom": {"required": False, "type": "str", "default": "root"},
        "https": {"required": False, "type": "bool", "default": True},
        "ssl_verify": {"required": False, "type": "bool", "default": True},
        "state": {"required": False, "type": "str",
                  "choices": ["present", "absent"]},
        "firewall_vip6": {
            "required": False, "type": "dict", "default": None,
            "options": {
                "state": {"required": False, "type": "str",
                          "choices": ["present", "absent"]},
                "arp_reply": {"required": False, "type": "str",
                              "choices": ["disable", "enable"]},
                "color": {"required": False, "type": "int"},
                "comment": {"required": False, "type": "str"},
                "extip": {"required": False, "type": "str"},
                "extport": {"required": False, "type": "str"},
                "http_cookie_age": {"required": False, "type": "int"},
                "http_cookie_domain": {"required": False, "type": "str"},
                "http_cookie_domain_from_host": {"required": False, "type": "str",
                                                 "choices": ["disable", "enable"]},
                "http_cookie_generation": {"required": False, "type": "int"},
                "http_cookie_path": {"required": False, "type": "str"},
                "http_cookie_share": {"required": False, "type": "str",
                                      "choices": ["disable", "same-ip"]},
                "http_ip_header": {"required": False, "type": "str",
                                   "choices": ["enable", "disable"]},
                "http_ip_header_name": {"required": False, "type": "str"},
                "http_multiplex": {"required": False, "type": "str",
                                   "choices": ["enable", "disable"]},
                "https_cookie_secure": {"required": False, "type": "str",
                                        "choices": ["disable", "enable"]},
                "id": {"required": False, "type": "int"},
                "ldb_method": {"required": False, "type": "str",
                               "choices": ["static", "round-robin", "weighted",
                                           "least-session", "least-rtt", "first-alive",
                                           "http-host"]},
                "mappedip": {"required": False, "type": "str"},
                "mappedport": {"required": False, "type": "str"},
                "max_embryonic_connections": {"required": False, "type": "int"},
                "monitor": {"required": False, "type": "list",
                            "options": {
                                "name": {"required": True, "type": "str"}
                            }},
                "name": {"required": True, "type": "str"},
                "outlook_web_access": {"required": False, "type": "str",
                                       "choices": ["disable", "enable"]},
                "persistence": {"required": False, "type": "str",
                                "choices": ["none", "http-cookie", "ssl-session-id"]},
                "portforward": {"required": False, "type": "str",
                                "choices": ["disable", "enable"]},
                "protocol": {"required": False, "type": "str",
                             "choices": ["tcp", "udp", "sctp"]},
                "realservers": {"required": False, "type": "list",
                                "options": {
                                    "client_ip": {"required": False, "type": "str"},
                                    "healthcheck": {"required": False, "type": "str",
                                                    "choices": ["disable", "enable", "vip"]},
                                    "holddown_interval": {"required": False, "type": "int"},
                                    "http_host": {"required": False, "type": "str"},
                                    "id": {"required": True, "type": "int"},
                                    "ip": {"required": False, "type": "str"},
                                    "max_connections": {"required": False, "type": "int"},
                                    "monitor": {"required": False, "type": "str"},
                                    "port": {"required": False, "type": "int"},
                                    "status": {"required": False, "type": "str",
                                               "choices": ["active", "standby", "disable"]},
                                    "weight": {"required": False, "type": "int"}
                                }},
                "server_type": {"required": False, "type": "str",
                                "choices": ["http", "https", "imaps",
                                            "pop3s", "smtps", "ssl",
                                            "tcp", "udp", "ip"]},
                "src_filter": {"required": False, "type": "list",
                               "options": {
                                   "range": {"required": True, "type": "str"}
                               }},
                "ssl_algorithm": {"required": False, "type": "str",
                                  "choices": ["high", "medium", "low",
                                              "custom"]},
                "ssl_certificate": {"required": False, "type": "str"},
                "ssl_cipher_suites": {"required": False, "type": "list",
                                      "options": {
                                          "cipher": {"required": False, "type": "str",
                                                     "choices": ["TLS-RSA-WITH-3DES-EDE-CBC-SHA", "TLS-DHE-RSA-WITH-DES-CBC-SHA",
                                                                 "TLS-DHE-DSS-WITH-DES-CBC-SHA"]},
                                          "priority": {"required": True, "type": "int"},
                                          "versions": {"required": False, "type": "str",
                                                       "choices": ["ssl-3.0", "tls-1.0", "tls-1.1",
                                                                   "tls-1.2"]}
                                      }},
                "ssl_client_fallback": {"required": False, "type": "str",
                                        "choices": ["disable", "enable"]},
                "ssl_client_renegotiation": {"required": False, "type": "str",
                                             "choices": ["allow", "deny", "secure"]},
                "ssl_client_session_state_max": {"required": False, "type": "int"},
                "ssl_client_session_state_timeout": {"required": False, "type": "int"},
                "ssl_client_session_state_type": {"required": False, "type": "str",
                                                  "choices": ["disable", "time", "count",
                                                              "both"]},
                "ssl_dh_bits": {"required": False, "type": "str",
                                "choices": ["768", "1024", "1536",
                                            "2048", "3072", "4096"]},
                "ssl_hpkp": {"required": False, "type": "str",
                             "choices": ["disable", "enable", "report-only"]},
                "ssl_hpkp_age": {"required": False, "type": "int"},
                "ssl_hpkp_backup": {"required": False, "type": "str"},
                "ssl_hpkp_include_subdomains": {"required": False, "type": "str",
                                                "choices": ["disable", "enable"]},
                "ssl_hpkp_primary": {"required": False, "type": "str"},
                "ssl_hpkp_report_uri": {"required": False, "type": "str"},
                "ssl_hsts": {"required": False, "type": "str",
                             "choices": ["disable", "enable"]},
                "ssl_hsts_age": {"required": False, "type": "int"},
                "ssl_hsts_include_subdomains": {"required": False, "type": "str",
                                                "choices": ["disable", "enable"]},
                "ssl_http_location_conversion": {"required": False, "type": "str",
                                                 "choices": ["enable", "disable"]},
                "ssl_http_match_host": {"required": False, "type": "str",
                                        "choices": ["enable", "disable"]},
                "ssl_max_version": {"required": False, "type": "str",
                                    "choices": ["ssl-3.0", "tls-1.0", "tls-1.1",
                                                "tls-1.2"]},
                "ssl_min_version": {"required": False, "type": "str",
                                    "choices": ["ssl-3.0", "tls-1.0", "tls-1.1",
                                                "tls-1.2"]},
                "ssl_mode": {"required": False, "type": "str",
                             "choices": ["half", "full"]},
                "ssl_pfs": {"required": False, "type": "str",
                            "choices": ["require", "deny", "allow"]},
                "ssl_send_empty_frags": {"required": False, "type": "str",
                                         "choices": ["enable", "disable"]},
                "ssl_server_algorithm": {"required": False, "type": "str",
                                         "choices": ["high", "medium", "low",
                                                     "custom", "client"]},
                "ssl_server_cipher_suites": {"required": False, "type": "list",
                                             "options": {
                                                 "cipher": {"required": False, "type": "str",
                                                            "choices": ["TLS-RSA-WITH-3DES-EDE-CBC-SHA", "TLS-DHE-RSA-WITH-DES-CBC-SHA",
                                                                        "TLS-DHE-DSS-WITH-DES-CBC-SHA"]},
                                                 "priority": {"required": True, "type": "int"},
                                                 "versions": {"required": False, "type": "str",
                                                              "choices": ["ssl-3.0", "tls-1.0", "tls-1.1",
                                                                          "tls-1.2"]}
                                             }},
                "ssl_server_max_version": {"required": False, "type": "str",
                                           "choices": ["ssl-3.0", "tls-1.0", "tls-1.1",
                                                       "tls-1.2", "client"]},
                "ssl_server_min_version": {"required": False, "type": "str",
                                           "choices": ["ssl-3.0", "tls-1.0", "tls-1.1",
                                                       "tls-1.2", "client"]},
                "ssl_server_session_state_max": {"required": False, "type": "int"},
                "ssl_server_session_state_timeout": {"required": False, "type": "int"},
                "ssl_server_session_state_type": {"required": False, "type": "str",
                                                  "choices": ["disable", "time", "count",
                                                              "both"]},
                "type": {"required": False, "type": "str",
                         "choices": ["static-nat", "server-load-balance"]},
                "uuid": {"required": False, "type": "str"},
                "weblogic_server": {"required": False, "type": "str",
                                    "choices": ["disable", "enable"]},
                "websphere_server": {"required": False, "type": "str",
                                     "choices": ["disable", "enable"]}

            }
        }
    }

    module = AnsibleModule(argument_spec=fields,
                           supports_check_mode=False)

    # legacy_mode refers to using fortiosapi instead of HTTPAPI
    legacy_mode = 'host' in module.params and module.params['host'] is not None and \
                  'username' in module.params and module.params['username'] is not None and \
                  'password' in module.params and module.params['password'] is not None

    if not legacy_mode:
        if module._socket_path:
            connection = Connection(module._socket_path)
            fos = FortiOSHandler(connection)

            is_error, has_changed, result = fortios_firewall(module.params, fos)
        else:
            module.fail_json(**FAIL_SOCKET_MSG)
    else:
        try:
            from fortiosapi import FortiOSAPI
        except ImportError:
            module.fail_json(msg="fortiosapi module is required")

        fos = FortiOSAPI()

        login(module.params, fos)
        is_error, has_changed, result = fortios_firewall(module.params, fos)
        fos.logout()

    if not is_error:
        module.exit_json(changed=has_changed, meta=result)
    else:
        module.fail_json(msg="Error in repo", meta=result)


if __name__ == '__main__':
    main()
