# 2014, Shivani Gowrishankar <s.gowrishankar@ntoggle.com>
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
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import psycopg2

from ansible.errors import AnsibleError
from ansible.plugins.lookup import LookupBase

class LookupModule(LookupBase):
    """

    postgresql module used to query tables in postgresql database.

    Example: lookup('postgresql','database=database user=user password=password sql=SQL query')

    """
    def run(self, terms, variables, **kwargs):

        ret = []
        if not isinstance(terms, list):
            terms = [ terms ]
        #splitting only till 3 parameters because sql query has ' ' inside
        for term in terms:
            params = term.split(' ',3)

        paramvals = {
            'database' : 'database',
            'user' : 'user',
            'password' : 'password',
            'sql' : 'query',
        }
        try:
            for param in params:
                name, value = param.split('=')
                assert(name in paramvals)
                paramvals[name] = value
        except (ValueError, AssertionError) as e:
            raise AnsibleError(e)
        #assigning args for postgresql connect 
        database = paramvals['database']
        user = paramvals['user']
        password = paramvals['password']
        sql = paramvals['sql']
        #Connection to postgresql
        con = None
        try:
            con = psycopg2.connect(database=database, user=user, password=password)
            cur = con.cursor()
            cur.execute(sql)
            rows = cur.fetchall()
            for row in rows:
                row_string = str(row)
                ret.append(row_string)
        except:
             raise AnsibleError("Connection Failed or something's wrong")

        finally:
            if con:
                con.close()
        return ret
