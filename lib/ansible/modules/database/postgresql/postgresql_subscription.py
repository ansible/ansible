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
    required: true
    type: str
  db:
    description:
    - Name of the database to connect to and where
      the subscription state will be changed.
    aliases: [ login_db ]
    type: str
  state:
    description:
    - The subscription state.
    default: present
    choices: [ absent, present, stat ]
    type: str
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
- name: Return the configuration of subscription acme if exists in mydb database
  postgresql_subscription:
    db: mydb
    name: acme
    state: stat
'''

RETURN = r'''
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
  sample: {}
final_state:
  description: Subscription configuration at the end of runtime.
  returned: always
  type: dict
  sample: {}
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
# from ansible.module_utils.six import iteritems

SUPPORTED_PG_VERSION = 10000


################################
# Module functions and classes #
################################

class PgSubscription():
    """Class to work with PostgreSQL subscription.

    Args:
        module (AnsibleModule): Object of AnsibleModule class.
        cursor (cursor): Cursor object of psycopg2 library to work with PostgreSQL.
        name (str): The name of the subscription.

    Attributes:
        module (AnsibleModule): Object of AnsibleModule class.
        cursor (cursor): Cursor object of psycopg2 library to work with PostgreSQL.
        name (str): Name of subscription.
        executed_queries (list): List of executed queries.
        attrs (dict): Dict with subscription attributes.
        exists (bool): Flag indicates the subscription exists or not.
    """

    def __init__(self, module, cursor, name):
        self.module = module
        self.cursor = cursor
        self.name = name
        self.executed_queries = []
        self.attrs = {
            'owner': '',
            'enabled': False,
            'synccommit': '',
            'conninfo': {},
            'slotname': '',
            'publications': [],
        }
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
            return False

        return True

    def create(self, check_mode=True):
        """Create the subscription.

        Args:

        Kwargs:
            check_mode (bool): If True, don't actually change anything,
                just make SQL, add it to ``self.executed_queries`` and return True.

        Returns:
            changed (bool): True if the subscription has been created, otherwise False.
        """
        return False

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

    def drop(self, check_mode=True):
        """Drop the subscription.

        Kwargs:
            check_mode (bool): If True, don't actually change anything,
                just make SQL, add it to ``self.executed_queries`` and return True.

        Returns:
            changed (bool): True if publication has been updated, otherwise False.
        """
        return False

    def __get_general_subscr_info(self):
        """Get and return general subscription information.

        Returns:
            Dict with subscription information if successful, False otherwise.
        """
        return {}

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
    )
    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    # Parameters handling:
    name = module.params['name']
    state = module.params['state']

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
    subscription = PgSubscription(module, cursor, name)

    if subscription.exists:
        initial_state = subscription.attrs
        final_state = deepcopy(initial_state)

    # If module.check_mode=True, nothing will be changed:
    if state == 'stat':
        # Information has been collected already, so nothing is needed:
        pass

    if state == 'present':
        if not subscription.exists:
            changed = subscription.create(check_mode=module.check_mode)

        else:
            changed = subscription.update(check_mode=module.check_mode)

    elif state == 'absent':
        changed = subscription.drop(check_mode=module.check_mode)

    # Get final subscription info if needed:
    if state == 'present' or (state == 'absent' and module.check_mode):
        final_state = subscription.get_info()
    elif state == 'absent' and not module.check_mode:
        subscription.exists = False

    # Connection is not needed any more:
    cursor.close()
    db_connection.close()

    # Return ret values and exit:
    module.exit_json(changed=changed,
                     exists=subscription.exists,
                     queries=subscription.executed_queries,
                     initial_state=initial_state,
                     final_state=final_state)


if __name__ == '__main__':
    main()
