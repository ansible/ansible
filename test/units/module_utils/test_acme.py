import base64
import datetime
import pytest

from mock import MagicMock


from ansible.module_utils.acme import (
    HAS_CURRENT_CRYPTOGRAPHY,
    nopad_b64,
    write_file,
    read_file,
    pem_to_der,
    _parse_key_openssl,
    # _sign_request_openssl,
    _parse_key_cryptography,
    # _sign_request_cryptography,
    _normalize_ip,
    cryptography_get_csr_identifiers,
    cryptography_get_cert_days,
)

################################################

NOPAD_B64 = [
    ("", ""),
    ("\n", "Cg"),
    ("123", "MTIz"),
    ("Lorem?ipsum", "TG9yZW0_aXBzdW0"),
]


@pytest.mark.parametrize("value, result", NOPAD_B64)
def test_nopad_b64(value, result):
    assert nopad_b64(value.encode('utf-8')) == result


################################################

TEST_TEXT = r"""1234
5678"""


def test_read_file(tmpdir):
    fn = tmpdir / 'test.txt'
    fn.write(TEST_TEXT)
    assert read_file(str(fn), 't') == TEST_TEXT
    assert read_file(str(fn), 'b') == TEST_TEXT.encode('utf-8')


def test_write_file(tmpdir):
    fn = tmpdir / 'test.txt'
    module = MagicMock()
    write_file(module, str(fn), TEST_TEXT.encode('utf-8'))
    assert fn.read() == TEST_TEXT


################################################

TEST_PEM_DERS = [
    (
        r"""
-----BEGIN EC PRIVATE KEY-----
MHcCAQEEIDWajU0PyhYKeulfy/luNtkAve7DkwQ01bXJ97zbxB66oAoGCCqGSM49
AwEHoUQDQgAEAJz0yAAXAwEmOhTRkjXxwgedbWO6gobYM3lWszrS68G8QSzhXR6A
mQ3IzZDimnTTXO7XhVylDT8SLzE44/Epmw==
-----END EC PRIVATE KEY-----
""",
        base64.b64decode('MHcCAQEEIDWajU0PyhYKeulfy/luNtkAve7DkwQ01bXJ97zbxB66oAo'
                         'GCCqGSM49AwEHoUQDQgAEAJz0yAAXAwEmOhTRkjXxwgedbWO6gobYM3'
                         'lWszrS68G8QSzhXR6AmQ3IzZDimnTTXO7XhVylDT8SLzE44/Epmw==')
    )
]


@pytest.mark.parametrize("pem, der", TEST_PEM_DERS)
def test_pem_to_der(pem, der, tmpdir):
    fn = tmpdir / 'test.pem'
    fn.write(pem)
    assert pem_to_der(str(fn)) == der


################################################

TEST_KEYS = [
    (
        r"""
-----BEGIN EC PRIVATE KEY-----
MHcCAQEEIDWajU0PyhYKeulfy/luNtkAve7DkwQ01bXJ97zbxB66oAoGCCqGSM49
AwEHoUQDQgAEAJz0yAAXAwEmOhTRkjXxwgedbWO6gobYM3lWszrS68G8QSzhXR6A
mQ3IzZDimnTTXO7XhVylDT8SLzE44/Epmw==
-----END EC PRIVATE KEY-----
""",
        {
            'alg': 'ES256',
            'hash': 'sha256',
            'jwk': {
                'crv': 'P-256',
                'kty': 'EC',
                'x': 'AJz0yAAXAwEmOhTRkjXxwgedbWO6gobYM3lWszrS68E',
                'y': 'vEEs4V0egJkNyM2Q4pp001zu14VcpQ0_Ei8xOOPxKZs',
            },
            'point_size': 32,
            'type': 'ec',
        },
        r"""
read EC key
Private-Key: (256 bit)
priv:
    35:9a:8d:4d:0f:ca:16:0a:7a:e9:5f:cb:f9:6e:36:
    d9:00:bd:ee:c3:93:04:34:d5:b5:c9:f7:bc:db:c4:
    1e:ba
pub:
    04:00:9c:f4:c8:00:17:03:01:26:3a:14:d1:92:35:
    f1:c2:07:9d:6d:63:ba:82:86:d8:33:79:56:b3:3a:
    d2:eb:c1:bc:41:2c:e1:5d:1e:80:99:0d:c8:cd:90:
    e2:9a:74:d3:5c:ee:d7:85:5c:a5:0d:3f:12:2f:31:
    38:e3:f1:29:9b
ASN1 OID: prime256v1
NIST CURVE: P-256
"""
    )
]


@pytest.mark.parametrize("pem, result, openssl_output", TEST_KEYS)
def test_eckeyparse_openssl(pem, result, openssl_output, tmpdir):
    fn = tmpdir / 'test.key'
    fn.write(pem)
    module = MagicMock()
    module.run_command = MagicMock(return_value=(0, openssl_output, 0))
    error, key = _parse_key_openssl('openssl', module, key_file=str(fn))
    assert error is None
    key.pop('key_file')
    assert key == result


