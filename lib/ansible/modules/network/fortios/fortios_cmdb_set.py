#!/usr/bin/python
# Copyright 2017 Fortinet, Inc.
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
# log_path = /var/log/ansible.log in your conf..

from __future__ import (absolute_import, division, print_function)

__metaclass__ = type

ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'metadata_version': '1.1'}


DOCUMENTATION = '''
---
module: fortios_cmdb_set
short_description: Module to configure all aspects of fortios and fortigate.
description:
    - This module is able to configure a fortios or fortigate by \
    allowing the user to set every configuration endpoint from a fortios \
    or fortigate device. The module transforms the playbook into \
    the needed REST API calls.

version_added: "1.2"
author: "Nicolas Thomas / thomnico / (nthomas at fortinet.com) and \
 Miguel Angel Munoz / mamunozgonzalez / (magonzalez at fortinet.com)"
notes:
    - "Requires fortiosapi library developed by Fortinet"
    - "Run as a local_action in your playbook"
requirements:
    - fortiosapi>=0.9.8
options:
    host:
        description:
            - FortiOS or fortigate IP adress.
        required: true

    username:
        description:
            - FortiOS or fortigate username.
        required: true

    password:
        description:
            - FortiOS or fortigate password.

    vdom:
        description:
            - Virtual domain, among those defined previously. A vdom is a \
            virtual instance of the fortigate that can be configured and \
            used as a different unit.
        default: root

    endpoint:
        description:
            - Defines the resource to be accessed, from the following choice
        required: true
        choices: [system resource, system vdom-resource, alertemail setting, \
         antivirus heuristic, antivirus profile, antivirus quarantine, \
         antivirus settings, application.casi profile, application custom, \
         application internet-service, application internet-service-custom, \
         application list, application name, application rule-settings, \
         certificate ca, certificate crl, certificate local, dlp filepattern, \
         dlp fp-doc-source, dlp fp-sensitivity, dlp sensor, dlp settings, \
         dnsfilter profile, dnsfilter urlfilter, endpoint-control client, \
         endpoint-control forticlient-registration-syn, \
         endpoint-control profile, endpoint-control registered-forticlient, \
         endpoint-control settings, extender-controller extender, \
         firewall.ipmacbinding setting, \
         firewall.ipmacbinding table, firewall.schedule group, \
         firewall.schedule onetime, firewall.schedule recurring, \
         firewall.service category, firewall.service custom, \
         firewall.service group, firewall.shaper per-ip-shaper, \
         firewall.shaper traffic-shaper, firewall.ssl setting, \
         firewall DoS-policy, firewall DoS-policy6, firewall address, \
         firewall address6, firewall addrgrp, firewall addrgrp6, \
         firewall auth-portal, firewall central-snat-map, \
         firewall dnstranslation, firewall explicit-proxy-address, \
         firewall explicit-proxy-addrgrp, firewall explicit-proxy-policy, \
         firewall identity-based-route, firewall interface-policy, \
         firewall interface-policy6, firewall ip-translation, \
         firewall ippool, firewall ippool6, firewall ipv6-eh-filter, \
         firewall ldb-monitor, firewall local-in-policy, \
         firewall local-in-policy6, firewall multicast-address, \
         firewall multicast-address6, firewall multicast-policy, \
         firewall multicast-policy6, firewall policy, firewall policy46, \
         firewall policy6, firewall policy64, firewall profile-group, \
         firewall profile-protocol-options, firewall shaping-policy, \
         firewall sniffer, firewall ssl-server, firewall ssl-ssh-profile, \
         firewall ttl-policy, firewall vip, firewall vip46, firewall vip6, \
         firewall vip64, firewall vipgrp, firewall vipgrp46, firewall vipgrp6, \
         firewall vipgrp64, ftp-proxy explicit, gui console, icap profile, \
         icap server, ips custom, ips dbinfo, ips decoder, ips global, \
         ips rule, ips rule-settings, ips sensor, ips settings, \
         log.disk filter, log.disk setting, log.fortianalyzer filter, \
         log.fortianalyzer override-filter, log.fortianalyzer override-setting, \
         log.fortianalyzer setting, log.fortianalyzer2 filter, \
         log.fortianalyzer2 setting, log.fortianalyzer3 filter, \
         log.fortianalyzer3 setting, log.fortiguard filter, \
         log.fortiguard override-filter, log.fortiguard override-setting, \
         log.fortiguard setting, log.memory filter, log.memory global-setting, \
         log.memory setting, log.null-device filter, log.null-device setting, \
         log.syslogd filter, log.syslogd override-filter, \
         log.syslogd override-setting, log.syslogd setting, \
         log.syslogd2 filter, log.syslogd2 setting, log.syslogd3 filter, \
         log.syslogd3 setting, log.syslogd4 filter, log.syslogd4 setting, \
         log.webtrends filter, log.webtrends setting, log custom-field, \
         log eventfilter, log gui-display, log setting, log threat-weight, \
         netscan assets, netscan settings, report chart, report dataset, \
         report layout, report setting, report style, report theme, \
         router access-list, router access-list6, router aspath-list, \
         router auth-path, router bfd, router bgp, router community-list, \
         router isis, router key-chain, router multicast, \
         router multicast-flow,router multicast6, router ospf, router ospf6, \
         router policy, router policy6, router prefix-list, \
         router prefix-list6, router rip, router ripng, router route-map, \
         router setting, router static, router static6, spamfilter bwl, \
         spamfilter bword, spamfilter dnsbl, spamfilter fortishield, \
         spamfilter iptrust, spamfilter mheader, spamfilter options, \
         spamfilter profile, switch-controller managed-switch, \
         system.autoupdate push-update, system.autoupdate schedule, \
         system.autoupdate tunneling, system.dhcp server, system.dhcp6 server, \
         system.replacemsg admin, system.replacemsg alertmail, \
         system.replacemsg auth, system.replacemsg device-detection-portal, \
         system.replacemsg ec, system.replacemsg fortiguard-wf, \
         system.replacemsg ftp, system.replacemsg http, system.replacemsg mail, \
         system.replacemsg nac-quar, system.replacemsg nntp, \
         system.replacemsg spam, system.replacemsg sslvpn, \
         system.replacemsg traffic-quota, system.replacemsg utm, \
         system.replacemsg webproxy, system.snmp community, \
         system.snmp sysinfo, system.snmp user, system accprofile,system admin, \
         system alarm, system arp-table, system auto-install, \
         system auto-script, system central-management, system cluster-sync, \
         system config backup, system config restore, system console, \
         system custom-language, system ddns, system dedicated-mgmt, \
         system dns, system dns-database, system dns-server, \
         system dscp-based-priority, system email-server, system fips-cc, \
         system fm, system fortiguard, system fortimanager, \
         system fortisandbox, system fsso-polling, system geoip-override, \
         system global, system gre-tunnel, system ha, system ha-monitor, \
         system interface, system ipip-tunnel, system ips-urlfilter-dns, \
         system ipv6-neighbor-cache, system ipv6-tunnel, system link-monitor, \
         system mac-address-table, system management-tunnel, \
         system mobile-tunnel, system nat64, system netflow, \
         system network-visibility, system nst, system ntp, system object-tag, \
         system password-policy, system password-policy-guest-admin, \
         system probe-response, system proxy-arp, system replacemsg-group, \
         system replacemsg-image, system resource-limits, \
         system session-helper,system session-ttl, system settings, \
         system sflow, system sit-tunnel, system sms-server, system storage, \
         system switch-interface, system tos-based-priority, system vdom, \
         system vdom-dns, system vdom-link, system vdom-netflow, \
         system vdom-property, system vdom-radius-server, system vdom-sflow, \
         system virtual-wan-link, system virtual-wire-pair, system wccp, \
         system zone, user adgrp, user device, user device-access-list, \
         user device-category, user device-group, user fortitoken, user fsso, \
         user fsso-polling, user group, user ldap, user local, \
         user password-policy, user peer, user peergrp, user pop3, user radius, \
         user security-exempt-list, user setting, user tacacs+, voip profile, \
         vpn.certificate ca, vpn.certificate crl, vpn.certificate local, \
         vpn.certificate ocsp-server, vpn.certificate remote, \
         vpn.certificate setting, vpn.ipsec concentrator, \
         vpn.ipsec forticlient, vpn.ipsec manualkey, \
         vpn.ipsec manualkey-interface, vpn.ipsec phase1, \
         vpn.ipsec phase1-interface, vpn.ipsec phase2, \
         vpn.ipsec phase2-interface, vpn.ssl.web host-check-software, \
         vpn.ssl.web portal, vpn.ssl.web realm, vpn.ssl.web user-bookmark, \
         vpn.ssl.web user-group-bookmark, vpn.ssl.web virtual-desktop-app-list, \
         vpn.ssl settings, vpn l2tp, vpn pptp, waf main-class, waf profile, \
         waf signature, waf sub-class, wanopt auth-group, wanopt peer, \
         wanopt profile, wanopt settings, wanopt storage, wanopt webcache, \
         web-proxy debug-url, web-proxy explicit, web-proxy forward-server, \
         web-proxy forward-server-group, web-proxy global, web-proxy profile, \
         web-proxy url-match, web-proxy wisp, webfilter content, \
         webfilter content-header, webfilter cookie-ovrd, webfilter fortiguard, \
         webfilter ftgd-local-cat, webfilter ftgd-local-rating, \
         webfilter ftgd-warning, webfilter ips-urlfilter-cache-setting, \
         webfilter ips-urlfilter-setting, webfilter override, \
         webfilter override-user, webfilter profile, webfilter search-engine, \
         webfilter urlfilter, wireless-controller ap-status, \
         wireless-controller global, wireless-controller setting, \
         wireless-controller timers, wireless-controller vap, \
         wireless-controller vap-group, wireless-controller wids-profile, \
         wireless-controller wtp, wireless-controller wtp-group, \
         wireless-controller wtp-profile]

    mkey:
        description:
            - Master key of the resource for those endpoints \
            representing a table

    config_parameters:
        description:
            - Any of the additional parameters that are required by some \
            endpoints to complete the request
        required: true
'''

