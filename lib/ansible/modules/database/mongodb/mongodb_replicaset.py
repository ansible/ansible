#!/usr/bin/python

# (c) 2017, Rhys Campbell <rhys.james.campbell@googlemail.com>
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type
from copy import deepcopy

ANSIBLE_METADATA = {'metadata_version': '0.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: mongodb_replicaset
short_description: Initialises a MongoDB replicaset before authentication has been turned on and then validates the configuration when it has been turned on.
description:
    - Initialises a MongoDB replicaset before authentication has been turned on and then validates the configuration when it has been turned on.
    - Validation takes the form of... replicaset name validation and memebers array length
    - This may change in the future to involve adding  and removing members
options:
    login_user:
        description:
            - The username used to authenticate with
        required: false
        default: localhost
    login_password:
        description:
            - The password used to authenticate with
        required: false
        default: null
    login_database:
        description:
            - The database where login credentials are stored
        required: false
        default: null
    replica_set:
        description:
            - Replicaset name
        required: false
        default: rs0
    members:
        description:
            - An comma sepaeated list consisting of the replicaset members.
            - By default play_hosts is assumed to be the rs members with the port 27017
            - Supply as a simple csv string
                mongodb1:27017,mongodb2:27017,mongodb3:27017
    validate:
        description:
            - Performs some basic validation on the provided replicaset config
        required: false
        default: true
    ssl:
        description:
            - Whether to use an SSL connection when connecting to the database
        default: False
    ssl_cert_reqs:
        description:
            - Specifies whether a certificate is required from the other side of the connection, and whether it will be validated if provided.
        required: false
        default: "CERT_REQUIRED"
        choices: ["CERT_REQUIRED", "CERT_OPTIONAL", "CERT_NONE"]
    arbiter_at_index:
        description: Identifies the position of the member array that is an arbiter
        required: false
        default: None
    chainingAllowed:
        description: When settings.chainingAllowed is true, the replica set allows secondary members to replicate from other secondary members. When settings.chainingAllowed is false, secondaries can replicate only from the primary.
        default: true
        required: false
    heartbeatTimeoutSecs:
        description: Number of seconds that the replica set members wait for a successful heartbeat from each other. If a member does not respond in time, other members mark the delinquent member as inaccessible. The setting only applies when using protocolVersion: 0. When using protocolVersion: 1 the relevant setting is settings.electionTimeoutMillis.
        default: 10
        required: false
    electionTimeoutMillis:
        description: The time limit in milliseconds for detecting when a replica set's primary is unreachable:
        default: 10000
        required: false
    protocolVersion:
        description: Version of the replica set election protocol.
        default: 1
        required: false

notes:
    - Requires the pymongo Python package on the remote host, version 2.4.2+. This
      can be installed using pip or the OS package manager. @see http://api.mongodb.org/python/current/installation.html
requirements: [ "pymongo" ]
'''

EXAMPLES = '''
# Create a replicaset called 'rs0' with the 3 provided members
- mongodb_replicaset:
    login_user: admin
    login_password: admin
    replica_set: rs0
    members: mongodb1:27017,mongodb2:27017,mongodb3:27017

 Create a replicaset called 'mongo_replset' with the members of the play_hosts ansible variable
- mongodb_replicaset:
    login_user: admin
    login_password: admin
    replica_set: mongo_replset
'''

LOCAL_MODULE_TESTING = '''
###############################
# LOCAL MODULE TESTING        #
###############################
http://docs.ansible.com/ansible/latest/dev_guide/developing_modules_general.html#localdirect-module-testing

1. Basic test
#############
cat << EOF > /tmp/args.json
{
    "ANSIBLE_MODULE_ARGS": {
	    "replica_set": "rs0",
	    "members": "localhost:27017,localhost:27018,localhost:27019",
        "debug": true
    }
}
EOF

# Fire up a mongodb replset
pkill mongod
rm -Rf mongotest/
mkdir -p ./mongotest/db1/ ./mongotest/db2 ./mongotest/db3
mongod --replSet rs0 --port 27017 --bind_ip localhost --dbpath ./mongotest/db1/ --logpath ./mongotest/db1/db1.log --smallfiles --oplogSize 128 --fork
mongod --replSet rs0 --port 27018 --bind_ip localhost --dbpath ./mongotest/db2/ --logpath ./mongotest/db2/db2.log --smallfiles --oplogSize 128 --fork
mongod --replSet rs0 --port 27019 --bind_ip localhost --dbpath ./mongotest/db3/ --logpath ./mongotest/db3/db3.log --smallfiles --oplogSize 128 --fork

python ./lib/ansible/modules/database/mongodb/mongodb_replicaset.py /tmp/args.json

2. Basic test with different replset name
cat << EOF > /tmp/args.json
{
    "ANSIBLE_MODULE_ARGS": {
	    "replica_set": "rhys",
	    "members": "localhost:27017,localhost:27018,localhost:27019"
    }
}
EOF

# Fire up a mongodb replset
pkill mongod && rm -Rf mongotest/
mkdir -p ./mongotest/db1/ ./mongotest/db2 ./mongotest/db3
mongod --replSet rhys --port 27017 --bind_ip localhost --dbpath ./mongotest/db1/ --logpath ./mongotest/db1/db1.log --smallfiles --oplogSize 128 --fork
mongod --replSet rhys --port 27018 --bind_ip localhost --dbpath ./mongotest/db2/ --logpath ./mongotest/db2/db2.log --smallfiles --oplogSize 128 --fork
mongod --replSet rhys --port 27019 --bind_ip localhost --dbpath ./mongotest/db3/ --logpath ./mongotest/db3/db3.log --smallfiles --oplogSize 128 --fork

python ./lib/ansible/modules/database/mongodb/mongodb_replicaset.py /tmp/args.json

3. 5 replset members
cat << EOF > /tmp/args.json
{
    "ANSIBLE_MODULE_ARGS": {
	    "replica_set": "rhys",
	    "members": "localhost:27017,localhost:27018,localhost:27019,localhost:27020,localhost:27021"
    }
}
EOF

# Fire up a mongodb replset
pkill mongod && rm -Rf mongotest/
mkdir -p ./mongotest/db1/ ./mongotest/db2 ./mongotest/db3 ./mongotest/db4 ./mongotest/db5
mongod --replSet rhys --port 27017 --bind_ip localhost --dbpath ./mongotest/db1/ --logpath ./mongotest/db1/db1.log --smallfiles --oplogSize 128 --fork
mongod --replSet rhys --port 27018 --bind_ip localhost --dbpath ./mongotest/db2/ --logpath ./mongotest/db2/db2.log --smallfiles --oplogSize 128 --fork
mongod --replSet rhys --port 27019 --bind_ip localhost --dbpath ./mongotest/db3/ --logpath ./mongotest/db3/db3.log --smallfiles --oplogSize 128 --fork
mongod --replSet rhys --port 27020 --bind_ip localhost --dbpath ./mongotest/db4/ --logpath ./mongotest/db4/db4.log --smallfiles --oplogSize 128 --fork
mongod --replSet rhys --port 27021 --bind_ip localhost --dbpath ./mongotest/db5/ --logpath ./mongotest/db5/db5.log --smallfiles --oplogSize 128 --fork

python ./lib/ansible/modules/database/mongodb/mongodb_replicaset.py /tmp/args.json

4. 7 Members with one arbiter

cat << EOF > /tmp/args.json
{
    "ANSIBLE_MODULE_ARGS": {
	    "replica_set": "rhys",
	    "members": "localhost:27017,localhost:27018,localhost:27019,localhost:27020,localhost:27021,localhost:27022,localhost:27023",
        "arbiter_at_index": 6
    }
}
EOF

pkill mongod & sleep 10
rm -Rf mongotest/
mkdir -p mongotest/db1 mongotest/db2 mongotest/db3 mongotest/db4 mongotest/db5 mongotest/db6 mongotest/db7
mongod --replSet rhys --port 27017 --bind_ip localhost --dbpath ./mongotest/db1 --logpath ./mongotest/db1/db1.log --smallfiles --oplogSize 128 --fork
mongod --replSet rhys --port 27018 --bind_ip localhost --dbpath ./mongotest/db2 --logpath ./mongotest/db2/db2.log --smallfiles --oplogSize 128 --fork
mongod --replSet rhys --port 27019 --bind_ip localhost --dbpath ./mongotest/db3 --logpath ./mongotest/db3/db3.log --smallfiles --oplogSize 128 --fork
mongod --replSet rhys --port 27020 --bind_ip localhost --dbpath ./mongotest/db4 --logpath ./mongotest/db4/db4.log --smallfiles --oplogSize 128 --fork
mongod --replSet rhys --port 27021 --bind_ip localhost --dbpath ./mongotest/db5 --logpath ./mongotest/db5/db5.log --smallfiles --oplogSize 128 --fork
mongod --replSet rhys --port 27022 --bind_ip localhost --dbpath ./mongotest/db6 --logpath ./mongotest/db6/db6.log --smallfiles --oplogSize 128 --fork
mongod --replSet rhys --port 27023 --bind_ip localhost --dbpath ./mongotest/db7 --logpath ./mongotest/db7/db7.log --smallfiles --oplogSize 128 --fork

python ./lib/ansible/modules/database/mongodb/mongodb_replicaset.py /tmp/args.json

# Now create a root user to test auth handling
mongo admin<<EOF
	db.createUser(
	{
		user: "admin",
		pwd: "admin",
		roles: [ { role: "root", db: "admin" } ]
	}
	);
EOF

# Restart with auth and keyfile
pkill mongod
openssl rand -base64 741 > keyfile.txt && chmod 600 keyfile.txt;
mongod --auth --keyFile keyfile.txt --replSet rhys --port 27017 --bind_ip localhost --dbpath ./mongotest/db1 --logpath ./mongotest/db1/db1.log --smallfiles --oplogSize 128 --fork
mongod --auth --keyFile keyfile.txt --replSet rhys --port 27018 --bind_ip localhost --dbpath ./mongotest/db2 --logpath ./mongotest/db2/db2.log --smallfiles --oplogSize 128 --fork
mongod --auth --keyFile keyfile.txt --replSet rhys --port 27019 --bind_ip localhost --dbpath ./mongotest/db3 --logpath ./mongotest/db3/db3.log --smallfiles --oplogSize 128 --fork
mongod --auth --keyFile keyfile.txt --replSet rhys --port 27020 --bind_ip localhost --dbpath ./mongotest/db4 --logpath ./mongotest/db4/db4.log --smallfiles --oplogSize 128 --fork
mongod --auth --keyFile keyfile.txt --replSet rhys --port 27021 --bind_ip localhost --dbpath ./mongotest/db5 --logpath ./mongotest/db5/db5.log --smallfiles --oplogSize 128 --fork
mongod --auth --keyFile keyfile.txt --replSet rhys --port 27022 --bind_ip localhost --dbpath ./mongotest/db6 --logpath ./mongotest/db6/db6.log --smallfiles --oplogSize 128 --fork
mongod --auth --keyFile keyfile.txt --replSet rhys --port 27023 --bind_ip localhost --dbpath ./mongotest/db7 --logpath ./mongotest/db7/db7.log --smallfiles --oplogSize 128 --fork

cat << EOF > /tmp/args.json
{
    "ANSIBLE_MODULE_ARGS": {
	    "replica_set": "rhys",
	    "members": "localhost:27017,localhost:27018,localhost:27019,localhost:27020,localhost:27021,localhost:27022,localhost:27023",
        "arbiter_at_index": 6,
        "login_user": "admin",
        "login_password": "admin"
    }
}
EOF

python ./lib/ansible/modules/database/mongodb/mongodb_replicaset.py /tmp/args.json

# Fire up a mongodb replset
pkill mongod && rm -Rf mongotest/
mkdir -p ./mongotest/db1/ ./mongotest/db2 ./mongotest/db3
mongod --replSet rhys --port 27017 --bind_ip localhost --dbpath ./mongotest/db1/ --logpath ./mongotest/db1/db1.log --smallfiles --oplogSize 128 --fork
mongod --replSet rhys --port 27018 --bind_ip localhost --dbpath ./mongotest/db2/ --logpath ./mongotest/db2/db2.log --smallfiles --oplogSize 128 --fork
mongod --replSet rhys --port 27019 --bind_ip localhost --dbpath ./mongotest/db3/ --logpath ./mongotest/db3/db3.log --smallfiles --oplogSize 128 --fork

python ./lib/ansible/modules/database/mongodb/mongodb_replicaset.py /tmp/args.json

5. Test with no port for one host to test default port default port
cat << EOF > /tmp/args.json
{
    "ANSIBLE_MODULE_ARGS": {
	    "replica_set": "rs0",
	    "members": "localhost,localhost:27018,localhost:27019"
    }
}
EOF

# Fire up a mongodb replset
pkill mongod
rm -Rf mongotest/
mkdir -p ./mongotest/db1/ ./mongotest/db2 ./mongotest/db3
mongod --replSet rs0 --port 27017 --bind_ip localhost --dbpath ./mongotest/db1/ --logpath ./mongotest/db1/db1.log --smallfiles --oplogSize 128 --fork
mongod --replSet rs0 --port 27018 --bind_ip localhost --dbpath ./mongotest/db2/ --logpath ./mongotest/db2/db2.log --smallfiles --oplogSize 128 --fork
mongod --replSet rs0 --port 27019 --bind_ip localhost --dbpath ./mongotest/db3/ --logpath ./mongotest/db3/db3.log --smallfiles --oplogSize 128 --fork

python ./lib/ansible/modules/database/mongodb/mongodb_replicaset.py /tmp/args.json
'''

RETURN = '''
replica_set:
    description: The name of the replicaset to create.
    returned: success
    type: string
'''

import os
import ssl as ssl_lib
import traceback
from distutils.version import LooseVersion

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
    for rs in client["local"].system.replset.find({ }):
                return rs["_id"]
    return False


def replicaset_add(module, client, replica_set, members, arbiter_at_index, protocolVersion, chainingAllowed, heartbeatTimeoutSecs, electionTimeoutMillis):

    try:
        from collections import OrderedDict
    except ImportError as excep:
        try:
            from ordereddict import OrderedDict
        except ImportError as excep:
            module.fail_json(msg='Cannot import OrderedDict class. You can probably install with: pip install ordereddict;: %s' % to_native(excep), exception=traceback.format_exc())

    members_dict_list = []
    index = 0
    settings = {
        "chainingAllowed": bool(chainingAllowed),
    }
    if protocolVersion == 0:
        settings['heartbeatTimeoutSecs'] = heartbeatTimeoutSecs
    else:
        settings['electionTimeoutMillis'] = electionTimeoutMillis
    for member in members:
        if ':' not in member: # No port supplied. Assume 27017
            member += ":27017"
        members_dict_list.append(OrderedDict([ ("_id", index),
                                               ("host", str(member)) ]))
        if index == arbiter_at_index:
            members_dict_list[index]['arbiterOnly'] = True
        index += 1

    conf = OrderedDict([
                            ("_id", replica_set),
                            ("protocolVersion", protocolVersion),
                            ("members", members_dict_list),
                            ("settings", settings)
    ])
    client["admin"].command('replSetInitiate', conf)

def replicaset_remove(module, client, replica_set):
    raise NotImplementedError
    #exists = replicaset_find(client, replica_set)
    #if exists:
    #    if module.check_mode:
    #        module.exit_json(changed=True, replica_set=replica_set)
    #    db = client[db_name]
    #    db.remove_user(replica_set)
    #else:
    #    module.exit_json(changed=False, user=user)

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

# =========================================
# Module execution.
#

def main():
    module = AnsibleModule(
        argument_spec = dict(
            login_user=dict(default=None),
            login_password=dict(default=None, no_log=True),
            login_database=dict(default="admin"),
            login_host=dict(default="localhost"),
            login_port=dict(default=27017),
            replica_set=dict(default=None),
            members=dict(required=False, default="{{ ansible_play_hosts }}"),
            arbiter_at_index=dict(required=False, default=None, type='int'),
            validate=dict(required=False, default=True, type='bool'),
            ssl=dict(default=False, type='bool'),
            ssl_cert_reqs=dict(default='CERT_REQUIRED', choices=['CERT_NONE', 'CERT_OPTIONAL', 'CERT_REQUIRED']),
            protocolVersion=dict(required=False, default=1, type='int', choices=[ 0, 1 ]),
            chainingAllowed=dict(required=False, default=True, type='bool'),
            heartbeatTimeoutSecs=dict(required=False, default=10, type='int'),
            electionTimeoutMillis=dict(required=False, default=10000, type='int'),
            debug=dict(required=False, default=False, type='bool')
        ),
        supports_check_mode=True
    )

    if not pymongo_found:
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
    protocolVersion = int(module.params['protocolVersion'])
    chainingAllowed = module.params['chainingAllowed']
    heartbeatTimeoutSecs = int(module.params['heartbeatTimeoutSecs'])
    electionTimeoutMillis = int(module.params['electionTimeoutMillis'])
    debug = module.params['debug']

    # convert members to python list if it's a commas seperated string
    if isinstance(members, str) and "," in members:
        temp = []
        temp = members.split(","):
        members = deepcopy(temp)

    if validate:
        if len(members) <= 2 or len(members) % 2 == 0:
            raise UserWarning("MongoDB Replicaset validation failed. Invalid number of replicaset members.")
        if arbiter_at_index is not None and len(members) - 1 > arbiter_at_index:
            raise UserWarning("MongoDB Replicaset validation failed. Invalid arbiter index.")

    try:

        connection_params = {
            "host": login_host,
            "port": int(login_port)
        }

        if ssl:
            connection_params["ssl"] = ssl
            connection_params["ssl_cert_reqs"] = getattr(ssl_lib, module.params['ssl_cert_reqs'])

        client = MongoClient(**connection_params)

        # NOTE: this check must be done ASAP.
        # We don't need to be authenticated.
        check_compatibility(module, client)

        if login_user is None and login_password is None:
            mongocnf_creds = load_mongocnf()
            if mongocnf_creds is not False:
                login_user = mongocnf_creds['user']
                login_password = mongocnf_creds['password']
        elif login_password is None or login_user is None:
            module.fail_json(msg='when supplying login arguments, both login_user and login_password must be provided')

        try:
            client['admin'].command('listDatabases', 1.0) # if this throws an error we need to authenticate
        except Exception as excep:
            if "not authorized on" in str(excep):
                if login_user is not None and login_password is not None:
                    client.admin.authenticate(login_user, login_password, source=login_database)
                else:
                    raise exceps
            else:
                raise excep

    except Exception as e:
        module.fail_json(msg='unable to connect to database: %s' % to_native(e), exception=traceback.format_exc())

    if len(replica_set) == 0:
        module.fail_json(msg='replica_set parameter must not be an empty string')
    try:
        replicaset_created = False
        if module.check_mode:
            if not replicaset_find(client):
                module.exit_json(changed=True, replica_set=replica_set)
            else:
                module.exit_json(changed=False, replica_set=replica_set)
        if not replicaset_find(client):
            replicaset_add(module, client, replica_set, members, arbiter_at_index, protocolVersion, chainingAllowed, heartbeatTimeoutSecs, electionTimeoutMillis)
            replicaset_created = True
        else:
            rs = replicaset_find(client)
            if rs is not None and rs != replica_set:
                module.fail_json(msg='The replica_set name of \'{0}\' does not match the expected: \'{1}\''.format(rs, replica_set))
    except Exception as e:
        module.fail_json(msg='Unable to create replica_set: %s' % to_native(e), exception=traceback.format_exc())

    module.exit_json(changed=replicaset_created, replica_set=replica_set)


if __name__ == '__main__':
    main()
