#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2012, Mark Theunissen <mark.theunissen@gmail.com>
# Sponsored by Four Kitchens http://fourkitchens.com.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: mysql_db
short_description: Add or remove MySQL databases from a remote host
description:
- Add or remove MySQL databases from a remote host.
version_added: '0.6'
options:
  name:
    description:
    - Name of the database to add or remove.
    - I(name=all) may only be provided if I(state) is C(dump) or C(import).
    - List of databases is provided with I(state=dump), I(state=present) and I(state=absent).
    - If I(name=all) it works like --all-databases option for mysqldump (Added in 2.0).
    required: true
    type: list
    elements: str
    aliases: [db]
  state:
    description:
    - The database state
    type: str
    default: present
    choices: ['absent', 'dump', 'import', 'present']
  collation:
    description:
    - Collation mode (sorting). This only applies to new table/databases and
      does not update existing ones, this is a limitation of MySQL.
    type: str
    default: ''
  encoding:
    description:
    - Encoding mode to use, examples include C(utf8) or C(latin1_swedish_ci),
      at creation of database, dump or importation of sql script.
    type: str
    default: ''
  target:
    description:
    - Location, on the remote host, of the dump file to read from or write to.
    - Uncompressed SQL files (C(.sql)) as well as bzip2 (C(.bz2)), gzip (C(.gz)) and
      xz (Added in 2.0) compressed files are supported.
    type: path
  single_transaction:
    description:
    - Execute the dump in a single transaction.
    type: bool
    default: no
    version_added: '2.1'
  quick:
    description:
    - Option used for dumping large tables.
    type: bool
    default: yes
    version_added: '2.1'
  ignore_tables:
    description:
    - A list of table names that will be ignored in the dump
      of the form database_name.table_name.
    type: list
    elements: str
    required: no
    default: []
    version_added: '2.7'
  hex_blob:
    description:
    - Dump binary columns using hexadecimal notation.
    required: no
    default: no
    type: bool
    version_added: '2.10'
  force:
    description:
    - Continue dump or import even if we get an SQL error.
    - Used only when I(state) is C(dump) or C(import).
    required: no
    type: bool
    default: no
    version_added: '2.10'
  master_data:
    description:
      - Option to dump a master replication server to produce a dump file
        that can be used to set up another server as a slave of the master.
      - C(0) to not include master data.
      - C(1) to generate a 'CHANGE MASTER TO' statement
        required on the slave to start the replication process.
      - C(2) to generate a commented 'CHANGE MASTER TO'.
      - Can be used when I(state=dump).
    required: no
    type: int
    choices: [0, 1, 2]
    default: 0
    version_added: '2.10'
  skip_lock_tables:
    description:
      - Skip locking tables for read. Used when I(state=dump), ignored otherwise.
    required: no
    type: bool
    default: no
    version_added: '2.10'
  dump_extra_args:
    description:
      - Provide additional arguments for mysqldump.
        Used when I(state=dump) only, ignored otherwise.
    required: no
    type: str
    version_added: '2.10'
seealso:
- module: mysql_info
- module: mysql_variables
- module: mysql_user
- module: mysql_replication
- name: MySQL command-line client reference
  description: Complete reference of the MySQL command-line client documentation.
  link: https://dev.mysql.com/doc/refman/8.0/en/mysql.html
- name: mysqldump reference
  description: Complete reference of the ``mysqldump`` client utility documentation.
  link: https://dev.mysql.com/doc/refman/8.0/en/mysqldump.html
- name: CREATE DATABASE reference
  description: Complete reference of the CREATE DATABASE command documentation.
  link: https://dev.mysql.com/doc/refman/8.0/en/create-database.html
- name: DROP DATABASE reference
  description: Complete reference of the DROP DATABASE command documentation.
  link: https://dev.mysql.com/doc/refman/8.0/en/drop-database.html
author: "Ansible Core Team"
requirements:
   - mysql (command line binary)
   - mysqldump (command line binary)
notes:
   - Requires the mysql and mysqldump binaries on the remote host.
   - This module is B(not idempotent) when I(state) is C(import),
     and will import the dump file each time if run more than once.
extends_documentation_fragment: mysql
'''

EXAMPLES = r'''
- name: Create a new database with name 'bobdata'
  mysql_db:
    name: bobdata
    state: present

- name: Create new databases with names 'foo' and 'bar'
  mysql_db:
    name:
      - foo
      - bar
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

- name: Restore database ignoring errors
  mysql_db:
    name: my_db
    state: import
    target: /tmp/dump.sql.bz2
    force: yes

- name: Dump multiple databases
  mysql_db:
    state: dump
    name: db_1,db_2
    target: /tmp/dump.sql

