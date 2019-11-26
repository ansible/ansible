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
module: fortios_wireless_controller_hotspot20_hs_profile
short_description: Configure hotspot profile in Fortinet's FortiOS and FortiGate.
description:
    - This module is able to configure a FortiGate or FortiOS (FOS) device by allowing the
      user to set and modify wireless_controller_hotspot20 feature and hs_profile category.
      Examples include all parameters and values need to be adjusted to datasources before usage.
      Tested with FOS v6.0.4
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
    state:
        description:
            - Indicates whether to create or remove the object.
        type: str
        required: true
        choices:
            - present
            - absent
    wireless_controller_hotspot20_hs_profile:
        description:
            - Configure hotspot profile.
        default: null
        type: dict
        suboptions:
            access_network_asra:
                description:
                    - Enable/disable additional step required for access (ASRA).
                type: str
                choices:
                    - enable
                    - disable
            access_network_esr:
                description:
                    - Enable/disable emergency services reachable (ESR).
                type: str
                choices:
                    - enable
                    - disable
            access_network_internet:
                description:
                    - Enable/disable connectivity to the Internet.
                type: str
                choices:
                    - enable
                    - disable
            access_network_type:
                description:
                    - Access network type.
                type: str
                choices:
                    - private-network
                    - private-network-with-guest-access
                    - chargeable-public-network
                    - free-public-network
                    - personal-device-network
                    - emergency-services-only-network
                    - test-or-experimental
                    - wildcard
            access_network_uesa:
                description:
                    - Enable/disable unauthenticated emergency service accessible (UESA).
                type: str
                choices:
                    - enable
                    - disable
            anqp_domain_id:
                description:
                    - ANQP Domain ID (0-65535).
                type: int
            bss_transition:
                description:
                    - Enable/disable basic service set (BSS) transition Support.
                type: str
                choices:
                    - enable
                    - disable
            conn_cap:
                description:
                    - Connection capability name. Source wireless-controller.hotspot20.h2qp-conn-capability.name.
                type: str
            deauth_request_timeout:
                description:
                    - Deauthentication request timeout (in seconds).
                type: int
            dgaf:
                description:
                    - Enable/disable downstream group-addressed forwarding (DGAF).
                type: str
                choices:
                    - enable
                    - disable
            domain_name:
                description:
                    - Domain name.
                type: str
            gas_comeback_delay:
                description:
                    - GAS comeback delay (0 or 100 - 4000 milliseconds).
                type: int
            gas_fragmentation_limit:
                description:
                    - GAS fragmentation limit (512 - 4096).
                type: int
            hessid:
                description:
                    - Homogeneous extended service set identifier (HESSID).
                type: str
            ip_addr_type:
                description:
                    - IP address type name. Source wireless-controller.hotspot20.anqp-ip-address-type.name.
                type: str
            l2tif:
                description:
                    - Enable/disable Layer 2 traffic inspection and filtering.
                type: str
                choices:
                    - enable
                    - disable
            nai_realm:
                description:
                    - NAI realm list name. Source wireless-controller.hotspot20.anqp-nai-realm.name.
                type: str
            name:
                description:
                    - Hotspot profile name.
                required: true
                type: str
            network_auth:
                description:
                    - Network authentication name. Source wireless-controller.hotspot20.anqp-network-auth-type.name.
                type: str
            oper_friendly_name:
                description:
                    - Operator friendly name. Source wireless-controller.hotspot20.h2qp-operator-name.name.
                type: str
            osu_provider:
                description:
                    - Manually selected list of OSU provider(s).
                type: list
                suboptions:
                    name:
                        description:
                            - OSU provider name. Source wireless-controller.hotspot20.h2qp-osu-provider.name.
                        required: true
                        type: str
            osu_ssid:
                description:
                    - Online sign up (OSU) SSID.
                type: str
            pame_bi:
                description:
                    - Enable/disable Pre-Association Message Exchange BSSID Independent (PAME-BI).
                type: str
                choices:
                    - disable
                    - enable
            proxy_arp:
                description:
                    - Enable/disable Proxy ARP.
                type: str
                choices:
                    - enable
                    - disable
            qos_map:
                description:
                    - QoS MAP set ID. Source wireless-controller.hotspot20.qos-map.name.
                type: str
            roaming_consortium:
                description:
                    - Roaming consortium list name. Source wireless-controller.hotspot20.anqp-roaming-consortium.name.
                type: str
            venue_group:
                description:
                    - Venue group.
                type: str
                choices:
                    - unspecified
                    - assembly
                    - business
                    - educational
                    - factory
                    - institutional
                    - mercantile
                    - residential
                    - storage
                    - utility
                    - vehicular
                    - outdoor
            venue_name:
                description:
                    - Venue name. Source wireless-controller.hotspot20.anqp-venue-name.name.
                type: str
            venue_type:
                description:
                    - Venue type.
                type: str
                choices:
                    - unspecified
                    - arena
                    - stadium
                    - passenger-terminal
                    - amphitheater
                    - amusement-park
                    - place-of-worship
                    - convention-center
                    - library
                    - museum
                    - restaurant
                    - theater
                    - bar
                    - coffee-shop
                    - zoo-or-aquarium
                    - emergency-center
                    - doctor-office
                    - bank
                    - fire-station
                    - police-station
                    - post-office
                    - professional-office
                    - research-facility
                    - attorney-office
                    - primary-school
                    - secondary-school
                    - university-or-college
                    - factory
                    - hospital
                    - long-term-care-facility
                    - rehab-center
                    - group-home
                    - prison-or-jail
                    - retail-store
                    - grocery-market
                    - auto-service-station
                    - shopping-mall
                    - gas-station
                    - private
                    - hotel-or-motel
                    - dormitory
                    - boarding-house
                    - automobile
                    - airplane
                    - bus
                    - ferry
                    - ship-or-boat
                    - train
                    - motor-bike
                    - muni-mesh-network
                    - city-park
                    - rest-area
                    - traffic-control
                    - bus-stop
                    - kiosk
            wan_metrics:
                description:
                    - WAN metric name. Source wireless-controller.hotspot20.h2qp-wan-metric.name.
                type: str
            wnm_sleep_mode:
                description:
                    - Enable/disable wireless network management (WNM) sleep mode.
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
  - name: Configure hotspot profile.
    fortios_wireless_controller_hotspot20_hs_profile:
      host:  "{{ host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{ vdom }}"
      https: "False"
      state: "present"
      wireless_controller_hotspot20_hs_profile:
        access_network_asra: "enable"
        access_network_esr: "enable"
        access_network_internet: "enable"
        access_network_type: "private-network"
        access_network_uesa: "enable"
        anqp_domain_id: "9"
        bss_transition: "enable"
        conn_cap: "<your_own_value> (source wireless-controller.hotspot20.h2qp-conn-capability.name)"
        deauth_request_timeout: "12"
        dgaf: "enable"
        domain_name: "<your_own_value>"
        gas_comeback_delay: "15"
        gas_fragmentation_limit: "16"
        hessid: "<your_own_value>"
        ip_addr_type: "<your_own_value> (source wireless-controller.hotspot20.anqp-ip-address-type.name)"
        l2tif: "enable"
        nai_realm: "<your_own_value> (source wireless-controller.hotspot20.anqp-nai-realm.name)"
        name: "default_name_21"
        network_auth: "<your_own_value> (source wireless-controller.hotspot20.anqp-network-auth-type.name)"
        oper_friendly_name: "<your_own_value> (source wireless-controller.hotspot20.h2qp-operator-name.name)"
        osu_provider:
         -
            name: "default_name_25 (source wireless-controller.hotspot20.h2qp-osu-provider.name)"
        osu_ssid: "<your_own_value>"
        pame_bi: "disable"
        proxy_arp: "enable"
        qos_map: "<your_own_value> (source wireless-controller.hotspot20.qos-map.name)"
        roaming_consortium: "<your_own_value> (source wireless-controller.hotspot20.anqp-roaming-consortium.name)"
        venue_group: "unspecified"
        venue_name: "<your_own_value> (source wireless-controller.hotspot20.anqp-venue-name.name)"
        venue_type: "unspecified"
        wan_metrics: "<your_own_value> (source wireless-controller.hotspot20.h2qp-wan-metric.name)"
        wnm_sleep_mode: "enable"
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


