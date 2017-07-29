#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: redis
short_description: Various redis commands, slave and flush
description:
   - Unified utility to interact with redis instances.
     'slave' sets a redis instance in slave or master mode.
     'flush' flushes all the instance or a specified db.
     'config' (new in 1.6), ensures a configuration setting on an instance.
version_added: "1.3"
options:
    command:
        description:
            - The selected redis command
        required: true
        default: null
        choices: [ "slave", "flush", "config" ]
    login_password:
        description:
            - The password used to authenticate with (usually not used)
        required: false
        default: null
    login_host:
        description:
            - The host running the database
        required: false
        default: localhost
    login_port:
        description:
            - The port to connect to
        required: false
        default: 6379
    master_host:
        description:
            - The host of the master instance [slave command]
        required: false
        default: null
    master_port:
        description:
            - The port of the master instance [slave command]
        required: false
        default: null
    slave_mode:
        description:
            - the mode of the redis instance [slave command]
        required: false
        default: slave
        choices: [ "master", "slave" ]
    db:
        description:
            - The database to flush (used in db mode) [flush command]
        required: false
        default: null
    flush_mode:
        description:
            - Type of flush (all the dbs in a redis instance or a specific one)
              [flush command]
        required: false
        default: all
        choices: [ "all", "db" ]
    name:
        version_added: 1.6
        description:
            - A redis config key.
        required: false
        default: null
    value:
        version_added: 1.6
        description:
            - A redis config value.
        required: false
        default: null


notes:
   - Requires the redis-py Python package on the remote host. You can
     install it with pip (pip install redis) or with a package manager.
     https://github.com/andymccurdy/redis-py
   - If the redis master instance we are making slave of is password protected
     this needs to be in the redis.conf in the masterauth variable

requirements: [ redis ]
author: "Xabier Larrakoetxea (@slok)"
'''

EXAMPLES = '''
# Set local redis instance to be slave of melee.island on port 6377
- redis:
    command: slave
    master_host: melee.island
    master_port: 6377

# Deactivate slave mode
- redis:
    command: slave
    slave_mode: master

# Flush all the redis db
- redis:
    command: flush
    flush_mode: all

# Flush only one db in a redis instance
- redis:
    command: flush
    db: 1
    flush_mode: db

# Configure local redis to have 10000 max clients
- redis:
    command: config
    name: maxclients
    value: 10000

# Configure local redis to have lua time limit of 100 ms
- redis:
    command: config
    name: lua-time-limit
    value: 100
