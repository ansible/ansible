# coding=utf-8
# (c) 2018, NetApp Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from ansible.modules.storage.netapp.netapp_e_iscsi_target import IscsiTarget
from units.modules.utils import AnsibleFailJson, ModuleTestCase, set_module_args

__metaclass__ = type

import mock

from units.compat.mock import PropertyMock


class IscsiTargetTest(ModuleTestCase):
    REQUIRED_PARAMS = {
        'api_username': 'rw',
        'api_password': 'password',
        'api_url': 'http://localhost',
        'ssid': '1',
        'name': 'abc',
    }

    CHAP_SAMPLE = 'a' * 14

    REQ_FUNC = 'ansible.modules.storage.netapp.netapp_e_iscsi_target.request'

    def _set_args(self, args=None):
        module_args = self.REQUIRED_PARAMS.copy()
        if args is not None:
            module_args.update(args)
        set_module_args(module_args)

    def test_validate_params(self):
        """Ensure we can pass valid parameters to the module"""
        for i in range(12, 57):
            secret = 'a' * i
            self._set_args(dict(chap=secret))
            tgt = IscsiTarget()

    def test_invalid_chap_secret(self):
        for secret in [11 * 'a', 58 * 'a']:
            with self.assertRaisesRegexp(AnsibleFailJson, r'.*?CHAP secret is not valid.*') as result:
                self._set_args(dict(chap=secret))
                tgt = IscsiTarget()

    def test_apply_iscsi_settings(self):
        """Ensure that the presence of CHAP always triggers an update."""
        self._set_args(dict(chap=self.CHAP_SAMPLE))
        tgt = IscsiTarget()

        # CHAP is enabled
        fake = dict(alias=self.REQUIRED_PARAMS.get('name'), chap=True)

        # We don't care about the return here
        with mock.patch(self.REQ_FUNC, return_value=(200, "")) as request:
            with mock.patch.object(IscsiTarget, 'target', new_callable=PropertyMock) as call:
                call.return_value = fake
                self.assertTrue(tgt.apply_iscsi_settings())
                self.assertTrue(request.called, msg="An update was expected!")

                # Retest with check_mode enabled
                tgt.check_mode = True
                request.reset_mock()
                self.assertTrue(tgt.apply_iscsi_settings())
                self.assertFalse(request.called, msg="No update was expected in check_mode!")

    def test_apply_iscsi_settings_no_change(self):
        """Ensure that we don't make unnecessary requests or updates"""
        name = 'abc'
        self._set_args(dict(alias=name))
        fake = dict(alias=name, chap=False)
        with mock.patch(self.REQ_FUNC, return_value=(200, "")) as request:
            with mock.patch.object(IscsiTarget, 'target', new_callable=PropertyMock) as call:
                call.return_value = fake
                tgt = IscsiTarget()
                self.assertFalse(tgt.apply_iscsi_settings())
                self.assertFalse(request.called, msg="No update was expected!")

    def test_apply_iscsi_settings_fail(self):
        """Ensure we handle request failures cleanly"""
        self._set_args()
        fake = dict(alias='', chap=True)
        with self.assertRaisesRegexp(AnsibleFailJson, r".*?update.*"):
            with mock.patch(self.REQ_FUNC, side_effect=Exception) as request:
                with mock.patch.object(IscsiTarget, 'target', new_callable=PropertyMock) as call:
                    call.return_value = fake
                    tgt = IscsiTarget()
                    tgt.apply_iscsi_settings()

    def test_apply_target_changes(self):
        """Ensure that changes trigger an update."""
        self._set_args(dict(ping=True, unnamed_discovery=True))
        tgt = IscsiTarget()

        # CHAP is enabled
        fake = dict(ping=False, unnamed_discovery=False)

        # We don't care about the return here
        with mock.patch(self.REQ_FUNC, return_value=(200, "")) as request:
            with mock.patch.object(IscsiTarget, 'target', new_callable=PropertyMock) as call:
                call.return_value = fake
                self.assertTrue(tgt.apply_target_changes())
                self.assertTrue(request.called, msg="An update was expected!")

                # Retest with check_mode enabled
                tgt.check_mode = True
                request.reset_mock()
                self.assertTrue(tgt.apply_target_changes())
                self.assertFalse(request.called, msg="No update was expected in check_mode!")

    def test_apply_target_changes_no_change(self):
        """Ensure that we don't make unnecessary requests or updates"""
        self._set_args(dict(ping=True, unnamed_discovery=True))
        fake = dict(ping=True, unnamed_discovery=True)
        with mock.patch(self.REQ_FUNC, return_value=(200, "")) as request:
            with mock.patch.object(IscsiTarget, 'target', new_callable=PropertyMock) as call:
                call.return_value = fake
                tgt = IscsiTarget()
                self.assertFalse(tgt.apply_target_changes())
                self.assertFalse(request.called, msg="No update was expected!")

    def test_apply_target_changes_fail(self):
        """Ensure we handle request failures cleanly"""
        self._set_args()
        fake = dict(ping=False, unnamed_discovery=False)
        with self.assertRaisesRegexp(AnsibleFailJson, r".*?update.*"):
            with mock.patch(self.REQ_FUNC, side_effect=Exception) as request:
                with mock.patch.object(IscsiTarget, 'target', new_callable=PropertyMock) as call:
                    call.return_value = fake
                    tgt = IscsiTarget()
                    tgt.apply_target_changes()
