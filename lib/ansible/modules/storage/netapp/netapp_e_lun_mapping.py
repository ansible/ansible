#!/usr/bin/python

# (c) 2016, NetApp, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.0',
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
options:
  validate_certs:
      required: false
      default: true
      description:
      - Should https certificates be validated?
  ssid:
    description:
      - "The storage system array identifier."
    required: False
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
  api_url:
    description:
      - "The full API url. Example: http://ENDPOINT:8080/devmgr/v2"
      - This can optionally be set via an environment variable, API_URL
    required: False
  api_username:
    description:
      - The username used to authenticate against the API. This can optionally be set via an environment variable, API_USERNAME
    required: False
  api_password:
    description:
      - The password used to authenticate against the API. This can optionally be set via an environment variable, API_PASSWORD
    required: False
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
from ansible.module_utils.pycompat24 import get_exception
from ansible.module_utils.urls import open_url

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.six.moves.urllib.error import HTTPError

HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json"
}


def request(url, data=None, headers=None, method='GET', use_proxy=True,
            force=False, last_mod_time=None, timeout=10, validate_certs=True,
            url_username=None, url_password=None, http_agent=None, force_basic_auth=True, ignore_errors=False):
    try:
        r = open_url(url=url, data=data, headers=headers, method=method, use_proxy=use_proxy,
                     force=force, last_mod_time=last_mod_time, timeout=timeout, validate_certs=validate_certs,
                     url_username=url_username, url_password=url_password, http_agent=http_agent,
                     force_basic_auth=force_basic_auth)
    except HTTPError:
        err = get_exception()
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


def get_host_and_group_map(module, ssid, api_url, user, pwd):
    mapping = dict(host=dict(), group=dict())

    hostgroups = 'storage-systems/%s/host-groups' % ssid
    groups_url = api_url + hostgroups
    try:
        hg_rc, hg_data = request(groups_url, headers=HEADERS, url_username=user, url_password=pwd)
    except:
        err = get_exception()
        module.fail_json(msg="Failed to get host groups. Id [%s]. Error [%s]" % (ssid, str(err)))

    for group in hg_data:
        mapping['group'][group['name']] = group['id']

    hosts = 'storage-systems/%s/hosts' % ssid
    hosts_url = api_url + hosts
    try:
        h_rc, h_data = request(hosts_url, headers=HEADERS, url_username=user, url_password=pwd)
    except:
        err = get_exception()
        module.fail_json(msg="Failed to get hosts. Id [%s]. Error [%s]" % (ssid, str(err)))

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


def get_hostgroups(module, ssid, api_url, user, pwd):
    groups = "storage-systems/%s/host-groups" % ssid
    url = api_url + groups
    try:
        rc, data = request(url, headers=HEADERS, url_username=user, url_password=pwd)
        return data
    except Exception:
        module.fail_json(msg="There was an issue with connecting, please check that your"
                             "endpoint is properly defined and your credentials are correct")


def get_volumes(module, ssid, api_url, user, pwd, mappable):
    volumes = 'storage-systems/%s/%s' % (ssid, mappable)
    url = api_url + volumes
    try:
        rc, data = request(url, url_username=user, url_password=pwd)
    except Exception:
        err = get_exception()
        module.fail_json(
            msg="Failed to mappable objects. Type[%s. Id [%s]. Error [%s]." % (mappable, ssid, str(err)))
    return data


def get_lun_mappings(ssid, api_url, user, pwd, get_all=None):
    mappings = 'storage-systems/%s/volume-mappings' % ssid
    url = api_url + mappings
    rc, data = request(url, url_username=user, url_password=pwd)

    if not get_all:
        remove_keys = ('ssid', 'perms', 'lunMappingRef', 'type', 'id')

        for key in remove_keys:
            for mapping in data:
                del mapping[key]

    return data


