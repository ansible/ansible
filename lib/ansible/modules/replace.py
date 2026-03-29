# -*- coding: utf-8 -*-

# Copyright: (c) 2013, Evan Kaufman <evan@digitalflophouse.com
# Copyright: (c) 2017, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations


DOCUMENTATION = r"""
---
module: replace
author: Evan Kaufman (@EvanK)
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
short_description: Replace all instances of a particular string in a
                   file using a back-referenced regular expression
description:
  - This module will replace all instances of a pattern within a file.
  - It is up to the user to maintain idempotence by ensuring that the
    same pattern would never match any replacements made.
version_added: "1.6"
options:
  path:
    description:
      - The file to modify.
      - Before Ansible 2.3 this option was only usable as O(dest), O(destfile) and O(name).
    type: path
    required: true
    aliases: [ dest, destfile, name ]
  regexp:
    description:
      - The regular expression to look for in the contents of the file.
      - Uses Python regular expressions; see
        U(https://docs.python.org/3/library/re.html).
      - Uses MULTILINE mode, which means V(^) and V($) match the beginning
        and end of the file, as well as the beginning and end respectively
        of I(each line) of the file.
      - Does not use DOTALL, which means the V(.) special character matches
        any character I(except newlines). A common mistake is to assume that
        a negated character set like V([^#]) will also not match newlines.
      - In order to exclude newlines, they must be added to the set like V([^#\\n]).
      - Note that, as of Ansible 2.0, short form tasks should have any escape
        sequences backslash-escaped in order to prevent them being parsed
        as string literal escapes. See the examples.
    type: str
    required: true
  replace:
    description:
      - The string to replace regexp matches.
      - May contain backreferences that will get expanded with the regexp capture groups if the regexp matches.
      - If not set, matches are removed entirely.
      - Backreferences can be used ambiguously like V(\\1), or explicitly like V(\\g<1>).
    type: str
    default: ''
  after:
    description:
      - If specified, only content after this match will be replaced/removed.
      - Can be used in combination with O(before).
      - Uses Python regular expressions; see
        U(https://docs.python.org/3/library/re.html).
      - Uses DOTALL, which means the V(.) special character I(can match newlines).
      - Does not use MULTILINE, so V(^) and V($) will only match the beginning and end of the file.
    type: str
    version_added: "2.4"
  before:
    description:
      - If specified, only content before this match will be replaced/removed.
      - Can be used in combination with O(after).
      - Uses Python regular expressions; see
        U(https://docs.python.org/3/library/re.html).
      - Uses DOTALL, which means the V(.) special character I(can match newlines).
      - Does not use MULTILINE, so V(^) and V($) will only match the beginning and end of the file.
    type: str
    version_added: "2.4"
  backup:
    description:
      - Create a backup file including the timestamp information so you can
        get the original file back if you somehow clobbered it incorrectly.
    type: bool
    default: no
  encoding:
    description:
      - The character encoding for reading and writing the file.
    type: str
    default: utf-8
    version_added: "2.4"
notes:
  - As of Ansible 2.3, the O(dest) option has been changed to O(path) as default, but O(dest) still works as well.
  - As of Ansible 2.7.10, the combined use of O(before) and O(after) works properly. If you were relying on the
    previous incorrect behavior, you may be need to adjust your tasks.
    See U(https://github.com/ansible/ansible/issues/31354) for details.
  - Option O(ignore:follow) has been removed in Ansible 2.5, because this module modifies the contents of the file
    so O(ignore:follow=no) does not make sense.
"""

EXAMPLES = r"""
- name: Replace old hostname with new hostname (requires Ansible >= 2.4)
  ansible.builtin.replace:
    path: /etc/hosts
    regexp: '(\s+)old\.host\.name(\s+.*)?$'
    replace: '\1new.host.name\2'

- name: Replace after the expression till the end of the file (requires Ansible >= 2.4)
  ansible.builtin.replace:
    path: /etc/apache2/sites-available/default.conf
    after: 'NameVirtualHost [*]'
    regexp: '^(.+)$'
    replace: '# \1'

- name: Replace before the expression from the beginning of the file (requires Ansible >= 2.4)
  ansible.builtin.replace:
    path: /etc/apache2/sites-available/default.conf
    before: '# live site config'
    regexp: '^(.+)$'
    replace: '# \1'

# Prior to Ansible 2.7.10, using before and after in combination did the opposite of what was intended.
# see https://github.com/ansible/ansible/issues/31354 for details.
# Note (?m) which turns on MULTILINE mode so ^ matches any line's beginning
- name: Replace between the expressions (requires Ansible >= 2.4)
  ansible.builtin.replace:
    path: /etc/hosts
    after: '(?m)^<VirtualHost [*]>'
    before: '</VirtualHost>'
    regexp: '^(.+)$'
    replace: '# \1'

- name: Supports common file attributes
  ansible.builtin.replace:
    path: /home/jdoe/.ssh/known_hosts
    regexp: '^old\.host\.name[^\n]*\n'
    owner: jdoe
    group: jdoe
    mode: '0644'

- name: Supports a validate command
  ansible.builtin.replace:
    path: /etc/apache/ports
    regexp: '^(NameVirtualHost|Listen)\s+80\s*$'
    replace: '\1 127.0.0.1:8080'
    validate: '/usr/sbin/apache2ctl -f %s -t'

- name: Short form task (in ansible 2+) necessitates backslash-escaped sequences
  ansible.builtin.replace: path=/etc/hosts regexp='\\b(localhost)(\\d*)\\b' replace='\\1\\2.localdomain\\2 \\1\\2'

- name: Long form task does not
  ansible.builtin.replace:
    path: /etc/hosts
    regexp: '\b(localhost)(\d*)\b'
    replace: '\1\2.localdomain\2 \1\2'

- name: Explicitly specifying positional matched groups in replacement
  ansible.builtin.replace:
    path: /etc/ssh/sshd_config
    regexp: '^(ListenAddress[ ]+)[^\n]+$'
    replace: '\g<1>0.0.0.0'

- name: Explicitly specifying named matched groups
  ansible.builtin.replace:
    path: /etc/ssh/sshd_config
    regexp: '^(?P<dctv>ListenAddress[ ]+)(?P<host>[^\n]+)$'
    replace: '#\g<dctv>\g<host>\n\g<dctv>0.0.0.0'
"""

