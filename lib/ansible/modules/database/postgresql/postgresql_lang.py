#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# (c) 2014, Jens Depuydt <http://www.jensd.be>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: postgresql_lang
short_description: Adds, removes or changes procedural languages with a PostgreSQL database
description:
- Adds, removes or changes procedural languages with a PostgreSQL database.
- This module allows you to add a language, remote a language or change the trust
  relationship with a PostgreSQL database.
- The module can be used on the machine where executed or on a remote host.
- When removing a language from a database, it is possible that dependencies prevent
  the database from being removed. In that case, you can specify casade to
  automatically drop objects that depend on the language (such as functions in the
  language).
- In case the language can't be deleted because it is required by the
  database system, you can specify fail_on_drop=no to ignore the error.
- Be carefull when marking a language as trusted since this could be a potential
  security breach. Untrusted languages allow only users with the PostgreSQL superuser
  privilege to use this language to create new functions.
- For more information about PostgreSQL languages see the official documentation
  U(https://www.postgresql.org/docs/current/sql-createlanguage.html),
  U(https://www.postgresql.org/docs/current/sql-alterlanguage.html),
  U(https://www.postgresql.org/docs/current/sql-droplanguage.html).
version_added: '1.7'
options:
  lang:
    description:
    - Name of the procedural language to add, remove or change.
    required: true
    type: str
    aliases:
    - name
  trust:
    description:
    - Make this language trusted for the selected db.
    type: bool
    default: 'no'
  db:
    description:
    - Name of database to connect to and where the language will be added, removed or changed.
    type: str
    aliases:
    - login_db
  force_trust:
    description:
    - Marks the language as trusted, even if it's marked as untrusted in pg_pltemplate.
    - Use with care!
    type: bool
    default: 'no'
  fail_on_drop:
    description:
    - If C(yes), fail when removing a language. Otherwise just log and continue.
    - In some cases, it is not possible to remove a language (used by the db-system).
    - When dependencies block the removal, consider using C(cascade).
    type: bool
    default: 'yes'
  cascade:
    description:
    - When dropping a language, also delete object that depend on this language.
    - Only used when C(state=absent).
    type: bool
    default: 'no'
  session_role:
    version_added: '2.8'
    description:
    - Switch to session_role after connecting.
    - The specified session_role must be a role that the current login_user is a member of.
    - Permissions checking for SQL commands is carried out as though the session_role were the one that had logged in originally.
    type: str
  state:
    description:
    - The state of the language for the selected database.
    type: str
    default: present
    choices: [ absent, present ]
  login_unix_socket:
    description:
      - Path to a Unix domain socket for local connections.
    type: str
    version_added: '2.8'
  ssl_mode:
    description:
      - Determines whether or with what priority a secure SSL TCP/IP connection will be negotiated with the server.
      - See https://www.postgresql.org/docs/current/static/libpq-ssl.html for more information on the modes.
      - Default of C(prefer) matches libpq default.
    type: str
    default: prefer
    choices: [ allow, disable, prefer, require, verify-ca, verify-full ]
    version_added: '2.8'
  ca_cert:
    description:
      - Specifies the name of a file containing SSL certificate authority (CA) certificate(s).
      - If the file exists, the server's certificate will be verified to be signed by one of these authorities.
    type: str
    aliases: [ ssl_rootcert ]
    version_added: '2.8'
notes:
- The default authentication assumes that you are either logging in as or
  sudo'ing to the postgres account on the host.
- This module uses psycopg2, a Python PostgreSQL database adapter. You must
  ensure that psycopg2 is installed on the host before using this module.
- If the remote host is the PostgreSQL server (which is the default case), then
  PostgreSQL must also be installed on the remote host.
- For Ubuntu-based systems, install the postgresql, libpq-dev, and python-psycopg2 packages
  on the remote host before using this module.
requirements: [ psycopg2 ]

author:
- Jens Depuydt (@jensdepuydt)
- Thomas O'Donnell (@andytom)
extends_documentation_fragment: postgres
'''

EXAMPLES = r'''
- name: Add language pltclu to database testdb if it doesn't exist
  postgresql_lang: db=testdb lang=pltclu state=present

# Add language pltclu to database testdb if it doesn't exist and mark it as trusted.
# Marks the language as trusted if it exists but isn't trusted yet.
# force_trust makes sure that the language will be marked as trusted
- name: Add language pltclu to database testdb if it doesn't exist and mark it as trusted
  postgresql_lang:
    db: testdb
    lang: pltclu
    state: present
    trust: yes
    force_trust: yes

- name: Remove language pltclu from database testdb
  postgresql_lang:
    db: testdb
    lang: pltclu
    state: absent

- name: Remove language pltclu from database testdb and remove all dependencies
  postgresql_lang:
    db: testdb
    lang: pltclu
    state: absent
    cascade: yes

- name: Remove language c from database testdb but ignore errors if something prevents the removal
  postgresql_lang:
    db: testdb
    lang: pltclu
    state: absent
    fail_on_drop: no
'''

RETURN = r'''
queries:
  description: List of executed queries.
  returned: always
  type: list
  sample: ['CREATE LANGUAGE "acme"']
  version_added: '2.8'
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.postgres import (
    connect_to_db,
    get_conn_params,
    postgres_common_argument_spec,
)

executed_queries = []


def lang_exists(cursor, lang):
    """Checks if language exists for db"""
    query = "SELECT lanname FROM pg_language WHERE lanname = '%s'" % lang
    cursor.execute(query)
    return cursor.rowcount > 0


def lang_istrusted(cursor, lang):
    """Checks if language is trusted for db"""
    query = "SELECT lanpltrusted FROM pg_language WHERE lanname = '%s'" % lang
    cursor.execute(query)
    return cursor.fetchone()[0]


def lang_altertrust(cursor, lang, trust):
    """Changes if language is trusted for db"""
    query = "UPDATE pg_language SET lanpltrusted = '%s' WHERE lanname = '%s'" % (trust, lang)
    executed_queries.append(query)
    cursor.execute(query)
    return True


def lang_add(cursor, lang, trust):
    """Adds language for db"""
    if trust:
        query = 'CREATE TRUSTED LANGUAGE "%s"' % lang
    else:
        query = 'CREATE LANGUAGE "%s"' % lang
    executed_queries.append(query)
    cursor.execute(query)
    return True


def lang_drop(cursor, lang, cascade):
    """Drops language for db"""
    cursor.execute("SAVEPOINT ansible_pgsql_lang_drop")
    try:
        if cascade:
            query = "DROP LANGUAGE \"%s\" CASCADE" % lang
        else:
            query = "DROP LANGUAGE \"%s\"" % lang
        executed_queries.append(query)
        cursor.execute(query)
    except Exception:
        cursor.execute("ROLLBACK TO SAVEPOINT ansible_pgsql_lang_drop")
        cursor.execute("RELEASE SAVEPOINT ansible_pgsql_lang_drop")
        return False
    cursor.execute("RELEASE SAVEPOINT ansible_pgsql_lang_drop")
    return True


def main():
    argument_spec = postgres_common_argument_spec()
    argument_spec.update(
        db=dict(type="str", required=True, aliases=["login_db"]),
        lang=dict(type="str", required=True, aliases=["name"]),
        state=dict(type="str", default="present", choices=["absent", "present"]),
        trust=dict(type="bool", default="no"),
        force_trust=dict(type="bool", default="no"),
        cascade=dict(type="bool", default="no"),
        fail_on_drop=dict(type="bool", default="yes"),
        session_role=dict(type="str"),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    db = module.params["db"]
    lang = module.params["lang"]
    state = module.params["state"]
    trust = module.params["trust"]
    force_trust = module.params["force_trust"]
    cascade = module.params["cascade"]
    fail_on_drop = module.params["fail_on_drop"]

    conn_params = get_conn_params(module, module.params)
    db_connection = connect_to_db(module, conn_params, autocommit=False)
    cursor = db_connection.cursor()

    changed = False
    kw = {'db': db, 'lang': lang, 'trust': trust}

    if state == "present":
        if lang_exists(cursor, lang):
            lang_trusted = lang_istrusted(cursor, lang)
            if (lang_trusted and not trust) or (not lang_trusted and trust):
                if module.check_mode:
                    changed = True
                else:
                    changed = lang_altertrust(cursor, lang, trust)
        else:
            if module.check_mode:
                changed = True
            else:
                changed = lang_add(cursor, lang, trust)
                if force_trust:
                    changed = lang_altertrust(cursor, lang, trust)

    else:
        if lang_exists(cursor, lang):
            if module.check_mode:
                changed = True
                kw['lang_dropped'] = True
            else:
                changed = lang_drop(cursor, lang, cascade)
                if fail_on_drop and not changed:
                    msg = "unable to drop language, use cascade to delete dependencies or fail_on_drop=no to ignore"
                    module.fail_json(msg=msg)
                kw['lang_dropped'] = changed

    if changed:
        if module.check_mode:
            db_connection.rollback()
        else:
            db_connection.commit()

    kw['changed'] = changed
    kw['queries'] = executed_queries
    db_connection.close()
    module.exit_json(**kw)


if __name__ == '__main__':
    main()
