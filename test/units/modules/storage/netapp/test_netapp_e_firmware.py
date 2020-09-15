# (c) 2018, NetApp Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import absolute_import, division, print_function
__metaclass__ = type

try:
    from unittest.mock import patch, mock_open
except ImportError:
    from mock import patch, mock_open

from ansible.module_utils import six
from ansible.modules.storage.netapp.netapp_e_firmware import NetAppESeriesFirmware
from units.modules.utils import AnsibleExitJson, AnsibleFailJson, ModuleTestCase, set_module_args

if six.PY2:
    builtin_path = "__builtin__.open"
else:
    builtin_path = "builtins.open"


def mock_open_with_iter(*args, **kwargs):
    mock = mock_open(*args, **kwargs)

    if six.PY2:
        mock.return_value.__iter__ = lambda x: iter(x.readline, "")
    else:
        mock.return_value.__iter__ = lambda x: x
        mock.return_value.__next__ = lambda x: iter(x.readline, "")
    return mock


class FirmwareTest(ModuleTestCase):
    REQUIRED_PARAMS = {"api_username": "username",
                       "api_password": "password",
                       "api_url": "http://localhost/devmgr/v2",
                       "ssid": "1",
                       "validate_certs": "no"}
    REQUEST_FUNC = "ansible.modules.storage.netapp.netapp_e_firmware.NetAppESeriesFirmware.request"
    BASE_REQUEST_FUNC = "ansible.modules.storage.netapp.netapp_e_firmware.request"
    CREATE_MULTIPART_FORMDATA_FUNC = "ansible.modules.storage.netapp.netapp_e_firmware.create_multipart_formdata"
    SLEEP_FUNC = "ansible.modules.storage.netapp.netapp_e_firmware.sleep"
    BUNDLE_HEADER = b'combined_content\x00\x00\x00\x04\x00\x00\x07\xf8#Engenio Downloadable Package\n#Tue Jun 04 11:46:48 CDT 2019\ncheckList=compatibleBoard' \
                    b'Map,compatibleSubmodelMap,compatibleFirmwareMap,fileManifest\ncompatibleSubmodelMap=261|true,262|true,263|true,264|true,276|true,277|t' \
                    b'rue,278|true,282|true,300|true,301|true,302|true,318|true,319|true,320|true,321|true,322|true,323|true,324|true,325|true,326|true,328|t' \
                    b'rue,329|true,330|true,331|true,332|true,333|true,338|true,339|true,340|true,341|true,342|true,343|true,344|true,345|true,346|true,347|t' \
                    b'rue,356|true,357|true,390|true\nnonDisplayableAttributeList=512\ndisplayableAttributeList=FILENAME|RCB_11.40.5_280x_5ceef00e.dlp,VERSI' \
                    b'ON|11.40.5\ndacStoreLimit=512\nfileManifest=metadata.tar|metadata|08.42.50.00.000|c04275f98fc2f07bd63126fc57cb0569|bundle|10240,084250' \
                    b'00_m3_e30_842_root.img|linux|08.42.50.00|367c5216e5c4b15b904a025bff69f039|linux|1342177280,RC_08425000_m3_e30_842_280x.img|linux_cfw|0' \
                    b'8.42.50.00|e6589b0a50b29ff34b34d3ced8ae3ccb|eos|1073741824,msw.img|sam|11.42.0000.0028|ef3ee5589ab4a019a3e6f83768364aa1|linux|41943040' \
                    b'0,iom.img|iom|11.42.0G00.0003|9bb740f8d3a4e62a0f2da2ec83c254c4|linux|8177664\nmanagementVersionList=devmgr.v1142api8.Manager\ncompatib' \
                    b'leFirmwareMap=08.30.*.*|true,08.30.*.30|false,08.30.*.31|false,08.30.*.32|false,08.30.*.33|false,08.30.*.34|false,08.30.*.35|false,08.' \
                    b'30.*.36|false,08.30.*.37|false,08.30.*.38|false,08.30.*.39|false,08.40.*.*|true,08.40.*.30|false,08.40.*.31|false,08.40.*.32|false,08.4' \
                    b'0.*.33|false,08.40.*.34|false,08.40.*.35|false,08.40.*.36|false,08.40.*.37|false,08.40.*.38|false,08.40.*.39|false,08.41.*.*|true,08.4' \
                    b'1.*.30|false,08.41.*.31|false,08.41.*.32|false,08.41.*.33|false,08.41.*.34|false,08.41.*.35|false,08.41.*.36|false,08.41.*.37|false,08' \
                    b'.41.*.38|false,08.41.*.39|false,08.42.*.*|true,08.42.*.30|false,08.42.*.31|false,08.42.*.32|false,08.42.*.33|false,08.42.*.34|false,08' \
                    b'.42.*.35|false,08.42.*.36|false,08.42.*.37|false,08.42.*.38|false,08.42.*.39|false\nversion=08.42.50.00.000\ntype=tar\nversionTag=comb' \
                    b'ined_content\n'

    NVSRAM_HEADER = b'nvsram          \x00\x00\x00\x01\x00\x00\x00\xa0\x00\x00\x00\x04280X\x00\x00\x00\x00\x00\x00\x00\x032801    2804    2806    \x00\x00' \
                    b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x02\x00\x00\x00\x1bArapaho controller, 8.52 FW\x00\x00\x001dual controller configuration, with cac' \
                    b'he battery\x07\x81A\x08Config\x00\x00\x0008.52.00.00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x02\x00\x00\x00\x00\x00\xdc\xaf\x00\x00' \
                    b'\x94\xc1\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\x00\x00\x00\x00 2801 2804 2806 \x00\x00\x00\x00\x00' \
                    b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00' \
                    b'\x00\x00\x00\x00\x00\x00Board\n    .Board Name                             = "NetApp RAID Controller"\n    .NVSRAM Configuration Number' \
                    b'            = "N280X-852834-D02"\n\nUserCfg\n    .Enable Synchronous Negotiation         = 0x00  \n'

    def _set_args(self, args=None):
        module_args = self.REQUIRED_PARAMS.copy()
        if args is not None:
            module_args.update(args)
        set_module_args(module_args)

    def test_is_firmware_bundled_pass(self):
        """Determine whether firmware file is bundled."""
        self._set_args({"firmware": "test.dlp", "nvsram": "test.dlp"})
        with patch(builtin_path, mock_open(read_data=b"firmwarexxxxxxxx")) as mock_file:
            firmware = NetAppESeriesFirmware()
            self.assertEqual(firmware.is_firmware_bundled(), False)

        self._set_args({"firmware": "test.dlp", "nvsram": "test.dlp"})
        with patch(builtin_path, mock_open(read_data=self.BUNDLE_HEADER[:16])) as mock_file:
            firmware = NetAppESeriesFirmware()
            self.assertEqual(firmware.is_firmware_bundled(), True)

    def test_is_firmware_bundles_fail(self):
        """Verify non-firmware fails."""
        self._set_args({"firmware": "test.dlp", "nvsram": "test.dlp"})
        with patch(builtin_path, mock_open(read_data=b"xxxxxxxxxxxxxxxx")) as mock_file:
            firmware = NetAppESeriesFirmware()
            with self.assertRaisesRegexp(AnsibleFailJson, "Firmware file is invalid."):
                firmware.is_firmware_bundled()

    def test_firmware_version(self):
        """Verify correct firmware version is returned."""
        self._set_args({"firmware": "test.dlp", "nvsram": "test.dlp"})
        firmware = NetAppESeriesFirmware()
        firmware.is_firmware_bundled = lambda: True
        with patch(builtin_path, mock_open_with_iter(read_data=self.BUNDLE_HEADER)) as mock_file:
            self.assertEqual(firmware.firmware_version(), b"11.40.5")

    def test_nvsram_version(self):
        """Verify correct nvsram version is returned."""
        self._set_args({"firmware": "test.dlp", "nvsram": "test.dlp"})
        firmware = NetAppESeriesFirmware()

        with patch(builtin_path, mock_open_with_iter(read_data=self.NVSRAM_HEADER)) as mock_file:
            self.assertEqual(firmware.nvsram_version(), b"N280X-852834-D02")

    def test_check_system_health_pass(self):
        """Validate check_system_health method."""
        self._set_args({"firmware": "test.dlp", "nvsram": "test.dlp"})
        firmware = NetAppESeriesFirmware()
        with patch(self.REQUEST_FUNC, side_effect=[(200, {"requestId": "1"}),
                                                   (200, {"healthCheckRunning": True,
                                                          "results": [{"processingTimeMS": 0}]}),
                                                   (200, {"healthCheckRunning": False,
                                                          "results": [{"successful": True}]})]):
            firmware.check_system_health()

    def test_check_system_health_fail(self):
        """Validate check_system_health method throws proper exceptions."""
        self._set_args({"firmware": "test.dlp", "nvsram": "test.dlp"})
        firmware = NetAppESeriesFirmware()
        with patch("time.sleep", return_value=None):
            with self.assertRaisesRegexp(AnsibleFailJson, "Failed to initiate health check."):
                with patch(self.REQUEST_FUNC, return_value=(404, Exception())):
                    firmware.check_system_health()

            with self.assertRaisesRegexp(AnsibleFailJson, "Failed to retrieve health check status."):
                with patch(self.REQUEST_FUNC, side_effect=[(200, {"requestId": "1"}),
                                                           (404, Exception())]):
                    firmware.check_system_health()

            with self.assertRaisesRegexp(AnsibleFailJson, "Health check failed to complete."):
                with patch(self.REQUEST_FUNC, side_effect=[(200, {"requestId": "1"}),
                                                           (200, {"healthCheckRunning": True,
                                                                  "results": [{"processingTimeMS": 120001}]})]):
                    firmware.check_system_health()

    def test_embedded_check_nvsram_compatibility_pass(self):
        """Verify embedded nvsram compatibility."""
        self._set_args({"firmware": "test.dlp", "nvsram": "test.dlp"})
        firmware = NetAppESeriesFirmware()
        with patch(self.CREATE_MULTIPART_FORMDATA_FUNC, return_value=("", {})):
            with patch(self.REQUEST_FUNC, return_value=(200, {"signatureTestingPassed": True,
                                                              "fileCompatible": True,
                                                              "versionContents": [{"module": "nvsram",
                                                                                   "bundledVersion": "N280X-842834-D02",
                                                                                   "onboardVersion": "N280X-842834-D02"}]})):
                firmware.embedded_check_nvsram_compatibility()

    def test_embedded_check_nvsram_compatibility_fail(self):
        """Verify embedded nvsram compatibility fails with expected exceptions."""
        self._set_args({"firmware": "test.dlp", "nvsram": "test.dlp"})
        firmware = NetAppESeriesFirmware()

        with patch(self.CREATE_MULTIPART_FORMDATA_FUNC, return_value=("", {})):
            with self.assertRaisesRegexp(AnsibleFailJson, "Failed to retrieve NVSRAM compatibility results."):
                with patch(self.REQUEST_FUNC, return_value=Exception()):
                    firmware.embedded_check_nvsram_compatibility()

            with self.assertRaisesRegexp(AnsibleFailJson, "Invalid NVSRAM file."):
                with patch(self.REQUEST_FUNC, return_value=(200, {"signatureTestingPassed": False,
                                                                  "fileCompatible": False,
                                                                  "versionContents": [{"module": "nvsram",
                                                                                       "bundledVersion": "N280X-842834-D02",
                                                                                       "onboardVersion": "N280X-842834-D02"}]})):
                    firmware.embedded_check_nvsram_compatibility()

            with self.assertRaisesRegexp(AnsibleFailJson, "Incompatible NVSRAM file."):
                with patch(self.REQUEST_FUNC, return_value=(200, {"signatureTestingPassed": True,
                                                                  "fileCompatible": False,
                                                                  "versionContents": [{"module": "nvsram",
                                                                                       "bundledVersion": "N280X-842834-D02",
                                                                                       "onboardVersion": "N280X-842834-D02"}]})):
                    firmware.embedded_check_nvsram_compatibility()

    def test_embedded_check_firmware_compatibility_pass(self):
        """Verify embedded firmware compatibility."""
        self._set_args({"firmware": "test.dlp", "nvsram": "test.dlp"})
        firmware = NetAppESeriesFirmware()

        with patch(self.CREATE_MULTIPART_FORMDATA_FUNC, return_value=("", {})):
            with patch(self.REQUEST_FUNC, return_value=(200, {
                "signatureTestingPassed": True,
                "fileCompatible": True,
                "versionContents": [
                    {"module": "bundle", "bundledVersion": "08.42.50.00.000", "onboardVersion": "08.42.30.05"},
                    {"module": "bundleDisplay", "bundledVersion": "11.40.5", "onboardVersion": "11.40.3R2"},
                    {"module": "hypervisor", "bundledVersion": "08.42.50.00", "onboardVersion": "08.42.30.05"},
                    {"module": "raid", "bundledVersion": "08.42.50.00", "onboardVersion": "08.42.30.05"},
                    {"module": "management", "bundledVersion": "11.42.0000.0028", "onboardVersion": "11.42.0000.0026"},
                    {"module": "iom", "bundledVersion": "11.42.0G00.0003", "onboardVersion": "11.42.0G00.0001"}]})):
                firmware.embedded_check_bundle_compatibility()

    def test_embedded_check_firmware_compatibility_fail(self):
        """Verify embedded firmware compatibility fails with expected exceptions."""
        self._set_args({"firmware": "test.dlp", "nvsram": "test.dlp"})
        firmware = NetAppESeriesFirmware()

        with self.assertRaisesRegexp(AnsibleFailJson, "Failed to retrieve bundle compatibility results."):
            with patch(self.CREATE_MULTIPART_FORMDATA_FUNC, return_value=("", {})):
                with patch(self.REQUEST_FUNC, return_value=Exception()):
                    firmware.embedded_check_bundle_compatibility()

        with self.assertRaisesRegexp(AnsibleFailJson, "Invalid firmware bundle file."):
            with patch(self.CREATE_MULTIPART_FORMDATA_FUNC, return_value=("", {})):
                with patch(self.REQUEST_FUNC, return_value=(200, {
                    "signatureTestingPassed": False,
                    "fileCompatible": True,
                    "versionContents": [
                        {"module": "bundle", "bundledVersion": "08.42.50.00.000", "onboardVersion": "08.42.30.05"},
                        {"module": "bundleDisplay", "bundledVersion": "11.40.5", "onboardVersion": "11.40.3R2"},
                        {"module": "hypervisor", "bundledVersion": "08.42.50.00", "onboardVersion": "08.42.30.05"},
                        {"module": "raid", "bundledVersion": "08.42.50.00", "onboardVersion": "08.42.30.05"},
                        {"module": "management", "bundledVersion": "11.42.0000.0028", "onboardVersion": "11.42.0000.0026"},
                        {"module": "iom", "bundledVersion": "11.42.0G00.0003", "onboardVersion": "11.42.0G00.0001"}]})):
                    firmware.embedded_check_bundle_compatibility()

        with self.assertRaisesRegexp(AnsibleFailJson, "Incompatible firmware bundle file."):
            with patch(self.CREATE_MULTIPART_FORMDATA_FUNC, return_value=("", {})):
                with patch(self.REQUEST_FUNC, return_value=(200, {
                    "signatureTestingPassed": True,
                    "fileCompatible": False,
                    "versionContents": [
                        {"module": "bundle", "bundledVersion": "08.42.50.00.000", "onboardVersion": "08.42.30.05"},
                        {"module": "bundleDisplay", "bundledVersion": "11.40.5", "onboardVersion": "11.40.3R2"},
                        {"module": "hypervisor", "bundledVersion": "08.42.50.00", "onboardVersion": "08.42.30.05"},
                        {"module": "raid", "bundledVersion": "08.42.50.00", "onboardVersion": "08.42.30.05"},
                        {"module": "management", "bundledVersion": "11.42.0000.0028", "onboardVersion": "11.42.0000.0026"},
                        {"module": "iom", "bundledVersion": "11.42.0G00.0003", "onboardVersion": "11.42.0G00.0001"}]})):
                    firmware.embedded_check_bundle_compatibility()

        with self.assertRaisesRegexp(AnsibleFailJson, "Downgrades are not permitted."):
            with patch(self.CREATE_MULTIPART_FORMDATA_FUNC, return_value=("", {})):
                with patch(self.REQUEST_FUNC, return_value=(200, {
                    "signatureTestingPassed": True,
                    "fileCompatible": True,
                    "versionContents": [
                        {"module": "bundle", "bundledVersion": "08.42.00.00.000", "onboardVersion": "08.50.30.05"},
                        {"module": "bundleDisplay", "bundledVersion": "11.40.5", "onboardVersion": "11.40.3R2"},
                        {"module": "hypervisor", "bundledVersion": "08.42.50.00", "onboardVersion": "08.42.30.05"},
                        {"module": "raid", "bundledVersion": "08.42.50.00", "onboardVersion": "08.42.30.05"},
                        {"module": "management", "bundledVersion": "11.42.0000.0028", "onboardVersion": "11.42.0000.0026"},
                        {"module": "iom", "bundledVersion": "11.42.0G00.0003", "onboardVersion": "11.42.0G00.0001"}]})):
                    firmware.embedded_check_bundle_compatibility()
        with self.assertRaisesRegexp(AnsibleFailJson, "Downgrades are not permitted."):
            with patch(self.CREATE_MULTIPART_FORMDATA_FUNC, return_value=("", {})):
                with patch(self.REQUEST_FUNC, return_value=(200, {
                    "signatureTestingPassed": True,
                    "fileCompatible": True,
                    "versionContents": [
                        {"module": "bundle", "bundledVersion": "08.42.00.00.000", "onboardVersion": "09.20.30.05"},
                        {"module": "bundleDisplay", "bundledVersion": "11.40.5", "onboardVersion": "11.40.3R2"},
                        {"module": "hypervisor", "bundledVersion": "08.42.50.00", "onboardVersion": "08.42.30.05"},
                        {"module": "raid", "bundledVersion": "08.42.50.00", "onboardVersion": "08.42.30.05"},
                        {"module": "management", "bundledVersion": "11.42.0000.0028", "onboardVersion": "11.42.0000.0026"},
                        {"module": "iom", "bundledVersion": "11.42.0G00.0003", "onboardVersion": "11.42.0G00.0001"}]})):
                    firmware.embedded_check_bundle_compatibility()

    def test_embedded_wait_for_upgrade_pass(self):
        """Verify controller reboot wait succeeds."""
        self._set_args({"firmware": "test.dlp", "nvsram": "test.dlp"})
        firmware = NetAppESeriesFirmware()
        firmware.firmware_version = lambda: b"11.40.3R2"
        firmware.nvsram_version = lambda: b"N280X-842834-D02"
        with patch(self.SLEEP_FUNC, return_value=None):
            with patch(self.REQUEST_FUNC, return_value=(200, [{"fwVersion": "08.42.30.05", "nvsramVersion": "N280X-842834-D02",
                                                               "extendedSAData": {"codeVersions": [{"codeModule": "bundleDisplay",
                                                                                                    "versionString": "11.40.3R2"}]}}])):
                firmware.embedded_wait_for_upgrade()

    def test_embedded_wait_for_upgrade_fail(self):
        """Verify controller reboot wait throws expected exceptions"""
        self._set_args({"firmware": "test.dlp", "nvsram": "test.dlp"})
        firmware = NetAppESeriesFirmware()
        with self.assertRaisesRegexp(AnsibleFailJson, "Timeout waiting for Santricity Web Services Embedded."):
            with patch(self.SLEEP_FUNC, return_value=None):
                with patch(self.BASE_REQUEST_FUNC, return_value=Exception()):
                    firmware.embedded_wait_for_upgrade()

    def test_embedded_upgrade_pass(self):
        """Verify embedded upgrade function."""
        with patch(self.CREATE_MULTIPART_FORMDATA_FUNC, return_value=("", {})):
            with patch(self.SLEEP_FUNC, return_value=None):

                self._set_args({"firmware": "test.dlp", "nvsram": "test.dlp"})
                firmware = NetAppESeriesFirmware()
                with patch(self.REQUEST_FUNC, return_value=(200, "")):
                    with patch(self.BASE_REQUEST_FUNC, side_effect=[Exception(), Exception(), (200, "")]):
                        firmware.embedded_upgrade()
                        self.assertTrue(firmware.upgrade_in_progress)

                self._set_args({"firmware": "test.dlp", "nvsram": "test.dlp", "wait_for_completion": True})
                firmware = NetAppESeriesFirmware()
                firmware.firmware_version = lambda: b"11.40.3R2"
                firmware.nvsram_version = lambda: b"N280X-842834-D02"
                with patch(self.REQUEST_FUNC, return_value=(200, [{"fwVersion": "08.42.30.05", "nvsramVersion": "N280X-842834-D02",
                                                                   "extendedSAData": {"codeVersions": [{"codeModule": "bundleDisplay",
                                                                                                        "versionString": "11.40.3R2"}]}}])):
                    firmware.embedded_upgrade()
                    self.assertFalse(firmware.upgrade_in_progress)

    def test_embedded_upgrade_fail(self):
        """Verify embedded upgrade throws expected exception."""
        self._set_args({"firmware": "test.dlp", "nvsram": "test.dlp"})
        firmware = NetAppESeriesFirmware()
        with self.assertRaisesRegexp(AnsibleFailJson, "Failed to upload and activate firmware."):
            with patch(self.CREATE_MULTIPART_FORMDATA_FUNC, return_value=("", {})):
                with patch(self.REQUEST_FUNC, return_value=Exception()):
                    firmware.embedded_upgrade()

    def test_check_nvsram_compatibility_pass(self):
        """Verify proxy nvsram compatibility."""
        self._set_args({"firmware": "test.dlp", "nvsram": "test_nvsram.dlp"})
        firmware = NetAppESeriesFirmware()
        with patch(self.SLEEP_FUNC, return_value=None):
            with patch(self.REQUEST_FUNC, side_effect=[(200, {"requestId": 1}),
                                                       (200, {"checkRunning": True}),
                                                       (200, {"checkRunning": False,
                                                              "results": [{"nvsramFiles": [{"filename": "test_nvsram.dlp"}]}]})]):
                firmware.proxy_check_nvsram_compatibility()

    def test_check_nvsram_compatibility_fail(self):
        """Verify proxy nvsram compatibility throws expected exceptions."""
        self._set_args({"firmware": "test.dlp", "nvsram": "test_nvsram.dlp"})
        firmware = NetAppESeriesFirmware()
        with patch(self.SLEEP_FUNC, return_value=None):
            with self.assertRaisesRegexp(AnsibleFailJson, "Failed to receive NVSRAM compatibility information."):
                with patch(self.REQUEST_FUNC, return_value=Exception()):
                    firmware.proxy_check_nvsram_compatibility()

            with self.assertRaisesRegexp(AnsibleFailJson, "Failed to retrieve NVSRAM status update from proxy."):
                with patch(self.REQUEST_FUNC, side_effect=[(200, {"requestId": 1}), Exception()]):
                    firmware.proxy_check_nvsram_compatibility()

            with self.assertRaisesRegexp(AnsibleFailJson, "NVSRAM is not compatible."):
                with patch(self.REQUEST_FUNC, side_effect=[(200, {"requestId": 1}),
                                                           (200, {"checkRunning": True}),
                                                           (200, {"checkRunning": False,
                                                                  "results": [{"nvsramFiles": [{"filename": "not_test_nvsram.dlp"}]}]})]):
                    firmware.proxy_check_nvsram_compatibility()

    def test_check_firmware_compatibility_pass(self):
        """Verify proxy firmware compatibility."""
        self._set_args({"firmware": "test_firmware.dlp", "nvsram": "test_nvsram.dlp"})
        firmware = NetAppESeriesFirmware()
        with patch(self.SLEEP_FUNC, return_value=None):
            with patch(self.REQUEST_FUNC, side_effect=[(200, {"requestId": 1}),
                                                       (200, {"checkRunning": True}),
                                                       (200, {"checkRunning": False,
                                                              "results": [{"cfwFiles": [{"filename": "test_firmware.dlp"}]}]})]):
                firmware.proxy_check_firmware_compatibility()

    def test_check_firmware_compatibility_fail(self):
        """Verify proxy firmware compatibility throws expected exceptions."""
        self._set_args({"firmware": "test_firmware.dlp", "nvsram": "test_nvsram.dlp"})
        firmware = NetAppESeriesFirmware()

        with patch(self.SLEEP_FUNC, return_value=None):
            with self.assertRaisesRegexp(AnsibleFailJson, "Failed to receive firmware compatibility information."):
                with patch(self.REQUEST_FUNC, return_value=Exception()):
                    firmware.proxy_check_firmware_compatibility()

            with self.assertRaisesRegexp(AnsibleFailJson, "Failed to retrieve firmware status update from proxy."):
                with patch(self.REQUEST_FUNC, side_effect=[(200, {"requestId": 1}), Exception()]):
                    firmware.proxy_check_firmware_compatibility()

            with self.assertRaisesRegexp(AnsibleFailJson, "Firmware bundle is not compatible."):
                with patch(self.REQUEST_FUNC, side_effect=[(200, {"requestId": 1}),
                                                           (200, {"checkRunning": True}),
                                                           (200, {"checkRunning": False,
                                                                  "results": [{"cfwFiles": [{"filename": "not_test_firmware.dlp"}]}]})]):
                    firmware.proxy_check_firmware_compatibility()

    def test_proxy_upload_and_check_compatibility_pass(self):
        """Verify proxy_upload_and_check_compatibility"""
        self._set_args({"firmware": "test_firmware.dlp", "nvsram": "test_nvsram.dlp"})
        firmware = NetAppESeriesFirmware()
        firmware.proxy_check_nvsram_compatibility = lambda: None
        firmware.proxy_check_firmware_compatibility = lambda: None
        with patch(self.CREATE_MULTIPART_FORMDATA_FUNC, return_value=("headers", "data")):
            with patch(self.REQUEST_FUNC, side_effect=[(200, [{"version": "XX.XX.XX.XX", "filename": "test"},
                                                              {"version": "XXXXXXXXXX", "filename": "test.dlp"}]),
                                                       (200, None), (200, None)]):
                firmware.proxy_upload_and_check_compatibility()

            with patch(self.REQUEST_FUNC, return_value=(200, [{"version": "XX.XX.XX.XX", "filename": "test"},
                                                              {"version": "test_nvsram", "filename": "test_nvsram.dlp"},
                                                              {"version": "test", "filename": "test.dlp"},
                                                              {"filename": "test_firmware.dlp", "version": "test_firmware"}])):
                firmware.proxy_upload_and_check_compatibility()

    def test_proxy_upload_and_check_compatibility_fail(self):
        """Verify proxy_upload_and_check_compatibility throws expected exceptions."""
        self._set_args({"firmware": "test_firmware.dlp", "nvsram": "test_nvsram.dlp"})
        firmware = NetAppESeriesFirmware()
        firmware.proxy_check_nvsram_compatibility = lambda: None
        with self.assertRaisesRegexp(AnsibleFailJson, "Failed to retrieve existing existing firmware files."):
            with patch(self.CREATE_MULTIPART_FORMDATA_FUNC, return_value=("headers", "data")):
                with patch(self.REQUEST_FUNC, return_value=Exception()):
                    firmware.proxy_upload_and_check_compatibility()

        with self.assertRaisesRegexp(AnsibleFailJson, "Failed to upload NVSRAM file."):
            with patch(self.CREATE_MULTIPART_FORMDATA_FUNC, return_value=("headers", "data")):
                with patch(self.REQUEST_FUNC, side_effect=[(200, [{"version": "XX.XX.XX.XX", "filename": "test"},
                                                                  {"version": "XXXXXXXXXX", "filename": "test.dlp"}]),
                                                           Exception()]):
                    firmware.proxy_upload_and_check_compatibility()

        with self.assertRaisesRegexp(AnsibleFailJson, "Failed to upload firmware bundle file."):
            with patch(self.CREATE_MULTIPART_FORMDATA_FUNC, return_value=("headers", "data")):
                with patch(self.REQUEST_FUNC, side_effect=[(200, [{"version": "XX.XX.XX.XX", "filename": "test"},
                                                                  {"version": "XXXXXXXXXX", "filename": "test.dlp"}]),
                                                           (200, None), Exception()]):
                    firmware.proxy_upload_and_check_compatibility()

    def test_proxy_check_upgrade_required_pass(self):
        """Verify proxy_check_upgrade_required."""
        self._set_args({"firmware": "test_firmware.dlp", "nvsram": "test_nvsram.dlp"})
        firmware = NetAppESeriesFirmware()

        firmware.firmware_version = lambda: b"08.42.50.00"
        firmware.nvsram_version = lambda: b"nvsram_version"
        with patch(self.REQUEST_FUNC, side_effect=[(200, [{"versionString": "08.42.50.00"}]), (200, ["nvsram_version"])]):
            firmware.is_firmware_bundled = lambda: True
            firmware.proxy_check_upgrade_required()
            self.assertFalse(firmware.upgrade_required)

        with patch(self.REQUEST_FUNC, side_effect=[(200, ["08.42.50.00"]), (200, ["nvsram_version"])]):
            firmware.is_firmware_bundled = lambda: False
            firmware.proxy_check_upgrade_required()
            self.assertFalse(firmware.upgrade_required)

        firmware.firmware_version = lambda: b"08.42.50.00"
        firmware.nvsram_version = lambda: b"not_nvsram_version"
        with patch(self.REQUEST_FUNC, side_effect=[(200, [{"versionString": "08.42.50.00"}]), (200, ["nvsram_version"])]):
            firmware.is_firmware_bundled = lambda: True
            firmware.proxy_check_upgrade_required()
            self.assertTrue(firmware.upgrade_required)

        with patch(self.REQUEST_FUNC, side_effect=[(200, ["08.42.50.00"]), (200, ["nvsram_version"])]):
            firmware.is_firmware_bundled = lambda: False
            firmware.proxy_check_upgrade_required()
            self.assertTrue(firmware.upgrade_required)

        firmware.firmware_version = lambda: b"08.52.00.00"
        firmware.nvsram_version = lambda: b"nvsram_version"
        with patch(self.REQUEST_FUNC, side_effect=[(200, [{"versionString": "08.42.50.00"}]), (200, ["nvsram_version"])]):
            firmware.is_firmware_bundled = lambda: True
            firmware.proxy_check_upgrade_required()
            self.assertTrue(firmware.upgrade_required)

        with patch(self.REQUEST_FUNC, side_effect=[(200, ["08.42.50.00"]), (200, ["nvsram_version"])]):
            firmware.is_firmware_bundled = lambda: False
            firmware.proxy_check_upgrade_required()
            self.assertTrue(firmware.upgrade_required)

        firmware.firmware_version = lambda: b"08.52.00.00"
        firmware.nvsram_version = lambda: b"not_nvsram_version"
        with patch(self.REQUEST_FUNC, side_effect=[(200, [{"versionString": "08.42.50.00"}]), (200, ["nvsram_version"])]):
            firmware.is_firmware_bundled = lambda: True
            firmware.proxy_check_upgrade_required()
            self.assertTrue(firmware.upgrade_required)

        with patch(self.REQUEST_FUNC, side_effect=[(200, ["08.42.50.00"]), (200, ["nvsram_version"])]):
            firmware.is_firmware_bundled = lambda: False
            firmware.proxy_check_upgrade_required()
            self.assertTrue(firmware.upgrade_required)

    def test_proxy_check_upgrade_required_fail(self):
        """Verify proxy_check_upgrade_required throws expected exceptions."""
        self._set_args({"firmware": "test_firmware.dlp", "nvsram": "test_nvsram.dlp"})
        firmware = NetAppESeriesFirmware()

        firmware.firmware_version = lambda: b"08.42.50.00"
        firmware.nvsram_version = lambda: b"not_nvsram_version"
        with self.assertRaisesRegexp(AnsibleFailJson, "Failed to retrieve controller firmware information."):
            with patch(self.REQUEST_FUNC, return_value=Exception()):
                firmware.proxy_check_upgrade_required()

        with self.assertRaisesRegexp(AnsibleFailJson, "Failed to retrieve storage system's NVSRAM version."):
            with patch(self.REQUEST_FUNC, side_effect=[(200, [{"versionString": "08.42.50.00"}]), Exception()]):
                firmware.is_firmware_bundled = lambda: True
                firmware.proxy_check_upgrade_required()

        with self.assertRaisesRegexp(AnsibleFailJson, "Failed to retrieve storage system's NVSRAM version."):
            with patch(self.REQUEST_FUNC, side_effect=[(200, ["08.42.50.00"]), Exception()]):
                firmware.is_firmware_bundled = lambda: False
                firmware.proxy_check_upgrade_required()

        with self.assertRaisesRegexp(AnsibleFailJson, "Downgrades are not permitted."):
            with patch(self.REQUEST_FUNC, side_effect=[(200, [{"versionString": "08.42.50.00"}]), (200, ["nvsram_version"])]):
                firmware.firmware_version = lambda: b"08.40.00.00"
                firmware.nvsram_version = lambda: "nvsram_version"
                firmware.is_firmware_bundled = lambda: True
                firmware.proxy_check_upgrade_required()

        with self.assertRaisesRegexp(AnsibleFailJson, "Downgrades are not permitted."):
            with patch(self.REQUEST_FUNC, side_effect=[(200, ["08.42.50.00"]), (200, ["nvsram_version"])]):
                firmware.is_firmware_bundled = lambda: False
                firmware.proxy_check_upgrade_required()

    def test_proxy_wait_for_upgrade_pass(self):
        """Verify proxy_wait_for_upgrade."""
        with patch(self.SLEEP_FUNC, return_value=None):
            self._set_args({"firmware": "test_firmware.dlp", "nvsram": "expected_nvsram.dlp"})
            firmware = NetAppESeriesFirmware()

            firmware.is_firmware_bundled = lambda: True
            with patch(self.REQUEST_FUNC, side_effect=[(200, {"status": "not_done"}), (200, {"status": "complete"})]):
                firmware.proxy_wait_for_upgrade("1")

            firmware.is_firmware_bundled = lambda: False
            firmware.firmware_version = lambda: b"08.50.00.00"
            firmware.nvsram_version = lambda: b"expected_nvsram"
            with patch(self.REQUEST_FUNC, side_effect=[(200, ["08.40.00.00"]), (200, ["not_expected_nvsram"]),
                                                       (200, ["08.50.00.00"]), (200, ["expected_nvsram"])]):
                firmware.proxy_wait_for_upgrade("1")

    def test_proxy_wait_for_upgrade_fail(self):
        """Verify proxy_wait_for_upgrade throws expected exceptions."""
        with patch(self.SLEEP_FUNC, return_value=None):
            self._set_args({"firmware": "test_firmware.dlp", "nvsram": "test_nvsram.dlp"})
            firmware = NetAppESeriesFirmware()

            firmware.is_firmware_bundled = lambda: True
            with self.assertRaisesRegexp(AnsibleFailJson, "Failed to retrieve firmware upgrade status."):
                with patch(self.REQUEST_FUNC, return_value=Exception()):
                    firmware.proxy_wait_for_upgrade("1")

            firmware.is_firmware_bundled = lambda: False
            with self.assertRaisesRegexp(AnsibleFailJson, "Timed out waiting for firmware upgrade to complete."):
                with patch(self.REQUEST_FUNC, return_value=Exception()):
                    firmware.proxy_wait_for_upgrade("1")

            firmware.is_firmware_bundled = lambda: True
            with self.assertRaisesRegexp(AnsibleFailJson, "Firmware upgrade failed to complete."):
                with patch(self.REQUEST_FUNC, side_effect=[(200, {"status": "not_done"}), (200, {"status": "failed"})]):
                    firmware.proxy_wait_for_upgrade("1")

    def test_proxy_upgrade_fail(self):
        """Verify proxy_upgrade throws expected exceptions."""
        self._set_args({"firmware": "test_firmware.dlp", "nvsram": "test_nvsram.dlp"})
        firmware = NetAppESeriesFirmware()

        firmware.is_firmware_bundled = lambda: True
        with self.assertRaisesRegexp(AnsibleFailJson, "Failed to initiate firmware upgrade."):
            with patch(self.REQUEST_FUNC, return_value=Exception()):
                firmware.proxy_upgrade()

        firmware.is_firmware_bundled = lambda: False
        with self.assertRaisesRegexp(AnsibleFailJson, "Failed to initiate firmware upgrade."):
            with patch(self.REQUEST_FUNC, return_value=Exception()):
                firmware.proxy_upgrade()