RETURN = r"""#"""

import os
import re
import tempfile

from ansible.module_utils.common.text.converters import to_text
from ansible.module_utils.basic import AnsibleModule


def write_changes(module, contents, path, encoding='utf-8'):

    tmpfd, tmpfile = tempfile.mkstemp(dir=module.tmpdir)
    with os.fdopen(tmpfd, 'w', encoding=encoding) as f:
        f.write(contents)

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
            path=dict(type='path', required=True, aliases=['dest', 'destfile', 'name']),
            regexp=dict(type='str', required=True),
            replace=dict(type='str', default=''),
            after=dict(type='str'),
            before=dict(type='str'),
            backup=dict(type='bool', default=False),
            validate=dict(type='str'),
            encoding=dict(type='str', default='utf-8'),
        ),
        add_file_common_args=True,
        supports_check_mode=True,
    )

    params = module.params
    path = params['path']
    encoding = params['encoding']
    res_args = dict(rc=0)
    contents = None

    params['after'] = to_text(params['after'], errors='surrogate_or_strict', nonstring='passthru')
    params['before'] = to_text(params['before'], errors='surrogate_or_strict', nonstring='passthru')
    params['regexp'] = to_text(params['regexp'], errors='surrogate_or_strict', nonstring='passthru')
    params['replace'] = to_text(params['replace'], errors='surrogate_or_strict', nonstring='passthru')

    if os.path.isdir(path):
        module.fail_json(rc=256, msg='Path %s is a directory !' % path)

    if not os.path.exists(path):
        module.fail_json(rc=257, msg='Path %s does not exist !' % path)
    else:
        try:
            with open(path, 'r', encoding=encoding) as f:
                contents = f.read()
        except OSError as ex:
            raise Exception(f"Unable to read the contents of {path!r}.") from ex

    pattern = u''
    if params['after'] and params['before']:
        pattern = u'%s(?P<subsection>.*?)%s' % (params['after'], params['before'])
    elif params['after']:
        pattern = u'%s(?P<subsection>.*)' % params['after']
    elif params['before']:
        pattern = u'(?P<subsection>.*)%s' % params['before']

    if pattern:
        section_re = re.compile(pattern, re.DOTALL)
        match = re.search(section_re, contents)
        if match:
            section = match.group('subsection')
            indices = [match.start('subsection'), match.end('subsection')]
        else:
            res_args['msg'] = 'Pattern for before/after params did not match the given file: %s' % pattern
            res_args['changed'] = False
            module.exit_json(**res_args)
    else:
        section = contents

    mre = re.compile(params['regexp'], re.MULTILINE)
    try:
        result = re.subn(mre, params['replace'], section, 0)
    except re.error as e:
        module.fail_json(msg="Unable to process replace due to error: %s" % to_text(e))

    if result[1] > 0 and section != result[0]:
        if pattern:
            result = (contents[:indices[0]] + result[0] + contents[indices[1]:], result[1])
        msg = '%s replacements made' % result[1]
        changed = True
        if module._diff:
            res_args['diff'] = {
                'before_header': path,
                'before': contents,
                'after_header': path,
                'after': result[0],
            }
    else:
        msg = ''
        changed = False

    if changed and not module.check_mode:
        if params['backup'] and os.path.exists(path):
            res_args['backup_file'] = module.backup_local(path)
        # We should always follow symlinks so that we change the real file
        path = os.path.realpath(path)
        write_changes(module, result[0], path, encoding=encoding)

    res_args['msg'], res_args['changed'] = check_file_attrs(module, changed, msg)
    module.exit_json(**res_args)


if __name__ == '__main__':
    main()
