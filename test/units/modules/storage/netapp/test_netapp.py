# Copyright (c) 2018 NetApp
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

''' unit tests for module_utils netapp.py '''
from __future__ import absolute_import, division, print_function

import pytest

from ansible.module_utils.ansible_release import __version__ as ansible_version

import ansible.module_utils.netapp as netapp_utils

if not netapp_utils.has_netapp_lib():
    pytestmark = pytest.mark.skip("skipping as missing required netapp_lib")


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
        xml = netapp_utils.zapi.NaElement('xml')
        attributes = netapp_utils.zapi.NaElement('attributes-list')
        attributes.add_node_with_children('vserver-info',
                                          **{'vserver-name': vserver})
        xml.add_child_elem(attributes)
        return xml


def test_ems_log_event_version():
    ''' validate Ansible version is correctly read '''
    source = 'unittest'
    server = MockONTAPConnection()
    netapp_utils.ems_log_event(source, server)
    xml = server.xml_in
    version = xml.get_child_content('app-version')
    assert version == ansible_version
    print("Ansible version: %s" % ansible_version)


def test_get_cserver():
    ''' validate cluster vserser name is correctly retrieved '''
    svm_name = 'svm1'
    server = MockONTAPConnection('vserver', svm_name)
    cserver = netapp_utils.get_cserver(server)
    assert cserver == svm_name
