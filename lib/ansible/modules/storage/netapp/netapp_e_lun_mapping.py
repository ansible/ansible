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
module: netapp_e_lun_mapping
author: Kevin Hulquest (@hulquest)
short_description: Create or Remove LUN Mappings
description:
     - Allows for the creation and removal of volume to host mappings for NetApp E-series storage arrays.
version_added: "2.2"
extends_documentation_fragment:
    - netapp.eseries
options:
  lun:
    description:
      - The LUN number you wish to give the mapping
      - If the supplied I(volume_name) is associated with a different LUN, it will be updated to what is supplied here.
    required: False
    default: 0
  target:
    description:
      - The name of host or hostgroup you wish to assign to the mapping
      - If omitted, the default hostgroup is used.
      - If the supplied I(volume_name) is associated with a different target, it will be updated to what is supplied here.
    required: False
  volume_name:
    description:
      - The name of the volume you wish to include in the mapping.
    required: True
  target_type:
    description:
      - Whether the target is a host or group.
      - Required if supplying an explicit target.
    required: False
    choices: ["host", "group"]
  state:
    description:
      - Present will ensure the mapping exists, absent will remove the mapping.
      - All parameters I(lun), I(target), I(target_type) and I(volume_name) must still be supplied.
    required: True
    choices: ["present", "absent"]
'''

EXAMPLES = '''
---
    - name: Lun Mapping Example
      netapp_e_lun_mapping:
        state: present
        ssid: 1
        lun: 12
        target: Wilson
        volume_name: Colby1
        target_type: group
        api_url: "{{ netapp_api_url }}"
        api_username: "{{ netapp_api_username }}"
        api_password: "{{ netapp_api_password }}"
'''
RETURN = '''
msg:
    description: Status of mapping
    returned: always
    type: string
    sample: 'Mapping existing'
