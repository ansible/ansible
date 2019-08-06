# coding=utf-8
# (c) 2018, NetApp Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import absolute_import, division, print_function
__metaclass__ = type

from units.modules.utils import AnsibleExitJson, AnsibleFailJson, ModuleTestCase, set_module_args
from ansible.modules.storage.netapp.netapp_e_storagepool import NetAppESeriesStoragePool

try:
    from unittest.mock import patch, PropertyMock
except ImportError:
    from mock import patch, PropertyMock


class StoragePoolTest(ModuleTestCase):
    REQUIRED_PARAMS = {"api_username": "username",
                       "api_password": "password",
                       "api_url": "http://localhost/devmgr/v2",
                       "ssid": "1",
                       "validate_certs": "no"}

    STORAGE_POOL_DATA = [{"raidLevel": "raidDiskPool", "volumeGroupRef": "04000000600A098000A4B28D000017805C7BD4D8",
                          "securityType": "capable",
                          "protectionInformationCapabilities": {"protectionInformationCapable": True,
                                                                "protectionType": "type2Protection"},
                          "volumeGroupData": {"diskPoolData": {"reconstructionReservedDriveCount": 2}},
                          "totalRaidedSpace": "2735894167552", "name": "pool",
                          "id": "04000000600A098000A4B28D000017805C7BD4D8", "driveMediaType": "hdd"}]
    DRIVES_DATA = [{'available': True, 'currentVolumeGroupRef': '0000000000000000000000000000000000000000',
                    'driveMediaType': 'hdd', 'id': '010000005000C500551ED1FF0000000000000000', 'fdeCapable': True,
                    'hotSpare': False, 'invalidDriveData': False, 'nonRedundantAccess': False, 'pfa': False,
                    'phyDriveType': 'sas', 'protectionInformationCapabilities': {'protectionInformationCapable': True,
                                                                                 'protectionType': 'type2Protection'},
                    'rawCapacity': '300000000000', 'removed': False, 'status': 'optimal', 'uncertified': False,
                    'usableCapacity': '299463129088'},
                   {'available': False, 'currentVolumeGroupRef': '04000000600A098000A4B28D000017805C7BD4D8',
                    'driveMediaType': 'hdd', 'id': '010000005000C500551EB1930000000000000000', 'fdeCapable': True,
                    'hotSpare': False, 'invalidDriveData': False, 'nonRedundantAccess': False, 'pfa': False,
                    'phyDriveType': 'sas', 'protectionInformationCapabilities': {'protectionInformationCapable': True,
                                                                                 'protectionType': 'type2Protection'},
                    'rawCapacity': '300000000000', 'removed': False, 'status': 'optimal', 'uncertified': False,
                    'usableCapacity': '299463129088'},
                   {'available': False, 'currentVolumeGroupRef': '04000000600A098000A4B28D000017805C7BD4D8',
                    'driveMediaType': 'hdd', 'id': '010000005000C500551EAAE30000000000000000', 'fdeCapable': True,
                    'hotSpare': False, 'invalidDriveData': False, 'nonRedundantAccess': False, 'pfa': False,
                    'phyDriveType': 'sas', 'protectionInformationCapabilities': {'protectionInformationCapable': True,
                                                                                 'protectionType': 'type2Protection'},
                    'rawCapacity': '300000000000', 'removed': False, 'status': 'optimal', 'uncertified': False,
                    'usableCapacity': '299463129088'},
                   {'available': False, 'currentVolumeGroupRef': '04000000600A098000A4B28D000017805C7BD4D8',
                    'driveMediaType': 'hdd', 'id': '010000005000C500551ECB1F0000000000000000', 'fdeCapable': True,
                    'hotSpare': False, 'invalidDriveData': False, 'nonRedundantAccess': False, 'pfa': False,
                    'phyDriveType': 'sas', 'protectionInformationCapabilities': {'protectionInformationCapable': True,
                                                                                 'protectionType': 'type2Protection'},
                    'rawCapacity': '300000000000', 'removed': False, 'status': 'optimal', 'uncertified': False,
                    'usableCapacity': '299463129088'},
                   {'available': False, 'currentVolumeGroupRef': '04000000600A098000A4B28D000017805C7BD4D8',
                    'driveMediaType': 'hdd', 'id': '010000005000C500551EB2930000000000000000', 'fdeCapable': True,
                    'hotSpare': False, 'invalidDriveData': False, 'nonRedundantAccess': False, 'pfa': False,
                    'phyDriveType': 'sas', 'protectionInformationCapabilities': {'protectionInformationCapable': True,
                                                                                 'protectionType': 'type2Protection'},
                    'rawCapacity': '300000000000', 'removed': False, 'status': 'optimal', 'uncertified': False,
                    'usableCapacity': '299463129088'},
                   {'available': False, 'currentVolumeGroupRef': '04000000600A098000A4B28D000017805C7BD4D8',
                    'driveMediaType': 'hdd', 'id': '010000005000C500551ECB0B0000000000000000', 'fdeCapable': True,
                    'hotSpare': False, 'invalidDriveData': False, 'nonRedundantAccess': False, 'pfa': False,
                    'phyDriveType': 'sas', 'protectionInformationCapabilities': {'protectionInformationCapable': True,
                                                                                 'protectionType': 'type2Protection'},
                    'rawCapacity': '300000000000', 'removed': False, 'status': 'optimal', 'uncertified': False,
                    'usableCapacity': '299463129088'},
                   {'available': False, 'currentVolumeGroupRef': '04000000600A098000A4B28D000017805C7BD4D8',
                    'driveMediaType': 'hdd', 'id': '010000005000C500551EC6C70000000000000000', 'fdeCapable': True,
                    'hotSpare': False, 'invalidDriveData': False, 'nonRedundantAccess': False, 'pfa': False,
                    'phyDriveType': 'sas', 'protectionInformationCapabilities': {'protectionInformationCapable': True,
                                                                                 'protectionType': 'type2Protection'},
                    'rawCapacity': '300000000000', 'removed': False, 'status': 'optimal', 'uncertified': False,
                    'usableCapacity': '299463129088'},
                   {'available': False, 'currentVolumeGroupRef': '04000000600A098000A4B28D000017805C7BD4D8',
                    'driveMediaType': 'hdd', 'id': '010000005000C500551E9BA70000000000000000', 'fdeCapable': True,
                    'hotSpare': False, 'invalidDriveData': False, 'nonRedundantAccess': False, 'pfa': False,
                    'phyDriveType': 'sas', 'protectionInformationCapabilities': {'protectionInformationCapable': True,
                                                                                 'protectionType': 'type2Protection'},
                    'rawCapacity': '300000000000', 'removed': False, 'status': 'optimal', 'uncertified': False,
                    'usableCapacity': '299463129088'},
                   {'available': False, 'currentVolumeGroupRef': '04000000600A098000A4B28D000017805C7BD4D8',
                    'driveMediaType': 'hdd', 'id': '010000005000C500551ED7CF0000000000000000', 'fdeCapable': True,
                    'hotSpare': False, 'invalidDriveData': False, 'nonRedundantAccess': False, 'pfa': False,
                    'phyDriveType': 'sas', 'protectionInformationCapabilities': {'protectionInformationCapable': True,
                                                                                 'protectionType': 'type2Protection'},
                    'rawCapacity': '300000000000', 'removed': False, 'status': 'optimal', 'uncertified': False,
                    'usableCapacity': '299463129088'},
                   {'available': False, 'currentVolumeGroupRef': '04000000600A098000A4B28D000017805C7BD4D8',
                    'driveMediaType': 'hdd', 'id': '010000005000C500551ECB0F0000000000000000', 'fdeCapable': True,
                    'hotSpare': False, 'invalidDriveData': False, 'nonRedundantAccess': False, 'pfa': False,
                    'phyDriveType': 'sas', 'protectionInformationCapabilities': {'protectionInformationCapable': True,
                                                                                 'protectionType': 'type2Protection'},
                    'rawCapacity': '300000000000', 'removed': False, 'status': 'optimal', 'uncertified': False,
                    'usableCapacity': '299463129088'},
                   {'available': False, 'currentVolumeGroupRef': '04000000600A098000A4B28D000017805C7BD4D8',
                    'driveMediaType': 'hdd', 'id': '010000005000C500551E72870000000000000000', 'fdeCapable': True,
                    'hotSpare': False, 'invalidDriveData': False, 'nonRedundantAccess': False, 'pfa': False,
                    'phyDriveType': 'sas', 'protectionInformationCapabilities': {'protectionInformationCapable': True,
                                                                                 'protectionType': 'type2Protection'},
                    'rawCapacity': '300000000000', 'removed': False, 'status': 'optimal', 'uncertified': False,
                    'usableCapacity': '299463129088'},
                   {'available': False, 'currentVolumeGroupRef': '04000000600A098000A4B28D000017805C7BD4D8',
                    'driveMediaType': 'hdd', 'id': '010000005000C500551E9DBB0000000000000000', 'fdeCapable': True,
                    'hotSpare': False, 'invalidDriveData': False, 'nonRedundantAccess': False, 'pfa': False,
                    'phyDriveType': 'sas', 'protectionInformationCapabilities': {'protectionInformationCapable': True,
                                                                                 'protectionType': 'type2Protection'},
                    'rawCapacity': '300000000000', 'removed': False, 'status': 'optimal', 'uncertified': False,
                    'usableCapacity': '299463129088'},
                   {'available': False, 'currentVolumeGroupRef': '04000000600A098000A4B28D000017805C7BD4D8',
                    'driveMediaType': 'hdd', 'id': '010000005000C500551EAC230000000000000000', 'fdeCapable': True,
                    'hotSpare': False, 'invalidDriveData': False, 'nonRedundantAccess': False, 'pfa': False,
                    'phyDriveType': 'sas', 'protectionInformationCapabilities': {'protectionInformationCapable': True,
                                                                                 'protectionType': 'type2Protection'},
                    'rawCapacity': '300000000000', 'removed': False, 'status': 'optimal', 'uncertified': False,
                    'usableCapacity': '299463129088'},
                   {'available': False, 'currentVolumeGroupRef': '04000000600A098000A4B28D000017805C7BD4D8',
                    'driveMediaType': 'hdd', 'id': '010000005000C500551EA0BB0000000000000000', 'fdeCapable': True,
                    'hotSpare': False, 'invalidDriveData': False, 'nonRedundantAccess': False, 'pfa': False,
                    'phyDriveType': 'sas', 'protectionInformationCapabilities': {'protectionInformationCapable': True,
                                                                                 'protectionType': 'type2Protection'},
                    'rawCapacity': '300000000000', 'removed': False, 'status': 'optimal', 'uncertified': False,
                    'usableCapacity': '299463129088'},
                   {'available': False, 'currentVolumeGroupRef': '04000000600A098000A4B28D000017805C7BD4D8',
                    'driveMediaType': 'hdd', 'id': '010000005000C500551EAC4B0000000000000000', 'fdeCapable': True,
                    'hotSpare': False, 'invalidDriveData': False, 'nonRedundantAccess': False, 'pfa': False,
                    'phyDriveType': 'sas', 'protectionInformationCapabilities': {'protectionInformationCapable': True,
                                                                                 'protectionType': 'type2Protection'},
                    'rawCapacity': '300000000000', 'removed': False, 'status': 'optimal', 'uncertified': False,
                    'usableCapacity': '299463129088'},
                   {'available': True, 'currentVolumeGroupRef': '0000000000000000000000000000000000000000',
                    'driveMediaType': 'hdd', 'id': '010000005000C500551E7F2B0000000000000000', 'fdeCapable': True,
                    'hotSpare': False, 'invalidDriveData': False, 'nonRedundantAccess': False, 'pfa': False,
                    'phyDriveType': 'sas', 'protectionInformationCapabilities': {'protectionInformationCapable': True,
                                                                                 'protectionType': 'type2Protection'},
                    'rawCapacity': '300000000000', 'removed': False, 'status': 'optimal', 'uncertified': False,
                    'usableCapacity': '299463129088'},
                   {'available': True, 'currentVolumeGroupRef': '0000000000000000000000000000000000000000',
                    'driveMediaType': 'hdd', 'id': '010000005000C500551EC9270000000000000000', 'fdeCapable': True,
                    'hotSpare': False, 'invalidDriveData': False, 'nonRedundantAccess': False, 'pfa': False,
                    'phyDriveType': 'sas', 'protectionInformationCapabilities': {'protectionInformationCapable': True,
                                                                                 'protectionType': 'type2Protection'},
                    'rawCapacity': '300000000000', 'removed': False, 'status': 'optimal', 'uncertified': False,
                    'usableCapacity': '299463129088'},
                   {'available': True, 'currentVolumeGroupRef': '0000000000000000000000000000000000000000',
                    'driveMediaType': 'hdd', 'id': '010000005000C500551EC97F0000000000000000', 'fdeCapable': True,
                    'hotSpare': False, 'invalidDriveData': False, 'nonRedundantAccess': False, 'pfa': False,
                    'phyDriveType': 'sas', 'protectionInformationCapabilities': {'protectionInformationCapable': True,
                                                                                 'protectionType': 'type2Protection'},
                    'rawCapacity': '300000000000', 'removed': False, 'status': 'optimal', 'uncertified': False,
                    'usableCapacity': '299463129088'},
                   {'available': True, 'currentVolumeGroupRef': '0000000000000000000000000000000000000000',
                    'driveMediaType': 'hdd', 'id': '010000005000C500551ECBFF0000000000000000', 'fdeCapable': True,
                    'hotSpare': False, 'invalidDriveData': False, 'nonRedundantAccess': False, 'pfa': False,
                    'phyDriveType': 'sas', 'protectionInformationCapabilities': {'protectionInformationCapable': True,
                                                                                 'protectionType': 'type2Protection'},
                    'rawCapacity': '300000000000', 'removed': False, 'status': 'optimal', 'uncertified': False,
                    'usableCapacity': '299463129088'},
                   {'available': True, 'currentVolumeGroupRef': '0000000000000000000000000000000000000000',
                    'driveMediaType': 'hdd', 'id': '010000005000C500551E9ED30000000000000000', 'fdeCapable': True,
                    'hotSpare': False, 'invalidDriveData': False, 'nonRedundantAccess': False, 'pfa': False,
                    'phyDriveType': 'sas', 'protectionInformationCapabilities': {'protectionInformationCapable': True,
                                                                                 'protectionType': 'type2Protection'},
                    'rawCapacity': '300000000000', 'removed': False, 'status': 'optimal', 'uncertified': False,
                    'usableCapacity': '299463129088'},
                   {'available': True, 'currentVolumeGroupRef': '0000000000000000000000000000000000000000',
                    'driveMediaType': 'hdd', 'id': '010000005000C500551EA4CF0000000000000000', 'fdeCapable': True,
                    'hotSpare': False, 'invalidDriveData': False, 'nonRedundantAccess': False, 'pfa': False,
                    'phyDriveType': 'sas', 'protectionInformationCapabilities': {'protectionInformationCapable': True,
                                                                                 'protectionType': 'type2Protection'},
                    'rawCapacity': '300000000000', 'removed': False, 'status': 'optimal', 'uncertified': False,
                    'usableCapacity': '299463129088'},
                   {'available': True, 'currentVolumeGroupRef': '0000000000000000000000000000000000000000',
                    'driveMediaType': 'hdd', 'id': '010000005000C500551EA29F0000000000000000', 'fdeCapable': True,
                    'hotSpare': False, 'invalidDriveData': False, 'nonRedundantAccess': False, 'pfa': False,
                    'phyDriveType': 'sas', 'protectionInformationCapabilities': {'protectionInformationCapable': True,
                                                                                 'protectionType': 'type2Protection'},
                    'rawCapacity': '300000000000', 'removed': False, 'status': 'optimal', 'uncertified': False,
                    'usableCapacity': '299463129088'},
                   {'available': True, 'currentVolumeGroupRef': '0000000000000000000000000000000000000000',
                    'driveMediaType': 'hdd', 'id': '010000005000C500551ECDFB0000000000000000', 'fdeCapable': True,
                    'hotSpare': False, 'invalidDriveData': False, 'nonRedundantAccess': False, 'pfa': False,
                    'phyDriveType': 'sas', 'protectionInformationCapabilities': {'protectionInformationCapable': True,
                                                                                 'protectionType': 'type2Protection'},
                    'rawCapacity': '300000000000', 'removed': False, 'status': 'optimal', 'uncertified': False,
                    'usableCapacity': '299463129088'},
                   {'available': True, 'currentVolumeGroupRef': '0000000000000000000000000000000000000000',
                    'driveMediaType': 'hdd', 'id': '010000005000C500551E99230000000000000000', 'fdeCapable': True,
                    'hotSpare': False, 'invalidDriveData': False, 'nonRedundantAccess': False, 'pfa': False,
                    'phyDriveType': 'sas', 'protectionInformationCapabilities': {'protectionInformationCapable': True,
                                                                                 'protectionType': 'type2Protection'},
                    'rawCapacity': '300000000000', 'removed': False, 'status': 'optimal', 'uncertified': False,
                    'usableCapacity': '299463129088'},
                   {'available': True, 'currentVolumeGroupRef': '0000000000000000000000000000000000000000',
                    'driveMediaType': 'ssd', 'id': '010000005000C500551E9ED31000000000000000', 'fdeCapable': True,
                    'hotSpare': False, 'invalidDriveData': False, 'nonRedundantAccess': False, 'pfa': False,
                    'phyDriveType': 'sas', 'protectionInformationCapabilities': {'protectionInformationCapable': True,
                                                                                 'protectionType': 'type2Protection'},
                    'rawCapacity': '300000000000', 'removed': False, 'status': 'optimal', 'uncertified': False,
                    'usableCapacity': '299463129088'},
                   {'available': True, 'currentVolumeGroupRef': '0000000000000000000000000000000000000000',
                    'driveMediaType': 'ssd', 'id': '010000005000C500551EA4CF2000000000000000', 'fdeCapable': True,
                    'hotSpare': False, 'invalidDriveData': False, 'nonRedundantAccess': False, 'pfa': False,
                    'phyDriveType': 'sas', 'protectionInformationCapabilities': {'protectionInformationCapable': True,
                                                                                 'protectionType': 'type2Protection'},
                    'rawCapacity': '300000000000', 'removed': False, 'status': 'optimal', 'uncertified': False,
                    'usableCapacity': '299463129088'},
                   {'available': True, 'currentVolumeGroupRef': '0000000000000000000000000000000000000000',
                    'driveMediaType': 'ssd', 'id': '010000005000C500551EA29F3000000000000000', 'fdeCapable': True,
                    'hotSpare': False, 'invalidDriveData': False, 'nonRedundantAccess': False, 'pfa': False,
                    'phyDriveType': 'sas', 'protectionInformationCapabilities': {'protectionInformationCapable': True,
                                                                                 'protectionType': 'type2Protection'},
                    'rawCapacity': '300000000000', 'removed': False, 'status': 'optimal', 'uncertified': False,
                    'usableCapacity': '299463129088'},
                   {'available': True, 'currentVolumeGroupRef': '0000000000000000000000000000000000000000',
                    'driveMediaType': 'ssd', 'id': '010000005000C500551ECDFB4000000000000000', 'fdeCapable': True,
                    'hotSpare': False, 'invalidDriveData': False, 'nonRedundantAccess': False, 'pfa': False,
                    'phyDriveType': 'sas', 'protectionInformationCapabilities': {'protectionInformationCapable': True,
                                                                                 'protectionType': 'type2Protection'},
                    'rawCapacity': '300000000000', 'removed': False, 'status': 'optimal', 'uncertified': False,
                    'usableCapacity': '299463129088'},
                   {'available': True, 'currentVolumeGroupRef': '0000000000000000000000000000000000000000',
                    'driveMediaType': 'ssd', 'id': '010000005000C500551E99235000000000000000', 'fdeCapable': True,
                    'hotSpare': False, 'invalidDriveData': False, 'nonRedundantAccess': False, 'pfa': False,
                    'phyDriveType': 'sata', 'protectionInformationCapabilities': {'protectionInformationCapable': True,
                                                                                  'protectionType': 'type2Protection'},
                    'rawCapacity': '300000000000', 'removed': False, 'status': 'optimal', 'uncertified': False,
                    'usableCapacity': '299463129088'}]

    RAID6_CANDIDATE_DRIVES = {"volumeCandidate": [
        {"raidLevel": "raid6", "trayLossProtection": False, "rawSize": "898389368832", "usableSize": "898388459520",
         "driveCount": 5, "freeExtentRef": "0000000000000000000000000000000000000000", "driveRefList": {
             "driveRef": ["010000005000C500551E7F2B0000000000000000", "010000005000C500551EC9270000000000000000",
                          "010000005000C500551EC97F0000000000000000", "010000005000C500551ECBFF0000000000000000",
                          "010000005000C500551E9ED30000000000000000"]}, "candidateSelectionType": "count",
         "spindleSpeedMatch": True, "spindleSpeed": 10000, "phyDriveType": "sas", "dssPreallocEnabled": False,
         "securityType": "capable", "drawerLossProtection": False, "driveMediaType": "hdd",
         "protectionInformationCapable": False,
         "protectionInformationCapabilities": {"protectionInformationCapable": True,
                                               "protectionType": "type2Protection"},
         "volumeCandidateData": {"type": "traditional", "diskPoolVolumeCandidateData": None},
         "driveBlockFormat": "allNative", "allocateReservedSpace": False, "securityLevel": "fde"},
        {"raidLevel": "raid6", "trayLossProtection": False, "rawSize": "1197852491776", "usableSize": "1197851279360",
         "driveCount": 6, "freeExtentRef": "0000000000000000000000000000000000000000", "driveRefList": {
             "driveRef": ["010000005000C500551E7F2B0000000000000000", "010000005000C500551EC9270000000000000000",
                          "010000005000C500551EC97F0000000000000000", "010000005000C500551ECBFF0000000000000000",
                          "010000005000C500551E9ED30000000000000000", "010000005000C500551EA4CF0000000000000000"]},
         "candidateSelectionType": "count", "spindleSpeedMatch": True, "spindleSpeed": 10000, "phyDriveType": "sas",
         "dssPreallocEnabled": False, "securityType": "capable", "drawerLossProtection": False, "driveMediaType": "hdd",
         "protectionInformationCapable": False,
         "protectionInformationCapabilities": {"protectionInformationCapable": True,
                                               "protectionType": "type2Protection"},
         "volumeCandidateData": {"type": "traditional", "diskPoolVolumeCandidateData": None},
         "driveBlockFormat": "allNative", "allocateReservedSpace": False, "securityLevel": "fde"},
        {"raidLevel": "raid6", "trayLossProtection": False, "rawSize": "1497315614720", "usableSize": "1497314099200",
         "driveCount": 7, "freeExtentRef": "0000000000000000000000000000000000000000", "driveRefList": {
             "driveRef": ["010000005000C500551E7F2B0000000000000000", "010000005000C500551EC9270000000000000000",
                          "010000005000C500551EC97F0000000000000000", "010000005000C500551ECBFF0000000000000000",
                          "010000005000C500551E9ED30000000000000000", "010000005000C500551EA4CF0000000000000000",
                          "010000005000C500551ED1FF0000000000000000"]}, "candidateSelectionType": "count",
         "spindleSpeedMatch": True, "spindleSpeed": 10000, "phyDriveType": "sas", "dssPreallocEnabled": False,
         "securityType": "capable", "drawerLossProtection": False, "driveMediaType": "hdd",
         "protectionInformationCapable": False,
         "protectionInformationCapabilities": {"protectionInformationCapable": True,
                                               "protectionType": "type2Protection"},
         "volumeCandidateData": {"type": "traditional", "diskPoolVolumeCandidateData": None},
         "driveBlockFormat": "allNative", "allocateReservedSpace": False, "securityLevel": "fde"},
        {"raidLevel": "raid6", "trayLossProtection": False, "rawSize": "1796778737664", "usableSize": "1796776919040",
         "driveCount": 8, "freeExtentRef": "0000000000000000000000000000000000000000", "driveRefList": {
             "driveRef": ["010000005000C500551E7F2B0000000000000000", "010000005000C500551EC9270000000000000000",
                          "010000005000C500551EC97F0000000000000000", "010000005000C500551ECBFF0000000000000000",
                          "010000005000C500551E9ED30000000000000000", "010000005000C500551EA4CF0000000000000000",
                          "010000005000C500551ED1FF0000000000000000", "010000005000C500551EA29F0000000000000000"]},
         "candidateSelectionType": "count", "spindleSpeedMatch": True, "spindleSpeed": 10000, "phyDriveType": "sas",
         "dssPreallocEnabled": False, "securityType": "capable", "drawerLossProtection": False, "driveMediaType": "hdd",
         "protectionInformationCapable": False,
         "protectionInformationCapabilities": {"protectionInformationCapable": True,
                                               "protectionType": "type2Protection"},
         "volumeCandidateData": {"type": "traditional", "diskPoolVolumeCandidateData": None},
         "driveBlockFormat": "allNative", "allocateReservedSpace": False, "securityLevel": "fde"},
        {"raidLevel": "raid6", "trayLossProtection": False, "rawSize": "2096241860608", "usableSize": "2096239738880",
         "driveCount": 9, "freeExtentRef": "0000000000000000000000000000000000000000", "driveRefList": {
             "driveRef": ["010000005000C500551E7F2B0000000000000000", "010000005000C500551EC9270000000000000000",
                          "010000005000C500551EC97F0000000000000000", "010000005000C500551ECBFF0000000000000000",
                          "010000005000C500551E9ED30000000000000000", "010000005000C500551EA4CF0000000000000000",
                          "010000005000C500551ED1FF0000000000000000", "010000005000C500551EA29F0000000000000000",
                          "010000005000C500551ECDFB0000000000000000"]}, "candidateSelectionType": "count",
         "spindleSpeedMatch": True, "spindleSpeed": 10000, "phyDriveType": "sas", "dssPreallocEnabled": False,
         "securityType": "capable", "drawerLossProtection": False, "driveMediaType": "hdd",
         "protectionInformationCapable": False,
         "protectionInformationCapabilities": {"protectionInformationCapable": True,
                                               "protectionType": "type2Protection"},
         "volumeCandidateData": {"type": "traditional", "diskPoolVolumeCandidateData": None},
         "driveBlockFormat": "allNative", "allocateReservedSpace": False, "securityLevel": "fde"},
        {"raidLevel": "raid6", "trayLossProtection": False, "rawSize": "2395704983552", "usableSize": "2395702558720",
         "driveCount": 10, "freeExtentRef": "0000000000000000000000000000000000000000", "driveRefList": {
             "driveRef": ["010000005000C500551E7F2B0000000000000000", "010000005000C500551EC9270000000000000000",
                          "010000005000C500551EC97F0000000000000000", "010000005000C500551ECBFF0000000000000000",
                          "010000005000C500551E9ED30000000000000000", "010000005000C500551EA4CF0000000000000000",
                          "010000005000C500551ED1FF0000000000000000", "010000005000C500551EA29F0000000000000000",
                          "010000005000C500551ECDFB0000000000000000", "010000005000C500551E99230000000000000000"]},
         "candidateSelectionType": "count", "spindleSpeedMatch": True, "spindleSpeed": 10000, "phyDriveType": "sas",
         "dssPreallocEnabled": False, "securityType": "capable", "drawerLossProtection": False, "driveMediaType": "hdd",
         "protectionInformationCapable": False,
         "protectionInformationCapabilities": {"protectionInformationCapable": True,
                                               "protectionType": "type2Protection"},
         "volumeCandidateData": {"type": "traditional", "diskPoolVolumeCandidateData": None},
         "driveBlockFormat": "allNative", "allocateReservedSpace": False, "securityLevel": "fde"}], "returnCode": "ok"}

    EXPANSION_DDP_DRIVES_LIST = ["010000005000C500551ED1FF0000000000000000", "010000005000C500551E7F2B0000000000000000",
                                 "010000005000C500551EC9270000000000000000", "010000005000C500551EC97F0000000000000000",
                                 "010000005000C500551ECBFF0000000000000000", "010000005000C500551E9ED30000000000000000",
                                 "010000005000C500551EA4CF0000000000000000", "010000005000C500551EA29F0000000000000000",
                                 "010000005000C500551ECDFB0000000000000000", "010000005000C500551E99230000000000000000",
                                 "010000005000C500551E9ED31000000000000000", "010000005000C500551EA4CF2000000000000000",
                                 "010000005000C500551EA29F3000000000000000", "010000005000C500551ECDFB4000000000000000",
                                 "010000005000C500551E99235000000000000000"]
    EXPANSION_DDP_DRIVE_DATA = {"returnCode": "ok", "candidates": [
        {"drives": ["010000005000C500551E7F2B0000000000000000"], "trayLossProtection": False, "wastedCapacity": "0",
         "spindleSpeedMatch": True, "drawerLossProtection": False, "usableCapacity": "299463129088",
         "driveBlockFormat": "allNative"},
        {"drives": ["010000005000C500551E7F2B0000000000000000", "010000005000C500551E99230000000000000000"],
         "trayLossProtection": False, "wastedCapacity": "0", "spindleSpeedMatch": True, "drawerLossProtection": False,
         "usableCapacity": "598926258176", "driveBlockFormat": "allNative"},
        {"drives": ["010000005000C500551E7F2B0000000000000000", "010000005000C500551E99230000000000000000",
                    "010000005000C500551E9ED30000000000000000"], "trayLossProtection": False, "wastedCapacity": "0",
         "spindleSpeedMatch": True, "drawerLossProtection": False, "usableCapacity": "898389387264",
         "driveBlockFormat": "allNative"},
        {"drives": ["010000005000C500551E7F2B0000000000000000", "010000005000C500551E99230000000000000000",
                    "010000005000C500551E9ED30000000000000000", "010000005000C500551EA29F0000000000000000"],
         "trayLossProtection": False, "wastedCapacity": "0", "spindleSpeedMatch": True, "drawerLossProtection": False,
         "usableCapacity": "1197852516352", "driveBlockFormat": "allNative"},
        {"drives": ["010000005000C500551E7F2B0000000000000000", "010000005000C500551E99230000000000000000",
                    "010000005000C500551E9ED30000000000000000", "010000005000C500551EA29F0000000000000000",
                    "010000005000C500551EA4CF0000000000000000"], "trayLossProtection": False, "wastedCapacity": "0",
         "spindleSpeedMatch": True, "drawerLossProtection": False, "usableCapacity": "1497315645440",
         "driveBlockFormat": "allNative"},
        {"drives": ["010000005000C500551E7F2B0000000000000000", "010000005000C500551E99230000000000000000",
                    "010000005000C500551E9ED30000000000000000", "010000005000C500551EA29F0000000000000000",
                    "010000005000C500551EA4CF0000000000000000", "010000005000C500551EC9270000000000000000"],
         "trayLossProtection": False, "wastedCapacity": "0", "spindleSpeedMatch": True, "drawerLossProtection": False,
         "usableCapacity": "1796778774528", "driveBlockFormat": "allNative"},
        {"drives": ["010000005000C500551E7F2B0000000000000000", "010000005000C500551E99230000000000000000",
                    "010000005000C500551E9ED30000000000000000", "010000005000C500551EA29F0000000000000000",
                    "010000005000C500551EA4CF0000000000000000", "010000005000C500551EC9270000000000000000",
                    "010000005000C500551EC97F0000000000000000"], "trayLossProtection": False, "wastedCapacity": "0",
         "spindleSpeedMatch": True, "drawerLossProtection": False, "usableCapacity": "2096241903616",
         "driveBlockFormat": "allNative"},
        {"drives": ["010000005000C500551E7F2B0000000000000000", "010000005000C500551E99230000000000000000",
                    "010000005000C500551E9ED30000000000000000", "010000005000C500551EA29F0000000000000000",
                    "010000005000C500551EA4CF0000000000000000", "010000005000C500551EC9270000000000000000",
                    "010000005000C500551EC97F0000000000000000", "010000005000C500551ECBFF0000000000000000"],
         "trayLossProtection": False, "wastedCapacity": "0", "spindleSpeedMatch": True, "drawerLossProtection": False,
         "usableCapacity": "2395705032704", "driveBlockFormat": "allNative"},
        {"drives": ["010000005000C500551E7F2B0000000000000000", "010000005000C500551E99230000000000000000",
                    "010000005000C500551E9ED30000000000000000", "010000005000C500551EA29F0000000000000000",
                    "010000005000C500551EA4CF0000000000000000", "010000005000C500551EC9270000000000000000",
                    "010000005000C500551EC97F0000000000000000", "010000005000C500551ECBFF0000000000000000",
                    "010000005000C500551ECDFB0000000000000000"], "trayLossProtection": False, "wastedCapacity": "0",
         "spindleSpeedMatch": True, "drawerLossProtection": False, "usableCapacity": "2695168161792",
         "driveBlockFormat": "allNative"},
        {"drives": ["010000005000C500551E7F2B0000000000000000", "010000005000C500551E99230000000000000000",
                    "010000005000C500551E9ED30000000000000000", "010000005000C500551EA29F0000000000000000",
                    "010000005000C500551EA4CF0000000000000000", "010000005000C500551EC9270000000000000000",
                    "010000005000C500551EC97F0000000000000000", "010000005000C500551ECBFF0000000000000000",
                    "010000005000C500551ECDFB0000000000000000", "010000005000C500551ED1FF0000000000000000"],
         "trayLossProtection": False, "wastedCapacity": "0", "spindleSpeedMatch": True, "drawerLossProtection": False,
         "usableCapacity": "2994631290880", "driveBlockFormat": "allNative"}]}

    REQUEST_FUNC = "ansible.modules.storage.netapp.netapp_e_storagepool.request"
    NETAPP_REQUEST_FUNC = "ansible.module_utils.netapp.NetAppESeriesModule.request"
    VALIDATE_FUNC = "ansible.modules.storage.netapp.netapp_e_storagepool.NetAppESeriesModule.validate_instance"

    DRIVES_PROPERTY = "ansible.modules.storage.netapp.netapp_e_storagepool.NetAppESeriesStoragePool.drives"
    STORAGE_POOL_PROPERTY = "ansible.modules.storage.netapp.netapp_e_storagepool.NetAppESeriesStoragePool.storage_pool"

    def _set_args(self, args=None):
        module_args = self.REQUIRED_PARAMS.copy()
        if args is not None:
            module_args.update(args)
        set_module_args(module_args)

    def _initialize_dummy_instance(self, alt_args=None):
        """Initialize a dummy instance of NetAppESeriesStoragePool for the purpose of testing individual methods."""
        args = {"state": "absent", "name": "storage_pool"}
        if alt_args:
            args.update(alt_args)
        self._set_args(args)
        return NetAppESeriesStoragePool()

    def test_drives_fail(self):
        """Verify exception is thrown."""

        with patch(self.NETAPP_REQUEST_FUNC) as netapp_request:
            netapp_request.return_value = Exception()
            storagepool = self._initialize_dummy_instance()
            with self.assertRaisesRegexp(AnsibleFailJson, "Failed to fetch disk drives."):
                drives = storagepool.drives

    def test_available_drives(self):
        """Verify all drives returned are available"""
        with patch(self.DRIVES_PROPERTY, new_callable=PropertyMock) as drives:
            drives.return_value = self.DRIVES_DATA

            storagepool = self._initialize_dummy_instance()
            self.assertEqual(storagepool.available_drives,
                             ['010000005000C500551ED1FF0000000000000000', '010000005000C500551E7F2B0000000000000000',
                              '010000005000C500551EC9270000000000000000', '010000005000C500551EC97F0000000000000000',
                              '010000005000C500551ECBFF0000000000000000', '010000005000C500551E9ED30000000000000000',
                              '010000005000C500551EA4CF0000000000000000', '010000005000C500551EA29F0000000000000000',
                              '010000005000C500551ECDFB0000000000000000', '010000005000C500551E99230000000000000000',
                              '010000005000C500551E9ED31000000000000000', '010000005000C500551EA4CF2000000000000000',
                              '010000005000C500551EA29F3000000000000000', '010000005000C500551ECDFB4000000000000000',
                              '010000005000C500551E99235000000000000000'])

    def test_available_drive_types(self):
        """Verify all drive types are returned in most common first order."""
        with patch(self.DRIVES_PROPERTY, new_callable=PropertyMock) as drives:
            drives.return_value = self.DRIVES_DATA

            storagepool = self._initialize_dummy_instance()
            self.assertEqual(storagepool.available_drive_types[0], "hdd")
            self.assertEqual(storagepool.available_drive_types[1], "ssd")

    def test_available_drive_interface_types(self):
        """Verify all interface types are returned in most common first order."""
        with patch(self.DRIVES_PROPERTY, new_callable=PropertyMock) as drives:
            drives.return_value = self.DRIVES_DATA

            storagepool = self._initialize_dummy_instance()
            self.assertEqual(storagepool.available_drive_interface_types[0], "sas")
            self.assertEqual(storagepool.available_drive_interface_types[1], "sata")

    def test_storage_pool_drives(self):
        """Verify storage pool drive collection."""
        with patch(self.DRIVES_PROPERTY, new_callable=PropertyMock) as drives:
            drives.return_value = self.DRIVES_DATA

            storagepool = self._initialize_dummy_instance(
                {"state": "present", "name": "pool", "criteria_drive_count": "12", "raid_level": "raidDiskPool"})
            storagepool.pool_detail = self.STORAGE_POOL_DATA[0]
            self.assertEqual(storagepool.storage_pool_drives, [
                {'available': False, 'pfa': False, 'driveMediaType': 'hdd', 'uncertified': False,
                 'protectionInformationCapabilities': {'protectionInformationCapable': True,
                                                       'protectionType': 'type2Protection'}, 'fdeCapable': True,
                 'currentVolumeGroupRef': '04000000600A098000A4B28D000017805C7BD4D8', 'invalidDriveData': False,
                 'nonRedundantAccess': False, 'hotSpare': False, 'status': 'optimal', 'rawCapacity': '300000000000',
                 'usableCapacity': '299463129088', 'phyDriveType': 'sas', 'removed': False,
                 'id': '010000005000C500551EB1930000000000000000'},
                {'available': False, 'pfa': False, 'driveMediaType': 'hdd', 'uncertified': False,
                 'protectionInformationCapabilities': {'protectionInformationCapable': True,
                                                       'protectionType': 'type2Protection'}, 'fdeCapable': True,
                 'currentVolumeGroupRef': '04000000600A098000A4B28D000017805C7BD4D8', 'invalidDriveData': False,
                 'nonRedundantAccess': False, 'hotSpare': False, 'status': 'optimal', 'rawCapacity': '300000000000',
                 'usableCapacity': '299463129088', 'phyDriveType': 'sas', 'removed': False,
                 'id': '010000005000C500551EAAE30000000000000000'},
                {'available': False, 'pfa': False, 'driveMediaType': 'hdd', 'uncertified': False,
                 'protectionInformationCapabilities': {'protectionInformationCapable': True,
                                                       'protectionType': 'type2Protection'}, 'fdeCapable': True,
                 'currentVolumeGroupRef': '04000000600A098000A4B28D000017805C7BD4D8', 'invalidDriveData': False,
                 'nonRedundantAccess': False, 'hotSpare': False, 'status': 'optimal', 'rawCapacity': '300000000000',
                 'usableCapacity': '299463129088', 'phyDriveType': 'sas', 'removed': False,
                 'id': '010000005000C500551ECB1F0000000000000000'},
                {'available': False, 'pfa': False, 'driveMediaType': 'hdd', 'uncertified': False,
                 'protectionInformationCapabilities': {'protectionInformationCapable': True,
                                                       'protectionType': 'type2Protection'}, 'fdeCapable': True,
                 'currentVolumeGroupRef': '04000000600A098000A4B28D000017805C7BD4D8', 'invalidDriveData': False,
                 'nonRedundantAccess': False, 'hotSpare': False, 'status': 'optimal', 'rawCapacity': '300000000000',
                 'usableCapacity': '299463129088', 'phyDriveType': 'sas', 'removed': False,
                 'id': '010000005000C500551EB2930000000000000000'},
                {'available': False, 'pfa': False, 'driveMediaType': 'hdd', 'uncertified': False,
                 'protectionInformationCapabilities': {'protectionInformationCapable': True,
                                                       'protectionType': 'type2Protection'}, 'fdeCapable': True,
                 'currentVolumeGroupRef': '04000000600A098000A4B28D000017805C7BD4D8', 'invalidDriveData': False,
                 'nonRedundantAccess': False, 'hotSpare': False, 'status': 'optimal', 'rawCapacity': '300000000000',
                 'usableCapacity': '299463129088', 'phyDriveType': 'sas', 'removed': False,
                 'id': '010000005000C500551ECB0B0000000000000000'},
                {'available': False, 'pfa': False, 'driveMediaType': 'hdd', 'uncertified': False,
                 'protectionInformationCapabilities': {'protectionInformationCapable': True,
                                                       'protectionType': 'type2Protection'}, 'fdeCapable': True,
                 'currentVolumeGroupRef': '04000000600A098000A4B28D000017805C7BD4D8', 'invalidDriveData': False,
                 'nonRedundantAccess': False, 'hotSpare': False, 'status': 'optimal', 'rawCapacity': '300000000000',
                 'usableCapacity': '299463129088', 'phyDriveType': 'sas', 'removed': False,
                 'id': '010000005000C500551EC6C70000000000000000'},
                {'available': False, 'pfa': False, 'driveMediaType': 'hdd', 'uncertified': False,
                 'protectionInformationCapabilities': {'protectionInformationCapable': True,
                                                       'protectionType': 'type2Protection'}, 'fdeCapable': True,
                 'currentVolumeGroupRef': '04000000600A098000A4B28D000017805C7BD4D8', 'invalidDriveData': False,
                 'nonRedundantAccess': False, 'hotSpare': False, 'status': 'optimal', 'rawCapacity': '300000000000',
                 'usableCapacity': '299463129088', 'phyDriveType': 'sas', 'removed': False,
                 'id': '010000005000C500551E9BA70000000000000000'},
                {'available': False, 'pfa': False, 'driveMediaType': 'hdd', 'uncertified': False,
                 'protectionInformationCapabilities': {'protectionInformationCapable': True,
                                                       'protectionType': 'type2Protection'}, 'fdeCapable': True,
                 'currentVolumeGroupRef': '04000000600A098000A4B28D000017805C7BD4D8', 'invalidDriveData': False,
                 'nonRedundantAccess': False, 'hotSpare': False, 'status': 'optimal', 'rawCapacity': '300000000000',
                 'usableCapacity': '299463129088', 'phyDriveType': 'sas', 'removed': False,
                 'id': '010000005000C500551ED7CF0000000000000000'},
                {'available': False, 'pfa': False, 'driveMediaType': 'hdd', 'uncertified': False,
                 'protectionInformationCapabilities': {'protectionInformationCapable': True,
                                                       'protectionType': 'type2Protection'}, 'fdeCapable': True,
                 'currentVolumeGroupRef': '04000000600A098000A4B28D000017805C7BD4D8', 'invalidDriveData': False,
                 'nonRedundantAccess': False, 'hotSpare': False, 'status': 'optimal', 'rawCapacity': '300000000000',
                 'usableCapacity': '299463129088', 'phyDriveType': 'sas', 'removed': False,
                 'id': '010000005000C500551ECB0F0000000000000000'},
                {'available': False, 'pfa': False, 'driveMediaType': 'hdd', 'uncertified': False,
                 'protectionInformationCapabilities': {'protectionInformationCapable': True,
                                                       'protectionType': 'type2Protection'}, 'fdeCapable': True,
                 'currentVolumeGroupRef': '04000000600A098000A4B28D000017805C7BD4D8', 'invalidDriveData': False,
                 'nonRedundantAccess': False, 'hotSpare': False, 'status': 'optimal', 'rawCapacity': '300000000000',
                 'usableCapacity': '299463129088', 'phyDriveType': 'sas', 'removed': False,
                 'id': '010000005000C500551E72870000000000000000'},
                {'available': False, 'pfa': False, 'driveMediaType': 'hdd', 'uncertified': False,
                 'protectionInformationCapabilities': {'protectionInformationCapable': True,
                                                       'protectionType': 'type2Protection'}, 'fdeCapable': True,
                 'currentVolumeGroupRef': '04000000600A098000A4B28D000017805C7BD4D8', 'invalidDriveData': False,
                 'nonRedundantAccess': False, 'hotSpare': False, 'status': 'optimal', 'rawCapacity': '300000000000',
                 'usableCapacity': '299463129088', 'phyDriveType': 'sas', 'removed': False,
                 'id': '010000005000C500551E9DBB0000000000000000'},
                {'available': False, 'pfa': False, 'driveMediaType': 'hdd', 'uncertified': False,
                 'protectionInformationCapabilities': {'protectionInformationCapable': True,
                                                       'protectionType': 'type2Protection'}, 'fdeCapable': True,
                 'currentVolumeGroupRef': '04000000600A098000A4B28D000017805C7BD4D8', 'invalidDriveData': False,
                 'nonRedundantAccess': False, 'hotSpare': False, 'status': 'optimal', 'rawCapacity': '300000000000',
                 'usableCapacity': '299463129088', 'phyDriveType': 'sas', 'removed': False,
                 'id': '010000005000C500551EAC230000000000000000'},
                {'available': False, 'pfa': False, 'driveMediaType': 'hdd', 'uncertified': False,
                 'protectionInformationCapabilities': {'protectionInformationCapable': True,
                                                       'protectionType': 'type2Protection'}, 'fdeCapable': True,
                 'currentVolumeGroupRef': '04000000600A098000A4B28D000017805C7BD4D8', 'invalidDriveData': False,
                 'nonRedundantAccess': False, 'hotSpare': False, 'status': 'optimal', 'rawCapacity': '300000000000',
                 'usableCapacity': '299463129088', 'phyDriveType': 'sas', 'removed': False,
                 'id': '010000005000C500551EA0BB0000000000000000'},
                {'available': False, 'pfa': False, 'driveMediaType': 'hdd', 'uncertified': False,
                 'protectionInformationCapabilities': {'protectionInformationCapable': True,
                                                       'protectionType': 'type2Protection'}, 'fdeCapable': True,
                 'currentVolumeGroupRef': '04000000600A098000A4B28D000017805C7BD4D8', 'invalidDriveData': False,
                 'nonRedundantAccess': False, 'hotSpare': False, 'status': 'optimal', 'rawCapacity': '300000000000',
                 'usableCapacity': '299463129088', 'phyDriveType': 'sas', 'removed': False,
                 'id': '010000005000C500551EAC4B0000000000000000'}])

    def test_get_ddp_capacity(self):
        """Evaluate returned capacity from get_ddp_capacity method."""
        with patch(self.DRIVES_PROPERTY, new_callable=PropertyMock) as drives:
            drives.return_value = self.DRIVES_DATA

            storagepool = self._initialize_dummy_instance(
                {"state": "present", "name": "pool", "criteria_drive_count": "12", "raid_level": "raidDiskPool"})
            storagepool.pool_detail = self.STORAGE_POOL_DATA[0]
            self.assertAlmostEqual(storagepool.get_ddp_capacity(self.EXPANSION_DDP_DRIVES_LIST), 6038680353645,
                                   places=-2)  # Allows for python version/architecture computational differences

    def test_get_candidate_drives(self):
        """Verify correct candidate list is returned."""
        with patch(self.NETAPP_REQUEST_FUNC) as netapp_request:
            netapp_request.return_value = (200, self.RAID6_CANDIDATE_DRIVES)
            with patch(self.DRIVES_PROPERTY, new_callable=PropertyMock) as drives:
                drives.return_value = self.DRIVES_DATA

                storagepool = self._initialize_dummy_instance(
                    {"state": "present", "name": "raid6_vg", "criteria_drive_count": "6", "raid_level": "raid6"})
                self.assertEqual(storagepool.get_candidate_drives(),
                                 {'candidateSelectionType': 'count', 'driveMediaType': 'hdd',
                                  'protectionInformationCapabilities': {'protectionInformationCapable': True,
                                                                        'protectionType': 'type2Protection'},
                                  'dssPreallocEnabled': False, 'phyDriveType': 'sas', 'allocateReservedSpace': False,
                                  'trayLossProtection': False, 'raidLevel': 'raid6', 'spindleSpeed': 10000,
                                  'securityType': 'capable', 'securityLevel': 'fde', 'spindleSpeedMatch': True,
                                  'driveBlockFormat': 'allNative', 'protectionInformationCapable': False,
                                  'freeExtentRef': '0000000000000000000000000000000000000000', 'driveCount': 6,
                                  'driveRefList': {'driveRef': ['010000005000C500551E7F2B0000000000000000',
                                                                '010000005000C500551EC9270000000000000000',
                                                                '010000005000C500551EC97F0000000000000000',
                                                                '010000005000C500551ECBFF0000000000000000',
                                                                '010000005000C500551E9ED30000000000000000',
                                                                '010000005000C500551EA4CF0000000000000000']},
                                  'rawSize': '1197852491776', 'usableSize': '1197851279360',
                                  'drawerLossProtection': False,
                                  'volumeCandidateData': {'type': 'traditional', 'diskPoolVolumeCandidateData': None}})

    def test_get_expansion_candidate_drives(self):
        """Verify correct drive list is returned"""
        with patch(self.NETAPP_REQUEST_FUNC) as netapp_request:
            netapp_request.return_value = (200, self.EXPANSION_DDP_DRIVE_DATA)
            with patch(self.DRIVES_PROPERTY, new_callable=PropertyMock) as drives:
                drives.return_value = self.DRIVES_DATA

                storagepool = self._initialize_dummy_instance(
                    {"state": "present", "name": "pool", "criteria_drive_count": "20", "raid_level": "raidDiskPool"})
                storagepool.pool_detail = self.STORAGE_POOL_DATA[0]
                self.assertEqual(storagepool.get_expansion_candidate_drives(), [
                    {'drawerLossProtection': False, 'trayLossProtection': False,
                     'drives': ['010000005000C500551E7F2B0000000000000000', '010000005000C500551E99230000000000000000',
                                '010000005000C500551E9ED30000000000000000', '010000005000C500551EA29F0000000000000000',
                                '010000005000C500551EA4CF0000000000000000', '010000005000C500551EC9270000000000000000'],
                     'spindleSpeedMatch': True, 'driveBlockFormat': 'allNative', 'usableCapacity': '1796778774528',
                     'wastedCapacity': '0'}])

    def test_get_maximum_reserve_drive_count(self):
        """Ensure maximum reserve drive count is accurately calculated."""
        with patch(self.NETAPP_REQUEST_FUNC) as netapp_request:
            netapp_request.return_value = (200, self.EXPANSION_DDP_DRIVE_DATA)
            with patch(self.DRIVES_PROPERTY, new_callable=PropertyMock) as drives:
                drives.return_value = self.DRIVES_DATA

                storagepool = self._initialize_dummy_instance(
                    {"state": "present", "name": "pool", "criteria_drive_count": "20", "raid_level": "raidDiskPool"})
                storagepool.pool_detail = self.STORAGE_POOL_DATA[0]
                self.assertEqual(storagepool.get_maximum_reserve_drive_count(), 5)

    def test_apply_check_mode_unchange(self):
        """Verify that the changes are appropriately determined."""
        # Absent storage pool required to be absent
        with self.assertRaisesRegexp(AnsibleExitJson, "'changed': False"):
            with patch(self.DRIVES_PROPERTY, new_callable=PropertyMock) as drives:
                drives.return_value = self.DRIVES_DATA
                with patch(self.STORAGE_POOL_PROPERTY, new_callable=PropertyMock) as storage_pool:
                    storage_pool.return_value = {}
                    storagepool = self._initialize_dummy_instance(
                        {"state": "absent", "name": "not-a-pool", "erase_secured_drives": False,
                         "criteria_drive_count": "14", "raid_level": "raidDiskPool"})
                    storagepool.module.check_mode = True
                    storagepool.is_drive_count_valid = lambda x: True
                    storagepool.apply()

        # Present storage pool with no changes
        with self.assertRaisesRegexp(AnsibleExitJson, "'changed': False"):
            with patch(self.DRIVES_PROPERTY, new_callable=PropertyMock) as drives:
                drives.return_value = self.DRIVES_DATA
                with patch(self.STORAGE_POOL_PROPERTY, new_callable=PropertyMock) as storage_pool:
                    storage_pool.return_value = self.STORAGE_POOL_DATA[0]
                    storagepool = self._initialize_dummy_instance(
                        {"state": "present", "name": "pool", "erase_secured_drives": False,
                         "criteria_drive_count": "14", "raid_level": "raidDiskPool"})
                    storagepool.module.check_mode = True
                    storagepool.is_drive_count_valid = lambda x: True
                    storagepool.apply()

    def test_apply_check_mode_change(self):
        """Verify that the changes are appropriately determined."""
        # Remove absent storage pool
        with self.assertRaisesRegexp(AnsibleExitJson, "'changed': True"):
            with patch(self.DRIVES_PROPERTY, new_callable=PropertyMock) as drives:
                drives.return_value = self.DRIVES_DATA
                with patch(self.STORAGE_POOL_PROPERTY, new_callable=PropertyMock) as storage_pool:
                    storage_pool.return_value = self.STORAGE_POOL_DATA[0]
                    storagepool = self._initialize_dummy_instance(
                        {"state": "absent", "name": "pool", "erase_secured_drives": False, "criteria_drive_count": "14",
                         "raid_level": "raidDiskPool"})
                    storagepool.module.check_mode = True
                    storagepool.is_drive_count_valid = lambda x: True
                    storagepool.apply()

        # Expand present storage pool
        with self.assertRaisesRegexp(AnsibleExitJson, "'changed': True"):
            with patch(self.DRIVES_PROPERTY, new_callable=PropertyMock) as drives:
                drives.return_value = self.DRIVES_DATA
                with patch(self.STORAGE_POOL_PROPERTY, new_callable=PropertyMock) as storage_pool:
                    storage_pool.return_value = self.STORAGE_POOL_DATA[0]
                    storagepool = self._initialize_dummy_instance(
                        {"state": "present", "name": "pool", "erase_secured_drives": False,
                         "criteria_drive_count": "15", "raid_level": "raidDiskPool"})
                    storagepool.module.check_mode = True
                    storagepool.is_drive_count_valid = lambda x: True
                    storagepool.expand_storage_pool = lambda check_mode: (True, 100)
                    storagepool.migrate_raid_level = lambda check_mode: False
                    storagepool.secure_storage_pool = lambda check_mode: False
                    storagepool.set_reserve_drive_count = lambda check_mode: False
                    storagepool.apply()

        # Migrate present storage pool raid level
        with self.assertRaisesRegexp(AnsibleExitJson, "'changed': True"):
            with patch(self.DRIVES_PROPERTY, new_callable=PropertyMock) as drives:
                drives.return_value = self.DRIVES_DATA
                with patch(self.STORAGE_POOL_PROPERTY, new_callable=PropertyMock) as storage_pool:
                    storage_pool.return_value = self.STORAGE_POOL_DATA[0]
                    storagepool = self._initialize_dummy_instance(
                        {"state": "present", "name": "pool", "erase_secured_drives": False,
                         "criteria_drive_count": "15", "raid_level": "raidDiskPool"})
                    storagepool.module.check_mode = True
                    storagepool.is_drive_count_valid = lambda x: True
                    storagepool.expand_storage_pool = lambda check_mode: (False, 0)
                    storagepool.migrate_raid_level = lambda check_mode: True
                    storagepool.secure_storage_pool = lambda check_mode: False
                    storagepool.set_reserve_drive_count = lambda check_mode: False
                    storagepool.apply()

        # Secure present storage pool
        with self.assertRaisesRegexp(AnsibleExitJson, "'changed': True"):
            with patch(self.DRIVES_PROPERTY, new_callable=PropertyMock) as drives:
                drives.return_value = self.DRIVES_DATA
                with patch(self.STORAGE_POOL_PROPERTY, new_callable=PropertyMock) as storage_pool:
                    storage_pool.return_value = self.STORAGE_POOL_DATA[0]
                    storagepool = self._initialize_dummy_instance(
                        {"state": "present", "name": "pool", "erase_secured_drives": False,
                         "criteria_drive_count": "15", "raid_level": "raidDiskPool"})
                    storagepool.module.check_mode = True
                    storagepool.is_drive_count_valid = lambda x: True
                    storagepool.expand_storage_pool = lambda check_mode: (False, 0)
                    storagepool.migrate_raid_level = lambda check_mode: False
                    storagepool.secure_storage_pool = lambda check_mode: True
                    storagepool.set_reserve_drive_count = lambda check_mode: False
                    storagepool.apply()

        # Change present storage pool reserve drive count
        with self.assertRaisesRegexp(AnsibleExitJson, "'changed': True"):
            with patch(self.DRIVES_PROPERTY, new_callable=PropertyMock) as drives:
                drives.return_value = self.DRIVES_DATA
                with patch(self.STORAGE_POOL_PROPERTY, new_callable=PropertyMock) as storage_pool:
                    storage_pool.return_value = self.STORAGE_POOL_DATA[0]
                    storagepool = self._initialize_dummy_instance(
                        {"state": "present", "name": "pool", "erase_secured_drives": False,
                         "criteria_drive_count": "15", "raid_level": "raidDiskPool"})
                    storagepool.module.check_mode = True
                    storagepool.is_drive_count_valid = lambda x: True
                    storagepool.expand_storage_pool = lambda check_mode: (False, 0)
                    storagepool.migrate_raid_level = lambda check_mode: False
                    storagepool.secure_storage_pool = lambda check_mode: False
                    storagepool.set_reserve_drive_count = lambda check_mode: True
                    storagepool.apply()
