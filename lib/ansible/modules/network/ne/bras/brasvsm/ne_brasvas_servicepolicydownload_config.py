#!/usr/bin/python
# coding=utf-8
from ansible.module_utils.network.ne.ne import get_nc_config, set_nc_config, ne_argument_spec
from ansible.module_utils.basic import AnsibleModule
from xml.etree import ElementTree
import copy
import logging
import re
ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: ne_brasvas_servicepolicydownload_config
version_added: "2.6"
short_description:  Manage brasvas module servicePolicyDownload config rule configuration.
description:
    -  Manage brasvas module servicePolicyDownload config rule configuration.
author:
    - liuhong (@CloudEngine-Ansible)
options:
    local:
        description:
            -  Indicates that a device obtains an EDSG service policy from the local configuration. The value can be a string of true or false.
        required: true
        choices: ['true','false']
    radius:
        description:
            -  Indicates that a device obtains an EDSG service policy from the RADIUS server. The value can be a string of true or false.
        required: true
        choices: ['true','false']
    radiusServerGroupName:
        description:
            -  Specifies the name of a RADIUS server group. The value must start with either uppercase letters A to Z or lowercase letters a to z and be a
            combination of letters, digits, hyphens (-), and underscores (_).
        required: true
    downloadpassword:
        description:
            -  Specifies an unencrypted/encrypted password.unencrypted password: The value is a string of 1 to 16 characters.encrypted password:
            The value is a string of 48 characters.
        required: true
    priority:
        description:
            -  Sets the priority between the local download and the radius download. The value can be a string of none or localRadius or radiusLocal.
        required: true
        default: none
        choices: ['none','localRadius','radiusLocal']
    operation:
        description:
            -  Manage the state of the resource.
               If operation is a get, no other parameters need to be configured.
        required: false
        default: merge
        choices: ['merge','get']
'''
EXAMPLES = '''

- name: Manage brasvas module servicePolicyDownload config rule configuration.
  hosts: ne_test
  connection: netconf
  gather_facts: no
  vars:
    cli:
      host: "{{inventory_hostname}}"
      port: "{{ansible_ssh_port}}"
      username: "{{ansible_user}}"
      password: "{{ansible_ssh_pass}}"
      transport: cli

  tasks:

  - name:merge a brasvas module  servicePolicyDownload config rule
    ne_brasvas_servicePolicyDownload_config:
    local='true'
    radius='true'
    radiusServerGroupName='v_radius_spt'
    downloadpassword='###ddd'
    priority='localRadius'
    operation='merge'
    provider="{{ cli }}"

  - name:get a brasvas module  servicePolicyDownload config rule
    ne_brasvas_servicePolicyDownload_config:
    operation='get'
    provider="{{ cli }}"

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
    sample: {
        "operation": "get",
        "priority": "none"
    }
existing:
    description: k/v pairs of existing object instance
    returned: always
    type: dict
    sample: {
            "servicePolicyDownloads": [
            {
                "local": "true",
                "priority": "localRadius",
                "radius": "true",
                "radiusServerGroupName": "v_radius_spt"
            }
        ]


    }
