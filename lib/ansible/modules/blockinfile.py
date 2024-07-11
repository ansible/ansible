# -*- coding: utf-8 -*-

# Copyright: (c) 2014, 2015 YAEGASHI Takeshi <yaegashi@debian.org>
# Copyright: (c) 2017, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations


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
    - Before Ansible 2.3 this option was only usable as O(dest), O(destfile) and O(name).
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
    - C({mark}) will be replaced with the values in O(marker_begin) (default=C(BEGIN)) and O(marker_end) (default=C(END)).
    - Using a custom marker without the C({mark}) variable may result in the block being repeatedly inserted on subsequent playbook runs.
    - Multi-line markers are not supported and will result in the block being repeatedly inserted on subsequent playbook runs.
    - A newline is automatically appended by the module to O(marker_begin) and O(marker_end).
    type: str
    default: '# {mark} ANSIBLE MANAGED BLOCK'
  block:
    description:
    - The text to insert inside the marker lines.
    - If it is missing or an empty string, the block will be removed as if O(state) were specified to V(absent).
    type: str
    default: ''
    aliases: [ content ]
  insertafter:
    description:
    - If specified and no begin/ending O(marker) lines are found, the block will be inserted after the last match of specified regular expression.
    - A special value is available; V(EOF) for inserting the block at the end of the file.
    - If specified regular expression has no matches or no value is passed, V(EOF) will be used instead.
    - The presence of the multiline flag (?m) in the regular expression controls whether the match is done line by line or with multiple lines.
      This behaviour was added in ansible-core 2.14.
    type: str
  insertbefore:
    description:
    - If specified and no begin/ending O(marker) lines are found, the block will be inserted before the last match of specified regular expression.
    - A special value is available; V(BOF) for inserting the block at the beginning of the file.
    - If specified regular expression has no matches, the block will be inserted at the end of the file.
    - The presence of the multiline flag (?m) in the regular expression controls whether the match is done line by line or with multiple lines.
      This behaviour was added in ansible-core 2.14.
    type: str
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
    - This will be inserted at C({mark}) in the opening ansible block O(marker).
    type: str
    default: BEGIN
    version_added: '2.5'
  marker_end:
    required: false
    description:
    - This will be inserted at C({mark}) in the closing ansible block O(marker).
    type: str
    default: END
    version_added: '2.5'
  append_newline:
    required: false
    description:
    - Append a blank line to the inserted block, if this does not appear at the end of the file.
    - Note that this attribute is not considered when C(state) is set to C(absent)
    type: bool
    default: no
    version_added: '2.16'
  prepend_newline:
    required: false
    description:
    - Prepend a blank line to the inserted block, if this does not appear at the beginning of the file.
    - Note that this attribute is not considered when C(state) is set to C(absent)
    type: bool
    default: no
    version_added: '2.16'
notes:
  - When using C(with_*) loops be aware that if you do not set a unique mark the block will be overwritten on each iteration.
  - As of Ansible 2.3, the O(dest) option has been changed to O(path) as default, but O(dest) still works as well.
  - Option O(ignore:follow) has been removed in Ansible 2.5, because this module modifies the contents of the file
    so O(ignore:follow=no) does not make sense.
  - When more than one block should be handled in one file you must change the O(marker) per task.
extends_documentation_fragment:
    - action_common_attributes
    - action_common_attributes.files
    - files
    - validate
attributes:
    check_mode:
        support: full
    diff_mode:
        support: full
    safe_file_operations:
      support: full
    platform:
      support: full
      platforms: posix
    vault:
      support: none
'''

EXAMPLES = r'''
# Before Ansible 2.3, option 'dest' or 'name' was used instead of 'path'
- name: Insert/Update "Match User" configuration block in /etc/ssh/sshd_config prepending and appending a new line
  ansible.builtin.blockinfile:
    path: /etc/ssh/sshd_config
    append_newline: true
    prepend_newline: true
    block: |
      Match User ansible-agent
      PasswordAuthentication no

- name: Insert/Update eth0 configuration stanza in /etc/network/interfaces
        (it might be better to copy files into /etc/network/interfaces.d/)
  ansible.builtin.blockinfile:
    path: /etc/network/interfaces
    block: |
      iface eth0 inet static
          address 192.0.2.23
          netmask 255.255.255.0

