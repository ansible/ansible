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
from ansible.module_utils.network.fortimanager.fortimanager import FortiManagerHandler
import pytest

try:
    from ansible.modules.network.fortimanager import fmgr_fwobj_vip
except ImportError:
    pytest.skip("Could not load required modules for testing", allow_module_level=True)


def load_fixtures():
    fixture_path = os.path.join(os.path.dirname(__file__), 'fixtures') + "/{filename}.json".format(
        filename=os.path.splitext(os.path.basename(__file__))[0])
    try:
        with open(fixture_path, "r") as fixture_file:
            fixture_data = json.load(fixture_file)
    except IOError:
        return []
    return [fixture_data]


@pytest.fixture(autouse=True)
def module_mock(mocker):
    connection_class_mock = mocker.patch('ansible.module_utils.basic.AnsibleModule')
    return connection_class_mock


@pytest.fixture(autouse=True)
def connection_mock(mocker):
    connection_class_mock = mocker.patch('ansible.modules.network.fortimanager.fmgr_fwobj_vip.Connection')
    return connection_class_mock


@pytest.fixture(scope="function", params=load_fixtures())
def fixture_data(request):
    func_name = request.function.__name__.replace("test_", "")
    return request.param.get(func_name, None)


fmg_instance = FortiManagerHandler(connection_mock, module_mock)


