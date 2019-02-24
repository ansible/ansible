#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2019, zhan9san <zhan9san@163.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: jsonpath
short_description: Manage pieces of JSON files
description:
- An XPath for JSON
- Refer to https://github.com/h2non/jsonpath-ng.
version_added: '2.8'
options:
  path:
    description:
    - Path to the file to operate on.
    - This file must exist ahead of time.
    - This parameter is required.
    type: path
    required: yes

  jsonpath:
    description:
    - A valid JSONPath expression describing the item(s) you want to manipulate.
    type: str
    required: yes

  value:
    description:
    - Either a string, or number.
    - This parameter is required.
    type: raw
    required: yes

requirements:
- jsonpath-ng >= 1.4.3
notes:
- This module does not handle complicated jsonpath expressions, so limit jsonpath selectors to simple expressions.

author:
- zhan9san (@zhan9san)
'''

EXAMPLES = r'''
# Consider the following JSON file:
#
# {
#   "menu": {
#     "id": "file",
#     "value": "File",
#     "popup": {
#       "menuitem": [{
#           "value": "New",
#           "onclick": "CreateNewDoc()"
#         },
#         {
#           "value": "Open",
#           "onclick": "OpenDoc()"
#         },
#         {
#           "value": "Close",
#           "onclick": "CloseDoc()"
#         }
#       ]
#     }
#   }
# }

- name: Set menuitem's id to '01'
  jsonpath:
    path: /foo/bar.json
    jsonpath: "menu['id']"
    value: '01'

- name: Set the first menuitem's onclick to 'NewDoc()'
  jsonpath:
    path: /foo/bar.json
    jsonpath: "menu['popup']['menuitem'][0]['onclick']"
    value: 'NewDoc()'
'''

RETURN = r'''
actions:
    description: A dictionary with the original jsonpath.
    type: dict
    returned: success
    sample: {jsonpath: jsonpath}

msg:
    description: A message related to the performed action(s).
    type: str
    returned: always
'''

import copy
import json
import os

from distutils.version import LooseVersion

try:
    from jsonpath_ng import parse
    from jsonpath_ng import __version__ as jsonpath_ng_version
    HAS_JSONPATH_NG = True
except ImportError:
    HAS_JSONPATH_NG = False

from ansible.module_utils.basic import AnsibleModule, json_dict_bytes_to_unicode
from ansible.module_utils._text import to_native


def set_target(module, data, jsonpath_expr, orig_value):
    if orig_value == module.params['value']:
        changed = False
    else:
        jsonpath_expr.update(data, module.params['value'])
        changed = True

    finish(module, data, changed)


def finish(module, data, changed=False, msg=''):

    result = dict(
        actions=dict(
            jsonpath=module.params['jsonpath'],
        ),
        changed=changed,
    )

    if msg:
        result['msg'] = msg

    if result['changed']:
        with open(module.params['path'], 'w') as f:
            try:
                json.dump(data, f, indent=2)
            except Exception as e:
                module.fail_json(msg="Write error in json file: %s (%s)" % (module.params['path'], e))

    module.exit_json(**result)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            path=dict(type='path', required=True),
            jsonpath=dict(type='str', required=True),
            value=dict(type='raw', required=True),
        ),
        supports_check_mode=False,
    )

    json_file = module.params['path']
    jsonpath = module.params['jsonpath']
    value = json_dict_bytes_to_unicode(module.params['value'])

    # Check if we have jsonpath-ng 1.4.3 or newer installed
    if not HAS_JSONPATH_NG:
        module.fail_json(msg='The jsonpath ansible module requires the jsonpath-ng python library installed on the managed machine')
    elif LooseVersion(jsonpath_ng_version) < LooseVersion('1.4.3'):
        module.fail_json(msg='The jsonpath ansible module requires jsonpath-ng 1.4.3 or newer installed on the managed machine')

    # Check if the file exists and load json
    if os.path.isfile(json_file):
        with open(json_file) as f:
            try:
                data = json.load(f)
            except Exception as e:
                module.fail_json(msg="Syntax error in json file: %s (%s)" % (json_file, e))
    else:
        module.fail_json(msg="The target JSON source '%s' does not exist." % json_file)

    # Parse jsonpath expression
    if jsonpath is not None:
        try:
            jsonpath_expr = parse(jsonpath)
        except Exception as e:
            module.fail_json(msg="Parser error in json expression: %s (%s)" % (jsonpath, e))

    # Try to parse in the target Json file
    try:
        rst = jsonpath_expr.find(data)[0].value
    except Exception as e:
        module.fail_json(msg="Error while parsing json: %s (%s)" % (json_file or 'xml_string', e))

    # Ensure we have the original copy to compare
    global orig_value
    orig_value = copy.deepcopy(rst)

    set_target(module, data, jsonpath_expr, orig_value)

    module.fail_json(msg="Don't know what to do")


if __name__ == '__main__':
    main()
