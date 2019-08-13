# (c) 2018, NetApp Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from ansible.modules.storage.netapp.netapp_e_syslog import Syslog
from units.modules.utils import AnsibleFailJson, ModuleTestCase, set_module_args

__metaclass__ = type
from units.compat import mock


class AsupTest(ModuleTestCase):
    REQUIRED_PARAMS = {
        "api_username": "rw",
        "api_password": "password",
        "api_url": "http://localhost",
    }
    REQ_FUNC = 'ansible.modules.storage.netapp.netapp_e_syslog.request'

    def _set_args(self, args=None):
        module_args = self.REQUIRED_PARAMS.copy()
        if args is not None:
            module_args.update(args)
        set_module_args(module_args)

    def test_test_configuration_fail(self):
        """Validate test_configuration fails when request exception is thrown."""
        initial = {"state": "present",
                   "ssid": "1",
                   "address": "192.168.1.1",
                   "port": "514",
                   "protocol": "udp",
                   "components": ["auditLog"]}
        self._set_args(initial)
        syslog = Syslog()

        with self.assertRaisesRegexp(AnsibleFailJson, r"We failed to send test message!"):
            with mock.patch(self.REQ_FUNC, side_effect=Exception()):
                with mock.patch("time.sleep", return_value=None):  # mocking sleep is not working
                    syslog.test_configuration(self.REQUIRED_PARAMS)

    def test_update_configuration_record_match_pass(self):
        """Verify existing syslog server record match does not issue update request."""
        initial = {"state": "present",
                   "ssid": "1",
                   "address": "192.168.1.1",
                   "port": "514",
                   "protocol": "udp",
                   "components": ["auditLog"]}
        expected = [{"id": "123456",
                     "serverAddress": "192.168.1.1",
                     "port": 514,
                     "protocol": "udp",
                     "components": [{"type": "auditLog"}]}]

        self._set_args(initial)
        syslog = Syslog()

        with mock.patch(self.REQ_FUNC, side_effect=[(200, expected), (200, None)]):
            updated = syslog.update_configuration()
            self.assertFalse(updated)

    def test_update_configuration_record_partial_match_pass(self):
        """Verify existing syslog server record partial match results in an update request."""
        initial = {"state": "present",
                   "ssid": "1",
                   "address": "192.168.1.1",
                   "port": "514",
                   "protocol": "tcp",
                   "components": ["auditLog"]}
        expected = [{"id": "123456",
                     "serverAddress": "192.168.1.1",
                     "port": 514,
                     "protocol": "udp",
                     "components": [{"type": "auditLog"}]}]

        self._set_args(initial)
        syslog = Syslog()

        with mock.patch(self.REQ_FUNC, side_effect=[(200, expected), (200, None)]):
            updated = syslog.update_configuration()
            self.assertTrue(updated)

    def test_update_configuration_record_no_match_pass(self):
        """Verify existing syslog server record partial match results in an update request."""
        initial = {"state": "present",
                   "ssid": "1",
                   "address": "192.168.1.1",
                   "port": "514",
                   "protocol": "tcp",
                   "components": ["auditLog"]}
        expected = [{"id": "123456",
                     "serverAddress": "192.168.1.100",
                     "port": 514,
                     "protocol": "udp",
                     "components": [{"type": "auditLog"}]}]

        self._set_args(initial)
        syslog = Syslog()

        with mock.patch(self.REQ_FUNC, side_effect=[(200, expected), (200, dict(id=1234))]):
            updated = syslog.update_configuration()
            self.assertTrue(updated)

    def test_update_configuration_record_no_match_defaults_pass(self):
        """Verify existing syslog server record partial match results in an update request."""
        initial = {"state": "present",
                   "ssid": "1",
                   "address": "192.168.1.1",
                   "port": "514",
                   "protocol": "tcp",
                   "components": ["auditLog"]}
        expected = [{"id": "123456",
                     "serverAddress": "192.168.1.100",
                     "port": 514,
                     "protocol": "udp",
                     "components": [{"type": "auditLog"}]}]

        self._set_args(initial)
        syslog = Syslog()

        with mock.patch(self.REQ_FUNC, side_effect=[(200, expected), (200, dict(id=1234))]):
            updated = syslog.update_configuration()
            self.assertTrue(updated)
