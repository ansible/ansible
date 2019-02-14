# (c) 2018, NetApp Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


from ansible.modules.storage.netapp.netapp_e_global import GlobalSettings
from units.modules.utils import AnsibleExitJson, AnsibleFailJson, ModuleTestCase, set_module_args

__metaclass__ = type
from units.compat import mock


class GlobalSettingsTest(ModuleTestCase):
    REQUIRED_PARAMS = {
        'api_username': 'rw',
        'api_password': 'password',
        'api_url': 'http://localhost',
        'ssid': '1',
    }
    REQ_FUNC = 'ansible.modules.storage.netapp.netapp_e_global.request'

    def _set_args(self, args=None):
        module_args = self.REQUIRED_PARAMS.copy()
        if args is not None:
            module_args.update(args)
        set_module_args(module_args)

    def test_set_name(self):
        """Ensure we can successfully set the name"""
        self._set_args(dict(name="x"))

        expected = dict(name='y', status='online')
        namer = GlobalSettings()
        # Expecting an update
        with mock.patch(self.REQ_FUNC, return_value=(200, expected)) as req:
            with mock.patch.object(namer, 'get_name', return_value='y'):
                update = namer.update_name()
                self.assertTrue(update)
        # Expecting no update
        with mock.patch(self.REQ_FUNC, return_value=(200, expected)) as req:
            with mock.patch.object(namer, 'get_name', return_value='x'):
                update = namer.update_name()
                self.assertFalse(update)

        # Expecting an update, but no actual calls, since we're using check_mode=True
        namer.check_mode = True
        with mock.patch(self.REQ_FUNC, return_value=(200, expected)) as req:
            with mock.patch.object(namer, 'get_name', return_value='y'):
                update = namer.update_name()
                self.assertEquals(0, req.called)
                self.assertTrue(update)

    def test_get_name(self):
        """Ensure we can successfully set the name"""
        self._set_args()

        expected = dict(name='y', status='online')
        namer = GlobalSettings()

        with mock.patch(self.REQ_FUNC, return_value=(200, expected)) as req:
            name = namer.get_name()
            self.assertEquals(name, expected['name'])

    def test_get_name_fail(self):
        """Ensure we can successfully set the name"""
        self._set_args()

        expected = dict(name='y', status='offline')
        namer = GlobalSettings()

        with self.assertRaises(AnsibleFailJson):
            with mock.patch(self.REQ_FUNC, side_effect=Exception()) as req:
                name = namer.get_name()

        with self.assertRaises(AnsibleFailJson):
            with mock.patch(self.REQ_FUNC, return_value=(200, expected)) as req:
                update = namer.update_name()
