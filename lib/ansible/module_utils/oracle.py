#  -*- coding: utf-8 -*-

# Copyright (c) 2017 Thomas Krahn (@Nosmoht)
# All rights reserved.
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

try:
    import cx_Oracle

    HAS_ORACLE_LIB = True
except ImportError:
    HAS_ORACLE_LIB = False

from ansible.module_utils.pycompat24 import get_exception


class OracleClient(object):
    def __init__(self, module):
        self.module = module
        self.conn = None
        self.version = None

    def connect(self, host, port, user, password, sid=None, service=None, mode=None):
        if sid:
            dsn = cx_Oracle.makedsn(host=host, port=port, sid=sid)
        else:
            dsn = cx_Oracle.makedsn(host=host, port=port, service_name=service)

        try:
            if mode:
                self.conn = cx_Oracle.connect(user=user, password=password, dsn=dsn, mode=self.map_mode(mode))
            else:
                self.conn = cx_Oracle.connect(user=user, password=password, dsn=dsn)
        except cx_Oracle.DatabaseError:
            e = get_exception()
            self.module.fail_json(msg='%s: %s' % (dsn, str(e)))

        self.version = self.get_version()

    def get_version(self):
        sql = 'SELECT version FROM v$instance'
        row = self.fetch_one(sql)
        return row[0]

    def map_mode(self, mode):
        if mode == 'SYSDBA':
            return cx_Oracle.SYSDBA
        elif mode == 'SYSOPER':
            return cx_Oracle.SYSOPER
        elif mode is None:
            return None
        else:
            self.module.fail_json(msg='unknown connection mode: %s' % (mode))

    def execute_sql(self, sql):
        cur = self.conn.cursor()
        try:
            cur.execute(sql)
        except cx_Oracle.DatabaseError:
            e = get_exception()
            self.module.fail_json(msg='"%s": %s' % (sql, e))

        cur.close()

    def fetch_one(self, sql, where={}):
        cur = self.conn.cursor()
        try:
            cur.prepare(sql)
            cur.execute(None, where)
            row = cur.fetchone()
        except cx_Oracle.DatabaseError:
            e = get_exception()
            self.module.fail_json(msg='"%s": %s' % (sql, str(e)))

        cur.close()
        return row

    def fetch_all(self, sql, where):
        cur = self.conn.cursor()
        try:
            cur.prepare(sql)
            cur.execute(None, where)
            rows = cur.fetchall()
        except cx_Oracle.DatabaseError:
            e = get_exception()
            self.module.fail_json(msg='"%s": %s' % (sql, str(e)))

        cur.close()
        return rows

    def is_rac(self):
        sql = 'SELECT parallel FROM v$instance'
        row = self.fetch_one(sql)
        return row[0] == 'YES'
