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
module: netapp_e_volume
version_added: "2.2"
short_description: Manage storage volumes (standard and thin)
description:
    - Create or remove volumes (standard and thin) for NetApp E/EF-series storage arrays.
extends_documentation_fragment:
    - netapp.eseries
options:
  state:
    description:
    - Whether the specified volume should exist or not.
    required: true
    choices: ['present', 'absent']
  name:
    description:
    - The name of the volume to manage
    required: true
  storage_pool_name:
    description:
    - "Required only when requested state is 'present'.  The name of the storage pool the volume should exist on."
    required: true
  size_unit:
    description:
    - The unit used to interpret the size parameter
    choices: ['bytes', 'b', 'kb', 'mb', 'gb', 'tb', 'pb', 'eb', 'zb', 'yb']
    default: 'gb'
  size:
    description:
    - "Required only when state = 'present'.  The size of the volume in (size_unit)."
    required: true
  segment_size_kb:
    description:
    - The segment size of the new volume
    default: 512
  thin_provision:
    description:
    - Whether the volume should be thin provisioned.  Thin volumes can only be created on disk pools (raidDiskPool).
    type: bool
    default: 'no'
  thin_volume_repo_size:
    description:
    - Initial size of the thin volume repository volume (in size_unit)
    required: True
  thin_volume_max_repo_size:
    description:
    - Maximum size that the thin volume repository volume will automatically expand to
    default: same as size (in size_unit)
  ssd_cache_enabled:
    description:
    - Whether an existing SSD cache should be enabled on the volume (fails if no SSD cache defined)
    - The default value is to ignore existing SSD cache setting.
    type: bool
  data_assurance_enabled:
    description:
    - If data assurance should be enabled for the volume
    type: bool
    default: 'no'

# TODO: doc thin volume parameters

author: Kevin Hulquest (@hulquest)

'''
EXAMPLES = '''
    - name: No thin volume
      netapp_e_volume:
        ssid: "{{ ssid }}"
        name: NewThinVolumeByAnsible
        state: absent
        log_path: /tmp/volume.log
        api_url: "{{ netapp_api_url }}"
        api_username: "{{ netapp_api_username }}"
        api_password: "{{ netapp_api_password }}"
        validate_certs: "{{ netapp_api_validate_certs }}"
      when: check_volume


    - name: No fat volume
      netapp_e_volume:
        ssid: "{{ ssid }}"
        name: NewVolumeByAnsible
        state: absent
        log_path: /tmp/volume.log
        api_url: "{{ netapp_api_url }}"
        api_username: "{{ netapp_api_username }}"
        api_password: "{{ netapp_api_password }}"
        validate_certs: "{{ netapp_api_validate_certs }}"
      when: check_volume
'''
RETURN = '''
---
msg:
    description: State of volume
    type: string
    returned: always
    sample: "Standard volume [workload_vol_1] has been created."
