#!/usr/bin/python
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.
#

ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'metadata_version': '1.0'}

DOCUMENTATION = '''
---
module: ce_aaa_server_host
version_added: "2.4"
short_description: Manages AAA server host configuration on HUAWEI CloudEngine switches.
description:
    - Manages AAA server host configuration on HUAWEI CloudEngine switches.
author:
    - wangdezhuang (@CloudEngine-Ansible)
options:
    state:
        description:
            - Specify desired state of the resource.
        required: false
        default: present
        choices: ['present', 'absent']
    local_user_name:
        description:
            - Name of a local user.
              The value is a string of 1 to 253 characters.
        required: false
        default: null
    local_password:
        description:
            - Login password of a user. The password can contain letters, numbers, and special characters.
              The value is a string of 1 to 255 characters.
        required: false
        default: null
    local_service_type:
        description:
            - The type of local user login through, such as ftp ssh snmp telnet.
        required: false
        default: null
    local_ftp_dir:
        description:
            - FTP user directory.
              The value is a string of 1 to 255 characters.
        required: false
        default: null
    local_user_level:
        description:
            - Login level of a local user.
              The value is an integer ranging from 0 to 15.
        required: false
        default: null
    local_user_group:
        description:
            - Name of the user group where the user belongs. The user inherits all the rights of the user group.
              The value is a string of 1 to 32 characters.
        required: false
        default: null
    radius_group_name:
        description:
            - RADIUS server group's name.
              The value is a string of 1 to 32 case-insensitive characters.
        required: false
        default: null
    radius_server_type:
        description:
            - Type of Radius Server.
        required: false
        default: null
        choices: ['Authentication', 'Accounting']
    radius_server_ip:
        description:
            - IPv4 address of configured server.
              The value is a string of 0 to 255 characters, in dotted decimal notation.
        required: false
        default: null
    radius_server_ipv6:
        description:
            - IPv6 address of configured server.
              The total length is 128 bits.
        required: false
        default: null
    radius_server_port:
        description:
            - Configured server port for a particular server.
              The value is an integer ranging from 1 to 65535.
        required: false
        default: null
    radius_server_mode:
        description:
            - Configured primary or secondary server for a particular server.
        required: false
        default: null
        choices: ['Secondary-server', 'Primary-server']
    radius_vpn_name:
        description:
            - Set VPN instance.
              The value is a string of 1 to 31 case-sensitive characters.
        required: false
        default: null
    radius_server_name:
        description:
            - Hostname of configured server.
              The value is a string of 0 to 255 case-sensitive characters.
        required: false
        default: null
    hwtacacs_template:
        description:
            - Name of a HWTACACS template.
              The value is a string of 1 to 32 case-insensitive characters.
        required: false
        default: null
    hwtacacs_server_ip:
        description:
            - Server IPv4 address. Must be a valid unicast IP address.
              The value is a string of 0 to 255 characters, in dotted decimal notation.
        required: false
        default: null
    hwtacacs_server_ipv6:
        description:
            - Server IPv6 address. Must be a valid unicast IP address.
              The total length is 128 bits.
        required: false
        default: null
    hwtacacs_server_type:
        description:
            - Hwtacacs server type.
        required: false
        default: null
        choices: ['Authentication', 'Authorization', 'Accounting', 'Common']
    hwtacacs_is_secondary_server:
        description:
            - Whether the server is secondary.
        required: false
        default: false
        choices: ['true', 'false']
    hwtacacs_vpn_name:
        description:
            - VPN instance name.
        required: false
        default: null
    hwtacacs_is_public_net:
        description:
            - Set the public-net.
        required: false
        default: false
        choices: ['true', 'false']
    hwtacacs_server_host_name:
        description:
            - Hwtacacs server host name.
        required: false
        default: null
'''

EXAMPLES = '''

- name: AAA server host test
  hosts: cloudengine
  connection: local
  gather_facts: no
  vars:
    cli:
      host: "{{ inventory_hostname }}"
      port: "{{ ansible_ssh_port }}"
      username: "{{ username }}"
      password: "{{ password }}"
      transport: cli

  tasks:

  - name: "Config local user when use local scheme"
    ce_aaa_server_host:
      state: present
      local_user_name: user1
      local_password: 123456
      provider: "{{ cli }}"

  - name: "Undo local user when use local scheme"
    ce_aaa_server_host:
      state: absent
      local_user_name: user1
      local_password: 123456
      provider: "{{ cli }}"

  - name: "Config radius server ip"
    ce_aaa_server_host:
      state: present
      radius_group_name: group1
      raduis_server_type: Authentication
      radius_server_ip: 10.1.10.1
      radius_server_port: 2000
      radius_server_mode: Primary-server
      radius_vpn_name: _public_
      provider: "{{ cli }}"

  - name: "Undo radius server ip"
    ce_aaa_server_host:
      state: absent
      radius_group_name: group1
      raduis_server_type: Authentication
      radius_server_ip: 10.1.10.1
      radius_server_port: 2000
      radius_server_mode: Primary-server
      radius_vpn_name: _public_
      provider: "{{ cli }}"

  - name: "Config hwtacacs server ip"
    ce_aaa_server_host:
      state: present
      hwtacacs_template: template
      hwtacacs_server_ip: 10.10.10.10
      hwtacacs_server_type: Authorization
      hwtacacs_vpn_name: _public_
      provider: "{{ cli }}"

  - name: "Undo hwtacacs server ip"
    ce_aaa_server_host:
      state: absent
      hwtacacs_template: template
      hwtacacs_server_ip: 10.10.10.10
      hwtacacs_server_type: Authorization
      hwtacacs_vpn_name: _public_
      provider: "{{ cli }}"
'''

RETURN = '''
changed:
    description: check to see if a change was made on the device
    returned: always
    type: boolean
    sample: true
proposed:
    description: k/v pairs of parameters passed into module
    returned: always
    type: dict
    sample: {"hwtacacs_is_public_net": "false",
             "hwtacacs_is_secondary_server": "false",
             "hwtacacs_server_ip": "10.135.182.157",
             "hwtacacs_server_type": "Authorization",
             "hwtacacs_template": "wdz",
             "hwtacacs_vpn_name": "_public_",
             "local_password": "******",
             "state": "present"}
existing:
    description: k/v pairs of existing aaa server host
    returned: always
    type: dict
    sample: {"radius server ipv4": []}
end_state:
    description: k/v pairs of aaa params after module execution
    returned: always
    type: dict
    sample: {"radius server ipv4": [
             [
                "10.1.10.1",
                "Authentication",
                "2000",
                "Primary-server",
                "_public_"
              ]
             ]}
updates:
    description: command sent to the device
    returned: always
    type: list
    sample: ["hwtacacs server template test",
             "hwtacacs server authorization 10.135.182.157 vpn-instance test_vpn public-net"]
'''

from xml.etree import ElementTree
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ce import get_nc_config, set_nc_config, ce_argument_spec, check_ip_addr

SUCCESS = """success"""
FAILED = """failed"""

INVALID_USER_NAME_CHAR = [' ', '/', '\\',
                          ':', '*', '?', '"', '\'', '<', '>', '%']

# get local user name
CE_GET_LOCAL_USER_INFO_HEADER = """
    <filter type="subtree">
      <aaa xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <lam>
          <users>
            <user>
              <userName></userName>
              <password></password>
"""
CE_GET_LOCAL_USER_INFO_TAIL = """
            </user>
          </users>
        </lam>
      </aaa>
    </filter>
"""

# merge local user name
CE_MERGE_LOCAL_USER_INFO_HEADER = """
    <config>
      <aaa xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <lam>
          <users>
            <user operation="merge">
              <userName>%s</userName>
"""
CE_MERGE_LOCAL_USER_INFO_TAIL = """
            </user>
          </users>
        </lam>
      </aaa>
    </config>
"""

# delete local user name
CE_DELETE_LOCAL_USER_INFO_HEADER = """
    <config>
      <aaa xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <lam>
          <users>
            <user operation="delete">
              <userName>%s</userName>
"""
CE_DELETE_LOCAL_USER_INFO_TAIL = """
            </user>
          </users>
        </lam>
      </aaa>
    </config>
"""

# get radius server config ipv4
CE_GET_RADIUS_SERVER_CFG_IPV4 = """
    <filter type="subtree">
      <radius xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <rdsTemplates>
          <rdsTemplate>
            <groupName>%s</groupName>
            <rdsServerIPV4s>
              <rdsServerIPV4>
                <serverType></serverType>
                <serverIPAddress></serverIPAddress>
                <serverPort></serverPort>
                <serverMode></serverMode>
                <vpnName></vpnName>
              </rdsServerIPV4>
            </rdsServerIPV4s>
          </rdsTemplate>
        </rdsTemplates>
      </radius>
    </filter>
"""

# merge radius server config ipv4
CE_MERGE_RADIUS_SERVER_CFG_IPV4 = """
    <config>
      <radius xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <rdsTemplates>
          <rdsTemplate>
            <groupName>%s</groupName>
            <rdsServerIPV4s>
              <rdsServerIPV4 operation="merge">
                <serverType>%s</serverType>
                <serverIPAddress>%s</serverIPAddress>
                <serverPort>%s</serverPort>
                <serverMode>%s</serverMode>
                <vpnName>%s</vpnName>
              </rdsServerIPV4>
            </rdsServerIPV4s>
          </rdsTemplate>
        </rdsTemplates>
      </radius>
    </config>
"""

# delete radius server config ipv4
CE_DELETE_RADIUS_SERVER_CFG_IPV4 = """
    <config>
      <radius xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <rdsTemplates>
          <rdsTemplate>
            <groupName>%s</groupName>
            <rdsServerIPV4s>
              <rdsServerIPV4 operation="delete">
                <serverType>%s</serverType>
                <serverIPAddress>%s</serverIPAddress>
                <serverPort>%s</serverPort>
                <serverMode>%s</serverMode>
                <vpnName>%s</vpnName>
              </rdsServerIPV4>
            </rdsServerIPV4s>
          </rdsTemplate>
        </rdsTemplates>
      </radius>
    </config>
"""

# get radius server config ipv6
CE_GET_RADIUS_SERVER_CFG_IPV6 = """
    <filter type="subtree">
      <radius xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <rdsTemplates>
          <rdsTemplate>
            <groupName>%s</groupName>
            <rdsServerIPV6s>
              <rdsServerIPV6>
                <serverType></serverType>
                <serverIPAddress></serverIPAddress>
                <serverPort></serverPort>
                <serverMode></serverMode>
              </rdsServerIPV6>
            </rdsServerIPV6s>
          </rdsTemplate>
        </rdsTemplates>
      </radius>
    </filter>
"""

# merge radius server config ipv6
CE_MERGE_RADIUS_SERVER_CFG_IPV6 = """
    <config>
      <radius xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <rdsTemplates>
          <rdsTemplate>
            <groupName>%s</groupName>
            <rdsServerIPV6s>
              <rdsServerIPV6 operation="merge">
                <serverType>%s</serverType>
                <serverIPAddress>%s</serverIPAddress>
                <serverPort>%s</serverPort>
                <serverMode>%s</serverMode>
              </rdsServerIPV6>
            </rdsServerIPV6s>
          </rdsTemplate>
        </rdsTemplates>
      </radius>
    </config>
"""

# delete radius server config ipv6
CE_DELETE_RADIUS_SERVER_CFG_IPV6 = """
    <config>
      <radius xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <rdsTemplates>
          <rdsTemplate>
            <groupName>%s</groupName>
            <rdsServerIPV6s>
              <rdsServerIPV6 operation="delete">
                <serverType>%s</serverType>
                <serverIPAddress>%s</serverIPAddress>
                <serverPort>%s</serverPort>
                <serverMode>%s</serverMode>
              </rdsServerIPV6>
            </rdsServerIPV6s>
          </rdsTemplate>
        </rdsTemplates>
      </radius>
    </config>
"""

