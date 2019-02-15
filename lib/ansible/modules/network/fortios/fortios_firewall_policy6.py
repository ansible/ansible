#!/usr/bin/python
from __future__ import (absolute_import, division, print_function)
# Copyright 2018 Fortinet, Inc.
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
module: fortios_firewall_policy6
short_description: Configure IPv6 policies in Fortinet's FortiOS and FortiGate.
description:
    - This module is able to configure a FortiGate or FortiOS by
      allowing the user to configure firewall feature and policy6 category.
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
        default: false
    firewall_policy6:
        description:
            - Configure IPv6 policies.
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
                    - Policy action (allow/deny/ipsec).
                choices:
                    - accept
                    - deny
                    - ipsec
            app-category:
                description:
                    - Application category ID list.
                suboptions:
                    id:
                        description:
                            - Category IDs.
                        required: true
            app-group:
                description:
                    - Application group names.
                suboptions:
                    name:
                        description:
                            - Application group names. Source application.group.name.
                        required: true
            application:
                description:
                    - Application ID list.
                suboptions:
                    id:
                        description:
                            - Application IDs.
                        required: true
            application-list:
                description:
                    - Name of an existing Application list. Source application.list.name.
            av-profile:
                description:
                    - Name of an existing Antivirus profile. Source antivirus.profile.name.
            comments:
                description:
                    - Comment.
            custom-log-fields:
                description:
                    - Log field index numbers to append custom log fields to log messages for this policy.
                suboptions:
                    field-id:
                        description:
                            - Custom log field. Source log.custom-field.id.
                        required: true
            devices:
                description:
                    - Names of devices or device groups that can be matched by the policy.
                suboptions:
                    name:
                        description:
                            - Device or group name. Source user.device.alias user.device-group.name user.device-category.name.
                        required: true
            diffserv-forward:
                description:
                    - Enable to change packet's DiffServ values to the specified diffservcode-forward value.
                choices:
                    - enable
                    - disable
            diffserv-reverse:
                description:
                    - Enable to change packet's reverse (reply) DiffServ values to the specified diffservcode-rev value.
                choices:
                    - enable
                    - disable
            diffservcode-forward:
                description:
                    - Change packet's DiffServ to this value.
            diffservcode-rev:
                description:
                    - Change packet's reverse (reply) DiffServ to this value.
            dlp-sensor:
                description:
                    - Name of an existing DLP sensor. Source dlp.sensor.name.
            dscp-match:
                description:
                    - Enable DSCP check.
                choices:
                    - enable
                    - disable
            dscp-negate:
                description:
                    - Enable negated DSCP match.
                choices:
                    - enable
                    - disable
            dscp-value:
                description:
                    - DSCP value.
            dsri:
                description:
                    - Enable DSRI to ignore HTTP server responses.
                choices:
                    - enable
                    - disable
            dstaddr:
                description:
                    - Destination address and address group names.
                suboptions:
                    name:
                        description:
                            - Address name. Source firewall.address6.name firewall.addrgrp6.name firewall.vip6.name firewall.vipgrp6.name.
                        required: true
            dstaddr-negate:
                description:
                    - When enabled dstaddr specifies what the destination address must NOT be.
                choices:
                    - enable
                    - disable
            dstintf:
                description:
                    - Outgoing (egress) interface.
                suboptions:
                    name:
                        description:
                            - Interface name. Source system.interface.name system.zone.name.
                        required: true
            firewall-session-dirty:
                description:
                    - How to handle sessions if the configuration of this firewall policy changes.
                choices:
                    - check-all
                    - check-new
            fixedport:
                description:
                    - Enable to prevent source NAT from changing a session's source port.
                choices:
                    - enable
                    - disable
            global-label:
                description:
                    - Label for the policy that appears when the GUI is in Global View mode.
            groups:
                description:
                    - Names of user groups that can authenticate with this policy.
                suboptions:
                    name:
                        description:
                            - Group name. Source user.group.name.
                        required: true
            icap-profile:
                description:
                    - Name of an existing ICAP profile. Source icap.profile.name.
            inbound:
                description:
                    - "Policy-based IPsec VPN: only traffic from the remote network can initiate a VPN."
                choices:
                    - enable
                    - disable
            ippool:
                description:
                    - Enable to use IP Pools for source NAT.
                choices:
                    - enable
                    - disable
            ips-sensor:
                description:
                    - Name of an existing IPS sensor. Source ips.sensor.name.
            label:
                description:
                    - Label for the policy that appears when the GUI is in Section View mode.
            logtraffic:
                description:
                    - Enable or disable logging. Log all sessions or security profile sessions.
                choices:
                    - all
                    - utm
                    - disable
            logtraffic-start:
                description:
                    - Record logs when a session starts and ends.
                choices:
                    - enable
                    - disable
            name:
                description:
                    - Policy name.
            nat:
                description:
                    - Enable/disable source NAT.
                choices:
                    - enable
                    - disable
            natinbound:
                description:
                    - "Policy-based IPsec VPN: apply destination NAT to inbound traffic."
                choices:
                    - enable
                    - disable
            natoutbound:
                description:
                    - "Policy-based IPsec VPN: apply source NAT to outbound traffic."
                choices:
                    - enable
                    - disable
            outbound:
                description:
                    - "Policy-based IPsec VPN: only traffic from the internal network can initiate a VPN."
                choices:
                    - enable
                    - disable
            per-ip-shaper:
                description:
                    - Per-IP traffic shaper. Source firewall.shaper.per-ip-shaper.name.
            policyid:
                description:
                    - Policy ID.
                required: true
            poolname:
                description:
                    - IP Pool names.
                suboptions:
                    name:
                        description:
                            - IP pool name. Source firewall.ippool6.name.
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
            replacemsg-override-group:
                description:
                    - Override the default replacement message group for this policy. Source system.replacemsg-group.name.
            rsso:
                description:
                    - Enable/disable RADIUS single sign-on (RSSO).
                choices:
                    - enable
                    - disable
            schedule:
                description:
                    - Schedule name. Source firewall.schedule.onetime.name firewall.schedule.recurring.name firewall.schedule.group.name.
            send-deny-packet:
                description:
                    - Enable/disable return of deny-packet.
                choices:
                    - enable
                    - disable
            service:
                description:
                    - Service and service group names.
                suboptions:
                    name:
                        description:
                            - Address name. Source firewall.service.custom.name firewall.service.group.name.
                        required: true
            service-negate:
                description:
                    - When enabled service specifies what the service must NOT be.
                choices:
                    - enable
                    - disable
            session-ttl:
                description:
                    - Session TTL in seconds for sessions accepted by this policy. 0 means use the system default session TTL.
            spamfilter-profile:
                description:
                    - Name of an existing Spam filter profile. Source spamfilter.profile.name.
            srcaddr:
                description:
                    - Source address and address group names.
                suboptions:
                    name:
                        description:
                            - Address name. Source firewall.address6.name firewall.addrgrp6.name.
                        required: true
            srcaddr-negate:
                description:
                    - When enabled srcaddr specifies what the source address must NOT be.
                choices:
                    - enable
                    - disable
            srcintf:
                description:
                    - Incoming (ingress) interface.
                suboptions:
                    name:
                        description:
                            - Interface name. Source system.zone.name system.interface.name.
                        required: true
            ssh-filter-profile:
                description:
                    - Name of an existing SSH filter profile. Source ssh-filter.profile.name.
            ssl-mirror:
                description:
                    - Enable to copy decrypted SSL traffic to a FortiGate interface (called SSL mirroring).
                choices:
                    - enable
                    - disable
            ssl-mirror-intf:
                description:
                    - SSL mirror interface name.
                suboptions:
                    name:
                        description:
                            - Interface name. Source system.zone.name system.interface.name.
                        required: true
            ssl-ssh-profile:
                description:
                    - Name of an existing SSL SSH profile. Source firewall.ssl-ssh-profile.name.
            status:
                description:
                    - Enable or disable this policy.
                choices:
                    - enable
                    - disable
            tcp-mss-receiver:
                description:
                    - Receiver TCP maximum segment size (MSS).
            tcp-mss-sender:
                description:
                    - Sender TCP maximum segment size (MSS).
            tcp-session-without-syn:
                description:
                    - Enable/disable creation of TCP session without SYN flag.
                choices:
                    - all
                    - data-only
                    - disable
            timeout-send-rst:
                description:
                    - Enable/disable sending RST packets when TCP sessions expire.
                choices:
                    - enable
                    - disable
            traffic-shaper:
                description:
                    - Reverse traffic shaper. Source firewall.shaper.traffic-shaper.name.
            traffic-shaper-reverse:
                description:
                    - Reverse traffic shaper. Source firewall.shaper.traffic-shaper.name.
            url-category:
                description:
                    - URL category ID list.
                suboptions:
                    id:
                        description:
                            - URL category ID.
                        required: true
            users:
                description:
                    - Names of individual users that can authenticate with this policy.
                suboptions:
                    name:
                        description:
                            - Names of individual users that can authenticate with this policy. Source user.local.name.
                        required: true
            utm-status:
                description:
                    - Enable AV/web/ips protection profile.
                choices:
                    - enable
                    - disable
            uuid:
                description:
                    - Universally Unique Identifier (UUID; automatically assigned but can be manually reset).
            vlan-cos-fwd:
                description:
                    - "VLAN forward direction user priority: 255 passthrough, 0 lowest, 7 highest"
            vlan-cos-rev:
                description:
                    - "VLAN reverse direction user priority: 255 passthrough, 0 lowest, 7 highest"
            vlan-filter:
                description:
                    - Set VLAN filters.
            voip-profile:
                description:
                    - Name of an existing VoIP profile. Source voip.profile.name.
            vpntunnel:
                description:
                    - "Policy-based IPsec VPN: name of the IPsec VPN Phase 1. Source vpn.ipsec.phase1.name vpn.ipsec.manualkey.name."
            webfilter-profile:
                description:
                    - Name of an existing Web filter profile. Source webfilter.profile.name.