- name: Dump multiple databases
  mysql_db:
    state: dump
    name:
      - db_1
      - db_2
    target: /tmp/dump.sql

- name: Dump all databases to hostname.sql
  mysql_db:
    state: dump
    name: all
    target: /tmp/dump.sql

- name: Dump all databases to hostname.sql including master data
  mysql_db:
    state: dump
    name: all
    target: /tmp/dump.sql
    master_data: 1

# Import of sql script with encoding option
- name: >
    Import dump.sql with specific latin1 encoding,
    similar to mysql -u <username> --default-character-set=latin1 -p <password> < dump.sql
  mysql_db:
    state: import
    name: all
    encoding: latin1
    target: /tmp/dump.sql

# Dump of database with encoding option
- name: >
    Dump of Databse with specific latin1 encoding,
    similar to mysqldump -u <username> --default-character-set=latin1 -p <password> <database>
  mysql_db:
    state: dump
    name: db_1
    encoding: latin1
    target: /tmp/dump.sql

- name: Delete database with name 'bobdata'
  mysql_db:
    name: bobdata
    state: absent

- name: Make sure there is neither a database with name 'foo', nor one with name 'bar'
  mysql_db:
    name:
      - foo
      - bar
    state: absent

# Dump database with argument not directly supported by this module
# using dump_extra_args parameter
- name: Dump databases without including triggers
  mysql_db:
    state: dump
    name: foo
    target: /tmp/dump.sql
    dump_extra_args: --skip-triggers
'''

RETURN = r'''
db:
  description: Database names in string format delimited by white space.
  returned: always
  type: str
  sample: "foo bar"
db_list:
  description: List of database names.
  returned: always
  type: list
  sample: ["foo", "bar"]
  version_added: '2.9'
executed_commands:
  description: List of commands which tried to run.
  returned: if executed
  type: list
  sample: ["CREATE DATABASE acme"]
  version_added: '2.10'
