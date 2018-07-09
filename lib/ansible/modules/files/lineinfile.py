#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2012, Daniel Hokka Zakrisson <daniel@hozac.com>
# Copyright: (c) 2014, Ahti Kitsik <ak@ahtik.com>
# Copyright: (c) 2017, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'core'}


DOCUMENTATION = """
---
module: lineinfile
author:
    - Daniel Hokka Zakrissoni (@dhozac)
    - Ahti Kitsik (@ahtik)
extends_documentation_fragment:
    - files
    - validate
short_description: Manage lines in text files
description:
  - This module ensures a particular line is in a file, or replace an
    existing line using a back-referenced regular expression.
  - This is primarily useful when you want to change a single line in
    a file only. See the M(replace) module if you want to change
    multiple, similar lines or check M(blockinfile) if you want to insert/update/remove a block of lines in a file.
    For other cases, see the M(copy) or M(template) modules.
version_added: "0.7"
options:
  path:
    description:
      - The file to modify.
      - Before 2.3 this option was only usable as I(dest), I(destfile) and I(name).
    aliases: [ dest, destfile, name ]
    required: true
  regexp:
    description:
      - The regular expression to look for in every line of the file. For
        C(state=present), the pattern to replace if found. Only the last line
        found will be replaced. For C(state=absent), the pattern of the line(s)
        to remove. Uses Python regular expressions.
        See U(http://docs.python.org/2/library/re.html).
    version_added: '1.7'
  state:
    description:
      - Whether the line should be there or not.
    choices: [ absent, present ]
    default: present
  line:
    description:
      - Required for C(state=present). The line to insert/replace into the
        file. If C(backrefs) is set, may contain backreferences that will get
        expanded with the C(regexp) capture groups if the regexp matches.
  backrefs:
    description:
      - Used with C(state=present). If set, C(line) can contain backreferences
        (both positional and named) that will get populated if the C(regexp)
        matches. This flag changes the operation of the module slightly;
        C(insertbefore) and C(insertafter) will be ignored, and if the C(regexp)
        doesn't match anywhere in the file, the file will be left unchanged.
        If the C(regexp) does match, the last matching line will be replaced by
        the expanded line parameter.
    type: bool
    default: 'no'
    version_added: "1.1"
  insertafter:
    description:
      - Used with C(state=present). If specified, the line will be inserted
        after the last match of specified regular expression.
        If the first match is required, use(firstmatch=yes).
        A special value is available; C(EOF) for inserting the line at the
        end of the file.
        If specified regular expression has no matches, EOF will be used instead.
        May not be used with C(backrefs).
    choices: [ EOF, '*regex*' ]
    default: EOF
  insertbefore:
    description:
      - Used with C(state=present). If specified, the line will be inserted
        before the last match of specified regular expression.
        If the first match is required, use(firstmatch=yes).
        A value is available; C(BOF) for inserting the line at
        the beginning of the file.
        If specified regular expression has no matches, the line will be
        inserted at the end of the file.  May not be used with C(backrefs).
    choices: [ BOF, '*regex*' ]
    version_added: "1.1"
  create:
    description:
      - Used with C(state=present). If specified, the file will be created
        if it does not already exist. By default it will fail if the file
        is missing.
    type: bool
    default: 'no'
  backup:
     description:
       - Create a backup file including the timestamp information so you can
         get the original file back if you somehow clobbered it incorrectly.
     type: bool
     default: 'no'
  firstmatch:
    description:
      - Used with C(insertafter) or C(insertbefore). If set, C(insertafter) and C(inserbefore) find
        a first line has regular expression matches.
    type: bool
    default: 'no'
    version_added: "2.5"
  others:
     description:
       - All arguments accepted by the M(file) module also work here.
notes:
  - As of Ansible 2.3, the I(dest) option has been changed to I(path) as default, but I(dest) still works as well.
"""

