#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2020, Andrew Klychkov (@Andersson007) <aaklychkov@mail.ru>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = r'''
---
module: postgresql_user_obj_stat_info
short_description: Gather statistics about PostgreSQL user objects
description:
- Gathers statistics about PostgreSQL user objects.
version_added: '2.10'
options:
  filter:
    description:
    - Limit the collected information by comma separated string or YAML list.
    - Allowable values are C(functions), C(indexes), C(tables).
    - By default, collects all subsets.
    - Unsupported values are ignored.
    type: list
    elements: str
  db:
    description:
    - Name of database to connect.
    type: str
    aliases:
    - login_db
  session_role:
    description:
    - Switch to session_role after connecting. The specified session_role must
      be a role that the current login_user is a member of.
    - Permissions checking for SQL commands is carried out as though
      the session_role were the one that had logged in originally.
    type: str
notes:
- For tracking function statistics the PostgreSQL ``track_functions`` parameter must be enabled.
  See U(https://www.postgresql.org/docs/current/runtime-config-statistics.html) for more information.
seealso:
- module: postgresql_info
- module: postgresql_ping
author:
- Andrew Klychkov (@Andersson007)
extends_documentation_fragment: postgres
'''

EXAMPLES = r'''
- name: Collect information about all supported objects the acme database
  postgresql_user_objects_info:
    db: acme

- name: Collect information about tables and indexes in the acme database
  postgresql_user_objects_info:
    db: acme
    filter: tables, indexes
'''

RETURN = r''' # '''

try:
    from psycopg2.extras import DictCursor
except ImportError:
    # psycopg2 is checked by connect_to_db()
    # from ansible.module_utils.postgres
    pass

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.postgres import (
    connect_to_db,
    exec_sql,
    get_conn_params,
    postgres_common_argument_spec,
)
from ansible.module_utils.six import iteritems


# ===========================================
# PostgreSQL module specific support methods.
#

class PgUserObjStatInfo():
    """Class to collect information about PostgreSQL user objects.

    Args:
        module (AnsibleModule): Object of AnsibleModule class.
        cursor (cursor): Cursor object of psycopg2 library to work with PostgreSQL.

    Attributes:
        module (AnsibleModule): Object of AnsibleModule class.
        cursor (cursor): Cursor object of psycopg2 library to work with PostgreSQL.
        executed_queries (list): List of executed queries.
        info (dict): Statistics dictionary.
        obj_func_mapping (dict): Mapping of object types to corresponding functions.
    """

    def __init__(self, module, cursor):
        self.module = module
        self.cursor = cursor
        self.info = {
            'functions': {},
            'indexes': {},
            'tables': {},
        }
        self.obj_func_mapping = {
            'functions': self.get_func_stat,
            'indexes': self.get_idx_stat,
            'tables': self.get_tbl_stat,
        }

    def collect(self, filter_=False):
        """Collect statistics information of user objects.

        Kwargs:
            filter_ (list): List of subsets which need to be collected.

        Returns:
            ``self.info``.
        """
        if filter_:
            for obj_type in filter_:
                self.obj_func_mapping.get(obj_type.strip())()

        else:
            for obj_type in self.obj_func_mapping:
                self.obj_func_mapping.get(obj_type)()

        return self.info

    def get_func_stat(self):
        """Get function statistics and fill out self.info dictionary."""
        result = exec_sql(self, "SELECT * FROM pg_stat_user_functions", add_to_executed=False)

        if not result:
            return

        self.__fill_out_info(result,
                             info_key='functions',
                             schema_key='schemaname',
                             name_key='funcname')

    def get_idx_stat(self):
        """Get index statistics and fill out self.info dictionary."""
        result = exec_sql(self, "SELECT * FROM pg_stat_user_indexes", add_to_executed=False)

        if not result:
            return

        self.__fill_out_info(result,
                             info_key='indexes',
                             schema_key='schemaname',
                             name_key='indexrelname')

    def get_tbl_stat(self):
        """Get table statistics and fill out self.info dictionary."""
        result = exec_sql(self, "SELECT * FROM pg_stat_user_tables", add_to_executed=False)

        if not result:
            return

        self.__fill_out_info(result,
                             info_key='tables',
                             schema_key='schemaname',
                             name_key='relname')

    def __fill_out_info(self, result, info_key=None, schema_key=None, name_key=None):
        # Convert result to list of dicts to handle it easier:
        result = [dict(row) for row in result]

        for elem in result:
            # Add schema name as a key if not presented:
            if not self.info[info_key].get(elem[schema_key]):
                self.info[info_key][elem[schema_key]] = {}

            # Add object name key as a subkey
            # (they must be uniq over a schema, so no need additional checks):
            self.info[info_key][elem[schema_key]][elem[name_key]] = {}

            # Add other other attributes to a certain index:
            for key, val in iteritems(elem):
                if key not in (schema_key, name_key):
                    self.info[info_key][elem[schema_key]][elem[name_key]][key] = val

            if info_key in ('tables', 'indexes'):
                relname = elem[name_key]
                result = exec_sql(self, "SELECT pg_relation_size ('%s')" % relname,
                                  add_to_executed=False)
                self.info[info_key][elem[schema_key]][elem[name_key]]['size'] = result[0][0]

                if info_key == 'tables':
                    relname = elem[name_key]
                    result = exec_sql(self, "SELECT pg_total_relation_size ('%s')" % relname,
                                      add_to_executed=False)
                    self.info[info_key][elem[schema_key]][elem[name_key]]['total_size'] = result[0][0]


# ===========================================
# Module execution.
#

def main():
    argument_spec = postgres_common_argument_spec()
    argument_spec.update(
        db=dict(type='str', aliases=['login_db']),
        filter=dict(type='list', elements='str'),
        session_role=dict(type='str'),
    )
    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    filter_ = module.params["filter"]

    # Connect to DB and make cursor object:
    pg_conn_params = get_conn_params(module, module.params)
    # We don't need to commit anything, so, set it to False:
    db_connection = connect_to_db(module, pg_conn_params, autocommit=False)
    cursor = db_connection.cursor(cursor_factory=DictCursor)

    ############################
    # Create object and do work:
    pg_obj_info = PgUserObjStatInfo(module, cursor)

    info_dict = pg_obj_info.collect(filter_)

    # Clean up:
    cursor.close()
    db_connection.close()

    # Return information:
    module.exit_json(**info_dict)


if __name__ == '__main__':
    main()
