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
    from ansible.modules.network.fortimanager import fmgr_device_provision_template
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
    connection_class_mock = mocker.patch('ansible.modules.network.fortimanager.'
                                         'fmgr_device_provision_template.Connection')
    return connection_class_mock


@pytest.fixture(scope="function", params=load_fixtures())
def fixture_data(request):
    func_name = request.function.__name__.replace("test_", "")
    return request.param.get(func_name, None)


fmg_instance = FortiManagerHandler(connection_mock, module_mock)


def test_get_devprof(fixture_data, mocker):
    mocker.patch("ansible.module_utils.network.fortimanager.fortimanager.FortiManagerHandler.process_request",
                 side_effect=fixture_data)
    #  Fixture sets used:###########################

    ##################################################
    # snmpv3_security_level: None
    # snmp_v2c_query_status: None
    # ntp_type: None
    # dns_suffix: None
    # snmpv3_queries: None
    # snmpv3_trap_status: None
    # snmp_v2c_name: None
    # syslog_facility: syslog
    # snmp_v2c_status: None
    # smtp_validate_cert: None
    # snmpv3_name: None
    # snmp_v2c_trap_src_ipv4: None
    # syslog_port: None
    # ntp_server: None
    # admin_https_port: None
    # ntp_status: None
    # syslog_server: None
    # dns_primary_ipv4: None
    # admin_timeout: None
    # snmpv3_auth_proto: None
    # smtp_port: None
    # snmpv3_priv_pwd: None
    # smtp_server: None
    # syslog_enc_algorithm: disable
    # dns_secondary_ipv4: None
    # smtp_username: None
    # snmpv3_auth_pwd: None
    # syslog_certificate: None
    # admin_fortiguard_target: None
    # snmpv3_query_port: None
    # smtp_password: None
    # adom: ansible
    # snmpv3_notify_hosts: None
    # syslog_mode: udp
    # snmp_v2c_query_port: None
    # snmp_v2c_trap_status: None
    # snmp_status: enable
    # syslog_status: None
    # admin_fortianalyzer_target: None
    # ntp_auth: None
    # snmp_v2c_id: None
    # admin_http_port: None
    # ntp_v3: None
    # snmp_v2c_query_hosts_ipv4: None
    # ntp_sync_interval: None
    # snmpv3_source_ip: None
    # snmpv3_trap_rport: None
    # admin_gui_theme: None
    # syslog_filter: None
    # ntp_auth_pwd: None
    # provisioning_template: ansibleTest
    # smtp_replyto: None
    # provision_targets: None
    # snmp_v2c_trap_port: None
    # snmpv3_priv_proto: None
    # admin_enable_fortiguard: None
    # admin_switch_controller: None
    # admin_language: None
    # smtp_conn_sec: None
    # mode: get
    # smtp_source_ipv4: None
    # snmpv3_status: None
    # delete_provisioning_template: None
    # snmp_v2c_trap_hosts_ipv4: None
    # admin_https_redirect: None
    ##################################################
    ##################################################
    # snmpv3_security_level: None
    # snmp_v2c_query_status: None
    # ntp_type: None
    # dns_suffix: None
    # snmpv3_queries: None
    # snmpv3_trap_status: None
    # snmp_v2c_name: None
    # syslog_facility: kernel
    # snmp_v2c_status: None
    # smtp_validate_cert: None
    # snmpv3_name: None
    # snmp_v2c_trap_src_ipv4: None
    # syslog_port: 514
    # ntp_server: None
    # admin_https_port: None
    # ntp_status: None
    # syslog_server: 10.7.220.59
    # dns_primary_ipv4: None
    # admin_timeout: None
    # snmpv3_auth_proto: None
    # smtp_port: None
    # snmpv3_priv_pwd: None
    # smtp_server: None
    # syslog_enc_algorithm: disable
    # dns_secondary_ipv4: None
    # smtp_replyto: None
    # smtp_username: None
    # snmpv3_auth_pwd: None
    # syslog_certificate: None
    # admin_fortiguard_target: None
    # snmpv3_query_port: None
    # smtp_password: None
    # adom: ansible
    # snmpv3_notify_hosts: None
    # syslog_mode: udp
    # snmp_v2c_query_port: None
    # snmp_v2c_trap_status: None
    # snmp_status: None
    # syslog_status: enable
    # admin_fortianalyzer_target: None
    # ntp_auth: None
    # snmp_v2c_id: None
    # admin_http_port: None
    # snmp_v2c_query_hosts_ipv4: None
    # ntp_sync_interval: None
    # snmpv3_source_ip: None
    # snmpv3_trap_rport: None
    # admin_gui_theme: None
    # syslog_filter: critical
    # ntp_auth_pwd: None
    # provisioning_template: ansibleTest
    # snmp_v2c_trap_hosts_ipv4: None
    # provision_targets: None
    # snmp_v2c_trap_port: None
    # snmpv3_priv_proto: None
    # admin_enable_fortiguard: None
    # admin_switch_controller: None
    # admin_language: None
    # smtp_conn_sec: None
    # mode: get
    # smtp_source_ipv4: None
    # snmpv3_status: None
    # delete_provisioning_template: None
    # ntp_v3: None
    # admin_https_redirect: None
    ##################################################
    ##################################################
    # snmpv3_security_level: None
    # snmp_v2c_query_status: enable
    # ntp_type: None
    # dns_suffix: None
    # snmpv3_queries: None
    # snmpv3_trap_status: None
    # snmp_v2c_name: ansibleV2c
    # syslog_facility: syslog
    # snmp_v2c_status: enable
    # smtp_validate_cert: None
    # snmpv3_name: None
    # snmp_v2c_trap_src_ipv4: 10.7.220.41
    # syslog_port: None
    # ntp_server: None
    # admin_https_port: None
    # ntp_status: None
    # syslog_server: None
    # dns_primary_ipv4: None
    # admin_timeout: None
    # snmpv3_auth_proto: None
    # smtp_port: None
    # snmpv3_priv_pwd: None
    # smtp_server: None
    # syslog_enc_algorithm: disable
    # dns_secondary_ipv4: None
    # smtp_username: None
    # snmpv3_auth_pwd: None
    # syslog_certificate: None
    # admin_fortiguard_target: None
    # snmpv3_query_port: None
    # smtp_password: None
    # adom: ansible
    # snmpv3_notify_hosts: None
    # syslog_mode: udp
    # snmp_v2c_query_port: 162
    # snmp_v2c_trap_status: enable
    # snmp_status: enable
    # syslog_status: None
    # admin_fortianalyzer_target: None
    # ntp_auth: None
    # snmp_v2c_id: 1
    # admin_http_port: None
    # ntp_v3: None
    # snmp_v2c_query_hosts_ipv4: 10.7.220.59 255.255.255.255, 10.7.220.0 255.255.255.0
    # ntp_sync_interval: None
    # snmpv3_source_ip: None
    # snmpv3_trap_rport: None
    # admin_gui_theme: None
    # syslog_filter: None
    # ntp_auth_pwd: None
    # provisioning_template: ansibleTest
    # smtp_replyto: None
    # provision_targets: None
    # snmp_v2c_trap_port: 161
    # snmpv3_priv_proto: None
    # admin_enable_fortiguard: None
    # admin_switch_controller: None
    # admin_language: None
    # smtp_conn_sec: None
    # mode: get
    # smtp_source_ipv4: None
    # snmpv3_status: None
    # delete_provisioning_template: None
    # snmp_v2c_trap_hosts_ipv4: 10.7.220.59 255.255.255.255, 10.7.220.60 255.255.255.255
    # admin_https_redirect: None
    ##################################################
    ##################################################
    # snmpv3_security_level: auth-priv
    # snmp_v2c_query_status: None
    # provision_targets: None
    # ntp_type: None
    # dns_suffix: None
    # snmpv3_queries: enable
    # snmpv3_trap_status: enable
    # snmp_v2c_name: None
    # syslog_facility: syslog
    # snmp_v2c_status: None
    # smtp_validate_cert: None
    # snmpv3_name: ansibleSNMPv3
    # snmp_v2c_id: None
    # syslog_port: None
    # ntp_server: None
    # admin_https_port: None
    # ntp_status: None
    # syslog_server: None
    # admin_switch_controller: None
    # admin_timeout: None
    # snmpv3_auth_proto: sha
    # smtp_port: None
    # snmpv3_priv_pwd: fortinet
    # smtp_server: None
    # syslog_enc_algorithm: disable
    # snmp_v2c_query_hosts_ipv4: None
    # smtp_username: None
    # mode: get
    # syslog_certificate: None
    # admin_fortiguard_target: None
    # snmpv3_query_port: 161
    # smtp_password: None
    # adom: ansible
    # snmpv3_notify_hosts: 10.7.220.59,10.7.220.60
    # syslog_mode: udp
    # snmp_v2c_query_port: None
    # snmp_v2c_trap_status: None
    # snmp_status: enable
    # syslog_status: None
    # snmp_v2c_trap_hosts_ipv4: None
    # admin_fortianalyzer_target: None
    # snmp_v2c_trap_src_ipv4: None
    # admin_http_port: None
    # dns_secondary_ipv4: None
    # syslog_filter: None
    # snmpv3_source_ip: 0.0.0.0
    # snmpv3_trap_rport: 162
    # admin_gui_theme: None
    # ntp_sync_interval: None
    # ntp_auth_pwd: None
    # provisioning_template: ansibleTest
    # ntp_v3: None
    # ntp_auth: None
    # snmp_v2c_trap_port: None
    # snmpv3_priv_proto: aes256
    # admin_enable_fortiguard: None
    # dns_primary_ipv4: None
    # admin_language: None
    # smtp_conn_sec: None
    # snmpv3_auth_pwd: fortinet
    # smtp_source_ipv4: None
    # snmpv3_status: enable
    # delete_provisioning_template: None
    # smtp_replyto: None
    # admin_https_redirect: None
    ##################################################
    ##################################################
    # snmpv3_security_level: None
    # snmp_v2c_query_status: None
    # ntp_type: fortiguard
    # dns_suffix: None
    # snmpv3_queries: None
    # snmpv3_trap_status: None
    # snmp_v2c_name: None
    # syslog_facility: syslog
    # snmp_v2c_status: None
    # smtp_validate_cert: None
    # snmpv3_name: None
    # snmp_v2c_trap_src_ipv4: None
    # syslog_port: None
    # ntp_server: None
    # admin_https_port: None
    # ntp_status: enable
    # syslog_server: None
    # dns_primary_ipv4: None
    # admin_timeout: None
    # snmpv3_auth_proto: None
    # smtp_port: None
    # snmpv3_priv_pwd: None
    # smtp_server: None
    # syslog_enc_algorithm: disable
    # dns_secondary_ipv4: None
    # smtp_replyto: None
    # smtp_username: None
    # snmpv3_auth_pwd: None
    # syslog_certificate: None
    # admin_fortiguard_target: None
    # snmpv3_query_port: None
    # smtp_password: None
    # adom: ansible
    # snmpv3_notify_hosts: None
    # syslog_mode: udp
    # snmp_v2c_query_port: None
    # snmp_v2c_trap_status: None
    # snmp_status: None
    # syslog_status: None
    # admin_fortianalyzer_target: None
    # ntp_auth: None
    # snmp_v2c_id: None
    # admin_http_port: None
    # snmp_v2c_query_hosts_ipv4: None
    # ntp_sync_interval: 60
    # snmpv3_source_ip: None
    # snmpv3_trap_rport: None
    # admin_gui_theme: None
    # syslog_filter: None
    # ntp_auth_pwd: None
    # provisioning_template: ansibleTest
    # snmp_v2c_trap_hosts_ipv4: None
    # provision_targets: None
    # snmp_v2c_trap_port: None
    # snmpv3_priv_proto: None
    # admin_enable_fortiguard: None
    # admin_switch_controller: None
    # admin_language: None
    # smtp_conn_sec: None
    # mode: get
    # smtp_source_ipv4: None
    # snmpv3_status: None
    # delete_provisioning_template: None
    # ntp_v3: None
    # admin_https_redirect: None
    ##################################################
    ##################################################
    # snmpv3_security_level: None
    # snmp_v2c_query_status: None
    # ntp_type: custom
    # dns_suffix: None
    # snmpv3_queries: None
    # snmpv3_trap_status: None
    # snmp_v2c_name: None
    # syslog_facility: syslog
    # snmp_v2c_status: None
    # smtp_validate_cert: None
    # snmpv3_name: None
    # snmp_v2c_trap_src_ipv4: None
    # syslog_port: None
    # ntp_server: 10.7.220.32,10.7.220.1
    # admin_https_port: None
    # ntp_status: enable
    # syslog_server: None
    # dns_primary_ipv4: None
    # admin_timeout: None
    # snmpv3_auth_proto: None
    # smtp_port: None
    # snmpv3_priv_pwd: None
    # smtp_server: None
    # syslog_enc_algorithm: disable
    # dns_secondary_ipv4: None
    # smtp_username: None
    # snmpv3_auth_pwd: None
    # syslog_certificate: None
    # admin_fortiguard_target: None
    # snmpv3_query_port: None
    # smtp_password: None
    # adom: ansible
    # snmpv3_notify_hosts: None
    # syslog_mode: udp
    # snmp_v2c_query_port: None
    # snmp_v2c_trap_status: None
    # snmp_status: None
    # syslog_status: None
    # admin_fortianalyzer_target: None
    # ntp_auth: enable
    # snmp_v2c_id: None
    # admin_http_port: None
    # ntp_v3: None
    # snmp_v2c_query_hosts_ipv4: None
    # ntp_sync_interval: 60
    # snmpv3_source_ip: None
    # snmpv3_trap_rport: None
    # admin_gui_theme: None
    # syslog_filter: None
    # ntp_auth_pwd: fortinet
    # provisioning_template: ansibleTest
    # smtp_replyto: None
    # provision_targets: None
    # snmp_v2c_trap_port: None
    # snmpv3_priv_proto: None
    # admin_enable_fortiguard: None
    # admin_switch_controller: None
    # admin_language: None
    # smtp_conn_sec: None
    # mode: get
    # smtp_source_ipv4: None
    # snmpv3_status: None
    # delete_provisioning_template: None
    # snmp_v2c_trap_hosts_ipv4: None
    # admin_https_redirect: None
    ##################################################
    ##################################################
    # snmpv3_security_level: None
    # snmp_v2c_query_status: None
    # ntp_type: None
    # dns_suffix: None
    # snmpv3_queries: None
    # snmpv3_trap_status: None
    # snmp_v2c_name: None
    # syslog_facility: syslog
    # snmp_v2c_status: None
    # smtp_validate_cert: None
    # snmpv3_name: None
    # snmp_v2c_trap_src_ipv4: None
    # syslog_port: None
    # ntp_server: None
    # admin_https_port: 4433
    # ntp_status: None
    # syslog_server: None
    # dns_primary_ipv4: None
    # admin_timeout: 60
    # snmpv3_auth_proto: None
    # smtp_port: None
    # snmpv3_priv_pwd: None
    # smtp_server: None
    # syslog_enc_algorithm: disable
    # dns_secondary_ipv4: None
    # smtp_replyto: None
    # smtp_username: None
    # snmpv3_auth_pwd: None
    # syslog_certificate: None
    # admin_fortiguard_target: None
    # snmpv3_query_port: None
    # smtp_password: None
    # adom: ansible
    # snmpv3_notify_hosts: None
    # syslog_mode: udp
    # snmp_v2c_query_port: None
    # snmp_v2c_trap_status: None
    # snmp_status: None
    # syslog_status: None
    # admin_fortianalyzer_target: 10.7.220.38
    # ntp_auth: None
    # snmp_v2c_id: None
    # admin_http_port: 8080
    # snmp_v2c_query_hosts_ipv4: None
    # ntp_sync_interval: None
    # snmpv3_source_ip: None
    # snmpv3_trap_rport: None
    # admin_gui_theme: blue
    # syslog_filter: None
    # ntp_auth_pwd: None
    # provisioning_template: ansibleTest
    # snmp_v2c_trap_hosts_ipv4: None
    # provision_targets: None
    # snmp_v2c_trap_port: None
    # snmpv3_priv_proto: None
    # admin_enable_fortiguard: this-fmg
    # admin_switch_controller: enable
    # admin_language: english
    # smtp_conn_sec: None
    # mode: get
    # smtp_source_ipv4: None
    # snmpv3_status: None
    # delete_provisioning_template: None
    # ntp_v3: None
    # admin_https_redirect: enable
    ##################################################
    ##################################################
    # snmpv3_security_level: None
    # snmp_v2c_query_status: None
    # ntp_type: None
    # dns_suffix: None
    # snmpv3_queries: None
    # snmpv3_trap_status: None
    # snmp_v2c_name: None
    # syslog_facility: syslog
    # snmp_v2c_status: None
    # smtp_validate_cert: disable
    # snmpv3_name: None
    # snmp_v2c_trap_src_ipv4: None
    # syslog_port: None
    # ntp_server: None
    # admin_https_port: None
    # ntp_status: None
    # syslog_server: None
    # dns_primary_ipv4: None
    # admin_timeout: None
    # snmpv3_auth_proto: None
    # smtp_port: 25
    # snmpv3_priv_pwd: None
    # smtp_server: 10.7.220.32
    # syslog_enc_algorithm: disable
    # dns_secondary_ipv4: None
    # smtp_username: ansible
    # snmpv3_auth_pwd: None
    # syslog_certificate: None
    # admin_fortiguard_target: None
    # snmpv3_query_port: None
    # smtp_password: fortinet
    # adom: ansible
    # snmpv3_notify_hosts: None
    # syslog_mode: udp
    # snmp_v2c_query_port: None
    # snmp_v2c_trap_status: None
    # snmp_status: None
    # syslog_status: None
    # admin_fortianalyzer_target: None
    # ntp_auth: None
    # snmp_v2c_id: None
    # admin_http_port: None
    # ntp_v3: None
    # snmp_v2c_query_hosts_ipv4: None
    # ntp_sync_interval: None
    # snmpv3_source_ip: None
    # snmpv3_trap_rport: None
    # admin_gui_theme: None
    # syslog_filter: None
    # ntp_auth_pwd: None
    # provisioning_template: ansibleTest
    # smtp_replyto: ansible@do-not-reply.com
    # provision_targets: None
    # snmp_v2c_trap_port: None
    # snmpv3_priv_proto: None
    # admin_enable_fortiguard: None
    # admin_switch_controller: None
    # admin_language: None
    # smtp_conn_sec: starttls
    # mode: get
    # smtp_source_ipv4: 0.0.0.0
    # snmpv3_status: None
    # delete_provisioning_template: None
    # snmp_v2c_trap_hosts_ipv4: None
    # admin_https_redirect: None
    ##################################################
    ##################################################
    # snmpv3_security_level: None
    # snmp_v2c_query_status: None
    # ntp_type: None
    # dns_suffix: ansible.local
    # snmpv3_queries: None
    # snmpv3_trap_status: None
    # snmp_v2c_name: None
    # syslog_facility: syslog
    # snmp_v2c_status: None
    # smtp_validate_cert: None
    # snmpv3_name: None
    # snmp_v2c_trap_src_ipv4: None
    # syslog_port: None
    # ntp_server: None
    # admin_https_port: None
    # ntp_status: None
    # syslog_server: None
    # dns_primary_ipv4: 8.8.8.8
    # admin_timeout: None
    # snmpv3_auth_proto: None
    # smtp_port: None
    # snmpv3_priv_pwd: None
    # smtp_server: None
    # syslog_enc_algorithm: disable
    # dns_secondary_ipv4: 4.4.4.4
    # smtp_replyto: None
    # smtp_username: None
    # snmpv3_auth_pwd: None
    # syslog_certificate: None
    # admin_fortiguard_target: None
    # snmpv3_query_port: None
    # smtp_password: None
    # adom: ansible
    # snmpv3_notify_hosts: None
    # syslog_mode: udp
    # snmp_v2c_query_port: None
    # snmp_v2c_trap_status: None
    # snmp_status: None
    # syslog_status: None
    # admin_fortianalyzer_target: None
    # ntp_auth: None
    # snmp_v2c_id: None
    # admin_http_port: None
    # snmp_v2c_query_hosts_ipv4: None
    # ntp_sync_interval: None
    # snmpv3_source_ip: None
    # snmpv3_trap_rport: None
    # admin_gui_theme: None
    # syslog_filter: None
    # ntp_auth_pwd: None
    # provisioning_template: ansibleTest
    # snmp_v2c_trap_hosts_ipv4: None
    # provision_targets: None
    # snmp_v2c_trap_port: None
    # snmpv3_priv_proto: None
    # admin_enable_fortiguard: None
    # admin_switch_controller: None
    # admin_language: None
    # smtp_conn_sec: None
    # mode: get
    # smtp_source_ipv4: None
    # snmpv3_status: None
    # delete_provisioning_template: None
    # ntp_v3: None
    # admin_https_redirect: None
    ##################################################
    ##################################################
    # snmpv3_security_level: None
    # snmp_v2c_query_status: None
    # ntp_type: None
    # dns_suffix: None
    # snmpv3_queries: None
    # snmpv3_trap_status: None
    # snmp_v2c_name: None
    # syslog_facility: syslog
    # snmp_v2c_status: None
    # smtp_validate_cert: None
    # snmpv3_name: None
    # snmp_v2c_trap_src_ipv4: None
    # syslog_port: None
    # ntp_server: None
    # admin_https_port: None
    # ntp_status: None
    # syslog_server: None
    # dns_primary_ipv4: None
    # admin_timeout: None
    # snmpv3_auth_proto: None
    # smtp_port: None
    # snmpv3_priv_pwd: None
    # smtp_server: None
    # syslog_enc_algorithm: disable
    # dns_secondary_ipv4: None
    # smtp_username: None
    # snmpv3_auth_pwd: None
    # syslog_certificate: None
    # admin_fortiguard_target: None
    # snmpv3_query_port: None
    # smtp_password: None
    # adom: ansible
    # snmpv3_notify_hosts: None
    # syslog_mode: udp
    # snmp_v2c_query_port: None
    # snmp_v2c_trap_status: None
    # snmp_status: None
    # syslog_status: None
    # admin_fortianalyzer_target: None
    # ntp_auth: None
    # snmp_v2c_id: None
    # admin_http_port: None
    # ntp_v3: None
    # snmp_v2c_query_hosts_ipv4: None
    # ntp_sync_interval: None
    # snmpv3_source_ip: None
    # snmpv3_trap_rport: None
    # admin_gui_theme: None
    # syslog_filter: None
    # ntp_auth_pwd: None
    # provisioning_template: ansibleTest
    # smtp_replyto: None
    # provision_targets: FGT1,FGT2
    # snmp_v2c_trap_port: None
    # snmpv3_priv_proto: None
    # admin_enable_fortiguard: None
    # admin_switch_controller: None
    # admin_language: None
    # smtp_conn_sec: None
    # mode: get
    # smtp_source_ipv4: None
    # snmpv3_status: None
    # delete_provisioning_template: None
    # snmp_v2c_trap_hosts_ipv4: None
    # admin_https_redirect: None
    ##################################################

    # Test using fixture 1 #
    output = fmgr_device_provision_template.get_devprof(fmg_instance, fixture_data[0]['paramgram_used'])
    assert isinstance(output['raw_response'], dict) is True
    # Test using fixture 2 #
    output = fmgr_device_provision_template.get_devprof(fmg_instance, fixture_data[1]['paramgram_used'])
    assert isinstance(output['raw_response'], dict) is True
    # Test using fixture 3 #
    output = fmgr_device_provision_template.get_devprof(fmg_instance, fixture_data[2]['paramgram_used'])
    assert isinstance(output['raw_response'], dict) is True
    # Test using fixture 4 #
    output = fmgr_device_provision_template.get_devprof(fmg_instance, fixture_data[3]['paramgram_used'])
    assert isinstance(output['raw_response'], dict) is True
    # Test using fixture 5 #
    output = fmgr_device_provision_template.get_devprof(fmg_instance, fixture_data[4]['paramgram_used'])
    assert isinstance(output['raw_response'], dict) is True
    # Test using fixture 6 #
    output = fmgr_device_provision_template.get_devprof(fmg_instance, fixture_data[5]['paramgram_used'])
    assert isinstance(output['raw_response'], dict) is True
    # Test using fixture 7 #
    output = fmgr_device_provision_template.get_devprof(fmg_instance, fixture_data[6]['paramgram_used'])
    assert isinstance(output['raw_response'], dict) is True
    # Test using fixture 8 #
    output = fmgr_device_provision_template.get_devprof(fmg_instance, fixture_data[7]['paramgram_used'])
    assert isinstance(output['raw_response'], dict) is True
    # Test using fixture 9 #
    output = fmgr_device_provision_template.get_devprof(fmg_instance, fixture_data[8]['paramgram_used'])
    assert isinstance(output['raw_response'], dict) is True
    # Test using fixture 10 #
    output = fmgr_device_provision_template.get_devprof(fmg_instance, fixture_data[9]['paramgram_used'])
    assert isinstance(output['raw_response'], dict) is True


