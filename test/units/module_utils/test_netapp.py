# (c) 2018, NetApp Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


from __future__ import absolute_import, division, print_function
__metaclass__ = type

import pytest

from ansible.module_utils.ansible_release import __version__ as ansible_version

import ansible.module_utils.netapp as netapp_utils

try:
    from unittest.mock import patch, mock_open
except ImportError:
    from mock import patch, mock_open

from ansible.module_utils.six.moves.urllib.error import URLError
from ansible.module_utils.netapp import NetAppESeriesModule, create_multipart_formdata
from units.modules.utils import AnsibleExitJson, AnsibleFailJson, ModuleTestCase, set_module_args


class StubNetAppESeriesModule(NetAppESeriesModule):
    def __init__(self):
        super(StubNetAppESeriesModule, self).__init__(ansible_options={})


class NetappTest(ModuleTestCase):
    REQUIRED_PARAMS = {"api_username": "rw",
                       "api_password": "password",
                       "api_url": "http://localhost",
                       "ssid": "1"}
    REQ_FUNC = "ansible.module_utils.netapp.request"

    def _set_args(self, args=None):
        module_args = self.REQUIRED_PARAMS.copy()
        if args is not None:
            module_args.update(args)
        set_module_args(module_args)

    def test_is_embedded_embedded_pass(self):
        """Verify is_embedded successfully returns True when an embedded web service's rest api is inquired."""
        self._set_args()
        with patch(self.REQ_FUNC, side_effect=[(200, {"version": "03.10.9000.0009"}),
                                               (200, {"runningAsProxy": False})]):
            base = StubNetAppESeriesModule()
            self.assertTrue(base.is_embedded())
        with patch(self.REQ_FUNC, side_effect=[(200, {"version": "03.10.9000.0009"}),
                                               (200, {"runningAsProxy": True})]):
            base = StubNetAppESeriesModule()
            self.assertFalse(base.is_embedded())

    def test_is_embedded_fail(self):
        """Verify exception is thrown when a web service's rest api fails to return about information."""
        self._set_args()
        with patch(self.REQ_FUNC, side_effect=[(200, {"version": "03.10.9000.0009"}), Exception()]):
            with self.assertRaisesRegexp(AnsibleFailJson, r"Failed to retrieve the webservices about information!"):
                base = StubNetAppESeriesModule()
                base.is_embedded()
        with patch(self.REQ_FUNC, side_effect=[(200, {"version": "03.10.9000.0009"}), URLError(""), Exception()]):
            with self.assertRaisesRegexp(AnsibleFailJson, r"Failed to retrieve the webservices about information!"):
                base = StubNetAppESeriesModule()
                base.is_embedded()

    def test_check_web_services_version_fail(self):
        """Verify that an unacceptable rest api version fails."""
        minimum_required = "02.10.9000.0010"
        test_set = ["02.10.9000.0009", "02.09.9000.0010", "01.10.9000.0010"]

        self._set_args()
        base = StubNetAppESeriesModule()
        base.web_services_version = minimum_required
        base.is_embedded = lambda: True
        for current_version in test_set:
            with patch(self.REQ_FUNC, return_value=(200, {"version": current_version})):
                with self.assertRaisesRegexp(AnsibleFailJson, r"version does not meet minimum version required."):
                    base._check_web_services_version()

    def test_check_web_services_version_pass(self):
        """Verify that an unacceptable rest api version fails."""
        minimum_required = "02.10.9000.0010"
        test_set = ["02.10.9000.0009", "02.09.9000.0010", "01.10.9000.0010"]

        self._set_args()
        base = StubNetAppESeriesModule()
        base.web_services_version = minimum_required
        base.is_embedded = lambda: True
        for current_version in test_set:
            with patch(self.REQ_FUNC, return_value=(200, {"version": current_version})):
                with self.assertRaisesRegexp(AnsibleFailJson, r"version does not meet minimum version required."):
                    base._check_web_services_version()

    def test_check_check_web_services_version_fail(self):
        """Verify exception is thrown when api url is invalid."""
        invalid_url_forms = ["localhost:8080/devmgr/v2",
                             "http:///devmgr/v2"]

        invalid_url_protocols = ["ssh://localhost:8080/devmgr/v2"]

        for url in invalid_url_forms:
            self._set_args({"api_url": url})
            with patch(self.REQ_FUNC, return_value=(200, {"runningAsProxy": True})):
                with self.assertRaisesRegexp(AnsibleFailJson, r"Failed to provide valid API URL."):
                    base = StubNetAppESeriesModule()
                    base._check_web_services_version()

        for url in invalid_url_protocols:
            self._set_args({"api_url": url})
            with patch(self.REQ_FUNC, return_value=(200, {"runningAsProxy": True})):
                with self.assertRaisesRegexp(AnsibleFailJson, r"Protocol must be http or https."):
                    base = StubNetAppESeriesModule()
                    base._check_web_services_version()


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


@pytest.mark.skipif(not netapp_utils.has_netapp_lib(), reason="skipping as missing required netapp_lib")
def test_ems_log_event_version():
    ''' validate Ansible version is correctly read '''
    source = 'unittest'
    server = MockONTAPConnection()
    netapp_utils.ems_log_event(source, server)
    xml = server.xml_in
    version = xml.get_child_content('app-version')
    assert version == ansible_version
    print("Ansible version: %s" % ansible_version)


@pytest.mark.skipif(not netapp_utils.has_netapp_lib(), reason="skipping as missing required netapp_lib")
def test_get_cserver():
    ''' validate cluster vserser name is correctly retrieved '''
    svm_name = 'svm1'
    server = MockONTAPConnection('vserver', svm_name)
    cserver = netapp_utils.get_cserver(server)
    assert cserver == svm_name
