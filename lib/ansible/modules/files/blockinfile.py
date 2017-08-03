#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2014, 2015 YAEGASHI Takeshi <yaegashi@debian.org>
# Copyright: (c) 2017, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'core'}


DOCUMENTATION = """
---
module: blockinfile
author:
    - 'YAEGASHI Takeshi (@yaegashi)'
extends_documentation_fragment:
    - files
    - validate
short_description: Insert/update/remove a text block
                   surrounded by marker lines.
version_added: '2.0'
description:
  - This module will insert/update/remove a block of multi-line text
    surrounded by customizable marker lines.
options:
  path:
    aliases: [ dest, destfile, name ]
    required: true
    description:
      - The file to modify.
      - Before 2.3 this option was only usable as I(dest), I(destfile) and I(name).
  state:
    required: false
    choices: [ present, absent ]
    default: present
    description:
      - Whether the block should be there or not.
  marker:
    required: false
    default: '# {mark} ANSIBLE MANAGED BLOCK'
    description:
      - The marker line template.
        "{mark}" will be replaced with "BEGIN" or "END".
  block:
    aliases: [ content ]
    required: false
    default: ''
    description:
      - The text to insert inside the marker lines.
        If it's missing or an empty string,
        the block will be removed as if C(state) were specified to C(absent).
  insertafter:
    required: false
    default: EOF
    description:
      - If specified, the block will be inserted after the last match of
        specified regular expression. A special value is available; C(EOF) for
        inserting the block at the end of the file.  If specified regular
        expression has no matches, C(EOF) will be used instead.
    choices: [ 'EOF', '*regex*' ]
  insertbefore:
    required: false
    default: None
    description:
      - If specified, the block will be inserted before the last match of
        specified regular expression. A special value is available; C(BOF) for
        inserting the block at the beginning of the file.  If specified regular
        expression has no matches, the block will be inserted at the end of the
        file.
    choices: [ 'BOF', '*regex*' ]
  create:
    required: false
    default: 'no'
    choices: [ 'yes', 'no' ]
    description:
      - Create a new file if it doesn't exist.
  backup:
    required: false
    default: 'no'
    choices: [ 'yes', 'no' ]
    description:
      - Create a backup file including the timestamp information so you can
        get the original file back if you somehow clobbered it incorrectly.
  follow:
    required: false
    default: "no"
    choices: [ "yes", "no" ]
    description:
      - 'This flag indicates that filesystem links, if they exist, should be followed.'
    version_added: "2.1"
notes:
  - This module supports check mode.
  - When using 'with_*' loops be aware that if you do not set a unique mark the block will be overwritten on each iteration.
  - As of Ansible 2.3, the I(dest) option has been changed to I(path) as default, but I(dest) still works as well.
"""

EXAMPLES = r"""
# Before 2.3, option 'dest' or 'name' was used instead of 'path'
- name: insert/update "Match User" configuration block in /etc/ssh/sshd_config
  blockinfile:
    path: /etc/ssh/sshd_config
    block: |
      Match User ansible-agent
      PasswordAuthentication no

- name: insert/update eth0 configuration stanza in /etc/network/interfaces
        (it might be better to copy files into /etc/network/interfaces.d/)
  blockinfile:
    path: /etc/network/interfaces
    block: |
      iface eth0 inet static
          address 192.0.2.23
          netmask 255.255.255.0

- name: insert/update configuration using a local file
  blockinfile:
    block: "{{ lookup('file', './local/ssh_config') }}"
    dest: "/etc/ssh/ssh_config"
    backup: yes

- name: insert/update HTML surrounded by custom markers after <body> line
  blockinfile:
    path: /var/www/html/index.html
    marker: "<!-- {mark} ANSIBLE MANAGED BLOCK -->"
    insertafter: "<body>"
    content: |
      <h1>Welcome to {{ ansible_hostname }}</h1>
      <p>Last updated on {{ ansible_date_time.iso8601 }}</p>

- name: remove HTML as well as surrounding markers
  blockinfile:
    path: /var/www/html/index.html
    marker: "<!-- {mark} ANSIBLE MANAGED BLOCK -->"
    content: ""

- name: Add mappings to /etc/hosts
  blockinfile:
    path: /etc/hosts
    block: |
      {{ item.ip }} {{ item.name }}
    marker: "# {mark} ANSIBLE MANAGED BLOCK {{ item.name }}"
  with_items:
    - { name: host1, ip: 10.10.1.10 }
    - { name: host2, ip: 10.10.1.11 }
    - { name: host3, ip: 10.10.1.12 }
"""

import re
import os
import tempfile
from ansible.module_utils.six import b
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_bytes


def write_changes(module, contents, path):

    tmpfd, tmpfile = tempfile.mkstemp()
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


def check_file_attrs(module, changed, message):

    file_args = module.load_file_common_arguments(module.params)
    if module.set_file_attributes_if_different(file_args, False):

        if changed:
            message += " and "
        changed = True
        message += "ownership, perms or SE linux context changed"

    return message, changed


def main():
    module = AnsibleModule(
        argument_spec=dict(
            path=dict(required=True, aliases=['dest', 'destfile', 'name'], type='path'),
            state=dict(default='present', choices=['absent', 'present']),
            marker=dict(default='# {mark} ANSIBLE MANAGED BLOCK', type='str'),
            block=dict(default='', type='str', aliases=['content']),
            insertafter=dict(default=None),
            insertbefore=dict(default=None),
            create=dict(default=False, type='bool'),
            backup=dict(default=False, type='bool'),
            validate=dict(default=None, type='str'),
        ),
        mutually_exclusive=[['insertbefore', 'insertafter']],
        add_file_common_args=True,
        supports_check_mode=True
    )

    params = module.params
    path = params['path']
    if module.boolean(params.get('follow', None)):
        path = os.path.realpath(path)

    if os.path.isdir(path):
        module.fail_json(rc=256,
                         msg='Path %s is a directory !' % path)

    path_exists = os.path.exists(path)
    if not path_exists:
        if not module.boolean(params['create']):
            module.fail_json(rc=257,
                             msg='Path %s does not exist !' % path)
        original = None
        lines = []
    else:
        f = open(path, 'rb')
        original = f.read()
        f.close()
        lines = original.splitlines()

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
        insertre = re.compile(insertafter)
    elif insertbefore not in (None, 'BOF'):
        insertre = re.compile(insertbefore)
    else:
        insertre = None

    marker0 = re.sub(b(r'{mark}'), b('BEGIN'), marker)
    marker1 = re.sub(b(r'{mark}'), b('END'), marker)
    if present and block:
        # Escape seqeuences like '\n' need to be handled in Ansible 1.x
        if module.ansible_version.startswith('1.'):
            block = re.sub('', block, '')
        blocklines = [marker0] + block.splitlines() + [marker1]
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
            n0 = 0           # insertbefore=BOF
        else:
            n0 = len(lines)  # insertafter=EOF
    elif n0 < n1:
        lines[n0:n1+1] = []
    else:
        lines[n1:n0+1] = []
        n0 = n1

    lines[n0:n0] = blocklines

    if lines:
        result = b('\n').join(lines)
        if original is None or original.endswith(b('\n')):
            result += b('\n')
    else:
        result = ''
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
        write_changes(module, result, path)

    if module.check_mode and not path_exists:
        module.exit_json(changed=changed, msg=msg)

    msg, changed = check_file_attrs(module, changed, msg)
    module.exit_json(changed=changed, msg=msg)


if __name__ == '__main__':
    main()
