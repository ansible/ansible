#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2014, Brian Coca <brian.coca+dev@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['stableinterface'],
                    'supported_by': 'core'}

DOCUMENTATION = r'''
---
module: getent
short_description: Query information from a getent database
description:
- Runs the C(getent) utility against one of its various databases and returns information into
  the host's facts, in a getent_<database> prefixed variable.
version_added: "1.8"
options:
  database:
    description:
    - The name of a getent database supported by the target system.
    - Possible values include
      C(ahosts), C(ahostsv4), C(ahostsv6), C(aliases), C(ethers), C(group), C(gshadow),
      C(hosts), C(initgroups), C(netgroup), C(networks), C(passwd), C(protocols), C(rpc),
      C(services), C(shadow) and more, depending on the target system.
    type: str
    required: true
  key:
    description:
    - Key from which to return values from the specified C(database).
    - If unset, the full contents will be returned in the C(getent_<database>) host fact.
    type: str
  split:
    description:
    - Character used to split the database values into lists/arrays.
    - Possible values include colon C(:) or TAB (\t), otherwise it will try to pick one depending on the C(database) used.
    type: str
  fail_key:
    description:
    - Whether the operation should fail of the supplied key is missing.
    - When set to C(yes) the operation will fail if the supplied key is missing.
    type: bool
    default: yes
notes:
- Not all databases support enumeration, check system documentation for details.
- This module updates the host facts, accessing results is done through C(getent_<database>) rather than registering return values.
author:
- Brian Coca (@bcoca)
'''

EXAMPLES = r'''
# Example using the passwd database
- name: Get root user info
  getent:
    database: passwd
    key: root
- debug:
    var: getent_passwd

# Example using the group database
- name: Get all groups
  getent:
    database: group
    split: ':'
- debug:
    var: getent_group

# Example using the hosts database
- name: Get all hosts, split by tab
  getent:
    database: hosts
- debug:
    var: getent_hosts

# Example using the services database
- name: Get http service info, no error if missing
  getent:
    database: services
    key: http
    fail_key: no
- debug:
    var: getent_services

# Example using the shadow database
- name: Get user password hash (requires sudo/root)
  getent:
    database: shadow
    key: www-data
    split: ':'
- debug:
    var: getent_shadow
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native


def main():
    module = AnsibleModule(
        argument_spec=dict(
            database=dict(type='str', required=True),
            key=dict(type='str'),
            split=dict(type='str'),
            fail_key=dict(type='bool', default=True),
        ),
        supports_check_mode=True,
    )

    colon = ['passwd', 'shadow', 'group', 'gshadow']

    database = module.params['database']
    key = module.params.get('key')
    split = module.params.get('split')
    fail_key = module.params.get('fail_key')

    getent_bin = module.get_bin_path('getent', True)

    if key is not None:
        cmd = [getent_bin, database, key]
    else:
        cmd = [getent_bin, database]

    if split is None and database in colon:
        split = ':'

    try:
        rc, out, err = module.run_command(cmd)
    except Exception as e:
        module.fail_json(msg=to_native(e))

    dbtree = 'getent_%s' % database
    results = {dbtree: {}}

    if rc == 0:
        for line in out.splitlines():
            record = line.split(split)
            results[dbtree][record[0]] = record[1:]
        module.exit_json(ansible_facts=results)

    elif rc == 1:
        module.fail_json(msg="Missing arguments, or database unknown.")

    elif rc == 2:
        if fail_key:
            module.fail_json(msg="One or more supplied keys could not be found in the database.")
        else:
            results[dbtree][key] = None
            module.exit_json(ansible_facts=results, msg="One or more supplied keys could not be found in the database.")

    elif rc == 3:
        module.fail_json(msg="Enumeration not supported on this database.")

    module.fail_json(msg="Unexpected failure!")


if __name__ == '__main__':
    main()
