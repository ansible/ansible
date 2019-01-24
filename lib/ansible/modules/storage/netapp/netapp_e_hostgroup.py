#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2016, NetApp, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: netapp_e_hostgroup
version_added: "2.2"
short_description: NetApp E-Series manage array host groups
author: Kevin Hulquest (@hulquest)
description:
- Create, update or destroy host groups on a NetApp E-Series storage array.
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
    - Whether the specified host group should exist or not.
    choices: ['present', 'absent']
  name:
    required: false
    description:
    - The name of the host group to manage. Either this or C(id_num) must be supplied.
  new_name:
    required: false
    description:
    - specify this when you need to update the name of a host group
  id:
    required: false
    description:
    - The id number of the host group to manage. Either this or C(name) must be supplied.
  hosts:
    required: false
    description:
    - a list of host names/labels to add to the group
'''
EXAMPLES = '''
    - name: Configure Hostgroup
      netapp_e_hostgroup:
        ssid: "{{ ssid }}"
        api_url: "{{ netapp_api_url }}"
        api_username: "{{ netapp_api_username }}"
        api_password: "{{ netapp_api_password }}"
        validate_certs: "{{ netapp_api_validate_certs }}"
        state: present
'''
RETURN = '''
clusterRef:
    description: The unique identification value for this object. Other objects may use this reference value to refer to the cluster.
    returned: always except when state is absent
    type: str
    sample: "3233343536373839303132333100000000000000"
confirmLUNMappingCreation:
    description: If true, indicates that creation of LUN-to-volume mappings should require careful confirmation from the end-user, since such a mapping
                 will alter the volume access rights of other clusters, in addition to this one.
    returned: always
    type: bool
    sample: false
hosts:
    description: A list of the hosts that are part of the host group after all operations.
    returned: always except when state is absent
    type: list
    sample: ["HostA","HostB"]
id:
    description: The id number of the hostgroup
    returned: always except when state is absent
    type: str
    sample: "3233343536373839303132333100000000000000"
isSAControlled:
    description: If true, indicates that I/O accesses from this cluster are subject to the storage array's default LUN-to-volume mappings. If false,
                 indicates that I/O accesses from the cluster are subject to cluster-specific LUN-to-volume mappings.
    returned: always except when state is absent
    type: bool
    sample: false
label:
    description: The user-assigned, descriptive label string for the cluster.
    returned: always
    type: str
    sample: "MyHostGroup"
name:
    description: same as label
    returned: always except when state is absent
    type: str
    sample: "MyHostGroup"
protectionInformationCapableAccessMethod:
    description: This field is true if the host has a PI capable access method.
    returned: always except when state is absent
    type: bool
    sample: true
