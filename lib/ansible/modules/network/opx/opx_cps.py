#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2018 Dell Inc. or its subsidiaries. All Rights Reserved.
#
# This file is part of Ansible by Red Hat
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

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = """
---
module: opx_cps
version_added: "2.7"
author: "Senthil Kumar Ganesan (@skg-net)"
short_description: CPS operations on networking device running Openswitch (OPX)
description:
  -  Executes the given operation on the YANG object, using CPS API in the
     networking device running OpenSwitch (OPX). It uses the YANG models
     provided in https://github.com/open-switch/opx-base-model.
options:
  module_name:
    description:
      - Yang path to be configured.
  attr_type:
    description:
      - Attribute Yang type.
  attr_data:
    description:
      - Attribute Yang path and their corresponding data.
  operation:
    description:
      - Operation to be performed on the object.
    default: create
    choices: ['delete', 'create', 'set', 'action', 'get']
  db:
    description:
      - Queries/Writes the specified yang path from/to the db.
    type: bool
    default: 'no'
  qualifier:
    description:
      - A qualifier provides the type of object data to retrieve or act on.
    default: target
    choices: ['target', 'observed', 'proposed', 'realtime', 'registration', 'running', 'startup']
  commit_event:
    description:
      - Attempts to force the auto-commit event to the specified yang object.
    type: bool
    default: 'no'
requirements:
    - "cps"
    - "cps_object"
    - "cps_utils"
"""

EXAMPLES = """
- name: Create VLAN
  opx_cps:
    module_name: "dell-base-if-cmn/if/interfaces/interface"
    attr_data: {
         "base-if-vlan/if/interfaces/interface/id": 230,
         "if/interfaces/interface/name": "br230",
         "if/interfaces/interface/type": "ianaift:l2vlan"
    }
    operation: "create"
- name: Get VLAN
  opx_cps:
    module_name: "dell-base-if-cmn/if/interfaces/interface"
    attr_data: {
         "if/interfaces/interface/name": "br230",
    }
    operation: "get"
- name: Modify some attributes in VLAN
  opx_cps:
    module_name: "dell-base-if-cmn/if/interfaces/interface"
    attr_data: {
         "cps/key_data":
            { "if/interfaces/interface/name": "br230" },
         "dell-if/if/interfaces/interface/untagged-ports": ["e101-008-0"],
    }
    operation: "set"
- name: Delete VLAN
  opx_cps:
    module_name: "dell-base-if-cmn/if/interfaces/interface"
    attr_data: {
         "if/interfaces/interface/name": "br230",
    }
    operation: "delete"
"""

