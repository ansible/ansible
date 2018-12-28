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
module: ne_brasvas_servicepolicy_ratelimits_config
version_added: "2.6"
short_description: Configures the inbound and outbound rate for the service policy template.
description:
    - Configures the inbound and outbound rate for the service policy template.
author:
    - liushuai (@CloudEngine-Ansible)
options:
    servicePolicyName:
        description:
            - Specifies the name of a value-added service policy.
        required: false
    rateLimitDirection:
        description:
            - Configures rate limit direction for the service policy template.
        required: false
        choices: ['inbound', 'outbound']
    cir:
        description:
            - Specifies committed information rate.
              It is an integer that ranges from 0 to 4294967294, in kbit/s.
              The rate is not restricted by default. If the CIR or PIR is set to 0, traffic is interrupted.
        required: false
    pir:
        description:
            - Specifies the peak information rate.
              It is an integer that ranges from 0 to 4294967294, in kbit/s.
              The rate is not restricted by default.
              If the CIR or PIR is set to 0, traffic is interrupted.
        required: false
    cbs:
        description:
            - Specifies the committed burst size.It is an integer that ranges from 0 to 4294967294, in byte.
        required: false
    pbs:
        description:
            - Specifies the peak burst size.It is an integer that ranges from 0 to 4294967294, in byte.
        required: false
    operation:
        description:
            - Specifies the operation type.
              if the operation is get,the cir and pir and cbs and pbs cannot take parameters,
              otherwise The echo of the command line is'This operation are not supported'.
        required: true
        choices: ['create', 'delete', 'merge', 'get']
'''

EXAMPLES = '''

- name: ne_brasvas_servicepolicy_ratelimits_config test
  hosts: ne_test
  connection: netconf
  gather_facts: no
  vars:
    cli:
        host: "{{ inventory_hostname }}"
        port: "{{ ansible_ssh_port }}"
        username: "{{ ansible_user }}"
        password: "{{ ansible_ssh_pass }}"
        transport: cli

    tasks:

    - name: "Configures the inbound and outbound rate for the service policy template, the operation type is 'create'."
      ne_brasvas_servicepolicy_ratelimits_config:
        servicePolicyName='nameTest1'
        rateLimitDirection='inbound'
        cir='1'
        pir='1'
        cbs='1'
        pbs='1'
        operation='create'
        provider: "{{ cli }}"

    - name: "Configures the inbound and outbound rate for the service policy template, the operation type is 'delete'."
      ne_brasvas_servicepolicy_ratelimits_config:
        servicePolicyName='nameTest1'
        rateLimitDirection='inbound'
        cir='1'
        pir='1'
        cbs='1'
        pbs='1'
        operation='delete'
        provider: "{{ cli }}"

    - name: "Configures the inbound and outbound rate for the service policy template, the operation type is 'get'."
      ne_brasvas_servicepolicy_ratelimits_config:
        servicePolicyName='nameTest1'
        rateLimitDirection='inbound'
        cir='1'
        pir='1'
        cbs='1'
        pbs='1'
        operation='get'
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
    sample: {
        "servicePolicyName": "nameTest1",
        "rateLimitDirection": "inbound",
        "cir": "1",
        "pir": "1",
        "cbs": "1",
        "pbs": "1",
        "operation": "create"
    }
existing:
    description: k/v pairs of existing object instance
    returned: always
    type: dict
    sample: {
        "rateLimits": [
            {
                "servicePolicyName": "nameTest1",
                "rateLimitDirection": "inbound",
                "cir": "1",
                "pir": "1",
                "cbs": "1",
                "pbs": "1"
            }
        ]
    }
end_state:
    description: k/v pairs of object instance params after module execution
    returned: always
    type: dict
    sample: {
        "rateLimits": [
            {
                "servicePolicyName": "nameTest1",
                "rateLimitDirection": "inbound",
                "cir": "1",
                "pir": "1",
                "cbs": "1",
                "pbs": "1"
            }
        ]
    }
