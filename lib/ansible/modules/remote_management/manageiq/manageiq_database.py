#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2017, Alex Braverman Masis <alexbmasis@gmail.com>
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

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: manageiq_database
description:
    - Manage appliance database configuration using the appliance_console_cli on ManageIQ.
short_description: Configure ManageIQ appliance database.
version_added: "2.4"
author: "Alex Braverman Masis (@abraverm)"
requirements:
    - appliance_console_cli
options:
    internal:
        description: Should ManageIQ appliance database be self hosted (internal).
        default: True
        type: bool
    region:
        description: ManageIQ region the database assosieted with.
        default: 0
    dbdisk:
        description: |
            In case of internal database, path of the disk to use for database
            server storage.
    username:
        description: User name to use for ManageIQ database.
        default: root
    password:
        description: Password to use for ManageIQ database.
        default: smartvm
    hostname:
        description: ManageIQ database server IP or FQDN connect to.
        default: 127.0.0.1
    dbname:
        description: Name of the database to use to store ManageIQ tables.
        default: vmdb_production
    backup_location:
        description: Two types of locations supported by ManageIQ, local and remote.
        default: local
    backup_path:
        description: File path or URI of the backup.
        default: /tmp/backup
    backup_username:
        description: User name for remote backup location access.
        default: root
    backup_password:
        description: Password for remote backup location access.
        default: smartvm
    pg_data_path:
        description: When removing database, the files are removed too.
        default: /var/opt/rh/rh-postgresql95/lib/pgsql/data/
'''

EXAMPLES = '''
- name: Create simple internal database
  manageiq_database:
      internal: true
      region: 0
'''

RETURN = ''' # '''

import os.path
import shutil
from ansible.module_utils.basic import AnsibleModule

VMDB = '/var/www/miq/vmdb'
CMD_NAME = '/usr/bin/appliance_console_cli'
VALUED_ARGS = ['dbdisk', 'username', 'password', 'hostname', 'dbname']
ENV = dict(DISABLE_DATABASE_ENVIRONMENT_CHECK='1')


def manageiq_db_arg_spec():
    return dict(
        state=dict(default='internal', type='str'),
        region=dict(default=1, type='int'),
        dbdisk=dict(type='str'),
        username=dict(default='root', type='str', no_log=True),
        password=dict(default='smartvm', type='str', no_log=True),
        hostname=dict(default='localhost', type='str'),
        dbname=dict(default='vmdb_production', type='str'),
        backup_path=dict(default='/tmp/backup', type='str'),
        backup_username=dict(default='root', type='str', no_log=True),
        backup_password=dict(default='smartvm', type='str', no_log=True),
        backup_location=dict(default='local', type='str'),
        pg_data_path=dict(
            default='/var/opt/rh/rh-postgresql95/lib/pgsql/data/',
            type='str')
    )


def run_command(module, command, cwd=VMDB, env=ENV, fail=True, **kwargs):
    result, out, err = module.run_command(command, cwd=cwd,
                                          environ_update=env, **kwargs)
    if result == 1:
        if fail:
            module.fail_json(msg="%s\n%s" % (out, err))
        else:
            return False, err
    return True, out


def stop_evm(module):
    tries = 3
    evm_status = ['bin/rake', 'evm:status']
# Its ok to use systemctl as ManageIQ is distributed as pre built images
    evm_stop = ['systemctl', 'stop', 'evmserverd']
    rc, out = run_command(module, evm_status, fail=False)
    while 'started' in out and tries > 0:
        run_command(module, evm_stop)
        rc, out = run_command(module, evm_status, fail=False)
        tries -= 1
    else:
        if 'started' in out:
            module.fail_json(msg='Unable to stop EVM service')
        return False
    return True


def db_state(module):
    db_state = {}
    db_state['configured'] = os.path.exists("%s/config/database.yml" % VMDB)
    result, out, err = module.run_command(['bin/rake', 'db:version'], cwd=VMDB,
                                          environ_update=ENV)
    db_state['exists'] = True if result == 0 else False
    return db_state


