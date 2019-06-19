# Copyright: (c) 2019, Andrew Klychkov (@Andersson007) <aaklychkov@mail.ru>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import pytest

import ansible.module_utils.postgres as pg


INPUT_DICT = dict(
    session_role=dict(default=''),
    login_user=dict(default='postgres'),
    login_password=dict(default='test', no_log=True),
    login_host=dict(default='test'),
    login_unix_socket=dict(default=''),
    port=dict(type='int', default=5432, aliases=['login_port']),
    ssl_mode=dict(
        default='prefer',
        choices=['allow', 'disable', 'prefer', 'require', 'verify-ca', 'verify-full']
    ),
    ca_cert=dict(aliases=['ssl_rootcert']),
)

EXPECTED_DICT = dict(
    user=dict(default='postgres'),
    password=dict(default='test', no_log=True),
    host=dict(default='test'),
    port=dict(type='int', default=5432, aliases=['login_port']),
    sslmode=dict(
        default='prefer',
        choices=['allow', 'disable', 'prefer', 'require', 'verify-ca', 'verify-full']
    ),
    sslrootcert=dict(aliases=['ssl_rootcert']),
)


class TestPostgresCommonArgSpec():

    """
    Namespace for testing postgresql_common_arg_spec() function.
    """

    def test_postgres_common_argument_spec(self):
        """
        Test for postgresql_common_arg_spec() function.

        The tested function just returns a dictionary with the default
        parameters and their values for PostgreSQL modules.
        The return and expected dictionaries must be compared.
        """
        expected_dict = dict(
            login_user=dict(default='postgres'),
            login_password=dict(default='', no_log=True),
            login_host=dict(default=''),
            login_unix_socket=dict(default=''),
            port=dict(type='int', default=5432, aliases=['login_port']),
            ssl_mode=dict(
                default='prefer',
                choices=['allow', 'disable', 'prefer', 'require', 'verify-ca', 'verify-full']
            ),
            ca_cert=dict(aliases=['ssl_rootcert']),
        )
        assert pg.postgres_common_argument_spec() == expected_dict


@pytest.fixture
def m_psycopg2():
    """Return mock object for psycopg2 emulation."""
    global Cursor
    Cursor = None

    class Cursor():
        def __init__(self):
            self.passed_query = None

        def execute(self, query):
            self.passed_query = query

        def close(self):
            pass

    global DbConnection
    DbConnection = None

    class DbConnection():
        def __init__(self):
            pass

        def cursor(self, cursor_factory=None):
            return Cursor()

        def set_session(self, autocommit=None):
            pass

        def set_isolation_level(self, isolevel):
            pass

    class Extras():
        def __init__(self):
            self.DictCursor = True

    class Extensions():
        def __init__(self):
            self.ISOLATION_LEVEL_AUTOCOMMIT = True

    class DummyPsycopg2():
        def __init__(self):
            self.__version__ = '2.4.3'
            self.extras = Extras()
            self.extensions = Extensions()

        def connect(self, host=None, port=None, user=None,
                    password=None, sslmode=None, sslrootcert=None):
            if user == 'Exception':
                raise Exception()

            return DbConnection()

    return DummyPsycopg2()


