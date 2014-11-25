#!/usr/bin/python
# -*- coding: utf-8 -*-

"""

Ansible module to manage mysql variables
(c) 2013, Balazs Pocze <banyek@gawker.com>
Certain parts are taken from Mark Theunissen's mysqldb module

This file is part of Ansible

Ansible is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Ansible is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.
You should have received a copy of the GNU General Public License
along with Ansible.  If not, see <http://www.gnu.org/licenses/>.
"""

DOCUMENTATION = '''
---
module: mysql_variables

short_description: Manage MySQL global variables
description:
    - Query / Set MySQL variables
version_added: 1.3
options:
    variable:
        description:
            - Variable name to operate
        required: True
    value:
        description:
            - If set, then sets variable value to this
        required: False
    login_user:
        description:
            - username to connect mysql host, if defined login_password also needed.
        required: False
    login_password:
        description:
            - password to connect mysql host, if defined login_user also needed.
        required: False
    login_host:
        description:
            - mysql host to connect
        required: False
    login_unix_socket:
        description:
            - unix socket to connect mysql server
'''
EXAMPLES = '''
# Check for sync_binlog setting
- mysql_variables: variable=sync_binlog

# Set read_only variable to 1
- mysql_variables: variable=read_only value=1
'''


import ConfigParser
import os
import warnings

try:
    import MySQLdb
except ImportError:
    mysqldb_found = False
else:
    mysqldb_found = True


def typedvalue(value):
    """
    Convert value to number whenever possible, return same value
    otherwise.

    >>> typedvalue('3')
    3
    >>> typedvalue('3.0')
    3.0
    >>> typedvalue('foobar')
    'foobar'

    """
    try:
        return int(value)
    except ValueError:
        pass

    try:
        return float(value)
    except ValueError:
        pass

    return value


def getvariable(cursor, mysqlvar):
    cursor.execute("SHOW VARIABLES LIKE %s", (mysqlvar,))
    mysqlvar_val = cursor.fetchall()
    return mysqlvar_val


def setvariable(cursor, mysqlvar, value):
    """ Set a global mysql variable to a given value

    The DB driver will handle quoting of the given value based on its
    type, thus numeric strings like '3.0' or '8' are illegal, they
    should be passed as numeric literals.

    """
    query = ["SET GLOBAL %s" % mysql_quote_identifier(mysqlvar, 'vars') ]
    query.append(" = %s")
    query = ' '.join(query)
    try:
        cursor.execute(query, (value,))
        cursor.fetchall()
        result = True
    except Exception, e:
        result = str(e)
    return result


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

    # If .my.cnf doesn't specify a user, default to user login name
    try:
        user = config_get(config, 'client', 'user')
    except (ConfigParser.NoOptionError):
        user = getpass.getuser()
    creds = dict(user=user, passwd=passwd)
    return creds


def main():
    module = AnsibleModule(
            argument_spec = dict(
            login_user=dict(default=None),
            login_password=dict(default=None),
            login_host=dict(default="localhost"),
            login_unix_socket=dict(default=None),
            variable=dict(default=None),
            value=dict(default=None)

        )
    )
    user = module.params["login_user"]
    password = module.params["login_password"]
    host = module.params["login_host"]
    mysqlvar = module.params["variable"]
    value = module.params["value"]
    if not mysqldb_found:
        module.fail_json(msg="the python mysqldb module is required")
    else:
        warnings.filterwarnings('error', category=MySQLdb.Warning)

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
    try:
        if module.params["login_unix_socket"]:
            db_connection = MySQLdb.connect(host=module.params["login_host"], unix_socket=module.params["login_unix_socket"], user=login_user, passwd=login_password, db="mysql")
        else:
            db_connection = MySQLdb.connect(host=module.params["login_host"], user=login_user, passwd=login_password, db="mysql")
        cursor = db_connection.cursor()
    except Exception, e:
        module.fail_json(msg="unable to connect to database, check login_user and login_password are correct or ~/.my.cnf has the credentials")
    if mysqlvar is None:
        module.fail_json(msg="Cannot run without variable to operate with")
    mysqlvar_val = getvariable(cursor, mysqlvar)
    if value is None:
        module.exit_json(msg=mysqlvar_val)
    else:
        if len(mysqlvar_val) < 1:
            module.fail_json(msg="Variable not available", changed=False)
        # Type values before using them
        value_wanted = typedvalue(value)
        value_actual = typedvalue(mysqlvar_val[0][1])
        if value_wanted == value_actual:
            module.exit_json(msg="Variable already set to requested value", changed=False)
        try:
            result = setvariable(cursor, mysqlvar, value_wanted)
        except SQLParseError, e:
            result = str(e)
        if result is True:
            module.exit_json(msg="Variable change succeeded prev_value=%s" % value_actual, changed=True)
        else:
            module.fail_json(msg=result, changed=False)

# import module snippets
from ansible.module_utils.basic import *
from ansible.module_utils.database import *
main()
