#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2012, Mark Theunissen <mark.theunissen@gmail.com>
# Sponsored by Four Kitchens http://fourkitchens.com.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: mysql_db
short_description: Add or remove MySQL databases from a remote host.
description:
   - Add or remove MySQL databases from a remote host.
version_added: "0.6"
options:
  name:
    description:
      - name of the database to add or remove
      - name=all May only be provided if I(state) is C(dump) or C(import).
      - if name=all Works like --all-databases option for mysqldump (Added in 2.0)
    required: true
    aliases: [ db ]
  state:
    description:
      - The database state
    default: present
    choices: [ "present", "absent", "dump", "import" ]
  collation:
    description:
      - Collation mode (sorting). This only applies to new table/databases and does not update existing ones, this is a limitation of MySQL.
  encoding:
    description:
      - Encoding mode to use, examples include C(utf8) or C(latin1_swedish_ci)
  target:
    description:
      - Location, on the remote host, of the dump file to read from or write to. Uncompressed SQL
        files (C(.sql)) as well as bzip2 (C(.bz2)), gzip (C(.gz)) and xz (Added in 2.0) compressed files are supported.
  single_transaction:
    description:
      - Execute the dump in a single transaction
    type: bool
    default: 'no'
    version_added: "2.1"
  quick:
    description:
      - Option used for dumping large tables
    type: bool
    default: 'yes'
    version_added: "2.1"
  ignore_tables:
    description:
      - A list of table names that will be ignored in the dump of the form database_name.table_name
    required: false
    default: []
    version_added: "2.7"
author: "Ansible Core Team"
requirements:
   - mysql (command line binary)
   - mysqldump (command line binary)
notes:
   - Requires the python-mysqldb package on the remote host, as well as mysql and mysqldump binaries.
extends_documentation_fragment: mysql
'''

EXAMPLES = '''
- name: Create a new database with name 'bobdata'
  mysql_db:
    name: bobdata
    state: present

# Copy database dump file to remote host and restore it to database 'my_db'
- name: Copy database dump file
  copy:
    src: dump.sql.bz2
    dest: /tmp
- name: Restore database
  mysql_db:
    name: my_db
    state: import
    target: /tmp/dump.sql.bz2

- name: Dump all databases to hostname.sql
  mysql_db:
    state: dump
    name: all
    target: /tmp/{{ inventory_hostname }}.sql

- name: Import file.sql similar to mysql -u <username> -p <password> < hostname.sql
  mysql_db:
    state: import
    name: all
    target: /tmp/{{ inventory_hostname }}.sql
