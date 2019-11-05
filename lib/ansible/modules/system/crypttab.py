#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2014, Steve <yo@groks.org>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: crypttab
short_description: Encrypted Linux block devices
description:
  - Control Linux encrypted block devices that are set up during system boot in C(/etc/crypttab).
version_added: "1.9"
options:
  name:
    description:
      - Name of the encrypted block device as it appears in the C(/etc/crypttab) file, or
        optionally prefixed with C(/dev/mapper/), as it appears in the filesystem. I(/dev/mapper/)
        will be stripped from I(name).
    type: str
    required: yes
  state:
    description:
      - Use I(present) to add a line to C(/etc/crypttab) or update its definition
        if already present.
      - Use I(absent) to remove a line with matching I(name).
      - Use I(opts_present) to add options to those already present; options with
        different values will be updated.
      - Use I(opts_absent) to remove options from the existing set.
    type: str
    required: yes
    choices: [ absent, opts_absent, opts_present, present ]
  backing_device:
    description:
      - Path to the underlying block device or file, or the UUID of a block-device
        prefixed with I(UUID=).
    type: str
  password:
    description:
      - Encryption password, the path to a file containing the password, or
        C(-) or unset if the password should be entered at boot.
    type: path
  opts:
    description:
      - A comma-delimited list of options. See C(crypttab(5) ) for details.
    type: str
  path:
    description:
      - Path to file to use instead of C(/etc/crypttab).
      - This might be useful in a chroot environment.
    type: path
    default: /etc/crypttab
author:
- Steve (@groks)
'''

EXAMPLES = r'''
- name: Set the options explicitly a device which must already exist
  crypttab:
    name: luks-home
    state: present
    opts: discard,cipher=aes-cbc-essiv:sha256

- name: Add the 'discard' option to any existing options for all devices
  crypttab:
    name: '{{ item.device }}'
    state: opts_present
    opts: discard
  loop: '{{ ansible_mounts }}'
  when: "'/dev/mapper/luks-' in {{ item.device }}"
