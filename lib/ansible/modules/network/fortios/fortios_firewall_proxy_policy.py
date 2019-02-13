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
module: fortios_firewall_proxy_policy
short_description: Configure proxy policies in Fortinet's FortiOS and FortiGate.
description:
    - This module is able to configure a FortiGate or FortiOS by
      allowing the user to configure firewall feature and proxy_policy category.
      Examples includes all options and need to be adjusted to datasources before usage.
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
    firewall_proxy_policy:
        description:
            - Configure proxy policies.
        default: null
        suboptions:
            state:
                description:
                    - Indicates whether to create or remove the object
                choices:
                    - present
                    - absent
            action:
                description:
                    - Accept or deny traffic matching the policy parameters.
                choices:
                    - accept
                    - deny
                    - redirect
            application-list:
                description:
                    - Name of an existing Application list. Source application.list.name.
            av-profile:
                description:
                    - Name of an existing Antivirus profile. Source antivirus.profile.name.
            comments:
                description:
                    - Optional comments.
            disclaimer:
                description:
                    - "Web proxy disclaimer setting: by domain, policy, or user."
                choices:
                    - disable
                    - domain
                    - policy
                    - user
            dlp-sensor:
                description:
                    - Name of an existing DLP sensor. Source dlp.sensor.name.
            dstaddr:
                description:
                    - Destination address objects.
                suboptions:
                    name:
                        description:
                            - Address name. Source firewall.address.name firewall.addrgrp.name firewall.proxy-address.name firewall.proxy-addrgrp.name
                               firewall.vip.name firewall.vipgrp.name firewall.vip46.name firewall.vipgrp46.name system.external-resource.name.
                        required: true
            dstaddr-negate:
                description:
                    - When enabled, destination addresses match against any address EXCEPT the specified destination addresses.
                choices:
                    - enable
                    - disable
            dstaddr6:
                description:
                    - IPv6 destination address objects.
                suboptions:
                    name:
                        description:
                            - Address name. Source firewall.address6.name firewall.addrgrp6.name firewall.vip6.name firewall.vipgrp6.name firewall.vip64.name
                               firewall.vipgrp64.name system.external-resource.name.
                        required: true
            dstintf:
                description:
                    - Destination interface names.
                suboptions:
                    name:
                        description:
                            - Interface name. Source system.interface.name system.zone.name.
                        required: true
            global-label:
                description:
                    - Global web-based manager visible label.
            groups:
                description:
                    - Names of group objects.
                suboptions:
                    name:
                        description:
                            - Group name. Source user.group.name.
                        required: true
            http-tunnel-auth:
                description:
                    - Enable/disable HTTP tunnel authentication.
                choices:
                    - enable
                    - disable
            icap-profile:
                description:
                    - Name of an existing ICAP profile. Source icap.profile.name.
            internet-service:
                description:
                    - Enable/disable use of Internet Services for this policy. If enabled, destination address and service are not used.
                choices:
                    - enable
                    - disable
            internet-service-custom:
                description:
                    - Custom Internet Service name.
                suboptions:
                    name:
                        description:
                            - Custom name. Source firewall.internet-service-custom.name.
                        required: true
            internet-service-id:
                description:
                    - Internet Service ID.
                suboptions:
                    id:
                        description:
                            - Internet Service ID. Source firewall.internet-service.id.
                        required: true
            internet-service-negate:
                description:
                    - When enabled, Internet Services match against any internet service EXCEPT the selected Internet Service.
                choices:
                    - enable
                    - disable
            ips-sensor:
                description:
                    - Name of an existing IPS sensor. Source ips.sensor.name.
            label:
                description:
                    - VDOM-specific GUI visible label.
            logtraffic:
                description:
                    - Enable/disable logging traffic through the policy.
                choices:
                    - all
                    - utm
                    - disable
            logtraffic-start:
                description:
                    - Enable/disable policy log traffic start.
                choices:
                    - enable
                    - disable
            policyid:
                description:
                    - Policy ID.
                required: true
            poolname:
                description:
                    - Name of IP pool object.
                suboptions:
                    name:
                        description:
                            - IP pool name. Source firewall.ippool.name.
                        required: true
            profile-group:
                description:
                    - Name of profile group. Source firewall.profile-group.name.
            profile-protocol-options:
                description:
                    - Name of an existing Protocol options profile. Source firewall.profile-protocol-options.name.
            profile-type:
                description:
                    - Determine whether the firewall policy allows security profile groups or single profiles only.
                choices:
                    - single
                    - group
            proxy:
                description:
                    - Type of explicit proxy.
                choices:
                    - explicit-web
                    - transparent-web
                    - ftp
                    - ssh
                    - ssh-tunnel
                    - wanopt
            redirect-url:
                description:
                    - Redirect URL for further explicit web proxy processing.
            replacemsg-override-group:
                description:
                    - Authentication replacement message override group. Source system.replacemsg-group.name.
            scan-botnet-connections:
                description:
                    - Enable/disable scanning of connections to Botnet servers.
                choices:
                    - disable
                    - block
                    - monitor
            schedule:
                description:
                    - Name of schedule object. Source firewall.schedule.onetime.name firewall.schedule.recurring.name firewall.schedule.group.name.
            service:
                description:
                    - Name of service objects.
                suboptions:
                    name:
                        description:
                            - Service name. Source firewall.service.custom.name firewall.service.group.name.
                        required: true
            service-negate:
                description:
                    - When enabled, services match against any service EXCEPT the specified destination services.
                choices:
                    - enable
                    - disable
            session-ttl:
                description:
                    - TTL in seconds for sessions accepted by this policy (0 means use the system default session TTL).
            spamfilter-profile:
                description:
                    - Name of an existing Spam filter profile. Source spamfilter.profile.name.
            srcaddr:
                description:
                    - Source address objects (must be set when using Web proxy).
                suboptions:
                    name:
                        description:
                            - Address name. Source firewall.address.name firewall.addrgrp.name firewall.proxy-address.name firewall.proxy-addrgrp.name system
                              .external-resource.name.
                        required: true
            srcaddr-negate:
                description:
                    - When enabled, source addresses match against any address EXCEPT the specified source addresses.
                choices:
                    - enable
                    - disable
            srcaddr6:
                description:
                    - IPv6 source address objects.
                suboptions:
                    name:
                        description:
                            - Address name. Source firewall.address6.name firewall.addrgrp6.name system.external-resource.name.
                        required: true
            srcintf:
                description:
                    - Source interface names.
                suboptions:
                    name:
                        description:
                            - Interface name. Source system.interface.name system.zone.name.
                        required: true
            ssh-filter-profile:
                description:
                    - Name of an existing SSH filter profile. Source ssh-filter.profile.name.
            ssl-ssh-profile:
                description:
                    - Name of an existing SSL SSH profile. Source firewall.ssl-ssh-profile.name.
            status:
                description:
                    - Enable/disable the active status of the policy.
                choices:
                    - enable
                    - disable
            transparent:
                description:
                    - Enable to use the IP address of the client to connect to the server.
                choices:
                    - enable
                    - disable
            users:
                description:
                    - Names of user objects.
                suboptions:
                    name:
                        description:
                            - Group name. Source user.local.name.
                        required: true
            utm-status:
                description:
                    - Enable the use of UTM profiles/sensors/lists.
                choices:
                    - enable
                    - disable
            uuid:
                description:
                    - Universally Unique Identifier (UUID; automatically assigned but can be manually reset).
            waf-profile:
                description:
                    - Name of an existing Web application firewall profile. Source waf.profile.name.
            webcache:
                description:
                    - Enable/disable web caching.
                choices:
                    - enable
                    - disable
            webcache-https:
                description:
                    - Enable/disable web caching for HTTPS (Requires deep-inspection enabled in ssl-ssh-profile).
                choices:
                    - disable
                    - enable
            webfilter-profile:
                description:
                    - Name of an existing Web filter profile. Source webfilter.profile.name.
            webproxy-forward-server:
                description:
                    - Name of web proxy forward server. Source web-proxy.forward-server.name web-proxy.forward-server-group.name.
            webproxy-profile:
                description:
                    - Name of web proxy profile. Source web-proxy.profile.name.
