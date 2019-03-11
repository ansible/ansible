#!/usr/bin/python

# Copyright: (c) 2018, Rhys Campbell <rhys.james.campbell@googlemail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: mongodb_replicaset
short_description: Initialises a MongoDB replicaset.
description:
- Initialises a MongoDB replicaset in a new deployment.
- Validates the replicaset name for existing deployments.
author: Rhys Campbell (@rhysmeister)
version_added: "2.8"
options:
  login_user:
    description:
    - The username to authenticate with.
    type: str
  login_password:
    description:
    - The password to authenticate with.
    type: str
  login_database:
    description:
    - The database where login credentials are stored.
    type: str
    default: admin
  login_host:
    description:
    - The MongoDB hostname.
    type: str
    default: localhost
  login_port:
    description:
    - The MongoDB port to login to.
    type: int
    default: 27017
  replica_set:
    description:
    - Replicaset name.
    type: str
    default: rs0
  members:
    description:
    - A comma-separated string or a yaml list consisting of the replicaset members.
    - Supply as a simple csv string, i.e. mongodb1:27017,mongodb2:27017,mongodb3:27017.
    - If a port number is not provided then 27017 is assumed.
    type: list
  validate:
    description:
    - Performs some basic validation on the provided replicaset config.
    type: bool
    default: yes
  ssl:
    description:
    - Whether to use an SSL connection when connecting to the database
    type: bool
    default: no
  ssl_cert_reqs:
    description:
    - Specifies whether a certificate is required from the other side of the connection, and whether it will be validated if provided.
    type: str
    default: CERT_REQUIRED
    choices: [ CERT_NONE, CERT_OPTIONAL, CERT_REQUIRED ]
  arbiter_at_index:
    description:
    - Identifies the position of the member in the array that is an arbiter.
    type: int
  chaining_allowed:
    description:
    - When I(settings.chaining_allowed=true), the replicaset allows secondary members to replicate from other
      secondary members.
    - When I(settings.chaining_allowed=false), secondaries can replicate only from the primary.
    type: bool
    default: yes
  heartbeat_timeout_secs:
    description:
    - Number of seconds that the replicaset members wait for a successful heartbeat from each other.
    - If a member does not respond in time, other members mark the delinquent member as inaccessible.
    - The setting only applies when using I(protocol_version=0). When using I(protocol_version=1) the relevant
      setting is I(settings.election_timeout_millis).
    type: int
    default: 10
  election_timeout_millis:
    description:
    - The time limit in milliseconds for detecting when a replicaset's primary is unreachable.
    type: int
    default: 10000
  protocol_version:
    description: Version of the replicaset election protocol.
    type: int
    choices: [ 0, 1 ]
    default: 1
