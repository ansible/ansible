#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2017, Opsview Ltd.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = """
---
module: opsview_monitoring_server
short_description: Manages Opsview Monitoring Servers
description:
  - Manages Monitoring Servers within Opsview.
version_added: '2.5'
author: Joshua Griffiths (@jpgxs)
requirements: [pyopsview]
options:
  username:
    description:
      - Username for the Opsview API.
    required: true
  endpoint:
    description:
      - Opsview API endpoint, including schema.
      - The C(/rest) suffix is optional.
    required: true
  token:
    description:
      - API token, usually returned by the C(opsview_login) module.
      - Required unless C(password) is specified.
  password:
    description:
      - Password for the Opsview API.
  verify_ssl:
    description:
      - Enable SSL verification for HTTPS endpoints.
      - Alternatively, a path to a CA can be provided.
    default: 'yes'
  state:
    description:
      - C(present) and C(updated) will create the object if it doesn't exist.
      - C(updated) will ensure that the object attributes are up to date with
        the given options.
      - C(absent) will ensure that the object is removed if it exists.
      - The object is identified by C(object_id) if specified. Otherwise, it is
        identified by C(name)
    choices: [updated, present, absent]
    default: updated
  object_id:
    description:
      - The internal ID of the object. If specified, the object will be
        found by ID instead of by C(name).
      - Usually only useful for renaming objects.
  name:
    description:
      - Unique name for the object. Will be used to identify existing objects
        unless C(object_id) is specified.
    required: true
  nodes:
    description:
      - List of Opsview host names to add to this cluster.
    required: true
  ssh_forward:
    description:
      - Initiate the SSH connection on the master monitoring server rather than
        the slave.
    default: 'yes'
    choices: ['yes', 'no']
"""

EXAMPLES = """
---
- name: Create Monitoring Server in Opsview
  opsview_monitoring_server:
    username: admin
    password: initial
    endpoint: https://opsview.example.com
    state: updated
    name: cluster-1
    nodes:
      - ov-mon-01
      - ov-mon-02
      - ov-mon-03
      - ov-mon-04
"""

RETURN = """
---
object_id:
  description: ID of the object in Opsview.
  returned: When not check_mode.
  type: int
"""

import traceback

from ansible.module_utils import opsview as ov
from ansible.module_utils.basic import to_native
from ansible.module_utils.six import string_types

ARG_SPEC = {
    "username": {
        "required": True
    },
    "endpoint": {
        "required": True
    },
    "password": {
        "no_log": True
    },
    "token": {
        "no_log": True
    },
    "verify_ssl": {
        "default": True
    },
    "state": {
        "choices": [
            "updated",
            "present",
            "absent"
        ],
        "default": "updated"
    },
    "object_id": {
        "type": "int"
    },
    "name": {
        "required": True
    },
    "nodes": {
        "required": True,
        "type": "list",
    },
    "ssh_forward": {
        "default": True,
        "type": "bool"
    }
}


def hook_trans_compare(params):
    if params['nodes']:
        # The API returns the nodes in a different format to the one it expects
        nodes_full = []
        for node in params['nodes']:
            if isinstance(node, string_types):
                nodes_full.append({'host': {'name': node}})
            elif isinstance(node, dict) and 'name' in node:
                nodes_full.append({'host': {'name': node['name']}})
            else:
                # Don't know what format this is... Try anyway.
                nodes_full.append(node)

        params['nodes'] = nodes_full

    return params


def hook_trans_payload(params):
    nodes_full = []
    for node in params.get('nodes', []):
        if isinstance(node, string_types):
            nodes_full.append({'name': node})
        else:
            nodes_full.append(node)

    params['nodes'] = nodes_full
    return params


def main():
    module = ov.new_module(ARG_SPEC)
    # Handle exception importing 'pyopsview'
    if ov.PYOV_IMPORT_EXC is not None:
        module.fail_json(msg=ov.PYOV_IMPORT_EXC[0],
                         exception=ov.PYOV_IMPORT_EXC[1])

    try:
        summary = ov.config_module_main(
            module, 'monitoringservers',
            pre_compare_hook=hook_trans_compare,
            payload_finalize_hook=hook_trans_payload
        )
    except Exception as e:
        module.fail_json(msg=to_native(e), exception=traceback.format_exc())

    module.exit_json(**summary)


if __name__ == '__main__':
    main()
