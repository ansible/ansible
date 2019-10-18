# (c) 2018, NetApp Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from ansible.modules.storage.netapp.netapp_e_auditlog import AuditLog
from units.modules.utils import AnsibleFailJson, ModuleTestCase, set_module_args

__metaclass__ = type
from units.compat import mock


class AuditLogTests(ModuleTestCase):
    REQUIRED_PARAMS = {'api_username': 'rw',
                       'api_password': 'password',
                       'api_url': 'http://localhost',
                       'ssid': '1'}
    REQ_FUNC = 'ansible.modules.storage.netapp.netapp_e_auditlog.request'
    MAX_RECORDS_MAXIMUM = 50000
    MAX_RECORDS_MINIMUM = 100

    def _set_args(self, **kwargs):
        module_args = self.REQUIRED_PARAMS.copy()
        if kwargs is not None:
            module_args.update(kwargs)
        set_module_args(module_args)

    def test_max_records_argument_pass(self):
        """Verify AuditLog arument's max_records and threshold upper and lower boundaries."""
        initial = {"max_records": 1000,
                   "log_level": "writeOnly",
                   "full_policy": "overWrite",
                   "threshold": 90}
        max_records_set = (self.MAX_RECORDS_MINIMUM, 25000, self.MAX_RECORDS_MAXIMUM)

        for max_records in max_records_set:
            initial["max_records"] = max_records
            self._set_args(**initial)
            with mock.patch(self.REQ_FUNC, return_value=(200, {"runningAsProxy": False})):
                audit_log = AuditLog()
                self.assertTrue(audit_log.max_records == max_records)

    def test_max_records_argument_fail(self):
        """Verify AuditLog arument's max_records and threshold upper and lower boundaries."""
        initial = {"max_records": 1000,
                   "log_level": "writeOnly",
                   "full_policy": "overWrite",
                   "threshold": 90}
        max_records_set = (self.MAX_RECORDS_MINIMUM - 1, self.MAX_RECORDS_MAXIMUM + 1)

        for max_records in max_records_set:
            with self.assertRaisesRegexp(AnsibleFailJson, r"Audit-log max_records count must be between 100 and 50000"):
                initial["max_records"] = max_records
                self._set_args(**initial)
                AuditLog()

    def test_threshold_argument_pass(self):
        """Verify AuditLog arument's max_records and threshold upper and lower boundaries."""
        initial = {"max_records": 1000,
                   "log_level": "writeOnly",
                   "full_policy": "overWrite",
                   "threshold": 90}
        threshold_set = (60, 75, 90)

        for threshold in threshold_set:
            initial["threshold"] = threshold
            self._set_args(**initial)
            with mock.patch(self.REQ_FUNC, return_value=(200, {"runningAsProxy": False})):
                audit_log = AuditLog()
                self.assertTrue(audit_log.threshold == threshold)

    def test_threshold_argument_fail(self):
        """Verify AuditLog arument's max_records and threshold upper and lower boundaries."""
        initial = {"max_records": 1000,
                   "log_level": "writeOnly",
                   "full_policy": "overWrite",
                   "threshold": 90}
        threshold_set = (59, 91)

        for threshold in threshold_set:
            with self.assertRaisesRegexp(AnsibleFailJson, r"Audit-log percent threshold must be between 60 and 90"):
                initial["threshold"] = threshold
                self._set_args(**initial)
                with mock.patch(self.REQ_FUNC, return_value=(200, {"runningAsProxy": False})):
                    AuditLog()

    def test_is_proxy_pass(self):
        """Verify that True is returned when proxy is used to communicate with storage."""
        initial = {"max_records": 1000,
                   "log_level": "writeOnly",
                   "full_policy": "overWrite",
                   "threshold": 90,
                   "api_url": "https://10.1.1.10/devmgr/v2"}

        self._set_args(**initial)
        with mock.patch(self.REQ_FUNC, return_value=(200, {"runningAsProxy": True})):
            audit_log = AuditLog()

        with mock.patch(self.REQ_FUNC, return_value=(200, {"runningAsProxy": True})):
            self.assertTrue(audit_log.is_proxy())

    def test_is_proxy_fail(self):
        """Verify that AnsibleJsonFail exception is thrown when exception occurs."""
        initial = {"max_records": 1000,
                   "log_level": "writeOnly",
                   "full_policy": "overWrite",
                   "threshold": 90}

        self._set_args(**initial)
        with mock.patch(self.REQ_FUNC, return_value=(200, {"runningAsProxy": True})):
            audit_log = AuditLog()

        with self.assertRaisesRegexp(AnsibleFailJson, r"Failed to retrieve the webservices about information"):
            with mock.patch(self.REQ_FUNC, return_value=Exception()):
                audit_log.is_proxy()

    def test_get_configuration_pass(self):
        """Validate get configuration does not throw exception when normal request is returned."""
        initial = {"max_records": 1000,
                   "log_level": "writeOnly",
                   "full_policy": "overWrite",
                   "threshold": 90}
        expected = {"auditLogMaxRecords": 1000,
                    "auditLogLevel": "writeOnly",
                    "auditLogFullPolicy": "overWrite",
                    "auditLogWarningThresholdPct": 90}

        self._set_args(**initial)
        with mock.patch(self.REQ_FUNC, return_value=(200, {"runningAsProxy": True})):
            audit_log = AuditLog()

        with mock.patch(self.REQ_FUNC, return_value=(200, expected)):
            body = audit_log.get_configuration()
            self.assertTrue(body == expected)

    def test_get_configuration_fail(self):
        """Verify AnsibleJsonFail exception is thrown."""
        initial = {"max_records": 1000,
                   "log_level": "writeOnly",
                   "full_policy": "overWrite",
                   "threshold": 90}

        self._set_args(**initial)
        with mock.patch(self.REQ_FUNC, return_value=(200, {"runningAsProxy": True})):
            audit_log = AuditLog()

        with self.assertRaisesRegexp(AnsibleFailJson, r"Failed to retrieve the audit-log configuration!"):
            with mock.patch(self.REQ_FUNC, return_value=Exception()):
                audit_log.get_configuration()

    def test_build_configuration_pass(self):
        """Validate configuration changes will force an update."""
        response = {"auditLogMaxRecords": 1000,
                    "auditLogLevel": "writeOnly",
                    "auditLogFullPolicy": "overWrite",
                    "auditLogWarningThresholdPct": 90}
        initial = {"max_records": 1000,
                   "log_level": "writeOnly",
                   "full_policy": "overWrite",
                   "threshold": 90}
        changes = [{"max_records": 50000},
                   {"log_level": "all"},
                   {"full_policy": "preventSystemAccess"},
                   {"threshold": 75}]

        for change in changes:
            initial_with_changes = initial.copy()
            initial_with_changes.update(change)
            self._set_args(**initial_with_changes)
            with mock.patch(self.REQ_FUNC, return_value=(200, {"runningAsProxy": True})):
                audit_log = AuditLog()

            with mock.patch(self.REQ_FUNC, return_value=(200, response)):
                update = audit_log.build_configuration()
                self.assertTrue(update)

    def test_delete_log_messages_fail(self):
        """Verify AnsibleJsonFail exception is thrown."""
        initial = {"max_records": 1000,
                   "log_level": "writeOnly",
                   "full_policy": "overWrite",
                   "threshold": 90}

        self._set_args(**initial)
        with mock.patch(self.REQ_FUNC, return_value=(200, {"runningAsProxy": True})):
            audit_log = AuditLog()

        with self.assertRaisesRegexp(AnsibleFailJson, r"Failed to delete audit-log messages!"):
            with mock.patch(self.REQ_FUNC, return_value=Exception()):
                audit_log.delete_log_messages()

    def test_update_configuration_delete_pass(self):
        """Verify 422 and force successfully returns True."""
        body = {"auditLogMaxRecords": 1000,
                "auditLogLevel": "writeOnly",
                "auditLogFullPolicy": "overWrite",
                "auditLogWarningThresholdPct": 90}
        initial = {"max_records": 2000,
                   "log_level": "writeOnly",
                   "full_policy": "overWrite",
                   "threshold": 90,
                   "force": True}

        self._set_args(**initial)
        with mock.patch(self.REQ_FUNC, return_value=(200, {"runningAsProxy": True})):
            audit_log = AuditLog()
            with mock.patch(self.REQ_FUNC, side_effect=[(200, body),
                                                        (422, {u"invalidFieldsIfKnown": None,
                                                               u"errorMessage": u"Configuration change...",
                                                               u"localizedMessage": u"Configuration change...",
                                                               u"retcode": u"auditLogImmediateFullCondition",
                                                               u"codeType": u"devicemgrerror"}),
                                                        (200, None),
                                                        (200, None)]):
                self.assertTrue(audit_log.update_configuration())

    def test_update_configuration_delete_skip_fail(self):
        """Verify 422 and no force results in AnsibleJsonFail exception."""
        body = {"auditLogMaxRecords": 1000,
                "auditLogLevel": "writeOnly",
                "auditLogFullPolicy": "overWrite",
                "auditLogWarningThresholdPct": 90}
        initial = {"max_records": 2000,
                   "log_level": "writeOnly",
                   "full_policy": "overWrite",
                   "threshold": 90,
                   "force": False}

        self._set_args(**initial)
        with mock.patch(self.REQ_FUNC, return_value=(200, {"runningAsProxy": True})):
            audit_log = AuditLog()

        with self.assertRaisesRegexp(AnsibleFailJson, r"Failed to update audit-log configuration!"):
            with mock.patch(self.REQ_FUNC, side_effect=[(200, body), Exception(422, {"errorMessage": "error"}),
                                                        (200, None), (200, None)]):
                audit_log.update_configuration()