def filter_wireless_controller_hotspot20_hs_profile_data(json):
    option_list = ['access_network_asra', 'access_network_esr',
                   'access_network_internet', 'access_network_type', 'access_network_uesa',
                   'anqp_domain_id', 'bss_transition', 'conn_cap',
                   'deauth_request_timeout', 'dgaf', 'domain_name',
                   'gas_comeback_delay', 'gas_fragmentation_limit', 'hessid',
                   'ip_addr_type', 'l2tif', 'nai_realm',
                   'name', 'network_auth', 'oper_friendly_name',
                   'osu_provider', 'osu_ssid', 'pame_bi',
                   'proxy_arp', 'qos_map', 'roaming_consortium',
                   'venue_group', 'venue_name', 'venue_type',
                   'wan_metrics', 'wnm_sleep_mode']
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


def wireless_controller_hotspot20_hs_profile(data, fos):
    vdom = data['vdom']
    state = data['state']
    wireless_controller_hotspot20_hs_profile_data = data['wireless_controller_hotspot20_hs_profile']
    filtered_data = underscore_to_hyphen(filter_wireless_controller_hotspot20_hs_profile_data(wireless_controller_hotspot20_hs_profile_data))

    if state == "present":
        return fos.set('wireless-controller.hotspot20',
                       'hs-profile',
                       data=filtered_data,
                       vdom=vdom)

    elif state == "absent":
        return fos.delete('wireless-controller.hotspot20',
                          'hs-profile',
                          mkey=filtered_data['name'],
                          vdom=vdom)


