# Copyright (c) 2018 NetApp
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

''' unit tests for module_utils netapp.py '''
from __future__ import absolute_import, division, print_function

try:
    from netapp_lib.api.zapi import zapi
    HAS_NETAPP_ZAPI = True
except ImportError:
    HAS_NETAPP_ZAPI = False

try:
    from ansible.module_utils.ansible_release import __version__ as ansible_version
except ImportError:
    ansible_version = 'unknown'

from units.compat import unittest
import ansible.module_utils.netapp as my_module
HAS_NETAPP_ZAPI_MSG = "pip install netapp_lib is required"


class MockONTAPConnection(object):
    ''' mock a server connection to ONTAP host '''

    def __init__(self, kind=None, parm1=None):
        ''' save arguments '''
        self.type = kind
        self.parm1 = parm1
        self.xml_in = None
        self.xml_out = None

    def invoke_successfully(self, xml, enable_tunneling):  # pylint: disable=unused-argument
        ''' mock invoke_successfully returning xml data '''
        self.xml_in = xml
        if self.type == 'vserver':
            xml = self.build_vserver_info(self.parm1)
        self.xml_out = xml
        return xml

    @staticmethod
    def build_vserver_info(vserver):
        ''' build xml data for vserser-info '''
        xml = zapi.NaElement('xml')
        attributes = zapi.NaElement('attributes-list')
        attributes.add_node_with_children('vserver-info',
                                          **{'vserver-name': vserver})
        xml.add_child_elem(attributes)
        return xml


class TestEMSLogVersion(unittest.TestCase):
    ''' validate version is read successfully from ansible release.py '''

    def setUp(self):
        self.assertTrue(HAS_NETAPP_ZAPI, HAS_NETAPP_ZAPI_MSG)
        self.source = 'unittest'
        self.server = MockONTAPConnection()

    def test_ems_log_event_version(self):
        ''' validate Ansible version is correctly read '''
        my_module.ems_log_event(self.source, self.server)
        xml = self.server.xml_in
        version = xml.get_child_content('app-version')
        self.assertEquals(version, ansible_version)
        print("Ansible version: %s" % ansible_version)


class TestGetCServer(unittest.TestCase):
    ''' validate cserver name is extracted correctly '''

    def setUp(self):
        self.assertTrue(HAS_NETAPP_ZAPI, HAS_NETAPP_ZAPI_MSG)
        self.svm_name = 'svm1'
        self.server = MockONTAPConnection('vserver', self.svm_name)

    def test_get_cserver(self):
        ''' validate cluster vserser name is correctly retrieved '''
        cserver = my_module.get_cserver(self.server)
        self.assertEquals(cserver, self.svm_name)


if __name__ == '__main__':
    unittest.main()
