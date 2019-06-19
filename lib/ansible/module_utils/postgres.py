# This code is part of Ansible, but is an independent component.
# This particular file snippet, and this file snippet only, is BSD licensed.
# Modules you write using this snippet, which is embedded dynamically by Ansible
# still belong to the author of the module, and may assign their own license
# to the complete work.
#
# Copyright (c), Ted Timmons <ted@timmons.me>, 2017.
# Most of this was originally added by other creators in the postgresql_user module.
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
    import psycopg2
    from psycopg2.extras import DictCursor
    HAS_PSYCOPG2 = True
except ImportError:
    HAS_PSYCOPG2 = False

from ansible.module_utils.basic import missing_required_lib
from ansible.module_utils._text import to_native
from ansible.module_utils.six import iteritems
from distutils.version import LooseVersion


class LibraryError(Exception):
    pass


def ensure_libs(sslrootcert=None):
    if not HAS_PSYCOPG2:
        raise LibraryError('psycopg2 is not installed. we need psycopg2.')
    if sslrootcert and psycopg2.__version__ < '2.4.3':
        raise LibraryError('psycopg2 must be at least 2.4.3 in order to use the ca_cert parameter')

    # no problems
    return None


def postgres_common_argument_spec():
    return dict(
        login_user=dict(default='postgres'),
        login_password=dict(default='', no_log=True),
        login_host=dict(default=''),
        login_unix_socket=dict(default=''),
        port=dict(type='int', default=5432, aliases=['login_port']),
        ssl_mode=dict(default='prefer', choices=['allow', 'disable', 'prefer', 'require', 'verify-ca', 'verify-full']),
        ca_cert=dict(aliases=['ssl_rootcert']),
    )


def ensure_required_libs(module):
    if not HAS_PSYCOPG2:
        module.fail_json(msg=missing_required_lib('psycopg2'))

    if module.params.get('ca_cert') and LooseVersion(psycopg2.__version__) < LooseVersion('2.4.3'):
        module.fail_json(msg='psycopg2 must be at least 2.4.3 in order to use the ca_cert parameter')


def connect_to_db(module, conn_params, autocommit=False, fail_on_conn=True):
    """Connect to a PostgreSQL database.

    Return psycopg2 connection object.

    Args:
        module (AnsibleModule) -- object of ansible.module_utils.basic.AnsibleModule class
        conn_params (dict) -- dictionary with connection parameters

    Kwargs:
        autocommit (bool) -- commit automatically (default False)
        fail_on_conn (bool) -- fail if connection failed or just warn and return None (default True)
    """
    ensure_required_libs(module)

    try:
        db_connection = psycopg2.connect(**conn_params)
        if autocommit:
            if psycopg2.__version__ >= '2.4.2':
                db_connection.set_session(autocommit=True)
            else:
                db_connection.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)

        # Switch role, if specified:
        cursor = db_connection.cursor(cursor_factory=DictCursor)
        if module.params.get('session_role'):
            try:
                cursor.execute('SET ROLE %s' % module.params['session_role'])
            except Exception as e:
                module.fail_json(msg="Could not switch role: %s" % to_native(e))
        cursor.close()

    except TypeError as e:
        if 'sslrootcert' in e.args[0]:
            module.fail_json(msg='Postgresql server must be at least '
                                 'version 8.4 to support sslrootcert')

        if fail_on_conn:
            module.fail_json(msg="unable to connect to database: %s" % to_native(e))
        else:
            module.warn("PostgreSQL server is unavailable: %s" % to_native(e))
            db_connection = None

    except Exception as e:
        if fail_on_conn:
            module.fail_json(msg="unable to connect to database: %s" % to_native(e))
        else:
            module.warn("PostgreSQL server is unavailable: %s" % to_native(e))
            db_connection = None

    return db_connection


def get_conn_params(module, params_dict, warn_db_default=True):
    """Get connection parameters from the passed dictionary.

    Return a dictionary with parameters to connect to PostgreSQL server.

    Args:
        module (AnsibleModule) -- object of ansible.module_utils.basic.AnsibleModule class
        params_dict (dict) -- dictionary with variables

    Kwargs:
        warn_db_default (bool) -- warn that the default DB is used (default True)
    """
    # To use defaults values, keyword arguments must be absent, so
    # check which values are empty and don't include in the return dictionary
    params_map = {
        "login_host": "host",
        "login_user": "user",
        "login_password": "password",
        "port": "port",
        "ssl_mode": "sslmode",
        "ca_cert": "sslrootcert"
    }

    # Might be different in the modules:
    if params_dict.get('db'):
        params_map['db'] = 'database'
    elif params_dict.get('database'):
        params_map['database'] = 'database'
    elif params_dict.get('login_db'):
        params_map['login_db'] = 'database'
    else:
        if warn_db_default:
            module.warn('Database name has not been passed, '
                        'used default database to connect to.')

    kw = dict((params_map[k], v) for (k, v) in iteritems(params_dict)
              if k in params_map and v != '' and v is not None)

    # If a login_unix_socket is specified, incorporate it here.
    is_localhost = "host" not in kw or kw["host"] is None or kw["host"] == "localhost"
    if is_localhost and params_dict["login_unix_socket"] != "":
        kw["host"] = params_dict["login_unix_socket"]

    return kw