def db_state_validate(module, db_state, configured, exists):
    if configured != db_state['configured']:
        if configured:
            module.fail_json(msg='Database need to be configured first')
        else:
            module.fail_json(msg='Database is already configured')
    if exists != db_state['exists']:
        if exists:
            module.fail_json(msg='Databse is not running or deployed correctly')
        else:
            module.fail_json(msg='Databse already exists')


def db_destroy(module, db_state):
    pg_data = module.params['pg_data_path']
    msg = ""
    changed = False
    if stop_evm(module):
        changed = True
        msg += "EVM stopped\n"
    rc, out = run_command(module, ['bin/rake', 'evm:db:stop'], fail=False)
    if rc:
        changed = True
        msg += "Postgress stopped\n"
    if os.path.exists(pg_data):
        shutil.rmtree(pg_data, ignore_errors=True)
        changed = True
        msg += "%s was removed\n" % pg_data
    if os.path.exists("%s/config/database.yml" % VMDB):
        os.remove("%s/config/database.yml" % VMDB)
        changed = True
        msg += "config/database.yml was removed\n"
    if changed:
        run_command(module, ['bin/rake', 'evm:db:stop'], fail=False)
        module.exit_json(changed=True, stdout=msg)
    else:
        module.exit_json(changed=False, stdout="Nothing to do")


def db_reset(module, db_state):
    db_state_validate(module, db_state, configured=True, exists=True)
    stop_evm(module)
    run_command(module, ['bin/rake', 'evm:db:reset'])
    module.exit_json(changed=True, stdout="EVM database was reset successfuly")


def db_backup(*args):
    db_backup_restore('backup', *args)


def db_restore(*args):
    db_backup_restore('restore', *args)


def db_backup_restore(action, module, db_state):
    location = module.params['backup_location']
    path = module.params['backup_path']
    username = module.params['backup_username']
    password = module.params['backup_password']
    dbname = module.params['dbname']

    db_state_validate(module, db_state, configured=True, exists=True)
    stop_evm(module)
    if location == 'remote':
        cmd = ['bin/rake', "evm:db:%s:%s" % (action, location), '--',
               '--dbname', dbname, '--uri', path, '--uri-username', username,
               '--uri-password', password]
    elif location == 'local':
        cmd = ['bin/rake', "evm:db:%s:%s" % (action, location), '--',
               '--local-file', path, '--dbname', dbname]
    else:
        module.fail_json(
            msg="Unknown location '%s', only 'remote' and 'local' are supported")
    rc, out = run_command(module, cmd)
    module.exit_json(changed=True,
                     stdout="Database %s was backed up to %s" % (dbname, path))


def main():
    module = AnsibleModule(
        argument_spec=manageiq_db_arg_spec()
        # Due to a bug, region means creating a region and not connecting to
        # http://talk.manageiq.org/t/setup-region-join-region-in-darga/1654/6
    )

    if not os.path.exists(CMD_NAME):
        module.fail_json(msg="Cannot find %s" % CMD_NAME)

    state = module.params['state']
    system_state = db_state(module)

    changed, stdout, stderr = False, '', ''

    if state in ['absent', 'destroy']:
        db_destroy(module, system_state)
    elif state == 'reset':
        db_reset(module, system_state)
    elif state == 'backup':
        db_backup(module, system_state)
    elif state == 'restore':
        db_restore(module, system_state)
    elif state in ['present', 'internal', 'external']:
        cmd = CMD_NAME
        region = module.params['region']
        db_state_validate(module, system_state, configured=False, exists=False)
        if state in ['present', 'internal']:
            cmd += " --internal --region=%d" % module.params['region']
        else:
            with open("%s/REGION" % VMDB, 'w') as region_file:
                region_file.write(str(region))

        for arg in VALUED_ARGS:
            if module.params[arg] is not None and module.params[arg] != '':
                cmd += " --{}={}".format(arg, module.params[arg])
        changed, stdout, sdterr = module.run_command(cmd)
        changed = False if "already exists" in stdout else True
        if stderr != '' or 'Failed' in stdout:
            module.fail_json(msg="%s\n%s\n%s" % (cmd, stdout, stderr))
        module.exit_json(changed=changed, cmd=cmd, stdout=stdout, stderr=stderr)
    else:
        module.fail_json(msg="unknown state: '%s'" % state)


if __name__ == "__main__":
    main()
