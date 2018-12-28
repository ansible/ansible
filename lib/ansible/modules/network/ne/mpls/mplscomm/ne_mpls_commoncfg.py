# -*- coding utf-8 -*-
# !/usr/bin/python

import sys
import socket
import re
import copy

from xml.etree import ElementTree
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.ne.ne import get_nc_config, set_nc_config, ne_argument_spec

from ansible.modules.network.ne.mpls.mplscomm.ne_mpls_def import NE_COMMON_XML_OPERATION_CREATE
from ansible.modules.network.ne.mpls.mplscomm.ne_mpls_def import NE_COMMON_XML_OPERATION_MERGE
from ansible.modules.network.ne.mpls.mplscomm.ne_mpls_def import NE_COMMON_XML_OPERATION_DELETE
from ansible.modules.network.ne.mpls.mplscomm.ne_mpls_def import NE_COMMON_XML_GET_MPLS_HEAD
from ansible.modules.network.ne.mpls.mplscomm.ne_mpls_def import NE_COMMON_XML_GET_MPLS_TAIL
from ansible.modules.network.ne.mpls.mplscomm.ne_mpls_def import NE_COMMON_XML_PROCESS_MPLS_HEAD
from ansible.modules.network.ne.mpls.mplscomm.ne_mpls_def import NE_COMMON_XML_PROCESS_MPLS_TAIL

from ansible.modules.network.ne.mpls.mplscomm.ne_mpls_def import constr_leaf_value
from ansible.modules.network.ne.mpls.mplscomm.ne_mpls_def import constr_leaf_novalue
from ansible.modules.network.ne.mpls.mplscomm.ne_mpls_def import constr_container_head
from ansible.modules.network.ne.mpls.mplscomm.ne_mpls_def import constr_container_tail
from ansible.modules.network.ne.mpls.mplscomm.ne_mpls_def import constr_container_process_head
from ansible.modules.network.ne.mpls.mplscomm.ne_mpls_def import constr_container_process_tail

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: ne_mpls_commoncfg
version_added: "2.6"
short_description: Manages MPLS coommon configuration on HUAWEI ne switches.
description:
    - Manages MPLS coommon configuration on HUAWEI ne switches.
author: Haoliansheng (@CloudEngine-Ansible)
notes:
options:
    mplsenable:
        description:
            - Specifies the enabling state of MPLS.
        required: false
        default: null
        choices:['true', 'false']
    teenable:
        description:
            - Specifies the enabling state of MPLS TE.
        required: false
        default: null
        choices:['true', 'false']
    rsvpteenable:
        description:
            - Specifies the enabling state of RSVP TE.
        required: false
        default: null
        choices:['true', 'false']
    ldpenable:
        description:
            - Specifies the enabling state of LDP.
        required: false
        default: null
        choices:['true', 'false']
    mplsmtuindependent:
        description:
            - Specifies the enabling state of MTU independent.
        required: false
        default: null
        choices:['true', 'false']
    srttlmode:
        description:
            - SR TTL mode, which can be Uniform or Pipe.
        required: false
        default: null
        choices:['uniform', 'pipe']
    ldpttlmode:
        description:
            - Specifies the enabling state of LDP.
        required: false
        default: null
        choices:['uniform', 'pipe']
    nulllabletype:
        description:
            - Specifies the enabling state of LDP.
        required: false
        default: null
        choices:['implicit_null', 'explicit_null', 'non_null']
    tettlmode:
        description:
            - Specifies the enabling state of LDP.
        required: false
        default: null
        choices:['uniform', 'pipe']
    state:
        description:
            - Specify desired state of the resource.
        required: true
        default: present
        choices: ['present', 'query']
'''

EXAMPLES = '''

