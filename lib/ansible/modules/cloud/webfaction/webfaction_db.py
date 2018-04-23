#!/usr/bin/python
#
# (c) Quentin Stafford-Fraser 2015, with contributions gratefully acknowledged from:
#     * Andy Baker
#     * Federico Tarantini
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
#
# Create a webfaction database using Ansible and the Webfaction API

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: webfaction_db
short_description: Add or remove a database on Webfaction
description:
    - Add or remove a database on a Webfaction host. Further documentation at https://github.com/quentinsf/ansible-webfaction.
author: Quentin Stafford-Fraser (@quentinsf)
version_added: "2.0"
notes:
    - >
      You can run playbooks that use this on a local machine, or on a Webfaction host, or elsewhere, since the scripts use the remote webfaction API.
      The location is not important. However, running them on multiple hosts I(simultaneously) is best avoided. If you don't specify I(localhost) as
      your host, you may want to add C(serial: 1) to the plays.
    - See `the webfaction API <https://docs.webfaction.com/xmlrpc-api/>`_ for more info.
options:

    name:
        description:
            - The name of the database
        required: true

    state:
        description:
            - Whether the database should exist
        choices: ['present', 'absent']
        default: "present"

    type:
        description:
            - The type of database to create.
        required: true
        choices: ['mysql', 'postgresql']

    password:
        description:
            - The password for the new database user.

    login_name:
        description:
            - The webfaction account to use
        required: true

    login_password:
        description:
            - The webfaction password to use
        required: true

    machine:
        description:
            - The machine name to use (optional for accounts with only one machine)
'''

EXAMPLES = '''
  # This will also create a default DB user with the same
  # name as the database, and the specified password.

  - name: Create a database
    webfaction_db:
      name: "{{webfaction_user}}_db1"
      password: mytestsql
      type: mysql
      login_name: "{{webfaction_user}}"
      login_password: "{{webfaction_passwd}}"
      machine: "{{webfaction_machine}}"

  # Note that, for symmetry's sake, deleting a database using
  # 'state: absent' will also delete the matching user.

'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.six.moves import xmlrpc_client


webfaction = xmlrpc_client.ServerProxy('https://api.webfaction.com/')


def main():

    module = AnsibleModule(
        argument_spec=dict(
            name=dict(required=True),
            state=dict(required=False, choices=['present', 'absent'], default='present'),
            # You can specify an IP address or hostname.
            type=dict(required=True, choices=['mysql', 'postgresql']),
            password=dict(required=False, default=None, no_log=True),
            login_name=dict(required=True),
            login_password=dict(required=True, no_log=True),
            machine=dict(required=False, default=None),
        ),
        supports_check_mode=True
    )
    db_name = module.params['name']
    db_state = module.params['state']
    db_type = module.params['type']
    db_passwd = module.params['password']

    if module.params['machine']:
        session_id, account = webfaction.login(
            module.params['login_name'],
            module.params['login_password'],
            module.params['machine']
        )
    else:
        session_id, account = webfaction.login(
            module.params['login_name'],
            module.params['login_password']
        )

    db_list = webfaction.list_dbs(session_id)
    db_map = dict([(i['name'], i) for i in db_list])
    existing_db = db_map.get(db_name)

    user_list = webfaction.list_db_users(session_id)
    user_map = dict([(i['username'], i) for i in user_list])
    existing_user = user_map.get(db_name)

    result = {}

    # Here's where the real stuff happens

    if db_state == 'present':

        # Does a database with this name already exist?
        if existing_db:
            # Yes, but of a different type - fail
            if existing_db['db_type'] != db_type:
                module.fail_json(msg="Database already exists but is a different type. Please fix by hand.")

            # If it exists with the right type, we don't change anything.
            module.exit_json(
                changed=False,
            )

        if not module.check_mode:
            # If this isn't a dry run, create the db
            # and default user.
            result.update(
                webfaction.create_db(
                    session_id, db_name, db_type, db_passwd
                )
            )

    elif db_state == 'absent':

        # If this isn't a dry run...
        if not module.check_mode:

            if not (existing_db or existing_user):
                module.exit_json(changed=False,)

            if existing_db:
                # Delete the db if it exists
                result.update(
                    webfaction.delete_db(session_id, db_name, db_type)
                )

            if existing_user:
                # Delete the default db user if it exists
                result.update(
                    webfaction.delete_db_user(session_id, db_name, db_type)
                )

    else:
        module.fail_json(msg="Unknown state specified: {}".format(db_state))

    module.exit_json(
        changed=True,
        result=result
    )


if __name__ == '__main__':
    main()