EXAMPLES = '''
- hosts: localhost
  vars:
   host: "192.168.40.8"
   username: "admin"
   password: ""
   vdom: "root"
  tasks:
  - name: Set static route on the fortigate
    fortios_cmdb_set:
     host:  "{{  host }}"
     username: "{{  username}}"
     password: "{{ password }}"
     vdom:  "{{  vdom }}"
     endpoint: "router static"
     config_parameters:
       seq-num: "8"
       dst: "10.10.32.0 255.255.255.0"
       device: "port2"
       gateway: "192.168.40.252"
  - name:   firewall policy
    fortios_cmdb_set:
     endpoint: "firewall policy"
     host: "{{ host }}"
     username: "{{ username }}"
     password: "{{ password }}"
     vdom:  "{{  vdom }}"
     config_parameters:
        policyid: "66"
        name: "ansible"
        json:
          policyid: "66"
          name: "ansible"
          action: "accept"
          srcintf: [ {"name": "port1"} ]
          dstintf: [{"name":"port2"} ]
          srcaddr: [{"name":"all"} ]
          dstaddr: [{"name":"all"}]
          schedule: "always"
          service:  [{"name":"HTTPS"}]
          logtraffic: "all"
'''

from ansible.module_utils.basic import AnsibleModule
import logging
try:
    from fortiosapi import FortiOSAPI
    HAS_FORTIOSAPI = True
