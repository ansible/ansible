# (c) 2018, NetApp Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from ansible.module_utils.six.moves.urllib.error import URLError

from ansible.module_utils.netapp import NetAppESeriesModule
from units.modules.utils import ModuleTestCase, set_module_args, AnsibleFailJson

__metaclass__ = type
from units.compat import mock


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

    def test_about_url_pass(self):
        """Verify about_url property returns expected about url."""
        test_set = [("http://localhost/devmgr/v2", "http://localhost:8080/devmgr/utils/about"),
                    ("http://localhost:8443/devmgr/v2", "https://localhost:8443/devmgr/utils/about"),
                    ("http://localhost:8443/devmgr/v2/", "https://localhost:8443/devmgr/utils/about"),
                    ("http://localhost:443/something_else", "https://localhost:8443/devmgr/utils/about"),
                    ("http://localhost:8443", "https://localhost:8443/devmgr/utils/about"),
                    ("http://localhost", "http://localhost:8080/devmgr/utils/about")]

        for url in test_set:
            self._set_args({"api_url": url[0]})
            base = StubNetAppESeriesModule()
            self.assertTrue(base._about_url == url[1])

    def test_is_embedded_embedded_pass(self):
        """Verify is_embedded successfully returns True when an embedded web service's rest api is inquired."""
        self._set_args()
        with mock.patch(self.REQ_FUNC, return_value=(200, {"runningAsProxy": False})):
            base = StubNetAppESeriesModule()
            self.assertTrue(base.is_embedded())
        with mock.patch(self.REQ_FUNC, return_value=(200, {"runningAsProxy": True})):
            base = StubNetAppESeriesModule()
            self.assertFalse(base.is_embedded())

    def test_check_web_services_version_pass(self):
        """Verify that an acceptable rest api version passes."""
        minimum_required = "02.10.9000.0010"
        test_set = ["03.9.9000.0010", "03.10.9000.0009", "02.11.9000.0009", "02.10.9000.0010"]

        self._set_args()
        base = StubNetAppESeriesModule()
        base.web_services_version = minimum_required
        base.is_embedded = lambda: True
        for current_version in test_set:
            with mock.patch(self.REQ_FUNC, return_value=(200, {"version": current_version})):
                self.assertTrue(base._is_web_services_valid())

    def test_check_web_services_version_fail(self):
        """Verify that an unacceptable rest api version fails."""
        minimum_required = "02.10.9000.0010"
        test_set = ["02.10.9000.0009", "02.09.9000.0010", "01.10.9000.0010"]

        self._set_args()
        base = StubNetAppESeriesModule()
        base.web_services_version = minimum_required
        base.is_embedded = lambda: True
        for current_version in test_set:
            with mock.patch(self.REQ_FUNC, return_value=(200, {"version": current_version})):
                with self.assertRaisesRegexp(AnsibleFailJson, r"version does not meet minimum version required."):
                    base._is_web_services_valid()

    def test_is_embedded_fail(self):
        """Verify exception is thrown when a web service's rest api fails to return about information."""
        self._set_args()
        with mock.patch(self.REQ_FUNC, return_value=Exception()):
            with self.assertRaisesRegexp(AnsibleFailJson, r"Failed to retrieve the webservices about information!"):
                base = StubNetAppESeriesModule()
                base.is_embedded()
        with mock.patch(self.REQ_FUNC, side_effect=[URLError(""), Exception()]):
            with self.assertRaisesRegexp(AnsibleFailJson, r"Failed to retrieve the webservices about information!"):
                base = StubNetAppESeriesModule()
                base.is_embedded()

    def test_tweak_url_pass(self):
        """Verify a range of valid netapp eseries rest api urls pass."""
        test_set = [("http://localhost/devmgr/v2", "http://localhost:8080/devmgr/v2/"),
                    ("localhost", "https://localhost:8443/devmgr/v2/"),
                    ("localhost:8443/devmgr/v2", "https://localhost:8443/devmgr/v2/"),
                    ("https://localhost/devmgr/v2", "https://localhost:8443/devmgr/v2/"),
                    ("http://localhost:8443", "https://localhost:8443/devmgr/v2/"),
                    ("http://localhost:/devmgr/v2", "https://localhost:8443/devmgr/v2/"),
                    ("http://localhost:8080", "http://localhost:8080/devmgr/v2/"),
                    ("http://localhost", "http://localhost:8080/devmgr/v2/"),
                    ("localhost/devmgr/v2", "https://localhost:8443/devmgr/v2/"),
                    ("localhost/devmgr", "https://localhost:8443/devmgr/v2/"),
                    ("localhost/devmgr/v3", "https://localhost:8443/devmgr/v2/"),
                    ("localhost/something", "https://localhost:8443/devmgr/v2/"),
                    ("ftp://localhost", "https://localhost:8443/devmgr/v2/"),
                    ("ftp://localhost:8080", "http://localhost:8080/devmgr/v2/"),
                    ("ftp://localhost/devmgr/v2/", "https://localhost:8443/devmgr/v2/")]

        for test in test_set:
            self._set_args({"api_url": test[0]})
            with mock.patch(self.REQ_FUNC, side_effect=[URLError(""), (200, {"runningAsProxy": False})]):
                base = StubNetAppESeriesModule()
                base._tweak_url()
                self.assertTrue(base.url == test[1])

    def test_check_url_missing_hostname_fail(self):
        """Verify exception is thrown when hostname or ip address is missing."""
        self._set_args({"api_url": "http:///devmgr/v2"})
        with mock.patch(self.REQ_FUNC, return_value=(200, {"runningAsProxy": True})):
            with self.assertRaisesRegexp(AnsibleFailJson, r"Failed to provide a valid hostname or IP address."):
                base = StubNetAppESeriesModule()
                base._tweak_url()