# get radius server name
CE_GET_RADIUS_SERVER_NAME = """
    <filter type="subtree">
      <radius xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <rdsTemplates>
          <rdsTemplate>
            <groupName>%s</groupName>
            <rdsServerNames>
              <rdsServerName>
                <serverType></serverType>
                <serverName></serverName>
                <serverPort></serverPort>
                <serverMode></serverMode>
                <vpnName></vpnName>
              </rdsServerName>
            </rdsServerNames>
          </rdsTemplate>
        </rdsTemplates>
      </radius>
    </filter>
"""

# merge radius server name
CE_MERGE_RADIUS_SERVER_NAME = """
    <config>
      <radius xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <rdsTemplates>
          <rdsTemplate>
            <groupName>%s</groupName>
            <rdsServerNames>
              <rdsServerName operation="merge">
                <serverType>%s</serverType>
                <serverName>%s</serverName>
                <serverPort>%s</serverPort>
                <serverMode>%s</serverMode>
                <vpnName>%s</vpnName>
              </rdsServerName>
            </rdsServerNames>
          </rdsTemplate>
        </rdsTemplates>
      </radius>
    </config>
"""

# delete radius server name
CE_DELETE_RADIUS_SERVER_NAME = """
    <config>
      <radius xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <rdsTemplates>
          <rdsTemplate>
            <groupName>%s</groupName>
            <rdsServerNames>
              <rdsServerName operation="delete">
                <serverType>%s</serverType>
                <serverName>%s</serverName>
                <serverPort>%s</serverPort>
                <serverMode>%s</serverMode>
                <vpnName>%s</vpnName>
              </rdsServerName>
            </rdsServerNames>
          </rdsTemplate>
        </rdsTemplates>
      </radius>
    </config>
"""

# get hwtacacs server config ipv4
CE_GET_HWTACACS_SERVER_CFG_IPV4 = """
    <filter type="subtree">
      <hwtacacs xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <hwTacTempCfgs>
          <hwTacTempCfg>
            <templateName>%s</templateName>
            <hwTacSrvCfgs>
              <hwTacSrvCfg>
                <serverIpAddress></serverIpAddress>
                <serverType></serverType>
                <isSecondaryServer></isSecondaryServer>
                <vpnName></vpnName>
                <isPublicNet></isPublicNet>
              </hwTacSrvCfg>
            </hwTacSrvCfgs>
          </hwTacTempCfg>
        </hwTacTempCfgs>
      </hwtacacs>
    </filter>
"""

# merge hwtacacs server config ipv4
CE_MERGE_HWTACACS_SERVER_CFG_IPV4 = """
    <config>
      <hwtacacs xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <hwTacTempCfgs>
          <hwTacTempCfg>
            <templateName>%s</templateName>
            <hwTacSrvCfgs>
              <hwTacSrvCfg operation="merge">
                <serverIpAddress>%s</serverIpAddress>
                <serverType>%s</serverType>
                <isSecondaryServer>%s</isSecondaryServer>
                <vpnName>%s</vpnName>
                <isPublicNet>%s</isPublicNet>
              </hwTacSrvCfg>
            </hwTacSrvCfgs>
          </hwTacTempCfg>
        </hwTacTempCfgs>
      </hwtacacs>
    </config>
"""

# delete hwtacacs server config ipv4
CE_DELETE_HWTACACS_SERVER_CFG_IPV4 = """
    <config>
      <hwtacacs xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <hwTacTempCfgs>
          <hwTacTempCfg>
            <templateName>%s</templateName>
            <hwTacSrvCfgs>
              <hwTacSrvCfg operation="delete">
                <serverIpAddress>%s</serverIpAddress>
                <serverType>%s</serverType>
                <isSecondaryServer>%s</isSecondaryServer>
                <vpnName>%s</vpnName>
                <isPublicNet>%s</isPublicNet>
              </hwTacSrvCfg>
            </hwTacSrvCfgs>
          </hwTacTempCfg>
        </hwTacTempCfgs>
      </hwtacacs>
    </config>
"""

# get hwtacacs server config ipv6
CE_GET_HWTACACS_SERVER_CFG_IPV6 = """
    <filter type="subtree">
      <hwtacacs xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <hwTacTempCfgs>
          <hwTacTempCfg>
            <templateName>%s</templateName>
            <hwTacIpv6SrvCfgs>
              <hwTacIpv6SrvCfg>
                <serverIpAddress></serverIpAddress>
                <serverType></serverType>
                <isSecondaryServer></isSecondaryServer>
                <vpnName></vpnName>
              </hwTacIpv6SrvCfg>
            </hwTacIpv6SrvCfgs>
          </hwTacTempCfg>
        </hwTacTempCfgs>
      </hwtacacs>
    </filter>
"""

# merge hwtacacs server config ipv6
CE_MERGE_HWTACACS_SERVER_CFG_IPV6 = """
    <config>
      <hwtacacs xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <hwTacTempCfgs>
          <hwTacTempCfg>
            <templateName>%s</templateName>
            <hwTacIpv6SrvCfgs>
              <hwTacIpv6SrvCfg operation="merge">
                <serverIpAddress>%s</serverIpAddress>
                <serverType>%s</serverType>
                <isSecondaryServer>%s</isSecondaryServer>
                <vpnName>%s</vpnName>
              </hwTacIpv6SrvCfg>
            </hwTacIpv6SrvCfgs>
          </hwTacTempCfg>
        </hwTacTempCfgs>
      </hwtacacs>
    </config>
"""

# delete hwtacacs server config ipv6
CE_DELETE_HWTACACS_SERVER_CFG_IPV6 = """
    <config>
      <hwtacacs xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <hwTacTempCfgs>
          <hwTacTempCfg>
            <templateName>%s</templateName>
            <hwTacIpv6SrvCfgs>
              <hwTacIpv6SrvCfg operation="delete">
                <serverIpAddress>%s</serverIpAddress>
                <serverType>%s</serverType>
                <isSecondaryServer>%s</isSecondaryServer>
                <vpnName>%s</vpnName>
              </hwTacIpv6SrvCfg>
            </hwTacIpv6SrvCfgs>
          </hwTacTempCfg>
        </hwTacTempCfgs>
      </hwtacacs>
    </config>
"""

# get hwtacacs host server config
CE_GET_HWTACACS_HOST_SERVER_CFG = """
    <filter type="subtree">
      <hwtacacs xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <hwTacTempCfgs>
          <hwTacTempCfg>
            <templateName>%s</templateName>
            <hwTacHostSrvCfgs>
              <hwTacHostSrvCfg>
                <serverHostName></serverHostName>
                <serverType></serverType>
                <isSecondaryServer></isSecondaryServer>
                <vpnName></vpnName>
                <isPublicNet></isPublicNet>
              </hwTacHostSrvCfg>
            </hwTacHostSrvCfgs>
          </hwTacTempCfg>
        </hwTacTempCfgs>
      </hwtacacs>
    </filter>
"""

# merge hwtacacs host server config
CE_MERGE_HWTACACS_HOST_SERVER_CFG = """
    <config>
      <hwtacacs xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <hwTacTempCfgs>
          <hwTacTempCfg>
            <templateName>%s</templateName>
            <hwTacHostSrvCfgs>
              <hwTacHostSrvCfg operation="merge">
                <serverHostName>%s</serverHostName>
                <serverType>%s</serverType>
                <isSecondaryServer>%s</isSecondaryServer>
                <vpnName>%s</vpnName>
                <isPublicNet>%s</isPublicNet>
              </hwTacHostSrvCfg>
            </hwTacHostSrvCfgs>
          </hwTacTempCfg>
        </hwTacTempCfgs>
      </hwtacacs>
    </config>
"""

# delete hwtacacs host server config
CE_DELETE_HWTACACS_HOST_SERVER_CFG = """
    <config>
      <hwtacacs xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <hwTacTempCfgs>
          <hwTacTempCfg>
            <templateName>%s</templateName>
            <hwTacHostSrvCfgs>
              <hwTacHostSrvCfg operation="delete">
                <serverHostName>%s</serverHostName>
                <serverType>%s</serverType>
                <isSecondaryServer>%s</isSecondaryServer>
                <vpnName>%s</vpnName>
                <isPublicNet>%s</isPublicNet>
              </hwTacHostSrvCfg>
            </hwTacHostSrvCfgs>
          </hwTacTempCfg>
        </hwTacTempCfgs>
      </hwtacacs>
    </config>
"""