def test_set_devprof(fixture_data, mocker):
    mocker.patch("ansible.module_utils.network.fortimanager.fortimanager.FortiManagerHandler.process_request",
                 side_effect=fixture_data)
    #  Fixture sets used:###########################

    ##################################################
    # snmpv3_security_level: None
    # snmp_v2c_query_status: None
    # smtp_port: None
    # ntp_type: None
    # dns_suffix: None
    # snmpv3_queries: None
    # snmpv3_trap_status: None
    # snmp_v2c_name: None
    # syslog_facility: syslog
    # snmp_v2c_status: None
    # smtp_validate_cert: None
    # snmpv3_name: None
    # snmp_v2c_trap_src_ipv4: None
    # syslog_port: None
    # ntp_server: None
    # admin_https_port: None
    # ntp_status: None
    # syslog_server: None
    # dns_primary_ipv4: None
    # admin_timeout: None
    # snmpv3_auth_proto: None
    # ntp_auth: None
    # snmpv3_priv_pwd: None
    # smtp_server: None
    # syslog_enc_algorithm: disable
    # dns_secondary_ipv4: None
    # smtp_replyto: None
    # smtp_username: None
    # snmpv3_auth_pwd: None
    # syslog_certificate: None
    # admin_fortiguard_target: None
    # snmpv3_query_port: None
    # smtp_password: None
    # adom: ansible
    # snmpv3_notify_hosts: None
    # syslog_mode: udp
    # snmp_v2c_query_port: None
    # snmp_v2c_trap_status: None
    # snmp_status: None
    # syslog_status: None
    # admin_fortianalyzer_target: None
    # snmp_v2c_id: None
    # admin_http_port: None
    # snmp_v2c_query_hosts_ipv4: None
    # ntp_sync_interval: None
    # snmpv3_source_ip: None
    # snmpv3_trap_rport: None
    # admin_gui_theme: None
    # syslog_filter: None
    # ntp_auth_pwd: None
    # provisioning_template: None
    # snmp_v2c_trap_hosts_ipv4: None
    # provision_targets: None
    # snmp_v2c_trap_port: None
    # snmpv3_priv_proto: None
    # admin_enable_fortiguard: None
    # admin_switch_controller: None
    # admin_language: None
    # smtp_conn_sec: None
    # mode: delete
    # smtp_source_ipv4: None
    # snmpv3_status: None
    # delete_provisioning_template: ansibleTest
    # ntp_v3: None
    # admin_https_redirect: None
    ##################################################

    # Test using fixture 1 #
    output = fmgr_device_provision_template.set_devprof(fmg_instance, fixture_data[0]['paramgram_used'])
    assert output['raw_response']['status']['code'] == 0


