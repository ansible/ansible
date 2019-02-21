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
module: fortios_system_admin
short_description: Configure admin users in Fortinet's FortiOS and FortiGate.
description:
    - This module is able to configure a FortiGate or FortiOS by allowing the
      user to set and modify system feature and admin category.
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
    system_admin:
        description:
            - Configure admin users.
        default: null
        suboptions:
            state:
                description:
                    - Indicates whether to create or remove the object
                choices:
                    - present
                    - absent
            accprofile:
                description:
                    - Access profile for this administrator. Access profiles control administrator access to FortiGate features. Source system.accprofile.name.
            accprofile-override:
                description:
                    - Enable to use the name of an access profile provided by the remote authentication server to control the FortiGate features that this
                       administrator can access.
                choices:
                    - enable
                    - disable
            allow-remove-admin-session:
                description:
                    - Enable/disable allow admin session to be removed by privileged admin users.
                choices:
                    - enable
                    - disable
            comments:
                description:
                    - Comment.
            email-to:
                description:
                    - This administrator's email address.
            force-password-change:
                description:
                    - Enable/disable force password change on next login.
                choices:
                    - enable
                    - disable
            fortitoken:
                description:
                    - This administrator's FortiToken serial number.
            guest-auth:
                description:
                    - Enable/disable guest authentication.
                choices:
                    - disable
                    - enable
            guest-lang:
                description:
                    - Guest management portal language. Source system.custom-language.name.
            guest-usergroups:
                description:
                    - Select guest user groups.
                suboptions:
                    name:
                        description:
                            - Select guest user groups.
                        required: true
            gui-dashboard:
                description:
                    - GUI dashboards.
                suboptions:
                    columns:
                        description:
                            - Number of columns.
                    id:
                        description:
                            - Dashboard ID.
                        required: true
                    layout-type:
                        description:
                            - Layout type.
                        choices:
                            - responsive
                            - fixed
                    name:
                        description:
                            - Dashboard name.
                    scope:
                        description:
                            - Dashboard scope.
                        choices:
                            - global
                            - vdom
                    widget:
                        description:
                            - Dashboard widgets.
                        suboptions:
                            fabric-device:
                                description:
                                    - Fabric device to monitor.
                            filters:
                                description:
                                    - FortiView filters.
                                suboptions:
                                    id:
                                        description:
                                            - FortiView Filter ID.
                                        required: true
                                    key:
                                        description:
                                            - Filter key.
                                    value:
                                        description:
                                            - Filter value.
                            height:
                                description:
                                    - Height.
                            id:
                                description:
                                    - Widget ID.
                                required: true
                            industry:
                                description:
                                    - Security Audit Rating industry.
                                choices:
                                    - default
                                    - custom
                            interface:
                                description:
                                    - Interface to monitor. Source system.interface.name.
                            region:
                                description:
                                    - Security Audit Rating region.
                                choices:
                                    - default
                                    - custom
                            report-by:
                                description:
                                    - Field to aggregate the data by.
                                choices:
                                    - source
                                    - destination
                                    - country
                                    - intfpair
                                    - srcintf
                                    - dstintf
                                    - policy
                                    - wificlient
                                    - shaper
                                    - endpoint-vulnerability
                                    - endpoint-device
                                    - application
                                    - cloud-app
                                    - cloud-user
                                    - web-domain
                                    - web-category
                                    - web-search-phrase
                                    - threat
                                    - system
                                    - unauth
                                    - admin
                                    - vpn
                            sort-by:
                                description:
                                    - Field to sort the data by.
                            timeframe:
                                description:
                                    - Timeframe period of reported data.
                                choices:
                                    - realtime
                                    - 5min
                                    - hour
                                    - day
                                    - week
                            title:
                                description:
                                    - Widget title.
                            type:
                                description:
                                    - Widget type.
                                choices:
                                    - sysinfo
                                    - licinfo
                                    - vminfo
                                    - forticloud
                                    - cpu-usage
                                    - memory-usage
                                    - disk-usage
                                    - log-rate
                                    - sessions
                                    - session-rate
                                    - tr-history
                                    - analytics
                                    - usb-modem
                                    - admins
                                    - security-fabric
                                    - security-fabric-ranking
                                    - ha-status
                                    - vulnerability-summary
                                    - host-scan-summary
                                    - fortiview
                                    - botnet-activity
                                    - fortimail
                            visualization:
                                description:
                                    - Visualization to use.
                                choices:
                                    - table
                                    - bubble
                                    - country
                                    - chord
                            width:
                                description:
                                    - Width.
                            x-pos:
                                description:
                                    - X position.
                            y-pos:
                                description:
                                    - Y position.
            gui-global-menu-favorites:
                description:
                    - Favorite GUI menu IDs for the global VDOM.
                suboptions:
                    id:
                        description:
                            - Select menu ID.
                        required: true
            gui-vdom-menu-favorites:
                description:
                    - Favorite GUI menu IDs for VDOMs.
                suboptions:
                    id:
                        description:
                            - Select menu ID.
                        required: true
            hidden:
                description:
                    - Admin user hidden attribute.
            history0:
                description:
                    - history0
            history1:
                description:
                    - history1
            ip6-trusthost1:
                description:
                    - Any IPv6 address from which the administrator can connect to the FortiGate unit. Default allows access from any IPv6 address.
            ip6-trusthost10:
                description:
                    - Any IPv6 address from which the administrator can connect to the FortiGate unit. Default allows access from any IPv6 address.
            ip6-trusthost2:
                description:
                    - Any IPv6 address from which the administrator can connect to the FortiGate unit. Default allows access from any IPv6 address.
            ip6-trusthost3:
                description:
                    - Any IPv6 address from which the administrator can connect to the FortiGate unit. Default allows access from any IPv6 address.
            ip6-trusthost4:
                description:
                    - Any IPv6 address from which the administrator can connect to the FortiGate unit. Default allows access from any IPv6 address.
            ip6-trusthost5:
                description:
                    - Any IPv6 address from which the administrator can connect to the FortiGate unit. Default allows access from any IPv6 address.
            ip6-trusthost6:
                description:
                    - Any IPv6 address from which the administrator can connect to the FortiGate unit. Default allows access from any IPv6 address.
            ip6-trusthost7:
                description:
                    - Any IPv6 address from which the administrator can connect to the FortiGate unit. Default allows access from any IPv6 address.
            ip6-trusthost8:
                description:
                    - Any IPv6 address from which the administrator can connect to the FortiGate unit. Default allows access from any IPv6 address.
            ip6-trusthost9:
                description:
                    - Any IPv6 address from which the administrator can connect to the FortiGate unit. Default allows access from any IPv6 address.
            login-time:
                description:
                    - Record user login time.
                suboptions:
                    last-failed-login:
                        description:
                            - Last failed login time.
                    last-login:
                        description:
                            - Last successful login time.
                    usr-name:
                        description:
                            - User name.
                        required: true
            name:
                description:
                    - User name.
                required: true
            password:
                description:
                    - Admin user password.
            password-expire:
                description:
                    - Password expire time.
            peer-auth:
                description:
                    - Set to enable peer certificate authentication (for HTTPS admin access).
                choices:
                    - enable
                    - disable
            peer-group:
                description:
                    - Name of peer group defined under config user group which has PKI members. Used for peer certificate authentication (for HTTPS admin
                       access).
            radius-vdom-override:
                description:
                    - Enable to use the names of VDOMs provided by the remote authentication server to control the VDOMs that this administrator can access.
                choices:
                    - enable
                    - disable
            remote-auth:
                description:
                    - Enable/disable authentication using a remote RADIUS, LDAP, or TACACS+ server.
                choices:
                    - enable
                    - disable
            remote-group:
                description:
                    - User group name used for remote auth.
            schedule:
                description:
                    - Firewall schedule used to restrict when the administrator can log in. No schedule means no restrictions.
            sms-custom-server:
                description:
                    - Custom SMS server to send SMS messages to. Source system.sms-server.name.
            sms-phone:
                description:
                    - Phone number on which the administrator receives SMS messages.
            sms-server:
                description:
                    - Send SMS messages using the FortiGuard SMS server or a custom server.
                choices:
                    - fortiguard
                    - custom
            ssh-certificate:
                description:
                    - Select the certificate to be used by the FortiGate for authentication with an SSH client. Source certificate.local.name.
            ssh-public-key1:
                description:
                    - Public key of an SSH client. The client is authenticated without being asked for credentials. Create the public-private key pair in the
                       SSH client application.
            ssh-public-key2:
                description:
                    - Public key of an SSH client. The client is authenticated without being asked for credentials. Create the public-private key pair in the
                       SSH client application.
            ssh-public-key3:
                description:
                    - Public key of an SSH client. The client is authenticated without being asked for credentials. Create the public-private key pair in the
                       SSH client application.
            trusthost1:
                description:
                    - Any IPv4 address or subnet address and netmask from which the administrator can connect to the FortiGate unit. Default allows access
                       from any IPv4 address.
            trusthost10:
                description:
                    - Any IPv4 address or subnet address and netmask from which the administrator can connect to the FortiGate unit. Default allows access
                       from any IPv4 address.
            trusthost2:
                description:
                    - Any IPv4 address or subnet address and netmask from which the administrator can connect to the FortiGate unit. Default allows access
                       from any IPv4 address.
            trusthost3:
                description:
                    - Any IPv4 address or subnet address and netmask from which the administrator can connect to the FortiGate unit. Default allows access
                       from any IPv4 address.
            trusthost4:
                description:
                    - Any IPv4 address or subnet address and netmask from which the administrator can connect to the FortiGate unit. Default allows access
                       from any IPv4 address.
            trusthost5:
                description:
                    - Any IPv4 address or subnet address and netmask from which the administrator can connect to the FortiGate unit. Default allows access
                       from any IPv4 address.
            trusthost6:
                description:
                    - Any IPv4 address or subnet address and netmask from which the administrator can connect to the FortiGate unit. Default allows access
                       from any IPv4 address.
            trusthost7:
                description:
                    - Any IPv4 address or subnet address and netmask from which the administrator can connect to the FortiGate unit. Default allows access
                       from any IPv4 address.
            trusthost8:
                description:
                    - Any IPv4 address or subnet address and netmask from which the administrator can connect to the FortiGate unit. Default allows access
                       from any IPv4 address.
            trusthost9:
                description:
                    - Any IPv4 address or subnet address and netmask from which the administrator can connect to the FortiGate unit. Default allows access
                       from any IPv4 address.
            two-factor:
                description:
                    - Enable/disable two-factor authentication.
                choices:
                    - disable
                    - fortitoken
                    - email
                    - sms
            vdom:
                description:
                    - Virtual domain(s) that the administrator can access.
                suboptions:
                    name:
                        description:
                            - Virtual domain name. Source system.vdom.name.
                        required: true
            wildcard:
                description:
                    - Enable/disable wildcard RADIUS authentication.
                choices:
                    - enable
                    - disable
