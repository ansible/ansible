#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2019, Loic Blot (@nerzhul) <loic.blot@unix-experience.fr>
# Copyright: (c) 2019, Andrew Klychkov (@Andersson007) <aaklychkov@mail.ru>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = r'''
---
module: postgresql_publication
short_description: Add, update, or remove PostgreSQL publication
description:
- Add, update, or remove PostgreSQL publication.
version_added: "2.9"
options:
  name:
    description:
    - Name of the publication to add, update, or remove.
    required: true
    type: str
  db:
    description:
    - Name of the database to connect to and where
      the publication state will be changed.
    aliases: [ login_db ]
    type: str
  tables:
    description:
    - List of tables to add to the publication.
    - If no value is set all tables are targeted.
    - If the publication already exists for specific tables and I(tables) is not passed,
      nothing will be changed. If you need to add all tables to the publication with the same name,
      drop existent and create new without passing I(tables).
    type: list
    elements: str
  state:
    description:
    - The publication state.
    default: present
    choices: [ absent, present ]
    type: str
  parameters:
    description:
    - Dictionary with optional publication parameters.
    - Available parameters depend on PostgreSQL version.
    type: dict
  owner:
    description:
    - Publication owner.
    - If I(owner) is not defined, the owner will be set as I(login_user) or I(session_role).
    type: str
  cascade:
    description:
    - Drop publication dependencies. Has effect with I(state=absent) only.
    type: bool
    default: false
notes:
- PostgreSQL version must be 10 or greater.
seealso:
- name: CREATE PUBLICATION reference
  description: Complete reference of the CREATE PUBLICATION command documentation.
  link: https://www.postgresql.org/docs/current/sql-createpublication.html
- name: ALTER PUBLICATION reference
  description: Complete reference of the ALTER PUBLICATION command documentation.
  link: https://www.postgresql.org/docs/current/sql-alterpublication.html
- name: DROP PUBLICATION reference
  description: Complete reference of the DROP PUBLICATION command documentation.
  link: https://www.postgresql.org/docs/current/sql-droppublication.html
author:
- Loic Blot (@nerzhul) <loic.blot@unix-experience.fr>
- Andrew Klychkov (@Andersson007) <aaklychkov@mail.ru>
extends_documentation_fragment:
- postgres
'''

EXAMPLES = r'''
- name: Create a new publication with name "acme" targeting all tables in database "test".
  postgresql_publication:
    db: test
    name: acme

- name: Create publication "acme" publishing only prices and vehicles tables.
  postgresql_publication:
    name: acme
    tables:
    - prices
    - vehicles

- name: >
    Create publication "acme", set user alice as an owner, targeting all tables.
    Allowable DML operations are INSERT and UPDATE only
  postgresql_publication:
    name: acme
    owner: alice
    parameters:
      publish: 'insert,update'

- name: >
    Assuming publication "acme" exists and there are targeted
    tables "prices" and "vehicles", add table "stores" to the publication.
  postgresql_publication:
    name: acme
    tables:
    - prices
    - vehicles
    - stores

- name: Remove publication "acme" if exists in database "test".
  postgresql_publication:
    db: test
    name: acme
    state: absent
'''

RETURN = r'''
exists:
  description:
  - Flag indicates the publication exists or not at the end of runtime.
  returned: always
  type: bool
  sample: true
queries:
  description: List of executed queries.
  returned: always
  type: str
  sample: [ 'DROP PUBLICATION "acme" CASCADE' ]
owner:
  description: Owner of the publication at the end of runtime.
  returned: if publication exists
  type: str
  sample: "alice"
tables:
  description:
  - List of tables in the publication at the end of runtime.
  - If all tables are published, returns empty list.
  returned: if publication exists
  type: list
  sample: ["\"public\".\"prices\"", "\"public\".\"vehicles\""]
alltables:
  description:
  - Flag indicates that all tables are published.
  returned: if publication exists
  type: bool
  sample: false
