#!/usr/bin/python

# (c) 2016, NetApp, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

ANSIBLE_METADATA = {"metadata_version": "1.1",
                    "status": ["preview"],
                    "supported_by": "community"}

DOCUMENTATION = """
---
module: netapp_e_storagepool
short_description: NetApp E-Series manage volume groups and disk pools
description: Create or remove volume groups and disk pools for NetApp E-series storage arrays.
version_added: '2.2'
author:
  - Kevin Hulquest (@hulquest)
  - Nathan Swartz (@ndswartz)
extends_documentation_fragment:
  - netapp.eseries
options:
  state:
    description:
      - Whether the specified storage pool should exist or not.
      - Note that removing a storage pool currently requires the removal of all defined volumes first.
    required: true
    choices: ["present", "absent"]
  name:
    description:
      - The name of the storage pool to manage
    required: true
  criteria_drive_count:
    description:
      - The number of disks to use for building the storage pool.
      - When I(state=="present") then I(criteria_drive_count) or I(criteria_min_usable_capacity) must be specified.
      - The pool will be expanded if this number exceeds the number of disks already in place (See expansion note below)
    required: false
    type: int
  criteria_min_usable_capacity:
    description:
      - The minimum size of the storage pool (in size_unit).
      - When I(state=="present") then I(criteria_drive_count) or I(criteria_min_usable_capacity) must be specified.
      - The pool will be expanded if this value exceeds its current size. (See expansion note below)
    required: false
    type: float
  criteria_drive_type:
    description:
      - The type of disk (hdd or ssd) to use when searching for candidates to use.
      - When not specified each drive type will be evaluated until successful drive candidates are found starting with
        the most prevalent drive type.
    required: false
    choices: ["hdd","ssd"]
  criteria_size_unit:
    description:
      - The unit used to interpret size parameters
    choices: ["bytes", "b", "kb", "mb", "gb", "tb", "pb", "eb", "zb", "yb"]
    default: "gb"
  criteria_drive_min_size:
    description:
      - The minimum individual drive size (in size_unit) to consider when choosing drives for the storage pool.
  criteria_drive_interface_type:
    description:
      - The interface type to use when selecting drives for the storage pool
      - If not provided then all interface types will be considered.
    choices: ["sas", "sas4k", "fibre", "fibre520b", "scsi", "sata", "pata"]
    required: false
  criteria_drive_require_da:
    description:
      - Ensures the storage pool will be created with only data assurance (DA) capable drives.
      - Only available for new storage pools; existing storage pools cannot be converted.
    default: false
    type: bool
    version_added: '2.9'
  criteria_drive_require_fde:
    description:
     - Whether full disk encryption ability is required for drives to be added to the storage pool
    default: false
    type: bool
  raid_level:
    description:
      - The RAID level of the storage pool to be created.
      - Required only when I(state=="present").
      - When I(raid_level=="raidDiskPool") then I(criteria_drive_count >= 10 or criteria_drive_count >= 11) is required
        depending on the storage array specifications.
      - When I(raid_level=="raid0") then I(1<=criteria_drive_count) is required.
      - When I(raid_level=="raid1") then I(2<=criteria_drive_count) is required.
      - When I(raid_level=="raid3") then I(3<=criteria_drive_count<=30) is required.
      - When I(raid_level=="raid5") then I(3<=criteria_drive_count<=30) is required.
      - When I(raid_level=="raid6") then I(5<=criteria_drive_count<=30) is required.
      - Note that raidAll will be treated as raidDiskPool and raid3 as raid5.
    required: false
    choices: ["raidAll", "raid0", "raid1", "raid3", "raid5", "raid6", "raidDiskPool"]
    default: "raidDiskPool"
  secure_pool:
    description:
      - Enables security at rest feature on the storage pool.
      - Will only work if all drives in the pool are security capable (FDE, FIPS, or mix)
      - Warning, once security is enabled it is impossible to disable without erasing the drives.
    required: false
    type: bool
  reserve_drive_count:
    description:
      - Set the number of drives reserved by the storage pool for reconstruction operations.
      - Only valid on raid disk pools.
    required: false
  remove_volumes:
    description:
    - Prior to removing a storage pool, delete all volumes in the pool.
    default: true
  erase_secured_drives:
    description:
      - If I(state=="absent") then all storage pool drives will be erase
      - If I(state=="present") then delete all available storage array drives that have security enabled.
    default: true
    type: bool
notes:
  - The expansion operations are non-blocking due to the time consuming nature of expanding volume groups
  - Traditional volume groups (raid0, raid1, raid5, raid6) are performed in steps dictated by the storage array. Each
    required step will be attempted until the request fails which is likely because of the required expansion time.
  - raidUnsupported will be treated as raid0, raidAll as raidDiskPool and raid3 as raid5.
  - Tray loss protection and drawer loss protection will be chosen if at all possible.
"""
EXAMPLES = """
- name: No disk groups
  netapp_e_storagepool:
    ssid: "{{ ssid }}"
    name: "{{ item }}"
    state: absent
    api_url: "{{ netapp_api_url }}"
    api_username: "{{ netapp_api_username }}"
    api_password: "{{ netapp_api_password }}"
    validate_certs: "{{ netapp_api_validate_certs }}"
"""
RETURN = """
msg:
    description: Success message
    returned: success
    type: str
    sample: Json facts for the pool that was created.
"""
import functools
from itertools import groupby
from time import sleep
from pprint import pformat
from ansible.module_utils.netapp import NetAppESeriesModule
from ansible.module_utils._text import to_native