def is_successful_status(status):
    return status['status'] == "success" or \
        status['http_method'] == "DELETE" and status['http_status'] == 404


def fortios_wireless_controller_hotspot20(data, fos):

    if data['wireless_controller_hotspot20_hs_profile']:
        resp = wireless_controller_hotspot20_hs_profile(data, fos)

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
        "state": {"required": True, "type": "str",
                  "choices": ["present", "absent"]},
        "wireless_controller_hotspot20_hs_profile": {
            "required": False, "type": "dict", "default": None,
            "options": {
                "access_network_asra": {"required": False, "type": "str",
                                        "choices": ["enable", "disable"]},
                "access_network_esr": {"required": False, "type": "str",
                                       "choices": ["enable", "disable"]},
                "access_network_internet": {"required": False, "type": "str",
                                            "choices": ["enable", "disable"]},
                "access_network_type": {"required": False, "type": "str",
                                        "choices": ["private-network", "private-network-with-guest-access", "chargeable-public-network",
                                                    "free-public-network", "personal-device-network", "emergency-services-only-network",
                                                    "test-or-experimental", "wildcard"]},
                "access_network_uesa": {"required": False, "type": "str",
                                        "choices": ["enable", "disable"]},
                "anqp_domain_id": {"required": False, "type": "int"},
                "bss_transition": {"required": False, "type": "str",
                                   "choices": ["enable", "disable"]},
                "conn_cap": {"required": False, "type": "str"},
                "deauth_request_timeout": {"required": False, "type": "int"},
                "dgaf": {"required": False, "type": "str",
                         "choices": ["enable", "disable"]},
                "domain_name": {"required": False, "type": "str"},
                "gas_comeback_delay": {"required": False, "type": "int"},
                "gas_fragmentation_limit": {"required": False, "type": "int"},
                "hessid": {"required": False, "type": "str"},
                "ip_addr_type": {"required": False, "type": "str"},
                "l2tif": {"required": False, "type": "str",
                          "choices": ["enable", "disable"]},
                "nai_realm": {"required": False, "type": "str"},
                "name": {"required": True, "type": "str"},
                "network_auth": {"required": False, "type": "str"},
                "oper_friendly_name": {"required": False, "type": "str"},
                "osu_provider": {"required": False, "type": "list",
                                 "options": {
                                     "name": {"required": True, "type": "str"}
                                 }},
                "osu_ssid": {"required": False, "type": "str"},
                "pame_bi": {"required": False, "type": "str",
                            "choices": ["disable", "enable"]},
                "proxy_arp": {"required": False, "type": "str",
                              "choices": ["enable", "disable"]},
                "qos_map": {"required": False, "type": "str"},
                "roaming_consortium": {"required": False, "type": "str"},
                "venue_group": {"required": False, "type": "str",
                                "choices": ["unspecified", "assembly", "business",
                                            "educational", "factory", "institutional",
                                            "mercantile", "residential", "storage",
                                            "utility", "vehicular", "outdoor"]},
                "venue_name": {"required": False, "type": "str"},
                "venue_type": {"required": False, "type": "str",
                               "choices": ["unspecified", "arena", "stadium",
                                           "passenger-terminal", "amphitheater", "amusement-park",
                                           "place-of-worship", "convention-center", "library",
                                           "museum", "restaurant", "theater",
                                           "bar", "coffee-shop", "zoo-or-aquarium",
                                           "emergency-center", "doctor-office", "bank",
                                           "fire-station", "police-station", "post-office",
                                           "professional-office", "research-facility", "attorney-office",
                                           "primary-school", "secondary-school", "university-or-college",
                                           "factory", "hospital", "long-term-care-facility",
                                           "rehab-center", "group-home", "prison-or-jail",
                                           "retail-store", "grocery-market", "auto-service-station",
                                           "shopping-mall", "gas-station", "private",
                                           "hotel-or-motel", "dormitory", "boarding-house",
                                           "automobile", "airplane", "bus",
                                           "ferry", "ship-or-boat", "train",
                                           "motor-bike", "muni-mesh-network", "city-park",
                                           "rest-area", "traffic-control", "bus-stop",
                                           "kiosk"]},
                "wan_metrics": {"required": False, "type": "str"},
                "wnm_sleep_mode": {"required": False, "type": "str",
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

            is_error, has_changed, result = fortios_wireless_controller_hotspot20(module.params, fos)
        else:
            module.fail_json(**FAIL_SOCKET_MSG)
    else:
        try:
            from fortiosapi import FortiOSAPI
        except ImportError:
            module.fail_json(msg="fortiosapi module is required")

        fos = FortiOSAPI()

        login(module.params, fos)
        is_error, has_changed, result = fortios_wireless_controller_hotspot20(module.params, fos)
        fos.logout()

    if not is_error:
        module.exit_json(changed=has_changed, meta=result)
    else:
        module.fail_json(msg="Error in repo", meta=result)


if __name__ == '__main__':
    main()