class TestEnsureReqLibs():

    """
    Namespace for testing ensure_required_libs() function.

    If there is something wrong with libs, the function invokes fail_json()
    method of AnsibleModule object passed as an argument called 'module'.
    Therefore we must check:
    1. value of err_msg attribute of m_ansible_module mock object.
    """

    @pytest.fixture(scope='class')
    def m_ansible_module(self):
        """Return an object of dummy AnsibleModule class."""
        class Dummym_ansible_module():
            def __init__(self):
                self.params = {'ca_cert': False}
                self.err_msg = ''

            def fail_json(self, msg):
                self.err_msg = msg

        return Dummym_ansible_module()

    def test_ensure_req_libs_has_not_psycopg2(self, m_ansible_module):
        """Test ensure_required_libs() with psycopg2 is None."""
        # HAS_PSYCOPG2 is False by default
        pg.ensure_required_libs(m_ansible_module)
        assert 'Failed to import the required Python library (psycopg2)' in m_ansible_module.err_msg

    def test_ensure_req_libs_has_psycopg2(self, m_ansible_module, monkeypatch):
        """Test ensure_required_libs() with psycopg2 is not None."""
        monkeypatch.setattr(pg, 'HAS_PSYCOPG2', True)

        pg.ensure_required_libs(m_ansible_module)
        assert m_ansible_module.err_msg == ''

    def test_ensure_req_libs_ca_cert(self, m_ansible_module, m_psycopg2, monkeypatch):
        """
        Test with module.params['ca_cert'], psycopg2 version is suitable.
        """
        m_ansible_module.params['ca_cert'] = True
        monkeypatch.setattr(pg, 'HAS_PSYCOPG2', True)
        monkeypatch.setattr(pg, 'psycopg2', m_psycopg2)

        pg.ensure_required_libs(m_ansible_module)
        assert m_ansible_module.err_msg == ''

    def test_ensure_req_libs_ca_cert_low_psycopg2_ver(self, m_ansible_module, m_psycopg2, monkeypatch):
        """
        Test with module.params['ca_cert'], psycopg2 version is wrong.
        """
        m_ansible_module.params['ca_cert'] = True
        monkeypatch.setattr(pg, 'HAS_PSYCOPG2', True)
        # Set wrong psycopg2 version number:
        psycopg2 = m_psycopg2
        psycopg2.__version__ = '2.4.2'
        monkeypatch.setattr(pg, 'psycopg2', psycopg2)

        pg.ensure_required_libs(m_ansible_module)
        assert 'psycopg2 must be at least 2.4.3' in m_ansible_module.err_msg


@pytest.fixture(scope='class')
def m_ansible_module():
    """Return an object of dummy AnsibleModule class."""
    class DummyAnsibleModule():
        def __init__(self):
            self.params = pg.postgres_common_argument_spec()
            self.err_msg = ''
            self.warn_msg = ''

        def fail_json(self, msg):
            self.err_msg = msg

        def warn(self, msg):
            self.warn_msg = msg

    return DummyAnsibleModule()


