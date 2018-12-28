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
# GNU General Public License for more detai++++++++ls.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.
#

from ansible.module_utils.network.ne.ne import get_nc_config, set_nc_config, execute_nc_action, ne_argument_spec
from ansible.module_utils.basic import AnsibleModule
from xml.etree import ElementTree
ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'aaa'}

DOCUMENTATION = '''
---
module: aaa_user_getconfig
version_added: "2.6"
short_description: Query local account infomation
description:
    -  Query local account infomation.
author:

options:
    localuser_username:
        description:
            - The user name of local account.
        required: false
        default: null
'''

EXAMPLES = '''

- name: get local user
  hosts: ne_test
  connection: netconf
  gather_facts: no
  vars:
    yang:
      host: "{{ inventory_hostname }}"
      port: "{{ ansible_ssh_port }}"
      username: "{{ ansible_user }}"
      password: "{{ ansible_ssh_pass }}"

  tasks:

  - name: "Get all  local accounts"
    aaa_user_getconfig:

  - name: "Get local account filtered by userName"
    aaa_user_getconfig:
      localuser_username: "test123"

'''

RETURN = '''
 localhost | SUCCESS => {
    "changed": false,
    "invocation": {
        "module_args": {
            "host": "10.252.8.172",
            "localuser_username": "root1234",
            "password": "VALUE_SPECIFIED_IN_NO_LOG_PARAMETER",
            "port": 20022,
            "provider": null,
            "timeout": null,
            "transport": null,
            "use_ssl": null,
            "username": "root123",
            "validate_certs": null
        }
    },
    "response": [
        {
            "AAA_user_info": [
                {
                    "failedTimes": "3",
                    "interval": "5",
                    "isLocked": "no",
                    "isPassChanged": "false",
                    "isPassExpired": "noConfig",
                    "passModifyTime": "2018-04-11T14:56:07Z",
                    "password": "$1c$kS)C-%o$lB$O_EOKG#N\";\\Z7O#kVCLY&o{x)aCEbW55ua5G3|N5$",
                    "passwordType": "irreversible-cipher",
                    "serviceFtp": "false",
                    "serviceMml": "false",
                    "servicePpp": "false",
                    "serviceQx": "false",
                    "serviceSnmp": "false",
                    "serviceSsh": "false",
                    "serviceTelnet": "false",
                    "serviceTerminal": "false",
                    "userName": "root1234",
                    "userState": "active"
                }
            ]
        }
    ]
}
'''
AAA_USER_GET_HEAD = """
  <filter type="subtree">
    <aaa:aaa xmlns:aaa="http://www.huawei.com/netconf/vrp/huawei-aaa">
      <aaa:lam>
        <aaa:users>
          <aaa:user>
"""

AAA_USER_GET_TAIL = """
          </aaa:user>
        </aaa:users>
      </aaa:lam>
    </aaa:aaa>
  </filter>
"""


aaa_local_user_argument_spec = {
    'localuser_username': dict(type='str')
}

aaa_local_user_get_filed = {
    'localuser_username': """
      <aaa:userName>%s</aaa:userName>"""
}


class AAAUserGet(object):
    """
    AAAUserGet class
    """

    def __init__(self, argument_spec):
        self.spec = argument_spec
        self.module = AnsibleModule(
            argument_spec=self.spec,
            supports_check_mode=True)
        self.results = dict()
        self.results['response'] = []

    def AAA_user_get_str(self):
        aaa_user_get_str = ''

        aaa_user_get_str += AAA_USER_GET_HEAD

        # k is the key of input param, v is the value of input param
        for k, v in self.module.params.items():
            if k in aaa_local_user_get_filed:  # if the send filed is exist of the key
                if v:
                    aaa_user_get_str += aaa_local_user_get_filed[k] % v

                aaa_user_get_str += AAA_USER_GET_TAIL

        return aaa_user_get_str

    def aaa_user_get(self):
        return get_nc_config(self.module, self.AAA_user_get_str())


def config_param_exist(arg):
    if arg or arg == '':
        return True
    return False


def aaa_user_parse(recv_xml):
    xml_str = recv_xml.replace('\r', '').replace('\n', '').\
        replace('xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"', "").\
        replace('xmlns="http://www.huawei.com/netconf/vrp/huawei-aaa"', "")

    root = ElementTree.fromstring(xml_str)
    cfg_info = root.findall("aaa/lam/users/user")

    result = dict()
    result["AAA_user_info"] = []
    if cfg_info:
        for temp in cfg_info:
            tmp_dict = dict()
            for site in temp:
                if site.tag in ["userName", "userGroupName", "userState",
                                "failedTimes", "interval", "passwordType",
                                "password", "userLevel", "ftpDir",
                                "serviceTerminal", "serviceTelnet", "serviceFtp",
                                "servicePpp", "serviceSsh", "serviceQx",
                                "serviceSnmp", "serviceMml", "maxAccessNum",
                                "isLocked", "leftLockTime", "passModifyTime",
                                "isPassChanged", "isPassExpired", "passwordExpireInDays", "agingInDays"]:
                    tmp_dict[site.tag] = site.text
            result["AAA_user_info"].append(tmp_dict)

    return result


def main():
    """ main function """

    argument_spec = dict()

    argument_spec.update(ne_argument_spec)
    argument_spec.update(aaa_local_user_argument_spec)

    module = AnsibleModule(
        argument_spec=argument_spec
    )

    aaa_user_get_obj = AAAUserGet(argument_spec)
    xml_ret = aaa_user_get_obj.aaa_user_get()

    results = dict()
    get_values = dict()
    get_result = aaa_user_parse(xml_ret)
    if get_result:
        for item in get_result:
            get_values[item] = get_result[item]

    results["response"] = []
    results["response"].append(get_values)

    module.exit_json(**results)


if __name__ == '__main__':
    main()