def test_set_devprof_scope(fixture_data, mocker):
    mocker.patch("ansible.module_utils.network.fortimanager.fortimanager.FortiManagerHandler.process_request",
                 side_effect=fixture_data)
    #  Fixture sets used:###########################

    ##################################################
    # snmpv3_security_level: None
    # snmp_v2c_query_status: None
    # provision_targets: FGT1,FGT2
    # ntp_type: None
    # dns_suffix: None
    # snmpv3_queries: None
    # snmpv3_trap_status: None
    # snmp_v2c_name: None
    # syslog_facility: syslog
    # snmp_v2c_status: None
    # smtp_validate_cert: None
    # snmpv3_name: None
    # snmp_v2c_id: None
    # syslog_port: None
    # ntp_server: None
    # admin_https_port: None
    # ntp_status: None
    # syslog_server: None
    # admin_switch_controller: None
    # admin_timeout: None
    # snmpv3_auth_proto: None
    # smtp_port: None
    # snmpv3_priv_pwd: None
    # smtp_server: None
    # syslog_enc_algorithm: disable
    # snmp_v2c_query_hosts_ipv4: None
    # smtp_username: None
    # mode: set
    # syslog_certificate: None
    # admin_fortiguard_target: None
    # snmpv3_query_port: None
    # smtp_password: None
    # adom: ansible
    # snmpv3_notify_hosts: None
    # syslog_mode: udp
    # snmp_v2c_query_port: None
    # snmp_v2c_trap_status: None
    # snmp_status: None
    # syslog_status: None
    # admin_https_redirect: None
    # admin_fortianalyzer_target: None
    # snmp_v2c_trap_src_ipv4: None
    # admin_http_port: None
    # dns_secondary_ipv4: None
    # syslog_filter: None
    # snmpv3_source_ip: None
    # snmpv3_trap_rport: None
    # admin_gui_theme: None
    # ntp_sync_interval: None
    # ntp_auth_pwd: None
    # provisioning_template: ansibleTest
    # smtp_replyto: None
    # ntp_auth: None
    # snmp_v2c_trap_port: None
    # snmpv3_priv_proto: None
    # admin_enable_fortiguard: None
    # dns_primary_ipv4: None
    # admin_language: None
    # smtp_conn_sec: None
    # snmpv3_auth_pwd: None
    # smtp_source_ipv4: None
    # snmpv3_status: None
    # delete_provisioning_template: None
    # snmp_v2c_trap_hosts_ipv4: None
    # ntp_v3: None
    ##################################################

    # Test using fixture 1 #
    output = fmgr_device_provision_template.set_devprof_scope(fmg_instance, fixture_data[0]['paramgram_used'])
    assert output['raw_response']['status']['code'] == 0


