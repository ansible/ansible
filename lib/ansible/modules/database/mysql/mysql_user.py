#!/usr/bin/python

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
module: mysql_user
short_description: Adds or removes a user from a MySQL database.
description:
   - Adds or removes a user from a MySQL database.
version_added: "0.6"
options:
  name:
    description:
      - name of the user (role) to add or remove
    required: true
    default: null
  user_anonymous:
    description:
      - username is to be ignored and anonymous users with no username
        handled
    required: false
    choices: [ "yes", "no" ]
    default: no
  password:
    description:
      - set the user's password. (Required when adding a user)
    required: false
    default: null
  encrypted:
    description:
      - Indicate that the 'password' field is a `mysql_native_password` hash
    required: false
    choices: [ "yes", "no" ]
    default: "no"
    version_added: "2.0"
  host:
    description:
      - the 'host' part of the MySQL username
    required: false
    default: localhost
  host_all:
    description:
      - override the host option, making ansible apply changes to
        all hostnames for a given user.  This option cannot be used
        when creating users
    required: false
    choices: [ "yes", "no" ]
    default: "no"
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
      - Port of the MySQL server
    required: false
    default: 3306
    version_added: '1.4'
  login_unix_socket:
    description:
      - The path to a Unix domain socket for local connections
    required: false
    default: null
  priv:
    description:
      - "MySQL privileges string in the format: C(db.table:priv1,priv2)"
    required: false
    default: null
  append_privs:
    description:
      - Append the privileges defined by priv to the existing ones for this
        user instead of overwriting existing ones.
    required: false
    choices: [ "yes", "no" ]
    default: "no"
    version_added: "1.4"
  state:
    description:
      - Whether the user should exist.  When C(absent), removes
        the user.
    required: false
    default: present
    choices: [ "present", "absent" ]
  check_implicit_admin:
    description:
      - Check if mysql allows login as root/nopassword before trying supplied credentials.
    required: false
    choices: [ "yes", "no" ]
    default: "no"
    version_added: "1.3"
  update_password:
    required: false
    default: always
    choices: ['always', 'on_create']
    version_added: "1.9"
    description:
      - C(always) will update passwords if they differ.  C(on_create) will only set the password for newly created users.
  config_file:
    description:
      - Specify a config file from which user and password are to be read 
    required: false
    default: null
    version_added: "1.8"
notes:
   - Requires the MySQLdb Python package on the remote host. For Ubuntu, this
     is as easy as apt-get install python-mysqldb.
   - Both C(login_password) and C(login_user) are required when you are
     passing credentials. If none are present, the module will attempt to read
     the credentials from C(~/.my.cnf), and finally fall back to using the MySQL
     default login of 'root' with no password.
   - "MySQL server installs with default login_user of 'root' and no password. To secure this user
     as part of an idempotent playbook, you must create at least two tasks: the first must change the root user's password,
     without providing any login_user/login_password details. The second must drop a ~/.my.cnf file containing
     the new root credentials. Subsequent runs of the playbook will then succeed by reading the new credentials from
     the file."
   - Currently, there is only support for the `mysql_native_password` encryted password hash module.

