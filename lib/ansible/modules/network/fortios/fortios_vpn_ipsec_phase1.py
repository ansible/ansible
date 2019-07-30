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
module: fortios_vpn_ipsec_phase1
short_description: Configure VPN remote gateway in Fortinet's FortiOS and FortiGate.
description:
    - This module is able to configure a FortiGate or FortiOS by allowing the
      user to set and modify vpn_ipsec feature and phase1 category.
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
    vpn_ipsec_phase1:
        description:
            - Configure VPN remote gateway.
        default: null
        suboptions:
            state:
                description:
                    - Indicates whether to create or remove the object
                choices:
                    - present
                    - absent
            acct-verify:
                description:
                    - Enable/disable verification of RADIUS accounting record.
                choices:
                    - enable
                    - disable
            add-gw-route:
                description:
                    - Enable/disable automatically add a route to the remote gateway.
                choices:
                    - enable
                    - disable
            add-route:
                description:
                    - Enable/disable control addition of a route to peer destination selector.
                choices:
                    - disable
                    - enable
            assign-ip:
                description:
                    - Enable/disable assignment of IP to IPsec interface via configuration method.
                choices:
                    - disable
                    - enable
            assign-ip-from:
                description:
                    - Method by which the IP address will be assigned.
                choices:
                    - range
                    - usrgrp
                    - dhcp
                    - name
            authmethod:
                description:
                    - Authentication method.
                choices:
                    - psk
                    - signature
            authmethod-remote:
                description:
                    - Authentication method (remote side).
                choices:
                    - psk
                    - signature
            authpasswd:
                description:
                    - XAuth password (max 35 characters).
            authusr:
                description:
                    - XAuth user name.
            authusrgrp:
                description:
                    - Authentication user group. Source user.group.name.
            auto-negotiate:
                description:
                    - Enable/disable automatic initiation of IKE SA negotiation.
                choices:
                    - enable
                    - disable
            backup-gateway:
                description:
                    - Instruct unity clients about the backup gateway address(es).
                suboptions:
                    address:
                        description:
                            - Address of backup gateway.
                        required: true
            banner:
                description:
                    - Message that unity client should display after connecting.
            cert-id-validation:
                description:
                    - Enable/disable cross validation of peer ID and the identity in the peer's certificate as specified in RFC 4945.
                choices:
                    - enable
                    - disable
            certificate:
                description:
                    - Names of up to 4 signed personal certificates.
                suboptions:
                    name:
                        description:
                            - Certificate name. Source vpn.certificate.local.name.
                        required: true
            childless-ike:
                description:
                    - Enable/disable childless IKEv2 initiation (RFC 6023).
                choices:
                    - enable
                    - disable
            client-auto-negotiate:
                description:
                    - Enable/disable allowing the VPN client to bring up the tunnel when there is no traffic.
                choices:
                    - disable
                    - enable
            client-keep-alive:
                description:
                    - Enable/disable allowing the VPN client to keep the tunnel up when there is no traffic.
                choices:
                    - disable
                    - enable
            comments:
                description:
                    - Comment.
            dhgrp:
                description:
                    - DH group.
                choices:
                    - 1
                    - 2
                    - 5
                    - 14
                    - 15
                    - 16
                    - 17
                    - 18
                    - 19
                    - 20
                    - 21
                    - 27
                    - 28
                    - 29
                    - 30
                    - 31
            digital-signature-auth:
                description:
                    - Enable/disable IKEv2 Digital Signature Authentication (RFC 7427).
                choices:
                    - enable
                    - disable
            distance:
                description:
                    - Distance for routes added by IKE (1 - 255).
            dns-mode:
                description:
                    - DNS server mode.
                choices:
                    - manual
                    - auto
            domain:
                description:
                    - Instruct unity clients about the default DNS domain.
            dpd:
                description:
                    - Dead Peer Detection mode.
                choices:
                    - disable
                    - on-idle
                    - on-demand
            dpd-retrycount:
                description:
                    - Number of DPD retry attempts.
            dpd-retryinterval:
                description:
                    - DPD retry interval.
            eap:
                description:
                    - Enable/disable IKEv2 EAP authentication.
                choices:
                    - enable
                    - disable
            eap-identity:
                description:
                    - IKEv2 EAP peer identity type.
                choices:
                    - use-id-payload
                    - send-request
            enforce-unique-id:
                description:
                    - Enable/disable peer ID uniqueness check.
                choices:
                    - disable
                    - keep-new
                    - keep-old
            forticlient-enforcement:
                description:
                    - Enable/disable FortiClient enforcement.
                choices:
                    - enable
                    - disable
            fragmentation:
                description:
                    - Enable/disable fragment IKE message on re-transmission.
                choices:
                    - enable
                    - disable
            fragmentation-mtu:
                description:
                    - IKE fragmentation MTU (500 - 16000).
            group-authentication:
                description:
                    - Enable/disable IKEv2 IDi group authentication.
                choices:
                    - enable
                    - disable
            group-authentication-secret:
                description:
                    - Password for IKEv2 IDi group authentication.  (ASCII string or hexadecimal indicated by a leading 0x.)
            ha-sync-esp-seqno:
                description:
                    - Enable/disable sequence number jump ahead for IPsec HA.
                choices:
                    - enable
                    - disable
            idle-timeout:
                description:
                    - Enable/disable IPsec tunnel idle timeout.
                choices:
                    - enable
                    - disable
            idle-timeoutinterval:
                description:
                    - IPsec tunnel idle timeout in minutes (5 - 43200).
            ike-version:
                description:
                    - IKE protocol version.
                choices:
                    - 1
                    - 2
            include-local-lan:
                description:
                    - Enable/disable allow local LAN access on unity clients.
                choices:
                    - disable
                    - enable
            interface:
                description:
                    - Local physical, aggregate, or VLAN outgoing interface. Source system.interface.name.
            ipv4-dns-server1:
                description:
                    - IPv4 DNS server 1.
            ipv4-dns-server2:
                description:
                    - IPv4 DNS server 2.
            ipv4-dns-server3:
                description:
                    - IPv4 DNS server 3.
            ipv4-end-ip:
                description:
                    - End of IPv4 range.
            ipv4-exclude-range:
                description:
                    - Configuration Method IPv4 exclude ranges.
                suboptions:
                    end-ip:
                        description:
                            - End of IPv4 exclusive range.
                    id:
                        description:
                            - ID.
                        required: true
                    start-ip:
                        description:
                            - Start of IPv4 exclusive range.
            ipv4-name:
                description:
                    - IPv4 address name. Source firewall.address.name firewall.addrgrp.name.
            ipv4-netmask:
                description:
                    - IPv4 Netmask.
            ipv4-split-exclude:
                description:
                    - IPv4 subnets that should not be sent over the IPsec tunnel. Source firewall.address.name firewall.addrgrp.name.
            ipv4-split-include:
                description:
                    - IPv4 split-include subnets. Source firewall.address.name firewall.addrgrp.name.
            ipv4-start-ip:
                description:
                    - Start of IPv4 range.
            ipv4-wins-server1:
                description:
                    - WINS server 1.
            ipv4-wins-server2:
                description:
                    - WINS server 2.
            ipv6-dns-server1:
                description:
                    - IPv6 DNS server 1.
            ipv6-dns-server2:
                description:
                    - IPv6 DNS server 2.
            ipv6-dns-server3:
                description:
                    - IPv6 DNS server 3.
            ipv6-end-ip:
                description:
                    - End of IPv6 range.
            ipv6-exclude-range:
                description:
                    - Configuration method IPv6 exclude ranges.
                suboptions:
                    end-ip:
                        description:
                            - End of IPv6 exclusive range.
                    id:
                        description:
                            - ID.
                        required: true
                    start-ip:
                        description:
                            - Start of IPv6 exclusive range.
            ipv6-name:
                description:
                    - IPv6 address name. Source firewall.address6.name firewall.addrgrp6.name.
            ipv6-prefix:
                description:
                    - IPv6 prefix.
            ipv6-split-exclude:
                description:
                    - IPv6 subnets that should not be sent over the IPsec tunnel. Source firewall.address6.name firewall.addrgrp6.name.
            ipv6-split-include:
                description:
                    - IPv6 split-include subnets. Source firewall.address6.name firewall.addrgrp6.name.
            ipv6-start-ip:
                description:
                    - Start of IPv6 range.
            keepalive:
                description:
                    - NAT-T keep alive interval.
            keylife:
                description:
                    - Time to wait in seconds before phase 1 encryption key expires.
            local-gw:
                description:
                    - Local VPN gateway.
            localid:
                description:
                    - Local ID.
            localid-type:
                description:
                    - Local ID type.
                choices:
                    - auto
                    - fqdn
                    - user-fqdn
                    - keyid
                    - address
                    - asn1dn
            mesh-selector-type:
                description:
                    - Add selectors containing subsets of the configuration depending on traffic.
                choices:
                    - disable
                    - subnet
                    - host
            mode:
                description:
                    - ID protection mode used to establish a secure channel.
                choices:
                    - aggressive
                    - main
            mode-cfg:
                description:
                    - Enable/disable configuration method.
                choices:
                    - disable
                    - enable
            name:
                description:
                    - IPsec remote gateway name.
                required: true
            nattraversal:
                description:
                    - Enable/disable NAT traversal.
                choices:
                    - enable
                    - disable
                    - forced
            negotiate-timeout:
                description:
                    - IKE SA negotiation timeout in seconds (1 - 300).
            npu-offload:
                description:
                    - Enable/disable offloading NPU.
                choices:
                    - enable
                    - disable
            peer:
                description:
                    - Accept this peer certificate. Source user.peer.name.
            peergrp:
                description:
                    - Accept this peer certificate group. Source user.peergrp.name.
            peerid:
                description:
                    - Accept this peer identity.
            peertype:
                description:
                    - Accept this peer type.
                choices:
                    - any
                    - one
                    - dialup
                    - peer
                    - peergrp
            ppk:
                description:
                    - Enable/disable IKEv2 Postquantum Preshared Key (PPK).
                choices:
                    - disable
                    - allow
                    - require
            ppk-identity:
                description:
                    - IKEv2 Postquantum Preshared Key Identity.
            ppk-secret:
                description:
                    - IKEv2 Postquantum Preshared Key (ASCII string or hexadecimal encoded with a leading 0x).
            priority:
                description:
                    - Priority for routes added by IKE (0 - 4294967295).
            proposal:
                description:
                    - Phase1 proposal.
                choices:
                    - des-md5
                    - des-sha1
                    - des-sha256
                    - des-sha384
                    - des-sha512
            psksecret:
                description:
                    - Pre-shared secret for PSK authentication (ASCII string or hexadecimal encoded with a leading 0x).
            psksecret-remote:
                description:
                    - Pre-shared secret for remote side PSK authentication (ASCII string or hexadecimal encoded with a leading 0x).
            reauth:
                description:
                    - Enable/disable re-authentication upon IKE SA lifetime expiration.
                choices:
                    - disable
                    - enable
            rekey:
                description:
                    - Enable/disable phase1 rekey.
                choices:
                    - enable
                    - disable
            remote-gw:
                description:
                    - Remote VPN gateway.
            remotegw-ddns:
                description:
                    - Domain name of remote gateway (eg. name.DDNS.com).
            rsa-signature-format:
                description:
                    - Digital Signature Authentication RSA signature format.
                choices:
                    - pkcs1
                    - pss
            save-password:
                description:
                    - Enable/disable saving XAuth username and password on VPN clients.
                choices:
                    - disable
                    - enable
            send-cert-chain:
                description:
                    - Enable/disable sending certificate chain.
                choices:
                    - enable
                    - disable
            signature-hash-alg:
                description:
                    - Digital Signature Authentication hash algorithms.
                choices:
                    - sha1
                    - sha2-256
                    - sha2-384
                    - sha2-512
            split-include-service:
                description:
                    - Split-include services. Source firewall.service.group.name firewall.service.custom.name.
            suite-b:
                description:
                    - Use Suite-B.
                choices:
                    - disable
                    - suite-b-gcm-128
                    - suite-b-gcm-256
            type:
                description:
                    - Remote gateway type.
                choices:
                    - static
                    - dynamic
                    - ddns
            unity-support:
                description:
                    - Enable/disable support for Cisco UNITY Configuration Method extensions.
                choices:
                    - disable
                    - enable
            usrgrp:
                description:
                    - User group name for dialup peers. Source user.group.name.
            wizard-type:
                description:
                    - GUI VPN Wizard Type.
                choices:
                    - custom
                    - dialup-forticlient
                    - dialup-ios
                    - dialup-android
                    - dialup-windows
                    - dialup-cisco
                    - static-fortigate
                    - dialup-fortigate
                    - static-cisco
                    - dialup-cisco-fw
            xauthtype:
                description:
                    - XAuth type.
                choices:
                    - disable
                    - client
                    - pap
                    - chap
                    - auto
