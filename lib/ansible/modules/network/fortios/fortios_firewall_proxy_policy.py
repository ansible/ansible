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
module: fortios_firewall_proxy_policy
short_description: Configure proxy policies in Fortinet's FortiOS and FortiGate.
description:
    - This module is able to configure a FortiGate or FortiOS (FOS) device by allowing the
      user to set and modify firewall feature and proxy_policy category.
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
    firewall_proxy_policy:
        description:
            - Configure proxy policies.
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
            action:
                description:
                    - Accept or deny traffic matching the policy parameters.
                type: str
                choices:
                    - accept
                    - deny
                    - redirect
            application_list:
                description:
                    - Name of an existing Application list. Source application.list.name.
                type: str
            av_profile:
                description:
                    - Name of an existing Antivirus profile. Source antivirus.profile.name.
                type: str
            comments:
                description:
                    - Optional comments.
                type: str
            disclaimer:
                description:
                    - "Web proxy disclaimer setting: by domain, policy, or user."
                type: str
                choices:
                    - disable
                    - domain
                    - policy
                    - user
            dlp_sensor:
                description:
                    - Name of an existing DLP sensor. Source dlp.sensor.name.
                type: str
            dstaddr:
                description:
                    - Destination address objects.
                type: list
                suboptions:
                    name:
                        description:
                            - Address name. Source firewall.address.name firewall.addrgrp.name firewall.proxy-address.name firewall.proxy-addrgrp.name
                               firewall.vip.name firewall.vipgrp.name firewall.vip46.name firewall.vipgrp46.name system.external-resource.name.
                        required: true
                        type: str
            dstaddr_negate:
                description:
                    - When enabled, destination addresses match against any address EXCEPT the specified destination addresses.
                type: str
                choices:
                    - enable
                    - disable
            dstaddr6:
                description:
                    - IPv6 destination address objects.
                type: list
                suboptions:
                    name:
                        description:
                            - Address name. Source firewall.address6.name firewall.addrgrp6.name firewall.vip6.name firewall.vipgrp6.name firewall.vip64.name
                               firewall.vipgrp64.name system.external-resource.name.
                        required: true
                        type: str
            dstintf:
                description:
                    - Destination interface names.
                type: list
                suboptions:
                    name:
                        description:
                            - Interface name. Source system.interface.name system.zone.name.
                        required: true
                        type: str
            global_label:
                description:
                    - Global web-based manager visible label.
                type: str
            groups:
                description:
                    - Names of group objects.
                type: list
                suboptions:
                    name:
                        description:
                            - Group name. Source user.group.name.
                        required: true
                        type: str
            http_tunnel_auth:
                description:
                    - Enable/disable HTTP tunnel authentication.
                type: str
                choices:
                    - enable
                    - disable
            icap_profile:
                description:
                    - Name of an existing ICAP profile. Source icap.profile.name.
                type: str
            internet_service:
                description:
                    - Enable/disable use of Internet Services for this policy. If enabled, destination address and service are not used.
                type: str
                choices:
                    - enable
                    - disable
            internet_service_custom:
                description:
                    - Custom Internet Service name.
                type: list
                suboptions:
                    name:
                        description:
                            - Custom name. Source firewall.internet-service-custom.name.
                        required: true
                        type: str
            internet_service_id:
                description:
                    - Internet Service ID.
                type: list
                suboptions:
                    id:
                        description:
                            - Internet Service ID. Source firewall.internet-service.id.
                        required: true
                        type: int
            internet_service_negate:
                description:
                    - When enabled, Internet Services match against any internet service EXCEPT the selected Internet Service.
                type: str
                choices:
                    - enable
                    - disable
            ips_sensor:
                description:
                    - Name of an existing IPS sensor. Source ips.sensor.name.
                type: str
            label:
                description:
                    - VDOM-specific GUI visible label.
                type: str
            logtraffic:
                description:
                    - Enable/disable logging traffic through the policy.
                type: str
                choices:
                    - all
                    - utm
                    - disable
            logtraffic_start:
                description:
                    - Enable/disable policy log traffic start.
                type: str
                choices:
                    - enable
                    - disable
            policyid:
                description:
                    - Policy ID.
                required: true
                type: int
            poolname:
                description:
                    - Name of IP pool object.
                type: list
                suboptions:
                    name:
                        description:
                            - IP pool name. Source firewall.ippool.name.
                        required: true
                        type: str
            profile_group:
                description:
                    - Name of profile group. Source firewall.profile-group.name.
                type: str
            profile_protocol_options:
                description:
                    - Name of an existing Protocol options profile. Source firewall.profile-protocol-options.name.
                type: str
            profile_type:
                description:
                    - Determine whether the firewall policy allows security profile groups or single profiles only.
                type: str
                choices:
                    - single
                    - group
            proxy:
                description:
                    - Type of explicit proxy.
                type: str
                choices:
                    - explicit-web
                    - transparent-web
                    - ftp
                    - ssh
                    - ssh-tunnel
                    - wanopt
            redirect_url:
                description:
                    - Redirect URL for further explicit web proxy processing.
                type: str
            replacemsg_override_group:
                description:
                    - Authentication replacement message override group. Source system.replacemsg-group.name.
                type: str
            scan_botnet_connections:
                description:
                    - Enable/disable scanning of connections to Botnet servers.
                type: str
                choices:
                    - disable
                    - block
                    - monitor
            schedule:
                description:
                    - Name of schedule object. Source firewall.schedule.onetime.name firewall.schedule.recurring.name firewall.schedule.group.name.
                type: str
            service:
                description:
                    - Name of service objects.
                type: list
                suboptions:
                    name:
                        description:
                            - Service name. Source firewall.service.custom.name firewall.service.group.name.
                        required: true
                        type: str
            service_negate:
                description:
                    - When enabled, services match against any service EXCEPT the specified destination services.
                type: str
                choices:
                    - enable
                    - disable
            session_ttl:
                description:
                    - TTL in seconds for sessions accepted by this policy (0 means use the system ).
                type: int
            spamfilter_profile:
                description:
                    - Name of an existing Spam filter profile. Source spamfilter.profile.name.
                type: str
            srcaddr:
                description:
                    - Source address objects.
                type: list
                suboptions:
                    name:
                        description:
                            - Address name. Source firewall.address.name firewall.addrgrp.name firewall.proxy-address.name firewall.proxy-addrgrp.name system
                              .external-resource.name.
                        required: true
                        type: str
            srcaddr_negate:
                description:
                    - When enabled, source addresses match against any address EXCEPT the specified source addresses.
                type: str
                choices:
                    - enable
                    - disable
            srcaddr6:
                description:
                    - IPv6 source address objects.
                type: list
                suboptions:
                    name:
                        description:
                            - Address name. Source firewall.address6.name firewall.addrgrp6.name system.external-resource.name.
                        required: true
                        type: str
            srcintf:
                description:
                    - Source interface names.
                type: list
                suboptions:
                    name:
                        description:
                            - Interface name. Source system.interface.name system.zone.name.
                        required: true
                        type: str
            ssh_filter_profile:
                description:
                    - Name of an existing SSH filter profile. Source ssh-filter.profile.name.
                type: str
            ssl_ssh_profile:
                description:
                    - Name of an existing SSL SSH profile. Source firewall.ssl-ssh-profile.name.
                type: str
            status:
                description:
                    - Enable/disable the active status of the policy.
                type: str
                choices:
                    - enable
                    - disable
            transparent:
                description:
                    - Enable to use the IP address of the client to connect to the server.
                type: str
                choices:
                    - enable
                    - disable
            users:
                description:
                    - Names of user objects.
                type: list
                suboptions:
                    name:
                        description:
                            - Group name. Source user.local.name.
                        required: true
                        type: str
            utm_status:
                description:
                    - Enable the use of UTM profiles/sensors/lists.
                type: str
                choices:
                    - enable
                    - disable
            uuid:
                description:
                    - Universally Unique Identifier (UUID; automatically assigned but can be manually reset).
                type: str
            waf_profile:
                description:
                    - Name of an existing Web application firewall profile. Source waf.profile.name.
                type: str
            webcache:
                description:
                    - Enable/disable web caching.
                type: str
                choices:
                    - enable
                    - disable
            webcache_https:
                description:
                    - Enable/disable web caching for HTTPS (Requires deep-inspection enabled in ssl-ssh-profile).
                type: str
                choices:
                    - disable
                    - enable
            webfilter_profile:
                description:
                    - Name of an existing Web filter profile. Source webfilter.profile.name.
                type: str
            webproxy_forward_server:
                description:
                    - Name of web proxy forward server. Source web-proxy.forward-server.name web-proxy.forward-server-group.name.
                type: str
            webproxy_profile:
                description:
                    - Name of web proxy profile. Source web-proxy.profile.name.
                type: str
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
  - name: Configure proxy policies.
    fortios_firewall_proxy_policy:
      host:  "{{ host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{ vdom }}"
      https: "False"
      state: "present"
      firewall_proxy_policy:
        action: "accept"
        application_list: "<your_own_value> (source application.list.name)"
        av_profile: "<your_own_value> (source antivirus.profile.name)"
        comments: "<your_own_value>"
        disclaimer: "disable"
        dlp_sensor: "<your_own_value> (source dlp.sensor.name)"
        dstaddr:
         -
            name: "default_name_10 (source firewall.address.name firewall.addrgrp.name firewall.proxy-address.name firewall.proxy-addrgrp.name firewall.vip
              .name firewall.vipgrp.name firewall.vip46.name firewall.vipgrp46.name system.external-resource.name)"
        dstaddr_negate: "enable"
        dstaddr6:
         -
            name: "default_name_13 (source firewall.address6.name firewall.addrgrp6.name firewall.vip6.name firewall.vipgrp6.name firewall.vip64.name firewall
              .vipgrp64.name system.external-resource.name)"
        dstintf:
         -
            name: "default_name_15 (source system.interface.name system.zone.name)"
        global_label: "<your_own_value>"
        groups:
         -
            name: "default_name_18 (source user.group.name)"
        http_tunnel_auth: "enable"
        icap_profile: "<your_own_value> (source icap.profile.name)"
        internet_service: "enable"
        internet_service_custom:
         -
            name: "default_name_23 (source firewall.internet-service-custom.name)"
        internet_service_id:
         -
            id:  "25 (source firewall.internet-service.id)"
        internet_service_negate: "enable"
        ips_sensor: "<your_own_value> (source ips.sensor.name)"
        label: "<your_own_value>"
        logtraffic: "all"
        logtraffic_start: "enable"
        policyid: "31"
        poolname:
         -
            name: "default_name_33 (source firewall.ippool.name)"
        profile_group: "<your_own_value> (source firewall.profile-group.name)"
        profile_protocol_options: "<your_own_value> (source firewall.profile-protocol-options.name)"
        profile_type: "single"
        proxy: "explicit-web"
        redirect_url: "<your_own_value>"
        replacemsg_override_group: "<your_own_value> (source system.replacemsg-group.name)"
        scan_botnet_connections: "disable"
        schedule: "<your_own_value> (source firewall.schedule.onetime.name firewall.schedule.recurring.name firewall.schedule.group.name)"
        service:
         -
            name: "default_name_43 (source firewall.service.custom.name firewall.service.group.name)"
        service_negate: "enable"
        session_ttl: "45"
        spamfilter_profile: "<your_own_value> (source spamfilter.profile.name)"
        srcaddr:
         -
            name: "default_name_48 (source firewall.address.name firewall.addrgrp.name firewall.proxy-address.name firewall.proxy-addrgrp.name system
              .external-resource.name)"
        srcaddr_negate: "enable"
        srcaddr6:
         -
            name: "default_name_51 (source firewall.address6.name firewall.addrgrp6.name system.external-resource.name)"
        srcintf:
         -
            name: "default_name_53 (source system.interface.name system.zone.name)"
        ssh_filter_profile: "<your_own_value> (source ssh-filter.profile.name)"
        ssl_ssh_profile: "<your_own_value> (source firewall.ssl-ssh-profile.name)"
        status: "enable"
        transparent: "enable"
        users:
         -
            name: "default_name_59 (source user.local.name)"
        utm_status: "enable"
        uuid: "<your_own_value>"
        waf_profile: "<your_own_value> (source waf.profile.name)"
        webcache: "enable"
        webcache_https: "disable"
        webfilter_profile: "<your_own_value> (source webfilter.profile.name)"
        webproxy_forward_server: "<your_own_value> (source web-proxy.forward-server.name web-proxy.forward-server-group.name)"
        webproxy_profile: "<your_own_value> (source web-proxy.profile.name)"
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


