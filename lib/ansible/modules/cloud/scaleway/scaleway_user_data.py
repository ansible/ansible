#!/usr/bin/python
#
# Scaleway user data management module
#
# Copyright (C) 2018 Online SAS.
# https://www.scaleway.com
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: scaleway_user_data
short_description: Scaleway user_data management module
version_added: "2.8"
author: Remy Leone (@sieben)
description:
    - "This module manages user_data on compute instances on Scaleway."
    - "It can be used to configure cloud-init for instance"
extends_documentation_fragment: scaleway

options:

  server_id:
    description:
    - Scaleway Compute instance ID of the server
    required: true

  user_data:
    description:
    - User defined data. Typically used for C(cloud-init).
    - Pass your cloud-init script here as a string to the C(cloud-init) key.
    - If you want to delete a key assign null to the key you want to delete
    required: false
    type: dict
    default: {}

  region:
    description:
    - Scaleway compute zone
    required: true
    choices:
      - ams1
      - EMEA-NL-EVS
      - par1
      - EMEA-FR-PAR1
'''

EXAMPLES = '''
- name: Update the cloud-init
  scaleway_user_data:
    server_id: '5a33b4ab-57dd-4eb6-8b0a-d95eb63492ce'
    region: ams1
    user_data:
      cloud-init: 'final_message: "Hello World!"'

# If you want to delete a key apply null to the key you want to delete
- name: Update the cloud-init
  scaleway_user_data:
    server_id: '5a33b4ab-57dd-4eb6-8b0a-d95eb63492ce'
    region: ams1
    user_data:
      cloud-init: null
'''

RETURN = '''
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.scaleway import SCALEWAY_LOCATION, scaleway_argument_spec, Scaleway


def patch_user_data(compute_api, server_id, key, value):
    compute_api.module.debug("Starting patching user_data attributes")
    path = "servers/%s/user_data/%s" % (server_id, key)
    response = compute_api.patch(path=path, data=value, headers={"Content-type": "text/plain"})
    if not response.ok:
        msg = 'Error during user_data patching: %s %s' % (response.status_code, response.body)
        compute_api.module.fail_json(msg=msg)


def delete_user_data(compute_api, server_id, key):
    compute_api.module.debug("Starting deleting user_data attributes: %s" % key)

    response = compute_api.delete(path="servers/%s/user_data/%s" % (server_id, key))

    if not response.ok:
        msg = 'Error during user_data deleting: (%s) %s' % (response.status_code, response.body)
        compute_api.module.fail_json(msg=msg)


def get_user_data(compute_api, server_id, key):
    compute_api.module.debug("Starting patching user_data attributes")

    path = "servers/%s/user_data/%s" % (server_id, key)
    response = compute_api.get(path=path)
    if not response.ok:
        msg = 'Error during user_data patching: %s %s' % (response.status_code, response.body)
        compute_api.module.fail_json(msg=msg)

    return response.body


def lookup_user_data(compute_api, server_id):
    user_data_list = compute_api.get(path="servers/%s/user_data" % server_id)
    if not user_data_list.ok:
        msg = 'Error during user_data fetching: %s %s' % (user_data_list.status_code, user_data_list.body)
        compute_api.module.fail_json(msg=msg)

    present_user_data_keys = user_data_list.json["user_data"]
    return dict(
        (key, get_user_data(compute_api=compute_api, server_id=server_id, key=key))
        for key in present_user_data_keys
    )


def core(module):
    region = module.params["region"]
    server_id = module.params["server_id"]
    user_data = module.params["user_data"]
    changed = False

    module.params['api_url'] = SCALEWAY_LOCATION[region]["api_endpoint"]
    compute_api = Scaleway(module=module)

    lookup = lookup_user_data(compute_api=compute_api, server_id=server_id)

    compute_api.module.debug("lookup: %s" % lookup)
    compute_api.module.debug("user_data: %s" % user_data)
    if lookup == user_data:
        module.exit_json(changed=changed, scaleway_user_data=lookup)

    # We apply a merge strategy for the items
    for user_data_key, user_data_value in user_data.items():

        # Keys we want to delete
        if user_data_key in lookup.keys() and user_data_value is None:
            changed = True
            if compute_api.module.check_mode:
                module.exit_json(changed=changed, msg={"status": "User-data of %s would be deleted." % server_id})

            delete_user_data(compute_api=compute_api, server_id=server_id, key=user_data_key)
            continue

        # Keys we want to patch
        if user_data_value is not None and (user_data_key not in lookup or user_data[user_data_key] != lookup[user_data_key]):
            changed = True
            if compute_api.module.check_mode:
                module.exit_json(changed=changed, msg={"status": "User-data of %s would be patched." % server_id})

            patch_user_data(compute_api=compute_api, server_id=server_id, key=user_data_key, value=user_data_value)

    # We return the complete set of keys
    confirmation_lookup = lookup_user_data(compute_api=compute_api, server_id=server_id)
    module.exit_json(changed=changed, scaleway_user_data=confirmation_lookup)


def main():
    argument_spec = scaleway_argument_spec()
    argument_spec.update(dict(
        region=dict(required=True, choices=SCALEWAY_LOCATION.keys()),
        user_data=dict(type="dict", default={}),
        server_id=dict(required=True),
    ))
    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    core(module)


if __name__ == '__main__':
    main()