'''

EXAMPLES = '''
- hosts: localhost
  vars:
   host: "192.168.122.40"
   username: "admin"
   password: ""
   vdom: "root"
  tasks:
  - name: Configure IPv6 policies.
    fortios_firewall_policy6:
      host:  "{{ host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{ vdom }}"
      firewall_policy6:
        state: "present"
        action: "accept"
        app-category:
         -
            id:  "5"
        app-group:
         -
            name: "default_name_7 (source application.group.name)"
        application:
         -
            id:  "9"
        application-list: "<your_own_value> (source application.list.name)"
        av-profile: "<your_own_value> (source antivirus.profile.name)"
        comments: "<your_own_value>"
        custom-log-fields:
         -
            field-id: "<your_own_value> (source log.custom-field.id)"
        devices:
         -
            name: "default_name_16 (source user.device.alias user.device-group.name user.device-category.name)"
        diffserv-forward: "enable"
        diffserv-reverse: "enable"
        diffservcode-forward: "<your_own_value>"
        diffservcode-rev: "<your_own_value>"
        dlp-sensor: "<your_own_value> (source dlp.sensor.name)"
        dscp-match: "enable"
        dscp-negate: "enable"
        dscp-value: "<your_own_value>"
        dsri: "enable"
        dstaddr:
         -
            name: "default_name_27 (source firewall.address6.name firewall.addrgrp6.name firewall.vip6.name firewall.vipgrp6.name)"
        dstaddr-negate: "enable"
        dstintf:
         -
            name: "default_name_30 (source system.interface.name system.zone.name)"
        firewall-session-dirty: "check-all"
        fixedport: "enable"
        global-label: "<your_own_value>"
        groups:
         -
            name: "default_name_35 (source user.group.name)"
        icap-profile: "<your_own_value> (source icap.profile.name)"
        inbound: "enable"
        ippool: "enable"
        ips-sensor: "<your_own_value> (source ips.sensor.name)"
        label: "<your_own_value>"
        logtraffic: "all"
        logtraffic-start: "enable"
        name: "default_name_43"
        nat: "enable"
        natinbound: "enable"
        natoutbound: "enable"
        outbound: "enable"
        per-ip-shaper: "<your_own_value> (source firewall.shaper.per-ip-shaper.name)"
        policyid: "49"
        poolname:
         -
            name: "default_name_51 (source firewall.ippool6.name)"
        profile-group: "<your_own_value> (source firewall.profile-group.name)"
        profile-protocol-options: "<your_own_value> (source firewall.profile-protocol-options.name)"
        profile-type: "single"
        replacemsg-override-group: "<your_own_value> (source system.replacemsg-group.name)"
        rsso: "enable"
        schedule: "<your_own_value> (source firewall.schedule.onetime.name firewall.schedule.recurring.name firewall.schedule.group.name)"
        send-deny-packet: "enable"
        service:
         -
            name: "default_name_60 (source firewall.service.custom.name firewall.service.group.name)"
        service-negate: "enable"
        session-ttl: "62"
        spamfilter-profile: "<your_own_value> (source spamfilter.profile.name)"
        srcaddr:
         -
            name: "default_name_65 (source firewall.address6.name firewall.addrgrp6.name)"
        srcaddr-negate: "enable"
        srcintf:
         -
            name: "default_name_68 (source system.zone.name system.interface.name)"
        ssh-filter-profile: "<your_own_value> (source ssh-filter.profile.name)"
        ssl-mirror: "enable"
        ssl-mirror-intf:
         -
            name: "default_name_72 (source system.zone.name system.interface.name)"
        ssl-ssh-profile: "<your_own_value> (source firewall.ssl-ssh-profile.name)"
        status: "enable"
        tcp-mss-receiver: "75"
        tcp-mss-sender: "76"
        tcp-session-without-syn: "all"
        timeout-send-rst: "enable"
        traffic-shaper: "<your_own_value> (source firewall.shaper.traffic-shaper.name)"
        traffic-shaper-reverse: "<your_own_value> (source firewall.shaper.traffic-shaper.name)"
        url-category:
         -
            id:  "82"
        users:
         -
            name: "default_name_84 (source user.local.name)"
        utm-status: "enable"
        uuid: "<your_own_value>"
        vlan-cos-fwd: "87"
        vlan-cos-rev: "88"
        vlan-filter: "<your_own_value>"
        voip-profile: "<your_own_value> (source voip.profile.name)"
        vpntunnel: "<your_own_value> (source vpn.ipsec.phase1.name vpn.ipsec.manualkey.name)"
        webfilter-profile: "<your_own_value> (source webfilter.profile.name)"
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
  sample: "key1"
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


