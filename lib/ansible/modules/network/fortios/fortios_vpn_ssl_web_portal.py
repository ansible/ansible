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
#
# the lib use python logging can get it if the following is set in your
# Ansible config.

__metaclass__ = type

ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'metadata_version': '1.1'}

DOCUMENTATION = '''
---
module: fortios_vpn_ssl_web_portal
short_description: Portal in Fortinet's FortiOS and FortiGate.
description:
    - This module is able to configure a FortiGate or FortiOS by allowing the
      user to set and modify vpn_ssl_web feature and portal category.
      Examples include all parameters and values need to be adjusted to datasources before usage.
      Tested with FOS v6.0.2
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
            - FortiOS or FortiGate ip address.
       required: true
    username:
        description:
            - FortiOS or FortiGate username.
        required: true
    password:
        description:
            - FortiOS or FortiGate password.
        default: ""
    vdom:
        description:
            - Virtual domain, among those defined previously. A vdom is a
              virtual instance of the FortiGate that can be configured and
              used as a different unit.
        default: root
    https:
        description:
            - Indicates if the requests towards FortiGate must use HTTPS
              protocol
        type: bool
        default: true
    vpn_ssl_web_portal:
        description:
            - Portal.
        default: null
        suboptions:
            state:
                description:
                    - Indicates whether to create or remove the object
                choices:
                    - present
                    - absent
            allow-user-access:
                description:
                    - Allow user access to SSL-VPN applications.
                choices:
                    - web
                    - ftp
                    - smb
                    - telnet
                    - ssh
                    - vnc
                    - rdp
                    - ping
                    - citrix
                    - portforward
            auto-connect:
                description:
                    - Enable/disable automatic connect by client when system is up.
                choices:
                    - enable
                    - disable
            bookmark-group:
                description:
                    - Portal bookmark group.
                suboptions:
                    bookmarks:
                        description:
                            - Bookmark table.
                        suboptions:
                            additional-params:
                                description:
                                    - Additional parameters.
                            apptype:
                                description:
                                    - Application type.
                                choices:
                                    - citrix
                                    - ftp
                                    - portforward
                                    - rdp
                                    - smb
                                    - ssh
                                    - telnet
                                    - vnc
                                    - web
                            description:
                                description:
                                    - Description.
                            folder:
                                description:
                                    - Network shared file folder parameter.
                            form-data:
                                description:
                                    - Form data.
                                suboptions:
                                    name:
                                        description:
                                            - Name.
                                        required: true
                                    value:
                                        description:
                                            - Value.
                            host:
                                description:
                                    - Host name/IP parameter.
                            listening-port:
                                description:
                                    - Listening port (0 - 65535).
                            load-balancing-info:
                                description:
                                    - The load balancing information or cookie which should be provided to the connection broker.
                            logon-password:
                                description:
                                    - Logon password.
                            logon-user:
                                description:
                                    - Logon user.
                            name:
                                description:
                                    - Bookmark name.
                                required: true
                            port:
                                description:
                                    - Remote port.
                            preconnection-blob:
                                description:
                                    - An arbitrary string which identifies the RDP source.
                            preconnection-id:
                                description:
                                    - The numeric ID of the RDP source (0-2147483648).
                            remote-port:
                                description:
                                    - Remote port (0 - 65535).
                            security:
                                description:
                                    - Security mode for RDP connection.
                                choices:
                                    - rdp
                                    - nla
                                    - tls
                                    - any
                            server-layout:
                                description:
                                    - Server side keyboard layout.
                                choices:
                                    - de-de-qwertz
                                    - en-gb-qwerty
                                    - en-us-qwerty
                                    - es-es-qwerty
                                    - fr-fr-azerty
                                    - fr-ch-qwertz
                                    - it-it-qwerty
                                    - ja-jp-qwerty
                                    - pt-br-qwerty
                                    - sv-se-qwerty
                                    - tr-tr-qwerty
                                    - failsafe
                            show-status-window:
                                description:
                                    - Enable/disable showing of status window.
                                choices:
                                    - enable
                                    - disable
                            sso:
                                description:
                                    - Single Sign-On.
                                choices:
                                    - disable
                                    - static
                                    - auto
                            sso-credential:
                                description:
                                    - Single sign-on credentials.
                                choices:
                                    - sslvpn-login
                                    - alternative
                            sso-credential-sent-once:
                                description:
                                    - Single sign-on credentials are only sent once to remote server.
                                choices:
                                    - enable
                                    - disable
                            sso-password:
                                description:
                                    - SSO password.
                            sso-username:
                                description:
                                    - SSO user name.
                            url:
                                description:
                                    - URL parameter.
                    name:
                        description:
                            - Bookmark group name.
                        required: true
            custom-lang:
                description:
                    - Change the web portal display language. Overrides config system global set language. You can use config system custom-language and
                       execute system custom-language to add custom language files. Source system.custom-language.name.
            customize-forticlient-download-url:
                description:
                    - Enable support of customized download URL for FortiClient.
                choices:
                    - enable
                    - disable
            display-bookmark:
                description:
                    - Enable to display the web portal bookmark widget.
                choices:
                    - enable
                    - disable
            display-connection-tools:
                description:
                    - Enable to display the web portal connection tools widget.
                choices:
                    - enable
                    - disable
            display-history:
                description:
                    - Enable to display the web portal user login history widget.
                choices:
                    - enable
                    - disable
            display-status:
                description:
                    - Enable to display the web portal status widget.
                choices:
                    - enable
                    - disable
            dns-server1:
                description:
                    - IPv4 DNS server 1.
            dns-server2:
                description:
                    - IPv4 DNS server 2.
            dns-suffix:
                description:
                    - DNS suffix.
            exclusive-routing:
                description:
                    - Enable/disable all traffic go through tunnel only.
                choices:
                    - enable
                    - disable
            forticlient-download:
                description:
                    - Enable/disable download option for FortiClient.
                choices:
                    - enable
                    - disable
            forticlient-download-method:
                description:
                    - FortiClient download method.
                choices:
                    - direct
                    - ssl-vpn
            heading:
                description:
                    - Web portal heading message.
            hide-sso-credential:
                description:
                    - Enable to prevent SSO credential being sent to client.
                choices:
                    - enable
                    - disable
            host-check:
                description:
                    - Type of host checking performed on endpoints.
                choices:
                    - none
                    - av
                    - fw
                    - av-fw
                    - custom
            host-check-interval:
                description:
                    - Periodic host check interval. Value of 0 means disabled and host checking only happens when the endpoint connects.
            host-check-policy:
                description:
                    - One or more policies to require the endpoint to have specific security software.
                suboptions:
                    name:
                        description:
                            - Host check software list name. Source vpn.ssl.web.host-check-software.name.
                        required: true
            ip-mode:
                description:
                    - Method by which users of this SSL-VPN tunnel obtain IP addresses.
                choices:
                    - range
                    - user-group
            ip-pools:
                description:
                    - IPv4 firewall source address objects reserved for SSL-VPN tunnel mode clients.
                suboptions:
                    name:
                        description:
                            - Address name. Source firewall.address.name firewall.addrgrp.name.
                        required: true
            ipv6-dns-server1:
                description:
                    - IPv6 DNS server 1.
            ipv6-dns-server2:
                description:
                    - IPv6 DNS server 2.
            ipv6-exclusive-routing:
                description:
                    - Enable/disable all IPv6 traffic go through tunnel only.
                choices:
                    - enable
                    - disable
            ipv6-pools:
                description:
                    - IPv4 firewall source address objects reserved for SSL-VPN tunnel mode clients.
                suboptions:
                    name:
                        description:
                            - Address name. Source firewall.address6.name firewall.addrgrp6.name.
                        required: true
            ipv6-service-restriction:
                description:
                    - Enable/disable IPv6 tunnel service restriction.
                choices:
                    - enable
                    - disable
            ipv6-split-tunneling:
                description:
                    - Enable/disable IPv6 split tunneling.
                choices:
                    - enable
                    - disable
            ipv6-split-tunneling-routing-address:
                description:
                    - IPv6 SSL-VPN tunnel mode firewall address objects that override firewall policy destination addresses to control split-tunneling access.
                suboptions:
                    name:
                        description:
                            - Address name. Source firewall.address6.name firewall.addrgrp6.name.
                        required: true
            ipv6-tunnel-mode:
                description:
                    - Enable/disable IPv6 SSL-VPN tunnel mode.
                choices:
                    - enable
                    - disable
            ipv6-wins-server1:
                description:
                    - IPv6 WINS server 1.
            ipv6-wins-server2:
                description:
                    - IPv6 WINS server 2.
            keep-alive:
                description:
                    - Enable/disable automatic reconnect for FortiClient connections.
                choices:
                    - enable
                    - disable
            limit-user-logins:
                description:
                    - Enable to limit each user to one SSL-VPN session at a time.
                choices:
                    - enable
                    - disable
            mac-addr-action:
                description:
                    - Client MAC address action.
                choices:
                    - allow
                    - deny
            mac-addr-check:
                description:
                    - Enable/disable MAC address host checking.
                choices:
                    - enable
                    - disable
            mac-addr-check-rule:
                description:
                    - Client MAC address check rule.
                suboptions:
                    mac-addr-list:
                        description:
                            - Client MAC address list.
                        suboptions:
                            addr:
                                description:
                                    - Client MAC address.
                                required: true
                    mac-addr-mask:
                        description:
                            - Client MAC address mask.
                    name:
                        description:
                            - Client MAC address check rule name.
                        required: true
            macos-forticlient-download-url:
                description:
                    - Download URL for Mac FortiClient.
            name:
                description:
                    - Portal name.
                required: true
            os-check:
                description:
                    - Enable to let the FortiGate decide action based on client OS.
                choices:
                    - enable
                    - disable
            os-check-list:
                description:
                    - SSL VPN OS checks.
                suboptions:
                    action:
                        description:
                            - OS check options.
                        choices:
                            - deny
                            - allow
                            - check-up-to-date
                    latest-patch-level:
                        description:
                            - Latest OS patch level.
                    name:
                        description:
                            - Name.
                        required: true
                    tolerance:
                        description:
                            - OS patch level tolerance.
            redir-url:
                description:
                    - Client login redirect URL.
            save-password:
                description:
                    - Enable/disable FortiClient saving the user's password.
                choices:
                    - enable
                    - disable
            service-restriction:
                description:
                    - Enable/disable tunnel service restriction.
                choices:
                    - enable
                    - disable
            skip-check-for-unsupported-browser:
                description:
                    - Enable to skip host check if browser does not support it.
                choices:
                    - enable
                    - disable
            skip-check-for-unsupported-os:
                description:
                    - Enable to skip host check if client OS does not support it.
                choices:
                    - enable
                    - disable
            smb-ntlmv1-auth:
                description:
                    - Enable support of NTLMv1 for Samba authentication.
                choices:
                    - enable
                    - disable
            smbv1:
                description:
                    - Enable/disable support of SMBv1 for Samba.
                choices:
                    - enable
                    - disable
            split-dns:
                description:
                    - Split DNS for SSL VPN.
                suboptions:
                    dns-server1:
                        description:
                            - DNS server 1.
                    dns-server2:
                        description:
                            - DNS server 2.
                    domains:
                        description:
                            - Split DNS domains used for SSL-VPN clients separated by comma(,).
                    id:
                        description:
                            - ID.
                        required: true
                    ipv6-dns-server1:
                        description:
                            - IPv6 DNS server 1.
                    ipv6-dns-server2:
                        description:
                            - IPv6 DNS server 2.
            split-tunneling:
                description:
                    - Enable/disable IPv4 split tunneling.
                choices:
                    - enable
                    - disable
            split-tunneling-routing-address:
                description:
                    - IPv4 SSL-VPN tunnel mode firewall address objects that override firewall policy destination addresses to control split-tunneling access.
                suboptions:
                    name:
                        description:
                            - Address name. Source firewall.address.name firewall.addrgrp.name.
                        required: true
            theme:
                description:
                    - Web portal color scheme.
                choices:
                    - blue
                    - green
                    - red
                    - melongene
                    - mariner
            tunnel-mode:
                description:
                    - Enable/disable IPv4 SSL-VPN tunnel mode.
                choices:
                    - enable
                    - disable
            user-bookmark:
                description:
                    - Enable to allow web portal users to create their own bookmarks.
                choices:
                    - enable
                    - disable
            user-group-bookmark:
                description:
                    - Enable to allow web portal users to create bookmarks for all users in the same user group.
                choices:
                    - enable
                    - disable
            web-mode:
                description:
                    - Enable/disable SSL VPN web mode.
                choices:
                    - enable
                    - disable
            windows-forticlient-download-url:
                description:
                    - Download URL for Windows FortiClient.
            wins-server1:
                description:
                    - IPv4 WINS server 1.
            wins-server2:
                description:
                    - IPv4 WINS server 1.
'''

