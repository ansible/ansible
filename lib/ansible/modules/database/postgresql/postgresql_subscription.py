#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2019, Andrew Klychkov (@Andersson007) <aaklychkov@mail.ru>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = r'''
---
module: postgresql_subscription
short_description: Add, update, or remove PostgreSQL subscription
description:
- Add, update, or remove PostgreSQL subscription.
version_added: '2.10'

options:
  name:
    description:
    - Name of the subscription to add, update, or remove.
    type: str
    required: yes
  db:
    description:
    - Name of the database to connect to and where
      the subscription state will be changed.
    aliases: [ login_db ]
    type: str
    required: yes
  state:
    description:
    - The subscription state.
    type: str
    choices: [ absent, present, stat ]
    default: present
  pubname:
    description:
    - The publication name on the publisher.
    type: str
  connparams:
    description:
    - The connection dict param-value to connect to the publisher.
    - For more information see U(https://www.postgresql.org/docs/current/libpq-connect.html#LIBPQ-CONNSTRING).
    type: dict
  cascade:
    description:
    - Drop subscription dependencies. Has effect with I(state=absent) only.
    type: bool
    default: false

notes:
- PostgreSQL version must be 10 or greater.

seealso:
- module: postgresql_publication
- name: CREATE SUBSCRIPTION reference
  description: Complete reference of the CREATE SUBSCRIPTION command documentation.
  link: https://www.postgresql.org/docs/current/sql-createsubscription.html
- name: ALTER SUBSCRIPTION reference
  description: Complete reference of the ALTER SUBSCRIPTION command documentation.
  link: https://www.postgresql.org/docs/current/sql-altersubscription.html
- name: DROP SUBSCRIPTION reference
  description: Complete reference of the DROP SUBSCRIPTION command documentation.
  link: https://www.postgresql.org/docs/current/sql-dropsubscription.html

author:
- Andrew Klychkov (@Andersson007) <aaklychkov@mail.ru>

extends_documentation_fragment:
- postgres
'''

EXAMPLES = r'''
- name: >
    Create acme subscription in mydb database using acme_publication and
    the following connection parameters to connect to the publisher
  postgresql_subscription:
    db: mydb
    name: acme
    state: present
    pubname: acme_publication
    connparams:
      host: 127.0.0.1
      port: 5432
      user: repl
      password: replpass
      dbname: mydb

- name: Return the configuration of subscription acme if exists in mydb database
  postgresql_subscription:
    db: mydb
    name: acme
    state: stat

- name: Drop acme subscription from mydb with dependencies (cascade=yes)
  postgresql_subscription:
    db: mydb
    name: acme
    state: absent
    cascade: yes
'''

RETURN = r'''
name:
  description:
  - Name of the subscription.
  returned: always
  type: str
  sample: acme
exists:
  description:
  - Flag indicates the subscription exists or not at the end of runtime.
  returned: always
  type: bool
  sample: true
queries:
  description: List of executed queries.
  returned: always
  type: str
  sample: [ 'DROP SUBSCRIPTION "mysubscription"' ]
initial_state:
  description: Subscription configuration at the beginning of runtime.
  returned: always
  type: dict
  sample: {"conninfo": {}, "enabled": true, "owner": "postgres", "slotname": "test", "synccommit": true}
final_state:
  description: Subscription configuration at the end of runtime.
  returned: always
  type: dict
  sample: {"conninfo": {}, "enabled": true, "owner": "postgres", "slotname": "test", "synccommit": true}
'''

from copy import deepcopy

try:
    from psycopg2.extras import DictCursor
except ImportError:
    # psycopg2 is checked by connect_to_db()
    # from ansible.module_utils.postgres
    pass

from ansible.module_utils.basic import AnsibleModule
# from ansible.module_utils.database import pg_quote_identifier
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

def convert_conn_params(conn_dict):
    """Converts the passed connection dictionary to string.

    Args:
        conn_dict (list): Dictionary which needs to be converted.

    Returns:
        Connection string.
    """
    conn_list = []
    for (param, val) in iteritems(conn_dict):
        conn_list.append('%s=%s' % (param, val))

    return ' '.join(conn_list)


class PgSubscription():
    """Class to work with PostgreSQL subscription.

    Args:
        module (AnsibleModule): Object of AnsibleModule class.
        cursor (cursor): Cursor object of psycopg2 library to work with PostgreSQL.
        name (str): The name of the subscription.
        db (str): The database name the subscription will be associated with.

    Attributes:
        module (AnsibleModule): Object of AnsibleModule class.
        cursor (cursor): Cursor object of psycopg2 library to work with PostgreSQL.
        name (str): Name of subscription.
        executed_queries (list): List of executed queries.
        attrs (dict): Dict with subscription attributes.
        exists (bool): Flag indicates the subscription exists or not.
    """

    def __init__(self, module, cursor, name, db):
        self.module = module
        self.cursor = cursor
        self.name = name
        self.db = db
        self.executed_queries = []
        self.attrs = {
            'owner': '',
            'enabled': False,
            'synccommit': '',
            'conninfo': {},
            'slotname': '',
            'publications': [],
        }
        self.empty_attrs = deepcopy(self.attrs)
        self.exists = self.check_subscr()

    def get_info(self):
        """Refresh the subscription information.

        Returns:
            ``self.attrs``.
        """
        self.exists = self.check_subscr()
        return self.attrs

    def check_subscr(self):
        """Check the subscription and refresh ``self.attrs`` subscription attribute.

        Returns:
            True if the subscription with ``self.name`` exists, False otherwise.
        """

        subscr_info = self.__get_general_subscr_info()

        if not subscr_info:
            # The subcrtiption does not exist:
            self.attrs = deepcopy(self.empty_attrs)
            return False

        self.attrs['owner'] = subscr_info.get('rolname')
        self.attrs['enabled'] = subscr_info.get('subenabled')
        self.attrs['synccommit'] = subscr_info.get('subenabled')
        self.attrs['slotname'] = subscr_info.get('subslotname')
        self.attrs['publications'] = subscr_info.get('subpublications')
        if subscr_info.get('subconninfo'):
            for param in subscr_info['subconninfo'].split(' '):
                tmp = param.split('=')
                self.attrs['conninfo'][tmp[0]] = tmp[1]

        return True

    def create(self, connparams, pubname, check_mode=True):
        """Create the subscription.

        Args:
            connparams (str): Connection string in ligpq style.
            pubname (str): Publication name on the master to use.

        Kwargs:
            check_mode (bool): If True, don't actually change anything,
                just make SQL, add it to ``self.executed_queries`` and return True.

        Returns:
            changed (bool): True if the subscription has been created, otherwise False.
        """
        query_fragments = ["CREATE SUBSCRIPTION %s CONNECTION '%s' PUBLICATION %s" % (self.name, connparams, pubname)]

        changed = self.__exec_sql(' '.join(query_fragments), check_mode=check_mode)

        return changed

    def update(self, check_mode=True):
        """Update the subscription.

        Args:

        Kwargs:
            check_mode (bool): If True, don't actually change anything,
                just make SQL, add it to ``self.executed_queries`` and return True.

        Returns:
            changed (bool): True if subscription has been updated, otherwise False.
        """
        return False

    def drop(self, cascade=False, check_mode=True):
        """Drop the subscription.

        Kwargs:
            cascade (bool): Flag indicates that the subscription needs to be deleted
                with its dependencies.
            check_mode (bool): If True, don't actually change anything,
                just make SQL, add it to ``self.executed_queries`` and return True.

        Returns:
            changed (bool): True if publication has been updated, otherwise False.
        """
        if self.exists:
            query_fragments = ["DROP SUBSCRIPTION %s" % self.name]
            if cascade:
                query_fragments.append("CASCADE")

            return self.__exec_sql(' '.join(query_fragments), check_mode=check_mode)

    def __get_general_subscr_info(self):
        """Get and return general subscription information.

        Returns:
            Dict with subscription information if successful, False otherwise.
        """
        query = ("SELECT d.datname, r.rolname, s.subenabled, "
                 "s.subconninfo, s.subslotname, s.subsynccommit, "
                 "s.subpublications FROM pg_catalog.pg_subscription s "
                 "JOIN pg_catalog.pg_database d "
                 "ON s.subdbid = d.oid "
                 "JOIN pg_catalog.pg_roles AS r "
                 "ON s.subowner = r.oid "
                 "WHERE s.subname = '%s' AND d.datname = '%s'" % (self.name, self.db))

        result = exec_sql(self, query, add_to_executed=False)
        if result:
            return result[0]
        else:
            return False

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
        state=dict(type='str', default='present', choices=['absent', 'present', 'stat']),
        pubname=dict(type='str'),
        connparams=dict(type='dict'),
        cascade=dict(type='bool', default=False),
    )
    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    # Parameters handling:
    db = module.params['db']
    name = module.params['name']
    state = module.params['state']
    pubname = module.params['pubname']
    cascade = module.params['cascade']
    if module.params.get('connparams'):
        connparams = convert_conn_params(module.params['connparams'])
    else:
        connparams = None

    if state == 'present' and cascade:
        module.warm('parameter "cascade" is ignored when state is not absent')

    # Connect to DB and make cursor object:
    conn_params = get_conn_params(module, module.params)
    # We check subscription state without DML queries execution, so set autocommit:
    db_connection = connect_to_db(module, conn_params, autocommit=True)
    cursor = db_connection.cursor(cursor_factory=DictCursor)

    # Check version:
    if cursor.connection.server_version < SUPPORTED_PG_VERSION:
        module.fail_json(msg="PostgreSQL server version should be 10.0 or greater")

    # Set defaults:
    changed = False
    initial_state = {}
    final_state = {}

    ###################################
    # Create object and do rock'n'roll:
    subscription = PgSubscription(module, cursor, name, db)

    if subscription.exists:
        initial_state = subscription.attrs
        final_state = deepcopy(initial_state)

    # If module.check_mode=True, nothing will be changed:
    if state == 'stat':
        # Information has been collected already, so nothing is needed:
        pass

    if state == 'present':
        if not subscription.exists:
            changed = subscription.create(connparams, pubname, check_mode=module.check_mode)

        else:
            changed = subscription.update(check_mode=module.check_mode)

    elif state == 'absent':
        changed = subscription.drop(cascade, check_mode=module.check_mode)

    # Get final subscription info if needed:
    final_state = subscription.get_info()

    # Connection is not needed any more:
    cursor.close()
    db_connection.close()

    # Return ret values and exit:
    module.exit_json(changed=changed,
                     name=name,
                     exists=subscription.exists,
                     queries=subscription.executed_queries,
                     initial_state=initial_state,
                     final_state=final_state)


if __name__ == '__main__':
    main()
