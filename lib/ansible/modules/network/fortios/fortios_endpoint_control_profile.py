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
module: fortios_endpoint_control_profile
short_description: Configure FortiClient endpoint control profiles in Fortinet's FortiOS and FortiGate.
description:
    - This module is able to configure a FortiGate or FortiOS (FOS) device by allowing the
      user to set and modify endpoint_control feature and profile category.
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
    endpoint_control_profile:
        description:
            - Configure FortiClient endpoint control profiles.
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
            description:
                description:
                    - Description.
                type: str
            device_groups:
                description:
                    - Device groups.
                type: list
                suboptions:
                    name:
                        description:
                            - Device group object from available options. Source user.device-group.name user.device-category.name.
                        required: true
                        type: str
            forticlient_android_settings:
                description:
                    - FortiClient settings for Android platform.
                type: dict
                suboptions:
                    disable_wf_when_protected:
                        description:
                            - Enable/disable FortiClient web category filtering when protected by FortiGate.
                        type: str
                        choices:
                            - enable
                            - disable
                    forticlient_advanced_vpn:
                        description:
                            - Enable/disable advanced FortiClient VPN configuration.
                        type: str
                        choices:
                            - enable
                            - disable
                    forticlient_advanced_vpn_buffer:
                        description:
                            - Advanced FortiClient VPN configuration.
                        type: str
                    forticlient_vpn_provisioning:
                        description:
                            - Enable/disable FortiClient VPN provisioning.
                        type: str
                        choices:
                            - enable
                            - disable
                    forticlient_vpn_settings:
                        description:
                            - FortiClient VPN settings.
                        type: list
                        suboptions:
                            auth_method:
                                description:
                                    - Authentication method.
                                type: str
                                choices:
                                    - psk
                                    - certificate
                            name:
                                description:
                                    - VPN name.
                                required: true
                                type: str
                            preshared_key:
                                description:
                                    - Pre-shared secret for PSK authentication.
                                type: str
                            remote_gw:
                                description:
                                    - IP address or FQDN of the remote VPN gateway.
                                type: str
                            sslvpn_access_port:
                                description:
                                    - SSL VPN access port (1 - 65535).
                                type: int
                            sslvpn_require_certificate:
                                description:
                                    - Enable/disable requiring SSL VPN client certificate.
                                type: str
                                choices:
                                    - enable
                                    - disable
                            type:
                                description:
                                    - VPN type (IPsec or SSL VPN).
                                type: str
                                choices:
                                    - ipsec
                                    - ssl
                    forticlient_wf:
                        description:
                            - Enable/disable FortiClient web filtering.
                        type: str
                        choices:
                            - enable
                            - disable
                    forticlient_wf_profile:
                        description:
                            - The FortiClient web filter profile to apply. Source webfilter.profile.name.
                        type: str
            forticlient_ios_settings:
                description:
                    - FortiClient settings for iOS platform.
                type: dict
                suboptions:
                    client_vpn_provisioning:
                        description:
                            - FortiClient VPN provisioning.
                        type: str
                        choices:
                            - enable
                            - disable
                    client_vpn_settings:
                        description:
                            - FortiClient VPN settings.
                        type: list
                        suboptions:
                            auth_method:
                                description:
                                    - Authentication method.
                                type: str
                                choices:
                                    - psk
                                    - certificate
                            name:
                                description:
                                    - VPN name.
                                required: true
                                type: str
                            preshared_key:
                                description:
                                    - Pre-shared secret for PSK authentication.
                                type: str
                            remote_gw:
                                description:
                                    - IP address or FQDN of the remote VPN gateway.
                                type: str
                            sslvpn_access_port:
                                description:
                                    - SSL VPN access port (1 - 65535).
                                type: int
                            sslvpn_require_certificate:
                                description:
                                    - Enable/disable requiring SSL VPN client certificate.
                                type: str
                                choices:
                                    - enable
                                    - disable
                            type:
                                description:
                                    - VPN type (IPsec or SSL VPN).
                                type: str
                                choices:
                                    - ipsec
                                    - ssl
                            vpn_configuration_content:
                                description:
                                    - Content of VPN configuration.
                                type: str
                            vpn_configuration_name:
                                description:
                                    - Name of VPN configuration.
                                type: str
                    configuration_content:
                        description:
                            - Content of configuration profile.
                        type: str
                    configuration_name:
                        description:
                            - Name of configuration profile.
                        type: str
                    disable_wf_when_protected:
                        description:
                            - Enable/disable FortiClient web category filtering when protected by FortiGate.
                        type: str
                        choices:
                            - enable
                            - disable
                    distribute_configuration_profile:
                        description:
                            - Enable/disable configuration profile (.mobileconfig file) distribution.
                        type: str
                        choices:
                            - enable
                            - disable
                    forticlient_wf:
                        description:
                            - Enable/disable FortiClient web filtering.
                        type: str
                        choices:
                            - enable
                            - disable
                    forticlient_wf_profile:
                        description:
                            - The FortiClient web filter profile to apply. Source webfilter.profile.name.
                        type: str
            forticlient_winmac_settings:
                description:
                    - FortiClient settings for Windows/Mac platform.
                type: dict
                suboptions:
                    av_realtime_protection:
                        description:
                            - Enable/disable FortiClient AntiVirus real-time protection.
                        type: str
                        choices:
                            - enable
                            - disable
                    av_signature_up_to_date:
                        description:
                            - Enable/disable FortiClient AV signature updates.
                        type: str
                        choices:
                            - enable
                            - disable
                    forticlient_application_firewall:
                        description:
                            - Enable/disable the FortiClient application firewall.
                        type: str
                        choices:
                            - enable
                            - disable
                    forticlient_application_firewall_list:
                        description:
                            - FortiClient application firewall rule list. Source application.list.name.
                        type: str
                    forticlient_av:
                        description:
                            - Enable/disable FortiClient AntiVirus scanning.
                        type: str
                        choices:
                            - enable
                            - disable
                    forticlient_ems_compliance:
                        description:
                            - Enable/disable FortiClient Enterprise Management Server (EMS) compliance.
                        type: str
                        choices:
                            - enable
                            - disable
                    forticlient_ems_compliance_action:
                        description:
                            - FortiClient EMS compliance action.
                        type: str
                        choices:
                            - block
                            - warning
                    forticlient_ems_entries:
                        description:
                            - FortiClient EMS entries.
                        type: list
                        suboptions:
                            name:
                                description:
                                    - FortiClient EMS name. Source endpoint-control.forticlient-ems.name.
                                required: true
                                type: str
                    forticlient_linux_ver:
                        description:
                            - Minimum FortiClient Linux version.
                        type: str
                    forticlient_log_upload:
                        description:
                            - Enable/disable uploading FortiClient logs.
                        type: str
                        choices:
                            - enable
                            - disable
                    forticlient_log_upload_level:
                        description:
                            - Select the FortiClient logs to upload.
                        type: str
                        choices:
                            - traffic
                            - vulnerability
                            - event
                    forticlient_log_upload_server:
                        description:
                            - IP address or FQDN of the server to which to upload FortiClient logs.
                        type: str
                    forticlient_mac_ver:
                        description:
                            - Minimum FortiClient Mac OS version.
                        type: str
                    forticlient_minimum_software_version:
                        description:
                            - Enable/disable requiring clients to run FortiClient with a minimum software version number.
                        type: str
                        choices:
                            - enable
                            - disable
                    forticlient_operating_system:
                        description:
                            - FortiClient operating system.
                        type: list
                        suboptions:
                            id:
                                description:
                                    - Operating system entry ID.
                                required: true
                                type: int
                            os_name:
                                description:
                                    - "Customize operating system name or Mac OS format:x.x.x"
                                type: str
                            os_type:
                                description:
                                    - Operating system type.
                                type: str
                                choices:
                                    - custom
                                    - mac-os
                                    - win-7
                                    - win-80
                                    - win-81
                                    - win-10
                                    - win-2000
                                    - win-home-svr
                                    - win-svr-10
                                    - win-svr-2003
                                    - win-svr-2003-r2
                                    - win-svr-2008
                                    - win-svr-2008-r2
                                    - win-svr-2012
                                    - win-svr-2012-r2
                                    - win-sto-svr-2003
                                    - win-vista
                                    - win-xp
                                    - ubuntu-linux
                                    - centos-linux
                                    - redhat-linux
                                    - fedora-linux
                    forticlient_own_file:
                        description:
                            - Checking the path and filename of the FortiClient application.
                        type: list
                        suboptions:
                            file:
                                description:
                                    - File path and name.
                                type: str
                            id:
                                description:
                                    - File ID.
                                required: true
                                type: int
                    forticlient_registration_compliance_action:
                        description:
                            - FortiClient registration compliance action.
                        type: str
                        choices:
                            - block
                            - warning
                    forticlient_registry_entry:
                        description:
                            - FortiClient registry entry.
                        type: list
                        suboptions:
                            id:
                                description:
                                    - Registry entry ID.
                                required: true
                                type: int
                            registry_entry:
                                description:
                                    - Registry entry.
                                type: str
                    forticlient_running_app:
                        description:
                            - Use FortiClient to verify if the listed applications are running on the client.
                        type: list
                        suboptions:
                            app_name:
                                description:
                                    - Application name.
                                type: str
                            app_sha256_signature:
                                description:
                                    - App's SHA256 signature.
                                type: str
                            app_sha256_signature2:
                                description:
                                    - App's SHA256 Signature.
                                type: str
                            app_sha256_signature3:
                                description:
                                    - App's SHA256 Signature.
                                type: str
                            app_sha256_signature4:
                                description:
                                    - App's SHA256 Signature.
                                type: str
                            application_check_rule:
                                description:
                                    - Application check rule.
                                type: str
                                choices:
                                    - present
                                    - absent
                            id:
                                description:
                                    - Application ID.
                                required: true
                                type: int
                            process_name:
                                description:
                                    - Process name.
                                type: str
                            process_name2:
                                description:
                                    - Process name.
                                type: str
                            process_name3:
                                description:
                                    - Process name.
                                type: str
                            process_name4:
                                description:
                                    - Process name.
                                type: str
                    forticlient_security_posture:
                        description:
                            - Enable/disable FortiClient security posture check options.
                        type: str
                        choices:
                            - enable
                            - disable
                    forticlient_security_posture_compliance_action:
                        description:
                            - FortiClient security posture compliance action.
                        type: str
                        choices:
                            - block
                            - warning
                    forticlient_system_compliance:
                        description:
                            - Enable/disable enforcement of FortiClient system compliance.
                        type: str
                        choices:
                            - enable
                            - disable
                    forticlient_system_compliance_action:
                        description:
                            - Block or warn clients not compliant with FortiClient requirements.
                        type: str
                        choices:
                            - block
                            - warning
                    forticlient_vuln_scan:
                        description:
                            - Enable/disable FortiClient vulnerability scanning.
                        type: str
                        choices:
                            - enable
                            - disable
                    forticlient_vuln_scan_compliance_action:
                        description:
                            - FortiClient vulnerability compliance action.
                        type: str
                        choices:
                            - block
                            - warning
                    forticlient_vuln_scan_enforce:
                        description:
                            - Configure the level of the vulnerability found that causes a FortiClient vulnerability compliance action.
                        type: str
                        choices:
                            - critical
                            - high
                            - medium
                            - low
                            - info
                    forticlient_vuln_scan_enforce_grace:
                        description:
                            - FortiClient vulnerability scan enforcement grace period (0 - 30 days).
                        type: int
                    forticlient_vuln_scan_exempt:
                        description:
                            - Enable/disable compliance exemption for vulnerabilities that cannot be patched automatically.
                        type: str
                        choices:
                            - enable
                            - disable
                    forticlient_wf:
                        description:
                            - Enable/disable FortiClient web filtering.
                        type: str
                        choices:
                            - enable
                            - disable
                    forticlient_wf_profile:
                        description:
                            - The FortiClient web filter profile to apply. Source webfilter.profile.name.
                        type: str
                    forticlient_win_ver:
                        description:
                            - Minimum FortiClient Windows version.
                        type: str
                    os_av_software_installed:
                        description:
                            - Enable/disable checking for OS recognized AntiVirus software.
                        type: str
                        choices:
                            - enable
                            - disable
                    sandbox_address:
                        description:
                            - FortiSandbox address.
                        type: str
                    sandbox_analysis:
                        description:
                            - Enable/disable sending files to FortiSandbox for analysis.
                        type: str
                        choices:
                            - enable
                            - disable
            on_net_addr:
                description:
                    - Addresses for on-net detection.
                type: list
                suboptions:
                    name:
                        description:
                            - Address object from available options. Source firewall.address.name firewall.addrgrp.name.
                        required: true
                        type: str
            profile_name:
                description:
                    - Profile name.
                type: str
            replacemsg_override_group:
                description:
                    - Select an endpoint control replacement message override group from available options. Source system.replacemsg-group.name.
                type: str
            src_addr:
                description:
                    - Source addresses.
                type: list
                suboptions:
                    name:
                        description:
                            - Address object from available options. Source firewall.address.name firewall.addrgrp.name.
                        required: true
                        type: str
            user_groups:
                description:
                    - User groups.
                type: list
                suboptions:
                    name:
                        description:
                            - User group name. Source user.group.name.
                        required: true
                        type: str
            users:
                description:
                    - Users.
                type: list
                suboptions:
                    name:
                        description:
                            - User name. Source user.local.name.
                        required: true
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
  - name: Configure FortiClient endpoint control profiles.
    fortios_endpoint_control_profile:
      host:  "{{ host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{ vdom }}"
      https: "False"
      state: "present"
      endpoint_control_profile:
        description: "<your_own_value>"
        device_groups:
         -
            name: "default_name_5 (source user.device-group.name user.device-category.name)"
        forticlient_android_settings:
            disable_wf_when_protected: "enable"
            forticlient_advanced_vpn: "enable"
            forticlient_advanced_vpn_buffer: "<your_own_value>"
            forticlient_vpn_provisioning: "enable"
            forticlient_vpn_settings:
             -
                auth_method: "psk"
                name: "default_name_13"
                preshared_key: "<your_own_value>"
                remote_gw: "<your_own_value>"
                sslvpn_access_port: "16"
                sslvpn_require_certificate: "enable"
                type: "ipsec"
            forticlient_wf: "enable"
            forticlient_wf_profile: "<your_own_value> (source webfilter.profile.name)"
        forticlient_ios_settings:
            client_vpn_provisioning: "enable"
            client_vpn_settings:
             -
                auth_method: "psk"
                name: "default_name_25"
                preshared_key: "<your_own_value>"
                remote_gw: "<your_own_value>"
                sslvpn_access_port: "28"
                sslvpn_require_certificate: "enable"
                type: "ipsec"
                vpn_configuration_content: "<your_own_value>"
                vpn_configuration_name: "<your_own_value>"
            configuration_content: "<your_own_value>"
            configuration_name: "<your_own_value>"
            disable_wf_when_protected: "enable"
            distribute_configuration_profile: "enable"
            forticlient_wf: "enable"
            forticlient_wf_profile: "<your_own_value> (source webfilter.profile.name)"
        forticlient_winmac_settings:
            av_realtime_protection: "enable"
            av_signature_up_to_date: "enable"
            forticlient_application_firewall: "enable"
            forticlient_application_firewall_list: "<your_own_value> (source application.list.name)"
            forticlient_av: "enable"
            forticlient_ems_compliance: "enable"
            forticlient_ems_compliance_action: "block"
            forticlient_ems_entries:
             -
                name: "default_name_48 (source endpoint-control.forticlient-ems.name)"
            forticlient_linux_ver: "<your_own_value>"
            forticlient_log_upload: "enable"
            forticlient_log_upload_level: "traffic"
            forticlient_log_upload_server: "<your_own_value>"
            forticlient_mac_ver: "<your_own_value>"
            forticlient_minimum_software_version: "enable"
            forticlient_operating_system:
             -
                id:  "56"
                os_name: "<your_own_value>"
                os_type: "custom"
            forticlient_own_file:
             -
                file: "<your_own_value>"
                id:  "61"
            forticlient_registration_compliance_action: "block"
            forticlient_registry_entry:
             -
                id:  "64"
                registry_entry: "<your_own_value>"
            forticlient_running_app:
             -
                app_name: "<your_own_value>"
                app_sha256_signature: "<your_own_value>"
                app_sha256_signature2: "<your_own_value>"
                app_sha256_signature3: "<your_own_value>"
                app_sha256_signature4: "<your_own_value>"
                application_check_rule: "present"
                id:  "73"
                process_name: "<your_own_value>"
                process_name2: "<your_own_value>"
                process_name3: "<your_own_value>"
                process_name4: "<your_own_value>"
            forticlient_security_posture: "enable"
            forticlient_security_posture_compliance_action: "block"
            forticlient_system_compliance: "enable"
            forticlient_system_compliance_action: "block"
            forticlient_vuln_scan: "enable"
            forticlient_vuln_scan_compliance_action: "block"
            forticlient_vuln_scan_enforce: "critical"
            forticlient_vuln_scan_enforce_grace: "85"
            forticlient_vuln_scan_exempt: "enable"
            forticlient_wf: "enable"
            forticlient_wf_profile: "<your_own_value> (source webfilter.profile.name)"
            forticlient_win_ver: "<your_own_value>"
            os_av_software_installed: "enable"
            sandbox_address: "<your_own_value>"
            sandbox_analysis: "enable"
        on_net_addr:
         -
            name: "default_name_94 (source firewall.address.name firewall.addrgrp.name)"
        profile_name: "<your_own_value>"
        replacemsg_override_group: "<your_own_value> (source system.replacemsg-group.name)"
        src_addr:
         -
            name: "default_name_98 (source firewall.address.name firewall.addrgrp.name)"
        user_groups:
         -
            name: "default_name_100 (source user.group.name)"
        users:
         -
            name: "default_name_102 (source user.local.name)"
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