'''

EXAMPLES = '''
- hosts: localhost
  vars:
   host: "192.168.122.40"
   username: "admin"
   password: ""
   vdom: "root"
  tasks:
  - name: Configure admin users.
    fortios_system_admin:
      host:  "{{ host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{ vdom }}"
      https: "False"
      system_admin:
        state: "present"
        accprofile: "<your_own_value> (source system.accprofile.name)"
        accprofile-override: "enable"
        allow-remove-admin-session: "enable"
        comments: "<your_own_value>"
        email-to: "<your_own_value>"
        force-password-change: "enable"
        fortitoken: "<your_own_value>"
        guest-auth: "disable"
        guest-lang: "<your_own_value> (source system.custom-language.name)"
        guest-usergroups:
         -
            name: "default_name_13"
        gui-dashboard:
         -
            columns: "15"
            id:  "16"
            layout-type: "responsive"
            name: "default_name_18"
            scope: "global"
            widget:
             -
                fabric-device: "<your_own_value>"
                filters:
                 -
                    id:  "23"
                    key: "<your_own_value>"
                    value: "<your_own_value>"
                height: "26"
                id:  "27"
                industry: "default"
                interface: "<your_own_value> (source system.interface.name)"
                region: "default"
                report-by: "source"
                sort-by: "<your_own_value>"
                timeframe: "realtime"
                title: "<your_own_value>"
                type: "sysinfo"
                visualization: "table"
                width: "37"
                x-pos: "38"
                y-pos: "39"
        gui-global-menu-favorites:
         -
            id:  "41"
        gui-vdom-menu-favorites:
         -
            id:  "43"
        hidden: "44"
        history0: "<your_own_value>"
        history1: "<your_own_value>"
        ip6-trusthost1: "<your_own_value>"
        ip6-trusthost10: "<your_own_value>"
        ip6-trusthost2: "<your_own_value>"
        ip6-trusthost3: "<your_own_value>"
        ip6-trusthost4: "<your_own_value>"
        ip6-trusthost5: "<your_own_value>"
        ip6-trusthost6: "<your_own_value>"
        ip6-trusthost7: "<your_own_value>"
        ip6-trusthost8: "<your_own_value>"
        ip6-trusthost9: "<your_own_value>"
        login-time:
         -
            last-failed-login: "<your_own_value>"
            last-login: "<your_own_value>"
            usr-name: "<your_own_value>"
        name: "default_name_61"
        password: "<your_own_value>"
        password-expire: "<your_own_value>"
        peer-auth: "enable"
        peer-group: "<your_own_value>"
        radius-vdom-override: "enable"
        remote-auth: "enable"
        remote-group: "<your_own_value>"
        schedule: "<your_own_value>"
        sms-custom-server: "<your_own_value> (source system.sms-server.name)"
        sms-phone: "<your_own_value>"
        sms-server: "fortiguard"
        ssh-certificate: "<your_own_value> (source certificate.local.name)"
        ssh-public-key1: "<your_own_value>"
        ssh-public-key2: "<your_own_value>"
        ssh-public-key3: "<your_own_value>"
        trusthost1: "<your_own_value>"
        trusthost10: "<your_own_value>"
        trusthost2: "<your_own_value>"
        trusthost3: "<your_own_value>"
        trusthost4: "<your_own_value>"
        trusthost5: "<your_own_value>"
        trusthost6: "<your_own_value>"
        trusthost7: "<your_own_value>"
        trusthost8: "<your_own_value>"
        trusthost9: "<your_own_value>"
        two-factor: "disable"
        vdom:
         -
            name: "default_name_89 (source system.vdom.name)"
        wildcard: "enable"
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


