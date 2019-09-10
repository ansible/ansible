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
module: fortios_alertemail_setting
short_description: Configure alert email settings in Fortinet's FortiOS and FortiGate.
description:
    - This module is able to configure a FortiGate or FortiOS (FOS) device by allowing the
      user to set and modify alertemail feature and setting category.
      Examples include all parameters and values need to be adjusted to datasources before usage.
      Tested with FOS v6.0.5
version_added: "2.9"
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
            - FortiOS or FortiGate IP address.
        type: str
        required: false
    username:
        description:
            - FortiOS or FortiGate username.
        type: str
        required: false
    password:
        description:
            - FortiOS or FortiGate password.
        type: str
        default: ""
    vdom:
        description:
            - Virtual domain, among those defined previously. A vdom is a
              virtual instance of the FortiGate that can be configured and
              used as a different unit.
        type: str
        default: root
    https:
        description:
            - Indicates if the requests towards FortiGate must use HTTPS protocol.
        type: bool
        default: true
    ssl_verify:
        description:
            - Ensures FortiGate certificate must be verified by a proper CA.
        type: bool
        default: true
    alertemail_setting:
        description:
            - Configure alert email settings.
        default: null
        type: dict
        suboptions:
            admin_login_logs:
                description:
                    - Enable/disable administrator login/logout logs in alert email.
                type: str
                choices:
                    - enable
                    - disable
            alert_interval:
                description:
                    - Alert alert interval in minutes.
                type: int
            amc_interface_bypass_mode:
                description:
                    - Enable/disable Fortinet Advanced Mezzanine Card (AMC) interface bypass mode logs in alert email.
                type: str
                choices:
                    - enable
                    - disable
            antivirus_logs:
                description:
                    - Enable/disable antivirus logs in alert email.
                type: str
                choices:
                    - enable
                    - disable
            configuration_changes_logs:
                description:
                    - Enable/disable configuration change logs in alert email.
                type: str
                choices:
                    - enable
                    - disable
            critical_interval:
                description:
                    - Critical alert interval in minutes.
                type: int
            debug_interval:
                description:
                    - Debug alert interval in minutes.
                type: int
            email_interval:
                description:
                    - Interval between sending alert emails (1 - 99999 min).
                type: int
            emergency_interval:
                description:
                    - Emergency alert interval in minutes.
                type: int
            error_interval:
                description:
                    - Error alert interval in minutes.
                type: int
            FDS_license_expiring_days:
                description:
                    - Number of days to send alert email prior to FortiGuard license expiration (1 - 100 days).
                type: int
            FDS_license_expiring_warning:
                description:
                    - Enable/disable FortiGuard license expiration warnings in alert email.
                type: str
                choices:
                    - enable
                    - disable
            FDS_update_logs:
                description:
                    - Enable/disable FortiGuard update logs in alert email.
                type: str
                choices:
                    - enable
                    - disable
            filter_mode:
                description:
                    - How to filter log messages that are sent to alert emails.
                type: str
                choices:
                    - category
                    - threshold
            FIPS_CC_errors:
                description:
                    - Enable/disable FIPS and Common Criteria error logs in alert email.
                type: str
                choices:
                    - enable
                    - disable
            firewall_authentication_failure_logs:
                description:
                    - Enable/disable firewall authentication failure logs in alert email.
                type: str
                choices:
                    - enable
                    - disable
            fortiguard_log_quota_warning:
                description:
                    - Enable/disable FortiCloud log quota warnings in alert email.
                type: str
                choices:
                    - enable
                    - disable
            FSSO_disconnect_logs:
                description:
                    - Enable/disable logging of FSSO collector agent disconnect.
                type: str
                choices:
                    - enable
                    - disable
            HA_logs:
                description:
                    - Enable/disable HA logs in alert email.
                type: str
                choices:
                    - enable
                    - disable
            information_interval:
                description:
                    - Information alert interval in minutes.
                type: int
            IPS_logs:
                description:
                    - Enable/disable IPS logs in alert email.
                type: str
                choices:
                    - enable
                    - disable
            IPsec_errors_logs:
                description:
                    - Enable/disable IPsec error logs in alert email.
                type: str
                choices:
                    - enable
                    - disable
            local_disk_usage:
                description:
                    - Disk usage percentage at which to send alert email (1 - 99 percent).
                type: int
            log_disk_usage_warning:
                description:
                    - Enable/disable disk usage warnings in alert email.
                type: str
                choices:
                    - enable
                    - disable
            mailto1:
                description:
                    - Email address to send alert email to (usually a system administrator) (max. 64 characters).
                type: str
            mailto2:
                description:
                    - Optional second email address to send alert email to (max. 64 characters).
                type: str
            mailto3:
                description:
                    - Optional third email address to send alert email to (max. 64 characters).
                type: str
            notification_interval:
                description:
                    - Notification alert interval in minutes.
                type: int
            PPP_errors_logs:
                description:
                    - Enable/disable PPP error logs in alert email.
                type: str
                choices:
                    - enable
                    - disable
            severity:
                description:
                    - Lowest severity level to log.
                type: str
                choices:
                    - emergency
                    - alert
                    - critical
                    - error
                    - warning
                    - notification
                    - information
                    - debug
            ssh_logs:
                description:
                    - Enable/disable SSH logs in alert email.
                type: str
                choices:
                    - enable
                    - disable
            sslvpn_authentication_errors_logs:
                description:
                    - Enable/disable SSL-VPN authentication error logs in alert email.
                type: str
                choices:
                    - enable
                    - disable
            username:
                description:
                    - "Name that appears in the From: field of alert emails (max. 36 characters)."
                type: str
            violation_traffic_logs:
                description:
                    - Enable/disable violation traffic logs in alert email.
                type: str
                choices:
                    - enable
                    - disable
            warning_interval:
                description:
                    - Warning alert interval in minutes.
                type: int
            webfilter_logs:
                description:
                    - Enable/disable web filter logs in alert email.
                type: str
                choices:
                    - enable
                    - disable