def filter_endpoint_control_profile_data(json):
    option_list = ['description', 'device_groups', 'forticlient_android_settings',
                   'forticlient_ios_settings', 'forticlient_winmac_settings', 'on_net_addr',
                   'profile_name', 'replacemsg_override_group', 'src_addr',
                   'user_groups', 'users']
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


def endpoint_control_profile(data, fos):
    vdom = data['vdom']
    if 'state' in data and data['state']:
        state = data['state']
    elif 'state' in data['endpoint_control_profile'] and data['endpoint_control_profile']:
        state = data['endpoint_control_profile']['state']
    else:
        state = True
    endpoint_control_profile_data = data['endpoint_control_profile']
    filtered_data = underscore_to_hyphen(filter_endpoint_control_profile_data(endpoint_control_profile_data))

    if state == "present":
        return fos.set('endpoint-control',
                       'profile',
                       data=filtered_data,
                       vdom=vdom)

    elif state == "absent":
        return fos.delete('endpoint-control',
                          'profile',
                          mkey=filtered_data['profile-name'],
                          vdom=vdom)


def is_successful_status(status):
    return status['status'] == "success" or \
        status['http_method'] == "DELETE" and status['http_status'] == 404


def fortios_endpoint_control(data, fos):

    if data['endpoint_control_profile']:
        resp = endpoint_control_profile(data, fos)

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
        "endpoint_control_profile": {
            "required": False, "type": "dict", "default": None,
            "options": {
                "state": {"required": False, "type": "str",
                          "choices": ["present", "absent"]},
                "description": {"required": False, "type": "str"},
                "device_groups": {"required": False, "type": "list",
                                  "options": {
                                      "name": {"required": True, "type": "str"}
                                  }},
                "forticlient_android_settings": {"required": False, "type": "dict",
                                                 "options": {
                                                     "disable_wf_when_protected": {"required": False, "type": "str",
                                                                                   "choices": ["enable", "disable"]},
                                                     "forticlient_advanced_vpn": {"required": False, "type": "str",
                                                                                  "choices": ["enable", "disable"]},
                                                     "forticlient_advanced_vpn_buffer": {"required": False, "type": "str"},
                                                     "forticlient_vpn_provisioning": {"required": False, "type": "str",
                                                                                      "choices": ["enable", "disable"]},
                                                     "forticlient_vpn_settings": {"required": False, "type": "list",
                                                                                  "options": {
                                                                                      "auth_method": {"required": False, "type": "str",
                                                                                                      "choices": ["psk", "certificate"]},
                                                                                      "name": {"required": True, "type": "str"},
                                                                                      "preshared_key": {"required": False, "type": "str"},
                                                                                      "remote_gw": {"required": False, "type": "str"},
                                                                                      "sslvpn_access_port": {"required": False, "type": "int"},
                                                                                      "sslvpn_require_certificate": {"required": False, "type": "str",
                                                                                                                     "choices": ["enable", "disable"]},
                                                                                      "type": {"required": False, "type": "str",
                                                                                               "choices": ["ipsec", "ssl"]}
                                                                                  }},
                                                     "forticlient_wf": {"required": False, "type": "str",
                                                                        "choices": ["enable", "disable"]},
                                                     "forticlient_wf_profile": {"required": False, "type": "str"}
                                                 }},
                "forticlient_ios_settings": {"required": False, "type": "dict",
                                             "options": {
                                                 "client_vpn_provisioning": {"required": False, "type": "str",
                                                                             "choices": ["enable", "disable"]},
                                                 "client_vpn_settings": {"required": False, "type": "list",
                                                                         "options": {
                                                                             "auth_method": {"required": False, "type": "str",
                                                                                             "choices": ["psk", "certificate"]},
                                                                             "name": {"required": True, "type": "str"},
                                                                             "preshared_key": {"required": False, "type": "str"},
                                                                             "remote_gw": {"required": False, "type": "str"},
                                                                             "sslvpn_access_port": {"required": False, "type": "int"},
                                                                             "sslvpn_require_certificate": {"required": False, "type": "str",
                                                                                                            "choices": ["enable", "disable"]},
                                                                             "type": {"required": False, "type": "str",
                                                                                      "choices": ["ipsec", "ssl"]},
                                                                             "vpn_configuration_content": {"required": False, "type": "str"},
                                                                             "vpn_configuration_name": {"required": False, "type": "str"}
                                                                         }},
                                                 "configuration_content": {"required": False, "type": "str"},
                                                 "configuration_name": {"required": False, "type": "str"},
                                                 "disable_wf_when_protected": {"required": False, "type": "str",
                                                                               "choices": ["enable", "disable"]},
                                                 "distribute_configuration_profile": {"required": False, "type": "str",
                                                                                      "choices": ["enable", "disable"]},
                                                 "forticlient_wf": {"required": False, "type": "str",
                                                                    "choices": ["enable", "disable"]},
                                                 "forticlient_wf_profile": {"required": False, "type": "str"}
                                             }},
                "forticlient_winmac_settings": {"required": False, "type": "dict",
                                                "options": {
                                                    "av_realtime_protection": {"required": False, "type": "str",
                                                                               "choices": ["enable", "disable"]},
                                                    "av_signature_up_to_date": {"required": False, "type": "str",
                                                                                "choices": ["enable", "disable"]},
                                                    "forticlient_application_firewall": {"required": False, "type": "str",
                                                                                         "choices": ["enable", "disable"]},
                                                    "forticlient_application_firewall_list": {"required": False, "type": "str"},
                                                    "forticlient_av": {"required": False, "type": "str",
                                                                       "choices": ["enable", "disable"]},
                                                    "forticlient_ems_compliance": {"required": False, "type": "str",
                                                                                   "choices": ["enable", "disable"]},
                                                    "forticlient_ems_compliance_action": {"required": False, "type": "str",
                                                                                          "choices": ["block", "warning"]},
                                                    "forticlient_ems_entries": {"required": False, "type": "list",
                                                                                "options": {
                                                                                    "name": {"required": True, "type": "str"}
                                                                                }},
                                                    "forticlient_linux_ver": {"required": False, "type": "str"},
                                                    "forticlient_log_upload": {"required": False, "type": "str",
                                                                               "choices": ["enable", "disable"]},
                                                    "forticlient_log_upload_level": {"required": False, "type": "str",
                                                                                     "choices": ["traffic", "vulnerability", "event"]},
                                                    "forticlient_log_upload_server": {"required": False, "type": "str"},
                                                    "forticlient_mac_ver": {"required": False, "type": "str"},
                                                    "forticlient_minimum_software_version": {"required": False, "type": "str",
                                                                                             "choices": ["enable", "disable"]},
                                                    "forticlient_operating_system": {"required": False, "type": "list",
                                                                                     "options": {
                                                                                         "id": {"required": True, "type": "int"},
                                                                                         "os_name": {"required": False, "type": "str"},
                                                                                         "os_type": {"required": False, "type": "str",
                                                                                                     "choices": ["custom", "mac-os", "win-7",
                                                                                                                 "win-80", "win-81", "win-10",
                                                                                                                 "win-2000", "win-home-svr", "win-svr-10",
                                                                                                                 "win-svr-2003", "win-svr-2003-r2",
                                                                                                                 "win-svr-2008", "win-svr-2008-r2",
                                                                                                                 "win-svr-2012", "win-svr-2012-r2",
                                                                                                                 "win-sto-svr-2003", "win-vista", "win-xp",
                                                                                                                 "ubuntu-linux", "centos-linux", "redhat-linux",
                                                                                                                 "fedora-linux"]}
                                                                                     }},
                                                    "forticlient_own_file": {"required": False, "type": "list",
                                                                             "options": {
                                                                                 "file": {"required": False, "type": "str"},
                                                                                 "id": {"required": True, "type": "int"}
                                                                             }},
                                                    "forticlient_registration_compliance_action": {"required": False, "type": "str",
                                                                                                   "choices": ["block", "warning"]},
                                                    "forticlient_registry_entry": {"required": False, "type": "list",
                                                                                   "options": {
                                                                                       "id": {"required": True, "type": "int"},
                                                                                       "registry_entry": {"required": False, "type": "str"}
                                                                                   }},
                                                    "forticlient_running_app": {"required": False, "type": "list",
                                                                                "options": {
                                                                                    "app_name": {"required": False, "type": "str"},
                                                                                    "app_sha256_signature": {"required": False, "type": "str"},
                                                                                    "app_sha256_signature2": {"required": False, "type": "str"},
                                                                                    "app_sha256_signature3": {"required": False, "type": "str"},
                                                                                    "app_sha256_signature4": {"required": False, "type": "str"},
                                                                                    "application_check_rule": {"required": False, "type": "str",
                                                                                                               "choices": ["present", "absent"]},
                                                                                    "id": {"required": True, "type": "int"},
                                                                                    "process_name": {"required": False, "type": "str"},
                                                                                    "process_name2": {"required": False, "type": "str"},
                                                                                    "process_name3": {"required": False, "type": "str"},
                                                                                    "process_name4": {"required": False, "type": "str"}
                                                                                }},
                                                    "forticlient_security_posture": {"required": False, "type": "str",
                                                                                     "choices": ["enable", "disable"]},
                                                    "forticlient_security_posture_compliance_action": {"required": False, "type": "str",
                                                                                                       "choices": ["block", "warning"]},
                                                    "forticlient_system_compliance": {"required": False, "type": "str",
                                                                                      "choices": ["enable", "disable"]},
                                                    "forticlient_system_compliance_action": {"required": False, "type": "str",
                                                                                             "choices": ["block", "warning"]},
                                                    "forticlient_vuln_scan": {"required": False, "type": "str",
                                                                              "choices": ["enable", "disable"]},
                                                    "forticlient_vuln_scan_compliance_action": {"required": False, "type": "str",
                                                                                                "choices": ["block", "warning"]},
                                                    "forticlient_vuln_scan_enforce": {"required": False, "type": "str",
                                                                                      "choices": ["critical", "high", "medium",
                                                                                                  "low", "info"]},
                                                    "forticlient_vuln_scan_enforce_grace": {"required": False, "type": "int"},
                                                    "forticlient_vuln_scan_exempt": {"required": False, "type": "str",
                                                                                     "choices": ["enable", "disable"]},
                                                    "forticlient_wf": {"required": False, "type": "str",
                                                                       "choices": ["enable", "disable"]},
                                                    "forticlient_wf_profile": {"required": False, "type": "str"},
                                                    "forticlient_win_ver": {"required": False, "type": "str"},
                                                    "os_av_software_installed": {"required": False, "type": "str",
                                                                                 "choices": ["enable", "disable"]},
                                                    "sandbox_address": {"required": False, "type": "str"},
                                                    "sandbox_analysis": {"required": False, "type": "str",
                                                                         "choices": ["enable", "disable"]}
                                                }},
                "on_net_addr": {"required": False, "type": "list",
                                "options": {
                                    "name": {"required": True, "type": "str"}
                                }},
                "profile_name": {"required": False, "type": "str"},
                "replacemsg_override_group": {"required": False, "type": "str"},
                "src_addr": {"required": False, "type": "list",
                             "options": {
                                 "name": {"required": True, "type": "str"}
                             }},
                "user_groups": {"required": False, "type": "list",
                                "options": {
                                    "name": {"required": True, "type": "str"}
                                }},
                "users": {"required": False, "type": "list",
                          "options": {
                              "name": {"required": True, "type": "str"}
                          }}

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

            is_error, has_changed, result = fortios_endpoint_control(module.params, fos)
        else:
            module.fail_json(**FAIL_SOCKET_MSG)
    else:
        try:
            from fortiosapi import FortiOSAPI
        except ImportError:
            module.fail_json(msg="fortiosapi module is required")

        fos = FortiOSAPI()

        login(module.params, fos)
        is_error, has_changed, result = fortios_endpoint_control(module.params, fos)
        fos.logout()

    if not is_error:
        module.exit_json(changed=has_changed, meta=result)
    else:
        module.fail_json(msg="Error in repo", meta=result)


if __name__ == '__main__':
    main()
