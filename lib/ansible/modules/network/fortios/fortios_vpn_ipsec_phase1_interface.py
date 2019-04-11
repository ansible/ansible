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
module: fortios_vpn_ipsec_phase1_interface
short_description: Configure VPN remote gateway in Fortinet's FortiOS and FortiGate.
description:
    - This module is able to configure a FortiGate or FortiOS by allowing the
      user to set and modify vpn_ipsec feature and phase1_interface category.
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
    vpn_ipsec_phase1_interface:
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
            auto-discovery-forwarder:
                description:
                    - Enable/disable forwarding auto-discovery short-cut messages.
                choices:
                    - enable
                    - disable
            auto-discovery-psk:
                description:
                    - Enable/disable use of pre-shared secrets for authentication of auto-discovery tunnels.
                choices:
                    - enable
                    - disable
            auto-discovery-receiver:
                description:
                    - Enable/disable accepting auto-discovery short-cut messages.
                choices:
                    - enable
                    - disable
            auto-discovery-sender:
                description:
                    - Enable/disable sending auto-discovery short-cut messages.
                choices:
                    - enable
                    - disable
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
                    - The names of up to 4 signed personal certificates.
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
            default-gw:
                description:
                    - IPv4 address of default route gateway to use for traffic exiting the interface.
            default-gw-priority:
                description:
                    - Priority for default gateway route. A higher priority number signifies a less preferred route.
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
            encap-local-gw4:
                description:
                    - Local IPv4 address of GRE/VXLAN tunnel.
            encap-local-gw6:
                description:
                    - Local IPv6 address of GRE/VXLAN tunnel.
            encap-remote-gw4:
                description:
                    - Remote IPv4 address of GRE/VXLAN tunnel.
            encap-remote-gw6:
                description:
                    - Remote IPv6 address of GRE/VXLAN tunnel.
            encapsulation:
                description:
                    - Enable/disable GRE/VXLAN encapsulation.
                choices:
                    - none
                    - gre
                    - vxlan
            encapsulation-address:
                description:
                    - Source for GRE/VXLAN tunnel address.
                choices:
                    - ike
                    - ipv4
                    - ipv6
            enforce-unique-id:
                description:
                    - Enable/disable peer ID uniqueness check.
                choices:
                    - disable
                    - keep-new
                    - keep-old
            exchange-interface-ip:
                description:
                    - Enable/disable exchange of IPsec interface IP address.
                choices:
                    - enable
                    - disable
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
            ip-version:
                description:
                    - IP version to use for VPN interface.
                choices:
                    - 4
                    - 6
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
                    - IPv4 address of the local gateway's external interface.
            local-gw6:
                description:
                    - IPv6 address of the local gateway's external interface.
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
                    - The ID protection mode used to establish a secure channel.
                choices:
                    - aggressive
                    - main
            mode-cfg:
                description:
                    - Enable/disable configuration method.
                choices:
                    - disable
                    - enable
            monitor:
                description:
                    - IPsec interface as backup for primary interface. Source vpn.ipsec.phase1-interface.name.
            monitor-hold-down-delay:
                description:
                    - Time to wait in seconds before recovery once primary re-establishes.
            monitor-hold-down-time:
                description:
                    - Time of day at which to fail back to primary after it re-establishes.
            monitor-hold-down-type:
                description:
                    - Recovery time method when primary interface re-establishes.
                choices:
                    - immediate
                    - delay
                    - time
            monitor-hold-down-weekday:
                description:
                    - Day of the week to recover once primary re-establishes.
                choices:
                    - everyday
                    - sunday
                    - monday
                    - tuesday
                    - wednesday
                    - thursday
                    - friday
                    - saturday
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
            net-device:
                description:
                    - Enable/disable kernel device creation for dialup instances.
                choices:
                    - enable
                    - disable
            npu-offload:
                description:
                    - Enable/disable offloading NPU.
                choices:
                    - enable
                    - disable
            passive-mode:
                description:
                    - Enable/disable IPsec passive mode for static tunnels.
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
                    - IPv4 address of the remote gateway's external interface.
            remote-gw6:
                description:
                    - IPv6 address of the remote gateway's external interface.
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
            tunnel-search:
                description:
                    - Tunnel search method for when the interface is shared.
                choices:
                    - selectors
                    - nexthop
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
            vni:
                description:
                    - VNI of VXLAN tunnel.
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
    fortios_vpn_ipsec_phase1_interface:
      host:  "{{ host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{ vdom }}"
      https: "False"
      vpn_ipsec_phase1_interface:
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
        auto-discovery-forwarder: "enable"
        auto-discovery-psk: "enable"
        auto-discovery-receiver: "enable"
        auto-discovery-sender: "enable"
        auto-negotiate: "enable"
        backup-gateway:
         -
            address: "<your_own_value>"
        banner: "<your_own_value>"
        cert-id-validation: "enable"
        certificate:
         -
            name: "default_name_23 (source vpn.certificate.local.name)"
        childless-ike: "enable"
        client-auto-negotiate: "disable"
        client-keep-alive: "disable"
        comments: "<your_own_value>"
        default-gw: "<your_own_value>"
        default-gw-priority: "29"
        dhgrp: "1"
        digital-signature-auth: "enable"
        distance: "32"
        dns-mode: "manual"
        domain: "<your_own_value>"
        dpd: "disable"
        dpd-retrycount: "36"
        dpd-retryinterval: "<your_own_value>"
        eap: "enable"
        eap-identity: "use-id-payload"
        encap-local-gw4: "<your_own_value>"
        encap-local-gw6: "<your_own_value>"
        encap-remote-gw4: "<your_own_value>"
        encap-remote-gw6: "<your_own_value>"
        encapsulation: "none"
        encapsulation-address: "ike"
        enforce-unique-id: "disable"
        exchange-interface-ip: "enable"
        forticlient-enforcement: "enable"
        fragmentation: "enable"
        fragmentation-mtu: "50"
        group-authentication: "enable"
        group-authentication-secret: "<your_own_value>"
        ha-sync-esp-seqno: "enable"
        idle-timeout: "enable"
        idle-timeoutinterval: "55"
        ike-version: "1"
        include-local-lan: "disable"
        interface: "<your_own_value> (source system.interface.name)"
        ip-version: "4"
        ipv4-dns-server1: "<your_own_value>"
        ipv4-dns-server2: "<your_own_value>"
        ipv4-dns-server3: "<your_own_value>"
        ipv4-end-ip: "<your_own_value>"
        ipv4-exclude-range:
         -
            end-ip: "<your_own_value>"
            id:  "66"
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
            id:  "81"
            start-ip: "<your_own_value>"
        ipv6-name: "<your_own_value> (source firewall.address6.name firewall.addrgrp6.name)"
        ipv6-prefix: "84"
        ipv6-split-exclude: "<your_own_value> (source firewall.address6.name firewall.addrgrp6.name)"
        ipv6-split-include: "<your_own_value> (source firewall.address6.name firewall.addrgrp6.name)"
        ipv6-start-ip: "<your_own_value>"
        keepalive: "88"
        keylife: "89"
        local-gw: "<your_own_value>"
        local-gw6: "<your_own_value>"
        localid: "<your_own_value>"
        localid-type: "auto"
        mesh-selector-type: "disable"
        mode: "aggressive"
        mode-cfg: "disable"
        monitor: "<your_own_value> (source vpn.ipsec.phase1-interface.name)"
        monitor-hold-down-delay: "98"
        monitor-hold-down-time: "<your_own_value>"
        monitor-hold-down-type: "immediate"
        monitor-hold-down-weekday: "everyday"
        name: "default_name_102"
        nattraversal: "enable"
        negotiate-timeout: "104"
        net-device: "enable"
        npu-offload: "enable"
        passive-mode: "enable"
        peer: "<your_own_value> (source user.peer.name)"
        peergrp: "<your_own_value> (source user.peergrp.name)"
        peerid: "<your_own_value>"
        peertype: "any"
        ppk: "disable"
        ppk-identity: "<your_own_value>"
        ppk-secret: "<your_own_value>"
        priority: "115"
        proposal: "des-md5"
        psksecret: "<your_own_value>"
        psksecret-remote: "<your_own_value>"
        reauth: "disable"
        rekey: "enable"
        remote-gw: "<your_own_value>"
        remote-gw6: "<your_own_value>"
        remotegw-ddns: "<your_own_value>"
        rsa-signature-format: "pkcs1"
        save-password: "disable"
        send-cert-chain: "enable"
        signature-hash-alg: "sha1"
        split-include-service: "<your_own_value> (source firewall.service.group.name firewall.service.custom.name)"
        suite-b: "disable"
        tunnel-search: "selectors"
        type: "static"
        unity-support: "disable"
        usrgrp: "<your_own_value> (source user.group.name)"
        vni: "134"
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


