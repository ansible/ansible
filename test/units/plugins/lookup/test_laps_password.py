# -*- coding: utf-8 -*-
# (c) 2019, Jordan Borean <jborean@redhat.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import platform
import pytest
import sys

from units.compat.mock import patch, MagicMock

from ansible.errors import AnsibleError
from ansible.plugins.lookup import laps_password

ldap = pytest.importorskip("ldap")


@pytest.fixture("function")
def reset_imports():
    # ensure the changes to these globals aren't persisted after each test
    orig_has_gssapi = laps_password.HAS_GSSAPI
    orig_gssapi_imp_err = laps_password.GSSAPI_IMP_ERR
    orig_has_ldap = laps_password.HAS_LDAP
    orig_ldap_imp_err = laps_password.LDAP_IMP_ERR
    yield None
    laps_password.HAS_GSSAPI = orig_has_gssapi
    laps_password.GSSAPI_IMP_ERR = orig_gssapi_imp_err
    laps_password.HAS_LDAP = orig_has_ldap
    laps_password.LDAP_IMP_ERR = orig_ldap_imp_err


def test_missing_ldap(reset_imports):
    laps_password.HAS_LDAP = False
    laps_password.LDAP_IMP_ERR = "no import for you!"

    with pytest.raises(AnsibleError) as err:
        laps_password.LookupModule().run(["host"])

    assert str(err.value) == "Failed to import the required Python library (python-ldap) on %s's Python %s. See " \
                             "https://pypi.org/project/python-ldap/ for more info. Please read module documentation " \
                             "and install in the appropriate location. " \
                             "Import Error: no import for you!" % (platform.node(), sys.executable)


def test_invalid_cert_mapping():
    with pytest.raises(AnsibleError) as err:
        laps_password.LookupModule().run(["host"], validate_certs="incorrect")

    assert str(err.value) == "Invalid validate_certs value 'incorrect': valid values are 'allow', 'demand', " \
                             "'never', 'try'"


def test_invalid_auth():
    with pytest.raises(AnsibleError) as err:
        laps_password.LookupModule().run(["host"], auth="fail")

    assert str(err.value) == "Invalid auth value 'fail': expecting either 'gssapi', or 'simple'"


def test_gssapi_without_sasl(monkeypatch):
    monkeypatch.setattr("ldap.SASL_AVAIL", 0)

    with pytest.raises(AnsibleError) as err:
        laps_password.LookupModule().run(["host"])

    assert str(err.value) == "Cannot use auth=gssapi when SASL is not configured with the local LDAP install"


def test_simple_auth_without_credentials():
    with pytest.raises(AnsibleError) as err:
        laps_password.LookupModule().run(["host"], auth="simple")

    assert str(err.value) == "The username and password values are required when auth=simple"


def test_password_not_set_with_username():
    with pytest.raises(AnsibleError) as err:
        laps_password.LookupModule().run(["host"], username="test")

    assert str(err.value) == "The password must be set if username is also set"


def test_not_encrypted_without_override():
    with pytest.raises(AnsibleError) as err:
        laps_password.LookupModule().run(["host"], kdc="dc01", auth="simple", username="test", password="test")

    assert str(err.value) == "Current configuration will result in plaintext traffic exposing credentials. Set " \
                             "auth=gssapi, scheme=ldaps, start_tls=True, or allow_plaintext=True to continue"


def test_ldaps_without_tls(monkeypatch):
    monkeypatch.setattr("ldap.TLS_AVAIL", 0)

    with pytest.raises(AnsibleError) as err:
        laps_password.LookupModule().run(["host"], kdc="dc01", scheme="ldaps")

    assert str(err.value) == "Cannot use TLS as the local LDAP installed has not been configured to support it"


def test_start_tls_without_tls(monkeypatch):
    monkeypatch.setattr("ldap.TLS_AVAIL", 0)

    with pytest.raises(AnsibleError) as err:
        laps_password.LookupModule().run(["host"], kdc="dc01", start_tls=True)

    assert str(err.value) == "Cannot use TLS as the local LDAP installed has not been configured to support it"