def filter_firewall_proxy_policy_data(json):
    option_list = ['action', 'application_list', 'av_profile',
                   'comments', 'disclaimer', 'dlp_sensor',
                   'dstaddr', 'dstaddr_negate', 'dstaddr6',
                   'dstintf', 'global_label', 'groups',
                   'http_tunnel_auth', 'icap_profile', 'internet_service',
                   'internet_service_custom', 'internet_service_id', 'internet_service_negate',
                   'ips_sensor', 'label', 'logtraffic',
                   'logtraffic_start', 'policyid', 'poolname',
                   'profile_group', 'profile_protocol_options', 'profile_type',
                   'proxy', 'redirect_url', 'replacemsg_override_group',
                   'scan_botnet_connections', 'schedule', 'service',
                   'service_negate', 'session_ttl', 'spamfilter_profile',
                   'srcaddr', 'srcaddr_negate', 'srcaddr6',
                   'srcintf', 'ssh_filter_profile', 'ssl_ssh_profile',
                   'status', 'transparent', 'users',
                   'utm_status', 'uuid', 'waf_profile',
                   'webcache', 'webcache_https', 'webfilter_profile',
                   'webproxy_forward_server', 'webproxy_profile']
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


def firewall_proxy_policy(data, fos):
    vdom = data['vdom']
    if 'state' in data and data['state']:
        state = data['state']
    elif 'state' in data['firewall_proxy_policy'] and data['firewall_proxy_policy']:
        state = data['firewall_proxy_policy']['state']
    else:
        state = True
    firewall_proxy_policy_data = data['firewall_proxy_policy']
    filtered_data = underscore_to_hyphen(filter_firewall_proxy_policy_data(firewall_proxy_policy_data))

    if state == "present":
        return fos.set('firewall',
                       'proxy-policy',
                       data=filtered_data,
                       vdom=vdom)

    elif state == "absent":
        return fos.delete('firewall',
                          'proxy-policy',
                          mkey=filtered_data['policyid'],
                          vdom=vdom)