'''

HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json"
}

import json

from ansible.module_utils.basic import AnsibleModule
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
    except HTTPError as e:
        r = e.fp

    try:
        raw_data = r.read()
        if raw_data:
            data = json.loads(raw_data)
        else:
            raw_data = None
    except Exception:
        if ignore_errors:
            pass
        else:
            raise Exception(raw_data)

    resp_code = r.getcode()

    if resp_code >= 400 and not ignore_errors:
        raise Exception(resp_code, data)
    else:
        return resp_code, data


def group_exists(module, id_type, ident, ssid, api_url, user, pwd):
    rc, data = get_hostgroups(module, ssid, api_url, user, pwd)
    for group in data:
        if group[id_type] == ident:
            return True, data
        else:
            continue

    return False, data


def get_hostgroups(module, ssid, api_url, user, pwd):
    groups = "storage-systems/%s/host-groups" % ssid
    url = api_url + groups
    try:
        rc, data = request(url, headers=HEADERS, url_username=user, url_password=pwd)
        return rc, data
    except HTTPError as e:
        module.fail_json(msg="Failed to get host groups. Id [%s]. Error [%s]." % (ssid, to_native(e)))


def get_hostref(module, ssid, name, api_url, user, pwd):
    all_hosts = 'storage-systems/%s/hosts' % ssid
    url = api_url + all_hosts
    try:
        rc, data = request(url, method='GET', headers=HEADERS, url_username=user, url_password=pwd)
    except Exception as e:
        module.fail_json(msg="Failed to get hosts. Id [%s]. Error [%s]." % (ssid, to_native(e)))

    for host in data:
        if host['name'] == name:
            return host['hostRef']
        else:
            continue

    module.fail_json(msg="No host with the name %s could be found" % name)


def create_hostgroup(module, ssid, name, api_url, user, pwd, hosts=None):
    groups = "storage-systems/%s/host-groups" % ssid
    url = api_url + groups
    hostrefs = []

    if hosts:
        for host in hosts:
            href = get_hostref(module, ssid, host, api_url, user, pwd)
            hostrefs.append(href)

    post_data = json.dumps(dict(name=name, hosts=hostrefs))
    try:
        rc, data = request(url, method='POST', data=post_data, headers=HEADERS, url_username=user, url_password=pwd)
    except Exception as e:
        module.fail_json(msg="Failed to create host group. Id [%s]. Error [%s]." % (ssid, to_native(e)))

    return rc, data


def update_hostgroup(module, ssid, name, api_url, user, pwd, hosts=None, new_name=None):
    gid = get_hostgroup_id(module, ssid, name, api_url, user, pwd)
    groups = "storage-systems/%s/host-groups/%s" % (ssid, gid)
    url = api_url + groups
    hostrefs = []

    if hosts:
        for host in hosts:
            href = get_hostref(module, ssid, host, api_url, user, pwd)
            hostrefs.append(href)

    if new_name:
        post_data = json.dumps(dict(name=new_name, hosts=hostrefs))
    else:
        post_data = json.dumps(dict(hosts=hostrefs))

    try:
        rc, data = request(url, method='POST', data=post_data, headers=HEADERS, url_username=user, url_password=pwd)
    except Exception as e:
        module.fail_json(msg="Failed to update host group. Group [%s]. Id [%s]. Error [%s]." % (gid, ssid,
                                                                                                to_native(e)))

    return rc, data


def delete_hostgroup(module, ssid, group_id, api_url, user, pwd):
    groups = "storage-systems/%s/host-groups/%s" % (ssid, group_id)
    url = api_url + groups
    # TODO: Loop through hosts, do mapping to href, make new list to pass to data
    try:
        rc, data = request(url, method='DELETE', headers=HEADERS, url_username=user, url_password=pwd)
    except Exception as e:
        module.fail_json(msg="Failed to delete host group. Group [%s]. Id [%s]. Error [%s]." % (group_id, ssid, to_native(e)))

    return rc, data


def get_hostgroup_id(module, ssid, name, api_url, user, pwd):
    all_groups = 'storage-systems/%s/host-groups' % ssid
    url = api_url + all_groups
    rc, data = request(url, method='GET', headers=HEADERS, url_username=user, url_password=pwd)
    for hg in data:
        if hg['name'] == name:
            return hg['id']
        else:
            continue

    module.fail_json(msg="A hostgroup with the name %s could not be found" % name)


def get_hosts_in_group(module, ssid, group_name, api_url, user, pwd):
    all_groups = 'storage-systems/%s/host-groups' % ssid
    g_url = api_url + all_groups
    try:
        g_rc, g_data = request(g_url, method='GET', headers=HEADERS, url_username=user, url_password=pwd)
    except Exception as e:
        module.fail_json(
            msg="Failed in first step getting hosts from group. Group: [%s]. Id [%s]. Error [%s]." % (group_name,
                                                                                                      ssid,
                                                                                                      to_native(e)))

    all_hosts = 'storage-systems/%s/hosts' % ssid
    h_url = api_url + all_hosts
    try:
        h_rc, h_data = request(h_url, method='GET', headers=HEADERS, url_username=user, url_password=pwd)
    except Exception as e:
        module.fail_json(
            msg="Failed in second step getting hosts from group. Group: [%s]. Id [%s]. Error [%s]." % (
                group_name,
                ssid,
                to_native(e)))

    hosts_in_group = []

    for hg in g_data:
        if hg['name'] == group_name:
            clusterRef = hg['clusterRef']

    for host in h_data:
        if host['clusterRef'] == clusterRef:
            hosts_in_group.append(host['name'])

    return hosts_in_group


def main():
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(required=False),
            new_name=dict(required=False),
            ssid=dict(required=True),
            id=dict(required=False),
            state=dict(required=True, choices=['present', 'absent']),
            hosts=dict(required=False, type='list'),
            api_url=dict(required=True),
            api_username=dict(required=True),
            validate_certs=dict(required=False, default=True),
            api_password=dict(required=True, no_log=True)
        ),
        supports_check_mode=False,
        mutually_exclusive=[['name', 'id']],
        required_one_of=[['name', 'id']]
    )

    name = module.params['name']
    new_name = module.params['new_name']
    ssid = module.params['ssid']
    id_num = module.params['id']
    state = module.params['state']
    hosts = module.params['hosts']
    user = module.params['api_username']
    pwd = module.params['api_password']
    api_url = module.params['api_url']

    if not api_url.endswith('/'):
        api_url += '/'

    if name:
        id_type = 'name'
        id_key = name
    elif id_num:
        id_type = 'id'
        id_key = id_num

    exists, group_data = group_exists(module, id_type, id_key, ssid, api_url, user, pwd)

    if state == 'present':
        if not exists:
            try:
                rc, data = create_hostgroup(module, ssid, name, api_url, user, pwd, hosts)
            except Exception as e:
                module.fail_json(msg="Failed to create a host group. Id [%s]. Error [%s]." % (ssid, to_native(e)))

            hosts = get_hosts_in_group(module, ssid, name, api_url, user, pwd)
            module.exit_json(changed=True, hosts=hosts, **data)
        else:
            current_hosts = get_hosts_in_group(module, ssid, name, api_url, user, pwd)

            if not current_hosts:
                current_hosts = []

            if not hosts:
                hosts = []

            if set(current_hosts) != set(hosts):
                try:
                    rc, data = update_hostgroup(module, ssid, name, api_url, user, pwd, hosts, new_name)
                except Exception as e:
                    module.fail_json(
                        msg="Failed to update host group. Group: [%s]. Id [%s]. Error [%s]." % (name, ssid, to_native(e)))
                module.exit_json(changed=True, hosts=hosts, **data)
            else:
                for group in group_data:
                    if group['name'] == name:
                        module.exit_json(changed=False, hosts=current_hosts, **group)

    elif state == 'absent':
        if exists:
            hg_id = get_hostgroup_id(module, ssid, name, api_url, user, pwd)
            try:
                rc, data = delete_hostgroup(module, ssid, hg_id, api_url, user, pwd)
            except Exception as e:
                module.fail_json(
                    msg="Failed to delete host group. Group: [%s]. Id [%s]. Error [%s]." % (name, ssid, to_native(e)))

            module.exit_json(changed=True, msg="Host Group deleted")
        else:
            module.exit_json(changed=False, msg="Host Group is already absent")


if __name__ == '__main__':
    main()