requirements: [ "MySQLdb" ]
author: "Jonathan Mainguy (@Jmainguy)"
'''

EXAMPLES = """
# Removes anonymous user account for localhost (the name parameter is required, but ignored)
- mysql_user: name=anonymous user_anonymous=yes host=localhost state=absent

# Removes all anonymous user accounts
- mysql_user: name=anonymous user_anonymous=yes host_all=yes state=absent

# Create database user with name 'bob' and password '12345' with all database privileges
- mysql_user: name=bob password=12345 priv=*.*:ALL state=present

# Create database user with name 'bob' and previously hashed mysql native password '*EE0D72C1085C46C5278932678FBE2C6A782821B4' with all database privileges
- mysql_user: name=bob password='*EE0D72C1085C46C5278932678FBE2C6A782821B4' encrypted=yes priv=*.*:ALL state=present

# Creates database user 'bob' and password '12345' with all database privileges and 'WITH GRANT OPTION'
- mysql_user: name=bob password=12345 priv=*.*:ALL,GRANT state=present

# Modifiy user Bob to require SSL connections. Note that REQUIRESSL is a special privilege that should only apply to *.* by itself.
- mysql_user: name=bob append_privs=true priv=*.*:REQUIRESSL state=present

# Ensure no user named 'sally'@'localhost' exists, also passing in the auth credentials.
- mysql_user: login_user=root login_password=123456 name=sally state=absent

# Ensure no user named 'sally' exists at all
- mysql_user: name=sally host_all=yes state=absent

# Specify grants composed of more than one word
- mysql_user: name=replication password=12345 priv=*.*:"REPLICATION CLIENT" state=present

# Revoke all privileges for user 'bob' and password '12345'
- mysql_user: name=bob password=12345 priv=*.*:USAGE state=present

# Example privileges string format
mydb.*:INSERT,UPDATE/anotherdb.*:SELECT/yetanotherdb.*:ALL

# Example using login_unix_socket to connect to server
- mysql_user: name=root password=abc123 login_unix_socket=/var/run/mysqld/mysqld.sock

# Example .my.cnf file for setting the root password

[client]
user=root
password=n<_665{vS43y
"""

import getpass
import tempfile
import re
import string
try:
    import MySQLdb
except ImportError:
    mysqldb_found = False
else:
    mysqldb_found = True

VALID_PRIVS = frozenset(('CREATE', 'DROP', 'GRANT', 'GRANT OPTION',
                         'LOCK TABLES', 'REFERENCES', 'EVENT', 'ALTER',
                         'DELETE', 'INDEX', 'INSERT', 'SELECT', 'UPDATE',
                         'CREATE TEMPORARY TABLES', 'TRIGGER', 'CREATE VIEW',
                         'SHOW VIEW', 'ALTER ROUTINE', 'CREATE ROUTINE',
                         'EXECUTE', 'FILE', 'CREATE TABLESPACE', 'CREATE USER',
                         'PROCESS', 'PROXY', 'RELOAD', 'REPLICATION CLIENT',
                         'REPLICATION SLAVE', 'SHOW DATABASES', 'SHUTDOWN',
                         'SUPER', 'ALL', 'ALL PRIVILEGES', 'USAGE', 'REQUIRESSL'))

class InvalidPrivsError(Exception):
    pass

# ===========================================
# MySQL module specific support methods.
#

def connect(module, login_user=None, login_password=None, config_file=''):
    config = {
        'host': module.params['login_host'],
        'db': 'mysql'
    }

    if module.params['login_unix_socket']:
        config['unix_socket'] = module.params['login_unix_socket']
    else:
        config['port'] = module.params['login_port']

    if os.path.exists(config_file):
        config['read_default_file'] = config_file
    else:
        config['user'] = login_user
        config['passwd'] = login_password
        
    db_connection = MySQLdb.connect(**config)
    return db_connection.cursor()

def user_exists(cursor, user, host, host_all):
    if host_all:
        cursor.execute("SELECT count(*) FROM user WHERE user = %s", user)
    else:
        cursor.execute("SELECT count(*) FROM user WHERE user = %s AND host = %s", (user,host))

    count = cursor.fetchone()
    return count[0] > 0

def user_add(cursor, user, host, host_all, password, new_priv):
    # we cannot create users without a proper hostname
    if host_all:
        return False

    cursor.execute("CREATE USER %s@%s IDENTIFIED BY %s", (user,host,password))
    if new_priv is not None:
        for db_table, priv in new_priv.iteritems():
            privileges_grant(cursor, user,host,db_table,priv)
    return True

def is_hash(password):
    ishash = False
    if len(password) == 41 and password[0] == '*':
        if frozenset(password[1:]).issubset(string.hexdigits):
            ishash = True
    return ishash

def user_mod(cursor, user, host, password, encrypted, new_priv, append_privs):
    changed = False
    grant_option = False

    # Handle clear text and hashed passwords.
    if bool(password):
        # Determine what user management method server uses
        old_user_mgmt = server_version_check(cursor)

    # to simplify code, if we have a specific host and no host_all, we create
    # a list with just host and loop over that
    if host_all:
        hostnames = user_get_hostnames(cursor, user)
    else:
        hostnames = [host]

    for host in hostnames:
        # Handle passwords
        if password is not None:
            cursor.execute("SELECT password FROM user WHERE user = %s AND host = %s", (user,host))
        else:
            cursor.execute("SELECT authentication_string FROM user WHERE user = %s AND host = %s", (user,host))
        current_pass_hash = cursor.fetchone()

        if encrypted:
            encrypted_string = (password)
            if is_hash(password):
                if current_pass_hash[0] != encrypted_string:
                    if old_user_mgmt:
                        cursor.execute("SET PASSWORD FOR %s@%s = %s", (user, host, password))
                    else:
                        cursor.execute("ALTER USER %s@%s IDENTIFIED WITH mysql_native_password AS %s", (user, host, password))
                    changed = True
            else:
                module.fail_json(msg="encrypted was specified however it does not appear to be a valid hash expecting: *SHA1(SHA1(your_password))")
        else:
            if old_user_mgmt:
                cursor.execute("SELECT PASSWORD(%s)", (password,))
            else:
                cursor.execute("SELECT CONCAT('*', UCASE(SHA1(UNHEX(SHA1(%s)))))", (password,))
            new_pass_hash = cursor.fetchone()
            if current_pass_hash[0] != new_pass_hash[0]:
                cursor.execute("SET PASSWORD FOR %s@%s = PASSWORD(%s)", (user,host,password))
                changed = True


    # Handle privileges
    if new_priv is not None:
        curr_priv = privileges_get(cursor, user,host)

        # If the user has privileges on a db.table that doesn't appear at all in
        # the new specification, then revoke all privileges on it.
        for db_table, priv in curr_priv.iteritems():
            # If the user has the GRANT OPTION on a db.table, revoke it first.
            if "GRANT" in priv:
                grant_option = True
            if db_table not in new_priv:
                if user != "root" and "PROXY" not in priv and not append_privs:
                    privileges_revoke(cursor, user,host,db_table,priv,grant_option)
                    changed = True

            # If the db.table specification exists in both the user's current privileges
            # and in the new privileges, then we need to see if there's a difference.
            db_table_intersect = set(new_priv.keys()) & set(curr_priv.keys())
            for db_table in db_table_intersect:
                priv_diff = set(new_priv[db_table]) ^ set(curr_priv[db_table])
                if (len(priv_diff) > 0):
                    if not append_privs:
                        privileges_revoke(cursor, user,host,db_table,curr_priv[db_table],grant_option)
                    privileges_grant(cursor, user,host,db_table,new_priv[db_table])
                    changed = True

    return changed

def user_delete(cursor, user, host, host_all):
    if host_all:
        hostnames = user_get_hostnames(cursor, user)

        for hostname in hostnames:
            cursor.execute("DROP USER %s@%s", (user, hostname))
    else:
        cursor.execute("DROP USER %s@%s", (user, host))

    return True

def user_get_hostnames(cursor, user):
    cursor.execute("SELECT Host FROM mysql.user WHERE user = %s", user)
    hostnames_raw = cursor.fetchall()
    hostnames = []

    for hostname_raw in hostnames_raw:
        hostnames.append(hostname_raw[0])

    return hostnames

def privileges_get(cursor, user,host):
    """ MySQL doesn't have a better method of getting privileges aside from the
    SHOW GRANTS query syntax, which requires us to then parse the returned string.
    Here's an example of the string that is returned from MySQL:

     GRANT USAGE ON *.* TO 'user'@'localhost' IDENTIFIED BY 'pass';

    This function makes the query and returns a dictionary containing the results.
    The dictionary format is the same as that returned by privileges_unpack() below.
    """
    output = {}
    cursor.execute("SHOW GRANTS FOR %s@%s", (user, host))
    grants = cursor.fetchall()

    def pick(x):
        if x == 'ALL PRIVILEGES':
            return 'ALL'
        else:
            return x

    for grant in grants:
        res = re.match("GRANT (.+) ON (.+) TO '.*'@'.+'( IDENTIFIED BY PASSWORD '.+')? ?(.*)", grant[0])
        if res is None:
            raise InvalidPrivsError('unable to parse the MySQL grant string: %s' % grant[0])
        privileges = res.group(1).split(", ")
        privileges = [ pick(x) for x in privileges]
        if "WITH GRANT OPTION" in res.group(4):
            privileges.append('GRANT')
        if "REQUIRE SSL" in res.group(4):
            privileges.append('REQUIRESSL')
        db = res.group(2)
        output[db] = privileges
    return output

def privileges_unpack(priv):
    """ Take a privileges string, typically passed as a parameter, and unserialize
    it into a dictionary, the same format as privileges_get() above. We have this
    custom format to avoid using YAML/JSON strings inside YAML playbooks. Example
    of a privileges string:

     mydb.*:INSERT,UPDATE/anotherdb.*:SELECT/yetanother.*:ALL

    The privilege USAGE stands for no privileges, so we add that in on *.* if it's
    not specified in the string, as MySQL will always provide this by default.
    """
    output = {}
    privs = []
    for item in priv.strip().split('/'):
        pieces = item.strip().split(':')
        dbpriv = pieces[0].rsplit(".", 1)
        # Do not escape if privilege is for database '*' (all databases)
        if dbpriv[0].strip('`') != '*':
            pieces[0] = "`%s`.%s" % (dbpriv[0].strip('`'), dbpriv[1])

        if '(' in pieces[1]:
            output[pieces[0]] = re.split(r',\s*(?=[^)]*(?:\(|$))', pieces[1].upper())
            for i in output[pieces[0]]:
                privs.append(re.sub(r'\(.*\)','',i))
        else:
            output[pieces[0]] = pieces[1].upper().split(',')
            privs = output[pieces[0]]
        new_privs = frozenset(privs)
        if not new_privs.issubset(VALID_PRIVS):
            raise InvalidPrivsError('Invalid privileges specified: %s' % new_privs.difference(VALID_PRIVS))

    if '*.*' not in output:
        output['*.*'] = ['USAGE']

    # if we are only specifying something like REQUIRESSL in *.* we still need
    # to add USAGE as a privilege to avoid syntax errors
    if priv.find('REQUIRESSL') != -1 and 'USAGE' not in output['*.*']:
        output['*.*'].append('USAGE')

    return output

def privileges_revoke(cursor, user,host,db_table,priv,grant_option):
    # Escape '%' since mysql db.execute() uses a format string
    db_table = db_table.replace('%', '%%')
    if grant_option:
        query = ["REVOKE GRANT OPTION ON %s" % mysql_quote_identifier(db_table, 'table')]
        query.append("FROM %s@%s")
        query = ' '.join(query)
        cursor.execute(query, (user, host))
    priv_string = ",".join([p for p in priv if p not in ('GRANT', 'REQUIRESSL')])
    query = ["REVOKE %s ON %s" % (priv_string, mysql_quote_identifier(db_table, 'table'))]
    query.append("FROM %s@%s")
    query = ' '.join(query)
    cursor.execute(query, (user, host))

def privileges_grant(cursor, user,host,db_table,priv):
    # Escape '%' since mysql db.execute uses a format string and the
    # specification of db and table often use a % (SQL wildcard)
    db_table = db_table.replace('%', '%%')
    priv_string = ",".join([p for p in priv if p not in ('GRANT', 'REQUIRESSL')])
    query = ["GRANT %s ON %s" % (priv_string, mysql_quote_identifier(db_table, 'table'))]
    query.append("TO %s@%s")
    if 'GRANT' in priv:
        query.append("WITH GRANT OPTION")
    if 'REQUIRESSL' in priv:
        query.append("REQUIRE SSL")
    query = ' '.join(query)
    cursor.execute(query, (user, host))

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
            user=dict(required=True, aliases=['name']),
            user_anonymous=dict(type="bool", default="no"),
            password=dict(default=None, no_log=True),
            encrypted=dict(default=False, type='bool'),
            host=dict(default="localhost"),
            host_all=dict(type="bool", default="no"),
            state=dict(default="present", choices=["absent", "present"]),
            priv=dict(default=None),
            append_privs=dict(default=False, type='bool'),
            check_implicit_admin=dict(default=False, type='bool'),
            update_password=dict(default="always", choices=["always", "on_create"]),
            config_file=dict(default="~/.my.cnf"),
        )
    )
    login_user = module.params["login_user"]
    login_password = module.params["login_password"]
    user = module.params["user"]
    user_anonymous = module.params["user_anonymous"]
    password = module.params["password"]
    encrypted = module.boolean(module.params["encrypted"])
    host = module.params["host"].lower()
    host_all = module.params["host_all"]
    state = module.params["state"]
    priv = module.params["priv"]
    check_implicit_admin = module.params['check_implicit_admin']
    config_file = module.params['config_file']
    append_privs = module.boolean(module.params["append_privs"])
    update_password = module.params['update_password']

    if user_anonymous:
        user = ''

    config_file = os.path.expanduser(os.path.expandvars(config_file))
    if not mysqldb_found:
        module.fail_json(msg="the python mysqldb module is required")

    if priv is not None:
        try:
            priv = privileges_unpack(priv)
        except Exception, e:
            module.fail_json(msg="invalid privileges string: %s" % str(e))

    cursor = None
    try:
        if check_implicit_admin:
            try:
                cursor = connect(module, 'root', '', config_file)
            except:
                pass

        if not cursor:
            cursor = connect(module, login_user, login_password, config_file)
    except Exception, e:
        module.fail_json(msg="unable to connect to database, check login_user and login_password are correct or ~/.my.cnf has the credentials")

    if state == "present":
        if user_exists(cursor, user, host):
            try:
                if update_password == 'always':
                    changed = user_mod(cursor, user, host, password, encrypted, priv, append_privs)
                else:
                    changed = user_mod(cursor, user, host, None, encrypted, priv, append_privs)

            except (SQLParseError, InvalidPrivsError, MySQLdb.Error), e:
                module.fail_json(msg=str(e))
        else:
            if password is None:
                module.fail_json(msg="password parameter required when adding a user")
            if host_all:
                module.fail_json(msg="host_all parameter cannot be used when adding a user")
            try:
                changed = user_add(cursor, user, host, host_all, password, priv)
            except (SQLParseError, InvalidPrivsError, MySQLdb.Error), e:
                module.fail_json(msg=str(e))
    elif state == "absent":
        if user_exists(cursor, user, host, host_all):
            changed = user_delete(cursor, user, host, host_all)
        else:
            changed = False
    module.exit_json(changed=changed, user=user)

# import module snippets
from ansible.module_utils.basic import *
from ansible.module_utils.database import *
if __name__ == '__main__':
    main()
