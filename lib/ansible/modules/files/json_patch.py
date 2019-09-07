#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2019, Joey Espinosa <jlouis.espinosa@gmail.com>
# Copyright: (c) 2019, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = r'''
---
module: json_patch
author: "Joey Espinosa (@ParticleDecay)"
short_description: Patch JSON documents
requirements: []
version_added: "2.10"
description:
    - Patch JSON documents using JSON Patch standard
    - "RFC 6901: https://tools.ietf.org/html/rfc6901"
    - "RFC 6902: https://tools.ietf.org/html/rfc6902"
options:
    src:
        description:
            - The path to the source JSON file
        required: True
        type: str
    dest:
        description:
            - The path to the destination JSON file
        required: False
        type: str
    operations:
        description:
            - A list of operations to perform on the JSON document
        required: True
        type: list
    backup:
        description:
            - Copy the targeted file to a backup prior to patch
        type: bool
    unsafe_writes:
        description:
            - Allow Ansible to fall back to unsafe methods of writing files (some systems do not support atomic operations)
        type: bool
    pretty:
        description:
            - Write pretty-print JSON when file is changed
        type: bool
'''


EXAMPLES = r'''
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
- name: add a fourth element to the "foo" object
  json_patch:
    src: "test.json"
    dest: "test2.json"
    operations:
      - op: add
        path: "/0/foo/four"
        value: 4

- name: remove the first object in the "baz" list of fruits
  json_patch:
    src: "test.json"
    pretty: yes
    operations:
      - op: remove
        path: "/2/baz/0"

- name: move the "potatoes" value from the "baz" list to the "foo" object
  json_patch:
    src: "test.json"
    backup: yes
    operations:
      - op: move
        from: "/2/baz/2/bar"
        path: "/0/foo/bar"

- name: test that the "foo" object has three members
  json_patch:
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
'''


RETURN = r'''
changed:
    description: whether the JSON object was modified
    returned: always
    type: bool
tested:
    description: the result of any included test operation
    returned: when test operation exists
    type: bool
backup:
    description: the name of the backed up file
    returned: when backup is true
    type: str
dest:
    description: the name of the file that was written
    returned: changed
    type: str