def test_set_devprof_snmp(fixture_data, mocker):
    mocker.patch("ansible.module_utils.network.fortimanager.fortimanager.FortiManagerHandler.process_request",
                 side_effect=fixture_data)
    #  Fixture sets used:###########################

    ##################################################
    # snmpv3_security_level: None
    # snmp_v2c_query_status: None
    # provision_targets: None
    # ntp_type: None
    # dns_suffix: None
    # snmpv3_queries: None
    # snmpv3_trap_status: None
    # snmp_v2c_name: None
    # syslog_facility: syslog
    # snmp_v2c_status: None
    # smtp_validate_cert: None
    # snmpv3_name: None
    # snmp_v2c_id: None
    # syslog_port: None
    # ntp_server: None
    # admin_https_port: None
    # ntp_status: None
    # syslog_server: None
    # admin_switch_controller: None
    # admin_timeout: None
    # snmpv3_auth_proto: None
    # smtp_port: None
    # snmpv3_priv_pwd: None
    # smtp_server: None
    # syslog_enc_algorithm: disable
    # snmp_v2c_query_hosts_ipv4: None
    # smtp_username: None
    # mode: set
    # syslog_certificate: None
    # admin_fortiguard_target: None
    # snmpv3_query_port: None
    # smtp_password: None
    # adom: ansible
    # snmpv3_notify_hosts: None
    # syslog_mode: udp
    # snmp_v2c_query_port: None
    # snmp_v2c_trap_status: None
    # snmp_status: enable
    # syslog_status: None
    # admin_https_redirect: None
    # admin_fortianalyzer_target: None
    # snmp_v2c_trap_src_ipv4: None
    # admin_http_port: None
    # dns_secondary_ipv4: None
    # syslog_filter: None
    # snmpv3_source_ip: None
    # snmpv3_trap_rport: None
    # admin_gui_theme: None
    # ntp_sync_interval: None
    # ntp_auth_pwd: None
    # provisioning_template: ansibleTest
    # smtp_replyto: None
    # ntp_auth: None
    # snmp_v2c_trap_port: None
    # snmpv3_priv_proto: None
    # admin_enable_fortiguard: None
    # dns_primary_ipv4: None
    # admin_language: None
    # smtp_conn_sec: None
    # snmpv3_auth_pwd: None
    # smtp_source_ipv4: None
    # snmpv3_status: None
    # delete_provisioning_template: None
    # snmp_v2c_trap_hosts_ipv4: None
    # ntp_v3: None
    ##################################################
    ##################################################
    # snmpv3_security_level: None
    # snmp_v2c_query_status: enable
    # provision_targets: None
    # ntp_type: None
    # dns_suffix: None
    # snmpv3_queries: None
    # snmpv3_trap_status: None
    # snmp_v2c_name: ansibleV2c
    # syslog_facility: syslog
    # snmp_v2c_status: enable
    # smtp_validate_cert: None
    # snmpv3_name: None
    # snmp_v2c_id: 1
    # syslog_port: None
    # ntp_server: None
    # admin_https_port: None
    # ntp_status: None
    # syslog_server: None
    # admin_switch_controller: None
    # admin_timeout: None
    # snmpv3_auth_proto: None
    # smtp_port: None
    # snmpv3_priv_pwd: None
    # smtp_server: None
    # syslog_enc_algorithm: disable
    # snmp_v2c_query_hosts_ipv4: 10.7.220.59 255.255.255.255, 10.7.220.0 255.255.255.0
    # smtp_username: None
    # mode: set
    # syslog_certificate: None
    # admin_fortiguard_target: None
    # snmpv3_query_port: None
    # smtp_password: None
    # adom: ansible
    # snmpv3_notify_hosts: None
    # syslog_mode: udp
    # snmp_v2c_query_port: 162
    # snmp_v2c_trap_status: enable
    # snmp_status: enable
    # syslog_status: None
    # admin_https_redirect: None
    # admin_fortianalyzer_target: None
    # snmp_v2c_trap_src_ipv4: 10.7.220.41
    # admin_http_port: None
    # dns_secondary_ipv4: None
    # syslog_filter: None
    # snmpv3_source_ip: None
    # snmpv3_trap_rport: None
    # admin_gui_theme: None
    # ntp_sync_interval: None
    # ntp_auth_pwd: None
    # provisioning_template: ansibleTest
    # smtp_replyto: None
    # ntp_auth: None
    # snmp_v2c_trap_port: 161
    # snmpv3_priv_proto: None
    # admin_enable_fortiguard: None
    # dns_primary_ipv4: None
    # admin_language: None
    # smtp_conn_sec: None
    # snmpv3_auth_pwd: None
    # smtp_source_ipv4: None
    # snmpv3_status: None
    # delete_provisioning_template: None
    # snmp_v2c_trap_hosts_ipv4: 10.7.220.59 255.255.255.255, 10.7.220.60 255.255.255.255
    # ntp_v3: None
    ##################################################
    ##################################################
    # snmpv3_security_level: auth-priv
    # snmp_v2c_query_status: None
    # ntp_type: None
    # dns_suffix: None
    # snmpv3_queries: enable
    # snmpv3_trap_status: enable
    # snmp_v2c_name: None
    # syslog_facility: syslog
    # snmp_v2c_status: None
    # smtp_validate_cert: None
    # snmpv3_name: ansibleSNMPv3
    # snmp_v2c_trap_src_ipv4: None
    # syslog_port: None
    # ntp_server: None
    # admin_https_port: None
    # ntp_status: None
    # syslog_server: None
    # dns_primary_ipv4: None
    # admin_timeout: None
    # snmpv3_auth_proto: sha
    # smtp_port: None
    # snmpv3_priv_pwd: fortinet
    # smtp_server: None
    # syslog_enc_algorithm: disable
    # dns_secondary_ipv4: None
    # smtp_username: None
    # snmpv3_auth_pwd: fortinet
    # syslog_certificate: None
    # admin_fortiguard_target: None
    # snmpv3_query_port: 161
    # smtp_password: None
    # adom: ansible
    # snmpv3_notify_hosts: 10.7.220.59,10.7.220.60
    # syslog_mode: udp
    # snmp_v2c_query_port: None
    # snmp_v2c_trap_status: None
    # snmp_status: enable
    # syslog_status: None
    # admin_fortianalyzer_target: None
    # ntp_auth: None
    # snmp_v2c_id: None
    # admin_http_port: None
    # ntp_v3: None
    # snmp_v2c_query_hosts_ipv4: None
    # ntp_sync_interval: None
    # snmpv3_source_ip: 0.0.0.0
    # snmpv3_trap_rport: 162
    # admin_gui_theme: None
    # syslog_filter: None
    # ntp_auth_pwd: None
    # provisioning_template: ansibleTest
    # smtp_replyto: None
    # provision_targets: None
    # snmp_v2c_trap_port: None
    # snmpv3_priv_proto: aes256
    # admin_enable_fortiguard: None
    # admin_switch_controller: None
    # admin_language: None
    # smtp_conn_sec: None
    # mode: set
    # smtp_source_ipv4: None
    # snmpv3_status: enable
    # delete_provisioning_template: None
    # snmp_v2c_trap_hosts_ipv4: None
    # admin_https_redirect: None
    ##################################################

    # Test using fixture 1 #
    output = fmgr_device_provision_template.set_devprof_snmp(fmg_instance, fixture_data[0]['paramgram_used'])
    assert output['raw_response']['status']['code'] == 0
    # Test using fixture 2 #
    output = fmgr_device_provision_template.set_devprof_snmp(fmg_instance, fixture_data[1]['paramgram_used'])
    assert output['raw_response']['status']['code'] == 0
    # Test using fixture 3 #
    output = fmgr_device_provision_template.set_devprof_snmp(fmg_instance, fixture_data[2]['paramgram_used'])
    assert output['raw_response']['status']['code'] == 0


