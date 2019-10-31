#!/usr/bin/python

# (c) 2012, Elliott Foster <elliott@fourkitchens.com>
# Sponsored by Four Kitchens http://fourkitchens.com.
# (c) 2014, Epic Games, Inc.
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: mongodb_user
short_description: Adds or removes a user from a MongoDB database.
description:
    - Adds or removes a user from a MongoDB database.
version_added: "1.1"
options:
    login_user:
        description:
            - The username used to authenticate with
    login_password:
        description:
            - The password used to authenticate with
    login_host:
        description:
            - The host running the database
        default: localhost
    login_port:
        description:
            - The port to connect to
        default: 27017
    login_database:
        version_added: "2.0"
        description:
            - The database where login credentials are stored
    replica_set:
        version_added: "1.6"
        description:
            - Replica set to connect to (automatically connects to primary for writes)
    database:
        description:
            - The name of the database to add/remove the user from
        required: true
    name:
        description:
            - The name of the user to add or remove
        required: true
        aliases: [ 'user' ]
    password:
        description:
            - The password to use for the user
    ssl:
        version_added: "1.8"
        description:
            - Whether to use an SSL connection when connecting to the database
        type: bool
    ssl_cert_reqs:
        version_added: "2.2"
        description:
            - Specifies whether a certificate is required from the other side of the connection, and whether it will be validated if provided.
        default: "CERT_REQUIRED"
        choices: ["CERT_REQUIRED", "CERT_OPTIONAL", "CERT_NONE"]
    roles:
        version_added: "1.3"
        description:
            - >
              The database user roles valid values could either be one or more of the following strings:
              'read', 'readWrite', 'dbAdmin', 'userAdmin', 'clusterAdmin', 'readAnyDatabase', 'readWriteAnyDatabase', 'userAdminAnyDatabase',
              'dbAdminAnyDatabase'
            - "Or the following dictionary '{ db: DATABASE_NAME, role: ROLE_NAME }'."
            - "This param requires pymongo 2.5+. If it is a string, mongodb 2.4+ is also required. If it is a dictionary, mongo 2.6+  is required."
    state:
        description:
            - The database user state
        default: present
        choices: [ "present", "absent" ]
    update_password:
        default: always
        choices: ['always', 'on_create']
        version_added: "2.1"
        description:
          - C(always) will update passwords if they differ.  C(on_create) will only set the password for newly created users.

notes:
    - Requires the pymongo Python package on the remote host, version 2.4.2+. This
      can be installed using pip or the OS package manager. @see http://api.mongodb.org/python/current/installation.html
requirements: [ "pymongo" ]
author:
    - "Elliott Foster (@elliotttf)"
    - "Julien Thebault (@Lujeni)"
'''

EXAMPLES = '''
# Create 'burgers' database user with name 'bob' and password '12345'.
- mongodb_user:
    database: burgers
    name: bob
    password: 12345
    state: present

# Create a database user via SSL (MongoDB must be compiled with the SSL option and configured properly)
- mongodb_user:
    database: burgers
    name: bob
    password: 12345
    state: present
    ssl: True

# Delete 'burgers' database user with name 'bob'.
- mongodb_user:
    database: burgers
    name: bob
    state: absent

# Define more users with various specific roles (if not defined, no roles is assigned, and the user will be added via pre mongo 2.2 style)
- mongodb_user:
    database: burgers
    name: ben
    password: 12345
    roles: read
    state: present
- mongodb_user:
    database: burgers
    name: jim
    password: 12345
    roles: readWrite,dbAdmin,userAdmin
    state: present
- mongodb_user:
    database: burgers
    name: joe
    password: 12345
    roles: readWriteAnyDatabase
    state: present

# add a user to database in a replica set, the primary server is automatically discovered and written to
- mongodb_user:
    database: burgers
    name: bob
    replica_set: belcher
    password: 12345
    roles: readWriteAnyDatabase
    state: present

# add a user 'oplog_reader' with read only access to the 'local' database on the replica_set 'belcher'. This is useful for oplog access (MONGO_OPLOG_URL).
# please notice the credentials must be added to the 'admin' database because the 'local' database is not synchronized and can't receive user credentials
# To login with such user, the connection string should be MONGO_OPLOG_URL="mongodb://oplog_reader:oplog_reader_password@server1,server2/local?authSource=admin"
# This syntax requires mongodb 2.6+ and pymongo 2.5+
- mongodb_user:
    login_user: root
    login_password: root_password
    database: admin
    user: oplog_reader
    password: oplog_reader_password
    state: present
    replica_set: belcher
    roles:
      - db: local
        role: read