end_state:
    description: k/v pairs of object instance params after module execution
    returned: always
    type: dict
    sample: {
        "end_state": {
           "servicePolicyDownloads": [
            {
                "local": "true",
                "priority": "localRadius",
                "radius": "true",
                "radiusServerGroupName": "v_radius_spt"
            }
        ]


    }
'''

logging.basicConfig(filename='example.log', level=logging.DEBUG)
SERVICEPOLICYDOWNLOAD_HEAD = """
    <config>
      <brasvas xmlns="http://www.huawei.com/netconf/vrp/huawei-brasvas">
"""

SERVICEPOLICYDOWNLOAD_TAIL = """
              </brasvas>
       </config>
"""

SERVICEPOLICYDOWNLOAD_GETHEAD = """
 <filter type="subtree">
    <brasvas xmlns="http://www.huawei.com/netconf/vrp/huawei-brasvas">
      <servicePolicyDownload>
         <local/>
         <radius/>
         <radiusServerGroupName/>
         <password/>
         <priority/>
      </servicePolicyDownload>
    </brasvas>
  </filter>
"""

SERVICEPOLICYDOWNLOAD_GETHEADGET = """
    <filter type="subtree">
    <brasvas xmlns="http://www.huawei.com/netconf/vrp/huawei-brasvas">
      <servicePolicyDownload>
"""

SERVICEPOLICYDOWNLOAD_GETTAILGET = """
      </servicePolicyDownload>
    </brasvas>
  </filter>
"""

SERVICEPOLICYDOWNLOAD_MERGE = """
        <servicePolicyDownload xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" nc:operation="merge">
"""

LOCAL = """
       <local>%s</local>
"""

RADIUS = """
   <radius>%s</radius>
"""

RADIUSSERVERGROUPNAME = """
   <radiusServerGroupName>%s</radiusServerGroupName>
"""

PASSWORD = """
    <password>%s</password>
"""

PRIORITY = """
    <priority>%s</priority>
"""
SERVICEPOLICYDOWNLOADEND = """
  </servicePolicyDownload>
"""


class MyOperation(object):
    """
     My Operation Concrete Realization
    """

    def __init__(self, argument_spec):
        self.spec = argument_spec
        self.module = AnsibleModule(
            argument_spec=self.spec,
            supports_check_mode=True)
        self.local = self.module.params['local']
        self.radius = self.module.params['radius']
        self.radiusServerGroupName = self.module.params['radiusServerGroupName']
        self.downloadpassword = self.module.params['downloadpassword']
        self.priority = self.module.params['priority']
        self.operation = self.module.params['operation']

        if self.operation != 'get' and self.priority is None:
            self.priority = 'none'
        # 解析输入生成 proposed 表
        self.proposed = dict()
        if self.local is not None:
            self.proposed["local"] = self.local
        if self.radius is not None:
            self.proposed["radius"] = self.radius
        if self.radiusServerGroupName is not None:
            self.proposed["radiusServerGroupName"] = self.radiusServerGroupName
        if self.downloadpassword is not None:
            self.proposed["downloadpassword"] = self.downloadpassword
        if self.priority is not None:
            self.proposed["priority"] = self.priority
        if self.operation is not None:
            self.proposed["operation"] = self.operation

        # result state
        self.changed = False
        self.results = dict()
        self.existing = dict()
        self.end_state = dict()

    def check_params(self):
        if self.poolName:
            if len(self.poolName) > 128 or len(
                    self.poolName.replace(' ', '')) < 1:
                self.module.fail_json(
                    msg='Error: poolName is not in the range from 1 to 128.')

    def create_set_delete_process(self):
        cfg_str = ''
        cfg_str += SERVICEPOLICYDOWNLOAD_HEAD
        if self.operation == 'merge':
            cfg_str += SERVICEPOLICYDOWNLOAD_MERGE
            if self.local is not None:
                cfg_str += LOCAL % self.local
            if self.radius is not None:
                cfg_str += RADIUS % self.radius
            if self.radiusServerGroupName is not None:
                cfg_str += RADIUSSERVERGROUPNAME % self.radiusServerGroupName
            if self.downloadpassword is not None:
                cfg_str += PASSWORD % self.downloadpassword
            if self.priority is not None:
                cfg_str += PRIORITY % self.priority
            cfg_str += SERVICEPOLICYDOWNLOADEND

            cfg_str += SERVICEPOLICYDOWNLOAD_TAIL

        # 第二步: 下发配置报文
        logging.debug(cfg_str)
        set_nc_config(self.module, cfg_str)

    def get_info_process(self):
        """get one attributes dict."""
        # 第一步, 构造查询报文
        cfg_str = ''
        if self.operation != 'get':
            cfg_str += SERVICEPOLICYDOWNLOAD_GETHEAD
        if self.operation == 'get':
            cfg_str += SERVICEPOLICYDOWNLOAD_GETHEADGET
            if self.local is not None:
                cfg_str += LOCAL % self.local
            if self.radius is not None:
                cfg_str += RADIUS % self.radius
            if self.radiusServerGroupName is not None:
                cfg_str += RADIUSSERVERGROUPNAME % self.radiusServerGroupName
            if self.downloadpassword is not None:
                cfg_str += PASSWORD % self.downloadpassword
            if self.priority is not None:
                cfg_str += PRIORITY % self.priority
            cfg_str += SERVICEPOLICYDOWNLOAD_GETTAILGET

        # 第二步: 下发查询报文
        xml_str = get_nc_config(self.module, cfg_str)
        # 第三步: 解析查询报文
        # 解析1: 删除无用字符串, 注意根据业务做替换
        xml_str = xml_str.replace('\r', '').replace('\n', '').\
            replace(' xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"', "").\
            replace(' xmlns="http://www.huawei.com/netconf/vrp"', "").\
            replace(
            ' xmlns="http://www.huawei.com/netconf/vrp/huawei-brasvas"', "")

        # 解析2: 无数据检测
        attributes_Info = dict()
        if "<data/>" in xml_str:
            return attributes_Info

        # 解析3: 提取自己关心的字段(叶子)值
        root = ElementTree.fromstring(xml_str)
        service_container_attributes_Info = root.findall(
            "brasvas/servicePolicyDownload")
        attributes_Info["servicePolicyDownloads"] = list()

        if len(service_container_attributes_Info) != 0:
            for service_node in service_container_attributes_Info:
                service_container_Table = dict()
                for leaf_service_Info in service_node:
                    if leaf_service_Info.tag in [
                            "local", "radius", "radiusServerGroupName", "downloadpassword", "priority"]:
                        service_container_Table[leaf_service_Info.tag] = leaf_service_Info.text
                attributes_Info["servicePolicyDownloads"].append(
                    service_container_Table)

        if len(attributes_Info["servicePolicyDownloads"]) == 0:
            attributes_Info.clear()
        # 解析5: 返回数据
        return attributes_Info

    def run(self):
        # 第一步: 检测输入

        # 第二步: 下发 get 报文, 查询当前配置
        self.existing = self.get_info_process()
        self.results['existing'] = self.existing

        # 第三步: 根据用户输入的操作码下发配置, 查询功能已经在 get_existing 实现
        if self.operation != 'get':
            self.create_set_delete_process()
            # 配置结束, 重新查询下当前状态
            self.end_state = self.get_info_process()
            self.results['end_state'] = self.end_state

        # 第四步: 设置最后状态
        self.results['changed'] = self.changed
        self.results['proposed'] = self.proposed
        self.module.exit_json(**self.results)


def main():
    """ main module """
    logging.debug('This message should go to the log file ******')
    argument_spec = dict(
        local=dict(required=False, choices=['true', 'false']),
        radius=dict(required=False, choices=['true', 'false']),
        radiusServerGroupName=dict(required=False, type='str'),
        downloadpassword=dict(required=False, type='str'),
        priority=dict(
            required=False,
            choices=[
                'none',
                'localRadius',
                'radiusLocal']),
        operation=dict(
            required=False,
            choices=[
                'merge',
                'get'],
            default='merge'),
    )
    argument_spec.update(ne_argument_spec)
    myOperation = MyOperation(argument_spec)
    myOperation.run()


if __name__ == '__main__':
    main()
