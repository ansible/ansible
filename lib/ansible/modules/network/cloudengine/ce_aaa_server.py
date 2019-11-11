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

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: ce_aaa_server
version_added: "2.4"
short_description: Manages AAA server global configuration on HUAWEI CloudEngine switches.
description:
    - Manages AAA server global configuration on HUAWEI CloudEngine switches.
author:
    - wangdezhuang (@QijunPan)
notes:
  - This module requires the netconf system service be enabled on the remote device being managed.
  - Recommended connection is C(netconf).
  - This module also works with C(local) connections for legacy playbooks.
options:
    state:
        description:
            - Specify desired state of the resource.
        type: str
        choices: [ absent, present ]
        default: present
    authen_scheme_name:
        description:
            - Name of an authentication scheme.
              The value is a string of 1 to 32 characters.
        type: str
    first_authen_mode:
        description:
            - Preferred authentication mode.
        type: str
        choices: ['invalid', 'local', 'hwtacacs', 'radius', 'none']
        default: local
    author_scheme_name:
        description:
            - Name of an authorization scheme.
              The value is a string of 1 to 32 characters.
        type: str
    first_author_mode:
        description:
            - Preferred authorization mode.
        type: str
        choices: ['invalid', 'local', 'hwtacacs', 'if-authenticated', 'none']
        default: local
    acct_scheme_name:
        description:
            - Accounting scheme name.
              The value is a string of 1 to 32 characters.
        type: str
    accounting_mode:
        description:
            - Accounting Mode.
        type: str
        choices: ['invalid', 'hwtacacs', 'radius', 'none']
        default: none
    domain_name:
        description:
            - Name of a domain.
              The value is a string of 1 to 64 characters.
        type: str
    radius_server_group:
        description:
            - RADIUS server group's name.
              The value is a string of 1 to 32 case-insensitive characters.
        type: str
    hwtacas_template:
        description:
            - Name of a HWTACACS template.
              The value is a string of 1 to 32 case-insensitive characters.
        type: str
    local_user_group:
        description:
            - Name of the user group where the user belongs. The user inherits all the rights of the user group.
              The value is a string of 1 to 32 characters.
        type: str
'''

EXAMPLES = r'''

- name: AAA server test
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

  - name: "Radius authentication Server Basic settings"
    ce_aaa_server:
      state: present
      authen_scheme_name: test1
      first_authen_mode: radius
      radius_server_group: test2
      provider: "{{ cli }}"

  - name: "Undo radius authentication Server Basic settings"
    ce_aaa_server:
      state: absent
      authen_scheme_name: test1
      first_authen_mode: radius
      radius_server_group: test2
      provider: "{{ cli }}"

  - name: "Hwtacacs accounting Server Basic settings"
    ce_aaa_server:
      state: present
      acct_scheme_name: test1
      accounting_mode: hwtacacs
      hwtacas_template: test2
      provider: "{{ cli }}"

  - name: "Undo hwtacacs accounting Server Basic settings"
    ce_aaa_server:
      state: absent
      acct_scheme_name: test1
      accounting_mode: hwtacacs
      hwtacas_template: test2
      provider: "{{ cli }}"
'''

RETURN = '''
changed:
    description: check to see if a change was made on the device
    returned: always
    type: bool
    sample: true
proposed:
    description: k/v pairs of parameters passed into module
    returned: always
    type: dict
    sample: {"accounting_mode": "hwtacacs", "acct_scheme_name": "test1",
            "hwtacas_template": "test2", "state": "present"}
existing:
    description: k/v pairs of existing aaa server
    returned: always
    type: dict
    sample: {"accounting scheme": [["hwtacacs"], ["default"]],
            "hwtacacs template": ["huawei"]}
end_state:
    description: k/v pairs of aaa params after module execution
    returned: always
    type: dict
    sample: {"accounting scheme": [["hwtacacs", "test1"]],
            "hwtacacs template": ["huawei", "test2"]}
updates:
    description: command sent to the device
    returned: always
    type: list
    sample: ["accounting-scheme test1",
             "accounting-mode hwtacacs",
             "hwtacacs server template test2",
             "hwtacacs enable"]
