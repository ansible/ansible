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
module: fortios_extender_controller_extender
short_description: Extender controller configuration in Fortinet's FortiOS and FortiGate.
description:
    - This module is able to configure a FortiGate or FortiOS (FOS) device by allowing the
      user to set and modify extender_controller feature and extender category.
      Examples include all parameters and values need to be adjusted to datasources before usage.
      Tested with FOS v6.0.5
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
        version_added: 2.9
    state:
        description:
            - Indicates whether to create or remove the object.
              This attribute was present already in previous version in a deeper level.
              It has been moved out to this outer level.
        type: str
        required: false
        choices:
            - present
            - absent
        version_added: 2.9
    extender_controller_extender:
        description:
            - Extender controller configuration.
        default: null
        type: dict
        suboptions:
            state:
                description:
                    - B(Deprecated)
                    - Starting with Ansible 2.9 we recommend using the top-level 'state' parameter.
                    - HORIZONTALLINE
                    - Indicates whether to create or remove the object.
                type: str
                required: false
                choices:
                    - present
                    - absent
            aaa_shared_secret:
                description:
                    - AAA shared secret.
                type: str
            access_point_name:
                description:
                    - Access point name(APN).
                type: str
            admin:
                description:
                    - FortiExtender Administration (enable or disable).
                type: str
                choices:
                    - disable
                    - discovered
                    - enable
            at_dial_script:
                description:
                    - Initialization AT commands specific to the MODEM.
                type: str
            billing_start_day:
                description:
                    - Billing start day.
                type: int
            cdma_aaa_spi:
                description:
                    - CDMA AAA SPI.
                type: str
            cdma_ha_spi:
                description:
                    - CDMA HA SPI.
                type: str
            cdma_nai:
                description:
                    - NAI for CDMA MODEMS.
                type: str
            conn_status:
                description:
                    - Connection status.
                type: int
            description:
                description:
                    - Description.
                type: str
            dial_mode:
                description:
                    - Dial mode (dial-on-demand or always-connect).
                type: str
                choices:
                    - dial-on-demand
                    - always-connect
            dial_status:
                description:
                    - Dial status.
                type: int
            ext_name:
                description:
                    - FortiExtender name.
                type: str
            ha_shared_secret:
                description:
                    - HA shared secret.
                type: str
            id:
                description:
                    - FortiExtender serial number.
                required: true
                type: str
            ifname:
                description:
                    - FortiExtender interface name.
                type: str
            initiated_update:
                description:
                    - Allow/disallow network initiated updates to the MODEM.
                type: str
                choices:
                    - enable
                    - disable
            mode:
                description:
                    - FortiExtender mode.
                type: str
                choices:
                    - standalone
                    - redundant
            modem_passwd:
                description:
                    - MODEM password.
                type: str
            modem_type:
                description:
                    - MODEM type (CDMA, GSM/LTE or WIMAX).
                type: str
                choices:
                    - cdma
                    - gsm/lte
                    - wimax
            multi_mode:
                description:
                    - MODEM mode of operation(3G,LTE,etc).
                type: str
                choices:
                    - auto
                    - auto-3g
                    - force-lte
                    - force-3g
                    - force-2g
            ppp_auth_protocol:
                description:
                    - PPP authentication protocol (PAP,CHAP or auto).
                type: str
                choices:
                    - auto
                    - pap
                    - chap
            ppp_echo_request:
                description:
                    - Enable/disable PPP echo request.
                type: str
                choices:
                    - enable
                    - disable
            ppp_password:
                description:
                    - PPP password.
                type: str
            ppp_username:
                description:
                    - PPP username.
                type: str
            primary_ha:
                description:
                    - Primary HA.
                type: str
            quota_limit_mb:
                description:
                    - Monthly quota limit (MB).
                type: int
            redial:
                description:
                    - Number of redials allowed based on failed attempts.
                type: str
                choices:
                    - none
                    - 1
                    - 2
                    - 3
                    - 4
                    - 5
                    - 6
                    - 7
                    - 8
                    - 9
                    - 10
            redundant_intf:
                description:
                    - Redundant interface.
                type: str
            roaming:
                description:
                    - Enable/disable MODEM roaming.
                type: str
                choices:
                    - enable
                    - disable
            role:
                description:
                    - FortiExtender work role(Primary, Secondary, None).
                type: str
                choices:
                    - none
                    - primary
                    - secondary
            secondary_ha:
                description:
                    - Secondary HA.
                type: str
            sim_pin:
                description:
                    - SIM PIN.
                type: str
            vdom:
                description:
                    - VDOM
                type: int
            wimax_auth_protocol:
                description:
                    - WiMax authentication protocol(TLS or TTLS).
                type: str
                choices:
                    - tls
                    - ttls
            wimax_carrier:
                description:
                    - WiMax carrier.
                type: str
            wimax_realm:
                description:
                    - WiMax realm.
                type: str
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
  - name: Extender controller configuration.
    fortios_extender_controller_extender:
      host:  "{{ host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{ vdom }}"
      https: "False"
      state: "present"
      extender_controller_extender:
        aaa_shared_secret: "<your_own_value>"
        access_point_name: "<your_own_value>"
        admin: "disable"
        at_dial_script: "<your_own_value>"
        billing_start_day: "7"
        cdma_aaa_spi: "<your_own_value>"
        cdma_ha_spi: "<your_own_value>"
        cdma_nai: "<your_own_value>"
        conn_status: "11"
        description: "<your_own_value>"
        dial_mode: "dial-on-demand"
        dial_status: "14"
        ext_name: "<your_own_value>"
        ha_shared_secret: "<your_own_value>"
        id:  "17"
        ifname: "<your_own_value>"
        initiated_update: "enable"
        mode: "standalone"
        modem_passwd: "<your_own_value>"
        modem_type: "cdma"
        multi_mode: "auto"
        ppp_auth_protocol: "auto"
        ppp_echo_request: "enable"
        ppp_password: "<your_own_value>"
        ppp_username: "<your_own_value>"
        primary_ha: "<your_own_value>"
        quota_limit_mb: "29"
        redial: "none"
        redundant_intf: "<your_own_value>"
        roaming: "enable"
        role: "none"
        secondary_ha: "<your_own_value>"
        sim_pin: "<your_own_value>"
        vdom: "36"
        wimax_auth_protocol: "tls"
        wimax_carrier: "<your_own_value>"
        wimax_realm: "<your_own_value>"
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


