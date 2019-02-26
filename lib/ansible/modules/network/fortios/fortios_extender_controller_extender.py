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
module: fortios_extender_controller_extender
short_description: Extender controller configuration in Fortinet's FortiOS and FortiGate.
description:
    - This module is able to configure a FortiGate or FortiOS by
      allowing the user to configure extender_controller feature and extender category.
      Examples includes all options and need to be adjusted to datasources before usage.
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
        default: false
    extender_controller_extender:
        description:
            - Extender controller configuration.
        default: null
        suboptions:
            state:
                description:
                    - Indicates whether to create or remove the object
                choices:
                    - present
                    - absent
            aaa-shared-secret:
                description:
                    - AAA shared secret.
            access-point-name:
                description:
                    - Access point name(APN).
            admin:
                description:
                    - FortiExtender Administration (enable or disable).
                choices:
                    - disable
                    - discovered
                    - enable
            at-dial-script:
                description:
                    - Initialization AT commands specific to the MODEM.
            billing-start-day:
                description:
                    - Billing start day.
            cdma-aaa-spi:
                description:
                    - CDMA AAA SPI.
            cdma-ha-spi:
                description:
                    - CDMA HA SPI.
            cdma-nai:
                description:
                    - NAI for CDMA MODEMS.
            conn-status:
                description:
                    - Connection status.
            description:
                description:
                    - Description.
            dial-mode:
                description:
                    - Dial mode (dial-on-demand or always-connect).
                choices:
                    - dial-on-demand
                    - always-connect
            dial-status:
                description:
                    - Dial status.
            ext-name:
                description:
                    - FortiExtender name.
            ha-shared-secret:
                description:
                    - HA shared secret.
            id:
                description:
                    - FortiExtender serial number.
                required: true
            ifname:
                description:
                    - FortiExtender interface name.
            initiated-update:
                description:
                    - Allow/disallow network initiated updates to the MODEM.
                choices:
                    - enable
                    - disable
            mode:
                description:
                    - FortiExtender mode.
                choices:
                    - standalone
                    - redundant
            modem-passwd:
                description:
                    - MODEM password.
            modem-type:
                description:
                    - MODEM type (CDMA, GSM/LTE or WIMAX).
                choices:
                    - cdma
                    - gsm/lte
                    - wimax
            multi-mode:
                description:
                    - MODEM mode of operation(3G,LTE,etc).
                choices:
                    - auto
                    - auto-3g
                    - force-lte
                    - force-3g
                    - force-2g
            ppp-auth-protocol:
                description:
                    - PPP authentication protocol (PAP,CHAP or auto).
                choices:
                    - auto
                    - pap
                    - chap
            ppp-echo-request:
                description:
                    - Enable/disable PPP echo request.
                choices:
                    - enable
                    - disable
            ppp-password:
                description:
                    - PPP password.
            ppp-username:
                description:
                    - PPP username.
            primary-ha:
                description:
                    - Primary HA.
            quota-limit-mb:
                description:
                    - Monthly quota limit (MB).
            redial:
                description:
                    - Number of redials allowed based on failed attempts.
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
            redundant-intf:
                description:
                    - Redundant interface.
            roaming:
                description:
                    - Enable/disable MODEM roaming.
                choices:
                    - enable
                    - disable
            role:
                description:
                    - FortiExtender work role(Primary, Secondary, None).
                choices:
                    - none
                    - primary
                    - secondary
            secondary-ha:
                description:
                    - Secondary HA.
            sim-pin:
                description:
                    - SIM PIN.
            vdom:
                description:
                    - VDOM
            wimax-auth-protocol:
                description:
                    - WiMax authentication protocol(TLS or TTLS).
                choices:
                    - tls
                    - ttls
            wimax-carrier:
                description:
                    - WiMax carrier.
            wimax-realm:
                description:
                    - WiMax realm.
'''

EXAMPLES = '''
- hosts: localhost
  vars:
   host: "192.168.122.40"
   username: "admin"
   password: ""
   vdom: "root"
  tasks:
  - name: Extender controller configuration.
    fortios_extender_controller_extender:
      host:  "{{ host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{ vdom }}"
      extender_controller_extender:
        state: "present"
        aaa-shared-secret: "<your_own_value>"
        access-point-name: "<your_own_value>"
        admin: "disable"
        at-dial-script: "<your_own_value>"
        billing-start-day: "7"
        cdma-aaa-spi: "<your_own_value>"
        cdma-ha-spi: "<your_own_value>"
        cdma-nai: "<your_own_value>"
        conn-status: "11"
        description: "<your_own_value>"
        dial-mode: "dial-on-demand"
        dial-status: "14"
        ext-name: "<your_own_value>"
        ha-shared-secret: "<your_own_value>"
        id:  "17"
        ifname: "<your_own_value>"
        initiated-update: "enable"
        mode: "standalone"
        modem-passwd: "<your_own_value>"
        modem-type: "cdma"
        multi-mode: "auto"
        ppp-auth-protocol: "auto"
        ppp-echo-request: "enable"
        ppp-password: "<your_own_value>"
        ppp-username: "<your_own_value>"
        primary-ha: "<your_own_value>"
        quota-limit-mb: "29"
        redial: "none"
        redundant-intf: "<your_own_value>"
        roaming: "enable"
        role: "none"
        secondary-ha: "<your_own_value>"
        sim-pin: "<your_own_value>"
        vdom: "36"
        wimax-auth-protocol: "tls"
        wimax-carrier: "<your_own_value>"
        wimax-realm: "<your_own_value>"
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