def test_normal_run(monkeypatch):
    def get_laps_password(conn, cn, search_base):
        return "CN=%s,%s" % (cn, search_base)

    mock_ldap = MagicMock()
    mock_ldap.return_value.read_rootdse_s.return_value = {"defaultNamingContext": ["DC=domain,DC=com"]}
    monkeypatch.setattr("ldap.initialize", mock_ldap)

    mock_get_laps_password = MagicMock(side_effect=get_laps_password)
    monkeypatch.setattr(laps_password, "get_laps_password", mock_get_laps_password)

    actual = laps_password.LookupModule().run(["host1", "host2"], kdc="dc01")
    assert actual == ["CN=host1,DC=domain,DC=com", "CN=host2,DC=domain,DC=com"]

    # Verify the call count to get_laps_password
    assert mock_get_laps_password.call_count == 2

    # Verify the initialize() method call
    assert mock_ldap.call_count == 1
    assert mock_ldap.call_args[0] == ("ldap://dc01:389",)
    assert mock_ldap.call_args[1] == {"bytes_mode": False}

    # Verify the number of calls made to the mocked LDAP object
    assert mock_ldap.mock_calls[1][0] == "().set_option"
    assert mock_ldap.mock_calls[1][1] == (ldap.OPT_PROTOCOL_VERSION, 3)

    assert mock_ldap.mock_calls[2][0] == "().set_option"
    assert mock_ldap.mock_calls[2][1] == (ldap.OPT_REFERRALS, 0)

    assert mock_ldap.mock_calls[3][0] == '().sasl_gssapi_bind_s'
    assert mock_ldap.mock_calls[3][1] == ()

    assert mock_ldap.mock_calls[4][0] == "().read_rootdse_s"
    assert mock_ldap.mock_calls[4][1] == ()

    assert mock_ldap.mock_calls[5][0] == "().unbind_s"
    assert mock_ldap.mock_calls[5][1] == ()


def test_run_with_simple_auth_and_search_base(monkeypatch):
    def get_laps_password(conn, cn, search_base):
        return "CN=%s,%s" % (cn, search_base)

    mock_ldap = MagicMock()
    monkeypatch.setattr("ldap.initialize", mock_ldap)

    mock_get_laps_password = MagicMock(side_effect=get_laps_password)
    monkeypatch.setattr(laps_password, "get_laps_password", mock_get_laps_password)

    actual = laps_password.LookupModule().run(["host1", "host2"], kdc="dc01", auth="simple", username="user",
                                              password="pass", allow_plaintext=True,
                                              search_base="OU=Workstations,DC=domain,DC=com")
    assert actual == ["CN=host1,OU=Workstations,DC=domain,DC=com", "CN=host2,OU=Workstations,DC=domain,DC=com"]

    # Verify the call count to get_laps_password
    assert mock_get_laps_password.call_count == 2

    # Verify the initialize() method call
    assert mock_ldap.call_count == 1
    assert mock_ldap.call_args[0] == ("ldap://dc01:389",)
    assert mock_ldap.call_args[1] == {"bytes_mode": False}

    # Verify the number of calls made to the mocked LDAP object
    assert mock_ldap.mock_calls[1][0] == "().set_option"
    assert mock_ldap.mock_calls[1][1] == (ldap.OPT_PROTOCOL_VERSION, 3)

    assert mock_ldap.mock_calls[2][0] == "().set_option"
    assert mock_ldap.mock_calls[2][1] == (ldap.OPT_REFERRALS, 0)

    assert mock_ldap.mock_calls[3][0] == '().bind_s'
    assert mock_ldap.mock_calls[3][1] == (u"user", u"pass")

    assert mock_ldap.mock_calls[4][0] == "().unbind_s"
    assert mock_ldap.mock_calls[4][1] == ()


@pytest.mark.parametrize("kwargs, expected", [
    [{"kdc": "dc01"}, "ldap://dc01:389"],
    [{"kdc": "dc02", "port": 1234}, "ldap://dc02:1234"],
    [{"kdc": "dc03", "scheme": "ldaps"}, "ldaps://dc03:636"],
    # Verifies that an explicit URI ignores port and scheme
    [{"kdc": "ldap://dc04", "port": 1234, "scheme": "ldaps"}, "ldap://dc04"],
])
def test_uri_options(monkeypatch, kwargs, expected):
    mock_ldap = MagicMock()
    monkeypatch.setattr("ldap.initialize", mock_ldap)

    laps_password.LookupModule().run([], **kwargs)

    assert mock_ldap.call_count == 1
    assert mock_ldap.call_args[0] == (expected,)
    assert mock_ldap.call_args[1] == {"bytes_mode": False}