'''

EXAMPLES = '''
- hosts: localhost
  vars:
   host: "192.168.122.40"
   username: "admin"
   password: ""
   vdom: "root"
  tasks:
  - name: Configure VPN remote gateway.
    fortios_vpn_ipsec_phase1:
      host:  "{{ host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{ vdom }}"
      https: "False"
      vpn_ipsec_phase1:
        state: "present"
        acct-verify: "enable"
        add-gw-route: "enable"
        add-route: "disable"
        assign-ip: "disable"
        assign-ip-from: "range"
        authmethod: "psk"
        authmethod-remote: "psk"
        authpasswd: "<your_own_value>"
        authusr: "<your_own_value>"
        authusrgrp: "<your_own_value> (source user.group.name)"
        auto-negotiate: "enable"
        backup-gateway:
         -
            address: "<your_own_value>"
        banner: "<your_own_value>"
        cert-id-validation: "enable"
        certificate:
         -
            name: "default_name_19 (source vpn.certificate.local.name)"
        childless-ike: "enable"
        client-auto-negotiate: "disable"
        client-keep-alive: "disable"
        comments: "<your_own_value>"
        dhgrp: "1"
        digital-signature-auth: "enable"
        distance: "26"
        dns-mode: "manual"
        domain: "<your_own_value>"
        dpd: "disable"
        dpd-retrycount: "30"
        dpd-retryinterval: "<your_own_value>"
        eap: "enable"
        eap-identity: "use-id-payload"
        enforce-unique-id: "disable"
        forticlient-enforcement: "enable"
        fragmentation: "enable"
        fragmentation-mtu: "37"
        group-authentication: "enable"
        group-authentication-secret: "<your_own_value>"
        ha-sync-esp-seqno: "enable"
        idle-timeout: "enable"
        idle-timeoutinterval: "42"
        ike-version: "1"
        include-local-lan: "disable"
        interface: "<your_own_value> (source system.interface.name)"
        ipv4-dns-server1: "<your_own_value>"
        ipv4-dns-server2: "<your_own_value>"
        ipv4-dns-server3: "<your_own_value>"
        ipv4-end-ip: "<your_own_value>"
        ipv4-exclude-range:
         -
            end-ip: "<your_own_value>"
            id:  "52"
            start-ip: "<your_own_value>"
        ipv4-name: "<your_own_value> (source firewall.address.name firewall.addrgrp.name)"
        ipv4-netmask: "<your_own_value>"
        ipv4-split-exclude: "<your_own_value> (source firewall.address.name firewall.addrgrp.name)"
        ipv4-split-include: "<your_own_value> (source firewall.address.name firewall.addrgrp.name)"
        ipv4-start-ip: "<your_own_value>"
        ipv4-wins-server1: "<your_own_value>"
        ipv4-wins-server2: "<your_own_value>"
        ipv6-dns-server1: "<your_own_value>"
        ipv6-dns-server2: "<your_own_value>"
        ipv6-dns-server3: "<your_own_value>"
        ipv6-end-ip: "<your_own_value>"
        ipv6-exclude-range:
         -
            end-ip: "<your_own_value>"
            id:  "67"
            start-ip: "<your_own_value>"
        ipv6-name: "<your_own_value> (source firewall.address6.name firewall.addrgrp6.name)"
        ipv6-prefix: "70"
        ipv6-split-exclude: "<your_own_value> (source firewall.address6.name firewall.addrgrp6.name)"
        ipv6-split-include: "<your_own_value> (source firewall.address6.name firewall.addrgrp6.name)"
        ipv6-start-ip: "<your_own_value>"
        keepalive: "74"
        keylife: "75"
        local-gw: "<your_own_value>"
        localid: "<your_own_value>"
        localid-type: "auto"
        mesh-selector-type: "disable"
        mode: "aggressive"
        mode-cfg: "disable"
        name: "default_name_82"
        nattraversal: "enable"
        negotiate-timeout: "84"
        npu-offload: "enable"
        peer: "<your_own_value> (source user.peer.name)"
        peergrp: "<your_own_value> (source user.peergrp.name)"
        peerid: "<your_own_value>"
        peertype: "any"
        ppk: "disable"
        ppk-identity: "<your_own_value>"
        ppk-secret: "<your_own_value>"
        priority: "93"
        proposal: "des-md5"
        psksecret: "<your_own_value>"
        psksecret-remote: "<your_own_value>"
        reauth: "disable"
        rekey: "enable"
        remote-gw: "<your_own_value>"
        remotegw-ddns: "<your_own_value>"
        rsa-signature-format: "pkcs1"
        save-password: "disable"
        send-cert-chain: "enable"
        signature-hash-alg: "sha1"
        split-include-service: "<your_own_value> (source firewall.service.group.name firewall.service.custom.name)"
        suite-b: "disable"
        type: "static"
        unity-support: "disable"
        usrgrp: "<your_own_value> (source user.group.name)"
        wizard-type: "custom"
        xauthtype: "disable"
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


