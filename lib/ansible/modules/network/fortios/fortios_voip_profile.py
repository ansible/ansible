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
module: fortios_voip_profile
short_description: Configure VoIP profiles in Fortinet's FortiOS and FortiGate.
description:
    - This module is able to configure a FortiGate or FortiOS by allowing the
      user to set and modify voip feature and profile category.
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
    voip_profile:
        description:
            - Configure VoIP profiles.
        default: null
        suboptions:
            state:
                description:
                    - Indicates whether to create or remove the object
                choices:
                    - present
                    - absent
            comment:
                description:
                    - Comment.
            name:
                description:
                    - Profile name.
                required: true
            sccp:
                description:
                    - SCCP.
                suboptions:
                    block-mcast:
                        description:
                            - Enable/disable block multicast RTP connections.
                        choices:
                            - disable
                            - enable
                    log-call-summary:
                        description:
                            - Enable/disable log summary of SCCP calls.
                        choices:
                            - disable
                            - enable
                    log-violations:
                        description:
                            - Enable/disable logging of SCCP violations.
                        choices:
                            - disable
                            - enable
                    max-calls:
                        description:
                            - Maximum calls per minute per SCCP client (max 65535).
                    status:
                        description:
                            - Enable/disable SCCP.
                        choices:
                            - disable
                            - enable
                    verify-header:
                        description:
                            - Enable/disable verify SCCP header content.
                        choices:
                            - disable
                            - enable
            sip:
                description:
                    - SIP.
                suboptions:
                    ack-rate:
                        description:
                            - ACK request rate limit (per second, per policy).
                    block-ack:
                        description:
                            - Enable/disable block ACK requests.
                        choices:
                            - disable
                            - enable
                    block-bye:
                        description:
                            - Enable/disable block BYE requests.
                        choices:
                            - disable
                            - enable
                    block-cancel:
                        description:
                            - Enable/disable block CANCEL requests.
                        choices:
                            - disable
                            - enable
                    block-geo-red-options:
                        description:
                            - Enable/disable block OPTIONS requests, but OPTIONS requests still notify for redundancy.
                        choices:
                            - disable
                            - enable
                    block-info:
                        description:
                            - Enable/disable block INFO requests.
                        choices:
                            - disable
                            - enable
                    block-invite:
                        description:
                            - Enable/disable block INVITE requests.
                        choices:
                            - disable
                            - enable
                    block-long-lines:
                        description:
                            - Enable/disable block requests with headers exceeding max-line-length.
                        choices:
                            - disable
                            - enable
                    block-message:
                        description:
                            - Enable/disable block MESSAGE requests.
                        choices:
                            - disable
                            - enable
                    block-notify:
                        description:
                            - Enable/disable block NOTIFY requests.
                        choices:
                            - disable
                            - enable
                    block-options:
                        description:
                            - Enable/disable block OPTIONS requests and no OPTIONS as notifying message for redundancy either.
                        choices:
                            - disable
                            - enable
                    block-prack:
                        description:
                            - Enable/disable block prack requests.
                        choices:
                            - disable
                            - enable
                    block-publish:
                        description:
                            - Enable/disable block PUBLISH requests.
                        choices:
                            - disable
                            - enable
                    block-refer:
                        description:
                            - Enable/disable block REFER requests.
                        choices:
                            - disable
                            - enable
                    block-register:
                        description:
                            - Enable/disable block REGISTER requests.
                        choices:
                            - disable
                            - enable
                    block-subscribe:
                        description:
                            - Enable/disable block SUBSCRIBE requests.
                        choices:
                            - disable
                            - enable
                    block-unknown:
                        description:
                            - Block unrecognized SIP requests (enabled by default).
                        choices:
                            - disable
                            - enable
                    block-update:
                        description:
                            - Enable/disable block UPDATE requests.
                        choices:
                            - disable
                            - enable
                    bye-rate:
                        description:
                            - BYE request rate limit (per second, per policy).
                    call-keepalive:
                        description:
                            - Continue tracking calls with no RTP for this many minutes.
                    cancel-rate:
                        description:
                            - CANCEL request rate limit (per second, per policy).
                    contact-fixup:
                        description:
                            - "Fixup contact anyway even if contact's IP:port doesn't match session's IP:port."
                        choices:
                            - disable
                            - enable
                    hnt-restrict-source-ip:
                        description:
                            - Enable/disable restrict RTP source IP to be the same as SIP source IP when HNT is enabled.
                        choices:
                            - disable
                            - enable
                    hosted-nat-traversal:
                        description:
                            - Hosted NAT Traversal (HNT).
                        choices:
                            - disable
                            - enable
                    info-rate:
                        description:
                            - INFO request rate limit (per second, per policy).
                    invite-rate:
                        description:
                            - INVITE request rate limit (per second, per policy).
                    ips-rtp:
                        description:
                            - Enable/disable allow IPS on RTP.
                        choices:
                            - disable
                            - enable
                    log-call-summary:
                        description:
                            - Enable/disable logging of SIP call summary.
                        choices:
                            - disable
                            - enable
                    log-violations:
                        description:
                            - Enable/disable logging of SIP violations.
                        choices:
                            - disable
                            - enable
                    malformed-header-allow:
                        description:
                            - Action for malformed Allow header.
                        choices:
                            - discard
                            - pass
                            - respond
                    malformed-header-call-id:
                        description:
                            - Action for malformed Call-ID header.
                        choices:
                            - discard
                            - pass
                            - respond
                    malformed-header-contact:
                        description:
                            - Action for malformed Contact header.
                        choices:
                            - discard
                            - pass
                            - respond
                    malformed-header-content-length:
                        description:
                            - Action for malformed Content-Length header.
                        choices:
                            - discard
                            - pass
                            - respond
                    malformed-header-content-type:
                        description:
                            - Action for malformed Content-Type header.
                        choices:
                            - discard
                            - pass
                            - respond
                    malformed-header-cseq:
                        description:
                            - Action for malformed CSeq header.
                        choices:
                            - discard
                            - pass
                            - respond
                    malformed-header-expires:
                        description:
                            - Action for malformed Expires header.
                        choices:
                            - discard
                            - pass
                            - respond
                    malformed-header-from:
                        description:
                            - Action for malformed From header.
                        choices:
                            - discard
                            - pass
                            - respond
                    malformed-header-max-forwards:
                        description:
                            - Action for malformed Max-Forwards header.
                        choices:
                            - discard
                            - pass
                            - respond
                    malformed-header-p-asserted-identity:
                        description:
                            - Action for malformed P-Asserted-Identity header.
                        choices:
                            - discard
                            - pass
                            - respond
                    malformed-header-rack:
                        description:
                            - Action for malformed RAck header.
                        choices:
                            - discard
                            - pass
                            - respond
                    malformed-header-record-route:
                        description:
                            - Action for malformed Record-Route header.
                        choices:
                            - discard
                            - pass
                            - respond
                    malformed-header-route:
                        description:
                            - Action for malformed Route header.
                        choices:
                            - discard
                            - pass
                            - respond
                    malformed-header-rseq:
                        description:
                            - Action for malformed RSeq header.
                        choices:
                            - discard
                            - pass
                            - respond
                    malformed-header-sdp-a:
                        description:
                            - Action for malformed SDP a line.
                        choices:
                            - discard
                            - pass
                            - respond
                    malformed-header-sdp-b:
                        description:
                            - Action for malformed SDP b line.
                        choices:
                            - discard
                            - pass
                            - respond
                    malformed-header-sdp-c:
                        description:
                            - Action for malformed SDP c line.
                        choices:
                            - discard
                            - pass
                            - respond
                    malformed-header-sdp-i:
                        description:
                            - Action for malformed SDP i line.
                        choices:
                            - discard
                            - pass
                            - respond
                    malformed-header-sdp-k:
                        description:
                            - Action for malformed SDP k line.
                        choices:
                            - discard
                            - pass
                            - respond
                    malformed-header-sdp-m:
                        description:
                            - Action for malformed SDP m line.
                        choices:
                            - discard
                            - pass
                            - respond
                    malformed-header-sdp-o:
                        description:
                            - Action for malformed SDP o line.
                        choices:
                            - discard
                            - pass
                            - respond
                    malformed-header-sdp-r:
                        description:
                            - Action for malformed SDP r line.
                        choices:
                            - discard
                            - pass
                            - respond
                    malformed-header-sdp-s:
                        description:
                            - Action for malformed SDP s line.
                        choices:
                            - discard
                            - pass
                            - respond
                    malformed-header-sdp-t:
                        description:
                            - Action for malformed SDP t line.
                        choices:
                            - discard
                            - pass
                            - respond
                    malformed-header-sdp-v:
                        description:
                            - Action for malformed SDP v line.
                        choices:
                            - discard
                            - pass
                            - respond
                    malformed-header-sdp-z:
                        description:
                            - Action for malformed SDP z line.
                        choices:
                            - discard
                            - pass
                            - respond
                    malformed-header-to:
                        description:
                            - Action for malformed To header.
                        choices:
                            - discard
                            - pass
                            - respond
                    malformed-header-via:
                        description:
                            - Action for malformed VIA header.
                        choices:
                            - discard
                            - pass
                            - respond
                    malformed-request-line:
                        description:
                            - Action for malformed request line.
                        choices:
                            - discard
                            - pass
                            - respond
                    max-body-length:
                        description:
                            - Maximum SIP message body length (0 meaning no limit).
                    max-dialogs:
                        description:
                            - Maximum number of concurrent calls/dialogs (per policy).
                    max-idle-dialogs:
                        description:
                            - Maximum number established but idle dialogs to retain (per policy).
                    max-line-length:
                        description:
                            - Maximum SIP header line length (78-4096).
                    message-rate:
                        description:
                            - MESSAGE request rate limit (per second, per policy).
                    nat-trace:
                        description:
                            - Enable/disable preservation of original IP in SDP i line.
                        choices:
                            - disable
                            - enable
                    no-sdp-fixup:
                        description:
                            - Enable/disable no SDP fix-up.
                        choices:
                            - disable
                            - enable
                    notify-rate:
                        description:
                            - NOTIFY request rate limit (per second, per policy).
                    open-contact-pinhole:
                        description:
                            - Enable/disable open pinhole for non-REGISTER Contact port.
                        choices:
                            - disable
                            - enable
                    open-record-route-pinhole:
                        description:
                            - Enable/disable open pinhole for Record-Route port.
                        choices:
                            - disable
                            - enable
                    open-register-pinhole:
                        description:
                            - Enable/disable open pinhole for REGISTER Contact port.
                        choices:
                            - disable
                            - enable
                    open-via-pinhole:
                        description:
                            - Enable/disable open pinhole for Via port.
                        choices:
                            - disable
                            - enable
                    options-rate:
                        description:
                            - OPTIONS request rate limit (per second, per policy).
                    prack-rate:
                        description:
                            - PRACK request rate limit (per second, per policy).
                    preserve-override:
                        description:
                            - "Override i line to preserve original IPS (default: append)."
                        choices:
                            - disable
                            - enable
                    provisional-invite-expiry-time:
                        description:
                            - Expiry time for provisional INVITE (10 - 3600 sec).
                    publish-rate:
                        description:
                            - PUBLISH request rate limit (per second, per policy).
                    refer-rate:
                        description:
                            - REFER request rate limit (per second, per policy).
                    register-contact-trace:
                        description:
                            - Enable/disable trace original IP/port within the contact header of REGISTER requests.
                        choices:
                            - disable
                            - enable
                    register-rate:
                        description:
                            - REGISTER request rate limit (per second, per policy).
                    rfc2543-branch:
                        description:
                            - Enable/disable support via branch compliant with RFC 2543.
                        choices:
                            - disable
                            - enable
                    rtp:
                        description:
                            - Enable/disable create pinholes for RTP traffic to traverse firewall.
                        choices:
                            - disable
                            - enable
                    ssl-algorithm:
                        description:
                            - Relative strength of encryption algorithms accepted in negotiation.
                        choices:
                            - high
                            - medium
                            - low
                    ssl-auth-client:
                        description:
                            - Require a client certificate and authenticate it with the peer/peergrp. Source user.peer.name user.peergrp.name.
                    ssl-auth-server:
                        description:
                            - Authenticate the server's certificate with the peer/peergrp. Source user.peer.name user.peergrp.name.
                    ssl-client-certificate:
                        description:
                            - Name of Certificate to offer to server if requested. Source vpn.certificate.local.name.
                    ssl-client-renegotiation:
                        description:
                            - Allow/block client renegotiation by server.
                        choices:
                            - allow
                            - deny
                            - secure
                    ssl-max-version:
                        description:
                            - Highest SSL/TLS version to negotiate.
                        choices:
                            - ssl-3.0
                            - tls-1.0
                            - tls-1.1
                            - tls-1.2
                    ssl-min-version:
                        description:
                            - Lowest SSL/TLS version to negotiate.
                        choices:
                            - ssl-3.0
                            - tls-1.0
                            - tls-1.1
                            - tls-1.2
                    ssl-mode:
                        description:
                            - SSL/TLS mode for encryption & decryption of traffic.
                        choices:
                            - off
                            - full
                    ssl-pfs:
                        description:
                            - SSL Perfect Forward Secrecy.
                        choices:
                            - require
                            - deny
                            - allow
                    ssl-send-empty-frags:
                        description:
                            - Send empty fragments to avoid attack on CBC IV (SSL 3.0 & TLS 1.0 only).
                        choices:
                            - enable
                            - disable
                    ssl-server-certificate:
                        description:
                            - Name of Certificate return to the client in every SSL connection. Source vpn.certificate.local.name.
                    status:
                        description:
                            - Enable/disable SIP.
                        choices:
                            - disable
                            - enable
                    strict-register:
                        description:
                            - Enable/disable only allow the registrar to connect.
                        choices:
                            - disable
                            - enable
                    subscribe-rate:
                        description:
                            - SUBSCRIBE request rate limit (per second, per policy).
                    unknown-header:
                        description:
                            - Action for unknown SIP header.
                        choices:
                            - discard
                            - pass
                            - respond
                    update-rate:
                        description:
                            - UPDATE request rate limit (per second, per policy).