'''


SERVICEPOLICYS_RATELIMITS_CONFIG_HEAD = """
    <config>
      <brasvas xmlns="http://www.huawei.com/netconf/vrp/huawei-brasvas">
        <servicePolicys>
          <servicePolicy>
"""

SERVICEPOLICYS_RATELIMITS_CONFIG_TAIL = """
          </servicePolicy>
        </servicePolicys>
      </brasvas>
    </config>
"""

RATELIMITS_START = """
            <rateLimits>"""

RATELIMIT_START = """
              <rateLimit>"""

SERVICEPOLICYS_RATELIMITS_CREATE = """
              <rateLimit nc:operation="create" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">"""

SERVICEPOLICYS_RATELIMITS_DELETE = """
              <rateLimit nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">"""

SERVICEPOLICYS_RATELIMITS_MERGE = """
              <rateLimit nc:operation="merge" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">"""

RATELIMIT_END = """
              </rateLimit>"""

RATELIMITS_END = """
            </rateLimits>"""

SERVICEPOLICYS_RATELIMITS_GET_HEAD = """
  <filter type="subtree">
    <brasvas xmlns="http://www.huawei.com/netconf/vrp/huawei-brasvas">
      <servicePolicys>
        <servicePolicy>"""

SERVICEPOLICYS_RATELIMITS_GET_TAIL = """
        </servicePolicy>
      </servicePolicys>
    </brasvas>
  </filter>"""

SERVICEPOLICYNAME = """
                <servicePolicyName>%s</servicePolicyName>"""

RATELIMITDIRECTION = """
                <rateLimitDirection>%s</rateLimitDirection>"""

CIR = """
                <cir>%s</cir>"""

PIR = """
                <pir>%s</pir>"""

CBS = """
                <cbs>%s</cbs>"""

PBS = """
                <pbs>%s</pbs>"""


class MyOperation(object):
    """
     My Operation Concrete Realization
    """

    def __init__(self, argument_spec):
        self.spec = argument_spec
        self.module = AnsibleModule(
            argument_spec=self.spec,
            supports_check_mode=True)

        # module input info
        self.servicePolicyName = self.module.params['servicePolicyName']
        self.rateLimitDirection = self.module.params['rateLimitDirection']
        self.cir = self.module.params['cir']
        self.pir = self.module.params['pir']
        self.cbs = self.module.params['cbs']
        self.pbs = self.module.params['pbs']
        self.operation = self.module.params['operation']

        self.proposed = dict()
        if self.servicePolicyName is not None:
            self.proposed["servicePolicyName"] = self.servicePolicyName
        if self.rateLimitDirection is not None:
            self.proposed["rateLimitDirection"] = self.rateLimitDirection
        if self.cir is not None:
            self.proposed["cir"] = self.cir
        if self.pir is not None:
            self.proposed["pir"] = self.pir
        if self.cbs is not None:
            self.proposed["cbs"] = self.cbs
        if self.pbs is not None:
            self.proposed["pbs"] = self.pbs
        if self.operation is not None:
            self.proposed["operation"] = self.operation

        # result state
        self.changed = False
        self.results = dict()
        self.existing = dict()
        self.end_state = dict()

    def create_set_delete_process(self):
        """get config rpc string"""
        cfg_str = ''
        self.changed = True
        cfg_str += SERVICEPOLICYS_RATELIMITS_CONFIG_HEAD
        if self.servicePolicyName is not None:
            cfg_str += SERVICEPOLICYNAME % self.servicePolicyName

        cfg_str += RATELIMITS_START
        if self.operation == 'create':
            cfg_str += SERVICEPOLICYS_RATELIMITS_CREATE
        if self.operation == 'merge':
            cfg_str += SERVICEPOLICYS_RATELIMITS_MERGE
        if self.operation == 'delete':
            cfg_str += SERVICEPOLICYS_RATELIMITS_DELETE

        if self.rateLimitDirection is not None:
            cfg_str += RATELIMITDIRECTION % self.rateLimitDirection
        if self.cir is not None:
            cfg_str += CIR % self.cir
        if self.pir is not None:
            cfg_str += PIR % self.pir
        if self.cbs is not None:
            cfg_str += CBS % self.cbs
        if self.pbs is not None:
            cfg_str += PBS % self.pbs

        cfg_str += RATELIMIT_END
        cfg_str += RATELIMITS_END
        cfg_str += SERVICEPOLICYS_RATELIMITS_CONFIG_TAIL

        logging.debug(cfg_str)
        set_nc_config(self.module, cfg_str)

    def get_info_process(self):
        """get one attributes dict."""
        cfg_str = ''
        cfg_str += SERVICEPOLICYS_RATELIMITS_GET_HEAD

        if self.servicePolicyName is not None:
            cfg_str += SERVICEPOLICYNAME % self.servicePolicyName
        cfg_str += RATELIMITS_START
        cfg_str += RATELIMIT_START
        if self.rateLimitDirection is not None:
            cfg_str += RATELIMITDIRECTION % self.rateLimitDirection
        cfg_str += RATELIMIT_END
        cfg_str += RATELIMITS_END

        cfg_str += SERVICEPOLICYS_RATELIMITS_GET_TAIL

        if self.operation == 'get':
            if self.cir is not None:
                self.module.fail_json(
                    msg='Error: This operation is not supported.')
            if self.pir is not None:
                self.module.fail_json(
                    msg='Error: This operation is not supported.')
            if self.cbs is not None:
                self.module.fail_json(
                    msg='Error: This operation is not supported.')
            if self.pbs is not None:
                self.module.fail_json(
                    msg='Error: This operation is not supported.')

        xml_str = get_nc_config(self.module, cfg_str)

        xml_str = xml_str.replace('\r', '').replace('\n', '').\
            replace(' xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"', "").\
            replace(' xmlns="http://www.huawei.com/netconf/vrp"', "").\
            replace(
            ' xmlns="http://www.huawei.com/netconf/vrp/huawei-brasvas"', "")

        attributes_Info = dict()
        if "<data/>" in xml_str:
            return attributes_Info

        root = ElementTree.fromstring(xml_str)
        container_1_attributes_Info = root.findall(
            "brasvas/servicePolicys/servicePolicy")
        attributes_Info["rateLimits"] = list()

        if len(container_1_attributes_Info) != 0:
            for container_1_node in container_1_attributes_Info:
                container_info_Table = dict()
                for leaf_1_Info in container_1_node:
                    if leaf_1_Info.tag in ["servicePolicyName"]:
                        container_info_Table[leaf_1_Info.tag] = leaf_1_Info.text

                container_2_attributes_Info = container_1_node.findall(
                    "rateLimits/rateLimit")
                if len(container_2_attributes_Info) != 0:
                    for container_2_node in container_2_attributes_Info:
                        container_2_info_Table = copy.deepcopy(
                            container_info_Table)
                        for leaf_2_Info in container_2_node:
                            if leaf_2_Info.tag in ["rateLimitDirection",
                                                   "cir",
                                                   "pir",
                                                   "cbs",
                                                   "pbs"]:
                                container_2_info_Table[leaf_2_Info.tag] = leaf_2_Info.text
                        attributes_Info["rateLimits"].append(
                            container_2_info_Table)

        if len(attributes_Info["rateLimits"]) == 0:
            attributes_Info.clear()
        return attributes_Info

    def run(self):
        # self.check_params()

        self.existing = self.get_info_process()
        self.results['existing'] = self.existing

        if self.operation != 'get':
            self.create_set_delete_process()
            self.end_state = self.get_info_process()
            self.results['end_state'] = self.end_state

        self.results['changed'] = self.changed
        self.results['proposed'] = self.proposed
        self.module.exit_json(**self.results)


def main():
    """ main module """
    logging.basicConfig(filename='example.log', level=logging.DEBUG)
    argument_spec = dict(
        servicePolicyName=dict(required=False, type='str'),
        rateLimitDirection=dict(
            required=False, choices=[
                'inbound', 'outbound']),
        cir=dict(required=False, type='int'),
        pir=dict(required=False, type='int'),
        cbs=dict(required=False, type='int'),
        pbs=dict(required=False, type='int'),
        operation=dict(
            required=True,
            choices=[
                'create',
                'delete',
                'merge',
                'get']),
    )
    argument_spec.update(ne_argument_spec)
    myOperation = MyOperation(argument_spec)
    myOperation.run()


if __name__ == '__main__':
    main()