RETURN = """
response:
  description: Output from the CPS transaction.
               Output of CPS Get operation if CPS set/create/delete not done.
  returned: when a CPS transaction is successfully performed.
  type: list
  sample:
    [{
        "data": {
            "base-if-vlan/if/interfaces/interface/id": 230,
            "cps/object-group/return-code": 0,
            "dell-base-if-cmn/if/interfaces/interface/if-index": 46,
            "if/interfaces/interface/name": "br230",
            "if/interfaces/interface/type": "ianaift:l2vlan"
        },
        "key": "target/dell-base-if-cmn/if/interfaces/interface"
    }]
cps_curr_config:
  description: Returns the CPS Get output i.e. the running configuration
               before CPS operation of set/delete is performed
  returned: when CPS operations set, delete
  type: dict
  sample:
    [{
        "data": {
            "base-if-vlan/if/interfaces/interface/id": 230,
            "cps/key_data": {
                "if/interfaces/interface/name": "br230"
            },
            "dell-base-if-cmn/if/interfaces/interface/if-index": 44,
            "dell-if/if/interfaces/interface/learning-mode": 1,
            "dell-if/if/interfaces/interface/mtu": 1532,
            "dell-if/if/interfaces/interface/phys-address": "",
            "dell-if/if/interfaces/interface/vlan-type": 1,
            "if/interfaces/interface/enabled": 0,
            "if/interfaces/interface/type": "ianaift:l2vlan"
        },
        "key": "target/dell-base-if-cmn/if/interfaces/interface"
    }]
diff:
  description: The actual configuration that will be pushed comparing
               the running configuration and input attributes
  returned: when CPS operations set, delete
  type: dict
  sample:
    {
        "cps/key_data": {
            "if/interfaces/interface/name": "br230"
        },
        "dell-if/if/interfaces/interface/untagged-ports": [
            "e101-007-0"
        ]
    }
db:
  description: Denotes if CPS DB transaction was performed
  returned: when db is set to True in module options
  type: bool
  sample: True
commit_event:
  description: Denotes if auto-commit event is set
  returned: when commit_event is set to True in module options
  type: bool
  sample: True
"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.six import iteritems
from ansible.module_utils.network.common.utils import dict_diff

try:
    import cps
    import cps_object
    import cps_utils
    HAS_CPS = True
except ImportError:
    HAS_CPS = False


def convert_cps_raw_list(raw_list):
    resp_list = []
    if raw_list:
        for raw_elem in raw_list:
            processed_element = convert_cps_raw_data(raw_elem)
            if processed_element:
                raw_key = raw_elem['key']
                individual_element = {}
                individual_element['data'] = processed_element
                individual_element['key'] = (cps.qual_from_key(raw_key) + "/" +
                                             cps.name_from_key(raw_key, 1))
                resp_list.append(individual_element)
    return resp_list


def convert_cps_raw_data(raw_elem):
    d = {}
    obj = cps_object.CPSObject(obj=raw_elem)
    for attr in raw_elem['data']:
        d[attr] = obj.get_attr_data(attr)
    return d


def parse_cps_parameters(module_name, qualifier, attr_type,
                         attr_data, operation=None, db=None,
                         commit_event=None):

    obj = cps_object.CPSObject(module=module_name, qual=qualifier)

    if operation:
        obj.set_property('oper', operation)

    if attr_type:
        for key, val in iteritems(attr_type):
            cps_utils.cps_attr_types_map.add_type(key, val)

    for key, val in iteritems(attr_data):

        embed_attrs = key.split(',')
        embed_attrs_len = len(embed_attrs)
        if embed_attrs_len >= 3:
            obj.add_embed_attr(embed_attrs, val, embed_attrs_len - 2)
        else:
            if isinstance(val, str):
                val_list = val.split(',')
                # Treat as list if value contains ',' but is not
                # enclosed within {}
                if len(val_list) == 1 or val.startswith('{'):
                    obj.add_attr(key, val)
                else:
                    obj.add_attr(key, val_list)
            else:
                obj.add_attr(key, val)

    if db:
        cps.set_ownership_type(obj.get_key(), 'db')
        obj.set_property('db', True)
    else:
        obj.set_property('db', False)

    if commit_event:
        cps.set_auto_commit_event(obj.get_key(), True)
        obj.set_property('commit-event', True)
    return obj


def cps_get(obj):

    RESULT = dict()
    key = obj.get()
    l = []
    cps.get([key], l)

    resp_list = convert_cps_raw_list(l)

    RESULT["response"] = resp_list
    return RESULT


def cps_transaction(obj):

    RESULT = dict()
    ch = {'operation': obj.get_property('oper'), 'change': obj.get()}
    if cps.transaction([ch]):
        RESULT["response"] = convert_cps_raw_list([ch['change']])
        RESULT["changed"] = True
    else:
        error_msg = "Transaction error while " + obj.get_property('oper')
        raise RuntimeError(error_msg)
    return RESULT


def parse_key_data(attrs):

    res = dict()
    for key, val in iteritems(attrs):
        if key == 'cps/key_data':
            res.update(val)
        else:
            res[key] = val
    return res


def main():
    """
    main entry point for module execution
    """
    argument_spec = dict(
        qualifier=dict(required=False,
                       default="target",
                       type='str',
                       choices=['target', 'observed', 'proposed', 'realtime',
                                'registration', 'running', 'startup']),
        module_name=dict(required=True, type='str'),
        attr_type=dict(required=False, type='dict'),
        attr_data=dict(required=True, type='dict'),
        operation=dict(required=False,
                       default="create",
                       type='str',
                       choices=['delete', 'create', 'set', 'action', 'get']),
        db=dict(required=False, default=False, type='bool'),
        commit_event=dict(required=False, default=False, type='bool')
    )

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=False)

    if not HAS_CPS:
        module.fail_json(msg='CPS library required for this module')

    qualifier = module.params['qualifier']
    module_name = module.params['module_name']
    attr_type = module.params["attr_type"]
    attr_data = module.params["attr_data"]
    operation = module.params['operation']
    db = module.params["db"]
    commit_event = module.params["commit_event"]
    RESULT = dict(changed=False, db=False, commit_event=False)

    if db:
        RESULT['db'] = True
    if commit_event:
        RESULT['commit_event'] = True

    try:
        # First do a CPS get operation
        get_obj = parse_cps_parameters(module_name, qualifier, attr_type,
                                       attr_data, 'get', db, commit_event)
        curr_config = cps_get(get_obj)

        if operation == 'get':
            RESULT.update(curr_config)
        else:
            diff = attr_data

            # Evaluate the changes in the attributes
            cfg = dict()
            if curr_config and curr_config['response']:
                cfg = curr_config['response'][0]['data']
                key_d = 'cps/key_data'

                # diff computation is not needed for delete
                if operation != 'delete':
                    configs = parse_key_data(cfg)
                    attributes = parse_key_data(attr_data)
                    diff = dict_diff(configs, attributes)
                    # Append diff with any 'cps/key_data' from attr_data
                    if diff and key_d in attr_data:
                        diff[key_d] = attr_data[key_d]

                # Append diff with any 'cps/key_data' from curr_config
                # Needed for all operations including delete
                if diff and key_d in cfg:
                    if key_d in diff:
                        diff[key_d].update(cfg[key_d])
                    else:
                        diff[key_d] = cfg[key_d]

                RESULT.update({"diff": diff})

            # Create object for cps operation
            obj = parse_cps_parameters(module_name, qualifier, attr_type,
                                       diff, operation, db, commit_event)

            res = dict()
            if operation == "delete":
                if cfg:
                    res = cps_transaction(obj)
            else:
                if diff:
                    res = cps_transaction(obj)

            if not res and cfg:
                res.update({"response": curr_config['response']})
            else:
                res.update({"cps_curr_config": curr_config['response']})
            RESULT.update(res)

    except Exception as e:
        module.fail_json(msg=str(type(e).__name__) + ": " + str(e))

    module.exit_json(**RESULT)


if __name__ == '__main__':
    main()