def is_successful_status(status):
    return status['status'] == "success" or \
        status['http_method'] == "DELETE" and status['http_status'] == 404


def fortios_firewall(data, fos):

    if data['firewall_proxy_policy']:
        resp = firewall_proxy_policy(data, fos)

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
        "firewall_proxy_policy": {
            "required": False, "type": "dict", "default": None,
            "options": {
                "state": {"required": False, "type": "str",
                          "choices": ["present", "absent"]},
                "action": {"required": False, "type": "str",
                           "choices": ["accept", "deny", "redirect"]},
                "application_list": {"required": False, "type": "str"},
                "av_profile": {"required": False, "type": "str"},
                "comments": {"required": False, "type": "str"},
                "disclaimer": {"required": False, "type": "str",
                               "choices": ["disable", "domain", "policy",
                                           "user"]},
                "dlp_sensor": {"required": False, "type": "str"},
                "dstaddr": {"required": False, "type": "list",
                            "options": {
                                "name": {"required": True, "type": "str"}
                            }},
                "dstaddr_negate": {"required": False, "type": "str",
                                   "choices": ["enable", "disable"]},
                "dstaddr6": {"required": False, "type": "list",
                             "options": {
                                 "name": {"required": True, "type": "str"}
                             }},
                "dstintf": {"required": False, "type": "list",
                            "options": {
                                "name": {"required": True, "type": "str"}
                            }},
                "global_label": {"required": False, "type": "str"},
                "groups": {"required": False, "type": "list",
                           "options": {
                               "name": {"required": True, "type": "str"}
                           }},
                "http_tunnel_auth": {"required": False, "type": "str",
                                     "choices": ["enable", "disable"]},
                "icap_profile": {"required": False, "type": "str"},
                "internet_service": {"required": False, "type": "str",
                                     "choices": ["enable", "disable"]},
                "internet_service_custom": {"required": False, "type": "list",
                                            "options": {
                                                "name": {"required": True, "type": "str"}
                                            }},
                "internet_service_id": {"required": False, "type": "list",
                                        "options": {
                                            "id": {"required": True, "type": "int"}
                                        }},
                "internet_service_negate": {"required": False, "type": "str",
                                            "choices": ["enable", "disable"]},
                "ips_sensor": {"required": False, "type": "str"},
                "label": {"required": False, "type": "str"},
                "logtraffic": {"required": False, "type": "str",
                               "choices": ["all", "utm", "disable"]},
                "logtraffic_start": {"required": False, "type": "str",
                                     "choices": ["enable", "disable"]},
                "policyid": {"required": True, "type": "int"},
                "poolname": {"required": False, "type": "list",
                             "options": {
                                 "name": {"required": True, "type": "str"}
                             }},
                "profile_group": {"required": False, "type": "str"},
                "profile_protocol_options": {"required": False, "type": "str"},
                "profile_type": {"required": False, "type": "str",
                                 "choices": ["single", "group"]},
                "proxy": {"required": False, "type": "str",
                          "choices": ["explicit-web", "transparent-web", "ftp",
                                      "ssh", "ssh-tunnel", "wanopt"]},
                "redirect_url": {"required": False, "type": "str"},
                "replacemsg_override_group": {"required": False, "type": "str"},
                "scan_botnet_connections": {"required": False, "type": "str",
                                            "choices": ["disable", "block", "monitor"]},
                "schedule": {"required": False, "type": "str"},
                "service": {"required": False, "type": "list",
                            "options": {
                                "name": {"required": True, "type": "str"}
                            }},
                "service_negate": {"required": False, "type": "str",
                                   "choices": ["enable", "disable"]},
                "session_ttl": {"required": False, "type": "int"},
                "spamfilter_profile": {"required": False, "type": "str"},
                "srcaddr": {"required": False, "type": "list",
                            "options": {
                                "name": {"required": True, "type": "str"}
                            }},
                "srcaddr_negate": {"required": False, "type": "str",
                                   "choices": ["enable", "disable"]},
                "srcaddr6": {"required": False, "type": "list",
                             "options": {
                                 "name": {"required": True, "type": "str"}
                             }},
                "srcintf": {"required": False, "type": "list",
                            "options": {
                                "name": {"required": True, "type": "str"}
                            }},
                "ssh_filter_profile": {"required": False, "type": "str"},
                "ssl_ssh_profile": {"required": False, "type": "str"},
                "status": {"required": False, "type": "str",
                           "choices": ["enable", "disable"]},
                "transparent": {"required": False, "type": "str",
                                "choices": ["enable", "disable"]},
                "users": {"required": False, "type": "list",
                          "options": {
                              "name": {"required": True, "type": "str"}
                          }},
                "utm_status": {"required": False, "type": "str",
                               "choices": ["enable", "disable"]},
                "uuid": {"required": False, "type": "str"},
                "waf_profile": {"required": False, "type": "str"},
                "webcache": {"required": False, "type": "str",
                             "choices": ["enable", "disable"]},
                "webcache_https": {"required": False, "type": "str",
                                   "choices": ["disable", "enable"]},
                "webfilter_profile": {"required": False, "type": "str"},
                "webproxy_forward_server": {"required": False, "type": "str"},
                "webproxy_profile": {"required": False, "type": "str"}

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