'''

EXAMPLES = '''
- hosts: localhost
  vars:
   host: "192.168.122.40"
   username: "admin"
   password: ""
   vdom: "root"
   ssl_verify: "False"
  tasks:
  - name: Configure alert email settings.
    fortios_alertemail_setting:
      host:  "{{ host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{ vdom }}"
      https: "False"
      alertemail_setting:
        admin_login_logs: "enable"
        alert_interval: "4"
        amc_interface_bypass_mode: "enable"
        antivirus_logs: "enable"
        configuration_changes_logs: "enable"
        critical_interval: "8"
        debug_interval: "9"
        email_interval: "10"
        emergency_interval: "11"
        error_interval: "12"
        FDS_license_expiring_days: "13"
        FDS_license_expiring_warning: "enable"
        FDS_update_logs: "enable"
        filter_mode: "category"
        FIPS_CC_errors: "enable"
        firewall_authentication_failure_logs: "enable"
        fortiguard_log_quota_warning: "enable"
        FSSO_disconnect_logs: "enable"
        HA_logs: "enable"
        information_interval: "22"
        IPS_logs: "enable"
        IPsec_errors_logs: "enable"
        local_disk_usage: "25"
        log_disk_usage_warning: "enable"
        mailto1: "<your_own_value>"
        mailto2: "<your_own_value>"
        mailto3: "<your_own_value>"
        notification_interval: "30"
        PPP_errors_logs: "enable"
        severity: "emergency"
        ssh_logs: "enable"
        sslvpn_authentication_errors_logs: "enable"
        username: "<your_own_value>"
        violation_traffic_logs: "enable"
        warning_interval: "37"
        webfilter_logs: "enable"
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
from ansible.module_utils.connection import Connection
from ansible.module_utils.network.fortios.fortios import FortiOSHandler
from ansible.module_utils.network.fortimanager.common import FAIL_SOCKET_MSG


def login(data, fos):
    host = data['host']
    username = data['username']
    password = data['password']
    ssl_verify = data['ssl_verify']

    fos.debug('on')
    if 'https' in data and not data['https']:
        fos.https('off')
    else:
        fos.https('on')

    fos.login(host, username, password, verify=ssl_verify)


def filter_alertemail_setting_data(json):
    option_list = ['admin_login_logs', 'alert_interval', 'amc_interface_bypass_mode',
                   'antivirus_logs', 'configuration_changes_logs', 'critical_interval',
                   'debug_interval', 'email_interval', 'emergency_interval',
                   'error_interval', 'FDS_license_expiring_days', 'FDS_license_expiring_warning',
                   'FDS_update_logs', 'filter_mode', 'FIPS_CC_errors',
                   'firewall_authentication_failure_logs', 'fortiguard_log_quota_warning', 'FSSO_disconnect_logs',
                   'HA_logs', 'information_interval', 'IPS_logs',
                   'IPsec_errors_logs', 'local_disk_usage', 'log_disk_usage_warning',
                   'mailto1', 'mailto2', 'mailto3',
                   'notification_interval', 'PPP_errors_logs', 'severity',
                   'ssh_logs', 'sslvpn_authentication_errors_logs', 'username',
                   'violation_traffic_logs', 'warning_interval', 'webfilter_logs']
    dictionary = {}

    for attribute in option_list:
        if attribute in json and json[attribute] is not None:
            dictionary[attribute] = json[attribute]

    return dictionary


def underscore_to_hyphen(data):
    if isinstance(data, list):
        for elem in data:
            elem = underscore_to_hyphen(elem)
    elif isinstance(data, dict):
        new_data = {}
        for k, v in data.items():
            new_data[k.replace('_', '-')] = underscore_to_hyphen(v)
        data = new_data

    return data


def alertemail_setting(data, fos):
    vdom = data['vdom']
    alertemail_setting_data = data['alertemail_setting']
    filtered_data = underscore_to_hyphen(filter_alertemail_setting_data(alertemail_setting_data))

    return fos.set('alertemail',
                   'setting',
                   data=filtered_data,
                   vdom=vdom)


def is_successful_status(status):
    return status['status'] == "success" or \
        status['http_method'] == "DELETE" and status['http_status'] == 404


