#!/usr/bin/python

# (c) 2015, Julien Thebault <julien.thebault@1000mercis.com>
# Sponsored by 1000mercis http://www.1000mercis.com
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

DOCUMENTATION = '''
---
module: mongodb_role
short_description: Creates/Updates/Removes a role and specifies its privileges.
description:
    - Creates/Updates/Removes a role and specifies its privileges.
options:
    login_host:
        description:
            - The host running the database.
        required: false
        default: localhost

    login_port:
        description:
            - The port to connect to.
        required: false
        default: 27017

    login_options:
        description:
            - Other optional parameters can be passed as keyword arguments.
        required: false
        default: null

    authenticate_name:
        description:
            - The name used to authenticate with.
        required: false
        default: null

    authenticate_password:
        description:
            - The password used to authenticate with.
        required: false
        default: null

    authenticate_source:
        description:
            - The source used to authenticate with.
        required: false
        default: null

    authenticate_mechanism:
        description
            - The mechanism used to authenticate with.
        required: false
        default: DEFAULT

    name:
        description:
            - The name of the role.
        required: true

    db:
        description:
            - The database to which the role belongs.
        required: true

    state:
        description:
            - The role state.
        required: false
        default: present
        choices: [ "present", "absent" ]

    privilege_db:
        description:
            - The database to which the privilege belongs.
        required: true

    privilege_collection:
        description:
            - The collection to which the privilege belongs.
        required: true

    privilege_actions:
        description:
            - Define the operations a user can perform on a resource.
        required: true

    privilege_state:
        description:
            - The privilege's role state
        required: false
        default: present
        choices: [ "present", "absent" ]

notes:
    - Requires the pymongo Python package on the remote host, version 2.4.2+. This
      can be installed using pip or the OS package manager. @see http://api.mongodb.org/python/current/installation.html
requirements: [ "pymongo" ]
author: "Julien Thebault (@Lujeni)"
'''

EXAMPLES = '''
# Create 'foobar' role on 'foo' database, allow 'find' and 'insert' operations on all collections.
- mongodb_role: db=foo name=foobar privilege_db=foo privilege_collection='' privilege_actions='find,insert'

# Add a privilege to 'foobar' role, allow 'find' operation on 'bar' collection.
- mongodb_role: db=foo name=foobar privilege_db=foo privilege_collection=bar privilege_actions='find'

# Remove a privilege to 'foobar' role.
- mongodb_role: db=foo name=foobar privilege_db=foo privilege_collection=bar privilege_actions='find' privilege_state=absent

# Remove a role.
- mongodb_role: db=foo name=foobar privilege_dbfoo privilege_collection='' privilege_actions='find,insert' state=absent
'''


from pymongo.errors import ConnectionFailure
from pymongo.errors import OperationFailure

try:
    from pymongo import MongoClient
except ImportError:
    try:
        from pymongo import Connection as MongoClient
    except ImportError:
        MongoClient = None


PRIVILEGE_ACTIONS = [
    'find', 'insert', 'remove', 'update', 'changeCustomData',
    'changeOwnCustomData', 'changeOwnPassword', 'changePassword', 'createCollection',
    'createIndex', 'createRole', 'createUser', 'dropCollection', 'dropRole',
    'dropUser', 'emptycapped', 'enableProfiler', 'grantRole', 'killCursors',
    'revokeRole', 'unlock', 'viewRole', 'viewUser', 'authSchemaUpgrade',
    'cleanupOrphaned', 'cpuProfiler', 'inprog', 'invalidateUserCache', 'killop',
    'planCacheRead', 'planCacheWrite', 'storageDetails', 'appendOplogNote',
    'replSetConfigure', 'replSetGetStatus', 'replSetHeartbeat', 'replSetStateChange',
    'resync', 'addShard', 'enableSharding', 'flushRouterConfig', 'getShardMap',
    'getShardVersion', 'listShards', 'moveChunk', 'removeShard', 'shardingState',
    'splitChunk', 'splitVector', 'applicationMessage', 'closeAllDatabases',
    'collMod', 'compact', 'connPoolSync', 'convertToCapped', 'dropDatabase',
    'dropIndex', 'fsync', 'getParameter', 'hostInfo', 'logRotate', 'reIndex',
    'renameCollectionSameDB', 'repairDatabase', 'setParameter', 'shutdown',
    'touch', 'collStats', 'connPoolStats', 'cursorInfo', 'dbHash', 'dbStats',
    'diagLogging', 'getCmdLineOpts', 'getLog', 'indexStats', 'listDatabases',
    'listCollections', 'listIndexes', 'netstat', 'serverStatus', 'validate',
    'top', 'anyAction', 'internal']

PRIVILEGES_COMMAND = {
    'present': 'grantPrivilegesToRole',
    'absent': 'revokePrivilegesFromRole'
}


