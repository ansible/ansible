#!/usr/bin/python -tt
# -*- coding: utf-8 -*-

# (c) 2016, Matthew Gamble <git@matthewgamble.net>
#
# This file is part of Ansible
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

ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'version': '1.0'}

DOCUMENTATION = '''
---
module: jsonmod
short_description: Update part of a JSON file without worrying about how it is formatted
description:
    - Used to update part of a JSON file by specifying a path to the node
      you want to update and what you want to add to or replace it with.
      It works regardless of how the JSON file is formatted.
version_added: "1.0"
author:
    - "Matthew Gamble <git@matthewgamble.net>"
notes: []
requirements: []
options:
  backup:
    description:
      - Create a backup file including the timestamp information so you can get
        the original file back if you somehow clobbered it incorrectly.
    required: false
    default: "no"
    choices: ["yes", "no"]
  create_file:
    description:
      - If the destination file doesn't exist, this flag will ensure it is
        created. Otherwise, an error will be returned.
    required: false
    default: "no"
    choices: ["yes", "no"]
  data_json:
    description:
      - A valid JSON serialized string. This will be decoded and placed at
        the path in the JSON document specified by I(json_path).
    required: false
    default: null
  data_str:
    description:
      - A string to be placed at the path in the JSON document specified by
        I(json_path). This will not be decoded as JSON.
    required: false
    default: ''
  json_path:
    description:
      - The path to a point inside the JSON document that should be updated.
    required: true
    default: null
  path:
    description:
      - Path to a file containing a JSON document.
    required: true
    default: null
  remove:
    description:
      - Instead of adding or replacing the node at the path specified by
        I(json_path), ensure it is removed.
    required: false
    default: "no"
    choices: ["yes", "no"]
'''

EXAMPLES = '''
# Before:
# {"param1": [1, 2], "param2": [3, 4]}
- name: Replace param1 values
  jsonmod:
    data_json: [5, 6]
    json_path: "param1"
    path: "/path/to/my.json"
# After:
# {"param1": [5, 6], "param2": [3, 4]}

# Before:
# {"droids": [{"name": "C-4PO"}, {"name": "R2D2"}]}
- name: Fix typo in droid name
  jsonmod:
    data_str: "C-3PO"
    json_path: "droids[0]name"
    path: "/path/to/droids.json"
# After:
# {"droids": [{"name": "C-3PO"}, {"name": "R2D2"}]}

# Before:
# {"droids": [{"name": "C-3PO"}, {"name": "R2D2"}]}
- name: Add droid to list
  jsonmod:
    data_json: {"name": "BB-8"}
    json_path: "droids[2]"
    path: "/path/to/droids.json"
# After:
# {"droids": [{"name": "C-3PO"}, {"name": "R2D2"}, {"name": "BB-8"}]}

# Before:
# {"train": {"type": "land"}, "aeroplane": {"type": "air", "speed": "fast"}}
- name: Add speed node to train info
  jsonmod:
    data_str: "not as fast"
    json_path: "train.speed"
    path: "/path/to/vehicles.json"
# After:
# {"train": {"type": "land", "speed": "not as fast"}, "aeroplane": {"type": "air", "speed": "fast"}}

# Before:
# ["item1", "item2", "item3"]
- name: Remove item2 from the list
  jsonmod:
    json_path: "[1]"
    path: "/path/to/items.json"
    remove: yes
# After:
# ["item1", "item3"]

# Before:
# {"item1": {"subitem1": [1, 2], "subitem2": [3, 4]}, "item2": {"subitem4": [7, 8]}}
- name: Remove subitem3
  jsonmod:
    json_path: "item2.subitem3"
    path: "/path/to/items.json"
    remove: yes
# After (notice no change):
# {"item1": {"subitem1": [1, 2], "subitem2": [3, 4]}, "item2": {"subitem4": [7, 8]}}

# Example where file doesn't currently exist
- name: Configure feature X
  jsonmod:
    create_file: yes
    data_json: "[1, 2, 3]"
    json_path: "groupA.featureX"
    path: "/path/to/configfile.json"
# After (file now exists):
# {"groupA": {"featureX": [1, 2, 3]}}
'''

from collections import OrderedDict
import copy
import json
import os
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.six import string_types, text_type