class AaaServerHost(object):
    """ Manages aaa server host configuration """

    def netconf_get_config(self, **kwargs):
        """ Get configure by netconf """

        module = kwargs["module"]
        conf_str = kwargs["conf_str"]

        xml_str = get_nc_config(module, conf_str)

        return xml_str

    def netconf_set_config(self, **kwargs):
        """ Set configure by netconf """

        module = kwargs["module"]
        conf_str = kwargs["conf_str"]

        recv_xml = set_nc_config(module, conf_str)

        return recv_xml

    def get_local_user_info(self, **kwargs):
        """ Get local user information """

        module = kwargs["module"]
        local_user_name = module.params['local_user_name']
        local_service_type = module.params['local_service_type']
        local_ftp_dir = module.params['local_ftp_dir']
        local_user_level = module.params['local_user_level']
        local_user_group = module.params['local_user_group']
        state = module.params['state']

        result = dict()
        result["local_user_info"] = []
        need_cfg = False

        conf_str = CE_GET_LOCAL_USER_INFO_HEADER

        if local_service_type:
            if local_service_type == "none":
                conf_str += "<serviceTerminal></serviceTerminal>"
                conf_str += "<serviceTelnet></serviceTelnet>"
                conf_str += "<serviceFtp></serviceFtp>"
                conf_str += "<serviceSsh></serviceSsh>"
                conf_str += "<serviceSnmp></serviceSnmp>"
                conf_str += "<serviceDot1x></serviceDot1x>"
            elif local_service_type == "dot1x":
                conf_str += "<serviceDot1x></serviceDot1x>"
            else:
                option = local_service_type.split(" ")
                for tmp in option:
                    if tmp == "dot1x":
                        module.fail_json(
                            msg='Error: Do not input dot1x with other service type.')
                    elif tmp == "none":
                        module.fail_json(
                            msg='Error: Do not input none with other service type.')
                    elif tmp == "ftp":
                        conf_str += "<serviceFtp></serviceFtp>"
                    elif tmp == "snmp":
                        conf_str += "<serviceSnmp></serviceSnmp>"
                    elif tmp == "ssh":
                        conf_str += "<serviceSsh></serviceSsh>"
                    elif tmp == "telnet":
                        conf_str += "<serviceTelnet></serviceTelnet>"
                    elif tmp == "terminal":
                        conf_str += "<serviceTerminal></serviceTerminal>"
                    else:
                        module.fail_json(
                            msg='Error: Do not support the type [%s].' % tmp)

        if local_ftp_dir:
            conf_str += "<ftpDir></ftpDir>"

        if local_user_level:
            conf_str += "<userLevel></userLevel>"

        if local_user_group:
            conf_str += "<userGroupName></userGroupName>"

        conf_str += CE_GET_LOCAL_USER_INFO_TAIL

        recv_xml = self.netconf_get_config(module=module, conf_str=conf_str)

        if "<data/>" in recv_xml:
            if state == "present":
                need_cfg = True

        else:
            xml_str = recv_xml.replace('\r', '').replace('\n', '').\
                replace('xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"', "").\
                replace('xmlns="http://www.huawei.com/netconf/vrp"', "")

            root = ElementTree.fromstring(xml_str)
            local_user_info = root.findall("data/aaa/lam/users/user")
            if local_user_info:
                for tmp in local_user_info:
                    tmp_dict = dict()
                    for site in tmp:
                        if site.tag in ["userName", "password", "userLevel", "ftpDir", "userGroupName",
                                        "serviceTerminal", "serviceTelnet", "serviceFtp", "serviceSsh",
                                        "serviceSnmp", "serviceDot1x"]:
                            tmp_dict[site.tag] = site.text

                    result["local_user_info"].append(tmp_dict)

            if state == "present":
                need_cfg = True
            else:
                if result["local_user_info"]:
                    for tmp in result["local_user_info"]:
                        if "userName" in tmp.keys():
                            if tmp["userName"] == local_user_name:

                                if not local_service_type and not local_user_level \
                                        and not local_ftp_dir and not local_user_group:

                                    need_cfg = True

                                if local_service_type:
                                    if local_service_type == "none":
                                        if tmp.get("serviceTerminal") == "true" or \
                                                tmp.get("serviceTelnet") == "true" or \
                                                tmp.get("serviceFtp") == "true" or \
                                                tmp.get("serviceSsh") == "true" or \
                                                tmp.get("serviceSnmp") == "true" or \
                                                tmp.get("serviceDot1x") == "true":
                                            need_cfg = True
                                    elif local_service_type == "dot1x":
                                        if tmp.get("serviceDot1x") == "true":
                                            need_cfg = True
                                    elif tmp == "ftp":
                                        if tmp.get("serviceFtp") == "true":
                                            need_cfg = True
                                    elif tmp == "snmp":
                                        if tmp.get("serviceSnmp") == "true":
                                            need_cfg = True
                                    elif tmp == "ssh":
                                        if tmp.get("serviceSsh") == "true":
                                            need_cfg = True
                                    elif tmp == "telnet":
                                        if tmp.get("serviceTelnet") == "true":
                                            need_cfg = True
                                    elif tmp == "terminal":
                                        if tmp.get("serviceTerminal") == "true":
                                            need_cfg = True

                                if local_user_level:
                                    if tmp.get("userLevel") == local_user_level:
                                        need_cfg = True

                                if local_ftp_dir:
                                    if tmp.get("ftpDir") == local_ftp_dir:
                                        need_cfg = True

                                if local_user_group:
                                    if tmp.get("userGroupName") == local_user_group:
                                        need_cfg = True

                                break

        result["need_cfg"] = need_cfg
        return result

    def merge_local_user_info(self, **kwargs):
        """ Merge local user information by netconf """

        module = kwargs["module"]
        local_user_name = module.params['local_user_name']
        local_password = module.params['local_password']
        local_service_type = module.params['local_service_type']
        local_ftp_dir = module.params['local_ftp_dir']
        local_user_level = module.params['local_user_level']
        local_user_group = module.params['local_user_group']
        state = module.params['state']

        cmds = []

        conf_str = CE_MERGE_LOCAL_USER_INFO_HEADER % local_user_name

        if local_password:
            conf_str += "<password>%s</password>" % local_password

        if state == "present":
            cmd = "local-user %s password cipher %s" % (
                local_user_name, local_password)
            cmds.append(cmd)

        if local_service_type:
            if local_service_type == "none":
                conf_str += "<serviceTerminal>false</serviceTerminal>"
                conf_str += "<serviceTelnet>false</serviceTelnet>"
                conf_str += "<serviceFtp>false</serviceFtp>"
                conf_str += "<serviceSsh>false</serviceSsh>"
                conf_str += "<serviceSnmp>false</serviceSnmp>"
                conf_str += "<serviceDot1x>false</serviceDot1x>"

                cmd = "local-user %s service-type none" % local_user_name
                cmds.append(cmd)

            elif local_service_type == "dot1x":
                if state == "present":
                    conf_str += "<serviceDot1x>true</serviceDot1x>"
                    cmd = "local-user %s service-type dot1x" % local_user_name
                else:
                    conf_str += "<serviceDot1x>false</serviceDot1x>"
                    cmd = "undo local-user %s service-type" % local_user_name

                cmds.append(cmd)

            else:
                option = local_service_type.split(" ")
                for tmp in option:
                    if tmp == "dot1x":
                        module.fail_json(
                            msg='Error: Do not input dot1x with other service type.')
                    if tmp == "none":
                        module.fail_json(
                            msg='Error: Do not input none with other service type.')

                    if state == "present":
                        if tmp == "ftp":
                            conf_str += "<serviceFtp>true</serviceFtp>"
                            cmd = "local-user %s service-type ftp" % local_user_name
                        elif tmp == "snmp":
                            conf_str += "<serviceSnmp>true</serviceSnmp>"
                            cmd = "local-user %s service-type snmp" % local_user_name
                        elif tmp == "ssh":
                            conf_str += "<serviceSsh>true</serviceSsh>"
                            cmd = "local-user %s service-type ssh" % local_user_name
                        elif tmp == "telnet":
                            conf_str += "<serviceTelnet>true</serviceTelnet>"
                            cmd = "local-user %s service-type telnet" % local_user_name
                        elif tmp == "terminal":
                            conf_str += "<serviceTerminal>true</serviceTerminal>"
                            cmd = "local-user %s service-type terminal" % local_user_name

                        cmds.append(cmd)

                    else:
                        if tmp == "ftp":
                            conf_str += "<serviceFtp>false</serviceFtp>"
                        elif tmp == "snmp":
                            conf_str += "<serviceSnmp>false</serviceSnmp>"
                        elif tmp == "ssh":
                            conf_str += "<serviceSsh>false</serviceSsh>"
                        elif tmp == "telnet":
                            conf_str += "<serviceTelnet>false</serviceTelnet>"
                        elif tmp == "terminal":
                            conf_str += "<serviceTerminal>false</serviceTerminal>"

                if state == "absent":
                    cmd = "undo local-user %s service-type" % local_user_name
                    cmds.append(cmd)

        if local_ftp_dir:
            if state == "present":
                conf_str += "<ftpDir>%s</ftpDir>" % local_ftp_dir
                cmd = "local-user %s ftp-directory %s" % (
                    local_user_name, local_ftp_dir)
                cmds.append(cmd)
            else:
                conf_str += "<ftpDir></ftpDir>"
                cmd = "undo local-user %s ftp-directory" % local_user_name
                cmds.append(cmd)

        if local_user_level:
            if state == "present":
                conf_str += "<userLevel>%s</userLevel>" % local_user_level
                cmd = "local-user %s level %s" % (
                    local_user_name, local_user_level)
                cmds.append(cmd)
            else:
                conf_str += "<userLevel></userLevel>"
                cmd = "undo local-user %s level" % local_user_name
                cmds.append(cmd)

        if local_user_group:
            if state == "present":
                conf_str += "<userGroupName>%s</userGroupName>" % local_user_group
                cmd = "local-user %s user-group %s" % (
                    local_user_name, local_user_group)
                cmds.append(cmd)
            else:
                conf_str += "<userGroupName></userGroupName>"
                cmd = "undo local-user %s user-group" % local_user_name
                cmds.append(cmd)

        conf_str += CE_MERGE_LOCAL_USER_INFO_TAIL

        recv_xml = self.netconf_set_config(module=module, conf_str=conf_str)

        if "<ok/>" not in recv_xml:
            module.fail_json(msg='Error: Merge local user info failed.')

        return cmds

    def delete_local_user_info(self, **kwargs):
        """ Delete local user information by netconf """

        module = kwargs["module"]
        local_user_name = module.params['local_user_name']
        conf_str = CE_DELETE_LOCAL_USER_INFO_HEADER % local_user_name
        conf_str += CE_DELETE_LOCAL_USER_INFO_TAIL

        cmds = []

        recv_xml = self.netconf_set_config(module=module, conf_str=conf_str)

        if "<ok/>" not in recv_xml:
            module.fail_json(msg='Error: Delete local user info failed.')

        cmd = "undo local-user %s" % local_user_name
        cmds.append(cmd)

        return cmds

    def get_radius_server_cfg_ipv4(self, **kwargs):
        """ Get radius server configure ipv4 """

        module = kwargs["module"]
        radius_group_name = module.params['radius_group_name']
        raduis_server_type = module.params['raduis_server_type']
        radius_server_ip = module.params['radius_server_ip']
        radius_server_port = module.params['radius_server_port']
        radius_server_mode = module.params['radius_server_mode']
        radius_vpn_name = module.params['radius_vpn_name']
        state = module.params['state']

        result = dict()
        result["radius_server_ip_v4"] = []
        need_cfg = False

        conf_str = CE_GET_RADIUS_SERVER_CFG_IPV4 % radius_group_name

        recv_xml = self.netconf_get_config(module=module, conf_str=conf_str)

        if "<data/>" in recv_xml:
            if state == "present":
                need_cfg = True

        else:
            xml_str = recv_xml.replace('\r', '').replace('\n', '').\
                replace('xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"', "").\
                replace('xmlns="http://www.huawei.com/netconf/vrp"', "")

            root = ElementTree.fromstring(xml_str)
            radius_server_ip_v4 = root.findall(
                "data/radius/rdsTemplates/rdsTemplate/rdsServerIPV4s/rdsServerIPV4")
            if radius_server_ip_v4:
                for tmp in radius_server_ip_v4:
                    tmp_dict = dict()
                    for site in tmp:
                        if site.tag in ["serverType", "serverIPAddress", "serverPort", "serverMode", "vpnName"]:
                            tmp_dict[site.tag] = site.text

                    result["radius_server_ip_v4"].append(tmp_dict)

            if result["radius_server_ip_v4"]:
                for tmp in result["radius_server_ip_v4"]:
                    if "serverType" in tmp.keys():
                        if state == "present":
                            if tmp["serverType"] != raduis_server_type:
                                need_cfg = True
                        else:
                            if tmp["serverType"] == raduis_server_type:
                                need_cfg = True
                    if "serverIPAddress" in tmp.keys():
                        if state == "present":
                            if tmp["serverIPAddress"] != radius_server_ip:
                                need_cfg = True
                        else:
                            if tmp["serverIPAddress"] == radius_server_ip:
                                need_cfg = True
                    if "serverPort" in tmp.keys():
                        if state == "present":
                            if tmp["serverPort"] != radius_server_port:
                                need_cfg = True
                        else:
                            if tmp["serverPort"] == radius_server_port:
                                need_cfg = True
                    if "serverMode" in tmp.keys():
                        if state == "present":
                            if tmp["serverMode"] != radius_server_mode:
                                need_cfg = True
                        else:
                            if tmp["serverMode"] == radius_server_mode:
                                need_cfg = True
                    if "vpnName" in tmp.keys():
                        if state == "present":
                            if tmp["vpnName"] != radius_vpn_name:
                                need_cfg = True
                        else:
                            if tmp["vpnName"] == radius_vpn_name:
                                need_cfg = True

        result["need_cfg"] = need_cfg
        return result

    def merge_radius_server_cfg_ipv4(self, **kwargs):
        """ Merge radius server configure ipv4 """

        module = kwargs["module"]
        radius_group_name = module.params['radius_group_name']
        raduis_server_type = module.params['raduis_server_type']
        radius_server_ip = module.params['radius_server_ip']
        radius_server_port = module.params['radius_server_port']
        radius_server_mode = module.params['radius_server_mode']
        radius_vpn_name = module.params['radius_vpn_name']

        conf_str = CE_MERGE_RADIUS_SERVER_CFG_IPV4 % (
            radius_group_name, raduis_server_type,
            radius_server_ip, radius_server_port,
            radius_server_mode, radius_vpn_name)

        recv_xml = self.netconf_set_config(module=module, conf_str=conf_str)

        if "<ok/>" not in recv_xml:
            module.fail_json(
                msg='Error: Merge radius server config ipv4 failed.')

        cmds = []

        cmd = "radius server group %s" % radius_group_name
        cmds.append(cmd)

        if raduis_server_type == "Authentication":
            cmd = "radius server authentication %s %s" % (
                radius_server_ip, radius_server_port)

            if radius_vpn_name and radius_vpn_name != "_public_":
                cmd += " vpn-instance %s" % radius_vpn_name

            if radius_server_mode == "Secondary-server":
                cmd += " secondary"
        else:
            cmd = "radius server accounting %s %s" % (
                radius_server_ip, radius_server_port)

            if radius_vpn_name and radius_vpn_name != "_public_":
                cmd += " vpn-instance %s" % radius_vpn_name

            if radius_server_mode == "Secondary-server":
                cmd += " secondary"

        cmds.append(cmd)
        return cmds

    def delete_radius_server_cfg_ipv4(self, **kwargs):
        """ Delete radius server configure ipv4 """

        module = kwargs["module"]
        radius_group_name = module.params['radius_group_name']
        raduis_server_type = module.params['raduis_server_type']
        radius_server_ip = module.params['radius_server_ip']
        radius_server_port = module.params['radius_server_port']
        radius_server_mode = module.params['radius_server_mode']
        radius_vpn_name = module.params['radius_vpn_name']

        conf_str = CE_DELETE_RADIUS_SERVER_CFG_IPV4 % (
            radius_group_name, raduis_server_type,
            radius_server_ip, radius_server_port,
            radius_server_mode, radius_vpn_name)

        recv_xml = self.netconf_set_config(module=module, conf_str=conf_str)

        if "<ok/>" not in recv_xml:
            module.fail_json(
                msg='Error: Create radius server config ipv4 failed.')

        cmds = []

        cmd = "radius server group %s" % radius_group_name
        cmds.append(cmd)

        if raduis_server_type == "Authentication":
            cmd = "undo radius server authentication %s %s" % (
                radius_server_ip, radius_server_port)

            if radius_vpn_name and radius_vpn_name != "_public_":
                cmd += " vpn-instance %s" % radius_vpn_name

            if radius_server_mode == "Secondary-server":
                cmd += " secondary"
        else:
            cmd = "undo radius server accounting  %s %s" % (
                radius_server_ip, radius_server_port)

            if radius_vpn_name and radius_vpn_name != "_public_":
                cmd += " vpn-instance %s" % radius_vpn_name

            if radius_server_mode == "Secondary-server":
                cmd += " secondary"

        cmds.append(cmd)
        return cmds

    def get_radius_server_cfg_ipv6(self, **kwargs):
        """ Get radius server configure ipv6 """

        module = kwargs["module"]
        radius_group_name = module.params['radius_group_name']
        raduis_server_type = module.params['raduis_server_type']
        radius_server_ipv6 = module.params['radius_server_ipv6']
        radius_server_port = module.params['radius_server_port']
        radius_server_mode = module.params['radius_server_mode']
        state = module.params['state']

        result = dict()
        result["radius_server_ip_v6"] = []
        need_cfg = False

        conf_str = CE_GET_RADIUS_SERVER_CFG_IPV6 % radius_group_name

        recv_xml = self.netconf_get_config(module=module, conf_str=conf_str)

        if "<data/>" in recv_xml:
            if state == "present":
                need_cfg = True

        else:
            xml_str = recv_xml.replace('\r', '').replace('\n', '').\
                replace('xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"', "").\
                replace('xmlns="http://www.huawei.com/netconf/vrp"', "")

            root = ElementTree.fromstring(xml_str)
            radius_server_ip_v6 = root.findall(
                "data/radius/rdsTemplates/rdsTemplate/rdsServerIPV6s/rdsServerIPV6")
            if radius_server_ip_v6:
                for tmp in radius_server_ip_v6:
                    tmp_dict = dict()
                    for site in tmp:
                        if site.tag in ["serverType", "serverIPAddress", "serverPort", "serverMode"]:
                            tmp_dict[site.tag] = site.text

                    result["radius_server_ip_v6"].append(tmp_dict)

            if result["radius_server_ip_v6"]:
                for tmp in result["radius_server_ip_v6"]:
                    if "serverType" in tmp.keys():
                        if state == "present":
                            if tmp["serverType"] != raduis_server_type:
                                need_cfg = True
                        else:
                            if tmp["serverType"] == raduis_server_type:
                                need_cfg = True
                    if "serverIPAddress" in tmp.keys():
                        if state == "present":
                            if tmp["serverIPAddress"] != radius_server_ipv6:
                                need_cfg = True
                        else:
                            if tmp["serverIPAddress"] == radius_server_ipv6:
                                need_cfg = True
                    if "serverPort" in tmp.keys():
                        if state == "present":
                            if tmp["serverPort"] != radius_server_port:
                                need_cfg = True
                        else:
                            if tmp["serverPort"] == radius_server_port:
                                need_cfg = True
                    if "serverMode" in tmp.keys():
                        if state == "present":
                            if tmp["serverMode"] != radius_server_mode:
                                need_cfg = True
                        else:
                            if tmp["serverMode"] == radius_server_mode:
                                need_cfg = True

        result["need_cfg"] = need_cfg
        return result

    def merge_radius_server_cfg_ipv6(self, **kwargs):
        """ Merge radius server configure ipv6 """

        module = kwargs["module"]
        radius_group_name = module.params['radius_group_name']
        raduis_server_type = module.params['raduis_server_type']
        radius_server_ipv6 = module.params['radius_server_ipv6']
        radius_server_port = module.params['radius_server_port']
        radius_server_mode = module.params['radius_server_mode']

        conf_str = CE_MERGE_RADIUS_SERVER_CFG_IPV6 % (
            radius_group_name, raduis_server_type,
            radius_server_ipv6, radius_server_port,
            radius_server_mode)

        recv_xml = self.netconf_set_config(module=module, conf_str=conf_str)

        if "<ok/>" not in recv_xml:
            module.fail_json(
                msg='Error: Merge radius server config ipv6 failed.')

        cmds = []

        cmd = "radius server group %s" % radius_group_name
        cmds.append(cmd)

        if raduis_server_type == "Authentication":
            cmd = "radius server authentication %s %s" % (
                radius_server_ipv6, radius_server_port)

            if radius_server_mode == "Secondary-server":
                cmd += " secondary"
        else:
            cmd = "radius server accounting  %s %s" % (
                radius_server_ipv6, radius_server_port)

            if radius_server_mode == "Secondary-server":
                cmd += " secondary"

        cmds.append(cmd)
        return cmds

    def delete_radius_server_cfg_ipv6(self, **kwargs):
        """ Delete radius server configure ipv6 """

        module = kwargs["module"]
        radius_group_name = module.params['radius_group_name']
        raduis_server_type = module.params['raduis_server_type']
        radius_server_ipv6 = module.params['radius_server_ipv6']
        radius_server_port = module.params['radius_server_port']
        radius_server_mode = module.params['radius_server_mode']

        conf_str = CE_DELETE_RADIUS_SERVER_CFG_IPV6 % (
            radius_group_name, raduis_server_type,
            radius_server_ipv6, radius_server_port,
            radius_server_mode)

        recv_xml = self.netconf_set_config(module=module, conf_str=conf_str)

        if "<ok/>" not in recv_xml:
            module.fail_json(
                msg='Error: Create radius server config ipv6 failed.')

        cmds = []

        cmd = "radius server group %s" % radius_group_name
        cmds.append(cmd)

        if raduis_server_type == "Authentication":
            cmd = "undo radius server authentication %s %s" % (
                radius_server_ipv6, radius_server_port)

            if radius_server_mode == "Secondary-server":
                cmd += " secondary"
        else:
            cmd = "undo radius server accounting  %s %s" % (
                radius_server_ipv6, radius_server_port)

            if radius_server_mode == "Secondary-server":
                cmd += " secondary"

        cmds.append(cmd)
        return cmds

    def get_radius_server_name(self, **kwargs):
        """ Get radius server name """

        module = kwargs["module"]
        radius_group_name = module.params['radius_group_name']
        raduis_server_type = module.params['raduis_server_type']
        radius_server_name = module.params['radius_server_name']
        radius_server_port = module.params['radius_server_port']
        radius_server_mode = module.params['radius_server_mode']
        radius_vpn_name = module.params['radius_vpn_name']
        state = module.params['state']

        result = dict()
        result["radius_server_name_cfg"] = []
        need_cfg = False

        conf_str = CE_GET_RADIUS_SERVER_NAME % radius_group_name

        recv_xml = self.netconf_get_config(module=module, conf_str=conf_str)

        if "<data/>" in recv_xml:
            if state == "present":
                need_cfg = True

        else:
            xml_str = recv_xml.replace('\r', '').replace('\n', '').\
                replace('xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"', "").\
                replace('xmlns="http://www.huawei.com/netconf/vrp"', "")

            root = ElementTree.fromstring(xml_str)
            radius_server_name_cfg = root.findall(
                "data/radius/rdsTemplates/rdsTemplate/rdsServerNames/rdsServerName")
            if radius_server_name_cfg:
                for tmp in radius_server_name_cfg:
                    tmp_dict = dict()
                    for site in tmp:
                        if site.tag in ["serverType", "serverName", "serverPort", "serverMode", "vpnName"]:
                            tmp_dict[site.tag] = site.text

                    result["radius_server_name_cfg"].append(tmp_dict)

            if result["radius_server_name_cfg"]:
                for tmp in result["radius_server_name_cfg"]:
                    if "serverType" in tmp.keys():
                        if state == "present":
                            if tmp["serverType"] != raduis_server_type:
                                need_cfg = True
                        else:
                            if tmp["serverType"] == raduis_server_type:
                                need_cfg = True
                    if "serverName" in tmp.keys():
                        if state == "present":
                            if tmp["serverName"] != radius_server_name:
                                need_cfg = True
                        else:
                            if tmp["serverName"] == radius_server_name:
                                need_cfg = True
                    if "serverPort" in tmp.keys():
                        if state == "present":
                            if tmp["serverPort"] != radius_server_port:
                                need_cfg = True
                        else:
                            if tmp["serverPort"] == radius_server_port:
                                need_cfg = True
                    if "serverMode" in tmp.keys():
                        if state == "present":
                            if tmp["serverMode"] != radius_server_mode:
                                need_cfg = True
                        else:
                            if tmp["serverMode"] == radius_server_mode:
                                need_cfg = True
                    if "vpnName" in tmp.keys():
                        if state == "present":
                            if tmp["vpnName"] != radius_vpn_name:
                                need_cfg = True
                        else:
                            if tmp["vpnName"] == radius_vpn_name:
                                need_cfg = True

        result["need_cfg"] = need_cfg
        return result

    def merge_radius_server_name(self, **kwargs):
        """ Merge radius server name """

        module = kwargs["module"]
        radius_group_name = module.params['radius_group_name']
        raduis_server_type = module.params['raduis_server_type']
        radius_server_name = module.params['radius_server_name']
        radius_server_port = module.params['radius_server_port']
        radius_server_mode = module.params['radius_server_mode']
        radius_vpn_name = module.params['radius_vpn_name']

        conf_str = CE_MERGE_RADIUS_SERVER_NAME % (
            radius_group_name, raduis_server_type,
            radius_server_name, radius_server_port,
            radius_server_mode, radius_vpn_name)

        recv_xml = self.netconf_set_config(module=module, conf_str=conf_str)

        if "<ok/>" not in recv_xml:
            module.fail_json(msg='Error: Merge radius server name failed.')

        cmds = []

        cmd = "radius server group %s" % radius_group_name
        cmds.append(cmd)

        if raduis_server_type == "Authentication":
            cmd = "radius server authentication hostname %s %s" % (
                radius_server_name, radius_server_port)

            if radius_vpn_name and radius_vpn_name != "_public_":
                cmd += " vpn-instance %s" % radius_vpn_name

            if radius_server_mode == "Secondary-server":
                cmd += " secondary"
        else:
            cmd = "radius server accounting hostname %s %s" % (
                radius_server_name, radius_server_port)

            if radius_vpn_name and radius_vpn_name != "_public_":
                cmd += " vpn-instance %s" % radius_vpn_name

            if radius_server_mode == "Secondary-server":
                cmd += " secondary"

        cmds.append(cmd)
        return cmds

    def delete_radius_server_name(self, **kwargs):
        """ Delete radius server name """

        module = kwargs["module"]
        radius_group_name = module.params['radius_group_name']
        raduis_server_type = module.params['raduis_server_type']
        radius_server_name = module.params['radius_server_name']
        radius_server_port = module.params['radius_server_port']
        radius_server_mode = module.params['radius_server_mode']
        radius_vpn_name = module.params['radius_vpn_name']

        conf_str = CE_DELETE_RADIUS_SERVER_NAME % (
            radius_group_name, raduis_server_type,
            radius_server_name, radius_server_port,
            radius_server_mode, radius_vpn_name)

        recv_xml = self.netconf_set_config(module=module, conf_str=conf_str)

        if "<ok/>" not in recv_xml:
            module.fail_json(msg='Error: delete radius server name failed.')

        cmds = []

        cmd = "radius server group %s" % radius_group_name
        cmds.append(cmd)

        if raduis_server_type == "Authentication":
            cmd = "undo radius server authentication hostname %s %s" % (
                radius_server_name, radius_server_port)

            if radius_vpn_name and radius_vpn_name != "_public_":
                cmd += " vpn-instance %s" % radius_vpn_name

            if radius_server_mode == "Secondary-server":
                cmd += " secondary"
        else:
            cmd = "undo radius server accounting hostname %s %s" % (
                radius_server_name, radius_server_port)

            if radius_vpn_name and radius_vpn_name != "_public_":
                cmd += " vpn-instance %s" % radius_vpn_name

            if radius_server_mode == "Secondary-server":
                cmd += " secondary"

        cmds.append(cmd)
        return cmds

    def get_hwtacacs_server_cfg_ipv4(self, **kwargs):
        """ Get hwtacacs server configure ipv4 """

        module = kwargs["module"]
        hwtacacs_template = module.params["hwtacacs_template"]
        hwtacacs_server_ip = module.params["hwtacacs_server_ip"]
        hwtacacs_server_type = module.params["hwtacacs_server_type"]
        hwtacacs_is_secondary_server = module.params[
            "hwtacacs_is_secondary_server"]
        hwtacacs_vpn_name = module.params["hwtacacs_vpn_name"]
        hwtacacs_is_public_net = module.params["hwtacacs_is_public_net"]
        state = module.params["state"]

        result = dict()
        result["hwtacacs_server_cfg_ipv4"] = []
        need_cfg = False

        conf_str = CE_GET_HWTACACS_SERVER_CFG_IPV4 % hwtacacs_template

        recv_xml = self.netconf_get_config(module=module, conf_str=conf_str)

        if "<data/>" in recv_xml:
            if state == "present":
                need_cfg = True

        else:
            xml_str = recv_xml.replace('\r', '').replace('\n', '').\
                replace('xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"', "").\
                replace('xmlns="http://www.huawei.com/netconf/vrp"', "")

            root = ElementTree.fromstring(xml_str)
            hwtacacs_server_cfg_ipv4 = root.findall(
                "data/hwtacacs/hwTacTempCfgs/hwTacTempCfg/hwTacSrvCfgs/hwTacSrvCfg")
            if hwtacacs_server_cfg_ipv4:
                for tmp in hwtacacs_server_cfg_ipv4:
                    tmp_dict = dict()
                    for site in tmp:
                        if site.tag in ["serverIpAddress", "serverType", "isSecondaryServer", "isPublicNet", "vpnName"]:
                            tmp_dict[site.tag] = site.text

                    result["hwtacacs_server_cfg_ipv4"].append(tmp_dict)

            if result["hwtacacs_server_cfg_ipv4"]:
                for tmp in result["hwtacacs_server_cfg_ipv4"]:
                    if "serverIpAddress" in tmp.keys():
                        if state == "present":
                            if tmp["serverIpAddress"] != hwtacacs_server_ip:
                                need_cfg = True
                        else:
                            if tmp["serverIpAddress"] == hwtacacs_server_ip:
                                need_cfg = True
                    if "serverType" in tmp.keys():
                        if state == "present":
                            if tmp["serverType"] != hwtacacs_server_type:
                                need_cfg = True
                        else:
                            if tmp["serverType"] == hwtacacs_server_type:
                                need_cfg = True
                    if "isSecondaryServer" in tmp.keys():
                        if state == "present":
                            if tmp["isSecondaryServer"] != str(hwtacacs_is_secondary_server).lower():
                                need_cfg = True
                        else:
                            if tmp["isSecondaryServer"] == str(hwtacacs_is_secondary_server).lower():
                                need_cfg = True
                    if "isPublicNet" in tmp.keys():
                        if state == "present":
                            if tmp["isPublicNet"] != str(hwtacacs_is_public_net).lower():
                                need_cfg = True
                        else:
                            if tmp["isPublicNet"] == str(hwtacacs_is_public_net).lower():
                                need_cfg = True
                    if "vpnName" in tmp.keys():
                        if state == "present":
                            if tmp["vpnName"] != hwtacacs_vpn_name:
                                need_cfg = True
                        else:
                            if tmp["vpnName"] == hwtacacs_vpn_name:
                                need_cfg = True

        result["need_cfg"] = need_cfg
        return result

    def merge_hwtacacs_server_cfg_ipv4(self, **kwargs):
        """ Merge hwtacacs server configure ipv4 """

        module = kwargs["module"]
        hwtacacs_template = module.params["hwtacacs_template"]
        hwtacacs_server_ip = module.params["hwtacacs_server_ip"]
        hwtacacs_server_type = module.params["hwtacacs_server_type"]
        hwtacacs_is_secondary_server = module.params[
            "hwtacacs_is_secondary_server"]
        hwtacacs_vpn_name = module.params["hwtacacs_vpn_name"]
        hwtacacs_is_public_net = module.params["hwtacacs_is_public_net"]

        conf_str = CE_MERGE_HWTACACS_SERVER_CFG_IPV4 % (
            hwtacacs_template, hwtacacs_server_ip,
            hwtacacs_server_type, str(hwtacacs_is_secondary_server).lower(),
            hwtacacs_vpn_name, str(hwtacacs_is_public_net).lower())

        recv_xml = self.netconf_set_config(module=module, conf_str=conf_str)

        if "<ok/>" not in recv_xml:
            module.fail_json(
                msg='Error: Merge hwtacacs server config ipv4 failed.')

        cmds = []

        cmd = "hwtacacs server template %s" % hwtacacs_template
        cmds.append(cmd)

        if hwtacacs_server_type == "Authentication":
            cmd = "hwtacacs server authentication %s" % hwtacacs_server_ip
            if hwtacacs_vpn_name and hwtacacs_vpn_name != "_public_":
                cmd += " vpn-instance %s" % hwtacacs_vpn_name
            if hwtacacs_is_public_net:
                cmd += " public-net"
            if hwtacacs_is_secondary_server:
                cmd += " secondary"

        elif hwtacacs_server_type == "Authorization":
            cmd = "hwtacacs server authorization %s" % hwtacacs_server_ip
            if hwtacacs_vpn_name and hwtacacs_vpn_name != "_public_":
                cmd += " vpn-instance %s" % hwtacacs_vpn_name
            if hwtacacs_is_public_net:
                cmd += " public-net"
            if hwtacacs_is_secondary_server:
                cmd += " secondary"

        elif hwtacacs_server_type == "Accounting":
            cmd = "hwtacacs server accounting %s" % hwtacacs_server_ip
            if hwtacacs_vpn_name and hwtacacs_vpn_name != "_public_":
                cmd += " vpn-instance %s" % hwtacacs_vpn_name
            if hwtacacs_is_public_net:
                cmd += " public-net"
            if hwtacacs_is_secondary_server:
                cmd += " secondary"

        elif hwtacacs_server_type == "Common":
            cmd = "hwtacacs server %s" % hwtacacs_server_ip
            if hwtacacs_vpn_name and hwtacacs_vpn_name != "_public_":
                cmd += " vpn-instance %s" % hwtacacs_vpn_name
            if hwtacacs_is_public_net:
                cmd += " public-net"
            if hwtacacs_is_secondary_server:
                cmd += " secondary"

        cmds.append(cmd)
        return cmds

    def delete_hwtacacs_server_cfg_ipv4(self, **kwargs):
        """ Delete hwtacacs server configure ipv4 """

        module = kwargs["module"]
        hwtacacs_template = module.params["hwtacacs_template"]
        hwtacacs_server_ip = module.params["hwtacacs_server_ip"]
        hwtacacs_server_type = module.params["hwtacacs_server_type"]
        hwtacacs_is_secondary_server = module.params[
            "hwtacacs_is_secondary_server"]
        hwtacacs_vpn_name = module.params["hwtacacs_vpn_name"]
        hwtacacs_is_public_net = module.params["hwtacacs_is_public_net"]

        conf_str = CE_DELETE_HWTACACS_SERVER_CFG_IPV4 % (
            hwtacacs_template, hwtacacs_server_ip,
            hwtacacs_server_type, str(hwtacacs_is_secondary_server).lower(),
            hwtacacs_vpn_name, str(hwtacacs_is_public_net).lower())

        recv_xml = self.netconf_set_config(module=module, conf_str=conf_str)

        if "<ok/>" not in recv_xml:
            module.fail_json(
                msg='Error: Delete hwtacacs server config ipv4 failed.')

        cmds = []

        cmd = "hwtacacs server template %s" % hwtacacs_template
        cmds.append(cmd)

        if hwtacacs_server_type == "Authentication":
            cmd = "undo hwtacacs server authentication %s" % hwtacacs_server_ip
            if hwtacacs_vpn_name and hwtacacs_vpn_name != "_public_":
                cmd += " vpn-instance %s" % hwtacacs_vpn_name
            if hwtacacs_is_public_net:
                cmd += " public-net"
            if hwtacacs_is_secondary_server:
                cmd += " secondary"

        elif hwtacacs_server_type == "Authorization":
            cmd = "undo hwtacacs server authorization %s" % hwtacacs_server_ip
            if hwtacacs_vpn_name and hwtacacs_vpn_name != "_public_":
                cmd += " vpn-instance %s" % hwtacacs_vpn_name
            if hwtacacs_is_public_net:
                cmd += " public-net"
            if hwtacacs_is_secondary_server:
                cmd += " secondary"

        elif hwtacacs_server_type == "Accounting":
            cmd = "undo hwtacacs server accounting %s" % hwtacacs_server_ip
            if hwtacacs_vpn_name and hwtacacs_vpn_name != "_public_":
                cmd += " vpn-instance %s" % hwtacacs_vpn_name
            if hwtacacs_is_public_net:
                cmd += " public-net"
            if hwtacacs_is_secondary_server:
                cmd += " secondary"

        elif hwtacacs_server_type == "Common":
            cmd = "undo hwtacacs server %s" % hwtacacs_server_ip
            if hwtacacs_vpn_name and hwtacacs_vpn_name != "_public_":
                cmd += " vpn-instance %s" % hwtacacs_vpn_name
            if hwtacacs_is_public_net:
                cmd += " public-net"
            if hwtacacs_is_secondary_server:
                cmd += " secondary"

        cmds.append(cmd)
        return cmds

    def get_hwtacacs_server_cfg_ipv6(self, **kwargs):
        """ Get hwtacacs server configure ipv6 """

        module = kwargs["module"]
        hwtacacs_template = module.params["hwtacacs_template"]
        hwtacacs_server_ipv6 = module.params["hwtacacs_server_ipv6"]
        hwtacacs_server_type = module.params["hwtacacs_server_type"]
        hwtacacs_is_secondary_server = module.params[
            "hwtacacs_is_secondary_server"]
        hwtacacs_vpn_name = module.params["hwtacacs_vpn_name"]
        state = module.params["state"]

        result = dict()
        result["hwtacacs_server_cfg_ipv6"] = []
        need_cfg = False

        conf_str = CE_GET_HWTACACS_SERVER_CFG_IPV6 % hwtacacs_template

        recv_xml = self.netconf_get_config(module=module, conf_str=conf_str)

        if "<data/>" in recv_xml:
            if state == "present":
                need_cfg = True

        else:
            xml_str = recv_xml.replace('\r', '').replace('\n', '').\
                replace('xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"', "").\
                replace('xmlns="http://www.huawei.com/netconf/vrp"', "")

            root = ElementTree.fromstring(xml_str)
            hwtacacs_server_cfg_ipv6 = root.findall(
                "data/hwtacacs/hwTacTempCfgs/hwTacTempCfg/hwTacIpv6SrvCfgs/hwTacIpv6SrvCfg")
            if hwtacacs_server_cfg_ipv6:
                for tmp in hwtacacs_server_cfg_ipv6:
                    tmp_dict = dict()
                    for site in tmp:
                        if site.tag in ["serverIpAddress", "serverType", "isSecondaryServer", "vpnName"]:
                            tmp_dict[site.tag] = site.text

                    result["hwtacacs_server_cfg_ipv6"].append(tmp_dict)

            if result["hwtacacs_server_cfg_ipv6"]:
                for tmp in result["hwtacacs_server_cfg_ipv6"]:
                    if "serverIpAddress" in tmp.keys():
                        if state == "present":
                            if tmp["serverIpAddress"] != hwtacacs_server_ipv6:
                                need_cfg = True
                        else:
                            if tmp["serverIpAddress"] == hwtacacs_server_ipv6:
                                need_cfg = True
                    if "serverType" in tmp.keys():
                        if state == "present":
                            if tmp["serverType"] != hwtacacs_server_type:
                                need_cfg = True
                        else:
                            if tmp["serverType"] == hwtacacs_server_type:
                                need_cfg = True
                    if "isSecondaryServer" in tmp.keys():
                        if state == "present":
                            if tmp["isSecondaryServer"] != str(hwtacacs_is_secondary_server).lower():
                                need_cfg = True
                        else:
                            if tmp["isSecondaryServer"] == str(hwtacacs_is_secondary_server).lower():
                                need_cfg = True
                    if "vpnName" in tmp.keys():
                        if state == "present":
                            if tmp["vpnName"] != hwtacacs_vpn_name:
                                need_cfg = True
                        else:
                            if tmp["vpnName"] == hwtacacs_vpn_name:
                                need_cfg = True

        result["need_cfg"] = need_cfg
        return result

    def merge_hwtacacs_server_cfg_ipv6(self, **kwargs):
        """ Merge hwtacacs server configure ipv6 """

        module = kwargs["module"]
        hwtacacs_template = module.params["hwtacacs_template"]
        hwtacacs_server_ipv6 = module.params["hwtacacs_server_ipv6"]
        hwtacacs_server_type = module.params["hwtacacs_server_type"]
        hwtacacs_is_secondary_server = module.params[
            "hwtacacs_is_secondary_server"]
        hwtacacs_vpn_name = module.params["hwtacacs_vpn_name"]

        conf_str = CE_MERGE_HWTACACS_SERVER_CFG_IPV6 % (
            hwtacacs_template, hwtacacs_server_ipv6,
            hwtacacs_server_type, str(hwtacacs_is_secondary_server).lower(),
            hwtacacs_vpn_name)

        recv_xml = self.netconf_set_config(module=module, conf_str=conf_str)

        if "<ok/>" not in recv_xml:
            module.fail_json(
                msg='Error: Merge hwtacacs server config ipv6 failed.')

        cmds = []

        cmd = "hwtacacs server template %s" % hwtacacs_template
        cmds.append(cmd)

        if hwtacacs_server_type == "Authentication":
            cmd = "hwtacacs server authentication %s" % hwtacacs_server_ipv6
            if hwtacacs_vpn_name and hwtacacs_vpn_name != "_public_":
                cmd += " vpn-instance %s" % hwtacacs_vpn_name
            if hwtacacs_is_secondary_server:
                cmd += " secondary"

        elif hwtacacs_server_type == "Authorization":
            cmd = "hwtacacs server authorization %s" % hwtacacs_server_ipv6
            if hwtacacs_vpn_name and hwtacacs_vpn_name != "_public_":
                cmd += " vpn-instance %s" % hwtacacs_vpn_name
            if hwtacacs_is_secondary_server:
                cmd += " secondary"

        elif hwtacacs_server_type == "Accounting":
            cmd = "hwtacacs server accounting %s" % hwtacacs_server_ipv6
            if hwtacacs_vpn_name and hwtacacs_vpn_name != "_public_":
                cmd += " vpn-instance %s" % hwtacacs_vpn_name
            if hwtacacs_is_secondary_server:
                cmd += " secondary"

        elif hwtacacs_server_type == "Common":
            cmd = "hwtacacs server %s" % hwtacacs_server_ipv6
            if hwtacacs_vpn_name and hwtacacs_vpn_name != "_public_":
                cmd += " vpn-instance %s" % hwtacacs_vpn_name
            if hwtacacs_is_secondary_server:
                cmd += " secondary"

        cmds.append(cmd)
        return cmds

    def delete_hwtacacs_server_cfg_ipv6(self, **kwargs):
        """ Delete hwtacacs server configure ipv6 """

        module = kwargs["module"]
        hwtacacs_template = module.params["hwtacacs_template"]
        hwtacacs_server_ipv6 = module.params["hwtacacs_server_ipv6"]
        hwtacacs_server_type = module.params["hwtacacs_server_type"]
        hwtacacs_is_secondary_server = module.params[
            "hwtacacs_is_secondary_server"]
        hwtacacs_vpn_name = module.params["hwtacacs_vpn_name"]

        conf_str = CE_DELETE_HWTACACS_SERVER_CFG_IPV6 % (
            hwtacacs_template, hwtacacs_server_ipv6,
            hwtacacs_server_type, str(hwtacacs_is_secondary_server).lower(),
            hwtacacs_vpn_name)

        recv_xml = self.netconf_set_config(module=module, conf_str=conf_str)

        if "<ok/>" not in recv_xml:
            module.fail_json(
                msg='Error: Delete hwtacacs server config ipv6 failed.')

        cmds = []

        cmd = "hwtacacs server template %s" % hwtacacs_template
        cmds.append(cmd)

        if hwtacacs_server_type == "Authentication":
            cmd = "undo hwtacacs server authentication %s" % hwtacacs_server_ipv6
            if hwtacacs_vpn_name and hwtacacs_vpn_name != "_public_":
                cmd += " vpn-instance %s" % hwtacacs_vpn_name
            if hwtacacs_is_secondary_server:
                cmd += " secondary"

        elif hwtacacs_server_type == "Authorization":
            cmd = "undo hwtacacs server authorization %s" % hwtacacs_server_ipv6
            if hwtacacs_vpn_name and hwtacacs_vpn_name != "_public_":
                cmd += " vpn-instance %s" % hwtacacs_vpn_name
            if hwtacacs_is_secondary_server:
                cmd += " secondary"

        elif hwtacacs_server_type == "Accounting":
            cmd = "undo hwtacacs server accounting %s" % hwtacacs_server_ipv6
            if hwtacacs_vpn_name and hwtacacs_vpn_name != "_public_":
                cmd += " vpn-instance %s" % hwtacacs_vpn_name
            if hwtacacs_is_secondary_server:
                cmd += " secondary"

        elif hwtacacs_server_type == "Common":
            cmd = "undo hwtacacs server %s" % hwtacacs_server_ipv6
            if hwtacacs_vpn_name and hwtacacs_vpn_name != "_public_":
                cmd += " vpn-instance %s" % hwtacacs_vpn_name
            if hwtacacs_is_secondary_server:
                cmd += " secondary"

        cmds.append(cmd)
        return cmds

    def get_hwtacacs_host_server_cfg(self, **kwargs):
        """ Get hwtacacs host server configure """

        module = kwargs["module"]
        hwtacacs_template = module.params["hwtacacs_template"]
        hwtacacs_server_host_name = module.params["hwtacacs_server_host_name"]
        hwtacacs_server_type = module.params["hwtacacs_server_type"]
        hwtacacs_is_secondary_server = module.params[
            "hwtacacs_is_secondary_server"]
        hwtacacs_vpn_name = module.params["hwtacacs_vpn_name"]
        hwtacacs_is_public_net = module.params["hwtacacs_is_public_net"]
        state = module.params["state"]

        result = dict()
        result["hwtacacs_server_name_cfg"] = []
        need_cfg = False

        conf_str = CE_GET_HWTACACS_HOST_SERVER_CFG % hwtacacs_template

        recv_xml = self.netconf_get_config(module=module, conf_str=conf_str)

        if "<data/>" in recv_xml:
            if state == "present":
                need_cfg = True

        else:
            xml_str = recv_xml.replace('\r', '').replace('\n', '').\
                replace('xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"', "").\
                replace('xmlns="http://www.huawei.com/netconf/vrp"', "")

            root = ElementTree.fromstring(xml_str)
            hwtacacs_server_name_cfg = root.findall(
                "data/hwtacacs/hwTacTempCfgs/hwTacTempCfg/hwTacHostSrvCfgs/hwTacHostSrvCfg")
            if hwtacacs_server_name_cfg:
                for tmp in hwtacacs_server_name_cfg:
                    tmp_dict = dict()
                    for site in tmp:
                        if site.tag in ["serverHostName", "serverType", "isSecondaryServer", "isPublicNet", "vpnName"]:
                            tmp_dict[site.tag] = site.text

                    result["hwtacacs_server_name_cfg"].append(tmp_dict)

            if result["hwtacacs_server_name_cfg"]:
                for tmp in result["hwtacacs_server_name_cfg"]:
                    if "serverHostName" in tmp.keys():
                        if state == "present":
                            if tmp["serverHostName"] != hwtacacs_server_host_name:
                                need_cfg = True
                        else:
                            if tmp["serverHostName"] == hwtacacs_server_host_name:
                                need_cfg = True
                    if "serverType" in tmp.keys():
                        if state == "present":
                            if tmp["serverType"] != hwtacacs_server_type:
                                need_cfg = True
                        else:
                            if tmp["serverType"] == hwtacacs_server_type:
                                need_cfg = True
                    if "isSecondaryServer" in tmp.keys():
                        if state == "present":
                            if tmp["isSecondaryServer"] != str(hwtacacs_is_secondary_server).lower():
                                need_cfg = True
                        else:
                            if tmp["isSecondaryServer"] == str(hwtacacs_is_secondary_server).lower():
                                need_cfg = True
                    if "isPublicNet" in tmp.keys():
                        if state == "present":
                            if tmp["isPublicNet"] != str(hwtacacs_is_public_net).lower():
                                need_cfg = True
                        else:
                            if tmp["isPublicNet"] == str(hwtacacs_is_public_net).lower():
                                need_cfg = True
                    if "vpnName" in tmp.keys():
                        if state == "present":
                            if tmp["vpnName"] != hwtacacs_vpn_name:
                                need_cfg = True
                        else:
                            if tmp["vpnName"] == hwtacacs_vpn_name:
                                need_cfg = True

        result["need_cfg"] = need_cfg
        return result

    def merge_hwtacacs_host_server_cfg(self, **kwargs):
        """ Merge hwtacacs host server configure """

        module = kwargs["module"]
        hwtacacs_template = module.params["hwtacacs_template"]
        hwtacacs_server_host_name = module.params["hwtacacs_server_host_name"]
        hwtacacs_server_type = module.params["hwtacacs_server_type"]
        hwtacacs_is_secondary_server = module.params[
            "hwtacacs_is_secondary_server"]
        hwtacacs_vpn_name = module.params["hwtacacs_vpn_name"]
        hwtacacs_is_public_net = module.params["hwtacacs_is_public_net"]

        conf_str = CE_MERGE_HWTACACS_HOST_SERVER_CFG % (
            hwtacacs_template, hwtacacs_server_host_name,
            hwtacacs_server_type, str(hwtacacs_is_secondary_server).lower(),
            hwtacacs_vpn_name, str(hwtacacs_is_public_net).lower())

        recv_xml = self.netconf_set_config(module=module, conf_str=conf_str)

        if "<ok/>" not in recv_xml:
            module.fail_json(
                msg='Error: Merge hwtacacs host server config failed.')

        cmds = []

        if hwtacacs_server_type == "Authentication":
            cmd = "hwtacacs server authentication host host-name %s" % hwtacacs_server_host_name
            if hwtacacs_vpn_name and hwtacacs_vpn_name != "_public_":
                cmd += " vpn-instance %s" % hwtacacs_vpn_name
            if hwtacacs_is_public_net:
                cmd += " public-net"
            if hwtacacs_is_secondary_server:
                cmd += " secondary"

        elif hwtacacs_server_type == "Authorization":
            cmd = "hwtacacs server authorization host host-name %s" % hwtacacs_server_host_name
            if hwtacacs_vpn_name and hwtacacs_vpn_name != "_public_":
                cmd += " vpn-instance %s" % hwtacacs_vpn_name
            if hwtacacs_is_public_net:
                cmd += " public-net"
            if hwtacacs_is_secondary_server:
                cmd += " secondary"

        elif hwtacacs_server_type == "Accounting":
            cmd = "hwtacacs server accounting host host-name %s" % hwtacacs_server_host_name
            if hwtacacs_vpn_name and hwtacacs_vpn_name != "_public_":
                cmd += " vpn-instance %s" % hwtacacs_vpn_name
            if hwtacacs_is_public_net:
                cmd += " public-net"
            if hwtacacs_is_secondary_server:
                cmd += " secondary"

        elif hwtacacs_server_type == "Common":
            cmd = "hwtacacs server host host-name %s" % hwtacacs_server_host_name
            if hwtacacs_vpn_name and hwtacacs_vpn_name != "_public_":
                cmd += " vpn-instance %s" % hwtacacs_vpn_name
            if hwtacacs_is_public_net:
                cmd += " public-net"
            if hwtacacs_is_secondary_server:
                cmd += " secondary"

        cmds.append(cmd)
        return cmds

    def delete_hwtacacs_host_server_cfg(self, **kwargs):
        """ Delete hwtacacs host server configure """

        module = kwargs["module"]
        hwtacacs_template = module.params["hwtacacs_template"]
        hwtacacs_server_host_name = module.params["hwtacacs_server_host_name"]
        hwtacacs_server_type = module.params["hwtacacs_server_type"]
        hwtacacs_is_secondary_server = module.params[
            "hwtacacs_is_secondary_server"]
        hwtacacs_vpn_name = module.params["hwtacacs_vpn_name"]
        hwtacacs_is_public_net = module.params["hwtacacs_is_public_net"]

        conf_str = CE_DELETE_HWTACACS_HOST_SERVER_CFG % (
            hwtacacs_template, hwtacacs_server_host_name,
            hwtacacs_server_type, str(hwtacacs_is_secondary_server).lower(),
            hwtacacs_vpn_name, str(hwtacacs_is_public_net).lower())

        recv_xml = self.netconf_set_config(module=module, conf_str=conf_str)

        if "<ok/>" not in recv_xml:
            module.fail_json(
                msg='Error: Delete hwtacacs host server config failed.')

        cmds = []

        if hwtacacs_server_type == "Authentication":
            cmd = "undo hwtacacs server authentication host host-name %s" % hwtacacs_server_host_name
            if hwtacacs_vpn_name and hwtacacs_vpn_name != "_public_":
                cmd += " vpn-instance %s" % hwtacacs_vpn_name
            if hwtacacs_is_public_net:
                cmd += " public-net"
            if hwtacacs_is_secondary_server:
                cmd += " secondary"

        elif hwtacacs_server_type == "Authorization":
            cmd = "undo hwtacacs server authorization host host-name %s" % hwtacacs_server_host_name
            if hwtacacs_vpn_name and hwtacacs_vpn_name != "_public_":
                cmd += " vpn-instance %s" % hwtacacs_vpn_name
            if hwtacacs_is_public_net:
                cmd += " public-net"
            if hwtacacs_is_secondary_server:
                cmd += " secondary"

        elif hwtacacs_server_type == "Accounting":
            cmd = "undo hwtacacs server accounting host host-name %s" % hwtacacs_server_host_name
            if hwtacacs_vpn_name and hwtacacs_vpn_name != "_public_":
                cmd += " vpn-instance %s" % hwtacacs_vpn_name
            if hwtacacs_is_public_net:
                cmd += " public-net"
            if hwtacacs_is_secondary_server:
                cmd += " secondary"

        elif hwtacacs_server_type == "Common":
            cmd = "undo hwtacacs server host host-name %s" % hwtacacs_server_host_name
            if hwtacacs_vpn_name and hwtacacs_vpn_name != "_public_":
                cmd += " vpn-instance %s" % hwtacacs_vpn_name
            if hwtacacs_is_public_net:
                cmd += " public-net"
            if hwtacacs_is_secondary_server:
                cmd += " secondary"

        cmds.append(cmd)
        return cmds