except ImportError:
    HAS_FORTIOSAPI = False

if HAS_FORTIOSAPI:
    fos = FortiOSAPI()
else:
    raise ImportError("fortiosapi module is required")

formatter = logging.Formatter('%(asctime)s %(name)-12s '
                              '%(levelname)-8s %(message)s')
logger = logging.getLogger('fortiosapi')
hdlr = logging.FileHandler('/var/tmp/ansible-fortiosconfig.log')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr)
logger.setLevel(logging.DEBUG)

AVAILABLE_ENDPOINTS = [
    'system resource',
    'system vdom-resource',
    'alertemail setting',
    'antivirus heuristic',
    'antivirus profile',
    'antivirus quarantine',
    'antivirus settings',
    'application.casi profile',
    'application custom',
    'application internet-service',
    'application internet-service-custom',
    'application list',
    'application name',
    'application rule-settings',
    'certificate ca',
    'certificate crl',
    'certificate local',
    'dlp filepattern',
    'dlp fp-doc-source',
    'dlp fp-sensitivity',
    'dlp sensor',
    'dlp settings',
    'dnsfilter profile',
    'dnsfilter urlfilter',
    'endpoint-control client',
    'endpoint-control forticlient-registration-syn',
    'endpoint-control profile',
    'endpoint-control registered-forticlient',
    'endpoint-control settings',
    'extender-controller extender',
    'firewall.ipmacbinding setting',
    'firewall.ipmacbinding table',
    'firewall.schedule group',
    'firewall.schedule onetime',
    'firewall.schedule recurring',
    'firewall.service category',
    'firewall.service custom',
    'firewall.service group',
    'firewall.shaper per-ip-shaper',
    'firewall.shaper traffic-shaper',
    'firewall.ssl setting',
    'firewall DoS-policy',
    'firewall DoS-policy6',
    'firewall address',
    'firewall address6',
    'firewall addrgrp',
    'firewall addrgrp6',
    'firewall auth-portal',
    'firewall central-snat-map',
    'firewall dnstranslation',
    'firewall explicit-proxy-address',
    'firewall explicit-proxy-addrgrp',
    'firewall explicit-proxy-policy',
    'firewall identity-based-route',
    'firewall interface-policy',
    'firewall interface-policy6',
    'firewall ip-translation',
    'firewall ippool',
    'firewall ippool6',
    'firewall ipv6-eh-filter',
    'firewall ldb-monitor',
    'firewall local-in-policy',
    'firewall local-in-policy6',
    'firewall multicast-address',
    'firewall multicast-address6',
    'firewall multicast-policy',
    'firewall multicast-policy6',
    'firewall policy',
    'firewall policy46',
    'firewall policy6',
    'firewall policy64',
    'firewall profile-group',
    'firewall profile-protocol-options',
    'firewall shaping-policy',
    'firewall sniffer',
    'firewall ssl-server',
    'firewall ssl-ssh-profile',
    'firewall ttl-policy',
    'firewall vip',
    'firewall vip46',
    'firewall vip6',
    'firewall vip64',
    'firewall vipgrp',
    'firewall vipgrp46',
    'firewall vipgrp6',
    'firewall vipgrp64',
    'ftp-proxy explicit',
    'gui console',
    'icap profile',
    'icap server',
    'ips custom',
    'ips dbinfo',
    'ips decoder',
    'ips global',
    'ips rule',
    'ips rule-settings',
    'ips sensor',
    'ips settings',
    'log.disk filter',
    'log.disk setting',
    'log.fortianalyzer filter',
    'log.fortianalyzer override-filter',
    'log.fortianalyzer override-setting',
    'log.fortianalyzer setting',
    'log.fortianalyzer2 filter',
    'log.fortianalyzer2 setting',
    'log.fortianalyzer3 filter',
    'log.fortianalyzer3 setting',
    'log.fortiguard filter',
    'log.fortiguard override-filter',
    'log.fortiguard override-setting',
    'log.fortiguard setting',
    'log.memory filter',
    'log.memory global-setting',
    'log.memory setting',
    'log.null-device filter',
    'log.null-device setting',
    'log.syslogd filter',
    'log.syslogd override-filter',
    'log.syslogd override-setting',
    'log.syslogd setting',
    'log.syslogd2 filter',
    'log.syslogd2 setting',
    'log.syslogd3 filter',
    'log.syslogd3 setting',
    'log.syslogd4 filter',
    'log.syslogd4 setting',
    'log.webtrends filter',
    'log.webtrends setting',
    'log custom-field',
    'log eventfilter',
    'log gui-display',
    'log setting',
    'log threat-weight',
    'netscan assets',
    'netscan settings',
    'report chart',
    'report dataset',
    'report layout',
    'report setting',
    'report style',
    'report theme',
    'router access-list',
    'router access-list6',
    'router aspath-list',
    'router auth-path',
    'router bfd',
    'router bgp',
    'router community-list',
    'router isis',
    'router key-chain',
    'router multicast',
    'router multicast-flow',
    'router multicast6',
    'router ospf',
    'router ospf6',
    'router policy',
    'router policy6',
    'router prefix-list',
    'router prefix-list6',
    'router rip',
    'router ripng',
    'router route-map',
    'router setting',
    'router static',
    'router static6',
    'spamfilter bwl',
    'spamfilter bword',
    'spamfilter dnsbl',
    'spamfilter fortishield',
    'spamfilter iptrust',
    'spamfilter mheader',
    'spamfilter options',
    'spamfilter profile',
    'switch-controller managed-switch',
    'system.autoupdate push-update',
    'system.autoupdate schedule',
    'system.autoupdate tunneling',
    'system.dhcp server',
    'system.dhcp6 server',
    'system.replacemsg admin',
    'system.replacemsg alertmail',
    'system.replacemsg auth',
    'system.replacemsg device-detection-portal',
    'system.replacemsg ec',
    'system.replacemsg fortiguard-wf',
    'system.replacemsg ftp',
    'system.replacemsg http',
    'system.replacemsg mail',
    'system.replacemsg nac-quar',
    'system.replacemsg nntp',
    'system.replacemsg spam',
    'system.replacemsg sslvpn',
    'system.replacemsg traffic-quota',
    'system.replacemsg utm',
    'system.replacemsg webproxy',
    'system.snmp community',
    'system.snmp sysinfo',
    'system.snmp user',
    'system accprofile',
    'system admin',
    'system alarm',
    'system arp-table',
    'system auto-install',
    'system auto-script',
    'system central-management',
    'system cluster-sync',
    'system config backup',
    'system config restore',
    'system console',
    'system custom-language',
    'system ddns',
    'system dedicated-mgmt',
    'system dns',
    'system dns-database',
    'system dns-server',
    'system dscp-based-priority',
    'system email-server',
    'system fips-cc',
    'system fm',
    'system fortiguard',
    'system fortimanager',
    'system fortisandbox',
    'system fsso-polling',
    'system geoip-override',
    'system global',
    'system gre-tunnel',
    'system ha',
    'system ha-monitor',
    'system interface',
    'system ipip-tunnel',
    'system ips-urlfilter-dns',
    'system ipv6-neighbor-cache',
    'system ipv6-tunnel',
    'system link-monitor',
    'system mac-address-table',
    'system management-tunnel',
    'system mobile-tunnel',
    'system nat64',
    'system netflow',
    'system network-visibility',
    'system nst',
    'system ntp',
    'system object-tag',
    'system password-policy',
    'system password-policy-guest-admin',
    'system probe-response',
    'system proxy-arp',
    'system replacemsg-group',
    'system replacemsg-image',
    'system resource-limits',
    'system session-helper',
    'system session-ttl',
    'system settings',
    'system sflow',
    'system sit-tunnel',
    'system sms-server',
    'system storage',
    'system switch-interface',
    'system tos-based-priority',
    'system vdom',
    'system vdom-dns',
    'system vdom-link',
    'system vdom-netflow',
    'system vdom-property',
    'system vdom-radius-server',
    'system vdom-sflow',
    'system virtual-wan-link',
    'system virtual-wire-pair',
    'system wccp',
    'system zone',
    'user adgrp',
    'user device',
    'user device-access-list',
    'user device-category',
    'user device-group',
    'user fortitoken',
    'user fsso',
    'user fsso-polling',
    'user group',
    'user ldap',
    'user local',
    'user password-policy',
    'user peer',
    'user peergrp',
    'user pop3',
    'user radius',
    'user security-exempt-list',
    'user setting',
    'user tacacs+',
    'voip profile',
    'vpn.certificate ca',
    'vpn.certificate crl',
    'vpn.certificate local',
    'vpn.certificate ocsp-server',
    'vpn.certificate remote',
    'vpn.certificate setting',
    'vpn.ipsec concentrator',
    'vpn.ipsec forticlient',
    'vpn.ipsec manualkey',
    'vpn.ipsec manualkey-interface',
    'vpn.ipsec phase1',
    'vpn.ipsec phase1-interface',
    'vpn.ipsec phase2',
    'vpn.ipsec phase2-interface',
    'vpn.ssl.web host-check-software',
    'vpn.ssl.web portal',
    'vpn.ssl.web realm',
    'vpn.ssl.web user-bookmark',
    'vpn.ssl.web user-group-bookmark',
    'vpn.ssl.web virtual-desktop-app-list',
    'vpn.ssl settings',
    'vpn l2tp',
    'vpn pptp',
    'waf main-class',
    'waf profile',
    'waf signature',
    'waf sub-class',
    'wanopt auth-group',
    'wanopt peer',
    'wanopt profile',
    'wanopt settings',
    'wanopt storage',
    'wanopt webcache',
    'web-proxy debug-url',
    'web-proxy explicit',
    'web-proxy forward-server',
    'web-proxy forward-server-group',
    'web-proxy global',
    'web-proxy profile',
    'web-proxy url-match',
    'web-proxy wisp',
    'webfilter content',
    'webfilter content-header',
    'webfilter cookie-ovrd',
    'webfilter fortiguard',
    'webfilter ftgd-local-cat',
    'webfilter ftgd-local-rating',
    'webfilter ftgd-warning',
    'webfilter ips-urlfilter-cache-setting',
    'webfilter ips-urlfilter-setting',
    'webfilter override',
    'webfilter override-user',
    'webfilter profile',
    'webfilter search-engine',
    'webfilter urlfilter',
    'wireless-controller ap-status',
    'wireless-controller global',
    'wireless-controller setting',
    'wireless-controller timers',
    'wireless-controller vap',
    'wireless-controller vap-group',
    'wireless-controller wids-profile',
    'wireless-controller wtp',
    'wireless-controller wtp-group',
    'wireless-controller wtp-profile']


