# -*- coding: utf-8 -*-
# (c) 2019, Jordan Borean <jborean@redhat.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
import platform
import pytest
import sys

from units.compat.mock import MagicMock

from ansible.errors import AnsibleLookupError
from ansible.plugins.loader import lookup_loader


class FakeLDAPError(Exception):
    pass


class FakeLDAPAuthUnknownError(Exception):
    pass


class FakeLdap(object):
    SASL_AVAIL = 1
    TLS_AVAIL = 1

    SCOPE_SUBTREE = 2

    OPT_PROTOCOL_VERSION = 17
    OPT_REFERRALS = 8

    OPT_X_TLS_NEVER = 0
    OPT_X_TLS_DEMAND = 2
    OPT_X_TLS_ALLOW = 3
    OPT_X_TLS_TRY = 4

    OPT_X_TLS_CACERTFILE = 24578
    OPT_X_TLS_REQUIRE_CERT = 24582

    LDAPError = FakeLDAPError
    AUTH_UNKNOWN = FakeLDAPAuthUnknownError

    @staticmethod
    def initialize(uri, bytes_mode=None, **kwargs):
        return MagicMock()

    @staticmethod
    def set_option(option, invalue):
        pass


class FakeLdapUrl(object):

    def __init__(self, ldapUrl=None, urlscheme='ldap', hostport='', **kwargs):
        url = ldapUrl if ldapUrl else "%s://%s" % (urlscheme, hostport)
        self.urlscheme = url.split('://', 2)[0].lower()
        self._url = url

    def initializeUrl(self):
        return self._url


def fake_is_ldap_url(s):
    s_lower = s.lower()
    return s_lower.startswith("ldap://") or s_lower.startswith("ldaps://") or s_lower.startswith("ldapi://")


@pytest.fixture(autouse=True)
def laps_password():
    """Imports and the laps_password lookup with a mocks laps module for testing"""

    # Build the fake ldap and ldapurl Python modules
    fake_ldap_obj = FakeLdap()
    fake_ldap_url_obj = MagicMock()
    fake_ldap_url_obj.isLDAPUrl.side_effect = fake_is_ldap_url
    fake_ldap_url_obj.LDAPUrl.side_effect = FakeLdapUrl

    # Take a snapshot of sys.modules before we manipulate it
    orig_modules = sys.modules.copy()
    try:
        sys.modules["ldap"] = fake_ldap_obj
        sys.modules["ldapurl"] = fake_ldap_url_obj

        from ansible.plugins.lookup import laps_password

        # ensure the changes to these globals aren't persisted after each test
        orig_has_ldap = laps_password.HAS_LDAP
        orig_ldap_imp_err = laps_password.LDAP_IMP_ERR

        yield laps_password

        laps_password.HAS_LDAP = orig_has_ldap
        laps_password.LDAP_IMP_ERR = orig_ldap_imp_err
    finally:
        # Restore sys.modules back to our pre-shenanigans
        sys.modules = orig_modules


def test_missing_ldap(laps_password):
    laps_password.HAS_LDAP = False
    laps_password.LDAP_IMP_ERR = "no import for you!"

    with pytest.raises(AnsibleLookupError) as err:
        lookup_loader.get('laps_password').run(["host"], domain="test")

    assert str(err.value) == "Failed to import the required Python library (python-ldap) on %s's Python %s. See " \
                             "https://pypi.org/project/python-ldap/ for more info. Please read module documentation " \
                             "and install in the appropriate location. " \
                             "Import Error: no import for you!" % (platform.node(), sys.executable)


def test_invalid_cert_mapping():
    with pytest.raises(AnsibleLookupError) as err:
        lookup_loader.get('laps_password').run(["host"], domain="test", validate_certs="incorrect")

    assert str(err.value) == "Invalid validate_certs value 'incorrect': valid values are 'allow', 'demand', " \
                             "'never', 'try'"


def test_invalid_auth():
    with pytest.raises(AnsibleLookupError) as err:
        lookup_loader.get('laps_password').run(["host"], domain="test", auth="fail")

    assert str(err.value) == "Invalid auth value 'fail': expecting either 'gssapi', or 'simple'"


def test_gssapi_without_sasl(monkeypatch, ):
    monkeypatch.setattr("ldap.SASL_AVAIL", 0)

    with pytest.raises(AnsibleLookupError) as err:
        lookup_loader.get('laps_password').run(["host"], domain="test")

    assert str(err.value) == "Cannot use auth=gssapi when SASL is not configured with the local LDAP install"


