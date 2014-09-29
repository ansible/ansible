#!/usr/bin/python
# -*- coding: utf-8 -*-

"""

Ansible module to manage mysql replication
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
module: mysql_replication

short_description: Manage MySQL replication
description:
    - Manages MySQL server replication, slave, master status get and change master host.
version_added: "1.3"
options:
    mode:
        description:
            - module operating mode. Could be getslave (SHOW SLAVE STATUS), getmaster (SHOW MASTER STATUS), changemaster (CHANGE MASTER TO), startslave (START SLAVE), stopslave (STOP SLAVE)
        required: False
        choices:
            - getslave
            - getmaster
            - changemaster
            - stopslave
            - startslave
        default: getslave
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
    login_port:
        description:
            - Port of the MySQL server. Requires login_host be defined as other then localhost if login_port is used
        required: False
        default: 3306
        version_added: "1.9"
    login_unix_socket:
        description:
            - unix socket to connect mysql server
    master_host:
        description:
            - same as mysql variable
    master_user:
        description:
            - same as mysql variable
    master_password:
        description:
            - same as mysql variable
    master_port:
        description:
            - same as mysql variable
    master_connect_retry:
        description:
            - same as mysql variable
    master_log_file:
        description:
            - same as mysql variable
    master_log_pos:
        description:
            - same as mysql variable
    relay_log_file:
        description:
            - same as mysql variable
    relay_log_pos:
        description:
            - same as mysql variable
    master_ssl:
        description:
            - same as mysql variable
        possible values: 0,1
    master_ssl_ca:
        description:
            - same as mysql variable
    master_ssl_capath:
        description:
            - same as mysql variable
    master_ssl_cert:
        description:
            - same as mysql variable
    master_ssl_key:
        description:
            - same as mysql variable
    master_ssl_cipher:
        description:
            - same as mysql variable

'''

EXAMPLES = '''
# Stop mysql slave thread
- mysql_replication: mode=stopslave

# Get master binlog file name and binlog position
- mysql_replication: mode=getmaster

# Change master to master server 192.168.1.1 and use binary log 'mysql-bin.000009' with position 4578
- mysql_replication: mode=changemaster master_host=192.168.1.1 master_log_file=mysql-bin.000009 master_log_pos=4578

# Check slave status using port 3308
- mysql_replication: mode=getslave login_host=ansible.example.com login_port=3308
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


def get_master_status(cursor):
    cursor.execute("SHOW MASTER STATUS")
    masterstatus = cursor.fetchone()
    return masterstatus


def get_slave_status(cursor):
    cursor.execute("SHOW SLAVE STATUS")
    slavestatus = cursor.fetchone()
    return slavestatus


def stop_slave(cursor):
    try:
        cursor.execute("STOP SLAVE")
        stopped = True
    except:
        stopped = False
    return stopped


def start_slave(cursor):
    try:
        cursor.execute("START SLAVE")
        started = True
    except:
        started = False
    return started


def changemaster(cursor, chm, chm_params):
    sql_param = ",".join(chm)
    query = 'CHANGE MASTER TO %s' % sql_param
    cursor.execute(query, chm_params)


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
            login_port=dict(default="3306"),
            login_unix_socket=dict(default=None),
            mode=dict(default="getslave", choices=["getmaster", "getslave", "changemaster", "stopslave", "startslave"]),
            master_host=dict(default=None),
            master_user=dict(default=None),
            master_password=dict(default=None),
            master_port=dict(default=None, type='int'),
            master_connect_retry=dict(default=None, type='int'),
            master_log_file=dict(default=None),
            master_log_pos=dict(default=None, type='int'),
            relay_log_file=dict(default=None),
            relay_log_pos=dict(default=None, type='int'),
            master_ssl=dict(default=False, type='bool'),
            master_ssl_ca=dict(default=None),
            master_ssl_capath=dict(default=None),
            master_ssl_cert=dict(default=None),
            master_ssl_key=dict(default=None),
            master_ssl_cipher=dict(default=None),
        )
    )
    user = module.params["login_user"]
    password = module.params["login_password"]
    host = module.params["login_host"]
    port = module.params["login_port"]
    mode = module.params["mode"]
    master_host = module.params["master_host"]
    master_user = module.params["master_user"]
    master_password = module.params["master_password"]
    master_port = module.params["master_port"]
    master_connect_retry = module.params["master_connect_retry"]
    master_log_file = module.params["master_log_file"]
    master_log_pos = module.params["master_log_pos"]
    relay_log_file = module.params["relay_log_file"]
    relay_log_pos = module.params["relay_log_pos"]
    master_ssl = module.params["master_ssl"]
    master_ssl_ca = module.params["master_ssl_ca"]
    master_ssl_capath = module.params["master_ssl_capath"]
    master_ssl_cert = module.params["master_ssl_cert"]
    master_ssl_key = module.params["master_ssl_key"]
    master_ssl_cipher = module.params["master_ssl_cipher"]

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
            db_connection = MySQLdb.connect(host=module.params["login_host"], unix_socket=module.params["login_unix_socket"], user=login_user, passwd=login_password)
        elif module.params["login_port"] != "3306" and module.params["login_host"] == "localhost":
            module.fail_json(msg="login_host is required when login_port is defined, login_host cannot be localhost when login_port is defined")
        else:
            db_connection = MySQLdb.connect(host=module.params["login_host"], port=int(module.params["login_port"]), user=login_user, passwd=login_password)
    except Exception, e:
        module.fail_json(msg="unable to connect to database, check login_user and login_password are correct or ~/.my.cnf has the credentials")
    try:
        cursor = db_connection.cursor(cursorclass=MySQLdb.cursors.DictCursor)
    except Exception, e:
        module.fail_json(msg="Trouble getting DictCursor from db_connection: %s" % e)

    if mode in "getmaster":
        masterstatus = get_master_status(cursor)
        try:
            module.exit_json( **masterstatus )
        except TypeError:
            module.fail_json(msg="Server is not configured as mysql master")

    elif mode in "getslave":
        slavestatus = get_slave_status(cursor)
        try:
            module.exit_json( **slavestatus )
        except TypeError:
            module.fail_json(msg="Server is not configured as mysql slave")

    elif mode in "changemaster":
        chm=[]
        chm_params = {}
        if master_host:
            chm.append("MASTER_HOST=%(master_host)s")
            chm_params['master_host'] = master_host
        if master_user:
            chm.append("MASTER_USER=%(master_user)s")
            chm_params['master_user'] = master_user
        if master_password:
            chm.append("MASTER_PASSWORD=%(master_password)s")
            chm_params['master_password'] = master_password
        if master_port is not None:
            chm.append("MASTER_PORT=%(master_port)s")
            chm_params['master_port'] = master_port
        if master_connect_retry is not None:
            chm.append("MASTER_CONNECT_RETRY=%(master_connect_retry)s")
            chm_params['master_connect_retry'] = master_connect_retry
        if master_log_file:
            chm.append("MASTER_LOG_FILE=%(master_log_file)s")
            chm_params['master_log_file'] = master_log_file
        if master_log_pos is not None:
            chm.append("MASTER_LOG_POS=%(master_log_pos)s")
            chm_params['master_log_pos'] = master_log_pos
        if relay_log_file:
            chm.append("RELAY_LOG_FILE=%(relay_log_file)s")
            chm_params['relay_log_file'] = relay_log_file
        if relay_log_pos is not None:
            chm.append("RELAY_LOG_POS=%(relay_log_pos)s")
            chm_params['relay_log_pos'] = relay_log_pos
        if master_ssl:
            chm.append("MASTER_SSL=1")
        if master_ssl_ca:
            chm.append("MASTER_SSL_CA=%(master_ssl_ca)s")
            chm_params['master_ssl_ca'] = master_ssl_ca
        if master_ssl_capath:
            chm.append("MASTER_SSL_CAPATH=%(master_ssl_capath)s")
            chm_params['master_ssl_capath'] = master_ssl_capath
        if master_ssl_cert:
            chm.append("MASTER_SSL_CERT=%(master_ssl_cert)s")
            chm_params['master_ssl_cert'] = master_ssl_cert
        if master_ssl_key:
            chm.append("MASTER_SSL_KEY=%(master_ssl_key)s")
            chm_params['master_ssl_key'] = master_ssl_key
        if master_ssl_cipher:
            chm.append("MASTER_SSL_CIPHER=%(master_ssl_cipher)s")
            chm_params['master_ssl_cipher'] = master_ssl_cipher
        changemaster(cursor, chm, chm_params)
        module.exit_json(changed=True)
    elif mode in "startslave":
        started = start_slave(cursor)
        if started is True:
            module.exit_json(msg="Slave started ", changed=True)
        else:
            module.exit_json(msg="Slave already started (Or cannot be started)", changed=False)
    elif mode in "stopslave":
        stopped = stop_slave(cursor)
        if stopped is True:
            module.exit_json(msg="Slave stopped", changed=True)
        else:
            module.exit_json(msg="Slave already stopped", changed=False)

# import module snippets
from ansible.module_utils.basic import *
main()
warnings.simplefilter("ignore")