EXAMPLES = r"""
# Before 2.3, option 'dest', 'destfile' or 'name' was used instead of 'path'
- lineinfile:
    path: /etc/selinux/config
    regexp: '^SELINUX='
    line: 'SELINUX=enforcing'

- lineinfile:
    path: /etc/sudoers
    state: absent
    regexp: '^%wheel'

- lineinfile:
    path: /etc/hosts
    regexp: '^127\.0\.0\.1'
    line: '127.0.0.1 localhost'
    owner: root
    group: root
    mode: 0644

- lineinfile:
    path: /etc/httpd/conf/httpd.conf
    regexp: '^Listen '
    insertafter: '^#Listen '
    line: 'Listen 8080'

- lineinfile:
    path: /etc/services
    regexp: '^# port for http'
    insertbefore: '^www.*80/tcp'
    line: '# port for http by default'

# Add a line to a file if the file does not exist, without passing regexp
- lineinfile:
    path: /tmp/testfile
    line: '192.168.1.99 foo.lab.net foo'
    create: yes

# Fully quoted because of the ': ' on the line. See the Gotchas in the YAML docs.
- lineinfile:
    path: /etc/sudoers
    state: present
    regexp: '^%wheel\s'
    line: '%wheel ALL=(ALL) NOPASSWD: ALL'

# Yaml requires escaping backslashes in double quotes but not in single quotes
- lineinfile:
    path: /opt/jboss-as/bin/standalone.conf
    regexp: '^(.*)Xms(\\d+)m(.*)$'
    line: '\1Xms${xms}m\3'
    backrefs: yes

# Validate the sudoers file before saving
- lineinfile:
    path: /etc/sudoers
    state: present
    regexp: '^%ADMIN ALL='
    line: '%ADMIN ALL=(ALL) NOPASSWD: ALL'
    validate: '/usr/sbin/visudo -cf %s'
"""

import os
import re
import tempfile

# import module snippets
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.six import b
from ansible.module_utils._text import to_bytes, to_native


def write_changes(module, b_lines, dest):

    tmpfd, tmpfile = tempfile.mkstemp()
    f = os.fdopen(tmpfd, 'wb')
    f.writelines(b_lines)
    f.close()

    validate = module.params.get('validate', None)
    valid = not validate
    if validate:
        if "%s" not in validate:
            module.fail_json(msg="validate must contain %%s: %s" % (validate))
        (rc, out, err) = module.run_command(to_bytes(validate % tmpfile, errors='surrogate_or_strict'))
        valid = rc == 0
        if rc != 0:
            module.fail_json(msg='failed to validate: '
                                 'rc:%s error:%s' % (rc, err))
    if valid:
        module.atomic_move(tmpfile,
                           to_native(os.path.realpath(to_bytes(dest, errors='surrogate_or_strict')), errors='surrogate_or_strict'),
                           unsafe_writes=module.params['unsafe_writes'])


def check_file_attrs(module, changed, message, diff):

    file_args = module.load_file_common_arguments(module.params)
    if module.set_fs_attributes_if_different(file_args, False, diff=diff):

        if changed:
            message += " and "
        changed = True
        message += "ownership, perms or SE linux context changed"

    return message, changed