'''

import re
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.cloudengine.ce import get_nc_config, set_nc_config, ce_argument_spec


SUCCESS = """success"""
FAILED = """failed"""

INVALID_SCHEME_CHAR = [' ', '/', '\\', ':', '*', '?', '"', '|', '<', '>']
INVALID_DOMAIN_CHAR = [' ', '*', '?', '"', '\'']
INVALID_GROUP_CHAR = ['/', '\\', ':', '*', '?', '"', '|', '<', '>']


# get authentication scheme
CE_GET_AUTHENTICATION_SCHEME = """
    <filter type="subtree">
      <aaa xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <authenticationSchemes>
          <authenticationScheme>
            <authenSchemeName></authenSchemeName>
            <firstAuthenMode></firstAuthenMode>
            <secondAuthenMode></secondAuthenMode>
          </authenticationScheme>
        </authenticationSchemes>
      </aaa>
    </filter>
"""

# merge authentication scheme
CE_MERGE_AUTHENTICATION_SCHEME = """
    <config>
      <aaa xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <authenticationSchemes>
          <authenticationScheme operation="merge">
            <authenSchemeName>%s</authenSchemeName>
            <firstAuthenMode>%s</firstAuthenMode>
            <secondAuthenMode>invalid</secondAuthenMode>
          </authenticationScheme>
        </authenticationSchemes>
      </aaa>
    </config>
"""

# create authentication scheme
CE_CREATE_AUTHENTICATION_SCHEME = """
    <config>
      <aaa xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <authenticationSchemes>
          <authenticationScheme operation="create">
            <authenSchemeName>%s</authenSchemeName>
            <firstAuthenMode>%s</firstAuthenMode>
            <secondAuthenMode>invalid</secondAuthenMode>
          </authenticationScheme>
        </authenticationSchemes>
      </aaa>
    </config>
"""

# delete authentication scheme
CE_DELETE_AUTHENTICATION_SCHEME = """
    <config>
      <aaa xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <authenticationSchemes>
          <authenticationScheme operation="delete">
            <authenSchemeName>%s</authenSchemeName>
            <firstAuthenMode>%s</firstAuthenMode>
            <secondAuthenMode>invalid</secondAuthenMode>
          </authenticationScheme>
        </authenticationSchemes>
      </aaa>
    </config>
"""

# get authorization scheme
CE_GET_AUTHORIZATION_SCHEME = """
    <filter type="subtree">
      <aaa xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <authorizationSchemes>
          <authorizationScheme>
            <authorSchemeName></authorSchemeName>
            <firstAuthorMode></firstAuthorMode>
            <secondAuthorMode></secondAuthorMode>
          </authorizationScheme>
        </authorizationSchemes>
      </aaa>
    </filter>
"""

# merge authorization scheme
CE_MERGE_AUTHORIZATION_SCHEME = """
    <config>
      <aaa xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <authorizationSchemes>
          <authorizationScheme operation="merge">
            <authorSchemeName>%s</authorSchemeName>
            <firstAuthorMode>%s</firstAuthorMode>
            <secondAuthorMode>invalid</secondAuthorMode>
          </authorizationScheme>
        </authorizationSchemes>
      </aaa>
    </config>
"""

# create authorization scheme
CE_CREATE_AUTHORIZATION_SCHEME = """
    <config>
      <aaa xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <authorizationSchemes>
          <authorizationScheme operation="create">
            <authorSchemeName>%s</authorSchemeName>
            <firstAuthorMode>%s</firstAuthorMode>
            <secondAuthorMode>invalid</secondAuthorMode>
          </authorizationScheme>
        </authorizationSchemes>
      </aaa>
    </config>
"""

# delete authorization scheme
CE_DELETE_AUTHORIZATION_SCHEME = """
    <config>
      <aaa xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <authorizationSchemes>
          <authorizationScheme operation="delete">
            <authorSchemeName>%s</authorSchemeName>
            <firstAuthorMode>%s</firstAuthorMode>
            <secondAuthorMode>invalid</secondAuthorMode>
          </authorizationScheme>
        </authorizationSchemes>
      </aaa>
    </config>
"""

# get accounting scheme
CE_GET_ACCOUNTING_SCHEME = """
    <filter type="subtree">
      <aaa xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <accountingSchemes>
          <accountingScheme>
            <acctSchemeName></acctSchemeName>
            <accountingMode></accountingMode>
          </accountingScheme>
        </accountingSchemes>
      </aaa>
    </filter>
"""

# merge accounting scheme
CE_MERGE_ACCOUNTING_SCHEME = """
    <config>
      <aaa xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <accountingSchemes>
          <accountingScheme operation="merge">
            <acctSchemeName>%s</acctSchemeName>
            <accountingMode>%s</accountingMode>
          </accountingScheme>
        </accountingSchemes>
      </aaa>
    </config>
"""

# create accounting scheme
CE_CREATE_ACCOUNTING_SCHEME = """
    <config>
      <aaa xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <accountingSchemes>
          <accountingScheme operation="create">
            <acctSchemeName>%s</acctSchemeName>
            <accountingMode>%s</accountingMode>
          </accountingScheme>
        </accountingSchemes>
      </aaa>
    </config>
"""

# delete accounting scheme
CE_DELETE_ACCOUNTING_SCHEME = """
    <config>
      <aaa xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <accountingSchemes>
          <accountingScheme operation="delete">
            <acctSchemeName>%s</acctSchemeName>
            <accountingMode>%s</accountingMode>
          </accountingScheme>
        </accountingSchemes>
      </aaa>
    </config>
"""

# get authentication domain
CE_GET_AUTHENTICATION_DOMAIN = """
    <filter type="subtree">
      <aaa xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <domains>
          <domain>
            <domainName></domainName>
            <authenSchemeName></authenSchemeName>
          </domain>
        </domains>
      </aaa>
    </filter>
"""

# merge authentication domain
CE_MERGE_AUTHENTICATION_DOMAIN = """
    <config>
      <aaa xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <domains>
          <domain operation="merge">
            <domainName>%s</domainName>
            <authenSchemeName>%s</authenSchemeName>
          </domain>
        </domains>
      </aaa>
    </config>
"""

# create authentication domain
CE_CREATE_AUTHENTICATION_DOMAIN = """
    <config>
      <aaa xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <domains>
          <domain operation="create">
            <domainName>%s</domainName>
            <authenSchemeName>%s</authenSchemeName>
          </domain>
        </domains>
      </aaa>
    </config>
"""

# delete authentication domain
CE_DELETE_AUTHENTICATION_DOMAIN = """
    <config>
      <aaa xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <domains>
          <domain operation="delete">
            <domainName>%s</domainName>
            <authenSchemeName>%s</authenSchemeName>
          </domain>
        </domains>
      </aaa>
    </config>
"""

# get authorization domain
CE_GET_AUTHORIZATION_DOMAIN = """
    <filter type="subtree">
      <aaa xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <domains>
          <domain>
            <domainName></domainName>
            <authorSchemeName></authorSchemeName>
          </domain>
        </domains>
      </aaa>
    </filter>
"""

# merge authorization domain
CE_MERGE_AUTHORIZATION_DOMAIN = """
    <config>
      <aaa xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <domains>
          <domain operation="merge">
            <domainName>%s</domainName>
            <authorSchemeName>%s</authorSchemeName>
          </domain>
        </domains>
      </aaa>
    </config>
"""

# create authorization domain
CE_CREATE_AUTHORIZATION_DOMAIN = """
    <config>
      <aaa xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <domains>
          <domain operation="create">
            <domainName>%s</domainName>
            <authorSchemeName>%s</authorSchemeName>
          </domain>
        </domains>
      </aaa>
    </config>
"""

# delete authorization domain
CE_DELETE_AUTHORIZATION_DOMAIN = """
    <config>
      <aaa xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <domains>
          <domain operation="delete">
            <domainName>%s</domainName>
            <authorSchemeName>%s</authorSchemeName>
          </domain>
        </domains>
      </aaa>
    </config>
"""

# get accounting domain
CE_GET_ACCOUNTING_DOMAIN = """
    <filter type="subtree">
      <aaa xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <domains>
          <domain>
            <domainName></domainName>
            <acctSchemeName></acctSchemeName>
          </domain>
        </domains>
      </aaa>
    </filter>
"""

# merge accounting domain
CE_MERGE_ACCOUNTING_DOMAIN = """
    <config>
      <aaa xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <domains>
          <domain operation="merge">
            <domainName>%s</domainName>
            <acctSchemeName>%s</acctSchemeName>
          </domain>
        </domains>
      </aaa>
    </config>
"""

# create accounting domain
CE_CREATE_ACCOUNTING_DOMAIN = """
    <config>
      <aaa xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <domains>
          <domain operation="create">
            <domainName>%s</domainName>
            <acctSchemeName>%s</acctSchemeName>
          </domain>
        </domains>
      </aaa>
    </config>
"""

# delete accounting domain
CE_DELETE_ACCOUNTING_DOMAIN = """
    <config>
      <aaa xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <domains>
          <domain operation="delete">
            <domainName>%s</domainName>
            <acctSchemeName>%s</acctSchemeName>
          </domain>
        </domains>
      </aaa>
    </config>
"""

# get radius template
CE_GET_RADIUS_TEMPLATE = """
    <filter type="subtree">
      <radius xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <rdsTemplates>
          <rdsTemplate>
            <groupName></groupName>
            <retransmissionCount></retransmissionCount>
            <retransmissionInterval></retransmissionInterval>
          </rdsTemplate>
        </rdsTemplates>
      </radius>
    </filter>
"""

# merge radius template
CE_MERGE_RADIUS_TEMPLATE = """
    <config>
      <radius xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <rdsTemplates>
          <rdsTemplate operation="merge">
            <groupName>%s</groupName>
            <retransmissionCount>3</retransmissionCount>
            <retransmissionInterval>5</retransmissionInterval>
          </rdsTemplate>
        </rdsTemplates>
      </radius>
    </config>
"""

# create radius template
CE_CREATE_RADIUS_TEMPLATE = """
    <config>
      <radius xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <rdsTemplates>
          <rdsTemplate operation="create">
            <groupName>%s</groupName>
            <retransmissionCount>3</retransmissionCount>
            <retransmissionInterval>5</retransmissionInterval>
          </rdsTemplate>
        </rdsTemplates>
      </radius>
    </config>
"""

# delete radius template
CE_DELETE_RADIUS_TEMPLATE = """
    <config>
      <radius xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <rdsTemplates>
          <rdsTemplate operation="delete">
            <groupName>%s</groupName>
            <retransmissionCount>3</retransmissionCount>
            <retransmissionInterval>5</retransmissionInterval>
          </rdsTemplate>
        </rdsTemplates>
      </radius>
    </config>
"""

# get hwtacacs template
CE_GET_HWTACACS_TEMPLATE = """
    <filter type="subtree">
      <hwtacacs xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <hwTacTempCfgs>
          <hwTacTempCfg>
            <templateName></templateName>
            <isDomainInclude></isDomainInclude>
            <responseTimeout></responseTimeout>
          </hwTacTempCfg>
        </hwTacTempCfgs>
      </hwtacacs>
    </filter>
"""

# merge hwtacacs template
CE_MERGE_HWTACACS_TEMPLATE = """
    <config>
      <hwtacacs xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <hwTacTempCfgs>
          <hwTacTempCfg operation="merge">
            <templateName>%s</templateName>
            <isDomainInclude>true</isDomainInclude>
            <responseTimeout>5</responseTimeout>
          </hwTacTempCfg>
        </hwTacTempCfgs>
      </hwtacacs>
    </config>
"""

# create hwtacacs template
CE_CREATE_HWTACACS_TEMPLATE = """
    <config>
      <hwtacacs xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <hwTacTempCfgs>
          <hwTacTempCfg operation="create">
            <templateName>%s</templateName>
            <isDomainInclude>true</isDomainInclude>
            <responseTimeout>5</responseTimeout>
          </hwTacTempCfg>
        </hwTacTempCfgs>
      </hwtacacs>
    </config>
"""

# delete hwtacacs template
CE_DELETE_HWTACACS_TEMPLATE = """
    <config>
      <hwtacacs xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <hwTacTempCfgs>
          <hwTacTempCfg operation="delete">
            <templateName>%s</templateName>
          </hwTacTempCfg>
        </hwTacTempCfgs>
      </hwtacacs>
    </config>
"""

# get radius client
CE_GET_RADIUS_CLIENT = """
    <filter type="subtree">
      <radius xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <rdsClient>
          <isEnable></isEnable>
          <coaEnable></coaEnable>
          <authClientIdentifier></authClientIdentifier>
        </rdsClient>
      </radius>
    </filter>
"""

# merge radius client
CE_MERGE_RADIUS_CLIENT = """
    <config>
      <radius xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <rdsClient operation="merge">
          <isEnable>%s</isEnable>
        </rdsClient>
      </radius>
    </config>
"""

# get hwtacacs global config
CE_GET_HWTACACS_GLOBAL_CFG = """
    <filter type="subtree">
      <hwtacacs xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <hwTacGlobalCfg>
          <isEnable></isEnable>
          <totalTemplateNo></totalTemplateNo>
          <totalSrvNo></totalSrvNo>
        </hwTacGlobalCfg>
      </hwtacacs>
    </filter>
"""

# merge hwtacacs global config
CE_MERGE_HWTACACS_GLOBAL_CFG = """
    <config>
      <hwtacacs xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <hwTacGlobalCfg operation="merge">
          <isEnable>%s</isEnable>
        </hwTacGlobalCfg>
      </hwtacacs>
    </config>
"""

# get local user group
CE_GET_LOCAL_USER_GROUP = """
    <filter type="subtree">
      <aaa xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <userGroups>
          <userGroup>
            <userGroupName></userGroupName>
          </userGroup>
        </userGroups>
      </aaa>
    </filter>
"""
# merge local user group
CE_MERGE_LOCAL_USER_GROUP = """
    <config>
      <aaa xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <userGroups>
          <userGroup operation="merge">
            <userGroupName>%s</userGroupName>
          </userGroup>
        </userGroups>
      </aaa>
    </config>
"""
# delete local user group
CE_DELETE_LOCAL_USER_GROUP = """
    <config>
      <aaa xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <userGroups>
          <userGroup operation="delete">
            <userGroupName>%s</userGroupName>
          </userGroup>
        </userGroups>
      </aaa>
    </config>
"""


class AaaServer(object):
    """ Manages aaa configuration """

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

    def get_authentication_scheme(self, **kwargs):
        """ Get scheme of authentication """

        module = kwargs["module"]
        conf_str = CE_GET_AUTHENTICATION_SCHEME

        xml_str = self.netconf_get_config(module=module, conf_str=conf_str)
        result = list()

        if "<data/>" in xml_str:
            return result
        else:
            re_find = re.findall(
                r'.*<authenSchemeName>(.*)</authenSchemeName>.*\s*'
                r'<firstAuthenMode>(.*)</firstAuthenMode>.*\s*'
                r'<secondAuthenMode>(.*)</secondAuthenMode>.*\s*', xml_str)

            if re_find:
                return re_find
            else:
                return result

    def get_authentication_domain(self, **kwargs):
        """ Get domain of authentication """

        module = kwargs["module"]
        conf_str = CE_GET_AUTHENTICATION_DOMAIN

        xml_str = self.netconf_get_config(module=module, conf_str=conf_str)

        result = list()

        if "<data/>" in xml_str:
            return result
        else:
            re_find = re.findall(
                r'.*<domainName>(.*)</domainName>.*\s*'
                r'<authenSchemeName>(.*)</authenSchemeName>.*', xml_str)

            if re_find:
                return re_find
            else:
                return result

    def merge_authentication_scheme(self, **kwargs):
        """ Merge scheme of authentication """

        authen_scheme_name = kwargs["authen_scheme_name"]
        first_authen_mode = kwargs["first_authen_mode"]
        module = kwargs["module"]
        conf_str = CE_MERGE_AUTHENTICATION_SCHEME % (
            authen_scheme_name, first_authen_mode)

        xml = self.netconf_set_config(module=module, conf_str=conf_str)

        if "<ok/>" not in xml:
            module.fail_json(msg='Error: Merge authentication scheme failed.')

        cmds = []
        cmd = "authentication-scheme %s" % authen_scheme_name
        cmds.append(cmd)
        cmd = "authentication-mode %s" % first_authen_mode
        cmds.append(cmd)

        return cmds

    def merge_authentication_domain(self, **kwargs):
        """ Merge domain of authentication """

        domain_name = kwargs["domain_name"]
        authen_scheme_name = kwargs["authen_scheme_name"]
        module = kwargs["module"]
        conf_str = CE_MERGE_AUTHENTICATION_DOMAIN % (
            domain_name, authen_scheme_name)

        xml = self.netconf_set_config(module=module, conf_str=conf_str)

        if "<ok/>" not in xml:
            module.fail_json(msg='Error: Merge authentication domain failed.')

        cmds = []
        cmd = "domain %s" % domain_name
        cmds.append(cmd)
        cmd = "authentication-scheme %s" % authen_scheme_name
        cmds.append(cmd)

        return cmds

    def create_authentication_scheme(self, **kwargs):
        """ Create scheme of authentication """

        authen_scheme_name = kwargs["authen_scheme_name"]
        first_authen_mode = kwargs["first_authen_mode"]
        module = kwargs["module"]
        conf_str = CE_CREATE_AUTHENTICATION_SCHEME % (
            authen_scheme_name, first_authen_mode)

        xml = self.netconf_set_config(module=module, conf_str=conf_str)

        if "<ok/>" not in xml:
            module.fail_json(msg='Error: Create authentication scheme failed.')

        cmds = []
        cmd = "authentication-scheme %s" % authen_scheme_name
        cmds.append(cmd)
        cmd = "authentication-mode %s" % first_authen_mode
        cmds.append(cmd)

        return cmds

    def create_authentication_domain(self, **kwargs):
        """ Create domain of authentication """

        domain_name = kwargs["domain_name"]
        authen_scheme_name = kwargs["authen_scheme_name"]
        module = kwargs["module"]
        conf_str = CE_CREATE_AUTHENTICATION_DOMAIN % (
            domain_name, authen_scheme_name)

        xml = self.netconf_set_config(module=module, conf_str=conf_str)

        if "<ok/>" not in xml:
            module.fail_json(msg='Error: Create authentication domain failed.')

        cmds = []
        cmd = "domain %s" % domain_name
        cmds.append(cmd)
        cmd = "authentication-scheme %s" % authen_scheme_name
        cmds.append(cmd)

        return cmds

    def delete_authentication_scheme(self, **kwargs):
        """ Delete scheme of authentication """

        authen_scheme_name = kwargs["authen_scheme_name"]
        first_authen_mode = kwargs["first_authen_mode"]
        module = kwargs["module"]

        if authen_scheme_name == "default":
            return SUCCESS

        conf_str = CE_DELETE_AUTHENTICATION_SCHEME % (
            authen_scheme_name, first_authen_mode)

        xml = self.netconf_set_config(module=module, conf_str=conf_str)

        if "<ok/>" not in xml:
            module.fail_json(msg='Error: Delete authentication scheme failed.')

        cmds = []
        cmd = "undo authentication-scheme %s" % authen_scheme_name
        cmds.append(cmd)
        cmd = "authentication-mode none"
        cmds.append(cmd)

        return cmds

    def delete_authentication_domain(self, **kwargs):
        """ Delete domain of authentication """

        domain_name = kwargs["domain_name"]
        authen_scheme_name = kwargs["authen_scheme_name"]
        module = kwargs["module"]

        if domain_name == "default":
            return SUCCESS

        conf_str = CE_DELETE_AUTHENTICATION_DOMAIN % (
            domain_name, authen_scheme_name)

        xml = self.netconf_set_config(module=module, conf_str=conf_str)

        if "<ok/>" not in xml:
            module.fail_json(msg='Error: Delete authentication domain failed.')

        cmds = []
        cmd = "undo authentication-scheme"
        cmds.append(cmd)
        cmd = "undo domain %s" % domain_name
        cmds.append(cmd)

        return cmds

    def get_authorization_scheme(self, **kwargs):
        """ Get scheme of authorization """

        module = kwargs["module"]
        conf_str = CE_GET_AUTHORIZATION_SCHEME

        xml_str = self.netconf_get_config(module=module, conf_str=conf_str)
        result = list()

        if "<data/>" in xml_str:
            return result
        else:
            re_find = re.findall(
                r'.*<authorSchemeName>(.*)</authorSchemeName>.*\s*'
                r'<firstAuthorMode>(.*)</firstAuthorMode>.*\s*'
                r'<secondAuthorMode>(.*)</secondAuthorMode>.*\s*', xml_str)

            if re_find:
                return re_find
            else:
                return result

    def get_authorization_domain(self, **kwargs):
        """ Get domain of authorization """

        module = kwargs["module"]
        conf_str = CE_GET_AUTHORIZATION_DOMAIN

        xml_str = self.netconf_get_config(module=module, conf_str=conf_str)

        result = list()

        if "<data/>" in xml_str:
            return result
        else:
            re_find = re.findall(
                r'.*<domainName>(.*)</domainName>.*\s*'
                r'<authorSchemeName>(.*)</authorSchemeName>.*', xml_str)

            if re_find:
                return re_find
            else:
                return result

    def merge_authorization_scheme(self, **kwargs):
        """ Merge scheme of authorization """

        author_scheme_name = kwargs["author_scheme_name"]
        first_author_mode = kwargs["first_author_mode"]
        module = kwargs["module"]
        conf_str = CE_MERGE_AUTHORIZATION_SCHEME % (
            author_scheme_name, first_author_mode)

        xml = self.netconf_set_config(module=module, conf_str=conf_str)

        if "<ok/>" not in xml:
            module.fail_json(msg='Error: Merge authorization scheme failed.')

        cmds = []
        cmd = "authorization-scheme %s" % author_scheme_name
        cmds.append(cmd)
        cmd = "authorization-mode %s" % first_author_mode
        cmds.append(cmd)

        return cmds

    def merge_authorization_domain(self, **kwargs):
        """ Merge domain of authorization """

        domain_name = kwargs["domain_name"]
        author_scheme_name = kwargs["author_scheme_name"]
        module = kwargs["module"]
        conf_str = CE_MERGE_AUTHORIZATION_DOMAIN % (
            domain_name, author_scheme_name)

        xml = self.netconf_set_config(module=module, conf_str=conf_str)

        if "<ok/>" not in xml:
            module.fail_json(msg='Error: Merge authorization domain failed.')

        cmds = []
        cmd = "domain %s" % domain_name
        cmds.append(cmd)
        cmd = "authorization-scheme %s" % author_scheme_name
        cmds.append(cmd)

        return cmds

    def create_authorization_scheme(self, **kwargs):
        """ Create scheme of authorization """

        author_scheme_name = kwargs["author_scheme_name"]
        first_author_mode = kwargs["first_author_mode"]
        module = kwargs["module"]
        conf_str = CE_CREATE_AUTHORIZATION_SCHEME % (
            author_scheme_name, first_author_mode)

        xml = self.netconf_set_config(module=module, conf_str=conf_str)

        if "<ok/>" not in xml:
            module.fail_json(msg='Error: Create authorization scheme failed.')

        cmds = []
        cmd = "authorization-scheme %s" % author_scheme_name
        cmds.append(cmd)
        cmd = "authorization-mode %s" % first_author_mode
        cmds.append(cmd)

        return cmds

    def create_authorization_domain(self, **kwargs):
        """ Create domain of authorization """

        domain_name = kwargs["domain_name"]
        author_scheme_name = kwargs["author_scheme_name"]
        module = kwargs["module"]
        conf_str = CE_CREATE_AUTHORIZATION_DOMAIN % (
            domain_name, author_scheme_name)

        xml = self.netconf_set_config(module=module, conf_str=conf_str)

        if "<ok/>" not in xml:
            module.fail_json(msg='Error: Create authorization domain failed.')

        cmds = []
        cmd = "domain %s" % domain_name
        cmds.append(cmd)
        cmd = "authorization-scheme %s" % author_scheme_name
        cmds.append(cmd)

        return cmds

    def delete_authorization_scheme(self, **kwargs):
        """ Delete scheme of authorization """

        author_scheme_name = kwargs["author_scheme_name"]
        first_author_mode = kwargs["first_author_mode"]
        module = kwargs["module"]

        if author_scheme_name == "default":
            return SUCCESS

        conf_str = CE_DELETE_AUTHORIZATION_SCHEME % (
            author_scheme_name, first_author_mode)

        xml = self.netconf_set_config(module=module, conf_str=conf_str)

        if "<ok/>" not in xml:
            module.fail_json(msg='Error: Delete authorization scheme failed.')

        cmds = []
        cmd = "undo authorization-scheme %s" % author_scheme_name
        cmds.append(cmd)
        cmd = "authorization-mode none"
        cmds.append(cmd)

        return cmds

    def delete_authorization_domain(self, **kwargs):
        """ Delete domain of authorization """

        domain_name = kwargs["domain_name"]
        author_scheme_name = kwargs["author_scheme_name"]
        module = kwargs["module"]

        if domain_name == "default":
            return SUCCESS

        conf_str = CE_DELETE_AUTHORIZATION_DOMAIN % (
            domain_name, author_scheme_name)

        xml = self.netconf_set_config(module=module, conf_str=conf_str)

        if "<ok/>" not in xml:
            module.fail_json(msg='Error: Delete authorization domain failed.')

        cmds = []
        cmd = "undo authorization-scheme"
        cmds.append(cmd)
        cmd = "undo domain %s" % domain_name
        cmds.append(cmd)

        return cmds

    def get_accounting_scheme(self, **kwargs):
        """ Get scheme of accounting """

        module = kwargs["module"]
        conf_str = CE_GET_ACCOUNTING_SCHEME

        xml_str = self.netconf_get_config(module=module, conf_str=conf_str)
        result = list()

        if "<data/>" in xml_str:
            return result
        else:
            re_find = re.findall(r'.*<acctSchemeName>(.*)</acctSchemeName>\s*<accountingMode>(.*)</accountingMode>', xml_str)
            if re_find:
                return re_find
            else:
                return result

    def get_accounting_domain(self, **kwargs):
        """ Get domain of accounting """

        module = kwargs["module"]
        conf_str = CE_GET_ACCOUNTING_DOMAIN

        xml_str = self.netconf_get_config(module=module, conf_str=conf_str)

        result = list()

        if "<data/>" in xml_str:
            return result
        else:
            re_find = re.findall(
                r'.*<domainName>(.*)</domainName>.*\s*'
                r'<acctSchemeName>(.*)</acctSchemeName>.*', xml_str)

            if re_find:
                return re_find
            else:
                return result

    def merge_accounting_scheme(self, **kwargs):
        """ Merge scheme of accounting """

        acct_scheme_name = kwargs["acct_scheme_name"]
        accounting_mode = kwargs["accounting_mode"]
        module = kwargs["module"]
        conf_str = CE_MERGE_ACCOUNTING_SCHEME % (
            acct_scheme_name, accounting_mode)

        xml = self.netconf_set_config(module=module, conf_str=conf_str)

        if "<ok/>" not in xml:
            module.fail_json(msg='Error: Merge accounting scheme failed.')

        cmds = []
        cmd = "accounting-scheme %s" % acct_scheme_name
        cmds.append(cmd)
        cmd = "accounting-mode %s" % accounting_mode
        cmds.append(cmd)

        return cmds

    def merge_accounting_domain(self, **kwargs):
        """ Merge domain of accounting """

        domain_name = kwargs["domain_name"]
        acct_scheme_name = kwargs["acct_scheme_name"]
        module = kwargs["module"]
        conf_str = CE_MERGE_ACCOUNTING_DOMAIN % (domain_name, acct_scheme_name)

        xml = self.netconf_set_config(module=module, conf_str=conf_str)

        if "<ok/>" not in xml:
            module.fail_json(msg='Error: Merge accounting domain failed.')

        cmds = []
        cmd = "domain %s" % domain_name
        cmds.append(cmd)
        cmd = "accounting-scheme %s" % acct_scheme_name
        cmds.append(cmd)

        return cmds

    def create_accounting_scheme(self, **kwargs):
        """ Create scheme of accounting """

        acct_scheme_name = kwargs["acct_scheme_name"]
        accounting_mode = kwargs["accounting_mode"]
        module = kwargs["module"]
        conf_str = CE_CREATE_ACCOUNTING_SCHEME % (
            acct_scheme_name, accounting_mode)

        xml = self.netconf_set_config(module=module, conf_str=conf_str)

        if "<ok/>" not in xml:
            module.fail_json(msg='Error: Create accounting scheme failed.')

        cmds = []
        cmd = "accounting-scheme %s" % acct_scheme_name
        cmds.append(cmd)
        cmd = "accounting-mode %s" % accounting_mode
        cmds.append(cmd)

        return cmds

    def create_accounting_domain(self, **kwargs):
        """ Create domain of accounting """

        domain_name = kwargs["domain_name"]
        acct_scheme_name = kwargs["acct_scheme_name"]
        module = kwargs["module"]
        conf_str = CE_CREATE_ACCOUNTING_DOMAIN % (
            domain_name, acct_scheme_name)

        xml = self.netconf_set_config(module=module, conf_str=conf_str)

        if "<ok/>" not in xml:
            module.fail_json(msg='Error: Create accounting domain failed.')

        cmds = []
        cmd = "domain %s" % domain_name
        cmds.append(cmd)
        cmd = "accounting-scheme %s" % acct_scheme_name
        cmds.append(cmd)

        return cmds

    def delete_accounting_scheme(self, **kwargs):
        """ Delete scheme of accounting """

        acct_scheme_name = kwargs["acct_scheme_name"]
        accounting_mode = kwargs["accounting_mode"]
        module = kwargs["module"]

        if acct_scheme_name == "default":
            return SUCCESS

        conf_str = CE_DELETE_ACCOUNTING_SCHEME % (
            acct_scheme_name, accounting_mode)

        xml = self.netconf_set_config(module=module, conf_str=conf_str)

        if "<ok/>" not in xml:
            module.fail_json(msg='Error: Delete accounting scheme failed.')

        cmds = []
        cmd = "undo accounting-scheme %s" % acct_scheme_name
        cmds.append(cmd)
        cmd = "accounting-mode none"
        cmds.append(cmd)

        return cmds

    def delete_accounting_domain(self, **kwargs):
        """ Delete domain of accounting """

        domain_name = kwargs["domain_name"]
        acct_scheme_name = kwargs["acct_scheme_name"]
        module = kwargs["module"]

        if domain_name == "default":
            return SUCCESS

        conf_str = CE_DELETE_ACCOUNTING_DOMAIN % (
            domain_name, acct_scheme_name)

        xml = self.netconf_set_config(module=module, conf_str=conf_str)

        if "<ok/>" not in xml:
            module.fail_json(msg='Error: Delete accounting domain failed.')

        cmds = []
        cmd = "undo domain %s" % domain_name
        cmds.append(cmd)
        cmd = "undo accounting-scheme"
        cmds.append(cmd)

        return cmds

    def get_radius_template(self, **kwargs):
        """ Get radius template """

        module = kwargs["module"]
        conf_str = CE_GET_RADIUS_TEMPLATE

        xml_str = self.netconf_get_config(module=module, conf_str=conf_str)

        result = list()

        if "<data/>" in xml_str:
            return result
        else:
            re_find = re.findall(
                r'.*<groupName>(.*)</groupName>.*', xml_str)

            if re_find:
                return re_find
            else:
                return result

    def merge_radius_template(self, **kwargs):
        """ Merge radius template """

        radius_server_group = kwargs["radius_server_group"]
        module = kwargs["module"]
        conf_str = CE_MERGE_RADIUS_TEMPLATE % radius_server_group

        xml = self.netconf_set_config(module=module, conf_str=conf_str)

        if "<ok/>" not in xml:
            module.fail_json(msg='Error: Merge radius template failed.')

        cmds = []
        cmd = "radius server group %s" % radius_server_group
        cmds.append(cmd)

        return cmds

    def create_radius_template(self, **kwargs):
        """ Create radius template """

        radius_server_group = kwargs["radius_server_group"]
        module = kwargs["module"]
        conf_str = CE_CREATE_RADIUS_TEMPLATE % radius_server_group

        xml = self.netconf_set_config(module=module, conf_str=conf_str)

        if "<ok/>" not in xml:
            module.fail_json(msg='Error: Create radius template failed.')

        cmds = []
        cmd = "radius server group %s" % radius_server_group
        cmds.append(cmd)

        return cmds

    def delete_radius_template(self, **kwargs):
        """ Delete radius template """

        radius_server_group = kwargs["radius_server_group"]
        module = kwargs["module"]
        conf_str = CE_DELETE_RADIUS_TEMPLATE % radius_server_group

        xml = self.netconf_set_config(module=module, conf_str=conf_str)

        if "<ok/>" not in xml:
            module.fail_json(msg='Error: Delete radius template failed.')

        cmds = []
        cmd = "undo radius server group %s" % radius_server_group
        cmds.append(cmd)

        return cmds

    def get_radius_client(self, **kwargs):
        """ Get radius client """

        module = kwargs["module"]
        conf_str = CE_GET_RADIUS_CLIENT

        xml_str = self.netconf_get_config(module=module, conf_str=conf_str)

        result = list()

        if "<data/>" in xml_str:
            return result
        else:
            re_find = re.findall(
                r'.*<isEnable>(.*)</isEnable>.*', xml_str)

            if re_find:
                return re_find
            else:
                return result

    def merge_radius_client(self, **kwargs):
        """ Merge radius client """

        enable = kwargs["isEnable"]
        module = kwargs["module"]
        conf_str = CE_MERGE_RADIUS_CLIENT % enable

        xml = self.netconf_set_config(module=module, conf_str=conf_str)

        if "<ok/>" not in xml:
            module.fail_json(msg='Error: Merge radius client failed.')

        cmds = []
        if enable == "true":
            cmd = "radius enable"
        else:
            cmd = "undo radius enable"
        cmds.append(cmd)

        return cmds

    def get_hwtacacs_template(self, **kwargs):
        """ Get hwtacacs template """

        module = kwargs["module"]
        conf_str = CE_GET_HWTACACS_TEMPLATE

        xml_str = self.netconf_get_config(module=module, conf_str=conf_str)

        result = list()

        if "<data/>" in xml_str:
            return result
        else:
            re_find = re.findall(
                r'.*<templateName>(.*)</templateName>.*', xml_str)

            if re_find:
                return re_find
            else:
                return result

    def merge_hwtacacs_template(self, **kwargs):
        """ Merge hwtacacs template """

        hwtacas_template = kwargs["hwtacas_template"]
        module = kwargs["module"]
        conf_str = CE_MERGE_HWTACACS_TEMPLATE % hwtacas_template

        xml = self.netconf_set_config(module=module, conf_str=conf_str)

        if "<ok/>" not in xml:
            module.fail_json(msg='Error: Merge hwtacacs template failed.')

        cmds = []
        cmd = "hwtacacs server template %s" % hwtacas_template
        cmds.append(cmd)

        return cmds

    def create_hwtacacs_template(self, **kwargs):
        """ Create hwtacacs template """

        hwtacas_template = kwargs["hwtacas_template"]
        module = kwargs["module"]
        conf_str = CE_CREATE_HWTACACS_TEMPLATE % hwtacas_template

        xml = self.netconf_set_config(module=module, conf_str=conf_str)

        if "<ok/>" not in xml:
            module.fail_json(msg='Error: Create hwtacacs template failed.')

        cmds = []
        cmd = "hwtacacs server template %s" % hwtacas_template
        cmds.append(cmd)

        return cmds

    def delete_hwtacacs_template(self, **kwargs):
        """ Delete hwtacacs template """

        hwtacas_template = kwargs["hwtacas_template"]
        module = kwargs["module"]
        conf_str = CE_DELETE_HWTACACS_TEMPLATE % hwtacas_template

        xml = self.netconf_set_config(module=module, conf_str=conf_str)

        if "<ok/>" not in xml:
            module.fail_json(msg='Error: Delete hwtacacs template failed.')

        cmds = []
        cmd = "undo hwtacacs server template %s" % hwtacas_template
        cmds.append(cmd)

        return cmds

    def get_hwtacacs_global_cfg(self, **kwargs):
        """ Get hwtacacs global configure """

        module = kwargs["module"]
        conf_str = CE_GET_HWTACACS_GLOBAL_CFG

        xml_str = self.netconf_get_config(module=module, conf_str=conf_str)

        result = list()

        if "<data/>" in xml_str:
            return result
        else:
            re_find = re.findall(
                r'.*<isEnable>(.*)</isEnable>.*', xml_str)

            if re_find:
                return re_find
            else:
                return result

    def merge_hwtacacs_global_cfg(self, **kwargs):
        """ Merge hwtacacs global configure """

        enable = kwargs["isEnable"]
        module = kwargs["module"]
        conf_str = CE_MERGE_HWTACACS_GLOBAL_CFG % enable

        xml = self.netconf_set_config(module=module, conf_str=conf_str)

        if "<ok/>" not in xml:
            module.fail_json(msg='Error: Merge hwtacacs global config failed.')

        cmds = []

        if enable == "true":
            cmd = "hwtacacs enable"
        else:
            cmd = "undo hwtacacs enable"
        cmds.append(cmd)

        return cmds

    def get_local_user_group(self, **kwargs):
        """ Get local user group """

        module = kwargs["module"]
        conf_str = CE_GET_LOCAL_USER_GROUP

        xml_str = self.netconf_get_config(module=module, conf_str=conf_str)

        result = list()

        if "<data/>" in xml_str:
            return result
        else:
            re_find = re.findall(
                r'.*<userGroupName>(.*)</userGroupName>.*', xml_str)

            if re_find:
                return re_find
            else:
                return result

    def merge_local_user_group(self, **kwargs):
        """ Merge local user group """

        local_user_group = kwargs["local_user_group"]
        module = kwargs["module"]
        conf_str = CE_MERGE_LOCAL_USER_GROUP % local_user_group

        xml = self.netconf_set_config(module=module, conf_str=conf_str)

        if "<ok/>" not in xml:
            module.fail_json(msg='Error: Merge local user group failed.')

        cmds = []
        cmd = "user-group %s" % local_user_group
        cmds.append(cmd)

        return cmds

    def delete_local_user_group(self, **kwargs):
        """ Delete local user group """

        local_user_group = kwargs["local_user_group"]
        module = kwargs["module"]
        conf_str = CE_DELETE_LOCAL_USER_GROUP % local_user_group

        xml = self.netconf_set_config(module=module, conf_str=conf_str)

        if "<ok/>" not in xml:
            module.fail_json(msg='Error: Delete local user group failed.')

        cmds = []
        cmd = "undo user-group %s" % local_user_group
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
                msg='Error: invalid char %s is in the name %s.' % (item, name))


def check_module_argument(**kwargs):
    """ Check module argument """

    module = kwargs["module"]

    authen_scheme_name = module.params['authen_scheme_name']
    author_scheme_name = module.params['author_scheme_name']
    acct_scheme_name = module.params['acct_scheme_name']
    domain_name = module.params['domain_name']
    radius_server_group = module.params['radius_server_group']
    hwtacas_template = module.params['hwtacas_template']
    local_user_group = module.params['local_user_group']

    if authen_scheme_name:
        if len(authen_scheme_name) > 32:
            module.fail_json(
                msg='Error: authen_scheme_name %s '
                    'is large than 32.' % authen_scheme_name)
        check_name(module=module, name=authen_scheme_name,
                   invalid_char=INVALID_SCHEME_CHAR)

    if author_scheme_name:
        if len(author_scheme_name) > 32:
            module.fail_json(
                msg='Error: author_scheme_name %s '
                    'is large than 32.' % author_scheme_name)
        check_name(module=module, name=author_scheme_name,
                   invalid_char=INVALID_SCHEME_CHAR)

    if acct_scheme_name:
        if len(acct_scheme_name) > 32:
            module.fail_json(
                msg='Error: acct_scheme_name %s '
                    'is large than 32.' % acct_scheme_name)
        check_name(module=module, name=acct_scheme_name,
                   invalid_char=INVALID_SCHEME_CHAR)

    if domain_name:
        if len(domain_name) > 64:
            module.fail_json(
                msg='Error: domain_name %s '
                    'is large than 64.' % domain_name)
        check_name(module=module, name=domain_name,
                   invalid_char=INVALID_DOMAIN_CHAR)
        if domain_name == "-" or domain_name == "--":
            module.fail_json(msg='domain_name %s '
                                 'is invalid.' % domain_name)

    if radius_server_group and len(radius_server_group) > 32:
        module.fail_json(msg='Error: radius_server_group %s '
                             'is large than 32.' % radius_server_group)

    if hwtacas_template and len(hwtacas_template) > 32:
        module.fail_json(
            msg='Error: hwtacas_template %s '
                'is large than 32.' % hwtacas_template)

    if local_user_group:
        if len(local_user_group) > 32:
            module.fail_json(
                msg='Error: local_user_group %s '
                    'is large than 32.' % local_user_group)
        check_name(module=module, name=local_user_group, invalid_char=INVALID_GROUP_CHAR)


def main():
    """ Module main """

    argument_spec = dict(
        state=dict(choices=['present', 'absent'], default='present'),
        authen_scheme_name=dict(type='str'),
        first_authen_mode=dict(default='local', choices=['invalid', 'local', 'hwtacacs', 'radius', 'none']),
        author_scheme_name=dict(type='str'),
        first_author_mode=dict(default='local', choices=['invalid', 'local', 'hwtacacs', 'if-authenticated', 'none']),
        acct_scheme_name=dict(type='str'),
        accounting_mode=dict(default='none', choices=['invalid', 'hwtacacs', 'radius', 'none']),
        domain_name=dict(type='str'),
        radius_server_group=dict(type='str'),
        hwtacas_template=dict(type='str'),
        local_user_group=dict(type='str')
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

    state = module.params['state']
    authen_scheme_name = module.params['authen_scheme_name']
    first_authen_mode = module.params['first_authen_mode']
    author_scheme_name = module.params['author_scheme_name']
    first_author_mode = module.params['first_author_mode']
    acct_scheme_name = module.params['acct_scheme_name']
    accounting_mode = module.params['accounting_mode']
    domain_name = module.params['domain_name']
    radius_server_group = module.params['radius_server_group']
    hwtacas_template = module.params['hwtacas_template']
    local_user_group = module.params['local_user_group']

    ce_aaa_server = AaaServer()

    if not ce_aaa_server:
        module.fail_json(msg='Error: init module failed.')

    # get proposed
    proposed["state"] = state
    if authen_scheme_name:
        proposed["authen_scheme_name"] = authen_scheme_name
    if first_authen_mode:
        proposed["first_authen_mode"] = first_authen_mode
    if author_scheme_name:
        proposed["author_scheme_name"] = author_scheme_name
    if first_author_mode:
        proposed["first_author_mode"] = first_author_mode
    if acct_scheme_name:
        proposed["acct_scheme_name"] = acct_scheme_name
    if accounting_mode:
        proposed["accounting_mode"] = accounting_mode
    if domain_name:
        proposed["domain_name"] = domain_name
    if radius_server_group:
        proposed["radius_server_group"] = radius_server_group
    if hwtacas_template:
        proposed["hwtacas_template"] = hwtacas_template
    if local_user_group:
        proposed["local_user_group"] = local_user_group

    # authentication
    if authen_scheme_name:

        scheme_exist = ce_aaa_server.get_authentication_scheme(module=module)
        scheme_new = (authen_scheme_name.lower(), first_authen_mode.lower(), "invalid")

        existing["authentication scheme"] = scheme_exist

        if state == "present":
            # present authentication scheme
            if len(scheme_exist) == 0:
                cmd = ce_aaa_server.create_authentication_scheme(
                    module=module,
                    authen_scheme_name=authen_scheme_name,
                    first_authen_mode=first_authen_mode)

                updates.append(cmd)
                changed = True

            elif scheme_new not in scheme_exist:
                cmd = ce_aaa_server.merge_authentication_scheme(
                    module=module,
                    authen_scheme_name=authen_scheme_name,
                    first_authen_mode=first_authen_mode)
                updates.append(cmd)
                changed = True

            # present authentication domain
            if domain_name:
                domain_exist = ce_aaa_server.get_authentication_domain(
                    module=module)
                domain_new = (domain_name.lower(), authen_scheme_name.lower())

                if len(domain_exist) == 0:
                    cmd = ce_aaa_server.create_authentication_domain(
                        module=module,
                        domain_name=domain_name,
                        authen_scheme_name=authen_scheme_name)
                    updates.append(cmd)
                    changed = True

                elif domain_new not in domain_exist:
                    cmd = ce_aaa_server.merge_authentication_domain(
                        module=module,
                        domain_name=domain_name,
                        authen_scheme_name=authen_scheme_name)
                    updates.append(cmd)
                    changed = True

        else:
            # absent authentication scheme
            if not domain_name:
                if len(scheme_exist) == 0:
                    pass
                elif scheme_new not in scheme_exist:
                    pass
                else:
                    cmd = ce_aaa_server.delete_authentication_scheme(
                        module=module,
                        authen_scheme_name=authen_scheme_name,
                        first_authen_mode=first_authen_mode)
                    updates.append(cmd)
                    changed = True

            # absent authentication domain
            else:
                domain_exist = ce_aaa_server.get_authentication_domain(
                    module=module)
                domain_new = (domain_name.lower(), authen_scheme_name.lower())

                if len(domain_exist) == 0:
                    pass
                elif domain_new not in domain_exist:
                    pass
                else:
                    cmd = ce_aaa_server.delete_authentication_domain(
                        module=module,
                        domain_name=domain_name,
                        authen_scheme_name=authen_scheme_name)
                    updates.append(cmd)
                    changed = True

        scheme_end = ce_aaa_server.get_authentication_scheme(module=module)
        end_state["authentication scheme"] = scheme_end

    # authorization
    if author_scheme_name:

        scheme_exist = ce_aaa_server.get_authorization_scheme(module=module)
        scheme_new = (author_scheme_name.lower(), first_author_mode.lower(), "invalid")

        existing["authorization scheme"] = scheme_exist

        if state == "present":
            # present authorization scheme
            if len(scheme_exist) == 0:
                cmd = ce_aaa_server.create_authorization_scheme(
                    module=module,
                    author_scheme_name=author_scheme_name,
                    first_author_mode=first_author_mode)
                updates.append(cmd)
                changed = True
            elif scheme_new not in scheme_exist:
                cmd = ce_aaa_server.merge_authorization_scheme(
                    module=module,
                    author_scheme_name=author_scheme_name,
                    first_author_mode=first_author_mode)
                updates.append(cmd)
                changed = True

            # present authorization domain
            if domain_name:
                domain_exist = ce_aaa_server.get_authorization_domain(
                    module=module)
                domain_new = (domain_name.lower(), author_scheme_name.lower())

                if len(domain_exist) == 0:
                    cmd = ce_aaa_server.create_authorization_domain(
                        module=module,
                        domain_name=domain_name,
                        author_scheme_name=author_scheme_name)
                    updates.append(cmd)
                    changed = True
                elif domain_new not in domain_exist:
                    cmd = ce_aaa_server.merge_authorization_domain(
                        module=module,
                        domain_name=domain_name,
                        author_scheme_name=author_scheme_name)
                    updates.append(cmd)
                    changed = True

        else:
            # absent authorization scheme
            if not domain_name:
                if len(scheme_exist) == 0:
                    pass
                elif scheme_new not in scheme_exist:
                    pass
                else:
                    cmd = ce_aaa_server.delete_authorization_scheme(
                        module=module,
                        author_scheme_name=author_scheme_name,
                        first_author_mode=first_author_mode)
                    updates.append(cmd)
                    changed = True

            # absent authorization domain
            else:
                domain_exist = ce_aaa_server.get_authorization_domain(
                    module=module)
                domain_new = (domain_name.lower(), author_scheme_name.lower())

                if len(domain_exist) == 0:
                    pass
                elif domain_new not in domain_exist:
                    pass
                else:
                    cmd = ce_aaa_server.delete_authorization_domain(
                        module=module,
                        domain_name=domain_name,
                        author_scheme_name=author_scheme_name)
                    updates.append(cmd)
                    changed = True

        scheme_end = ce_aaa_server.get_authorization_scheme(module=module)
        end_state["authorization scheme"] = scheme_end

    # accounting
    if acct_scheme_name:

        scheme_exist = ce_aaa_server.get_accounting_scheme(module=module)
        scheme_new = (acct_scheme_name.lower(), accounting_mode.lower())

        existing["accounting scheme"] = scheme_exist

        if state == "present":
            # present accounting scheme
            if len(scheme_exist) == 0:
                cmd = ce_aaa_server.create_accounting_scheme(
                    module=module,
                    acct_scheme_name=acct_scheme_name,
                    accounting_mode=accounting_mode)
                updates.append(cmd)
                changed = True
            elif scheme_new not in scheme_exist:
                cmd = ce_aaa_server.merge_accounting_scheme(
                    module=module,
                    acct_scheme_name=acct_scheme_name,
                    accounting_mode=accounting_mode)
                updates.append(cmd)
                changed = True

            # present accounting domain
            if domain_name:
                domain_exist = ce_aaa_server.get_accounting_domain(
                    module=module)
                domain_new = (domain_name.lower(), acct_scheme_name.lower())

                if len(domain_exist) == 0:
                    cmd = ce_aaa_server.create_accounting_domain(
                        module=module,
                        domain_name=domain_name,
                        acct_scheme_name=acct_scheme_name)
                    updates.append(cmd)
                    changed = True
                elif domain_new not in domain_exist:
                    cmd = ce_aaa_server.merge_accounting_domain(
                        module=module,
                        domain_name=domain_name,
                        acct_scheme_name=acct_scheme_name)
                    updates.append(cmd)
                    changed = True

        else:
            # absent accounting scheme
            if not domain_name:
                if len(scheme_exist) == 0:
                    pass
                elif scheme_new not in scheme_exist:
                    pass
                else:
                    cmd = ce_aaa_server.delete_accounting_scheme(
                        module=module,
                        acct_scheme_name=acct_scheme_name,
                        accounting_mode=accounting_mode)
                    updates.append(cmd)
                    changed = True

            # absent accounting domain
            else:
                domain_exist = ce_aaa_server.get_accounting_domain(
                    module=module)
                domain_new = (domain_name.lower(), acct_scheme_name.lower())
                if len(domain_exist) == 0:
                    pass
                elif domain_new not in domain_exist:
                    pass
                else:
                    cmd = ce_aaa_server.delete_accounting_domain(
                        module=module,
                        domain_name=domain_name,
                        acct_scheme_name=acct_scheme_name)
                    updates.append(cmd)
                    changed = True

        scheme_end = ce_aaa_server.get_accounting_scheme(module=module)
        end_state["accounting scheme"] = scheme_end

    # radius group name
    if (authen_scheme_name and first_authen_mode.lower() == "radius") \
            or (acct_scheme_name and accounting_mode.lower() == "radius"):

        if not radius_server_group:
            module.fail_json(msg='please input radius_server_group when use radius.')

        rds_template_exist = ce_aaa_server.get_radius_template(module=module)
        rds_template_new = (radius_server_group)

        rds_enable_exist = ce_aaa_server.get_radius_client(module=module)

        existing["radius template"] = rds_template_exist
        existing["radius enable"] = rds_enable_exist

        if state == "present":
            # present radius group name
            if len(rds_template_exist) == 0:
                cmd = ce_aaa_server.create_radius_template(
                    module=module, radius_server_group=radius_server_group)
                updates.append(cmd)
                changed = True
            elif rds_template_new not in rds_template_exist:
                cmd = ce_aaa_server.merge_radius_template(
                    module=module, radius_server_group=radius_server_group)
                updates.append(cmd)
                changed = True

            rds_enable_new = ("true")
            if rds_enable_new not in rds_enable_exist:
                cmd = ce_aaa_server.merge_radius_client(
                    module=module, isEnable="true")
                updates.append(cmd)
                changed = True

        else:
            # absent radius group name
            if len(rds_template_exist) == 0:
                pass
            elif rds_template_new not in rds_template_exist:
                pass
            else:
                cmd = ce_aaa_server.delete_radius_template(
                    module=module, radius_server_group=radius_server_group)
                updates.append(cmd)
                changed = True

            rds_enable_new = ("false")
            if rds_enable_new not in rds_enable_exist:
                cmd = ce_aaa_server.merge_radius_client(
                    module=module, isEnable="false")
                updates.append(cmd)
                changed = True
            else:
                pass

        rds_template_end = ce_aaa_server.get_radius_template(module=module)
        end_state["radius template"] = rds_template_end

        rds_enable_end = ce_aaa_server.get_radius_client(module=module)
        end_state["radius enable"] = rds_enable_end

    tmp_scheme = author_scheme_name

    # hwtacas template
    if (authen_scheme_name and first_authen_mode.lower() == "hwtacacs") \
            or (tmp_scheme and first_author_mode.lower() == "hwtacacs") \
            or (acct_scheme_name and accounting_mode.lower() == "hwtacacs"):

        if not hwtacas_template:
            module.fail_json(
                msg='please input hwtacas_template when use hwtacas.')

        hwtacacs_exist = ce_aaa_server.get_hwtacacs_template(module=module)
        hwtacacs_new = (hwtacas_template)

        hwtacacs_enbale_exist = ce_aaa_server.get_hwtacacs_global_cfg(
            module=module)

        existing["hwtacacs template"] = hwtacacs_exist
        existing["hwtacacs enable"] = hwtacacs_enbale_exist

        if state == "present":
            # present hwtacas template
            if len(hwtacacs_exist) == 0:
                cmd = ce_aaa_server.create_hwtacacs_template(
                    module=module, hwtacas_template=hwtacas_template)
                updates.append(cmd)
                changed = True
            elif hwtacacs_new not in hwtacacs_exist:
                cmd = ce_aaa_server.merge_hwtacacs_template(
                    module=module, hwtacas_template=hwtacas_template)
                updates.append(cmd)
                changed = True

            hwtacacs_enbale_new = ("true")
            if hwtacacs_enbale_new not in hwtacacs_enbale_exist:
                cmd = ce_aaa_server.merge_hwtacacs_global_cfg(
                    module=module, isEnable="true")
                updates.append(cmd)
                changed = True

        else:
            # absent hwtacas template
            if len(hwtacacs_exist) == 0:
                pass
            elif hwtacacs_new not in hwtacacs_exist:
                pass
            else:
                cmd = ce_aaa_server.delete_hwtacacs_template(
                    module=module, hwtacas_template=hwtacas_template)
                updates.append(cmd)
                changed = True

            hwtacacs_enbale_new = ("false")
            if hwtacacs_enbale_new not in hwtacacs_enbale_exist:
                cmd = ce_aaa_server.merge_hwtacacs_global_cfg(
                    module=module, isEnable="false")
                updates.append(cmd)
                changed = True
            else:
                pass

        hwtacacs_end = ce_aaa_server.get_hwtacacs_template(module=module)
        end_state["hwtacacs template"] = hwtacacs_end

        hwtacacs_enable_end = ce_aaa_server.get_hwtacacs_global_cfg(
            module=module)
        end_state["hwtacacs enable"] = hwtacacs_enable_end

    # local user group
    if local_user_group:

        user_group_exist = ce_aaa_server.get_local_user_group(module=module)
        user_group_new = (local_user_group)

        existing["local user group"] = user_group_exist

        if state == "present":
            # present local user group
            if len(user_group_exist) == 0:
                cmd = ce_aaa_server.merge_local_user_group(
                    module=module, local_user_group=local_user_group)
                updates.append(cmd)
                changed = True
            elif user_group_new not in user_group_exist:
                cmd = ce_aaa_server.merge_local_user_group(
                    module=module, local_user_group=local_user_group)
                updates.append(cmd)
                changed = True

        else:
            # absent local user group
            if len(user_group_exist) == 0:
                pass
            elif user_group_new not in user_group_exist:
                pass
            else:
                cmd = ce_aaa_server.delete_local_user_group(
                    module=module, local_user_group=local_user_group)
                updates.append(cmd)
                changed = True

        user_group_end = ce_aaa_server.get_local_user_group(module=module)
        end_state["local user group"] = user_group_end

    results = dict()
    results['proposed'] = proposed
    results['existing'] = existing
    results['changed'] = changed
    results['end_state'] = end_state
    results['updates'] = updates

    module.exit_json(**results)


if __name__ == '__main__':
    main()