def filter_system_admin_data(json):
    option_list = ['accprofile', 'accprofile-override', 'allow-remove-admin-session',
                   'comments', 'email-to', 'force-password-change',
                   'fortitoken', 'guest-auth', 'guest-lang',
                   'guest-usergroups', 'gui-dashboard', 'gui-global-menu-favorites',
                   'gui-vdom-menu-favorites', 'hidden', 'history0',
                   'history1', 'ip6-trusthost1', 'ip6-trusthost10',
                   'ip6-trusthost2', 'ip6-trusthost3', 'ip6-trusthost4',
                   'ip6-trusthost5', 'ip6-trusthost6', 'ip6-trusthost7',
                   'ip6-trusthost8', 'ip6-trusthost9', 'login-time',
                   'name', 'password', 'password-expire',
                   'peer-auth', 'peer-group', 'radius-vdom-override',
                   'remote-auth', 'remote-group', 'schedule',
                   'sms-custom-server', 'sms-phone', 'sms-server',
                   'ssh-certificate', 'ssh-public-key1', 'ssh-public-key2',
                   'ssh-public-key3', 'trusthost1', 'trusthost10',
                   'trusthost2', 'trusthost3', 'trusthost4',
                   'trusthost5', 'trusthost6', 'trusthost7',
                   'trusthost8', 'trusthost9', 'two-factor',
                   'vdom', 'wildcard']
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


