#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2012, Jan-Piet Mens <jpmens () gmail.com>
# (c) 2015, Ales Nosek <anosek.nosek () gmail.com>
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
#

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
version_added: "0.9"
options:
  dest:
    description:
      - Path to the INI-style file; this file is created if required
    required: true
    default: null
  section:
    description:
      - Section name in INI file. This is added if C(state=present) automatically when
        a single value is being set.
    required: true
    default: null
  option:
    description:
      - if set (required for changing a I(value)), this is the name of the option.
      - May be omitted if adding/removing a whole I(section).
    required: false
    default: null
  value:
    description:
     - the string value to be associated with an I(option). May be omitted when removing an I(option).
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
       - all arguments accepted by the M(file) module also work here
     required: false
  state:
     description:
       - If set to C(absent) the option or section will be removed if present instead of created.
     required: false
     default: "present"
     choices: [ "present", "absent" ]
  no_extra_spaces:
     description:
       - do not insert spaces before and after '=' symbol
     required: false
     default: false
     version_added: "2.1"
notes:
   - While it is possible to add an I(option) without specifying a I(value), this makes
     no sense.
   - A section named C(default) cannot be added by the module, but if it exists, individual
     options within the section can be updated. (This is a limitation of Python's I(ConfigParser).)
     Either use M(template) to create a base INI file with a C([default]) section, or use
     M(lineinfile) to add the missing line.
requirements: [ ConfigParser ]
author:
    - "Jan-Piet Mens (@jpmens)"
    - "Ales Nosek (@noseka1)"
'''

EXAMPLES = '''
# Ensure "fav=lemonade is in section "[drinks]" in specified file
- ini_file: dest=/etc/conf section=drinks option=fav value=lemonade mode=0600 backup=yes

- ini_file: dest=/etc/anotherconf
            section=drinks
            option=temperature
            value=cold
            backup=yes
'''

import ConfigParser
import sys
import os

# ==============================================================
# match_opt

def match_opt(option, line):
  option = re.escape(option)
  return re.match('%s( |\t)*=' % option, line) \
    or re.match('# *%s( |\t)*=' % option, line) \
    or re.match('; *%s( |\t)*=' % option, line)

# ==============================================================
# match_active_opt

def match_active_opt(option, line):
  option = re.escape(option)
  return re.match('%s( |\t)*=' % option, line)

# ==============================================================
# do_ini

def do_ini(module, filename, section=None, option=None, value=None, state='present', backup=False, no_extra_spaces=False):


    if not os.path.exists(filename):
      try:
        open(filename,'w').close()
      except:
        module.fail_json(msg="Destination file %s not writable" % filename)
    ini_file = open(filename, 'r')
    try:
        ini_lines = ini_file.readlines()
        # append a fake section line to simplify the logic
        ini_lines.append('[')
    finally:
        ini_file.close()

    within_section = not section
    section_start = 0
    changed = False
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
                    ini_lines.insert(index, assignment_format % (option, value))
                    changed = True
                elif state == 'absent' and not option:
                    # remove the entire section
                    del ini_lines[section_start:index]
                    changed = True
                break
        else:
            if within_section and option:
                if state == 'present':
                    # change the existing option line
                    if match_opt(option, line):
                        newline = assignment_format % (option, value)
                        changed = ini_lines[index] != newline
                        ini_lines[index] = newline
                        if changed:
                            # remove all possible option occurences from the rest of the section
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
                else:
                    # comment out the existing option line
                    if match_active_opt(option, line):
                        ini_lines[index] = '#%s' % ini_lines[index]
                        changed = True
                        break

    # remove the fake section line
    del ini_lines[-1:]

    if not within_section and option and state == 'present':
        ini_lines.append('[%s]\n' % section)
        ini_lines.append(assignment_format % (option, value))
        changed = True


    if changed and not module.check_mode:
        if backup:
            module.backup_local(filename)
        ini_file = open(filename, 'w')
        try:
            ini_file.writelines(ini_lines)
        finally:
            ini_file.close()

    return changed

# ==============================================================
# main

def main():

    module = AnsibleModule(
        argument_spec = dict(
            dest = dict(required=True),
            section = dict(required=True),
            option = dict(required=False),
            value = dict(required=False),
            backup = dict(default='no', type='bool'),
            state = dict(default='present', choices=['present', 'absent']),
            no_extra_spaces = dict(required=False, default=False, type='bool')
        ),
        add_file_common_args = True,
        supports_check_mode = True
    )

    info = dict()

    dest = os.path.expanduser(module.params['dest'])
    section = module.params['section']
    option = module.params['option']
    value = module.params['value']
    state = module.params['state']
    backup = module.params['backup']
    no_extra_spaces = module.params['no_extra_spaces']

    changed = do_ini(module, dest, section, option, value, state, backup, no_extra_spaces)

    file_args = module.load_file_common_arguments(module.params)
    changed = module.set_fs_attributes_if_different(file_args, changed)

    # Mission complete
    module.exit_json(dest=dest, changed=changed, msg="OK")

# import module snippets
from ansible.module_utils.basic import *
if __name__ == '__main__':
    main()
