#!/usr/bin/python
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.
#

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'metadata_version': '1.1'}

DOCUMENTATION = '''
---
module: fmgr_secprof_voip
version_added: "2.8"
notes:
    - Full Documentation at U(https://ftnt-ansible-docs.readthedocs.io/en/latest/).
author:
    - Luke Weighall (@lweighall)
    - Andrew Welsh (@Ghilli3)
    - Jim Huber (@p4r4n0y1ng)
short_description: VOIP security profiles in FMG
description:
  -  Manage VOIP security profiles in FortiManager via API

options:
  adom:
    description:
      - The ADOM the configuration should belong to.
    required: false
    default: root

  mode:
    description:
      - Sets one of three modes for managing the object.
      - Allows use of soft-adds instead of overwriting existing values
    choices: ['add', 'set', 'delete', 'update']
    required: false
    default: add

  name:
    description:
      - Profile name.
    required: false

  comment:
    description:
      - Comment.
    required: false

  sccp:
    description:
      - EXPERTS ONLY! KNOWLEDGE OF FMGR JSON API IS REQUIRED!
      - List of multiple child objects to be added. Expects a list of dictionaries.
      - Dictionaries must use FortiManager API parameters, not the ansible ones listed below.
      - If submitted, all other prefixed sub-parameters ARE IGNORED.
      - This object is MUTUALLY EXCLUSIVE with its options.
      - We expect that you know what you are doing with these list parameters, and are leveraging the JSON API Guide.
      - WHEN IN DOUBT, USE THE SUB OPTIONS BELOW INSTEAD TO CREATE OBJECTS WITH MULTIPLE TASKS
    required: false

  sccp_block_mcast:
    description:
      - Enable/disable block multicast RTP connections.
      - choice | disable | Disable status.
      - choice | enable | Enable status.
    required: false
    choices: ["disable", "enable"]

  sccp_log_call_summary:
    description:
      - Enable/disable log summary of SCCP calls.
      - choice | disable | Disable status.
      - choice | enable | Enable status.
    required: false
    choices: ["disable", "enable"]

  sccp_log_violations:
    description:
      - Enable/disable logging of SCCP violations.
      - choice | disable | Disable status.
      - choice | enable | Enable status.
    required: false
    choices: ["disable", "enable"]

  sccp_max_calls:
    description:
      - Maximum calls per minute per SCCP client (max 65535).
    required: false

  sccp_status:
    description:
      - Enable/disable SCCP.
      - choice | disable | Disable status.
      - choice | enable | Enable status.
    required: false
    choices: ["disable", "enable"]

  sccp_verify_header:
    description:
      - Enable/disable verify SCCP header content.
      - choice | disable | Disable status.
      - choice | enable | Enable status.
    required: false
    choices: ["disable", "enable"]

  sip:
    description:
      - EXPERTS ONLY! KNOWLEDGE OF FMGR JSON API IS REQUIRED!
      - List of multiple child objects to be added. Expects a list of dictionaries.
      - Dictionaries must use FortiManager API parameters, not the ansible ones listed below.
      - If submitted, all other prefixed sub-parameters ARE IGNORED.
      - This object is MUTUALLY EXCLUSIVE with its options.
      - We expect that you know what you are doing with these list parameters, and are leveraging the JSON API Guide.
      - WHEN IN DOUBT, USE THE SUB OPTIONS BELOW INSTEAD TO CREATE OBJECTS WITH MULTIPLE TASKS
    required: false

  sip_ack_rate:
    description:
      - ACK request rate limit (per second, per policy).
    required: false

  sip_block_ack:
    description:
      - Enable/disable block ACK requests.
      - choice | disable | Disable status.
      - choice | enable | Enable status.
    required: false
    choices: ["disable", "enable"]

  sip_block_bye:
    description:
      - Enable/disable block BYE requests.
      - choice | disable | Disable status.
      - choice | enable | Enable status.
    required: false
    choices: ["disable", "enable"]

  sip_block_cancel:
    description:
      - Enable/disable block CANCEL requests.
      - choice | disable | Disable status.
      - choice | enable | Enable status.
    required: false
    choices: ["disable", "enable"]

  sip_block_geo_red_options:
    description:
      - Enable/disable block OPTIONS requests, but OPTIONS requests still notify for redundancy.
      - choice | disable | Disable status.
      - choice | enable | Enable status.
    required: false
    choices: ["disable", "enable"]

  sip_block_info:
    description:
      - Enable/disable block INFO requests.
      - choice | disable | Disable status.
      - choice | enable | Enable status.
    required: false
    choices: ["disable", "enable"]

  sip_block_invite:
    description:
      - Enable/disable block INVITE requests.
      - choice | disable | Disable status.
      - choice | enable | Enable status.
    required: false
    choices: ["disable", "enable"]

  sip_block_long_lines:
    description:
      - Enable/disable block requests with headers exceeding max-line-length.
      - choice | disable | Disable status.
      - choice | enable | Enable status.
    required: false
    choices: ["disable", "enable"]

  sip_block_message:
    description:
      - Enable/disable block MESSAGE requests.
      - choice | disable | Disable status.
      - choice | enable | Enable status.
    required: false
    choices: ["disable", "enable"]

  sip_block_notify:
    description:
      - Enable/disable block NOTIFY requests.
      - choice | disable | Disable status.
      - choice | enable | Enable status.
    required: false
    choices: ["disable", "enable"]

  sip_block_options:
    description:
      - Enable/disable block OPTIONS requests and no OPTIONS as notifying message for redundancy either.
      - choice | disable | Disable status.
      - choice | enable | Enable status.
    required: false
    choices: ["disable", "enable"]

  sip_block_prack:
    description:
      - Enable/disable block prack requests.
      - choice | disable | Disable status.
      - choice | enable | Enable status.
    required: false
    choices: ["disable", "enable"]

  sip_block_publish:
    description:
      - Enable/disable block PUBLISH requests.
      - choice | disable | Disable status.
      - choice | enable | Enable status.
    required: false
    choices: ["disable", "enable"]

  sip_block_refer:
    description:
      - Enable/disable block REFER requests.
      - choice | disable | Disable status.
      - choice | enable | Enable status.
    required: false
    choices: ["disable", "enable"]

  sip_block_register:
    description:
      - Enable/disable block REGISTER requests.
      - choice | disable | Disable status.
      - choice | enable | Enable status.
    required: false
    choices: ["disable", "enable"]

  sip_block_subscribe:
    description:
      - Enable/disable block SUBSCRIBE requests.
      - choice | disable | Disable status.
      - choice | enable | Enable status.
    required: false
    choices: ["disable", "enable"]

  sip_block_unknown:
    description:
      - Block unrecognized SIP requests (enabled by default).
      - choice | disable | Disable status.
      - choice | enable | Enable status.
    required: false
    choices: ["disable", "enable"]

  sip_block_update:
    description:
      - Enable/disable block UPDATE requests.
      - choice | disable | Disable status.
      - choice | enable | Enable status.
    required: false
    choices: ["disable", "enable"]

  sip_bye_rate:
    description:
      - BYE request rate limit (per second, per policy).
    required: false

  sip_call_keepalive:
    description:
      - Continue tracking calls with no RTP for this many minutes.
    required: false

  sip_cancel_rate:
    description:
      - CANCEL request rate limit (per second, per policy).
    required: false

  sip_contact_fixup:
    description:
      - Fixup contact anyway even if contact's IP|port doesn't match session's IP|port.
      - choice | disable | Disable status.
      - choice | enable | Enable status.
    required: false
    choices: ["disable", "enable"]

  sip_hnt_restrict_source_ip:
    description:
      - Enable/disable restrict RTP source IP to be the same as SIP source IP when HNT is enabled.
      - choice | disable | Disable status.
      - choice | enable | Enable status.
    required: false
    choices: ["disable", "enable"]

  sip_hosted_nat_traversal:
    description:
      - Hosted NAT Traversal (HNT).
      - choice | disable | Disable status.
      - choice | enable | Enable status.
    required: false
    choices: ["disable", "enable"]

  sip_info_rate:
    description:
      - INFO request rate limit (per second, per policy).
    required: false

  sip_invite_rate:
    description:
      - INVITE request rate limit (per second, per policy).
    required: false

  sip_ips_rtp:
    description:
      - Enable/disable allow IPS on RTP.
      - choice | disable | Disable status.
      - choice | enable | Enable status.
    required: false
    choices: ["disable", "enable"]

  sip_log_call_summary:
    description:
      - Enable/disable logging of SIP call summary.
      - choice | disable | Disable status.
      - choice | enable | Enable status.
    required: false
    choices: ["disable", "enable"]

  sip_log_violations:
    description:
      - Enable/disable logging of SIP violations.
      - choice | disable | Disable status.
      - choice | enable | Enable status.
    required: false
    choices: ["disable", "enable"]

  sip_malformed_header_allow:
    description:
      - Action for malformed Allow header.
      - choice | pass | Bypass malformed messages.
      - choice | discard | Discard malformed messages.
      - choice | respond | Respond with error code.
    required: false
    choices: ["pass", "discard", "respond"]

  sip_malformed_header_call_id:
    description:
      - Action for malformed Call-ID header.
      - choice | pass | Bypass malformed messages.
      - choice | discard | Discard malformed messages.
      - choice | respond | Respond with error code.
    required: false
    choices: ["pass", "discard", "respond"]

  sip_malformed_header_contact:
    description:
      - Action for malformed Contact header.
      - choice | pass | Bypass malformed messages.
      - choice | discard | Discard malformed messages.
      - choice | respond | Respond with error code.
    required: false
    choices: ["pass", "discard", "respond"]

  sip_malformed_header_content_length:
    description:
      - Action for malformed Content-Length header.
      - choice | pass | Bypass malformed messages.
      - choice | discard | Discard malformed messages.
      - choice | respond | Respond with error code.
    required: false
    choices: ["pass", "discard", "respond"]

  sip_malformed_header_content_type:
    description:
      - Action for malformed Content-Type header.
      - choice | pass | Bypass malformed messages.
      - choice | discard | Discard malformed messages.
      - choice | respond | Respond with error code.
    required: false
    choices: ["pass", "discard", "respond"]

  sip_malformed_header_cseq:
    description:
      - Action for malformed CSeq header.
      - choice | pass | Bypass malformed messages.
      - choice | discard | Discard malformed messages.
      - choice | respond | Respond with error code.
    required: false
    choices: ["pass", "discard", "respond"]

  sip_malformed_header_expires:
    description:
      - Action for malformed Expires header.
      - choice | pass | Bypass malformed messages.
      - choice | discard | Discard malformed messages.
      - choice | respond | Respond with error code.
    required: false
    choices: ["pass", "discard", "respond"]

  sip_malformed_header_from:
    description:
      - Action for malformed From header.
      - choice | pass | Bypass malformed messages.
      - choice | discard | Discard malformed messages.
      - choice | respond | Respond with error code.
    required: false
    choices: ["pass", "discard", "respond"]

  sip_malformed_header_max_forwards:
    description:
      - Action for malformed Max-Forwards header.
      - choice | pass | Bypass malformed messages.
      - choice | discard | Discard malformed messages.
      - choice | respond | Respond with error code.
    required: false
    choices: ["pass", "discard", "respond"]

  sip_malformed_header_p_asserted_identity:
    description:
      - Action for malformed P-Asserted-Identity header.
      - choice | pass | Bypass malformed messages.
      - choice | discard | Discard malformed messages.
      - choice | respond | Respond with error code.
    required: false
    choices: ["pass", "discard", "respond"]

  sip_malformed_header_rack:
    description:
      - Action for malformed RAck header.
      - choice | pass | Bypass malformed messages.
      - choice | discard | Discard malformed messages.
      - choice | respond | Respond with error code.
    required: false
    choices: ["pass", "discard", "respond"]

  sip_malformed_header_record_route:
    description:
      - Action for malformed Record-Route header.
      - choice | pass | Bypass malformed messages.
      - choice | discard | Discard malformed messages.
      - choice | respond | Respond with error code.
    required: false
    choices: ["pass", "discard", "respond"]

  sip_malformed_header_route:
    description:
      - Action for malformed Route header.
      - choice | pass | Bypass malformed messages.
      - choice | discard | Discard malformed messages.
      - choice | respond | Respond with error code.
    required: false
    choices: ["pass", "discard", "respond"]

  sip_malformed_header_rseq:
    description:
      - Action for malformed RSeq header.
      - choice | pass | Bypass malformed messages.
      - choice | discard | Discard malformed messages.
      - choice | respond | Respond with error code.
    required: false
    choices: ["pass", "discard", "respond"]

  sip_malformed_header_sdp_a:
    description:
      - Action for malformed SDP a line.
      - choice | pass | Bypass malformed messages.
      - choice | discard | Discard malformed messages.
      - choice | respond | Respond with error code.
    required: false
    choices: ["pass", "discard", "respond"]

  sip_malformed_header_sdp_b:
    description:
      - Action for malformed SDP b line.
      - choice | pass | Bypass malformed messages.
      - choice | discard | Discard malformed messages.
      - choice | respond | Respond with error code.
    required: false
    choices: ["pass", "discard", "respond"]

  sip_malformed_header_sdp_c:
    description:
      - Action for malformed SDP c line.
      - choice | pass | Bypass malformed messages.
      - choice | discard | Discard malformed messages.
      - choice | respond | Respond with error code.
    required: false
    choices: ["pass", "discard", "respond"]

  sip_malformed_header_sdp_i:
    description:
      - Action for malformed SDP i line.
      - choice | pass | Bypass malformed messages.
      - choice | discard | Discard malformed messages.
      - choice | respond | Respond with error code.
    required: false
    choices: ["pass", "discard", "respond"]

  sip_malformed_header_sdp_k:
    description:
      - Action for malformed SDP k line.
      - choice | pass | Bypass malformed messages.
      - choice | discard | Discard malformed messages.
      - choice | respond | Respond with error code.
    required: false
    choices: ["pass", "discard", "respond"]

  sip_malformed_header_sdp_m:
    description:
      - Action for malformed SDP m line.
      - choice | pass | Bypass malformed messages.
      - choice | discard | Discard malformed messages.
      - choice | respond | Respond with error code.
    required: false
    choices: ["pass", "discard", "respond"]

  sip_malformed_header_sdp_o:
    description:
      - Action for malformed SDP o line.
      - choice | pass | Bypass malformed messages.
      - choice | discard | Discard malformed messages.
      - choice | respond | Respond with error code.
    required: false
    choices: ["pass", "discard", "respond"]

  sip_malformed_header_sdp_r:
    description:
      - Action for malformed SDP r line.
      - choice | pass | Bypass malformed messages.
      - choice | discard | Discard malformed messages.
      - choice | respond | Respond with error code.
    required: false
    choices: ["pass", "discard", "respond"]

  sip_malformed_header_sdp_s:
    description:
      - Action for malformed SDP s line.
      - choice | pass | Bypass malformed messages.
      - choice | discard | Discard malformed messages.
      - choice | respond | Respond with error code.
    required: false
    choices: ["pass", "discard", "respond"]

  sip_malformed_header_sdp_t:
    description:
      - Action for malformed SDP t line.
      - choice | pass | Bypass malformed messages.
      - choice | discard | Discard malformed messages.
      - choice | respond | Respond with error code.
    required: false
    choices: ["pass", "discard", "respond"]

  sip_malformed_header_sdp_v:
    description:
      - Action for malformed SDP v line.
      - choice | pass | Bypass malformed messages.
      - choice | discard | Discard malformed messages.
      - choice | respond | Respond with error code.
    required: false
    choices: ["pass", "discard", "respond"]

  sip_malformed_header_sdp_z:
    description:
      - Action for malformed SDP z line.
      - choice | pass | Bypass malformed messages.
      - choice | discard | Discard malformed messages.
      - choice | respond | Respond with error code.
    required: false
    choices: ["pass", "discard", "respond"]

  sip_malformed_header_to:
    description:
      - Action for malformed To header.
      - choice | pass | Bypass malformed messages.
      - choice | discard | Discard malformed messages.
      - choice | respond | Respond with error code.
    required: false
    choices: ["pass", "discard", "respond"]

  sip_malformed_header_via:
    description:
      - Action for malformed VIA header.
      - choice | pass | Bypass malformed messages.
      - choice | discard | Discard malformed messages.
      - choice | respond | Respond with error code.
    required: false
    choices: ["pass", "discard", "respond"]

  sip_malformed_request_line:
    description:
      - Action for malformed request line.
      - choice | pass | Bypass malformed messages.
      - choice | discard | Discard malformed messages.
      - choice | respond | Respond with error code.
    required: false
    choices: ["pass", "discard", "respond"]

  sip_max_body_length:
    description:
      - Maximum SIP message body length (0 meaning no limit).
    required: false

  sip_max_dialogs:
    description:
      - Maximum number of concurrent calls/dialogs (per policy).
    required: false

  sip_max_idle_dialogs:
    description:
      - Maximum number established but idle dialogs to retain (per policy).
    required: false

  sip_max_line_length:
    description:
      - Maximum SIP header line length (78-4096).
    required: false

  sip_message_rate:
    description:
      - MESSAGE request rate limit (per second, per policy).
    required: false

  sip_nat_trace:
    description:
      - Enable/disable preservation of original IP in SDP i line.
      - choice | disable | Disable status.
      - choice | enable | Enable status.
    required: false
    choices: ["disable", "enable"]

  sip_no_sdp_fixup:
    description:
      - Enable/disable no SDP fix-up.
      - choice | disable | Disable status.
      - choice | enable | Enable status.
    required: false
    choices: ["disable", "enable"]

  sip_notify_rate:
    description:
      - NOTIFY request rate limit (per second, per policy).
    required: false

  sip_open_contact_pinhole:
    description:
      - Enable/disable open pinhole for non-REGISTER Contact port.
      - choice | disable | Disable status.
      - choice | enable | Enable status.
    required: false
    choices: ["disable", "enable"]

  sip_open_record_route_pinhole:
    description:
      - Enable/disable open pinhole for Record-Route port.
      - choice | disable | Disable status.
      - choice | enable | Enable status.
    required: false
    choices: ["disable", "enable"]

  sip_open_register_pinhole:
    description:
      - Enable/disable open pinhole for REGISTER Contact port.
      - choice | disable | Disable status.
      - choice | enable | Enable status.
    required: false
    choices: ["disable", "enable"]

  sip_open_via_pinhole:
    description:
      - Enable/disable open pinhole for Via port.
      - choice | disable | Disable status.
      - choice | enable | Enable status.
    required: false
    choices: ["disable", "enable"]

  sip_options_rate:
    description:
      - OPTIONS request rate limit (per second, per policy).
    required: false

  sip_prack_rate:
    description:
      - PRACK request rate limit (per second, per policy).
    required: false

  sip_preserve_override:
    description:
      - Override i line to preserve original IPS (default| append).
      - choice | disable | Disable status.
      - choice | enable | Enable status.
    required: false
    choices: ["disable", "enable"]

  sip_provisional_invite_expiry_time:
    description:
      - Expiry time for provisional INVITE (10 - 3600 sec).
    required: false

  sip_publish_rate:
    description:
      - PUBLISH request rate limit (per second, per policy).
    required: false

  sip_refer_rate:
    description:
      - REFER request rate limit (per second, per policy).
    required: false

  sip_register_contact_trace:
    description:
      - Enable/disable trace original IP/port within the contact header of REGISTER requests.
      - choice | disable | Disable status.
      - choice | enable | Enable status.
    required: false
    choices: ["disable", "enable"]

  sip_register_rate:
    description:
      - REGISTER request rate limit (per second, per policy).
    required: false

  sip_rfc2543_branch:
    description:
      - Enable/disable support via branch compliant with RFC 2543.
      - choice | disable | Disable status.
      - choice | enable | Enable status.
    required: false
    choices: ["disable", "enable"]

  sip_rtp:
    description:
      - Enable/disable create pinholes for RTP traffic to traverse firewall.
      - choice | disable | Disable status.
      - choice | enable | Enable status.
    required: false
    choices: ["disable", "enable"]

  sip_ssl_algorithm:
    description:
      - Relative strength of encryption algorithms accepted in negotiation.
      - choice | high | High encryption. Allow only AES and ChaCha.
      - choice | medium | Medium encryption. Allow AES, ChaCha, 3DES, and RC4.
      - choice | low | Low encryption. Allow AES, ChaCha, 3DES, RC4, and DES.
    required: false
    choices: ["high", "medium", "low"]

  sip_ssl_auth_client:
    description:
      - Require a client certificate and authenticate it with the peer/peergrp.
    required: false

  sip_ssl_auth_server:
    description:
      - Authenticate the server's certificate with the peer/peergrp.
    required: false

  sip_ssl_client_certificate:
    description:
      - Name of Certificate to offer to server if requested.
    required: false

  sip_ssl_client_renegotiation:
    description:
      - Allow/block client renegotiation by server.
      - choice | allow | Allow a SSL client to renegotiate.
      - choice | deny | Abort any SSL connection that attempts to renegotiate.
      - choice | secure | Reject any SSL connection that does not offer a RFC 5746 Secure Renegotiation Indication.
    required: false
    choices: ["allow", "deny", "secure"]

  sip_ssl_max_version:
    description:
      - Highest SSL/TLS version to negotiate.
      - choice | ssl-3.0 | SSL 3.0.
      - choice | tls-1.0 | TLS 1.0.
      - choice | tls-1.1 | TLS 1.1.
      - choice | tls-1.2 | TLS 1.2.
    required: false
    choices: ["ssl-3.0", "tls-1.0", "tls-1.1", "tls-1.2"]

  sip_ssl_min_version:
    description:
      - Lowest SSL/TLS version to negotiate.
      - choice | ssl-3.0 | SSL 3.0.
      - choice | tls-1.0 | TLS 1.0.
      - choice | tls-1.1 | TLS 1.1.
      - choice | tls-1.2 | TLS 1.2.
    required: false
    choices: ["ssl-3.0", "tls-1.0", "tls-1.1", "tls-1.2"]

  sip_ssl_mode:
    description:
      - SSL/TLS mode for encryption &amp; decryption of traffic.
      - choice | off | No SSL.
      - choice | full | Client to FortiGate and FortiGate to Server SSL.
    required: false
    choices: ["off", "full"]

  sip_ssl_pfs:
    description:
      - SSL Perfect Forward Secrecy.
      - choice | require | PFS mandatory.
      - choice | deny | PFS rejected.
      - choice | allow | PFS allowed.
    required: false
    choices: ["require", "deny", "allow"]

  sip_ssl_send_empty_frags:
    description:
      - Send empty fragments to avoid attack on CBC IV (SSL 3.0 &amp; TLS 1.0 only).
      - choice | disable | Do not send empty fragments.
      - choice | enable | Send empty fragments.
    required: false
    choices: ["disable", "enable"]

  sip_ssl_server_certificate:
    description:
      - Name of Certificate return to the client in every SSL connection.
    required: false

  sip_status:
    description:
      - Enable/disable SIP.
      - choice | disable | Disable status.
      - choice | enable | Enable status.
    required: false
    choices: ["disable", "enable"]

  sip_strict_register:
    description:
      - Enable/disable only allow the registrar to connect.
      - choice | disable | Disable status.
      - choice | enable | Enable status.
    required: false
    choices: ["disable", "enable"]

  sip_subscribe_rate:
    description:
      - SUBSCRIBE request rate limit (per second, per policy).
    required: false

  sip_unknown_header:
    description:
      - Action for unknown SIP header.
      - choice | pass | Bypass malformed messages.
      - choice | discard | Discard malformed messages.
      - choice | respond | Respond with error code.
    required: false
    choices: ["pass", "discard", "respond"]

  sip_update_rate:
    description:
      - UPDATE request rate limit (per second, per policy).
    required: false


'''

