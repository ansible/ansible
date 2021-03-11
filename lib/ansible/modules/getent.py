#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2014, Brian Coca <brian.coca+dev@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = '''
---
module: getent
short_description: A wrapper to the unix getent utility
description:
     - Runs getent against one of it's various databases and returns information into
       the host's facts, in a getent_<database> prefixed variable.
version_added: "1.8"
options:
    database:
        description:
            - The name of a getent database supported by the target system (passwd, group,
              hosts, etc).
        type: str
        required: True
    key:
        description:
            - Key from which to return values from the specified database, otherwise the
              full contents are returned.
        type: str
        default: ''
    service:
        description:
            - Override all databases with the specified service
            - The underlying system must support the service flag which is not always available.
        type: str
        version_added: "2.9"
    split:
        description:
            - "Character used to split the database values into lists/arrays such as ':' or '\t', otherwise  it will try to pick one depending on the database."
        type: str
    fail_key:
        description:
            - If a supplied key is missing this will make the task fail if C(yes).
        type: bool
        default: 'yes'

notes:
   - Not all databases support enumeration, check system documentation for details.
author:
- Brian Coca (@bcoca)
'''

EXAMPLES = '''
- name: Get root user info
  getent:
    database: passwd
    key: root
- debug:
    var: getent_passwd

- name: Get all groups
  getent:
    database: group
    split: ':'
- debug:
    var: getent_group

- name: Get all hosts, split by tab
  getent:
    database: hosts
- debug:
    var: getent_hosts

- name: Get http service info, no error if missing
  getent:
    database: services
    key: http
    fail_key: False
- debug:
    var: getent_services

- name: Get user password hash (requires sudo/root)
  getent:
    database: shadow
    key: www-data
    split: ':'
- debug:
    var: getent_shadow

'''
import traceback

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native


def main():
    module = AnsibleModule(
        argument_spec=dict(
            database=dict(type='str', required=True),
            key=dict(type='str', no_log=False),
            service=dict(type='str'),
            split=dict(type='str'),
            fail_key=dict(type='bool', default=True),
        ),
        supports_check_mode=True,
    )

    colon = ['passwd', 'shadow', 'group', 'gshadow']

    database = module.params['database']
    key = module.params.get('key')
    split = module.params.get('split')
    service = module.params.get('service')
    fail_key = module.params.get('fail_key')

    getent_bin = module.get_bin_path('getent', True)

    if key is not None:
        cmd = [getent_bin, database, key]
    else:
        cmd = [getent_bin, database]

    if service is not None:
        cmd.extend(['-s', service])

    if split is None and database in colon:
        split = ':'

    try:
        rc, out, err = module.run_command(cmd)
    except Exception as e:
        module.fail_json(msg=to_native(e), exception=traceback.format_exc())

    msg = "Unexpected failure!"
    dbtree = 'getent_%s' % database
    results = {dbtree: {}}

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


if __name__ == '__main__':
    main()
