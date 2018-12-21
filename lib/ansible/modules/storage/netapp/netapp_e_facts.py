#!/usr/bin/python

# (c) 2016, NetApp, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
module: netapp_e_facts
version_added: '2.2'
short_description: NetApp E-Series retrieve facts about NetApp E-Series storage arrays
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
    type: bool
  ssid:
    required: true
    description:
    - The ID of the array to manage. This value must be unique for each array.

description:
    - Return various information about NetApp E-Series storage arrays (eg, configuration, disks)

author: Kevin Hulquest (@hulquest)
'''

EXAMPLES = """
---
    - name: Get array facts
      netapp_e_facts:
        array_id: "{{ netapp_array_id }}"
        api_url: "{{ netapp_api_url }}"
        api_username: "{{ netapp_api_username }}"
        api_password: "{{ netapp_api_password }}"
        validate_certs: "{{ netapp_api_validate_certs }}"
"""

RETURN = """
msg:
    description: Gathered facts for <StorageArrayId>.
    returned: always
    type: str
"""
import json

from ansible.module_utils.api import basic_auth_argument_spec
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native
from ansible.module_utils.urls import open_url
from ansible.module_utils.six.moves.urllib.error import HTTPError


def request(url, data=None, headers=None, method='GET', use_proxy=True,
            force=False, last_mod_time=None, timeout=10, validate_certs=True,
            url_username=None, url_password=None, http_agent=None, force_basic_auth=True, ignore_errors=False):
    try:
        r = open_url(url=url, data=data, headers=headers, method=method, use_proxy=use_proxy,
                     force=force, last_mod_time=last_mod_time, timeout=timeout, validate_certs=validate_certs,
                     url_username=url_username, url_password=url_password, http_agent=http_agent,
                     force_basic_auth=force_basic_auth)
    except HTTPError as e:
        r = e.fp

    try:
        raw_data = r.read()
        if raw_data:
            data = json.loads(raw_data)
        else:
            data = None
    except Exception:
        if ignore_errors:
            pass
        else:
            raise

    resp_code = r.getcode()

    if resp_code >= 400 and not ignore_errors:
        raise Exception(resp_code, data)
    else:
        return resp_code, data


def main():
    argument_spec = basic_auth_argument_spec()
    argument_spec.update(
        api_username=dict(type='str', required=True),
        api_password=dict(type='str', required=True, no_log=True),
        api_url=dict(type='str', required=True),
        ssid=dict(required=True))

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True
    )

    p = module.params

    ssid = p['ssid']
    validate_certs = p['validate_certs']

    api_usr = p['api_username']
    api_pwd = p['api_password']
    api_url = p['api_url']

    facts = dict(ssid=ssid)

    # fetch the list of storage-pool objects and look for one with a matching name
    try:
        (rc, resp) = request(api_url + "/storage-systems/%s/graph" % ssid,
                             headers=dict(Accept="application/json"),
                             url_username=api_usr, url_password=api_pwd, validate_certs=validate_certs)
    except Exception as e:
        module.fail_json(
            msg="Failed to obtain facts from storage array with id [%s]. Error [%s]" % (ssid, to_native(e)))

    facts['snapshot_images'] = [
        dict(
            id=d['id'],
            status=d['status'],
            pit_capacity=d['pitCapacity'],
            creation_method=d['creationMethod'],
            reposity_cap_utilization=d['repositoryCapacityUtilization'],
            active_cow=d['activeCOW'],
            rollback_source=d['isRollbackSource']
        ) for d in resp['highLevelVolBundle']['pit']]

    facts['netapp_disks'] = [
        dict(
            id=d['id'],
            available=d['available'],
            media_type=d['driveMediaType'],
            status=d['status'],
            usable_bytes=d['usableCapacity'],
            tray_ref=d['physicalLocation']['trayRef'],
            product_id=d['productID'],
            firmware_version=d['firmwareVersion'],
            serial_number=d['serialNumber'].lstrip()
        ) for d in resp['drive']]

    facts['netapp_storage_pools'] = [
        dict(
            id=sp['id'],
            name=sp['name'],
            available_capacity=sp['freeSpace'],
            total_capacity=sp['totalRaidedSpace'],
            used_capacity=sp['usedSpace']
        ) for sp in resp['volumeGroup']]

    all_volumes = list(resp['volume'])
    # all_volumes.extend(resp['thinVolume'])

    # TODO: exclude thin-volume repo volumes (how to ID?)
    facts['netapp_volumes'] = [
        dict(
            id=v['id'],
            name=v['name'],
            parent_storage_pool_id=v['volumeGroupRef'],
            capacity=v['capacity'],
            is_thin_provisioned=v['thinProvisioned']
        ) for v in all_volumes]

    features = [f for f in resp['sa']['capabilities']]
    features.extend([f['capability'] for f in resp['sa']['premiumFeatures'] if f['isEnabled']])
    features = list(set(features))  # ensure unique
    features.sort()
    facts['netapp_enabled_features'] = features

    # TODO: include other details about the storage pool (size, type, id, etc)
    result = dict(ansible_facts=facts, changed=False)
    module.exit_json(msg="Gathered facts for %s." % ssid, **result)


if __name__ == "__main__":
    main()
