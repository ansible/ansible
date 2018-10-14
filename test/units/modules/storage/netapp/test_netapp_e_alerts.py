# (c) 2018, NetApp Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
import json

from ansible.modules.storage.netapp.netapp_e_alerts import Alerts
from units.modules.utils import AnsibleExitJson, AnsibleFailJson, ModuleTestCase, set_module_args

__metaclass__ = type
from units.compat import mock


class AlertsTest(ModuleTestCase):
    REQUIRED_PARAMS = {
        'api_username': 'rw',
        'api_password': 'password',
        'api_url': 'http://localhost',
        'ssid': '1',
        'state': 'disabled'
    }
    REQ_FUNC = 'ansible.modules.storage.netapp.netapp_e_alerts.request'

    def _set_args(self, **kwargs):
        module_args = self.REQUIRED_PARAMS.copy()
        if kwargs is not None:
            module_args.update(kwargs)
        set_module_args(module_args)

    def _validate_args(self, **kwargs):
        self._set_args(**kwargs)
        Alerts()

    def test_validation_disable(self):
        """Ensure a default configuration succeeds"""
        self._validate_args()

    def test_validation_enable(self):
        """Ensure a typical, default configuration succeeds"""
        self._validate_args(state='enabled', server='localhost', sender='x@y.z', recipients=['a@b.c'])

    def test_validation_fail_required(self):
        """Ensure we fail on missing configuration"""

        # Missing recipients
        with self.assertRaises(AnsibleFailJson):
            self._validate_args(state='enabled', server='localhost', sender='x@y.z')
            Alerts()

        # Missing sender
        with self.assertRaises(AnsibleFailJson):
            self._validate_args(state='enabled', server='localhost', recipients=['a@b.c'])
            Alerts()

        # Missing server
        with self.assertRaises(AnsibleFailJson):
            self._validate_args(state='enabled', sender='x@y.z', recipients=['a@b.c'])

    def test_validation_fail(self):
        # Empty recipients
        with self.assertRaises(AnsibleFailJson):
            self._validate_args(state='enabled', server='localhost', sender='x@y.z', recipients=[])

        # Bad sender
        with self.assertRaises(AnsibleFailJson):
            self._validate_args(state='enabled', server='localhost', sender='y.z', recipients=['a@b.c'])

    def test_get_configuration(self):
        """Validate retrieving the current configuration"""
        self._set_args(state='enabled', server='localhost', sender='x@y.z', recipients=['a@b.c'])

        expected = 'result'
        alerts = Alerts()
        # Expecting an update
        with mock.patch(self.REQ_FUNC, return_value=(200, expected)) as req:
            actual = alerts.get_configuration()
            self.assertEquals(expected, actual)
            self.assertEquals(req.call_count, 1)

    def test_update_configuration(self):
        """Validate updating the configuration"""
        initial = dict(alertingEnabled=True,
                       emailServerAddress='localhost',
                       sendAdditionalContactInformation=True,
                       additionalContactInformation='None',
                       emailSenderAddress='x@y.z',
                       recipientEmailAddresses=['x@y.z']
                       )

        args = dict(state='enabled', server=initial['emailServerAddress'], sender=initial['emailSenderAddress'],
                    contact=initial['additionalContactInformation'], recipients=initial['recipientEmailAddresses'])

        self._set_args(**args)

        alerts = Alerts()

        # Ensure when trigger updates when each relevant field is changed
        with mock.patch(self.REQ_FUNC, return_value=(200, None)) as req:
            with mock.patch.object(alerts, 'get_configuration', return_value=initial):
                update = alerts.update_configuration()
                self.assertFalse(update)

                alerts.sender = 'a@b.c'
                update = alerts.update_configuration()
                self.assertTrue(update)
                self._set_args(**args)

                alerts.recipients = ['a@b.c']
                update = alerts.update_configuration()
                self.assertTrue(update)
                self._set_args(**args)

                alerts.contact = 'abc'
                update = alerts.update_configuration()
                self.assertTrue(update)
                self._set_args(**args)

                alerts.server = 'abc'
                update = alerts.update_configuration()
                self.assertTrue(update)

    def test_send_test_email_check(self):
        """Ensure we handle check_mode correctly"""
        self._set_args(test=True)
        alerts = Alerts()
        alerts.check_mode = True
        with mock.patch(self.REQ_FUNC) as req:
            with mock.patch.object(alerts, 'update_configuration', return_value=True):
                alerts.send_test_email()
                self.assertFalse(req.called)

    def test_send_test_email(self):
        """Ensure we send a test email if test=True"""
        self._set_args(test=True)
        alerts = Alerts()

        with mock.patch(self.REQ_FUNC, return_value=(200, dict(response='emailSentOK'))) as req:
            alerts.send_test_email()
            self.assertTrue(req.called)

    def test_send_test_email_fail(self):
        """Ensure we fail if the test returned a failure status"""
        self._set_args(test=True)
        alerts = Alerts()

        ret_msg = 'fail'
        with self.assertRaisesRegexp(AnsibleFailJson, ret_msg):
            with mock.patch(self.REQ_FUNC, return_value=(200, dict(response=ret_msg))) as req:
                alerts.send_test_email()
                self.assertTrue(req.called)

    def test_send_test_email_fail_connection(self):
        """Ensure we fail cleanly if we hit a connection failure"""
        self._set_args(test=True)
        alerts = Alerts()

        with self.assertRaisesRegexp(AnsibleFailJson, r"failed to send"):
            with mock.patch(self.REQ_FUNC, side_effect=Exception) as req:
                alerts.send_test_email()
                self.assertTrue(req.called)

    def test_update(self):
        # Ensure that when test is enabled and alerting is enabled, we run the test
        self._set_args(state='enabled', server='localhost', sender='x@y.z', recipients=['a@b.c'], test=True)
        alerts = Alerts()
        with self.assertRaisesRegexp(AnsibleExitJson, r"enabled"):
            with mock.patch.object(alerts, 'update_configuration', return_value=True):
                with mock.patch.object(alerts, 'send_test_email') as test:
                    alerts.update()
                    self.assertTrue(test.called)

        # Ensure we don't run a test when changed=False
        with self.assertRaisesRegexp(AnsibleExitJson, r"enabled"):
            with mock.patch.object(alerts, 'update_configuration', return_value=False):
                with mock.patch.object(alerts, 'send_test_email') as test:
                    alerts.update()
                    self.assertFalse(test.called)

        # Ensure that test is not called when we have alerting disabled
        self._set_args(state='disabled')
        alerts = Alerts()
        with self.assertRaisesRegexp(AnsibleExitJson, r"disabled"):
            with mock.patch.object(alerts, 'update_configuration', return_value=True):
                with mock.patch.object(alerts, 'send_test_email') as test:
                    alerts.update()
                    self.assertFalse(test.called)
