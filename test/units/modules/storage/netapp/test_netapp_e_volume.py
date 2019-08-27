# coding=utf-8
# (c) 2018, NetApp Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import absolute_import, division, print_function
__metaclass__ = type

try:
    from unittest import mock
except ImportError:
    import mock

from ansible.module_utils.netapp import NetAppESeriesModule
from ansible.modules.storage.netapp.netapp_e_volume import NetAppESeriesVolume
from units.modules.utils import AnsibleFailJson, ModuleTestCase, set_module_args


class NetAppESeriesVolumeTest(ModuleTestCase):
    REQUIRED_PARAMS = {"api_username": "username",
                       "api_password": "password",
                       "api_url": "http://localhost/devmgr/v2",
                       "ssid": "1",
                       "validate_certs": "no"}

    THIN_VOLUME_RESPONSE = [{"capacity": "1288490188800",
                             "volumeRef": "3A000000600A098000A4B28D000010475C405428",
                             "status": "optimal",
                             "protectionType": "type1Protection",
                             "maxVirtualCapacity": "281474976710656",
                             "initialProvisionedCapacity": "4294967296",
                             "currentProvisionedCapacity": "4294967296",
                             "provisionedCapacityQuota": "1305670057984",
                             "growthAlertThreshold": 85,
                             "expansionPolicy": "automatic",
                             "flashCached": False,
                             "metadata": [{"key": "workloadId", "value": "4200000001000000000000000000000000000000"},
                                          {"key": "volumeTypeId", "value": "volume"}],
                             "dataAssurance": True,
                             "segmentSize": 131072,
                             "diskPool": True,
                             "listOfMappings": [],
                             "mapped": False,
                             "currentControllerId": "070000000000000000000001",
                             "cacheSettings": {"readCacheEnable": True, "writeCacheEnable": True,
                                               "readAheadMultiplier": 0},
                             "name": "thin_volume",
                             "id": "3A000000600A098000A4B28D000010475C405428"}]
    VOLUME_GET_RESPONSE = [{"offline": False,
                            "raidLevel": "raid6",
                            "capacity": "214748364800",
                            "reconPriority": 1,
                            "segmentSize": 131072,
                            "volumeRef": "02000000600A098000A4B9D100000F095C2F7F31",
                            "status": "optimal",
                            "protectionInformationCapable": False,
                            "protectionType": "type0Protection",
                            "diskPool": True,
                            "flashCached": False,
                            "metadata": [{"key": "workloadId", "value": "4200000002000000000000000000000000000000"},
                                         {"key": "volumeTypeId", "value": "Clare"}],
                            "dataAssurance": False,
                            "currentControllerId": "070000000000000000000002",
                            "cacheSettings": {"readCacheEnable": True, "writeCacheEnable": False,
                                              "readAheadMultiplier": 0},
                            "thinProvisioned": False,
                            "totalSizeInBytes": "214748364800",
                            "name": "Matthew",
                            "id": "02000000600A098000A4B9D100000F095C2F7F31"},
                           {"offline": False,
                            "raidLevel": "raid6",
                            "capacity": "107374182400",
                            "reconPriority": 1,
                            "segmentSize": 131072,
                            "volumeRef": "02000000600A098000A4B28D00000FBE5C2F7F26",
                            "status": "optimal",
                            "protectionInformationCapable": False,
                            "protectionType": "type0Protection",
                            "diskPool": True,
                            "flashCached": False,
                            "metadata": [{"key": "workloadId", "value": "4200000002000000000000000000000000000000"},
                                         {"key": "volumeTypeId", "value": "Samantha"}],
                            "dataAssurance": False,
                            "currentControllerId": "070000000000000000000001",
                            "cacheSettings": {"readCacheEnable": True, "writeCacheEnable": False,
                                              "readAheadMultiplier": 0},
                            "thinProvisioned": False,
                            "totalSizeInBytes": "107374182400",
                            "name": "Samantha",
                            "id": "02000000600A098000A4B28D00000FBE5C2F7F26"},
                           {"offline": False,
                            "raidLevel": "raid6",
                            "capacity": "107374182400",
                            "segmentSize": 131072,
                            "volumeRef": "02000000600A098000A4B9D100000F0B5C2F7F40",
                            "status": "optimal",
                            "protectionInformationCapable": False,
                            "protectionType": "type0Protection",
                            "volumeGroupRef": "04000000600A098000A4B9D100000F085C2F7F26",
                            "diskPool": True,
                            "flashCached": False,
                            "metadata": [{"key": "workloadId", "value": "4200000002000000000000000000000000000000"},
                                         {"key": "volumeTypeId", "value": "Micah"}],
                            "dataAssurance": False,
                            "currentControllerId": "070000000000000000000002",
                            "cacheSettings": {"readCacheEnable": True, "writeCacheEnable": False,
                                              "readAheadMultiplier": 0},
                            "thinProvisioned": False,
                            "totalSizeInBytes": "107374182400",
                            "name": "Micah",
                            "id": "02000000600A098000A4B9D100000F0B5C2F7F40"}]
    STORAGE_POOL_GET_RESPONSE = [{"offline": False,
                                  "raidLevel": "raidDiskPool",
                                  "volumeGroupRef": "04000000600A",
                                  "securityType": "capable",
                                  "protectionInformationCapable": False,
                                  "protectionInformationCapabilities": {"protectionInformationCapable": True,
                                                                        "protectionType": "type2Protection"},
                                  "volumeGroupData": {"type": "diskPool",
                                                      "diskPoolData": {"reconstructionReservedDriveCount": 1,
                                                                       "reconstructionReservedAmt": "296889614336",
                                                                       "reconstructionReservedDriveCountCurrent": 1,
                                                                       "poolUtilizationWarningThreshold": 0,
                                                                       "poolUtilizationCriticalThreshold": 85,
                                                                       "poolUtilizationState": "utilizationOptimal",
                                                                       "unusableCapacity": "0",
                                                                       "degradedReconstructPriority": "high",
                                                                       "criticalReconstructPriority": "highest",
                                                                       "backgroundOperationPriority": "low",
                                                                       "allocGranularity": "4294967296"}},
                                  "reservedSpaceAllocated": False,
                                  "securityLevel": "fde",
                                  "usedSpace": "863288426496",
                                  "totalRaidedSpace": "2276332666880",
                                  "raidStatus": "optimal",
                                  "freeSpace": "1413044240384",
                                  "drivePhysicalType": "sas",
                                  "driveMediaType": "hdd",
                                  "diskPool": True,
                                  "id": "04000000600A098000A4B9D100000F085C2F7F26",
                                  "name": "employee_data_storage_pool"},
                                 {"offline": False,
                                  "raidLevel": "raid1",
                                  "volumeGroupRef": "04000000600A098000A4B28D00000FBD5C2F7F19",
                                  "state": "complete",
                                  "securityType": "capable",
                                  "drawerLossProtection": False,
                                  "protectionInformationCapable": False,
                                  "protectionInformationCapabilities": {"protectionInformationCapable": True,
                                                                        "protectionType": "type2Protection"},
                                  "volumeGroupData": {"type": "unknown", "diskPoolData": None},
                                  "reservedSpaceAllocated": False,
                                  "securityLevel": "fde",
                                  "usedSpace": "322122547200",
                                  "totalRaidedSpace": "598926258176",
                                  "raidStatus": "optimal",
                                  "freeSpace": "276803710976",
                                  "drivePhysicalType": "sas",
                                  "driveMediaType": "hdd",
                                  "diskPool": False,
                                  "id": "04000000600A098000A4B28D00000FBD5C2F7F19",
                                  "name": "database_storage_pool"}]

    GET_LONG_LIVED_OPERATION_RESPONSE = [
        {"returnCode": "ok",
         "longLivedOpsProgress": [
             {"volAction": "initializing", "reconstruct": None, "volExpansion": None, "volAndCapExpansion": None,
              "init": {"volumeRef": "02000000600A098000A4B9D1000037315D494C6F", "pending": False, "percentComplete": 1, "timeToCompletion": 20},
              "format": None, "volCreation": None, "volDeletion": None},
             {"volAction": "initializing", "reconstruct": None, "volExpansion": None, "volAndCapExpansion": None,
              "init": {"volumeRef": "02000000600A098000A4B28D00003D2C5D494C87", "pending": False, "percentComplete": 0, "timeToCompletion": 18},
              "volCreation": None, "volDeletion": None}]},
        {"returnCode": "ok",
         "longLivedOpsProgress": [
             {"volAction": "complete", "reconstruct": None, "volExpansion": None, "volAndCapExpansion": None,
              "init": {"volumeRef": "02000000600A098000A4B9D1000037315D494C6F", "pending": False, "percentComplete": 1, "timeToCompletion": 20},
              "format": None, "volCreation": None, "volDeletion": None},
             {"volAction": "initializing", "reconstruct": None, "volExpansion": None, "volAndCapExpansion": None,
              "init": {"volumeRef": "02000000600A098000A4B28D00003D2C5D494C87", "pending": False, "percentComplete": 0, "timeToCompletion": 18},
              "volCreation": None, "volDeletion": None}]},
        {"returnCode": "ok",
         "longLivedOpsProgress": [
             {"volAction": "initializing", "reconstruct": None, "volExpansion": None, "volAndCapExpansion": None,
              "init": {"volumeRef": "02000000600A098000A4B9D1000037315D494C6F", "pending": False, "percentComplete": 1, "timeToCompletion": 20},
              "format": None, "volCreation": None, "volDeletion": None},
             {"volAction": "complete", "reconstruct": None, "volExpansion": None, "volAndCapExpansion": None,
              "init": {"volumeRef": "02000000600A098000A4B28D00003D2C5D494C87", "pending": False, "percentComplete": 0, "timeToCompletion": 18},
              "volCreation": None, "volDeletion": None}]},
        {"returnCode": "ok",
         "longLivedOpsProgress": [
             {"volAction": "complete", "reconstruct": None, "volExpansion": None, "volAndCapExpansion": None,
              "init": {"volumeRef": "02000000600A098000A4B9D1000037315D494C6F", "pending": False, "percentComplete": 1, "timeToCompletion": 20},
              "format": None, "volCreation": None, "volDeletion": None},
             {"volAction": "complete", "reconstruct": None, "volExpansion": None, "volAndCapExpansion": None,
              "init": {"volumeRef": "02000000600A098000A4B28D00003D2C5D494C87", "pending": False, "percentComplete": 0, "timeToCompletion": 18},
              "volCreation": None, "volDeletion": None}]}]

    WORKLOAD_GET_RESPONSE = [{"id": "4200000001000000000000000000000000000000", "name": "general_workload_1",
                              "workloadAttributes": [{"key": "profileId", "value": "Other_1"}]},
                             {"id": "4200000002000000000000000000000000000000", "name": "employee_data",
                              "workloadAttributes": [{"key": "use", "value": "EmployeeData"},
                                                     {"key": "location", "value": "ICT"},
                                                     {"key": "private", "value": "public"},
                                                     {"key": "profileId", "value": "ansible_workload_1"}]},
                             {"id": "4200000003000000000000000000000000000000", "name": "customer_database",
                              "workloadAttributes": [{"key": "use", "value": "customer_information"},
                                                     {"key": "location", "value": "global"},
                                                     {"key": "profileId", "value": "ansible_workload_2"}]},
                             {"id": "4200000004000000000000000000000000000000", "name": "product_database",
                              "workloadAttributes": [{"key": "use", "value": "production_information"},
                                                     {"key": "security", "value": "private"},
                                                     {"key": "location", "value": "global"},
                                                     {"key": "profileId", "value": "ansible_workload_4"}]}]

    REQUEST_FUNC = "ansible.modules.storage.netapp.netapp_e_volume.NetAppESeriesVolume.request"
    GET_VOLUME_FUNC = "ansible.modules.storage.netapp.netapp_e_volume.NetAppESeriesVolume.get_volume"
    SLEEP_FUNC = "ansible.modules.storage.netapp.netapp_e_volume.sleep"

    def _set_args(self, args=None):
        module_args = self.REQUIRED_PARAMS.copy()
        if args is not None:
            module_args.update(args)
        set_module_args(module_args)

    def test_module_arguments_pass(self):
        """Ensure valid arguments successful create a class instance."""
        arg_sets = [{"state": "present", "name": "vol", "storage_pool_name": "pool", "size": 100, "size_unit": "tb",
                     "thin_provision": True, "thin_volume_repo_size": 64, "thin_volume_max_repo_size": 1000,
                     "thin_volume_growth_alert_threshold": 10},
                    {"state": "present", "name": "vol", "storage_pool_name": "pool", "size": 100, "size_unit": "gb",
                     "thin_provision": True, "thin_volume_repo_size": 64, "thin_volume_max_repo_size": 1024,
                     "thin_volume_growth_alert_threshold": 99},
                    {"state": "present", "name": "vol", "storage_pool_name": "pool", "size": 100, "size_unit": "gb",
                     "thin_provision": True, "thin_volume_repo_size": 64},
                    {"state": "present", "name": "vol", "storage_pool_name": "pool", "size": 100, "size_unit": "kb",
                     "thin_provision": True, "thin_volume_repo_size": 64, "thin_volume_max_repo_size": 67108864}]

        # validate size normalization
        for arg_set in arg_sets:
            self._set_args(arg_set)
            volume_object = NetAppESeriesVolume()

            self.assertEqual(volume_object.size_b, volume_object.convert_to_aligned_bytes(arg_set["size"]))
            self.assertEqual(volume_object.thin_volume_repo_size_b, volume_object.convert_to_aligned_bytes(arg_set["thin_volume_repo_size"]))
            self.assertEqual(volume_object.thin_volume_expansion_policy, "automatic")
            if "thin_volume_max_repo_size" not in arg_set.keys():
                self.assertEqual(volume_object.thin_volume_max_repo_size_b, volume_object.convert_to_aligned_bytes(arg_set["size"]))
            else:
                self.assertEqual(volume_object.thin_volume_max_repo_size_b,
                                 volume_object.convert_to_aligned_bytes(arg_set["thin_volume_max_repo_size"]))

        # validate metadata form
        self._set_args(
            {"state": "present", "name": "vol", "storage_pool_name": "pool", "size": 10, "workload_name": "workload1",
             "metadata": {"availability": "public", "security": "low"}})
        volume_object = NetAppESeriesVolume()
        for entry in volume_object.metadata:
            self.assertTrue(entry in [{'value': 'low', 'key': 'security'}, {'value': 'public', 'key': 'availability'}])

    def test_module_arguments_fail(self):
        """Ensure invalid arguments values do not create a class instance."""
        arg_sets = [{"state": "present", "name": "vol", "storage_pool_name": "pool", "size": 100, "size_unit": "tb",
                     "thin_provision": True, "thin_volume_repo_size": 260},
                    {"state": "present", "name": "vol", "storage_pool_name": "pool", "size": 10000, "size_unit": "tb",
                     "thin_provision": True, "thin_volume_repo_size": 64, "thin_volume_max_repo_size": 10},
                    {"state": "present", "name": "vol", "storage_pool_name": "pool", "size": 10000, "size_unit": "gb",
                     "thin_provision": True, "thin_volume_repo_size": 64, "thin_volume_max_repo_size": 1000,
                     "thin_volume_growth_alert_threshold": 9},
                    {"state": "present", "name": "vol", "storage_pool_name": "pool", "size": 10000, "size_unit": "gb",
                     "thin_provision": True, "thin_volume_repo_size": 64, "thin_volume_max_repo_size": 1000,
                     "thin_volume_growth_alert_threshold": 100}]

        for arg_set in arg_sets:
            with self.assertRaises(AnsibleFailJson):
                self._set_args(arg_set)
                print(arg_set)
                volume_object = NetAppESeriesVolume()

    def test_get_volume_pass(self):
        """Evaluate the get_volume method."""
        with mock.patch(self.REQUEST_FUNC,
                        side_effect=[(200, self.VOLUME_GET_RESPONSE), (200, self.THIN_VOLUME_RESPONSE)]):
            self._set_args({"state": "present", "name": "Matthew", "storage_pool_name": "pool", "size": 100})
            volume_object = NetAppESeriesVolume()
            self.assertEqual(volume_object.get_volume(),
                             [entry for entry in self.VOLUME_GET_RESPONSE if entry["name"] == "Matthew"][0])

        with mock.patch(self.REQUEST_FUNC,
                        side_effect=[(200, self.VOLUME_GET_RESPONSE), (200, self.THIN_VOLUME_RESPONSE)]):
            self._set_args({"state": "present", "name": "NotAVolume", "storage_pool_name": "pool", "size": 100})
            volume_object = NetAppESeriesVolume()
            self.assertEqual(volume_object.get_volume(), {})

    def test_get_volume_fail(self):
        """Evaluate the get_volume exception paths."""
        with self.assertRaisesRegexp(AnsibleFailJson, "Failed to obtain list of thick volumes."):
            with mock.patch(self.REQUEST_FUNC, return_value=Exception()):
                self._set_args({"state": "present", "name": "Matthew", "storage_pool_name": "pool", "size": 100})
                volume_object = NetAppESeriesVolume()
                volume_object.get_volume()

        with self.assertRaisesRegexp(AnsibleFailJson, "Failed to obtain list of thin volumes."):
            with mock.patch(self.REQUEST_FUNC, side_effect=[(200, self.VOLUME_GET_RESPONSE), Exception()]):
                self._set_args({"state": "present", "name": "Matthew", "storage_pool_name": "pool", "size": 100})
                volume_object = NetAppESeriesVolume()
                volume_object.get_volume()

    def tests_wait_for_volume_availability_pass(self):
        """Ensure wait_for_volume_availability completes as expected."""
        self._set_args({"state": "present", "name": "NewVolume", "storage_pool_name": "employee_data_storage_pool", "size": 100,
                        "wait_for_initialization": True})
        volume_object = NetAppESeriesVolume()
        with mock.patch(self.SLEEP_FUNC, return_value=None):
            with mock.patch(self.GET_VOLUME_FUNC, side_effect=[False, False, True]):
                volume_object.wait_for_volume_availability()

    def tests_wait_for_volume_availability_fail(self):
        """Ensure wait_for_volume_availability throws the expected exceptions."""
        self._set_args({"state": "present", "name": "NewVolume", "storage_pool_name": "employee_data_storage_pool", "size": 100,
                        "wait_for_initialization": True})
        volume_object = NetAppESeriesVolume()
        volume_object.get_volume = lambda: False
        with self.assertRaisesRegexp(AnsibleFailJson, "Timed out waiting for the volume"):
            with mock.patch(self.SLEEP_FUNC, return_value=None):
                volume_object.wait_for_volume_availability()

    def tests_wait_for_volume_action_pass(self):
        """Ensure wait_for_volume_action completes as expected."""
        self._set_args({"state": "present", "name": "NewVolume", "storage_pool_name": "employee_data_storage_pool", "size": 100,
                        "wait_for_initialization": True})
        volume_object = NetAppESeriesVolume()
        volume_object.volume_detail = {"id": "02000000600A098000A4B9D1000037315D494C6F",
                                       "storageVolumeRef": "02000000600A098000A4B9D1000037315DXXXXXX"}
        with mock.patch(self.SLEEP_FUNC, return_value=None):
            with mock.patch(self.REQUEST_FUNC, side_effect=[(200, self.GET_LONG_LIVED_OPERATION_RESPONSE[0]),
                                                            (200, self.GET_LONG_LIVED_OPERATION_RESPONSE[1]),
                                                            (200, self.GET_LONG_LIVED_OPERATION_RESPONSE[2]),
                                                            (200, self.GET_LONG_LIVED_OPERATION_RESPONSE[3])]):
                volume_object.wait_for_volume_action()

        self._set_args({"state": "present", "name": "NewVolume", "storage_pool_name": "employee_data_storage_pool", "size": 100,
                        "wait_for_initialization": True})
        volume_object = NetAppESeriesVolume()
        volume_object.volume_detail = {"id": "02000000600A098000A4B9D1000037315DXXXXXX",
                                       "storageVolumeRef": "02000000600A098000A4B9D1000037315D494C6F"}
        with mock.patch(self.SLEEP_FUNC, return_value=None):
            with mock.patch(self.REQUEST_FUNC, side_effect=[(200, self.GET_LONG_LIVED_OPERATION_RESPONSE[0]),
                                                            (200, self.GET_LONG_LIVED_OPERATION_RESPONSE[1]),
                                                            (200, self.GET_LONG_LIVED_OPERATION_RESPONSE[2]),
                                                            (200, self.GET_LONG_LIVED_OPERATION_RESPONSE[3])]):
                volume_object.wait_for_volume_action()

    def tests_wait_for_volume_action_fail(self):
        """Ensure wait_for_volume_action throws the expected exceptions."""
        self._set_args({"state": "present", "name": "NewVolume", "storage_pool_name": "employee_data_storage_pool", "size": 100,
                        "wait_for_initialization": True})
        volume_object = NetAppESeriesVolume()
        volume_object.volume_detail = {"id": "02000000600A098000A4B9D1000037315DXXXXXX",
                                       "storageVolumeRef": "02000000600A098000A4B9D1000037315D494C6F"}
        with mock.patch(self.SLEEP_FUNC, return_value=None):
            with self.assertRaisesRegexp(AnsibleFailJson, "Failed to get volume expansion progress."):
                with mock.patch(self.REQUEST_FUNC, return_value=Exception()):
                    volume_object.wait_for_volume_action()

            with self.assertRaisesRegexp(AnsibleFailJson, "Expansion action failed to complete."):
                with mock.patch(self.REQUEST_FUNC, return_value=(200, self.GET_LONG_LIVED_OPERATION_RESPONSE[0])):
                    volume_object.wait_for_volume_action(timeout=300)

    def test_get_storage_pool_pass(self):
        """Evaluate the get_storage_pool method."""
        with mock.patch(self.REQUEST_FUNC, return_value=(200, self.STORAGE_POOL_GET_RESPONSE)):
            self._set_args({"state": "present", "name": "NewVolume", "storage_pool_name": "employee_data_storage_pool",
                            "size": 100})
            volume_object = NetAppESeriesVolume()
            self.assertEqual(volume_object.get_storage_pool(), [entry for entry in self.STORAGE_POOL_GET_RESPONSE if
                                                                entry["name"] == "employee_data_storage_pool"][0])

            self._set_args(
                {"state": "present", "name": "NewVolume", "storage_pool_name": "NotAStoragePool", "size": 100})
            volume_object = NetAppESeriesVolume()
            self.assertEqual(volume_object.get_storage_pool(), {})

    def test_get_storage_pool_fail(self):
        """Evaluate the get_storage_pool exception paths."""
        with self.assertRaisesRegexp(AnsibleFailJson, "Failed to obtain list of storage pools."):
            with mock.patch(self.REQUEST_FUNC, return_value=Exception()):
                self._set_args({"state": "present", "name": "Matthew", "storage_pool_name": "pool", "size": 100})
                volume_object = NetAppESeriesVolume()
                volume_object.get_storage_pool()

    def test_check_storage_pool_sufficiency_pass(self):
        """Ensure passing logic."""
        self._set_args({"state": "present", "name": "Matthew", "storage_pool_name": "pool", "size": 100})
        volume_object = NetAppESeriesVolume()
        volume_object.pool_detail = [entry for entry in self.STORAGE_POOL_GET_RESPONSE
                                     if entry["name"] == "employee_data_storage_pool"][0]
        volume_object.check_storage_pool_sufficiency()

    def test_check_storage_pool_sufficiency_fail(self):
        """Validate exceptions are thrown for insufficient storage pool resources."""
        self._set_args({"state": "present", "name": "vol", "storage_pool_name": "pool", "size": 100, "size_unit": "tb",
                        "thin_provision": True, "thin_volume_repo_size": 64, "thin_volume_max_repo_size": 1000,
                        "thin_volume_growth_alert_threshold": 10})
        volume_object = NetAppESeriesVolume()

        with self.assertRaisesRegexp(AnsibleFailJson, "Requested storage pool"):
            volume_object.check_storage_pool_sufficiency()

        with self.assertRaisesRegexp(AnsibleFailJson,
                                     "Thin provisioned volumes can only be created on raid disk pools."):
            volume_object.pool_detail = [entry for entry in self.STORAGE_POOL_GET_RESPONSE
                                         if entry["name"] == "database_storage_pool"][0]
            volume_object.volume_detail = {}
            volume_object.check_storage_pool_sufficiency()

        with self.assertRaisesRegexp(AnsibleFailJson, "requires the storage pool to be DA-compatible."):
            volume_object.pool_detail = {"diskPool": True,
                                         "protectionInformationCapabilities": {"protectionType": "type0Protection",
                                                                               "protectionInformationCapable": False}}
            volume_object.volume_detail = {}
            volume_object.data_assurance_enabled = True
            volume_object.check_storage_pool_sufficiency()

            volume_object.pool_detail = {"diskPool": True,
                                         "protectionInformationCapabilities": {"protectionType": "type2Protection",
                                                                               "protectionInformationCapable": True}}
            volume_object.check_storage_pool_sufficiency()

        self._set_args({"state": "present", "name": "vol", "storage_pool_name": "pool", "size": 100, "size_unit": "tb",
                        "thin_provision": False})
        volume_object = NetAppESeriesVolume()
        with self.assertRaisesRegexp(AnsibleFailJson,
                                     "Not enough storage pool free space available for the volume's needs."):
            volume_object.pool_detail = {"freeSpace": 10, "diskPool": True,
                                         "protectionInformationCapabilities": {"protectionType": "type2Protection",
                                                                               "protectionInformationCapable": True}}
            volume_object.volume_detail = {"totalSizeInBytes": 100}
            volume_object.data_assurance_enabled = True
            volume_object.size_b = 1
            volume_object.check_storage_pool_sufficiency()

    def test_update_workload_tags_pass(self):
        """Validate updating workload tags."""
        test_sets = [[{"state": "present", "name": "Matthew", "storage_pool_name": "pool", "size": 100}, False],
                     [{"state": "present", "name": "Matthew", "storage_pool_name": "pool", "size": 100,
                       "workload_name": "employee_data"}, False],
                     [{"state": "present", "name": "Matthew", "storage_pool_name": "pool", "size": 100,
                       "workload_name": "customer_database",
                       "metadata": {"use": "customer_information", "location": "global"}}, False],
                     [{"state": "present", "name": "Matthew", "storage_pool_name": "pool", "size": 100,
                       "workload_name": "customer_database",
                       "metadata": {"use": "customer_information"}}, True],
                     [{"state": "present", "name": "Matthew", "storage_pool_name": "pool", "size": 100,
                       "workload_name": "customer_database",
                       "metadata": {"use": "customer_information", "location": "local"}}, True],
                     [{"state": "present", "name": "Matthew", "storage_pool_name": "pool", "size": 100,
                       "workload_name": "customer_database",
                       "metadata": {"use": "customer_information", "location": "global", "importance": "no"}}, True],
                     [{"state": "present", "name": "Matthew", "storage_pool_name": "pool", "size": 100,
                       "workload_name": "newWorkload",
                       "metadata": {"for_testing": "yes"}}, True],
                     [{"state": "present", "name": "Matthew", "storage_pool_name": "pool", "size": 100,
                       "workload_name": "newWorkload"}, True]]

        for test in test_sets:
            self._set_args(test[0])
            volume_object = NetAppESeriesVolume()

            with mock.patch(self.REQUEST_FUNC, side_effect=[(200, self.WORKLOAD_GET_RESPONSE), (200, {"id": 1})]):
                self.assertEqual(volume_object.update_workload_tags(), test[1])

    def test_update_workload_tags_fail(self):
        """Validate updating workload tags fails appropriately."""
        self._set_args({"state": "present", "name": "Matthew", "storage_pool_name": "pool", "size": 100,
                        "workload_name": "employee_data"})
        volume_object = NetAppESeriesVolume()
        with self.assertRaisesRegexp(AnsibleFailJson, "Failed to retrieve storage array workload tags."):
            with mock.patch(self.REQUEST_FUNC, return_value=Exception()):
                volume_object.update_workload_tags()

        self._set_args({"state": "present", "name": "Matthew", "storage_pool_name": "pool", "size": 100,
                        "workload_name": "employee_data", "metadata": {"key": "not-use", "value": "EmployeeData"}})
        volume_object = NetAppESeriesVolume()
        with self.assertRaisesRegexp(AnsibleFailJson, "Failed to create new workload tag."):
            with mock.patch(self.REQUEST_FUNC, side_effect=[(200, self.WORKLOAD_GET_RESPONSE), Exception()]):
                volume_object.update_workload_tags()

        self._set_args({"state": "present", "name": "Matthew", "storage_pool_name": "pool", "size": 100,
                        "workload_name": "employee_data2", "metadata": {"key": "use", "value": "EmployeeData"}})
        volume_object = NetAppESeriesVolume()
        with self.assertRaisesRegexp(AnsibleFailJson, "Failed to create new workload tag."):
            with mock.patch(self.REQUEST_FUNC, side_effect=[(200, self.WORKLOAD_GET_RESPONSE), Exception()]):
                volume_object.update_workload_tags()

    def test_get_volume_property_changes_pass(self):
        """Verify correct dictionary is returned"""

        # no property changes
        self._set_args(
            {"state": "present", "name": "Matthew", "storage_pool_name": "pool", "size": 100, "ssd_cache_enabled": True,
             "read_cache_enable": True, "write_cache_enable": True,
             "read_ahead_enable": True, "thin_provision": False})
        volume_object = NetAppESeriesVolume()
        volume_object.volume_detail = {"metadata": [],
                                       "cacheSettings": {"cwob": False, "readCacheEnable": True, "writeCacheEnable": True,
                                                         "readAheadMultiplier": 1}, "flashCached": True,
                                       "segmentSize": str(128 * 1024)}
        self.assertEqual(volume_object.get_volume_property_changes(), dict())

        self._set_args(
            {"state": "present", "name": "Matthew", "storage_pool_name": "pool", "size": 100, "ssd_cache_enabled": True,
             "read_cache_enable": True, "write_cache_enable": True,
             "read_ahead_enable": True, "thin_provision": True, "thin_volume_repo_size": 64,
             "thin_volume_max_repo_size": 1000, "thin_volume_growth_alert_threshold": 90})
        volume_object = NetAppESeriesVolume()
        volume_object.volume_detail = {"metadata": [],
                                       "cacheSettings": {"cwob": False, "readCacheEnable": True, "writeCacheEnable": True,
                                                         "readAheadMultiplier": 1},
                                       "flashCached": True, "growthAlertThreshold": "90",
                                       "expansionPolicy": "automatic", "segmentSize": str(128 * 1024)}
        self.assertEqual(volume_object.get_volume_property_changes(), dict())

        # property changes
        self._set_args(
            {"state": "present", "name": "Matthew", "storage_pool_name": "pool", "size": 100, "ssd_cache_enabled": True,
             "read_cache_enable": True, "write_cache_enable": True,
             "read_ahead_enable": True, "thin_provision": False})
        volume_object = NetAppESeriesVolume()
        volume_object.volume_detail = {"metadata": [],
                                       "cacheSettings": {"cwob": False, "readCacheEnable": False, "writeCacheEnable": True,
                                                         "readAheadMultiplier": 1}, "flashCached": True,
                                       "segmentSize": str(128 * 1024)}
        self.assertEqual(volume_object.get_volume_property_changes(),
                         {"metaTags": [], 'cacheSettings': {'readCacheEnable': True, 'writeCacheEnable': True},
                          'flashCache': True})
        self._set_args(
            {"state": "present", "name": "Matthew", "storage_pool_name": "pool", "size": 100, "ssd_cache_enabled": True,
             "read_cache_enable": True, "write_cache_enable": True, "cache_without_batteries": False,
             "read_ahead_enable": True, "thin_provision": False})
        volume_object = NetAppESeriesVolume()
        volume_object.volume_detail = {"metadata": [],
                                       "cacheSettings": {"cwob": False, "readCacheEnable": True, "writeCacheEnable": False,
                                                         "readAheadMultiplier": 1}, "flashCached": True,
                                       "segmentSize": str(128 * 1024)}
        self.assertEqual(volume_object.get_volume_property_changes(),
                         {"metaTags": [], 'cacheSettings': {'readCacheEnable': True, 'writeCacheEnable': True},
                          'flashCache': True})
        self._set_args(
            {"state": "present", "name": "Matthew", "storage_pool_name": "pool", "size": 100, "ssd_cache_enabled": True,
             "read_cache_enable": True, "write_cache_enable": True, "cache_without_batteries": True,
             "read_ahead_enable": True, "thin_provision": False})
        volume_object = NetAppESeriesVolume()
        volume_object.volume_detail = {"metadata": [],
                                       "cacheSettings": {"cwob": False, "readCacheEnable": True, "writeCacheEnable": True,
                                                         "readAheadMultiplier": 1}, "flashCached": False,
                                       "segmentSize": str(128 * 1024)}
        self.assertEqual(volume_object.get_volume_property_changes(),
                         {"metaTags": [], 'cacheSettings': {'readCacheEnable': True, 'writeCacheEnable': True, "cacheWithoutBatteries": True},
                          'flashCache': True})
        self._set_args(
            {"state": "present", "name": "Matthew", "storage_pool_name": "pool", "size": 100, "ssd_cache_enabled": True,
             "read_cache_enable": True, "write_cache_enable": True, "cache_without_batteries": True,
             "read_ahead_enable": False, "thin_provision": False})
        volume_object = NetAppESeriesVolume()
        volume_object.volume_detail = {"metadata": [],
                                       "cacheSettings": {"cwob": False, "readCacheEnable": True, "writeCacheEnable": True,
                                                         "readAheadMultiplier": 1}, "flashCached": False,
                                       "segmentSize": str(128 * 1024)}
        self.assertEqual(volume_object.get_volume_property_changes(), {"metaTags": [],
                                                                       'cacheSettings': {'readCacheEnable': True,
                                                                                         'writeCacheEnable': True,
                                                                                         'readAheadEnable': False,
                                                                                         "cacheWithoutBatteries": True},
                                                                       'flashCache': True})

        self._set_args(
            {"state": "present", "name": "Matthew", "storage_pool_name": "pool", "size": 100, "ssd_cache_enabled": True,
             "read_cache_enable": True, "write_cache_enable": True,
             "read_ahead_enable": True, "thin_provision": True, "thin_volume_repo_size": 64,
             "thin_volume_max_repo_size": 1000, "thin_volume_growth_alert_threshold": 90})
        volume_object = NetAppESeriesVolume()
        volume_object.volume_detail = {"metadata": [],
                                       "cacheSettings": {"cwob": True, "readCacheEnable": True, "writeCacheEnable": True,
                                                         "readAheadMultiplier": 1},
                                       "flashCached": True, "growthAlertThreshold": "95",
                                       "expansionPolicy": "automatic", "segmentSize": str(128 * 1024)}
        self.assertEqual(volume_object.get_volume_property_changes(),
                         {"metaTags": [], 'cacheSettings': {'readCacheEnable': True, 'writeCacheEnable': True},
                          'growthAlertThreshold': 90, 'flashCache': True})

    def test_get_volume_property_changes_fail(self):
        """Verify correct exception is thrown"""
        self._set_args(
            {"state": "present", "name": "Matthew", "storage_pool_name": "pool", "size": 100, "ssd_cache_enabled": True,
             "read_cache_enable": True, "write_cache_enable": True, "read_ahead_enable": True, "thin_provision": False})
        volume_object = NetAppESeriesVolume()
        volume_object.volume_detail = {
            "cacheSettings": {"cwob": False, "readCacheEnable": True, "writeCacheEnable": True, "readAheadMultiplier": 1},
            "flashCached": True, "segmentSize": str(512 * 1024)}
        with self.assertRaisesRegexp(AnsibleFailJson, "Existing volume segment size is"):
            volume_object.get_volume_property_changes()

    def test_get_expand_volume_changes_pass(self):
        """Verify expansion changes."""
        # thick volumes
        self._set_args(
            {"state": "present", "name": "Matthew", "storage_pool_name": "pool", "size": 100, "thin_provision": False})
        volume_object = NetAppESeriesVolume()
        volume_object.volume_detail = {"capacity": str(50 * 1024 * 1024 * 1024), "thinProvisioned": False}
        self.assertEqual(volume_object.get_expand_volume_changes(),
                         {"sizeUnit": "bytes", "expansionSize": 100 * 1024 * 1024 * 1024})

        # thin volumes
        self._set_args(
            {"state": "present", "name": "Matthew", "storage_pool_name": "pool", "size": 100, "thin_provision": True,
             "thin_volume_expansion_policy": "automatic", "thin_volume_repo_size": 64,
             "thin_volume_max_repo_size": 1000, "thin_volume_growth_alert_threshold": 90})
        volume_object = NetAppESeriesVolume()
        volume_object.volume_detail = {"capacity": str(50 * 1024 * 1024 * 1024), "thinProvisioned": True,
                                       "expansionPolicy": "automatic",
                                       "provisionedCapacityQuota": str(1000 * 1024 * 1024 * 1024)}
        self.assertEqual(volume_object.get_expand_volume_changes(),
                         {"sizeUnit": "bytes", "newVirtualSize": 100 * 1024 * 1024 * 1024})
        self._set_args(
            {"state": "present", "name": "Matthew", "storage_pool_name": "pool", "size": 100, "thin_provision": True,
             "thin_volume_expansion_policy": "automatic", "thin_volume_repo_size": 64,
             "thin_volume_max_repo_size": 1000, "thin_volume_growth_alert_threshold": 90})
        volume_object = NetAppESeriesVolume()
        volume_object.volume_detail = {"capacity": str(100 * 1024 * 1024 * 1024), "thinProvisioned": True,
                                       "expansionPolicy": "automatic",
                                       "provisionedCapacityQuota": str(500 * 1024 * 1024 * 1024)}
        self.assertEqual(volume_object.get_expand_volume_changes(),
                         {"sizeUnit": "bytes", "newRepositorySize": 1000 * 1024 * 1024 * 1024})
        self._set_args(
            {"state": "present", "name": "Matthew", "storage_pool_name": "pool", "size": 100, "thin_provision": True,
             "thin_volume_expansion_policy": "manual", "thin_volume_repo_size": 504, "thin_volume_max_repo_size": 1000,
             "thin_volume_growth_alert_threshold": 90})
        volume_object = NetAppESeriesVolume()
        volume_object.volume_detail = {"capacity": str(100 * 1024 * 1024 * 1024), "thinProvisioned": True,
                                       "expansionPolicy": "manual",
                                       "currentProvisionedCapacity": str(500 * 1024 * 1024 * 1024)}
        self.assertEqual(volume_object.get_expand_volume_changes(),
                         {"sizeUnit": "bytes", "newRepositorySize": 504 * 1024 * 1024 * 1024})
        self._set_args(
            {"state": "present", "name": "Matthew", "storage_pool_name": "pool", "size": 100, "thin_provision": True,
             "thin_volume_expansion_policy": "manual", "thin_volume_repo_size": 756, "thin_volume_max_repo_size": 1000,
             "thin_volume_growth_alert_threshold": 90})
        volume_object = NetAppESeriesVolume()
        volume_object.volume_detail = {"capacity": str(100 * 1024 * 1024 * 1024), "thinProvisioned": True,
                                       "expansionPolicy": "manual",
                                       "currentProvisionedCapacity": str(500 * 1024 * 1024 * 1024)}
        self.assertEqual(volume_object.get_expand_volume_changes(),
                         {"sizeUnit": "bytes", "newRepositorySize": 756 * 1024 * 1024 * 1024})

    def test_get_expand_volume_changes_fail(self):
        """Verify exceptions are thrown."""
        self._set_args(
            {"state": "present", "name": "Matthew", "storage_pool_name": "pool", "size": 100, "thin_provision": False})
        volume_object = NetAppESeriesVolume()
        volume_object.volume_detail = {"capacity": str(1000 * 1024 * 1024 * 1024)}
        with self.assertRaisesRegexp(AnsibleFailJson, "Reducing the size of volumes is not permitted."):
            volume_object.get_expand_volume_changes()

        self._set_args(
            {"state": "present", "name": "Matthew", "storage_pool_name": "pool", "size": 100, "thin_provision": True,
             "thin_volume_expansion_policy": "manual", "thin_volume_repo_size": 502, "thin_volume_max_repo_size": 1000,
             "thin_volume_growth_alert_threshold": 90})
        volume_object = NetAppESeriesVolume()
        volume_object.volume_detail = {"capacity": str(100 * 1024 * 1024 * 1024), "thinProvisioned": True,
                                       "expansionPolicy": "manual",
                                       "currentProvisionedCapacity": str(500 * 1024 * 1024 * 1024)}
        with self.assertRaisesRegexp(AnsibleFailJson, "The thin volume repository increase must be between or equal"):
            volume_object.get_expand_volume_changes()

        self._set_args(
            {"state": "present", "name": "Matthew", "storage_pool_name": "pool", "size": 100, "thin_provision": True,
             "thin_volume_expansion_policy": "manual", "thin_volume_repo_size": 760, "thin_volume_max_repo_size": 1000,
             "thin_volume_growth_alert_threshold": 90})
        volume_object = NetAppESeriesVolume()
        volume_object.volume_detail = {"capacity": str(100 * 1024 * 1024 * 1024), "thinProvisioned": True,
                                       "expansionPolicy": "manual",
                                       "currentProvisionedCapacity": str(500 * 1024 * 1024 * 1024)}
        with self.assertRaisesRegexp(AnsibleFailJson, "The thin volume repository increase must be between or equal"):
            volume_object.get_expand_volume_changes()

    def test_create_volume_pass(self):
        """Verify volume creation."""
        self._set_args(
            {"state": "present", "name": "Matthew", "storage_pool_name": "pool", "size": 100, "thin_provision": False})
        volume_object = NetAppESeriesVolume()
        volume_object.pool_detail = {"id": "12345"}
        with mock.patch(self.REQUEST_FUNC, return_value=(200, {})):
            volume_object.create_volume()

        self._set_args(
            {"state": "present", "name": "Matthew", "storage_pool_name": "pool", "size": 100, "thin_provision": True,
             "thin_volume_expansion_policy": "manual", "thin_volume_repo_size": 760, "thin_volume_max_repo_size": 1000,
             "thin_volume_growth_alert_threshold": 90})
        volume_object = NetAppESeriesVolume()
        volume_object.pool_detail = {"id": "12345"}
        with mock.patch(self.REQUEST_FUNC, return_value=(200, {})):
            volume_object.create_volume()

    def test_create_volume_fail(self):
        """Verify exceptions thrown."""
        self._set_args(
            {"state": "present", "name": "Matthew", "storage_pool_name": "pool", "size": 100, "thin_provision": False})
        volume_object = NetAppESeriesVolume()
        volume_object.pool_detail = {"id": "12345"}
        with self.assertRaisesRegexp(AnsibleFailJson, "Failed to create volume."):
            with mock.patch(self.REQUEST_FUNC, return_value=Exception()):
                volume_object.create_volume()

        self._set_args(
            {"state": "present", "name": "Matthew", "storage_pool_name": "pool", "size": 100, "thin_provision": True,
             "thin_volume_expansion_policy": "manual", "thin_volume_repo_size": 760, "thin_volume_max_repo_size": 1000,
             "thin_volume_growth_alert_threshold": 90})
        volume_object = NetAppESeriesVolume()
        volume_object.pool_detail = {"id": "12345"}
        with self.assertRaisesRegexp(AnsibleFailJson, "Failed to create thin volume."):
            with mock.patch(self.REQUEST_FUNC, return_value=Exception()):
                volume_object.create_volume()

    def test_update_volume_properties_pass(self):
        """verify property update."""
        self._set_args(
            {"state": "present", "name": "Matthew", "storage_pool_name": "pool", "size": 100, "thin_provision": False})
        volume_object = NetAppESeriesVolume()
        volume_object.pool_detail = {"id": "12345"}
        volume_object.wait_for_volume_availability = lambda: None
        volume_object.get_volume = lambda: {"id": "12345'"}
        volume_object.get_volume_property_changes = lambda: {
            'cacheSettings': {'readCacheEnable': True, 'writeCacheEnable': True}, 'growthAlertThreshold': 90,
            'flashCached': True}
        volume_object.workload_id = "4200000001000000000000000000000000000000"
        with mock.patch(self.REQUEST_FUNC, return_value=(200, {})):
            self.assertTrue(volume_object.update_volume_properties())

        self._set_args(
            {"state": "present", "name": "Matthew", "storage_pool_name": "pool", "size": 100, "thin_provision": True,
             "thin_volume_expansion_policy": "manual", "thin_volume_repo_size": 760, "thin_volume_max_repo_size": 1000,
             "thin_volume_growth_alert_threshold": 90})
        volume_object = NetAppESeriesVolume()
        volume_object.pool_detail = {"id": "12345"}
        volume_object.wait_for_volume_availability = lambda: None
        volume_object.get_volume = lambda: {"id": "12345'"}
        volume_object.get_volume_property_changes = lambda: {
            'cacheSettings': {'readCacheEnable': True, 'writeCacheEnable': True}, 'growthAlertThreshold': 90,
            'flashCached': True}
        volume_object.workload_id = "4200000001000000000000000000000000000000"
        with mock.patch(self.REQUEST_FUNC, return_value=(200, {})):
            self.assertTrue(volume_object.update_volume_properties())

        self._set_args(
            {"state": "present", "name": "Matthew", "storage_pool_name": "pool", "size": 100, "thin_provision": False})
        volume_object = NetAppESeriesVolume()
        volume_object.pool_detail = {"metadata": [{"key": "workloadId", "value": "12345"}]}
        volume_object.wait_for_volume_availability = lambda: None
        volume_object.get_volume = lambda: {"id": "12345'"}
        volume_object.get_volume_property_changes = lambda: {}
        volume_object.workload_id = "4200000001000000000000000000000000000000"
        self.assertFalse(volume_object.update_volume_properties())

    def test_update_volume_properties_fail(self):
        """Verify exceptions are thrown."""
        self._set_args(
            {"state": "present", "name": "Matthew", "storage_pool_name": "pool", "size": 100, "thin_provision": False})
        volume_object = NetAppESeriesVolume()
        volume_object.pool_detail = {"id": "12345"}
        volume_object.wait_for_volume_availability = lambda: None
        volume_object.get_volume = lambda: {"id": "12345'"}
        volume_object.get_volume_property_changes = lambda: {
            'cacheSettings': {'readCacheEnable': True, 'writeCacheEnable': True}, 'growthAlertThreshold': 90,
            'flashCached': True}
        volume_object.workload_id = "4200000001000000000000000000000000000000"
        with self.assertRaisesRegexp(AnsibleFailJson, "Failed to update volume properties."):
            with mock.patch(self.REQUEST_FUNC, return_value=Exception()):
                self.assertTrue(volume_object.update_volume_properties())

        self._set_args(
            {"state": "present", "name": "Matthew", "storage_pool_name": "pool", "size": 100, "thin_provision": True,
             "thin_volume_expansion_policy": "manual", "thin_volume_repo_size": 760, "thin_volume_max_repo_size": 1000,
             "thin_volume_growth_alert_threshold": 90})
        volume_object = NetAppESeriesVolume()
        volume_object.pool_detail = {"id": "12345"}
        volume_object.wait_for_volume_availability = lambda: None
        volume_object.get_volume = lambda: {"id": "12345'"}
        volume_object.get_volume_property_changes = lambda: {
            'cacheSettings': {'readCacheEnable': True, 'writeCacheEnable': True}, 'growthAlertThreshold': 90,
            'flashCached': True}
        volume_object.workload_id = "4200000001000000000000000000000000000000"
        with self.assertRaisesRegexp(AnsibleFailJson, "Failed to update thin volume properties."):
            with mock.patch(self.REQUEST_FUNC, return_value=Exception()):
                self.assertTrue(volume_object.update_volume_properties())

    def test_expand_volume_pass(self):
        """Verify volume expansion."""
        self._set_args(
            {"state": "present", "name": "Matthew", "storage_pool_name": "pool", "size": 100, "thin_provision": False})
        volume_object = NetAppESeriesVolume()
        volume_object.get_expand_volume_changes = lambda: {"sizeUnit": "bytes",
                                                           "expansionSize": 100 * 1024 * 1024 * 1024}
        volume_object.volume_detail = {"id": "12345", "thinProvisioned": True}
        with mock.patch(self.REQUEST_FUNC, return_value=(200, {})):
            volume_object.expand_volume()

        self._set_args(
            {"state": "present", "name": "Matthew", "storage_pool_name": "pool", "size": 100, "thin_provision": True,
             "thin_volume_expansion_policy": "manual", "thin_volume_repo_size": 760, "thin_volume_max_repo_size": 1000,
             "thin_volume_growth_alert_threshold": 90})
        volume_object = NetAppESeriesVolume()
        volume_object.get_expand_volume_changes = lambda: {"sizeUnit": "bytes",
                                                           "expansionSize": 100 * 1024 * 1024 * 1024}
        volume_object.volume_detail = {"id": "12345", "thinProvisioned": True}
        with mock.patch(self.REQUEST_FUNC, return_value=(200, {})):
            volume_object.expand_volume()

    def test_expand_volume_fail(self):
        """Verify exceptions are thrown."""
        self._set_args(
            {"state": "present", "name": "Matthew", "storage_pool_name": "pool", "size": 100, "thin_provision": False})
        volume_object = NetAppESeriesVolume()
        volume_object.get_expand_volume_changes = lambda: {"sizeUnit": "bytes",
                                                           "expansionSize": 100 * 1024 * 1024 * 1024}
        volume_object.volume_detail = {"id": "12345", "thinProvisioned": False}
        with self.assertRaisesRegexp(AnsibleFailJson, "Failed to expand volume."):
            with mock.patch(self.REQUEST_FUNC, return_value=Exception()):
                volume_object.expand_volume()

        self._set_args(
            {"state": "present", "name": "Matthew", "storage_pool_name": "pool", "size": 100, "thin_provision": True})
        volume_object = NetAppESeriesVolume()
        volume_object.get_expand_volume_changes = lambda: {"sizeUnit": "bytes",
                                                           "expansionSize": 100 * 1024 * 1024 * 1024}
        volume_object.volume_detail = {"id": "12345", "thinProvisioned": True}
        with self.assertRaisesRegexp(AnsibleFailJson, "Failed to expand thin volume."):
            with mock.patch(self.REQUEST_FUNC, return_value=Exception()):
                volume_object.expand_volume()

    def test_delete_volume_pass(self):
        """Verify volume deletion."""
        self._set_args(
            {"state": "present", "name": "Matthew", "storage_pool_name": "pool", "size": 100, "thin_provision": False})
        volume_object = NetAppESeriesVolume()
        volume_object.volume_detail = {"id": "12345"}
        with mock.patch(self.REQUEST_FUNC, return_value=(200, {})):
            volume_object.delete_volume()

        self._set_args(
            {"state": "present", "name": "Matthew", "storage_pool_name": "pool", "size": 100, "thin_provision": True,
             "thin_volume_expansion_policy": "manual", "thin_volume_repo_size": 760, "thin_volume_max_repo_size": 1000,
             "thin_volume_growth_alert_threshold": 90})
        volume_object = NetAppESeriesVolume()
        volume_object.volume_detail = {"id": "12345"}
        with mock.patch(self.REQUEST_FUNC, return_value=(200, {})):
            volume_object.delete_volume()

    def test_delete_volume_fail(self):
        """Verify exceptions are thrown."""
        self._set_args(
            {"state": "present", "name": "Matthew", "storage_pool_name": "pool", "size": 100, "thin_provision": False})
        volume_object = NetAppESeriesVolume()
        with self.assertRaisesRegexp(AnsibleFailJson, "Failed to delete volume."):
            with mock.patch(self.REQUEST_FUNC, return_value=Exception()):
                volume_object.delete_volume()

        self._set_args(
            {"state": "present", "name": "Matthew", "storage_pool_name": "pool", "size": 100, "thin_provision": True})
        volume_object = NetAppESeriesVolume()
        with self.assertRaisesRegexp(AnsibleFailJson, "Failed to delete thin volume."):
            with mock.patch(self.REQUEST_FUNC, return_value=Exception()):
                volume_object.delete_volume()