def test_fmgr_firewall_vip_modify(fixture_data, mocker):
    mocker.patch("ansible.module_utils.network.fortimanager.fortimanager.FortiManagerHandler.process_request",
                 side_effect=fixture_data)
    #  Fixture sets used:###########################

    ##################################################
    # comment: Created by Ansible
    # ssl-send-empty-frags: None
    # srcintf-filter: None
    # ssl-max-version: None
    # ssl-server-session-state-max: None
    # ssl-hpkp: None
    # mapped-addr: None
    # ssl-client-session-state-timeout: None
    # src-filter: None
    # server-type: None
    # ssl-hpkp-include-subdomains: None
    # ssl-http-location-conversion: None
    # https-cookie-secure: None
    # mappedip: 10.7.220.25
    # ssl-server-cipher-suites: {'priority': None, 'cipher': None, 'versions': None}
    # protocol: tcp
    # ssl-hpkp-backup: None
    # ssl-dh-bits: None
    # dns-mapping-ttl: None
    # ssl-hsts-age: None
    # extaddr: None
    # ssl-client-renegotiation: None
    # monitor: None
    # service: None
    # ssl-hpkp-age: None
    # http-cookie-age: None
    # weblogic-server: None
    # http-cookie-share: None
    # color: 17
    # ssl-mode: None
    # portforward: enable
    # http-multiplex: None
    # http-cookie-generation: None
    # ssl-client-fallback: None
    # extip: 82.72.192.185
    # extintf: any
    # persistence: None
    # websphere-server: None
    # nat-source-vip: None
    # portmapping-type: None

    # adom: ansible
    # ssl-client-session-state-max: None
    # http-ip-header: None
    # http-ip-header-name: None
    # ssl-certificate: None
    # ssl-hsts: None
    # arp-reply: None
    # ssl-hsts-include-subdomains: None
    # ssl-min-version: None
    # ldb-method: None
    # ssl-server-session-state-timeout: None
    # ssl-server-min-version: None
    # http-cookie-domain: None
    # mappedport: 443
    # name: Basic PNAT Map Port 10443
    # ssl-cipher-suites: {'cipher': None, 'versions': None}
    # ssl-hpkp-primary: None
    # outlook-web-access: None
    # ssl-server-session-state-type: None
    # ssl-client-session-state-type: None

    # ssl-http-match-host: None

    # ssl-server-max-version: None
    # ssl-hpkp-report-uri: None
    # http-cookie-domain-from-host: None
    # ssl-algorithm: None
    # gratuitous-arp-interval: None
    # extport: 10443
    # max-embryonic-connections: None
    # mode: set
    # http-cookie-path: None
    # ssl-pfs: None
    # ssl-server-algorithm: None
    ##################################################
    ##################################################
    # comment: Created by Ansible
    # ssl-send-empty-frags: None
    # srcintf-filter: None
    # ssl-max-version: None
    # ssl-server-session-state-max: None
    # ssl-hpkp: None
    # ssl-hsts-include-subdomains: None
    # mapped-addr: None
    # src-filter: None
    # server-type: None
    # mode: set
    # ssl-hpkp-include-subdomains: None
    # ssl-http-location-conversion: None
    # https-cookie-secure: None
    # mappedip: 3.3.3.0/24, 4.0.0.0/24
    # ssl-server-cipher-suites: {'priority': None, 'cipher': None, 'versions': None}
    # protocol: None
    # ssl-hpkp-backup: None
    # ssl-dh-bits: None
    # dns-mapping-ttl: None
    # ssl-hsts-age: None
    # ssl-client-renegotiation: None
    # monitor: None
    # service: None
    # ssl-hpkp-age: None
    # http-cookie-age: None
    # adom: ansible
    # http-cookie-share: None
    # ssl-server-session-state-timeout: None
    # color: 12
    # ssl-mode: None
    # portforward: None
    # http-cookie-generation: None
    # max-embryonic-connections: None
    # ssl-client-fallback: None
    # ssl-hpkp-report-uri: None
    # extip: 192.168.0.1-192.168.0.100
    # extintf: dmz
    # persistence: None
    # websphere-server: None
    # nat-source-vip: None
    # portmapping-type: None
    # http-ip-header-name: None
    # weblogic-server: None
    # ssl-client-session-state-max: None
    # http-ip-header: None

    # ssl-hsts: None
    # arp-reply: None
    # extaddr: None
    # ssl-min-version: None
    # ldb-method: None
    # ssl-certificate: None
    # ssl-server-min-version: None
    # http-cookie-domain: None
    # mappedport: None
    # outlook-web-access: None
    # ssl-cipher-suites: {'cipher': None, 'versions': None}
    # ssl-hpkp-primary: None
    # name: Basic DNS Translation
    # ssl-server-session-state-type: None
    # ssl-client-session-state-type: None

    # ssl-http-match-host: None

    # ssl-pfs: None
    # ssl-server-max-version: None
    # ssl-client-session-state-timeout: None
    # http-cookie-domain-from-host: None
    # extport: None
    # ssl-server-algorithm: None
    # gratuitous-arp-interval: None
    # http-cookie-path: None
    # ssl-algorithm: None
    # http-multiplex: None
    ##################################################
    ##################################################
    # comment: Created by Ansible
    # ssl-send-empty-frags: None
    # srcintf-filter: None
    # ssl-max-version: None
    # ssl-server-session-state-max: None
    # ssl-hpkp: None
    # mapped-addr: google-play
    # ssl-client-session-state-timeout: None
    # src-filter: None
    # ldb-method: None
    # server-type: None
    # ssl-hpkp-include-subdomains: None
    # ssl-client-renegotiation: None
    # ssl-http-location-conversion: None
    # https-cookie-secure: None
    # mappedip: None
    # ssl-server-cipher-suites: {'priority': None, 'cipher': None, 'versions': None}
    # protocol: None
    # ssl-hpkp-backup: None
    # ssl-dh-bits: None
    # dns-mapping-ttl: None
    # ssl-hsts-age: None
    # extaddr: None
    # monitor: None
    # service: None
    # ssl-hpkp-age: None
    # http-cookie-age: None
    # weblogic-server: None
    # http-cookie-share: None
    # color: 5
    # ssl-mode: None
    # portforward: None
    # http-cookie-generation: None
    # ssl-client-fallback: None
    # extip: None
    # extintf: None
    # persistence: None
    # websphere-server: None
    # nat-source-vip: None
    # portmapping-type: None

    # adom: ansible
    # ssl-client-session-state-max: None
    # http-ip-header: None
    # http-ip-header-name: None
    # ssl-certificate: None
    # ssl-hsts: None
    # arp-reply: None
    # extport: None
    # ssl-min-version: None
    # ssl-server-algorithm: None
    # ssl-server-session-state-timeout: None
    # ssl-server-min-version: None
    # http-cookie-domain: None
    # mappedport: None
    # name: Basic FQDN Translation
    # ssl-cipher-suites: {'cipher': None, 'versions': None}
    # ssl-hpkp-primary: None
    # outlook-web-access: None
    # ssl-server-session-state-type: None
    # ssl-client-session-state-type: None

    # ssl-http-match-host: None

    # ssl-server-max-version: None
    # ssl-hpkp-report-uri: None
    # http-cookie-domain-from-host: None
    # ssl-algorithm: None
    # gratuitous-arp-interval: None
    # ssl-hsts-include-subdomains: None
    # max-embryonic-connections: None
    # mode: set
    # http-cookie-path: None
    # ssl-pfs: None
    # http-multiplex: None
    ##################################################
    ##################################################
    # comment: Created by Ansible
    # ssl-send-empty-frags: None
    # srcintf-filter: None
    # ssl-max-version: None
    # ssl-server-session-state-max: None
    # ssl-hpkp: None
    # mapped-addr: None
    # src-filter: None
    # server-type: None
    # mode: set
    # ssl-hpkp-include-subdomains: None
    # extport: None
    # ssl-http-location-conversion: None
    # https-cookie-secure: None
    # mappedip: 10.7.220.25
    # ssl-server-cipher-suites: {'priority': None, 'cipher': None, 'versions': None}
    # protocol: None
    # ssl-hpkp-backup: None
    # ssl-dh-bits: None
    # dns-mapping-ttl: None
    # ssl-hsts-age: None
    # ssl-server-algorithm: None
    # extaddr: None
    # monitor: None
    # service: None
    # ssl-hpkp-age: None
    # http-cookie-age: None
    # adom: ansible
    # http-cookie-share: None
    # ssl-server-session-state-timeout: None
    # color: 17
    # ssl-mode: None
    # portforward: None
    # http-cookie-generation: None
    # max-embryonic-connections: None
    # ssl-client-fallback: None
    # ssl-hpkp-report-uri: None
    # extip: 82.72.192.185
    # extintf: any
    # persistence: None
    # websphere-server: None
    # nat-source-vip: None
    # portmapping-type: None
    # http-ip-header-name: None
    # weblogic-server: None
    # ssl-client-session-state-max: None
    # http-ip-header: None

    # ssl-hsts: None
    # arp-reply: None
    # ssl-client-renegotiation: None
    # ssl-min-version: None
    # ldb-method: None
    # ssl-certificate: None
    # ssl-server-min-version: None
    # http-cookie-domain: None
    # mappedport: None
    # outlook-web-access: None
    # ssl-cipher-suites: {'cipher': None, 'versions': None}
    # ssl-hpkp-primary: None
    # name: Basic StaticNAT Map
    # ssl-server-session-state-type: None
    # ssl-client-session-state-type: None

    # ssl-http-match-host: None

    # ssl-pfs: None
    # ssl-client-session-state-timeout: None
    # http-cookie-domain-from-host: None
    # ssl-hsts-include-subdomains: None
    # ssl-server-max-version: None
    # gratuitous-arp-interval: None
    # http-cookie-path: None
    # ssl-algorithm: None
    # http-multiplex: None
    ##################################################
    ##################################################
    # comment: Created by Ansible
    # ssl-send-empty-frags: None
    # srcintf-filter: None
    # ssl-max-version: None
    # ssl-server-session-state-max: None
    # ssl-hpkp: None
    # mapped-addr: None
    # ssl-client-session-state-timeout: None
    # src-filter: None
    # server-type: None
    # ssl-hpkp-include-subdomains: None
    # ssl-client-renegotiation: None
    # ssl-http-location-conversion: None
    # https-cookie-secure: None
    # mappedip: 10.7.220.25
    # ssl-server-cipher-suites: {'priority': None, 'cipher': None, 'versions': None}
    # protocol: tcp
    # ssl-hpkp-backup: None
    # ssl-dh-bits: None
    # dns-mapping-ttl: None
    # ssl-hsts-age: None
    # extaddr: None
    # monitor: None
    # service: None
    # ssl-hpkp-age: None
    # http-cookie-age: None
    # weblogic-server: None
    # http-cookie-share: None
    # color: 17
    # ssl-mode: None
    # portforward: enable
    # http-cookie-generation: None
    # ssl-client-fallback: None
    # extip: 82.72.192.185
    # extintf: any
    # persistence: None
    # websphere-server: None
    # nat-source-vip: None
    # portmapping-type: None

    # adom: ansible
    # ssl-client-session-state-max: None
    # http-ip-header: None
    # http-ip-header-name: None
    # ssl-min-version: None
    # ssl-certificate: None
    # ssl-hsts: None
    # arp-reply: None
    # ssl-hsts-include-subdomains: None
    # http-multiplex: None
    # ldb-method: None
    # ssl-server-session-state-timeout: None
    # ssl-server-min-version: None
    # http-cookie-domain: None
    # mappedport: 443
    # name: Basic PNAT Map Port 10443
    # ssl-cipher-suites: {'cipher': None, 'versions': None}
    # ssl-hpkp-primary: None
    # outlook-web-access: None
    # ssl-server-session-state-type: None
    # ssl-client-session-state-type: None

    # ssl-http-match-host: None

    # ssl-server-max-version: None
    # ssl-hpkp-report-uri: None
    # http-cookie-domain-from-host: None
    # ssl-algorithm: None
    # gratuitous-arp-interval: None
    # extport: 10443
    # max-embryonic-connections: None
    # mode: set
    # http-cookie-path: None
    # ssl-pfs: None
    # ssl-server-algorithm: None
    ##################################################
    ##################################################
    # comment: None
    # ssl-send-empty-frags: None
    # srcintf-filter: None
    # ssl-max-version: None
    # ssl-server-session-state-max: None
    # ssl-hpkp: None
    # ssl-hsts-include-subdomains: None
    # mapped-addr: None
    # src-filter: None
    # server-type: None
    # mode: delete
    # ssl-hpkp-include-subdomains: None
    # ssl-http-location-conversion: None
    # https-cookie-secure: None
    # mappedip: None
    # ssl-server-cipher-suites: {'priority': None, 'cipher': None, 'versions': None}
    # protocol: None
    # ssl-hpkp-backup: None
    # ssl-dh-bits: None
    # dns-mapping-ttl: None
    # ssl-hsts-age: None
    # extaddr: None
    # monitor: None
    # service: None
    # ssl-hpkp-age: None
    # http-cookie-age: None
    # adom: ansible
    # http-cookie-share: None
    # ssl-server-session-state-timeout: None
    # color: None
    # ssl-mode: None
    # portforward: None
    # http-cookie-generation: None
    # max-embryonic-connections: None
    # ssl-client-fallback: None
    # ssl-hpkp-report-uri: None
    # extip: None
    # extintf: None
    # persistence: None
    # websphere-server: None
    # nat-source-vip: None
    # portmapping-type: None
    # http-ip-header-name: None
    # weblogic-server: None
    # ssl-client-session-state-max: None
    # http-ip-header: None

    # ssl-hsts: None
    # arp-reply: None
    # ssl-client-renegotiation: None
    # http-multiplex: None
    # ldb-method: None
    # ssl-certificate: None
    # ssl-server-min-version: None
    # http-cookie-domain: None
    # mappedport: None
    # outlook-web-access: None
    # ssl-cipher-suites: {'cipher': None, 'versions': None}
    # ssl-hpkp-primary: None
    # name: Basic PNAT Map Port 10443
    # ssl-server-session-state-type: None
    # ssl-client-session-state-type: None

    # ssl-http-match-host: None

    # ssl-pfs: None
    # ssl-server-max-version: None
    # ssl-client-session-state-timeout: None
    # http-cookie-domain-from-host: None
    # extport: None
    # ssl-server-algorithm: None
    # gratuitous-arp-interval: None
    # http-cookie-path: None
    # ssl-algorithm: None
    # ssl-min-version: None
    ##################################################
    ##################################################
    # comment: None
    # ssl-send-empty-frags: None
    # srcintf-filter: None
    # ssl-max-version: None
    # ssl-server-session-state-max: None
    # mappedip: None
    # mapped-addr: None
    # ssl-client-session-state-timeout: None
    # src-filter: None
    # ldb-method: None
    # server-type: None
    # ssl-hpkp-include-subdomains: None
    # ssl-http-location-conversion: None
    # https-cookie-secure: None
    # ssl-hpkp: None
    # ssl-server-cipher-suites: {'priority': None, 'cipher': None, 'versions': None}
    # protocol: None
    # ssl-hpkp-backup: None
    # ssl-dh-bits: None
    # dns-mapping-ttl: None
    # ssl-hsts-age: None
    # extaddr: None
    # ssl-client-renegotiation: None
    # monitor: None
    # service: None
    # ssl-hpkp-age: None
    # http-cookie-age: None
    # weblogic-server: None
    # http-cookie-share: None
    # color: None
    # ssl-mode: None
    # portforward: None
    # http-cookie-generation: None
    # ssl-client-fallback: None
    # extip: None
    # extintf: None
    # persistence: None
    # websphere-server: None
    # nat-source-vip: None
    # portmapping-type: None

    # adom: ansible
    # ssl-client-session-state-max: None
    # http-ip-header: None
    # http-ip-header-name: None
    # ssl-certificate: None
    # ssl-hsts: None
    # arp-reply: None
    # extport: None
    # http-multiplex: None
    # ssl-server-algorithm: None
    # ssl-server-session-state-timeout: None
    # ssl-server-min-version: None
    # http-cookie-domain: None
    # mappedport: None
    # name: Basic StaticNAT Map
    # ssl-cipher-suites: {'cipher': None, 'versions': None}
    # ssl-hpkp-primary: None
    # outlook-web-access: None
    # ssl-server-session-state-type: None
    # ssl-client-session-state-type: None

    # ssl-http-match-host: None

    # ssl-server-max-version: None
    # ssl-hpkp-report-uri: None
    # http-cookie-domain-from-host: None
    # ssl-algorithm: None
    # gratuitous-arp-interval: None
    # ssl-hsts-include-subdomains: None
    # max-embryonic-connections: None
    # mode: delete
    # http-cookie-path: None
    # ssl-pfs: None
    # ssl-min-version: None
    ##################################################
    ##################################################
    # comment: None
    # ssl-send-empty-frags: None
    # srcintf-filter: None
    # ssl-max-version: None
    # ssl-server-session-state-max: None
    # mappedip: None
    # mapped-addr: None
    # src-filter: None
    # server-type: None
    # mode: delete
    # ssl-hpkp-include-subdomains: None
    # extport: None
    # ssl-http-location-conversion: None
    # https-cookie-secure: None
    # ssl-hpkp: None
    # ssl-server-cipher-suites: {'priority': None, 'cipher': None, 'versions': None}
    # protocol: None
    # ssl-hpkp-backup: None
    # ssl-dh-bits: None
    # dns-mapping-ttl: None
    # ssl-hsts-age: None
    # ssl-server-algorithm: None
    # ssl-client-renegotiation: None
    # monitor: None
    # service: None
    # ssl-hpkp-age: None
    # http-cookie-age: None
    # adom: ansible
    # http-cookie-share: None
    # ssl-server-session-state-timeout: None
    # color: None
    # ssl-mode: None
    # portforward: None
    # http-multiplex: None
    # http-cookie-generation: None
    # max-embryonic-connections: None
    # ssl-client-fallback: None
    # ssl-hpkp-report-uri: None
    # extip: None
    # extintf: None
    # persistence: None
    # websphere-server: None
    # nat-source-vip: None
    # portmapping-type: None
    # http-ip-header-name: None
    # weblogic-server: None
    # ssl-client-session-state-max: None
    # http-ip-header: None
    # ssl-hsts: None
    # arp-reply: None
    # extaddr: None
    # ssl-hpkp-primary: None
    # ldb-method: None
    # ssl-certificate: None
    # ssl-server-min-version: None
    # http-cookie-domain: None
    # mappedport: None
    # outlook-web-access: None
    # ssl-cipher-suites: {'cipher': None, 'versions': None}
    # ssl-client-session-state-type: None
    # name: Basic DNS Translation
    # ssl-server-session-state-type: None

    # ssl-http-match-host: None
    # ssl-pfs: None
    # ssl-client-session-state-timeout: None
    # http-cookie-domain-from-host: None
    # ssl-hsts-include-subdomains: None
    # ssl-server-max-version: None
    # gratuitous-arp-interval: None
    # http-cookie-path: None
    # ssl-algorithm: None
    # ssl-min-version: None
    ##################################################
    ##################################################
    # ldb-method: None
    # ssl-send-empty-frags: None
    # srcintf-filter: None
    # ssl-max-version: None
    # ssl-server-session-state-max: None
    # mappedip: None
    # ssl-hsts: None
    # mapped-addr: None
    # src-filter: None
    # server-type: None
    # ssl-hpkp-include-subdomains: None
    # ssl-client-renegotiation: None
    # ssl-http-location-conversion: None
    # https-cookie-secure: None
    # extip: None
    # ssl-hpkp: None
    # ssl-server-cipher-suites: {'priority': None, 'cipher': None, 'versions': None}
    # protocol: None
    # ssl-hpkp-backup: None
    # ssl-dh-bits: None
    # dns-mapping-ttl: None
    # ssl-hsts-age: None
    # extaddr: None
    # ssl-hpkp-primary: None
    # monitor: None
    # service: None
    # ssl-hpkp-age: None
    # http-cookie-age: None
    # weblogic-server: None
    # http-cookie-share: None
    # name: Basic FQDN Translation
    # color: None
    # ssl-mode: None
    # portforward: None
    # http-cookie-generation: None
    # ssl-client-fallback: None

    # http-ip-header: None
    # persistence: None
    # websphere-server: None
    # nat-source-vip: None
    # portmapping-type: None
    # adom: ansible
    # ssl-client-session-state-max: None
    # extintf: None
    # ssl-server-max-version: None
    # http-ip-header-name: None
    # ssl-certificate: None
    # ssl-server-session-state-type: None
    # arp-reply: None
    # ssl-hsts-include-subdomains: None
    # ssl-min-version: None
    # ssl-server-algorithm: None
    # ssl-server-session-state-timeout: None
    # ssl-server-min-version: None
    # http-cookie-domain: None
    # mappedport: None
    # outlook-web-access: None
    # ssl-cipher-suites: {'cipher': None, 'versions': None}
    # ssl-client-session-state-type: None
    # ssl-http-match-host: None

    # ssl-client-session-state-timeout: None
    # comment: None
    # ssl-hpkp-report-uri: None
    # http-cookie-domain-from-host: None
    # ssl-algorithm: None
    # gratuitous-arp-interval: None
    # extport: None
    # max-embryonic-connections: None
    # mode: delete
    # http-cookie-path: None
    # ssl-pfs: None
    # http-multiplex: None
    ##################################################

    # Test using fixture 1 #
    output = fmgr_fwobj_vip.fmgr_firewall_vip_modify(fmg_instance, fixture_data[0]['paramgram_used'])
    assert output['raw_response']['status']['code'] == 0
    # Test using fixture 2 #
    output = fmgr_fwobj_vip.fmgr_firewall_vip_modify(fmg_instance, fixture_data[1]['paramgram_used'])
    assert output['raw_response']['status']['code'] == -10131
    # Test using fixture 3 #
    output = fmgr_fwobj_vip.fmgr_firewall_vip_modify(fmg_instance, fixture_data[2]['paramgram_used'])
    assert output['raw_response']['status']['code'] == 0
    # Test using fixture 4 #
    output = fmgr_fwobj_vip.fmgr_firewall_vip_modify(fmg_instance, fixture_data[3]['paramgram_used'])
    assert output['raw_response']['status']['code'] == 0
    # Test using fixture 5 #
    output = fmgr_fwobj_vip.fmgr_firewall_vip_modify(fmg_instance, fixture_data[4]['paramgram_used'])
    assert output['raw_response']['status']['code'] == 0
    # Test using fixture 6 #
    output = fmgr_fwobj_vip.fmgr_firewall_vip_modify(fmg_instance, fixture_data[5]['paramgram_used'])
    assert output['raw_response']['status']['code'] == 0
    # Test using fixture 7 #
    output = fmgr_fwobj_vip.fmgr_firewall_vip_modify(fmg_instance, fixture_data[6]['paramgram_used'])
    assert output['raw_response']['status']['code'] == 0
    # Test using fixture 8 #
    output = fmgr_fwobj_vip.fmgr_firewall_vip_modify(fmg_instance, fixture_data[7]['paramgram_used'])
    assert output['raw_response']['status']['code'] == -3
    # Test using fixture 9 #
    output = fmgr_fwobj_vip.fmgr_firewall_vip_modify(fmg_instance, fixture_data[8]['paramgram_used'])
    assert output['raw_response']['status']['code'] == 0
