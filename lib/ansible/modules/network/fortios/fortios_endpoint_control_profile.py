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
module: fortios_endpoint_control_profile
short_description: Configure FortiClient endpoint control profiles in Fortinet's FortiOS and FortiGate.
description:
    - This module is able to configure a FortiGate or FortiOS by
      allowing the user to configure endpoint_control feature and profile category.
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
    endpoint_control_profile:
        description:
            - Configure FortiClient endpoint control profiles.
        default: null
        suboptions:
            state:
                description:
                    - Indicates whether to create or remove the object
                choices:
                    - present
                    - absent
            description:
                description:
                    - Description.
            device-groups:
                description:
                    - Device groups.
                suboptions:
                    name:
                        description:
                            - Device group object from available options. Source user.device-group.name user.device-category.name.
                        required: true
            forticlient-android-settings:
                description:
                    - FortiClient settings for Android platform.
                suboptions:
                    disable-wf-when-protected:
                        description:
                            - Enable/disable FortiClient web category filtering when protected by FortiGate.
                        choices:
                            - enable
                            - disable
                    forticlient-advanced-vpn:
                        description:
                            - Enable/disable advanced FortiClient VPN configuration.
                        choices:
                            - enable
                            - disable
                    forticlient-advanced-vpn-buffer:
                        description:
                            - Advanced FortiClient VPN configuration.
                    forticlient-vpn-provisioning:
                        description:
                            - Enable/disable FortiClient VPN provisioning.
                        choices:
                            - enable
                            - disable
                    forticlient-vpn-settings:
                        description:
                            - FortiClient VPN settings.
                        suboptions:
                            auth-method:
                                description:
                                    - Authentication method.
                                choices:
                                    - psk
                                    - certificate
                            name:
                                description:
                                    - VPN name.
                                required: true
                            preshared-key:
                                description:
                                    - Pre-shared secret for PSK authentication.
                            remote-gw:
                                description:
                                    - IP address or FQDN of the remote VPN gateway.
                            sslvpn-access-port:
                                description:
                                    - SSL VPN access port (1 - 65535).
                            sslvpn-require-certificate:
                                description:
                                    - Enable/disable requiring SSL VPN client certificate.
                                choices:
                                    - enable
                                    - disable
                            type:
                                description:
                                    - VPN type (IPsec or SSL VPN).
                                choices:
                                    - ipsec
                                    - ssl
                    forticlient-wf:
                        description:
                            - Enable/disable FortiClient web filtering.
                        choices:
                            - enable
                            - disable
                    forticlient-wf-profile:
                        description:
                            - The FortiClient web filter profile to apply. Source webfilter.profile.name.
            forticlient-ios-settings:
                description:
                    - FortiClient settings for iOS platform.
                suboptions:
                    client-vpn-provisioning:
                        description:
                            - FortiClient VPN provisioning.
                        choices:
                            - enable
                            - disable
                    client-vpn-settings:
                        description:
                            - FortiClient VPN settings.
                        suboptions:
                            auth-method:
                                description:
                                    - Authentication method.
                                choices:
                                    - psk
                                    - certificate
                            name:
                                description:
                                    - VPN name.
                                required: true
                            preshared-key:
                                description:
                                    - Pre-shared secret for PSK authentication.
                            remote-gw:
                                description:
                                    - IP address or FQDN of the remote VPN gateway.
                            sslvpn-access-port:
                                description:
                                    - SSL VPN access port (1 - 65535).
                            sslvpn-require-certificate:
                                description:
                                    - Enable/disable requiring SSL VPN client certificate.
                                choices:
                                    - enable
                                    - disable
                            type:
                                description:
                                    - VPN type (IPsec or SSL VPN).
                                choices:
                                    - ipsec
                                    - ssl
                            vpn-configuration-content:
                                description:
                                    - Content of VPN configuration.
                            vpn-configuration-name:
                                description:
                                    - Name of VPN configuration.
                    configuration-content:
                        description:
                            - Content of configuration profile.
                    configuration-name:
                        description:
                            - Name of configuration profile.
                    disable-wf-when-protected:
                        description:
                            - Enable/disable FortiClient web category filtering when protected by FortiGate.
                        choices:
                            - enable
                            - disable
                    distribute-configuration-profile:
                        description:
                            - Enable/disable configuration profile (.mobileconfig file) distribution.
                        choices:
                            - enable
                            - disable
                    forticlient-wf:
                        description:
                            - Enable/disable FortiClient web filtering.
                        choices:
                            - enable
                            - disable
                    forticlient-wf-profile:
                        description:
                            - The FortiClient web filter profile to apply. Source webfilter.profile.name.
            forticlient-winmac-settings:
                description:
                    - FortiClient settings for Windows/Mac platform.
                suboptions:
                    av-realtime-protection:
                        description:
                            - Enable/disable FortiClient AntiVirus real-time protection.
                        choices:
                            - enable
                            - disable
                    av-signature-up-to-date:
                        description:
                            - Enable/disable FortiClient AV signature updates.
                        choices:
                            - enable
                            - disable
                    forticlient-application-firewall:
                        description:
                            - Enable/disable the FortiClient application firewall.
                        choices:
                            - enable
                            - disable
                    forticlient-application-firewall-list:
                        description:
                            - FortiClient application firewall rule list. Source application.list.name.
                    forticlient-av:
                        description:
                            - Enable/disable FortiClient AntiVirus scanning.
                        choices:
                            - enable
                            - disable
                    forticlient-ems-compliance:
                        description:
                            - Enable/disable FortiClient Enterprise Management Server (EMS) compliance.
                        choices:
                            - enable
                            - disable
                    forticlient-ems-compliance-action:
                        description:
                            - FortiClient EMS compliance action.
                        choices:
                            - block
                            - warning
                    forticlient-ems-entries:
                        description:
                            - FortiClient EMS entries.
                        suboptions:
                            name:
                                description:
                                    - FortiClient EMS name. Source endpoint-control.forticlient-ems.name.
                                required: true
                    forticlient-linux-ver:
                        description:
                            - Minimum FortiClient Linux version.
                    forticlient-log-upload:
                        description:
                            - Enable/disable uploading FortiClient logs.
                        choices:
                            - enable
                            - disable
                    forticlient-log-upload-level:
                        description:
                            - Select the FortiClient logs to upload.
                        choices:
                            - traffic
                            - vulnerability
                            - event
                    forticlient-log-upload-server:
                        description:
                            - IP address or FQDN of the server to which to upload FortiClient logs.
                    forticlient-mac-ver:
                        description:
                            - Minimum FortiClient Mac OS version.
                    forticlient-minimum-software-version:
                        description:
                            - Enable/disable requiring clients to run FortiClient with a minimum software version number.
                        choices:
                            - enable
                            - disable
                    forticlient-operating-system:
                        description:
                            - FortiClient operating system.
                        suboptions:
                            id:
                                description:
                                    - Operating system entry ID.
                                required: true
                            os-name:
                                description:
                                    - "Customize operating system name or Mac OS format:x.x.x"
                            os-type:
                                description:
                                    - Operating system type.
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
                    forticlient-own-file:
                        description:
                            - Checking the path and filename of the FortiClient application.
                        suboptions:
                            file:
                                description:
                                    - File path and name.
                            id:
                                description:
                                    - File ID.
                                required: true
                    forticlient-registration-compliance-action:
                        description:
                            - FortiClient registration compliance action.
                        choices:
                            - block
                            - warning
                    forticlient-registry-entry:
                        description:
                            - FortiClient registry entry.
                        suboptions:
                            id:
                                description:
                                    - Registry entry ID.
                                required: true
                            registry-entry:
                                description:
                                    - Registry entry.
                    forticlient-running-app:
                        description:
                            - Use FortiClient to verify if the listed applications are running on the client.
                        suboptions:
                            app-name:
                                description:
                                    - Application name.
                            app-sha256-signature:
                                description:
                                    - App's SHA256 signature.
                            app-sha256-signature2:
                                description:
                                    - App's SHA256 Signature.
                            app-sha256-signature3:
                                description:
                                    - App's SHA256 Signature.
                            app-sha256-signature4:
                                description:
                                    - App's SHA256 Signature.
                            application-check-rule:
                                description:
                                    - Application check rule.
                                choices:
                                    - present
                                    - absent
                            id:
                                description:
                                    - Application ID.
                                required: true
                            process-name:
                                description:
                                    - Process name.
                            process-name2:
                                description:
                                    - Process name.
                            process-name3:
                                description:
                                    - Process name.
                            process-name4:
                                description:
                                    - Process name.
                    forticlient-security-posture:
                        description:
                            - Enable/disable FortiClient security posture check options.
                        choices:
                            - enable
                            - disable
                    forticlient-security-posture-compliance-action:
                        description:
                            - FortiClient security posture compliance action.
                        choices:
                            - block
                            - warning
                    forticlient-system-compliance:
                        description:
                            - Enable/disable enforcement of FortiClient system compliance.
                        choices:
                            - enable
                            - disable
                    forticlient-system-compliance-action:
                        description:
                            - Block or warn clients not compliant with FortiClient requirements.
                        choices:
                            - block
                            - warning
                    forticlient-vuln-scan:
                        description:
                            - Enable/disable FortiClient vulnerability scanning.
                        choices:
                            - enable
                            - disable
                    forticlient-vuln-scan-compliance-action:
                        description:
                            - FortiClient vulnerability compliance action.
                        choices:
                            - block
                            - warning
                    forticlient-vuln-scan-enforce:
                        description:
                            - Configure the level of the vulnerability found that causes a FortiClient vulnerability compliance action.
                        choices:
                            - critical
                            - high
                            - medium
                            - low
                            - info
                    forticlient-vuln-scan-enforce-grace:
                        description:
                            - FortiClient vulnerability scan enforcement grace period (0 - 30 days, default = 1).
                    forticlient-vuln-scan-exempt:
                        description:
                            - Enable/disable compliance exemption for vulnerabilities that cannot be patched automatically.
                        choices:
                            - enable
                            - disable
                    forticlient-wf:
                        description:
                            - Enable/disable FortiClient web filtering.
                        choices:
                            - enable
                            - disable
                    forticlient-wf-profile:
                        description:
                            - The FortiClient web filter profile to apply. Source webfilter.profile.name.
                    forticlient-win-ver:
                        description:
                            - Minimum FortiClient Windows version.
                    os-av-software-installed:
                        description:
                            - Enable/disable checking for OS recognized AntiVirus software.
                        choices:
                            - enable
                            - disable
                    sandbox-address:
                        description:
                            - FortiSandbox address.
                    sandbox-analysis:
                        description:
                            - Enable/disable sending files to FortiSandbox for analysis.
                        choices:
                            - enable
                            - disable
            on-net-addr:
                description:
                    - Addresses for on-net detection.
                suboptions:
                    name:
                        description:
                            - Address object from available options. Source firewall.address.name firewall.addrgrp.name.
                        required: true
            profile-name:
                description:
                    - Profile name.
                required: true
            replacemsg-override-group:
                description:
                    - Select an endpoint control replacement message override group from available options. Source system.replacemsg-group.name.
            src-addr:
                description:
                    - Source addresses.
                suboptions:
                    name:
                        description:
                            - Address object from available options. Source firewall.address.name firewall.addrgrp.name.
                        required: true
            user-groups:
                description:
                    - User groups.
                suboptions:
                    name:
                        description:
                            - User group name. Source user.group.name.
                        required: true
            users:
                description:
                    - Users.
                suboptions:
                    name:
                        description:
                            - User name. Source user.local.name.
                        required: true
