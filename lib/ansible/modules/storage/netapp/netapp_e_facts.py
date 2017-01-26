#!/usr/bin/python

# (c) 2016, NetApp, Inc
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.
#

ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'version': '1.0'}

DOCUMENTATION = '''
module: netapp_e_facts
version_added: '2.2'
short_description: Get facts about NetApp E-Series arrays
extends_documentation_fragment:
    - netapp.eseries

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
msg: Gathered facts for <StorageArrayId>.
"""

from ansible.module_utils.api import basic_auth_argument_spec
from ansible.module_utils.basic import AnsibleModule, get_exception
from ansible.module_utils.netapp import request

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
    except:
        error = get_exception()
        module.fail_json(
            msg="Failed to obtain facts from storage array with id [%s]. Error [%s]" % (ssid, str(error)))

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
