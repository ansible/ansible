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
    - User defined data. Typically used with `cloud-init`.
    - Pass your cloud-init script here as a string
    required: false

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

    return response


def delete_user_data(compute_api, server_id, key):
    compute_api.module.debug("Starting deleting user_data attributes: %s" % key)

    response = compute_api.delete(path="servers/%s/user_data/%s" % (server_id, key))

    if not response.ok:
        msg = 'Error during user_data deleting: (%s) %s' % response.status_code, response.body
        compute_api.module.fail_json(msg=msg)

    return response


def get_user_data(compute_api, server_id, key):
    compute_api.module.debug("Starting patching user_data attributes")

    path = "servers/%s/user_data/%s" % (server_id, key)
    response = compute_api.get(path=path)
    if not response.ok:
        msg = 'Error during user_data patching: %s %s' % (response.status_code, response.body)
        compute_api.module.fail_json(msg=msg)

    return response.json


def core(module):
    region = module.params["region"]
    server_id = module.params["server_id"]
    user_data = module.params["user_data"]
    changed = False

    module.params['api_url'] = SCALEWAY_LOCATION[region]["api_endpoint"]
    compute_api = Scaleway(module=module)

    user_data_list = compute_api.get(path="servers/%s/user_data" % server_id)
    if not user_data_list.ok:
        msg = 'Error during user_data fetching: %s %s' % user_data_list.status_code, user_data_list.body
        compute_api.module.fail_json(msg=msg)

    present_user_data_keys = user_data_list.json["user_data"]
    present_user_data = dict(
        (key, get_user_data(compute_api=compute_api, server_id=server_id, key=key))
        for key in present_user_data_keys
    )

    if present_user_data == user_data:
        module.exit_json(changed=changed, msg=user_data_list.json)

    # First we remove keys that are not defined in the wished user_data
    for key in present_user_data:
        if key not in user_data:

            changed = True
            if compute_api.module.check_mode:
                module.exit_json(changed=changed, msg={"status": "User-data of %s would be patched." % server_id})

            delete_user_data(compute_api=compute_api, server_id=server_id, key=key)

    # Then we patch keys that are different
    for key, value in user_data.items():
        if key not in present_user_data or user_data[key] != present_user_data[key]:

            changed = True
            if compute_api.module.check_mode:
                module.exit_json(changed=changed, msg={"status": "User-data of %s would be patched." % server_id})

            patch_user_data(compute_api=compute_api, server_id=server_id, key=key, value=value)

    module.exit_json(changed=changed, msg=user_data)


def main():
    argument_spec = scaleway_argument_spec()
    argument_spec.update(dict(
        region=dict(required=True, choices=SCALEWAY_LOCATION.keys()),
        user_data=dict(type="dict"),
        server_id=dict(required=True),
    ))
    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    core(module)


if __name__ == '__main__':
    main()