def login(data):
    host = data['host']
    username = data['username']
    fos.debug('on')
    fos.login(host, username, '')


def logout():
    fos.logout()


def fortios_cmdb_set(data):
    host = data['host']
    username = data['username']
    password = data['password']
    fos.login(host, username, password)

    functions = data['endpoint'].split()

    resp = fos.set(functions[0],
                   functions[1],
                   vdom=data['vdom'],
                   mkey=data['mkey'] if 'mkey' in data else None,
                   data=data['config_parameters'])
    fos.logout()

    meta = {"status": resp['status'], 'version': resp['version'], }
    if resp['status'] == "success":
        return False, True, meta
    else:
        return True, False, meta


def main():
    if not HAS_FORTIOSAPI:
        module.fail_json(msg="Need FortiOSApi library installed")

    fields = {
        "host": {"required": True, "type": "str"},
        "password": {"required": False, "type": "str"},
        "username": {"required": True, "type": "str"},
        "vdom": {"required": False, "type": "str", "default": "root"},
        "endpoint": {"required": True,
                     "choices": AVAILABLE_ENDPOINTS,
                     "type": "str"},
        "mkey": {"required": False, "type": "str"},
        "config_parameters": {"required": True, "type": "dict"},
    }

    module = AnsibleModule(argument_spec=fields,
                           supports_check_mode=False)
    is_error, has_changed, result = fortios_cmdb_set(module.params)

    if not is_error:
        module.exit_json(changed=has_changed, meta=result)
    else:
        module.fail_json(msg="Error in repo", meta=result)


if __name__ == '__main__':
    main()