class TestConnectToDb():

    """
    Namespace for testing connect_to_db() function.

    When some connection errors occure connect_to_db() caught any of them
    and invoke fail_json() or warn() methods of AnsibleModule object
    depending on the passed parameters.
    connect_to_db may return db_connection object or None if errors occured.
    Therefore we must check:
    1. Values of err_msg and warn_msg attributes of m_ansible_module mock object.
    2. Types of return objects (db_connection and cursor).
    """

    def test_connect_to_db(self, m_ansible_module, monkeypatch, m_psycopg2):
        """Test connect_to_db(), common test."""
        monkeypatch.setattr(pg, 'HAS_PSYCOPG2', True)
        monkeypatch.setattr(pg, 'psycopg2', m_psycopg2)

        conn_params = pg.get_conn_params(m_ansible_module, m_ansible_module.params)
        db_connection = pg.connect_to_db(m_ansible_module, conn_params)
        cursor = db_connection.cursor()
        # if errors, db_connection returned as None:
        assert isinstance(db_connection, DbConnection)
        assert isinstance(cursor, Cursor)
        assert m_ansible_module.err_msg == ''
        # The default behaviour, normal in this case:
        assert 'Database name has not been passed' in m_ansible_module.warn_msg

    def test_session_role(self, m_ansible_module, monkeypatch, m_psycopg2):
        """Test connect_to_db(), switch on session_role."""
        monkeypatch.setattr(pg, 'HAS_PSYCOPG2', True)
        monkeypatch.setattr(pg, 'psycopg2', m_psycopg2)

        m_ansible_module.params['session_role'] = 'test_role'
        conn_params = pg.get_conn_params(m_ansible_module, m_ansible_module.params)
        db_connection = pg.connect_to_db(m_ansible_module, conn_params)
        cursor = db_connection.cursor()
        # if errors, db_connection returned as None:
        assert isinstance(db_connection, DbConnection)
        assert isinstance(cursor, Cursor)
        assert m_ansible_module.err_msg == ''
        # The default behaviour, normal in this case:
        assert 'Database name has not been passed' in m_ansible_module.warn_msg

    def test_fail_on_conn_true(self, m_ansible_module, monkeypatch, m_psycopg2):
        """
        Test connect_to_db(), fail_on_conn arg passed as True (the default behavior).
        """
        monkeypatch.setattr(pg, 'HAS_PSYCOPG2', True)
        monkeypatch.setattr(pg, 'psycopg2', m_psycopg2)

        m_ansible_module.params['login_user'] = 'Exception'  # causes Exception

        conn_params = pg.get_conn_params(m_ansible_module, m_ansible_module.params)
        db_connection = pg.connect_to_db(m_ansible_module, conn_params, fail_on_conn=True)

        assert 'unable to connect to database' in m_ansible_module.err_msg
        assert db_connection is None

    def test_fail_on_conn_false(self, m_ansible_module, monkeypatch, m_psycopg2):
        """
        Test connect_to_db(), fail_on_conn arg passed as False.
        """
        monkeypatch.setattr(pg, 'HAS_PSYCOPG2', True)
        monkeypatch.setattr(pg, 'psycopg2', m_psycopg2)

        m_ansible_module.params['login_user'] = 'Exception'  # causes Exception

        conn_params = pg.get_conn_params(m_ansible_module, m_ansible_module.params)
        db_connection = pg.connect_to_db(m_ansible_module, conn_params, fail_on_conn=False)

        assert m_ansible_module.err_msg == ''
        assert 'PostgreSQL server is unavailable' in m_ansible_module.warn_msg
        assert db_connection is None

    def test_autocommit_true(self, m_ansible_module, monkeypatch, m_psycopg2):
        """
        Test connect_to_db(), autocommit arg passed as True (the default is False).
        """
        monkeypatch.setattr(pg, 'HAS_PSYCOPG2', True)

        # case 1: psycopg2.__version >= 2.4.2 (the default in m_psycopg2)
        monkeypatch.setattr(pg, 'psycopg2', m_psycopg2)

        conn_params = pg.get_conn_params(m_ansible_module, m_ansible_module.params)
        db_connection = pg.connect_to_db(m_ansible_module, conn_params, autocommit=True)
        cursor = db_connection.cursor()

        # if errors, db_connection returned as None:
        assert isinstance(db_connection, DbConnection)
        assert isinstance(cursor, Cursor)
        assert m_ansible_module.err_msg == ''

        # case 2: psycopg2.__version < 2.4.2
        m_psycopg2.__version__ = '2.4.1'
        monkeypatch.setattr(pg, 'psycopg2', m_psycopg2)

        conn_params = pg.get_conn_params(m_ansible_module, m_ansible_module.params)
        db_connection = pg.connect_to_db(m_ansible_module, conn_params, autocommit=True)
        cursor = db_connection.cursor()

        # if errors, db_connection returned as None:
        assert isinstance(db_connection, DbConnection)
        assert isinstance(cursor, Cursor)
        assert 'psycopg2 must be at least 2.4.3' in m_ansible_module.err_msg


class TestGetConnParams():

    """Namespace for testing get_conn_params() function."""

    def test_get_conn_params_def(self, m_ansible_module):
        """Test get_conn_params(), warn_db_default kwarg is default."""
        assert pg.get_conn_params(m_ansible_module, INPUT_DICT) == EXPECTED_DICT
        assert m_ansible_module.warn_msg == 'Database name has not been passed, used default database to connect to.'

    def test_get_conn_params_warn_db_def_false(self, m_ansible_module):
        """Test get_conn_params(), warn_db_default kwarg is False."""
        assert pg.get_conn_params(m_ansible_module, INPUT_DICT, warn_db_default=False) == EXPECTED_DICT
        assert m_ansible_module.warn_msg == ''
