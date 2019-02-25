#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2019, Joey Espinosa <jlouis.espinosa@gmail.com>
# Copyright: (c) 2019, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import json
import os

from ansible.module_utils import basic
from ansible.module_utils._text import to_bytes


ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}


DOCUMENTATION = """
---
module: jsonpatch
author: "Joey Espinosa (@ParticleDecay)"
short_description: Patch JSON documents
requirements: []
version_added: "2.7"
description:
    - Patch JSON documents using JSON Patch standard
    - RFC 6902: https://tools.ietf.org/html/rfc6902
options:
    src:
        description:
            - The path to the source JSON file
        required: True
    dest:
        description:
            - The path to the destination JSON file
        required: False
    operations:
        description:
            - A list of operations to perform on the JSON document
        required: True
    backup:
        description:
            - Copy the targeted file to a backup prior to patch
"""


EXAMPLES = """
# These examples are using the following JSON:
#
# [
#   {
#     "foo": {
#       "one": 1,
#       "two": 2,
#       "three": 3
#     },
#     "enabled": true
#   },
#   {
#     "bar": {
#       "one": 1,
#       "two": 2,
#       "three": 3
#     },
#     "enabled": false
#   },
#   {
#     "baz": [
#       {
#         "foo": "apples",
#         "bar": "oranges"
#       },
#       {
#         "foo": "grapes",
#         "bar": "oranges"
#       },
#       {
#         "foo": "bananas",
#         "bar": "potatoes"
#       }
#     ],
#     "enabled": true
#   }
# ] 
#
# # test if the "bar" object is enabled
jsonpatch:
  src: "test.json"
  operations:
    - op: test
      path: "/1/enabled"
      value: true

# add a fourth element to the "foo" object
jsonpatch:
  src: "test.json"
  operations:
    - op: add
      path: "/0/foo/four"
      value: 4

# remove the first object in the "baz" list of fruits
jsonpatch:
  src: "test.json"
  operations:
    - op: remove
      path: "/2/baz/0"

# move the "potatoes" value from the "baz" list to the "foo" object
jsonpatch:
  src: "test.json"
  operations:
    - op: move
      from: "/2/baz/2/bar"
      path: "/0/foo/bar"

# test that the "foo" object has three members
jsonpatch:
  src: "test.json"
  operations:
    - op: test
      path: "/0/foo/one"
      value: 1
    - op: test
      path: "/0/foo/two"
      value: 2
    - op: test
      path: "/0/foo/three"
      value: 3
"""


def set_module_args(args):
    """For dynamic module args (such as for testing)."""
    args = json.dumps({'ANSIBLE_MODULE_ARGS': args})
    basic._ANSIBLE_ARGS = to_bytes(args)


class PathError(Exception):
    """Raised when no valid JSON object or property is found for a given path."""
    pass


class PatchManager(object):
    """Manage the Ansible portion of JSONPatcher."""

    def __init__(self, module):
        self.module = module

        # validate file
        self.src = self.module.params['src']
        if not os.path.isfile(self.src):
            self.module.fail_json(msg="could not find file at `%s`" % self.src)

        # use 'src' as the output file, unless 'dest' is provided
        self.outfile = self.src
        self.dest = self.module.params.get('dest')
        if self.dest is not None:
            self.outfile = self.dest

        try:
            self.json_doc = open(self.src).read()
        except IOError:
            self.module.fail_json(msg="could not read file at `%s`" % self.src)
        
        self.operations = self.module.params['operations']
        try:
            self.patcher = JSONPatcher(self.json_doc, *self.operations)
        except Exception as e:
            self.module.fail_json(msg=e.message)

        self.do_backup = self.module.params.get('backup', False)
        self.changed = False

    def run(self):
        self.changed = self.patcher.patch()
        if self.changed:  # let's write the changes
            self.write()
        return self.changed

    def backup(self):
        """Create a backup copy of the JSON file."""
        path = self.outfile
        counter = 0
        while os.path.exists("%s.bak" % path):
            path = "%s.%s" % (path, str(counter))
            counter += 1
        filename = "%s.bak" % path

        with open(filename, "w") as bak:
            bak.write(open(self.outfile, "r").read())

    def write(self):
        if self.do_backup:  # backup first if needed
            self.backup()
        
        with open(self.outfile, "w") as f:
            f.write(json.dumps(self.patcher.obj))


