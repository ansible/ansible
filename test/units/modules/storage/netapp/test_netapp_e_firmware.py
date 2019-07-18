# (c) 2018, NetApp Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

__metaclass__ = type

try:
    from unittest import mock
except ImportError:
    import mock

from ansible.module_utils import six
from ansible.modules.storage.netapp.netapp_e_firmware import NetAppESeriesFirmware, create_multipart_formdata
from units.modules.utils import AnsibleExitJson, AnsibleFailJson, ModuleTestCase, set_module_args
import re


class FirmwareTest(ModuleTestCase):
    REQUIRED_PARAMS = {"api_username": "username",
                       "api_password": "password",
                       "api_url": "http://localhost/devmgr/v2",
                       "ssid": "1",
                       "validate_certs": "no"}
    REQUEST_FUNC = "ansible.modules.storage.netapp.netapp_e_firmware.NetAppESeriesFirmware.request"
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

    def _set_args(self, args=None):
        module_args = self.REQUIRED_PARAMS.copy()
        if args is not None:
            module_args.update(args)
        set_module_args(module_args)

    def test_create_multipart_formdata_pass(self):
        """Verify create_multipart_formdata properly creates request information."""
        expected_headers = {'Content-Type': 'multipart/form-data; boundary=---------------------------XXXXXXXXXXXXXXXXXXXXXXXXXXX', 'Content-Length': '708'}
        expected_data = b'-----------------------------XXXXXXXXXXXXXXXXXXXXXXXXXXX\r\nContent-Disposition: form-data; name="field_0_key"\r\n\r\nfield_0_value' \
                        b'\r\n-----------------------------XXXXXXXXXXXXXXXXXXXXXXXXXXX\r\nContent-Disposition: form-data; name="field_1_key"\r\n\r\nfield_1_v' \
                        b'alue\r\n-----------------------------XXXXXXXXXXXXXXXXXXXXXXXXXXX\r\nContent-Disposition: form-data; name="test_file_0"; filename="t' \
                        b'est_file_0.dlp"\r\nContent-Type: application/octet-stream\r\n\r\ntest_file_0.dlp\r\n-----------------------------XXXXXXXXXXXXXXXXXX' \
                        b'XXXXXXXXX\r\nContent-Disposition: form-data; name="test_file_1"; filename="test_file_1.dlp"\r\nContent-Type: application/octet-stre' \
                        b'am\r\n\r\ntest_file_1.dlp\r\n-----------------------------XXXXXXXXXXXXXXXXXXXXXXXXXXX--\r\n'

        # create test files and define create_multipart_formdata arguments
        for index in range(2):
            with open("test_file_%s.dlp" % index, "w") as fh:
                fh.write("test_file_%s.dlp" % index)
        fields = [("field_0_key", "field_0_value"),
                  ("field_1_key", "field_1_value")]
        files = [("test_file_0", "test_file_0.dlp", "test_file_0.dlp"),
                 ("test_file_1", "test_file_1.dlp", "test_file_1.dlp")]
        headers, data = create_multipart_formdata(files=files, fields=fields)

        # update expected values with randomized boundary value
        boundary = re.findall("[0-9]{27}", headers["Content-Type"])[0]
        expected_headers["Content-Type"] = expected_headers["Content-Type"].replace("XXXXXXXXXXXXXXXXXXXXXXXXXXX", boundary)
        expected_data = expected_data.replace(b"XXXXXXXXXXXXXXXXXXXXXXXXXXX", six.b(boundary))

        self.assertEqual(headers, expected_headers)
        self.assertEqual(data, expected_data)

    def test_is_firmware_bundled_pass(self):
        """Determine whether firmware file is bundled."""
        self._set_args({"firmware": "test.dlp", "nvsram": "test.dlp"})
        with open("test.dlp", "wb") as fh:
            fh.write(b"firmwarexxxxxxxxxxxxxxxxxx")
        firmware = NetAppESeriesFirmware()
        self.assertEqual(firmware.is_firmware_bundled(), False)

        self._set_args({"firmware": "test.dlp", "nvsram": "test.dlp"})
        with open("test.dlp", "wb") as fh:
            fh.write(self.BUNDLE_HEADER)
        firmware = NetAppESeriesFirmware()
        self.assertEqual(firmware.is_firmware_bundled(), True)

    def test_is_firmware_bundles_fail(self):
        """Verify non-firmware fails."""
        self._set_args({"firmware": "test.dlp", "nvsram": "test.dlp"})
        with open("test.dlp", "wb") as fh:
            fh.write(b"xxxxxxxxxxxxxxxxxxxxxxxxxx")
        firmware = NetAppESeriesFirmware()
        with self.assertRaisesRegexp(AnsibleFailJson, "Firmware file is invalid."):
            firmware.is_firmware_bundled()

    def test_check_system_health_pass(self):
        """Validate check_system_health method."""
        self._set_args({"firmware": "test.dlp", "nvsram": "test.dlp"})
        firmware = NetAppESeriesFirmware()
        with mock.patch(self.REQUEST_FUNC, side_effect=[(200, {"requestId": "1"}),
                                                        (200, {"healthCheckRunning": True,
                                                               "results": [{"processingTimeMS": 0}]}),
                                                        (200, {"healthCheckRunning": False,
                                                               "results": [{"successful": True}]})]):
            firmware.check_system_health()

    def test_check_system_health_fail(self):
        """Validate check_system_health method throws proper exceptions."""
        self._set_args({"firmware": "test.dlp", "nvsram": "test.dlp"})
        firmware = NetAppESeriesFirmware()
        with mock.patch("time.sleep", return_value=None):
            with self.assertRaisesRegexp(AnsibleFailJson, "Failed to initiate health check."):
                with mock.patch(self.REQUEST_FUNC, return_value=(404, Exception())):
                    firmware.check_system_health()

            with self.assertRaisesRegexp(AnsibleFailJson, "Failed to retrieve health check status."):
                with mock.patch(self.REQUEST_FUNC, side_effect=[(200, {"requestId": "1"}),
                                                                (404, Exception())]):
                    firmware.check_system_health()

            with self.assertRaisesRegexp(AnsibleFailJson, "Health check failed to complete."):
                with mock.patch(self.REQUEST_FUNC, side_effect=[(200, {"requestId": "1"}),
                                                                (200, {"healthCheckRunning": True,
                                                                       "results": [{"processingTimeMS": 120001}]})]):
                    firmware.check_system_health()
