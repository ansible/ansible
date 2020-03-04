#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2020, Andrew Klychkov (@Andersson007) <aaklychkov@mail.ru>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: mongodb_info

short_description: Gather information about MongoDB instance.

description:
- Gather information about MongoDB instance.

author: Andrew Klychkov (@Andersson007)

version_added: '2.10'

options:
  filter:
    description:
    - Limit the collected information by comma separated string or YAML list.
    - Allowable values are C(general), C(databases), C(total_size), C(parameters), C(users), C(roles).
    - By default, collects all subsets.
    - You can use '!' before value (for example, C(!users)) to exclude it from the information.
    - If you pass including and excluding values to the filter, for example, I(filter=!general,users),
      the excluding values, C(!general) in this case, will be ignored.
    required: no
    type: list
    elements: str
  login_user:
    description:
    - The MongoDB user to login with.
    - Required when I(login_password) is specified.
    required: no
    type: str
  login_password:
    description:
    - The password used to authenticate with.
    - Required when I(login_user) is specified.
    required: no
    type: str
  login_database:
    description:
    - The database where login credentials are stored.
    required: no
    type: str
    default: 'admin'
  login_host:
    description:
    - The host running MongoDB instance to login to.
    required: no
    type: str
    default: 'localhost'
  login_port:
    description:
    - The MongoDB server port to login to.
    required: no
    type: int
    default: 27017
  ssl:
    description:
    - Whether to use an SSL connection when connecting to the database.
    required: no
    type: bool
    default: no
  ssl_cert_reqs:
    description:
    - Specifies whether a certificate is required from the other side of the connection,
      and whether it will be validated if provided.
    required: no
    type: str
    default: 'CERT_REQUIRED'
    choices: ['CERT_NONE', 'CERT_OPTIONAL', 'CERT_REQUIRED']

notes:
    - Requires the pymongo Python package on the remote host, version 2.4.2+.

requirements: [ 'pymongo' ]
'''

EXAMPLES = r'''
- name: Gather all supported information
  mongodb_info:
    login_user: admin
    login_password: secret
  register: result

- name: Show gathered info
  debug:
    msg: '{{ result }}'

- name: Gather only information about databases and their total size
  mongodb_info:
    login_user: admin
    login_password: secret
    filter: databases, total_size

- name: Gather all information except parameters
  mongodb_info:
    login_user: admin
    login_password: secret
    filter: '!parameters'
'''

RETURN = r'''
general:
  description: General instance information.
  returned: always
  type: dict
  sample: {"allocator": "tcmalloc", "bits": 64, "storageEngines": ["biggie"], "version": "4.2.3", "maxBsonObjectSize": 16777216}
databases:
  description: Database information.
  returned: always
  type: dict
  sample: {"admin": {"empty": false, "sizeOnDisk": 245760}, "config": {"empty": false, "sizeOnDisk": 110592}}
total_size:
  description: Total size of all databases in bytes.
  returned: always
  type: int
  sample: 397312
users:
  description: User information.
  returned: always
  type: dict
  sample: {"new_user": {"_id": "config.new_user", "db": "config", "mechanisms": ["SCRAM-SHA-1", "SCRAM-SHA-256"], "roles": []}}
roles:
  description: Role information.
  returned: always
  type: dict
  sample: {"restore": {"db": "admin", "inheritedRoles": [], "isBuiltin": true, "roles": []}}
parameters:
  description: Server parameters information.
  returned: always
  type: dict
  sample: {"maxOplogTruncationPointsAfterStartup": 100, "maxOplogTruncationPointsDuringStartup": 100, "maxSessions": 1000000}
