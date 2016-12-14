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

DOCUMENTATION = '''
---

module: ce_aaa_server
version_added: "2.2"
short_description: Manages AAA server global configuration.
description:
    - Manages AAA server global configuration
extends_documentation_fragment: cloudengine
author:
    - wangdezhuang (@CloudEngine-Ansible)
notes:
    - The server_type parameter is always required.
options:
    state:
        description:
            - Manage the state of the resource.
        required: true
        default: present
        choices: ['present','absent']
    local_user_name:
        description:
            - local user name when use local scheme.
        required: false
        default: null
    local_password:
        description:
            - local user password when use local scheme.
        required: false
        default: null
    radius_group_name:
        description:
            - radius group name.
        required: false
        default: null
    raduis_server_type:
        description:
            - raduis server type.
        required: false
        default: null
        choices: ['Authentication', 'Accounting']
    radius_server_ip:
        description:
            - radius server ip.
        required: false
        default: null
    radius_server_ipv6:
        description:
            - radius server ipv6.
        required: false
        default: null
    radius_server_port:
        description:
            - radius server port.
        required: false
        default: null
    radius_server_mode:
        description:
            - radius server mode.
        required: false
        default: null
        choices: ['Secondary-server', 'Primary-server']
    radius_vpn_name:
        description:
            - radius vpn name.
        required: false
        default: null
    radius_server_name:
        description:
            - radius server name.
        required: false
        default: null
    hwtacacs_template:
        description:
            - hwtacacs template.
        required: false
        default: null
    hwtacacs_server_ip:
        description:
            - hwtacacs server ip.
        required: false
        default: null
    hwtacacs_server_ipv6:
        description:
            - hwtacacs server ipv6.
        required: false
        default: null
    hwtacacs_server_type:
        description:
            - hwtacacs server type.
        required: false
        default: null
        choices: ['Authentication', 'Authorization', 'Accounting', 'Common']
    hwtacacs_is_secondary_server:
        description:
            - hwtacacs server type.
        required: false
        default: 'true'
        choices: ['true', 'false']
    hwtacacs_vpn_name:
        description:
            - hwtacacs vpn name.
        required: false
        default: null
    hwtacacs_is_public_net:
        description:
            - hwtacacs server type.
        required: false
        default: 'false'
        choices: ['true', 'false']
    hwtacacs_server_host_name:
        description:
            - hwtacacs server host name.
        required: false
        default: null
'''

EXAMPLES = '''
# config local user when use local scheme
  - name: "config local user when use local scheme"
    ce_aaa_server_host:
        state:  present
        local_user_name:  user1
        local_password:  123456
        host:  {{inventory_hostname}}
        port:  {{ansible_ssh_port}}
        username:  {{username}}
        password:  {{password}}

# undo local user when use local scheme
  - name: "undo local user when use local scheme"
    ce_aaa_server_host:
        state:  absent
        local_user_name:  user1
        local_password:  123456
        host:  {{inventory_hostname}}
        port:  {{ansible_ssh_port}}
        username:  {{username}}
        password:  {{password}}

# config radius server ip
  - name: "config radius server ip"
    ce_aaa_server_host:
        state:  present
        radius_group_name:  group1
        raduis_server_type:  Authentication
        radius_server_ip:  10.1.10.1
        radius_server_port:  2000
        radius_server_mode:  Primary-server
        radius_vpn_name:  _public_
        host:  {{inventory_hostname}}
        port:  {{ansible_ssh_port}}
        username:  {{username}}
        password:  {{password}}

# config hwtacacs server ip
  - name: "config hwtacacs server ip"
    ce_aaa_server_host:
        state:  present
        hwtacacs_template:  template
        hwtacacs_server_ip:  10.10.10.10
        hwtacacs_server_type:  Authorization
        hwtacacs_vpn_name:  _public_
        host:  {{inventory_hostname}}
        port:  {{ansible_ssh_port}}
        username:  {{username}}
        password:  {{password}}
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
             "hwtacacs_is_secondary_server": "true",
             "local_password": "******",
             "radius_group_name": "group1",
             "radius_server_ip": "10.1.10.1",
             "radius_server_mode": "Primary-server",
             "radius_server_port": "2000",
             "radius_vpn_name": "_public_",
             "raduis_server_type": "Authentication",
             "state": "present"}
existing:
    description:
        - k/v pairs of existing aaa server host
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
execute_time:
    description: the module execute time
    returned: always
    type: string
    sample: "0:00:03.380753"
'''

import re
import datetime
from ansible.module_utils.network import NetworkModule
from ansible.module_utils.cloudengine import get_netconf

HAS_NCCLIENT = False
try:
    from ncclient.operations.rpc import RPCError
    HAS_NCCLIENT = True
except ImportError:
    HAS_NCCLIENT = False


SUCCESS = """success"""
FAILED = """failed"""

INVALID_USER_NAME_CHAR = [' ', '/', '\\',
                          ':', '*', '?', '"', '\'', '<', '>', '\%']

# get local user name
CE_GET_LOCAL_USER_INFO = """
    <filter type="subtree">
      <aaa xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <lam>
          <users>
            <user>
              <userName></userName>
              <password></password>
            </user>
          </users>
        </lam>
      </aaa>
    </filter>
"""

# merge local user name
CE_MERGE_LOCAL_USER_INFO = """
    <config>
      <aaa xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <lam>
          <users>
            <user operation="merge">
              <userName>%s</userName>
              <password>%s</password>
            </user>
          </users>
        </lam>
      </aaa>
    </config>
"""

# create local user name
CE_CREATE_LOCAL_USER_INFO = """
    <config>
      <aaa xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <lam>
          <users>
            <user operation="create">
              <userName>%s</userName>
              <password>%s</password>
            </user>
          </users>
        </lam>
      </aaa>
    </config>
"""

# delete local user name
CE_DELETE_LOCAL_USER_INFO = """
    <config>
      <aaa xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <lam>
          <users>
            <user operation="delete">
              <userName>%s</userName>
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

# create radius server config ipv4
CE_CREATE_RADIUS_SERVER_CFG_IPV4 = """
    <config>
      <radius xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <rdsTemplates>
          <rdsTemplate>
            <groupName>%s</groupName>
            <rdsServerIPV4s>
              <rdsServerIPV4 operation="create">
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

# create radius server config ipv6
CE_CREATE_RADIUS_SERVER_CFG_IPV6 = """
    <config>
      <radius xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <rdsTemplates>
          <rdsTemplate>
            <groupName>%s</groupName>
            <rdsServerIPV6s>
              <rdsServerIPV6 operation="create">
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

# create radius server name
CE_CREATE_RADIUS_SERVER_NAME = """
    <config>
      <radius xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <rdsTemplates>
          <rdsTemplate>
            <groupName>%s</groupName>
            <rdsServerNames>
              <rdsServerName operation="create">
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

# create hwtacacs server config ipv4
CE_CREATE_HWTACACS_SERVER_CFG_IPV4 = """
    <config>
      <hwtacacs xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <hwTacTempCfgs>
          <hwTacTempCfg>
            <templateName>%s</templateName>
            <hwTacSrvCfgs>
              <hwTacSrvCfg operation="create">
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

# create hwtacacs server config ipv6
CE_CREATE_HWTACACS_SERVER_CFG_IPV6 = """
    <config>
      <hwtacacs xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <hwTacTempCfgs>
          <hwTacTempCfg>
            <templateName>%s</templateName>
            <hwTacIpv6SrvCfgs>
              <hwTacIpv6SrvCfg operation="create">
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