'''
import json

from ansible.module_utils.api import basic_auth_argument_spec
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.netapp import request, eseries_host_argument_spec
from ansible.module_utils._text import to_native

HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json"
}


def get_host_and_group_map(module, ssid, api_url, user, pwd, validate_certs):
    mapping = dict(host=dict(), group=dict())

    hostgroups = 'storage-systems/%s/host-groups' % ssid
    groups_url = api_url + hostgroups
    try:
        hg_rc, hg_data = request(groups_url, headers=HEADERS, url_username=user, url_password=pwd,
                                 validate_certs=validate_certs)
    except Exception as err:
        module.fail_json(msg="Failed to get host groups. Id [%s]. Error [%s]" % (ssid, to_native(err)))

    for group in hg_data:
        mapping['group'][group['name']] = group['id']

    hosts = 'storage-systems/%s/hosts' % ssid
    hosts_url = api_url + hosts
    try:
        h_rc, h_data = request(hosts_url, headers=HEADERS, url_username=user, url_password=pwd,
                               validate_certs=validate_certs)
    except Exception as err:
        module.fail_json(msg="Failed to get hosts. Id [%s]. Error [%s]" % (ssid, to_native(err)))

    for host in h_data:
        mapping['host'][host['name']] = host['id']

    return mapping


def get_volume_id(module, data, ssid, name, api_url, user, pwd):
    qty = 0
    for volume in data:
        if volume['name'] == name:
            qty += 1

            if qty > 1:
                module.fail_json(msg="More than one volume with the name: %s was found, "
                                     "please use the volume WWN instead" % name)
            else:
                wwn = volume['wwn']

    try:
        return wwn
    except NameError:
        module.fail_json(msg="No volume with the name: %s, was found" % (name))


def get_hostgroups(module, ssid, api_url, user, pwd, validate_certs):
    groups = "storage-systems/%s/host-groups" % ssid
    url = api_url + groups
    try:
        rc, data = request(url, headers=HEADERS, url_username=user, url_password=pwd, validate_certs=validate_certs)
        return data
    except Exception:
        module.fail_json(msg="There was an issue with connecting, please check that your"
                             "endpoint is properly defined and your credentials are correct")


def get_volumes(module, ssid, api_url, user, pwd, mappable, validate_certs):
    volumes = 'storage-systems/%s/%s' % (ssid, mappable)
    url = api_url + volumes
    try:
        rc, data = request(url, url_username=user, url_password=pwd, validate_certs=validate_certs)
    except Exception as err:
        module.fail_json(
            msg="Failed to mappable objects. Type[%s. Id [%s]. Error [%s]." % (mappable, ssid, to_native(err)))
    return data


def get_lun_mappings(ssid, api_url, user, pwd, validate_certs, get_all=None):
    mappings = 'storage-systems/%s/volume-mappings' % ssid
    url = api_url + mappings
    rc, data = request(url, url_username=user, url_password=pwd, validate_certs=validate_certs)

    if not get_all:
        remove_keys = ('ssid', 'perms', 'lunMappingRef', 'type', 'id')

        for key in remove_keys:
            for mapping in data:
                del mapping[key]

    return data


def create_mapping(module, ssid, lun_map, vol_name, api_url, user, pwd, validate_certs):
    mappings = 'storage-systems/%s/volume-mappings' % ssid
    url = api_url + mappings

    if lun_map is not None:
        post_body = json.dumps(dict(
            mappableObjectId=lun_map['volumeRef'],
            targetId=lun_map['mapRef'],
            lun=lun_map['lun']
        ))
    else:
        post_body = json.dumps(dict(
            mappableObjectId=lun_map['volumeRef'],
            targetId=lun_map['mapRef'],
        ))

    rc, data = request(url, data=post_body, method='POST', url_username=user, url_password=pwd, headers=HEADERS,
                       ignore_errors=True, validate_certs=validate_certs)

    if rc == 422 and lun_map['lun'] is not None:
        data = move_lun(module, ssid, lun_map, vol_name, api_url, user, pwd, validate_certs)
        # module.fail_json(msg="The volume you specified '%s' is already "
        #                      "part of a different LUN mapping. If you "
        #                      "want to move it to a different host or "
        #                      "hostgroup, then please use the "
        #                      "netapp_e_move_lun module" % vol_name)
    return data


def move_lun(module, ssid, lun_map, vol_name, api_url, user, pwd, validate_certs):
    lun_id = get_lun_id(module, ssid, lun_map, api_url, user, pwd, validate_certs)
    move_lun = "storage-systems/%s/volume-mappings/%s/move" % (ssid, lun_id)
    url = api_url + move_lun
    post_body = json.dumps(dict(targetId=lun_map['mapRef'], lun=lun_map['lun']))
    rc, data = request(url, data=post_body, method='POST', url_username=user, url_password=pwd, headers=HEADERS,
                       validate_certs=validate_certs)
    return data


def get_lun_id(module, ssid, lun_mapping, api_url, user, pwd, validate_certs):
    data = get_lun_mappings(ssid, api_url, user, pwd, validate_certs, get_all=True)

    for lun_map in data:
        if lun_map['volumeRef'] == lun_mapping['volumeRef']:
            return lun_map['id']
    # This shouldn't ever get called
    module.fail_json(msg="No LUN map found.")


def remove_mapping(module, ssid, lun_mapping, api_url, user, pwd, validate_certs):
    lun_id = get_lun_id(module, ssid, lun_mapping, api_url, user, pwd)
    lun_del = "storage-systems/%s/volume-mappings/%s" % (ssid, lun_id)
    url = api_url + lun_del
    rc, data = request(url, method='DELETE', url_username=user, url_password=pwd, headers=HEADERS,
                       validate_certs=validate_certs)
    return data


def main():
    argument_spec = eseries_host_argument_spec()
    argument_spec.update(dict(
        state=dict(required=True, choices=['present', 'absent']),
        target=dict(required=False, default=None),
        target_type=dict(required=False, choices=['host', 'group']),
        lun=dict(required=False, type='int'),
        volume_name=dict(required=True),
    ))

    module = AnsibleModule(argument_spec=argument_spec)

    state = module.params['state']
    target = module.params['target']
    target_type = module.params['target_type']
    lun = module.params['lun']
    ssid = module.params['ssid']
    validate_certs = module.params['validate_certs']
    vol_name = module.params['volume_name']
    user = module.params['api_username']
    pwd = module.params['api_password']
    api_url = module.params['api_url']

    if not api_url.endswith('/'):
        api_url += '/'

    volume_map = get_volumes(module, ssid, api_url, user, pwd, "volumes", validate_certs)
    thin_volume_map = get_volumes(module, ssid, api_url, user, pwd, "thin-volumes", validate_certs)
    volref = None

    for vol in volume_map:
        if vol['label'] == vol_name:
            volref = vol['volumeRef']

    if not volref:
        for vol in thin_volume_map:
            if vol['label'] == vol_name:
                volref = vol['volumeRef']

    if not volref:
        module.fail_json(changed=False, msg="No volume with the name %s was found" % vol_name)

    host_and_group_mapping = get_host_and_group_map(module, ssid, api_url, user, pwd, validate_certs)

    desired_lun_mapping = dict(
        mapRef=host_and_group_mapping[target_type][target],
        lun=lun,
        volumeRef=volref
    )

    lun_mappings = get_lun_mappings(ssid, api_url, user, pwd, validate_certs)

    if state == 'present':
        if desired_lun_mapping in lun_mappings:
            module.exit_json(changed=False, msg="Mapping exists")
        else:
            result = create_mapping(module, ssid, desired_lun_mapping, vol_name, api_url, user, pwd, validate_certs)
            module.exit_json(changed=True, **result)

    elif state == 'absent':
        if desired_lun_mapping in lun_mappings:
            result = remove_mapping(module, ssid, desired_lun_mapping, api_url, user, pwd, validate_certs)
            module.exit_json(changed=True, msg="Mapping removed")
        else:
            module.exit_json(changed=False, msg="Mapping absent")


if __name__ == '__main__':
    main()