- name: NE device mpls module test
  hosts: mydevice
  vars:
    cli:
      host: "{{ inventory_hostname }}"
      port: "{{ ansible_ssh_port }}"
      username: "{{ ansible_user }}"
      password: "{{ ansible_ssh_pass }}"
      transport: cli
  connection: netconf
  gather_facts: no


  tasks:

  - name: "Query mpls common configuration"
    ne_mpls_commoncfg: state=query provider="{{ cli }}"
    register: data
    ignore_errors: true

  - name: "Enable mpls"
    ne_mpls_commoncfg: state=present mplsenable=true provider="{{ cli }}"
    register: data
    ignore_errors: false

  - name: "Enable mpls ldp"
    ne_mpls_commoncfg: state=present ldpenable=true provider="{{ cli }}"
    register: data
    ignore_errors: false

  - name: "Merge mpls common configuration"
    ne_mpls_commoncfg: state=present teenable=false rsvpteenable=false nulllabletype=non_null tettlmode=pipe ldpttlmode=pipe \
    srttlmode=pipe mplsmtuindependent=false provider="{{ cli }}"
    register: data
    ignore_errors: false

'''
RETURN = '''
proposed:
    description: k/v pairs of parameters passed into module
    returned: always
    type: dict
    sample: { "ldpttlmode": "pipe",   "mplsmtuindependent": "true",  "nulllabletype": "non_null", "rsvpteenable": "true",
        "srttlmode": "pipe",         "state": "present",         "teenable": "true",         "tettlmode": "pipe"    }
existing:
    description: k/v pairs of existing switchport
    returned: always
    type: dict
    sample: {        "ldpenable": "true",         "ldpttlmode": "uniform",         "mplsenable": "true",         "mplslabelspace": "32784",
        "mplslsrid": "1.1.1.1",         "mplsmtuindependent": "true",         "nulllabletype": "non_null",         "rsvpteenable": "true",
        "srttlmode": "uniform",         "teenable": "true",         "tettlmode": "uniform"    }
end_state:
    description: k/v pairs of switchport after module execution
    returned: always
    type: dict
    sample: {
        "ldpenable": "true",         "ldpttlmode": "uniform",         "mplsenable": "true",         "mplslabelspace": "32784",
        "mplslsrid": "1.1.1.1",         "mplsmtuindependent": "true",         "nulllabletype": "non_null",         "rsvpteenable": "true",
        "srttlmode": "uniform",         "teenable": "true",         "tettlmode": "uniform"    },
changed:
    description: check to see if a change was made on the device
    returned: always
    type: boolean
    sample: true