'''

import os
import traceback

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_bytes, to_native


def main():
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(type='str', required=True),
            state=dict(type='str', required=True, choices=['absent', 'opts_absent', 'opts_present', 'present']),
            backing_device=dict(type='str'),
            password=dict(type='path'),
            opts=dict(type='str'),
            path=dict(type='path', default='/etc/crypttab')
        ),
        supports_check_mode=True,
    )

    backing_device = module.params['backing_device']
    password = module.params['password']
    opts = module.params['opts']
    state = module.params['state']
    path = module.params['path']
    name = module.params['name']
    if name.startswith('/dev/mapper/'):
        name = name[len('/dev/mapper/'):]

    if state != 'absent' and backing_device is None and password is None and opts is None:
        module.fail_json(msg="expected one or more of 'backing_device', 'password' or 'opts'",
                         **module.params)

    if 'opts' in state and (backing_device is not None or password is not None):
        module.fail_json(msg="cannot update 'backing_device' or 'password' when state=%s" % state,
                         **module.params)

    for arg_name, arg in (('name', name),
                          ('backing_device', backing_device),
                          ('password', password),
                          ('opts', opts)):
        if (arg is not None and (' ' in arg or '\t' in arg or arg == '')):
            module.fail_json(msg="invalid '%s': contains white space or is empty" % arg_name,
                             **module.params)

    try:
        crypttab = Crypttab(path)
        existing_line = crypttab.match(name)
    except Exception as e:
        module.fail_json(msg="failed to open and parse crypttab file: %s" % to_native(e),
                         exception=traceback.format_exc(), **module.params)

    if 'present' in state and existing_line is None and backing_device is None:
        module.fail_json(msg="'backing_device' required to add a new entry",
                         **module.params)

    changed, reason = False, '?'

    if state == 'absent':
        if existing_line is not None:
            changed, reason = existing_line.remove()

    elif state == 'present':
        if existing_line is not None:
            changed, reason = existing_line.set(backing_device, password, opts)
        else:
            changed, reason = crypttab.add(Line(None, name, backing_device, password, opts))

    elif state == 'opts_present':
        if existing_line is not None:
            changed, reason = existing_line.opts.add(opts)
        else:
            changed, reason = crypttab.add(Line(None, name, backing_device, password, opts))

    elif state == 'opts_absent':
        if existing_line is not None:
            changed, reason = existing_line.opts.remove(opts)

    if changed and not module.check_mode:
        try:
            f = open(path, 'wb')
            f.write(to_bytes(crypttab, errors='surrogate_or_strict'))
        finally:
            f.close()

    module.exit_json(changed=changed, msg=reason, **module.params)


class Crypttab(object):
    _lines = []

    def __init__(self, path):
        self.path = path
        if not os.path.exists(path):
            if not os.path.exists(os.path.dirname(path)):
                os.makedirs(os.path.dirname(path))
            open(path, 'a').close()

        try:
            f = open(path, 'r')
            for line in f.readlines():
                self._lines.append(Line(line))
        finally:
            f.close()

    def add(self, line):
        self._lines.append(line)
        return True, 'added line'

    def lines(self):
        for line in self._lines:
            if line.valid():
                yield line

    def match(self, name):
        for line in self.lines():
            if line.name == name:
                return line
        return None

    def __str__(self):
        lines = []
        for line in self._lines:
            lines.append(str(line))
        crypttab = '\n'.join(lines)
        if len(crypttab) == 0:
            crypttab += '\n'
        if crypttab[-1] != '\n':
            crypttab += '\n'
        return crypttab


class Line(object):
    def __init__(self, line=None, name=None, backing_device=None, password=None, opts=None):
        self.line = line
        self.name = name
        self.backing_device = backing_device
        self.password = password
        self.opts = Options(opts)

        if line is not None:
            self.line = self.line.rstrip('\n')
            if self._line_valid(line):
                self.name, backing_device, password, opts = self._split_line(line)

        self.set(backing_device, password, opts)

    def set(self, backing_device, password, opts):
        changed = False

        if backing_device is not None and self.backing_device != backing_device:
            self.backing_device = backing_device
            changed = True

        if password is not None and self.password != password:
            self.password = password
            changed = True

        if opts is not None:
            opts = Options(opts)
            if opts != self.opts:
                self.opts = opts
                changed = True

        return changed, 'updated line'

    def _line_valid(self, line):
        if not line.strip() or line.startswith('#') or len(line.split()) not in (2, 3, 4):
            return False
        return True

    def _split_line(self, line):
        fields = line.split()
        try:
            field2 = fields[2]
        except IndexError:
            field2 = None
        try:
            field3 = fields[3]
        except IndexError:
            field3 = None

        return (fields[0],
                fields[1],
                field2,
                field3)

    def remove(self):
        self.line, self.name, self.backing_device = '', None, None
        return True, 'removed line'

    def valid(self):
        if self.name is not None and self.backing_device is not None:
            return True
        return False

    def __str__(self):
        if self.valid():
            fields = [self.name, self.backing_device]
            if self.password is not None or self.opts:
                if self.password is not None:
                    fields.append(self.password)
                else:
                    fields.append('none')
            if self.opts:
                fields.append(str(self.opts))
            return ' '.join(fields)
        return self.line


class Options(dict):
    """opts_string looks like: 'discard,foo=bar,baz=greeble' """

    def __init__(self, opts_string):
        super(Options, self).__init__()
        self.itemlist = []
        if opts_string is not None:
            for opt in opts_string.split(','):
                kv = opt.split('=')
                if len(kv) > 1:
                    k, v = (kv[0], kv[1])
                else:
                    k, v = (kv[0], None)
                self[k] = v

    def add(self, opts_string):
        changed = False
        for k, v in Options(opts_string).items():
            if k in self:
                if self[k] != v:
                    changed = True
            else:
                changed = True
            self[k] = v
        return changed, 'updated options'

    def remove(self, opts_string):
        changed = False
        for k in Options(opts_string):
            if k in self:
                del self[k]
                changed = True
        return changed, 'removed options'

    def keys(self):
        return self.itemlist

    def values(self):
        return [self[key] for key in self]

    def items(self):
        return [(key, self[key]) for key in self]

    def __iter__(self):
        return iter(self.itemlist)

    def __setitem__(self, key, value):
        if key not in self:
            self.itemlist.append(key)
        super(Options, self).__setitem__(key, value)

    def __delitem__(self, key):
        self.itemlist.remove(key)
        super(Options, self).__delitem__(key)

    def __ne__(self, obj):
        return not (isinstance(obj, Options) and sorted(self.items()) == sorted(obj.items()))

    def __str__(self):
        ret = []
        for k, v in self.items():
            if v is None:
                ret.append(k)
            else:
                ret.append('%s=%s' % (k, v))
        return ','.join(ret)


if __name__ == '__main__':
    main()