def filter_extender_controller_extender_data(json):
    option_list = ['aaa_shared_secret', 'access_point_name', 'admin',
                   'at_dial_script', 'billing_start_day', 'cdma_aaa_spi',
                   'cdma_ha_spi', 'cdma_nai', 'conn_status',
                   'description', 'dial_mode', 'dial_status',
                   'ext_name', 'ha_shared_secret', 'id',
                   'ifname', 'initiated_update', 'mode',
                   'modem_passwd', 'modem_type', 'multi_mode',
                   'ppp_auth_protocol', 'ppp_echo_request', 'ppp_password',
                   'ppp_username', 'primary_ha', 'quota_limit_mb',
                   'redial', 'redundant_intf', 'roaming',
                   'role', 'secondary_ha', 'sim_pin',
                   'vdom', 'wimax_auth_protocol', 'wimax_carrier',
                   'wimax_realm']
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


def extender_controller_extender(data, fos):
    vdom = data['vdom']
    if 'state' in data and data['state']:
        state = data['state']
    elif 'state' in data['extender_controller_extender'] and data['extender_controller_extender']:
        state = data['extender_controller_extender']['state']
    else:
        state = True
    extender_controller_extender_data = data['extender_controller_extender']
    filtered_data = underscore_to_hyphen(filter_extender_controller_extender_data(extender_controller_extender_data))

    if state == "present":
        return fos.set('extender-controller',
                       'extender',
                       data=filtered_data,
                       vdom=vdom)

    elif state == "absent":
        return fos.delete('extender-controller',
                          'extender',
                          mkey=filtered_data['id'],
                          vdom=vdom)