def present(module, dest, regexp, line, insertafter, insertbefore, create,
            backup, backrefs, firstmatch):

    diff = {'before': '',
            'after': '',
            'before_header': '%s (content)' % dest,
            'after_header': '%s (content)' % dest}

    b_dest = to_bytes(dest, errors='surrogate_or_strict')
    if not os.path.exists(b_dest):
        if not create:
            module.fail_json(rc=257, msg='Destination %s does not exist !' % dest)
        b_destpath = os.path.dirname(b_dest)
        if not os.path.exists(b_destpath) and not module.check_mode:
            try:
                os.makedirs(b_destpath)
            except Exception as e:
                module.fail_json(msg='Error creating %s Error code: %s Error description: %s' % (b_destpath, e[0], e[1]))

        b_lines = []
    else:
        f = open(b_dest, 'rb')
        b_lines = f.readlines()
        f.close()

    if module._diff:
        diff['before'] = to_native(b('').join(b_lines))

    if regexp is not None:
        bre_m = re.compile(to_bytes(regexp, errors='surrogate_or_strict'))

    if insertafter not in (None, 'BOF', 'EOF'):
        bre_ins = re.compile(to_bytes(insertafter, errors='surrogate_or_strict'))
    elif insertbefore not in (None, 'BOF'):
        bre_ins = re.compile(to_bytes(insertbefore, errors='surrogate_or_strict'))
    else:
        bre_ins = None

    # index[0] is the line num where regexp has been found
    # index[1] is the line num where insertafter/inserbefore has been found
    index = [-1, -1]
    m = None
    b_line = to_bytes(line, errors='surrogate_or_strict')
    for lineno, b_cur_line in enumerate(b_lines):
        if regexp is not None:
            match_found = bre_m.search(b_cur_line)
        else:
            match_found = b_line == b_cur_line.rstrip(b('\r\n'))
        if match_found:
            index[0] = lineno
            m = match_found
        elif bre_ins is not None and bre_ins.search(b_cur_line):
            if insertafter:
                # + 1 for the next line
                index[1] = lineno + 1
                if firstmatch:
                    break
            if insertbefore:
                # index[1] for the previous line
                index[1] = lineno
                if firstmatch:
                    break

    msg = ''
    changed = False
    b_linesep = to_bytes(os.linesep, errors='surrogate_or_strict')
    # Regexp matched a line in the file
    if index[0] != -1:
        if backrefs:
            b_new_line = m.expand(b_line)
        else:
            # Don't do backref expansion if not asked.
            b_new_line = b_line

        if not b_new_line.endswith(b_linesep):
            b_new_line += b_linesep

        # If no regexp was given and a line match is found anywhere in the file,
        # insert the line appropriately if using insertbefore or insertafter
        if regexp is None and m:

            # Insert lines
            if insertafter and insertafter != 'EOF':
                # Ensure there is a line separator after the found string
                # at the end of the file.
                if b_lines and not b_lines[-1][-1:] in (b('\n'), b('\r')):
                    b_lines[-1] = b_lines[-1] + b_linesep

                # If the line to insert after is at the end of the file
                # use the appropriate index value.
                if len(b_lines) == index[1]:
                    if b_lines[index[1] - 1].rstrip(b('\r\n')) != b_line:
                        b_lines.append(b_line + b_linesep)
                        msg = 'line added'
                        changed = True
                elif b_lines[index[1]].rstrip(b('\r\n')) != b_line:
                    b_lines.insert(index[1], b_line + b_linesep)
                    msg = 'line added'
                    changed = True

            elif insertbefore and insertbefore != 'BOF':
                # If the line to insert before is at the beginning of the file
                # use the appropriate index value.
                if index[1] == 0:
                    if b_lines[index[1]].rstrip(b('\r\n')) != b_line:
                        b_lines.insert(index[1], b_line + b_linesep)
                        msg = 'line replaced'
                        changed = True

                elif b_lines[index[1] - 1].rstrip(b('\r\n')) != b_line:
                    b_lines.insert(index[1], b_line + b_linesep)
                    msg = 'line replaced'
                    changed = True

        elif b_lines[index[0]] != b_new_line:
            b_lines[index[0]] = b_new_line
            msg = 'line replaced'
            changed = True

    elif backrefs:
        # Do absolutely nothing, since it's not safe generating the line
        # without the regexp matching to populate the backrefs.
        pass
    # Add it to the beginning of the file
    elif insertbefore == 'BOF' or insertafter == 'BOF':
        b_lines.insert(0, b_line + b_linesep)
        msg = 'line added'
        changed = True
    # Add it to the end of the file if requested or
    # if insertafter/insertbefore didn't match anything
    # (so default behaviour is to add at the end)
    elif insertafter == 'EOF' or index[1] == -1:

        # If the file is not empty then ensure there's a newline before the added line
        if b_lines and not b_lines[-1][-1:] in (b('\n'), b('\r')):
            b_lines.append(b_linesep)

        b_lines.append(b_line + b_linesep)
        msg = 'line added'
        changed = True
    # insert matched, but not the regexp
    else:
        b_lines.insert(index[1], b_line + b_linesep)
        msg = 'line added'
        changed = True

    if module._diff:
        diff['after'] = to_native(b('').join(b_lines))

    backupdest = ""
    if changed and not module.check_mode:
        if backup and os.path.exists(b_dest):
            backupdest = module.backup_local(dest)
        write_changes(module, b_lines, dest)

    if module.check_mode and not os.path.exists(b_dest):
        module.exit_json(changed=changed, msg=msg, backup=backupdest, diff=diff)

    attr_diff = {}
    msg, changed = check_file_attrs(module, changed, msg, attr_diff)

    attr_diff['before_header'] = '%s (file attributes)' % dest
    attr_diff['after_header'] = '%s (file attributes)' % dest

    difflist = [diff, attr_diff]
    module.exit_json(changed=changed, msg=msg, backup=backupdest, diff=difflist)