'''

EXAMPLES = '''
- hosts: localhost
  vars:
   host: "192.168.122.40"
   username: "admin"
   password: ""
   vdom: "root"
  tasks:
  - name: Configure FortiClient endpoint control profiles.
    fortios_endpoint_control_profile:
      host:  "{{ host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{ vdom }}"
      endpoint_control_profile:
        state: "present"
        description: "<your_own_value>"
        device-groups:
         -
            name: "default_name_5 (source user.device-group.name user.device-category.name)"
        forticlient-android-settings:
            disable-wf-when-protected: "enable"
            forticlient-advanced-vpn: "enable"
            forticlient-advanced-vpn-buffer: "<your_own_value>"
            forticlient-vpn-provisioning: "enable"
            forticlient-vpn-settings:
             -
                auth-method: "psk"
                name: "default_name_13"
                preshared-key: "<your_own_value>"
                remote-gw: "<your_own_value>"
                sslvpn-access-port: "16"
                sslvpn-require-certificate: "enable"
                type: "ipsec"
            forticlient-wf: "enable"
            forticlient-wf-profile: "<your_own_value> (source webfilter.profile.name)"
        forticlient-ios-settings:
            client-vpn-provisioning: "enable"
            client-vpn-settings:
             -
                auth-method: "psk"
                name: "default_name_25"
                preshared-key: "<your_own_value>"
                remote-gw: "<your_own_value>"
                sslvpn-access-port: "28"
                sslvpn-require-certificate: "enable"
                type: "ipsec"
                vpn-configuration-content: "<your_own_value>"
                vpn-configuration-name: "<your_own_value>"
            configuration-content: "<your_own_value>"
            configuration-name: "<your_own_value>"
            disable-wf-when-protected: "enable"
            distribute-configuration-profile: "enable"
            forticlient-wf: "enable"
            forticlient-wf-profile: "<your_own_value> (source webfilter.profile.name)"
        forticlient-winmac-settings:
            av-realtime-protection: "enable"
            av-signature-up-to-date: "enable"
            forticlient-application-firewall: "enable"
            forticlient-application-firewall-list: "<your_own_value> (source application.list.name)"
            forticlient-av: "enable"
            forticlient-ems-compliance: "enable"
            forticlient-ems-compliance-action: "block"
            forticlient-ems-entries:
             -
                name: "default_name_48 (source endpoint-control.forticlient-ems.name)"
            forticlient-linux-ver: "<your_own_value>"
            forticlient-log-upload: "enable"
            forticlient-log-upload-level: "traffic"
            forticlient-log-upload-server: "<your_own_value>"
            forticlient-mac-ver: "<your_own_value>"
            forticlient-minimum-software-version: "enable"
            forticlient-operating-system:
             -
                id:  "56"
                os-name: "<your_own_value>"
                os-type: "custom"
            forticlient-own-file:
             -
                file: "<your_own_value>"
                id:  "61"
            forticlient-registration-compliance-action: "block"
            forticlient-registry-entry:
             -
                id:  "64"
                registry-entry: "<your_own_value>"
            forticlient-running-app:
             -
                app-name: "<your_own_value>"
                app-sha256-signature: "<your_own_value>"
                app-sha256-signature2: "<your_own_value>"
                app-sha256-signature3: "<your_own_value>"
                app-sha256-signature4: "<your_own_value>"
                application-check-rule: "present"
                id:  "73"
                process-name: "<your_own_value>"
                process-name2: "<your_own_value>"
                process-name3: "<your_own_value>"
                process-name4: "<your_own_value>"
            forticlient-security-posture: "enable"
            forticlient-security-posture-compliance-action: "block"
            forticlient-system-compliance: "enable"
            forticlient-system-compliance-action: "block"
            forticlient-vuln-scan: "enable"
            forticlient-vuln-scan-compliance-action: "block"
            forticlient-vuln-scan-enforce: "critical"
            forticlient-vuln-scan-enforce-grace: "85"
            forticlient-vuln-scan-exempt: "enable"
            forticlient-wf: "enable"
            forticlient-wf-profile: "<your_own_value> (source webfilter.profile.name)"
            forticlient-win-ver: "<your_own_value>"
            os-av-software-installed: "enable"
            sandbox-address: "<your_own_value>"
            sandbox-analysis: "enable"
        on-net-addr:
         -
            name: "default_name_94 (source firewall.address.name firewall.addrgrp.name)"
        profile-name: "<your_own_value>"
        replacemsg-override-group: "<your_own_value> (source system.replacemsg-group.name)"
        src-addr:
         -
            name: "default_name_98 (source firewall.address.name firewall.addrgrp.name)"
        user-groups:
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