'''


class MPLS_mplsCommonCfg:
    """Manages configuration of an MPLS_mplsCommonCfg instance."""

    def __init__(self, argument_spec):
        """constructor"""

        self.spec = argument_spec
        self.module = None
        self.init_module()

        # module input info
        self.mplslsrid = self.module.params['mplslsrid']
        self.mplsenable = self.module.params['mplsenable']
        self.teenable = self.module.params['teenable']
        self.rsvpteenable = self.module.params['rsvpteenable']
        self.ldpenable = self.module.params['ldpenable']
        self.nulllabletype = self.module.params['nulllabletype']
        self.tettlmode = self.module.params['tettlmode']
        self.ldpttlmode = self.module.params['ldpttlmode']
        self.srttlmode = self.module.params['srttlmode']
        # self.mplslabelspace         = self.module.params['mplslabelspace']
        self.mplsmtuindependent = self.module.params['mplsmtuindependent']

        self.state = self.module.params['state']
        # mplsCommonCfg info
        self.mplsCommonCfg_info = dict()

        # states
        self.changed = False
        self.updates_cmd = list()
        self.results = dict()
        self.proposed = dict()
        self.existing = dict()
        self.end_state = dict()

    def init_module(self):
        """init module"""
        self.module = AnsibleModule(
            argument_spec=self.spec,
            supports_check_mode=True)

    def check_params(self):
        """check all input params"""

        if self.mplslsrid:
            if len(self.mplslsrid) > 255 or len(self.mplslsrid) < 0:
                self.module.fail_json(
                    msg='Error : mplsLsrID is not in the range from 0 to 255.')

    def check_response(self, xml_str, xml_name):
        """Check if response message is already succeed"""

        if "<ok/>" not in xml_str:
            self.module.fail_json(msg='Error : %s failed .' % xml_name)

    def get_mplsCommon_dict(self):
        """get one mplsCommonCfg attributes dict."""

        mplsCommonCfg_info = dict()

        conf_str = NE_COMMON_XML_GET_MPLS_HEAD
        conf_str = constr_container_head(conf_str, "mplsCommon")
        conf_str = constr_container_head(conf_str, "mplsCommonCfg")

        # conf_str = constr_leaf_novalue(conf_str, "mplsLsrID")
        # conf_str = constr_leaf_novalue(conf_str, "mplsEnable")
        # conf_str = constr_leaf_novalue(conf_str, "teEnable")
        # conf_str = constr_leaf_novalue(conf_str, "rsvpTeEnable")
        # conf_str = constr_leaf_novalue(conf_str, "ldpEnable")
        # conf_str = constr_leaf_novalue(conf_str, "nullLableType")
        # conf_str = constr_leaf_novalue(conf_str, "teTtlMode")
        # conf_str = constr_leaf_novalue(conf_str, "ldpTtlMode")
        # conf_str = constr_leaf_novalue(conf_str, "srTtlMode")
        # conf_str = constr_leaf_novalue(conf_str, "mplsLabelSpace")
        # conf_str = constr_leaf_novalue(conf_str, "mplsMtuIndependent")

        conf_str = constr_container_tail(conf_str, "mplsCommonCfg")
        conf_str = constr_container_tail(conf_str, "mplsCommon")
        conf_str += NE_COMMON_XML_GET_MPLS_TAIL

        xml_str = get_nc_config(self.module, conf_str)

        if "<data/>" in xml_str:
            return mplsCommonCfg_info

        xml_str = xml_str.replace('\r', '').replace('\n', '').\
            replace('xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"', "").\
            replace('xmlns="http://www.huawei.com/netconf/vrp"', "").\
            replace('xmlns="http://www.huawei.com/netconf/vrp/huawei-mpls"', "")

        root = ElementTree.fromstring(xml_str)

        mplsCommonCfg = root.find("mpls/mplsCommon/mplsCommonCfg")

        if mplsCommonCfg is not None:
            for site in mplsCommonCfg:
                if site.tag in ["mplsLsrID",
                                "mplsEnable",
                                "teEnable",
                                "rsvpTeEnable",
                                "ldpEnable",
                                "nullLableType",
                                "teTtlMode",
                                "ldpTtlMode",
                                "srTtlMode",
                                # "mplsLabelSpace",
                                "mplsMtuIndependent"]:
                    mplsCommonCfg_info[site.tag.lower()] = site.text

        return mplsCommonCfg_info

    def get_proposed(self):
        """get proposed info"""

        if self.mplslsrid is not None:
            self.proposed["mplslsrid"] = self.mplslsrid
        if self.mplsenable is not None:
            self.proposed["mplsenable"] = self.mplsenable
        if self.teenable is not None:
            self.proposed["teenable"] = self.teenable
        if self.rsvpteenable is not None:
            self.proposed["rsvpteenable"] = self.rsvpteenable
        if self.ldpenable is not None:
            self.proposed["ldpenable"] = self.ldpenable
        if self.nulllabletype is not None:
            self.proposed["nulllabletype"] = self.nulllabletype
        if self.tettlmode is not None:
            self.proposed["tettlmode"] = self.tettlmode
        if self.ldpttlmode is not None:
            self.proposed["ldpttlmode"] = self.ldpttlmode
        if self.srttlmode is not None:
            self.proposed["srttlmode"] = self.srttlmode
        if self.mplsmtuindependent is not None:
            self.proposed["mplsmtuindependent"] = self.mplsmtuindependent

        self.proposed["state"] = self.state

    def get_existing(self):
        """get existing info"""

        if not self.mplsCommonCfg_info:
            return

        self.existing = copy.deepcopy(self.mplsCommonCfg_info)

    def get_end_state(self):
        """get end state info"""
        mplsCommonCfg_info = self.get_mplsCommon_dict()
        if not mplsCommonCfg_info:
            return

        self.end_state = copy.deepcopy(mplsCommonCfg_info)

    def merge_process(self, operation_Desc):
        """merge process"""

        xml_str = NE_COMMON_XML_PROCESS_MPLS_HEAD

        xml_str = constr_container_head(xml_str, "mplsCommon")
        xml_str += " <mplsCommonCfg xc:operation=\"merge\">"
        xml_str = constr_leaf_value(xml_str, "mplsLsrID", self.mplslsrid)
        xml_str = constr_leaf_value(xml_str, "mplsEnable", self.mplsenable)
        xml_str = constr_leaf_value(xml_str, "teEnable", self.teenable)
        xml_str = constr_leaf_value(xml_str, "rsvpTeEnable", self.rsvpteenable)
        xml_str = constr_leaf_value(xml_str, "ldpEnable", self.ldpenable)
        xml_str = constr_leaf_value(xml_str, "nullLableType", self.nulllabletype)
        xml_str = constr_leaf_value(xml_str, "teTtlMode", self.tettlmode)
        xml_str = constr_leaf_value(xml_str, "ldpTtlMode", self.ldpttlmode)
        xml_str = constr_leaf_value(xml_str, "srTtlMode", self.srttlmode)
        # xml_str = constr_leaf_value(xml_str, "mplsLabelSpace",         self.mplslabelspace)
        xml_str = constr_leaf_value(xml_str, "mplsMtuIndependent", self.mplsmtuindependent)

        xml_str = constr_container_tail(xml_str, "mplsCommonCfg")
        xml_str = constr_container_tail(xml_str, "mplsCommon")
        xml_str += NE_COMMON_XML_PROCESS_MPLS_TAIL

        recv_xml = set_nc_config(self.module, xml_str)
        self.check_response(recv_xml, operation_Desc)

        self.changed = True

    def work(self):
        """worker"""
        self.check_params()

        self.mplsCommonCfg_info = self.get_mplsCommon_dict()
        self.get_proposed()
        self.get_existing()

        # if self.state == "absent":
        #    self.module.fail_json(msg = 'Error: mplsCommonCfg does not support delete operation.')

        if self.state == "present":
            if not self.mplsCommonCfg_info:
                # we don`t support create operation
                self.module.fail_json(
                    msg='Error : MPLS Common Config Instance does not exist, and it does not support create operation')
            else:
                # merge
                self.merge_process("MERGE_PROCESS")
        else:
            if not self.mplsCommonCfg_info:
                self.module.fail_json(
                    msg='Error : MPLS Common Config does not exist.')

        self.get_end_state()
        self.results['changed'] = self.changed
        self.results['proposed'] = self.proposed
        self.results['existing'] = self.existing
        self.results['end_state'] = self.end_state
        # if self.changed:
        #    self.results['updates'] = self.updates_cmd
        # else:
        #    self.results['updates'] = list()

        self.module.exit_json(**self.results)


def main():
    """main process"""

    argument_spec = dict(
        mplslsrid=dict(required=False, type='str'),
        mplsenable=dict(required=False, choices=['true', 'false']),
        teenable=dict(required=False, choices=['true', 'false']),
        rsvpteenable=dict(required=False, choices=['true', 'false']),
        ldpenable=dict(required=False, choices=['true', 'false']),
        nulllabletype=dict(required=False, choices=['implicit_null', 'explicit_null', 'non_null']),
        tettlmode=dict(required=False, choices=['uniform', 'pipe']),
        ldpttlmode=dict(required=False, choices=['uniform', 'pipe']),
        srttlmode=dict(required=False, choices=['uniform', 'pipe']),
        # Donot support update.
        # mplslabelspace          = dict(required = False, type = 'int'),
        mplsmtuindependent=dict(required=False, choices=['true', 'false']),

        state=dict(required=False, default='present', choices=['present', 'query'])
    )

    argument_spec.update(ne_argument_spec)
    module = MPLS_mplsCommonCfg(argument_spec)
    module.work()


if __name__ == '__main__':
    main()