def get_most_common_elements(iterator):
    """Returns a generator containing a descending list of most common elements."""
    if not isinstance(iterator, list):
        raise TypeError("iterator must be a list.")

    grouped = [(key, len(list(group))) for key, group in groupby(sorted(iterator))]
    return sorted(grouped, key=lambda x: x[1], reverse=True)


def memoize(func):
    """Generic memoizer for any function with any number of arguments including zero."""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        class MemoizeFuncArgs(dict):
            def __missing__(self, _key):
                self[_key] = func(*args, **kwargs)
                return self[_key]

        key = str((args, kwargs)) if args and kwargs else "no_argument_response"
        return MemoizeFuncArgs().__getitem__(key)

    return wrapper


class NetAppESeriesStoragePool(NetAppESeriesModule):
    EXPANSION_TIMEOUT_SEC = 10
    DEFAULT_DISK_POOL_MINIMUM_DISK_COUNT = 11

    def __init__(self):
        version = "02.00.0000.0000"
        ansible_options = dict(
            state=dict(required=True, choices=["present", "absent"], type="str"),
            name=dict(required=True, type="str"),
            criteria_size_unit=dict(choices=["bytes", "b", "kb", "mb", "gb", "tb", "pb", "eb", "zb", "yb"],
                                    default="gb", type="str"),
            criteria_drive_count=dict(type="int"),
            criteria_drive_interface_type=dict(choices=["sas", "sas4k", "fibre", "fibre520b", "scsi", "sata", "pata"],
                                               type="str"),
            criteria_drive_type=dict(choices=["ssd", "hdd"], type="str", required=False),
            criteria_drive_min_size=dict(type="float"),
            criteria_drive_require_da=dict(type="bool", required=False),
            criteria_drive_require_fde=dict(type="bool", required=False),
            criteria_min_usable_capacity=dict(type="float"),
            raid_level=dict(choices=["raidAll", "raid0", "raid1", "raid3", "raid5", "raid6", "raidDiskPool"],
                            default="raidDiskPool"),
            erase_secured_drives=dict(type="bool", default=True),
            secure_pool=dict(type="bool", default=False),
            reserve_drive_count=dict(type="int"),
            remove_volumes=dict(type="bool", default=True))

        required_if = [["state", "present", ["raid_level"]]]
        super(NetAppESeriesStoragePool, self).__init__(ansible_options=ansible_options,
                                                       web_services_version=version,
                                                       supports_check_mode=True,
                                                       required_if=required_if)

        args = self.module.params
        self.state = args["state"]
        self.ssid = args["ssid"]
        self.name = args["name"]
        self.criteria_drive_count = args["criteria_drive_count"]
        self.criteria_min_usable_capacity = args["criteria_min_usable_capacity"]
        self.criteria_size_unit = args["criteria_size_unit"]
        self.criteria_drive_min_size = args["criteria_drive_min_size"]
        self.criteria_drive_type = args["criteria_drive_type"]
        self.criteria_drive_interface_type = args["criteria_drive_interface_type"]
        self.criteria_drive_require_fde = args["criteria_drive_require_fde"]
        self.criteria_drive_require_da = args["criteria_drive_require_da"]
        self.raid_level = args["raid_level"]
        self.erase_secured_drives = args["erase_secured_drives"]
        self.secure_pool = args["secure_pool"]
        self.reserve_drive_count = args["reserve_drive_count"]
        self.remove_volumes = args["remove_volumes"]
        self.pool_detail = None

        # Change all sizes to be measured in bytes
        if self.criteria_min_usable_capacity:
            self.criteria_min_usable_capacity = int(self.criteria_min_usable_capacity *
                                                    self.SIZE_UNIT_MAP[self.criteria_size_unit])
        if self.criteria_drive_min_size:
            self.criteria_drive_min_size = int(self.criteria_drive_min_size *
                                               self.SIZE_UNIT_MAP[self.criteria_size_unit])
        self.criteria_size_unit = "bytes"

        # Adjust unused raid level option to reflect documentation
        if self.raid_level == "raidAll":
            self.raid_level = "raidDiskPool"
        if self.raid_level == "raid3":
            self.raid_level = "raid5"

    @property
    @memoize
    def available_drives(self):
        """Determine the list of available drives"""
        return [drive["id"] for drive in self.drives if drive["available"] and drive["status"] == "optimal"]

    @property
    @memoize
    def available_drive_types(self):
        """Determine the types of available drives sorted by the most common first."""
        types = [drive["driveMediaType"] for drive in self.drives]
        return [entry[0] for entry in get_most_common_elements(types)]

    @property
    @memoize
    def available_drive_interface_types(self):
        """Determine the types of available drives."""
        interfaces = [drive["phyDriveType"] for drive in self.drives]
        return [entry[0] for entry in get_most_common_elements(interfaces)]

    @property
    def storage_pool_drives(self, exclude_hotspares=True):
        """Retrieve list of drives found in storage pool."""
        if exclude_hotspares:
            return [drive for drive in self.drives
                    if drive["currentVolumeGroupRef"] == self.pool_detail["id"] and not drive["hotSpare"]]

        return [drive for drive in self.drives if drive["currentVolumeGroupRef"] == self.pool_detail["id"]]

    @property
    def expandable_drive_count(self):
        """Maximum number of drives that a storage pool can be expanded at a given time."""
        capabilities = None
        if self.raid_level == "raidDiskPool":
            return len(self.available_drives)

        try:
            rc, capabilities = self.request("storage-systems/%s/capabilities" % self.ssid)
        except Exception as error:
            self.module.fail_json(msg="Failed to fetch maximum expandable drive count. Array id [%s].  Error[%s]."
                                      % (self.ssid, to_native(error)))

        return capabilities["featureParameters"]["maxDCEDrives"]

    @property
    def disk_pool_drive_minimum(self):
        """Provide the storage array's minimum disk pool drive count."""
        rc, attr = self.request("storage-systems/%s/symbol/getSystemAttributeDefaults" % self.ssid, ignore_errors=True)

        # Standard minimum is 11 drives but some allow 10 drives. 10 will be the default
        if (rc != 200 or "minimumDriveCount" not in attr["defaults"]["diskPoolDefaultAttributes"].keys() or
                attr["defaults"]["diskPoolDefaultAttributes"]["minimumDriveCount"] == 0):
            return self.DEFAULT_DISK_POOL_MINIMUM_DISK_COUNT

        return attr["defaults"]["diskPoolDefaultAttributes"]["minimumDriveCount"]

    def get_available_drive_capacities(self, drive_id_list=None):
        """Determine the list of available drive capacities."""
        if drive_id_list:
            available_drive_capacities = set([int(drive["usableCapacity"]) for drive in self.drives
                                              if drive["id"] in drive_id_list and drive["available"] and
                                              drive["status"] == "optimal"])
        else:
            available_drive_capacities = set([int(drive["usableCapacity"]) for drive in self.drives
                                              if drive["available"] and drive["status"] == "optimal"])

        self.module.log("available drive capacities: %s" % available_drive_capacities)
        return list(available_drive_capacities)

    @property
    def drives(self):
        """Retrieve list of drives found in storage pool."""
        drives = None
        try:
            rc, drives = self.request("storage-systems/%s/drives" % self.ssid)
        except Exception as error:
            self.module.fail_json(msg="Failed to fetch disk drives. Array id [%s].  Error[%s]."
                                      % (self.ssid, to_native(error)))

        return drives

    def is_drive_count_valid(self, drive_count):
        """Validate drive count criteria is met."""
        if self.criteria_drive_count and drive_count < self.criteria_drive_count:
            return False

        if self.raid_level == "raidDiskPool":
            return drive_count >= self.disk_pool_drive_minimum
        if self.raid_level == "raid0":
            return drive_count > 0
        if self.raid_level == "raid1":
            return drive_count >= 2 and (drive_count % 2) == 0
        if self.raid_level in ["raid3", "raid5"]:
            return 3 <= drive_count <= 30
        if self.raid_level == "raid6":
            return 5 <= drive_count <= 30
        return False

    @property
    def storage_pool(self):
        """Retrieve storage pool information."""
        storage_pools_resp = None
        try:
            rc, storage_pools_resp = self.request("storage-systems/%s/storage-pools" % self.ssid)
        except Exception as err:
            self.module.fail_json(msg="Failed to get storage pools. Array id [%s]. Error[%s]. State[%s]."
                                      % (self.ssid, to_native(err), self.state))

        pool_detail = [pool for pool in storage_pools_resp if pool["name"] == self.name]
        return pool_detail[0] if pool_detail else dict()

    @property
    def storage_pool_volumes(self):
        """Retrieve list of volumes associated with storage pool."""
        volumes_resp = None
        try:
            rc, volumes_resp = self.request("storage-systems/%s/volumes" % self.ssid)
        except Exception as err:
            self.module.fail_json(msg="Failed to get storage pools. Array id [%s]. Error[%s]. State[%s]."
                                      % (self.ssid, to_native(err), self.state))

        group_ref = self.storage_pool["volumeGroupRef"]
        storage_pool_volume_list = [volume["id"] for volume in volumes_resp if volume["volumeGroupRef"] == group_ref]
        return storage_pool_volume_list

    def get_ddp_capacity(self, expansion_drive_list):
        """Return the total usable capacity based on the additional drives."""

        def get_ddp_error_percent(_drive_count, _extent_count):
            """Determine the space reserved for reconstruction"""
            if _drive_count <= 36:
                if _extent_count <= 600:
                    return 0.40
                elif _extent_count <= 1400:
                    return 0.35
                elif _extent_count <= 6200:
                    return 0.20
                elif _extent_count <= 50000:
                    return 0.15
            elif _drive_count <= 64:
                if _extent_count <= 600:
                    return 0.20
                elif _extent_count <= 1400:
                    return 0.15
                elif _extent_count <= 6200:
                    return 0.10
                elif _extent_count <= 50000:
                    return 0.05
            elif _drive_count <= 480:
                if _extent_count <= 600:
                    return 0.20
                elif _extent_count <= 1400:
                    return 0.15
                elif _extent_count <= 6200:
                    return 0.10
                elif _extent_count <= 50000:
                    return 0.05

            self.module.fail_json(msg="Drive count exceeded the error percent table. Array[%s]" % self.ssid)

        def get_ddp_reserved_drive_count(_disk_count):
            """Determine the number of reserved drive."""
            reserve_count = 0

            if self.reserve_drive_count:
                reserve_count = self.reserve_drive_count
            elif _disk_count >= 256:
                reserve_count = 8
            elif _disk_count >= 192:
                reserve_count = 7
            elif _disk_count >= 128:
                reserve_count = 6
            elif _disk_count >= 64:
                reserve_count = 4
            elif _disk_count >= 32:
                reserve_count = 3
            elif _disk_count >= 12:
                reserve_count = 2
            elif _disk_count == 11:
                reserve_count = 1

            return reserve_count

        if self.pool_detail:
            drive_count = len(self.storage_pool_drives) + len(expansion_drive_list)
        else:
            drive_count = len(expansion_drive_list)

        drive_usable_capacity = min(min(self.get_available_drive_capacities()),
                                    min(self.get_available_drive_capacities(expansion_drive_list)))
        drive_data_extents = ((drive_usable_capacity - 8053063680) / 536870912)
        maximum_stripe_count = (drive_count * drive_data_extents) / 10

        error_percent = get_ddp_error_percent(drive_count, drive_data_extents)
        error_overhead = (drive_count * drive_data_extents / 10 * error_percent + 10) / 10

        total_stripe_count = maximum_stripe_count - error_overhead
        stripe_count_per_drive = total_stripe_count / drive_count
        reserved_stripe_count = get_ddp_reserved_drive_count(drive_count) * stripe_count_per_drive
        available_stripe_count = total_stripe_count - reserved_stripe_count

        return available_stripe_count * 4294967296

    @memoize
    def get_candidate_drives(self):
        """Retrieve set of drives candidates for creating a new storage pool."""

        def get_candidate_drive_request():
            """Perform request for new volume creation."""
            candidates_list = list()
            drive_types = [self.criteria_drive_type] if self.criteria_drive_type else self.available_drive_types
            interface_types = [self.criteria_drive_interface_type] \
                if self.criteria_drive_interface_type else self.available_drive_interface_types

            for interface_type in interface_types:
                for drive_type in drive_types:
                    candidates = None
                    volume_candidate_request_data = dict(
                        type="diskPool" if self.raid_level == "raidDiskPool" else "traditional",
                        diskPoolVolumeCandidateRequestData=dict(
                            reconstructionReservedDriveCount=65535))
                    candidate_selection_type = dict(
                        candidateSelectionType="count",
                        driveRefList=dict(driveRef=self.available_drives))
                    criteria = dict(raidLevel=self.raid_level,
                                    phyDriveType=interface_type,
                                    dssPreallocEnabled=False,
                                    securityType="capable" if self.criteria_drive_require_fde else "none",
                                    driveMediaType=drive_type,
                                    onlyProtectionInformationCapable=True if self.criteria_drive_require_da else False,
                                    volumeCandidateRequestData=volume_candidate_request_data,
                                    allocateReserveSpace=False,
                                    securityLevel="fde" if self.criteria_drive_require_fde else "none",
                                    candidateSelectionType=candidate_selection_type)

                    try:
                        rc, candidates = self.request("storage-systems/%s/symbol/getVolumeCandidates?verboseError"
                                                      "Response=true" % self.ssid, data=criteria, method="POST")
                    except Exception as error:
                        self.module.fail_json(msg="Failed to retrieve volume candidates. Array [%s]. Error [%s]."
                                                  % (self.ssid, to_native(error)))

                    if candidates:
                        candidates_list.extend(candidates["volumeCandidate"])

            # Sort output based on tray and then drawer protection first
            tray_drawer_protection = list()
            tray_protection = list()
            drawer_protection = list()
            no_protection = list()
            sorted_candidates = list()
            for item in candidates_list:
                if item["trayLossProtection"]:
                    if item["drawerLossProtection"]:
                        tray_drawer_protection.append(item)
                    else:
                        tray_protection.append(item)
                elif item["drawerLossProtection"]:
                    drawer_protection.append(item)
                else:
                    no_protection.append(item)

            if tray_drawer_protection:
                sorted_candidates.extend(tray_drawer_protection)
            if tray_protection:
                sorted_candidates.extend(tray_protection)
            if drawer_protection:
                sorted_candidates.extend(drawer_protection)
            if no_protection:
                sorted_candidates.extend(no_protection)

            return sorted_candidates

        # Determine the appropriate candidate list
        for candidate in get_candidate_drive_request():

            # Evaluate candidates for required drive count, collective drive usable capacity and minimum drive size
            if self.criteria_drive_count:
                if self.criteria_drive_count != int(candidate["driveCount"]):
                    continue
            if self.criteria_min_usable_capacity:
                if ((self.raid_level == "raidDiskPool" and self.criteria_min_usable_capacity >
                     self.get_ddp_capacity(candidate["driveRefList"]["driveRef"])) or
                        self.criteria_min_usable_capacity > int(candidate["usableSize"])):
                    continue
            if self.criteria_drive_min_size:
                if self.criteria_drive_min_size > min(self.get_available_drive_capacities(candidate["driveRefList"]["driveRef"])):
                    continue

            return candidate

        self.module.fail_json(msg="Not enough drives to meet the specified criteria. Array [%s]." % self.ssid)

    @memoize
    def get_expansion_candidate_drives(self):
        """Retrieve required expansion drive list.

        Note: To satisfy the expansion criteria each item in the candidate list must added specified group since there
        is a potential limitation on how many drives can be incorporated at a time.
            * Traditional raid volume groups must be added two drives maximum at a time. No limits on raid disk pools.

        :return list(candidate): list of candidate structures from the getVolumeGroupExpansionCandidates symbol endpoint
        """

        def get_expansion_candidate_drive_request():
            """Perform the request for expanding existing volume groups or disk pools.

            Note: the list of candidate structures do not necessarily produce candidates that meet all criteria.
            """
            candidates_list = None
            url = "storage-systems/%s/symbol/getVolumeGroupExpansionCandidates?verboseErrorResponse=true" % self.ssid
            if self.raid_level == "raidDiskPool":
                url = "storage-systems/%s/symbol/getDiskPoolExpansionCandidates?verboseErrorResponse=true" % self.ssid

            try:
                rc, candidates_list = self.request(url, method="POST", data=self.pool_detail["id"])
            except Exception as error:
                self.module.fail_json(msg="Failed to retrieve volume candidates. Array [%s]. Error [%s]."
                                          % (self.ssid, to_native(error)))

            return candidates_list["candidates"]

        required_candidate_list = list()
        required_additional_drives = 0
        required_additional_capacity = 0
        total_required_capacity = 0

        # determine whether and how much expansion is need to satisfy the specified criteria
        if self.criteria_min_usable_capacity:
            total_required_capacity = self.criteria_min_usable_capacity
            required_additional_capacity = self.criteria_min_usable_capacity - int(self.pool_detail["totalRaidedSpace"])

        if self.criteria_drive_count:
            required_additional_drives = self.criteria_drive_count - len(self.storage_pool_drives)

        # Determine the appropriate expansion candidate list
        if required_additional_drives > 0 or required_additional_capacity > 0:
            for candidate in get_expansion_candidate_drive_request():

                if self.criteria_drive_min_size:
                    if self.criteria_drive_min_size > min(self.get_available_drive_capacities(candidate["drives"])):
                        continue

                if self.raid_level == "raidDiskPool":
                    if (len(candidate["drives"]) >= required_additional_drives and
                            self.get_ddp_capacity(candidate["drives"]) >= total_required_capacity):
                        required_candidate_list.append(candidate)
                        break
                else:
                    required_additional_drives -= len(candidate["drives"])
                    required_additional_capacity -= int(candidate["usableCapacity"])
                    required_candidate_list.append(candidate)

                # Determine if required drives and capacities are satisfied
                if required_additional_drives <= 0 and required_additional_capacity <= 0:
                    break
            else:
                self.module.fail_json(msg="Not enough drives to meet the specified criteria. Array [%s]." % self.ssid)

        return required_candidate_list

    def get_reserve_drive_count(self):
        """Retrieve the current number of reserve drives for raidDiskPool (Only for raidDiskPool)."""

        if not self.pool_detail:
            self.module.fail_json(msg="The storage pool must exist. Array [%s]." % self.ssid)

        if self.raid_level != "raidDiskPool":
            self.module.fail_json(msg="The storage pool must be a raidDiskPool. Pool [%s]. Array [%s]."
                                      % (self.pool_detail["id"], self.ssid))

        return self.pool_detail["volumeGroupData"]["diskPoolData"]["reconstructionReservedDriveCount"]

    def get_maximum_reserve_drive_count(self):
        """Retrieve the maximum number of reserve drives for storage pool (Only for raidDiskPool)."""
        if self.raid_level != "raidDiskPool":
            self.module.fail_json(msg="The storage pool must be a raidDiskPool. Pool [%s]. Array [%s]."
                                      % (self.pool_detail["id"], self.ssid))

        drives_ids = list()

        if self.pool_detail:
            drives_ids.extend(self.storage_pool_drives)
            for candidate in self.get_expansion_candidate_drives():
                drives_ids.extend((candidate["drives"]))
        else:
            candidate = self.get_candidate_drives()
            drives_ids.extend(candidate["driveRefList"]["driveRef"])

        drive_count = len(drives_ids)
        maximum_reserve_drive_count = min(int(drive_count * 0.2 + 1), drive_count - 10)
        if maximum_reserve_drive_count > 10:
            maximum_reserve_drive_count = 10

        return maximum_reserve_drive_count

    def set_reserve_drive_count(self, check_mode=False):
        """Set the reserve drive count for raidDiskPool."""
        changed = False

        if self.raid_level == "raidDiskPool" and self.reserve_drive_count:
            maximum_count = self.get_maximum_reserve_drive_count()

            if self.reserve_drive_count < 0 or self.reserve_drive_count > maximum_count:
                self.module.fail_json(msg="Supplied reserve drive count is invalid or exceeds the maximum allowed. "
                                          "Note that it may be necessary to wait for expansion operations to complete "
                                          "before the adjusting the reserve drive count. Maximum [%s]. Array [%s]."
                                          % (maximum_count, self.ssid))

            if self.reserve_drive_count != self.get_reserve_drive_count():
                changed = True

            if not check_mode:
                try:
                    rc, resp = self.request("storage-systems/%s/symbol/setDiskPoolReservedDriveCount" % self.ssid,
                                            method="POST", data=dict(volumeGroupRef=self.pool_detail["id"],
                                                                     newDriveCount=self.reserve_drive_count))
                except Exception as error:
                    self.module.fail_json(msg="Failed to set reserve drive count for disk pool. Disk Pool [%s]."
                                              " Array [%s]." % (self.pool_detail["id"], self.ssid))

        return changed

    def erase_all_available_secured_drives(self, check_mode=False):
        """Erase all available drives that have encryption at rest feature enabled."""
        changed = False
        drives_list = list()
        for drive in self.drives:
            if drive["available"] and drive["fdeEnabled"]:
                changed = True
                drives_list.append(drive["id"])

        if drives_list and not check_mode:
            try:
                rc, resp = self.request("storage-systems/%s/symbol/reprovisionDrive?verboseErrorResponse=true"
                                        % self.ssid, method="POST", data=dict(driveRef=drives_list))
            except Exception as error:
                self.module.fail_json(msg="Failed to erase all secured drives. Array [%s]" % self.ssid)

        return changed

    def create_storage_pool(self):
        """Create new storage pool."""
        url = "storage-systems/%s/symbol/createVolumeGroup?verboseErrorResponse=true" % self.ssid
        request_body = dict(label=self.name,
                            candidate=self.get_candidate_drives())

        if self.raid_level == "raidDiskPool":
            url = "storage-systems/%s/symbol/createDiskPool?verboseErrorResponse=true" % self.ssid

            request_body.update(
                dict(backgroundOperationPriority="useDefault",
                     criticalReconstructPriority="useDefault",
                     degradedReconstructPriority="useDefault",
                     poolUtilizationCriticalThreshold=65535,
                     poolUtilizationWarningThreshold=0))

            if self.reserve_drive_count:
                request_body.update(dict(volumeCandidateData=dict(
                    diskPoolVolumeCandidateData=dict(reconstructionReservedDriveCount=self.reserve_drive_count))))

        try:
            rc, resp = self.request(url, method="POST", data=request_body)
        except Exception as error:
            self.module.fail_json(msg="Failed to create storage pool. Array id [%s].  Error[%s]."
                                      % (self.ssid, to_native(error)))

        # Update drive and storage pool information
        self.pool_detail = self.storage_pool

    def delete_storage_pool(self):
        """Delete storage pool."""
        storage_pool_drives = [drive["id"] for drive in self.storage_pool_drives if drive["fdeEnabled"]]
        try:
            delete_volumes_parameter = "?delete-volumes=true" if self.remove_volumes else ""
            rc, resp = self.request("storage-systems/%s/storage-pools/%s%s"
                                    % (self.ssid, self.pool_detail["id"], delete_volumes_parameter), method="DELETE")
        except Exception as error:
            self.module.fail_json(msg="Failed to delete storage pool. Pool id [%s]. Array id [%s].  Error[%s]."
                                      % (self.pool_detail["id"], self.ssid, to_native(error)))

        if storage_pool_drives and self.erase_secured_drives:
            try:
                rc, resp = self.request("storage-systems/%s/symbol/reprovisionDrive?verboseErrorResponse=true"
                                        % self.ssid, method="POST", data=dict(driveRef=storage_pool_drives))
            except Exception as error:
                self.module.fail_json(msg="Failed to erase drives prior to creating new storage pool. Array [%s]."
                                          " Error [%s]." % (self.ssid, to_native(error)))

    def secure_storage_pool(self, check_mode=False):
        """Enable security on an existing storage pool"""
        self.pool_detail = self.storage_pool
        needs_secure_pool = False

        if not self.secure_pool and self.pool_detail["securityType"] == "enabled":
            self.module.fail_json(msg="It is not possible to disable storage pool security! See array documentation.")
        if self.secure_pool and self.pool_detail["securityType"] != "enabled":
            needs_secure_pool = True

        if needs_secure_pool and not check_mode:
            try:
                rc, resp = self.request("storage-systems/%s/storage-pools/%s" % (self.ssid, self.pool_detail["id"]),
                                        data=dict(securePool=True), method="POST")
            except Exception as error:
                self.module.fail_json(msg="Failed to secure storage pool. Pool id [%s]. Array [%s]. Error"
                                          " [%s]." % (self.pool_detail["id"], self.ssid, to_native(error)))

        self.pool_detail = self.storage_pool
        return needs_secure_pool

    def migrate_raid_level(self, check_mode=False):
        """Request storage pool raid level migration."""
        needs_migration = self.raid_level != self.pool_detail["raidLevel"]
        if needs_migration and self.pool_detail["raidLevel"] == "raidDiskPool":
            self.module.fail_json(msg="Raid level cannot be changed for disk pools")

        if needs_migration and not check_mode:
            sp_raid_migrate_req = dict(raidLevel=self.raid_level)

            try:
                rc, resp = self.request("storage-systems/%s/storage-pools/%s/raid-type-migration"
                                        % (self.ssid, self.name), data=sp_raid_migrate_req, method="POST")
            except Exception as error:
                self.module.fail_json(msg="Failed to change the raid level of storage pool. Array id [%s]."
                                          "  Error[%s]." % (self.ssid, to_native(error)))

        self.pool_detail = self.storage_pool
        return needs_migration

    def expand_storage_pool(self, check_mode=False):
        """Add drives to existing storage pool.

        :return bool: whether drives were required to be added to satisfy the specified criteria."""
        expansion_candidate_list = self.get_expansion_candidate_drives()
        changed_required = bool(expansion_candidate_list)
        estimated_completion_time = 0.0

        # build expandable groupings of traditional raid candidate
        required_expansion_candidate_list = list()
        while expansion_candidate_list:
            subset = list()
            while expansion_candidate_list and len(subset) < self.expandable_drive_count:
                subset.extend(expansion_candidate_list.pop()["drives"])
            required_expansion_candidate_list.append(subset)

        if required_expansion_candidate_list and not check_mode:
            url = "storage-systems/%s/symbol/startVolumeGroupExpansion?verboseErrorResponse=true" % self.ssid
            if self.raid_level == "raidDiskPool":
                url = "storage-systems/%s/symbol/startDiskPoolExpansion?verboseErrorResponse=true" % self.ssid

            while required_expansion_candidate_list:
                candidate_drives_list = required_expansion_candidate_list.pop()
                request_body = dict(volumeGroupRef=self.pool_detail["volumeGroupRef"],
                                    driveRef=candidate_drives_list)
                try:
                    rc, resp = self.request(url, method="POST", data=request_body)
                except Exception as error:
                    rc, actions_resp = self.request("storage-systems/%s/storage-pools/%s/action-progress"
                                                    % (self.ssid, self.pool_detail["id"]), ignore_errors=True)
                    if rc == 200 and actions_resp:
                        actions = [action["currentAction"] for action in actions_resp
                                   if action["volumeRef"] in self.storage_pool_volumes]
                        self.module.fail_json(msg="Failed to add drives to the storage pool possibly because of actions"
                                                  " in progress. Actions [%s]. Pool id [%s]. Array id [%s]. Error[%s]."
                                                  % (", ".join(actions), self.pool_detail["id"], self.ssid,
                                                     to_native(error)))

                    self.module.fail_json(msg="Failed to add drives to storage pool. Pool id [%s]. Array id [%s]."
                                              "  Error[%s]." % (self.pool_detail["id"], self.ssid, to_native(error)))

                # Wait for expansion completion unless it is the last request in the candidate list
                if required_expansion_candidate_list:
                    for dummy in range(self.EXPANSION_TIMEOUT_SEC):
                        rc, actions_resp = self.request("storage-systems/%s/storage-pools/%s/action-progress"
                                                        % (self.ssid, self.pool_detail["id"]), ignore_errors=True)
                        if rc == 200:
                            for action in actions_resp:
                                if (action["volumeRef"] in self.storage_pool_volumes and
                                        action["currentAction"] == "remappingDce"):
                                    sleep(1)
                                    estimated_completion_time = action["estimatedTimeToCompletion"]
                                    break
                            else:
                                estimated_completion_time = 0.0
                                break

        return changed_required, estimated_completion_time

    def apply(self):
        """Apply requested state to storage array."""
        changed = False

        if self.state == "present":
            if self.criteria_drive_count is None and self.criteria_min_usable_capacity is None:
                self.module.fail_json(msg="One of criteria_min_usable_capacity or criteria_drive_count must be"
                                          " specified.")
            if self.criteria_drive_count and not self.is_drive_count_valid(self.criteria_drive_count):
                self.module.fail_json(msg="criteria_drive_count must be valid for the specified raid level.")

        self.pool_detail = self.storage_pool
        self.module.log(pformat(self.pool_detail))

        if self.state == "present" and self.erase_secured_drives:
            self.erase_all_available_secured_drives(check_mode=True)

        # Determine whether changes need to be applied to the storage array
        if self.pool_detail:

            if self.state == "absent":
                changed = True

            elif self.state == "present":

                if self.criteria_drive_count and self.criteria_drive_count < len(self.storage_pool_drives):
                    self.module.fail_json(msg="Failed to reduce the size of the storage pool. Array [%s]. Pool [%s]."
                                              % (self.ssid, self.pool_detail["id"]))

                if self.criteria_drive_type and self.criteria_drive_type != self.pool_detail["driveMediaType"]:
                    self.module.fail_json(msg="Failed! It is not possible to modify storage pool media type."
                                              " Array [%s]. Pool [%s]." % (self.ssid, self.pool_detail["id"]))

                if (self.criteria_drive_require_da is not None and self.criteria_drive_require_da !=
                        self.pool_detail["protectionInformationCapabilities"]["protectionInformationCapable"]):
                    self.module.fail_json(msg="Failed! It is not possible to modify DA-capability. Array [%s]."
                                              " Pool [%s]." % (self.ssid, self.pool_detail["id"]))

                # Evaluate current storage pool for required change.
                needs_expansion, estimated_completion_time = self.expand_storage_pool(check_mode=True)
                if needs_expansion:
                    changed = True
                if self.migrate_raid_level(check_mode=True):
                    changed = True
                if self.secure_storage_pool(check_mode=True):
                    changed = True
                if self.set_reserve_drive_count(check_mode=True):
                    changed = True

        elif self.state == "present":
            changed = True

        # Apply changes to storage array
        msg = "No changes were required for the storage pool [%s]."
        if changed and not self.module.check_mode:
            if self.state == "present":
                if self.erase_secured_drives:
                    self.erase_all_available_secured_drives()

                if self.pool_detail:
                    change_list = list()

                    # Expansion needs to occur before raid level migration to account for any sizing needs.
                    expanded, estimated_completion_time = self.expand_storage_pool()
                    if expanded:
                        change_list.append("expanded")
                    if self.migrate_raid_level():
                        change_list.append("raid migration")
                    if self.secure_storage_pool():
                        change_list.append("secured")
                    if self.set_reserve_drive_count():
                        change_list.append("adjusted reserve drive count")

                    if change_list:
                        msg = "Following changes have been applied to the storage pool [%s]: " + ", ".join(change_list)

                    if expanded:
                        msg += "\nThe expansion operation will complete in an estimated %s minutes."\
                               % estimated_completion_time
                else:
                    self.create_storage_pool()
                    msg = "Storage pool [%s] was created."

                    if self.secure_storage_pool():
                        msg = "Storage pool [%s] was created and secured."
                    if self.set_reserve_drive_count():
                        msg += " Adjusted reserve drive count."

            elif self.pool_detail:
                self.delete_storage_pool()
                msg = "Storage pool [%s] removed."

        self.pool_detail = self.storage_pool
        self.module.log(pformat(self.pool_detail))
        self.module.log(msg % self.name)
        self.module.exit_json(msg=msg % self.name, changed=changed, **self.pool_detail)


def main():
    storage_pool = NetAppESeriesStoragePool()
    storage_pool.apply()


if __name__ == "__main__":
    main()
