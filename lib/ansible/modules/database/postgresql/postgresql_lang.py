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


DOCUMENTATION = '''
---
module: postgresql_lang
short_description: Adds, removes or changes procedural languages with a PostgreSQL database.
description:
   - Adds, removes or changes procedural languages with a PostgreSQL database.
   - This module allows you to add a language, remote a language or change the trust
     relationship with a PostgreSQL database. The module can be used on the machine
     where executed or on a remote host.
   - When removing a language from a database, it is possible that dependencies prevent
     the database from being removed. In that case, you can specify casade to
     automatically drop objects that depend on the language (such as functions in the
     language). In case the language can't be deleted because it is required by the
     database system, you can specify fail_on_drop=no to ignore the error.
   - Be carefull when marking a language as trusted since this could be a potential
     security breach. Untrusted languages allow only users with the PostgreSQL superuser
     privilege to use this language to create new functions.
version_added: "1.7"
options:
  lang:
    description:
      - name of the procedural language to add, remove or change
    required: true
    default: null
  trust:
    description:
      - make this language trusted for the selected db
    required: false
    default: no
    choices: [ "yes", "no" ]
  db:
    description:
      - name of database where the language will be added, removed or changed
    required: false
    default: null
  force_trust:
    description:
      - marks the language as trusted, even if it's marked as untrusted in pg_pltemplate.
      - use with care!
    required: false
    default: no
    choices: [ "yes", "no" ]
  fail_on_drop:
    description:
      - if C(yes), fail when removing a language. Otherwise just log and continue
      - in some cases, it is not possible to remove a language (used by the db-system). When         dependencies block the removal, consider using C(cascade).
    required: false
    default: 'yes'
    choices: [ "yes", "no" ]
  cascade:
    description:
      - when dropping a language, also delete object that depend on this language.
      - only used when C(state=absent).
    required: false
    default: no
    choices: [ "yes", "no" ]
  port:
    description:
      - Database port to connect to.
    required: false
    default: 5432
  login_user:
    description:
      - User used to authenticate with PostgreSQL
    required: false
    default: postgres
  login_password:
    description:
      - Password used to authenticate with PostgreSQL (must match C(login_user))
    required: false
    default: null
  login_host:
    description:
      - Host running PostgreSQL where you want to execute the actions.
    required: false
    default: localhost
  state:
    description:
      - The state of the language for the selected database
    required: false
    default: present
    choices: [ "present", "absent" ]
notes:
   - The default authentication assumes that you are either logging in as or
     sudo'ing to the postgres account on the host.
   - This module uses psycopg2, a Python PostgreSQL database adapter. You must
     ensure that psycopg2 is installed on the host before using this module. If
     the remote host is the PostgreSQL server (which is the default case), then
     PostgreSQL must also be installed on the remote host. For Ubuntu-based
     systems, install the postgresql, libpq-dev, and python-psycopg2 packages
     on the remote host before using this module.
requirements: [ psycopg2 ]
author: "Jens Depuydt (@jensdepuydt)"
'''

EXAMPLES = '''
# Add language pltclu to database testdb if it doesn't exist:
- postgresql_lang db=testdb lang=pltclu state=present

# Add language pltclu to database testdb if it doesn't exist and mark it as trusted:
# Marks the language as trusted if it exists but isn't trusted yet
# force_trust makes sure that the language will be marked as trusted
- postgresql_lang:
    db: testdb
    lang: pltclu
    state: present
    trust: yes
    force_trust: yes

# Remove language pltclu from database testdb:
- postgresql_lang:
    db: testdb
    lang: pltclu
    state: absent

# Remove language pltclu from database testdb and remove all dependencies:
- postgresql_lang:
    db: testdb
    lang: pltclu
    state: absent
    cascade: yes

# Remove language c from database testdb but ignore errors if something prevents the removal:
- postgresql_lang:
    db: testdb
    lang: pltclu
    state: absent
    fail_on_drop: no
'''
import traceback

try:
    import psycopg2
except ImportError:
    postgresqldb_found = False
else:
    postgresqldb_found = True

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native


def lang_exists(cursor, lang):
    """Checks if language exists for db"""
    query = "SELECT lanname FROM pg_language WHERE lanname='%s'" % lang
    cursor.execute(query)
    return cursor.rowcount > 0


def lang_istrusted(cursor, lang):
    """Checks if language is trusted for db"""
    query = "SELECT lanpltrusted FROM pg_language WHERE lanname='%s'" % lang
    cursor.execute(query)
    return cursor.fetchone()[0]


def lang_altertrust(cursor, lang, trust):
    """Changes if language is trusted for db"""
    query = "UPDATE pg_language SET lanpltrusted = %s WHERE lanname=%s"
    cursor.execute(query, (trust, lang))
    return True


def lang_add(cursor, lang, trust):
    """Adds language for db"""
    if trust:
        query = 'CREATE TRUSTED LANGUAGE "%s"' % lang
    else:
        query = 'CREATE LANGUAGE "%s"' % lang
    cursor.execute(query)
    return True


def lang_drop(cursor, lang, cascade):
    """Drops language for db"""
    cursor.execute("SAVEPOINT ansible_pgsql_lang_drop")
    try:
        if cascade:
            cursor.execute("DROP LANGUAGE \"%s\" CASCADE" % lang)
        else:
            cursor.execute("DROP LANGUAGE \"%s\"" % lang)
    except:
        cursor.execute("ROLLBACK TO SAVEPOINT ansible_pgsql_lang_drop")
        cursor.execute("RELEASE SAVEPOINT ansible_pgsql_lang_drop")
        return False
    cursor.execute("RELEASE SAVEPOINT ansible_pgsql_lang_drop")
    return True


def main():
    module = AnsibleModule(
        argument_spec=dict(
            login_user=dict(default="postgres"),
            login_password=dict(default="", no_log=True),
            login_host=dict(default=""),
            db=dict(required=True),
            port=dict(default='5432'),
            lang=dict(required=True),
            state=dict(default="present", choices=["absent", "present"]),
            trust=dict(type='bool', default='no'),
            force_trust=dict(type='bool', default='no'),
            cascade=dict(type='bool', default='no'),
            fail_on_drop=dict(type='bool', default='yes'),
        ),
        supports_check_mode=True
    )

    db = module.params["db"]
    lang = module.params["lang"]
    state = module.params["state"]
    trust = module.params["trust"]
    force_trust = module.params["force_trust"]
    cascade = module.params["cascade"]
    fail_on_drop = module.params["fail_on_drop"]

    if not postgresqldb_found:
        module.fail_json(msg="the python psycopg2 module is required")

    params_map = {
        "login_host": "host",
        "login_user": "user",
        "login_password": "password",
        "port": "port",
        "db": "database"
    }
    kw = dict((params_map[k], v) for (k, v) in module.params.items()
              if k in params_map and v != "")
    try:
        db_connection = psycopg2.connect(**kw)
        cursor = db_connection.cursor()
    except Exception as e:
        module.fail_json(msg="unable to connect to database: %s" % to_native(e), exception=traceback.format_exc())
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
    module.exit_json(**kw)


if __name__ == '__main__':
    main()
