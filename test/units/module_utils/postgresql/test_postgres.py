# Copyright: (c) 2019, Andrew Klychkov (@Andersson007) <aaklychkov@mail.ru>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import pytest

from ansible.module_utils.postgres import (
    ensure_required_libs,
    postgres_common_argument_spec,
)


def test_postgres_common_argument_spec():
    expected_dict = dict(
        login_user=dict(default='postgres'),
        login_password=dict(default='', no_log=True),
        login_host=dict(default=''),
        login_unix_socket=dict(default=''),
        port=dict(type='int', default=5432, aliases=['login_port']),
        ssl_mode=dict(default='prefer', choices=['allow', 'disable', 'prefer', 'require', 'verify-ca', 'verify-full']),
        ca_cert=dict(aliases=['ssl_rootcert']),
    )
    actual_dict = postgres_common_argument_spec()
    assert(expected_dict == actual_dict)


def test_ensure_required_libs_has_psycopg2():
    """
    Test ensure_required_libs() with psycopg2 is not None
    """
    pass


def test_ensure_required_libs_has_not_psycopg2():
    """
    Test ensure_required_libs() with psycopg2 is None
    """
    pass


def test_ensure_required_libs_ca_cert():
    """
    Test ensure_required_libs() with module.params['ca_cert']
    and suitable psycopg2 version
    """
    pass


def test_ensure_required_libs_ca_cert_low_psycopg2_ver():
    """
    Test ensure_required_libs() with module.params['ca_cert']
    and wrong psycopg2 version
    """
    pass


# def ensure_required_libs(module):
#     if not HAS_PSYCOPG2:
#         module.fail_json(msg=missing_required_lib('psycopg2'))
#
#     if module.params.get('ca_cert') and LooseVersion(psycopg2.__version__) < LooseVersion('2.4.3'):
#         module.fail_json(msg='psycopg2 must be at least 2.4.3 in order to use the ca_cert parameter')
