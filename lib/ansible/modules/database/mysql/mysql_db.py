#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2012, Mark Theunissen <mark.theunissen@gmail.com>
# Sponsored by Four Kitchens http://fourkitchens.com.
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
    default: null
    aliases: [ db ]
  login_user:
    description:
      - The username used to authenticate with
    required: false
    default: null
  login_password:
    description:
      - The password used to authenticate with
    required: false
    default: null
  login_host:
    description:
      - Host running the database
    required: false
    default: localhost
  login_port:
    description:
      - Port of the MySQL server. Requires login_host be defined as other then localhost if login_port is used
    required: false
    default: 3306
  login_unix_socket:
    description:
      - The path to a Unix domain socket for local connections
    required: false
    default: null
  state:
    description:
      - The database state
    required: false
    default: present
    choices: [ "present", "absent", "dump", "import" ]
  collation:
    description:
      - Collation mode
    required: false
    default: null
  encoding:
    description:
      - Encoding mode
    required: false
    default: null
  target:
    description:
      - Location, on the remote host, of the dump file to read from or write to. Uncompressed SQL
        files (C(.sql)) as well as bzip2 (C(.bz2)), gzip (C(.gz)) and xz compressed files are supported.
    required: false
notes:
   - Requires the MySQLdb Python package on the remote host. For Ubuntu, this
     is as easy as apt-get install python-mysqldb. (See M(apt).)
   - Both I(login_password) and I(login_user) are required when you are
     passing credentials. If none are present, the module will attempt to read
     the credentials from C(~/.my.cnf), and finally fall back to using the MySQL
     default login of C(root) with no password.
requirements: [ ConfigParser ]
author: "Mark Theunissen (@marktheunissen)"
'''

EXAMPLES = '''
# Create a new database with name 'bobdata'
- mysql_db: name=bobdata state=present

# Copy database dump file to remote host and restore it to database 'my_db'
- copy: src=dump.sql.bz2 dest=/tmp
- mysql_db: name=my_db state=import target=/tmp/dump.sql.bz2

# Dumps all databases to hostname.sql
- mysql_db: state=dump name=all target=/tmp/{{ inventory_hostname }}.sql