if HAS_CURRENT_CRYPTOGRAPHY:
    @pytest.mark.parametrize("pem, result, dummy", TEST_KEYS)
    def test_eckeyparse_cryptography(pem, result, dummy):
        module = MagicMock()
        error, key = _parse_key_cryptography(module, key_content=pem)
        assert error is None
        key.pop('key_obj')
        assert key == result


################################################

TEST_IPS = [
    ("0:0:0:0:0:0:0:1", "::1"),
    ("1::0:2", "1::2"),
    ("0000:0001:0000:0000:0000:0000:0000:0001", "0:1::1"),
    ("0000:0001:0000:0000:0001:0000:0000:0001", "0:1::1:0:0:1"),
    ("0000:0001:0000:0001:0000:0001:0000:0001", "0:1:0:1:0:1:0:1"),
    ("0.0.0.0", "0.0.0.0"),
    ("000.001.000.000", "0.1.0.0"),
    ("2001:d88:ac10:fe01:0:0:0:0", "2001:d88:ac10:fe01::"),
    ("0000:0000:0000:0000:0000:0000:0000:0000", "::"),
]


@pytest.mark.parametrize("ip, result", TEST_IPS)
def test_normalize_ip(ip, result):
    assert _normalize_ip(ip) == result


################################################

TEST_CSR = r"""
-----BEGIN NEW CERTIFICATE REQUEST-----
MIIBJTCBzQIBADAWMRQwEgYDVQQDEwthbnNpYmxlLmNvbTBZMBMGByqGSM49AgEG
CCqGSM49AwEHA0IABACc9MgAFwMBJjoU0ZI18cIHnW1juoKG2DN5VrM60uvBvEEs
4V0egJkNyM2Q4pp001zu14VcpQ0/Ei8xOOPxKZugVTBTBgkqhkiG9w0BCQ4xRjBE
MCMGA1UdEQQcMBqCC2V4YW1wbGUuY29tggtleGFtcGxlLm9yZzAMBgNVHRMBAf8E
AjAAMA8GA1UdDwEB/wQFAwMHgAAwCgYIKoZIzj0EAwIDRwAwRAIgcDyoRmwFVBDl
FvbFZtiSd5wmJU1ltM6JtcfnLWnjY54CICruOByrropFUkOKKb4xXOYsgaDT93Wr
URnCJfTLr2T3
-----END NEW CERTIFICATE REQUEST-----
"""


if HAS_CURRENT_CRYPTOGRAPHY:
    def test_csrdomains_cryptography(tmpdir):
        fn = tmpdir / 'test.csr'
        fn.write(TEST_CSR)
        module = MagicMock()
        domains = cryptography_get_csr_identifiers(module, str(fn))
        assert domains == set([('dns', 'ansible.com'), ('dns', 'example.com'), ('dns', 'example.org')])


################################################

TEST_CERT = r"""
-----BEGIN CERTIFICATE-----
MIIBljCCATugAwIBAgIBATAKBggqhkjOPQQDAjAWMRQwEgYDVQQDEwthbnNpYmxl
LmNvbTAeFw0xODExMjUxNTI4MjNaFw0xODExMjYxNTI4MjRaMBYxFDASBgNVBAMT
C2Fuc2libGUuY29tMFkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDQgAEAJz0yAAXAwEm
OhTRkjXxwgedbWO6gobYM3lWszrS68G8QSzhXR6AmQ3IzZDimnTTXO7XhVylDT8S
LzE44/Epm6N6MHgwIwYDVR0RBBwwGoILZXhhbXBsZS5jb22CC2V4YW1wbGUub3Jn
MAwGA1UdEwEB/wQCMAAwDwYDVR0PAQH/BAUDAweAADATBgNVHSUEDDAKBggrBgEF
BQcDATAdBgNVHQ4EFgQUmNL9PMzNaUX74owwLFRiGDS3B3MwCgYIKoZIzj0EAwID
SQAwRgIhALz7Ur96ky0OfM5D9MwFmCg2jccqm/UglGI9+4KeOEIyAiEAwFX4tdll
QSrd1HY/jMsHwdK5wH3JkK/9+fGwyRP11VI=
-----END CERTIFICATE-----
"""

TEST_CERT_DAYS = [
    (datetime.datetime(2018, 11, 15, 1, 2, 3), 11),
    (datetime.datetime(2018, 11, 25, 15, 20, 0), 1),
    (datetime.datetime(2018, 11, 25, 15, 30, 0), 0),
]


if HAS_CURRENT_CRYPTOGRAPHY:
    @pytest.mark.parametrize("now, expected_days", TEST_CERT_DAYS)
    def test_certdays_cryptography(now, expected_days, tmpdir):
        fn = tmpdir / 'test-cert.pem'
        fn.write(TEST_CERT)
        module = MagicMock()
        days = cryptography_get_cert_days(module, str(fn), now=now)
        assert days == expected_days
