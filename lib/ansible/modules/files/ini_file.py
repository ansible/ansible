#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2012, Jan-Piet Mens <jpmens () gmail.com>
# Copyright: (c) 2015, Ales Nosek <anosek.nosek () gmail.com>
# Copyright: (c) 2017, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type
#

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: ini_file
short_description: Tweak settings in INI files
extends_documentation_fragment: files
description:
     - Manage (add, remove, change) individual settings in an INI-style file without having
       to manage the file as a whole with, say, M(template) or M(assemble). Adds missing
       sections if they don't exist.
     - Before version 2.0, comments are discarded when the source file is read, and therefore will not show up in the destination file.
     - Since version 2.3, this module adds missing ending newlines to files to keep in line with the POSIX standard, even when
       no other modifications need to be applied.
version_added: "0.9"
options:
  path:
    description:
      - Path to the INI-style file; this file is created if required.
      - Before 2.3 this option was only usable as I(dest).
    required: true
    default: null
    aliases: ['dest']
  section:
    description:
      - Section name in INI file. This is added if C(state=present) automatically when
        a single value is being set.
      - If left empty or set to `null`, the I(option) will be placed before the first I(section).
        Using `null` is also required if the config format does not support sections.
    required: true
    default: null
  option:
    description:
      - If set (required for changing a I(value)), this is the name of the option.
      - May be omitted if adding/removing a whole I(section).
    required: false
    default: null
  value:
    description:
     - The string value to be associated with an I(option). May be omitted when removing an I(option).
    required: false
    default: null
  backup:
    description:
      - Create a backup file including the timestamp information so you can get
        the original file back if you somehow clobbered it incorrectly.
    required: false
    default: "no"
    choices: [ "yes", "no" ]
  others:
     description:
       - All arguments accepted by the M(file) module also work here
     required: false
  state:
     description:
       - If set to C(absent) the option or section will be removed if present instead of created.
     required: false
     default: "present"
     choices: [ "present", "absent" ]
  no_extra_spaces:
     description:
       - Do not insert spaces before and after '=' symbol
     required: false
     default: false
     version_added: "2.1"
  create:
     required: false
     choices: [ "yes", "no" ]
     default: "yes"
     description:
       - If set to 'no', the module will fail if the file does not already exist.
         By default it will create the file if it is missing.
     version_added: "2.2"
notes:
   - While it is possible to add an I(option) without specifying a I(value), this makes
     no sense.
   - As of Ansible 2.3, the I(dest) option has been changed to I(path) as default, but
     I(dest) still works as well.
author:
    - "Jan-Piet Mens (@jpmens)"
    - "Ales Nosek (@noseka1)"
'''

EXAMPLES = '''
# Before 2.3, option 'dest' was used instead of 'path'
- name: Ensure "fav=lemonade is in section "[drinks]" in specified file
  ini_file:
    path: /etc/conf
    section: drinks
    option: fav
    value: lemonade
    mode: 0600
    backup: yes

- ini_file:
    path: /etc/anotherconf
    section: drinks
    option: temperature
    value: cold
    backup: yes
'''

import os
import re

# import module snippets
from ansible.module_utils.basic import AnsibleModule

# ==============================================================
# match_opt

def match_opt(option, line):
    option = re.escape(option)
    return re.match(' *%s( |\t)*=' % option, line) \
      or re.match('# *%s( |\t)*=' % option, line) \
      or re.match('; *%s( |\t)*=' % option, line)

# ==============================================================
# match_active_opt

def match_active_opt(option, line):
    option = re.escape(option)
    return re.match(' *%s( |\t)*=' % option, line)

# ==============================================================
# do_ini

def do_ini(module, filename, section=None, option=None, value=None,
        state='present', backup=False, no_extra_spaces=False, create=True):

    diff = {'before': '',
            'after': '',
            'before_header': '%s (content)' % filename,
            'after_header': '%s (content)' % filename}

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

    # append a fake section line to simplify the logic
    ini_lines.append('[')

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
    del ini_lines[-1:]

    if not within_section and option and state == 'present':
        ini_lines.append('[%s]\n' % section)
        ini_lines.append(assignment_format % (option, value))
        changed = True
        msg = 'section and option added'

    if module._diff:
        diff['after'] = ''.join(ini_lines)

    backup_file = None
    if changed and not module.check_mode:
        if backup:
            backup_file = module.backup_local(filename)
        ini_file = open(filename, 'w')
        try:
            ini_file.writelines(ini_lines)
        finally:
            ini_file.close()

    return (changed, backup_file, diff, msg)

# ==============================================================
# main

def main():

    module = AnsibleModule(
        argument_spec = dict(
            path = dict(required=True, aliases=['dest'], type='path'),
            section = dict(required=True),
            option = dict(required=False),
            value = dict(required=False),
            backup = dict(default='no', type='bool'),
            state = dict(default='present', choices=['present', 'absent']),
            no_extra_spaces = dict(required=False, default=False, type='bool'),
            create=dict(default=True, type='bool')
        ),
        add_file_common_args = True,
        supports_check_mode = True
    )

    path = module.params['path']
    section = module.params['section']
    option = module.params['option']
    value = module.params['value']
    state = module.params['state']
    backup = module.params['backup']
    no_extra_spaces = module.params['no_extra_spaces']
    create = module.params['create']

    (changed,backup_file,diff,msg) = do_ini(module, path, section, option, value, state, backup, no_extra_spaces, create)

    if not module.check_mode and os.path.exists(path):
        file_args = module.load_file_common_arguments(module.params)
        changed = module.set_fs_attributes_if_different(file_args, changed)

    results = { 'changed': changed, 'msg': msg, 'path': path, 'diff': diff }
    if backup_file is not None:
        results['backup_file'] = backup_file

    # Mission complete
    module.exit_json(**results)

if __name__ == '__main__':
    main()
