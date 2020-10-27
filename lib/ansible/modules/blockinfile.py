#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2014, 2015 YAEGASHI Takeshi <yaegashi@debian.org>
# Copyright: (c) 2017, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = r'''
---
module: blockinfile
short_description: Insert/update/remove a text block surrounded by marker lines
version_added: '2.0'
description:
- This module will insert/update/remove a block of multi-line text surrounded by customizable marker lines.
author:
- Yaegashi Takeshi (@yaegashi)
options:
  path:
    description:
    - The file to modify.
    - Before Ansible 2.3 this option was only usable as I(dest), I(destfile) and I(name).
    type: path
    required: yes
    aliases: [ dest, destfile, name ]
  state:
    description:
    - Whether the block should be there or not.
    type: str
    choices: [ absent, present ]
    default: present
  marker:
    description:
    - The marker line template.
    - C({mark}) will be replaced with the values in C(marker_begin) (default="BEGIN") and C(marker_end) (default="END").
    - Using a custom marker without the C({mark}) variable may result in the block being repeatedly inserted on subsequent playbook runs.
    type: str
    default: '# {mark} ANSIBLE MANAGED BLOCK'
  block:
    description:
    - The text to insert inside the marker lines.
    - If it is missing or an empty string, the block will be removed as if C(state) were specified to C(absent).
    type: str
    default: ''
    aliases: [ content ]
  insertafter:
    description:
    - If specified and no begin/ending C(marker) lines are found, the block will be inserted after the last match of specified regular expression.
    - A special value is available; C(EOF) for inserting the block at the end of the file.
    - If specified regular expression has no matches, C(EOF) will be used instead.
    type: str
    choices: [ EOF, '*regex*' ]
    default: EOF
  insertbefore:
    description:
    - If specified and no begin/ending C(marker) lines are found, the block will be inserted before the last match of specified regular expression.
    - A special value is available; C(BOF) for inserting the block at the beginning of the file.
    - If specified regular expression has no matches, the block will be inserted at the end of the file.
    type: str
    choices: [ BOF, '*regex*' ]
  create:
    description:
    - Create a new file if it does not exist.
    type: bool
    default: no
  backup:
    description:
    - Create a backup file including the timestamp information so you can
      get the original file back if you somehow clobbered it incorrectly.
    type: bool
    default: no
  marker_begin:
    description:
    - This will be inserted at C({mark}) in the opening ansible block marker.
    type: str
    default: BEGIN
    version_added: '2.5'
  marker_end:
    required: false
    description:
    - This will be inserted at C({mark}) in the closing ansible block marker.
    type: str
    default: END
    version_added: '2.5'
notes:
  - This module supports check mode.
  - When using 'with_*' loops be aware that if you do not set a unique mark the block will be overwritten on each iteration.
  - As of Ansible 2.3, the I(dest) option has been changed to I(path) as default, but I(dest) still works as well.
  - Option I(follow) has been removed in Ansible 2.5, because this module modifies the contents of the file so I(follow=no) doesn't make sense.
  - When more then one block should be handled in one file you must change the I(marker) per task.
extends_documentation_fragment:
- files
- validate
'''

EXAMPLES = r'''
# Before Ansible 2.3, option 'dest' or 'name' was used instead of 'path'
- name: Insert/Update "Match User" configuration block in /etc/ssh/sshd_config
  blockinfile:
    path: /etc/ssh/sshd_config
    block: |
      Match User ansible-agent
      PasswordAuthentication no

- name: Insert/Update eth0 configuration stanza in /etc/network/interfaces
        (it might be better to copy files into /etc/network/interfaces.d/)
  blockinfile:
    path: /etc/network/interfaces
    block: |
      iface eth0 inet static
          address 192.0.2.23
          netmask 255.255.255.0

- name: Insert/Update configuration using a local file and validate it
  blockinfile:
    block: "{{ lookup('file', './local/sshd_config') }}"
    path: /etc/ssh/sshd_config
    backup: yes
    validate: /usr/sbin/sshd -T -f %s

- name: Insert/Update HTML surrounded by custom markers after <body> line
  blockinfile:
    path: /var/www/html/index.html
    marker: "<!-- {mark} ANSIBLE MANAGED BLOCK -->"
    insertafter: "<body>"
    block: |
      <h1>Welcome to {{ ansible_hostname }}</h1>
      <p>Last updated on {{ ansible_date_time.iso8601 }}</p>

- name: Remove HTML as well as surrounding markers
  blockinfile:
    path: /var/www/html/index.html
    marker: "<!-- {mark} ANSIBLE MANAGED BLOCK -->"
    block: ""

- name: Add mappings to /etc/hosts
  blockinfile:
    path: /etc/hosts
    block: |
      {{ item.ip }} {{ item.name }}
    marker: "# {mark} ANSIBLE MANAGED BLOCK {{ item.name }}"
  loop:
    - { name: host1, ip: 10.10.1.10 }
    - { name: host2, ip: 10.10.1.11 }
    - { name: host3, ip: 10.10.1.12 }