def create_mapping(module, ssid, lun_map, vol_name, api_url, user, pwd):
    mappings = 'storage-systems/%s/volume-mappings' % ssid
    url = api_url + mappings
    post_body = json.dumps(dict(
        mappableObjectId=lun_map['volumeRef'],
        targetId=lun_map['mapRef'],
        lun=lun_map['lun']
    ))

    rc, data = request(url, data=post_body, method='POST', url_username=user, url_password=pwd, headers=HEADERS,
                       ignore_errors=True)

    if rc == 422:
        data = move_lun(module, ssid, lun_map, vol_name, api_url, user, pwd)
        # module.fail_json(msg="The volume you specified '%s' is already "
        #                      "part of a different LUN mapping. If you "
        #                      "want to move it to a different host or "
        #                      "hostgroup, then please use the "
        #                      "netapp_e_move_lun module" % vol_name)
    return data


def move_lun(module, ssid, lun_map, vol_name, api_url, user, pwd):
    lun_id = get_lun_id(module, ssid, lun_map, api_url, user, pwd)
    move_lun = "storage-systems/%s/volume-mappings/%s/move" % (ssid, lun_id)
    url = api_url + move_lun
    post_body = json.dumps(dict(targetId=lun_map['mapRef'], lun=lun_map['lun']))
    rc, data = request(url, data=post_body, method='POST', url_username=user, url_password=pwd, headers=HEADERS)
    return data


def get_lun_id(module, ssid, lun_mapping, api_url, user, pwd):
    data = get_lun_mappings(ssid, api_url, user, pwd, get_all=True)

    for lun_map in data:
        if lun_map['volumeRef'] == lun_mapping['volumeRef']:
            return lun_map['id']
    # This shouldn't ever get called
    module.fail_json(msg="No LUN map found.")


def remove_mapping(module, ssid, lun_mapping, api_url, user, pwd):
    lun_id = get_lun_id(module, ssid, lun_mapping, api_url, user, pwd)
    lun_del = "storage-systems/%s/volume-mappings/%s" % (ssid, lun_id)
    url = api_url + lun_del
    rc, data = request(url, method='DELETE', url_username=user, url_password=pwd, headers=HEADERS)
    return data


def main():
    argument_spec = basic_auth_argument_spec()
    argument_spec.update(dict(
        api_username=dict(type='str', required=True),
        api_password=dict(type='str', required=True, no_log=True),
        api_url=dict(type='str', required=True),
        state=dict(required=True, choices=['present', 'absent']),
        target=dict(required=False, default=None),
        target_type=dict(required=False, choices=['host', 'group']),
        lun=dict(required=False, type='int', default=0),
        ssid=dict(required=False),
        volume_name=dict(required=True),
    ))

    module = AnsibleModule(argument_spec=argument_spec)

    state = module.params['state']
    target = module.params['target']
    target_type = module.params['target_type']
    lun = module.params['lun']
    ssid = module.params['ssid']
    vol_name = module.params['volume_name']
    user = module.params['api_username']
    pwd = module.params['api_password']
    api_url = module.params['api_url']

    if not api_url.endswith('/'):
        api_url += '/'

    volume_map = get_volumes(module, ssid, api_url, user, pwd, "volumes")
    thin_volume_map = get_volumes(module, ssid, api_url, user, pwd, "thin-volumes")
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

    host_and_group_mapping = get_host_and_group_map(module, ssid, api_url, user, pwd)

    desired_lun_mapping = dict(
        mapRef=host_and_group_mapping[target_type][target],
        lun=lun,
        volumeRef=volref
    )

    lun_mappings = get_lun_mappings(ssid, api_url, user, pwd)

    if state == 'present':
        if desired_lun_mapping in lun_mappings:
            module.exit_json(changed=False, msg="Mapping exists")
        else:
            result = create_mapping(module, ssid, desired_lun_mapping, vol_name, api_url, user, pwd)
            module.exit_json(changed=True, **result)

    elif state == 'absent':
        if desired_lun_mapping in lun_mappings:
            result = remove_mapping(module, ssid, desired_lun_mapping, api_url, user, pwd)
            module.exit_json(changed=True, msg="Mapping removed")
        else:
            module.exit_json(changed=False, msg="Mapping absent")


if __name__ == '__main__':
    main()
