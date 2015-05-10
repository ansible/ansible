#! /usr/bin/python
# Create webfaction database using Ansible and the Webfaction API
#
# Quentin Stafford-Fraser 2015

DOCUMENTATION = '''
---
module: webfaction_db
short_description: Add or remove a database on Webfaction
description:
    - Add or remove a database on a Webfaction host. Further documentation at http://github.com/quentinsf/ansible-webfaction.
author: Quentin Stafford-Fraser
version_added: "2.0"
notes:
    - "You can run playbooks that use this on a local machine, or on a Webfaction host, or elsewhere, since the scripts use the remote webfaction API - the location is not important. However, running them on multiple hosts I(simultaneously) is best avoided. If you don't specify I(localhost) as your host, you may want to add C(serial: 1) to the plays."
    - See `the webfaction API <http://docs.webfaction.com/xmlrpc-api/>`_ for more info.
options:

    name:
        description:
            - The name of the database
        required: true

    state:
        description:
            - Whether the database should exist
        required: false
        choices: ['present', 'absent']
        default: "present"

    type:
        description:
            - The type of database to create.
        required: true
        choices: ['mysql', 'postgresql']

    login_name:
        description:
            - The webfaction account to use
        required: true

    login_password:
        description:
            - The webfaction password to use
        required: true
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
'''

import socket
import xmlrpclib

webfaction = xmlrpclib.ServerProxy('https://api.webfaction.com/')

def main():

    module = AnsibleModule(
        argument_spec = dict(
            name = dict(required=True),
            state = dict(required=False, choices=['present', 'absent'], default='present'),
            # You can specify an IP address or hostname.
            type = dict(required=True),
            password = dict(required=False, default=None),
            login_name = dict(required=True),
            login_password = dict(required=True),
        ),
        supports_check_mode=True
    )
    db_name  = module.params['name']
    db_state = module.params['state']
    db_type  = module.params['type']
    db_passwd = module.params['password']

    session_id, account = webfaction.login(
        module.params['login_name'],
        module.params['login_password']
    )

    db_list = webfaction.list_dbs(session_id)
    db_map = dict([(i['name'], i) for i in db_list])
    existing_db = db_map.get(db_name)

    result = {}
    
    # Here's where the real stuff happens

    if db_state == 'present':

        # Does an app with this name already exist?
        if existing_db:
            # Yes, but of a different type - fail
            if existing_db['db_type'] != db_type:
                module.fail_json(msg="Database already exists but is a different type. Please fix by hand.")

            # If it exists with the right type, we don't change anything.
            module.exit_json(
                changed = False,
            )


        if not module.check_mode:
            # If this isn't a dry run, create the app
            # print positional_args
            result.update(
                webfaction.create_db(
                    session_id, db_name, db_type, db_passwd
                )
            )

    elif db_state == 'absent':

        # If the app's already not there, nothing changed.
        if not existing_db:
            module.exit_json(
                changed = False,
            )

        if not module.check_mode:
            # If this isn't a dry run, delete the app
            result.update(
                webfaction.delete_db(session_id, db_name, db_type)
            )

    else:
        module.fail_json(msg="Unknown state specified: {}".format(db_state))

    module.exit_json(
        changed = True,
        result = result
    )

from ansible.module_utils.basic import *
main()