'''

EXAMPLES = '''
- hosts: localhost
  vars:
   host: "192.168.122.40"
   username: "admin"
   password: ""
   vdom: "root"
  tasks:
  - name: Configure VoIP profiles.
    fortios_voip_profile:
      host:  "{{ host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{ vdom }}"
      https: "False"
      voip_profile:
        state: "present"
        comment: "Comment."
        name: "default_name_4"
        sccp:
            block-mcast: "disable"
            log-call-summary: "disable"
            log-violations: "disable"
            max-calls: "9"
            status: "disable"
            verify-header: "disable"
        sip:
            ack-rate: "13"
            block-ack: "disable"
            block-bye: "disable"
            block-cancel: "disable"
            block-geo-red-options: "disable"
            block-info: "disable"
            block-invite: "disable"
            block-long-lines: "disable"
            block-message: "disable"
            block-notify: "disable"
            block-options: "disable"
            block-prack: "disable"
            block-publish: "disable"
            block-refer: "disable"
            block-register: "disable"
            block-subscribe: "disable"
            block-unknown: "disable"
            block-update: "disable"
            bye-rate: "31"
            call-keepalive: "32"
            cancel-rate: "33"
            contact-fixup: "disable"
            hnt-restrict-source-ip: "disable"
            hosted-nat-traversal: "disable"
            info-rate: "37"
            invite-rate: "38"
            ips-rtp: "disable"
            log-call-summary: "disable"
            log-violations: "disable"
            malformed-header-allow: "discard"
            malformed-header-call-id: "discard"
            malformed-header-contact: "discard"
            malformed-header-content-length: "discard"
            malformed-header-content-type: "discard"
            malformed-header-cseq: "discard"
            malformed-header-expires: "discard"
            malformed-header-from: "discard"
            malformed-header-max-forwards: "discard"
            malformed-header-p-asserted-identity: "discard"
            malformed-header-rack: "discard"
            malformed-header-record-route: "discard"
            malformed-header-route: "discard"
            malformed-header-rseq: "discard"
            malformed-header-sdp-a: "discard"
            malformed-header-sdp-b: "discard"
            malformed-header-sdp-c: "discard"
            malformed-header-sdp-i: "discard"
            malformed-header-sdp-k: "discard"
            malformed-header-sdp-m: "discard"
            malformed-header-sdp-o: "discard"
            malformed-header-sdp-r: "discard"
            malformed-header-sdp-s: "discard"
            malformed-header-sdp-t: "discard"
            malformed-header-sdp-v: "discard"
            malformed-header-sdp-z: "discard"
            malformed-header-to: "discard"
            malformed-header-via: "discard"
            malformed-request-line: "discard"
            max-body-length: "71"
            max-dialogs: "72"
            max-idle-dialogs: "73"
            max-line-length: "74"
            message-rate: "75"
            nat-trace: "disable"
            no-sdp-fixup: "disable"
            notify-rate: "78"
            open-contact-pinhole: "disable"
            open-record-route-pinhole: "disable"
            open-register-pinhole: "disable"
            open-via-pinhole: "disable"
            options-rate: "83"
            prack-rate: "84"
            preserve-override: "disable"
            provisional-invite-expiry-time: "86"
            publish-rate: "87"
            refer-rate: "88"
            register-contact-trace: "disable"
            register-rate: "90"
            rfc2543-branch: "disable"
            rtp: "disable"
            ssl-algorithm: "high"
            ssl-auth-client: "<your_own_value> (source user.peer.name user.peergrp.name)"
            ssl-auth-server: "<your_own_value> (source user.peer.name user.peergrp.name)"
            ssl-client-certificate: "<your_own_value> (source vpn.certificate.local.name)"
            ssl-client-renegotiation: "allow"
            ssl-max-version: "ssl-3.0"
            ssl-min-version: "ssl-3.0"
            ssl-mode: "off"
            ssl-pfs: "require"
            ssl-send-empty-frags: "enable"
            ssl-server-certificate: "<your_own_value> (source vpn.certificate.local.name)"
            status: "disable"
            strict-register: "disable"
            subscribe-rate: "106"
            unknown-header: "discard"
            update-rate: "108"
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