def filter_endpoint_control_profile_data(json):
    option_list = ['description', 'device-groups', 'forticlient-android-settings',
                   'forticlient-ios-settings', 'forticlient-winmac-settings', 'on-net-addr',
                   'profile-name', 'replacemsg-override-group', 'src-addr',
                   'user-groups', 'users']
    dictionary = {}

    for attribute in option_list:
        if attribute in json and json[attribute] is not None:
            dictionary[attribute] = json[attribute]

    return dictionary


def endpoint_control_profile(data, fos):
    vdom = data['vdom']
    endpoint_control_profile_data = data['endpoint_control_profile']
    filtered_data = filter_endpoint_control_profile_data(endpoint_control_profile_data)
    if endpoint_control_profile_data['state'] == "present":
        return fos.set('endpoint-control',
                       'profile',
                       data=filtered_data,
                       vdom=vdom)

    elif endpoint_control_profile_data['state'] == "absent":
        return fos.delete('endpoint-control',
                          'profile',
                          mkey=filtered_data['profile-name'],
                          vdom=vdom)


def fortios_endpoint_control(data, fos):
    login(data)

    methodlist = ['endpoint_control_profile']
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
        "endpoint_control_profile": {
            "required": False, "type": "dict",
            "options": {
                "state": {"required": True, "type": "str",
                          "choices": ["present", "absent"]},
                "description": {"required": False, "type": "str"},
                "device-groups": {"required": False, "type": "list",
                                  "options": {
                                      "name": {"required": True, "type": "str"}
                                  }},
                "forticlient-android-settings": {"required": False, "type": "dict",
                                                 "options": {
                                                     "disable-wf-when-protected": {"required": False, "type": "str",
                                                                                   "choices": ["enable", "disable"]},
                                                     "forticlient-advanced-vpn": {"required": False, "type": "str",
                                                                                  "choices": ["enable", "disable"]},
                                                     "forticlient-advanced-vpn-buffer": {"required": False, "type": "str"},
                                                     "forticlient-vpn-provisioning": {"required": False, "type": "str",
                                                                                      "choices": ["enable", "disable"]},
                                                     "forticlient-vpn-settings": {"required": False, "type": "list",
                                                                                  "options": {
                                                                                      "auth-method": {"required": False, "type": "str",
                                                                                                      "choices": ["psk", "certificate"]},
                                                                                      "name": {"required": True, "type": "str"},
                                                                                      "preshared-key": {"required": False, "type": "str"},
                                                                                      "remote-gw": {"required": False, "type": "str"},
                                                                                      "sslvpn-access-port": {"required": False, "type": "int"},
                                                                                      "sslvpn-require-certificate": {"required": False, "type": "str",
                                                                                                                     "choices": ["enable", "disable"]},
                                                                                      "type": {"required": False, "type": "str",
                                                                                               "choices": ["ipsec", "ssl"]}
                                                                                  }},
                                                     "forticlient-wf": {"required": False, "type": "str",
                                                                        "choices": ["enable", "disable"]},
                                                     "forticlient-wf-profile": {"required": False, "type": "str"}
                                                 }},
                "forticlient-ios-settings": {"required": False, "type": "dict",
                                             "options": {
                                                 "client-vpn-provisioning": {"required": False, "type": "str",
                                                                             "choices": ["enable", "disable"]},
                                                 "client-vpn-settings": {"required": False, "type": "list",
                                                                         "options": {
                                                                             "auth-method": {"required": False, "type": "str",
                                                                                             "choices": ["psk", "certificate"]},
                                                                             "name": {"required": True, "type": "str"},
                                                                             "preshared-key": {"required": False, "type": "str"},
                                                                             "remote-gw": {"required": False, "type": "str"},
                                                                             "sslvpn-access-port": {"required": False, "type": "int"},
                                                                             "sslvpn-require-certificate": {"required": False, "type": "str",
                                                                                                            "choices": ["enable", "disable"]},
                                                                             "type": {"required": False, "type": "str",
                                                                                      "choices": ["ipsec", "ssl"]},
                                                                             "vpn-configuration-content": {"required": False, "type": "str"},
                                                                             "vpn-configuration-name": {"required": False, "type": "str"}
                                                                         }},
                                                 "configuration-content": {"required": False, "type": "str"},
                                                 "configuration-name": {"required": False, "type": "str"},
                                                 "disable-wf-when-protected": {"required": False, "type": "str",
                                                                               "choices": ["enable", "disable"]},
                                                 "distribute-configuration-profile": {"required": False, "type": "str",
                                                                                      "choices": ["enable", "disable"]},
                                                 "forticlient-wf": {"required": False, "type": "str",
                                                                    "choices": ["enable", "disable"]},
                                                 "forticlient-wf-profile": {"required": False, "type": "str"}
                                             }},
                "forticlient-winmac-settings": {"required": False, "type": "dict",
                                                "options": {
                                                    "av-realtime-protection": {"required": False, "type": "str",
                                                                               "choices": ["enable", "disable"]},
                                                    "av-signature-up-to-date": {"required": False, "type": "str",
                                                                                "choices": ["enable", "disable"]},
                                                    "forticlient-application-firewall": {"required": False, "type": "str",
                                                                                         "choices": ["enable", "disable"]},
                                                    "forticlient-application-firewall-list": {"required": False, "type": "str"},
                                                    "forticlient-av": {"required": False, "type": "str",
                                                                       "choices": ["enable", "disable"]},
                                                    "forticlient-ems-compliance": {"required": False, "type": "str",
                                                                                   "choices": ["enable", "disable"]},
                                                    "forticlient-ems-compliance-action": {"required": False, "type": "str",
                                                                                          "choices": ["block", "warning"]},
                                                    "forticlient-ems-entries": {"required": False, "type": "list",
                                                                                "options": {
                                                                                    "name": {"required": True, "type": "str"}
                                                                                }},
                                                    "forticlient-linux-ver": {"required": False, "type": "str"},
                                                    "forticlient-log-upload": {"required": False, "type": "str",
                                                                               "choices": ["enable", "disable"]},
                                                    "forticlient-log-upload-level": {"required": False, "type": "str",
                                                                                     "choices": ["traffic", "vulnerability", "event"]},
                                                    "forticlient-log-upload-server": {"required": False, "type": "str"},
                                                    "forticlient-mac-ver": {"required": False, "type": "str"},
                                                    "forticlient-minimum-software-version": {"required": False, "type": "str",
                                                                                             "choices": ["enable", "disable"]},
                                                    "forticlient-operating-system": {"required": False, "type": "list",
                                                                                     "options": {
                                                                                         "id": {"required": True, "type": "int"},
                                                                                         "os-name": {"required": False, "type": "str"},
                                                                                         "os-type": {"required": False, "type": "str",
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
                                                    "forticlient-own-file": {"required": False, "type": "list",
                                                                             "options": {
                                                                                 "file": {"required": False, "type": "str"},
                                                                                 "id": {"required": True, "type": "int"}
                                                                             }},
                                                    "forticlient-registration-compliance-action": {"required": False, "type": "str",
                                                                                                   "choices": ["block", "warning"]},
                                                    "forticlient-registry-entry": {"required": False, "type": "list",
                                                                                   "options": {
                                                                                       "id": {"required": True, "type": "int"},
                                                                                       "registry-entry": {"required": False, "type": "str"}
                                                                                   }},
                                                    "forticlient-running-app": {"required": False, "type": "list",
                                                                                "options": {
                                                                                    "app-name": {"required": False, "type": "str"},
                                                                                    "app-sha256-signature": {"required": False, "type": "str"},
                                                                                    "app-sha256-signature2": {"required": False, "type": "str"},
                                                                                    "app-sha256-signature3": {"required": False, "type": "str"},
                                                                                    "app-sha256-signature4": {"required": False, "type": "str"},
                                                                                    "application-check-rule": {"required": False, "type": "str",
                                                                                                               "choices": ["present", "absent"]},
                                                                                    "id": {"required": True, "type": "int"},
                                                                                    "process-name": {"required": False, "type": "str"},
                                                                                    "process-name2": {"required": False, "type": "str"},
                                                                                    "process-name3": {"required": False, "type": "str"},
                                                                                    "process-name4": {"required": False, "type": "str"}
                                                                                }},
                                                    "forticlient-security-posture": {"required": False, "type": "str",
                                                                                     "choices": ["enable", "disable"]},
                                                    "forticlient-security-posture-compliance-action": {"required": False, "type": "str",
                                                                                                       "choices": ["block", "warning"]},
                                                    "forticlient-system-compliance": {"required": False, "type": "str",
                                                                                      "choices": ["enable", "disable"]},
                                                    "forticlient-system-compliance-action": {"required": False, "type": "str",
                                                                                             "choices": ["block", "warning"]},
                                                    "forticlient-vuln-scan": {"required": False, "type": "str",
                                                                              "choices": ["enable", "disable"]},
                                                    "forticlient-vuln-scan-compliance-action": {"required": False, "type": "str",
                                                                                                "choices": ["block", "warning"]},
                                                    "forticlient-vuln-scan-enforce": {"required": False, "type": "str",
                                                                                      "choices": ["critical", "high", "medium",
                                                                                                  "low", "info"]},
                                                    "forticlient-vuln-scan-enforce-grace": {"required": False, "type": "int"},
                                                    "forticlient-vuln-scan-exempt": {"required": False, "type": "str",
                                                                                     "choices": ["enable", "disable"]},
                                                    "forticlient-wf": {"required": False, "type": "str",
                                                                       "choices": ["enable", "disable"]},
                                                    "forticlient-wf-profile": {"required": False, "type": "str"},
                                                    "forticlient-win-ver": {"required": False, "type": "str"},
                                                    "os-av-software-installed": {"required": False, "type": "str",
                                                                                 "choices": ["enable", "disable"]},
                                                    "sandbox-address": {"required": False, "type": "str"},
                                                    "sandbox-analysis": {"required": False, "type": "str",
                                                                         "choices": ["enable", "disable"]}
                                                }},
                "on-net-addr": {"required": False, "type": "list",
                                "options": {
                                    "name": {"required": True, "type": "str"}
                                }},
                "profile-name": {"required": True, "type": "str"},
                "replacemsg-override-group": {"required": False, "type": "str"},
                "src-addr": {"required": False, "type": "list",
                             "options": {
                                 "name": {"required": True, "type": "str"}
                             }},
                "user-groups": {"required": False, "type": "list",
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
    try:
        from fortiosapi import FortiOSAPI
    except ImportError:
        module.fail_json(msg="fortiosapi module is required")

    global fos
    fos = FortiOSAPI()

    is_error, has_changed, result = fortios_endpoint_control(module.params, fos)

    if not is_error:
        module.exit_json(changed=has_changed, meta=result)
    else:
        module.fail_json(msg="Error in repo", meta=result)


if __name__ == '__main__':
    main()