'''


import json
import os
import tempfile

from ansible.module_utils import basic
from ansible.module_utils._text import to_bytes, to_native


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
            self.module.fail_json(msg=str(e))

        self.do_backup = self.module.params.get('backup', False)
        self.pretty_print = self.module.params.get('pretty', False)

    def run(self):
        changed, tested = self.patcher.patch()
        result = {'changed': changed}
        if tested is not None:
            result['tested'] = tested
        if result['changed']:  # let's write the changes
            result.update(self.write())
        return result

    def backup(self):
        """Create a backup copy of the JSON file."""
        return {'backup': self.module.backup_local(self.outfile)}

    def write(self):
        result = {'dest': self.outfile}

        if self.module.check_mode:  # stop here before doing anything permanent
            return result

        dump_kwargs = {}
        if self.pretty_print:
            dump_kwargs.update({'indent': 4, 'separators': (',', ': ')})

        if self.do_backup:  # backup first if needed
            result.update(self.backup())

        tmpfd, tmpfile = tempfile.mkstemp()
        with open(tmpfile, "w") as f:
            f.write(json.dumps(self.patcher.obj, **dump_kwargs))

        self.module.atomic_move(tmpfile,
                                to_native(os.path.realpath(to_bytes(self.outfile, errors='surrogate_or_strict')), errors='surrogate_or_strict'),
                                unsafe_writes=self.module.params['unsafe_writes'])

        return result


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
        modified = None  # whether we modified the object after all operations
        test_result = None
        for patch in self.operations:
            op = patch['op']
            del patch['op']

            # we can't accept 'from' as a dict key
            if patch.get('from') is not None:
                patch['from_path'] = patch['from']
                del patch['from']

            # attach object to patch operation (helpful for recursion)
            patch['obj'] = self.obj
            new_obj, changed, tested = getattr(self, op)(**patch)
            if changed is not None or op == "remove":  # 'remove' will fail if we don't actually remove anything
                modified = bool(changed)
                if modified is True:
                    self.obj = new_obj
            if tested is not None:
                test_result = False if test_result is False else tested  # one false test fails everything
        return modified, test_result

    def _get(self, path, obj, **discard):
        """Return a value at 'path'."""
        elements = path.lstrip('/').split('/')
        next_obj = obj
        for idx, elem in enumerate(elements):
            try:
                next_obj = next_obj[elem]
            except KeyError:
                if idx == (len(elements) - 1):  # this helps us stay idempotent
                    return None
                raise PathError("'%s' was not found in the JSON object" % path)  # wrong path specified
            except TypeError:  # it's a list
                if not elem.isdigit():
                    raise PathError("'%s' is not a valid index for a JSON array" % path)
                try:
                    next_obj = next_obj[int(elem)]
                except IndexError:
                    if idx == (len(elements) - 1):  # this helps us stay idempotent
                        return None
                    raise PathError("specified index '%s' was not found in JSON array" % path)
        return next_obj

    # https://tools.ietf.org/html/rfc6902#section-4.1
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
                return obj, chg, None
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
                return obj, chg, None
        else:  # traverse obj until last path member
            elements = path.split('/')
            path, remaining = elements[0], '/'.join(elements[1:])

            next_obj = None
            if isinstance(obj, dict):
                try:
                    next_obj = obj[path]
                except KeyError:
                    raise PathError("could not find '%s' member in JSON object" % path)
                obj[path], chg, tst = self.add(remaining, value, next_obj)
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
                obj[int(path)], chg, tst = self.add(remaining, value, next_obj)
            return obj, chg, None

    # https://tools.ietf.org/html/rfc6902#section-4.2
    def remove(self, path, obj, **discard):
        """Perform a 'remove' operation."""
        removed = None
        path = path.lstrip('/')
        if "/" not in path:  # recursion termination
            try:
                removed = obj.pop(path)
            except KeyError:
                return obj, None, None
            except TypeError:  # it's a list
                if not path.isdigit():
                    raise PathError("'%s' is not a valid index for a JSON array" % path)
                try:
                    removed = obj.pop(int(path))
                except IndexError:
                    return obj, None, None
            return obj, removed, None
        else:  # traverse obj until last path member
            elements = path.split('/')
            path, remaining = elements[0], '/'.join(elements[1:])

            next_obj = None
            if isinstance(obj, dict):
                try:
                    next_obj = obj[path]
                except KeyError:
                    raise PathError("could not find '%s' member in JSON object" % path)
                obj[path], removed, tst = self.remove(remaining, next_obj)
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
                obj[int(path)], removed, tst = self.remove(remaining, next_obj)
            return obj, removed, None

    # https://tools.ietf.org/html/rfc6902#section-4.3
    def replace(self, path, value, obj, **discard):
        """Perform a 'replace' operation."""
        old_value = self._get(path, obj)
        if old_value == value:
            return obj, False, None
        if old_value is None:  # the target location must exist for operation to be successful
            raise PathError("could not find '%s' member in JSON object" % path)
        new_obj, dummy, tst = self.remove(path, obj)
        new_obj, chg, tst = self.add(path, value, new_obj)
        return new_obj, chg, None

    # https://tools.ietf.org/html/rfc6902#section-4.4
    def move(self, from_path, path, obj, **discard):
        """Perform a 'move' operation."""
        chg = False
        new_obj, removed, tst = self.remove(from_path, obj)
        if removed is not None:  # don't inadvertently add 'None' as a value somewhere
            new_obj, chg, tst = self.add(path, removed, new_obj)
        return new_obj, chg, None

    # https://tools.ietf.org/html/rfc6902#section-4.5
    def copy(self, from_path, path, obj, **discard):
        """Perform a 'copy' operation."""
        value = self._get(from_path, obj)
        if value is None:
            raise PathError("could not find '%s' member in JSON object" % path)
        new_obj, chg, tst = self.add(path, value, obj)
        return new_obj, chg, None

    # https://tools.ietf.org/html/rfc6902#section-4.6
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
                    return obj, None, False
                for sub_obj in next_obj:
                    dummy, chg, found = self.test('/'.join(elements[(idx + 1):]), value, sub_obj)
                    if found:
                        return obj, None, found
                return obj, None, False
            try:
                next_obj = next_obj[elem]
            except KeyError:
                return obj, None, False
            except TypeError:  # it's a list
                if not elem.isdigit():
                    return obj, None, False
                try:
                    next_obj = next_obj[int(elem)]
                except IndexError:
                    return obj, None, False
        return obj, None, next_obj == value


def main():
    # Parsing argument file
    module = basic.AnsibleModule(
        argument_spec=dict(
            src=dict(required=True, type='str'),
            dest=dict(required=False, type='str'),
            operations=dict(required=True, type='list'),
            backup=dict(required=False, default=False, type='bool'),
            unsafe_writes=dict(required=False, default=False, type='bool'),
            pretty=dict(required=False, default=False, type='bool'),
        ),
        supports_check_mode=True
    )

    manager = PatchManager(module)
    result = manager.run()

    module.exit_json(**result)


if __name__ == "__main__":
    main()