EXAMPLES = '''
  - name: DELETE Profile
    fmgr_secprof_voip:
      name: "Ansible_VOIP_Profile"
      mode: "delete"

  - name: Create FMGR_VOIP_PROFILE
    fmgr_secprof_voip:
      mode: "set"
      adom: "root"
      name: "Ansible_VOIP_Profile"
      comment: "Created by Ansible"
      sccp: {block-mcast: "enable", log-call-summary: "enable", log-violations: "enable", status: "enable"}
'''

RETURN = """
api_result:
  description: full API response, includes status code and message
  returned: always
  type: str
"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.connection import Connection
from ansible.module_utils.network.fortimanager.fortimanager import FortiManagerHandler
from ansible.module_utils.network.fortimanager.common import FMGBaseException
from ansible.module_utils.network.fortimanager.common import FMGRCommon
from ansible.module_utils.network.fortimanager.common import DEFAULT_RESULT_OBJ
from ansible.module_utils.network.fortimanager.common import FAIL_SOCKET_MSG
from ansible.module_utils.network.fortimanager.common import prepare_dict
from ansible.module_utils.network.fortimanager.common import scrub_dict


###############
# START METHODS
###############


def fmgr_voip_profile_modify(fmgr, paramgram):
    """
    :param fmgr: The fmgr object instance from fortimanager.py
    :type fmgr: class object
    :param paramgram: The formatted dictionary of options to process
    :type paramgram: dict
    :return: The response from the FortiManager
    :rtype: dict
    """

    mode = paramgram["mode"]
    adom = paramgram["adom"]

    response = DEFAULT_RESULT_OBJ
    url = ""
    datagram = {}

    # EVAL THE MODE PARAMETER FOR SET OR ADD
    if mode in ['set', 'add', 'update']:
        url = '/pm/config/adom/{adom}/obj/voip/profile'.format(adom=adom)
        datagram = scrub_dict(prepare_dict(paramgram))

    # EVAL THE MODE PARAMETER FOR DELETE
    elif mode == "delete":
        # SET THE CORRECT URL FOR DELETE
        url = '/pm/config/adom/{adom}/obj/voip/profile/{name}'.format(adom=adom, name=paramgram["name"])
        datagram = {}

    response = fmgr.process_request(url, datagram, paramgram["mode"])

    return response


#############
# END METHODS
#############


def main():
    argument_spec = dict(
        adom=dict(type="str", default="root"),
        mode=dict(choices=["add", "set", "delete", "update"], type="str", default="add"),

        name=dict(required=False, type="str"),
        comment=dict(required=False, type="str"),
        sccp=dict(required=False, type="dict"),
        sccp_block_mcast=dict(required=False, type="str", choices=["disable", "enable"]),
        sccp_log_call_summary=dict(required=False, type="str", choices=["disable", "enable"]),
        sccp_log_violations=dict(required=False, type="str", choices=["disable", "enable"]),
        sccp_max_calls=dict(required=False, type="int"),
        sccp_status=dict(required=False, type="str", choices=["disable", "enable"]),
        sccp_verify_header=dict(required=False, type="str", choices=["disable", "enable"]),
        sip=dict(required=False, type="dict"),
        sip_ack_rate=dict(required=False, type="int"),
        sip_block_ack=dict(required=False, type="str", choices=["disable", "enable"]),
        sip_block_bye=dict(required=False, type="str", choices=["disable", "enable"]),
        sip_block_cancel=dict(required=False, type="str", choices=["disable", "enable"]),
        sip_block_geo_red_options=dict(required=False, type="str", choices=["disable", "enable"]),
        sip_block_info=dict(required=False, type="str", choices=["disable", "enable"]),
        sip_block_invite=dict(required=False, type="str", choices=["disable", "enable"]),
        sip_block_long_lines=dict(required=False, type="str", choices=["disable", "enable"]),
        sip_block_message=dict(required=False, type="str", choices=["disable", "enable"]),
        sip_block_notify=dict(required=False, type="str", choices=["disable", "enable"]),
        sip_block_options=dict(required=False, type="str", choices=["disable", "enable"]),
        sip_block_prack=dict(required=False, type="str", choices=["disable", "enable"]),
        sip_block_publish=dict(required=False, type="str", choices=["disable", "enable"]),
        sip_block_refer=dict(required=False, type="str", choices=["disable", "enable"]),
        sip_block_register=dict(required=False, type="str", choices=["disable", "enable"]),
        sip_block_subscribe=dict(required=False, type="str", choices=["disable", "enable"]),
        sip_block_unknown=dict(required=False, type="str", choices=["disable", "enable"]),
        sip_block_update=dict(required=False, type="str", choices=["disable", "enable"]),
        sip_bye_rate=dict(required=False, type="int"),
        sip_call_keepalive=dict(required=False, type="int"),
        sip_cancel_rate=dict(required=False, type="int"),
        sip_contact_fixup=dict(required=False, type="str", choices=["disable", "enable"]),
        sip_hnt_restrict_source_ip=dict(required=False, type="str", choices=["disable", "enable"]),
        sip_hosted_nat_traversal=dict(required=False, type="str", choices=["disable", "enable"]),
        sip_info_rate=dict(required=False, type="int"),
        sip_invite_rate=dict(required=False, type="int"),
        sip_ips_rtp=dict(required=False, type="str", choices=["disable", "enable"]),
        sip_log_call_summary=dict(required=False, type="str", choices=["disable", "enable"]),
        sip_log_violations=dict(required=False, type="str", choices=["disable", "enable"]),
        sip_malformed_header_allow=dict(required=False, type="str", choices=["pass", "discard", "respond"]),
        sip_malformed_header_call_id=dict(required=False, type="str", choices=["pass", "discard", "respond"]),
        sip_malformed_header_contact=dict(required=False, type="str", choices=["pass", "discard", "respond"]),
        sip_malformed_header_content_length=dict(required=False, type="str", choices=["pass", "discard", "respond"]),
        sip_malformed_header_content_type=dict(required=False, type="str", choices=["pass", "discard", "respond"]),
        sip_malformed_header_cseq=dict(required=False, type="str", choices=["pass", "discard", "respond"]),
        sip_malformed_header_expires=dict(required=False, type="str", choices=["pass", "discard", "respond"]),
        sip_malformed_header_from=dict(required=False, type="str", choices=["pass", "discard", "respond"]),
        sip_malformed_header_max_forwards=dict(required=False, type="str", choices=["pass", "discard", "respond"]),
        sip_malformed_header_p_asserted_identity=dict(required=False, type="str", choices=["pass",
                                                                                           "discard",
                                                                                           "respond"]),
        sip_malformed_header_rack=dict(required=False, type="str", choices=["pass", "discard", "respond"]),
        sip_malformed_header_record_route=dict(required=False, type="str", choices=["pass", "discard", "respond"]),
        sip_malformed_header_route=dict(required=False, type="str", choices=["pass", "discard", "respond"]),
        sip_malformed_header_rseq=dict(required=False, type="str", choices=["pass", "discard", "respond"]),
        sip_malformed_header_sdp_a=dict(required=False, type="str", choices=["pass", "discard", "respond"]),
        sip_malformed_header_sdp_b=dict(required=False, type="str", choices=["pass", "discard", "respond"]),
        sip_malformed_header_sdp_c=dict(required=False, type="str", choices=["pass", "discard", "respond"]),
        sip_malformed_header_sdp_i=dict(required=False, type="str", choices=["pass", "discard", "respond"]),
        sip_malformed_header_sdp_k=dict(required=False, type="str", choices=["pass", "discard", "respond"]),
        sip_malformed_header_sdp_m=dict(required=False, type="str", choices=["pass", "discard", "respond"]),
        sip_malformed_header_sdp_o=dict(required=False, type="str", choices=["pass", "discard", "respond"]),
        sip_malformed_header_sdp_r=dict(required=False, type="str", choices=["pass", "discard", "respond"]),
        sip_malformed_header_sdp_s=dict(required=False, type="str", choices=["pass", "discard", "respond"]),
        sip_malformed_header_sdp_t=dict(required=False, type="str", choices=["pass", "discard", "respond"]),
        sip_malformed_header_sdp_v=dict(required=False, type="str", choices=["pass", "discard", "respond"]),
        sip_malformed_header_sdp_z=dict(required=False, type="str", choices=["pass", "discard", "respond"]),
        sip_malformed_header_to=dict(required=False, type="str", choices=["pass", "discard", "respond"]),
        sip_malformed_header_via=dict(required=False, type="str", choices=["pass", "discard", "respond"]),
        sip_malformed_request_line=dict(required=False, type="str", choices=["pass", "discard", "respond"]),
        sip_max_body_length=dict(required=False, type="int"),
        sip_max_dialogs=dict(required=False, type="int"),
        sip_max_idle_dialogs=dict(required=False, type="int"),
        sip_max_line_length=dict(required=False, type="int"),
        sip_message_rate=dict(required=False, type="int"),
        sip_nat_trace=dict(required=False, type="str", choices=["disable", "enable"]),
        sip_no_sdp_fixup=dict(required=False, type="str", choices=["disable", "enable"]),
        sip_notify_rate=dict(required=False, type="int"),
        sip_open_contact_pinhole=dict(required=False, type="str", choices=["disable", "enable"]),
        sip_open_record_route_pinhole=dict(required=False, type="str", choices=["disable", "enable"]),
        sip_open_register_pinhole=dict(required=False, type="str", choices=["disable", "enable"]),
        sip_open_via_pinhole=dict(required=False, type="str", choices=["disable", "enable"]),
        sip_options_rate=dict(required=False, type="int"),
        sip_prack_rate=dict(required=False, type="int"),
        sip_preserve_override=dict(required=False, type="str", choices=["disable", "enable"]),
        sip_provisional_invite_expiry_time=dict(required=False, type="int"),
        sip_publish_rate=dict(required=False, type="int"),
        sip_refer_rate=dict(required=False, type="int"),
        sip_register_contact_trace=dict(required=False, type="str", choices=["disable", "enable"]),
        sip_register_rate=dict(required=False, type="int"),
        sip_rfc2543_branch=dict(required=False, type="str", choices=["disable", "enable"]),
        sip_rtp=dict(required=False, type="str", choices=["disable", "enable"]),
        sip_ssl_algorithm=dict(required=False, type="str", choices=["high", "medium", "low"]),
        sip_ssl_auth_client=dict(required=False, type="str"),
        sip_ssl_auth_server=dict(required=False, type="str"),
        sip_ssl_client_certificate=dict(required=False, type="str"),
        sip_ssl_client_renegotiation=dict(required=False, type="str", choices=["allow", "deny", "secure"]),
        sip_ssl_max_version=dict(required=False, type="str", choices=["ssl-3.0", "tls-1.0", "tls-1.1", "tls-1.2"]),
        sip_ssl_min_version=dict(required=False, type="str", choices=["ssl-3.0", "tls-1.0", "tls-1.1", "tls-1.2"]),
        sip_ssl_mode=dict(required=False, type="str", choices=["off", "full"]),
        sip_ssl_pfs=dict(required=False, type="str", choices=["require", "deny", "allow"]),
        sip_ssl_send_empty_frags=dict(required=False, type="str", choices=["disable", "enable"]),
        sip_ssl_server_certificate=dict(required=False, type="str"),
        sip_status=dict(required=False, type="str", choices=["disable", "enable"]),
        sip_strict_register=dict(required=False, type="str", choices=["disable", "enable"]),
        sip_subscribe_rate=dict(required=False, type="int"),
        sip_unknown_header=dict(required=False, type="str", choices=["pass", "discard", "respond"]),
        sip_update_rate=dict(required=False, type="int"),

    )

    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=False, )
    # MODULE PARAMGRAM
    paramgram = {
        "mode": module.params["mode"],
        "adom": module.params["adom"],
        "name": module.params["name"],
        "comment": module.params["comment"],
        "sccp": {
            "block-mcast": module.params["sccp_block_mcast"],
            "log-call-summary": module.params["sccp_log_call_summary"],
            "log-violations": module.params["sccp_log_violations"],
            "max-calls": module.params["sccp_max_calls"],
            "status": module.params["sccp_status"],
            "verify-header": module.params["sccp_verify_header"],
        },
        "sip": {
            "ack-rate": module.params["sip_ack_rate"],
            "block-ack": module.params["sip_block_ack"],
            "block-bye": module.params["sip_block_bye"],
            "block-cancel": module.params["sip_block_cancel"],
            "block-geo-red-options": module.params["sip_block_geo_red_options"],
            "block-info": module.params["sip_block_info"],
            "block-invite": module.params["sip_block_invite"],
            "block-long-lines": module.params["sip_block_long_lines"],
            "block-message": module.params["sip_block_message"],
            "block-notify": module.params["sip_block_notify"],
            "block-options": module.params["sip_block_options"],
            "block-prack": module.params["sip_block_prack"],
            "block-publish": module.params["sip_block_publish"],
            "block-refer": module.params["sip_block_refer"],
            "block-register": module.params["sip_block_register"],
            "block-subscribe": module.params["sip_block_subscribe"],
            "block-unknown": module.params["sip_block_unknown"],
            "block-update": module.params["sip_block_update"],
            "bye-rate": module.params["sip_bye_rate"],
            "call-keepalive": module.params["sip_call_keepalive"],
            "cancel-rate": module.params["sip_cancel_rate"],
            "contact-fixup": module.params["sip_contact_fixup"],
            "hnt-restrict-source-ip": module.params["sip_hnt_restrict_source_ip"],
            "hosted-nat-traversal": module.params["sip_hosted_nat_traversal"],
            "info-rate": module.params["sip_info_rate"],
            "invite-rate": module.params["sip_invite_rate"],
            "ips-rtp": module.params["sip_ips_rtp"],
            "log-call-summary": module.params["sip_log_call_summary"],
            "log-violations": module.params["sip_log_violations"],
            "malformed-header-allow": module.params["sip_malformed_header_allow"],
            "malformed-header-call-id": module.params["sip_malformed_header_call_id"],
            "malformed-header-contact": module.params["sip_malformed_header_contact"],
            "malformed-header-content-length": module.params["sip_malformed_header_content_length"],
            "malformed-header-content-type": module.params["sip_malformed_header_content_type"],
            "malformed-header-cseq": module.params["sip_malformed_header_cseq"],
            "malformed-header-expires": module.params["sip_malformed_header_expires"],
            "malformed-header-from": module.params["sip_malformed_header_from"],
            "malformed-header-max-forwards": module.params["sip_malformed_header_max_forwards"],
            "malformed-header-p-asserted-identity": module.params["sip_malformed_header_p_asserted_identity"],
            "malformed-header-rack": module.params["sip_malformed_header_rack"],
            "malformed-header-record-route": module.params["sip_malformed_header_record_route"],
            "malformed-header-route": module.params["sip_malformed_header_route"],
            "malformed-header-rseq": module.params["sip_malformed_header_rseq"],
            "malformed-header-sdp-a": module.params["sip_malformed_header_sdp_a"],
            "malformed-header-sdp-b": module.params["sip_malformed_header_sdp_b"],
            "malformed-header-sdp-c": module.params["sip_malformed_header_sdp_c"],
            "malformed-header-sdp-i": module.params["sip_malformed_header_sdp_i"],
            "malformed-header-sdp-k": module.params["sip_malformed_header_sdp_k"],
            "malformed-header-sdp-m": module.params["sip_malformed_header_sdp_m"],
            "malformed-header-sdp-o": module.params["sip_malformed_header_sdp_o"],
            "malformed-header-sdp-r": module.params["sip_malformed_header_sdp_r"],
            "malformed-header-sdp-s": module.params["sip_malformed_header_sdp_s"],
            "malformed-header-sdp-t": module.params["sip_malformed_header_sdp_t"],
            "malformed-header-sdp-v": module.params["sip_malformed_header_sdp_v"],
            "malformed-header-sdp-z": module.params["sip_malformed_header_sdp_z"],
            "malformed-header-to": module.params["sip_malformed_header_to"],
            "malformed-header-via": module.params["sip_malformed_header_via"],
            "malformed-request-line": module.params["sip_malformed_request_line"],
            "max-body-length": module.params["sip_max_body_length"],
            "max-dialogs": module.params["sip_max_dialogs"],
            "max-idle-dialogs": module.params["sip_max_idle_dialogs"],
            "max-line-length": module.params["sip_max_line_length"],
            "message-rate": module.params["sip_message_rate"],
            "nat-trace": module.params["sip_nat_trace"],
            "no-sdp-fixup": module.params["sip_no_sdp_fixup"],
            "notify-rate": module.params["sip_notify_rate"],
            "open-contact-pinhole": module.params["sip_open_contact_pinhole"],
            "open-record-route-pinhole": module.params["sip_open_record_route_pinhole"],
            "open-register-pinhole": module.params["sip_open_register_pinhole"],
            "open-via-pinhole": module.params["sip_open_via_pinhole"],
            "options-rate": module.params["sip_options_rate"],
            "prack-rate": module.params["sip_prack_rate"],
            "preserve-override": module.params["sip_preserve_override"],
            "provisional-invite-expiry-time": module.params["sip_provisional_invite_expiry_time"],
            "publish-rate": module.params["sip_publish_rate"],
            "refer-rate": module.params["sip_refer_rate"],
            "register-contact-trace": module.params["sip_register_contact_trace"],
            "register-rate": module.params["sip_register_rate"],
            "rfc2543-branch": module.params["sip_rfc2543_branch"],
            "rtp": module.params["sip_rtp"],
            "ssl-algorithm": module.params["sip_ssl_algorithm"],
            "ssl-auth-client": module.params["sip_ssl_auth_client"],
            "ssl-auth-server": module.params["sip_ssl_auth_server"],
            "ssl-client-certificate": module.params["sip_ssl_client_certificate"],
            "ssl-client-renegotiation": module.params["sip_ssl_client_renegotiation"],
            "ssl-max-version": module.params["sip_ssl_max_version"],
            "ssl-min-version": module.params["sip_ssl_min_version"],
            "ssl-mode": module.params["sip_ssl_mode"],
            "ssl-pfs": module.params["sip_ssl_pfs"],
            "ssl-send-empty-frags": module.params["sip_ssl_send_empty_frags"],
            "ssl-server-certificate": module.params["sip_ssl_server_certificate"],
            "status": module.params["sip_status"],
            "strict-register": module.params["sip_strict_register"],
            "subscribe-rate": module.params["sip_subscribe_rate"],
            "unknown-header": module.params["sip_unknown_header"],
            "update-rate": module.params["sip_update_rate"],
        }
    }

    module.paramgram = paramgram
    fmgr = None
    if module._socket_path:
        connection = Connection(module._socket_path)
        fmgr = FortiManagerHandler(connection, module)
        fmgr.tools = FMGRCommon()
    else:
        module.fail_json(**FAIL_SOCKET_MSG)

    list_overrides = ['sccp', 'sip']
    paramgram = fmgr.tools.paramgram_child_list_override(list_overrides=list_overrides,
                                                         paramgram=paramgram, module=module)
    module.paramgram = paramgram

    results = DEFAULT_RESULT_OBJ
    try:

        results = fmgr_voip_profile_modify(fmgr, paramgram)
        fmgr.govern_response(module=module, results=results,
                             ansible_facts=fmgr.construct_ansible_facts(results, module.params, paramgram))

    except Exception as err:
        raise FMGBaseException(err)

    return module.exit_json(**results[1])


if __name__ == "__main__":
    main()