'''

RETURN = '''
user:
    description: The name of the user to add or remove.
    returned: success
    type: str
'''

import os
import ssl as ssl_lib
import traceback
from distutils.version import LooseVersion
from operator import itemgetter

try:
    from pymongo.errors import ConnectionFailure
    from pymongo.errors import OperationFailure
    from pymongo import version as PyMongoVersion
    from pymongo import MongoClient
except ImportError:
    try:  # for older PyMongo 2.2
        from pymongo import Connection as MongoClient
    except ImportError:
        pymongo_found = False
    else:
        pymongo_found = True
else:
    pymongo_found = True

from ansible.module_utils.basic import AnsibleModule, missing_required_lib
from ansible.module_utils.six import binary_type, text_type
from ansible.module_utils.six.moves import configparser
from ansible.module_utils._text import to_native


# =========================================
# MongoDB module specific support methods.
#

def check_compatibility(module, client):
    """Check the compatibility between the driver and the database.

       See: https://docs.mongodb.com/ecosystem/drivers/driver-compatibility-reference/#python-driver-compatibility

    Args:
        module: Ansible module.
        client (cursor): Mongodb cursor on admin database.
    """
    loose_srv_version = LooseVersion(client.server_info()['version'])
    loose_driver_version = LooseVersion(PyMongoVersion)

    if loose_srv_version >= LooseVersion('3.2') and loose_driver_version < LooseVersion('3.2'):
        module.fail_json(msg=' (Note: you must use pymongo 3.2+ with MongoDB >= 3.2)')

    elif loose_srv_version >= LooseVersion('3.0') and loose_driver_version <= LooseVersion('2.8'):
        module.fail_json(msg=' (Note: you must use pymongo 2.8+ with MongoDB 3.0)')

    elif loose_srv_version >= LooseVersion('2.6') and loose_driver_version <= LooseVersion('2.7'):
        module.fail_json(msg=' (Note: you must use pymongo 2.7+ with MongoDB 2.6)')

    elif LooseVersion(PyMongoVersion) <= LooseVersion('2.5'):
        module.fail_json(msg=' (Note: you must be on mongodb 2.4+ and pymongo 2.5+ to use the roles param)')


def user_find(client, user, db_name):
    """Check if the user exists.

    Args:
        client (cursor): Mongodb cursor on admin database.
        user (str): User to check.
        db_name (str): User's database.

    Returns:
        dict: when user exists, False otherwise.
    """
    for mongo_user in client["admin"].system.users.find():
        if mongo_user['user'] == user:
            # NOTE: there is no 'db' field in mongo 2.4.
            if 'db' not in mongo_user:
                return mongo_user

            if mongo_user["db"] == db_name:
                return mongo_user
    return False


def user_add(module, client, db_name, user, password, roles):
    # pymongo's user_add is a _create_or_update_user so we won't know if it was changed or updated
    # without reproducing a lot of the logic in database.py of pymongo
    db = client[db_name]

    if roles is None:
        db.add_user(user, password, False)
    else:
        db.add_user(user, password, None, roles=roles)


def user_remove(module, client, db_name, user):
    exists = user_find(client, user, db_name)
    if exists:
        if module.check_mode:
            module.exit_json(changed=True, user=user)
        db = client[db_name]
        db.remove_user(user)
    else:
        module.exit_json(changed=False, user=user)


def load_mongocnf():
    config = configparser.RawConfigParser()
    mongocnf = os.path.expanduser('~/.mongodb.cnf')

    try:
        config.readfp(open(mongocnf))
        creds = dict(
            user=config.get('client', 'user'),
            password=config.get('client', 'pass')
        )
    except (configparser.NoOptionError, IOError):
        return False

    return creds


def check_if_roles_changed(uinfo, roles, db_name):
    # We must be aware of users which can read the oplog on a replicaset
    # Such users must have access to the local DB, but since this DB does not store users credentials
    # and is not synchronized among replica sets, the user must be stored on the admin db
    # Therefore their structure is the following :
    # {
    #     "_id" : "admin.oplog_reader",
    #     "user" : "oplog_reader",
    #     "db" : "admin",                    # <-- admin DB
    #     "roles" : [
    #         {
    #             "role" : "read",
    #             "db" : "local"             # <-- local DB
    #         }
    #     ]
    # }

    def make_sure_roles_are_a_list_of_dict(roles, db_name):
        output = list()
        for role in roles:
            if isinstance(role, (binary_type, text_type)):
                new_role = {"role": role, "db": db_name}
                output.append(new_role)
            else:
                output.append(role)
        return output

    roles_as_list_of_dict = make_sure_roles_are_a_list_of_dict(roles, db_name)
    uinfo_roles = uinfo.get('roles', [])

    if sorted(roles_as_list_of_dict, key=itemgetter('db')) == sorted(uinfo_roles, key=itemgetter('db')):
        return False
    return True


# =========================================
# Module execution.
#

def main():
    module = AnsibleModule(
        argument_spec=dict(
            login_user=dict(default=None),
            login_password=dict(default=None, no_log=True),
            login_host=dict(default='localhost'),
            login_port=dict(default='27017'),
            login_database=dict(default=None),
            replica_set=dict(default=None),
            database=dict(required=True, aliases=['db']),
            name=dict(required=True, aliases=['user']),
            password=dict(aliases=['pass'], no_log=True),
            ssl=dict(default=False, type='bool'),
            roles=dict(default=None, type='list'),
            state=dict(default='present', choices=['absent', 'present']),
            update_password=dict(default="always", choices=["always", "on_create"]),
            ssl_cert_reqs=dict(default='CERT_REQUIRED', choices=['CERT_NONE', 'CERT_OPTIONAL', 'CERT_REQUIRED']),
        ),
        supports_check_mode=True
    )

    if not pymongo_found:
        module.fail_json(msg=missing_required_lib('pymongo'))

    login_user = module.params['login_user']
    login_password = module.params['login_password']
    login_host = module.params['login_host']
    login_port = module.params['login_port']
    login_database = module.params['login_database']

    replica_set = module.params['replica_set']
    db_name = module.params['database']
    user = module.params['name']
    password = module.params['password']
    ssl = module.params['ssl']
    roles = module.params['roles'] or []
    state = module.params['state']
    update_password = module.params['update_password']

    try:
        connection_params = {
            "host": login_host,
            "port": int(login_port),
        }

        if replica_set:
            connection_params["replicaset"] = replica_set

        if ssl:
            connection_params["ssl"] = ssl
            connection_params["ssl_cert_reqs"] = getattr(ssl_lib, module.params['ssl_cert_reqs'])

        client = MongoClient(**connection_params)

        # NOTE: this check must be done ASAP.
        # We doesn't need to be authenticated (this ability has lost in PyMongo 3.6)
        if LooseVersion(PyMongoVersion) <= LooseVersion('3.5'):
            check_compatibility(module, client)

        if login_user is None and login_password is None:
            mongocnf_creds = load_mongocnf()
            if mongocnf_creds is not False:
                login_user = mongocnf_creds['user']
                login_password = mongocnf_creds['password']
        elif login_password is None or login_user is None:
            module.fail_json(msg='when supplying login arguments, both login_user and login_password must be provided')

        if login_user is not None and login_password is not None:
            client.admin.authenticate(login_user, login_password, source=login_database)
        elif LooseVersion(PyMongoVersion) >= LooseVersion('3.0'):
            if db_name != "admin":
                module.fail_json(msg='The localhost login exception only allows the first admin account to be created')
            # else: this has to be the first admin user added

    except Exception as e:
        module.fail_json(msg='unable to connect to database: %s' % to_native(e), exception=traceback.format_exc())

    if state == 'present':
        if password is None and update_password == 'always':
            module.fail_json(msg='password parameter required when adding a user unless update_password is set to on_create')

        try:
            if update_password != 'always':
                uinfo = user_find(client, user, db_name)
                if uinfo:
                    password = None
                    if not check_if_roles_changed(uinfo, roles, db_name):
                        module.exit_json(changed=False, user=user)

            if module.check_mode:
                module.exit_json(changed=True, user=user)

            user_add(module, client, db_name, user, password, roles)
        except Exception as e:
            module.fail_json(msg='Unable to add or update user: %s' % to_native(e), exception=traceback.format_exc())

            # Here we can  check password change if mongo provide a query for that : https://jira.mongodb.org/browse/SERVER-22848
            # newuinfo = user_find(client, user, db_name)
            # if uinfo['role'] == newuinfo['role'] and CheckPasswordHere:
            #    module.exit_json(changed=False, user=user)

    elif state == 'absent':
        try:
            user_remove(module, client, db_name, user)
        except Exception as e:
            module.fail_json(msg='Unable to remove user: %s' % to_native(e), exception=traceback.format_exc())

    module.exit_json(changed=True, user=user)


if __name__ == '__main__':
    main()