def check_name(**kwargs):
    """ Check invalid name """

    module = kwargs["module"]
    name = kwargs["name"]
    invalid_char = kwargs["invalid_char"]

    for item in invalid_char:
        if item in name:
            module.fail_json(
                msg='Error: Invalid char %s is in the name %s ' % (item, name))


def check_module_argument(**kwargs):
    """ Check module argument """

    module = kwargs["module"]

    # local para
    local_user_name = module.params['local_user_name']
    local_password = module.params['local_password']
    local_ftp_dir = module.params['local_ftp_dir']
    local_user_level = module.params['local_user_level']
    local_user_group = module.params['local_user_group']

    # radius para
    radius_group_name = module.params['radius_group_name']
    radius_server_ip = module.params['radius_server_ip']
    radius_server_port = module.params['radius_server_port']
    radius_vpn_name = module.params['radius_vpn_name']
    radius_server_name = module.params['radius_server_name']

    # hwtacacs para
    hwtacacs_template = module.params['hwtacacs_template']
    hwtacacs_server_ip = module.params['hwtacacs_server_ip']
    hwtacacs_vpn_name = module.params['hwtacacs_vpn_name']
    hwtacacs_server_host_name = module.params['hwtacacs_server_host_name']

    if local_user_name:
        if len(local_user_name) > 253:
            module.fail_json(
                msg='Error: The local_user_name %s is large than 253.' % local_user_name)
        check_name(module=module, name=local_user_name,
                   invalid_char=INVALID_USER_NAME_CHAR)

    if local_password and len(local_password) > 255:
        module.fail_json(
            msg='Error: The local_password %s is large than 255.' % local_password)

    if local_user_level:
        if int(local_user_level) > 15 or int(local_user_level) < 0:
            module.fail_json(
                msg='Error: The local_user_level %s is out of [0 - 15].' % local_user_level)

    if local_ftp_dir:
        if len(local_ftp_dir) > 255:
            module.fail_json(
                msg='Error: The local_ftp_dir %s is large than 255.' % local_ftp_dir)

    if local_user_group:
        if len(local_user_group) > 32 or len(local_user_group) < 1:
            module.fail_json(
                msg='Error: The local_user_group %s is out of [1 - 32].' % local_user_group)

    if radius_group_name and len(radius_group_name) > 32:
        module.fail_json(
            msg='Error: The radius_group_name %s is large than 32.' % radius_group_name)

    if radius_server_ip and not check_ip_addr(radius_server_ip):
        module.fail_json(
            msg='Error: The radius_server_ip %s is invalid.' % radius_server_ip)

    if radius_server_port and not radius_server_port.isdigit():
        module.fail_json(
            msg='Error: The radius_server_port %s is invalid.' % radius_server_port)

    if radius_vpn_name:
        if len(radius_vpn_name) > 31:
            module.fail_json(
                msg='Error: The radius_vpn_name %s is large than 31.' % radius_vpn_name)
        if ' ' in radius_vpn_name:
            module.fail_json(
                msg='Error: The radius_vpn_name %s include space.' % radius_vpn_name)

    if radius_server_name:
        if len(radius_server_name) > 255:
            module.fail_json(
                msg='Error: The radius_server_name %s is large than 255.' % radius_server_name)
        if ' ' in radius_server_name:
            module.fail_json(
                msg='Error: The radius_server_name %s include space.' % radius_server_name)

    if hwtacacs_template and len(hwtacacs_template) > 32:
        module.fail_json(
            msg='Error: The hwtacacs_template %s is large than 32.' % hwtacacs_template)

    if hwtacacs_server_ip and not check_ip_addr(hwtacacs_server_ip):
        module.fail_json(
            msg='Error: The hwtacacs_server_ip %s is invalid.' % hwtacacs_server_ip)

    if hwtacacs_vpn_name:
        if len(hwtacacs_vpn_name) > 31:
            module.fail_json(
                msg='Error: The hwtacacs_vpn_name %s is large than 31.' % hwtacacs_vpn_name)
        if ' ' in hwtacacs_vpn_name:
            module.fail_json(
                msg='Error: The hwtacacs_vpn_name %s include space.' % hwtacacs_vpn_name)

    if hwtacacs_server_host_name:
        if len(hwtacacs_server_host_name) > 255:
            module.fail_json(
                msg='Error: The hwtacacs_server_host_name %s is large than 255.' % hwtacacs_server_host_name)
        if ' ' in hwtacacs_server_host_name:
            module.fail_json(
                msg='Error: The hwtacacs_server_host_name %s include space.' % hwtacacs_server_host_name)