def test_set_devprof_snmp_v2c(fixture_data, mocker):
    mocker.patch("ansible.module_utils.network.fortimanager.fortimanager.FortiManagerHandler.process_request",
                 side_effect=fixture_data)
    #  Fixture sets used:###########################

    ##################################################
    # snmpv3_security_level: None
    # snmp_v2c_query_status: enable
    # ntp_type: None
    # dns_suffix: None
    # snmpv3_queries: None
    # snmpv3_trap_status: None
    # snmp_v2c_name: ansibleV2c
    # syslog_facility: syslog
    # snmp_v2c_status: enable
    # smtp_validate_cert: None
    # snmpv3_name: None
    # snmp_v2c_trap_src_ipv4: 10.7.220.41
    # syslog_port: None
    # ntp_server: None
    # admin_https_port: None
    # ntp_status: None
    # syslog_server: None
    # dns_primary_ipv4: None
    # admin_timeout: None
    # snmpv3_auth_proto: None
    # smtp_port: None
    # snmpv3_priv_pwd: None
    # smtp_server: None
    # syslog_enc_algorithm: disable
    # dns_secondary_ipv4: None
    # smtp_replyto: None
    # smtp_username: None
    # snmpv3_auth_pwd: None
    # syslog_certificate: None
    # admin_fortiguard_target: None
    # snmpv3_query_port: None
    # smtp_password: None
    # adom: ansible
    # snmpv3_notify_hosts: None
    # syslog_mode: udp
    # snmp_v2c_query_port: 162
    # snmp_v2c_trap_status: enable
    # snmp_status: enable
    # syslog_status: None
    # admin_fortianalyzer_target: None
    # ntp_auth: None
    # snmp_v2c_id: 1
    # admin_http_port: None
    # snmp_v2c_query_hosts_ipv4: 10.7.220.59 255.255.255.255, 10.7.220.0 255.255.255.0
    # ntp_sync_interval: None
    # snmpv3_source_ip: None
    # snmpv3_trap_rport: None
    # admin_gui_theme: None
    # syslog_filter: None
    # ntp_auth_pwd: None
    # provisioning_template: ansibleTest
    # snmp_v2c_trap_hosts_ipv4: 10.7.220.59 255.255.255.255, 10.7.220.60 255.255.255.255
    # provision_targets: None
    # snmp_v2c_trap_port: 161
    # snmpv3_priv_proto: None
    # admin_enable_fortiguard: None
    # admin_switch_controller: None
    # admin_language: None
    # smtp_conn_sec: None
    # mode: set
    # smtp_source_ipv4: None
    # snmpv3_status: None
    # delete_provisioning_template: None
    # ntp_v3: None
    # admin_https_redirect: None
    ##################################################

    # Test using fixture 1 #
    output = fmgr_device_provision_template.set_devprof_snmp_v2c(fmg_instance, fixture_data[0]['paramgram_used'])
    assert isinstance(output['raw_response'], dict) is True