'''

import traceback

from uuid import UUID

import ssl as ssl_lib
from distutils.version import LooseVersion

PYMONGO_IMP_ERR = None
try:
    from pymongo import version as PyMongoVersion
    from pymongo import MongoClient
except ImportError:
    PYMONGO_IMP_ERR = traceback.format_exc()
    pymongo_found = False
else:
    pymongo_found = True

from ansible.module_utils.basic import AnsibleModule, missing_required_lib
from ansible.module_utils._text import to_native
from ansible.module_utils.six import iteritems


# =========================================
# MongoDB module specific support methods.
#

def check_compatibility(module, srv_version, driver_version):
    """Check the compatibility between the driver and the database.

    See: https://docs.mongodb.com/ecosystem/drivers/driver-compatibility-reference/#python-driver-compatibility

    Args:
        module: Ansible module.
        srv_version (LooseVersion): MongoDB server version.
        driver_version (LooseVersion): Pymongo version.
    """
    msg = 'pymongo driver version and MongoDB version are incompatible: '

    if srv_version >= LooseVersion('4.2') and driver_version < LooseVersion('3.9'):
        msg += 'you must use pymongo 3.9+ with MongoDB >= 4.2'
        module.fail_json(msg=msg)

    elif srv_version >= LooseVersion('4.0') and driver_version < LooseVersion('3.7'):
        msg += 'you must use pymongo 3.7+ with MongoDB >= 4.0'
        module.fail_json(msg=msg)

    elif srv_version >= LooseVersion('3.6') and driver_version < LooseVersion('3.6'):
        msg += 'you must use pymongo 3.6+ with MongoDB >= 3.6'
        module.fail_json(msg=msg)

    elif srv_version >= LooseVersion('3.4') and driver_version < LooseVersion('3.4'):
        msg += 'you must use pymongo 3.4+ with MongoDB >= 3.4'
        module.fail_json(msg=msg)

    elif srv_version >= LooseVersion('3.2') and driver_version < LooseVersion('3.2'):
        msg += 'you must use pymongo 3.2+ with MongoDB >= 3.2'
        module.fail_json(msg=msg)

    elif srv_version >= LooseVersion('3.0') and driver_version <= LooseVersion('2.8'):
        msg += 'you must use pymongo 2.8+ with MongoDB 3.0'
        module.fail_json(msg=msg)

    elif srv_version >= LooseVersion('2.6') and driver_version <= LooseVersion('2.7'):
        msg += 'you must use pymongo 2.7+ with MongoDB 2.6'
        module.fail_json(msg=msg)


class MongoDbInfo():
    """Class for gathering MongoDB instance information.

    Args:
        module (AnsibleModule): Object of AnsibleModule class.
        client (pymongo): pymongo client object to interact with the database.
    """
    def __init__(self, module, client):
        self.module = module
        self.client = client
        self.admin_db = self.client.admin
        self.info = {
            'general': {},
            'databases': {},
            'total_size': {},
            'parameters': {},
            'users': {},
            'roles': {},
        }

    def get_info(self, filter_):
        """Get MongoDB instance information and return it based on filter_.

        Args:
            filter_ (list): List of collected subsets (e.g., general, users, etc.),
                when it is empty, return all available information.
        """
        self.__collect()

        inc_list = []
        exc_list = []

        if filter_:
            partial_info = {}

            for fi in filter_:
                if fi.lstrip('!') not in self.info:
                    self.module.warn("filter element '%s' is not allowable, ignored" % fi)
                    continue

                if fi[0] == '!':
                    exc_list.append(fi.lstrip('!'))

                else:
                    inc_list.append(fi)

            if inc_list:
                for i in self.info:
                    if i in inc_list:
                        partial_info[i] = self.info[i]

            else:
                for i in self.info:
                    if i not in exc_list:
                        partial_info[i] = self.info[i]

            return partial_info

        else:
            return self.info

    def __collect(self):
        """Collect information."""
        # Get general info:
        self.info['general'] = self.client.server_info()

        # Get parameters:
        self.info['parameters'] = self.get_parameters_info()

        # Gather info about databases and their total size:
        self.info['databases'], self.info['total_size'] = self.get_db_info()

        for dbname, val in iteritems(self.info['databases']):
            # Gather info about users for each database:
            self.info['users'].update(self.get_users_info(dbname))

            # Gather info about roles for each database:
            self.info['roles'].update(self.get_roles_info(dbname))

    def get_roles_info(self, dbname):
        """Gather information about roles.

        Args:
            dbname (str): Database name to get role info from.

        Returns a dictionary with role information.
        """
        db = self.client[dbname]
        result = db.command({'rolesInfo': 1, 'showBuiltinRoles': True})['roles']

        roles_dict = {}
        for elem in result:
            roles_dict[elem['role']] = {}
            for key, val in iteritems(elem):
                if key == 'role':
                    continue

                roles_dict[elem['role']][key] = val

        return roles_dict

    def get_users_info(self, dbname):
        """Gather information about users.

        Args:
            dbname (str): Database name to get user info from.

        Returns a dictionary with user information.
        """
        db = self.client[dbname]
        result = db.command({'usersInfo': 1})['users']

        users_dict = {}
        for elem in result:
            users_dict[elem['user']] = {}
            for key, val in iteritems(elem):
                if key == 'user':
                    continue

                if isinstance(val, UUID):
                    val = val.hex

                users_dict[elem['user']][key] = val

        return users_dict

    def get_db_info(self):
        """Gather information about databases.

        Returns a dictionary with database information.
        """
        result = self.admin_db.command({'listDatabases': 1})
        total_size = int(result['totalSize'])
        result = result['databases']

        db_dict = {}
        for elem in result:
            db_dict[elem['name']] = {}
            for key, val in iteritems(elem):
                if key == 'name':
                    continue

                if key == 'sizeOnDisk':
                    val = int(val)

                db_dict[elem['name']][key] = val

        return db_dict, total_size

    def get_parameters_info(self):
        """Gather parameters information.

        Returns a dictionary with parameters.
        """
        return self.admin_db.command({'getParameter': '*'})


# ================
# Module execution
#

def main():
    argument_spec = dict(
        login_user=dict(type='str', required=False),
        login_password=dict(type='str', required=False, no_log=True),
        login_database=dict(type='str', required=False, default='admin'),
        login_host=dict(type='str', required=False, default='localhost'),
        login_port=dict(type='int', required=False, default=27017),
        ssl=dict(type='bool', required=False, default=False),
        ssl_cert_reqs=dict(type='str', required=False, default='CERT_REQUIRED',
                           choices=['CERT_NONE', 'CERT_OPTIONAL', 'CERT_REQUIRED']),
        filter=dict(type='list', elements='str', required=False),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_together=[['login_user', 'login_password']],
    )

    if not pymongo_found:
        module.fail_json(msg=missing_required_lib('pymongo'), exception=PYMONGO_IMP_ERR)

    login_user = module.params['login_user']
    login_password = module.params['login_password']
    login_database = module.params['login_database']
    login_host = module.params['login_host']
    login_port = module.params['login_port']
    ssl = module.params['ssl']
    filter_ = module.params['filter']

    if filter_:
        filter_ = [f.strip() for f in filter_]

    connection_params = {
        'host': login_host,
        'port': login_port,
    }

    if ssl:
        connection_params['ssl'] = ssl
        connection_params['ssl_cert_reqs'] = getattr(ssl_lib, module.params['ssl_cert_reqs'])

    client = MongoClient(**connection_params)

    if login_user:
        try:
            client.admin.authenticate(login_user, login_password, source=login_database)
        except Exception as e:
            module.fail_json(msg='Unable to authenticate: %s' % to_native(e))

    # Get server version:
    try:
        srv_version = LooseVersion(client.server_info()['version'])
    except Exception as e:
        module.fail_json(msg='Unable to get MongoDB server version: %s' % to_native(e))

    # Get driver version::
    driver_version = LooseVersion(PyMongoVersion)

    # Check driver and server version compatibility:
    check_compatibility(module, srv_version, driver_version)

    # Initialize an object and start main work:
    mongodb = MongoDbInfo(module, client)

    module.exit_json(changed=False, **mongodb.get_info(filter_))


if __name__ == '__main__':
    main()
