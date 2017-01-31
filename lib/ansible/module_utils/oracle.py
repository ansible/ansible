#!/usr/bin/python
# -*- coding: utf-8 -*-

# This code is part of Ansible, but is an independent component.
# This particular file snippet, and this file snippet only, is BSD licensed.
# Modules you write using this snippet, which is embedded dynamically by Ansible
# still belong to the author of the module, and may assign their own license
# to the complete work.
#
# Copyright (c) 2017 Thomas Krahn (@Nosmoht)
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#
#    * Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
#    * Redistributions in binary form must reproduce the above copyright notice,
#      this list of conditions and the following disclaimer in the documentation
#      and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
# IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE
# USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

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
        finally:
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
        finally:
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
        finally:
            cur.close()
        return rows

    def is_rac(self):
        sql = 'SELECT parallel FROM v$instance'
        row = self.fetch_one(sql)
        return row[0] == 'YES'
