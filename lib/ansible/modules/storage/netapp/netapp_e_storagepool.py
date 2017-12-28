#!/usr/bin/python

# (c) 2016, NetApp, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: netapp_e_storagepool
short_description: Manage disk groups and disk pools
version_added: '2.2'
description:
    - Create or remove disk groups and disk pools for NetApp E-series storage arrays.
extends_documentation_fragment:
    - netapp.eseries
options:
  state:
    required: true
    description:
    - Whether the specified storage pool should exist or not.
    - Note that removing a storage pool currently requires the removal of all defined volumes first.
    choices: ['present', 'absent']
  name:
    required: true
    description:
    - The name of the storage pool to manage
  criteria_drive_count:
    description:
    - The number of disks to use for building the storage pool. The pool will be expanded if this number exceeds the number of disks already in place
  criteria_drive_type:
    description:
    - The type of disk (hdd or ssd) to use when searching for candidates to use.
    choices: ['hdd','ssd']
  criteria_size_unit:
    description:
    - The unit used to interpret size parameters
    choices: ['bytes', 'b', 'kb', 'mb', 'gb', 'tb', 'pb', 'eb', 'zb', 'yb']
    default: 'gb'
  criteria_drive_min_size:
    description:
    - The minimum individual drive size (in size_unit) to consider when choosing drives for the storage pool.
  criteria_min_usable_capacity:
    description:
    - The minimum size of the storage pool (in size_unit). The pool will be expanded if this value exceeds itscurrent size.
  criteria_drive_interface_type:
    description:
    - The interface type to use when selecting drives for the storage pool (no value means all interface types will be considered)
    choices: ['sas', 'sas4k', 'fibre', 'fibre520b', 'scsi', 'sata', 'pata']
  criteria_drive_require_fde:
    description:
    - Whether full disk encryption ability is required for drives to be added to the storage pool
  raid_level:
    required: true
    choices: ['raidAll', 'raid0', 'raid1', 'raid3', 'raid5', 'raid6', 'raidDiskPool']
    description:
    - "Only required when the requested state is 'present'.  The RAID level of the storage pool to be created."
  erase_secured_drives:
    required: false
    choices: ['true', 'false']
    description:
    - Whether to erase secured disks before adding to storage pool
  secure_pool:
    required: false
    choices: ['true', 'false']
    description:
    - Whether to convert to a secure storage pool. Will only work if all drives in the pool are security capable.
  reserve_drive_count:
    required: false
    description:
    - Set the number of drives reserved by the storage pool for reconstruction operations. Only valide on raid disk pools.
  remove_volumes:
    required: false
    default: False
    description:
    - Prior to removing a storage pool, delete all volumes in the pool.
author: Kevin Hulquest (@hulquest)

'''
EXAMPLES = '''
    - name: No disk groups
      netapp_e_storagepool:
        ssid: "{{ ssid }}"
        name: "{{ item }}"
        state: absent
        api_url: "{{ netapp_api_url }}"
        api_username: "{{ netapp_api_username }}"
        api_password: "{{ netapp_api_password }}"
        validate_certs: "{{ netapp_api_validate_certs }}"
'''
RETURN = '''
msg:
    description: Success message
    returned: success
    type: string
    sample: Json facts for the pool that was created.
