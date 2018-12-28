# -*- coding: utf-8 -*-
# !/usr/bin/python

import sys
import copy
import socket

from xml.etree import ElementTree
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.ne.ne import execute_nc_action_yang, ne_argument_spec

from ansible.modules.network.ne.mpls.mplscomm.ne_mpls_def import NE_COMMON_XML_EXECUTE_MPLS_HEAD
from ansible.modules.network.ne.mpls.mplscomm.ne_mpls_def import NE_COMMON_XML_EXECUTE_MPLS_TAIL

from ansible.modules.network.ne.mpls.mplscomm.ne_mpls_def import constr_leaf_value
from ansible.modules.network.ne.mpls.mplscomm.ne_mpls_def import constr_leaf_novalue
from ansible.modules.network.ne.mpls.mplscomm.ne_mpls_def import constr_container_head
from ansible.modules.network.ne.mpls.mplscomm.ne_mpls_def import constr_container_tail


class MPLS_resetAllLdp(object):
    """Manages configuration of an MPLS_resetAllLdp instance."""

    def __init__(self, argument_spec):
        self.spec = argument_spec
        self.module = None
        self.init_module()

        self.vrfname = self.module.params['vrfname']
        self.graceful = self.module.params['graceful']

        self.Succeed = False
        self.results = dict()

    def init_module(self):
        self.module = AnsibleModule(
            argument_spec=self.spec,
            supports_check_mode=True)

    def check_params(self):
        # TO DO: check params
        return

    def check_response(self, xml_str, xml_name):
        """Check if response message is already succeed"""
        if "<ok/>" not in xml_str:
            self.module.fail_json(msg='Error: %s failed.' % xml_name)

    def action_process(self):
        """action proposed info"""

        xml_str = """
            <mplsLdp-resetAllLdp xmlns="http://www.huawei.com/netconf/vrp/huawei-mpls">
                <VrfName>_public_</VrfName>
            </mplsLdp-resetAllLdp>
        """
        recv_xml = execute_nc_action_yang(self.module, xml_str)

        self.check_response(recv_xml, "ACTION_OPERATION")
        self.succeed = True

    def work(self):
        """worker"""

        self.check_params()
        self.action_process()

        self.results['succeed'] = self.succeed
        self.module.exit_json(**self.results)


def main():
    """main porcess"""

    argument_spec = dict(
        vrfname=dict(required=True, type='str'),
        graceful=dict(required=False, type='str'),
        state=dict(required=False, default='execute', chioces=['execute'])
    )

    argument_spec.update(ne_argument_spec)
    module = MPLS_resetAllLdp(argument_spec)
    module.work()


if __name__ == '__main__':
    main()