def filter_vpn_ipsec_phase1_interface_data(json):
    option_list = ['acct-verify', 'add-gw-route', 'add-route',
                   'assign-ip', 'assign-ip-from', 'authmethod',
                   'authmethod-remote', 'authpasswd', 'authusr',
                   'authusrgrp', 'auto-discovery-forwarder', 'auto-discovery-psk',
                   'auto-discovery-receiver', 'auto-discovery-sender', 'auto-negotiate',
                   'backup-gateway', 'banner', 'cert-id-validation',
                   'certificate', 'childless-ike', 'client-auto-negotiate',
                   'client-keep-alive', 'comments', 'default-gw',
                   'default-gw-priority', 'dhgrp', 'digital-signature-auth',
                   'distance', 'dns-mode', 'domain',
                   'dpd', 'dpd-retrycount', 'dpd-retryinterval',
                   'eap', 'eap-identity', 'encap-local-gw4',
                   'encap-local-gw6', 'encap-remote-gw4', 'encap-remote-gw6',
                   'encapsulation', 'encapsulation-address', 'enforce-unique-id',
                   'exchange-interface-ip', 'forticlient-enforcement', 'fragmentation',
                   'fragmentation-mtu', 'group-authentication', 'group-authentication-secret',
                   'ha-sync-esp-seqno', 'idle-timeout', 'idle-timeoutinterval',
                   'ike-version', 'include-local-lan', 'interface',
                   'ip-version', 'ipv4-dns-server1', 'ipv4-dns-server2',
                   'ipv4-dns-server3', 'ipv4-end-ip', 'ipv4-exclude-range',
                   'ipv4-name', 'ipv4-netmask', 'ipv4-split-exclude',
                   'ipv4-split-include', 'ipv4-start-ip', 'ipv4-wins-server1',
                   'ipv4-wins-server2', 'ipv6-dns-server1', 'ipv6-dns-server2',
                   'ipv6-dns-server3', 'ipv6-end-ip', 'ipv6-exclude-range',
                   'ipv6-name', 'ipv6-prefix', 'ipv6-split-exclude',
                   'ipv6-split-include', 'ipv6-start-ip', 'keepalive',
                   'keylife', 'local-gw', 'local-gw6',
                   'localid', 'localid-type', 'mesh-selector-type',
                   'mode', 'mode-cfg', 'monitor',
                   'monitor-hold-down-delay', 'monitor-hold-down-time', 'monitor-hold-down-type',
                   'monitor-hold-down-weekday', 'name', 'nattraversal',
                   'negotiate-timeout', 'net-device', 'npu-offload',
                   'passive-mode', 'peer', 'peergrp',
                   'peerid', 'peertype', 'ppk',
                   'ppk-identity', 'ppk-secret', 'priority',
                   'proposal', 'psksecret', 'psksecret-remote',
                   'reauth', 'rekey', 'remote-gw',
                   'remote-gw6', 'remotegw-ddns', 'rsa-signature-format',
                   'save-password', 'send-cert-chain', 'signature-hash-alg',
                   'split-include-service', 'suite-b', 'tunnel-search',
                   'type', 'unity-support', 'usrgrp',
                   'vni', 'wizard-type', 'xauthtype']
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