def filter_extender_controller_extender_data(json):
    option_list = ['aaa-shared-secret', 'access-point-name', 'admin',
                   'at-dial-script', 'billing-start-day', 'cdma-aaa-spi',
                   'cdma-ha-spi', 'cdma-nai', 'conn-status',
                   'description', 'dial-mode', 'dial-status',
                   'ext-name', 'ha-shared-secret', 'id',
                   'ifname', 'initiated-update', 'mode',
                   'modem-passwd', 'modem-type', 'multi-mode',
                   'ppp-auth-protocol', 'ppp-echo-request', 'ppp-password',
                   'ppp-username', 'primary-ha', 'quota-limit-mb',
                   'redial', 'redundant-intf', 'roaming',
                   'role', 'secondary-ha', 'sim-pin',
                   'vdom', 'wimax-auth-protocol', 'wimax-carrier',
                   'wimax-realm']
    dictionary = {}

    for attribute in option_list:
        if attribute in json and json[attribute] is not None:
            dictionary[attribute] = json[attribute]

    return dictionary


def extender_controller_extender(data, fos):
    vdom = data['vdom']
    extender_controller_extender_data = data['extender_controller_extender']
    filtered_data = filter_extender_controller_extender_data(extender_controller_extender_data)
    if extender_controller_extender_data['state'] == "present":
        return fos.set('extender-controller',
                       'extender',
                       data=filtered_data,
                       vdom=vdom)

    elif extender_controller_extender_data['state'] == "absent":
        return fos.delete('extender-controller',
                          'extender',
                          mkey=filtered_data['id'],
                          vdom=vdom)


def fortios_extender_controller(data, fos):
    login(data)

    methodlist = ['extender_controller_extender']
    for method in methodlist:
        if data[method]:
            resp = eval(method)(data, fos)
            break

    fos.logout()
    return not resp['status'] == "success", resp['status'] == "success", resp


def main():
    fields = {
        "host": {"required": True, "type": "str"},
        "username": {"required": True, "type": "str"},
        "password": {"required": False, "type": "str", "no_log": True},
        "vdom": {"required": False, "type": "str", "default": "root"},
        "https": {"required": False, "type": "bool", "default": "False"},
        "extender_controller_extender": {
            "required": False, "type": "dict",
            "options": {
                "state": {"required": True, "type": "str",
                          "choices": ["present", "absent"]},
                "aaa-shared-secret": {"required": False, "type": "str"},
                "access-point-name": {"required": False, "type": "str"},
                "admin": {"required": False, "type": "str",
                          "choices": ["disable", "discovered", "enable"]},
                "at-dial-script": {"required": False, "type": "str"},
                "billing-start-day": {"required": False, "type": "int"},
                "cdma-aaa-spi": {"required": False, "type": "str"},
                "cdma-ha-spi": {"required": False, "type": "str"},
                "cdma-nai": {"required": False, "type": "str"},
                "conn-status": {"required": False, "type": "int"},
                "description": {"required": False, "type": "str"},
                "dial-mode": {"required": False, "type": "str",
                              "choices": ["dial-on-demand", "always-connect"]},
                "dial-status": {"required": False, "type": "int"},
                "ext-name": {"required": False, "type": "str"},
                "ha-shared-secret": {"required": False, "type": "str"},
                "id": {"required": True, "type": "str"},
                "ifname": {"required": False, "type": "str"},
                "initiated-update": {"required": False, "type": "str",
                                     "choices": ["enable", "disable"]},
                "mode": {"required": False, "type": "str",
                         "choices": ["standalone", "redundant"]},
                "modem-passwd": {"required": False, "type": "str"},
                "modem-type": {"required": False, "type": "str",
                               "choices": ["cdma", "gsm/lte", "wimax"]},
                "multi-mode": {"required": False, "type": "str",
                               "choices": ["auto", "auto-3g", "force-lte",
                                           "force-3g", "force-2g"]},
                "ppp-auth-protocol": {"required": False, "type": "str",
                                      "choices": ["auto", "pap", "chap"]},
                "ppp-echo-request": {"required": False, "type": "str",
                                     "choices": ["enable", "disable"]},
                "ppp-password": {"required": False, "type": "str"},
                "ppp-username": {"required": False, "type": "str"},
                "primary-ha": {"required": False, "type": "str"},
                "quota-limit-mb": {"required": False, "type": "int"},
                "redial": {"required": False, "type": "str",
                           "choices": ["none", "1", "2",
                                       "3", "4", "5",
                                       "6", "7", "8",
                                       "9", "10"]},
                "redundant-intf": {"required": False, "type": "str"},
                "roaming": {"required": False, "type": "str",
                            "choices": ["enable", "disable"]},
                "role": {"required": False, "type": "str",
                         "choices": ["none", "primary", "secondary"]},
                "secondary-ha": {"required": False, "type": "str"},
                "sim-pin": {"required": False, "type": "str"},
                "vdom": {"required": False, "type": "int"},
                "wimax-auth-protocol": {"required": False, "type": "str",
                                        "choices": ["tls", "ttls"]},
                "wimax-carrier": {"required": False, "type": "str"},
                "wimax-realm": {"required": False, "type": "str"}

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

    is_error, has_changed, result = fortios_extender_controller(module.params, fos)

    if not is_error:
        module.exit_json(changed=has_changed, meta=result)
    else:
        module.fail_json(msg="Error in repo", meta=result)


if __name__ == '__main__':
    main()
