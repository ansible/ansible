#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2012, Jan-Piet Mens <jpmens () gmail.com>
# Copyright: (c) 2015, Ales Nosek <anosek.nosek () gmail.com>
# Copyright: (c) 2017, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: ini_file
short_description: Tweak settings in INI files
extends_documentation_fragment: files
description:
     - Manage (add, remove, change) individual settings in an INI-style file without having
       to manage the file as a whole with, say, M(template) or M(assemble).
     - Adds missing sections if they don't exist.
     - Before Ansible 2.0, comments are discarded when the source file is read, and therefore will not show up in the destination file.
     - Since Ansible 2.3, this module adds missing ending newlines to files to keep in line with the POSIX standard, even when
       no other modifications need to be applied.
version_added: "0.9"
options:
  path:
    description:
      - Path to the INI-style file; this file is created if required.
      - Before Ansible 2.3 this option was only usable as I(dest).
    type: path
    required: true
    aliases: [ dest ]
  section:
    description:
      - Section name in INI file. This is added if C(state=present) automatically when
        a single value is being set.
      - If left empty or set to C(null), the I(option) will be placed before the first I(section).
      - Using C(null) is also required if the config format does not support sections.
    type: str
    required: true
  option:
    description:
      - If set (required for changing a I(value)), this is the name of the option.
      - May be omitted if adding/removing a whole I(section).
    type: str
  value:
    description:
      - The string value to be associated with an I(option).
      - May be omitted when removing an I(option).
    type: str
  backup:
    description:
      - Create a backup file including the timestamp information so you can get
        the original file back if you somehow clobbered it incorrectly.
    type: bool
    default: no
  state:
    description:
      - If set to C(absent) the option or section will be removed if present instead of created.
    type: str
    choices: [ absent, present ]
    default: present
  no_extra_spaces:
    description:
      - Do not insert spaces before and after '=' symbol.
    type: bool
    default: no
    version_added: "2.1"
  create:
    description:
      - If set to C(no), the module will fail if the file does not already exist.
      - By default it will create the file if it is missing.
    type: bool
    default: yes
    version_added: "2.2"
  allow_no_value:
    description:
      - Allow option without value and without '=' symbol.
    type: bool
    default: no
    version_added: "2.6"
notes:
   - While it is possible to add an I(option) without specifying a I(value), this makes no sense.
   - As of Ansible 2.3, the I(dest) option has been changed to I(path) as default, but I(dest) still works as well.
author:
    - Jan-Piet Mens (@jpmens)
    - Ales Nosek (@noseka1)
'''

EXAMPLES = r'''
# Before Ansible 2.3, option 'dest' was used instead of 'path'
- name: Ensure "fav=lemonade is in section "[drinks]" in specified file
  ini_file:
    path: /etc/conf
    section: drinks
    option: fav
    value: lemonade
    mode: '0600'
    backup: yes

- name: Ensure "temperature=cold is in section "[drinks]" in specified file
  ini_file:
    path: /etc/anotherconf
    section: drinks
    option: temperature
    value: cold
    backup: yes