def filter_vpn_ipsec_phase1_data(json):
    option_list = ['acct-verify', 'add-gw-route', 'add-route',
                   'assign-ip', 'assign-ip-from', 'authmethod',
                   'authmethod-remote', 'authpasswd', 'authusr',
                   'authusrgrp', 'auto-negotiate', 'backup-gateway',
                   'banner', 'cert-id-validation', 'certificate',
                   'childless-ike', 'client-auto-negotiate', 'client-keep-alive',
                   'comments', 'dhgrp', 'digital-signature-auth',
                   'distance', 'dns-mode', 'domain',
                   'dpd', 'dpd-retrycount', 'dpd-retryinterval',
                   'eap', 'eap-identity', 'enforce-unique-id',
                   'forticlient-enforcement', 'fragmentation', 'fragmentation-mtu',
                   'group-authentication', 'group-authentication-secret', 'ha-sync-esp-seqno',
                   'idle-timeout', 'idle-timeoutinterval', 'ike-version',
                   'include-local-lan', 'interface', 'ipv4-dns-server1',
                   'ipv4-dns-server2', 'ipv4-dns-server3', 'ipv4-end-ip',
                   'ipv4-exclude-range', 'ipv4-name', 'ipv4-netmask',
                   'ipv4-split-exclude', 'ipv4-split-include', 'ipv4-start-ip',
                   'ipv4-wins-server1', 'ipv4-wins-server2', 'ipv6-dns-server1',
                   'ipv6-dns-server2', 'ipv6-dns-server3', 'ipv6-end-ip',
                   'ipv6-exclude-range', 'ipv6-name', 'ipv6-prefix',
                   'ipv6-split-exclude', 'ipv6-split-include', 'ipv6-start-ip',
                   'keepalive', 'keylife', 'local-gw',
                   'localid', 'localid-type', 'mesh-selector-type',
                   'mode', 'mode-cfg', 'name',
                   'nattraversal', 'negotiate-timeout', 'npu-offload',
                   'peer', 'peergrp', 'peerid',
                   'peertype', 'ppk', 'ppk-identity',
                   'ppk-secret', 'priority', 'proposal',
                   'psksecret', 'psksecret-remote', 'reauth',
                   'rekey', 'remote-gw', 'remotegw-ddns',
                   'rsa-signature-format', 'save-password', 'send-cert-chain',
                   'signature-hash-alg', 'split-include-service', 'suite-b',
                   'type', 'unity-support', 'usrgrp',
                   'wizard-type', 'xauthtype']
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


