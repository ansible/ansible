#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2018, Mikhail Yohman (fragmentedpacket) <mikhail.yohman@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = r'''
PLACEHOLDER FOR DOCUMENTATION
'''


from ansible.module_utils.basic import AnsibleModule
try:
    import pynetbox
    HAS_PYNETBOX = True
except ImportError:
    HAS_PYNETBOX = False

import json

search_type = dict(
    prefixes="q",
    ip_addresses="q",
    devices="name",
    device_types="slug",
    device_roles="slug",
    sites="slug",
)


def find_id(nb_app, endpoint, search):
    nb_endpoint = getattr(nb_app, endpoint)
    results = nb_endpoint.get(**{search_type.get(endpoint, "q"): search})
    if results:
        return results.id
    else:
        return 1


def netbox_add(nb_app, nb_endpoint, data):
    clean_json = data.replace("'", '"')
    data = json.loads(clean_json)
    data = normalize_data(data)
    site = find_id(nb_app, "sites", data.get("site"))
    device_role = find_id(nb_app, "device_roles", data.get("device_role"))
    device_type = find_id(nb_app, "device_types", data.get("device_type"))
    data["status"] = 1 if data.get("status").lower() == "active" else 0
    data["site"] = site
    data["device_role"] = device_role
    data["device_type"] = device_type
    try:
        return [nb_endpoint.create([data])]
    except pynetbox.RequestError as e:
        return e.error


def normalize_data(data):
    for k, v in data.items():
        if 'device_role' in k:
            if ' ' in v:
                data[k] = v.replace(' ', '-').lower()
        elif 'device_type' in k:
            if ' ' in v:
                data[k] = v.replace(' ', '-').lower()
        elif 'site' in k:
            if ' ' in v:
                data[k] = v.replace(' ', '-').lower()
        elif 'status' in k:
                data[k] = v.lower()
        elif 'tags' in k:
            if not isinstance(v, list):
                temp_list = []
                temp_list.append(v)
                v = temp_list
                data[k] = v
    return data


def main():
    module = AnsibleModule(
        argument_spec=dict(
            url=dict(type="str", required=True),
            token=dict(type="str", required=True),
            data=dict(type="str", required=True),
        )
    )
    if not HAS_PYNETBOX:
        module.fail_json(msg='pynetbox is required for this module')

    app = 'dcim'
    endpoint = 'devices'
    url = module.params["url"]
    token = module.params["token"]
    data = module.params["data"]
    nb = pynetbox.api(url, token=token)
    nb_app = getattr(nb, app)
    nb_endpoint = getattr(nb_app, endpoint)
    response = netbox_add(nb_app, nb_endpoint, data)

    module.exit_json(changed=False, meta=response)


if __name__ == "__main__":
    main()