def absent(module, dest, regexp, line, backup):

    b_dest = to_bytes(dest, errors='surrogate_or_strict')
    if not os.path.exists(b_dest):
        module.exit_json(changed=False, msg="file not present")

    msg = ''
    diff = {'before': '',
            'after': '',
            'before_header': '%s (content)' % dest,
            'after_header': '%s (content)' % dest}

    f = open(b_dest, 'rb')
    b_lines = f.readlines()
    f.close()

    if module._diff:
        diff['before'] = to_native(b('').join(b_lines))

    if regexp is not None:
        bre_c = re.compile(to_bytes(regexp, errors='surrogate_or_strict'))
    found = []

    b_line = to_bytes(line, errors='surrogate_or_strict')

    def matcher(b_cur_line):
        if regexp is not None:
            match_found = bre_c.search(b_cur_line)
        else:
            match_found = b_line == b_cur_line.rstrip(b('\r\n'))
        if match_found:
            found.append(b_cur_line)
        return not match_found

    b_lines = [l for l in b_lines if matcher(l)]
    changed = len(found) > 0

    if module._diff:
        diff['after'] = to_native(b('').join(b_lines))

    backupdest = ""
    if changed and not module.check_mode:
        if backup:
            backupdest = module.backup_local(dest)
        write_changes(module, b_lines, dest)

    if changed:
        msg = "%s line(s) removed" % len(found)

    attr_diff = {}
    msg, changed = check_file_attrs(module, changed, msg, attr_diff)

    attr_diff['before_header'] = '%s (file attributes)' % dest
    attr_diff['after_header'] = '%s (file attributes)' % dest

    difflist = [diff, attr_diff]

    module.exit_json(changed=changed, found=len(found), msg=msg, backup=backupdest, diff=difflist)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            path=dict(type='path', required=True, aliases=['dest', 'destfile', 'name']),
            state=dict(type='str', default='present', choices=['absent', 'present']),
            regexp=dict(type='str'),
            line=dict(type='str', aliases=['value']),
            insertafter=dict(type='str'),
            insertbefore=dict(type='str'),
            backrefs=dict(type='bool', default=False),
            create=dict(type='bool', default=False),
            backup=dict(type='bool', default=False),
            firstmatch=dict(default=False, type='bool'),
            validate=dict(type='str'),
        ),
        mutually_exclusive=[['insertbefore', 'insertafter']],
        add_file_common_args=True,
        supports_check_mode=True,
    )

    params = module.params
    create = params['create']
    backup = params['backup']
    backrefs = params['backrefs']
    path = params['path']
    firstmatch = params['firstmatch']
    regexp = params['regexp']
    line = params['line']

    if regexp == '':
        module.warn(
            "The regular expression is an empty string, which will match every line in the file. "
            "This may have unintended consequences, such as replacing the last line in the file rather than appending. "
            "If this is desired, use '^' to match every line in the file and avoid this warning.")

    b_path = to_bytes(path, errors='surrogate_or_strict')
    if os.path.isdir(b_path):
        module.fail_json(rc=256, msg='Path %s is a directory !' % path)

    if params['state'] == 'present':
        if backrefs and regexp is None:
            module.fail_json(msg='regexp is required with backrefs=true')

        if line is None:
            module.fail_json(msg='line is required with state=present')

        # Deal with the insertafter default value manually, to avoid errors
        # because of the mutually_exclusive mechanism.
        ins_bef, ins_aft = params['insertbefore'], params['insertafter']
        if ins_bef is None and ins_aft is None:
            ins_aft = 'EOF'

        present(module, path, params['regexp'], line,
                ins_aft, ins_bef, create, backup, backrefs, firstmatch)
    else:
        if regexp is None and line is None:
            module.fail_json(msg='one of line or regexp is required with state=absent')

        absent(module, path, params['regexp'], params.get('line', None), backup)


if __name__ == '__main__':
    main()