class JSONPathUpdater(object):
    def __init__(self, json_path):
        self._json_path = json_path
        self._index = 0
        self._pathlen = len(json_path)

    def _get_next_token(self):
        index = self._index
        curtoken = ''
        inside_array_index = False
        while index < self._pathlen:
            curchar = self._json_path[index]
            index += 1
            if curchar == ".":
                if inside_array_index:
                    raise Exception("Cannot have decimal list indexes")
                if curtoken == "":
                    raise Exception("Cannot have empty key")
                break
            elif curchar == "[":
                if len(curtoken) > 0:
                    index -= 1
                    break
                if inside_array_index:
                    raise Exception("Cannot have nested brackets")
                inside_array_index = True
                continue
            elif curchar == "]":
                if not inside_array_index:
                    raise Exception("Mis-matched closing bracket")
                if curtoken == "":
                    raise Exception("Cannot have empty key")
                break
            curtoken += curchar

        if inside_array_index:
            try:
                returnval = int(curtoken)
            except ValueError:
                raise Exception("Non-numerical list index supplied")
        else:
            returnval = curtoken
        self._index = index
        return returnval

    def update_json(self, data, update_data=None, remove=False):
        prevtoken = None
        curtoken = self._get_next_token()
        prevdata = None
        curdata = data

        key_missing = False
        while True:
            if isinstance(curdata, dict):
                if not isinstance(curtoken, string_types):
                    raise Exception("Dictionary keys must be strings")
                if curtoken in curdata:
                    prevdata = curdata
                    curdata = curdata[curtoken]
                else:
                    key_missing = True
                    break
            elif isinstance(curdata, list):
                if not isinstance(curtoken, int):
                    raise Exception("List keys must be integers")
                if curtoken < len(curdata):
                    prevdata = curdata
                    curdata = curdata[curtoken]
                else:
                    key_missing = True
                    break
            elif isinstance(curdata, (int, bool, string_types)):
                raise Exception("Cannot index into an int, bool or string")
            else:
                raise Exception("Unknown data type found")
            prevtoken = curtoken
            curtoken = self._get_next_token()
            if isinstance(curtoken, string_types) and len(curtoken) == 0:
                break

        if key_missing:
            if remove:
                return
            
            while True:
                prevtoken = curtoken
                curtoken = self._get_next_token()
                if isinstance(curtoken, string_types) and len(curtoken) == 0:
                    if isinstance(curdata, dict):
                        curdata[prevtoken] = update_data
                    elif isinstance(curdata, list):
                        curdata.append(update_data)
                    return
                else:
                    if isinstance(curtoken, string_types):
                        nextcontainertype = OrderedDict
                    elif isinstance(curtoken, int):
                        nextcontainertype = list
                    else:
                        raise Exception("Unknown key type found")
                    if isinstance(prevtoken, string_types):
                        curdata[prevtoken] = nextcontainertype()
                    elif isinstance(prevtoken, int):
                        curdata.append(nextcontainertype())
                    else:
                        raise Exception("Unknown key type found")
                prevdata = curdata
                if isinstance(curdata, list):
                    curdata = curdata[len(curdata) - 1]
                else:
                    curdata = curdata[prevtoken]
        else:
            if remove:
                del prevdata[prevtoken]
            else:
                prevdata[prevtoken] = update_data

def main():
    module = AnsibleModule(
        argument_spec = dict(
            backup      = dict(type='bool', required=False, default=False),
            create_file = dict(type='bool', required=False, default=False),
            data_json   = dict(type='json', required=False),
            data_str    = dict(type='str', required=False),
            json_path   = dict(type='str', required=True),
            path        = dict(type='path', required=True),
            remove      = dict(type='bool', required=False, default=False),
        ),
        mutually_exclusive = [['data_json', 'data_str', 'remove']],
        required_one_of = [['data_json', 'data_str', 'remove']],
        supports_check_mode = True
    )
    p = module.params

    remove = p.get("remove", False)
    if not remove:
        if p.get("data_json") is None and p.get("data_str") is None:
            module.fail_json(msg="Must supply either some JSON or a raw string to update with when not removing")

    filename = p.get("path")
    if os.path.exists(filename):
        with open(filename, "r") as json_file:
            data = json.load(json_file, object_pairs_hook=OrderedDict)
        origdata = copy.deepcopy(data)
    else:
        if not p.get("create_file", False):
            module.fail_json(rc=257, msg="Destination %s does not exist!" % filename)
        destpath = os.path.dirname(filename)
        if not os.path.exists(destpath) and not module.check_mode:
            os.makedirs(destpath)
        if p.get("json_path")[0] == "[":
            data = []
            origdata = []
        else:
            data = OrderedDict()
            origdata = OrderedDict()

    updater = JSONPathUpdater(p.get("json_path"))
    remove = p.get("remove")

    if not remove:
        if p.get("data_json") is not None:
            update_data_jsonstr = p.get("data_json")
            try:
                update_data = json.loads(update_data_jsonstr)
            except Exception, e:
                module.fail_json(msg="Error while decoding JSON for updating: %s" % text_type(e))
        elif p.get("data_str") is not None:
            update_data = p.get("data_str")
        else:
            module.fail_json(msg="No update data supplied")

    try:
        if remove:
            updater.update_json(data, remove=True)
        else:
            updater.update_json(data, update_data=update_data)
    except Exception, e:
        module.fail_json(msg="Error while updating JSON: %s" % text_type(e))

    before = json.dumps(origdata, indent=4)
    after = json.dumps(data, indent=4)
    diff = {"before": before,
            "after": after,
            "before_header": "%s (content)" % filename,
            "after_header": "%s (content)" % filename}
    changed = before != after

    if changed:
        if module.check_mode:
            msg = "Would have updated the file"
        else:
            if p.get("backup", False):
                backup_file = module.backup_local(filename)
            with open(filename, mode="w", encoding="utf-8") as json_file:
                json.dump(json_file, data)
            msg = "Updated the file"
    else:
        msg = "File already up to date"

    result = {"changed": changed, "msg": msg, "diff": diff}
    if changed and not module.check_mode and p.get("backup", False):
        result["backup_file"] = backup_file
    module.exit_json(**result)


if __name__ == "__main__":
    main()