class MongoRoleModule(object):
    """ Creates/Updates a role and specifies its privileges.
        see https://docs.mongodb.org/manual/reference/system-roles-collection/
    """

    def __init__(self, module):
        """ Instanciate the mongoDB connection and the module params.

        Args:
            module: The ansible module.
        """
        try:
            self.module = module

            # mongodb
            login_host = self.module.params['login_host']
            login_port = self.module.params['login_port']
            login_options = self.module.params['login_options'] or {}

            # mongodb authentication
            authenticate_name = self.module.params['authenticate_name']
            authenticate_password = self.module.params['authenticate_password']
            authenticate_source = self.module.params['authenticate_source']
            authenticate_mechanism = self.module.params['authenticate_mechanism'] or 'DEFAULT'
            authenticate_options = self.module.params['authenticate_options'] or {}

            # role
            self.role_name = self.module.params['name']
            self.role_db = self.module.params['db']
            self.role_id = '{}.{}'.format(self.role_db, self.role_name)
            self.role_state = self.module.params['state']

            # privilege
            self.privilege_db = self.module.params['privilege_db']
            self.privilege_collection = self.module.params['privilege_collection']
            self.privilege_actions = self.module.params['privilege_actions']
            self.privilege_state = self.module.params['privilege_state']
            # TODO: The roles array contains role documents that specify
            # the roles from which this role inherits privileges.
            # self.resource_roles = self.module.params['resource_roles'] or []
            self.privilege = {
                'resource' : {
                    'db': self.privilege_db,
                    'collection': self.privilege_collection},
                'actions' : self.privilege_actions,
            }

            # mongodb privileges
            self.query_privilege = {
                'privileges': {
                    '$elemMatch': {
                        'resource.db': self.privilege_db,
                        'resource.collection': self.privilege_collection,
                    }
                }
            }

            self.conn = MongoClient(
                host=login_host,
                port=login_port,
                **login_options
            )

            if authenticate_name and authenticate_password:
                self.conn.admin.authenticate(
                    name=authenticate_name,
                    password=authenticate_password,
                    source=authenticate_source,
                    mechanism=authenticate_mechanism,
                    **authenticate_options)
        except OperationFailure, e:
            self.module.fail_json(msg='authentication failure :: {}'.format(e))
        except ConnectionFailure, e:
            self.module.fail_json(msg='unable to connect to database :: {}'.format(e))
        except Exception, e:
            self.module.fail_json(msg='unable to instanciate the module :: {}'.format(e))

    def upsert_role(self):
        """ Manage roles.

            Assigns additional privileges or removes the specified privileges
            to a user-defined role.
        """
        try:
            if self.role_state == 'absent':
                return self.drop_role()

            if not self.find_role():
                return True, self.conn[self.role_db].command('createRole', self.role_name, privileges=[self.privilege], roles=[])

            # NOTE: fishy way to manage the idempotent state of the privileges.
            if not self.conn.admin.system.roles.find_one(self.query_privilege):
                if self.privilege_state == 'absent':
                    return False, 'No privilege exist :: {}'.format(self.privilege)
                return True, self.conn[self.role_db].command('grantPrivilegesToRole', self.role_name,privileges=[self.privilege])

            # NOTE: To revoke a privilege, the resource document pattern
            # must match exactly the resource field of that privilege.
            result_privileges = self.conn.admin.system.roles.find_one(
                self.query_privilege, {'privileges.$': 1})

            if self.privilege_state == 'absent':
                return True, self.conn[self.role_db].command('revokePrivilegesFromRole', self.role_name, privileges=result_privileges['privileges'])

            # NOTE: need to verify the actions part.
            if self.privilege_actions == result_privileges['privileges'][0]['actions']:
                return False, 'This privilege already exist :: {}'.format(self.privilege)

            self.conn[self.role_db].command('revokePrivilegesFromRole', self.role_name, privileges=result_privileges['privileges'])
            return True, self.conn[self.role_db].command('grantPrivilegesToRole', self.role_name, privileges=[self.privilege])
        except Exception, e:
            return True, e

    def drop_role(self):
        """ Deletes a user-defined role from the database on which you run the command.

            Returns:
                bool: The task state (changed or not).
                string: The result task message.
        """
        try:
            if self.find_role():
                return True, self.conn[self.role_db].command('dropRole', self.role_name)
            return False, 'No role named {}'.format(self.role_name)
        except OperationFailure, e:
            return True, e

    def find_role(self):
        """ Find a specific role from the name.

            Returns:
                bool: True if found, False otherwise.
        """
        try:
            return self.conn.admin.system.roles.find_one({'_id': self.role_id})
        except Exception, e:
            self.module.fail_json(msg='unable to found the role {} :: {}'.format(self.role_id, e))


def main():
    module = AnsibleModule(
        argument_spec=dict(
            login_host=dict(default='localhost'),
            login_port=dict(default=27017, type='int'),
            login_options=dict(default={}),
            authenticate_name=dict(default=None),
            authenticate_password=dict(default=None),
            authenticate_source=dict(default=None),
            authenticate_mechanism=dict(default=None),
            authenticate_options=dict(default=None),
            name=dict(required=True),
            db=dict(required=True),
            privilege_db=dict(required=True, default=None),
            privilege_collection=dict(required=True, default=None),
            privilege_actions=dict(required=True, type='list'),
            privilege_state=dict(default='present', choices=['absent', 'present']),
            state=dict(default='present', choices=['absent', 'present']),
        )
    )

    if not MongoClient:
        module.fail_json(msg='the python pymongo module is required')

    for action in module.params.get('privilege_actions', []):
        if action not in PRIVILEGE_ACTIONS:
            module.fail_json(msg='{} must be one of the privileges actions'.format(action))

    changed = True
    mongo_role_module = MongoRoleModule(module=module)
    changed, result = mongo_role_module.upsert_role()
    module.exit_json(changed=changed, msg=result)


from ansible.module_utils.basic import *
if __name__ == '__main__':
    main()