EXAMPLES = '''
- hosts: localhost
  vars:
   host: "192.168.122.40"
   username: "admin"
   password: ""
   vdom: "root"
  tasks:
  - name: Portal.
    fortios_vpn_ssl_web_portal:
      host:  "{{ host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{ vdom }}"
      https: "False"
      vpn_ssl_web_portal:
        state: "present"
        allow-user-access: "web"
        auto-connect: "enable"
        bookmark-group:
         -
            bookmarks:
             -
                additional-params: "<your_own_value>"
                apptype: "citrix"
                description: "<your_own_value>"
                folder: "<your_own_value>"
                form-data:
                 -
                    name: "default_name_12"
                    value: "<your_own_value>"
                host: "<your_own_value>"
                listening-port: "15"
                load-balancing-info: "<your_own_value>"
                logon-password: "<your_own_value>"
                logon-user: "<your_own_value>"
                name: "default_name_19"
                port: "20"
                preconnection-blob: "<your_own_value>"
                preconnection-id: "22"
                remote-port: "23"
                security: "rdp"
                server-layout: "de-de-qwertz"
                show-status-window: "enable"
                sso: "disable"
                sso-credential: "sslvpn-login"
                sso-credential-sent-once: "enable"
                sso-password: "<your_own_value>"
                sso-username: "<your_own_value>"
                url: "myurl.com"
            name: "default_name_33"
        custom-lang: "<your_own_value> (source system.custom-language.name)"
        customize-forticlient-download-url: "enable"
        display-bookmark: "enable"
        display-connection-tools: "enable"
        display-history: "enable"
        display-status: "enable"
        dns-server1: "<your_own_value>"
        dns-server2: "<your_own_value>"
        dns-suffix: "<your_own_value>"
        exclusive-routing: "enable"
        forticlient-download: "enable"
        forticlient-download-method: "direct"
        heading: "<your_own_value>"
        hide-sso-credential: "enable"
        host-check: "none"
        host-check-interval: "49"
        host-check-policy:
         -
            name: "default_name_51 (source vpn.ssl.web.host-check-software.name)"
        ip-mode: "range"
        ip-pools:
         -
            name: "default_name_54 (source firewall.address.name firewall.addrgrp.name)"
        ipv6-dns-server1: "<your_own_value>"
        ipv6-dns-server2: "<your_own_value>"
        ipv6-exclusive-routing: "enable"
        ipv6-pools:
         -
            name: "default_name_59 (source firewall.address6.name firewall.addrgrp6.name)"
        ipv6-service-restriction: "enable"
        ipv6-split-tunneling: "enable"
        ipv6-split-tunneling-routing-address:
         -
            name: "default_name_63 (source firewall.address6.name firewall.addrgrp6.name)"
        ipv6-tunnel-mode: "enable"
        ipv6-wins-server1: "<your_own_value>"
        ipv6-wins-server2: "<your_own_value>"
        keep-alive: "enable"
        limit-user-logins: "enable"
        mac-addr-action: "allow"
        mac-addr-check: "enable"
        mac-addr-check-rule:
         -
            mac-addr-list:
             -
                addr: "<your_own_value>"
            mac-addr-mask: "74"
            name: "default_name_75"
        macos-forticlient-download-url: "<your_own_value>"
        name: "default_name_77"
        os-check: "enable"
        os-check-list:
         -
            action: "deny"
            latest-patch-level: "<your_own_value>"
            name: "default_name_82"
            tolerance: "83"
        redir-url: "<your_own_value>"
        save-password: "enable"
        service-restriction: "enable"
        skip-check-for-unsupported-browser: "enable"
        skip-check-for-unsupported-os: "enable"
        smb-ntlmv1-auth: "enable"
        smbv1: "enable"
        split-dns:
         -
            dns-server1: "<your_own_value>"
            dns-server2: "<your_own_value>"
            domains: "<your_own_value>"
            id:  "95"
            ipv6-dns-server1: "<your_own_value>"
            ipv6-dns-server2: "<your_own_value>"
        split-tunneling: "enable"
        split-tunneling-routing-address:
         -
            name: "default_name_100 (source firewall.address.name firewall.addrgrp.name)"
        theme: "blue"
        tunnel-mode: "enable"
        user-bookmark: "enable"
        user-group-bookmark: "enable"
        web-mode: "enable"
        windows-forticlient-download-url: "<your_own_value>"
        wins-server1: "<your_own_value>"
        wins-server2: "<your_own_value>"
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

fos = None


def login(data):
    host = data['host']
    username = data['username']
    password = data['password']

    fos.debug('on')
    if 'https' in data and not data['https']:
        fos.https('off')
    else:
        fos.https('on')

    fos.login(host, username, password)


def filter_vpn_ssl_web_portal_data(json):
    option_list = ['allow-user-access', 'auto-connect', 'bookmark-group',
                   'custom-lang', 'customize-forticlient-download-url', 'display-bookmark',
                   'display-connection-tools', 'display-history', 'display-status',
                   'dns-server1', 'dns-server2', 'dns-suffix',
                   'exclusive-routing', 'forticlient-download', 'forticlient-download-method',
                   'heading', 'hide-sso-credential', 'host-check',
                   'host-check-interval', 'host-check-policy', 'ip-mode',
                   'ip-pools', 'ipv6-dns-server1', 'ipv6-dns-server2',
                   'ipv6-exclusive-routing', 'ipv6-pools', 'ipv6-service-restriction',
                   'ipv6-split-tunneling', 'ipv6-split-tunneling-routing-address', 'ipv6-tunnel-mode',
                   'ipv6-wins-server1', 'ipv6-wins-server2', 'keep-alive',
                   'limit-user-logins', 'mac-addr-action', 'mac-addr-check',
                   'mac-addr-check-rule', 'macos-forticlient-download-url', 'name',
                   'os-check', 'os-check-list', 'redir-url',
                   'save-password', 'service-restriction', 'skip-check-for-unsupported-browser',
                   'skip-check-for-unsupported-os', 'smb-ntlmv1-auth', 'smbv1',
                   'split-dns', 'split-tunneling', 'split-tunneling-routing-address',
                   'theme', 'tunnel-mode', 'user-bookmark',
                   'user-group-bookmark', 'web-mode', 'windows-forticlient-download-url',
                   'wins-server1', 'wins-server2']
    dictionary = {}

    for attribute in option_list:
        if attribute in json and json[attribute] is not None:
            dictionary[attribute] = json[attribute]

    return dictionary


def flatten_multilists_attributes(data):
    multilist_attrs = []

    for attr in multilist_attrs:
        try:
            path = "data['" + "']['".join(elem for elem in attr) + "']"
            current_val = eval(path)
            flattened_val = ' '.join(elem for elem in current_val)
            exec(path + '= flattened_val')
        except BaseException:
            pass

    return data


def vpn_ssl_web_portal(data, fos):
    vdom = data['vdom']
    vpn_ssl_web_portal_data = data['vpn_ssl_web_portal']
    flattened_data = flatten_multilists_attributes(vpn_ssl_web_portal_data)
    filtered_data = filter_vpn_ssl_web_portal_data(flattened_data)
    if vpn_ssl_web_portal_data['state'] == "present":
        return fos.set('vpn.ssl.web',
                       'portal',
                       data=filtered_data,
                       vdom=vdom)

    elif vpn_ssl_web_portal_data['state'] == "absent":
        return fos.delete('vpn.ssl.web',
                          'portal',
                          mkey=filtered_data['name'],
                          vdom=vdom)


def fortios_vpn_ssl_web(data, fos):
    login(data)

    if data['vpn_ssl_web_portal']:
        resp = vpn_ssl_web_portal(data, fos)

    fos.logout()
    return not resp['status'] == "success", resp['status'] == "success", resp


def main():
    fields = {
        "host": {"required": True, "type": "str"},
        "username": {"required": True, "type": "str"},
        "password": {"required": False, "type": "str", "no_log": True},
        "vdom": {"required": False, "type": "str", "default": "root"},
        "https": {"required": False, "type": "bool", "default": True},
        "vpn_ssl_web_portal": {
            "required": False, "type": "dict",
            "options": {
                "state": {"required": True, "type": "str",
                          "choices": ["present", "absent"]},
                "allow-user-access": {"required": False, "type": "str",
                                      "choices": ["web", "ftp", "smb",
                                                  "telnet", "ssh", "vnc",
                                                  "rdp", "ping", "citrix",
                                                  "portforward"]},
                "auto-connect": {"required": False, "type": "str",
                                 "choices": ["enable", "disable"]},
                "bookmark-group": {"required": False, "type": "list",
                                   "options": {
                                       "bookmarks": {"required": False, "type": "list",
                                                     "options": {
                                                         "additional-params": {"required": False, "type": "str"},
                                                         "apptype": {"required": False, "type": "str",
                                                                     "choices": ["citrix", "ftp", "portforward",
                                                                                 "rdp", "smb", "ssh",
                                                                                 "telnet", "vnc", "web"]},
                                                         "description": {"required": False, "type": "str"},
                                                         "folder": {"required": False, "type": "str"},
                                                         "form-data": {"required": False, "type": "list",
                                                                       "options": {
                                                                           "name": {"required": True, "type": "str"},
                                                                           "value": {"required": False, "type": "str"}
                                                                       }},
                                                         "host": {"required": False, "type": "str"},
                                                         "listening-port": {"required": False, "type": "int"},
                                                         "load-balancing-info": {"required": False, "type": "str"},
                                                         "logon-password": {"required": False, "type": "str"},
                                                         "logon-user": {"required": False, "type": "str"},
                                                         "name": {"required": True, "type": "str"},
                                                         "port": {"required": False, "type": "int"},
                                                         "preconnection-blob": {"required": False, "type": "str"},
                                                         "preconnection-id": {"required": False, "type": "int"},
                                                         "remote-port": {"required": False, "type": "int"},
                                                         "security": {"required": False, "type": "str",
                                                                      "choices": ["rdp", "nla", "tls",
                                                                                  "any"]},
                                                         "server-layout": {"required": False, "type": "str",
                                                                           "choices": ["de-de-qwertz", "en-gb-qwerty", "en-us-qwerty",
                                                                                       "es-es-qwerty", "fr-fr-azerty", "fr-ch-qwertz",
                                                                                       "it-it-qwerty", "ja-jp-qwerty", "pt-br-qwerty",
                                                                                       "sv-se-qwerty", "tr-tr-qwerty", "failsafe"]},
                                                         "show-status-window": {"required": False, "type": "str",
                                                                                "choices": ["enable", "disable"]},
                                                         "sso": {"required": False, "type": "str",
                                                                 "choices": ["disable", "static", "auto"]},
                                                         "sso-credential": {"required": False, "type": "str",
                                                                            "choices": ["sslvpn-login", "alternative"]},
                                                         "sso-credential-sent-once": {"required": False, "type": "str",
                                                                                      "choices": ["enable", "disable"]},
                                                         "sso-password": {"required": False, "type": "str"},
                                                         "sso-username": {"required": False, "type": "str"},
                                                         "url": {"required": False, "type": "str"}
                                                     }},
                                       "name": {"required": True, "type": "str"}
                                   }},
                "custom-lang": {"required": False, "type": "str"},
                "customize-forticlient-download-url": {"required": False, "type": "str",
                                                       "choices": ["enable", "disable"]},
                "display-bookmark": {"required": False, "type": "str",
                                     "choices": ["enable", "disable"]},
                "display-connection-tools": {"required": False, "type": "str",
                                             "choices": ["enable", "disable"]},
                "display-history": {"required": False, "type": "str",
                                    "choices": ["enable", "disable"]},
                "display-status": {"required": False, "type": "str",
                                   "choices": ["enable", "disable"]},
                "dns-server1": {"required": False, "type": "str"},
                "dns-server2": {"required": False, "type": "str"},
                "dns-suffix": {"required": False, "type": "str"},
                "exclusive-routing": {"required": False, "type": "str",
                                      "choices": ["enable", "disable"]},
                "forticlient-download": {"required": False, "type": "str",
                                         "choices": ["enable", "disable"]},
                "forticlient-download-method": {"required": False, "type": "str",
                                                "choices": ["direct", "ssl-vpn"]},
                "heading": {"required": False, "type": "str"},
                "hide-sso-credential": {"required": False, "type": "str",
                                        "choices": ["enable", "disable"]},
                "host-check": {"required": False, "type": "str",
                               "choices": ["none", "av", "fw",
                                           "av-fw", "custom"]},
                "host-check-interval": {"required": False, "type": "int"},
                "host-check-policy": {"required": False, "type": "list",
                                      "options": {
                                          "name": {"required": True, "type": "str"}
                                      }},
                "ip-mode": {"required": False, "type": "str",
                            "choices": ["range", "user-group"]},
                "ip-pools": {"required": False, "type": "list",
                             "options": {
                                 "name": {"required": True, "type": "str"}
                             }},
                "ipv6-dns-server1": {"required": False, "type": "str"},
                "ipv6-dns-server2": {"required": False, "type": "str"},
                "ipv6-exclusive-routing": {"required": False, "type": "str",
                                           "choices": ["enable", "disable"]},
                "ipv6-pools": {"required": False, "type": "list",
                               "options": {
                                   "name": {"required": True, "type": "str"}
                               }},
                "ipv6-service-restriction": {"required": False, "type": "str",
                                             "choices": ["enable", "disable"]},
                "ipv6-split-tunneling": {"required": False, "type": "str",
                                         "choices": ["enable", "disable"]},
                "ipv6-split-tunneling-routing-address": {"required": False, "type": "list",
                                                         "options": {
                                                             "name": {"required": True, "type": "str"}
                                                         }},
                "ipv6-tunnel-mode": {"required": False, "type": "str",
                                     "choices": ["enable", "disable"]},
                "ipv6-wins-server1": {"required": False, "type": "str"},
                "ipv6-wins-server2": {"required": False, "type": "str"},
                "keep-alive": {"required": False, "type": "str",
                               "choices": ["enable", "disable"]},
                "limit-user-logins": {"required": False, "type": "str",
                                      "choices": ["enable", "disable"]},
                "mac-addr-action": {"required": False, "type": "str",
                                    "choices": ["allow", "deny"]},
                "mac-addr-check": {"required": False, "type": "str",
                                   "choices": ["enable", "disable"]},
                "mac-addr-check-rule": {"required": False, "type": "list",
                                        "options": {
                                            "mac-addr-list": {"required": False, "type": "list",
                                                              "options": {
                                                                  "addr": {"required": True, "type": "str"}
                                                              }},
                                            "mac-addr-mask": {"required": False, "type": "int"},
                                            "name": {"required": True, "type": "str"}
                                        }},
                "macos-forticlient-download-url": {"required": False, "type": "str"},
                "name": {"required": True, "type": "str"},
                "os-check": {"required": False, "type": "str",
                             "choices": ["enable", "disable"]},
                "os-check-list": {"required": False, "type": "list",
                                  "options": {
                                      "action": {"required": False, "type": "str",
                                                 "choices": ["deny", "allow", "check-up-to-date"]},
                                      "latest-patch-level": {"required": False, "type": "str"},
                                      "name": {"required": True, "type": "str"},
                                      "tolerance": {"required": False, "type": "int"}
                                  }},
                "redir-url": {"required": False, "type": "str"},
                "save-password": {"required": False, "type": "str",
                                  "choices": ["enable", "disable"]},
                "service-restriction": {"required": False, "type": "str",
                                        "choices": ["enable", "disable"]},
                "skip-check-for-unsupported-browser": {"required": False, "type": "str",
                                                       "choices": ["enable", "disable"]},
                "skip-check-for-unsupported-os": {"required": False, "type": "str",
                                                  "choices": ["enable", "disable"]},
                "smb-ntlmv1-auth": {"required": False, "type": "str",
                                    "choices": ["enable", "disable"]},
                "smbv1": {"required": False, "type": "str",
                          "choices": ["enable", "disable"]},
                "split-dns": {"required": False, "type": "list",
                              "options": {
                                  "dns-server1": {"required": False, "type": "str"},
                                  "dns-server2": {"required": False, "type": "str"},
                                  "domains": {"required": False, "type": "str"},
                                  "id": {"required": True, "type": "int"},
                                  "ipv6-dns-server1": {"required": False, "type": "str"},
                                  "ipv6-dns-server2": {"required": False, "type": "str"}
                              }},
                "split-tunneling": {"required": False, "type": "str",
                                    "choices": ["enable", "disable"]},
                "split-tunneling-routing-address": {"required": False, "type": "list",
                                                    "options": {
                                                        "name": {"required": True, "type": "str"}
                                                    }},
                "theme": {"required": False, "type": "str",
                          "choices": ["blue", "green", "red",
                                      "melongene", "mariner"]},
                "tunnel-mode": {"required": False, "type": "str",
                                "choices": ["enable", "disable"]},
                "user-bookmark": {"required": False, "type": "str",
                                  "choices": ["enable", "disable"]},
                "user-group-bookmark": {"required": False, "type": "str",
                                        "choices": ["enable", "disable"]},
                "web-mode": {"required": False, "type": "str",
                             "choices": ["enable", "disable"]},
                "windows-forticlient-download-url": {"required": False, "type": "str"},
                "wins-server1": {"required": False, "type": "str"},
                "wins-server2": {"required": False, "type": "str"}

            }
        }
    }

    module = AnsibleModule(argument_spec=fields,
                           supports_check_mode=False)
    try:
        from fortiosapi import FortiOSAPI
    except ImportError:
        module.fail_json(msg="fortiosapi module is required")

    global fos
    fos = FortiOSAPI()

    is_error, has_changed, result = fortios_vpn_ssl_web(module.params, fos)

    if not is_error:
        module.exit_json(changed=has_changed, meta=result)
    else:
        module.fail_json(msg="Error in repo", meta=result)


if __name__ == '__main__':
    main()