def test_simple_auth_without_credentials():
    with pytest.raises(AnsibleLookupError) as err:
        lookup_loader.get('laps_password').run(["host"], domain="test", auth="simple")

    assert str(err.value) == "The username and password values are required when auth=simple"


def test_gssapi_auth_with_credentials():
    with pytest.raises(AnsibleLookupError) as err:
        lookup_loader.get('laps_password').run(["host"], domain="test", auth="gssapi", username="u", password="p")

    assert str(err.value) == "Explicit credentials are not supported when auth='gssapi'. Call kinit outside of Ansible"


def test_not_encrypted_without_override():
    with pytest.raises(AnsibleLookupError) as err:
        lookup_loader.get('laps_password').run(["host"], domain="dc01", auth="simple", username="test", password="test")

    assert str(err.value) == "Current configuration will result in plaintext traffic exposing credentials. Set " \
                             "auth=gssapi, scheme=ldaps, start_tls=True, or allow_plaintext=True to continue"


def test_ldaps_without_tls(monkeypatch, ):
    monkeypatch.setattr("ldap.TLS_AVAIL", 0)

    with pytest.raises(AnsibleLookupError) as err:
        lookup_loader.get('laps_password').run(["host"], domain="dc01", scheme="ldaps")

    assert str(err.value) == "Cannot use TLS as the local LDAP installed has not been configured to support it"


def test_start_tls_without_tls(monkeypatch, ):
    monkeypatch.setattr("ldap.TLS_AVAIL", 0)

    with pytest.raises(AnsibleLookupError) as err:
        lookup_loader.get('laps_password').run(["host"], domain="dc01", start_tls=True)

    assert str(err.value) == "Cannot use TLS as the local LDAP installed has not been configured to support it"


def test_normal_run(monkeypatch, laps_password):
    def get_laps_password(conn, cn, search_base):
        return "CN=%s,%s" % (cn, search_base)

    mock_ldap = MagicMock()
    mock_ldap.return_value.read_rootdse_s.return_value = {"defaultNamingContext": ["DC=domain,DC=com"]}
    monkeypatch.setattr("ldap.initialize", mock_ldap)

    mock_get_laps_password = MagicMock(side_effect=get_laps_password)
    monkeypatch.setattr(laps_password, "get_laps_password", mock_get_laps_password)

    actual = lookup_loader.get('laps_password').run(["host1", "host2"], domain="dc01")
    assert actual == ["CN=host1,DC=domain,DC=com", "CN=host2,DC=domain,DC=com"]

    # Verify the call count to get_laps_password
    assert mock_get_laps_password.call_count == 2

    # Verify the initialize() method call
    assert mock_ldap.call_count == 1
    assert mock_ldap.call_args[0] == ("ldap://dc01:389",)
    assert mock_ldap.call_args[1] == {"bytes_mode": False}

    # Verify the number of calls made to the mocked LDAP object
    assert mock_ldap.mock_calls[1][0] == "().set_option"
    assert mock_ldap.mock_calls[1][1] == (FakeLdap.OPT_PROTOCOL_VERSION, 3)

    assert mock_ldap.mock_calls[2][0] == "().set_option"
    assert mock_ldap.mock_calls[2][1] == (FakeLdap.OPT_REFERRALS, 0)

    assert mock_ldap.mock_calls[3][0] == '().sasl_gssapi_bind_s'
    assert mock_ldap.mock_calls[3][1] == ()

    assert mock_ldap.mock_calls[4][0] == "().read_rootdse_s"
    assert mock_ldap.mock_calls[4][1] == ()

    assert mock_ldap.mock_calls[5][0] == "().unbind_s"
    assert mock_ldap.mock_calls[5][1] == ()


