# (c) 2018, NetApp Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import os
import shutil
import tempfile

from ansible.modules.storage.netapp.netapp_e_ldap import Ldap
from units.modules.utils import ModuleTestCase, set_module_args, AnsibleFailJson, AnsibleExitJson

__metaclass__ = type
from units.compat import mock


class LdapTest(ModuleTestCase):
    REQUIRED_PARAMS = {
        'api_username': 'admin',
        'api_password': 'password',
        'api_url': 'http://localhost',
        'ssid': '1',
        'state': 'absent',
    }
    REQ_FUNC = 'ansible.modules.storage.netapp.netapp_e_ldap.request'

    def setUp(self):
        super(LdapTest, self).setUp()

        self.temp_dir = tempfile.mkdtemp('ansible-test_netapp_e_ldap-')
        self.REQUIRED_PARAMS['log_path'] = os.path.join(self.temp_dir, 'debug.log')

    def tearDown(self):
        super(LdapTest, self).tearDown()

        shutil.rmtree(self.temp_dir)

    def _make_ldap_instance(self):
        self._set_args()
        ldap = Ldap()
        ldap.base_path = '/'
        return ldap

    def _set_args(self, **kwargs):
        module_args = self.REQUIRED_PARAMS.copy()
        module_args.update(kwargs)
        set_module_args(module_args)

    def test_init_defaults(self):
        """Validate a basic run with required arguments set."""
        self._set_args(log_path=None,
                       state='present',
                       username='myBindAcct',
                       password='myBindPass',
                       server='ldap://example.com:384',
                       search_base='OU=Users,DC=example,DC=com',
                       role_mappings={'.*': ['storage.monitor']},
                       )

        ldap = Ldap()

    def test_init(self):
        """Validate a basic run with required arguments set."""
        self._set_args(log_path=None)
        ldap = Ldap()

    def test_is_embedded(self):
        """Ensure we can properly detect the type of Web Services instance we're utilizing."""
        self._set_args()

        result = dict(runningAsProxy=False)

        with mock.patch(self.REQ_FUNC, return_value=(200, result)):
            ldap = Ldap()
            embedded = ldap.is_embedded()
            self.assertTrue(embedded)

        result = dict(runningAsProxy=True)

        with mock.patch(self.REQ_FUNC, return_value=(200, result)):
            ldap = Ldap()
            embedded = ldap.is_embedded()
            self.assertFalse(embedded)

    def test_is_embedded_fail(self):
        """Ensure we fail gracefully when fetching the About data."""

        self._set_args()
        with self.assertRaises(AnsibleFailJson):
            with mock.patch(self.REQ_FUNC, side_effect=Exception):
                ldap = Ldap()
                ldap.is_embedded()

    def test_get_full_configuration(self):
        self._set_args()

        resp = dict(result=None)

        with mock.patch(self.REQ_FUNC, return_value=(200, resp)):
            ldap = self._make_ldap_instance()
            result = ldap.get_full_configuration()
            self.assertEqual(resp, result)

    def test_get_full_configuration_failure(self):
        self._set_args()

        resp = dict(result=None)
        with self.assertRaises(AnsibleFailJson):
            with mock.patch(self.REQ_FUNC, side_effect=Exception):
                ldap = self._make_ldap_instance()
                ldap.get_full_configuration()

    def test_get_configuration(self):
        self._set_args()

        resp = dict(result=None)

        with mock.patch(self.REQ_FUNC, return_value=(200, resp)):
            ldap = self._make_ldap_instance()
            result = ldap.get_configuration('')
            self.assertEqual(resp, result)

        with mock.patch(self.REQ_FUNC, return_value=(404, resp)):
            ldap = self._make_ldap_instance()
            result = ldap.get_configuration('')
            self.assertIsNone(result)

    def test_clear_configuration(self):
        self._set_args()

        # No changes are required if the domains are empty
        config = dict(ldapDomains=[])

        ldap = self._make_ldap_instance()
        with mock.patch.object(ldap, 'get_full_configuration', return_value=config):
            with mock.patch(self.REQ_FUNC, return_value=(204, None)):
                msg, result = ldap.clear_configuration()
                self.assertFalse(result)

        config = dict(ldapDomains=['abc'])

        # When domains exist, we need to clear
        ldap = self._make_ldap_instance()
        with mock.patch.object(ldap, 'get_full_configuration', return_value=config):
            with mock.patch(self.REQ_FUNC, return_value=(204, None)) as req:
                msg, result = ldap.clear_configuration()
                self.assertTrue(result)
                self.assertTrue(req.called)

                # Valid check_mode makes no changes
                req.reset_mock()
                ldap.check_mode = True
                msg, result = ldap.clear_configuration()
                self.assertTrue(result)
                self.assertFalse(req.called)

    def test_clear_single_configuration(self):
        self._set_args()

        # No changes are required if the domains are empty
        config = 'abc'

        ldap = self._make_ldap_instance()
        with mock.patch.object(ldap, 'get_configuration', return_value=config):
            with mock.patch(self.REQ_FUNC, return_value=(204, None)) as req:
                msg, result = ldap.clear_single_configuration()
                self.assertTrue(result)

                # Valid check_mode makes no changes
                req.reset_mock()
                ldap.check_mode = True
                msg, result = ldap.clear_single_configuration()
                self.assertTrue(result)
                self.assertFalse(req.called)

        # When domains exist, we need to clear
        ldap = self._make_ldap_instance()
        with mock.patch.object(ldap, 'get_configuration', return_value=None):
            with mock.patch(self.REQ_FUNC, return_value=(204, None)) as req:
                msg, result = ldap.clear_single_configuration()
                self.assertFalse(result)
                self.assertFalse(req.called)

    def test_update_configuration(self):
        self._set_args()

        config = dict(id='abc')
        body = dict(id='xyz')

        ldap = self._make_ldap_instance()
        with mock.patch.object(ldap, 'make_configuration', return_value=body):
            with mock.patch.object(ldap, 'get_configuration', return_value=config):
                with mock.patch(self.REQ_FUNC, return_value=(200, None)) as req:
                    msg, result = ldap.update_configuration()
                    self.assertTrue(result)

                    # Valid check_mode makes no changes
                    req.reset_mock()
                    ldap.check_mode = True
                    msg, result = ldap.update_configuration()
                    self.assertTrue(result)
                    self.assertFalse(req.called)

    def test_update(self):
        self._set_args()

        ldap = self._make_ldap_instance()
        with self.assertRaises(AnsibleExitJson):
            with mock.patch.object(ldap, 'get_base_path', return_value='/'):
                with mock.patch.object(ldap, 'update_configuration', return_value=('', True)) as update:
                    ldap.ldap = True
                    msg, result = ldap.update()
                    self.assertTrue(result)
                    self.assertTrue(update.called)

    def test_update_disable(self):
        self._set_args()

        ldap = self._make_ldap_instance()
        with self.assertRaises(AnsibleExitJson):
            with mock.patch.object(ldap, 'get_base_path', return_value='/'):
                with mock.patch.object(ldap, 'clear_single_configuration', return_value=('', True)) as update:
                    ldap.ldap = False
                    ldap.identifier = 'abc'
                    msg, result = ldap.update()
                    self.assertTrue(result)
                    self.assertTrue(update.called)

    def test_update_disable_all(self):
        self._set_args()

        ldap = self._make_ldap_instance()
        with self.assertRaises(AnsibleExitJson):
            with mock.patch.object(ldap, 'get_base_path', return_value='/'):
                with mock.patch.object(ldap, 'clear_configuration', return_value=('', True)) as update:
                    ldap.ldap = False
                    msg, result = ldap.update()
                    self.assertTrue(result)
                    self.assertTrue(update.called)

    def test_get_configuration_failure(self):
        self._set_args()

        with self.assertRaises(AnsibleFailJson):
            with mock.patch(self.REQ_FUNC, side_effect=Exception):
                ldap = self._make_ldap_instance()
                ldap.get_configuration('')

        # We expect this for any code not in [200, 404]
        with self.assertRaises(AnsibleFailJson):
            with mock.patch(self.REQ_FUNC, return_value=(401, '')):
                ldap = self._make_ldap_instance()
                result = ldap.get_configuration('')
                self.assertIsNone(result)

    def test_make_configuration(self):
        """Validate the make_configuration method that translates Ansible params to the input body"""
        data = dict(log_path=None,
                    state='present',
                    username='myBindAcct',
                    password='myBindPass',
                    server='ldap://example.com:384',
                    search_base='OU=Users,DC=example,DC=com',
                    role_mappings={'.*': ['storage.monitor']},
                    )

        self._set_args(**data)
        ldap = Ldap()
        expected = dict(id='default',
                        bindLookupUser=dict(user=data['username'],
                                            password=data['password'], ),
                        groupAttributes=['memberOf'],
                        ldapUrl=data['server'],
                        names=['example.com'],
                        searchBase=data['search_base'],
                        roleMapCollection=[{"groupRegex": ".*",
                                            "ignoreCase": True,
                                            "name": "storage.monitor"
                                            }
                                           ],
                        userAttribute='sAMAccountName'
                        )

        actual = ldap.make_configuration()
        self.maxDiff = None
        self.assertEqual(expected, actual)

    #
    # def test_get_config_on_demand_capable_false(self):
    #     """Ensure we fail correctly if ASUP is not available on this platform"""
    #     self._set_args()
    #
    #     expected = dict(asupCapable=True, onDemandCapable=False)
    #     asup = Asup()
    #     # Expecting an update
    #     with self.assertRaisesRegexp(AnsibleFailJson, r"not supported"):
    #         with mock.patch(self.REQ_FUNC, return_value=(200, expected)):
    #             asup.get_configuration()
    #
    # def test_get_config(self):
    #     """Validate retrieving the ASUP configuration"""
    #     self._set_args()
    #
    #     expected = dict(asupCapable=True, onDemandCapable=True)
    #     asup = Asup()
    #
    #     with mock.patch(self.REQ_FUNC, return_value=(200, expected)):
    #         config = asup.get_configuration()
    #         self.assertEquals(config, expected)
    #
    # def test_update_configuration(self):
    #     """Validate retrieving the ASUP configuration"""
    #     self._set_args(dict(asup='present'))
    #
    #     expected = dict()
    #     initial = dict(asupCapable=True,
    #                    asupEnabled=True,
    #                    onDemandEnabled=False,
    #                    remoteDiagsEnabled=False,
    #                    schedule=dict(daysOfWeek=[], dailyMinTime=0, weeklyMinTime=0, dailyMaxTime=24, weeklyMaxTime=24))
    #     asup = Asup()
    #
    #     with mock.patch(self.REQ_FUNC, return_value=(200, expected)) as req:
    #         with mock.patch.object(asup, 'get_configuration', return_value=initial):
    #             updated = asup.update_configuration()
    #             self.assertTrue(req.called)
    #             self.assertTrue(updated)
    #
    # def test_update_configuration_asup_disable(self):
    #     """Validate retrieving the ASUP configuration"""
    #     self._set_args(dict(asup='absent'))
    #
    #     expected = dict()
    #     initial = dict(asupCapable=True,
    #                    asupEnabled=True,
    #                    onDemandEnabled=False,
    #                    remoteDiagsEnabled=False,
    #                    schedule=dict(daysOfWeek=[], dailyMinTime=0, weeklyMinTime=0, dailyMaxTime=24, weeklyMaxTime=24))
    #     asup = Asup()
    #
    #     with mock.patch(self.REQ_FUNC, return_value=(200, expected)) as req:
    #         with mock.patch.object(asup, 'get_configuration', return_value=initial):
    #             updated = asup.update_configuration()
    #             self.assertTrue(updated)
    #
    #             self.assertTrue(req.called)
    #
    #             # Ensure it was called with the right arguments
    #             called_with = req.call_args
    #             body = json.loads(called_with[1]['data'])
    #             self.assertFalse(body['asupEnabled'])
    #
    # def test_update_configuration_enable(self):
    #     """Validate retrieving the ASUP configuration"""
    #     self._set_args(dict(asup='enabled'))
    #
    #     expected = dict()
    #     initial = dict(asupCapable=False,
    #                    asupEnabled=False,
    #                    onDemandEnabled=False,
    #                    remoteDiagsEnabled=False,
    #                    schedule=dict(daysOfWeek=[], dailyMinTime=0, weeklyMinTime=0, dailyMaxTime=24, weeklyMaxTime=24))
    #     asup = Asup()
    #
    #     with mock.patch(self.REQ_FUNC, return_value=(200, expected)) as req:
    #         with mock.patch.object(asup, 'get_configuration', return_value=initial):
    #             updated = asup.update_configuration()
    #             self.assertTrue(updated)
    #
    #             self.assertTrue(req.called)
    #
    #             # Ensure it was called with the right arguments
    #             called_with = req.call_args
    #             body = json.loads(called_with[1]['data'])
    #             self.assertTrue(body['asupEnabled'])
    #             self.assertTrue(body['onDemandEnabled'])
    #             self.assertTrue(body['remoteDiagsEnabled'])
    #
    # def test_update_configuration_request_exception(self):
    #     """Validate exception handling when request throws an exception."""
    #     config_response = dict(asupEnabled=True,
    #                            onDemandEnabled=True,
    #                            remoteDiagsEnabled=True,
    #                            schedule=dict(daysOfWeek=[],
    #                                          dailyMinTime=0,
    #                                          weeklyMinTime=0,
    #                                          dailyMaxTime=24,
    #                                          weeklyMaxTime=24))
    #
    #     self._set_args(dict(state="enabled"))
    #     asup = Asup()
    #     with self.assertRaises(Exception):
    #         with mock.patch.object(asup, 'get_configuration', return_value=config_response):
    #             with mock.patch(self.REQ_FUNC, side_effect=Exception):
    #                 asup.update_configuration()
    #
    # def test_init_schedule(self):
    #     """Validate schedule correct schedule initialization"""
    #     self._set_args(dict(state="enabled", active=True, days=["sunday", "monday", "tuesday"], start=20, end=24))
    #     asup = Asup()
    #
    #     self.assertTrue(asup.asup)
    #     self.assertEquals(asup.days, ["sunday", "monday", "tuesday"]),
    #     self.assertEquals(asup.start, 1200)
    #     self.assertEquals(asup.end, 1439)
    #
    # def test_init_schedule_invalid(self):
    #     """Validate updating ASUP with invalid schedule fails test."""
    #     self._set_args(dict(state="enabled", active=True, start=22, end=20))
    #     with self.assertRaisesRegexp(AnsibleFailJson, r"start time is invalid"):
    #         Asup()
    #
    # def test_init_schedule_days_invalid(self):
    #     """Validate updating ASUP with invalid schedule fails test."""
    #     self._set_args(dict(state="enabled", active=True, days=["someday", "thataday", "nonday"]))
    #     with self.assertRaises(AnsibleFailJson):
    #         Asup()
    #
    # def test_update(self):
    #     """Validate updating ASUP with valid schedule passes"""
    #     initial = dict(asupCapable=True,
    #                    onDemandCapable=True,
    #                    asupEnabled=True,
    #                    onDemandEnabled=False,
    #                    remoteDiagsEnabled=False,
    #                    schedule=dict(daysOfWeek=[], dailyMinTime=0, weeklyMinTime=0, dailyMaxTime=24, weeklyMaxTime=24))
    #     self._set_args(dict(state="enabled", active=True, days=["sunday", "monday", "tuesday"], start=10, end=20))
    #     asup = Asup()
    #     with self.assertRaisesRegexp(AnsibleExitJson, r"ASUP settings have been updated"):
    #         with mock.patch(self.REQ_FUNC, return_value=(200, dict(asupCapable=True))):
    #             with mock.patch.object(asup, "get_configuration", return_value=initial):
    #                 asup.update()