'''
import traceback

try:
    import redis
except ImportError:
    redis_found = False
else:
    redis_found = True

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native


# ===========================================
# Redis module specific support methods.
#

def set_slave_mode(client, master_host, master_port):
    try:
        return client.slaveof(master_host, master_port)
    except Exception:
        return False


def set_master_mode(client):
    try:
        return client.slaveof()
    except Exception:
        return False


def flush(client, db=None):
    try:
        if not isinstance(db, int):
            return client.flushall()
        else:
            # The passed client has been connected to the database already
            return client.flushdb()
    except Exception:
        return False


# ===========================================
# Module execution.
#

def main():
    module = AnsibleModule(
        argument_spec = dict(
            command=dict(default=None, choices=['slave', 'flush', 'config']),
            login_password=dict(default=None, no_log=True),
            login_host=dict(default='localhost'),
            login_port=dict(default=6379, type='int'),
            master_host=dict(default=None),
            master_port=dict(default=None, type='int'),
            slave_mode=dict(default='slave', choices=['master', 'slave']),
            db=dict(default=None, type='int'),
            flush_mode=dict(default='all', choices=['all', 'db']),
            name=dict(default=None),
            value=dict(default=None)
        ),
        supports_check_mode = True
    )

    if not redis_found:
        module.fail_json(msg="python redis module is required")

    login_password = module.params['login_password']
    login_host = module.params['login_host']
    login_port = module.params['login_port']
    command = module.params['command']

    # Slave Command section -----------
    if command == "slave":
        master_host = module.params['master_host']
        master_port = module.params['master_port']
        mode = module.params['slave_mode']

        #Check if we have all the data
        if mode == "slave":  # Only need data if we want to be slave
            if not master_host:
                module.fail_json(
                    msg='In slave mode master host must be provided')

            if not master_port:
                module.fail_json(
                    msg='In slave mode master port must be provided')

        #Connect and check
        r = redis.StrictRedis(host=login_host,
                              port=login_port,
                              password=login_password)
        try:
            r.ping()
        except Exception as e:
            module.fail_json(msg="unable to connect to database: %s" % to_native(e),
                             exception=traceback.format_exc())

        #Check if we are already in the mode that we want
        info = r.info()
        if mode == "master" and info["role"] == "master":
            module.exit_json(changed=False, mode=mode)

        elif mode == "slave" and\
             info["role"] == "slave" and\
             info["master_host"] == master_host and\
             info["master_port"] == master_port:
            status = {
                'status': mode,
                'master_host': master_host,
                'master_port': master_port,
            }
            module.exit_json(changed=False, mode=status)
        else:
            # Do the stuff
            # (Check Check_mode before commands so the commands aren't evaluated
            # if not necessary)
            if mode == "slave":
                if module.check_mode or\
                   set_slave_mode(r, master_host, master_port):
                    info = r.info()
                    status = {
                        'status': mode,
                        'master_host': master_host,
                        'master_port': master_port,
                    }
                    module.exit_json(changed=True, mode=status)
                else:
                    module.fail_json(msg='Unable to set slave mode')

            else:
                if module.check_mode or set_master_mode(r):
                    module.exit_json(changed=True, mode=mode)
                else:
                    module.fail_json(msg='Unable to set master mode')

    # flush Command section -----------
    elif command == "flush":
        db = module.params['db']
        mode = module.params['flush_mode']

        #Check if we have all the data
        if mode == "db":
            if db is None:
                module.fail_json(
                    msg="In db mode the db number must be provided")

        #Connect and check
        r = redis.StrictRedis(host=login_host,
                              port=login_port,
                              password=login_password,
                              db=db)
        try:
            r.ping()
        except Exception as e:
            module.fail_json(msg="unable to connect to database: %s" % to_native(e),
                             exception=traceback.format_exc())

        # Do the stuff
        # (Check Check_mode before commands so the commands aren't evaluated
        # if not necessary)
        if mode == "all":
            if module.check_mode or flush(r):
                module.exit_json(changed=True, flushed=True)
            else:  # Flush never fails :)
                module.fail_json(msg="Unable to flush all databases")

        else:
            if module.check_mode or flush(r, db):
                module.exit_json(changed=True, flushed=True, db=db)
            else:  # Flush never fails :)
                module.fail_json(msg="Unable to flush '%d' database" % db)
    elif command == 'config':
        name = module.params['name']
        value = module.params['value']

        r = redis.StrictRedis(host=login_host,
                              port=login_port,
                              password=login_password)

        try:
            r.ping()
        except Exception as e:
            module.fail_json(msg="unable to connect to database: %s" % to_native(e),
                             exception=traceback.format_exc())


        try:
            old_value = r.config_get(name)[name]
        except Exception as e:
            module.fail_json(msg="unable to read config: %s" % to_native(e),
                             exception=traceback.format_exc())
        changed = old_value != value

        if module.check_mode or not changed:
            module.exit_json(changed=changed, name=name, value=value)
        else:
            try:
                r.config_set(name, value)
            except Exception as e:
                module.fail_json(msg="unable to write config: %s" % to_native(e),
                                 exception=traceback.format_exc())
            module.exit_json(changed=changed, name=name, value=value)
    else:
        module.fail_json(msg='A valid command must be provided')


if __name__ == '__main__':
    main()