def test_set_devprof_snmp_v3(fixture_data, mocker):
    mocker.patch("ansible.module_utils.network.fortimanager.fortimanager.FortiManagerHandler.process_request",
                 side_effect=fixture_data)
    #  Fixture sets used:###########################

    ##################################################
    # snmpv3_security_level: auth-priv
    # snmp_v2c_query_status: None
    # provision_targets: None
    # ntp_type: None
    # dns_suffix: None
    # snmpv3_queries: enable
    # snmpv3_trap_status: enable
    # snmp_v2c_name: None
    # syslog_facility: syslog
    # snmp_v2c_status: None
    # smtp_validate_cert: None
    # snmpv3_name: ansibleSNMPv3
    # snmp_v2c_id: None
    # syslog_port: None
    # ntp_server: None
    # admin_https_port: None
    # ntp_status: None
    # syslog_server: None
    # admin_switch_controller: None
    # admin_timeout: None
    # snmpv3_auth_proto: sha
    # smtp_port: None
    # snmpv3_priv_pwd: fortinet
    # smtp_server: None
    # syslog_enc_algorithm: disable
    # snmp_v2c_query_hosts_ipv4: None
    # smtp_username: None
    # mode: set
    # syslog_certificate: None
    # admin_fortiguard_target: None
    # snmpv3_query_port: 161
    # smtp_password: None
    # adom: ansible
    # snmpv3_notify_hosts: 10.7.220.59,10.7.220.60
    # syslog_mode: udp
    # snmp_v2c_query_port: None
    # snmp_v2c_trap_status: None
    # snmp_status: enable
    # syslog_status: None
    # admin_https_redirect: None
    # admin_fortianalyzer_target: None
    # snmp_v2c_trap_src_ipv4: None
    # admin_http_port: None
    # dns_secondary_ipv4: None
    # syslog_filter: None
    # snmpv3_source_ip: 0.0.0.0
    # snmpv3_trap_rport: 162
    # admin_gui_theme: None
    # ntp_sync_interval: None
    # ntp_auth_pwd: None
    # provisioning_template: ansibleTest
    # smtp_replyto: None
    # ntp_auth: None
    # snmp_v2c_trap_port: None
    # snmpv3_priv_proto: aes256
    # admin_enable_fortiguard: None
    # dns_primary_ipv4: None
    # admin_language: None
    # smtp_conn_sec: None
    # snmpv3_auth_pwd: fortinet
    # smtp_source_ipv4: None
    # snmpv3_status: enable
    # delete_provisioning_template: None
    # snmp_v2c_trap_hosts_ipv4: None
    # ntp_v3: None
    ##################################################

    # Test using fixture 1 #
    output = fmgr_device_provision_template.set_devprof_snmp_v3(fmg_instance, fixture_data[0]['paramgram_used'])
    assert output['raw_response']['status']['code'] == 0


