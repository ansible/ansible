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
# along with Ansible.  If not, see <https://www.gnu.org/licenses/>.

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
import json
from pyFMG.fortimgr import FortiManager
import pytest

try:
    from ansible.modules.network.fortimanager import fmgr_secprof_voip
except ImportError:
    pytest.skip("Could not load required modules for testing", allow_module_level=True)

fmg_instance = FortiManager("1.1.1.1", "admin", "")


def load_fixtures():
    fixture_path = os.path.join(
        os.path.dirname(__file__),
        'fixtures') + "/{filename}.json".format(
        filename=os.path.splitext(
            os.path.basename(__file__))[0])
    try:
        with open(fixture_path, "r") as fixture_file:
            fixture_data = json.load(fixture_file)
    except IOError:
        return []
    return [fixture_data]


@pytest.fixture(scope="function", params=load_fixtures())
def fixture_data(request):
    func_name = request.function.__name__.replace("test_", "")
    return request.param.get(func_name, None)


def test_fmgr_voip_profile_addsetdelete(fixture_data, mocker):
    mocker.patch("pyFMG.fortimgr.FortiManager._post_request", side_effect=fixture_data)
    #  Fixture sets used:###########################

    ##################################################
    # comment: None
    # sip: {'block-publish': None, 'ssl-max-version': None, 'malformed-header-rack': None, 'rtp': None,
    #  'publish-rate': None, 'ssl-client-renegotiation': None, 'malformed-header-from': None,
    #  'ssl-client-certificate': None, 'malformed-header-p-asserted-identity': None, 'info-rate': None,
    #  'malformed-header-via': None, 'notify-rate': None, 'preserve-override': None, 'block-info': None,
    #  'options-rate': None, 'block-update': None, 'max-body-length': None, 'block-subscribe': None, 'ssl-pfs': None,
    #  'ssl-send-empty-frags': None, 'ssl-auth-client': None, 'malformed-header-record-route': None, 'refer-rate': None,
    #  'open-record-route-pinhole': None, 'register-rate': None, 'unknown-header': None, 'block-unknown': None,
    #  'ssl-server-certificate': None, 'block-invite': None, 'malformed-request-line': None, 'max-dialogs': None,
    #  'block-cancel': None, 'no-sdp-fixup': None, 'open-register-pinhole': None, 'block-notify': None,
    #  'max-idle-dialogs': None, 'strict-register': None, 'block-long-lines': None, 'log-violations': None,
    #  'ssl-min-version': None, 'provisional-invite-expiry-time': None, 'rfc2543-branch': None, 'block-ack': None,
    #  'malformed-header-max-forwards': None, 'block-message': None, 'malformed-header-call-id': None,
    #  'invite-rate': None, 'cancel-rate': None, 'register-contact-trace': None, 'block-refer': None,
    #  'block-register': None, 'ssl-mode': None, 'prack-rate': None, 'block-bye': None, 'ssl-algorithm': None,
    #  'malformed-header-to': None, 'block-geo-red-options': None, 'call-keepalive': None, 'message-rate': None,
    #  'malformed-header-expires': None, 'block-options': None, 'log-call-summary': None,
    #  'hnt-restrict-source-ip': None, 'ssl-auth-server': None, 'contact-fixup': None, 'ack-rate': None,
    #  'malformed-header-allow': None, 'malformed-header-sdp-v': None, 'malformed-header-sdp-t': None,
    #  'malformed-header-contact': None, 'malformed-header-sdp-s': None, 'hosted-nat-traversal': None,
    #  'subscribe-rate': None, 'malformed-header-content-length': None, 'malformed-header-sdp-z': None,
    #  'malformed-header-route': None, 'malformed-header-sdp-b': None, 'malformed-header-sdp-c': None,
    #  'malformed-header-sdp-a': None, 'malformed-header-sdp-o': None, 'malformed-header-sdp-m': None,
    #  'malformed-header-sdp-k': None, 'malformed-header-sdp-i': None, 'status': None, 'open-via-pinhole': None,
    #  'bye-rate': None, 'block-prack': None, 'malformed-header-sdp-r': None, 'open-contact-pinhole': None,
    #  'ips-rtp': None, 'malformed-header-content-type': None, 'nat-trace': None, 'malformed-header-rseq': None,
    #  'max-line-length': None, 'update-rate': None, 'malformed-header-cseq': None}
    # name: Ansible_VOIP_Profile
    # adom: root
    # sccp: {'status': None, 'log-call-summary': None, 'block-mcast': None, 'max-calls': None, 'verify-header': None,
    #  'log-violations': None}
    # mode: delete
    ##################################################
    ##################################################
    # comment: Created by Ansible
    # sip: {'block-publish': None, 'ssl-max-version': None, 'malformed-header-rack': None, 'rtp': None,
    #  'publish-rate': None, 'ssl-client-renegotiation': None, 'malformed-header-from': None,
    #  'open-contact-pinhole': None, 'ssl-client-certificate': None, 'malformed-header-p-asserted-identity': None,
    #  'rfc2543-branch': None, 'malformed-header-via': None, 'notify-rate': None, 'preserve-override': None,
    #  'block-info': None, 'options-rate': None, 'block-update': None, 'max-body-length': None, 'block-subscribe': None,
    #  'ssl-pfs': None, 'ssl-send-empty-frags': None, 'ssl-auth-client': None, 'malformed-header-record-route': None,
    #  'refer-rate': None, 'info-rate': None, 'open-record-route-pinhole': None, 'register-rate': None,
    #  'unknown-header': None, 'block-unknown': None, 'ssl-server-certificate': None, 'block-invite': None,
    #  'strict-register': None, 'max-dialogs': None, 'block-cancel': None, 'no-sdp-fixup': None,
    #  'open-register-pinhole': None, 'block-notify': None, 'max-idle-dialogs': None, 'malformed-request-line': None,
    #  'block-long-lines': None, 'log-violations': None, 'ssl-min-version': None,
    #  'provisional-invite-expiry-time': None, 'block-prack': None, 'malformed-header-max-forwards': None,
    #  'block-message': None, 'malformed-header-call-id': None, 'invite-rate': None, 'cancel-rate': None,
    #  'register-contact-trace': None, 'block-register': None, 'ssl-mode': None, 'prack-rate': None, 'block-bye': None,
    #  'ssl-algorithm': None, 'malformed-header-to': None, 'block-geo-red-options': None, 'call-keepalive': None,
    #  'message-rate': None, 'malformed-header-expires': None, 'block-options': None, 'log-call-summary': None,
    #  'hnt-restrict-source-ip': None, 'ssl-auth-server': None, 'contact-fixup': None, 'ack-rate': None,
    #  'malformed-header-allow': None, 'malformed-header-sdp-v': None, 'malformed-header-sdp-t': None,
    #  'malformed-header-contact': None, 'malformed-header-sdp-s': None, 'hosted-nat-traversal': None,
    #  'subscribe-rate': None, 'malformed-header-content-length': None, 'malformed-header-sdp-z': None,
    #  'malformed-header-route': None, 'malformed-header-sdp-b': None, 'malformed-header-sdp-c': None,
    #  'malformed-header-sdp-a': None, 'malformed-header-sdp-o': None, 'malformed-header-sdp-m': None,
    #  'malformed-header-sdp-k': None, 'malformed-header-sdp-i': None, 'status': None, 'open-via-pinhole': None,
    #  'bye-rate': None, 'block-ack': None, 'malformed-header-sdp-r': None, 'block-refer': None, 'ips-rtp': None,
    #  'malformed-header-content-type': None, 'nat-trace': None, 'malformed-header-rseq': None, 'max-line-length': None,
    #  'update-rate': None, 'malformed-header-cseq': None}
    # name: Ansible_VOIP_Profile
    # adom: adom
    # sccp: {'status': None, 'log-call-summary': None, 'block-mcast': None, 'max-calls': None, 'verify-header': None,
    #  'log-violations': None}
    # mode: set
    ##################################################
    ##################################################
    # comment: Created by Ansible
    # sip: {'block-publish': None, 'ssl-max-version': None, 'malformed-header-rack': None, 'rtp': None,
    #  'publish-rate': None, 'ssl-client-renegotiation': None, 'malformed-header-from': None,
    #  'ssl-client-certificate': None, 'malformed-header-p-asserted-identity': None, 'info-rate': None,
    #  'malformed-header-via': None, 'notify-rate': None, 'preserve-override': None, 'block-info': None,
    #  'options-rate': None, 'block-update': None, 'max-body-length': None, 'block-subscribe': None, 'ssl-pfs': None,
    #  'ssl-send-empty-frags': None, 'ssl-auth-client': None, 'malformed-header-record-route': None, 'refer-rate': None,
    #  'open-record-route-pinhole': None, 'register-rate': None, 'unknown-header': None, 'block-unknown': None,
    #  'ssl-server-certificate': None, 'block-invite': None, 'malformed-request-line': None, 'max-dialogs': None,
    #  'block-cancel': None, 'no-sdp-fixup': None, 'open-register-pinhole': None, 'block-notify': None,
    #  'max-idle-dialogs': None, 'strict-register': None, 'block-long-lines': None, 'log-violations': None,
    #  'ssl-min-version': None, 'provisional-invite-expiry-time': None, 'rfc2543-branch': None, 'block-ack': None,
    #  'malformed-header-max-forwards': None, 'block-message': None, 'malformed-header-call-id': None,
    #  'invite-rate': None, 'cancel-rate': None, 'register-contact-trace': None, 'block-refer': None,
    #  'block-register': None, 'ssl-mode': None, 'prack-rate': None, 'block-bye': None, 'ssl-algorithm': None,
    #  'malformed-header-to': None, 'block-geo-red-options': None, 'call-keepalive': None, 'message-rate': None,
    #  'malformed-header-expires': None, 'block-options': None, 'log-call-summary': None,
    #  'hnt-restrict-source-ip': None, 'ssl-auth-server': None, 'contact-fixup': None, 'ack-rate': None,
    #  'malformed-header-allow': None, 'malformed-header-sdp-v': None, 'malformed-header-sdp-t': None,
    #  'malformed-header-contact': None, 'malformed-header-sdp-s': None, 'hosted-nat-traversal': None,
    #  'subscribe-rate': None, 'malformed-header-content-length': None, 'malformed-header-sdp-z': None,
    #  'malformed-header-route': None, 'malformed-header-sdp-b': None, 'malformed-header-sdp-c': None,
    #  'malformed-header-sdp-a': None, 'malformed-header-sdp-o': None, 'malformed-header-sdp-m': None,
    #  'malformed-header-sdp-k': None, 'malformed-header-sdp-i': None, 'status': None, 'open-via-pinhole': None,
    #  'bye-rate': None, 'block-prack': None, 'malformed-header-sdp-r': None, 'open-contact-pinhole': None,
    #  'ips-rtp': None, 'malformed-header-content-type': None, 'nat-trace': None, 'malformed-header-rseq': None,
    #  'max-line-length': None, 'update-rate': None, 'malformed-header-cseq': None}
    # name: Ansible_VOIP_Profile
    # adom: root
    # sccp: {'status': None, 'log-call-summary': None, 'block-mcast': None, 'max-calls': None, 'verify-header': None,
    #  'log-violations': None}
    # mode: set
    ##################################################
    ##################################################
    # comment: None
    # sip: {'block-publish': None, 'ssl-max-version': None, 'malformed-header-rack': None, 'rtp': None,
    #  'publish-rate': None, 'ssl-client-renegotiation': None, 'malformed-header-from': None,
    #  'open-contact-pinhole': None, 'ssl-client-certificate': None, 'malformed-header-p-asserted-identity': None,
    #  'rfc2543-branch': None, 'malformed-header-via': None, 'notify-rate': None, 'preserve-override': None,
    #  'block-info': None, 'options-rate': None, 'block-update': None, 'max-body-length': None, 'block-subscribe': None,
    #  'ssl-pfs': None, 'ssl-send-empty-frags': None, 'ssl-auth-client': None, 'malformed-header-record-route': None,
    #  'refer-rate': None, 'info-rate': None, 'open-record-route-pinhole': None, 'register-rate': None,
    #  'unknown-header': None, 'block-unknown': None, 'ssl-server-certificate': None, 'block-invite': None,
    #  'strict-register': None, 'max-dialogs': None, 'block-cancel': None, 'no-sdp-fixup': None,
    #  'open-register-pinhole': None, 'block-notify': None, 'max-idle-dialogs': None, 'malformed-request-line': None,
    #  'block-long-lines': None, 'log-violations': None, 'ssl-min-version': None,
    #  'provisional-invite-expiry-time': None, 'block-prack': None, 'malformed-header-max-forwards': None,
    #  'block-message': None, 'malformed-header-call-id': None, 'invite-rate': None, 'cancel-rate': None,
    #  'register-contact-trace': None, 'block-register': None, 'ssl-mode': None, 'prack-rate': None, 'block-bye': None,
    #  'ssl-algorithm': None, 'malformed-header-to': None, 'block-geo-red-options': None, 'call-keepalive': None,
    #  'message-rate': None, 'malformed-header-expires': None, 'block-options': None, 'log-call-summary': None,
    #  'hnt-restrict-source-ip': None, 'ssl-auth-server': None, 'contact-fixup': None, 'ack-rate': None,
    #  'malformed-header-allow': None, 'malformed-header-sdp-v': None, 'malformed-header-sdp-t': None,
    #  'malformed-header-contact': None, 'malformed-header-sdp-s': None, 'hosted-nat-traversal': None,
    #  'subscribe-rate': None, 'malformed-header-content-length': None, 'malformed-header-sdp-z': None,
    #  'malformed-header-route': None, 'malformed-header-sdp-b': None, 'malformed-header-sdp-c': None,
    #  'malformed-header-sdp-a': None, 'malformed-header-sdp-o': None, 'malformed-header-sdp-m': None,
    #  'malformed-header-sdp-k': None, 'malformed-header-sdp-i': None, 'status': None, 'open-via-pinhole': None,
    #  'bye-rate': None, 'block-ack': None, 'malformed-header-sdp-r': None, 'block-refer': None, 'ips-rtp': None,
    #  'malformed-header-content-type': None, 'nat-trace': None, 'malformed-header-rseq': None, 'max-line-length': None,
    #  'update-rate': None, 'malformed-header-cseq': None}
    # name: Ansible_VOIP_Profile
    # adom: root
    # sccp: {'status': None, 'log-call-summary': None, 'block-mcast': None, 'max-calls': None, 'verify-header': None,
    #  'log-violations': None}
    # mode: delete
    ##################################################
    ##################################################
    # comment: Created by Ansible
    # sip: {'block-publish': None, 'ssl-max-version': None, 'malformed-header-rack': None, 'rtp': None,
    #  'publish-rate': None, 'ssl-client-renegotiation': None, 'malformed-header-from': None,
    #  'ssl-client-certificate': None, 'malformed-header-p-asserted-identity': None, 'info-rate': None,
    #  'malformed-header-via': None, 'notify-rate': None, 'preserve-override': None, 'block-info': None,
    #  'options-rate': None, 'block-update': None, 'max-body-length': None, 'block-subscribe': None,
    #  'ssl-pfs': None, 'ssl-send-empty-frags': None, 'ssl-auth-client': None, 'malformed-header-record-route': None,
    #  'refer-rate': None, 'open-record-route-pinhole': None, 'register-rate': None, 'unknown-header': None,
    #  'block-unknown': None, 'ssl-server-certificate': None, 'block-invite': None, 'malformed-request-line': None,
    #  'max-dialogs': None, 'block-cancel': None, 'no-sdp-fixup': None, 'open-register-pinhole': None,
    #  'block-notify': None, 'max-idle-dialogs': None, 'strict-register': None, 'block-long-lines': None,
    #  'log-violations': None, 'ssl-min-version': None, 'provisional-invite-expiry-time': None, 'rfc2543-branch': None,
    #  'block-ack': None, 'malformed-header-max-forwards': None, 'block-message': None,
    #  'malformed-header-call-id': None, 'invite-rate': None, 'cancel-rate': None, 'register-contact-trace': None,
    #  'block-refer': None, 'block-register': None, 'ssl-mode': None, 'prack-rate': None, 'block-bye': None,
    #  'ssl-algorithm': None, 'malformed-header-to': None, 'block-geo-red-options': None, 'call-keepalive': None,
    #  'message-rate': None, 'malformed-header-expires': None, 'block-options': None, 'log-call-summary': None,
    #  'hnt-restrict-source-ip': None, 'ssl-auth-server': None, 'contact-fixup': None, 'ack-rate': None,
    #  'malformed-header-allow': None, 'malformed-header-sdp-v': None, 'malformed-header-sdp-t': None,
    #  'malformed-header-contact': None, 'malformed-header-sdp-s': None, 'hosted-nat-traversal': None,
    #  'subscribe-rate': None, 'malformed-header-content-length': None, 'malformed-header-sdp-z': None,
    #  'malformed-header-route': None, 'malformed-header-sdp-b': None, 'malformed-header-sdp-c': None,
    #  'malformed-header-sdp-a': None, 'malformed-header-sdp-o': None, 'malformed-header-sdp-m': None,
    #  'malformed-header-sdp-k': None, 'malformed-header-sdp-i': None, 'status': None, 'open-via-pinhole': None,
    #  'bye-rate': None, 'block-prack': None, 'malformed-header-sdp-r': None, 'open-contact-pinhole': None,
    #  'ips-rtp': None, 'malformed-header-content-type': None, 'nat-trace': None, 'malformed-header-rseq': None,
    #  'max-line-length': None, 'update-rate': None, 'malformed-header-cseq': None}
    # name: Ansible_VOIP_Profile
    # adom: root
    # sccp: {'status': None, 'log-call-summary': None, 'block-mcast': None, 'max-calls': None, 'verify-header': None,
    #  'log-violations': None}
    # mode: set
    ##################################################
    ##################################################
    # comment: None
    # sip: {'block-publish': None, 'ssl-max-version': None, 'malformed-header-rack': None, 'rtp': None,
    #  'publish-rate': None, 'ssl-client-renegotiation': None, 'malformed-header-from': None,
    #  'open-contact-pinhole': None, 'ssl-client-certificate': None, 'malformed-header-p-asserted-identity': None,
    #  'rfc2543-branch': None, 'malformed-header-via': None, 'notify-rate': None, 'preserve-override': None,
    #  'block-info': None, 'options-rate': None, 'block-update': None, 'max-body-length': None, 'block-subscribe': None,
    #  'ssl-pfs': None, 'ssl-send-empty-frags': None, 'ssl-auth-client': None, 'malformed-header-record-route': None,
    #  'refer-rate': None, 'info-rate': None, 'open-record-route-pinhole': None, 'register-rate': None,
    #  'unknown-header': None, 'block-unknown': None, 'ssl-server-certificate': None, 'block-invite': None,
    #  'strict-register': None, 'max-dialogs': None, 'block-cancel': None, 'no-sdp-fixup': None,
    #  'open-register-pinhole': None, 'block-notify': None, 'max-idle-dialogs': None, 'malformed-request-line': None,
    #  'block-long-lines': None, 'log-violations': None, 'ssl-min-version': None,
    #  'provisional-invite-expiry-time': None, 'block-prack': None, 'malformed-header-max-forwards': None,
    #  'block-message': None, 'malformed-header-call-id': None, 'invite-rate': None, 'cancel-rate': None,
    #  'register-contact-trace': None, 'block-register': None, 'ssl-mode': None, 'prack-rate': None, 'block-bye': None,
    #  'ssl-algorithm': None, 'malformed-header-to': None, 'block-geo-red-options': None, 'call-keepalive': None,
    #  'message-rate': None, 'malformed-header-expires': None, 'block-options': None, 'log-call-summary': None,
    #  'hnt-restrict-source-ip': None, 'ssl-auth-server': None, 'contact-fixup': None, 'ack-rate': None,
    #  'malformed-header-allow': None, 'malformed-header-sdp-v': None, 'malformed-header-sdp-t': None,
    #  'malformed-header-contact': None, 'malformed-header-sdp-s': None, 'hosted-nat-traversal': None,
    #  'subscribe-rate': None, 'malformed-header-content-length': None, 'malformed-header-sdp-z': None,
    #  'malformed-header-route': None, 'malformed-header-sdp-b': None, 'malformed-header-sdp-c': None,
    #  'malformed-header-sdp-a': None, 'malformed-header-sdp-o': None, 'malformed-header-sdp-m': None,
    #  'malformed-header-sdp-k': None, 'malformed-header-sdp-i': None, 'status': None, 'open-via-pinhole': None,
    #  'bye-rate': None, 'block-ack': None, 'malformed-header-sdp-r': None, 'block-refer': None, 'ips-rtp': None,
    #  'malformed-header-content-type': None, 'nat-trace': None, 'malformed-header-rseq': None, 'max-line-length': None,
    #  'update-rate': None, 'malformed-header-cseq': None}
    # name: Ansible_VOIP_Profile
    # adom: root
    # sccp: {'status': None, 'log-call-summary': None, 'block-mcast': None, 'max-calls': None, 'verify-header': None,
    #  'log-violations': None}
    # mode: delete
    ##################################################
    ##################################################
    # comment: None
    # sip: {'block-publish': None, 'ssl-max-version': None, 'malformed-header-rack': None, 'rtp': None,
    #  'publish-rate': None, 'ssl-client-renegotiation': None, 'malformed-header-from': None,
    #  'ssl-client-certificate': None, 'malformed-header-p-asserted-identity': None, 'info-rate': None,
    #  'malformed-header-via': None, 'notify-rate': None, 'preserve-override': None, 'block-info': None,
    #  'options-rate': None, 'block-update': None, 'max-body-length': None, 'block-subscribe': None, 'ssl-pfs': None,
    #  'ssl-send-empty-frags': None, 'ssl-auth-client': None, 'malformed-header-record-route': None, 'refer-rate': None,
    #  'open-record-route-pinhole': None, 'register-rate': None, 'unknown-header': None, 'block-unknown': None,
    #  'ssl-server-certificate': None, 'block-invite': None, 'malformed-request-line': None, 'max-dialogs': None,
    #  'block-cancel': None, 'no-sdp-fixup': None, 'open-register-pinhole': None, 'block-notify': None,
    #  'max-idle-dialogs': None, 'strict-register': None, 'block-long-lines': None, 'log-violations': None,
    #  'ssl-min-version': None, 'provisional-invite-expiry-time': None, 'rfc2543-branch': None, 'block-ack': None,
    #  'malformed-header-max-forwards': None, 'block-message': None, 'malformed-header-call-id': None,
    #  'invite-rate': None, 'cancel-rate': None, 'register-contact-trace': None, 'block-refer': None,
    #  'block-register': None, 'ssl-mode': None, 'prack-rate': None, 'block-bye': None, 'ssl-algorithm': None,
    #  'malformed-header-to': None, 'block-geo-red-options': None, 'call-keepalive': None, 'message-rate': None,
    #  'malformed-header-expires': None, 'block-options': None, 'log-call-summary': None,
    #  'hnt-restrict-source-ip': None, 'ssl-auth-server': None, 'contact-fixup': None, 'ack-rate': None,
    #  'malformed-header-allow': None, 'malformed-header-sdp-v': None, 'malformed-header-sdp-t': None,
    #  'malformed-header-contact': None, 'malformed-header-sdp-s': None, 'hosted-nat-traversal': None,
    #  'subscribe-rate': None, 'malformed-header-content-length': None, 'malformed-header-sdp-z': None,
    #  'malformed-header-route': None, 'malformed-header-sdp-b': None, 'malformed-header-sdp-c': None,
    #  'malformed-header-sdp-a': None, 'malformed-header-sdp-o': None, 'malformed-header-sdp-m': None,
    #  'malformed-header-sdp-k': None, 'malformed-header-sdp-i': None, 'status': None, 'open-via-pinhole': None,
    #  'bye-rate': None, 'block-prack': None, 'malformed-header-sdp-r': None, 'open-contact-pinhole': None,
    #  'ips-rtp': None, 'malformed-header-content-type': None, 'nat-trace': None, 'malformed-header-rseq': None,
    #  'max-line-length': None, 'update-rate': None, 'malformed-header-cseq': None}
    # name: Ansible_VOIP_Profile
    # adom: root
    # sccp: {'status': None, 'log-call-summary': None, 'block-mcast': None, 'max-calls': None, 'verify-header': None,
    #  'log-violations': None}
    # mode: delete
    ##################################################
    ##################################################
    # comment: Created by Ansible
    # sip: {'block-publish': None, 'ssl-max-version': None, 'malformed-header-rack': None, 'rtp': None,
    #  'publish-rate': None, 'ssl-client-renegotiation': None, 'malformed-header-from': None,
    #  'open-contact-pinhole': None, 'ssl-client-certificate': None, 'malformed-header-p-asserted-identity': None,
    #  'rfc2543-branch': None, 'malformed-header-via': None, 'notify-rate': None, 'preserve-override': None,
    #  'block-info': None, 'options-rate': None, 'block-update': None, 'max-body-length': None, 'block-subscribe': None,
    #  'ssl-pfs': None, 'ssl-send-empty-frags': None, 'ssl-auth-client': None, 'malformed-header-record-route': None,
    #  'refer-rate': None, 'info-rate': None, 'open-record-route-pinhole': None, 'register-rate': None,
    #  'unknown-header': None, 'block-unknown': None, 'ssl-server-certificate': None, 'block-invite': None,
    #  'strict-register': None, 'max-dialogs': None, 'block-cancel': None, 'no-sdp-fixup': None,
    #  'open-register-pinhole': None, 'block-notify': None, 'max-idle-dialogs': None, 'malformed-request-line': None,
    #  'block-long-lines': None, 'log-violations': None, 'ssl-min-version': None,
    #  'provisional-invite-expiry-time': None, 'block-prack': None, 'malformed-header-max-forwards': None,
    #  'block-message': None, 'malformed-header-call-id': None, 'invite-rate': None, 'cancel-rate': None,
    #  'register-contact-trace': None, 'block-register': None, 'ssl-mode': None, 'prack-rate': None, 'block-bye': None,
    #  'ssl-algorithm': None, 'malformed-header-to': None, 'block-geo-red-options': None, 'call-keepalive': None,
    #  'message-rate': None, 'malformed-header-expires': None, 'block-options': None, 'log-call-summary': None,
    #  'hnt-restrict-source-ip': None, 'ssl-auth-server': None, 'contact-fixup': None, 'ack-rate': None,
    #  'malformed-header-allow': None, 'malformed-header-sdp-v': None, 'malformed-header-sdp-t': None,
    #  'malformed-header-contact': None, 'malformed-header-sdp-s': None, 'hosted-nat-traversal': None,
    #  'subscribe-rate': None, 'malformed-header-content-length': None, 'malformed-header-sdp-z': None,
    #  'malformed-header-route': None, 'malformed-header-sdp-b': None, 'malformed-header-sdp-c': None,
    #  'malformed-header-sdp-a': None, 'malformed-header-sdp-o': None, 'malformed-header-sdp-m': None,
    #  'malformed-header-sdp-k': None, 'malformed-header-sdp-i': None, 'status': None, 'open-via-pinhole': None,
    #  'bye-rate': None, 'block-ack': None, 'malformed-header-sdp-r': None, 'block-refer': None, 'ips-rtp': None,
    #  'malformed-header-content-type': None, 'nat-trace': None, 'malformed-header-rseq': None, 'max-line-length': None,
    #  'update-rate': None, 'malformed-header-cseq': None}
    # name: Ansible_VOIP_Profile
    # adom: root
    # sccp: [{'status': 'enable', 'log-call-summary': 'enable', 'log-violations': 'enable', 'block-mcast': 'enable'}]
    # mode: set
    ##################################################
    ##################################################
    # comment: Created by Ansible
    # sip: {'block-publish': None, 'ssl-max-version': None, 'malformed-header-rack': None, 'rtp': None,
    #  'publish-rate': None, 'ssl-client-renegotiation': None, 'malformed-header-from': None,
    #  'ssl-client-certificate': None, 'malformed-header-p-asserted-identity': None, 'info-rate': None,
    #  'malformed-header-via': None, 'notify-rate': None, 'preserve-override': None, 'block-info': None,
    #  'options-rate': None, 'block-update': None, 'max-body-length': None, 'block-subscribe': None, 'ssl-pfs': None,
    #  'ssl-send-empty-frags': None, 'ssl-auth-client': None, 'malformed-header-record-route': None, 'refer-rate': None,
    #  'open-record-route-pinhole': None, 'register-rate': None, 'unknown-header': None, 'block-unknown': None,
    #  'ssl-server-certificate': None, 'block-invite': None, 'malformed-request-line': None, 'max-dialogs': None,
    #  'block-cancel': None, 'no-sdp-fixup': None, 'open-register-pinhole': None, 'block-notify': None,
    #  'max-idle-dialogs': None, 'strict-register': None, 'block-long-lines': None, 'log-violations': None,
    #  'ssl-min-version': None, 'provisional-invite-expiry-time': None, 'rfc2543-branch': None, 'block-ack': None,
    #  'malformed-header-max-forwards': None, 'block-message': None, 'malformed-header-call-id': None,
    #  'invite-rate': None, 'cancel-rate': None, 'register-contact-trace': None, 'block-refer': None,
    #  'block-register': None, 'ssl-mode': None, 'prack-rate': None, 'block-bye': None, 'ssl-algorithm': None,
    #  'malformed-header-to': None, 'block-geo-red-options': None, 'call-keepalive': None, 'message-rate': None,
    #  'malformed-header-expires': None, 'block-options': None, 'log-call-summary': None,
    #  'hnt-restrict-source-ip': None, 'ssl-auth-server': None, 'contact-fixup': None, 'ack-rate': None,
    #  'malformed-header-allow': None, 'malformed-header-sdp-v': None, 'malformed-header-sdp-t': None,
    #  'malformed-header-contact': None, 'malformed-header-sdp-s': None, 'hosted-nat-traversal': None,
    #  'subscribe-rate': None, 'malformed-header-content-length': None, 'malformed-header-sdp-z': None,
    #  'malformed-header-route': None, 'malformed-header-sdp-b': None, 'malformed-header-sdp-c': None,
    #  'malformed-header-sdp-a': None, 'malformed-header-sdp-o': None, 'malformed-header-sdp-m': None,
    #  'malformed-header-sdp-k': None, 'malformed-header-sdp-i': None, 'status': None, 'open-via-pinhole': None,
    #  'bye-rate': None, 'block-prack': None, 'malformed-header-sdp-r': None, 'open-contact-pinhole': None,
    #  'ips-rtp': None, 'malformed-header-content-type': None, 'nat-trace': None, 'malformed-header-rseq': None,
    #  'max-line-length': None, 'update-rate': None, 'malformed-header-cseq': None}
    # name: Ansible_VOIP_Profile
    # adom: root
    # sccp: {'status': 'enable', 'log-call-summary': 'enable', 'log-violations': 'enable', 'block-mcast': 'enable'}
    # mode: set
    ##################################################
    ##################################################
    # comment: None
    # sip: {'block-publish': None, 'ssl-max-version': None, 'malformed-header-rack': None, 'rtp': None,
    #  'publish-rate': None, 'ssl-client-renegotiation': None, 'malformed-header-from': None,
    #  'open-contact-pinhole': None, 'ssl-client-certificate': None, 'malformed-header-p-asserted-identity': None,
    #  'rfc2543-branch': None, 'malformed-header-via': None, 'notify-rate': None, 'preserve-override': None,
    #  'block-info': None, 'options-rate': None, 'block-update': None, 'max-body-length': None, 'block-subscribe': None,
    #  'ssl-pfs': None, 'ssl-send-empty-frags': None, 'ssl-auth-client': None, 'malformed-header-record-route': None,
    #  'refer-rate': None, 'info-rate': None, 'open-record-route-pinhole': None, 'register-rate': None,
    #  'unknown-header': None, 'block-unknown': None, 'ssl-server-certificate': None, 'block-invite': None,
    #  'strict-register': None, 'max-dialogs': None, 'block-cancel': None, 'no-sdp-fixup': None,
    #  'open-register-pinhole': None, 'block-notify': None, 'max-idle-dialogs': None, 'malformed-request-line': None,
    #  'block-long-lines': None, 'log-violations': None, 'ssl-min-version': None,
    #  'provisional-invite-expiry-time': None, 'block-prack': None, 'malformed-header-max-forwards': None,
    #  'block-message': None, 'malformed-header-call-id': None, 'invite-rate': None, 'cancel-rate': None,
    #  'register-contact-trace': None, 'block-register': None, 'ssl-mode': None, 'prack-rate': None, 'block-bye': None,
    #  'ssl-algorithm': None, 'malformed-header-to': None, 'block-geo-red-options': None, 'call-keepalive': None,
    #  'message-rate': None, 'malformed-header-expires': None, 'block-options': None, 'log-call-summary': None,
    #  'hnt-restrict-source-ip': None, 'ssl-auth-server': None, 'contact-fixup': None, 'ack-rate': None,
    #  'malformed-header-allow': None, 'malformed-header-sdp-v': None, 'malformed-header-sdp-t': None,
    #  'malformed-header-contact': None, 'malformed-header-sdp-s': None, 'hosted-nat-traversal': None,
    #  'subscribe-rate': None, 'malformed-header-content-length': None, 'malformed-header-sdp-z': None,
    #  'malformed-header-route': None, 'malformed-header-sdp-b': None, 'malformed-header-sdp-c': None,
    #  'malformed-header-sdp-a': None, 'malformed-header-sdp-o': None, 'malformed-header-sdp-m': None,
    #  'malformed-header-sdp-k': None, 'malformed-header-sdp-i': None, 'status': None, 'open-via-pinhole': None,
    #  'bye-rate': None, 'block-ack': None, 'malformed-header-sdp-r': None, 'block-refer': None, 'ips-rtp': None,
    #  'malformed-header-content-type': None, 'nat-trace': None, 'malformed-header-rseq': None, 'max-line-length': None,
    #  'update-rate': None, 'malformed-header-cseq': None}
    # name: Ansible_VOIP_Profile
    # adom: root
    # sccp: {'status': None, 'log-call-summary': None, 'block-mcast': None, 'max-calls': None, 'verify-header': None,
    #  'log-violations': None}
    # mode: delete
    ##################################################
    ##################################################
    # comment: Created by Ansible
    # sip: {'block-publish': None, 'ssl-max-version': None, 'malformed-header-rack': None, 'rtp': None,
    #  'publish-rate': None, 'ssl-client-renegotiation': None, 'malformed-header-from': None,
    #  'ssl-client-certificate': None, 'malformed-header-p-asserted-identity': None, 'info-rate': None,
    #  'malformed-header-via': None, 'notify-rate': None, 'preserve-override': None, 'block-info': None,
    #  'options-rate': None, 'block-update': None, 'max-body-length': None, 'block-subscribe': None, 'ssl-pfs': None,
    #  'ssl-send-empty-frags': None, 'ssl-auth-client': None, 'malformed-header-record-route': None, 'refer-rate': None,
    #  'open-record-route-pinhole': None, 'register-rate': None, 'unknown-header': None, 'block-unknown': None,
    #  'ssl-server-certificate': None, 'block-invite': None, 'malformed-request-line': None, 'max-dialogs': None,
    #  'block-cancel': None, 'no-sdp-fixup': None, 'open-register-pinhole': None, 'block-options': None,
    #  'max-idle-dialogs': None, 'strict-register': None, 'block-long-lines': None, 'log-violations': None,
    #  'ssl-min-version': None, 'provisional-invite-expiry-time': None, 'rfc2543-branch': None, 'block-ack': None,
    #  'malformed-header-max-forwards': None, 'block-message': None, 'malformed-header-call-id': None,
    #  'invite-rate': None, 'cancel-rate': None, 'register-contact-trace': None, 'block-refer': None,
    #  'block-register': None, 'ssl-mode': None, 'prack-rate': None, 'block-bye': None, 'ssl-algorithm': None,
    #  'malformed-header-to': None, 'block-geo-red-options': None, 'call-keepalive': None, 'message-rate': None,
    #  'malformed-header-expires': None, 'log-call-summary': None, 'hnt-restrict-source-ip': None,
    #  'ssl-auth-server': None, 'contact-fixup': None, 'ack-rate': None, 'malformed-header-allow': None,
    #  'malformed-header-sdp-v': None, 'malformed-header-sdp-t': None, 'malformed-header-contact': None,
    #  'malformed-header-sdp-s': None, 'hosted-nat-traversal': None, 'subscribe-rate': None,
    #  'malformed-header-content-length': None, 'malformed-header-sdp-z': None, 'malformed-header-route': None,
    #  'block-notify': None, 'malformed-header-sdp-b': None, 'malformed-header-sdp-c': None,
    #  'malformed-header-sdp-a': None, 'malformed-header-sdp-o': None, 'malformed-header-sdp-m': None,
    #  'malformed-header-sdp-k': None, 'malformed-header-sdp-i': None, 'status': None, 'open-via-pinhole': None,
    #  'bye-rate': None, 'block-prack': None, 'malformed-header-sdp-r': None, 'open-contact-pinhole': None,
    #  'ips-rtp': None, 'malformed-header-content-type': None, 'nat-trace': None, 'malformed-header-rseq': None,
    #  'max-line-length': None, 'update-rate': None, 'malformed-header-cseq': None}
    # name: Ansible_VOIP_Profile
    # adom: root
    # sccp: {'status': 'enable', 'log-call-summary': 'enable', 'log-violations': 'enable', 'block-mcast': 'enable'}
    # mode: set
    ##################################################

    # Test using fixture 1 #
    output = fmgr_secprof_voip.fmgr_voip_profile_addsetdelete(fmg_instance, fixture_data[0]['paramgram_used'])
    assert output['raw_response']['status']['code'] == -3
    # Test using fixture 2 #
    output = fmgr_secprof_voip.fmgr_voip_profile_addsetdelete(fmg_instance, fixture_data[1]['paramgram_used'])
    assert output['raw_response']['status']['code'] == -6
    # Test using fixture 3 #
    output = fmgr_secprof_voip.fmgr_voip_profile_addsetdelete(fmg_instance, fixture_data[2]['paramgram_used'])
    assert output['raw_response']['status']['code'] == 0
    # Test using fixture 4 #
    output = fmgr_secprof_voip.fmgr_voip_profile_addsetdelete(fmg_instance, fixture_data[3]['paramgram_used'])
    assert output['raw_response']['status']['code'] == 0
    # Test using fixture 5 #
    output = fmgr_secprof_voip.fmgr_voip_profile_addsetdelete(fmg_instance, fixture_data[4]['paramgram_used'])
    assert output['raw_response']['status']['code'] == 0
    # Test using fixture 6 #
    output = fmgr_secprof_voip.fmgr_voip_profile_addsetdelete(fmg_instance, fixture_data[5]['paramgram_used'])
    assert output['raw_response']['status']['code'] == 0
    # Test using fixture 7 #
    output = fmgr_secprof_voip.fmgr_voip_profile_addsetdelete(fmg_instance, fixture_data[6]['paramgram_used'])
    assert output['raw_response']['status']['code'] == -3
    # Test using fixture 8 #
    output = fmgr_secprof_voip.fmgr_voip_profile_addsetdelete(fmg_instance, fixture_data[7]['paramgram_used'])
    assert output['raw_response']['status']['code'] == -10
    # Test using fixture 9 #
    output = fmgr_secprof_voip.fmgr_voip_profile_addsetdelete(fmg_instance, fixture_data[8]['paramgram_used'])
    assert output['raw_response']['status']['code'] == 0
    # Test using fixture 10 #
    output = fmgr_secprof_voip.fmgr_voip_profile_addsetdelete(fmg_instance, fixture_data[9]['paramgram_used'])
    assert output['raw_response']['status']['code'] == 0
    # Test using fixture 11 #
    output = fmgr_secprof_voip.fmgr_voip_profile_addsetdelete(fmg_instance, fixture_data[10]['paramgram_used'])
    assert output['raw_response']['status']['code'] == 0