def filter_firewall_policy6_data(json):
    option_list = ['action', 'app-category', 'app-group',
                   'application', 'application-list', 'av-profile',
                   'comments', 'custom-log-fields', 'devices',
                   'diffserv-forward', 'diffserv-reverse', 'diffservcode-forward',
                   'diffservcode-rev', 'dlp-sensor', 'dscp-match',
                   'dscp-negate', 'dscp-value', 'dsri',
                   'dstaddr', 'dstaddr-negate', 'dstintf',
                   'firewall-session-dirty', 'fixedport', 'global-label',
                   'groups', 'icap-profile', 'inbound',
                   'ippool', 'ips-sensor', 'label',
                   'logtraffic', 'logtraffic-start', 'name',
                   'nat', 'natinbound', 'natoutbound',
                   'outbound', 'per-ip-shaper', 'policyid',
                   'poolname', 'profile-group', 'profile-protocol-options',
                   'profile-type', 'replacemsg-override-group', 'rsso',
                   'schedule', 'send-deny-packet', 'service',
                   'service-negate', 'session-ttl', 'spamfilter-profile',
                   'srcaddr', 'srcaddr-negate', 'srcintf',
                   'ssh-filter-profile', 'ssl-mirror', 'ssl-mirror-intf',
                   'ssl-ssh-profile', 'status', 'tcp-mss-receiver',
                   'tcp-mss-sender', 'tcp-session-without-syn', 'timeout-send-rst',
                   'traffic-shaper', 'traffic-shaper-reverse', 'url-category',
                   'users', 'utm-status', 'uuid',
                   'vlan-cos-fwd', 'vlan-cos-rev', 'vlan-filter',
                   'voip-profile', 'vpntunnel', 'webfilter-profile']
    dictionary = {}

    for attribute in option_list:
        if attribute in json and json[attribute] is not None:
            dictionary[attribute] = json[attribute]

    return dictionary