def vpn_ipsec_phase1_interface(data, fos):
    vdom = data['vdom']
    vpn_ipsec_phase1_interface_data = data['vpn_ipsec_phase1_interface']
    flattened_data = flatten_multilists_attributes(vpn_ipsec_phase1_interface_data)
    filtered_data = filter_vpn_ipsec_phase1_interface_data(flattened_data)
    if vpn_ipsec_phase1_interface_data['state'] == "present":
        return fos.set('vpn.ipsec',
                       'phase1-interface',
                       data=filtered_data,
                       vdom=vdom)

    elif vpn_ipsec_phase1_interface_data['state'] == "absent":
        return fos.delete('vpn.ipsec',
                          'phase1-interface',
                          mkey=filtered_data['name'],
                          vdom=vdom)


def fortios_vpn_ipsec(data, fos):
    login(data)

    if data['vpn_ipsec_phase1_interface']:
        resp = vpn_ipsec_phase1_interface(data, fos)

    fos.logout()
    return not resp['status'] == "success", resp['status'] == "success", resp


def main():
    fields = {
        "host": {"required": True, "type": "str"},
        "username": {"required": True, "type": "str"},
        "password": {"required": False, "type": "str", "no_log": True},
        "vdom": {"required": False, "type": "str", "default": "root"},
        "https": {"required": False, "type": "bool", "default": True},
        "vpn_ipsec_phase1_interface": {
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
                "auto-discovery-forwarder": {"required": False, "type": "str",
                                             "choices": ["enable", "disable"]},
                "auto-discovery-psk": {"required": False, "type": "str",
                                       "choices": ["enable", "disable"]},
                "auto-discovery-receiver": {"required": False, "type": "str",
                                            "choices": ["enable", "disable"]},
                "auto-discovery-sender": {"required": False, "type": "str",
                                          "choices": ["enable", "disable"]},
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
                "default-gw": {"required": False, "type": "str"},
                "default-gw-priority": {"required": False, "type": "int"},
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
                "encap-local-gw4": {"required": False, "type": "str"},
                "encap-local-gw6": {"required": False, "type": "str"},
                "encap-remote-gw4": {"required": False, "type": "str"},
                "encap-remote-gw6": {"required": False, "type": "str"},
                "encapsulation": {"required": False, "type": "str",
                                  "choices": ["none", "gre", "vxlan"]},
                "encapsulation-address": {"required": False, "type": "str",
                                          "choices": ["ike", "ipv4", "ipv6"]},
                "enforce-unique-id": {"required": False, "type": "str",
                                      "choices": ["disable", "keep-new", "keep-old"]},
                "exchange-interface-ip": {"required": False, "type": "str",
                                          "choices": ["enable", "disable"]},
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
                "ip-version": {"required": False, "type": "str",
                               "choices": ["4", "6"]},
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
                "local-gw6": {"required": False, "type": "str"},
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
                "monitor": {"required": False, "type": "str"},
                "monitor-hold-down-delay": {"required": False, "type": "int"},
                "monitor-hold-down-time": {"required": False, "type": "str"},
                "monitor-hold-down-type": {"required": False, "type": "str",
                                           "choices": ["immediate", "delay", "time"]},
                "monitor-hold-down-weekday": {"required": False, "type": "str",
                                              "choices": ["everyday", "sunday", "monday",
                                                          "tuesday", "wednesday", "thursday",
                                                          "friday", "saturday"]},
                "name": {"required": True, "type": "str"},
                "nattraversal": {"required": False, "type": "str",
                                 "choices": ["enable", "disable", "forced"]},
                "negotiate-timeout": {"required": False, "type": "int"},
                "net-device": {"required": False, "type": "str",
                               "choices": ["enable", "disable"]},
                "npu-offload": {"required": False, "type": "str",
                                "choices": ["enable", "disable"]},
                "passive-mode": {"required": False, "type": "str",
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
                "remote-gw6": {"required": False, "type": "str"},
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
                "tunnel-search": {"required": False, "type": "str",
                                  "choices": ["selectors", "nexthop"]},
                "type": {"required": False, "type": "str",
                         "choices": ["static", "dynamic", "ddns"]},
                "unity-support": {"required": False, "type": "str",
                                  "choices": ["disable", "enable"]},
                "usrgrp": {"required": False, "type": "str"},
                "vni": {"required": False, "type": "int"},
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
