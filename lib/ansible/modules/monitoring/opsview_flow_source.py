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

DOCUMENTATION = """\
---
module: opsview_flow_source
short_description: Manages Opsview sFlow and NetFlow sources
description:
  - Manages sFlow and NetFlow sources in Opsview.
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
      - Must correspond with the host name in Opsview.
    required: true
  collector:
    description:
      - The name of the flow collector as configured in Opsview.
    required: true
  flow_type:
    description:
      - The flow protocol to be used.
    choices: [netflow, sflow]
    default: netflow
  alt_address:
    description:
      - IP address from which flow data will be received if different from the
        address stored for the host in Opsview.
"""

EXAMPLES = """
---
- name: Create Flow Source in Opsview
  opsview_flow_source:
    username: admin
    password: initial
    endpoint: https://opsview.example.com
    state: updated
    name: cisco-uk-01
    flow_type: sflow
    alt_address: 10.0.17.24
    collector: Master Collector
"""

RETURN = """
---
object_id:
  description: ID of the object in Opsview.
  returned: When not check_mode.
  type: int
"""

import functools
import traceback

from ansible.module_utils import opsview as ov
from ansible.module_utils.basic import to_native
from ansible.module_utils.six import iteritems

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
        "required": True,
    },
    "collector": {
        "required": True,
    },
    "flow_type": {
        "default": "netflow",
        "choices": ["netflow", "sflow"],
    },
    "alt_address": {},
}


def _hook_trans_payload(params, opsview_client, module):
    if 'collector' in params and 'collector_id' not in params:
        # Get the collector by name
        collector = opsview_client.config.flowcollectors\
            .find_one(name=params['collector'])

        if not collector:
            module.fail_json(msg='No flow collector exists with name \'%s\'' %
                             params['collector'])

        # Set the collector ID and unset the collector name
        params['collector_id'] = collector.get('id')

    # Ensure that the flow type is lowercased
    params['flow_type'] = params['flow_type'].lower()

    if 'host_id' not in params:
        # Get the IP address of the host by name
        host = opsview_client.config.hosts.find_one(name=params['name'])
        if not host:
            module.fail_json(msg='No host exists with name \'%s\'' %
                             params['name'])

        # Set the host ID
        params['host_id'] = host.get('id')

    if 'address' not in params:
        # Set the host IP address and set the override flag if necessary
        src_addr = params.get('alt_address')
        if not src_addr:
            src_addr = host['address']

        params['ip_override'] = (src_addr != host['address'])
        params['address'] = src_addr

    for field in ('collector', 'name', 'alt_address'):
        try:
            del params[field]
        except KeyError:
            pass

    return params


def module_main(module):
    opsview_client = ov.new_opsview_client(
        username=module.params['username'],
        password=module.params['password'],
        endpoint=module.params['endpoint'],
        token=module.params['token'],
        verify=module.params['verify_ssl'],
    )

    # Wrap up the hook function to already have the module and opsview client
    hook_trans_payload = functools.partial(_hook_trans_payload, module=module,
                                           opsview_client=opsview_client)

    config_manager = ov.get_config_manager(opsview_client, 'flowsources')

    # if finding the flow source by name, must first find the host and then
    # find the associated flow source
    if module.params.get('object_id'):
        identity = {'id': module.params['object_id']}

    elif module.params.get('name'):
        host_manager = ov.get_config_manager(opsview_client, 'hosts')
        host_identity = {'name': module.params['name']}
        host = ov.find_existing_object(host_manager, host_identity)
        if host and 'id' in host:
            identity = {'host_id': host['id']}
        else:
            identity = None
    else:
        raise ValueError("'name' or 'object_id' must be specified")

    if identity:
        existing_object = ov.find_existing_object(config_manager, identity)
    else:
        existing_object = None

    if module.params['state'] == 'absent':
        return ov.ensure_absent(config_manager, existing_object,
                                check_mode=module.check_mode)

    payload = ov.create_object_payload(
        module.params, payload_finalize_hook=hook_trans_payload
    )

    if module.params['state'] == 'present':
        return ov.ensure_present(config_manager, existing_object, payload,
                                 check_mode=module.check_mode)

    elif module.params['state'] == 'updated':
        return ov.ensure_updated(config_manager, existing_object, payload,
                                 pre_compare_hook=hook_trans_payload,
                                 check_mode=module.check_mode)

    raise ValueError("Unknown value for 'state': '%s'" %
                     module.params['state'])


def main():
    module = ov.new_module(ARG_SPEC)
    # Handle exception importing 'pyopsview'
    if ov.PYOV_IMPORT_EXC is not None:
        module.fail_json(msg=ov.PYOV_IMPORT_EXC[0],
                         exception=ov.PYOV_IMPORT_EXC[1])

    try:
        summary = module_main(module)
    except Exception as e:
        module.fail_json(msg=to_native(e), exception=traceback.format_exc())

    module.exit_json(**summary)


if __name__ == '__main__':
    main()