notes:
- Requires the pymongo Python package on the remote host, version 2.4.2+. This
  can be installed using pip or the OS package manager. @see U(http://api.mongodb.org/python/current/installation.html)
requirements:
- pymongo
'''

EXAMPLES = r'''
# Create a replicaset called 'rs0' with the 3 provided members
- name: Ensure replicaset rs0 exists
  mongodb_replicaset:
    login_host: localhost
    login_user: admin
    login_password: admin
    replica_set: rs0
    members:
    - mongodb1:27017
    - mongodb2:27017
    - mongodb3:27017
  when: groups.mongod.index(inventory_hostname) == 0

# Create two single-node replicasets on the localhost for testing
- name: Ensure replicaset rs0 exists
  mongodb_replicaset:
    login_host: localhost
    login_port: 3001
    login_user: admin
    login_password: secret
    login_database: admin
    replica_set: rs0
    members: localhost:3001
    validate: no

- name: Ensure replicaset rs1 exists
  mongodb_replicaset:
    login_host: localhost
    login_port: 3002
    login_user: admin
    login_password: secret
    login_database: admin
    replica_set: rs1
    members: localhost:3002
    validate: no
'''

RETURN = r'''
mongodb_replicaset:
  description: The name of the replicaset that has been created.
  returned: success
  type: str
'''

from copy import deepcopy

import os
import ssl as ssl_lib
from distutils.version import LooseVersion

try:
    from pymongo.errors import ConnectionFailure
    from pymongo.errors import OperationFailure
    from pymongo import version as PyMongoVersion
    from pymongo import MongoClient
    HAS_PYMONGO = True
except ImportError:
    try:  # for older PyMongo 2.2
        from pymongo import Connection as MongoClient
        HAS_PYMONGO = True
    except ImportError:
        HAS_PYMONGO = False

from ansible.module_utils.basic import AnsibleModule
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


def replicaset_find(client):
    """Check if a replicaset exists.

    Args:
        client (cursor): Mongodb cursor on admin database.
        replica_set (str): replica_set to check.

    Returns:
        dict: when user exists, False otherwise.
    """
    for rs in client["local"].system.replset.find({}):
        return rs["_id"]
    return False


def replicaset_add(module, client, replica_set, members, arbiter_at_index, protocol_version,
                   chaining_allowed, heartbeat_timeout_secs, election_timeout_millis):

    try:
        from collections import OrderedDict
    except ImportError as excep:
        try:
            from ordereddict import OrderedDict
        except ImportError as excep:
            module.fail_json(msg='Cannot import OrderedDict class. You can probably install with: pip install ordereddict: %s'
                             % to_native(excep))

    members_dict_list = []
    index = 0
    settings = {
        "chainingAllowed": bool(chaining_allowed),
    }
    if protocol_version == 0:
        settings['heartbeatTimeoutSecs'] = heartbeat_timeout_secs
    else:
        settings['electionTimeoutMillis'] = election_timeout_millis
    for member in members:
        if ':' not in member:  # No port supplied. Assume 27017
            member += ":27017"
        members_dict_list.append(OrderedDict([("_id", index), ("host", member)]))
        if index == arbiter_at_index:
            members_dict_list[index]['arbiterOnly'] = True
        index += 1

    conf = OrderedDict([("_id", replica_set),
                        ("protocolVersion", protocol_version),
                        ("members", members_dict_list),
                        ("settings", settings)])
    client["admin"].command('replSetInitiate', conf)


def replicaset_remove(module, client, replica_set):
    raise NotImplementedError
    # exists = replicaset_find(client, replica_set)
    # if exists:
    #    if module.check_mode:
    #        module.exit_json(changed=True, replica_set=replica_set)
    #    db = client[db_name]
    #    db.remove_user(replica_set)
    # else:
    #    module.exit_json(changed=False, user=user)


def load_mongocnf():
    config = configparser.RawConfigParser()
    mongocnf = os.path.expanduser('~/.mongodb.cnf')

    try:
        config.readfp(open(mongocnf))
    except (configparser.NoOptionError, IOError):
        return False

    creds = dict(
        user=config.get('client', 'user'),
        password=config.get('client', 'pass')
    )

    return creds


# =========================================
# Module execution.
#


def main():
    module = AnsibleModule(
        argument_spec=dict(
            login_user=dict(type='str'),
            login_password=dict(type='str', no_log=True),
            login_database=dict(type='str', default="admin"),
            login_host=dict(type='str', default="localhost"),
            login_port=dict(type='int', default=27017),
            replica_set=dict(type='str', default="rs0"),
            members=dict(type='list'),
            arbiter_at_index=dict(type='int'),
            validate=dict(type='bool', default=True),
            ssl=dict(type='bool', default=False),
            ssl_cert_reqs=dict(type='str', default='CERT_REQUIRED', choices=['CERT_NONE', 'CERT_OPTIONAL', 'CERT_REQUIRED']),
            protocol_version=dict(type='int', default=1, choices=[0, 1]),
            chaining_allowed=dict(type='bool', default=True),
            heartbeat_timeout_secs=dict(type='int', default=10),
            election_timeout_millis=dict(type='int', default=10000)
        ),
        supports_check_mode=True,
    )

    if not HAS_PYMONGO:
        module.fail_json(msg='the python pymongo module is required')

    login_user = module.params['login_user']
    login_password = module.params['login_password']
    login_database = module.params['login_database']
    login_host = module.params['login_host']
    login_port = module.params['login_port']
    replica_set = module.params['replica_set']
    members = module.params['members']
    arbiter_at_index = module.params['arbiter_at_index']
    validate = module.params['validate']
    ssl = module.params['ssl']
    protocol_version = module.params['protocol_version']
    chaining_allowed = module.params['chaining_allowed']
    heartbeat_timeout_secs = module.params['heartbeat_timeout_secs']
    election_timeout_millis = module.params['election_timeout_millis']

    if validate:
        if len(members) <= 2 or len(members) % 2 == 0:
            module.fail_json(msg="MongoDB Replicaset validation failed. Invalid number of replicaset members.")
        if arbiter_at_index is not None and len(members) - 1 > arbiter_at_index:
            module.fail_json(msg="MongoDB Replicaset validation failed. Invalid arbiter index.")

    result = dict(
        changed=False,
        replica_set=replica_set,
    )

    connection_params = dict(
        host=login_host,
        port=int(login_port),
    )

    if ssl:
        connection_params["ssl"] = ssl
        connection_params["ssl_cert_reqs"] = getattr(ssl_lib, module.params['ssl_cert_reqs'])

    try:
        client = MongoClient(**connection_params)
    except Exception as e:
        module.fail_json(msg='Unable to connect to database: %s' % to_native(e))

    try:
        check_compatibility(module, client)
    except Exception as excep:
        if "not authorized on" not in str(excep) and "there are no users authenticated" not in str(excep):
            raise excep
        if login_user is None or login_password is None:
            raise excep
        client.admin.authenticate(login_user, login_password, source=login_database)
        check_compatibility(module, client)

    if login_user is None and login_password is None:
        mongocnf_creds = load_mongocnf()
        if mongocnf_creds is not False:
            login_user = mongocnf_creds['user']
            login_password = mongocnf_creds['password']
    elif login_password is None or login_user is None:
        module.fail_json(msg="When supplying login arguments, both 'login_user' and 'login_password' must be provided")

    try:
        client['admin'].command('listDatabases', 1.0)  # if this throws an error we need to authenticate
    except Exception as excep:
        if "not authorized on" in str(excep) or "command listDatabases requires authentication" in str(excep):
            if login_user is not None and login_password is not None:
                client.admin.authenticate(login_user, login_password, source=login_database)
            else:
                raise excep
        else:
            raise excep

    if len(replica_set) == 0:
        module.fail_json(msg="Parameter 'replica_set' must not be an empty string")

    try:
        rs = replicaset_find(client)
    except Exception as e:
        module.fail_json(msg='Unable to query replica_set info: %s' % to_native(e))

    if not rs:
        if not module.check_mode:
            try:
                replicaset_add(module, client, replica_set, members, arbiter_at_index, protocol_version,
                               chaining_allowed, heartbeat_timeout_secs, election_timeout_millis)
                result['changed'] = True
            except Exception as e:
                module.fail_json(msg='Unable to create replica_set: %s' % to_native(e))
    else:
        if not module.check_mode:
            try:
                rs = replicaset_find(client)
            except Exception as e:
                module.fail_json(msg='Unable to query replica_set info: %s' % to_native(e))
            if rs is not None and rs != replica_set:
                module.fail_json(msg="The replica_set name of '{0}' does not match the expected: '{1}'".format(rs, replica_set))
        result['changed'] = False

    module.exit_json(**result)


if __name__ == '__main__':
    main()