@pytest.mark.parametrize("validate, expected", [
    ["never", ldap.OPT_X_TLS_NEVER],
    ["allow", ldap.OPT_X_TLS_ALLOW],
    ["try", ldap.OPT_X_TLS_TRY],
    ["demand", ldap.OPT_X_TLS_DEMAND],
])
def test_certificate_validation(monkeypatch, validate, expected):
    mock_ldap = MagicMock()
    monkeypatch.setattr("ldap.initialize", mock_ldap)

    laps_password.LookupModule().run([], kdc="dc01", start_tls=True, validate_certs=validate)

    assert mock_ldap.mock_calls[3][0] == "().set_option"
    assert mock_ldap.mock_calls[3][1] == (ldap.OPT_X_TLS_REQUIRE_CERT, expected)

    assert mock_ldap.mock_calls[4][0] == "().set_option"
    assert mock_ldap.mock_calls[4][1] == (ldap.OPT_X_TLS_NEWCTX, 0)

    assert mock_ldap.mock_calls[5][0] == "().start_tls_s"
    assert mock_ldap.mock_calls[5][1] == ()

    assert mock_ldap.mock_calls[6][0] == "().sasl_gssapi_bind_s"
    assert mock_ldap.mock_calls[6][1] == ()


def test_certificate_validate_with_custom_cacert(monkeypatch):
    mock_ldap = MagicMock()
    monkeypatch.setattr("ldap.initialize", mock_ldap)

    laps_password.LookupModule().run([], kdc="dc01", scheme="ldaps", cacert_file="cacert.pem")

    assert mock_ldap.mock_calls[3][0] == "().set_option"
    assert mock_ldap.mock_calls[3][1] == (ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_DEMAND)

    assert mock_ldap.mock_calls[4][0] == "().set_option"
    assert mock_ldap.mock_calls[4][1] == (ldap.OPT_X_TLS_CACERTFILE, u"cacert.pem")

    assert mock_ldap.mock_calls[5][0] == "().set_option"
    assert mock_ldap.mock_calls[5][1] == (ldap.OPT_X_TLS_NEWCTX, 0)

    assert mock_ldap.mock_calls[6][0] == "().sasl_gssapi_bind_s"
    assert mock_ldap.mock_calls[6][1] == ()


def test_certificate_validate_with_custom_cacert_fail(monkeypatch):
    def set_option(key, value):
        if key == ldap.OPT_X_TLS_CACERTFILE:
            raise ValueError("set_option() failed")

    mock_ldap = MagicMock()
    mock_ldap.return_value.set_option.side_effect = set_option
    monkeypatch.setattr("ldap.initialize", mock_ldap)

    with pytest.raises(AnsibleError) as err:
        laps_password.LookupModule().run([], kdc="dc01", scheme="ldaps", cacert_file="cacert.pem")

    assert str(err.value) == "Failed to set path to cacert file, this is a known issue with older OpenLDAP " \
                             "libraries on the host. Update OpenLDAP and reinstall python-ldap to continue"


def test_simple_auth_with_ldaps(monkeypatch):
    mock_ldap = MagicMock()
    monkeypatch.setattr("ldap.initialize", mock_ldap)

    laps_password.LookupModule().run([], kdc="dc01", scheme="ldaps", auth="simple", username="user", password="pass")

    assert mock_ldap.mock_calls[3][0] == "().set_option"
    assert mock_ldap.mock_calls[3][1] == (ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_DEMAND)

    assert mock_ldap.mock_calls[4][0] == "().set_option"
    assert mock_ldap.mock_calls[4][1] == (ldap.OPT_X_TLS_NEWCTX, 0)

    assert mock_ldap.mock_calls[5][0] == '().bind_s'
    assert mock_ldap.mock_calls[5][1] == (u"user", u"pass")

    assert mock_ldap.mock_calls[6][0] == "().read_rootdse_s"
    assert mock_ldap.mock_calls[6][1] == ()


