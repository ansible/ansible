#!/usr/bin/python

# (c) 2018, Jakub Kramarz <jakub.kramarz@freshmail.pl>
# Sponsored by FreshMail sp. z o.o. http://freshmail.pl
# (c) 2014, Epic Games, Inc.
# (c) 2012, Elliott Foster <elliott@fourkitchens.com>
# Sponsored by Four Kitchens http://fourkitchens.com.
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: mongodb_role
short_description: Adds or removes a role from a MongoDB database.
description:
    - Adds or removes a role from a MongoDB database.
version_added: "2.8"
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
        description:
            - The database where login credentials are stored
    replica_set:
        description:
            - Replica set to connect to (automatically connects to primary for writes)
    database:
        description:
            - The name of the database to add/remove the role from
        required: true
        aliases: [ 'db' ]
    name:
        description:
            - The name of the role to add or remove
        required: true
        aliases: [ 'role' ]
    privileges:
        description:
            - The privileges to grant to this role
    ssl:
        description:
            - Whether to use an SSL connection when connecting to the database
        type: bool
        default: 'no'
    ssl_cert_reqs:
        description:
            - Specifies whether a certificate is required from the other side of the connection, and whether it will be validated if provided
        default: "CERT_REQUIRED"
        choices: ["CERT_REQUIRED", "CERT_OPTIONAL", "CERT_NONE"]
    roles:
        description:
            - An array of roles from which this role inherits
    authentication_restrictions:
        description:
            - The authentication restrictions the server enforces on the role
    state:
        description:
            - The database role state
        default: present
        choices: [ "present", "absent" ]

notes:
    - Requires the pymongo Python package on the remote host, version 2.4.2+. This
      can be installed using pip or the OS package manager. @see http://api.mongodb.org/python/current/installation.html
    - Authentication Restrictions are not present in rolesInfo result up to MongoDB 4.0, so are not supported here in such versions.
    - This module is loosely based on mongodb_user by Elliott Foster (@elliotttf) and Julien Thebault (@lujeni).
requirements: [ "pymongo" ]
author:
    - "Jakub Kramarz (@jkramarz)"
'''

EXAMPLES = '''
# Create 'overlord' role with inherited 'readWrite' role privileges in database 'test'.
- mongodb_role:
    database: test
    name: overlord
    roles:
        - readWrite
    state: present

# Create role 'producer' in database 'test' with 'insert' privilege to 'whatever' collection in database 'test' and 'readWrite' access in database 'private'.
- mongodb_role:
    database: test
    name: producer
    roles:
        - db: private
          role: readWrite
    privileges:
        - resource:
            db: test
            collection: whatever
          actions:
            - insert
    state: present

# Remove role 'kaktus' from database 'test' via SSL (MongoDB must be compiled with the SSL option and configured properly)
- mongodb_role:
    database: test
    name: kaktus
    state: absent
    ssl: True
'''

RETURN = '''
role:
    description: The name of the role to add or remove.
    returned: success
    type: string