def login(data, fos):
    host = data['host']
    username = data['username']
    password = data['password']

    fos.debug('on')
    if 'https' in data and not data['https']:
        fos.https('off')
    else:
        fos.https('on')

    fos.login(host, username, password)


def filter_voip_profile_data(json):
    option_list = ['comment', 'name', 'sccp',
                   'sip']
    dictionary = {}

    for attribute in option_list:
        if attribute in json and json[attribute] is not None:
            dictionary[attribute] = json[attribute]

    return dictionary


def voip_profile(data, fos):
    vdom = data['vdom']
    voip_profile_data = data['voip_profile']
    filtered_data = filter_voip_profile_data(voip_profile_data)

    if voip_profile_data['state'] == "present":
        return fos.set('voip',
                       'profile',
                       data=filtered_data,
                       vdom=vdom)

    elif voip_profile_data['state'] == "absent":
        return fos.delete('voip',
                          'profile',
                          mkey=filtered_data['name'],
                          vdom=vdom)


def fortios_voip(data, fos):
    login(data, fos)

    if data['voip_profile']:
        resp = voip_profile(data, fos)

    fos.logout()
    return not resp['status'] == "success", resp['status'] == "success", resp


def main():
    fields = {
        "host": {"required": True, "type": "str"},
        "username": {"required": True, "type": "str"},
        "password": {"required": False, "type": "str", "no_log": True},
        "vdom": {"required": False, "type": "str", "default": "root"},
        "https": {"required": False, "type": "bool", "default": True},
        "voip_profile": {
            "required": False, "type": "dict",
            "options": {
                "state": {"required": True, "type": "str",
                          "choices": ["present", "absent"]},
                "comment": {"required": False, "type": "str"},
                "name": {"required": True, "type": "str"},
                "sccp": {"required": False, "type": "dict",
                         "options": {
                             "block-mcast": {"required": False, "type": "str",
                                             "choices": ["disable", "enable"]},
                             "log-call-summary": {"required": False, "type": "str",
                                                  "choices": ["disable", "enable"]},
                             "log-violations": {"required": False, "type": "str",
                                                "choices": ["disable", "enable"]},
                             "max-calls": {"required": False, "type": "int"},
                             "status": {"required": False, "type": "str",
                                        "choices": ["disable", "enable"]},
                             "verify-header": {"required": False, "type": "str",
                                               "choices": ["disable", "enable"]}
                         }},
                "sip": {"required": False, "type": "dict",
                        "options": {
                            "ack-rate": {"required": False, "type": "int"},
                            "block-ack": {"required": False, "type": "str",
                                          "choices": ["disable", "enable"]},
                            "block-bye": {"required": False, "type": "str",
                                          "choices": ["disable", "enable"]},
                            "block-cancel": {"required": False, "type": "str",
                                             "choices": ["disable", "enable"]},
                            "block-geo-red-options": {"required": False, "type": "str",
                                                      "choices": ["disable", "enable"]},
                            "block-info": {"required": False, "type": "str",
                                           "choices": ["disable", "enable"]},
                            "block-invite": {"required": False, "type": "str",
                                             "choices": ["disable", "enable"]},
                            "block-long-lines": {"required": False, "type": "str",
                                                 "choices": ["disable", "enable"]},
                            "block-message": {"required": False, "type": "str",
                                              "choices": ["disable", "enable"]},
                            "block-notify": {"required": False, "type": "str",
                                             "choices": ["disable", "enable"]},
                            "block-options": {"required": False, "type": "str",
                                              "choices": ["disable", "enable"]},
                            "block-prack": {"required": False, "type": "str",
                                            "choices": ["disable", "enable"]},
                            "block-publish": {"required": False, "type": "str",
                                              "choices": ["disable", "enable"]},
                            "block-refer": {"required": False, "type": "str",
                                            "choices": ["disable", "enable"]},
                            "block-register": {"required": False, "type": "str",
                                               "choices": ["disable", "enable"]},
                            "block-subscribe": {"required": False, "type": "str",
                                                "choices": ["disable", "enable"]},
                            "block-unknown": {"required": False, "type": "str",
                                              "choices": ["disable", "enable"]},
                            "block-update": {"required": False, "type": "str",
                                             "choices": ["disable", "enable"]},
                            "bye-rate": {"required": False, "type": "int"},
                            "call-keepalive": {"required": False, "type": "int"},
                            "cancel-rate": {"required": False, "type": "int"},
                            "contact-fixup": {"required": False, "type": "str",
                                              "choices": ["disable", "enable"]},
                            "hnt-restrict-source-ip": {"required": False, "type": "str",
                                                       "choices": ["disable", "enable"]},
                            "hosted-nat-traversal": {"required": False, "type": "str",
                                                     "choices": ["disable", "enable"]},
                            "info-rate": {"required": False, "type": "int"},
                            "invite-rate": {"required": False, "type": "int"},
                            "ips-rtp": {"required": False, "type": "str",
                                        "choices": ["disable", "enable"]},
                            "log-call-summary": {"required": False, "type": "str",
                                                 "choices": ["disable", "enable"]},
                            "log-violations": {"required": False, "type": "str",
                                               "choices": ["disable", "enable"]},
                            "malformed-header-allow": {"required": False, "type": "str",
                                                       "choices": ["discard", "pass", "respond"]},
                            "malformed-header-call-id": {"required": False, "type": "str",
                                                         "choices": ["discard", "pass", "respond"]},
                            "malformed-header-contact": {"required": False, "type": "str",
                                                         "choices": ["discard", "pass", "respond"]},
                            "malformed-header-content-length": {"required": False, "type": "str",
                                                                "choices": ["discard", "pass", "respond"]},
                            "malformed-header-content-type": {"required": False, "type": "str",
                                                              "choices": ["discard", "pass", "respond"]},
                            "malformed-header-cseq": {"required": False, "type": "str",
                                                      "choices": ["discard", "pass", "respond"]},
                            "malformed-header-expires": {"required": False, "type": "str",
                                                         "choices": ["discard", "pass", "respond"]},
                            "malformed-header-from": {"required": False, "type": "str",
                                                      "choices": ["discard", "pass", "respond"]},
                            "malformed-header-max-forwards": {"required": False, "type": "str",
                                                              "choices": ["discard", "pass", "respond"]},
                            "malformed-header-p-asserted-identity": {"required": False, "type": "str",
                                                                     "choices": ["discard", "pass", "respond"]},
                            "malformed-header-rack": {"required": False, "type": "str",
                                                      "choices": ["discard", "pass", "respond"]},
                            "malformed-header-record-route": {"required": False, "type": "str",
                                                              "choices": ["discard", "pass", "respond"]},
                            "malformed-header-route": {"required": False, "type": "str",
                                                       "choices": ["discard", "pass", "respond"]},
                            "malformed-header-rseq": {"required": False, "type": "str",
                                                      "choices": ["discard", "pass", "respond"]},
                            "malformed-header-sdp-a": {"required": False, "type": "str",
                                                       "choices": ["discard", "pass", "respond"]},
                            "malformed-header-sdp-b": {"required": False, "type": "str",
                                                       "choices": ["discard", "pass", "respond"]},
                            "malformed-header-sdp-c": {"required": False, "type": "str",
                                                       "choices": ["discard", "pass", "respond"]},
                            "malformed-header-sdp-i": {"required": False, "type": "str",
                                                       "choices": ["discard", "pass", "respond"]},
                            "malformed-header-sdp-k": {"required": False, "type": "str",
                                                       "choices": ["discard", "pass", "respond"]},
                            "malformed-header-sdp-m": {"required": False, "type": "str",
                                                       "choices": ["discard", "pass", "respond"]},
                            "malformed-header-sdp-o": {"required": False, "type": "str",
                                                       "choices": ["discard", "pass", "respond"]},
                            "malformed-header-sdp-r": {"required": False, "type": "str",
                                                       "choices": ["discard", "pass", "respond"]},
                            "malformed-header-sdp-s": {"required": False, "type": "str",
                                                       "choices": ["discard", "pass", "respond"]},
                            "malformed-header-sdp-t": {"required": False, "type": "str",
                                                       "choices": ["discard", "pass", "respond"]},
                            "malformed-header-sdp-v": {"required": False, "type": "str",
                                                       "choices": ["discard", "pass", "respond"]},
                            "malformed-header-sdp-z": {"required": False, "type": "str",
                                                       "choices": ["discard", "pass", "respond"]},
                            "malformed-header-to": {"required": False, "type": "str",
                                                    "choices": ["discard", "pass", "respond"]},
                            "malformed-header-via": {"required": False, "type": "str",
                                                     "choices": ["discard", "pass", "respond"]},
                            "malformed-request-line": {"required": False, "type": "str",
                                                       "choices": ["discard", "pass", "respond"]},
                            "max-body-length": {"required": False, "type": "int"},
                            "max-dialogs": {"required": False, "type": "int"},
                            "max-idle-dialogs": {"required": False, "type": "int"},
                            "max-line-length": {"required": False, "type": "int"},
                            "message-rate": {"required": False, "type": "int"},
                            "nat-trace": {"required": False, "type": "str",
                                          "choices": ["disable", "enable"]},
                            "no-sdp-fixup": {"required": False, "type": "str",
                                             "choices": ["disable", "enable"]},
                            "notify-rate": {"required": False, "type": "int"},
                            "open-contact-pinhole": {"required": False, "type": "str",
                                                     "choices": ["disable", "enable"]},
                            "open-record-route-pinhole": {"required": False, "type": "str",
                                                          "choices": ["disable", "enable"]},
                            "open-register-pinhole": {"required": False, "type": "str",
                                                      "choices": ["disable", "enable"]},
                            "open-via-pinhole": {"required": False, "type": "str",
                                                 "choices": ["disable", "enable"]},
                            "options-rate": {"required": False, "type": "int"},
                            "prack-rate": {"required": False, "type": "int"},
                            "preserve-override": {"required": False, "type": "str",
                                                  "choices": ["disable", "enable"]},
                            "provisional-invite-expiry-time": {"required": False, "type": "int"},
                            "publish-rate": {"required": False, "type": "int"},
                            "refer-rate": {"required": False, "type": "int"},
                            "register-contact-trace": {"required": False, "type": "str",
                                                       "choices": ["disable", "enable"]},
                            "register-rate": {"required": False, "type": "int"},
                            "rfc2543-branch": {"required": False, "type": "str",
                                               "choices": ["disable", "enable"]},
                            "rtp": {"required": False, "type": "str",
                                    "choices": ["disable", "enable"]},
                            "ssl-algorithm": {"required": False, "type": "str",
                                              "choices": ["high", "medium", "low"]},
                            "ssl-auth-client": {"required": False, "type": "str"},
                            "ssl-auth-server": {"required": False, "type": "str"},
                            "ssl-client-certificate": {"required": False, "type": "str"},
                            "ssl-client-renegotiation": {"required": False, "type": "str",
                                                         "choices": ["allow", "deny", "secure"]},
                            "ssl-max-version": {"required": False, "type": "str",
                                                "choices": ["ssl-3.0", "tls-1.0", "tls-1.1",
                                                            "tls-1.2"]},
                            "ssl-min-version": {"required": False, "type": "str",
                                                "choices": ["ssl-3.0", "tls-1.0", "tls-1.1",
                                                            "tls-1.2"]},
                            "ssl-mode": {"required": False, "type": "str",
                                         "choices": ["off", "full"]},
                            "ssl-pfs": {"required": False, "type": "str",
                                        "choices": ["require", "deny", "allow"]},
                            "ssl-send-empty-frags": {"required": False, "type": "str",
                                                     "choices": ["enable", "disable"]},
                            "ssl-server-certificate": {"required": False, "type": "str"},
                            "status": {"required": False, "type": "str",
                                       "choices": ["disable", "enable"]},
                            "strict-register": {"required": False, "type": "str",
                                                "choices": ["disable", "enable"]},
                            "subscribe-rate": {"required": False, "type": "int"},
                            "unknown-header": {"required": False, "type": "str",
                                               "choices": ["discard", "pass", "respond"]},
                            "update-rate": {"required": False, "type": "int"}
                        }}

            }
        }
    }

    module = AnsibleModule(argument_spec=fields,
                           supports_check_mode=False)
    try:
        from fortiosapi import FortiOSAPI
    except ImportError:
        module.fail_json(msg="fortiosapi module is required")

    fos = FortiOSAPI()

    is_error, has_changed, result = fortios_voip(module.params, fos)

    if not is_error:
        module.exit_json(changed=has_changed, meta=result)
    else:
        module.fail_json(msg="Error in repo", meta=result)


if __name__ == '__main__':
    main()