def test_set_devprof_syslog(fixture_data, mocker):
    mocker.patch("ansible.module_utils.network.fortimanager.fortimanager.FortiManagerHandler.process_request",
                 side_effect=fixture_data)
    #  Fixture sets used:###########################

    ##################################################
    # snmpv3_security_level: None
    # snmp_v2c_query_status: None
    # provision_targets: None
    # ntp_type: None
    # dns_suffix: None
    # snmpv3_queries: None
    # snmpv3_trap_status: None
    # snmp_v2c_name: None
    # syslog_facility: kernel
    # snmp_v2c_status: None
    # smtp_validate_cert: None
    # snmpv3_name: None
    # snmp_v2c_id: None
    # syslog_port: 514
    # ntp_server: None
    # admin_https_port: None
    # ntp_status: None
    # syslog_server: 10.7.220.59
    # admin_switch_controller: None
    # admin_timeout: None
    # snmpv3_auth_proto: None
    # smtp_port: None
    # snmpv3_priv_pwd: None
    # smtp_server: None
    # syslog_enc_algorithm: disable
    # snmp_v2c_query_hosts_ipv4: None
    # smtp_username: None
    # mode: set
    # syslog_certificate: None
    # admin_fortiguard_target: None
    # snmpv3_query_port: None
    # smtp_password: None
    # adom: ansible
    # snmpv3_notify_hosts: None
    # syslog_mode: udp
    # snmp_v2c_query_port: None
    # snmp_v2c_trap_status: None
    # snmp_status: None
    # syslog_status: enable
    # snmp_v2c_trap_hosts_ipv4: None
    # admin_fortianalyzer_target: None
    # snmp_v2c_trap_src_ipv4: None
    # admin_http_port: None
    # dns_secondary_ipv4: None
    # syslog_filter: critical
    # snmpv3_source_ip: None
    # snmpv3_trap_rport: None
    # admin_gui_theme: None
    # ntp_sync_interval: None
    # ntp_auth_pwd: None
    # provisioning_template: ansibleTest
    # ntp_v3: None
    # ntp_auth: None
    # snmp_v2c_trap_port: None
    # snmpv3_priv_proto: None
    # admin_enable_fortiguard: None
    # dns_primary_ipv4: None
    # admin_language: None
    # smtp_conn_sec: None
    # snmpv3_auth_pwd: None
    # smtp_source_ipv4: None
    # snmpv3_status: None
    # delete_provisioning_template: None
    # smtp_replyto: None
    # admin_https_redirect: None
    ##################################################

    # Test using fixture 1 #
    output = fmgr_device_provision_template.set_devprof_syslog(fmg_instance, fixture_data[0]['paramgram_used'])
    assert output['raw_response']['status']['code'] == 0


def test_set_devprof_ntp(fixture_data, mocker):
    mocker.patch("ansible.module_utils.network.fortimanager.fortimanager.FortiManagerHandler.process_request",
                 side_effect=fixture_data)
    #  Fixture sets used:###########################

    ##################################################
    # snmpv3_security_level: None
    # snmp_v2c_query_status: None
    # provision_targets: None
    # ntp_type: fortiguard
    # dns_suffix: None
    # snmpv3_queries: None
    # snmpv3_trap_status: None
    # snmp_v2c_name: None
    # syslog_facility: syslog
    # snmp_v2c_status: None
    # smtp_validate_cert: None
    # snmpv3_name: None
    # snmp_v2c_id: None
    # syslog_port: None
    # ntp_server: None
    # admin_https_port: None
    # ntp_status: enable
    # syslog_server: None
    # admin_switch_controller: None
    # admin_timeout: None
    # snmpv3_auth_proto: None
    # smtp_port: None
    # snmpv3_priv_pwd: None
    # smtp_server: None
    # syslog_enc_algorithm: disable
    # snmp_v2c_query_hosts_ipv4: None
    # smtp_username: None
    # mode: set
    # syslog_certificate: None
    # admin_fortiguard_target: None
    # snmpv3_query_port: None
    # smtp_password: None
    # adom: ansible
    # snmpv3_notify_hosts: None
    # syslog_mode: udp
    # snmp_v2c_query_port: None
    # snmp_v2c_trap_status: None
    # snmp_status: None
    # syslog_status: None
    # snmp_v2c_trap_hosts_ipv4: None
    # admin_fortianalyzer_target: None
    # snmp_v2c_trap_src_ipv4: None
    # admin_http_port: None
    # dns_secondary_ipv4: None
    # syslog_filter: None
    # snmpv3_source_ip: None
    # snmpv3_trap_rport: None
    # admin_gui_theme: None
    # ntp_sync_interval: 60
    # ntp_auth_pwd: None
    # provisioning_template: ansibleTest
    # ntp_v3: None
    # ntp_auth: None
    # snmp_v2c_trap_port: None
    # snmpv3_priv_proto: None
    # admin_enable_fortiguard: None
    # dns_primary_ipv4: None
    # admin_language: None
    # smtp_conn_sec: None
    # snmpv3_auth_pwd: None
    # smtp_source_ipv4: None
    # snmpv3_status: None
    # delete_provisioning_template: None
    # smtp_replyto: None
    # admin_https_redirect: None
    ##################################################
    ##################################################
    # snmpv3_security_level: None
    # snmp_v2c_query_status: None
    # provision_targets: None
    # ntp_type: custom
    # dns_suffix: None
    # snmpv3_queries: None
    # snmpv3_trap_status: None
    # snmp_v2c_name: None
    # syslog_facility: syslog
    # snmp_v2c_status: None
    # smtp_validate_cert: None
    # snmpv3_name: None
    # snmp_v2c_id: None
    # syslog_port: None
    # ntp_server: 10.7.220.32,10.7.220.1
    # admin_https_port: None
    # ntp_status: enable
    # syslog_server: None
    # admin_switch_controller: None
    # admin_timeout: None
    # snmpv3_auth_proto: None
    # smtp_port: None
    # snmpv3_priv_pwd: None
    # smtp_server: None
    # syslog_enc_algorithm: disable
    # snmp_v2c_query_hosts_ipv4: None
    # smtp_username: None
    # mode: set
    # syslog_certificate: None
    # admin_fortiguard_target: None
    # snmpv3_query_port: None
    # smtp_password: None
    # adom: ansible
    # snmpv3_notify_hosts: None
    # syslog_mode: udp
    # snmp_v2c_query_port: None
    # snmp_v2c_trap_status: None
    # snmp_status: None
    # syslog_status: None
    # admin_https_redirect: None
    # admin_fortianalyzer_target: None
    # snmp_v2c_trap_src_ipv4: None
    # admin_http_port: None
    # dns_secondary_ipv4: None
    # syslog_filter: None
    # snmpv3_source_ip: None
    # snmpv3_trap_rport: None
    # admin_gui_theme: None
    # ntp_sync_interval: 60
    # ntp_auth_pwd: fortinet
    # provisioning_template: ansibleTest
    # smtp_replyto: None
    # ntp_auth: enable
    # snmp_v2c_trap_port: None
    # snmpv3_priv_proto: None
    # admin_enable_fortiguard: None
    # dns_primary_ipv4: None
    # admin_language: None
    # smtp_conn_sec: None
    # snmpv3_auth_pwd: None
    # smtp_source_ipv4: None
    # snmpv3_status: None
    # delete_provisioning_template: None
    # snmp_v2c_trap_hosts_ipv4: None
    # ntp_v3: None
    ##################################################

    # Test using fixture 1 #
    output = fmgr_device_provision_template.set_devprof_ntp(fmg_instance, fixture_data[0]['paramgram_used'])
    assert output['raw_response']['status']['code'] == 0
    # Test using fixture 2 #
    output = fmgr_device_provision_template.set_devprof_ntp(fmg_instance, fixture_data[1]['paramgram_used'])
    assert output['raw_response']['status']['code'] == 0