class JSONPatcher(object):
    """Patch JSON documents according to RFC 6902."""

    def __init__(self, json_doc, *operations):
        try:
            self.obj = json.loads(json_doc)  # let this fail if it must
        except (ValueError, TypeError):
            raise Exception(msg="invalid JSON found")
        self.operations = operations

        # validate all operations
        for op in self.operations:
            self.validate_operation(op)

    def validate_operation(self, members):
        """Validate that an operation is in compliance with RFC 6902.

        Args:
            members(dict): a dict of members that comprise one patch operation
        """
        if 'op' not in members:
            raise ValueError("'%s' is missing an 'op' member" % repr(members))
        
        allowed_ops = ('add', 'remove', 'replace', 'move', 'copy', 'test')
        if members['op'] not in allowed_ops:
            raise ValueError("'%s' is not a valid patch operation" % members['op'])
        
        if 'path' not in members:
            raise ValueError("'%s' is missing a 'path' member" % repr(members))

        if members['op'] == 'add':
            if 'value' not in members:
                raise ValueError("'%s' is an 'add' but does not have a 'value'" % repr(members))

    def patch(self):
        """Perform all of the given patch operations."""
        modified = False  # whether we modified the object after all operations
        for patch in self.operations:
            op = patch['op']
            del patch['op']

            # we can't accept 'from' as a dict key
            if patch.get('from') is not None:
                patch['from_path'] = patch['from']
                del patch['from']
            
            # attach object to patch operation (helpful for recursion)
            patch['obj'] = self.obj
            new_obj, changed = getattr(self, op)(**patch)
            if changed or op == "remove":  # 'remove' will fail if we don't actually remove anything
                modified = True
                self.obj = new_obj
        return modified

    def _get(self, path, obj, **discard):
        """Return a value at 'path'."""
        elements = path.lstrip('/').split('/')
        next_obj = obj
        for elem in elements:
            try:
                next_obj = next_obj[elem]
            except KeyError:
                raise PathError("'%s' was not found in the JSON object" % path)
            except TypeError:  # it's a list
                if not elem.isdigit():
                    raise PathError("'%s' is not a valid index for a JSON array" % path)
                try:
                    next_obj = next_obj[int(elem)]
                except IndexError:
                    raise PathError("specified index '%s' was not found in JSON array" % path)
        return next_obj

    def add(self, path, value, obj, **discard):
        """Perform an 'add' operation."""
        chg = False
        path = path.lstrip('/')
        if "/" not in path:  # recursion termination
            if isinstance(obj, dict):
                old_value = obj.get(path)
                obj[path] = value
                if obj[path] != old_value:
                    chg = True
                return obj, chg
            elif isinstance(obj, list):
                if path == "-":  # points to end of list
                    obj.append(value)
                    chg = True
                elif not path.isdigit():
                    raise PathError("'%s' is not a valid index for a JSON array" % path)
                else:
                    idx = int(path)
                    if idx > len(obj):  # violation of rfc 6902
                        raise PathError("specified index '%s' cannot be greater than the number of elements in JSON array" % path)
                    obj.insert(idx, value)
                    chg = True
                return obj, chg
        else:  # traverse obj until last path member
            elements = path.split('/')
            path, remaining = elements[0], '/'.join(elements[1:])

            next_obj = None
            if isinstance(obj, dict):
                try:
                    next_obj = obj[path]
                except KeyError:
                    raise PathError("could not find '%s' member in JSON object" % path)
                obj[path], chg = self.add(remaining, value, next_obj)
            elif isinstance(obj, list):
                if not path.isdigit():
                    raise PathError("'%s' is not a valid index for a JSON array" % path)
                try:
                    next_obj = obj[int(path)]
                except IndexError:
                    if int(path) > len(obj):  # violation of rfc 6902
                        raise PathError("specified index '%s' cannot be greater than the number of elements in JSON array" % path)
                    else:
                        raise PathError("could not find index '%s' in JSON array" % path)
                obj[int(path)], chg = self.add(remaining, value, next_obj)
            return obj, chg
            
    def remove(self, path, obj, **discard):
        """Perform a 'remove' operation."""
        removed = None
        path = path.lstrip('/')
        if "/" not in path:  # recursion termination
            try:
                removed = obj.pop(path)
            except KeyError:
                raise PathError("'%s' was not found in the JSON object" % path)
            except TypeError:  # it's a list
                if not path.isdigit():
                    raise PathError("'%s' is not a valid index for a JSON array" % path)
                try:
                    removed = obj.pop(int(path))
                except IndexError:
                    raise PathError("specified index '%s' was not found in JSON array" % path)
            return obj, removed
        else:  # traverse obj until last path member
            elements = path.split('/')
            path, remaining = elements[0], '/'.join(elements[1:])

            next_obj = None
            if isinstance(obj, dict):
                try:
                    next_obj = obj[path]
                except KeyError:
                    raise PathError("could not find '%s' member in JSON object" % path)
                obj[path], removed = self.remove(remaining, next_obj)
            elif isinstance(obj, list):
                if not path.isdigit():
                    raise PathError("'%s' is not a valid index for a JSON array" % path)
                try:
                    next_obj = obj[int(path)]
                except IndexError:
                    if int(path) > len(obj):  # violation of rfc 6902
                        raise PathError("specified index '%s' cannot be greater than the number of elements in JSON array" % path)
                    else:
                        raise PathError("could not find index '%s' in JSON array" % path)
                obj[int(path)], removed = self.remove(remaining, next_obj)
            return obj, removed

    def replace(self, path, value, obj, **discard):
        """Perform a 'replace' operation."""
        new_obj, _ = self.remove(path, obj)
        new_obj, chg = self.add(path, value, new_obj)
        return new_obj, chg

    def move(self, from_path, path, obj, **discard):
        """Perform a 'move' operation."""
        new_obj, removed = self.remove(from_path, obj)
        new_obj, chg = self.add(path, removed, new_obj)
        return new_obj, chg

    def copy(self, from_path, path, obj, **discard):
        """Perform a 'copy' operation."""
        value = self._get(from_path, obj)
        new_obj, chg = self.add(path, value, obj)
        return new_obj, chg

    def test(self, path, value, obj, **discard):
        """Perform a 'test' operation.

        This operation supports an additional feature not outlined in
        RFC 6901 (https://tools.ietf.org/html/rfc6901): The ability to
        reference every member of an array by using an asterisk (*).
        
        In such a case, each member of the array at that point in the
        path will be tested sequentially for the given value, and if
        a matching value is found, the method will return immediately
        with a True value.

        Example:
            {"op": "test", "path": "/array/*/member/property", "value": 2}

        If the object to be tested looked like...
        {
            "array": [
                {"member": {"property": 1}},
                {"member": {"property": 2}}
            ]
        }
        ... the result would be True, because an object exists within
        "array" that has the matching path and value.
        """
        elements = path.lstrip('/').split('/')
        next_obj = obj
        for idx, elem in enumerate(elements):
            if elem == "*":  # wildcard
                if not isinstance(next_obj, list):
                    raise PathError("'*' does not refer to a JSON array")
                for sub_obj in next_obj:
                    _, found = self.test('/'.join(elements[(idx + 1):]), value, sub_obj)
                    if found:
                        return obj, found
                return obj, False
            else:
                try:
                    next_obj = next_obj[elem]
                except KeyError:
                    raise PathError("'%s' was not found in the JSON object" % elem)
                except TypeError:  # it's a list
                    if not elem.isdigit():
                        raise PathError("'%s' is not a valid index for a JSON array" % elem)
                    try:
                        next_obj = next_obj[int(elem)]
                    except IndexError:
                        raise PathError("specified index '%s' was not found in JSON array" % elem)
        return obj, next_obj == value


def main():
    # Parsing argument file
    module = basic.AnsibleModule(
        argument_spec=dict(
            src=dict(required=True, type='str'),
            dest=dict(required=False, type='str'),
            operations=dict(required=True, type='list'),
            backup=dict(required=False, default=False, type='bool'),
        ),
        supports_check_mode=False
    )

    manager = PatchManager(module)
    manager.run()
    result = {"changed": manager.changed}

    module.exit_json(**result)

if __name__ == "__main__":
    main()