- name: Insert/Update configuration using a local file and validate it
  ansible.builtin.blockinfile:
    block: "{{ lookup('ansible.builtin.file', './local/sshd_config') }}"
    path: /etc/ssh/sshd_config
    backup: yes
    validate: /usr/sbin/sshd -T -f %s

- name: Insert/Update HTML surrounded by custom markers after <body> line
  ansible.builtin.blockinfile:
    path: /var/www/html/index.html
    marker: "<!-- {mark} ANSIBLE MANAGED BLOCK -->"
    insertafter: "<body>"
    block: |
      <h1>Welcome to {{ ansible_hostname }}</h1>
      <p>Last updated on {{ ansible_date_time.iso8601 }}</p>

- name: Remove HTML as well as surrounding markers
  ansible.builtin.blockinfile:
    path: /var/www/html/index.html
    marker: "<!-- {mark} ANSIBLE MANAGED BLOCK -->"
    block: ""

- name: Add mappings to /etc/hosts
  ansible.builtin.blockinfile:
    path: /etc/hosts
    block: |
      {{ item.ip }} {{ item.name }}
    marker: "# {mark} ANSIBLE MANAGED BLOCK {{ item.name }}"
  loop:
    - { name: host1, ip: 10.10.1.10 }
    - { name: host2, ip: 10.10.1.11 }
    - { name: host3, ip: 10.10.1.12 }

- name: Search with a multiline search flags regex and if found insert after
  blockinfile:
    path: listener.ora
    block: "{{ listener_line | indent(width=8, first=True) }}"
    insertafter: '(?m)SID_LIST_LISTENER_DG =\n.*\(SID_LIST ='
    marker: "    <!-- {mark} ANSIBLE MANAGED BLOCK -->"

'''

import re
import os
import tempfile
from ansible.module_utils.six import b
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.common.text.converters import to_bytes, to_native


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
            append_newline=dict(type='bool', default=False),
            prepend_newline=dict(type='bool', default=False),
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
        if destpath and not os.path.exists(destpath) and not module.check_mode:
            try:
                os.makedirs(destpath)
            except OSError as e:
                module.fail_json(msg='Error creating %s Error code: %s Error description: %s' % (destpath, e.errno, e.strerror))
            except Exception as e:
                module.fail_json(msg='Error creating %s Error: %s' % (destpath, to_native(e)))
        original = None
        lines = []
    else:
        with open(path, 'rb') as f:
            original = f.read()
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
    blank_line = [b(os.linesep)]

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
            if insertre.flags & re.MULTILINE:
                match = insertre.search(original)
                if match:
                    if insertafter:
                        n0 = to_native(original).count('\n', 0, match.end())
                    elif insertbefore:
                        n0 = to_native(original).count('\n', 0, match.start())
            else:
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

    # Before the block: check if we need to prepend a blank line
    # If yes, we need to add the blank line if we are not at the beginning of the file
    # and the previous line is not a blank line
    # In both cases, we need to shift by one on the right the inserting position of the block
    if params['prepend_newline'] and present:
        if n0 != 0 and lines[n0 - 1] != b(os.linesep):
            lines[n0:n0] = blank_line
            n0 += 1

    # Insert the block
    lines[n0:n0] = blocklines

    # After the block: check if we need to append a blank line
    # If yes, we need to add the blank line if we are not at the end of the file
    # and the line right after is not a blank line
    if params['append_newline'] and present:
        line_after_block = n0 + len(blocklines)
        if line_after_block < len(lines) and lines[line_after_block] != b(os.linesep):
            lines[line_after_block:line_after_block] = blank_line

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

    backup_file = None
    if changed and not module.check_mode:
        if module.boolean(params['backup']) and path_exists:
            backup_file = module.backup_local(path)
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

    if backup_file is None:
        module.exit_json(changed=changed, msg=msg, diff=difflist)
    else:
        module.exit_json(changed=changed, msg=msg, diff=difflist, backup_file=backup_file)


if __name__ == '__main__':
    main()
