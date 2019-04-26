import base64
import datetime
import os.path
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
    openssl_get_csr_identifiers,
    cryptography_get_csr_identifiers,
    cryptography_get_cert_days,
)


def load_fixture(name):
    with open(os.path.join(os.path.dirname(__file__), 'fixtures', name)) as f:
        return f.read()


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
        load_fixture('privatekey_1.pem'),
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
        load_fixture('privatekey_1.pem'),
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
        load_fixture('privatekey_1.txt'),
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

TEST_CSRS = [
    (
        load_fixture('csr_1.pem'),
        set([
            ('dns', 'ansible.com'),
            ('dns', 'example.com'),
            ('dns', 'example.org')
        ]),
        load_fixture('csr_1.txt'),
    ),
    (
        load_fixture('csr_2.pem'),
        set([
            ('dns', 'ansible.com'),
            ('ip', '127.0.0.1'),
            ('ip', '::1'),
            ('ip', '2001:d88:ac10:fe01::'),
            ('ip', '2001:1234:5678:abcd:9876:5432:10fe:dcba')
        ]),
        load_fixture('csr_2.txt'),
    ),
]


@pytest.mark.parametrize("csr, result, openssl_output", TEST_CSRS)
def test_csridentifiers_openssl(csr, result, openssl_output, tmpdir):
    fn = tmpdir / 'test.csr'
    fn.write(csr)
    module = MagicMock()
    module.run_command = MagicMock(return_value=(0, openssl_output, 0))
    identifiers = openssl_get_csr_identifiers('openssl', module, str(fn))
    assert identifiers == result


if HAS_CURRENT_CRYPTOGRAPHY:
    @pytest.mark.parametrize("csr, result, openssl_output", TEST_CSRS)
    def test_csridentifiers_cryptography(csr, result, openssl_output, tmpdir):
        fn = tmpdir / 'test.csr'
        fn.write(csr)
        module = MagicMock()
        identifiers = cryptography_get_csr_identifiers(module, str(fn))
        assert identifiers == result


################################################

TEST_CERT = load_fixture("cert_1.pem")

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