def main():
    """ Module main """

    argument_spec = dict(
        state=dict(choices=['present', 'absent'], default='present'),
        local_user_name=dict(type='str'),
        local_password=dict(type='str', no_log=True),
        local_service_type=dict(type='str'),
        local_ftp_dir=dict(type='str'),
        local_user_level=dict(type='str'),
        local_user_group=dict(type='str'),
        radius_group_name=dict(type='str'),
        raduis_server_type=dict(choices=['Authentication', 'Accounting']),
        radius_server_ip=dict(type='str'),
        radius_server_ipv6=dict(type='str'),
        radius_server_port=dict(type='str'),
        radius_server_mode=dict(
            choices=['Secondary-server', 'Primary-server']),
        radius_vpn_name=dict(type='str'),
        radius_server_name=dict(type='str'),
        hwtacacs_template=dict(type='str'),
        hwtacacs_server_ip=dict(type='str'),
        hwtacacs_server_ipv6=dict(type='str'),
        hwtacacs_server_type=dict(
            choices=['Authentication', 'Authorization', 'Accounting', 'Common']),
        hwtacacs_is_secondary_server=dict(
            required=False, default=False, type='bool'),
        hwtacacs_vpn_name=dict(type='str'),
        hwtacacs_is_public_net=dict(
            required=False, default=False, type='bool'),
        hwtacacs_server_host_name=dict(type='str')
    )

    argument_spec.update(ce_argument_spec)

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True)

    check_module_argument(module=module)

    changed = False
    proposed = dict()
    existing = dict()
    end_state = dict()
    updates = []

    # common para
    state = module.params['state']

    # local para
    local_user_name = module.params['local_user_name']
    local_password = module.params['local_password']
    local_service_type = module.params['local_service_type']
    local_ftp_dir = module.params['local_ftp_dir']
    local_user_level = module.params['local_user_level']
    local_user_group = module.params['local_user_group']

    # radius para
    radius_group_name = module.params['radius_group_name']
    raduis_server_type = module.params['raduis_server_type']
    radius_server_ip = module.params['radius_server_ip']
    radius_server_ipv6 = module.params['radius_server_ipv6']
    radius_server_port = module.params['radius_server_port']
    radius_server_mode = module.params['radius_server_mode']
    radius_vpn_name = module.params['radius_vpn_name']
    radius_server_name = module.params['radius_server_name']

    # hwtacacs para
    hwtacacs_template = module.params['hwtacacs_template']
    hwtacacs_server_ip = module.params['hwtacacs_server_ip']
    hwtacacs_server_ipv6 = module.params['hwtacacs_server_ipv6']
    hwtacacs_server_type = module.params['hwtacacs_server_type']
    hwtacacs_is_secondary_server = module.params[
        'hwtacacs_is_secondary_server']
    hwtacacs_vpn_name = module.params['hwtacacs_vpn_name']
    hwtacacs_is_public_net = module.params['hwtacacs_is_public_net']
    hwtacacs_server_host_name = module.params['hwtacacs_server_host_name']

    ce_aaa_server_host = AaaServerHost()

    if not ce_aaa_server_host:
        module.fail_json(msg='Error: Construct ce_aaa_server failed.')

    # get proposed
    proposed["state"] = state
    if local_user_name:
        proposed["local_user_name"] = local_user_name
    if local_password:
        proposed["local_password"] = "******"
    if local_service_type:
        proposed["local_service_type"] = local_service_type
    if local_ftp_dir:
        proposed["local_ftp_dir"] = local_ftp_dir
    if local_user_level:
        proposed["local_user_level"] = local_user_level
    if local_user_group:
        proposed["local_user_group"] = local_user_group
    if radius_group_name:
        proposed["radius_group_name"] = radius_group_name
    if raduis_server_type:
        proposed["raduis_server_type"] = raduis_server_type
    if radius_server_ip:
        proposed["radius_server_ip"] = radius_server_ip
    if radius_server_ipv6:
        proposed["radius_server_ipv6"] = radius_server_ipv6
    if radius_server_port:
        proposed["radius_server_port"] = radius_server_port
    if radius_server_mode:
        proposed["radius_server_mode"] = radius_server_mode
    if radius_vpn_name:
        proposed["radius_vpn_name"] = radius_vpn_name
    if radius_server_name:
        proposed["radius_server_name"] = radius_server_name
    if hwtacacs_template:
        proposed["hwtacacs_template"] = hwtacacs_template
    if hwtacacs_server_ip:
        proposed["hwtacacs_server_ip"] = hwtacacs_server_ip
    if hwtacacs_server_ipv6:
        proposed["hwtacacs_server_ipv6"] = hwtacacs_server_ipv6
    if hwtacacs_server_type:
        proposed["hwtacacs_server_type"] = hwtacacs_server_type
    proposed["hwtacacs_is_secondary_server"] = hwtacacs_is_secondary_server
    if hwtacacs_vpn_name:
        proposed["hwtacacs_vpn_name"] = hwtacacs_vpn_name
    proposed["hwtacacs_is_public_net"] = hwtacacs_is_public_net
    if hwtacacs_server_host_name:
        proposed["hwtacacs_server_host_name"] = hwtacacs_server_host_name

    if local_user_name:

        if state == "present" and not local_password:
            module.fail_json(
                msg='Error: Please input local_password when config local user.')

        local_user_result = ce_aaa_server_host.get_local_user_info(
            module=module)
        existing["local user name"] = local_user_result["local_user_info"]

        if state == "present":
            # present local user
            if local_user_result["need_cfg"]:
                cmd = ce_aaa_server_host.merge_local_user_info(module=module)

                changed = True
                updates.append(cmd)

        else:
            # absent local user
            if local_user_result["need_cfg"]:
                if not local_service_type and not local_ftp_dir and not local_user_level and not local_user_group:
                    cmd = ce_aaa_server_host.delete_local_user_info(
                        module=module)
                else:
                    cmd = ce_aaa_server_host.merge_local_user_info(
                        module=module)

                changed = True
                updates.append(cmd)

        local_user_result = ce_aaa_server_host.get_local_user_info(
            module=module)
        end_state["local user name"] = local_user_result["local_user_info"]

    if radius_group_name:

        if not radius_server_ip and not radius_server_ipv6 and not radius_server_name:
            module.fail_json(
                msg='Error: Please input radius_server_ip or radius_server_ipv6 or radius_server_name.')

        if radius_server_ip and radius_server_ipv6:
            module.fail_json(
                msg='Error: Please do not input radius_server_ip and radius_server_ipv6 at the same time.')

        if not raduis_server_type or not radius_server_port or not radius_server_mode or not radius_vpn_name:
            module.fail_json(
                msg='Error: Please input raduis_server_type radius_server_port radius_server_mode radius_vpn_name.')

        if radius_server_ip:
            rds_server_ipv4_result = ce_aaa_server_host.get_radius_server_cfg_ipv4(
                module=module)
        if radius_server_ipv6:
            rds_server_ipv6_result = ce_aaa_server_host.get_radius_server_cfg_ipv6(
                module=module)
        if radius_server_name:
            rds_server_name_result = ce_aaa_server_host.get_radius_server_name(
                module=module)

        if radius_server_ip and rds_server_ipv4_result["radius_server_ip_v4"]:
            existing["radius server ipv4"] = rds_server_ipv4_result[
                "radius_server_ip_v4"]
        if radius_server_ipv6 and rds_server_ipv6_result["radius_server_ip_v6"]:
            existing["radius server ipv6"] = rds_server_ipv6_result[
                "radius_server_ip_v6"]
        if radius_server_name and rds_server_name_result["radius_server_name_cfg"]:
            existing["radius server name cfg"] = rds_server_name_result[
                "radius_server_name_cfg"]

        if state == "present":
            if radius_server_ip and rds_server_ipv4_result["need_cfg"]:
                cmd = ce_aaa_server_host.merge_radius_server_cfg_ipv4(
                    module=module)
                changed = True
                updates.append(cmd)

            if radius_server_ipv6 and rds_server_ipv6_result["need_cfg"]:
                cmd = ce_aaa_server_host.merge_radius_server_cfg_ipv6(
                    module=module)
                changed = True
                updates.append(cmd)

            if radius_server_name and rds_server_name_result["need_cfg"]:
                cmd = ce_aaa_server_host.merge_radius_server_name(
                    module=module)
                changed = True
                updates.append(cmd)
        else:
            if radius_server_ip and rds_server_ipv4_result["need_cfg"]:
                cmd = ce_aaa_server_host.delete_radius_server_cfg_ipv4(
                    module=module)
                changed = True
                updates.append(cmd)

            if radius_server_ipv6 and rds_server_ipv6_result["need_cfg"]:
                cmd = ce_aaa_server_host.delete_radius_server_cfg_ipv6(
                    module=module)
                changed = True
                updates.append(cmd)

            if radius_server_name and rds_server_name_result["need_cfg"]:
                cmd = ce_aaa_server_host.delete_radius_server_name(
                    module=module)
                changed = True
                updates.append(cmd)

        if radius_server_ip:
            rds_server_ipv4_result = ce_aaa_server_host.get_radius_server_cfg_ipv4(
                module=module)
        if radius_server_ipv6:
            rds_server_ipv6_result = ce_aaa_server_host.get_radius_server_cfg_ipv6(
                module=module)
        if radius_server_name:
            rds_server_name_result = ce_aaa_server_host.get_radius_server_name(
                module=module)

        if radius_server_ip and rds_server_ipv4_result["radius_server_ip_v4"]:
            end_state["radius server ipv4"] = rds_server_ipv4_result[
                "radius_server_ip_v4"]
        if radius_server_ipv6 and rds_server_ipv6_result["radius_server_ip_v6"]:
            end_state["radius server ipv6"] = rds_server_ipv6_result[
                "radius_server_ip_v6"]
        if radius_server_name and rds_server_name_result["radius_server_name_cfg"]:
            end_state["radius server name cfg"] = rds_server_name_result[
                "radius_server_name_cfg"]

    if hwtacacs_template:

        if not hwtacacs_server_ip and not hwtacacs_server_ipv6 and not hwtacacs_server_host_name:
            module.fail_json(
                msg='Error: Please input hwtacacs_server_ip or hwtacacs_server_ipv6 or hwtacacs_server_host_name.')

        if not hwtacacs_server_type or not hwtacacs_vpn_name:
            module.fail_json(
                msg='Error: Please input hwtacacs_server_type hwtacacs_vpn_name.')

        if hwtacacs_server_ip and hwtacacs_server_ipv6:
            module.fail_json(
                msg='Error: Please do not set hwtacacs_server_ip and hwtacacs_server_ipv6 at the same time.')

        if hwtacacs_vpn_name and hwtacacs_is_public_net:
            module.fail_json(
                msg='Error: Please do not set vpn and public net at the same time.')

        if hwtacacs_server_ip:
            hwtacacs_server_ipv4_result = ce_aaa_server_host.get_hwtacacs_server_cfg_ipv4(
                module=module)
        if hwtacacs_server_ipv6:
            hwtacacs_server_ipv6_result = ce_aaa_server_host.get_hwtacacs_server_cfg_ipv6(
                module=module)
        if hwtacacs_server_host_name:
            hwtacacs_host_name_result = ce_aaa_server_host.get_hwtacacs_host_server_cfg(
                module=module)

        if hwtacacs_server_ip and hwtacacs_server_ipv4_result["hwtacacs_server_cfg_ipv4"]:
            existing["hwtacacs server cfg ipv4"] = hwtacacs_server_ipv4_result[
                "hwtacacs_server_cfg_ipv4"]
        if hwtacacs_server_ipv6 and hwtacacs_server_ipv6_result["hwtacacs_server_cfg_ipv6"]:
            existing["hwtacacs server cfg ipv6"] = hwtacacs_server_ipv6_result[
                "hwtacacs_server_cfg_ipv6"]
        if hwtacacs_server_host_name and hwtacacs_host_name_result["hwtacacs_server_name_cfg"]:
            existing["hwtacacs server name cfg"] = hwtacacs_host_name_result[
                "hwtacacs_server_name_cfg"]

        if state == "present":
            if hwtacacs_server_ip and hwtacacs_server_ipv4_result["need_cfg"]:
                cmd = ce_aaa_server_host.merge_hwtacacs_server_cfg_ipv4(
                    module=module)
                changed = True
                updates.append(cmd)

            if hwtacacs_server_ipv6 and hwtacacs_server_ipv6_result["need_cfg"]:
                cmd = ce_aaa_server_host.merge_hwtacacs_server_cfg_ipv6(
                    module=module)
                changed = True
                updates.append(cmd)

            if hwtacacs_server_host_name and hwtacacs_host_name_result["need_cfg"]:
                cmd = ce_aaa_server_host.merge_hwtacacs_host_server_cfg(
                    module=module)
                changed = True
                updates.append(cmd)

        else:
            if hwtacacs_server_ip and hwtacacs_server_ipv4_result["need_cfg"]:
                cmd = ce_aaa_server_host.delete_hwtacacs_server_cfg_ipv4(
                    module=module)
                changed = True
                updates.append(cmd)

            if hwtacacs_server_ipv6 and hwtacacs_server_ipv6_result["need_cfg"]:
                cmd = ce_aaa_server_host.delete_hwtacacs_server_cfg_ipv6(
                    module=module)
                changed = True
                updates.append(cmd)

            if hwtacacs_server_host_name and hwtacacs_host_name_result["need_cfg"]:
                cmd = ce_aaa_server_host.delete_hwtacacs_host_server_cfg(
                    module=module)
                changed = True
                updates.append(cmd)

        if hwtacacs_server_ip:
            hwtacacs_server_ipv4_result = ce_aaa_server_host.get_hwtacacs_server_cfg_ipv4(
                module=module)
        if hwtacacs_server_ipv6:
            hwtacacs_server_ipv6_result = ce_aaa_server_host.get_hwtacacs_server_cfg_ipv6(
                module=module)
        if hwtacacs_server_host_name:
            hwtacacs_host_name_result = ce_aaa_server_host.get_hwtacacs_host_server_cfg(
                module=module)

        if hwtacacs_server_ip and hwtacacs_server_ipv4_result["hwtacacs_server_cfg_ipv4"]:
            end_state["hwtacacs server cfg ipv4"] = hwtacacs_server_ipv4_result[
                "hwtacacs_server_cfg_ipv4"]
        if hwtacacs_server_ipv6 and hwtacacs_server_ipv6_result["hwtacacs_server_cfg_ipv6"]:
            end_state["hwtacacs server cfg ipv6"] = hwtacacs_server_ipv6_result[
                "hwtacacs_server_cfg_ipv6"]
        if hwtacacs_server_host_name and hwtacacs_host_name_result["hwtacacs_server_name_cfg"]:
            end_state["hwtacacs server name cfg"] = hwtacacs_host_name_result[
                "hwtacacs_server_name_cfg"]

    results = dict()
    results['proposed'] = proposed
    results['existing'] = existing
    results['changed'] = changed
    results['end_state'] = end_state
    results['updates'] = updates

    module.exit_json(**results)


if __name__ == '__main__':
    main()