'''

EXAMPLES = '''
- hosts: localhost
  vars:
   host: "192.168.122.40"
   username: "admin"
   password: ""
   vdom: "root"
  tasks:
  - name: Configure proxy policies.
    fortios_firewall_proxy_policy:
      host:  "{{ host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{ vdom }}"
      https: "False"
      firewall_proxy_policy:
        state: "present"
        action: "accept"
        application-list: "<your_own_value> (source application.list.name)"
        av-profile: "<your_own_value> (source antivirus.profile.name)"
        comments: "<your_own_value>"
        disclaimer: "disable"
        dlp-sensor: "<your_own_value> (source dlp.sensor.name)"
        dstaddr:
         -
            name: "default_name_10 (source firewall.address.name firewall.addrgrp.name firewall.proxy-address.name firewall.proxy-addrgrp.name firewall.vip
              .name firewall.vipgrp.name firewall.vip46.name firewall.vipgrp46.name system.external-resource.name)"
        dstaddr-negate: "enable"
        dstaddr6:
         -
            name: "default_name_13 (source firewall.address6.name firewall.addrgrp6.name firewall.vip6.name firewall.vipgrp6.name firewall.vip64.name firewall
              .vipgrp64.name system.external-resource.name)"
        dstintf:
         -
            name: "default_name_15 (source system.interface.name system.zone.name)"
        global-label: "<your_own_value>"
        groups:
         -
            name: "default_name_18 (source user.group.name)"
        http-tunnel-auth: "enable"
        icap-profile: "<your_own_value> (source icap.profile.name)"
        internet-service: "enable"
        internet-service-custom:
         -
            name: "default_name_23 (source firewall.internet-service-custom.name)"
        internet-service-id:
         -
            id:  "25 (source firewall.internet-service.id)"
        internet-service-negate: "enable"
        ips-sensor: "<your_own_value> (source ips.sensor.name)"
        label: "<your_own_value>"
        logtraffic: "all"
        logtraffic-start: "enable"
        policyid: "31"
        poolname:
         -
            name: "default_name_33 (source firewall.ippool.name)"
        profile-group: "<your_own_value> (source firewall.profile-group.name)"
        profile-protocol-options: "<your_own_value> (source firewall.profile-protocol-options.name)"
        profile-type: "single"
        proxy: "explicit-web"
        redirect-url: "<your_own_value>"
        replacemsg-override-group: "<your_own_value> (source system.replacemsg-group.name)"
        scan-botnet-connections: "disable"
        schedule: "<your_own_value> (source firewall.schedule.onetime.name firewall.schedule.recurring.name firewall.schedule.group.name)"
        service:
         -
            name: "default_name_43 (source firewall.service.custom.name firewall.service.group.name)"
        service-negate: "enable"
        session-ttl: "45"
        spamfilter-profile: "<your_own_value> (source spamfilter.profile.name)"
        srcaddr:
         -
            name: "default_name_48 (source firewall.address.name firewall.addrgrp.name firewall.proxy-address.name firewall.proxy-addrgrp.name system
              .external-resource.name)"
        srcaddr-negate: "enable"
        srcaddr6:
         -
            name: "default_name_51 (source firewall.address6.name firewall.addrgrp6.name system.external-resource.name)"
        srcintf:
         -
            name: "default_name_53 (source system.interface.name system.zone.name)"
        ssh-filter-profile: "<your_own_value> (source ssh-filter.profile.name)"
        ssl-ssh-profile: "<your_own_value> (source firewall.ssl-ssh-profile.name)"
        status: "enable"
        transparent: "enable"
        users:
         -
            name: "default_name_59 (source user.local.name)"
        utm-status: "enable"
        uuid: "<your_own_value>"
        waf-profile: "<your_own_value> (source waf.profile.name)"
        webcache: "enable"
        webcache-https: "disable"
        webfilter-profile: "<your_own_value> (source webfilter.profile.name)"
        webproxy-forward-server: "<your_own_value> (source web-proxy.forward-server.name web-proxy.forward-server-group.name)"
        webproxy-profile: "<your_own_value> (source web-proxy.profile.name)"
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


