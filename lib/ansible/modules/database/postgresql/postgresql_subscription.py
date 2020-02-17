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
    - C(present) implies that if I(name) subscription doesn't exist, it will be created.
    - C(absent) implies that if I(name) subscription exists, it will be removed.
    - C(refresh) implies that if I(name) subscription exists, it will be refreshed.
      Fetch missing table information from publisher. Always returns ``changed`` is ``True``.
      This will start replication of tables that were added to the subscribed-to publications
      since the last invocation of REFRESH PUBLICATION or since CREATE SUBSCRIPTION.
      The existing data in the publications that are being subscribed to
      should be copied once the replication starts.
    - For more information about C(refresh) see U(https://www.postgresql.org/docs/current/sql-altersubscription.html).
    type: str
    choices: [ absent, present, refresh ]
    default: present
  owner:
    description:
    - Subscription owner.
    - If I(owner) is not defined, the owner will be set as I(login_user) or I(session_role).
    - Ignored when I(state) is not C(present).
    type: str
  publications:
    description:
    - The publication names on the publisher to use for the subscription.
    - Ignored when I(state) is not C(present).
    type: list
    elements: str
  connparams:
    description:
    - The connection dict param-value to connect to the publisher.
    - For more information see U(https://www.postgresql.org/docs/current/libpq-connect.html#LIBPQ-CONNSTRING).
    - Ignored when I(state) is not C(present).
    type: dict
  cascade:
    description:
    - Drop subscription dependencies. Has effect with I(state=absent) only.
    - Ignored when I(state) is not C(absent).
    type: bool
    default: false
  subsparams:
    description:
    - Dictionary of optional parameters for a subscription, e.g. copy_data, enabled, create_slot, etc.
    - For update the subscription allowed keys are C(enabled), C(slot_name), C(synchronous_commit), C(publication_name).
    - See available parameters to create a new subscription
      on U(https://www.postgresql.org/docs/current/sql-createsubscription.html).
    - Ignored when I(state) is not C(present).
    type: dict

notes:
- PostgreSQL version must be 10 or greater.

seealso:
- module: postgresql_publication
- module: postgresql_info
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
    the following connection parameters to connect to the publisher.
    Set the subscription owner as alice.
  postgresql_subscription:
    db: mydb
    name: acme
    state: present
    publications: acme_publication
    owner: alice
    connparams:
      host: 127.0.0.1
      port: 5432
      user: repl
      password: replpass
      dbname: mydb

- name: Assuming that acme subscription exists, try to change conn parameters
  postgresql_subscription:
    db: mydb
    name: acme
    connparams:
      host: 127.0.0.1
      port: 5432
      user: repl
      password: replpass
      connect_timeout: 100

- name: Refresh acme publication
  postgresql_subscription:
    db: mydb
    name: acme
    state: refresh

- name: Drop acme subscription from mydb with dependencies (cascade=yes)
  postgresql_subscription:
    db: mydb
    name: acme
    state: absent
    cascade: yes

- name: Assuming that acme subscription exists and enabled, disable the subscription
  postgresql_subscription:
    db: mydb
    name: acme
    state: present
    subsparams:
      enabled: no
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
from ansible.module_utils.postgres import (
    connect_to_db,
    exec_sql,
    get_conn_params,
    postgres_common_argument_spec,
)
from ansible.module_utils.six import iteritems

SUPPORTED_PG_VERSION = 10000

SUBSPARAMS_KEYS_FOR_UPDATE = ('enabled', 'synchronous_commit', 'slot_name')


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


def convert_subscr_params(params_dict):
    """Converts the passed params dictionary to string.

    Args:
        params_dict (list): Dictionary which needs to be converted.

    Returns:
        Parameters string.
    """
    params_list = []
    for (param, val) in iteritems(params_dict):
        if val is False:
            val = 'false'
        elif val is True:
            val = 'true'

        params_list.append('%s = %s' % (param, val))

    return ', '.join(params_list)


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
            'owner': None,
            'enabled': None,
            'synccommit': None,
            'conninfo': {},
            'slotname': None,
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
            # The subscription does not exist:
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
                try:
                    self.attrs['conninfo'][tmp[0]] = int(tmp[1])
                except ValueError:
                    self.attrs['conninfo'][tmp[0]] = tmp[1]

        return True

    def create(self, connparams, publications, subsparams, check_mode=True):
        """Create the subscription.

        Args:
            connparams (str): Connection string in libpq style.
            publications (list): Publications on the master to use.
            subsparams (str): Parameters string in WITH () clause style.

        Kwargs:
            check_mode (bool): If True, don't actually change anything,
                just make SQL, add it to ``self.executed_queries`` and return True.

        Returns:
            changed (bool): True if the subscription has been created, otherwise False.
        """
        query_fragments = []
        query_fragments.append("CREATE SUBSCRIPTION %s CONNECTION '%s' "
                               "PUBLICATION %s" % (self.name, connparams, ', '.join(publications)))

        if subsparams:
            query_fragments.append("WITH (%s)" % subsparams)

        changed = self.__exec_sql(' '.join(query_fragments), check_mode=check_mode)

        return changed

    def update(self, connparams, publications, subsparams, check_mode=True):
        """Update the subscription.

        Args:
            connparams (str): Connection string in libpq style.
            publications (list): Publications on the master to use.
            subsparams (dict): Dictionary of optional parameters.

        Kwargs:
            check_mode (bool): If True, don't actually change anything,
                just make SQL, add it to ``self.executed_queries`` and return True.

        Returns:
            changed (bool): True if subscription has been updated, otherwise False.
        """
        changed = False

        if connparams:
            if connparams != self.attrs['conninfo']:
                changed = self.__set_conn_params(convert_conn_params(connparams),
                                                 check_mode=check_mode)

        if publications:
            if sorted(self.attrs['publications']) != sorted(publications):
                changed = self.__set_publications(publications, check_mode=check_mode)

        if subsparams:
            params_to_update = []

            for (param, value) in iteritems(subsparams):
                if param == 'enabled':
                    if self.attrs['enabled'] and value is False:
                        changed = self.enable(enabled=False, check_mode=check_mode)
                    elif not self.attrs['enabled'] and value is True:
                        changed = self.enable(enabled=True, check_mode=check_mode)

                elif param == 'synchronous_commit':
                    if self.attrs['synccommit'] is True and value is False:
                        params_to_update.append("%s = false" % param)
                    elif self.attrs['synccommit'] is False and value is True:
                        params_to_update.append("%s = true" % param)

                elif param == 'slot_name':
                    if self.attrs['slotname'] and self.attrs['slotname'] != value:
                        params_to_update.append("%s = %s" % (param, value))

                else:
                    self.module.warn("Parameter '%s' is not in params supported "
                                     "for update '%s', ignored..." % (param, SUBSPARAMS_KEYS_FOR_UPDATE))

            if params_to_update:
                changed = self.__set_params(params_to_update, check_mode=check_mode)

        return changed

    def drop(self, cascade=False, check_mode=True):
        """Drop the subscription.

        Kwargs:
            cascade (bool): Flag indicates that the subscription needs to be deleted
                with its dependencies.
            check_mode (bool): If True, don't actually change anything,
                just make SQL, add it to ``self.executed_queries`` and return True.

        Returns:
            changed (bool): True if the subscription has been removed, otherwise False.
        """
        if self.exists:
            query_fragments = ["DROP SUBSCRIPTION %s" % self.name]
            if cascade:
                query_fragments.append("CASCADE")

            return self.__exec_sql(' '.join(query_fragments), check_mode=check_mode)

    def set_owner(self, role, check_mode=True):
        """Set a subscription owner.

        Args:
            role (str): Role (user) name that needs to be set as a subscription owner.

        Kwargs:
            check_mode (bool): If True, don't actually change anything,
                just make SQL, add it to ``self.executed_queries`` and return True.

        Returns:
            True if successful, False otherwise.
        """
        query = 'ALTER SUBSCRIPTION %s OWNER TO "%s"' % (self.name, role)
        return self.__exec_sql(query, check_mode=check_mode)

    def refresh(self, check_mode=True):
        """Refresh publication.

        Fetches missing table info from publisher.

        Kwargs:
            check_mode (bool): If True, don't actually change anything,
                just make SQL, add it to ``self.executed_queries`` and return True.

        Returns:
            True if successful, False otherwise.
        """
        query = 'ALTER SUBSCRIPTION %s REFRESH PUBLICATION' % self.name
        return self.__exec_sql(query, check_mode=check_mode)

    def __set_params(self, params_to_update, check_mode=True):
        """Update optional subscription parameters.

        Args:
            params_to_update (list): Parameters with values to update.

        Kwargs:
            check_mode (bool): If True, don't actually change anything,
                just make SQL, add it to ``self.executed_queries`` and return True.

        Returns:
            True if successful, False otherwise.
        """
        query = 'ALTER SUBSCRIPTION %s SET (%s)' % (self.name, ', '.join(params_to_update))
        return self.__exec_sql(query, check_mode=check_mode)

    def __set_conn_params(self, connparams, check_mode=True):
        """Update connection parameters.

        Args:
            connparams (str): Connection string in libpq style.

        Kwargs:
            check_mode (bool): If True, don't actually change anything,
                just make SQL, add it to ``self.executed_queries`` and return True.

        Returns:
            True if successful, False otherwise.
        """
        query = "ALTER SUBSCRIPTION %s CONNECTION '%s'" % (self.name, connparams)
        return self.__exec_sql(query, check_mode=check_mode)

    def __set_publications(self, publications, check_mode=True):
        """Update publications.

        Args:
            publications (list): Publications on the master to use.

        Kwargs:
            check_mode (bool): If True, don't actually change anything,
                just make SQL, add it to ``self.executed_queries`` and return True.

        Returns:
            True if successful, False otherwise.
        """
        query = 'ALTER SUBSCRIPTION %s SET PUBLICATION %s' % (self.name, ', '.join(publications))
        return self.__exec_sql(query, check_mode=check_mode)

    def enable(self, enabled=True, check_mode=True):
        """Enable or disable the subscription.

        Kwargs:
            enable (bool): Flag indicates that the subscription needs
                to be enabled or disabled.
            check_mode (bool): If True, don't actually change anything,
                just make SQL, add it to ``self.executed_queries`` and return True.

        Returns:
            True if successful, False otherwise.
        """
        if enabled:
            query = 'ALTER SUBSCRIPTION %s ENABLE' % self.name
        else:
            query = 'ALTER SUBSCRIPTION %s DISABLE' % self.name

        return self.__exec_sql(query, check_mode=check_mode)

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
                 "WHERE s.subname = %(name)s AND d.datname = %(db)s")

        result = exec_sql(self, query, query_params={'name': self.name, 'db': self.db}, add_to_executed=False)
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
        name=dict(type='str', required=True),
        db=dict(type='str', required=True, aliases=['login_db']),
        state=dict(type='str', default='present', choices=['absent', 'present', 'refresh']),
        publications=dict(type='list', elements='str'),
        connparams=dict(type='dict'),
        cascade=dict(type='bool', default=False),
        owner=dict(type='str'),
        subsparams=dict(type='dict'),
    )
    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    # Parameters handling:
    db = module.params['db']
    name = module.params['name']
    state = module.params['state']
    publications = module.params['publications']
    cascade = module.params['cascade']
    owner = module.params['owner']
    subsparams = module.params['subsparams']
    connparams = module.params['connparams']

    if state == 'present' and cascade:
        module.warn('parameter "cascade" is ignored when state is not absent')

    if state != 'present':
        if owner:
            module.warn("parameter 'owner' is ignored when state is not 'present'")
        if publications:
            module.warn("parameter 'publications' is ignored when state is not 'present'")
        if connparams:
            module.warn("parameter 'connparams' is ignored when state is not 'present'")
        if subsparams:
            module.warn("parameter 'subsparams' is ignored when state is not 'present'")

    # Connect to DB and make cursor object:
    pg_conn_params = get_conn_params(module, module.params)
    # We check subscription state without DML queries execution, so set autocommit:
    db_connection = connect_to_db(module, pg_conn_params, autocommit=True)
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
        initial_state = deepcopy(subscription.attrs)
        final_state = deepcopy(initial_state)

    if state == 'present':
        if not subscription.exists:
            if subsparams:
                subsparams = convert_subscr_params(subsparams)

            if connparams:
                connparams = convert_conn_params(connparams)

            changed = subscription.create(connparams,
                                          publications,
                                          subsparams,
                                          check_mode=module.check_mode)

        else:
            changed = subscription.update(connparams,
                                          publications,
                                          subsparams,
                                          check_mode=module.check_mode)

        if owner and subscription.attrs['owner'] != owner:
            changed = subscription.set_owner(owner, check_mode=module.check_mode) or changed

    elif state == 'absent':
        changed = subscription.drop(cascade, check_mode=module.check_mode)

    elif state == 'refresh':
        if not subscription.exists:
            module.fail_json(msg="Refresh failed: subscription '%s' does not exist" % name)

        # Always returns True:
        changed = subscription.refresh(check_mode=module.check_mode)

    # Get final subscription info:
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