'''

import os
import ssl as ssl_lib
import traceback
from distutils.version import LooseVersion

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False

try:
    from pymongo.errors import ConnectionFailure
    from pymongo.errors import OperationFailure
    from pymongo import version as PyMongoVersion
    from pymongo import MongoClient
except ImportError:
    try:  # for older PyMongo 2.2
        from pymongo import Connection as MongoClient
    except ImportError:
        HAS_PYMONGO = False
    else:
        HAS_PYMONGO = True
else:
    HAS_PYMONGO = True

from ansible.module_utils.basic import AnsibleModule
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


def load_mongocnf():
    config = configparser.RawConfigParser()
    mongo_client_configuration_file = os.path.expanduser('~/.mongodb.cnf')

    try:
        config.readfp(open(mongo_client_configuration_file))
        creds = dict(
            user=config.get('client', 'user'),
            password=config.get('client', 'pass')
        )
    except (configparser.NoOptionError, IOError):
        return False

    return creds


def check_authentication_restrictions_support(client):
    loose_srv_version = LooseVersion(client.server_info()['version'])
    return loose_srv_version >= LooseVersion('4.0')


def role_find(module, client, db_name, role, authentication_restrictions_supported):
    db = client[db_name]

    if authentication_restrictions_supported:
        # yes, showAuthenticationRestrictions *is* undocumented
        result = db.command('rolesInfo',
                            role,
                            showPrivileges=True,
                            showAuthenticationRestrictions=True
                            )
    else:
        result = db.command('rolesInfo',
                            role,
                            showPrivileges=True
                            )

    if result['ok'] != 1:
        module.fail_json(msg='rolesInfo failed', exception=traceback.format_exc())

    if result['roles']:
        return result['roles'][0]
    else:
        return None


def role_add(module, client, db_name, role, privileges, roles, authentication_restrictions, authentication_restrictions_supported):
    db = client[db_name]

    if authentication_restrictions_supported:
        result = db.command('createRole',
                            role,
                            privileges=privileges,
                            roles=roles,
                            authenticationRestrictions=authentication_restrictions
                            )
    else:
        result = db.command('createRole',
                            role,
                            privileges=privileges,
                            roles=roles)

    if result['ok'] != 1:
        module.fail_json(msg='createRole failed', exception=traceback.format_exc())


def role_update(module, client, db_name, role, privileges, roles, authentication_restrictions, authentication_restrictions_supported):
    db = client[db_name]

    if authentication_restrictions_supported:
        result = db.command('updateRole',
                            role,
                            privileges=privileges,
                            roles=roles,
                            authenticationRestrictions=authentication_restrictions
                            )
    else:
        result = db.command('updateRole',
                            role,
                            privileges=privileges,
                            roles=roles
                            )

    if result['ok'] != 1:
        module.fail_json(msg='updateRole failed', exception=traceback.format_exc())


def role_compare(privileges, roles, authentication_restrictions, current, authentication_restrictions_supported):
    if authentication_restrictions_supported:
        # yes, rolesInfo does return single element list of lists
        if current['authenticationRestrictions']:
            current_restrictions = current['authenticationRestrictions'][0]
        else:
            current_restrictions = []

        return sorted(current['roles']) == sorted(roles) \
            and sorted(current['privileges']) == sorted(privileges) \
            and sorted(current_restrictions) == sorted(authentication_restrictions)
    else:
        return sorted(current['roles']) == sorted(roles) \
            and sorted(current['privileges']) == sorted(privileges)


def role_remove(module, client, db_name, role):
    db = client[db_name]
    result = db.command('dropRole', role)

    if result['ok'] != 1:
        module.fail_json(msg='dropRole failed', exception=traceback.format_exc())


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
            name=dict(required=True, aliases=['role']),

            roles=dict(default=[]),
            privileges=dict(default=[]),
            authentication_restrictions=dict(default=[]),

            state=dict(default='present', choices=['absent', 'present']),

            ssl=dict(default=False, type='bool'),
            ssl_cert_reqs=dict(default='CERT_REQUIRED', choices=['CERT_NONE', 'CERT_OPTIONAL', 'CERT_REQUIRED']),
        ),
        supports_check_mode=True
    )

    if not HAS_YAML:
        module.fail_json(msg="This module requires PyYAML. Try `pip install PyYAML`")

    if not HAS_PYMONGO:
        module.fail_json(msg="This module requires pymongo. Try `pip install pymongo`")

    ssl = module.params['ssl']

    login_user = module.params['login_user']
    login_password = module.params['login_password']
    login_host = module.params['login_host']
    login_port = module.params['login_port']
    login_database = module.params['login_database']
    replica_set = module.params['replica_set']

    db_name = module.params['database']
    role = module.params['name']
    privileges = yaml.load(module.params['privileges'])
    roles = yaml.load(module.params['roles'])
    authentication_restrictions = yaml.load(module.params['authentication_restrictions'])

    state = module.params['state']

    authentication_restrictions_supported = False

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
        # We doesn't need to be authenticated.
        check_compatibility(module, client)

        authentication_restrictions_supported = check_authentication_restrictions_support(client)
        if authentication_restrictions and not authentication_restrictions_supported:
            module.fail_json(msg='Authentication Restrictions are supported from MongoDB 3.6, but not reporter properly up to 4.0')

        if login_user is None and login_password is None:
            mongo_configuration_credentials = load_mongocnf()
            if mongo_configuration_credentials is not False:
                login_user = mongo_configuration_credentials['user']
                login_password = mongo_configuration_credentials['password']
        elif login_password is None or login_user is None:
            module.fail_json(msg='when supplying login arguments, both login_user and login_password must be provided')

        if login_user is not None and login_password is not None:
            client.admin.authenticate(login_user, login_password, source=login_database)

    except Exception as e:
        module.fail_json(msg='unable to connect to database: %s' % to_native(e), exception=traceback.format_exc())

    changed = False
    current = role_find(module, client, db_name, role, authentication_restrictions_supported)

    if state == 'present':
        if not roles and not privileges:
            module.fail_json(msg='at last one role or privilege must be specified')
        if current:
            role_is_up_to_date = role_compare(privileges,
                                              roles,
                                              authentication_restrictions,
                                              current,
                                              authentication_restrictions_supported
                                              )
            if not role_is_up_to_date:
                if not module.check_mode:
                    role_update(module,
                                client,
                                db_name,
                                role,
                                privileges,
                                roles,
                                authentication_restrictions,
                                authentication_restrictions_supported
                                )
                changed = True
        else:
            if not module.check_mode:
                role_add(module,
                         client,
                         db_name,
                         role,
                         privileges,
                         roles,
                         authentication_restrictions,
                         authentication_restrictions_supported
                         )
            changed = True
    elif state == 'absent':
        if current:
            if not module.check_mode:
                role_remove(module,
                            client,
                            db_name,
                            role
                            )
            changed = True

    module.exit_json(changed=changed, role=role)


if __name__ == '__main__':
    main()
