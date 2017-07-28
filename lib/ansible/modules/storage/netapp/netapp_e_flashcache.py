#!/usr/bin/python

# (c) 2016, NetApp, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
module: netapp_e_flashcache
author: Kevin Hulquest (@hulquest)
version_added: '2.2'
short_description: Manage NetApp SSD caches
description:
- Create or remove SSD caches on a NetApp E-Series storage array.
options:
  api_username:
      required: true
      description:
      - The username to authenticate with the SANtricity WebServices Proxy or embedded REST API.
  api_password:
      required: true
      description:
      - The password to authenticate with the SANtricity WebServices Proxy or embedded REST API.
  api_url:
      required: true
      description:
      - The url to the SANtricity WebServices Proxy or embedded REST API.
  validate_certs:
      required: false
      default: true
      description:
      - Should https certificates be validated?
  ssid:
    required: true
    description:
    - The ID of the array to manage (as configured on the web services proxy).
  state:
    required: true
    description:
    - Whether the specified SSD cache should exist or not.
    choices: ['present', 'absent']
    default: present
  name:
    required: true
    description:
    - The name of the SSD cache to manage
  io_type:
    description:
    - The type of workload to optimize the cache for.
    choices: ['filesystem','database','media']
    default: filesystem
  disk_count:
    description:
    - The minimum number of disks to use for building the cache. The cache will be expanded if this number exceeds the number of disks already in place
  size_unit:
    description:
    - The unit to be applied to size arguments
    choices: ['bytes', 'b', 'kb', 'mb', 'gb', 'tb', 'pb', 'eb', 'zb', 'yb']
    default: gb
  cache_size_min:
    description:
    - The minimum size (in size_units) of the ssd cache. The cache will be expanded if this exceeds the current size of the cache.