def test_set_devprof_admin(fixture_data, mocker):
    mocker.patch("ansible.module_utils.network.fortimanager.fortimanager.FortiManagerHandler.process_request",
                 side_effect=fixture_data)
    #  Fixture sets used:###########################

    ##################################################
    # snmpv3_security_level: None
    # snmp_v2c_query_status: None
    # provision_targets: None
    # ntp_type: None
    # dns_suffix: None
    # snmpv3_queries: None
    # snmpv3_trap_status: None
    # snmp_v2c_name: None
    # syslog_facility: syslog
    # snmp_v2c_status: None
    # smtp_validate_cert: None
    # snmpv3_name: None
    # snmp_v2c_id: None
    # syslog_port: None
    # ntp_server: None
    # admin_https_port: 4433
    # ntp_status: None
    # syslog_server: None
    # admin_switch_controller: enable
    # admin_timeout: 60
    # snmpv3_auth_proto: None
    # smtp_port: None
    # snmpv3_priv_pwd: None
    # smtp_server: None
    # syslog_enc_algorithm: disable
    # snmp_v2c_query_hosts_ipv4: None
    # smtp_username: None
    # mode: set
    # syslog_certificate: None
    # admin_fortiguard_target: None
    # snmpv3_query_port: None
    # smtp_password: None
    # adom: ansible
    # snmpv3_notify_hosts: None
    # syslog_mode: udp
    # snmp_v2c_query_port: None
    # snmp_v2c_trap_status: None
    # snmp_status: None
    # syslog_status: None
    # snmp_v2c_trap_hosts_ipv4: None
    # admin_fortianalyzer_target: 10.7.220.38
    # snmp_v2c_trap_src_ipv4: None
    # admin_http_port: 8080
    # dns_secondary_ipv4: None
    # syslog_filter: None
    # snmpv3_source_ip: None
    # snmpv3_trap_rport: None
    # admin_gui_theme: blue
    # ntp_sync_interval: None
    # ntp_auth_pwd: None
    # provisioning_template: ansibleTest
    # ntp_v3: None
    # ntp_auth: None
    # snmp_v2c_trap_port: None
    # snmpv3_priv_proto: None
    # admin_enable_fortiguard: this-fmg
    # dns_primary_ipv4: None
    # admin_language: english
    # smtp_conn_sec: None
    # snmpv3_auth_pwd: None
    # smtp_source_ipv4: None
    # snmpv3_status: None
    # delete_provisioning_template: None
    # smtp_replyto: None
    # admin_https_redirect: enable
    ##################################################

    # Test using fixture 1 #
    output = fmgr_device_provision_template.set_devprof_admin(fmg_instance, fixture_data[0]['paramgram_used'])
    assert output['raw_response']['status']['code'] == 0


def test_set_devprof_smtp(fixture_data, mocker):
    mocker.patch("ansible.module_utils.network.fortimanager.fortimanager.FortiManagerHandler.process_request",
                 side_effect=fixture_data)
    #  Fixture sets used:###########################

    ##################################################
    # snmpv3_security_level: None
    # snmp_v2c_query_status: None
    # provision_targets: None
    # ntp_type: None
    # dns_suffix: None
    # snmpv3_queries: None
    # snmpv3_trap_status: None
    # snmp_v2c_name: None
    # syslog_facility: syslog
    # snmp_v2c_status: None
    # smtp_validate_cert: disable
    # snmpv3_name: None
    # snmp_v2c_id: None
    # syslog_port: None
    # ntp_server: None
    # admin_https_port: None
    # ntp_status: None
    # syslog_server: None
    # admin_switch_controller: None
    # admin_timeout: None
    # snmpv3_auth_proto: None
    # smtp_port: 25
    # snmpv3_priv_pwd: None
    # smtp_server: 10.7.220.32
    # syslog_enc_algorithm: disable
    # snmp_v2c_query_hosts_ipv4: None
    # smtp_username: ansible
    # mode: set
    # syslog_certificate: None
    # admin_fortiguard_target: None
    # snmpv3_query_port: None
    # smtp_password: fortinet
    # adom: ansible
    # snmpv3_notify_hosts: None
    # syslog_mode: udp
    # snmp_v2c_query_port: None
    # snmp_v2c_trap_status: None
    # snmp_status: None
    # syslog_status: None
    # admin_https_redirect: None
    # admin_fortianalyzer_target: None
    # snmp_v2c_trap_src_ipv4: None
    # admin_http_port: None
    # dns_secondary_ipv4: None
    # syslog_filter: None
    # snmpv3_source_ip: None
    # snmpv3_trap_rport: None
    # admin_gui_theme: None
    # ntp_sync_interval: None
    # ntp_auth_pwd: None
    # provisioning_template: ansibleTest
    # smtp_replyto: ansible@do-not-reply.com
    # ntp_auth: None
    # snmp_v2c_trap_port: None
    # snmpv3_priv_proto: None
    # admin_enable_fortiguard: None
    # dns_primary_ipv4: None
    # admin_language: None
    # smtp_conn_sec: starttls
    # snmpv3_auth_pwd: None
    # smtp_source_ipv4: 0.0.0.0
    # snmpv3_status: None
    # delete_provisioning_template: None
    # snmp_v2c_trap_hosts_ipv4: None
    # ntp_v3: None
    ##################################################

    # Test using fixture 1 #
    output = fmgr_device_provision_template.set_devprof_smtp(fmg_instance, fixture_data[0]['paramgram_used'])
    assert output['raw_response']['status']['code'] == 0


def test_set_devprof_dns(fixture_data, mocker):
    mocker.patch("ansible.module_utils.network.fortimanager.fortimanager.FortiManagerHandler.process_request",
                 side_effect=fixture_data)
    #  Fixture sets used:###########################

    ##################################################
    # snmpv3_security_level: None
    # snmp_v2c_query_status: None
    # provision_targets: None
    # ntp_type: None
    # dns_suffix: ansible.local
    # snmpv3_queries: None
    # snmpv3_trap_status: None
    # snmp_v2c_name: None
    # syslog_facility: syslog
    # snmp_v2c_status: None
    # smtp_validate_cert: None
    # snmpv3_name: None
    # snmp_v2c_id: None
    # syslog_port: None
    # ntp_server: None
    # admin_https_port: None
    # ntp_status: None
    # syslog_server: None
    # admin_switch_controller: None
    # admin_timeout: None
    # snmpv3_auth_proto: None
    # smtp_port: None
    # snmpv3_priv_pwd: None
    # smtp_server: None
    # syslog_enc_algorithm: disable
    # snmp_v2c_query_hosts_ipv4: None
    # smtp_username: None
    # mode: set
    # syslog_certificate: None
    # admin_fortiguard_target: None
    # snmpv3_query_port: None
    # smtp_password: None
    # adom: ansible
    # snmpv3_notify_hosts: None
    # syslog_mode: udp
    # snmp_v2c_query_port: None
    # snmp_v2c_trap_status: None
    # snmp_status: None
    # syslog_status: None
    # snmp_v2c_trap_hosts_ipv4: None
    # admin_fortianalyzer_target: None
    # snmp_v2c_trap_src_ipv4: None
    # admin_http_port: None
    # dns_secondary_ipv4: 4.4.4.4
    # syslog_filter: None
    # snmpv3_source_ip: None
    # snmpv3_trap_rport: None
    # admin_gui_theme: None
    # ntp_sync_interval: None
    # ntp_auth_pwd: None
    # provisioning_template: ansibleTest
    # ntp_v3: None
    # ntp_auth: None
    # snmp_v2c_trap_port: None
    # snmpv3_priv_proto: None
    # admin_enable_fortiguard: None
    # dns_primary_ipv4: 8.8.8.8
    # admin_language: None
    # smtp_conn_sec: None
    # snmpv3_auth_pwd: None
    # smtp_source_ipv4: None
    # snmpv3_status: None
    # delete_provisioning_template: None
    # smtp_replyto: None
    # admin_https_redirect: None
    ##################################################

    # Test using fixture 1 #
    output = fmgr_device_provision_template.set_devprof_dns(fmg_instance, fixture_data[0]['paramgram_used'])
    assert output['raw_response']['status']['code'] == 0