def filter_firewall_proxy_policy_data(json):
    option_list = ['action', 'application-list', 'av-profile',
                   'comments', 'disclaimer', 'dlp-sensor',
                   'dstaddr', 'dstaddr-negate', 'dstaddr6',
                   'dstintf', 'global-label', 'groups',
                   'http-tunnel-auth', 'icap-profile', 'internet-service',
                   'internet-service-custom', 'internet-service-id', 'internet-service-negate',
                   'ips-sensor', 'label', 'logtraffic',
                   'logtraffic-start', 'policyid', 'poolname',
                   'profile-group', 'profile-protocol-options', 'profile-type',
                   'proxy', 'redirect-url', 'replacemsg-override-group',
                   'scan-botnet-connections', 'schedule', 'service',
                   'service-negate', 'session-ttl', 'spamfilter-profile',
                   'srcaddr', 'srcaddr-negate', 'srcaddr6',
                   'srcintf', 'ssh-filter-profile', 'ssl-ssh-profile',
                   'status', 'transparent', 'users',
                   'utm-status', 'uuid', 'waf-profile',
                   'webcache', 'webcache-https', 'webfilter-profile',
                   'webproxy-forward-server', 'webproxy-profile']
    dictionary = {}

    for attribute in option_list:
        if attribute in json and json[attribute] is not None:
            dictionary[attribute] = json[attribute]

    return dictionary