# Imports file.sql similiar to mysql -u <username> -p <password> < hostname.sql
- mysql_db: state=import name=all target=/tmp/{{ inventory_hostname }}.sql
'''

import ConfigParser
import os
import pipes
import stat
import subprocess
try:
    import MySQLdb
except ImportError:
    mysqldb_found = False
else:
    mysqldb_found = True

# ===========================================
# MySQL module specific support methods.
#

def db_exists(cursor, db):
    res = cursor.execute("SHOW DATABASES LIKE %s", (db.replace("_","\_"),))
    return bool(res)

def db_delete(cursor, db):
    query = "DROP DATABASE %s" % mysql_quote_identifier(db, 'database')
    cursor.execute(query)
    return True

def db_dump(module, host, user, password, db_name, target, all_databases, port, socket=None):
    cmd = module.get_bin_path('mysqldump', True)
    cmd += " --quick --user=%s --password=%s" % (pipes.quote(user), pipes.quote(password))
    if socket is not None:
        cmd += " --socket=%s" % pipes.quote(socket)
    else:
        cmd += " --host=%s --port=%i" % (pipes.quote(host), port)
    if all_databases:
        cmd += " --all-databases"
    else:
        cmd += " %s" % pipes.quote(db_name)

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

def db_import(module, host, user, password, db_name, target, all_databases, port, socket=None):
    if not os.path.exists(target):
        return module.fail_json(msg="target %s does not exist on the host" % target)

    cmd = [module.get_bin_path('mysql', True)]
    if user:
        cmd.append("--user=%s" % pipes.quote(user))
    if password:
        cmd.append("--password=%s" % pipes.quote(password))
    if socket is not None:
        cmd.append("--socket=%s" % pipes.quote(socket))
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
    res = cursor.execute(query, query_params)
    return True

def strip_quotes(s):
    """ Remove surrounding single or double quotes

    >>> print strip_quotes('hello')
    hello
    >>> print strip_quotes('"hello"')
    hello
    >>> print strip_quotes("'hello'")
    hello
    >>> print strip_quotes("'hello")
    'hello

    """
    single_quote = "'"
    double_quote = '"'

    if s.startswith(single_quote) and s.endswith(single_quote):
        s = s.strip(single_quote)
    elif s.startswith(double_quote) and s.endswith(double_quote):
        s = s.strip(double_quote)
    return s


def config_get(config, section, option):
    """ Calls ConfigParser.get and strips quotes

    See: http://dev.mysql.com/doc/refman/5.0/en/option-files.html
    """
    return strip_quotes(config.get(section, option))


def load_mycnf():
    config = ConfigParser.RawConfigParser()
    mycnf = os.path.expanduser('~/.my.cnf')
    if not os.path.exists(mycnf):
        return False
    try:
        config.readfp(open(mycnf))
    except (IOError):
        return False
    # We support two forms of passwords in .my.cnf, both pass= and password=,
    # as these are both supported by MySQL.
    try:
        passwd = config_get(config, 'client', 'password')
    except (ConfigParser.NoOptionError):
        try:
            passwd = config_get(config, 'client', 'pass')
        except (ConfigParser.NoOptionError):
            return False
    try:
        creds = dict(user=config_get(config, 'client', 'user'),passwd=passwd)
    except (ConfigParser.NoOptionError):
        return False
    return creds

# ===========================================
# Module execution.
#

def main():
    module = AnsibleModule(
        argument_spec = dict(
            login_user=dict(default=None),
            login_password=dict(default=None),
            login_host=dict(default="localhost"),
            login_port=dict(default=3306, type='int'),
            login_unix_socket=dict(default=None),
            name=dict(required=True, aliases=['db']),
            encoding=dict(default=""),
            collation=dict(default=""),
            target=dict(default=None),
            state=dict(default="present", choices=["absent", "present","dump", "import"]),
        )
    )

    if not mysqldb_found:
        module.fail_json(msg="the python mysqldb module is required")

    db = module.params["name"]
    encoding = module.params["encoding"]
    collation = module.params["collation"]
    state = module.params["state"]
    target = module.params["target"]
    socket = module.params["login_unix_socket"]
    login_port = module.params["login_port"]
    if login_port < 0 or login_port > 65535:
        module.fail_json(msg="login_port must be a valid unix port number (0-65535)")

    # make sure the target path is expanded for ~ and $HOME
    if target is not None:
        target = os.path.expandvars(os.path.expanduser(target))

    # Either the caller passes both a username and password with which to connect to
    # mysql, or they pass neither and allow this module to read the credentials from
    # ~/.my.cnf.
    login_password = module.params["login_password"]
    login_user = module.params["login_user"]
    if login_user is None and login_password is None:
        mycnf_creds = load_mycnf()
        if mycnf_creds is False:
            login_user = "root"
            login_password = ""
        else:
            login_user = mycnf_creds["user"]
            login_password = mycnf_creds["passwd"]
    elif login_password is None or login_user is None:
        module.fail_json(msg="when supplying login arguments, both login_user and login_password must be provided")
    login_host = module.params["login_host"]

    if state in ['dump','import']:
        if target is None:
            module.fail_json(msg="with state=%s target is required" % (state))
	if db == 'all':
            connect_to_db = 'mysql'
            db = 'mysql'
            all_databases = True
        else:
            connect_to_db = db
            all_databases = False
    else:
        if db == 'all':
            module.fail_json(msg="name is not allowed to equal 'all' unless state equals import, or dump.")
        connect_to_db = ''
    try:
        if socket:
            try:
                socketmode = os.stat(socket).st_mode
                if not stat.S_ISSOCK(socketmode):
                    module.fail_json(msg="%s, is not a socket, unable to connect" % socket)
            except OSError:
                module.fail_json(msg="%s, does not exist, unable to connect" % socket)
            db_connection = MySQLdb.connect(host=module.params["login_host"], unix_socket=socket, user=login_user, passwd=login_password, db=connect_to_db)
        elif login_port != 3306 and module.params["login_host"] == "localhost":
            module.fail_json(msg="login_host is required when login_port is defined, login_host cannot be localhost when login_port is defined")
        else:
            db_connection = MySQLdb.connect(host=module.params["login_host"], port=login_port, user=login_user, passwd=login_password, db=connect_to_db)
        cursor = db_connection.cursor()
    except Exception, e:
        errno, errstr = e.args
        if "Unknown database" in str(e):
                module.fail_json(msg="ERROR: %s %s" % (errno, errstr))
        else:
                module.fail_json(msg="unable to connect, check login credentials (login_user, and login_password, which can be defined in ~/.my.cnf), check that mysql socket exists and mysql server is running (ERROR: %s %s)" % (errno, errstr))

    changed = False
    if db_exists(cursor, db):
        if state == "absent":
            try:
                changed = db_delete(cursor, db)
            except Exception, e:
                module.fail_json(msg="error deleting database: " + str(e))
        elif state == "dump":
            rc, stdout, stderr = db_dump(module, login_host, login_user, 
                                        login_password, db, target, all_databases,
                                        port=login_port,
                                        socket=module.params['login_unix_socket'])
            if rc != 0:
                module.fail_json(msg="%s" % stderr)
            else:
                module.exit_json(changed=True, db=db, msg=stdout)
        elif state == "import":
            rc, stdout, stderr = db_import(module, login_host, login_user, 
                                        login_password, db, target, all_databases,
                                        port=login_port,
                                        socket=module.params['login_unix_socket'])
            if rc != 0:
                module.fail_json(msg="%s" % stderr)
            else:
                module.exit_json(changed=True, db=db, msg=stdout)
    else:
        if state == "present":
            try:
                changed = db_create(cursor, db, encoding, collation)
            except Exception, e:
                module.fail_json(msg="error creating database: " + str(e))

    module.exit_json(changed=changed, db=db)

# import module snippets
from ansible.module_utils.basic import *
from ansible.module_utils.database import *
if __name__ == '__main__':
    main()