'''

import os
import re
import tempfile
import traceback

from ansible.module_utils.basic import AnsibleModule


def match_opt(option, line):
    option = re.escape(option)
    return re.match('( |\t)*%s( |\t)*(=|$)' % option, line) \
        or re.match('#( |\t)*%s( |\t)*(=|$)' % option, line) \
        or re.match(';( |\t)*%s( |\t)*(=|$)' % option, line)


def match_active_opt(option, line):
    option = re.escape(option)
    return re.match('( |\t)*%s( |\t)*(=|$)' % option, line)


def do_ini(module, filename, section=None, option=None, value=None,
           state='present', backup=False, no_extra_spaces=False, create=True,
           allow_no_value=False):

    diff = dict(
        before='',
        after='',
        before_header='%s (content)' % filename,
        after_header='%s (content)' % filename,
    )

    if not os.path.exists(filename):
        if not create:
            module.fail_json(rc=257, msg='Destination %s does not exist !' % filename)
        destpath = os.path.dirname(filename)
        if not os.path.exists(destpath) and not module.check_mode:
            os.makedirs(destpath)
        ini_lines = []
    else:
        ini_file = open(filename, 'r')
        try:
            ini_lines = ini_file.readlines()
        finally:
            ini_file.close()

    if module._diff:
        diff['before'] = ''.join(ini_lines)

    changed = False

    # ini file could be empty
    if not ini_lines:
        ini_lines.append('\n')

    # last line of file may not contain a trailing newline
    if ini_lines[-1] == "" or ini_lines[-1][-1] != '\n':
        ini_lines[-1] += '\n'
        changed = True

    # append fake section lines to simplify the logic
    # At top:
    # Fake random section to do not match any other in the file
    # Using commit hash as fake section name
    fake_section_name = "ad01e11446efb704fcdbdb21f2c43757423d91c5"

    # Insert it at the beginning
    ini_lines.insert(0, '[%s]' % fake_section_name)

    # At botton:
    ini_lines.append('[')

    # If no section is defined, fake section is used
    if not section:
        section = fake_section_name

    within_section = not section
    section_start = 0
    msg = 'OK'
    if no_extra_spaces:
        assignment_format = '%s=%s\n'
    else:
        assignment_format = '%s = %s\n'

    for index, line in enumerate(ini_lines):
        if line.startswith('[%s]' % section):
            within_section = True
            section_start = index
        elif line.startswith('['):
            if within_section:
                if state == 'present':
                    # insert missing option line at the end of the section
                    for i in range(index, 0, -1):
                        # search backwards for previous non-blank or non-comment line
                        if not re.match(r'^[ \t]*([#;].*)?$', ini_lines[i - 1]):
                            if not value and allow_no_value:
                                ini_lines.insert(i, '%s\n' % option)
                            else:
                                ini_lines.insert(i, assignment_format % (option, value))
                            msg = 'option added'
                            changed = True
                            break
                elif state == 'absent' and not option:
                    # remove the entire section
                    del ini_lines[section_start:index]
                    msg = 'section removed'
                    changed = True
                break
        else:
            if within_section and option:
                if state == 'present':
                    # change the existing option line
                    if match_opt(option, line):
                        if not value and allow_no_value:
                            newline = '%s\n' % option
                        else:
                            newline = assignment_format % (option, value)
                        option_changed = ini_lines[index] != newline
                        changed = changed or option_changed
                        if option_changed:
                            msg = 'option changed'
                        ini_lines[index] = newline
                        if option_changed:
                            # remove all possible option occurrences from the rest of the section
                            index = index + 1
                            while index < len(ini_lines):
                                line = ini_lines[index]
                                if line.startswith('['):
                                    break
                                if match_active_opt(option, line):
                                    del ini_lines[index]
                                else:
                                    index = index + 1
                        break
                elif state == 'absent':
                    # delete the existing line
                    if match_active_opt(option, line):
                        del ini_lines[index]
                        changed = True
                        msg = 'option changed'
                        break

    # remove the fake section line
    del ini_lines[0]
    del ini_lines[-1:]

    if not within_section and option and state == 'present':
        ini_lines.append('[%s]\n' % section)
        if not value and allow_no_value:
            ini_lines.append('%s\n' % option)
        else:
            ini_lines.append(assignment_format % (option, value))
        changed = True
        msg = 'section and option added'

    if module._diff:
        diff['after'] = ''.join(ini_lines)

    backup_file = None
    if changed and not module.check_mode:
        if backup:
            backup_file = module.backup_local(filename)

        try:
            tmpfd, tmpfile = tempfile.mkstemp(dir=module.tmpdir)
            f = os.fdopen(tmpfd, 'w')
            f.writelines(ini_lines)
            f.close()
        except IOError:
            module.fail_json(msg="Unable to create temporary file %s", traceback=traceback.format_exc())

        try:
            module.atomic_move(tmpfile, filename)
        except IOError:
            module.ansible.fail_json(msg='Unable to move temporary \
                                   file %s to %s, IOError' % (tmpfile, filename), traceback=traceback.format_exc())

    return (changed, backup_file, diff, msg)


def main():

    module = AnsibleModule(
        argument_spec=dict(
            path=dict(type='path', required=True, aliases=['dest']),
            section=dict(type='str', required=True),
            option=dict(type='str'),
            value=dict(type='str'),
            backup=dict(type='bool', default=False),
            state=dict(type='str', default='present', choices=['absent', 'present']),
            no_extra_spaces=dict(type='bool', default=False),
            allow_no_value=dict(type='bool', default=False),
            create=dict(type='bool', default=True)
        ),
        add_file_common_args=True,
        supports_check_mode=True,
    )

    path = module.params['path']
    section = module.params['section']
    option = module.params['option']
    value = module.params['value']
    state = module.params['state']
    backup = module.params['backup']
    no_extra_spaces = module.params['no_extra_spaces']
    allow_no_value = module.params['allow_no_value']
    create = module.params['create']

    (changed, backup_file, diff, msg) = do_ini(module, path, section, option, value, state, backup, no_extra_spaces, create, allow_no_value)

    if not module.check_mode and os.path.exists(path):
        file_args = module.load_file_common_arguments(module.params)
        changed = module.set_fs_attributes_if_different(file_args, changed)

    results = dict(
        changed=changed,
        diff=diff,
        msg=msg,
        path=path,
    )
    if backup_file is not None:
        results['backup_file'] = backup_file

    # Mission complete
    module.exit_json(**results)


if __name__ == '__main__':
    main()
