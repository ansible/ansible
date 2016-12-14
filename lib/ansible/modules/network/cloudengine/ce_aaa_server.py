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
    authen_scheme_name:
        description:
            - authentication scheme name.
        required: false
        default: default
    first_authen_mode:
        description:
            - first authentication scheme mode.
        required: false
        default: local
        choices: ['invalid', 'local', 'hwtacacs', 'radius',  'none']
    author_scheme_name:
        description:
            - authorization scheme name.
        required: false
        default: default
    first_author_mode:
        description:
            - first authorization scheme mode.
        required: false
        default: local
        choices: ['invalid', 'local', 'hwtacacs', 'if-authenticated',  'none'
    acct_scheme_name:
        description:
            - accounting scheme name.
        required: false
        default: default
    accounting_mode:
        description:
            - accounting scheme mode.
        required: false
        default: none
        choices: ['invalid', 'hwtacacs', 'radius',  'none']
    domain_name:
        description:
            - domain name.
        required: false
        default: default
    group_name:
        description:
            - radius group name.
        required: false
        default: none
    hwtacas_template:
        description:
            - hwtacas template name.
        required: false
        default: none
'''

EXAMPLES = '''
# radius authentication Server Basic settings
  - name: "radius authentication Server Basic settings"
    ce_aaa_server:
        state:  present
        authen_scheme_name:  test1
        first_authen_mode:  radius
        group_name:  test2
        host:  {{inventory_hostname}}
        username:  {{username}}
        password:  {{password}}

# hwtacacs accounting Server Basic settings
  - name: "hwtacacs accounting Server Basic settings"
    ce_aaa_server:
        state:  present
        acct_scheme_name:  test1
        accounting_mode:  hwtacacs
        hwtacas_template:  test2
        host:  {{inventory_hostname}}
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
    sample: {"accounting_mode": "hwtacacs", "acct_scheme_name": "test1",
            "hwtacas_template": "test2", "state": "present"}
existing:
    description:
        - k/v pairs of existing aaa server
    type: dict
    sample: {"accounting scheme": [["hwtacacs"], ["default"]],
            "hwtacacs template": ["huawei"]}
end_state:
    description: k/v pairs of aaa params after module execution
    returned: always
    type: dict
    sample: {"accounting scheme": [["hwtacacs", "test1"]],
            "hwtacacs template": ["huawei", "test2"]}
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

INVALID_SCHEME_CHAR = [' ', '/', '\\', ':', '*', '?', '"', '|', '<', '>']
INVALID_DOMAIN_CHAR = [' ', '*', '?', '"', '\'']


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


class ce_aaa_server(object):
    """ ce_aaa_server """

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

    def get_authentication_scheme(self, **kwargs):
        """ get_authentication_scheme """

        module = kwargs["module"]
        conf_str = CE_GET_AUTHENTICATION_SCHEME

        con_obj = self.netconf_get_config(module=module, conf_str=conf_str)

        xml_str = con_obj.xml
        result = list()

        if "<data/>" in xml_str:
            return result
        else:
            re_find = re.findall(
                r'.*<firstAuthenMode>(.*)</firstAuthenMode>.*\s*'
                r'<secondAuthenMode>(.*)</secondAuthenMode>.*\s*'
                r'<authenSchemeName>(.*)</authenSchemeName>.*', xml_str)

            if re_find:
                return re_find
            else:
                return result

    def get_authentication_domain(self, **kwargs):
        """ get_authentication_domain """

        module = kwargs["module"]
        conf_str = CE_GET_AUTHENTICATION_DOMAIN

        con_obj = self.netconf_get_config(module=module, conf_str=conf_str)

        xml_str = con_obj.xml
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
        """ merge_authentication_scheme """

        authen_scheme_name = kwargs["authen_scheme_name"]
        first_authen_mode = kwargs["first_authen_mode"]
        module = kwargs["module"]
        conf_str = CE_MERGE_AUTHENTICATION_SCHEME % (
            authen_scheme_name, first_authen_mode)

        con_obj = self.netconf_set_config(module=module, conf_str=conf_str)

        if "<ok/>" not in con_obj.xml:
            module.fail_json(msg='merge authentication scheme failed.')

        return SUCCESS

    def merge_authentication_domain(self, **kwargs):
        """ merge_authentication_domain """

        domain_name = kwargs["domain_name"]
        authen_scheme_name = kwargs["authen_scheme_name"]
        module = kwargs["module"]
        conf_str = CE_MERGE_AUTHENTICATION_DOMAIN % (
            domain_name, authen_scheme_name)

        con_obj = self.netconf_set_config(module=module, conf_str=conf_str)

        if "<ok/>" not in con_obj.xml:
            module.fail_json(msg='merge authentication domain failed.')

        return SUCCESS

    def create_authentication_scheme(self, **kwargs):
        """ create_authentication_scheme """

        authen_scheme_name = kwargs["authen_scheme_name"]
        first_authen_mode = kwargs["first_authen_mode"]
        module = kwargs["module"]
        conf_str = CE_CREATE_AUTHENTICATION_SCHEME % (
            authen_scheme_name, first_authen_mode)

        con_obj = self.netconf_set_config(module=module, conf_str=conf_str)

        if "<ok/>" not in con_obj.xml:
            module.fail_json(msg='create authentication scheme failed.')

        return SUCCESS

    def create_authentication_domain(self, **kwargs):
        """ create_authentication_domain """

        domain_name = kwargs["domain_name"]
        authen_scheme_name = kwargs["authen_scheme_name"]
        module = kwargs["module"]
        conf_str = CE_CREATE_AUTHENTICATION_DOMAIN % (
            domain_name, authen_scheme_name)

        con_obj = self.netconf_set_config(module=module, conf_str=conf_str)

        if "<ok/>" not in con_obj.xml:
            module.fail_json(msg='create authentication domain failed.')

        return SUCCESS

    def delete_authentication_scheme(self, **kwargs):
        """ delete_authentication_scheme """

        authen_scheme_name = kwargs["authen_scheme_name"]
        first_authen_mode = kwargs["first_authen_mode"]
        module = kwargs["module"]

        if authen_scheme_name == "default":
            return SUCCESS

        conf_str = CE_DELETE_AUTHENTICATION_SCHEME % (
            authen_scheme_name, first_authen_mode)

        con_obj = self.netconf_set_config(module=module, conf_str=conf_str)

        if "<ok/>" not in con_obj.xml:
            module.fail_json(msg='delete authentication scheme failed.')

        return SUCCESS

    def delete_authentication_domain(self, **kwargs):
        """ delete_authentication_domain """

        domain_name = kwargs["domain_name"]
        authen_scheme_name = kwargs["authen_scheme_name"]
        module = kwargs["module"]

        if domain_name == "default":
            return SUCCESS

        conf_str = CE_DELETE_AUTHENTICATION_DOMAIN % (
            domain_name, authen_scheme_name)

        con_obj = self.netconf_set_config(module=module, conf_str=conf_str)

        if "<ok/>" not in con_obj.xml:
            module.fail_json(msg='delete authentication domain failed.')

        return SUCCESS

    def get_authorization_scheme(self, **kwargs):
        """ get_authorization_scheme """

        module = kwargs["module"]
        conf_str = CE_GET_AUTHORIZATION_SCHEME

        con_obj = self.netconf_get_config(module=module, conf_str=conf_str)

        xml_str = con_obj.xml
        result = list()

        if "<data/>" in xml_str:
            return result
        else:
            re_find = re.findall(
                r'.*<firstAuthorMode>(.*)</firstAuthorMode>.*\s*'
                r'<secondAuthorMode>(.*)</secondAuthorMode>.*\s*'
                r'<authorSchemeName>(.*)</authorSchemeName>.*', xml_str)

            if re_find:
                return re_find
            else:
                return result

    def get_authorization_domain(self, **kwargs):
        """ get_authorization_domain """

        module = kwargs["module"]
        conf_str = CE_GET_AUTHORIZATION_DOMAIN

        con_obj = self.netconf_get_config(module=module, conf_str=conf_str)

        xml_str = con_obj.xml
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
        """ merge_authorization_scheme """

        author_scheme_name = kwargs["author_scheme_name"]
        first_author_mode = kwargs["first_author_mode"]
        module = kwargs["module"]
        conf_str = CE_MERGE_AUTHORIZATION_SCHEME % (
            author_scheme_name, first_author_mode)

        con_obj = self.netconf_set_config(module=module, conf_str=conf_str)

        if "<ok/>" not in con_obj.xml:
            module.fail_json(msg='merge authorization scheme failed.')

        return SUCCESS

    def merge_authorization_domain(self, **kwargs):
        """ merge_authorization_domain """

        domain_name = kwargs["domain_name"]
        author_scheme_name = kwargs["author_scheme_name"]
        module = kwargs["module"]
        conf_str = CE_MERGE_AUTHORIZATION_DOMAIN % (
            domain_name, author_scheme_name)

        con_obj = self.netconf_set_config(module=module, conf_str=conf_str)

        if "<ok/>" not in con_obj.xml:
            module.fail_json(msg='merge authorization domain failed.')

        return SUCCESS

    def create_authorization_scheme(self, **kwargs):
        """ create_authorization_scheme """

        author_scheme_name = kwargs["author_scheme_name"]
        first_author_mode = kwargs["first_author_mode"]
        module = kwargs["module"]
        conf_str = CE_CREATE_AUTHORIZATION_SCHEME % (
            author_scheme_name, first_author_mode)

        con_obj = self.netconf_set_config(module=module, conf_str=conf_str)

        if "<ok/>" not in con_obj.xml:
            module.fail_json(msg='create authorization scheme failed.')

        return SUCCESS

    def create_authorization_domain(self, **kwargs):
        """ create_authorization_domain """

        domain_name = kwargs["domain_name"]
        author_scheme_name = kwargs["author_scheme_name"]
        module = kwargs["module"]
        conf_str = CE_CREATE_AUTHORIZATION_DOMAIN % (
            domain_name, author_scheme_name)

        con_obj = self.netconf_set_config(module=module, conf_str=conf_str)

        if "<ok/>" not in con_obj.xml:
            module.fail_json(msg='create authorization domain failed.')

        return SUCCESS

    def delete_authorization_scheme(self, **kwargs):
        """ delete_authorization_scheme """

        author_scheme_name = kwargs["author_scheme_name"]
        first_author_mode = kwargs["first_author_mode"]
        module = kwargs["module"]

        if author_scheme_name == "default":
            return SUCCESS

        conf_str = CE_DELETE_AUTHORIZATION_SCHEME % (
            author_scheme_name, first_author_mode)

        con_obj = self.netconf_set_config(module=module, conf_str=conf_str)

        if "<ok/>" not in con_obj.xml:
            module.fail_json(msg='delete authorization scheme failed.')

        return SUCCESS

    def delete_authorization_domain(self, **kwargs):
        """ delete_authorization_domain """

        domain_name = kwargs["domain_name"]
        author_scheme_name = kwargs["author_scheme_name"]
        module = kwargs["module"]

        if domain_name == "default":
            return SUCCESS

        conf_str = CE_DELETE_AUTHORIZATION_DOMAIN % (
            domain_name, author_scheme_name)

        con_obj = self.netconf_set_config(module=module, conf_str=conf_str)

        if "<ok/>" not in con_obj.xml:
            module.fail_json(msg='delete authorization domian failed.')

        return SUCCESS

    def get_accounting_scheme(self, **kwargs):
        """ get_accounting_scheme """

        module = kwargs["module"]
        conf_str = CE_GET_ACCOUNTING_SCHEME

        con_obj = self.netconf_get_config(module=module, conf_str=conf_str)

        xml_str = con_obj.xml
        result = list()

        if "<data/>" in xml_str:
            return result
        else:
            re_find = re.findall(
                r'.*<accountingMode>(.*)</accountingMode>.*\s*'
                r'<acctSchemeName>(.*)</acctSchemeName>.*', xml_str)

            if re_find:
                return re_find
            else:
                return result

    def get_accounting_domain(self, **kwargs):
        """ get_accounting_domain """

        module = kwargs["module"]
        conf_str = CE_GET_ACCOUNTING_DOMAIN

        con_obj = self.netconf_get_config(module=module, conf_str=conf_str)

        xml_str = con_obj.xml
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
        """ merge_accounting_scheme """

        acct_scheme_name = kwargs["acct_scheme_name"]
        accounting_mode = kwargs["accounting_mode"]
        module = kwargs["module"]
        conf_str = CE_MERGE_ACCOUNTING_SCHEME % (
            acct_scheme_name, accounting_mode)

        con_obj = self.netconf_set_config(module=module, conf_str=conf_str)

        if "<ok/>" not in con_obj.xml:
            module.fail_json(msg='merge accounting scheme failed.')

        return SUCCESS

    def merge_accounting_domain(self, **kwargs):
        """ merge_accounting_domain """

        domain_name = kwargs["domain_name"]
        acct_scheme_name = kwargs["acct_scheme_name"]
        module = kwargs["module"]
        conf_str = CE_MERGE_ACCOUNTING_DOMAIN % (domain_name, acct_scheme_name)

        con_obj = self.netconf_set_config(module=module, conf_str=conf_str)

        if "<ok/>" not in con_obj.xml:
            module.fail_json(msg='merge accounting domain failed.')

        return SUCCESS

    def create_accounting_scheme(self, **kwargs):
        """ create_accounting_scheme """

        acct_scheme_name = kwargs["acct_scheme_name"]
        accounting_mode = kwargs["accounting_mode"]
        module = kwargs["module"]
        conf_str = CE_CREATE_ACCOUNTING_SCHEME % (
            acct_scheme_name, accounting_mode)

        con_obj = self.netconf_set_config(module=module, conf_str=conf_str)

        if "<ok/>" not in con_obj.xml:
            module.fail_json(msg='create accounting scheme failed.')

        return SUCCESS

    def create_accounting_domain(self, **kwargs):
        """ create_accounting_domain """

        domain_name = kwargs["domain_name"]
        acct_scheme_name = kwargs["acct_scheme_name"]
        module = kwargs["module"]
        conf_str = CE_CREATE_ACCOUNTING_DOMAIN % (
            domain_name, acct_scheme_name)

        con_obj = self.netconf_set_config(module=module, conf_str=conf_str)

        if "<ok/>" not in con_obj.xml:
            module.fail_json(msg='create accounting domain failed.')

        return SUCCESS

    def delete_accounting_scheme(self, **kwargs):
        """ delete_accounting_scheme """

        acct_scheme_name = kwargs["acct_scheme_name"]
        accounting_mode = kwargs["accounting_mode"]
        module = kwargs["module"]

        if acct_scheme_name == "default":
            return SUCCESS

        conf_str = CE_DELETE_ACCOUNTING_SCHEME % (
            acct_scheme_name, accounting_mode)

        con_obj = self.netconf_set_config(module=module, conf_str=conf_str)

        if "<ok/>" not in con_obj.xml:
            module.fail_json(msg='delete accounting scheme failed.')

        return SUCCESS

    def delete_accounting_domain(self, **kwargs):
        """ delete_accounting_domain """

        domain_name = kwargs["domain_name"]
        acct_scheme_name = kwargs["acct_scheme_name"]
        module = kwargs["module"]

        if domain_name == "default":
            return SUCCESS

        conf_str = CE_DELETE_ACCOUNTING_DOMAIN % (
            domain_name, acct_scheme_name)

        con_obj = self.netconf_set_config(module=module, conf_str=conf_str)

        if "<ok/>" not in con_obj.xml:
            module.fail_json(msg='delete accounting domain failed.')

        return SUCCESS

    def get_radius_template(self, **kwargs):
        """ get_radius_template """

        module = kwargs["module"]
        conf_str = CE_GET_RADIUS_TEMPLATE

        con_obj = self.netconf_get_config(module=module, conf_str=conf_str)

        xml_str = con_obj.xml
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
        """ merge_radius_template """

        group_name = kwargs["group_name"]
        module = kwargs["module"]
        conf_str = CE_MERGE_RADIUS_TEMPLATE % group_name

        con_obj = self.netconf_set_config(module=module, conf_str=conf_str)

        if "<ok/>" not in con_obj.xml:
            module.fail_json(msg='merge radius template failed.')

        return SUCCESS

    def create_radius_template(self, **kwargs):
        """ create_radius_template """

        group_name = kwargs["group_name"]
        module = kwargs["module"]
        conf_str = CE_CREATE_RADIUS_TEMPLATE % group_name

        con_obj = self.netconf_set_config(module=module, conf_str=conf_str)

        if "<ok/>" not in con_obj.xml:
            module.fail_json(msg='create radius template failed.')

        return SUCCESS

    def delete_radius_template(self, **kwargs):
        """ delete_radius_template """

        group_name = kwargs["group_name"]
        module = kwargs["module"]
        conf_str = CE_DELETE_RADIUS_TEMPLATE % group_name

        con_obj = self.netconf_set_config(module=module, conf_str=conf_str)

        if "<ok/>" not in con_obj.xml:
            module.fail_json(msg='delete radius template failed.')

        return SUCCESS

    def get_radius_client(self, **kwargs):
        """ get_radius_client """

        module = kwargs["module"]
        conf_str = CE_GET_RADIUS_CLIENT

        con_obj = self.netconf_get_config(module=module, conf_str=conf_str)

        xml_str = con_obj.xml
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
        """ merge_radius_client """

        isEnable = kwargs["isEnable"]
        module = kwargs["module"]
        conf_str = CE_MERGE_RADIUS_CLIENT % isEnable

        con_obj = self.netconf_set_config(module=module, conf_str=conf_str)

        if "<ok/>" not in con_obj.xml:
            module.fail_json(msg='merge radius client failed.')

        return SUCCESS

    def get_hwtacacs_template(self, **kwargs):
        """ get_hwtacacs_template """

        module = kwargs["module"]
        conf_str = CE_GET_HWTACACS_TEMPLATE

        con_obj = self.netconf_get_config(module=module, conf_str=conf_str)

        xml_str = con_obj.xml
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
        """ merge_hwtacacs_template """

        hwtacas_template = kwargs["hwtacas_template"]
        module = kwargs["module"]
        conf_str = CE_MERGE_HWTACACS_TEMPLATE % hwtacas_template

        con_obj = self.netconf_set_config(module=module, conf_str=conf_str)

        if "<ok/>" not in con_obj.xml:
            module.fail_json(msg='merge hwtacacs template failed.')

        return SUCCESS

    def create_hwtacacs_template(self, **kwargs):
        """ create_hwtacacs_template """

        hwtacas_template = kwargs["hwtacas_template"]
        module = kwargs["module"]
        conf_str = CE_CREATE_HWTACACS_TEMPLATE % hwtacas_template

        con_obj = self.netconf_set_config(module=module, conf_str=conf_str)

        if "<ok/>" not in con_obj.xml:
            module.fail_json(msg='create hwtacacs template failed.')

        return SUCCESS

    def delete_hwtacacs_template(self, **kwargs):
        """ delete_hwtacacs_template """

        hwtacas_template = kwargs["hwtacas_template"]
        module = kwargs["module"]
        conf_str = CE_DELETE_HWTACACS_TEMPLATE % hwtacas_template

        con_obj = self.netconf_set_config(module=module, conf_str=conf_str)

        if "<ok/>" not in con_obj.xml:
            module.fail_json(msg='delete hwtacacs template failed.')

        return SUCCESS

    def get_hwtacacs_global_cfg(self, **kwargs):
        """ get_hwtacacs_global_cfg """

        module = kwargs["module"]
        conf_str = CE_GET_HWTACACS_GLOBAL_CFG

        con_obj = self.netconf_get_config(module=module, conf_str=conf_str)

        xml_str = con_obj.xml
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
        """ merge_hwtacacs_global_cfg """

        isEnable = kwargs["isEnable"]
        module = kwargs["module"]
        conf_str = CE_MERGE_HWTACACS_GLOBAL_CFG % isEnable

        con_obj = self.netconf_set_config(module=module, conf_str=conf_str)

        if "<ok/>" not in con_obj.xml:
            module.fail_json(msg='merge hwtacacs global config failed.')

        return SUCCESS


def get_ce_aaa_server(**kwargs):
    """ get_ce_aaa_server """

    return ce_aaa_server(**kwargs)


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

    authen_scheme_name = module.params['authen_scheme_name']
    author_scheme_name = module.params['author_scheme_name']
    acct_scheme_name = module.params['acct_scheme_name']
    domain_name = module.params['domain_name']
    group_name = module.params['group_name']
    hwtacas_template = module.params['hwtacas_template']

    if authen_scheme_name:
        if len(authen_scheme_name) > 32:
            module.fail_json(
                msg='authen_scheme_name %s '
                    'is large than 32.' % authen_scheme_name)
        check_name(module=module, name=authen_scheme_name,
                   invalid_char=INVALID_SCHEME_CHAR)

    if author_scheme_name:
        if len(author_scheme_name) > 32:
            module.fail_json(
                msg='author_scheme_name %s '
                    'is large than 32.' % author_scheme_name)
        check_name(module=module, name=author_scheme_name,
                   invalid_char=INVALID_SCHEME_CHAR)

    if acct_scheme_name:
        if len(acct_scheme_name) > 32:
            module.fail_json(
                msg='acct_scheme_name %s '
                    'is large than 32.' % acct_scheme_name)
        check_name(module=module, name=acct_scheme_name,
                   invalid_char=INVALID_SCHEME_CHAR)

    if domain_name:
        if len(domain_name) > 64:
            module.fail_json(
                msg='domain_name %s '
                    'is large than 64.' % domain_name)
        check_name(module=module, name=domain_name,
                   invalid_char=INVALID_DOMAIN_CHAR)
        if domain_name == "-" or domain_name == "--":
            module.fail_json(msg='domain_name %s '
                                 'is invalid.' % domain_name)

    if group_name and len(group_name) > 32:
        module.fail_json(msg='group_name %s '
                             'is large than 32.' % group_name)

    if hwtacas_template and len(hwtacas_template) > 32:
        module.fail_json(
            msg='hwtacas_template %s '
                'is large than 32.' % hwtacas_template)


def main():
    """ main """

    start_time = datetime.datetime.now()

    argument_spec = dict(
        state=dict(choices=['present', 'absent'],
                   default='present'),
        host=dict(required=True),
        username=dict(required=True),
        password=dict(required=True),
        authen_scheme_name=dict(type='str'),
        first_authen_mode=dict(choices=['invalid', 'local',
                                        'hwtacacs', 'radius', 'none'],
                               default='local'),
        author_scheme_name=dict(type='str'),
        first_author_mode=dict(choices=['invalid', 'local',
                                        'hwtacacs', 'if-authenticated', 'none'],
                               default='local'),
        acct_scheme_name=dict(type='str'),
        accounting_mode=dict(choices=['invalid', 'hwtacacs',
                                      'radius', 'none'],
                             default='none'),
        domain_name=dict(type='str'),
        group_name=dict(type='str'),
        hwtacas_template=dict(type='str')
    )

    if not HAS_NCCLIENT:
        raise Exception("the ncclient library is required")

    module = NetworkModule(argument_spec=argument_spec,
                        supports_check_mode=True)

    check_module_argument(module=module)

    state = module.params['state']
    host = module.params['host']
    port = module.params['port']
    username = module.params['username']
    password = module.params['password']
    authen_scheme_name = module.params['authen_scheme_name']
    first_authen_mode = module.params['first_authen_mode']
    author_scheme_name = module.params['author_scheme_name']
    first_author_mode = module.params['first_author_mode']
    acct_scheme_name = module.params['acct_scheme_name']
    accounting_mode = module.params['accounting_mode']
    domain_name = module.params['domain_name']
    group_name = module.params['group_name']
    hwtacas_template = module.params['hwtacas_template']

    ce_aaa_server = get_ce_aaa_server(
        host=host, port=port, username=username, password=password)

    if not ce_aaa_server:
        module.fail_json(msg='init module failed.')

    args = dict(authen_scheme_name=authen_scheme_name,
                first_authen_mode=first_authen_mode,
                author_scheme_name=author_scheme_name,
                first_author_mode=first_author_mode,
                acct_scheme_name=acct_scheme_name,
                accounting_mode=accounting_mode,
                domain_name=domain_name,
                group_name=group_name,
                hwtacas_template=hwtacas_template,
                state=state)

    changed = False
    proposed = dict((k, v) for k, v in args.iteritems() if v is not None)
    existing = dict()
    end_state = dict()

    # authentication
    if authen_scheme_name:

        scheme_exist = ce_aaa_server.get_authentication_scheme(module=module)
        scheme_new = (first_authen_mode.lower(), "invalid",
                      authen_scheme_name.lower())

        existing["authentication scheme"] = scheme_exist

        if state == "present":
            # present authentication scheme
            if len(scheme_exist) == 0:
                ce_aaa_server.create_authentication_scheme(
                    module=module,
                    authen_scheme_name=authen_scheme_name,
                    first_authen_mode=first_authen_mode)

            elif scheme_new not in scheme_exist:
                ce_aaa_server.merge_authentication_scheme(
                    module=module,
                    authen_scheme_name=authen_scheme_name,
                    first_authen_mode=first_authen_mode)

            else:
                pass

            # present authentication domain
            if domain_name:
                domain_exist = ce_aaa_server.get_authentication_domain(
                    module=module)
                domain_new = (domain_name.lower(), authen_scheme_name.lower())

                if len(domain_exist) == 0:
                    ce_aaa_server.create_authentication_domain(
                        module=module,
                        domain_name=domain_name,
                        authen_scheme_name=authen_scheme_name)

                elif domain_new not in domain_exist:
                    ce_aaa_server.merge_authentication_domain(
                        module=module,
                        domain_name=domain_name,
                        authen_scheme_name=authen_scheme_name)

                else:
                    pass

        else:
            # absent authentication scheme
            if len(scheme_exist) == 0:
                pass
            elif scheme_new not in scheme_exist:
                pass
            else:
                ce_aaa_server.delete_authentication_scheme(
                    module=module,
                    authen_scheme_name=authen_scheme_name,
                    first_authen_mode=first_authen_mode)

            # absent authentication domain
            if domain_name:
                domain_exist = ce_aaa_server.get_authentication_domain(
                    module=module)
                domain_new = (domain_name.lower(), authen_scheme_name.lower())

                if len(domain_exist) == 0:
                    pass
                elif domain_new not in domain_exist:
                    pass
                else:
                    ce_aaa_server.delete_authentication_domain(
                        module=module,
                        domain_name=domain_name,
                        authen_scheme_name=authen_scheme_name)

        scheme_end = ce_aaa_server.get_authentication_scheme(module=module)
        end_state["authentication scheme"] = scheme_end

        if changed == False:
            scheme_exist.sort()
            scheme_end.sort()

            if scheme_exist != scheme_end:
                changed = True

    # authorization
    if author_scheme_name:

        scheme_exist = ce_aaa_server.get_authorization_scheme(module=module)
        scheme_new = (first_author_mode.lower(), "invalid",
                      author_scheme_name.lower())

        existing["authorization scheme"] = scheme_exist

        if state == "present":
            # present authorization scheme
            if len(scheme_exist) == 0:
                ce_aaa_server.create_authorization_scheme(
                    module=module,
                    author_scheme_name=author_scheme_name,
                    first_author_mode=first_author_mode)
            elif scheme_new not in scheme_exist:
                ce_aaa_server.merge_authorization_scheme(
                    module=module,
                    author_scheme_name=author_scheme_name,
                    first_author_mode=first_author_mode)
            else:
                pass

            # present authorization domain
            if domain_name:
                domain_exist = ce_aaa_server.get_authorization_domain(
                    module=module)
                domain_new = (domain_name.lower(), author_scheme_name.lower())

                if len(domain_exist) == 0:
                    ce_aaa_server.create_authorization_domain(
                        module=module,
                        domain_name=domain_name,
                        author_scheme_name=author_scheme_name)
                elif domain_new not in domain_exist:
                    ce_aaa_server.merge_authorization_domain(
                        module=module,
                        domain_name=domain_name,
                        author_scheme_name=author_scheme_name)
                else:
                    pass

        else:
            # absent authorization scheme
            if len(scheme_exist) == 0:
                pass
            elif scheme_new not in scheme_exist:
                pass
            else:
                ce_aaa_server.delete_authorization_scheme(
                    module=module,
                    author_scheme_name=author_scheme_name,
                    first_author_mode=first_author_mode)

            # absent authorization domain
            if domain_name:
                domain_exist = ce_aaa_server.get_authorization_domain(
                    module=module)
                domain_new = (domain_name.lower(), author_scheme_name.lower())

                if len(domain_exist) == 0:
                    pass
                elif domain_new not in domain_exist:
                    pass
                else:
                    ce_aaa_server.delete_authorization_domain(
                        module=module,
                        domain_name=domain_name,
                        author_scheme_name=author_scheme_name)

        scheme_end = ce_aaa_server.get_authorization_scheme(module=module)
        end_state["authorization scheme"] = scheme_end

        if changed == False:
            scheme_exist.sort()
            scheme_end.sort()

            if scheme_exist != scheme_end:
                changed = True

    # accounting
    if acct_scheme_name:

        scheme_exist = ce_aaa_server.get_accounting_scheme(module=module)
        scheme_new = (accounting_mode.lower(), acct_scheme_name.lower())

        existing["accounting scheme"] = scheme_exist

        if state == "present":
            # present accounting scheme
            if len(scheme_exist) == 0:
                ce_aaa_server.create_accounting_scheme(
                    module=module,
                    acct_scheme_name=acct_scheme_name,
                    accounting_mode=accounting_mode)
            elif scheme_new not in scheme_exist:
                ce_aaa_server.merge_accounting_scheme(
                    module=module,
                    acct_scheme_name=acct_scheme_name,
                    accounting_mode=accounting_mode)
            else:
                pass

            # present accounting domain
            if domain_name:
                domain_exist = ce_aaa_server.get_accounting_domain(
                    module=module)
                domain_new = (domain_name.lower(), acct_scheme_name.lower())

                if len(domain_exist) == 0:
                    ce_aaa_server.create_accounting_domain(
                        module=module,
                        domain_name=domain_name,
                        acct_scheme_name=acct_scheme_name)
                elif domain_new not in domain_exist:
                    ce_aaa_server.merge_accounting_domain(
                        module=module,
                        domain_name=domain_name,
                        acct_scheme_name=acct_scheme_name)
                else:
                    pass

        else:
            # absent accounting scheme
            if len(scheme_exist) == 0:
                pass
            elif scheme_new not in scheme_exist:
                pass
            else:
                ce_aaa_server.delete_accounting_scheme(
                    module=module,
                    acct_scheme_name=acct_scheme_name,
                    accounting_mode=accounting_mode)

            # absent accounting domain
            if domain_name:
                domain_exist = ce_aaa_server.get_accounting_domain(
                    module=module)
                domain_new = (domain_name.lower(), acct_scheme_name.lower())
                if len(domain_exist) == 0:
                    pass
                elif domain_new not in domain_exist:
                    pass
                else:
                    ce_aaa_server.delete_accounting_domain(
                        module=module,
                        domain_name=domain_name,
                        acct_scheme_name=acct_scheme_name)

        scheme_end = ce_aaa_server.get_accounting_scheme(module=module)
        end_state["accounting scheme"] = scheme_end

        if changed == False:
            scheme_exist.sort()
            scheme_end.sort()

            if scheme_exist != scheme_end:
                changed = True

    # radius group name
    if (authen_scheme_name and first_authen_mode.lower() == "radius") \
            or (acct_scheme_name and accounting_mode.lower() == "radius"):

        if not group_name:
            module.fail_json(msg='please input group_name when use radius.')

        rds_template_exist = ce_aaa_server.get_radius_template(module=module)
        rds_template_new = (group_name)

        rds_enable_exist = ce_aaa_server.get_radius_client(module=module)

        existing["radius template"] = rds_template_exist
        existing["radius enable"] = rds_enable_exist

        if state == "present":
            # present radius group name
            if len(rds_template_exist) == 0:
                ce_aaa_server.create_radius_template(
                    module=module, group_name=group_name)
            elif rds_template_new not in rds_template_exist:
                ce_aaa_server.merge_radius_template(
                    module=module, group_name=group_name)
            else:
                pass

            rds_enable_new = ("true")
            if rds_enable_new not in rds_enable_exist:
                ce_aaa_server.merge_radius_client(
                    module=module, isEnable="true")
            else:
                pass

        else:
            # absent radius group name
            if len(rds_template_exist) == 0:
                pass
            elif rds_template_new not in rds_template_exist:
                pass
            else:
                ce_aaa_server.delete_radius_template(
                    module=module, group_name=group_name)

            rds_enable_new = ("false")
            if rds_enable_new not in rds_enable_exist:
                ce_aaa_server.merge_radius_client(
                    module=module, isEnable="false")
            else:
                pass

        rds_template_end = ce_aaa_server.get_radius_template(module=module)
        end_state["radius template"] = rds_template_end

        rds_enable_end = ce_aaa_server.get_radius_client(module=module)
        end_state["radius enable"] = rds_enable_end

        if changed == False:
            rds_template_exist.sort()
            rds_template_end.sort()

            if rds_template_exist != rds_template_end:
                changed = True

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
                ce_aaa_server.create_hwtacacs_template(
                    module=module, hwtacas_template=hwtacas_template)
            elif hwtacacs_new not in hwtacacs_exist:
                ce_aaa_server.merge_hwtacacs_template(
                    module=module, hwtacas_template=hwtacas_template)
            else:
                pass

            hwtacacs_enbale_new = ("true")
            if hwtacacs_enbale_new not in hwtacacs_enbale_exist:
                ce_aaa_server.merge_hwtacacs_global_cfg(
                    module=module, isEnable="true")
            else:
                pass

        else:
            # absent hwtacas template
            if len(hwtacacs_exist) == 0:
                pass
            elif hwtacacs_new not in hwtacacs_exist:
                pass
            else:
                ce_aaa_server.delete_hwtacacs_template(
                    module=module, hwtacas_template=hwtacas_template)

            hwtacacs_enbale_new = ("false")
            if hwtacacs_enbale_new not in hwtacacs_enbale_exist:
                ce_aaa_server.merge_hwtacacs_global_cfg(
                    module=module, isEnable="false")
            else:
                pass

        hwtacacs_end = ce_aaa_server.get_hwtacacs_template(module=module)
        end_state["hwtacacs template"] = hwtacacs_end

        hwtacacs_enable_end = ce_aaa_server.get_hwtacacs_global_cfg(
            module=module)
        end_state["hwtacacs enable"] = hwtacacs_enable_end

        if changed == False:
            hwtacacs_exist.sort()
            hwtacacs_end.sort()

            if hwtacacs_exist != hwtacacs_end:
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
