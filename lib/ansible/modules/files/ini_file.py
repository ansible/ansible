#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2012, Jan-Piet Mens <jpmens () gmail.com>
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
     - Comments are discarded when the source file is read, and therefore will not 
       show up in the destination file.
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
notes:
   - While it is possible to add an I(option) without specifying a I(value), this makes
     no sense.
   - A section named C(default) cannot be added by the module, but if it exists, individual
     options within the section can be updated. (This is a limitation of Python's I(ConfigParser).)
     Either use M(template) to create a base INI file with a C([default]) section, or use
     M(lineinfile) to add the missing line.
requirements: [ ConfigParser ]
author: Jan-Piet Mens
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

# ==============================================================
# do_ini

def do_ini(module, filename, section=None, option=None, value=None, state='present', backup=False):

    changed = False
    if (sys.version_info[0] == 2 and sys.version_info[1] >= 7) or sys.version_info[0] >= 3: 
        cp = ConfigParser.ConfigParser(allow_no_value=True)
    else:
        cp = ConfigParser.ConfigParser()
    cp.optionxform = identity

    try:
        f = open(filename)
        cp.readfp(f)
    except IOError:
        pass


    if state == 'absent':
        if option is None and value is None:
            if cp.has_section(section):
                cp.remove_section(section)
                changed = True
        else:
            if option is not None:
                try:
                    if cp.get(section, option):
                        cp.remove_option(section, option)
                        changed = True
                except:
                    pass

    if state == 'present':

        # DEFAULT section is always there by DEFAULT, so never try to add it.
        if not cp.has_section(section) and section.upper() != 'DEFAULT':

            cp.add_section(section)
            changed = True

        if option is not None and value is not None:
            try:
                oldvalue = cp.get(section, option)
                if str(value) != str(oldvalue):
                    cp.set(section, option, value)
                    changed = True
            except ConfigParser.NoSectionError:
                cp.set(section, option, value)
                changed = True
            except ConfigParser.NoOptionError:
                cp.set(section, option, value)
                changed = True

    if changed and not module.check_mode:
        if backup:
            module.backup_local(filename)

        try:
            f = open(filename, 'w')
            cp.write(f)
        except:
            module.fail_json(msg="Can't create %s" % filename)

    return changed

# ==============================================================
# identity

def identity(arg):
    """
    This function simply returns its argument. It serves as a
    replacement for ConfigParser.optionxform, which by default
    changes arguments to lower case. The identity function is a
    better choice than str() or unicode(), because it is
    encoding-agnostic.
    """
    return arg

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
            state = dict(default='present', choices=['present', 'absent'])
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

    changed = do_ini(module, dest, section, option, value, state, backup)

    file_args = module.load_file_common_arguments(module.params)
    changed = module.set_fs_attributes_if_different(file_args, changed)

    # Mission complete
    module.exit_json(dest=dest, changed=changed, msg="OK")

# import module snippets
from ansible.module_utils.basic import *
main()