def test_simple_auth_with_start_tls(monkeypatch):
    mock_ldap = MagicMock()
    monkeypatch.setattr("ldap.initialize", mock_ldap)

    laps_password.LookupModule().run([], kdc="dc01", start_tls=True, auth="simple", username="user", password="pass")

    assert mock_ldap.mock_calls[3][0] == "().set_option"
    assert mock_ldap.mock_calls[3][1] == (ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_DEMAND)

    assert mock_ldap.mock_calls[4][0] == "().set_option"
    assert mock_ldap.mock_calls[4][1] == (ldap.OPT_X_TLS_NEWCTX, 0)

    assert mock_ldap.mock_calls[5][0] == "().start_tls_s"
    assert mock_ldap.mock_calls[5][1] == ()

    assert mock_ldap.mock_calls[6][0] == '().bind_s'
    assert mock_ldap.mock_calls[6][1] == (u"user", u"pass")

    assert mock_ldap.mock_calls[7][0] == "().read_rootdse_s"
    assert mock_ldap.mock_calls[7][1] == ()


def test_gssapi_with_explicit_credentials(monkeypatch):
    mock_kinit = MagicMock()
    monkeypatch.setattr(laps_password, "kinit", mock_kinit)

    mock_ldap = MagicMock()
    monkeypatch.setattr("ldap.initialize", mock_ldap)

    laps_password.LookupModule().run([], kdc="dc01", username="user", password="pass")

    # Assert we called kinit at least once
    assert mock_kinit.call_count == 1
    assert mock_kinit.call_args[0] == ("user", "pass")

    # Verify the number of calls made to the mocked LDAP object
    assert mock_ldap.mock_calls[1][0] == "().set_option"
    assert mock_ldap.mock_calls[1][1] == (ldap.OPT_PROTOCOL_VERSION, 3)

    assert mock_ldap.mock_calls[2][0] == "().set_option"
    assert mock_ldap.mock_calls[2][1] == (ldap.OPT_REFERRALS, 0)

    assert mock_ldap.mock_calls[3][0] == '().sasl_gssapi_bind_s'
    assert mock_ldap.mock_calls[3][1] == ()

    assert mock_ldap.mock_calls[4][0] == "().read_rootdse_s"
    assert mock_ldap.mock_calls[4][1] == ()


def test_gssapi_with_explicit_credentials_no_gssapi(monkeypatch):
    laps_password.HAS_GSSAPI = False
    laps_password.GSSAPI_IMP_ERR = "no import for you!"

    mock_ldap = MagicMock()
    monkeypatch.setattr("ldap.initialize", mock_ldap)

    with pytest.raises(AnsibleError) as err:
        laps_password.LookupModule().run([], kdc="dc01", username="user", password="pass")

    assert str(err.value) == "Failed to import the required Python library (gssapi) on %s's Python %s. This is " \
                             "required for explicit credentials with auth=gssapi. See " \
                             "https://pypi.org/project/gssapi/ for more info. Please read module documentation " \
                             "and install in the appropriate location. " \
                             "Import Error: no import for you!" % (platform.node(), sys.executable)


def test_get_password_valid():
    mock_conn = MagicMock()
    mock_conn.search_s.return_value = [
        ("CN=server,DC=domain,DC=local",
         {"ms-Mcs-AdmPwd": ["pass"], "distinguishedName": ["CN=server,DC=domain,DC=local"]}),
        # Replicates the 3 extra entries AD returns that aren't server objects
        (None, ["ldap://ForestDnsZones.domain.com/DC=ForestDnsZones,DC=domain,DC=com"]),
        (None, ["ldap://DomainDnsZones.domain.com/DC=DomainDnsZones,DC=domain,DC=com"]),
        (None, ["ldap://domain.com/CN=Configuration,DC=domain,DC=com"]),
    ]

    actual = laps_password.get_laps_password(mock_conn, "server", "DC=domain,DC=local")
    assert actual == "pass"

    assert len(mock_conn.method_calls) == 1
    assert mock_conn.method_calls[0][0] == "search_s"
    assert mock_conn.method_calls[0][1] == ("DC=domain,DC=local", ldap.SCOPE_SUBTREE,
                                            "(&(objectClass=computer)(CN=server))")
    assert mock_conn.method_calls[0][2] == {"attrlist": ["distinguishedName", "ms-Mcs-AdmPwd"]}