def firewall_policy6(data, fos):
    vdom = data['vdom']
    firewall_policy6_data = data['firewall_policy6']
    filtered_data = filter_firewall_policy6_data(firewall_policy6_data)
    if firewall_policy6_data['state'] == "present":
        return fos.set('firewall',
                       'policy6',
                       data=filtered_data,
                       vdom=vdom)

    elif firewall_policy6_data['state'] == "absent":
        return fos.delete('firewall',
                          'policy6',
                          mkey=filtered_data['policyid'],
                          vdom=vdom)


def fortios_firewall(data, fos):
    login(data)

    methodlist = ['firewall_policy6']
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
        "https": {"required": False, "type": "bool", "default": "False"},
        "firewall_policy6": {
            "required": False, "type": "dict",
            "options": {
                "state": {"required": True, "type": "str",
                          "choices": ["present", "absent"]},
                "action": {"required": False, "type": "str",
                           "choices": ["accept", "deny", "ipsec"]},
                "app-category": {"required": False, "type": "list",
                                 "options": {
                                     "id": {"required": True, "type": "int"}
                                 }},
                "app-group": {"required": False, "type": "list",
                              "options": {
                                  "name": {"required": True, "type": "str"}
                              }},
                "application": {"required": False, "type": "list",
                                "options": {
                                    "id": {"required": True, "type": "int"}
                                }},
                "application-list": {"required": False, "type": "str"},
                "av-profile": {"required": False, "type": "str"},
                "comments": {"required": False, "type": "str"},
                "custom-log-fields": {"required": False, "type": "list",
                                      "options": {
                                          "field-id": {"required": True, "type": "str"}
                                      }},
                "devices": {"required": False, "type": "list",
                            "options": {
                                "name": {"required": True, "type": "str"}
                            }},
                "diffserv-forward": {"required": False, "type": "str",
                                     "choices": ["enable", "disable"]},
                "diffserv-reverse": {"required": False, "type": "str",
                                     "choices": ["enable", "disable"]},
                "diffservcode-forward": {"required": False, "type": "str"},
                "diffservcode-rev": {"required": False, "type": "str"},
                "dlp-sensor": {"required": False, "type": "str"},
                "dscp-match": {"required": False, "type": "str",
                               "choices": ["enable", "disable"]},
                "dscp-negate": {"required": False, "type": "str",
                                "choices": ["enable", "disable"]},
                "dscp-value": {"required": False, "type": "str"},
                "dsri": {"required": False, "type": "str",
                         "choices": ["enable", "disable"]},
                "dstaddr": {"required": False, "type": "list",
                            "options": {
                                "name": {"required": True, "type": "str"}
                            }},
                "dstaddr-negate": {"required": False, "type": "str",
                                   "choices": ["enable", "disable"]},
                "dstintf": {"required": False, "type": "list",
                            "options": {
                                "name": {"required": True, "type": "str"}
                            }},
                "firewall-session-dirty": {"required": False, "type": "str",
                                           "choices": ["check-all", "check-new"]},
                "fixedport": {"required": False, "type": "str",
                              "choices": ["enable", "disable"]},
                "global-label": {"required": False, "type": "str"},
                "groups": {"required": False, "type": "list",
                           "options": {
                               "name": {"required": True, "type": "str"}
                           }},
                "icap-profile": {"required": False, "type": "str"},
                "inbound": {"required": False, "type": "str",
                            "choices": ["enable", "disable"]},
                "ippool": {"required": False, "type": "str",
                           "choices": ["enable", "disable"]},
                "ips-sensor": {"required": False, "type": "str"},
                "label": {"required": False, "type": "str"},
                "logtraffic": {"required": False, "type": "str",
                               "choices": ["all", "utm", "disable"]},
                "logtraffic-start": {"required": False, "type": "str",
                                     "choices": ["enable", "disable"]},
                "name": {"required": False, "type": "str"},
                "nat": {"required": False, "type": "str",
                        "choices": ["enable", "disable"]},
                "natinbound": {"required": False, "type": "str",
                               "choices": ["enable", "disable"]},
                "natoutbound": {"required": False, "type": "str",
                                "choices": ["enable", "disable"]},
                "outbound": {"required": False, "type": "str",
                             "choices": ["enable", "disable"]},
                "per-ip-shaper": {"required": False, "type": "str"},
                "policyid": {"required": True, "type": "int"},
                "poolname": {"required": False, "type": "list",
                             "options": {
                                 "name": {"required": True, "type": "str"}
                             }},
                "profile-group": {"required": False, "type": "str"},
                "profile-protocol-options": {"required": False, "type": "str"},
                "profile-type": {"required": False, "type": "str",
                                 "choices": ["single", "group"]},
                "replacemsg-override-group": {"required": False, "type": "str"},
                "rsso": {"required": False, "type": "str",
                         "choices": ["enable", "disable"]},
                "schedule": {"required": False, "type": "str"},
                "send-deny-packet": {"required": False, "type": "str",
                                     "choices": ["enable", "disable"]},
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
                "srcintf": {"required": False, "type": "list",
                            "options": {
                                "name": {"required": True, "type": "str"}
                            }},
                "ssh-filter-profile": {"required": False, "type": "str"},
                "ssl-mirror": {"required": False, "type": "str",
                               "choices": ["enable", "disable"]},
                "ssl-mirror-intf": {"required": False, "type": "list",
                                    "options": {
                                        "name": {"required": True, "type": "str"}
                                    }},
                "ssl-ssh-profile": {"required": False, "type": "str"},
                "status": {"required": False, "type": "str",
                           "choices": ["enable", "disable"]},
                "tcp-mss-receiver": {"required": False, "type": "int"},
                "tcp-mss-sender": {"required": False, "type": "int"},
                "tcp-session-without-syn": {"required": False, "type": "str",
                                            "choices": ["all", "data-only", "disable"]},
                "timeout-send-rst": {"required": False, "type": "str",
                                     "choices": ["enable", "disable"]},
                "traffic-shaper": {"required": False, "type": "str"},
                "traffic-shaper-reverse": {"required": False, "type": "str"},
                "url-category": {"required": False, "type": "list",
                                 "options": {
                                     "id": {"required": True, "type": "int"}
                                 }},
                "users": {"required": False, "type": "list",
                          "options": {
                              "name": {"required": True, "type": "str"}
                          }},
                "utm-status": {"required": False, "type": "str",
                               "choices": ["enable", "disable"]},
                "uuid": {"required": False, "type": "str"},
                "vlan-cos-fwd": {"required": False, "type": "int"},
                "vlan-cos-rev": {"required": False, "type": "int"},
                "vlan-filter": {"required": False, "type": "str"},
                "voip-profile": {"required": False, "type": "str"},
                "vpntunnel": {"required": False, "type": "str"},
                "webfilter-profile": {"required": False, "type": "str"}

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