# create hwtacacs host server config
CE_CREATE_HWTACACS_HOST_SERVER_CFG = """
    <config>
      <hwtacacs xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <hwTacTempCfgs>
          <hwTacTempCfg>
            <templateName>%s</templateName>
            <hwTacHostSrvCfgs>
              <hwTacHostSrvCfg operation="create">
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


class ce_aaa_server_host(object):
    """ ce_aaa_server_host """

    def __init__(self, **kwargs):
        """ __init__ """

        self.netconf = get_netconf(**kwargs)

    def netconf_get_config(self, **kwargs):
        """ netconf_get_config """

        module = kwargs["module"]
        conf_str = kwargs["conf_str"]

        try:
            con_obj = self.netconf.get_config(filter=conf_str)
        except RPCError as e:
            module.fail_json(msg='Error: %s' % e.message)

        return con_obj

    def netconf_set_config(self, **kwargs):
        """ netconf_set_config """

        module = kwargs["module"]
        conf_str = kwargs["conf_str"]

        try:
            con_obj = self.netconf.set_config(config=conf_str)
        except RPCError as e:
            module.fail_json(msg='Error: %s' % e.message)

        return con_obj

    def get_local_user_info(self, **kwargs):
        """ netconf_set_config """

        module = kwargs["module"]
        conf_str = CE_GET_LOCAL_USER_INFO

        con_obj = self.netconf_get_config(module=module,
                                          conf_str=conf_str)

        xml_str = con_obj.xml
        result = list()

        if "<data/>" in xml_str:
            return result
        else:
            re_find = re.findall(
                r'.*<userName>(.*)</userName>.*', xml_str)

            if re_find:
                return re_find
            else:
                return result

    def merge_local_user_info(self, **kwargs):
        """ merge_local_user_info """

        module = kwargs["module"]
        local_user_name = kwargs["local_user_name"]
        local_password = kwargs["local_password"]
        conf_str = CE_MERGE_LOCAL_USER_INFO % (local_user_name,
                                               local_password)

        con_obj = self.netconf_set_config(module=module,
                                          conf_str=conf_str)

        if "<ok/>" not in con_obj.xml:
            module.fail_json(msg='merge local user info failed.')

        return SUCCESS

    def create_local_user_info(self, **kwargs):
        """ create_local_user_info """

        module = kwargs["module"]
        local_user_name = kwargs["local_user_name"]
        local_password = kwargs["local_password"]
        conf_str = CE_CREATE_LOCAL_USER_INFO % (
            local_user_name, local_password)

        con_obj = self.netconf_set_config(module=module,
                                          conf_str=conf_str)

        if "<ok/>" not in con_obj.xml:
            module.fail_json(msg='create local user info failed.')

        return SUCCESS

    def delete_local_user_info(self, **kwargs):
        """ delete_local_user_info """

        module = kwargs["module"]
        local_user_name = kwargs["local_user_name"]
        conf_str = CE_DELETE_LOCAL_USER_INFO % local_user_name

        con_obj = self.netconf_set_config(module=module,
                                          conf_str=conf_str)

        if "<ok/>" not in con_obj.xml:
            module.fail_json(msg='delete local user info failed.')

        return SUCCESS

    def get_radius_server_cfg_ipv4(self, **kwargs):
        """ get_radius_server_cfg_ipv4 """

        module = kwargs["module"]
        radius_group_name = kwargs["radius_group_name"]
        conf_str = CE_GET_RADIUS_SERVER_CFG_IPV4 % radius_group_name

        con_obj = self.netconf_get_config(module=module,
                                          conf_str=conf_str)

        xml_str = con_obj.xml
        result = list()

        if "<data/>" in xml_str:
            return result
        else:
            re_find = re.findall(
                r'.*<serverIPAddress>(.*)</serverIPAddress>.*\s*'
                r'<serverType>(.*)</serverType>.*\s*'
                r'<serverPort>(.*)</serverPort>.*\s*'
                r'<serverMode>(.*)</serverMode>.*\s*'
                r'<vpnName>(.*)</vpnName>.*', xml_str)

            if re_find:
                return re_find
            else:
                return result

    def merge_radius_server_cfg_ipv4(self, **kwargs):
        """ merge_radius_server_cfg_ipv4 """

        module = kwargs["module"]
        radius_group_name = kwargs["radius_group_name"]
        raduis_server_type = kwargs["raduis_server_type"]
        radius_server_ip = kwargs["radius_server_ip"]
        radius_server_port = kwargs["radius_server_port"]
        radius_server_mode = kwargs["radius_server_mode"]
        radius_vpn_name = kwargs["radius_vpn_name"]

        conf_str = CE_MERGE_RADIUS_SERVER_CFG_IPV4 % (
            radius_group_name, raduis_server_type,
            radius_server_ip, radius_server_port,
            radius_server_mode, radius_vpn_name)

        con_obj = self.netconf_set_config(module=module,
                                          conf_str=conf_str)

        if "<ok/>" not in con_obj.xml:
            module.fail_json(msg='merge radius server config ipv4 failed.')

        return SUCCESS

    def create_radius_server_cfg_ipv4(self, **kwargs):
        """ create_radius_server_cfg_ipv4 """

        module = kwargs["module"]
        radius_group_name = kwargs["radius_group_name"]
        raduis_server_type = kwargs["raduis_server_type"]
        radius_server_ip = kwargs["radius_server_ip"]
        radius_server_port = kwargs["radius_server_port"]
        radius_server_mode = kwargs["radius_server_mode"]
        radius_vpn_name = kwargs["radius_vpn_name"]

        conf_str = CE_CREATE_RADIUS_SERVER_CFG_IPV4 % (
            radius_group_name, raduis_server_type,
            radius_server_ip, radius_server_port,
            radius_server_mode, radius_vpn_name)

        con_obj = self.netconf_set_config(module=module,
                                          conf_str=conf_str)

        if "<ok/>" not in con_obj.xml:
            module.fail_json(msg='create radius server config ipv4 failed.')

        return SUCCESS

    def delete_radius_server_cfg_ipv4(self, **kwargs):
        """ delete_radius_server_cfg_ipv4 """

        module = kwargs["module"]
        radius_group_name = kwargs["radius_group_name"]
        raduis_server_type = kwargs["raduis_server_type"]
        radius_server_ip = kwargs["radius_server_ip"]
        radius_server_port = kwargs["radius_server_port"]
        radius_server_mode = kwargs["radius_server_mode"]
        radius_vpn_name = kwargs["radius_vpn_name"]

        conf_str = CE_DELETE_RADIUS_SERVER_CFG_IPV4 % (
            radius_group_name, raduis_server_type,
            radius_server_ip, radius_server_port,
            radius_server_mode, radius_vpn_name)

        con_obj = self.netconf_set_config(module=module,
                                          conf_str=conf_str)

        if "<ok/>" not in con_obj.xml:
            module.fail_json(msg='create radius server config ipv4 failed.')

        return SUCCESS

    def get_radius_server_cfg_ipv6(self, **kwargs):
        """ get_radius_server_cfg_ipv6 """

        module = kwargs["module"]
        radius_group_name = kwargs["radius_group_name"]
        conf_str = CE_GET_RADIUS_SERVER_CFG_IPV6 % radius_group_name

        con_obj = self.netconf_get_config(module=module,
                                          conf_str=conf_str)

        xml_str = con_obj.xml
        result = list()

        if "<data/>" in xml_str:
            return result
        else:
            re_find = re.findall(
                r'.*<serverIPAddress>(.*)</serverIPAddress>.*\s*'
                r'<serverType>(.*)</serverType>.*\s*'
                r'<serverPort>(.*)</serverPort>.*\s*'
                r'<serverMode>(.*)</serverMode>.*', xml_str)

            if re_find:
                return re_find
            else:
                return result

    def merge_radius_server_cfg_ipv6(self, **kwargs):
        """ merge_radius_server_cfg_ipv6 """

        module = kwargs["module"]
        radius_group_name = kwargs["radius_group_name"]
        raduis_server_type = kwargs["raduis_server_type"]
        radius_server_ipv6 = kwargs["radius_server_ipv6"]
        radius_server_port = kwargs["radius_server_port"]
        radius_server_mode = kwargs["radius_server_mode"]

        conf_str = CE_MERGE_RADIUS_SERVER_CFG_IPV6 % (
            radius_group_name, raduis_server_type,
            radius_server_ipv6, radius_server_port,
            radius_server_mode)

        con_obj = self.netconf_set_config(module=module,
                                          conf_str=conf_str)

        if "<ok/>" not in con_obj.xml:
            module.fail_json(msg='merge radius server config ipv6 failed.')

        return SUCCESS

    def create_radius_server_cfg_ipv6(self, **kwargs):
        """ create_radius_server_cfg_ipv6 """

        module = kwargs["module"]
        radius_group_name = kwargs["radius_group_name"]
        raduis_server_type = kwargs["raduis_server_type"]
        radius_server_ipv6 = kwargs["radius_server_ipv6"]
        radius_server_port = kwargs["radius_server_port"]
        radius_server_mode = kwargs["radius_server_mode"]

        conf_str = CE_CREATE_RADIUS_SERVER_CFG_IPV6 % (
            radius_group_name, raduis_server_type,
            radius_server_ipv6, radius_server_port,
            radius_server_mode)

        con_obj = self.netconf_set_config(module=module,
                                          conf_str=conf_str)

        if "<ok/>" not in con_obj.xml:
            module.fail_json(msg='create radius server config ipv6 failed.')

        return SUCCESS

    def delete_radius_server_cfg_ipv6(self, **kwargs):
        """ delete_radius_server_cfg_ipv6 """

        module = kwargs["module"]
        radius_group_name = kwargs["radius_group_name"]
        raduis_server_type = kwargs["raduis_server_type"]
        radius_server_ipv6 = kwargs["radius_server_ipv6"]
        radius_server_port = kwargs["radius_server_port"]
        radius_server_mode = kwargs["radius_server_mode"]

        conf_str = CE_DELETE_RADIUS_SERVER_CFG_IPV6 % (
            radius_group_name, raduis_server_type,
            radius_server_ipv6, radius_server_port,
            radius_server_mode)

        con_obj = self.netconf_set_config(module=module, conf_str=conf_str)

        if "<ok/>" not in con_obj.xml:
            module.fail_json(msg='create radius server config ipv6 failed.')

        return SUCCESS

    def get_radius_server_name(self, **kwargs):
        """ get_radius_server_name """

        module = kwargs["module"]
        radius_group_name = kwargs["radius_group_name"]
        conf_str = CE_GET_RADIUS_SERVER_NAME % radius_group_name

        con_obj = self.netconf_get_config(module=module,
                                          conf_str=conf_str)

        xml_str = con_obj.xml
        result = list()

        if "<data/>" in xml_str:
            return result
        else:
            re_find = re.findall(
                r'.*<serverName>(.*)</serverName>.*\s*'
                r'<serverType>(.*)</serverType>.*\s*'
                r'<serverPort>(.*)</serverPort>.*\s*'
                r'<serverMode>(.*)</serverMode>.*\s*'
                r'<vpnName>(.*)</vpnName>.*', xml_str)

            if re_find:
                return re_find
            else:
                return result

    def merge_radius_server_name(self, **kwargs):
        """ merge_radius_server_name """

        module = kwargs["module"]
        radius_group_name = kwargs["radius_group_name"]
        raduis_server_type = kwargs["raduis_server_type"]
        radius_server_name = kwargs["radius_server_name"]
        radius_server_port = kwargs["radius_server_port"]
        radius_server_mode = kwargs["radius_server_mode"]
        radius_vpn_name = kwargs["radius_vpn_name"]

        conf_str = CE_MERGE_RADIUS_SERVER_NAME % (
            radius_group_name, raduis_server_type,
            radius_server_name, radius_server_port,
            radius_server_mode, radius_vpn_name)

        con_obj = self.netconf_set_config(module=module,
                                          conf_str=conf_str)

        if "<ok/>" not in con_obj.xml:
            module.fail_json(msg='merge radius server name failed.')

        return SUCCESS

    def create_radius_server_name(self, **kwargs):
        """ create_radius_server_name """

        module = kwargs["module"]
        radius_group_name = kwargs["radius_group_name"]
        raduis_server_type = kwargs["raduis_server_type"]
        radius_server_name = kwargs["radius_server_name"]
        radius_server_port = kwargs["radius_server_port"]
        radius_server_mode = kwargs["radius_server_mode"]
        radius_vpn_name = kwargs["radius_vpn_name"]

        conf_str = CE_CREATE_RADIUS_SERVER_NAME % (
            radius_group_name, raduis_server_type,
            radius_server_name, radius_server_port,
            radius_server_mode, radius_vpn_name)

        con_obj = self.netconf_set_config(module=module,
                                          conf_str=conf_str)

        if "<ok/>" not in con_obj.xml:
            module.fail_json(msg='create radius server name failed.')

        return SUCCESS

    def delete_radius_server_name(self, **kwargs):
        """ delete_radius_server_name """

        module = kwargs["module"]
        radius_group_name = kwargs["radius_group_name"]
        raduis_server_type = kwargs["raduis_server_type"]
        radius_server_name = kwargs["radius_server_name"]
        radius_server_port = kwargs["radius_server_port"]
        radius_server_mode = kwargs["radius_server_mode"]
        radius_vpn_name = kwargs["radius_vpn_name"]

        conf_str = CE_DELETE_RADIUS_SERVER_NAME % (
            radius_group_name, raduis_server_type,
            radius_server_name, radius_server_port,
            radius_server_mode, radius_vpn_name)

        con_obj = self.netconf_set_config(module=module,
                                          conf_str=conf_str)

        if "<ok/>" not in con_obj.xml:
            module.fail_json(msg='delete radius server name failed.')

        return SUCCESS

    def get_hwtacacs_server_cfg_ipv4(self, **kwargs):
        """ get_hwtacacs_server_cfg_ipv4 """

        module = kwargs["module"]
        hwtacacs_template = kwargs["hwtacacs_template"]
        conf_str = CE_GET_HWTACACS_SERVER_CFG_IPV4 % hwtacacs_template

        con_obj = self.netconf_get_config(module=module,
                                          conf_str=conf_str)

        xml_str = con_obj.xml
        result = list()

        if "<data/>" in xml_str:
            return result
        else:
            re_find = re.findall(
                r'.*<serverIpAddress>(.*)</serverIpAddress>.*\s*'
                r'<serverType>(.*)</serverType>.*\s*'
                r'<isSecondaryServer>(.*)</isSecondaryServer>.*\s*'
                r'<vpnName>(.*)</vpnName>.*\s*'
                r'<isPublicNet>(.*)</isPublicNet>.*', xml_str)

            if re_find:
                return re_find
            else:
                return result

    def merge_hwtacacs_server_cfg_ipv4(self, **kwargs):
        """ merge_hwtacacs_server_cfg_ipv4 """

        module = kwargs["module"]
        hwtacacs_template = kwargs["hwtacacs_template"]
        hwtacacs_server_ip = kwargs["hwtacacs_server_ip"]
        hwtacacs_server_type = kwargs["hwtacacs_server_type"]
        hwtacacs_is_secondary_server = kwargs["hwtacacs_is_secondary_server"]
        hwtacacs_vpn_name = kwargs["hwtacacs_vpn_name"]
        hwtacacs_is_public_net = kwargs["hwtacacs_is_public_net"]

        conf_str = CE_MERGE_HWTACACS_SERVER_CFG_IPV4 % (
            hwtacacs_template, hwtacacs_server_ip,
            hwtacacs_server_type, hwtacacs_is_secondary_server,
            hwtacacs_vpn_name, hwtacacs_is_public_net)

        con_obj = self.netconf_set_config(module=module,
                                          conf_str=conf_str)

        if "<ok/>" not in con_obj.xml:
            module.fail_json(msg='merge hwtacacs server config ipv4 failed.')

        return SUCCESS

    def create_hwtacacs_server_cfg_ipv4(self, **kwargs):
        """ create_hwtacacs_server_cfg_ipv4 """

        module = kwargs["module"]
        hwtacacs_template = kwargs["hwtacacs_template"]
        hwtacacs_server_ip = kwargs["hwtacacs_server_ip"]
        hwtacacs_server_type = kwargs["hwtacacs_server_type"]
        hwtacacs_is_secondary_server = kwargs["hwtacacs_is_secondary_server"]
        hwtacacs_vpn_name = kwargs["hwtacacs_vpn_name"]
        hwtacacs_is_public_net = kwargs["hwtacacs_is_public_net"]

        conf_str = CE_CREATE_HWTACACS_SERVER_CFG_IPV4 % (
            hwtacacs_template, hwtacacs_server_ip,
            hwtacacs_server_type, hwtacacs_is_secondary_server,
            hwtacacs_vpn_name, hwtacacs_is_public_net)

        con_obj = self.netconf_set_config(module=module,
                                          conf_str=conf_str)

        if "<ok/>" not in con_obj.xml:
            module.fail_json(msg='create hwtacacs server config ipv4 failed.')

        return SUCCESS

    def delete_hwtacacs_server_cfg_ipv4(self, **kwargs):
        """ delete_hwtacacs_server_cfg_ipv4 """

        module = kwargs["module"]
        hwtacacs_template = kwargs["hwtacacs_template"]
        hwtacacs_server_ip = kwargs["hwtacacs_server_ip"]
        hwtacacs_server_type = kwargs["hwtacacs_server_type"]
        hwtacacs_is_secondary_server = kwargs["hwtacacs_is_secondary_server"]
        hwtacacs_vpn_name = kwargs["hwtacacs_vpn_name"]
        hwtacacs_is_public_net = kwargs["hwtacacs_is_public_net"]

        conf_str = CE_DELETE_HWTACACS_SERVER_CFG_IPV4 % (
            hwtacacs_template, hwtacacs_server_ip,
            hwtacacs_server_type, hwtacacs_is_secondary_server,
            hwtacacs_vpn_name, hwtacacs_is_public_net)

        con_obj = self.netconf_set_config(module=module, conf_str=conf_str)

        if "<ok/>" not in con_obj.xml:
            module.fail_json(msg='delete hwtacacs server config ipv4 failed.')

        return SUCCESS

    def get_hwtacacs_server_cfg_ipv6(self, **kwargs):
        """ get_hwtacacs_server_cfg_ipv6 """

        module = kwargs["module"]
        hwtacacs_template = kwargs["hwtacacs_template"]
        conf_str = CE_GET_HWTACACS_SERVER_CFG_IPV6 % hwtacacs_template

        con_obj = self.netconf_get_config(module=module, conf_str=conf_str)

        xml_str = con_obj.xml
        result = list()

        if "<data/>" in xml_str:
            return result
        else:
            re_find = re.findall(
                r'.*<serverIpAddress>(.*)</serverIpAddress>.*\s*'
                r'<serverType>(.*)</serverType>.*\s*'
                r'<isSecondaryServer>(.*)</isSecondaryServer>.*\s*'
                r'<vpnName>(.*)</vpnName>.*', xml_str)

            if re_find:
                return re_find
            else:
                return result

    def merge_hwtacacs_server_cfg_ipv6(self, **kwargs):
        """ merge_hwtacacs_server_cfg_ipv6 """

        module = kwargs["module"]
        hwtacacs_template = kwargs["hwtacacs_template"]
        hwtacacs_server_ip = kwargs["hwtacacs_server_ip"]
        hwtacacs_server_type = kwargs["hwtacacs_server_type"]
        hwtacacs_is_secondary_server = kwargs["hwtacacs_is_secondary_server"]
        hwtacacs_vpn_name = kwargs["hwtacacs_vpn_name"]

        conf_str = CE_MERGE_HWTACACS_SERVER_CFG_IPV6 % (
            hwtacacs_template, hwtacacs_server_ip,
            hwtacacs_server_type, hwtacacs_is_secondary_server,
            hwtacacs_vpn_name)

        con_obj = self.netconf_set_config(module=module,
                                          conf_str=conf_str)

        if "<ok/>" not in con_obj.xml:
            module.fail_json(msg='merge hwtacacs server config ipv6 failed.')

        return SUCCESS

    def create_hwtacacs_server_cfg_ipv6(self, **kwargs):
        """ create_hwtacacs_server_cfg_ipv6 """

        module = kwargs["module"]
        hwtacacs_template = kwargs["hwtacacs_template"]
        hwtacacs_server_ip = kwargs["hwtacacs_server_ip"]
        hwtacacs_server_type = kwargs["hwtacacs_server_type"]
        hwtacacs_is_secondary_server = kwargs["hwtacacs_is_secondary_server"]
        hwtacacs_vpn_name = kwargs["hwtacacs_vpn_name"]

        conf_str = CE_CREATE_HWTACACS_SERVER_CFG_IPV6 % (
            hwtacacs_template, hwtacacs_server_ip,
            hwtacacs_server_type, hwtacacs_is_secondary_server,
            hwtacacs_vpn_name)

        con_obj = self.netconf_set_config(module=module,
                                          conf_str=conf_str)

        if "<ok/>" not in con_obj.xml:
            module.fail_json(msg='create hwtacacs server config ipv6 failed.')

        return SUCCESS

    def delete_hwtacacs_server_cfg_ipv6(self, **kwargs):
        """ delete_hwtacacs_server_cfg_ipv6 """

        module = kwargs["module"]
        hwtacacs_template = kwargs["hwtacacs_template"]
        hwtacacs_server_ip = kwargs["hwtacacs_server_ip"]
        hwtacacs_server_type = kwargs["hwtacacs_server_type"]
        hwtacacs_is_secondary_server = kwargs["hwtacacs_is_secondary_server"]
        hwtacacs_vpn_name = kwargs["hwtacacs_vpn_name"]

        conf_str = CE_DELETE_HWTACACS_SERVER_CFG_IPV6 % (
            hwtacacs_template, hwtacacs_server_ip,
            hwtacacs_server_type, hwtacacs_is_secondary_server,
            hwtacacs_vpn_name)

        con_obj = self.netconf_set_config(module=module, conf_str=conf_str)

        if "<ok/>" not in con_obj.xml:
            module.fail_json(msg='delete hwtacacs server config ipv6 failed.')

        return SUCCESS

    def get_hwtacacs_host_server_cfg(self, **kwargs):
        """ get_hwtacacs_host_server_cfg """

        module = kwargs["module"]
        hwtacacs_template = kwargs["hwtacacs_template"]
        conf_str = CE_GET_HWTACACS_HOST_SERVER_CFG % hwtacacs_template

        con_obj = self.netconf_get_config(module=module, conf_str=conf_str)

        xml_str = con_obj.xml
        result = list()

        if "<data/>" in xml_str:
            return result
        else:
            re_find = re.findall(
                r'.*<serverHostName>(.*)</serverHostName>.*\s*'
                r'<serverType>(.*)</serverType>.*\s*'
                r'<isSecondaryServer>(.*)</isSecondaryServer>.*\s*'
                r'<vpnName>(.*)</vpnName>.*\s*'
                r'<isPublicNet>(.*)</isPublicNet>.*', xml_str)

            if re_find:
                return re_find
            else:
                return result

    def merge_hwtacacs_host_server_cfg(self, **kwargs):
        """ merge_hwtacacs_host_server_cfg """

        module = kwargs["module"]
        hwtacacs_template = kwargs["hwtacacs_template"]
        hwtacacs_server_host_name = kwargs["hwtacacs_server_host_name"]
        hwtacacs_server_type = kwargs["hwtacacs_server_type"]
        hwtacacs_is_secondary_server = kwargs["hwtacacs_is_secondary_server"]
        hwtacacs_vpn_name = kwargs["hwtacacs_vpn_name"]
        hwtacacs_is_public_net = kwargs["hwtacacs_is_public_net"]

        conf_str = CE_MERGE_HWTACACS_HOST_SERVER_CFG % (
            hwtacacs_template, hwtacacs_server_host_name,
            hwtacacs_server_type, hwtacacs_is_secondary_server,
            hwtacacs_vpn_name, hwtacacs_is_public_net)

        con_obj = self.netconf_set_config(module=module,
                                          conf_str=conf_str)

        if "<ok/>" not in con_obj.xml:
            module.fail_json(msg='merge hwtacacs host server config failed.')

        return SUCCESS

    def create_hwtacacs_host_server_cfg(self, **kwargs):
        """ create_hwtacacs_host_server_cfg """

        module = kwargs["module"]
        hwtacacs_template = kwargs["hwtacacs_template"]
        hwtacacs_server_host_name = kwargs["hwtacacs_server_host_name"]
        hwtacacs_server_type = kwargs["hwtacacs_server_type"]
        hwtacacs_is_secondary_server = kwargs["hwtacacs_is_secondary_server"]
        hwtacacs_vpn_name = kwargs["hwtacacs_vpn_name"]
        hwtacacs_is_public_net = kwargs["hwtacacs_is_public_net"]

        conf_str = CE_CREATE_HWTACACS_HOST_SERVER_CFG % (
            hwtacacs_template, hwtacacs_server_host_name,
            hwtacacs_server_type, hwtacacs_is_secondary_server,
            hwtacacs_vpn_name, hwtacacs_is_public_net)

        con_obj = self.netconf_set_config(module=module,
                                          conf_str=conf_str)

        if "<ok/>" not in con_obj.xml:
            module.fail_json(msg='create hwtacacs host server config failed.')

        return SUCCESS

    def delete_hwtacacs_host_server_cfg(self, **kwargs):
        """ delete_hwtacacs_host_server_cfg """

        module = kwargs["module"]
        hwtacacs_template = kwargs["hwtacacs_template"]
        hwtacacs_server_host_name = kwargs["hwtacacs_server_host_name"]
        hwtacacs_server_type = kwargs["hwtacacs_server_type"]
        hwtacacs_is_secondary_server = kwargs["hwtacacs_is_secondary_server"]
        hwtacacs_vpn_name = kwargs["hwtacacs_vpn_name"]
        hwtacacs_is_public_net = kwargs["hwtacacs_is_public_net"]

        conf_str = CE_DELETE_HWTACACS_HOST_SERVER_CFG % (
            hwtacacs_template, hwtacacs_server_host_name,
            hwtacacs_server_type, hwtacacs_is_secondary_server,
            hwtacacs_vpn_name, hwtacacs_is_public_net)

        con_obj = self.netconf_set_config(module=module,
                                          conf_str=conf_str)

        if "<ok/>" not in con_obj.xml:
            module.fail_json(msg='delete hwtacacs host server config failed.')

        return SUCCESS


def get_ce_aaa_server_host(**kwargs):
    """ get_ce_aaa_server_host """

    return ce_aaa_server_host(**kwargs)


def check_ip_addr(ipaddr):
    """ check_ip_addr """

    addr = ipaddr.strip().split('.')

    if len(addr) != 4:
        return FAILED

    for i in range(4):
        try:
            addr[i] = int(addr[i])
        except:
            return FAILED
        if addr[i] <= 255 and addr[i] >= 0:
            pass
        else:
            return FAILED
    return SUCCESS


def check_name(**kwargs):
    """ check_name """

    module = kwargs["module"]
    name = kwargs["name"]
    invalid_char = kwargs["invalid_char"]

    for item in invalid_char:
        if item in name:
            module.fail_json(
                msg='invalid char %s is in the name %s ' % (item, name))


def check_module_argument(**kwargs):
    """ check_module_argument """

    module = kwargs["module"]

    # local para
    local_user_name = module.params['local_user_name']
    local_password = module.params['local_password']

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
                msg='local_user_name %s is large than 253.' % local_user_name)
        check_name(module=module, name=local_user_name,
                   invalid_char=INVALID_USER_NAME_CHAR)

    if local_password and len(local_password) > 255:
        module.fail_json(
            msg='local_password %s is large than 255.' % local_password)

    if radius_group_name and len(radius_group_name) > 32:
        module.fail_json(
            msg='radius_group_name %s is large than 32.' % radius_group_name)

    if radius_server_ip and check_ip_addr(radius_server_ip) == FAILED:
        module.fail_json(msg='radius_server_ip %s is invalid.' %
                         radius_server_ip)

    if radius_server_port and not radius_server_port.isdigit():
        module.fail_json(msg='radius_server_port %s is invalid.' %
                         radius_server_port)

    if radius_vpn_name:
        if len(radius_vpn_name) > 31:
            module.fail_json(
                msg='radius_vpn_name %s is large than 31.' % radius_vpn_name)
        if ' ' in radius_vpn_name:
            module.fail_json(
                msg='radius_vpn_name %s include space.' % radius_vpn_name)

    if radius_server_name:
        if len(radius_server_name) > 255:
            module.fail_json(
                msg='radius_server_name %s '
                    'is large than 255.' % radius_server_name)
        if ' ' in radius_server_name:
            module.fail_json(
                msg='radius_server_name %s include space.' % radius_server_name)

    if hwtacacs_template and len(hwtacacs_template) > 32:
        module.fail_json(
            msg='hwtacacs_template %s is large than 32.' % hwtacacs_template)

    if hwtacacs_server_ip and check_ip_addr(hwtacacs_server_ip) == FAILED:
        module.fail_json(msg='hwtacacs_server_ip %s is invalid.' %
                         hwtacacs_server_ip)

    if hwtacacs_vpn_name:
        if len(hwtacacs_vpn_name) > 31:
            module.fail_json(
                msg='hwtacacs_vpn_name %s '
                    'is large than 31.' % hwtacacs_vpn_name)
        if ' ' in hwtacacs_vpn_name:
            module.fail_json(
                msg='hwtacacs_vpn_name %s '
                    'include space.' % hwtacacs_vpn_name)

    if hwtacacs_server_host_name:
        if len(hwtacacs_server_host_name) > 255:
            module.fail_json(
                msg='hwtacacs_server_host_name %s '
                    'is large than 255.' % hwtacacs_server_host_name)
        if ' ' in hwtacacs_server_host_name:
            module.fail_json(
                msg='hwtacacs_server_host_name %s '
                    'include space.' % hwtacacs_server_host_name)


def main():
    """ main """

    start_time = datetime.datetime.now()

    argument_spec = dict(
        state=dict(choices=['present', 'absent'],
                   default='present'),
        host=dict(required=True),
        username=dict(required=True),
        password=dict(required=True),
        local_user_name=dict(type='str'),
        local_password=dict(type='str'),
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
            choices=['Authentication', 'Authorization',
                     'Accounting', 'Common']),
        hwtacacs_is_secondary_server=dict(
            choices=['true', 'false'], default='true'),
        hwtacacs_vpn_name=dict(type='str'),
        hwtacacs_is_public_net=dict(
            choices=['true', 'false'], default='false'),
        hwtacacs_server_host_name=dict(type='str')
    )

    if not HAS_NCCLIENT:
        raise Exception("the ncclient library is required")

    module = NetworkModule(argument_spec=argument_spec,
                        supports_check_mode=True)

    check_module_argument(module=module)

    # common para
    state = module.params['state']
    host = module.params['host']
    port = module.params['port']
    username = module.params['username']
    password = module.params['password']

    # local para
    local_user_name = module.params['local_user_name']
    local_password = module.params['local_password']

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

    ce_aaa_server_host = get_ce_aaa_server_host(
        host=host, port=port, username=username, password=password)

    if not ce_aaa_server_host:
        module.fail_json(msg='construct ce_aaa_server failed.')

    args = dict(local_user_name=local_user_name,
                local_password="******",
                radius_group_name=radius_group_name,
                raduis_server_type=raduis_server_type,
                radius_server_ip=radius_server_ip,
                radius_server_ipv6=radius_server_ipv6,
                radius_server_port=radius_server_port,
                radius_server_mode=radius_server_mode,
                radius_vpn_name=radius_vpn_name,
                radius_server_name=radius_server_name,
                hwtacacs_template=hwtacacs_template,
                hwtacacs_server_ip=hwtacacs_server_ip,
                hwtacacs_server_ipv6=hwtacacs_server_ipv6,
                hwtacacs_server_type=hwtacacs_server_type,
                hwtacacs_is_secondary_server=hwtacacs_is_secondary_server,
                hwtacacs_vpn_name=hwtacacs_vpn_name,
                hwtacacs_is_public_net=hwtacacs_is_public_net,
                hwtacacs_server_host_name=hwtacacs_server_host_name,
                state=state)

    changed = False
    proposed = dict((k, v) for k, v in args.iteritems() if v is not None)
    existing = dict()
    end_state = dict()

    tmp_var = None

    if local_user_name:

        if not local_password:
            module.fail_json(
                msg='please input local_password when config local user.')

        local_user_exist = ce_aaa_server_host.get_local_user_info(
            module=module)
        local_user_new = (local_user_name.lower())

        existing["local user name"] = local_user_exist

        if state == "present":
            # present local user
            if len(local_user_exist) == 0:
                ce_aaa_server_host.create_local_user_info(
                    module=module,
                    local_user_name=local_user_name,
                    local_password=local_password)

            elif local_user_new not in local_user_exist:
                ce_aaa_server_host.merge_local_user_info(
                    module=module,
                    local_user_name=local_user_name,
                    local_password=local_password)

            else:
                pass

        else:
            # absent local user
            if len(local_user_exist) == 0:
                pass

            elif local_user_new not in local_user_exist:
                pass

            else:
                ce_aaa_server_host.delete_local_user_info(
                    module=module, local_user_name=local_user_name)

        local_user_end = ce_aaa_server_host.get_local_user_info(
            module=module)
        end_state["local user name"] = local_user_end

        if changed == False:
            local_user_exist.sort()
            local_user_end.sort()

            if local_user_exist != local_user_end:
                changed = True

    if radius_group_name:

        if not radius_server_ip \
                and not radius_server_ipv6 \
                and not radius_server_name:
            module.fail_json(
                msg='please input radius_server_ip or '
                    'radius_server_ipv6 or radius_server_name.')

        if not raduis_server_type \
                or not radius_server_port \
                or not radius_server_mode \
                or not radius_vpn_name:
            module.fail_json(
                msg='please input raduis_server_type '
                    'radius_server_port radius_server_mode radius_vpn_name.')

        rds_server_ipv4_exist = ce_aaa_server_host.get_radius_server_cfg_ipv4(
            module=module, radius_group_name=radius_group_name)
        rds_server_ipv6_exist = ce_aaa_server_host.get_radius_server_cfg_ipv6(
            module=module, radius_group_name=radius_group_name)
        rds_server_name_exist = ce_aaa_server_host.get_radius_server_name(
            module=module, radius_group_name=radius_group_name)

        if state == "present":
            # present radius group
            if radius_server_ip:
                rds_server_ipv4_new = (radius_server_ip,
                                       raduis_server_type,
                                       radius_server_port,
                                       radius_server_mode,
                                       radius_vpn_name)

                existing["radius server ipv4"] = rds_server_ipv4_exist

                if len(rds_server_ipv4_exist) == 0:
                    ce_aaa_server_host.\
                        create_radius_server_cfg_ipv4\
                        (module=module,
                         radius_group_name=radius_group_name,
                         raduis_server_type=raduis_server_type,
                         radius_server_ip=radius_server_ip,
                         radius_server_port=radius_server_port,
                         radius_server_mode=radius_server_mode,
                         radius_vpn_name=radius_vpn_name)

                elif rds_server_ipv4_new not in rds_server_ipv4_exist:
                    ce_aaa_server_host.\
                        merge_radius_server_cfg_ipv4\
                        (module=module,
                         radius_group_name=radius_group_name,
                         raduis_server_type=raduis_server_type,
                         radius_server_ip=radius_server_ip,
                         radius_server_port=radius_server_port,
                         radius_server_mode=radius_server_mode,
                         radius_vpn_name=radius_vpn_name)

                else:
                    pass

            elif radius_server_ipv6:
                rds_server_ipv6_new = (
                    radius_server_ipv6,
                    raduis_server_type,
                    radius_server_port,
                    radius_server_mode)

                existing["radius server ipv6"] = rds_server_ipv6_exist

                if len(rds_server_ipv6_exist) == 0:
                    ce_aaa_server_host.\
                        create_radius_server_cfg_ipv6\
                        (module=module,
                         radius_group_name=radius_group_name,
                         raduis_server_type=raduis_server_type,
                         radius_server_ipv6=radius_server_ipv6,
                         radius_server_port=radius_server_port,
                         radius_server_mode=radius_server_mode)

                elif rds_server_ipv6_new not in rds_server_ipv6_exist:
                    ce_aaa_server_host.\
                        merge_radius_server_cfg_ipv6\
                        (module=module,
                         radius_group_name=radius_group_name,
                         raduis_server_type=raduis_server_type,
                         radius_server_ipv6=radius_server_ipv6,
                         radius_server_port=radius_server_port,
                         radius_server_mode=radius_server_mode)

                else:
                    pass

            elif radius_server_name:
                # present radius host server name
                rds_server_name_new = (radius_server_name,
                                       raduis_server_type,
                                       radius_server_port,
                                       radius_server_mode,
                                       radius_vpn_name)
                existing["radius server name"] = rds_server_name_exist

                if len(rds_server_name_exist) == 0:
                    ce_aaa_server_host.\
                        create_radius_server_name\
                        (module=module,
                         radius_group_name=radius_group_name,
                         raduis_server_type=raduis_server_type,
                         radius_server_name=radius_server_name,
                         radius_server_port=radius_server_port,
                         radius_server_mode=radius_server_mode,
                         radius_vpn_name=radius_vpn_name)

                elif rds_server_name_new not in rds_server_name_exist:
                    ce_aaa_server_host.\
                        merge_radius_server_name\
                        (module=module,
                         radius_group_name=radius_group_name,
                         raduis_server_type=raduis_server_type,
                         radius_server_name=radius_server_name,
                         radius_server_port=radius_server_port,
                         radius_server_mode=radius_server_mode,
                         radius_vpn_name=radius_vpn_name)

                else:
                    pass

        else:
            # absent radius group
            if radius_server_ip:
                rds_server_ipv4_new = (radius_server_ip,
                                       raduis_server_type,
                                       radius_server_port,
                                       radius_server_mode,
                                       radius_vpn_name)

                existing["radius server ipv4"] = rds_server_ipv4_exist

                if len(rds_server_ipv4_exist) == 0:
                    pass

                elif rds_server_ipv4_new not in rds_server_ipv4_exist:
                    pass

                else:
                    ce_aaa_server_host.\
                        delete_radius_server_cfg_ipv4\
                        (module=module,
                         radius_group_name=radius_group_name,
                         raduis_server_type=raduis_server_type,
                         radius_server_ip=radius_server_ip,
                         radius_server_port=radius_server_port,
                         radius_server_mode=radius_server_mode,
                         radius_vpn_name=radius_vpn_name)

            elif radius_server_ipv6:
                rds_server_ipv6_new = (
                    radius_server_ipv6,
                    raduis_server_type,
                    radius_server_port,
                    radius_server_mode)

                existing["radius server ipv6"] = rds_server_ipv6_exist

                if len(rds_server_ipv6_exist) == 0:
                    pass

                elif rds_server_ipv6_new not in rds_server_ipv6_exist:
                    pass

                else:
                    ce_aaa_server_host.\
                        delete_radius_server_cfg_ipv6\
                        (module=module,
                         radius_group_name=radius_group_name,
                         raduis_server_type=raduis_server_type,
                         radius_server_ipv6=radius_server_ipv6,
                         radius_server_port=radius_server_port,
                         radius_server_mode=radius_server_mode)

            elif radius_server_name:
                # absent radius host server name
                rds_server_name_new = (radius_server_name,
                                       raduis_server_type,
                                       radius_server_port,
                                       radius_server_mode,
                                       radius_vpn_name)
                existing["radius server name"] = rds_server_name_exist
                if len(rds_server_name_exist) == 0:
                    pass

                elif rds_server_name_new not in rds_server_name_exist:
                    pass

                else:
                    ce_aaa_server_host.\
                        delete_radius_server_name\
                        (module=module,
                         radius_group_name=radius_group_name,
                         raduis_server_type=raduis_server_type,
                         radius_server_name=radius_server_name,
                         radius_server_port=radius_server_port,
                         radius_server_mode=radius_server_mode,
                         radius_vpn_name=radius_vpn_name)

        # state config
        if radius_server_ip:
            rds_server_ipv4_end = ce_aaa_server_host.get_radius_server_cfg_ipv4(
                module=module, radius_group_name=radius_group_name)
            end_state["radius server ipv4"] = rds_server_ipv4_end
            if changed == False:
                rds_server_ipv4_end.sort()
                rds_server_ipv4_exist.sort()
                if rds_server_ipv4_end != rds_server_ipv4_exist:
                    changed = True

        elif radius_server_ipv6:
            rds_server_ipv6_end = ce_aaa_server_host.get_radius_server_cfg_ipv6(
                module=module, radius_group_name=radius_group_name)
            end_state["radius server ipv6"] = rds_server_ipv6_end
            if changed == False:
                rds_server_ipv6_end.sort()
                rds_server_ipv6_exist.sort()
                if rds_server_ipv6_end != rds_server_ipv6_exist:
                    changed = True

        elif radius_server_name:
            rds_server_name_end = ce_aaa_server_host.get_radius_server_name(
                module=module, radius_group_name=radius_group_name)
            end_state["radius server name"] = rds_server_name_end
            if changed == False:
                rds_server_name_end.sort()
                rds_server_name_exist.sort()
                if rds_server_name_end != rds_server_name_exist:
                    changed = True

    if hwtacacs_template:

        if not hwtacacs_server_ip \
                and not hwtacacs_server_ipv6 \
                and not hwtacacs_server_host_name:
            module.fail_json(
                msg='please input hwtacacs_server_ip or '
                    'hwtacacs_server_ipv6 or hwtacacs_server_host_name.')

        if not hwtacacs_server_type \
                or not hwtacacs_is_secondary_server \
                or not hwtacacs_vpn_name \
                or not hwtacacs_is_public_net:
            module.fail_json(
                msg='please input hwtacacs_server_type '
                    'hwtacacs_is_secondary_server hwtacacs_vpn_name '
                    'hwtacacs_is_public_net.')

        hwtacacs_server_ipv4_exist = ce_aaa_server_host.\
            get_hwtacacs_server_cfg_ipv4\
            (module=module, hwtacacs_template=hwtacacs_template)
        hwtacacs_server_ipv6_exist = ce_aaa_server_host.\
            get_hwtacacs_server_cfg_ipv6\
            (module=module, hwtacacs_template=hwtacacs_template)
        hwtacacs_host_name_exist = ce_aaa_server_host.\
            get_hwtacacs_host_server_cfg\
            (module=module, hwtacacs_template=hwtacacs_template)

        tmp_var = hwtacacs_is_secondary_server

        if state == "present":
            # present hwtacacs config
            if hwtacacs_server_ip:
                hwtacacs_server_ipv4_new = (hwtacacs_server_ip,
                                            hwtacacs_server_type,
                                            hwtacacs_is_secondary_server,
                                            hwtacacs_vpn_name,
                                            hwtacacs_is_public_net)

                existing["hwtacacs server ipv4"] = hwtacacs_server_ipv4_exist

                if len(hwtacacs_server_ipv4_exist) == 0:
                    ce_aaa_server_host.create_hwtacacs_server_cfg_ipv4\
                        (module=module,
                         hwtacacs_template=hwtacacs_template,
                         hwtacacs_server_ip=hwtacacs_server_ip,
                         hwtacacs_server_type=hwtacacs_server_type,
                         hwtacacs_is_secondary_server=tmp_var,
                         hwtacacs_vpn_name=hwtacacs_vpn_name,
                         hwtacacs_is_public_net=hwtacacs_is_public_net)

                elif hwtacacs_server_ipv4_new \
                        not in hwtacacs_server_ipv4_exist:
                    ce_aaa_server_host.merge_hwtacacs_server_cfg_ipv4\
                        (module=module,
                         hwtacacs_template=hwtacacs_template,
                         hwtacacs_server_ip=hwtacacs_server_ip,
                         hwtacacs_server_type=hwtacacs_server_type,
                         hwtacacs_is_secondary_server=tmp_var,
                         hwtacacs_vpn_name=hwtacacs_vpn_name,
                         hwtacacs_is_public_net=hwtacacs_is_public_net)

                else:
                    pass

            elif hwtacacs_server_ipv6:
                hwtacacs_server_ipv6_new = (
                    hwtacacs_server_ip, hwtacacs_server_type,
                    hwtacacs_is_secondary_server, hwtacacs_vpn_name)

                existing["hwtacacs server ipv6"] = hwtacacs_server_ipv6_exist

                if len(hwtacacs_server_ipv6_exist) == 0:
                    ce_aaa_server_host.\
                        create_hwtacacs_server_cfg_ipv6\
                        (module=module,
                         hwtacacs_template=hwtacacs_template,
                         hwtacacs_server_ip=hwtacacs_server_ip,
                         hwtacacs_server_type=hwtacacs_server_type,
                         hwtacacs_is_secondary_server=tmp_var,
                         hwtacacs_vpn_name=hwtacacs_vpn_name)

                elif hwtacacs_server_ipv6_new \
                        not in hwtacacs_server_ipv6_exist:
                    ce_aaa_server_host.\
                        merge_hwtacacs_server_cfg_ipv6\
                        (module=module,
                         hwtacacs_template=hwtacacs_template,
                         hwtacacs_server_ip=hwtacacs_server_ip,
                         hwtacacs_server_type=hwtacacs_server_type,
                         hwtacacs_is_secondary_server=tmp_var,
                         hwtacacs_vpn_name=hwtacacs_vpn_name)

                else:
                    pass

            elif hwtacacs_server_host_name:
                hwtacacs_host_server_new = (hwtacacs_server_host_name,
                                            hwtacacs_server_type,
                                            hwtacacs_is_secondary_server,
                                            hwtacacs_vpn_name,
                                            hwtacacs_is_public_net)
                existing["hwtacacs host name"] = hwtacacs_host_name_exist

                if len(hwtacacs_host_name_exist) == 0:
                    ce_aaa_server_host.\
                        create_hwtacacs_host_server_cfg\
                        (module=module,
                         hwtacacs_template=hwtacacs_template,
                         hwtacacs_server_host_name=hwtacacs_server_host_name,
                         hwtacacs_server_type=hwtacacs_server_type,
                         hwtacacs_is_secondary_server=tmp_var,
                         hwtacacs_vpn_name=hwtacacs_vpn_name,
                         hwtacacs_is_public_net=hwtacacs_is_public_net)

                elif hwtacacs_host_server_new \
                        not in hwtacacs_host_name_exist:
                    ce_aaa_server_host.\
                        merge_hwtacacs_host_server_cfg\
                        (module=module,
                         hwtacacs_template=hwtacacs_template,
                         hwtacacs_server_host_name=hwtacacs_server_host_name,
                         hwtacacs_server_type=hwtacacs_server_type,
                         hwtacacs_is_secondary_server=tmp_var,
                         hwtacacs_vpn_name=hwtacacs_vpn_name,
                         hwtacacs_is_public_net=hwtacacs_is_public_net)

                else:
                    pass

        else:
            # absent hwtacacs config
            if hwtacacs_server_ip:
                hwtacacs_server_ipv4_new = (hwtacacs_server_ip,
                                            hwtacacs_server_type,
                                            hwtacacs_is_secondary_server,
                                            hwtacacs_vpn_name,
                                            hwtacacs_is_public_net)

                existing["hwtacacs server ipv4"] = hwtacacs_server_ipv4_exist

                if len(hwtacacs_server_ipv4_exist) == 0:
                    pass

                elif hwtacacs_server_ipv4_new \
                        not in hwtacacs_server_ipv4_exist:
                    pass

                else:
                    ce_aaa_server_host.\
                        delete_hwtacacs_server_cfg_ipv4\
                        (module=module,
                         hwtacacs_template=hwtacacs_template,
                         hwtacacs_server_ip=hwtacacs_server_ip,
                         hwtacacs_server_type=hwtacacs_server_type,
                         hwtacacs_is_secondary_server=tmp_var,
                         hwtacacs_vpn_name=hwtacacs_vpn_name,
                         hwtacacs_is_public_net=hwtacacs_is_public_net)

            elif hwtacacs_server_ipv6:
                hwtacacs_server_ipv6_new = (
                    hwtacacs_server_ip, hwtacacs_server_type,
                    hwtacacs_is_secondary_server, hwtacacs_vpn_name)

                existing["hwtacacs server ipv6"] = hwtacacs_server_ipv6_exist

                if len(hwtacacs_server_ipv6_exist) == 0:
                    pass

                elif hwtacacs_server_ipv6_new \
                        not in hwtacacs_server_ipv6_exist:
                    pass

                else:
                    ce_aaa_server_host.\
                        delete_hwtacacs_server_cfg_ipv6\
                        (module=module,
                         hwtacacs_template=hwtacacs_template,
                         hwtacacs_server_ip=hwtacacs_server_ip,
                         hwtacacs_server_type=hwtacacs_server_type,
                         hwtacacs_is_secondary_server=tmp_var,
                         hwtacacs_vpn_name=hwtacacs_vpn_name)

            elif hwtacacs_server_host_name:
                hwtacacs_host_server_new = (hwtacacs_server_host_name,
                                            hwtacacs_server_type,
                                            hwtacacs_is_secondary_server,
                                            hwtacacs_vpn_name,
                                            hwtacacs_is_public_net)
                existing["hwtacacs host name"] = hwtacacs_host_name_exist

                if len(hwtacacs_host_name_exist) == 0:
                    pass

                elif hwtacacs_host_server_new \
                        not in hwtacacs_host_name_exist:
                    pass

                else:
                    ce_aaa_server_host.\
                        delete_hwtacacs_host_server_cfg\
                        (module=module,
                         hwtacacs_template=hwtacacs_template,
                         hwtacacs_server_host_name=hwtacacs_server_host_name,
                         hwtacacs_server_type=hwtacacs_server_type,
                         hwtacacs_is_secondary_server=tmp_var,
                         hwtacacs_vpn_name=hwtacacs_vpn_name,
                         hwtacacs_is_public_net=hwtacacs_is_public_net)

        # state config
        if hwtacacs_server_ip:
            hwtacacs_server_ipv4_end = ce_aaa_server_host.\
                get_hwtacacs_server_cfg_ipv4\
                (module=module, hwtacacs_template=hwtacacs_template)
            end_state["hwtacacs server ipv4"] = hwtacacs_server_ipv4_end
            if changed == False:
                hwtacacs_server_ipv4_end.sort()
                hwtacacs_server_ipv4_exist.sort()
                if hwtacacs_server_ipv4_end != hwtacacs_server_ipv4_exist:
                    changed = True

        elif hwtacacs_server_ipv6:
            hwtacacs_server_ipv6_end = ce_aaa_server_host.\
                get_hwtacacs_server_cfg_ipv6\
                (module=module, hwtacacs_template=hwtacacs_template)
            end_state["hwtacacs server ipv6"] = hwtacacs_server_ipv6_end
            if changed == False:
                hwtacacs_server_ipv6_end.sort()
                hwtacacs_server_ipv6_exist.sort()
                if hwtacacs_server_ipv6_end != hwtacacs_server_ipv6_exist:
                    changed = True

        elif hwtacacs_server_host_name:
            hwtacacs_host_name_end = ce_aaa_server_host.\
                get_hwtacacs_host_server_cfg\
                (module=module, hwtacacs_template=hwtacacs_template)
            end_state["hwtacacs host name"] = hwtacacs_host_name_end
            if changed == False:
                hwtacacs_host_name_end.sort()
                hwtacacs_host_name_exist.sort()
                if hwtacacs_host_name_end != hwtacacs_host_name_exist:
                    changed = True

    results = dict()
    results['proposed'] = proposed
    results['existing'] = existing
    results['changed'] = changed
    results['end_state'] = end_state

    end_time = datetime.datetime.now()
    results['execute_time'] = str(end_time - start_time)

    module.exit_json(**results)


if __name__ == '__main__':
    main()
