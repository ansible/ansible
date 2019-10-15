#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2016, Loic Blot <loic.blot@unix-experience.fr>
# Sponsored by Infopro Digital. http://www.infopro-digital.com/
# Sponsored by E.T.A.I. http://www.etai.fr/
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: mongodb_parameter
short_description: Change an administrative parameter on a MongoDB server.
description:
    - Change an administrative parameter on a MongoDB server.
version_added: "2.1"
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
            - The name of the database to add/remove the user from
        required: true
    ssl:
        description:
            - Whether to use an SSL connection when connecting to the database
        type: bool
        default: 'no'
    ssl_cert_reqs:
        version_added: "2.10"
        description:
            - Specifies whether a certificate is required from the other side of the connection, and whether it will be validated if provided.
        required: false
        default: "CERT_REQUIRED"
        choices: ["CERT_REQUIRED", "CERT_OPTIONAL", "CERT_NONE"]
    ssl_ca_certs:
        version_added: "2.10"
        description:
            - The path to a file containing certificate(s) of CA(s) that may be trusted to create the SSL cert presented by the MongoDB server
            - Implies ssl=True
        type: str
    ssl_certfile:
        version_added: "2.10"
        description:
            - Path to the file containing a TLS client certificate and (optionally) private key, in PEM encoding
            - If the private key is not in this file, ssl_keyfile is required
            - Only required when using TLS client certificates for "TLS mutual authentication"
            - Implies ssl=True
        type: str
    ssl_keyfile:
        version_added: "2.10"
        description:
            - Path to the file containing the private key corresponding to the certificate specified via ssl_certfile, in PEM encoding
            - If the private key is already in the ssl_certfile, this parameter is optional
            - Only required when using TLS client certificates for "TLS mutual authentication"
        type: str
    param:
        description:
            - MongoDB administrative parameter to modify
        required: true
    value:
        description:
            - MongoDB administrative parameter value to set
        required: true
    param_type:
        description:
            - Define the parameter value (str, int)
        default: str

notes:
    - Requires the pymongo Python package on the remote host, version 2.4.2+. This
      can be installed using pip or the OS package manager. @see http://api.mongodb.org/python/current/installation.html
requirements: [ "pymongo" ]
author: "Loic Blot (@nerzhul)"
'''

EXAMPLES = '''
# Set MongoDB syncdelay to 60 (this is an int)
- mongodb_parameter:
    param: syncdelay
    value: 60
    param_type: int
'''

RETURN = '''
before:
    description: value before modification
    returned: success
    type: str
after:
    description: value after modification
    returned: success
    type: str
'''

import os
import ssl as ssl_lib
import traceback

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
from ansible.module_utils.six.moves import configparser
from ansible.module_utils._text import to_native


# =========================================
# MongoDB module specific support methods.
#

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
        argument_spec=dict(
            login_user=dict(default=None),
            login_password=dict(default=None, no_log=True),
            login_host=dict(default='localhost'),
            login_port=dict(default=27017, type='int'),
            login_database=dict(default=None),
            replica_set=dict(default=None),
            param=dict(default=None, required=True),
            value=dict(default=None, required=True),
            param_type=dict(default="str", choices=['str', 'int']),
            ssl=dict(default=False, type='bool'),
            ssl_cert_reqs=dict(default='CERT_REQUIRED', choices=['CERT_NONE', 'CERT_OPTIONAL', 'CERT_REQUIRED']),
            ssl_certfile=dict(default=None),
            ssl_keyfile=dict(default=None),
            ssl_ca_certs=dict(default=None),
        )
    )

    if not pymongo_found:
        module.fail_json(msg=missing_required_lib('pymongo'))

    login_user = module.params['login_user']
    login_password = module.params['login_password']
    login_host = module.params['login_host']
    login_port = module.params['login_port']
    login_database = module.params['login_database']

    replica_set = module.params['replica_set']
    ssl = module.params['ssl']
    ssl_certfile = module.params['ssl_certfile']
    ssl_keyfile = module.params['ssl_keyfile']
    ssl_ca_certs = module.params['ssl_ca_certs']

    param = module.params['param']
    param_type = module.params['param_type']
    value = module.params['value']

    # Verify parameter is coherent with specified type
    try:
        if param_type == 'int':
            value = int(value)
    except ValueError:
        module.fail_json(msg="value '%s' is not %s" % (value, param_type))

    try:
        connection_params = {
            "host": login_host,
            "port": int(login_port)
        }

        if replica_set:
            connection_params["replicaset"] = replica_set

        if ssl:
            connection_params["ssl"] = ssl
            connection_params["ssl_cert_reqs"] = getattr(ssl_lib, module.params['ssl_cert_reqs'])
        if ssl_certfile:
            connection_params["ssl_certfile"] = ssl_certfile
        if ssl_keyfile:
            connection_params["ssl_keyfile"] = ssl_keyfile
        if ssl_ca_certs:
            connection_params["ssl_ca_certs"] = ssl_ca_certs

        client = MongoClient(**connection_params)

        if login_user is None and login_password is None:
            mongocnf_creds = load_mongocnf()
            if mongocnf_creds is not False:
                login_user = mongocnf_creds['user']
                login_password = mongocnf_creds['password']
        elif login_password is None or login_user is None:
            module.fail_json(msg='when supplying login arguments, both login_user and login_password must be provided')

        if login_user is not None and login_password is not None:
            client.admin.authenticate(login_user, login_password, source=login_database)

    except ConnectionFailure as e:
        module.fail_json(msg='unable to connect to database: %s' % to_native(e), exception=traceback.format_exc())

    db = client.admin

    try:
        after_value = db.command("setParameter", **{param: value})
    except OperationFailure as e:
        module.fail_json(msg="unable to change parameter: %s" % to_native(e), exception=traceback.format_exc())

    if "was" not in after_value:
        module.exit_json(changed=True, msg="Unable to determine old value, assume it changed.")
    else:
        module.exit_json(changed=(value != after_value["was"]), before=after_value["was"],
                         after=value)


if __name__ == '__main__':
    main()
