# -*- coding: utf-8 -*-
# !/usr/bin/python

import sys
import socket

from xml.etree import ElementTree
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.ne.ne import get_nc_config, set_nc_config, ne_argument_spec

from ansible.modules.network.ne.bgp.l3vpn.ne_public_precfgxmlall import ALL_PRECOFING_XMLS


class PreConfiguration(object):
    """class PreConfiguration"""

    def __init__(self, argument_spec):
        self.spec = argument_spec
        self.module = None
        self.init_module()

        self.precfgname = self.module.params['precfgname']

        self.Succeed = False
        self.results = dict()

    def init_module(self):
        self.module = AnsibleModule(
            argument_spec=self.spec,
            supports_check_mode=True)

    def check_response(self, xml_str, xml_name):
        """Check if response message is already succeed"""
        if "<ok/>" not in xml_str:
            self.module.fail_json(msg='Error: %s failed.' % xml_name)

    def Do_PreConfiguration(self, xml_name, xml_str):

        recv_xml = set_nc_config(self.module, xml_str, True)

        self.check_response(recv_xml, xml_name)
        self.Succeed = True

    def getConfigXml(self, precfgname):

        try:
            preCfgXml = ALL_PRECOFING_XMLS[precfgname]
        except BaseException:
            self.module.fail_json(
                'Error: Could not find the config xml named: %s! Please check the file ne_public_precfgxmlall\n' %
                precfgname)

        return preCfgXml

    def work(self):
        """work"""

        preCfgXml = self.getConfigXml(self.precfgname)
        self.Do_PreConfiguration(self.precfgname, preCfgXml)

        self.results['Succeed'] = self.Succeed
        self.module.exit_json(**self.results)


def main():
    """main porcess"""

    argument_spec = dict(
        precfgname=dict(required=True, type='str')
    )

    argument_spec.update(ne_argument_spec)
    module = PreConfiguration(argument_spec)
    module.work()


if __name__ == '__main__':
    main()