def firewall_proxy_policy(data, fos):
    vdom = data['vdom']
    firewall_proxy_policy_data = data['firewall_proxy_policy']
    filtered_data = filter_firewall_proxy_policy_data(firewall_proxy_policy_data)
    if firewall_proxy_policy_data['state'] == "present":
        return fos.set('firewall',
                       'proxy-policy',
                       data=filtered_data,
                       vdom=vdom)

    elif firewall_proxy_policy_data['state'] == "absent":
        return fos.delete('firewall',
                          'proxy-policy',
                          mkey=filtered_data['policyid'],
                          vdom=vdom)


def fortios_firewall(data, fos):
    login(data)

    methodlist = ['firewall_proxy_policy']
    for method in methodlist:
        if data[method]:
            resp = eval(method)(data, fos)
            break

    fos.logout()
    return not resp['status'] == "success", resp['status'] == "success", resp


def main():
    fields = {
        "host": {"required": True, "type": "str"},
        "username": {"required": True, "type": "str"},
        "password": {"required": False, "type": "str", "no_log": True},
        "vdom": {"required": False, "type": "str", "default": "root"},
        "https": {"required": False, "type": "bool", "default": True},
        "firewall_proxy_policy": {
            "required": False, "type": "dict",
            "options": {
                "state": {"required": True, "type": "str",
                          "choices": ["present", "absent"]},
                "action": {"required": False, "type": "str",
                           "choices": ["accept", "deny", "redirect"]},
                "application-list": {"required": False, "type": "str"},
                "av-profile": {"required": False, "type": "str"},
                "comments": {"required": False, "type": "str"},
                "disclaimer": {"required": False, "type": "str",
                               "choices": ["disable", "domain", "policy",
                                           "user"]},
                "dlp-sensor": {"required": False, "type": "str"},
                "dstaddr": {"required": False, "type": "list",
                            "options": {
                                "name": {"required": True, "type": "str"}
                            }},
                "dstaddr-negate": {"required": False, "type": "str",
                                   "choices": ["enable", "disable"]},
                "dstaddr6": {"required": False, "type": "list",
                             "options": {
                                 "name": {"required": True, "type": "str"}
                             }},
                "dstintf": {"required": False, "type": "list",
                            "options": {
                                "name": {"required": True, "type": "str"}
                            }},
                "global-label": {"required": False, "type": "str"},
                "groups": {"required": False, "type": "list",
                           "options": {
                               "name": {"required": True, "type": "str"}
                           }},
                "http-tunnel-auth": {"required": False, "type": "str",
                                     "choices": ["enable", "disable"]},
                "icap-profile": {"required": False, "type": "str"},
                "internet-service": {"required": False, "type": "str",
                                     "choices": ["enable", "disable"]},
                "internet-service-custom": {"required": False, "type": "list",
                                            "options": {
                                                "name": {"required": True, "type": "str"}
                                            }},
                "internet-service-id": {"required": False, "type": "list",
                                        "options": {
                                            "id": {"required": True, "type": "int"}
                                        }},
                "internet-service-negate": {"required": False, "type": "str",
                                            "choices": ["enable", "disable"]},
                "ips-sensor": {"required": False, "type": "str"},
                "label": {"required": False, "type": "str"},
                "logtraffic": {"required": False, "type": "str",
                               "choices": ["all", "utm", "disable"]},
                "logtraffic-start": {"required": False, "type": "str",
                                     "choices": ["enable", "disable"]},
                "policyid": {"required": True, "type": "int"},
                "poolname": {"required": False, "type": "list",
                             "options": {
                                 "name": {"required": True, "type": "str"}
                             }},
                "profile-group": {"required": False, "type": "str"},
                "profile-protocol-options": {"required": False, "type": "str"},
                "profile-type": {"required": False, "type": "str",
                                 "choices": ["single", "group"]},
                "proxy": {"required": False, "type": "str",
                          "choices": ["explicit-web", "transparent-web", "ftp",
                                      "ssh", "ssh-tunnel", "wanopt"]},
                "redirect-url": {"required": False, "type": "str"},
                "replacemsg-override-group": {"required": False, "type": "str"},
                "scan-botnet-connections": {"required": False, "type": "str",
                                            "choices": ["disable", "block", "monitor"]},
                "schedule": {"required": False, "type": "str"},
                "service": {"required": False, "type": "list",
                            "options": {
                                "name": {"required": True, "type": "str"}
                            }},
                "service-negate": {"required": False, "type": "str",
                                   "choices": ["enable", "disable"]},
                "session-ttl": {"required": False, "type": "int"},
                "spamfilter-profile": {"required": False, "type": "str"},
                "srcaddr": {"required": False, "type": "list",
                            "options": {
                                "name": {"required": True, "type": "str"}
                            }},
                "srcaddr-negate": {"required": False, "type": "str",
                                   "choices": ["enable", "disable"]},
                "srcaddr6": {"required": False, "type": "list",
                             "options": {
                                 "name": {"required": True, "type": "str"}
                             }},
                "srcintf": {"required": False, "type": "list",
                            "options": {
                                "name": {"required": True, "type": "str"}
                            }},
                "ssh-filter-profile": {"required": False, "type": "str"},
                "ssl-ssh-profile": {"required": False, "type": "str"},
                "status": {"required": False, "type": "str",
                           "choices": ["enable", "disable"]},
                "transparent": {"required": False, "type": "str",
                                "choices": ["enable", "disable"]},
                "users": {"required": False, "type": "list",
                          "options": {
                              "name": {"required": True, "type": "str"}
                          }},
                "utm-status": {"required": False, "type": "str",
                               "choices": ["enable", "disable"]},
                "uuid": {"required": False, "type": "str"},
                "waf-profile": {"required": False, "type": "str"},
                "webcache": {"required": False, "type": "str",
                             "choices": ["enable", "disable"]},
                "webcache-https": {"required": False, "type": "str",
                                   "choices": ["disable", "enable"]},
                "webfilter-profile": {"required": False, "type": "str"},
                "webproxy-forward-server": {"required": False, "type": "str"},
                "webproxy-profile": {"required": False, "type": "str"}

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

    is_error, has_changed, result = fortios_firewall(module.params, fos)

    if not is_error:
        module.exit_json(changed=has_changed, meta=result)
    else:
        module.fail_json(msg="Error in repo", meta=result)


if __name__ == '__main__':
    main()