'''

import json
import logging
import time
from traceback import format_exc

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.netapp import request, eseries_host_argument_spec
from ansible.module_utils._text import to_native

HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json",
}


def ifilter(predicate, iterable):
    # python 2, 3 generic filtering.
    if predicate is None:
        predicate = bool
    for x in iterable:
        if predicate(x):
            yield x


class NetAppESeriesVolume(object):
    def __init__(self):
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
            state=dict(required=True, choices=['present', 'absent']),
            name=dict(required=True, type='str'),
            storage_pool_name=dict(type='str'),
            size_unit=dict(default='gb', choices=['bytes', 'b', 'kb', 'mb', 'gb', 'tb', 'pb', 'eb', 'zb', 'yb'],
                           type='str'),
            size=dict(type='int'),
            segment_size_kb=dict(default=128, choices=[8, 16, 32, 64, 128, 256, 512], type='int'),
            ssd_cache_enabled=dict(type='bool'),  # no default, leave existing setting alone
            data_assurance_enabled=dict(default=False, type='bool'),
            thin_provision=dict(default=False, type='bool'),
            thin_volume_repo_size=dict(type='int'),
            thin_volume_max_repo_size=dict(type='int'),
            # TODO: add cache, owning controller support, thin expansion policy, etc
            log_path=dict(type='str'),
        ))

        self.module = AnsibleModule(argument_spec=argument_spec,
                                    required_if=[
                                        ('state', 'present', ['storage_pool_name', 'size']),
                                        ('thin_provision', 'true', ['thin_volume_repo_size'])
                                    ],
                                    supports_check_mode=True)
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
        self.storage_pool_name = p['storage_pool_name']
        self.size_unit = p['size_unit']
        self.size = p['size']
        self.segment_size_kb = p['segment_size_kb']
        self.ssd_cache_enabled = p['ssd_cache_enabled']
        self.data_assurance_enabled = p['data_assurance_enabled']
        self.thin_provision = p['thin_provision']
        self.thin_volume_repo_size = p['thin_volume_repo_size']
        self.thin_volume_max_repo_size = p['thin_volume_max_repo_size']

        if not self.thin_volume_max_repo_size:
            self.thin_volume_max_repo_size = self.size

        self.validate_certs = p['validate_certs']

        try:
            self.api_usr = p['api_username']
            self.api_pwd = p['api_password']
            self.api_url = p['api_url']
        except KeyError:
            self.module.fail_json(msg="You must pass in api_username "
                                      "and api_password and api_url to the module.")

    def get_volume(self, volume_name):
        self.debug('fetching volumes')
        # fetch the list of volume objects and look for one with a matching name (we'll need to merge volumes and thin-volumes)
        try:
            (rc, volumes) = request(self.api_url + "/storage-systems/%s/volumes" % (self.ssid),
                                    headers=dict(Accept="application/json"), url_username=self.api_usr,
                                    url_password=self.api_pwd, validate_certs=self.validate_certs)
        except Exception as err:
            self.module.fail_json(
                msg="Failed to obtain list of standard/thick volumes.  Array Id [%s]. Error[%s]." % (self.ssid,
                                                                                                     to_native(err)))

        try:
            self.debug('fetching thin-volumes')
            (rc, thinvols) = request(self.api_url + "/storage-systems/%s/thin-volumes" % (self.ssid),
                                     headers=dict(Accept="application/json"), url_username=self.api_usr,
                                     url_password=self.api_pwd, validate_certs=self.validate_certs)
        except Exception as err:
            self.module.fail_json(
                msg="Failed to obtain list of thin volumes.  Array Id [%s]. Error[%s]." % (self.ssid, to_native(err)))

        volumes.extend(thinvols)

        self.debug("searching for volume '%s'", volume_name)
        volume_detail = next(ifilter(lambda a: a['name'] == volume_name, volumes), None)

        if volume_detail:
            self.debug('found')
        else:
            self.debug('not found')

        return volume_detail

    def get_storage_pool(self, storage_pool_name):
        self.debug("fetching storage pools")
        # map the storage pool name to its id
        try:
            (rc, resp) = request(self.api_url + "/storage-systems/%s/storage-pools" % (self.ssid),
                                 headers=dict(Accept="application/json"), url_username=self.api_usr,
                                 url_password=self.api_pwd, validate_certs=self.validate_certs)
        except Exception as err:
            self.module.fail_json(
                msg="Failed to obtain list of storage pools.  Array Id [%s]. Error[%s]." % (self.ssid, to_native(err)))

        self.debug("searching for storage pool '%s'", storage_pool_name)
        pool_detail = next(ifilter(lambda a: a['name'] == storage_pool_name, resp), None)

        if pool_detail:
            self.debug('found')
        else:
            self.debug('not found')

        return pool_detail

    def create_volume(self, pool_id, name, size_unit, size, segment_size_kb, data_assurance_enabled):
        volume_add_req = dict(
            name=name,
            poolId=pool_id,
            sizeUnit=size_unit,
            size=size,
            segSize=segment_size_kb,
            dataAssuranceEnabled=data_assurance_enabled,
        )

        self.debug("creating volume '%s'", name)
        try:
            (rc, resp) = request(self.api_url + "/storage-systems/%s/volumes" % (self.ssid),
                                 data=json.dumps(volume_add_req), headers=HEADERS, method='POST',
                                 url_username=self.api_usr, url_password=self.api_pwd,
                                 validate_certs=self.validate_certs,
                                 timeout=120)
        except Exception as err:
            self.module.fail_json(
                msg="Failed to create volume.  Volume [%s].  Array Id [%s]. Error[%s]." % (self.name, self.ssid,
                                                                                           to_native(err)))

    def create_thin_volume(self, pool_id, name, size_unit, size, thin_volume_repo_size,
                           thin_volume_max_repo_size, data_assurance_enabled):
        thin_volume_add_req = dict(
            name=name,
            poolId=pool_id,
            sizeUnit=size_unit,
            virtualSize=size,
            repositorySize=thin_volume_repo_size,
            maximumRepositorySize=thin_volume_max_repo_size,
            dataAssuranceEnabled=data_assurance_enabled,
        )

        self.debug("creating thin-volume '%s'", name)
        try:
            (rc, resp) = request(self.api_url + "/storage-systems/%s/thin-volumes" % (self.ssid),
                                 data=json.dumps(thin_volume_add_req), headers=HEADERS, method='POST',
                                 url_username=self.api_usr, url_password=self.api_pwd,
                                 validate_certs=self.validate_certs,
                                 timeout=120)
        except Exception as err:
            self.module.fail_json(
                msg="Failed to create thin volume.  Volume [%s].  Array Id [%s]. Error[%s]." % (self.name,
                                                                                                self.ssid,
                                                                                                to_native(err)))

    def delete_volume(self):
        # delete the volume
        self.debug("deleting volume '%s'", self.volume_detail['name'])
        try:
            (rc, resp) = request(
                self.api_url + "/storage-systems/%s/%s/%s" % (self.ssid, self.volume_resource_name,
                                                              self.volume_detail['id']),
                method='DELETE', url_username=self.api_usr, url_password=self.api_pwd,
                validate_certs=self.validate_certs, timeout=120)
        except Exception as err:
            self.module.fail_json(
                msg="Failed to delete volume.  Volume [%s].  Array Id [%s]. Error[%s]." % (self.name, self.ssid,
                                                                                           to_native(err)))

    @property
    def volume_resource_name(self):
        if self.volume_detail['thinProvisioned']:
            return 'thin-volumes'
        else:
            return 'volumes'

    @property
    def volume_properties_changed(self):
        return self.volume_ssdcache_setting_changed  # or with other props here when extended

        # TODO: add support for r/w cache settings, owning controller, scan settings, expansion policy, growth alert threshold

    @property
    def volume_ssdcache_setting_changed(self):
        # None means ignore existing setting
        if self.ssd_cache_enabled is not None and self.ssd_cache_enabled != self.volume_detail['flashCached']:
            self.debug("flash cache setting changed")
            return True

    def update_volume_properties(self):
        update_volume_req = dict()

        # conditionally add values so we ignore unspecified props
        if self.volume_ssdcache_setting_changed:
            update_volume_req['flashCache'] = self.ssd_cache_enabled

        self.debug("updating volume properties...")
        try:
            (rc, resp) = request(
                self.api_url + "/storage-systems/%s/%s/%s/" % (self.ssid, self.volume_resource_name,
                                                               self.volume_detail['id']),
                data=json.dumps(update_volume_req), headers=HEADERS, method='POST',
                url_username=self.api_usr, url_password=self.api_pwd, validate_certs=self.validate_certs,
                timeout=120)
        except Exception as err:
            self.module.fail_json(
                msg="Failed to update volume properties.  Volume [%s].  Array Id [%s]. Error[%s]." % (self.name,
                                                                                                      self.ssid,
                                                                                                      to_native(err)))

    @property
    def volume_needs_expansion(self):
        current_size_bytes = int(self.volume_detail['capacity'])
        requested_size_bytes = self.size * self._size_unit_map[self.size_unit]

        # TODO: check requested/current repo volume size for thin-volumes as well

        # TODO: do we need to build any kind of slop factor in here?
        return requested_size_bytes > current_size_bytes

    def expand_volume(self):
        is_thin = self.volume_detail['thinProvisioned']
        if is_thin:
            # TODO: support manual repo expansion as well
            self.debug('expanding thin volume')
            thin_volume_expand_req = dict(
                newVirtualSize=self.size,
                sizeUnit=self.size_unit
            )
            try:
                (rc, resp) = request(self.api_url + "/storage-systems/%s/thin-volumes/%s/expand" % (self.ssid,
                                                                                                    self.volume_detail[
                                                                                                        'id']),
                                     data=json.dumps(thin_volume_expand_req), headers=HEADERS, method='POST',
                                     url_username=self.api_usr, url_password=self.api_pwd,
                                     validate_certs=self.validate_certs, timeout=120)
            except Exception as err:
                self.module.fail_json(
                    msg="Failed to expand thin volume.  Volume [%s].  Array Id [%s]. Error[%s]." % (self.name,
                                                                                                    self.ssid,
                                                                                                    to_native(err)))

                # TODO: check return code
        else:
            self.debug('expanding volume')
            volume_expand_req = dict(
                expansionSize=self.size,
                sizeUnit=self.size_unit
            )
            try:
                (rc, resp) = request(
                    self.api_url + "/storage-systems/%s/volumes/%s/expand" % (self.ssid,
                                                                              self.volume_detail['id']),
                    data=json.dumps(volume_expand_req), headers=HEADERS, method='POST',
                    url_username=self.api_usr, url_password=self.api_pwd, validate_certs=self.validate_certs,
                    timeout=120)
            except Exception as err:
                self.module.fail_json(
                    msg="Failed to expand volume.  Volume [%s].  Array Id [%s]. Error[%s]." % (self.name,
                                                                                               self.ssid,
                                                                                               to_native(err)))

            self.debug('polling for completion...')

            while True:
                try:
                    (rc, resp) = request(self.api_url + "/storage-systems/%s/volumes/%s/expand" % (self.ssid,
                                                                                                   self.volume_detail[
                                                                                                       'id']),
                                         method='GET', url_username=self.api_usr, url_password=self.api_pwd,
                                         validate_certs=self.validate_certs)
                except Exception as err:
                    self.module.fail_json(
                        msg="Failed to get volume expansion progress.  Volume [%s].  Array Id [%s]. Error[%s]." % (
                            self.name, self.ssid, to_native(err)))

                action = resp['action']
                percent_complete = resp['percentComplete']

                self.debug('expand action %s, %s complete...', action, percent_complete)

                if action == 'none':
                    self.debug('expand complete')
                    break
                else:
                    time.sleep(5)

    def apply(self):
        changed = False
        volume_exists = False
        msg = None

        self.volume_detail = self.get_volume(self.name)

        if self.volume_detail:
            volume_exists = True

            if self.state == 'absent':
                self.debug("CHANGED: volume exists, but requested state is 'absent'")
                changed = True
            elif self.state == 'present':
                # check requested volume size, see if expansion is necessary
                if self.volume_needs_expansion:
                    self.debug("CHANGED: requested volume size %s%s is larger than current size %sb",
                               self.size, self.size_unit, self.volume_detail['capacity'])
                    changed = True

                if self.volume_properties_changed:
                    self.debug("CHANGED: one or more volume properties have changed")
                    changed = True

        else:
            if self.state == 'present':
                self.debug("CHANGED: volume does not exist, but requested state is 'present'")
                changed = True

        if changed:
            if self.module.check_mode:
                self.debug('skipping changes due to check mode')
            else:
                if self.state == 'present':
                    if not volume_exists:
                        pool_detail = self.get_storage_pool(self.storage_pool_name)

                        if not pool_detail:
                            self.module.fail_json(msg='Requested storage pool (%s) not found' % self.storage_pool_name)

                        if self.thin_provision and not pool_detail['diskPool']:
                            self.module.fail_json(
                                msg='Thin provisioned volumes can only be located on disk pools (not volume groups)')

                        pool_id = pool_detail['id']

                        if not self.thin_provision:
                            self.create_volume(pool_id, self.name, self.size_unit, self.size, self.segment_size_kb,
                                               self.data_assurance_enabled)
                            msg = "Standard volume [%s] has been created." % (self.name)

                        else:
                            self.create_thin_volume(pool_id, self.name, self.size_unit, self.size,
                                                    self.thin_volume_repo_size, self.thin_volume_max_repo_size,
                                                    self.data_assurance_enabled)
                            msg = "Thin volume [%s] has been created." % (self.name)

                    else:  # volume exists but differs, modify...
                        if self.volume_needs_expansion:
                            self.expand_volume()
                            msg = "Volume [%s] has been expanded." % (self.name)

                    # this stuff always needs to run on present (since props can't be set on creation)
                    if self.volume_properties_changed:
                        self.update_volume_properties()
                        msg = "Properties of volume [%s] has been updated." % (self.name)

                elif self.state == 'absent':
                    self.delete_volume()
                    msg = "Volume [%s] has been deleted." % (self.name)
        else:
            self.debug("exiting with no changes")
            if self.state == 'absent':
                msg = "Volume [%s] did not exist." % (self.name)
            else:
                msg = "Volume [%s] already exists." % (self.name)

        self.module.exit_json(msg=msg, changed=changed)


def main():
    v = NetAppESeriesVolume()

    try:
        v.apply()
    except Exception as e:
        v.debug("Exception in apply(): \n%s", format_exc())
        v.module.fail_json(msg="Module failed. Error [%s]." % to_native(e))


if __name__ == '__main__':
    main()