'''

import os
import pipes
import subprocess
import traceback

try:
    import MySQLdb
except ImportError:
    mysqldb_found = False
else:
    mysqldb_found = True

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.database import mysql_quote_identifier
from ansible.module_utils.mysql import mysql_connect, mysqldb_found
from ansible.module_utils._text import to_native


# ===========================================
# MySQL module specific support methods.
#


def db_exists(cursor, db):
    res = cursor.execute("SHOW DATABASES LIKE %s", (db.replace("_", r"\_"),))
    return bool(res)


def db_delete(cursor, db):
    query = "DROP DATABASE %s" % mysql_quote_identifier(db, 'database')
    cursor.execute(query)
    return True


def db_dump(module, host, user, password, db_name, target, all_databases, port, config_file, socket=None, ssl_cert=None, ssl_key=None, ssl_ca=None,
            single_transaction=None, quick=None, ignore_tables=None):
    cmd = module.get_bin_path('mysqldump', True)
    # If defined, mysqldump demands --defaults-extra-file be the first option
    if config_file:
        cmd += " --defaults-extra-file=%s" % pipes.quote(config_file)
    if user is not None:
        cmd += " --user=%s" % pipes.quote(user)
    if password is not None:
        cmd += " --password=%s" % pipes.quote(password)
    if ssl_cert is not None:
        cmd += " --ssl-cert=%s" % pipes.quote(ssl_cert)
    if ssl_key is not None:
        cmd += " --ssl-key=%s" % pipes.quote(ssl_key)
    if ssl_cert is not None:
        cmd += " --ssl-ca=%s" % pipes.quote(ssl_ca)
    if socket is not None:
        cmd += " --socket=%s" % pipes.quote(socket)
    else:
        cmd += " --host=%s --port=%i" % (pipes.quote(host), port)
    if all_databases:
        cmd += " --all-databases"
    else:
        cmd += " %s" % pipes.quote(db_name)
    if single_transaction:
        cmd += " --single-transaction=true"
    if quick:
        cmd += " --quick"
    if ignore_tables:
        for an_ignored_table in ignore_tables:
            cmd += " --ignore-table={0}".format(an_ignored_table)

    path = None
    if os.path.splitext(target)[-1] == '.gz':
        path = module.get_bin_path('gzip', True)
    elif os.path.splitext(target)[-1] == '.bz2':
        path = module.get_bin_path('bzip2', True)
    elif os.path.splitext(target)[-1] == '.xz':
        path = module.get_bin_path('xz', True)

    if path:
        cmd = '%s | %s > %s' % (cmd, path, pipes.quote(target))
    else:
        cmd += " > %s" % pipes.quote(target)

    rc, stdout, stderr = module.run_command(cmd, use_unsafe_shell=True)
    return rc, stdout, stderr


def db_import(module, host, user, password, db_name, target, all_databases, port, config_file, socket=None, ssl_cert=None, ssl_key=None, ssl_ca=None):
    if not os.path.exists(target):
        return module.fail_json(msg="target %s does not exist on the host" % target)

    cmd = [module.get_bin_path('mysql', True)]
    # --defaults-file must go first, or errors out
    if config_file:
        cmd.append("--defaults-extra-file=%s" % pipes.quote(config_file))
    if user:
        cmd.append("--user=%s" % pipes.quote(user))
    if password:
        cmd.append("--password=%s" % pipes.quote(password))
    if socket is not None:
        cmd.append("--socket=%s" % pipes.quote(socket))
    if ssl_cert is not None:
        cmd.append("--ssl-cert=%s" % pipes.quote(ssl_cert))
    if ssl_key is not None:
        cmd.append("--ssl-key=%s" % pipes.quote(ssl_key))
    if ssl_cert is not None:
        cmd.append("--ssl-ca=%s" % pipes.quote(ssl_ca))
    else:
        cmd.append("--host=%s" % pipes.quote(host))
        cmd.append("--port=%i" % port)
    if not all_databases:
        cmd.append("-D")
        cmd.append(pipes.quote(db_name))

    comp_prog_path = None
    if os.path.splitext(target)[-1] == '.gz':
        comp_prog_path = module.get_bin_path('gzip', required=True)
    elif os.path.splitext(target)[-1] == '.bz2':
        comp_prog_path = module.get_bin_path('bzip2', required=True)
    elif os.path.splitext(target)[-1] == '.xz':
        comp_prog_path = module.get_bin_path('xz', required=True)

    if comp_prog_path:
        p1 = subprocess.Popen([comp_prog_path, '-dc', target], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        p2 = subprocess.Popen(cmd, stdin=p1.stdout, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        (stdout2, stderr2) = p2.communicate()
        p1.stdout.close()
        p1.wait()
        if p1.returncode != 0:
            stderr1 = p1.stderr.read()
            return p1.returncode, '', stderr1
        else:
            return p2.returncode, stdout2, stderr2
    else:
        cmd = ' '.join(cmd)
        cmd += " < %s" % pipes.quote(target)
        rc, stdout, stderr = module.run_command(cmd, use_unsafe_shell=True)
        return rc, stdout, stderr


def db_create(cursor, db, encoding, collation):
    query_params = dict(enc=encoding, collate=collation)
    query = ['CREATE DATABASE %s' % mysql_quote_identifier(db, 'database')]
    if encoding:
        query.append("CHARACTER SET %(enc)s")
    if collation:
        query.append("COLLATE %(collate)s")
    query = ' '.join(query)
    cursor.execute(query, query_params)
    return True

# ===========================================
# Module execution.
#


def main():
    module = AnsibleModule(
        argument_spec=dict(
            login_user=dict(default=None),
            login_password=dict(default=None, no_log=True),
            login_host=dict(default="localhost"),
            login_port=dict(default=3306, type='int'),
            login_unix_socket=dict(default=None),
            name=dict(required=True, aliases=['db']),
            encoding=dict(default=""),
            collation=dict(default=""),
            target=dict(default=None, type='path'),
            state=dict(default="present", choices=["absent", "present", "dump", "import"]),
            ssl_cert=dict(default=None, type='path'),
            ssl_key=dict(default=None, type='path'),
            ssl_ca=dict(default=None, type='path'),
            connect_timeout=dict(default=30, type='int'),
            config_file=dict(default="~/.my.cnf", type='path'),
            single_transaction=dict(default=False, type='bool'),
            quick=dict(default=True, type='bool'),
            ignore_tables=dict(default=[], type='list')
        ),
        supports_check_mode=True
    )

    if not mysqldb_found:
        module.fail_json(msg="The MySQL-python module is required.")

    db = module.params["name"]
    encoding = module.params["encoding"]
    collation = module.params["collation"]
    state = module.params["state"]
    target = module.params["target"]
    socket = module.params["login_unix_socket"]
    login_port = module.params["login_port"]
    if login_port < 0 or login_port > 65535:
        module.fail_json(msg="login_port must be a valid unix port number (0-65535)")
    ssl_cert = module.params["ssl_cert"]
    ssl_key = module.params["ssl_key"]
    ssl_ca = module.params["ssl_ca"]
    connect_timeout = module.params['connect_timeout']
    config_file = module.params['config_file']
    login_password = module.params["login_password"]
    login_user = module.params["login_user"]
    login_host = module.params["login_host"]
    ignore_tables = module.params["ignore_tables"]
    for a_table in ignore_tables:
        if a_table == "":
            module.fail_json(msg="Name of ignored table cannot be empty")
    single_transaction = module.params["single_transaction"]
    quick = module.params["quick"]

    if state in ['dump', 'import']:
        if target is None:
            module.fail_json(msg="with state=%s target is required" % state)
        if db == 'all':
            db = 'mysql'
            all_databases = True
        else:
            all_databases = False
    else:
        if db == 'all':
            module.fail_json(msg="name is not allowed to equal 'all' unless state equals import, or dump.")
    try:
        cursor = mysql_connect(module, login_user, login_password, config_file, ssl_cert, ssl_key, ssl_ca,
                               connect_timeout=connect_timeout)
    except Exception as e:
        if os.path.exists(config_file):
            module.fail_json(msg="unable to connect to database, check login_user and login_password are correct or %s has the credentials. "
                                 "Exception message: %s" % (config_file, to_native(e)))
        else:
            module.fail_json(msg="unable to find %s. Exception message: %s" % (config_file, to_native(e)))

    changed = False
    if not os.path.exists(config_file):
        config_file = None
    if db_exists(cursor, db):
        if state == "absent":
            if module.check_mode:
                module.exit_json(changed=True, db=db)
            else:
                try:
                    changed = db_delete(cursor, db)
                except Exception as e:
                    module.fail_json(msg="error deleting database: %s" % to_native(e))
                module.exit_json(changed=changed, db=db)

        elif state == "dump":
            if module.check_mode:
                module.exit_json(changed=True, db=db)
            else:
                rc, stdout, stderr = db_dump(module, login_host, login_user,
                                             login_password, db, target, all_databases,
                                             login_port, config_file, socket, ssl_cert, ssl_key,
                                             ssl_ca, single_transaction, quick, ignore_tables)
                if rc != 0:
                    module.fail_json(msg="%s" % stderr)
                else:
                    module.exit_json(changed=True, db=db, msg=stdout)

        elif state == "import":
            if module.check_mode:
                module.exit_json(changed=True, db=db)
            else:
                rc, stdout, stderr = db_import(module, login_host, login_user,
                                               login_password, db, target,
                                               all_databases,
                                               login_port, config_file,
                                               socket, ssl_cert, ssl_key, ssl_ca)
                if rc != 0:
                    module.fail_json(msg="%s" % stderr)
                else:
                    module.exit_json(changed=True, db=db, msg=stdout)

        elif state == "present":
            if module.check_mode:
                module.exit_json(changed=False, db=db)
            module.exit_json(changed=False, db=db)

    else:
        if state == "present":
            if module.check_mode:
                changed = True
            else:
                try:
                    changed = db_create(cursor, db, encoding, collation)
                except Exception as e:
                    module.fail_json(msg="error creating database: %s" % to_native(e),
                                     exception=traceback.format_exc())
            module.exit_json(changed=changed, db=db)

        elif state == "import":
            if module.check_mode:
                module.exit_json(changed=True, db=db)
            else:
                try:
                    changed = db_create(cursor, db, encoding, collation)
                    if changed:
                        rc, stdout, stderr = db_import(module, login_host, login_user,
                                                       login_password, db, target, all_databases,
                                                       login_port, config_file, socket, ssl_cert, ssl_key, ssl_ca)
                        if rc != 0:
                            module.fail_json(msg="%s" % stderr)
                        else:
                            module.exit_json(changed=True, db=db, msg=stdout)
                except Exception as e:
                    module.fail_json(msg="error creating database: %s" % to_native(e),
                                     exception=traceback.format_exc())

        elif state == "absent":
            if module.check_mode:
                module.exit_json(changed=False, db=db)
            module.exit_json(changed=False, db=db)

        elif state == "dump":
            if module.check_mode:
                module.exit_json(changed=False, db=db)
            module.fail_json(msg="Cannot dump database %s - not found" % (db))


if __name__ == '__main__':
    main()