def is_successful_status(status):
    return status['status'] == "success" or \
        status['http_method'] == "DELETE" and status['http_status'] == 404


def fortios_extender_controller(data, fos):

    if data['extender_controller_extender']:
        resp = extender_controller_extender(data, fos)

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
        "state": {"required": False, "type": "str",
                  "choices": ["present", "absent"]},
        "extender_controller_extender": {
            "required": False, "type": "dict", "default": None,
            "options": {
                "state": {"required": False, "type": "str",
                          "choices": ["present", "absent"]},
                "aaa_shared_secret": {"required": False, "type": "str"},
                "access_point_name": {"required": False, "type": "str"},
                "admin": {"required": False, "type": "str",
                          "choices": ["disable", "discovered", "enable"]},
                "at_dial_script": {"required": False, "type": "str"},
                "billing_start_day": {"required": False, "type": "int"},
                "cdma_aaa_spi": {"required": False, "type": "str"},
                "cdma_ha_spi": {"required": False, "type": "str"},
                "cdma_nai": {"required": False, "type": "str"},
                "conn_status": {"required": False, "type": "int"},
                "description": {"required": False, "type": "str"},
                "dial_mode": {"required": False, "type": "str",
                              "choices": ["dial-on-demand", "always-connect"]},
                "dial_status": {"required": False, "type": "int"},
                "ext_name": {"required": False, "type": "str"},
                "ha_shared_secret": {"required": False, "type": "str"},
                "id": {"required": True, "type": "str"},
                "ifname": {"required": False, "type": "str"},
                "initiated_update": {"required": False, "type": "str",
                                     "choices": ["enable", "disable"]},
                "mode": {"required": False, "type": "str",
                         "choices": ["standalone", "redundant"]},
                "modem_passwd": {"required": False, "type": "str"},
                "modem_type": {"required": False, "type": "str",
                               "choices": ["cdma", "gsm/lte", "wimax"]},
                "multi_mode": {"required": False, "type": "str",
                               "choices": ["auto", "auto-3g", "force-lte",
                                           "force-3g", "force-2g"]},
                "ppp_auth_protocol": {"required": False, "type": "str",
                                      "choices": ["auto", "pap", "chap"]},
                "ppp_echo_request": {"required": False, "type": "str",
                                     "choices": ["enable", "disable"]},
                "ppp_password": {"required": False, "type": "str"},
                "ppp_username": {"required": False, "type": "str"},
                "primary_ha": {"required": False, "type": "str"},
                "quota_limit_mb": {"required": False, "type": "int"},
                "redial": {"required": False, "type": "str",
                           "choices": ["none", "1", "2",
                                       "3", "4", "5",
                                       "6", "7", "8",
                                       "9", "10"]},
                "redundant_intf": {"required": False, "type": "str"},
                "roaming": {"required": False, "type": "str",
                            "choices": ["enable", "disable"]},
                "role": {"required": False, "type": "str",
                         "choices": ["none", "primary", "secondary"]},
                "secondary_ha": {"required": False, "type": "str"},
                "sim_pin": {"required": False, "type": "str"},
                "vdom": {"required": False, "type": "int"},
                "wimax_auth_protocol": {"required": False, "type": "str",
                                        "choices": ["tls", "ttls"]},
                "wimax_carrier": {"required": False, "type": "str"},
                "wimax_realm": {"required": False, "type": "str"}

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

            is_error, has_changed, result = fortios_extender_controller(module.params, fos)
        else:
            module.fail_json(**FAIL_SOCKET_MSG)
    else:
        try:
            from fortiosapi import FortiOSAPI
        except ImportError:
            module.fail_json(msg="fortiosapi module is required")

        fos = FortiOSAPI()

        login(module.params, fos)
        is_error, has_changed, result = fortios_extender_controller(module.params, fos)
        fos.logout()

    if not is_error:
        module.exit_json(changed=has_changed, meta=result)
    else:
        module.fail_json(msg="Error in repo", meta=result)


if __name__ == '__main__':
    main()