def system_admin(data, fos):
    vdom = data['vdom']
    system_admin_data = data['system_admin']
    flattened_data = flatten_multilists_attributes(system_admin_data)
    filtered_data = filter_system_admin_data(flattened_data)
    if system_admin_data['state'] == "present":
        return fos.set('system',
                       'admin',
                       data=filtered_data,
                       vdom=vdom)

    elif system_admin_data['state'] == "absent":
        return fos.delete('system',
                          'admin',
                          mkey=filtered_data['name'],
                          vdom=vdom)


def fortios_system(data, fos):
    login(data)

    if data['system_admin']:
        resp = system_admin(data, fos)

    fos.logout()
    return not resp['status'] == "success", resp['status'] == "success", resp


def main():
    fields = {
        "host": {"required": True, "type": "str"},
        "username": {"required": True, "type": "str"},
        "password": {"required": False, "type": "str", "no_log": True},
        "vdom": {"required": False, "type": "str", "default": "root"},
        "https": {"required": False, "type": "bool", "default": True},
        "system_admin": {
            "required": False, "type": "dict",
            "options": {
                "state": {"required": True, "type": "str",
                          "choices": ["present", "absent"]},
                "accprofile": {"required": False, "type": "str"},
                "accprofile-override": {"required": False, "type": "str",
                                        "choices": ["enable", "disable"]},
                "allow-remove-admin-session": {"required": False, "type": "str",
                                               "choices": ["enable", "disable"]},
                "comments": {"required": False, "type": "str"},
                "email-to": {"required": False, "type": "str"},
                "force-password-change": {"required": False, "type": "str",
                                          "choices": ["enable", "disable"]},
                "fortitoken": {"required": False, "type": "str"},
                "guest-auth": {"required": False, "type": "str",
                               "choices": ["disable", "enable"]},
                "guest-lang": {"required": False, "type": "str"},
                "guest-usergroups": {"required": False, "type": "list",
                                     "options": {
                                         "name": {"required": True, "type": "str"}
                                     }},
                "gui-dashboard": {"required": False, "type": "list",
                                  "options": {
                                      "columns": {"required": False, "type": "int"},
                                      "id": {"required": True, "type": "int"},
                                      "layout-type": {"required": False, "type": "str",
                                                      "choices": ["responsive", "fixed"]},
                                      "name": {"required": False, "type": "str"},
                                      "scope": {"required": False, "type": "str",
                                                "choices": ["global", "vdom"]},
                                      "widget": {"required": False, "type": "list",
                                                 "options": {
                                                     "fabric-device": {"required": False, "type": "str"},
                                                     "filters": {"required": False, "type": "list",
                                                                 "options": {
                                                                     "id": {"required": True, "type": "int"},
                                                                     "key": {"required": False, "type": "str"},
                                                                     "value": {"required": False, "type": "str"}
                                                                 }},
                                                     "height": {"required": False, "type": "int"},
                                                     "id": {"required": True, "type": "int"},
                                                     "industry": {"required": False, "type": "str",
                                                                  "choices": ["default", "custom"]},
                                                     "interface": {"required": False, "type": "str"},
                                                     "region": {"required": False, "type": "str",
                                                                "choices": ["default", "custom"]},
                                                     "report-by": {"required": False, "type": "str",
                                                                   "choices": ["source", "destination", "country",
                                                                               "intfpair", "srcintf", "dstintf",
                                                                               "policy", "wificlient", "shaper",
                                                                               "endpoint-vulnerability", "endpoint-device", "application",
                                                                               "cloud-app", "cloud-user", "web-domain",
                                                                               "web-category", "web-search-phrase", "threat",
                                                                               "system", "unauth", "admin",
                                                                               "vpn"]},
                                                     "sort-by": {"required": False, "type": "str"},
                                                     "timeframe": {"required": False, "type": "str",
                                                                   "choices": ["realtime", "5min", "hour",
                                                                               "day", "week"]},
                                                     "title": {"required": False, "type": "str"},
                                                     "type": {"required": False, "type": "str",
                                                              "choices": ["sysinfo", "licinfo", "vminfo",
                                                                          "forticloud", "cpu-usage", "memory-usage",
                                                                          "disk-usage", "log-rate", "sessions",
                                                                          "session-rate", "tr-history", "analytics",
                                                                          "usb-modem", "admins", "security-fabric",
                                                                          "security-fabric-ranking", "ha-status", "vulnerability-summary",
                                                                          "host-scan-summary", "fortiview", "botnet-activity",
                                                                          "fortimail"]},
                                                     "visualization": {"required": False, "type": "str",
                                                                       "choices": ["table", "bubble", "country",
                                                                                   "chord"]},
                                                     "width": {"required": False, "type": "int"},
                                                     "x-pos": {"required": False, "type": "int"},
                                                     "y-pos": {"required": False, "type": "int"}
                                                 }}
                                  }},
                "gui-global-menu-favorites": {"required": False, "type": "list",
                                              "options": {
                                                  "id": {"required": True, "type": "str"}
                                              }},
                "gui-vdom-menu-favorites": {"required": False, "type": "list",
                                            "options": {
                                                "id": {"required": True, "type": "str"}
                                            }},
                "hidden": {"required": False, "type": "int"},
                "history0": {"required": False, "type": "str"},
                "history1": {"required": False, "type": "str"},
                "ip6-trusthost1": {"required": False, "type": "str"},
                "ip6-trusthost10": {"required": False, "type": "str"},
                "ip6-trusthost2": {"required": False, "type": "str"},
                "ip6-trusthost3": {"required": False, "type": "str"},
                "ip6-trusthost4": {"required": False, "type": "str"},
                "ip6-trusthost5": {"required": False, "type": "str"},
                "ip6-trusthost6": {"required": False, "type": "str"},
                "ip6-trusthost7": {"required": False, "type": "str"},
                "ip6-trusthost8": {"required": False, "type": "str"},
                "ip6-trusthost9": {"required": False, "type": "str"},
                "login-time": {"required": False, "type": "list",
                               "options": {
                                   "last-failed-login": {"required": False, "type": "str"},
                                   "last-login": {"required": False, "type": "str"},
                                   "usr-name": {"required": True, "type": "str"}
                               }},
                "name": {"required": True, "type": "str"},
                "password": {"required": False, "type": "str"},
                "password-expire": {"required": False, "type": "str"},
                "peer-auth": {"required": False, "type": "str",
                              "choices": ["enable", "disable"]},
                "peer-group": {"required": False, "type": "str"},
                "radius-vdom-override": {"required": False, "type": "str",
                                         "choices": ["enable", "disable"]},
                "remote-auth": {"required": False, "type": "str",
                                "choices": ["enable", "disable"]},
                "remote-group": {"required": False, "type": "str"},
                "schedule": {"required": False, "type": "str"},
                "sms-custom-server": {"required": False, "type": "str"},
                "sms-phone": {"required": False, "type": "str"},
                "sms-server": {"required": False, "type": "str",
                               "choices": ["fortiguard", "custom"]},
                "ssh-certificate": {"required": False, "type": "str"},
                "ssh-public-key1": {"required": False, "type": "str"},
                "ssh-public-key2": {"required": False, "type": "str"},
                "ssh-public-key3": {"required": False, "type": "str"},
                "trusthost1": {"required": False, "type": "str"},
                "trusthost10": {"required": False, "type": "str"},
                "trusthost2": {"required": False, "type": "str"},
                "trusthost3": {"required": False, "type": "str"},
                "trusthost4": {"required": False, "type": "str"},
                "trusthost5": {"required": False, "type": "str"},
                "trusthost6": {"required": False, "type": "str"},
                "trusthost7": {"required": False, "type": "str"},
                "trusthost8": {"required": False, "type": "str"},
                "trusthost9": {"required": False, "type": "str"},
                "two-factor": {"required": False, "type": "str",
                               "choices": ["disable", "fortitoken", "email",
                                           "sms"]},
                "vdom": {"required": False, "type": "list",
                         "options": {
                             "name": {"required": True, "type": "str"}
                         }},
                "wildcard": {"required": False, "type": "str",
                             "choices": ["enable", "disable"]}

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

    is_error, has_changed, result = fortios_system(module.params, fos)

    if not is_error:
        module.exit_json(changed=has_changed, meta=result)
    else:
        module.fail_json(msg="Error in repo", meta=result)


if __name__ == '__main__':
    main()
