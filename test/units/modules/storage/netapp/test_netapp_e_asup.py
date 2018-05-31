# (c) 2018, NetApp Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
import json

from ansible.modules.storage.netapp.netapp_e_asup import Asup
from units.modules.utils import AnsibleExitJson, AnsibleFailJson, ModuleTestCase, set_module_args

__metaclass__ = type
from ansible.compat.tests import mock


class AsupTest(ModuleTestCase):
    REQUIRED_PARAMS = {
        'api_username': 'rw',
        'api_password': 'password',
        'api_url': 'http://localhost',
        'ssid': '1',
    }
    REQ_FUNC = 'ansible.modules.storage.netapp.netapp_e_asup.request'

    def _set_args(self, args=None):
        module_args = self.REQUIRED_PARAMS.copy()
        if args is not None:
            module_args.update(args)
        set_module_args(module_args)

    def test_get_config_invalid(self):
        """Ensure we fail correctly if ASUP is not available on this platform"""
        self._set_args()

        expected = dict(asupCapable=False)
        asup = Asup()
        # Expecting an update
        with self.assertRaisesRegexp(AnsibleFailJson, r"not supported"):
            with mock.patch(self.REQ_FUNC, return_value=(200, expected)) as req:
                config = asup.get_configuration()

    def test_get_config(self):
        """Validate retrieving the ASUP configuration"""
        self._set_args()

        expected = dict(asupCapable=True)
        asup = Asup()

        with mock.patch(self.REQ_FUNC, return_value=(200, expected)) as req:
            config = asup.get_configuration()
            self.assertEquals(config, expected)

    def test_update_configuration(self):
        """Validate retrieving the ASUP configuration"""
        self._set_args(dict(asup='present'))

        expected = dict()
        initial = dict(asupCapable=True,
                       asupEnabled=True,
                       onDemandEnabled=False,
                       remoteDiagsEnabled=False,
                       schedule=dict(daysOfWeek=[], dailyMinTime=0, weeklyMinTime=0, dailyMaxTime=24, weeklyMaxTime=24))
        asup = Asup()

        with mock.patch(self.REQ_FUNC, return_value=(200, expected)) as req:
            with mock.patch.object(asup, 'get_configuration', return_value=initial):
                updated = asup.update_configuration()
                self.assertTrue(req.called)
                self.assertTrue(updated)

    def test_update_configuration_asup_disable(self):
        """Validate retrieving the ASUP configuration"""
        self._set_args(dict(asup='absent'))

        expected = dict()
        initial = dict(asupCapable=True,
                       asupEnabled=True,
                       onDemandEnabled=False,
                       remoteDiagsEnabled=False,
                       schedule=dict(daysOfWeek=[], dailyMinTime=0, weeklyMinTime=0, dailyMaxTime=24, weeklyMaxTime=24))
        asup = Asup()

        with mock.patch(self.REQ_FUNC, return_value=(200, expected)) as req:
            with mock.patch.object(asup, 'get_configuration', return_value=initial):
                updated = asup.update_configuration()
                self.assertTrue(updated)

                self.assertTrue(req.called)

                # Ensure it was called with the right arguments
                called_with = req.call_args
                body = json.loads(called_with[1]['data'])
                self.assertFalse(body['asupEnabled'])

    def test_update_configuration_enable(self):
        """Validate retrieving the ASUP configuration"""
        self._set_args(dict(asup='enabled'))

        expected = dict()
        initial = dict(asupCapable=False,
                       asupEnabled=False,
                       onDemandEnabled=False,
                       remoteDiagsEnabled=False,
                       schedule=dict(daysOfWeek=[], dailyMinTime=0, weeklyMinTime=0, dailyMaxTime=24, weeklyMaxTime=24))
        asup = Asup()

        with mock.patch(self.REQ_FUNC, return_value=(200, expected)) as req:
            with mock.patch.object(asup, 'get_configuration', return_value=initial):
                updated = asup.update_configuration()
                self.assertTrue(updated)

                self.assertTrue(req.called)

                # Ensure it was called with the right arguments
                called_with = req.call_args
                body = json.loads(called_with[1]['data'])
                self.assertTrue(body['asupEnabled'])
                self.assertTrue(body['onDemandEnabled'])
                self.assertTrue(body['remoteDiagsEnabled'])
