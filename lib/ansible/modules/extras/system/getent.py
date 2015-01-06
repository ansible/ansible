#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2014, Brian Coca <brian.coca+dev@gmail.com>
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
module: getent
short_description: a wrapper to the unix getent utility
description:
     - Runs getent against one of it's various databases and returns information into
       the host's facts, in a getent_<database> prefixed variable
version_added: "1.8"
options:
    database:
        required: True
        description:
            - the name of a getent database supported by the target system (passwd, group,
              hosts, etc).
    key:
        required: False
        default: ''
        description:
            - key from which to return values from the specified database, otherwise the
              full contents are returned.
    split:
        required: False
        default: None
        description:
            - "character used to split the database values into lists/arrays such as ':' or '\t', otherwise  it will try to pick one depending on the database"
    fail_key:
        required: False
        default: True
        description:
            - If a supplied key is missing this will make the task fail if True

notes:
   - "Not all databases support enumeration, check system documentation for details"
requirements: [ ]
author: Brian Coca
'''

EXAMPLES = '''
# get root user info
- getent: database=passwd key=root
- debug: var=getent_passwd

# get all groups
- getent: database=group split=':'
- debug: var=getent_group

# get all hosts, split by tab
- getent: database=hosts
- debug: var=getent_hosts

# get http service info, no error if missing
- getent: database=services key=http fail_key=False
- debug: var=getent_services

# get user password hash (requires sudo/root)
- getent: database=shadow key=www-data split=:
- debug: var=getent_shadow

'''

def main():
    module = AnsibleModule(
        argument_spec = dict(
            database = dict(required=True),
            key      = dict(required=False, default=None),
            split    = dict(required=False, default=None),
            fail_key = dict(required=False, type='bool', default=True),
        ),
        supports_check_mode = True,
    )

    colon = [ 'passwd', 'shadow', 'group', 'gshadow' ]

    database = module.params['database']
    key      = module.params.get('key')
    split    = module.params.get('split')
    fail_key = module.params.get('fail_key')

    getent_bin = module.get_bin_path('getent', True)

    if key is not None:
        cmd = [ getent_bin, database, key ]
    else:
        cmd = [ getent_bin, database ]

    if split is None and database in colon:
        split = ':'

    try:
        rc, out, err = module.run_command(cmd)
    except Exception, e:
        module.fail_json(msg=str(e))

    msg = "Unexpected failure!"
    dbtree = 'getent_%s' % database
    results = { dbtree: {} }

    if rc == 0:
        for line in out.splitlines():
            record = line.split(split)
            results[dbtree][record[0]] = record[1:]

        module.exit_json(ansible_facts=results)

    elif rc == 1:
        msg = "Missing arguments, or database unknown."
    elif rc == 2:
        msg = "One or more supplied key could not be found in the database."
        if not fail_key:
            results[dbtree][key] = None
            module.exit_json(ansible_facts=results, msg=msg)
    elif rc == 3:
        msg = "Enumeration not supported on this database."

    module.fail_json(msg=msg)

# import module snippets
from ansible.module_utils.basic import *

main()

