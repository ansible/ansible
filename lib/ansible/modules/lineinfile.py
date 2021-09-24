#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2012, Daniel Hokka Zakrisson <daniel@hozac.com>
# Copyright: (c) 2014, Ahti Kitsik <ak@ahtik.com>
# Copyright: (c) 2017, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = r'''
---
module: lineinfile
short_description: Manage lines in text files
description:
  - This module ensures a particular line is in a file, or replace an
    existing line using a back-referenced regular expression.
  - This is primarily useful when you want to change a single line in a file only.
  - See the M(ansible.builtin.replace) module if you want to change multiple, similar lines
    or check M(ansible.builtin.blockinfile) if you want to insert/update/remove a block of lines in a file.
    For other cases, see the M(ansible.builtin.copy) or M(ansible.builtin.template) modules.
version_added: "0.7"
options:
  path:
    description:
      - The file to modify.
      - Before Ansible 2.3 this option was only usable as I(dest), I(destfile) and I(name).
    type: path
    required: true
    aliases: [ dest, destfile, name ]
  regexp:
    description:
      - The regular expression to look for in every line of the file.
      - For C(state=present), the pattern to replace if found. Only the last line found will be replaced.
      - For C(state=absent), the pattern of the line(s) to remove.
      - If the regular expression is not matched, the line will be
        added to the file in keeping with C(insertbefore) or C(insertafter)
        settings.
      - When modifying a line the regexp should typically match both the initial state of
        the line as well as its state after replacement by C(line) to ensure idempotence.
      - Uses Python regular expressions. See U(https://docs.python.org/3/library/re.html).
    type: str
    aliases: [ regex ]
    version_added: '1.7'
  search_string:
    description:
      - The literal string to look for in every line of the file. This does not have to match the entire line.
      - For C(state=present), the line to replace if the string is found in the file. Only the last line found will be replaced.
      - For C(state=absent), the line(s) to remove if the string is in the line.
      - If the literal expression is not matched, the line will be
        added to the file in keeping with C(insertbefore) or C(insertafter)
        settings.
      - Mutually exclusive with C(backrefs) and C(regexp).
    type: str
    version_added: '2.11'
  state:
    description:
      - Whether the line should be there or not.
    type: str
    choices: [ absent, present ]
    default: present
  line:
    description:
      - The line to insert/replace into the file.
      - Required for C(state=present).
      - If C(backrefs) is set, may contain backreferences that will get
        expanded with the C(regexp) capture groups if the regexp matches.
    type: str
    aliases: [ value ]
  backrefs:
    description:
      - Used with C(state=present).
      - If set, C(line) can contain backreferences (both positional and named)
        that will get populated if the C(regexp) matches.
      - This parameter changes the operation of the module slightly;
        C(insertbefore) and C(insertafter) will be ignored, and if the C(regexp)
        does not match anywhere in the file, the file will be left unchanged.
      - If the C(regexp) does match, the last matching line will be replaced by
        the expanded line parameter.
      - Mutually exclusive with C(search_string).
    type: bool
    default: no
    version_added: "1.1"
  insertafter:
    description:
      - Used with C(state=present).
      - If specified, the line will be inserted after the last match of specified regular expression.
      - If the first match is required, use(firstmatch=yes).
      - A special value is available; C(EOF) for inserting the line at the end of the file.
      - If specified regular expression has no matches, EOF will be used instead.
      - If C(insertbefore) is set, default value C(EOF) will be ignored.
      - If regular expressions are passed to both C(regexp) and C(insertafter), C(insertafter) is only honored if no match for C(regexp) is found.
      - May not be used with C(backrefs) or C(insertbefore).
    type: str
    choices: [ EOF, '*regex*' ]
    default: EOF
  insertbefore:
    description:
      - Used with C(state=present).
      - If specified, the line will be inserted before the last match of specified regular expression.
      - If the first match is required, use C(firstmatch=yes).
      - A value is available; C(BOF) for inserting the line at the beginning of the file.
      - If specified regular expression has no matches, the line will be inserted at the end of the file.
      - If regular expressions are passed to both C(regexp) and C(insertbefore), C(insertbefore) is only honored if no match for C(regexp) is found.
      - May not be used with C(backrefs) or C(insertafter).
    type: str
    choices: [ BOF, '*regex*' ]
    version_added: "1.1"
  create:
    description:
      - Used with C(state=present).
      - If specified, the file will be created if it does not already exist.
      - By default it will fail if the file is missing.
    type: bool
    default: no
  backup:
    description:
      - Create a backup file including the timestamp information so you can
        get the original file back if you somehow clobbered it incorrectly.
    type: bool
    default: no
  firstmatch:
    description:
      - Used with C(insertafter) or C(insertbefore).
      - If set, C(insertafter) and C(insertbefore) will work with the first line that matches the given regular expression.
    type: bool
    default: no
    version_added: "2.5"
  others:
    description:
      - All arguments accepted by the M(ansible.builtin.file) module also work here.
    type: str
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
    platform:
        platforms: posix
    safe_file_operations:
        support: full
    vault:
        support: none
notes:
  - As of Ansible 2.3, the I(dest) option has been changed to I(path) as default, but I(dest) still works as well.
seealso:
- module: ansible.builtin.blockinfile
- module: ansible.builtin.copy
- module: ansible.builtin.file
- module: ansible.builtin.replace
- module: ansible.builtin.template
- module: community.windows.win_lineinfile
author:
    - Daniel Hokka Zakrissoni (@dhozac)
    - Ahti Kitsik (@ahtik)
    - Jose Angel Munoz (@imjoseangel)
'''

EXAMPLES = r'''
# NOTE: Before 2.3, option 'dest', 'destfile' or 'name' was used instead of 'path'
- name: Ensure SELinux is set to enforcing mode
  ansible.builtin.lineinfile:
    path: /etc/selinux/config
    regexp: '^SELINUX='
    line: SELINUX=enforcing

- name: Make sure group wheel is not in the sudoers configuration
  ansible.builtin.lineinfile:
    path: /etc/sudoers
    state: absent
    regexp: '^%wheel'

- name: Replace a localhost entry with our own
  ansible.builtin.lineinfile:
    path: /etc/hosts
    regexp: '^127\.0\.0\.1'
    line: 127.0.0.1 localhost
    owner: root
    group: root
    mode: '0644'

- name: Replace a localhost entry searching for a literal string to avoid escaping
  lineinfile:
    path: /etc/hosts
    search_string: '127.0.0.1'
    line: 127.0.0.1 localhost
    owner: root
    group: root
    mode: '0644'

- name: Ensure the default Apache port is 8080
  ansible.builtin.lineinfile:
    path: /etc/httpd/conf/httpd.conf
    regexp: '^Listen '
    insertafter: '^#Listen '
    line: Listen 8080

- name: Ensure php extension matches new pattern
  lineinfile:
    path: /etc/httpd/conf/httpd.conf
    search_string: '<FilesMatch ".php[45]?$">'
    insertafter: '^\t<Location \/>\n'
    line: '        <FilesMatch ".php[34]?$">'

- name: Ensure we have our own comment added to /etc/services
  ansible.builtin.lineinfile:
    path: /etc/services
    regexp: '^# port for http'
    insertbefore: '^www.*80/tcp'
    line: '# port for http by default'

- name: Add a line to a file if the file does not exist, without passing regexp
  ansible.builtin.lineinfile:
    path: /tmp/testfile
    line: 192.168.1.99 foo.lab.net foo
    create: yes

# NOTE: Yaml requires escaping backslashes in double quotes but not in single quotes
- name: Ensure the JBoss memory settings are exactly as needed
  ansible.builtin.lineinfile:
    path: /opt/jboss-as/bin/standalone.conf
    regexp: '^(.*)Xms(\d+)m(.*)$'
    line: '\1Xms${xms}m\3'
    backrefs: yes

# NOTE: Fully quoted because of the ': ' on the line. See the Gotchas in the YAML docs.
- name: Validate the sudoers file before saving
  ansible.builtin.lineinfile:
    path: /etc/sudoers
    state: present
    regexp: '^%ADMIN ALL='
    line: '%ADMIN ALL=(ALL) NOPASSWD: ALL'
    validate: /usr/sbin/visudo -cf %s

# See https://docs.python.org/3/library/re.html for further details on syntax
- name: Use backrefs with alternative group syntax to avoid conflicts with variable values
  ansible.builtin.lineinfile:
    path: /tmp/config
    regexp: ^(host=).*
    line: \g<1>{{ hostname }}
    backrefs: yes
'''

RETURN = r'''#'''

import os
import re
import tempfile

# import module snippets
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_bytes, to_native, to_text


def write_changes(module, b_lines, dest):

    tmpfd, tmpfile = tempfile.mkstemp(dir=module.tmpdir)
    with os.fdopen(tmpfd, 'wb') as f:
        f.writelines(b_lines)

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


def present(module, dest, regexp, search_string, line, insertafter, insertbefore, create,
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
        if b_destpath and not os.path.exists(b_destpath) and not module.check_mode:
            try:
                os.makedirs(b_destpath)
            except Exception as e:
                module.fail_json(msg='Error creating %s (%s)' % (to_text(b_destpath), to_text(e)))

        b_lines = []
    else:
        with open(b_dest, 'rb') as f:
            b_lines = f.readlines()

    if module._diff:
        diff['before'] = to_native(b''.join(b_lines))

    if regexp is not None:
        bre_m = re.compile(to_bytes(regexp, errors='surrogate_or_strict'))

    if insertafter not in (None, 'BOF', 'EOF'):
        bre_ins = re.compile(to_bytes(insertafter, errors='surrogate_or_strict'))
    elif insertbefore not in (None, 'BOF'):
        bre_ins = re.compile(to_bytes(insertbefore, errors='surrogate_or_strict'))
    else:
        bre_ins = None

    # index[0] is the line num where regexp has been found
    # index[1] is the line num where insertafter/insertbefore has been found
    index = [-1, -1]
    match = None
    exact_line_match = False
    b_line = to_bytes(line, errors='surrogate_or_strict')

    # The module's doc says
    # "If regular expressions are passed to both regexp and
    # insertafter, insertafter is only honored if no match for regexp is found."
    # Therefore:
    # 1. regexp or search_string was found -> ignore insertafter, replace the founded line
    # 2. regexp or search_string was not found -> insert the line after 'insertafter' or 'insertbefore' line

    # Given the above:
    # 1. First check that there is no match for regexp:
    if regexp is not None:
        for lineno, b_cur_line in enumerate(b_lines):
            match_found = bre_m.search(b_cur_line)
            if match_found:
                index[0] = lineno
                match = match_found
                if firstmatch:
                    break

    # 2. Second check that there is no match for search_string:
    if search_string is not None:
        for lineno, b_cur_line in enumerate(b_lines):
            match_found = to_bytes(search_string, errors='surrogate_or_strict') in b_cur_line
            if match_found:
                index[0] = lineno
                match = match_found
                if firstmatch:
                    break

    # 3. When no match found on the previous step,
    # parse for searching insertafter/insertbefore:
    if not match:
        for lineno, b_cur_line in enumerate(b_lines):
            if b_line == b_cur_line.rstrip(b'\r\n'):
                index[0] = lineno
                exact_line_match = True

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
    # Exact line or Regexp matched a line in the file
    if index[0] != -1:
        if backrefs and match:
            b_new_line = match.expand(b_line)
        else:
            # Don't do backref expansion if not asked.
            b_new_line = b_line

        if not b_new_line.endswith(b_linesep):
            b_new_line += b_linesep

        # If no regexp or search_string was given and no line match is found anywhere in the file,
        # insert the line appropriately if using insertbefore or insertafter
        if (regexp, search_string, match) == (None, None, None) and not exact_line_match:

            # Insert lines
            if insertafter and insertafter != 'EOF':
                # Ensure there is a line separator after the found string
                # at the end of the file.
                if b_lines and not b_lines[-1][-1:] in (b'\n', b'\r'):
                    b_lines[-1] = b_lines[-1] + b_linesep

                # If the line to insert after is at the end of the file
                # use the appropriate index value.
                if len(b_lines) == index[1]:
                    if b_lines[index[1] - 1].rstrip(b'\r\n') != b_line:
                        b_lines.append(b_line + b_linesep)
                        msg = 'line added'
                        changed = True
                elif b_lines[index[1]].rstrip(b'\r\n') != b_line:
                    b_lines.insert(index[1], b_line + b_linesep)
                    msg = 'line added'
                    changed = True

            elif insertbefore and insertbefore != 'BOF':
                # If the line to insert before is at the beginning of the file
                # use the appropriate index value.
                if index[1] <= 0:
                    if b_lines[index[1]].rstrip(b'\r\n') != b_line:
                        b_lines.insert(index[1], b_line + b_linesep)
                        msg = 'line added'
                        changed = True

                elif b_lines[index[1] - 1].rstrip(b'\r\n') != b_line:
                    b_lines.insert(index[1], b_line + b_linesep)
                    msg = 'line added'
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
        if b_lines and not b_lines[-1][-1:] in (b'\n', b'\r'):
            b_lines.append(b_linesep)

        b_lines.append(b_line + b_linesep)
        msg = 'line added'
        changed = True

    elif insertafter and index[1] != -1:

        # Don't insert the line if it already matches at the index.
        # If the line to insert after is at the end of the file use the appropriate index value.
        if len(b_lines) == index[1]:
            if b_lines[index[1] - 1].rstrip(b'\r\n') != b_line:
                b_lines.append(b_line + b_linesep)
                msg = 'line added'
                changed = True
        elif b_line != b_lines[index[1]].rstrip(b'\n\r'):
            b_lines.insert(index[1], b_line + b_linesep)
            msg = 'line added'
            changed = True

    # insert matched, but not the regexp or search_string
    else:
        b_lines.insert(index[1], b_line + b_linesep)
        msg = 'line added'
        changed = True

    if module._diff:
        diff['after'] = to_native(b''.join(b_lines))

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


def absent(module, dest, regexp, search_string, line, backup):

    b_dest = to_bytes(dest, errors='surrogate_or_strict')
    if not os.path.exists(b_dest):
        module.exit_json(changed=False, msg="file not present")

    msg = ''
    diff = {'before': '',
            'after': '',
            'before_header': '%s (content)' % dest,
            'after_header': '%s (content)' % dest}

    with open(b_dest, 'rb') as f:
        b_lines = f.readlines()

    if module._diff:
        diff['before'] = to_native(b''.join(b_lines))

    if regexp is not None:
        bre_c = re.compile(to_bytes(regexp, errors='surrogate_or_strict'))
    found = []

    b_line = to_bytes(line, errors='surrogate_or_strict')

    def matcher(b_cur_line):
        if regexp is not None:
            match_found = bre_c.search(b_cur_line)
        elif search_string is not None:
            match_found = to_bytes(search_string, errors='surrogate_or_strict') in b_cur_line
        else:
            match_found = b_line == b_cur_line.rstrip(b'\r\n')
        if match_found:
            found.append(b_cur_line)
        return not match_found

    b_lines = [l for l in b_lines if matcher(l)]
    changed = len(found) > 0

    if module._diff:
        diff['after'] = to_native(b''.join(b_lines))

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
            regexp=dict(type='str', aliases=['regex']),
            search_string=dict(type='str'),
            line=dict(type='str', aliases=['value']),
            insertafter=dict(type='str'),
            insertbefore=dict(type='str'),
            backrefs=dict(type='bool', default=False),
            create=dict(type='bool', default=False),
            backup=dict(type='bool', default=False),
            firstmatch=dict(type='bool', default=False),
            validate=dict(type='str'),
        ),
        mutually_exclusive=[
            ['insertbefore', 'insertafter'], ['regexp', 'search_string'], ['backrefs', 'search_string']],
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
    search_string = params['search_string']
    line = params['line']

    if '' in [regexp, search_string]:
        msg = ("The %s is an empty string, which will match every line in the file. "
               "This may have unintended consequences, such as replacing the last line in the file rather than appending.")
        param_name = 'search string'
        if regexp == '':
            param_name = 'regular expression'
            msg += " If this is desired, use '^' to match every line in the file and avoid this warning."
        module.warn(msg % param_name)

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

        present(module, path, regexp, search_string, line,
                ins_aft, ins_bef, create, backup, backrefs, firstmatch)
    else:
        if (regexp, search_string, line) == (None, None, None):
            module.fail_json(msg='one of line, search_string, or regexp is required with state=absent')

        absent(module, path, regexp, search_string, line, backup)


if __name__ == '__main__':
    main()