'''

import json
import logging
from traceback import format_exc

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.netapp import request, eseries_host_argument_spec
from ansible.module_utils.pycompat24 import get_exception


def select(predicate, iterable):
    # python 2, 3 generic filtering.
    if predicate is None:
        predicate = bool
    for x in iterable:
        if predicate(x):
            yield x


def _identity(obj):
    return obj


class GroupBy(object):
    # python 2, 3 generic grouping.
    def __init__(self, iterable, key=None):
        self.keyfunc = key if key else _identity
        self.it = iter(iterable)
        self.tgtkey = self.currkey = self.currvalue = object()

    def __iter__(self):
        return self

    def next(self):
        while self.currkey == self.tgtkey:
            self.currvalue = next(self.it)  # Exit on StopIteration
            self.currkey = self.keyfunc(self.currvalue)
        self.tgtkey = self.currkey
        return (self.currkey, self._grouper(self.tgtkey))

    def _grouper(self, tgtkey):
        while self.currkey == tgtkey:
            yield self.currvalue
            self.currvalue = next(self.it)  # Exit on StopIteration
            self.currkey = self.keyfunc(self.currvalue)


class NetAppESeriesStoragePool(object):
    def __init__(self):
        self._sp_drives_cached = None

        self._size_unit_map = dict(
            bytes=1,
            b=1,
            kb=1024,
            mb=1024 ** 2,
            gb=1024 ** 3,
            tb=1024 ** 4,
            pb=1024 ** 5,
            eb=1024 ** 6,
            zb=1024 ** 7,
            yb=1024 ** 8
        )

        argument_spec = eseries_host_argument_spec()
        argument_spec.update(dict(
            api_url=dict(type='str', required=True),
            state=dict(required=True, choices=['present', 'absent'], type='str'),
            name=dict(required=True, type='str'),
            criteria_size_unit=dict(default='gb', type='str'),
            criteria_drive_count=dict(type='int'),
            criteria_drive_interface_type=dict(choices=['sas', 'sas4k', 'fibre', 'fibre520b', 'scsi', 'sata', 'pata'],
                                               type='str'),
            criteria_drive_type=dict(choices=['ssd', 'hdd'], type='str'),
            criteria_drive_min_size=dict(type='int'),
            criteria_drive_require_fde=dict(type='bool'),
            criteria_min_usable_capacity=dict(type='int'),
            raid_level=dict(
                choices=['raidUnsupported', 'raidAll', 'raid0', 'raid1', 'raid3', 'raid5', 'raid6', 'raidDiskPool']),
            erase_secured_drives=dict(type='bool'),
            log_path=dict(type='str'),
            remove_drives=dict(type='list'),
            secure_pool=dict(type='bool', default=False),
            reserve_drive_count=dict(type='int'),
            remove_volumes=dict(type='bool', default=False)
        ))

        self.module = AnsibleModule(
            argument_spec=argument_spec,
            required_if=[
                ('state', 'present', ['raid_level'])
            ],
            mutually_exclusive=[

            ],
            # TODO: update validation for various selection criteria
            supports_check_mode=True
        )

        p = self.module.params

        log_path = p['log_path']

        # logging setup
        self._logger = logging.getLogger(self.__class__.__name__)
        self.debug = self._logger.debug

        if log_path:
            logging.basicConfig(level=logging.DEBUG, filename=log_path)

        self.state = p['state']
        self.ssid = p['ssid']
        self.name = p['name']
        self.validate_certs = p['validate_certs']

        self.criteria_drive_count = p['criteria_drive_count']
        self.criteria_drive_type = p['criteria_drive_type']
        self.criteria_size_unit = p['criteria_size_unit']
        self.criteria_drive_min_size = p['criteria_drive_min_size']
        self.criteria_min_usable_capacity = p['criteria_min_usable_capacity']
        self.criteria_drive_interface_type = p['criteria_drive_interface_type']
        self.criteria_drive_require_fde = p['criteria_drive_require_fde']

        self.raid_level = p['raid_level']
        self.erase_secured_drives = p['erase_secured_drives']
        self.remove_drives = p['remove_drives']
        self.secure_pool = p['secure_pool']
        self.reserve_drive_count = p['reserve_drive_count']
        self.remove_volumes = p['remove_volumes']

        try:
            self.api_usr = p['api_username']
            self.api_pwd = p['api_password']
            self.api_url = p['api_url']
        except KeyError:
            self.module.fail_json(msg="You must pass in api_username "
                                      "and api_password and api_url to the module.")

        self.post_headers = dict(Accept="application/json")
        self.post_headers['Content-Type'] = 'application/json'

    # Quick and dirty drive selector, since the one provided by web service proxy is broken for min_disk_size as of 2016-03-12.
    # Doesn't really need to be a class once this is in module_utils or retired- just groups everything together so we
    # can copy/paste to other modules more easily.
    # Filters all disks by specified criteria, then groups remaining disks by capacity, interface and disk type, and selects
    # the first set that matches the specified count and/or aggregate capacity.
    # class DriveSelector(object):
    def filter_drives(
            self,
            drives,  # raw drives resp
            interface_type=None,  # sas, sata, fibre, etc
            drive_type=None,  # ssd/hdd
            spindle_speed=None,  # 7200, 10000, 15000, ssd (=0)
            min_drive_size=None,
            max_drive_size=None,
            fde_required=None,
            size_unit='gb',
            min_total_capacity=None,
            min_drive_count=None,
            exact_drive_count=None,
            raid_level=None
    ):
        if min_total_capacity is None and exact_drive_count is None:
            raise Exception("One of criteria_min_total_capacity or criteria_drive_count must be specified.")

        if min_total_capacity:
            min_total_capacity = min_total_capacity * self._size_unit_map[size_unit]

        # filter clearly invalid/unavailable drives first
        drives = select(self._is_valid_drive, drives)

        if interface_type:
            drives = select(lambda d: d['phyDriveType'] == interface_type, drives)

        if drive_type:
            drives = select(lambda d: d['driveMediaType'] == drive_type, drives)

        if spindle_speed is not None:  # 0 is valid for ssds
            drives = select(lambda d: d['spindleSpeed'] == spindle_speed, drives)

        if min_drive_size:
            min_drive_size_bytes = min_drive_size * self._size_unit_map[size_unit]
            drives = select(lambda d: int(d['rawCapacity']) >= min_drive_size_bytes, drives)

        if max_drive_size:
            max_drive_size_bytes = max_drive_size * self._size_unit_map[size_unit]
            drives = select(lambda d: int(d['rawCapacity']) <= max_drive_size_bytes, drives)

        if fde_required:
            drives = select(lambda d: d['fdeCapable'], drives)

        # initial implementation doesn't have a preference for any of these values...
        # just return the first set we find that matches the requested disk count and/or minimum total capacity
        for (cur_capacity, drives_by_capacity) in GroupBy(drives, lambda d: int(d['rawCapacity'])):
            for (cur_interface_type, drives_by_interface_type) in GroupBy(drives_by_capacity,
                                                                          lambda d: d['phyDriveType']):
                for (cur_drive_type, drives_by_drive_type) in GroupBy(drives_by_interface_type,
                                                                      lambda d: d['driveMediaType']):
                    # listify so we can consume more than once
                    drives_by_drive_type = list(drives_by_drive_type)
                    candidate_set = list()  # reset candidate list on each iteration of the innermost loop

                    if exact_drive_count:
                        if len(drives_by_drive_type) < exact_drive_count:
                            continue  # we know this set is too small, move on

                    for drive in drives_by_drive_type:
                        candidate_set.append(drive)
                        if self._candidate_set_passes(candidate_set, min_capacity_bytes=min_total_capacity,
                                                      min_drive_count=min_drive_count,
                                                      exact_drive_count=exact_drive_count, raid_level=raid_level):
                            return candidate_set

        raise Exception("couldn't find an available set of disks to match specified criteria")

    def _is_valid_drive(self, d):
        is_valid = d['available'] \
            and d['status'] == 'optimal' \
            and not d['pfa'] \
            and not d['removed'] \
            and not d['uncertified'] \
            and not d['invalidDriveData'] \
            and not d['nonRedundantAccess']

        return is_valid

    def _candidate_set_passes(self, candidate_set, min_capacity_bytes=None, min_drive_count=None,
                              exact_drive_count=None, raid_level=None):
        if not self._is_drive_count_valid(len(candidate_set), min_drive_count=min_drive_count,
                                          exact_drive_count=exact_drive_count, raid_level=raid_level):
            return False
        # TODO: this assumes candidate_set is all the same size- if we want to allow wastage, need to update to use min size of set
        if min_capacity_bytes is not None and self._calculate_usable_capacity(int(candidate_set[0]['rawCapacity']),
                                                                              len(candidate_set),
                                                                              raid_level=raid_level) < min_capacity_bytes:
            return False

        return True

    def _calculate_usable_capacity(self, disk_size_bytes, disk_count, raid_level=None):
        if raid_level in [None, 'raid0']:
            return disk_size_bytes * disk_count
        if raid_level == 'raid1':
            return (disk_size_bytes * disk_count) // 2
        if raid_level in ['raid3', 'raid5']:
            return (disk_size_bytes * disk_count) - disk_size_bytes
        if raid_level in ['raid6', 'raidDiskPool']:
            return (disk_size_bytes * disk_count) - (disk_size_bytes * 2)
        raise Exception("unsupported raid_level: %s" % raid_level)

    def _is_drive_count_valid(self, drive_count, min_drive_count=0, exact_drive_count=None, raid_level=None):
        if exact_drive_count and exact_drive_count != drive_count:
            return False
        if raid_level == 'raidDiskPool':
            if drive_count < 11:
                return False
        if raid_level == 'raid1':
            if drive_count % 2 != 0:
                return False
        if raid_level in ['raid3', 'raid5']:
            if drive_count < 3:
                return False
        if raid_level == 'raid6':
            if drive_count < 4:
                return False
        if min_drive_count and drive_count < min_drive_count:
            return False

        return True

    def get_storage_pool(self, storage_pool_name):
        # global ifilter
        self.debug("fetching storage pools")
        # map the storage pool name to its id
        try:
            (rc, resp) = request(self.api_url + "/storage-systems/%s/storage-pools" % (self.ssid),
                                 headers=dict(Accept="application/json"), url_username=self.api_usr,
                                 url_password=self.api_pwd, validate_certs=self.validate_certs)
        except Exception:
            err = get_exception()
            rc = err.args[0]
            if rc == 404 and self.state == 'absent':
                self.module.exit_json(
                    msg="Storage pool [%s] did not exist." % (self.name))
            else:
                err = get_exception()
                self.module.exit_json(
                    msg="Failed to get storage pools. Array id [%s].  Error[%s]. State[%s]. RC[%s]." %
                        (self.ssid, str(err), self.state, rc))

        self.debug("searching for storage pool '%s'", storage_pool_name)

        pool_detail = next(select(lambda a: a['name'] == storage_pool_name, resp), None)

        if pool_detail:
            found = 'found'
        else:
            found = 'not found'
        self.debug(found)

        return pool_detail

    def get_candidate_disks(self):
        self.debug("getting candidate disks...")

        # driveCapacityMin is broken on /drives POST. Per NetApp request we built our own
        # switch back to commented code below if it gets fixed
        # drives_req = dict(
        #     driveCount = self.criteria_drive_count,
        #     sizeUnit = 'mb',
        #     raidLevel = self.raid_level
        # )
        #
        # if self.criteria_drive_type:
        #     drives_req['driveType'] = self.criteria_drive_type
        # if self.criteria_disk_min_aggregate_size_mb:
        #     drives_req['targetUsableCapacity'] = self.criteria_disk_min_aggregate_size_mb
        #
        # # TODO: this arg appears to be ignored, uncomment if it isn't
        # #if self.criteria_disk_min_size_gb:
        # #    drives_req['driveCapacityMin'] = self.criteria_disk_min_size_gb * 1024
        # (rc,drives_resp) = request(self.api_url + "/storage-systems/%s/drives" % (self.ssid), data=json.dumps(drives_req), headers=self.post_headers,
        #                            method='POST', url_username=self.api_usr, url_password=self.api_pwd, validate_certs=self.validate_certs)
        #
        # if rc == 204:
        #     self.module.fail_json(msg='Cannot find disks to match requested criteria for storage pool')

        # disk_ids = [d['id'] for d in drives_resp]

        try:
            (rc, drives_resp) = request(self.api_url + "/storage-systems/%s/drives" % (self.ssid), method='GET',
                                        url_username=self.api_usr, url_password=self.api_pwd,
                                        validate_certs=self.validate_certs)
        except:
            err = get_exception()
            self.module.exit_json(
                msg="Failed to fetch disk drives. Array id [%s].  Error[%s]." % (self.ssid, str(err)))

        try:
            candidate_set = self.filter_drives(drives_resp,
                                               exact_drive_count=self.criteria_drive_count,
                                               drive_type=self.criteria_drive_type,
                                               min_drive_size=self.criteria_drive_min_size,
                                               raid_level=self.raid_level,
                                               size_unit=self.criteria_size_unit,
                                               min_total_capacity=self.criteria_min_usable_capacity,
                                               interface_type=self.criteria_drive_interface_type,
                                               fde_required=self.criteria_drive_require_fde
                                               )
        except:
            err = get_exception()
            self.module.fail_json(
                msg="Failed to allocate adequate drive count. Id [%s]. Error [%s]." % (self.ssid, str(err)))

        disk_ids = [d['id'] for d in candidate_set]

        return disk_ids

    def create_storage_pool(self):
        self.debug("creating storage pool...")

        sp_add_req = dict(
            raidLevel=self.raid_level,
            diskDriveIds=self.disk_ids,
            name=self.name
        )

        if self.erase_secured_drives:
            sp_add_req['eraseSecuredDrives'] = self.erase_secured_drives

        try:
            (rc, resp) = request(self.api_url + "/storage-systems/%s/storage-pools" % (self.ssid),
                                 data=json.dumps(sp_add_req), headers=self.post_headers, method='POST',
                                 url_username=self.api_usr, url_password=self.api_pwd,
                                 validate_certs=self.validate_certs,
                                 timeout=120)
        except:
            err = get_exception()
            pool_id = self.pool_detail['id']
            self.module.exit_json(
                msg="Failed to create storage pool. Pool id [%s]. Array id [%s].  Error[%s]." % (pool_id,
                                                                                                 self.ssid,
                                                                                                 str(err)))

        self.pool_detail = self.get_storage_pool(self.name)

        if self.secure_pool:
            secure_pool_data = dict(securePool=True)
            try:
                (retc, r) = request(
                    self.api_url + "/storage-systems/%s/storage-pools/%s" % (self.ssid, self.pool_detail['id']),
                    data=json.dumps(secure_pool_data), headers=self.post_headers, method='POST',
                    url_username=self.api_usr,
                    url_password=self.api_pwd, validate_certs=self.validate_certs, timeout=120, ignore_errors=True)
            except:
                err = get_exception()
                pool_id = self.pool_detail['id']
                self.module.exit_json(
                    msg="Failed to update storage pool. Pool id [%s]. Array id [%s].  Error[%s]." % (pool_id,
                                                                                                     self.ssid,
                                                                                                     str(err)))

    @property
    def needs_raid_level_migration(self):
        current_raid_level = self.pool_detail['raidLevel']
        needs_migration = self.raid_level != current_raid_level

        if needs_migration:  # sanity check some things so we can fail early/check-mode
            if current_raid_level == 'raidDiskPool':
                self.module.fail_json(msg="raid level cannot be changed for disk pools")

        return needs_migration

    def migrate_raid_level(self):
        self.debug("migrating storage pool to raid level '%s'...", self.raid_level)
        sp_raid_migrate_req = dict(
            raidLevel=self.raid_level
        )
        try:
            (rc, resp) = request(
                self.api_url + "/storage-systems/%s/storage-pools/%s/raid-type-migration" % (self.ssid,
                                                                                             self.name),
                data=json.dumps(sp_raid_migrate_req), headers=self.post_headers, method='POST',
                url_username=self.api_usr,
                url_password=self.api_pwd, validate_certs=self.validate_certs, timeout=120)
        except:
            err = get_exception()
            pool_id = self.pool_detail['id']
            self.module.exit_json(
                msg="Failed to change the raid level of storage pool. Pool id [%s]. Array id [%s].  Error[%s]." % (
                    pool_id, self.ssid, str(err)))

    @property
    def sp_drives(self, exclude_hotspares=True):
        if not self._sp_drives_cached:

            self.debug("fetching drive list...")
            try:
                (rc, resp) = request(self.api_url + "/storage-systems/%s/drives" % (self.ssid), method='GET',
                                     url_username=self.api_usr, url_password=self.api_pwd,
                                     validate_certs=self.validate_certs)
            except:
                err = get_exception()
                pool_id = self.pool_detail['id']
                self.module.exit_json(
                    msg="Failed to fetch disk drives. Pool id [%s]. Array id [%s].  Error[%s]." % (pool_id, self.ssid, str(err)))

            sp_id = self.pool_detail['id']
            if exclude_hotspares:
                self._sp_drives_cached = [d for d in resp if d['currentVolumeGroupRef'] == sp_id and not d['hotSpare']]
            else:
                self._sp_drives_cached = [d for d in resp if d['currentVolumeGroupRef'] == sp_id]

        return self._sp_drives_cached

    @property
    def reserved_drive_count_differs(self):
        if int(self.pool_detail['volumeGroupData']['diskPoolData']['reconstructionReservedDriveCount']) != self.reserve_drive_count:
            return True
        return False

    @property
    def needs_expansion(self):
        if self.criteria_drive_count > len(self.sp_drives):
            return True
        # TODO: is totalRaidedSpace the best attribute for "how big is this SP"?
        if self.criteria_min_usable_capacity and \
                (self.criteria_min_usable_capacity * self._size_unit_map[self.criteria_size_unit]) > int(self.pool_detail['totalRaidedSpace']):
            return True

        return False

    def get_expansion_candidate_drives(self):
        # sanity checks; don't call this if we can't/don't need to expand
        if not self.needs_expansion:
            self.module.fail_json(msg="can't get expansion candidates when pool doesn't need expansion")

        self.debug("fetching expansion candidate drives...")
        try:
            (rc, resp) = request(
                self.api_url + "/storage-systems/%s/storage-pools/%s/expand" % (self.ssid,
                                                                                self.pool_detail['id']),
                method='GET', url_username=self.api_usr, url_password=self.api_pwd, validate_certs=self.validate_certs,
                timeout=120)
        except:
            err = get_exception()
            pool_id = self.pool_detail['id']
            self.module.exit_json(
                msg="Failed to fetch candidate drives for storage pool. Pool id [%s]. Array id [%s].  Error[%s]." % (
                    pool_id, self.ssid, str(err)))

        current_drive_count = len(self.sp_drives)
        current_capacity_bytes = int(self.pool_detail['totalRaidedSpace'])  # TODO: is this the right attribute to use?

        if self.criteria_min_usable_capacity:
            requested_capacity_bytes = self.criteria_min_usable_capacity * self._size_unit_map[self.criteria_size_unit]
        else:
            requested_capacity_bytes = current_capacity_bytes

        if self.criteria_drive_count:
            minimum_disks_to_add = max((self.criteria_drive_count - current_drive_count), 1)
        else:
            minimum_disks_to_add = 1

        minimum_bytes_to_add = max(requested_capacity_bytes - current_capacity_bytes, 0)

        # FUTURE: allow more control over expansion candidate selection?
        # loop over candidate disk sets and add until we've met both criteria

        added_drive_count = 0
        added_capacity_bytes = 0

        drives_to_add = set()

        for s in resp:
            # don't trust the API not to give us duplicate drives across candidate sets, especially in multi-drive sets
            candidate_drives = s['drives']
            if len(drives_to_add.intersection(candidate_drives)) != 0:
                # duplicate, skip
                continue
            drives_to_add.update(candidate_drives)
            added_drive_count += len(candidate_drives)
            added_capacity_bytes += int(s['usableCapacity'])

            if added_drive_count >= minimum_disks_to_add and added_capacity_bytes >= minimum_bytes_to_add:
                break

        if (added_drive_count < minimum_disks_to_add) or (added_capacity_bytes < minimum_bytes_to_add):
            self.module.fail_json(
                msg="unable to find at least %s drives to add that would add at least %s bytes of capacity" % (
                    minimum_disks_to_add, minimum_bytes_to_add))

        return list(drives_to_add)

    def expand_storage_pool(self):
        drives_to_add = self.get_expansion_candidate_drives()

        self.debug("adding %s drives to storage pool...", len(drives_to_add))
        sp_expand_req = dict(
            drives=drives_to_add
        )
        try:
            request(
                self.api_url + "/storage-systems/%s/storage-pools/%s/expand" % (self.ssid,
                                                                                self.pool_detail['id']),
                data=json.dumps(sp_expand_req), headers=self.post_headers, method='POST', url_username=self.api_usr,
                url_password=self.api_pwd, validate_certs=self.validate_certs, timeout=120)
        except:
            err = get_exception()
            pool_id = self.pool_detail['id']
            self.module.exit_json(
                msg="Failed to add drives to storage pool. Pool id [%s]. Array id [%s].  Error[%s]." % (pool_id,
                                                                                                        self.ssid,
                                                                                                        str(
                                                                                                            err)))

            # TODO: check response
            # TODO: support blocking wait?

    def reduce_drives(self, drive_list):
        if all(drive in drive_list for drive in self.sp_drives):
            # all the drives passed in are present in the system
            pass
        else:
            self.module.fail_json(
                msg="One of the drives you wish to remove does not currently exist in the storage pool you specified")

        try:
            (rc, resp) = request(
                self.api_url + "/storage-systems/%s/storage-pools/%s/reduction" % (self.ssid,
                                                                                   self.pool_detail['id']),
                data=json.dumps(drive_list), headers=self.post_headers, method='POST', url_username=self.api_usr,
                url_password=self.api_pwd, validate_certs=self.validate_certs, timeout=120)
        except:
            err = get_exception()
            pool_id = self.pool_detail['id']
            self.module.exit_json(
                msg="Failed to remove drives from storage pool. Pool id [%s]. Array id [%s].  Error[%s]." % (
                    pool_id, self.ssid, str(err)))

    def update_reserve_drive_count(self, qty):
        data = dict(reservedDriveCount=qty)
        try:
            (rc, resp) = request(
                self.api_url + "/storage-systems/%s/storage-pools/%s" % (self.ssid, self.pool_detail['id']),
                data=json.dumps(data), headers=self.post_headers, method='POST', url_username=self.api_usr,
                url_password=self.api_pwd, validate_certs=self.validate_certs, timeout=120)
        except:
            err = get_exception()
            pool_id = self.pool_detail['id']
            self.module.exit_json(
                msg="Failed to update reserve drive count. Pool id [%s]. Array id [%s].  Error[%s]." % (pool_id,
                                                                                                        self.ssid,
                                                                                                        str(
                                                                                                            err)))

    def apply(self):
        changed = False
        pool_exists = False

        self.pool_detail = self.get_storage_pool(self.name)

        if self.pool_detail:
            pool_exists = True
            pool_id = self.pool_detail['id']

            if self.state == 'absent':
                self.debug("CHANGED: storage pool exists, but requested state is 'absent'")
                changed = True
            elif self.state == 'present':
                # sanity checks first- we can't change these, so we'll bomb if they're specified
                if self.criteria_drive_type and self.criteria_drive_type != self.pool_detail['driveMediaType']:
                    self.module.fail_json(
                        msg="drive media type %s cannot be changed to %s" % (self.pool_detail['driveMediaType'],
                                                                             self.criteria_drive_type))

                # now the things we can change...
                if self.needs_expansion:
                    self.debug("CHANGED: storage pool needs expansion")
                    changed = True

                if self.needs_raid_level_migration:
                    self.debug(
                        "CHANGED: raid level migration required; storage pool uses '%s', requested is '%s'",
                        self.pool_detail['raidLevel'], self.raid_level)
                    changed = True

                    # if self.reserved_drive_count_differs:
                    # changed = True

                    # TODO: validate other state details? (pool priority, alert threshold)

                    # per FPoole and others, pool reduce operations will not be supported. Automatic "smart" reduction
                    # presents a difficult parameter issue, as the disk count can increase due to expansion, so we
                    # can't just use disk count > criteria_drive_count.

        else:  # pool does not exist
            if self.state == 'present':
                self.debug("CHANGED: storage pool does not exist, but requested state is 'present'")
                changed = True

                # ensure we can get back a workable set of disks
                # (doing this early so candidate selection runs under check mode)
                self.disk_ids = self.get_candidate_disks()
            else:
                self.module.exit_json(msg="Storage pool [%s] did not exist." % (self.name))

        if changed and not self.module.check_mode:
            # apply changes
            if self.state == 'present':
                if not pool_exists:
                    self.create_storage_pool()
                else:  # pool exists but differs, modify...
                    if self.needs_expansion:
                        self.expand_storage_pool()

                    if self.remove_drives:
                        self.reduce_drives(self.remove_drives)

                    if self.needs_raid_level_migration:
                        self.migrate_raid_level()

                    # if self.reserved_drive_count_differs:
                    #    self.update_reserve_drive_count(self.reserve_drive_count)

                    if self.secure_pool:
                        secure_pool_data = dict(securePool=True)
                        try:
                            (retc, r) = request(
                                self.api_url + "/storage-systems/%s/storage-pools/%s" % (self.ssid,
                                                                                         self.pool_detail[
                                                                                             'id']),
                                data=json.dumps(secure_pool_data), headers=self.post_headers, method='POST',
                                url_username=self.api_usr, url_password=self.api_pwd,
                                validate_certs=self.validate_certs, timeout=120, ignore_errors=True)
                        except:
                            err = get_exception()
                            self.module.exit_json(
                                msg="Failed to delete storage pool. Pool id [%s]. Array id [%s].  Error[%s]." % (
                                    pool_id, self.ssid, str(err)))

                        if int(retc) == 422:
                            self.module.fail_json(
                                msg="Error in enabling secure pool. One of the drives in the specified storage pool is likely not security capable")

            elif self.state == 'absent':
                # delete the storage pool
                try:
                    remove_vol_opt = ''
                    if self.remove_volumes:
                        remove_vol_opt = '?delete-volumes=true'
                    (rc, resp) = request(
                        self.api_url + "/storage-systems/%s/storage-pools/%s%s" % (self.ssid, pool_id,
                                                                                   remove_vol_opt),
                        method='DELETE',
                        url_username=self.api_usr, url_password=self.api_pwd, validate_certs=self.validate_certs,
                        timeout=120)
                except:
                    err = get_exception()
                    self.module.exit_json(
                        msg="Failed to delete storage pool. Pool id [%s]. Array id [%s].  Error[%s]." % (pool_id,
                                                                                                         self.ssid,
                                                                                                         str(err)))

        self.module.exit_json(changed=changed, **self.pool_detail)


def main():
    sp = NetAppESeriesStoragePool()
    try:
        sp.apply()
    except Exception:
        e = get_exception()
        sp.debug("Exception in apply(): \n%s", format_exc(e))
        raise


if __name__ == '__main__':
    main()