'''

import os
import subprocess
import traceback

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.database import mysql_quote_identifier
from ansible.module_utils.mysql import mysql_connect, mysql_driver, mysql_driver_fail_msg
from ansible.module_utils.six.moves import shlex_quote
from ansible.module_utils._text import to_native

executed_commands = []

# ===========================================
# MySQL module specific support methods.
#


def db_exists(cursor, db):
    res = 0
    for each_db in db:
        res += cursor.execute("SHOW DATABASES LIKE %s", (each_db.replace("_", r"\_"),))
    return res == len(db)


def db_delete(cursor, db):
    if not db:
        return False
    for each_db in db:
        query = "DROP DATABASE %s" % mysql_quote_identifier(each_db, 'database')
        executed_commands.append(query)
        cursor.execute(query)
    return True


def db_dump(module, host, user, password, db_name, target, all_databases, port,
            config_file, socket=None, ssl_cert=None, ssl_key=None, ssl_ca=None,
            single_transaction=None, quick=None, ignore_tables=None, hex_blob=None,
            encoding=None, force=False, master_data=0, skip_lock_tables=False, dump_extra_args=None):
    cmd = module.get_bin_path('mysqldump', True)
    # If defined, mysqldump demands --defaults-extra-file be the first option
    if config_file:
        cmd += " --defaults-extra-file=%s" % shlex_quote(config_file)
    if user is not None:
        cmd += " --user=%s" % shlex_quote(user)
    if password is not None:
        cmd += " --password=%s" % shlex_quote(password)
    if ssl_cert is not None:
        cmd += " --ssl-cert=%s" % shlex_quote(ssl_cert)
    if ssl_key is not None:
        cmd += " --ssl-key=%s" % shlex_quote(ssl_key)
    if ssl_ca is not None:
        cmd += " --ssl-ca=%s" % shlex_quote(ssl_ca)
    if force:
        cmd += " --force"
    if socket is not None:
        cmd += " --socket=%s" % shlex_quote(socket)
    else:
        cmd += " --host=%s --port=%i" % (shlex_quote(host), port)

    if all_databases:
        cmd += " --all-databases"
    elif len(db_name) > 1:
        cmd += " --databases {0}".format(' '.join(db_name))
    else:
        cmd += " %s" % shlex_quote(' '.join(db_name))

    if skip_lock_tables:
        cmd += " --skip-lock-tables"
    if (encoding is not None) and (encoding != ""):
        cmd += " --default-character-set=%s" % shlex_quote(encoding)
    if single_transaction:
        cmd += " --single-transaction=true"
    if quick:
        cmd += " --quick"
    if ignore_tables:
        for an_ignored_table in ignore_tables:
            cmd += " --ignore-table={0}".format(an_ignored_table)
    if hex_blob:
        cmd += " --hex-blob"
    if master_data:
        cmd += " --master-data=%s" % master_data
    if dump_extra_args is not None:
        cmd += " " + dump_extra_args

    path = None
    if os.path.splitext(target)[-1] == '.gz':
        path = module.get_bin_path('gzip', True)
    elif os.path.splitext(target)[-1] == '.bz2':
        path = module.get_bin_path('bzip2', True)
    elif os.path.splitext(target)[-1] == '.xz':
        path = module.get_bin_path('xz', True)

    if path:
        cmd = '%s | %s > %s' % (cmd, path, shlex_quote(target))
    else:
        cmd += " > %s" % shlex_quote(target)

    executed_commands.append(cmd)
    rc, stdout, stderr = module.run_command(cmd, use_unsafe_shell=True)
    return rc, stdout, stderr


def db_import(module, host, user, password, db_name, target, all_databases, port, config_file,
              socket=None, ssl_cert=None, ssl_key=None, ssl_ca=None, encoding=None, force=False):
    if not os.path.exists(target):
        return module.fail_json(msg="target %s does not exist on the host" % target)

    cmd = [module.get_bin_path('mysql', True)]
    # --defaults-file must go first, or errors out
    if config_file:
        cmd.append("--defaults-extra-file=%s" % shlex_quote(config_file))
    if user:
        cmd.append("--user=%s" % shlex_quote(user))
    if password:
        cmd.append("--password=%s" % shlex_quote(password))
    if ssl_cert is not None:
        cmd.append("--ssl-cert=%s" % shlex_quote(ssl_cert))
    if ssl_key is not None:
        cmd.append("--ssl-key=%s" % shlex_quote(ssl_key))
    if ssl_ca is not None:
        cmd.append("--ssl-ca=%s" % shlex_quote(ssl_ca))
    if force:
        cmd.append("-f")
    if socket is not None:
        cmd.append("--socket=%s" % shlex_quote(socket))
    else:
        cmd.append("--host=%s" % shlex_quote(host))
        cmd.append("--port=%i" % port)
    if (encoding is not None) and (encoding != ""):
        cmd.append("--default-character-set=%s" % shlex_quote(encoding))
    if not all_databases:
        cmd.append("--one-database")
        cmd.append(shlex_quote(''.join(db_name)))

    comp_prog_path = None
    if os.path.splitext(target)[-1] == '.gz':
        comp_prog_path = module.get_bin_path('gzip', required=True)
    elif os.path.splitext(target)[-1] == '.bz2':
        comp_prog_path = module.get_bin_path('bzip2', required=True)
    elif os.path.splitext(target)[-1] == '.xz':
        comp_prog_path = module.get_bin_path('xz', required=True)
    if comp_prog_path:
        # The line above is for returned data only:
        executed_commands.append('%s -dc %s | %s' % (comp_prog_path, target, ' '.join(cmd)))
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
        cmd += " < %s" % shlex_quote(target)
        executed_commands.append(cmd)
        rc, stdout, stderr = module.run_command(cmd, use_unsafe_shell=True)
        return rc, stdout, stderr


def db_create(cursor, db, encoding, collation):
    if not db:
        return False
    query_params = dict(enc=encoding, collate=collation)
    res = 0
    for each_db in db:
        query = ['CREATE DATABASE %s' % mysql_quote_identifier(each_db, 'database')]
        if encoding:
            query.append("CHARACTER SET %(enc)s")
        if collation:
            query.append("COLLATE %(collate)s")
        query = ' '.join(query)
        res += cursor.execute(query, query_params)
        try:
            executed_commands.append(cursor.mogrify(query, query_params))
        except AttributeError:
            executed_commands.append(cursor._executed)
        except Exception:
            executed_commands.append(query)
    return res > 0


# ===========================================
# Module execution.
#


def main():
    module = AnsibleModule(
        argument_spec=dict(
            login_user=dict(type='str'),
            login_password=dict(type='str', no_log=True),
            login_host=dict(type='str', default='localhost'),
            login_port=dict(type='int', default=3306),
            login_unix_socket=dict(type='str'),
            name=dict(type='list', required=True, aliases=['db']),
            encoding=dict(type='str', default=''),
            collation=dict(type='str', default=''),
            target=dict(type='path'),
            state=dict(type='str', default='present', choices=['absent', 'dump', 'import', 'present']),
            client_cert=dict(type='path', aliases=['ssl_cert']),
            client_key=dict(type='path', aliases=['ssl_key']),
            ca_cert=dict(type='path', aliases=['ssl_ca']),
            connect_timeout=dict(type='int', default=30),
            config_file=dict(type='path', default='~/.my.cnf'),
            single_transaction=dict(type='bool', default=False),
            quick=dict(type='bool', default=True),
            ignore_tables=dict(type='list', default=[]),
            hex_blob=dict(default=False, type='bool'),
            force=dict(type='bool', default=False),
            master_data=dict(type='int', default=0, choices=[0, 1, 2]),
            skip_lock_tables=dict(type='bool', default=False),
            dump_extra_args=dict(type='str'),
        ),
        supports_check_mode=True,
    )

    if mysql_driver is None:
        module.fail_json(msg=mysql_driver_fail_msg)

    db = module.params["name"]
    if not db:
        module.exit_json(changed=False, db=db, db_list=[])
    db = [each_db.strip() for each_db in db]

    encoding = module.params["encoding"]
    collation = module.params["collation"]
    state = module.params["state"]
    target = module.params["target"]
    socket = module.params["login_unix_socket"]
    login_port = module.params["login_port"]
    if login_port < 0 or login_port > 65535:
        module.fail_json(msg="login_port must be a valid unix port number (0-65535)")
    ssl_cert = module.params["client_cert"]
    ssl_key = module.params["client_key"]
    ssl_ca = module.params["ca_cert"]
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
    hex_blob = module.params["hex_blob"]
    force = module.params["force"]
    master_data = module.params["master_data"]
    skip_lock_tables = module.params["skip_lock_tables"]
    dump_extra_args = module.params["dump_extra_args"]

    if len(db) > 1 and state == 'import':
        module.fail_json(msg="Multiple databases are not supported with state=import")
    db_name = ' '.join(db)

    all_databases = False
    if state in ['dump', 'import']:
        if target is None:
            module.fail_json(msg="with state=%s target is required" % state)
        if db == ['all']:
            all_databases = True
    else:
        if db == ['all']:
            module.fail_json(msg="name is not allowed to equal 'all' unless state equals import, or dump.")
    try:
        cursor, db_conn = mysql_connect(module, login_user, login_password, config_file, ssl_cert, ssl_key, ssl_ca,
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

    existence_list = []
    non_existence_list = []

    if not all_databases:
        for each_database in db:
            if db_exists(cursor, [each_database]):
                existence_list.append(each_database)
            else:
                non_existence_list.append(each_database)

    if state == "absent":
        if module.check_mode:
            module.exit_json(changed=bool(existence_list), db=db_name, db_list=db)
        try:
            changed = db_delete(cursor, existence_list)
        except Exception as e:
            module.fail_json(msg="error deleting database: %s" % to_native(e))
        module.exit_json(changed=changed, db=db_name, db_list=db, executed_commands=executed_commands)
    elif state == "present":
        if module.check_mode:
            module.exit_json(changed=bool(non_existence_list), db=db_name, db_list=db)
        changed = False
        if non_existence_list:
            try:
                changed = db_create(cursor, non_existence_list, encoding, collation)
            except Exception as e:
                module.fail_json(msg="error creating database: %s" % to_native(e),
                                 exception=traceback.format_exc())
        module.exit_json(changed=changed, db=db_name, db_list=db, executed_commands=executed_commands)
    elif state == "dump":
        if non_existence_list and not all_databases:
            module.fail_json(msg="Cannot dump database(s) %r - not found" % (', '.join(non_existence_list)))
        if module.check_mode:
            module.exit_json(changed=True, db=db_name, db_list=db)
        rc, stdout, stderr = db_dump(module, login_host, login_user,
                                     login_password, db, target, all_databases,
                                     login_port, config_file, socket, ssl_cert, ssl_key,
                                     ssl_ca, single_transaction, quick, ignore_tables,
                                     hex_blob, encoding, force, master_data, skip_lock_tables,
                                     dump_extra_args)
        if rc != 0:
            module.fail_json(msg="%s" % stderr)
        module.exit_json(changed=True, db=db_name, db_list=db, msg=stdout,
                         executed_commands=executed_commands)
    elif state == "import":
        if module.check_mode:
            module.exit_json(changed=True, db=db_name, db_list=db)
        if non_existence_list and not all_databases:
            try:
                db_create(cursor, non_existence_list, encoding, collation)
            except Exception as e:
                module.fail_json(msg="error creating database: %s" % to_native(e),
                                 exception=traceback.format_exc())
        rc, stdout, stderr = db_import(module, login_host, login_user,
                                       login_password, db, target,
                                       all_databases,
                                       login_port, config_file,
                                       socket, ssl_cert, ssl_key, ssl_ca, encoding, force)
        if rc != 0:
            module.fail_json(msg="%s" % stderr)
        module.exit_json(changed=True, db=db_name, db_list=db, msg=stdout,
                         executed_commands=executed_commands)


if __name__ == '__main__':
    main()