'''

import re
import os
import tempfile
from ansible.module_utils.six import b
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_bytes


def write_changes(module, contents, path):

    tmpfd, tmpfile = tempfile.mkstemp(dir=module.tmpdir)
    f = os.fdopen(tmpfd, 'wb')
    f.write(contents)
    f.close()

    validate = module.params.get('validate', None)
    valid = not validate
    if validate:
        if "%s" not in validate:
            module.fail_json(msg="validate must contain %%s: %s" % (validate))
        (rc, out, err) = module.run_command(validate % tmpfile)
        valid = rc == 0
        if rc != 0:
            module.fail_json(msg='failed to validate: '
                                 'rc:%s error:%s' % (rc, err))
    if valid:
        module.atomic_move(tmpfile, path, unsafe_writes=module.params['unsafe_writes'])


def check_file_attrs(module, changed, message, diff):

    file_args = module.load_file_common_arguments(module.params)
    if module.set_file_attributes_if_different(file_args, False, diff=diff):

        if changed:
            message += " and "
        changed = True
        message += "ownership, perms or SE linux context changed"

    return message, changed


def main():
    module = AnsibleModule(
        argument_spec=dict(
            path=dict(type='path', required=True, aliases=['dest', 'destfile', 'name']),
            state=dict(type='str', default='present', choices=['absent', 'present']),
            marker=dict(type='str', default='# {mark} ANSIBLE MANAGED BLOCK'),
            block=dict(type='str', default='', aliases=['content']),
            insertafter=dict(type='str'),
            insertbefore=dict(type='str'),
            create=dict(type='bool', default=False),
            backup=dict(type='bool', default=False),
            validate=dict(type='str'),
            marker_begin=dict(type='str', default='BEGIN'),
            marker_end=dict(type='str', default='END'),
        ),
        mutually_exclusive=[['insertbefore', 'insertafter']],
        add_file_common_args=True,
        supports_check_mode=True
    )
    params = module.params
    path = params['path']

    if os.path.isdir(path):
        module.fail_json(rc=256,
                         msg='Path %s is a directory !' % path)

    path_exists = os.path.exists(path)
    if not path_exists:
        if not module.boolean(params['create']):
            module.fail_json(rc=257,
                             msg='Path %s does not exist !' % path)
        destpath = os.path.dirname(path)
        if not os.path.exists(destpath) and not module.check_mode:
            try:
                os.makedirs(destpath)
            except Exception as e:
                module.fail_json(msg='Error creating %s Error code: %s Error description: %s' % (destpath, e[0], e[1]))
        original = None
        lines = []
    else:
        f = open(path, 'rb')
        original = f.read()
        f.close()
        lines = original.splitlines(True)

    diff = {'before': '',
            'after': '',
            'before_header': '%s (content)' % path,
            'after_header': '%s (content)' % path}

    if module._diff and original:
        diff['before'] = original

    insertbefore = params['insertbefore']
    insertafter = params['insertafter']
    block = to_bytes(params['block'])
    marker = to_bytes(params['marker'])
    present = params['state'] == 'present'

    if not present and not path_exists:
        module.exit_json(changed=False, msg="File %s not present" % path)

    if insertbefore is None and insertafter is None:
        insertafter = 'EOF'

    if insertafter not in (None, 'EOF'):
        insertre = re.compile(to_bytes(insertafter, errors='surrogate_or_strict'))
    elif insertbefore not in (None, 'BOF'):
        insertre = re.compile(to_bytes(insertbefore, errors='surrogate_or_strict'))
    else:
        insertre = None

    marker0 = re.sub(b(r'{mark}'), b(params['marker_begin']), marker) + b(os.linesep)
    marker1 = re.sub(b(r'{mark}'), b(params['marker_end']), marker) + b(os.linesep)
    if present and block:
        # Escape sequences like '\n' need to be handled in Ansible 1.x
        if module.ansible_version.startswith('1.'):
            block = re.sub('', block, '')
        if not block.endswith(b(os.linesep)):
            block += b(os.linesep)
        blocklines = [marker0] + block.splitlines(True) + [marker1]
    else:
        blocklines = []

    n0 = n1 = None
    for i, line in enumerate(lines):
        if line == marker0:
            n0 = i
        if line == marker1:
            n1 = i

    if None in (n0, n1):
        n0 = None
        if insertre is not None:
            for i, line in enumerate(lines):
                if insertre.search(line):
                    n0 = i
            if n0 is None:
                n0 = len(lines)
            elif insertafter is not None:
                n0 += 1
        elif insertbefore is not None:
            n0 = 0  # insertbefore=BOF
        else:
            n0 = len(lines)  # insertafter=EOF
    elif n0 < n1:
        lines[n0:n1 + 1] = []
    else:
        lines[n1:n0 + 1] = []
        n0 = n1

    # Ensure there is a line separator before the block of lines to be inserted
    if n0 > 0:
        if not lines[n0 - 1].endswith(b(os.linesep)):
            lines[n0 - 1] += b(os.linesep)

    lines[n0:n0] = blocklines
    if lines:
        result = b''.join(lines)
    else:
        result = b''

    if module._diff:
        diff['after'] = result

    if original == result:
        msg = ''
        changed = False
    elif original is None:
        msg = 'File created'
        changed = True
    elif not blocklines:
        msg = 'Block removed'
        changed = True
    else:
        msg = 'Block inserted'
        changed = True

    if changed and not module.check_mode:
        if module.boolean(params['backup']) and path_exists:
            module.backup_local(path)
        # We should always follow symlinks so that we change the real file
        real_path = os.path.realpath(params['path'])
        write_changes(module, result, real_path)

    if module.check_mode and not path_exists:
        module.exit_json(changed=changed, msg=msg, diff=diff)

    attr_diff = {}
    msg, changed = check_file_attrs(module, changed, msg, attr_diff)

    attr_diff['before_header'] = '%s (file attributes)' % path
    attr_diff['after_header'] = '%s (file attributes)' % path

    difflist = [diff, attr_diff]
    module.exit_json(changed=changed, msg=msg, diff=difflist)


if __name__ == '__main__':
    main()
