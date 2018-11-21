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
    from ansible.modules.network.fortimanager import fmgr_secprof_ssl_ssh
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


def test_fmgr_firewall_ssl_ssh_profile_addsetdelete(fixture_data, mocker):
    mocker.patch("pyFMG.fortimgr.FortiManager._post_request", side_effect=fixture_data)
    #  Fixture sets used:###########################

    ##################################################
    # comment: None
    # untrusted-caname: None
    # mapi-over-https: None
    # whitelist: None
    # caname: None
    # ftps: {'status': None, 'allow-invalid-server-cert': None, 'unsupported-ssl': None, 'client-cert-request': None,
    #  'ports': None, 'untrusted-cert': None}
    # ssl-exemptions-log: None
    # https: {'status': None, 'allow-invalid-server-cert': None, 'unsupported-ssl': None, 'client-cert-request': None,
    #  'ports': None, 'untrusted-cert': None}
    # imaps: {'status': None, 'allow-invalid-server-cert': None, 'unsupported-ssl': None, 'client-cert-request': None,
    #  'ports': None, 'untrusted-cert': None}
    # server-cert-mode: None
    # adom: root
    # ssl-exempt: {'regex': None, 'wildcard-fqdn': None, 'fortiguard-category': None, 'address6': None,
    #  'address': None, 'type': None}
    # ssl: {'inspect-all': None, 'allow-invalid-server-cert': None, 'client-cert-request': None,
    #  'untrusted-cert': None, 'unsupported-ssl': None}
    # ssh: {'status': None, 'inspect-all': None, 'ssh-tun-policy-check': None, 'ssh-policy-check': None,
    #  'ssh-algorithm': None, 'unsupported-version': None, 'ports': None}
    # use-ssl-server: None
    # server-cert: None
    # name: Ansible_SSL_SSH_Profile
    # ssl-anomalies-log: None
    # ssl-server: {'pop3s-client-cert-request': None, 'imaps-client-cert-request': None,
    #  'smtps-client-cert-request': None, 'ip': None, 'ssl-other-client-cert-request': None,
    #  'https-client-cert-request': None, 'ftps-client-cert-request': None}
    # smtps: {'status': None, 'allow-invalid-server-cert': None, 'unsupported-ssl': None, 'client-cert-request': None,
    #  'ports': None, 'untrusted-cert': None}
    # rpc-over-https: None
    # mode: delete
    # pop3s: {'status': None, 'allow-invalid-server-cert': None, 'unsupported-ssl': None, 'client-cert-request': None,
    #  'ports': None, 'untrusted-cert': None}
    ##################################################
    ##################################################
    # comment: Created by Ansible Module TEST
    # untrusted-caname: None
    # mapi-over-https: enable
    # whitelist: enable
    # caname: None
    # ftps: {'status': None, 'allow-invalid-server-cert': None, 'unsupported-ssl': None, 'untrusted-cert': None,
    #  'client-cert-request': None, 'ports': None}
    # ssl-exemptions-log: enable
    # https: {'status': None, 'allow-invalid-server-cert': None, 'unsupported-ssl': None, 'untrusted-cert': None,
    #  'client-cert-request': None, 'ports': None}
    # pop3s: {'status': None, 'allow-invalid-server-cert': None, 'unsupported-ssl': None, 'untrusted-cert': None,
    #  'client-cert-request': None, 'ports': None}
    # server-cert-mode: replace
    # adom: root
    # ssl-exempt: {'regex': None, 'wildcard-fqdn': None, 'fortiguard-category': None, 'address6': None,
    #  'address': None, 'type': None}
    # ssl: {'unsupported-ssl': None, 'inspect-all': None, 'allow-invalid-server-cert': None, 'untrusted-cert': None,
    #  'client-cert-request': None}
    # ssh: {'status': None, 'inspect-all': None, 'ssh-tun-policy-check': None, 'ssh-policy-check': None,
    #  'ssh-algorithm': None, 'unsupported-version': None, 'ports': None}
    # server-cert: None
    # name: Ansible_SSL_SSH_Profile
    # ssl-anomalies-log: enable
    # ssl-server: {'pop3s-client-cert-request': None, 'imaps-client-cert-request': None,
    #  'smtps-client-cert-request': None, 'ip': None, 'ssl-other-client-cert-request': None,
    #  'https-client-cert-request': None, 'ftps-client-cert-request': None}
    # smtps: {'status': None, 'allow-invalid-server-cert': None, 'unsupported-ssl': None, 'untrusted-cert': None,
    #  'client-cert-request': None, 'ports': None}
    # imaps: {'status': None, 'allow-invalid-server-cert': None, 'unsupported-ssl': None, 'untrusted-cert': None,
    #  'client-cert-request': None, 'ports': None}
    # rpc-over-https: enable
    # mode: set
    # use-ssl-server: enable
    ##################################################

    # Test using fixture 1 #
    output = fmgr_secprof_ssl_ssh.fmgr_firewall_ssl_ssh_profile_addsetdelete(
        fmg_instance, fixture_data[0]['paramgram_used'])
    assert output['raw_response']['status']['code'] == 0
    # Test using fixture 2 #
    output = fmgr_secprof_ssl_ssh.fmgr_firewall_ssl_ssh_profile_addsetdelete(
        fmg_instance, fixture_data[1]['paramgram_used'])
    assert output['raw_response']['status']['code'] == 0