def test_get_password_laps_not_configured():
    mock_conn = MagicMock()
    mock_conn.search_s.return_value = [
        ("CN=server,DC=domain,DC=local", {"distinguishedName": ["CN=server,DC=domain,DC=local"]}),
        (None, ["ldap://ForestDnsZones.domain.com/DC=ForestDnsZones,DC=domain,DC=com"]),
        (None, ["ldap://DomainDnsZones.domain.com/DC=DomainDnsZones,DC=domain,DC=com"]),
        (None, ["ldap://domain.com/CN=Configuration,DC=domain,DC=com"]),
    ]

    with pytest.raises(AnsibleError) as err:
        laps_password.get_laps_password(mock_conn, "server2", "DC=test,DC=local")
    assert str(err.value) == \
        "The server 'CN=server,DC=domain,DC=local' did not have the LAPS attribute 'ms-Mcs-AdmPwd'"

    assert len(mock_conn.method_calls) == 1
    assert mock_conn.method_calls[0][0] == "search_s"
    assert mock_conn.method_calls[0][1] == ("DC=test,DC=local", ldap.SCOPE_SUBTREE,
                                            "(&(objectClass=computer)(CN=server2))")
    assert mock_conn.method_calls[0][2] == {"attrlist": ["distinguishedName", "ms-Mcs-AdmPwd"]}


def test_get_password_no_results():
    mock_conn = MagicMock()
    mock_conn.search_s.return_value = [
        (None, ["ldap://ForestDnsZones.domain.com/DC=ForestDnsZones,DC=domain,DC=com"]),
        (None, ["ldap://DomainDnsZones.domain.com/DC=DomainDnsZones,DC=domain,DC=com"]),
        (None, ["ldap://domain.com/CN=Configuration,DC=domain,DC=com"]),
    ]

    with pytest.raises(AnsibleError) as err:
        laps_password.get_laps_password(mock_conn, "server", "DC=domain,DC=local")
    assert str(err.value) == "Failed to find the server 'server' in the base 'DC=domain,DC=local'"

    assert len(mock_conn.method_calls) == 1
    assert mock_conn.method_calls[0][0] == "search_s"
    assert mock_conn.method_calls[0][1] == ("DC=domain,DC=local", ldap.SCOPE_SUBTREE,
                                            "(&(objectClass=computer)(CN=server))")
    assert mock_conn.method_calls[0][2] == {"attrlist": ["distinguishedName", "ms-Mcs-AdmPwd"]}


def test_get_password_multiple_results():
    mock_conn = MagicMock()
    mock_conn.search_s.return_value = [
        ("CN=server,OU=Workstations,DC=domain,DC=local",
         {"ms-Mcs-AdmPwd": ["pass"], "distinguishedName": ["CN=server,OU=Workstations,DC=domain,DC=local"]}),
        ("CN=server,OU=Servers,DC=domain,DC=local",
         {"ms-Mcs-AdmPwd": ["pass"], "distinguishedName": ["CN=server,OU=Servers,DC=domain,DC=local"]}),
        (None, ["ldap://ForestDnsZones.domain.com/DC=ForestDnsZones,DC=domain,DC=com"]),
        (None, ["ldap://DomainDnsZones.domain.com/DC=DomainDnsZones,DC=domain,DC=com"]),
        (None, ["ldap://domain.com/CN=Configuration,DC=domain,DC=com"]),
    ]

    with pytest.raises(AnsibleError) as err:
        laps_password.get_laps_password(mock_conn, "server", "DC=domain,DC=local")
    assert str(err.value) == \
        "Found too many results for the server 'server' in the base 'DC=domain,DC=local'. Specify a more explicit " \
        "search base for the server required. Found servers 'CN=server,OU=Workstations,DC=domain,DC=local', " \
        "'CN=server,OU=Servers,DC=domain,DC=local'"

    assert len(mock_conn.method_calls) == 1
    assert mock_conn.method_calls[0][0] == "search_s"
    assert mock_conn.method_calls[0][1] == ("DC=domain,DC=local", ldap.SCOPE_SUBTREE,
                                            "(&(objectClass=computer)(CN=server))")
    assert mock_conn.method_calls[0][2] == {"attrlist": ["distinguishedName", "ms-Mcs-AdmPwd"]}
