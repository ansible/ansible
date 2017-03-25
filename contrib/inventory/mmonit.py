#!/usr/bin/env python

# (c) 2017, Prakritish Sen Eshore <prakritish@seneshore.com>
#
# This file is part of Ansible,
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible. If not, see <http://www.gnu.org/licenses/>.

"""
M/Monit external inventory script.
==================================

Returns hosts and hostgroups from M/Monit.

Configuration is read from `mmonit.ini`.
"""

import os
import argparse
try:
    import configparser
except ImportError:
    import ConfigParser
    configparser = ConfigParser
import json

import pycurl
try:
    # python 3
    from urllib.parse import urlencode
except ImportError:
    # python 2
    from urllib import urlencode

try:
    from io import BytesIO
except ImportError:
    from StringIO import StringIO as BytesIO

try:
    from sqlalchemy import text
    from sqlalchemy.engine import create_engine
except ImportError:
    print("Error: SQLAlchemy is needed. Try something like: pip install sqlalchemy")
    exit(1)


class mMonitInventory(object):
    def read_settings(self):
        config = configparser.SafeConfigParser()
        config.read(os.path.dirname(os.path.realpath(__file__)) + '/mmonit.ini')
        self.server = 'localhost'
        self.port = '3306'
        self.user = 'mmonit'
        self.passwd = 'mmonit'
        self.db = 'mmonit'
        self.connection = 'mysql'

        if config.has_option('mmonit', 'server'):
            self.server = config.get('mmonit', 'server')
        if config.has_option('mmonit', 'connection'):
            self.connection = config.get('mmonit', 'connection')
        if config.has_option('mmonit', 'port'):
            self.port = config.get('mmonit', 'port')
        if config.has_option('mmonit', 'user'):
            self.user = config.get('mmonit', 'user')
        if config.has_option('mmonit', 'passwd'):
            self.passwd = config.get('mmonit', 'passwd')
        if config.has_option('mmonit', 'db'):
            self.db = config.get('mmonit', 'db')
        if self.connection == 'mysql':
            self.db_uri = "mysql+mysqldb://{}:{}@{}:{}/{}?charset=utf8&use_unicode=1".format(
                self.user, self.passwd, self.server, self.port, self.db
            )
        else:
            self.url = "{}://{}:{}".format(
                self.connection, self.server, self.port
            )

    def read_cli(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('--host', nargs=1)
        parser.add_argument('--list', action='store_true')
        self.options = parser.parse_args()

    def http_get_hosts(self):
        cookie = "/tmp/cookie_{}".format(self.server)
        con = pycurl.Curl()
        con.setopt(con.URL, "{}/index.csp".format(self.url))
        con.setopt(pycurl.COOKIEJAR, cookie)
        con.perform()
        con.close()
        con = pycurl.Curl()
        con.setopt(con.URL, "{}/z_security_check".format(self.url))
        con.setopt(pycurl.COOKIEFILE, cookie)
        credentials = {
            'z_username': self.user,
            'z_password': self.passwd,
            'z_csrf_protection': "off"
        }
        postfields = urlencode(credentials)
        con.setopt(con.POSTFIELDS, postfields)
        con.perform()
        con.close()
        con = pycurl.Curl()
        con.setopt(con.URL, "{}/admin/groups/list".format(self.url))
        con.setopt(pycurl.COOKIEFILE, cookie)
        buffer = BytesIO()
        con.setopt(con.WRITEFUNCTION, buffer.write)
        con.perform()
        con.close()
        body = buffer.getvalue()
        data = json.loads(body.decode('iso-8859-1'))
        self.result = {'all': {'hosts': []}}
        host_list = {}
        for host in data['hosts']:
            self.result['all']['hosts'].append(host['name'])
            host_list[host['id']] = host['name']
        for hostgroup in data['groups']:
            self.result[hostgroup['name']] = {'hosts': []}
            for id in hostgroup['hosts']:
                self.result[hostgroup['name']]['hosts'].append(host_list[id])

    def mysql_get_hosts(self):
        engine = create_engine(self.db_uri)
        connection = engine.connect()
        select_hosts = text("SELECT name.name AS display_name \
                            FROM  host, name WHERE host.nameid = name.id")
        select_hostgroups = text("SELECT name.name AS alias, hostgroup.id \
                                    FROM hostgroup, name \
                                    WHERE hostgroup.nameid = name.id")
        select_hostgroup_hosts = text("SELECT name.name AS display_name \
                                        FROM groupedhost, name, host \
                                        WHERE host.id = groupedhost.hostid AND \
                                        host.nameid = name.id AND \
                                        groupedhost.groupid = :hostgroup_id")
        hosts = connection.execute(select_hosts)
        self.result = {'all': {'hosts': []}}
        self.result['all']['hosts'] = [host['display_name'] for host in hosts]

        for hostgroup in connection.execute(select_hostgroups):
            hostgroup_alias = hostgroup['alias']
            hostgroup_id = hostgroup['id']
            self.result[hostgroup_alias] = {}
            hosts = connection.execute(select_hostgroup_hosts, hostgroup_id=hostgroup_id)
            self.result[hostgroup_alias]['hosts'] = [host['display_name'] for host in hosts]

    def __init__(self):
        self.ndo_database_uri = None
        self.options = None

        self.read_settings()
        self.read_cli()

        self.result = {}
        self.result['all'] = {}
        self.result['all']['hosts'] = []
        self.result['_meta'] = {}
        self.result['_meta']['hostvars'] = {}

        if self.connection == 'mysql':
            self.mysql_get_hosts()
        elif self.connection == 'http' or self.connection == 'https':
            self.http_get_hosts()
        else:
            print("Error: M/Monit configuration is missing. See mmonit.ini.")
            exit(1)
        if self.options.host:
            print(json.dumps({}))
        elif self.options.list:
            print(json.dumps(self.result))
        else:
            print("usage: --list or --host HOSTNAME")
            exit(1)

mMonitInventory()