def vpn_ipsec_phase1(data, fos):
    vdom = data['vdom']
    vpn_ipsec_phase1_data = data['vpn_ipsec_phase1']
    flattened_data = flatten_multilists_attributes(vpn_ipsec_phase1_data)
    filtered_data = filter_vpn_ipsec_phase1_data(flattened_data)
    if vpn_ipsec_phase1_data['state'] == "present":
        return fos.set('vpn.ipsec',
                       'phase1',
                       data=filtered_data,
                       vdom=vdom)

    elif vpn_ipsec_phase1_data['state'] == "absent":
        return fos.delete('vpn.ipsec',
                          'phase1',
                          mkey=filtered_data['name'],
                          vdom=vdom)


def fortios_vpn_ipsec(data, fos):
    login(data)

    if data['vpn_ipsec_phase1']:
        resp = vpn_ipsec_phase1(data, fos)

    fos.logout()
    return not resp['status'] == "success", resp['status'] == "success", resp


def main():
    fields = {
        "host": {"required": True, "type": "str"},
        "username": {"required": True, "type": "str"},
        "password": {"required": False, "type": "str", "no_log": True},
        "vdom": {"required": False, "type": "str", "default": "root"},
        "https": {"required": False, "type": "bool", "default": True},
        "vpn_ipsec_phase1": {
            "required": False, "type": "dict",
            "options": {
                "state": {"required": True, "type": "str",
                          "choices": ["present", "absent"]},
                "acct-verify": {"required": False, "type": "str",
                                "choices": ["enable", "disable"]},
                "add-gw-route": {"required": False, "type": "str",
                                 "choices": ["enable", "disable"]},
                "add-route": {"required": False, "type": "str",
                              "choices": ["disable", "enable"]},
                "assign-ip": {"required": False, "type": "str",
                              "choices": ["disable", "enable"]},
                "assign-ip-from": {"required": False, "type": "str",
                                   "choices": ["range", "usrgrp", "dhcp",
                                               "name"]},
                "authmethod": {"required": False, "type": "str",
                               "choices": ["psk", "signature"]},
                "authmethod-remote": {"required": False, "type": "str",
                                      "choices": ["psk", "signature"]},
                "authpasswd": {"required": False, "type": "str"},
                "authusr": {"required": False, "type": "str"},
                "authusrgrp": {"required": False, "type": "str"},
                "auto-negotiate": {"required": False, "type": "str",
                                   "choices": ["enable", "disable"]},
                "backup-gateway": {"required": False, "type": "list",
                                   "options": {
                                       "address": {"required": True, "type": "str"}
                                   }},
                "banner": {"required": False, "type": "str"},
                "cert-id-validation": {"required": False, "type": "str",
                                       "choices": ["enable", "disable"]},
                "certificate": {"required": False, "type": "list",
                                "options": {
                                    "name": {"required": True, "type": "str"}
                                }},
                "childless-ike": {"required": False, "type": "str",
                                  "choices": ["enable", "disable"]},
                "client-auto-negotiate": {"required": False, "type": "str",
                                          "choices": ["disable", "enable"]},
                "client-keep-alive": {"required": False, "type": "str",
                                      "choices": ["disable", "enable"]},
                "comments": {"required": False, "type": "str"},
                "dhgrp": {"required": False, "type": "str",
                          "choices": ["1", "2", "5",
                                      "14", "15", "16",
                                      "17", "18", "19",
                                      "20", "21", "27",
                                      "28", "29", "30",
                                      "31"]},
                "digital-signature-auth": {"required": False, "type": "str",
                                           "choices": ["enable", "disable"]},
                "distance": {"required": False, "type": "int"},
                "dns-mode": {"required": False, "type": "str",
                             "choices": ["manual", "auto"]},
                "domain": {"required": False, "type": "str"},
                "dpd": {"required": False, "type": "str",
                        "choices": ["disable", "on-idle", "on-demand"]},
                "dpd-retrycount": {"required": False, "type": "int"},
                "dpd-retryinterval": {"required": False, "type": "str"},
                "eap": {"required": False, "type": "str",
                        "choices": ["enable", "disable"]},
                "eap-identity": {"required": False, "type": "str",
                                 "choices": ["use-id-payload", "send-request"]},
                "enforce-unique-id": {"required": False, "type": "str",
                                      "choices": ["disable", "keep-new", "keep-old"]},
                "forticlient-enforcement": {"required": False, "type": "str",
                                            "choices": ["enable", "disable"]},
                "fragmentation": {"required": False, "type": "str",
                                  "choices": ["enable", "disable"]},
                "fragmentation-mtu": {"required": False, "type": "int"},
                "group-authentication": {"required": False, "type": "str",
                                         "choices": ["enable", "disable"]},
                "group-authentication-secret": {"required": False, "type": "password-3"},
                "ha-sync-esp-seqno": {"required": False, "type": "str",
                                      "choices": ["enable", "disable"]},
                "idle-timeout": {"required": False, "type": "str",
                                 "choices": ["enable", "disable"]},
                "idle-timeoutinterval": {"required": False, "type": "int"},
                "ike-version": {"required": False, "type": "str",
                                "choices": ["1", "2"]},
                "include-local-lan": {"required": False, "type": "str",
                                      "choices": ["disable", "enable"]},
                "interface": {"required": False, "type": "str"},
                "ipv4-dns-server1": {"required": False, "type": "str"},
                "ipv4-dns-server2": {"required": False, "type": "str"},
                "ipv4-dns-server3": {"required": False, "type": "str"},
                "ipv4-end-ip": {"required": False, "type": "str"},
                "ipv4-exclude-range": {"required": False, "type": "list",
                                       "options": {
                                           "end-ip": {"required": False, "type": "str"},
                                           "id": {"required": True, "type": "int"},
                                           "start-ip": {"required": False, "type": "str"}
                                       }},
                "ipv4-name": {"required": False, "type": "str"},
                "ipv4-netmask": {"required": False, "type": "str"},
                "ipv4-split-exclude": {"required": False, "type": "str"},
                "ipv4-split-include": {"required": False, "type": "str"},
                "ipv4-start-ip": {"required": False, "type": "str"},
                "ipv4-wins-server1": {"required": False, "type": "str"},
                "ipv4-wins-server2": {"required": False, "type": "str"},
                "ipv6-dns-server1": {"required": False, "type": "str"},
                "ipv6-dns-server2": {"required": False, "type": "str"},
                "ipv6-dns-server3": {"required": False, "type": "str"},
                "ipv6-end-ip": {"required": False, "type": "str"},
                "ipv6-exclude-range": {"required": False, "type": "list",
                                       "options": {
                                           "end-ip": {"required": False, "type": "str"},
                                           "id": {"required": True, "type": "int"},
                                           "start-ip": {"required": False, "type": "str"}
                                       }},
                "ipv6-name": {"required": False, "type": "str"},
                "ipv6-prefix": {"required": False, "type": "int"},
                "ipv6-split-exclude": {"required": False, "type": "str"},
                "ipv6-split-include": {"required": False, "type": "str"},
                "ipv6-start-ip": {"required": False, "type": "str"},
                "keepalive": {"required": False, "type": "int"},
                "keylife": {"required": False, "type": "int"},
                "local-gw": {"required": False, "type": "str"},
                "localid": {"required": False, "type": "str"},
                "localid-type": {"required": False, "type": "str",
                                 "choices": ["auto", "fqdn", "user-fqdn",
                                             "keyid", "address", "asn1dn"]},
                "mesh-selector-type": {"required": False, "type": "str",
                                       "choices": ["disable", "subnet", "host"]},
                "mode": {"required": False, "type": "str",
                         "choices": ["aggressive", "main"]},
                "mode-cfg": {"required": False, "type": "str",
                             "choices": ["disable", "enable"]},
                "name": {"required": True, "type": "str"},
                "nattraversal": {"required": False, "type": "str",
                                 "choices": ["enable", "disable", "forced"]},
                "negotiate-timeout": {"required": False, "type": "int"},
                "npu-offload": {"required": False, "type": "str",
                                "choices": ["enable", "disable"]},
                "peer": {"required": False, "type": "str"},
                "peergrp": {"required": False, "type": "str"},
                "peerid": {"required": False, "type": "str"},
                "peertype": {"required": False, "type": "str",
                             "choices": ["any", "one", "dialup",
                                         "peer", "peergrp"]},
                "ppk": {"required": False, "type": "str",
                        "choices": ["disable", "allow", "require"]},
                "ppk-identity": {"required": False, "type": "str"},
                "ppk-secret": {"required": False, "type": "password-3"},
                "priority": {"required": False, "type": "int"},
                "proposal": {"required": False, "type": "str",
                             "choices": ["des-md5", "des-sha1", "des-sha256",
                                         "des-sha384", "des-sha512"]},
                "psksecret": {"required": False, "type": "password-3"},
                "psksecret-remote": {"required": False, "type": "password-3"},
                "reauth": {"required": False, "type": "str",
                           "choices": ["disable", "enable"]},
                "rekey": {"required": False, "type": "str",
                          "choices": ["enable", "disable"]},
                "remote-gw": {"required": False, "type": "str"},
                "remotegw-ddns": {"required": False, "type": "str"},
                "rsa-signature-format": {"required": False, "type": "str",
                                         "choices": ["pkcs1", "pss"]},
                "save-password": {"required": False, "type": "str",
                                  "choices": ["disable", "enable"]},
                "send-cert-chain": {"required": False, "type": "str",
                                    "choices": ["enable", "disable"]},
                "signature-hash-alg": {"required": False, "type": "str",
                                       "choices": ["sha1", "sha2-256", "sha2-384",
                                                   "sha2-512"]},
                "split-include-service": {"required": False, "type": "str"},
                "suite-b": {"required": False, "type": "str",
                            "choices": ["disable", "suite-b-gcm-128", "suite-b-gcm-256"]},
                "type": {"required": False, "type": "str",
                         "choices": ["static", "dynamic", "ddns"]},
                "unity-support": {"required": False, "type": "str",
                                  "choices": ["disable", "enable"]},
                "usrgrp": {"required": False, "type": "str"},
                "wizard-type": {"required": False, "type": "str",
                                "choices": ["custom", "dialup-forticlient", "dialup-ios",
                                            "dialup-android", "dialup-windows", "dialup-cisco",
                                            "static-fortigate", "dialup-fortigate", "static-cisco",
                                            "dialup-cisco-fw"]},
                "xauthtype": {"required": False, "type": "str",
                              "choices": ["disable", "client", "pap",
                                          "chap", "auto"]}

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

    is_error, has_changed, result = fortios_vpn_ipsec(module.params, fos)

    if not is_error:
        module.exit_json(changed=has_changed, meta=result)
    else:
        module.fail_json(msg="Error in repo", meta=result)


if __name__ == '__main__':
    main()