parameters:
  description: Publication parameters at the end of runtime.
  returned: if publication exists
  type: dict
  sample: {'publish': {'insert': false, 'delete': false, 'update': true}}
'''


try:
    from psycopg2.extras import DictCursor
except ImportError:
    # psycopg2 is checked by connect_to_db()
    # from ansible.module_utils.postgres
    pass

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.database import pg_quote_identifier
from ansible.module_utils.postgres import (
    connect_to_db,
    exec_sql,
    get_conn_params,
    postgres_common_argument_spec,
)
from ansible.module_utils.six import iteritems

SUPPORTED_PG_VERSION = 10000


################################
# Module functions and classes #
################################

def transform_tables_representation(tbl_list):
    """Add 'public.' to names of tables where a schema identifier is absent
    and add quotes to each element.

    Args:
        tbl_list (list): List of table names.

    Returns:
        tbl_list (list): Changed list.
    """
    for i, table in enumerate(tbl_list):
        if '.' not in table:
            tbl_list[i] = pg_quote_identifier('public.%s' % table.strip(), 'table')
        else:
            tbl_list[i] = pg_quote_identifier(table.strip(), 'table')

    return tbl_list


class PgPublication():
    """Class to work with PostgreSQL publication.

    Args:
        module (AnsibleModule): Object of AnsibleModule class.
        cursor (cursor): Cursor object of psycopg2 library to work with PostgreSQL.
        name (str): The name of the publication.

    Attributes:
        module (AnsibleModule): Object of AnsibleModule class.
        cursor (cursor): Cursor object of psycopg2 library to work with PostgreSQL.
        name (str): Name of the publication.
        executed_queries (list): List of executed queries.
        attrs (dict): Dict with publication attributes.
        exists (bool): Flag indicates the publication exists or not.
    """

    def __init__(self, module, cursor, name):
        self.module = module
        self.cursor = cursor
        self.name = name
        self.executed_queries = []
        self.attrs = {
            'alltables': False,
            'tables': [],
            'parameters': {},
            'owner': '',
        }
        self.exists = self.check_pub()

    def get_info(self):
        """Refresh the publication information.

        Returns:
            ``self.attrs``.
        """
        self.exists = self.check_pub()
        return self.attrs

    def check_pub(self):
        """Check the publication and refresh ``self.attrs`` publication attribute.

        Returns:
            True if the publication with ``self.name`` exists, False otherwise.
        """

        pub_info = self.__get_general_pub_info()

        if not pub_info:
            # Publication does not exist:
            return False

        self.attrs['owner'] = pub_info.get('pubowner')

        # Publication DML operations:
        self.attrs['parameters']['publish'] = {}
        self.attrs['parameters']['publish']['insert'] = pub_info.get('pubinsert', False)
        self.attrs['parameters']['publish']['update'] = pub_info.get('pubupdate', False)
        self.attrs['parameters']['publish']['delete'] = pub_info.get('pubdelete', False)
        if pub_info.get('pubtruncate'):
            self.attrs['parameters']['publish']['truncate'] = pub_info.get('pubtruncate')

        # If alltables flag is False, get the list of targeted tables:
        if not pub_info.get('puballtables'):
            table_info = self.__get_tables_pub_info()
            # Join sublists [['schema', 'table'], ...] to ['schema.table', ...]
            # for better representation:
            for i, schema_and_table in enumerate(table_info):
                table_info[i] = pg_quote_identifier('.'.join(schema_and_table), 'table')

            self.attrs['tables'] = table_info
        else:
            self.attrs['alltables'] = True

        # Publication exists:
        return True

    def create(self, tables, params, owner, check_mode=True):
        """Create the publication.

        Args:
            tables (list): List with names of the tables that need to be added to the publication.
            params (dict): Dict contains optional publication parameters and their values.
            owner (str): Name of the publication owner.

        Kwargs:
            check_mode (bool): If True, don't actually change anything,
                just make SQL, add it to ``self.executed_queries`` and return True.

        Returns:
            changed (bool): True if publication has been created, otherwise False.
        """
        changed = True

        query_fragments = ["CREATE PUBLICATION %s" % pg_quote_identifier(self.name, 'publication')]

        if tables:
            query_fragments.append("FOR TABLE %s" % ', '.join(tables))
        else:
            query_fragments.append("FOR ALL TABLES")

        if params:
            params_list = []
            # Make list ["param = 'value'", ...] from params dict:
            for (key, val) in iteritems(params):
                params_list.append("%s = '%s'" % (key, val))

            # Add the list to query_fragments:
            query_fragments.append("WITH (%s)" % ', '.join(params_list))

        changed = self.__exec_sql(' '.join(query_fragments), check_mode=check_mode)

        if owner:
            # If check_mode, just add possible SQL to
            # executed_queries and return:
            self.__pub_set_owner(owner, check_mode=check_mode)

        return changed

    def update(self, tables, params, owner, check_mode=True):
        """Update the publication.

        Args:
            tables (list): List with names of the tables that need to be presented in the publication.
            params (dict): Dict contains optional publication parameters and their values.
            owner (str): Name of the publication owner.

        Kwargs:
            check_mode (bool): If True, don't actually change anything,
                just make SQL, add it to ``self.executed_queries`` and return True.

        Returns:
            changed (bool): True if publication has been updated, otherwise False.
        """
        changed = False

        # Add or drop tables from published tables suit:
        if tables and not self.attrs['alltables']:

            # 1. If needs to add table to the publication:
            for tbl in tables:
                if tbl not in self.attrs['tables']:
                    # If needs to add table to the publication:
                    changed = self.__pub_add_table(tbl, check_mode=check_mode)

            # 2. if there is a table in targeted tables
            # that's not presented in the passed tables:
            for tbl in self.attrs['tables']:
                if tbl not in tables:
                    changed = self.__pub_drop_table(tbl, check_mode=check_mode)

        elif tables and self.attrs['alltables']:
            changed = self.__pub_set_tables(tables, check_mode=check_mode)

        # Update pub parameters:
        if params:
            for key, val in iteritems(params):
                if self.attrs['parameters'].get(key):

                    # In PostgreSQL 10/11 only 'publish' optional parameter is presented.
                    if key == 'publish':
                        # 'publish' value can be only a string with comma-separated items
                        # of allowed DML operations like 'insert,update' or
                        # 'insert,update,delete', etc.
                        # Make dictionary to compare with current attrs later:
                        val_dict = self.attrs['parameters']['publish'].copy()
                        val_list = val.split(',')
                        for v in val_dict:
                            if v in val_list:
                                val_dict[v] = True
                            else:
                                val_dict[v] = False

                        # Compare val_dict and the dict with current 'publish' parameters,
                        # if they're different, set new values:
                        if val_dict != self.attrs['parameters']['publish']:
                            changed = self.__pub_set_param(key, val, check_mode=check_mode)

                    # Default behavior for other cases:
                    elif self.attrs['parameters'][key] != val:
                        changed = self.__pub_set_param(key, val, check_mode=check_mode)

                else:
                    # If the parameter was not set before:
                    changed = self.__pub_set_param(key, val, check_mode=check_mode)

        # Update pub owner:
        if owner:
            if owner != self.attrs['owner']:
                changed = self.__pub_set_owner(owner, check_mode=check_mode)

        return changed

    def drop(self, cascade=False, check_mode=True):
        """Drop the publication.

        Kwargs:
            cascade (bool): Flag indicates that publication needs to be deleted
                with its dependencies.
            check_mode (bool): If True, don't actually change anything,
                just make SQL, add it to ``self.executed_queries`` and return True.

        Returns:
            changed (bool): True if publication has been updated, otherwise False.
        """
        if self.exists:
            query_fragments = []
            query_fragments.append("DROP PUBLICATION %s" % pg_quote_identifier(self.name, 'publication'))
            if cascade:
                query_fragments.append("CASCADE")

            return self.__exec_sql(' '.join(query_fragments), check_mode=check_mode)

    def __get_general_pub_info(self):
        """Get and return general publication information.

        Returns:
            Dict with publication information if successful, False otherwise.
        """
        # Check pg_publication.pubtruncate exists (supported from PostgreSQL 11):
        pgtrunc_sup = exec_sql(self, ("SELECT 1 FROM information_schema.columns "
                                      "WHERE table_name = 'pg_publication' "
                                      "AND column_name = 'pubtruncate'"), add_to_executed=False)

        if pgtrunc_sup:
            query = ("SELECT r.rolname AS pubowner, p.puballtables, p.pubinsert, "
                     "p.pubupdate , p.pubdelete, p.pubtruncate FROM pg_publication AS p "
                     "JOIN pg_catalog.pg_roles AS r "
                     "ON p.pubowner = r.oid "
                     "WHERE p.pubname = '%s'" % self.name)
        else:
            query = ("SELECT r.rolname AS pubowner, p.puballtables, p.pubinsert, "
                     "p.pubupdate , p.pubdelete FROM pg_publication AS p "
                     "JOIN pg_catalog.pg_roles AS r "
                     "ON p.pubowner = r.oid "
                     "WHERE p.pubname = '%s'" % self.name)

        result = exec_sql(self, query, add_to_executed=False)
        if result:
            return result[0]
        else:
            return False

    def __get_tables_pub_info(self):
        """Get and return tables that are published by the publication.

        Returns:
            List of dicts with published tables.
        """
        query = ("SELECT schemaname, tablename "
                 "FROM pg_publication_tables WHERE pubname = '%s'" % self.name)
        return exec_sql(self, query, add_to_executed=False)

    def __pub_add_table(self, table, check_mode=False):
        """Add a table to the publication.

        Args:
            table (str): Table name.

        Kwargs:
            check_mode (bool): If True, don't actually change anything,
                just make SQL, add it to ``self.executed_queries`` and return True.

        Returns:
            True if successful, False otherwise.
        """
        query = ("ALTER PUBLICATION %s ADD TABLE %s" % (pg_quote_identifier(self.name, 'publication'),
                                                        pg_quote_identifier(table, 'table')))
        return self.__exec_sql(query, check_mode=check_mode)

    def __pub_drop_table(self, table, check_mode=False):
        """Drop a table from the publication.

        Args:
            table (str): Table name.

        Kwargs:
            check_mode (bool): If True, don't actually change anything,
                just make SQL, add it to ``self.executed_queries`` and return True.

        Returns:
            True if successful, False otherwise.
        """
        query = ("ALTER PUBLICATION %s DROP TABLE %s" % (pg_quote_identifier(self.name, 'publication'),
                                                         pg_quote_identifier(table, 'table')))
        return self.__exec_sql(query, check_mode=check_mode)

    def __pub_set_tables(self, tables, check_mode=False):
        """Set a table suit that need to be published by the publication.

        Args:
            tables (list): List of tables.

        Kwargs:
            check_mode (bool): If True, don't actually change anything,
                just make SQL, add it to ``self.executed_queries`` and return True.

        Returns:
            True if successful, False otherwise.
        """
        quoted_tables = [pg_quote_identifier(t, 'table') for t in tables]
        query = ("ALTER PUBLICATION %s SET TABLE %s" % (pg_quote_identifier(self.name, 'publication'),
                                                        ', '.join(quoted_tables)))
        return self.__exec_sql(query, check_mode=check_mode)

    def __pub_set_param(self, param, value, check_mode=False):
        """Set an optional publication parameter.

        Args:
            param (str): Name of the parameter.
            value (str): Parameter value.

        Kwargs:
            check_mode (bool): If True, don't actually change anything,
                just make SQL, add it to ``self.executed_queries`` and return True.

        Returns:
            True if successful, False otherwise.
        """
        query = ("ALTER PUBLICATION %s SET (%s = '%s')" % (pg_quote_identifier(self.name, 'publication'),
                                                           param, value))
        return self.__exec_sql(query, check_mode=check_mode)

    def __pub_set_owner(self, role, check_mode=False):
        """Set a publication owner.

        Args:
            role (str): Role (user) name that needs to be set as a publication owner.

        Kwargs:
            check_mode (bool): If True, don't actually change anything,
                just make SQL, add it to ``self.executed_queries`` and return True.

        Returns:
            True if successful, False otherwise.
        """
        query = ("ALTER PUBLICATION %s OWNER TO %s" % (pg_quote_identifier(self.name, 'publication'),
                                                       pg_quote_identifier(role, 'role')))
        return self.__exec_sql(query, check_mode=check_mode)

    def __exec_sql(self, query, check_mode=False):
        """Execute SQL query.

        Note: If we need just to get information from the database,
            we use ``exec_sql`` function directly.

        Args:
            query (str): Query that needs to be executed.

        Kwargs:
            check_mode (bool): If True, don't actually change anything,
                just add ``query`` to ``self.executed_queries`` and return True.

        Returns:
            True if successful, False otherwise.
        """
        if check_mode:
            self.executed_queries.append(query)
            return True
        else:
            return exec_sql(self, query, ddl=True)


# ===========================================
# Module execution.
#


def main():
    argument_spec = postgres_common_argument_spec()
    argument_spec.update(
        name=dict(required=True),
        db=dict(type='str', aliases=['login_db']),
        state=dict(type='str', default='present', choices=['absent', 'present']),
        tables=dict(type='list'),
        parameters=dict(type='dict'),
        owner=dict(type='str'),
        cascade=dict(type='bool', default=False),
    )
    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    # Parameters handling:
    name = module.params['name']
    state = module.params['state']
    tables = module.params['tables']
    params = module.params['parameters']
    owner = module.params['owner']
    cascade = module.params['cascade']

    if state == 'absent':
        if tables:
            module.warn('parameter "tables" is ignored when "state=absent"')
        if params:
            module.warn('parameter "parameters" is ignored when "state=absent"')
        if owner:
            module.warn('parameter "owner" is ignored when "state=absent"')

    if state == 'present' and cascade:
        module.warn('parameter "cascade" is ignored when "state=present"')

    # Connect to DB and make cursor object:
    conn_params = get_conn_params(module, module.params)
    # We check publication state without DML queries execution, so set autocommit:
    db_connection = connect_to_db(module, conn_params, autocommit=True)
    cursor = db_connection.cursor(cursor_factory=DictCursor)

    # Check version:
    if cursor.connection.server_version < SUPPORTED_PG_VERSION:
        module.fail_json(msg="PostgreSQL server version should be 10.0 or greater")

    # Nothing was changed by default:
    changed = False

    ###################################
    # Create object and do rock'n'roll:
    publication = PgPublication(module, cursor, name)

    if tables:
        tables = transform_tables_representation(tables)

    # If module.check_mode=True, nothing will be changed:
    if state == 'present':
        if not publication.exists:
            changed = publication.create(tables, params, owner, check_mode=module.check_mode)

        else:
            changed = publication.update(tables, params, owner, check_mode=module.check_mode)

    elif state == 'absent':
        changed = publication.drop(cascade=cascade, check_mode=module.check_mode)

    # Get final publication info:
    pub_fin_info = {}
    if state == 'present' or (state == 'absent' and module.check_mode):
        pub_fin_info = publication.get_info()
    elif state == 'absent' and not module.check_mode:
        publication.exists = False

    # Connection is not needed any more:
    cursor.close()
    db_connection.close()

    # Update publication info and return ret values:
    module.exit_json(changed=changed, queries=publication.executed_queries, exists=publication.exists, **pub_fin_info)


if __name__ == '__main__':
    main()