def test_run_with_simple_auth_and_search_base(monkeypatch, laps_password):
    def get_laps_password(conn, cn, search_base):
        return "CN=%s,%s" % (cn, search_base)

    mock_ldap = MagicMock()
    monkeypatch.setattr("ldap.initialize", mock_ldap)

    mock_get_laps_password = MagicMock(side_effect=get_laps_password)
    monkeypatch.setattr(laps_password, "get_laps_password", mock_get_laps_password)

    actual = lookup_loader.get('laps_password').run(["host1", "host2"], domain="dc01", auth="simple", username="user",
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
    assert mock_ldap.mock_calls[1][1] == (FakeLdap.OPT_PROTOCOL_VERSION, 3)

    assert mock_ldap.mock_calls[2][0] == "().set_option"
    assert mock_ldap.mock_calls[2][1] == (FakeLdap.OPT_REFERRALS, 0)

    assert mock_ldap.mock_calls[3][0] == '().bind_s'
    assert mock_ldap.mock_calls[3][1] == (u"user", u"pass")

    assert mock_ldap.mock_calls[4][0] == "().unbind_s"
    assert mock_ldap.mock_calls[4][1] == ()


@pytest.mark.parametrize("kwargs, expected", [
    [{"domain": "dc01"}, "ldap://dc01:389"],
    [{"domain": "dc02", "port": 1234}, "ldap://dc02:1234"],
    [{"domain": "dc03", "scheme": "ldaps"}, "ldaps://dc03:636"],
    # Verifies that an explicit URI ignores port and scheme
    [{"domain": "ldap://dc04", "port": 1234, "scheme": "ldaps"}, "ldap://dc04"],
])
def test_uri_options(monkeypatch, kwargs, expected):
    mock_ldap = MagicMock()
    monkeypatch.setattr("ldap.initialize", mock_ldap)

    lookup_loader.get('laps_password').run([], **kwargs)

    assert mock_ldap.call_count == 1
    assert mock_ldap.call_args[0] == (expected,)
    assert mock_ldap.call_args[1] == {"bytes_mode": False}


@pytest.mark.parametrize("validate, expected", [
    ["never", FakeLdap.OPT_X_TLS_NEVER],
    ["allow", FakeLdap.OPT_X_TLS_ALLOW],
    ["try", FakeLdap.OPT_X_TLS_TRY],
    ["demand", FakeLdap.OPT_X_TLS_DEMAND],
])
def test_certificate_validation(monkeypatch, validate, expected):
    mock_ldap_option = MagicMock()
    monkeypatch.setattr(FakeLdap, "set_option", mock_ldap_option)

    mock_ldap = MagicMock()
    monkeypatch.setattr("ldap.initialize", mock_ldap)

    lookup_loader.get('laps_password').run([], domain="dc01", start_tls=True, validate_certs=validate)

    assert mock_ldap_option.mock_calls[0][1] == (FakeLdap.OPT_X_TLS_REQUIRE_CERT, expected)

    assert mock_ldap.mock_calls[3][0] == "().start_tls_s"
    assert mock_ldap.mock_calls[3][1] == ()

    assert mock_ldap.mock_calls[4][0] == "().sasl_gssapi_bind_s"
    assert mock_ldap.mock_calls[4][1] == ()


def test_certificate_validate_with_custom_cacert(monkeypatch):
    mock_ldap_option = MagicMock()
    monkeypatch.setattr(FakeLdap, "set_option", mock_ldap_option)

    mock_ldap = MagicMock()
    monkeypatch.setattr("ldap.initialize", mock_ldap)
    monkeypatch.setattr(os.path, 'exists', lambda x: True)

    lookup_loader.get('laps_password').run([], domain="dc01", scheme="ldaps", cacert_file="cacert.pem")

    assert mock_ldap_option.mock_calls[0][1] == (FakeLdap.OPT_X_TLS_REQUIRE_CERT, FakeLdap.OPT_X_TLS_DEMAND)
    assert mock_ldap_option.mock_calls[1][1] == (FakeLdap.OPT_X_TLS_CACERTFILE, u"cacert.pem")

    assert mock_ldap.mock_calls[3][0] == "().sasl_gssapi_bind_s"
    assert mock_ldap.mock_calls[3][1] == ()


def test_certificate_validate_with_custom_cacert_fail(monkeypatch):
    def set_option(self, key, value):
        if key == FakeLdap.OPT_X_TLS_CACERTFILE:
            raise ValueError("set_option() failed")

    monkeypatch.setattr(FakeLdap, "set_option", set_option)
    monkeypatch.setattr(os.path, 'exists', lambda x: True)

    with pytest.raises(AnsibleLookupError) as err:
        lookup_loader.get('laps_password').run([], domain="dc01", scheme="ldaps", cacert_file="cacert.pem")

    assert str(err.value) == "Failed to set path to cacert file, this is a known issue with older OpenLDAP " \
                             "libraries on the host. Update OpenLDAP and reinstall python-ldap to continue"


@pytest.mark.parametrize("path", [
    "cacert.pem",
    "~/.certs/cacert.pem",
    "~/.certs/$USER/cacert.pem",
])
def test_certificate_invalid_path(monkeypatch, path):
    monkeypatch.setattr(os.path, 'exists', lambda x: False)
    expected_path = os.path.expanduser(os.path.expandvars(path))

    with pytest.raises(AnsibleLookupError) as err:
        lookup_loader.get('laps_password').run([], domain="dc01", scheme="ldaps", cacert_file=path)

    assert str(err.value) == "The cacert_file specified '%s' does not exist" % expected_path


def test_simple_auth_with_ldaps(monkeypatch):
    mock_ldap_option = MagicMock()
    monkeypatch.setattr(FakeLdap, "set_option", mock_ldap_option)

    mock_ldap = MagicMock()
    monkeypatch.setattr("ldap.initialize", mock_ldap)

    lookup_loader.get('laps_password').run([], domain="dc01", scheme="ldaps", auth="simple", username="user",
                                           password="pass")

    assert mock_ldap_option.mock_calls[0][1] == (FakeLdap.OPT_X_TLS_REQUIRE_CERT, FakeLdap.OPT_X_TLS_DEMAND)

    assert mock_ldap.mock_calls[3][0] == '().bind_s'
    assert mock_ldap.mock_calls[3][1] == (u"user", u"pass")

    assert mock_ldap.mock_calls[4][0] == "().read_rootdse_s"
    assert mock_ldap.mock_calls[4][1] == ()


def test_simple_auth_with_start_tls(monkeypatch):
    mock_ldap_option = MagicMock()
    monkeypatch.setattr(FakeLdap, "set_option", mock_ldap_option)

    mock_ldap = MagicMock()
    monkeypatch.setattr("ldap.initialize", mock_ldap)

    lookup_loader.get('laps_password').run([], domain="dc01", start_tls=True, auth="simple", username="user",
                                           password="pass")

    assert mock_ldap_option.mock_calls[0][1] == (FakeLdap.OPT_X_TLS_REQUIRE_CERT, FakeLdap.OPT_X_TLS_DEMAND)

    assert mock_ldap.mock_calls[3][0] == "().start_tls_s"
    assert mock_ldap.mock_calls[3][1] == ()

    assert mock_ldap.mock_calls[4][0] == '().bind_s'
    assert mock_ldap.mock_calls[4][1] == (u"user", u"pass")

    assert mock_ldap.mock_calls[5][0] == "().read_rootdse_s"
    assert mock_ldap.mock_calls[5][1] == ()


def test_start_tls_ldap_error(monkeypatch):
    mock_ldap = MagicMock()
    mock_ldap.return_value.start_tls_s.side_effect = FakeLDAPError("fake error")
    monkeypatch.setattr("ldap.initialize", mock_ldap)

    with pytest.raises(AnsibleLookupError) as err:
        lookup_loader.get('laps_password').run([], domain="dc01", start_tls=True)

    assert str(err.value) == "Failed to send StartTLS to LDAP host 'ldap://dc01:389': fake error"


def test_simple_bind_ldap_error(monkeypatch):
    mock_ldap = MagicMock()
    mock_ldap.return_value.bind_s.side_effect = FakeLDAPError("fake error")
    monkeypatch.setattr("ldap.initialize", mock_ldap)

    with pytest.raises(AnsibleLookupError) as err:
        lookup_loader.get('laps_password').run([], domain="dc01", auth="simple", username="user", password="pass",
                                               allow_plaintext=True)

    assert str(err.value) == "Failed to simple bind against LDAP host 'ldap://dc01:389': fake error"


def test_sasl_bind_ldap_error(monkeypatch):
    mock_ldap = MagicMock()
    mock_ldap.return_value.sasl_gssapi_bind_s.side_effect = FakeLDAPError("fake error")
    monkeypatch.setattr("ldap.initialize", mock_ldap)

    with pytest.raises(AnsibleLookupError) as err:
        lookup_loader.get('laps_password').run([], domain="dc01")

    assert str(err.value) == "Failed to do a sasl bind against LDAP host 'ldap://dc01:389': fake error"


def test_sasl_bind_ldap_no_mechs_error(monkeypatch):
    mock_ldap = MagicMock()
    mock_ldap.return_value.sasl_gssapi_bind_s.side_effect = FakeLDAPAuthUnknownError("no mechs")
    monkeypatch.setattr("ldap.initialize", mock_ldap)

    with pytest.raises(AnsibleLookupError) as err:
        lookup_loader.get('laps_password').run([], domain="dc01")

    assert str(err.value) == "Failed to do a sasl bind against LDAP host 'ldap://dc01:389', the GSSAPI mech is " \
                             "not installed: no mechs"


def test_get_password_valid(laps_password):
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
    assert mock_conn.method_calls[0][1] == ("DC=domain,DC=local", FakeLdap.SCOPE_SUBTREE,
                                            "(&(objectClass=computer)(CN=server))")
    assert mock_conn.method_calls[0][2] == {"attrlist": ["distinguishedName", "ms-Mcs-AdmPwd"]}


def test_get_password_laps_not_configured(laps_password):
    mock_conn = MagicMock()
    mock_conn.search_s.return_value = [
        ("CN=server,DC=domain,DC=local", {"distinguishedName": ["CN=server,DC=domain,DC=local"]}),
        (None, ["ldap://ForestDnsZones.domain.com/DC=ForestDnsZones,DC=domain,DC=com"]),
        (None, ["ldap://DomainDnsZones.domain.com/DC=DomainDnsZones,DC=domain,DC=com"]),
        (None, ["ldap://domain.com/CN=Configuration,DC=domain,DC=com"]),
    ]

    with pytest.raises(AnsibleLookupError) as err:
        laps_password.get_laps_password(mock_conn, "server2", "DC=test,DC=local")
    assert str(err.value) == \
        "The server 'CN=server,DC=domain,DC=local' did not have the LAPS attribute 'ms-Mcs-AdmPwd'"

    assert len(mock_conn.method_calls) == 1
    assert mock_conn.method_calls[0][0] == "search_s"
    assert mock_conn.method_calls[0][1] == ("DC=test,DC=local", FakeLdap.SCOPE_SUBTREE,
                                            "(&(objectClass=computer)(CN=server2))")
    assert mock_conn.method_calls[0][2] == {"attrlist": ["distinguishedName", "ms-Mcs-AdmPwd"]}


def test_get_password_no_results(laps_password):
    mock_conn = MagicMock()
    mock_conn.search_s.return_value = [
        (None, ["ldap://ForestDnsZones.domain.com/DC=ForestDnsZones,DC=domain,DC=com"]),
        (None, ["ldap://DomainDnsZones.domain.com/DC=DomainDnsZones,DC=domain,DC=com"]),
        (None, ["ldap://domain.com/CN=Configuration,DC=domain,DC=com"]),
    ]

    with pytest.raises(AnsibleLookupError) as err:
        laps_password.get_laps_password(mock_conn, "server", "DC=domain,DC=local")
    assert str(err.value) == "Failed to find the server 'server' in the base 'DC=domain,DC=local'"

    assert len(mock_conn.method_calls) == 1
    assert mock_conn.method_calls[0][0] == "search_s"
    assert mock_conn.method_calls[0][1] == ("DC=domain,DC=local", FakeLdap.SCOPE_SUBTREE,
                                            "(&(objectClass=computer)(CN=server))")
    assert mock_conn.method_calls[0][2] == {"attrlist": ["distinguishedName", "ms-Mcs-AdmPwd"]}


def test_get_password_multiple_results(laps_password):
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

    with pytest.raises(AnsibleLookupError) as err:
        laps_password.get_laps_password(mock_conn, "server", "DC=domain,DC=local")
    assert str(err.value) == \
        "Found too many results for the server 'server' in the base 'DC=domain,DC=local'. Specify a more explicit " \
        "search base for the server required. Found servers 'CN=server,OU=Workstations,DC=domain,DC=local', " \
        "'CN=server,OU=Servers,DC=domain,DC=local'"

    assert len(mock_conn.method_calls) == 1
    assert mock_conn.method_calls[0][0] == "search_s"
    assert mock_conn.method_calls[0][1] == ("DC=domain,DC=local", FakeLdap.SCOPE_SUBTREE,
                                            "(&(objectClass=computer)(CN=server))")
    assert mock_conn.method_calls[0][2] == {"attrlist": ["distinguishedName", "ms-Mcs-AdmPwd"]}