'''

EXAMPLES = """
    - name: Flash Cache
      netapp_e_flashcache:
        ssid: "{{ ssid }}"
        api_url: "{{ netapp_api_url }}"
        api_username: "{{ netapp_api_username }}"
        api_password: "{{ netapp_api_password }}"
        validate_certs: "{{ netapp_api_validate_certs }}"
        name: SSDCacheBuiltByAnsible
"""

RETURN = """
msg:
    description: Success message
    returned: success
    type: string
    sample: json for newly created flash cache
"""
import json
import logging
import sys
import traceback

from ansible.module_utils.api import basic_auth_argument_spec
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.six.moves import reduce
from ansible.module_utils.six.moves.urllib.error import HTTPError
from ansible.module_utils._text import to_native
from ansible.module_utils.urls import open_url


def request(url, data=None, headers=None, method='GET', use_proxy=True,
            force=False, last_mod_time=None, timeout=10, validate_certs=True,
            url_username=None, url_password=None, http_agent=None, force_basic_auth=True, ignore_errors=False):
    try:
        r = open_url(url=url, data=data, headers=headers, method=method, use_proxy=use_proxy,
                     force=force, last_mod_time=last_mod_time, timeout=timeout, validate_certs=validate_certs,
                     url_username=url_username, url_password=url_password, http_agent=http_agent,
                     force_basic_auth=force_basic_auth)
    except HTTPError as err:
        r = err.fp

    try:
        raw_data = r.read()
        if raw_data:
            data = json.loads(raw_data)
        else:
            raw_data = None
    except:
        if ignore_errors:
            pass
        else:
            raise Exception(raw_data)

    resp_code = r.getcode()

    if resp_code >= 400 and not ignore_errors:
        raise Exception(resp_code, data)
    else:
        return resp_code, data


class NetAppESeriesFlashCache(object):
    def __init__(self):
        self.name = None
        self.log_mode = None
        self.log_path = None
        self.api_url = None
        self.api_username = None
        self.api_password = None
        self.ssid = None
        self.validate_certs = None
        self.disk_count = None
        self.size_unit = None
        self.cache_size_min = None
        self.io_type = None
        self.driveRefs = None
        self.state = None
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

        argument_spec = basic_auth_argument_spec()
        argument_spec.update(dict(
            api_username=dict(type='str', required=True),
            api_password=dict(type='str', required=True, no_log=True),
            api_url=dict(type='str', required=True),
            state=dict(default='present', choices=['present', 'absent'], type='str'),
            ssid=dict(required=True, type='str'),
            name=dict(required=True, type='str'),
            disk_count=dict(type='int'),
            disk_refs=dict(type='list'),
            cache_size_min=dict(type='int'),
            io_type=dict(default='filesystem', choices=['filesystem', 'database', 'media']),
            size_unit=dict(default='gb', choices=['bytes', 'b', 'kb', 'mb', 'gb', 'tb', 'pb', 'eb', 'zb', 'yb'],
                           type='str'),
            criteria_disk_phy_type=dict(choices=['sas', 'sas4k', 'fibre', 'fibre520b', 'scsi', 'sata', 'pata'],
                                        type='str'),
            log_mode=dict(type='str'),
            log_path=dict(type='str'),
        ))
        self.module = AnsibleModule(
            argument_spec=argument_spec,
            required_if=[

            ],
            mutually_exclusive=[

            ],
            # TODO: update validation for various selection criteria
            supports_check_mode=True
        )

        self.__dict__.update(self.module.params)

        # logging setup
        self._logger = logging.getLogger(self.__class__.__name__)
        self.debug = self._logger.debug

        if self.log_mode == 'file' and self.log_path:
            logging.basicConfig(level=logging.DEBUG, filename=self.log_path)
        elif self.log_mode == 'stderr':
            logging.basicConfig(level=logging.DEBUG, stream=sys.stderr)

        self.post_headers = dict(Accept="application/json")
        self.post_headers['Content-Type'] = 'application/json'

    def get_candidate_disks(self, disk_count, size_unit='gb', capacity=None):
        self.debug("getting candidate disks...")

        drives_req = dict(
            driveCount=disk_count,
            sizeUnit=size_unit,
            driveType='ssd',
        )

        if capacity:
            drives_req['targetUsableCapacity'] = capacity

        (rc, drives_resp) = request(self.api_url + "/storage-systems/%s/drives" % (self.ssid),
                                    data=json.dumps(drives_req), headers=self.post_headers, method='POST',
                                    url_username=self.api_username, url_password=self.api_password,
                                    validate_certs=self.validate_certs)

        if rc == 204:
            self.module.fail_json(msg='Cannot find disks to match requested criteria for ssd cache')

        disk_ids = [d['id'] for d in drives_resp]
        bytes = reduce(lambda s, d: s + int(d['usableCapacity']), drives_resp, 0)

        return (disk_ids, bytes)

    def create_cache(self):
        (disk_ids, bytes) = self.get_candidate_disks(disk_count=self.disk_count, size_unit=self.size_unit,
                                                     capacity=self.cache_size_min)

        self.debug("creating ssd cache...")

        create_fc_req = dict(
            driveRefs=disk_ids,
            name=self.name
        )

        (rc, self.resp) = request(self.api_url + "/storage-systems/%s/flash-cache" % (self.ssid),
                                  data=json.dumps(create_fc_req), headers=self.post_headers, method='POST',
                                  url_username=self.api_username, url_password=self.api_password,
                                  validate_certs=self.validate_certs)

    def update_cache(self):
        self.debug('updating flash cache config...')
        update_fc_req = dict(
            name=self.name,
            configType=self.io_type
        )

        (rc, self.resp) = request(self.api_url + "/storage-systems/%s/flash-cache/configure" % (self.ssid),
                                  data=json.dumps(update_fc_req), headers=self.post_headers, method='POST',
                                  url_username=self.api_username, url_password=self.api_password,
                                  validate_certs=self.validate_certs)

    def delete_cache(self):
        self.debug('deleting flash cache...')
        (rc, self.resp) = request(self.api_url + "/storage-systems/%s/flash-cache" % (self.ssid), method='DELETE',
                                  url_username=self.api_username, url_password=self.api_password,
                                  validate_certs=self.validate_certs, ignore_errors=True)

    @property
    def needs_more_disks(self):
        if len(self.cache_detail['driveRefs']) < self.disk_count:
            self.debug("needs resize: current disk count %s < requested requested count %s" % (
                len(self.cache_detail['driveRefs']), self.disk_count))
            return True

    @property
    def needs_less_disks(self):
        if len(self.cache_detail['driveRefs']) > self.disk_count:
            self.debug("needs resize: current disk count %s < requested requested count %s" % (
                len(self.cache_detail['driveRefs']), self.disk_count))
            return True

    @property
    def current_size_bytes(self):
        return int(self.cache_detail['fcDriveInfo']['fcWithDrives']['usedCapacity'])

    @property
    def requested_size_bytes(self):
        if self.cache_size_min:
            return self.cache_size_min * self._size_unit_map[self.size_unit]
        else:
            return 0

    @property
    def needs_more_capacity(self):
        if self.current_size_bytes < self.requested_size_bytes:
            self.debug("needs resize: current capacity %sb is less than requested minimum %sb" % (
                self.current_size_bytes, self.requested_size_bytes))
            return True

    @property
    def needs_resize(self):
        return self.needs_more_disks or self.needs_more_capacity or self.needs_less_disks

    def resize_cache(self):
        # increase up to disk count first, then iteratively add disks until we meet requested capacity

        # TODO: perform this calculation in check mode
        current_disk_count = len(self.cache_detail['driveRefs'])
        proposed_new_disks = 0

        proposed_additional_bytes = 0
        proposed_disk_ids = []

        if self.needs_more_disks:
            proposed_disk_count = self.disk_count - current_disk_count

            (disk_ids, bytes) = self.get_candidate_disks(disk_count=proposed_disk_count)
            proposed_additional_bytes = bytes
            proposed_disk_ids = disk_ids

            while self.current_size_bytes + proposed_additional_bytes < self.requested_size_bytes:
                proposed_new_disks += 1
                (disk_ids, bytes) = self.get_candidate_disks(disk_count=proposed_new_disks)
                proposed_disk_ids = disk_ids
                proposed_additional_bytes = bytes

            add_drives_req = dict(
                driveRef=proposed_disk_ids
            )

            self.debug("adding drives to flash-cache...")
            (rc, self.resp) = request(self.api_url + "/storage-systems/%s/flash-cache/addDrives" % (self.ssid),
                                      data=json.dumps(add_drives_req), headers=self.post_headers, method='POST',
                                      url_username=self.api_username, url_password=self.api_password,
                                      validate_certs=self.validate_certs)

        elif self.needs_less_disks and self.driveRefs:
            rm_drives = dict(driveRef=self.driveRefs)
            (rc, self.resp) = request(self.api_url + "/storage-systems/%s/flash-cache/removeDrives" % (self.ssid),
                                      data=json.dumps(rm_drives), headers=self.post_headers, method='POST',
                                      url_username=self.api_username, url_password=self.api_password,
                                      validate_certs=self.validate_certs)

    def apply(self):
        result = dict(changed=False)
        (rc, cache_resp) = request(self.api_url + "/storage-systems/%s/flash-cache" % (self.ssid),
                                   url_username=self.api_username, url_password=self.api_password,
                                   validate_certs=self.validate_certs, ignore_errors=True)

        if rc == 200:
            self.cache_detail = cache_resp
        else:
            self.cache_detail = None

        if rc not in [200, 404]:
            raise Exception(
                "Unexpected error code %s fetching flash cache detail. Response data was %s" % (rc, cache_resp))

        if self.state == 'present':
            if self.cache_detail:
                # TODO: verify parameters against detail for changes
                if self.cache_detail['name'] != self.name:
                    self.debug("CHANGED: name differs")
                    result['changed'] = True
                if self.cache_detail['flashCacheBase']['configType'] != self.io_type:
                    self.debug("CHANGED: io_type differs")
                    result['changed'] = True
                if self.needs_resize:
                    self.debug("CHANGED: resize required")
                    result['changed'] = True
            else:
                self.debug("CHANGED: requested state is 'present' but cache does not exist")
                result['changed'] = True
        else:  # requested state is absent
            if self.cache_detail:
                self.debug("CHANGED: requested state is 'absent' but cache exists")
                result['changed'] = True

        if not result['changed']:
            self.debug("no changes, exiting...")
            self.module.exit_json(**result)

        if self.module.check_mode:
            self.debug("changes pending in check mode, exiting early...")
            self.module.exit_json(**result)

        if self.state == 'present':
            if not self.cache_detail:
                self.create_cache()
            else:
                if self.needs_resize:
                    self.resize_cache()

            # run update here as well, since io_type can't be set on creation
            self.update_cache()

        elif self.state == 'absent':
            self.delete_cache()

        # TODO: include other details about the storage pool (size, type, id, etc)
        self.module.exit_json(changed=result['changed'], **self.resp)


def main():
    sp = NetAppESeriesFlashCache()
    try:
        sp.apply()
    except Exception as e:
        sp.debug("Exception in apply(): \n%s" % to_native(e))
        sp.module.fail_json(msg="Failed to create flash cache. Error[%s]" % to_native(e),
                            exception=traceback.format_exc())


if __name__ == '__main__':
    main()
