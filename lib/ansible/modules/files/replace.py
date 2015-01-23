#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2013, Evan Kaufman <evan@digitalflophouse.com
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

import re
import os
import tempfile

DOCUMENTATION = """
---
module: replace
author: Evan Kaufman
extends_documentation_fragment: files
short_description: Replace all instances of a particular string in a
                   file using a back-referenced regular expression.
description:
  - This module will replace all instances of a pattern within a file.
  - It is up to the user to maintain idempotence by ensuring that the
    same pattern would never match any replacements made.
version_added: "1.6"
options:
  dest:
    required: true
    aliases: [ name, destfile ]
    description:
      - The file to modify.
  regexp:
    required: true
    description:
      - The regular expression to look for in the contents of the file.
        Uses Python regular expressions; see
        U(http://docs.python.org/2/library/re.html).
        Uses multiline mode, which means C(^) and C($) match the beginning
        and end respectively of I(each line) of the file.
  replace:
    required: false
    description:
      - The string to replace regexp matches. May contain backreferences
        that will get expanded with the regexp capture groups if the regexp
        matches. If not set, matches are removed entirely.
  backup:
    required: false
    default: "no"
    choices: [ "yes", "no" ]
    description:
      - Create a backup file including the timestamp information so you can
        get the original file back if you somehow clobbered it incorrectly.
  validate:
    required: false
    description:
      - validation to run before copying into place
    required: false
    default: None
  others:
    description:
      - All arguments accepted by the M(file) module also work here.
    required: false
"""

EXAMPLES = r"""
- replace: dest=/etc/hosts regexp='(\s+)old\.host\.name(\s+.*)?$' replace='\1new.host.name\2' backup=yes

- replace: dest=/home/jdoe/.ssh/known_hosts regexp='^old\.host\.name[^\n]*\n' owner=jdoe group=jdoe mode=644

- replace: dest=/etc/apache/ports regexp='^(NameVirtualHost|Listen)\s+80\s*$' replace='\1 127.0.0.1:8080' validate='/usr/sbin/apache2ctl -f %s -t'
"""

def write_changes(module,contents,dest):

    tmpfd, tmpfile = tempfile.mkstemp()
    f = os.fdopen(tmpfd,'wb')
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
                                 'rc:%s error:%s' % (rc,err))
    if valid:
        module.atomic_move(tmpfile, dest)

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
            dest=dict(required=True, aliases=['name', 'destfile']),
            regexp=dict(required=True),
            replace=dict(default='', type='str'),
            backup=dict(default=False, type='bool'),
            validate=dict(default=None, type='str'),
        ),
        add_file_common_args=True,
        supports_check_mode=True
    )

    params = module.params
    dest = os.path.expanduser(params['dest'])

    if os.path.isdir(dest):
        module.fail_json(rc=256, msg='Destination %s is a directory !' % dest)

    if not os.path.exists(dest):
        module.fail_json(rc=257, msg='Destination %s does not exist !' % dest)
    else:
        f = open(dest, 'rb')
        contents = f.read()
        f.close()

    mre = re.compile(params['regexp'], re.MULTILINE)
    result = re.subn(mre, params['replace'], contents, 0)

    if result[1] > 0 and contents != result[0]:
        msg = '%s replacements made' % result[1]
        changed = True
    else:
        msg = ''
        changed = False

    if changed and not module.check_mode:
        if params['backup'] and os.path.exists(dest):
            module.backup_local(dest)
        if params['follow'] and os.path.islink(dest):
            dest = os.path.realpath(dest)
        write_changes(module, result[0], dest)

    msg, changed = check_file_attrs(module, changed, msg)
    module.exit_json(changed=changed, msg=msg)

# this is magic, see lib/ansible/module_common.py
#<<INCLUDE_ANSIBLE_MODULE_COMMON>>

main()