def fortios_alertemail(data, fos):

    if data['alertemail_setting']:
        resp = alertemail_setting(data, fos)

    return not is_successful_status(resp), \
        resp['status'] == "success", \
        resp


def main():
    fields = {
        "host": {"required": False, "type": "str"},
        "username": {"required": False, "type": "str"},
        "password": {"required": False, "type": "str", "default": "", "no_log": True},
        "vdom": {"required": False, "type": "str", "default": "root"},
        "https": {"required": False, "type": "bool", "default": True},
        "ssl_verify": {"required": False, "type": "bool", "default": True},
        "alertemail_setting": {
            "required": False, "type": "dict", "default": None,
            "options": {
                "admin_login_logs": {"required": False, "type": "str",
                                     "choices": ["enable", "disable"]},
                "alert_interval": {"required": False, "type": "int"},
                "amc_interface_bypass_mode": {"required": False, "type": "str",
                                              "choices": ["enable", "disable"]},
                "antivirus_logs": {"required": False, "type": "str",
                                   "choices": ["enable", "disable"]},
                "configuration_changes_logs": {"required": False, "type": "str",
                                               "choices": ["enable", "disable"]},
                "critical_interval": {"required": False, "type": "int"},
                "debug_interval": {"required": False, "type": "int"},
                "email_interval": {"required": False, "type": "int"},
                "emergency_interval": {"required": False, "type": "int"},
                "error_interval": {"required": False, "type": "int"},
                "FDS_license_expiring_days": {"required": False, "type": "int"},
                "FDS_license_expiring_warning": {"required": False, "type": "str",
                                                 "choices": ["enable", "disable"]},
                "FDS_update_logs": {"required": False, "type": "str",
                                    "choices": ["enable", "disable"]},
                "filter_mode": {"required": False, "type": "str",
                                "choices": ["category", "threshold"]},
                "FIPS_CC_errors": {"required": False, "type": "str",
                                   "choices": ["enable", "disable"]},
                "firewall_authentication_failure_logs": {"required": False, "type": "str",
                                                         "choices": ["enable", "disable"]},
                "fortiguard_log_quota_warning": {"required": False, "type": "str",
                                                 "choices": ["enable", "disable"]},
                "FSSO_disconnect_logs": {"required": False, "type": "str",
                                         "choices": ["enable", "disable"]},
                "HA_logs": {"required": False, "type": "str",
                            "choices": ["enable", "disable"]},
                "information_interval": {"required": False, "type": "int"},
                "IPS_logs": {"required": False, "type": "str",
                             "choices": ["enable", "disable"]},
                "IPsec_errors_logs": {"required": False, "type": "str",
                                      "choices": ["enable", "disable"]},
                "local_disk_usage": {"required": False, "type": "int"},
                "log_disk_usage_warning": {"required": False, "type": "str",
                                           "choices": ["enable", "disable"]},
                "mailto1": {"required": False, "type": "str"},
                "mailto2": {"required": False, "type": "str"},
                "mailto3": {"required": False, "type": "str"},
                "notification_interval": {"required": False, "type": "int"},
                "PPP_errors_logs": {"required": False, "type": "str",
                                    "choices": ["enable", "disable"]},
                "severity": {"required": False, "type": "str",
                             "choices": ["emergency", "alert", "critical",
                                         "error", "warning", "notification",
                                         "information", "debug"]},
                "ssh_logs": {"required": False, "type": "str",
                             "choices": ["enable", "disable"]},
                "sslvpn_authentication_errors_logs": {"required": False, "type": "str",
                                                      "choices": ["enable", "disable"]},
                "username": {"required": False, "type": "str"},
                "violation_traffic_logs": {"required": False, "type": "str",
                                           "choices": ["enable", "disable"]},
                "warning_interval": {"required": False, "type": "int"},
                "webfilter_logs": {"required": False, "type": "str",
                                   "choices": ["enable", "disable"]}

            }
        }
    }

    module = AnsibleModule(argument_spec=fields,
                           supports_check_mode=False)

    # legacy_mode refers to using fortiosapi instead of HTTPAPI
    legacy_mode = 'host' in module.params and module.params['host'] is not None and \
                  'username' in module.params and module.params['username'] is not None and \
                  'password' in module.params and module.params['password'] is not None

    if not legacy_mode:
        if module._socket_path:
            connection = Connection(module._socket_path)
            fos = FortiOSHandler(connection)

            is_error, has_changed, result = fortios_alertemail(module.params, fos)
        else:
            module.fail_json(**FAIL_SOCKET_MSG)
    else:
        try:
            from fortiosapi import FortiOSAPI
        except ImportError:
            module.fail_json(msg="fortiosapi module is required")

        fos = FortiOSAPI()

        login(module.params, fos)
        is_error, has_changed, result = fortios_alertemail(module.params, fos)
        fos.logout()

    if not is_error:
        module.exit_json(changed=has_changed, meta=result)
    else:
        module.fail_json(msg="Error in repo", meta=result)


if __name__ == '__main__':
    main()
