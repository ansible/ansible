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
    openssl_get_csr_identifiers,
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

TEST_CSRS = [
    (
        r"""
-----BEGIN NEW CERTIFICATE REQUEST-----
MIIBJTCBzQIBADAWMRQwEgYDVQQDEwthbnNpYmxlLmNvbTBZMBMGByqGSM49AgEG
CCqGSM49AwEHA0IABACc9MgAFwMBJjoU0ZI18cIHnW1juoKG2DN5VrM60uvBvEEs
4V0egJkNyM2Q4pp001zu14VcpQ0/Ei8xOOPxKZugVTBTBgkqhkiG9w0BCQ4xRjBE
MCMGA1UdEQQcMBqCC2V4YW1wbGUuY29tggtleGFtcGxlLm9yZzAMBgNVHRMBAf8E
AjAAMA8GA1UdDwEB/wQFAwMHgAAwCgYIKoZIzj0EAwIDRwAwRAIgcDyoRmwFVBDl
FvbFZtiSd5wmJU1ltM6JtcfnLWnjY54CICruOByrropFUkOKKb4xXOYsgaDT93Wr
URnCJfTLr2T3
-----END NEW CERTIFICATE REQUEST-----
""",
        set([
            ('dns', 'ansible.com'),
            ('dns', 'example.com'),
            ('dns', 'example.org')
        ]),
        r"""
Certificate Request:
    Data:
        Version: 1 (0x0)
        Subject: CN = ansible.com
        Subject Public Key Info:
            Public Key Algorithm: id-ecPublicKey
                Public-Key: (256 bit)
                pub:
                    04:00:9c:f4:c8:00:17:03:01:26:3a:14:d1:92:35:
                    f1:c2:07:9d:6d:63:ba:82:86:d8:33:79:56:b3:3a:
                    d2:eb:c1:bc:41:2c:e1:5d:1e:80:99:0d:c8:cd:90:
                    e2:9a:74:d3:5c:ee:d7:85:5c:a5:0d:3f:12:2f:31:
                    38:e3:f1:29:9b
                ASN1 OID: prime256v1
                NIST CURVE: P-256
        Attributes:
        Requested Extensions:
            X509v3 Subject Alternative Name: 
                DNS:example.com, DNS:example.org
            X509v3 Basic Constraints: critical
                CA:FALSE
            X509v3 Key Usage: critical
                Digital Signature
    Signature Algorithm: ecdsa-with-SHA256
         30:44:02:20:70:3c:a8:46:6c:05:54:10:e5:16:f6:c5:66:d8:
         92:77:9c:26:25:4d:65:b4:ce:89:b5:c7:e7:2d:69:e3:63:9e:
         02:20:2a:ee:38:1c:ab:ae:8a:45:52:43:8a:29:be:31:5c:e6:
         2c:81:a0:d3:f7:75:ab:51:19:c2:25:f4:cb:af:64:f7
""",
    ),
    (
        r"""
-----BEGIN CERTIFICATE REQUEST-----
MIIEqjCCApICAQAwADCCAiIwDQYJKoZIhvcNAQEBBQADggIPADCCAgoCggIBANv1
V7gDsh76O//d9wclBcW6kNpWeR6eAggzThwbMZjcO7GFHQsBZCZGGVdyS37uhejc
RrIBdtDDWXhoh3Dz+GQxD+6GuwAEFyL1F3MfT0v1HHoO8fE74G5mD6+ZA2HRDeU9
jf8BPyVWHBtNbCmJGSlSNOFejWCmwvsLARQxqFBuTyRjgos4BkLyWMqZRukrzO1P
z7IBhuFrB608t+AG4vGnPXZNM7xefhzO8bPOiepT0YS2ERPkFmOy97SnwTGdKykw
ZYM9oKukYhE4Z+yOaTFpJMBNXwDCI5TMnhtc6eJrf5sOFH92n2E9+YWMoahUOiTw
G6XV5HfSpySpwORUaTITQRsPAM+bmK9f1jB6ctfFVwpa8uW/h8pSgbHgZvkeD6s6
rFLh9TQ24t0vrRmhnY7/AMFgbgJoBTBq0l0lEXS4FCGKDGqQOqSws+eHR/pHA4uY
v8d498SQl9fYsT/c7Uj3/JnMSRVN942yQUFCzwLf0/WzWCi2HTqPM8CPh5ryiJ30
GAN2eb026/noyTOXm479Tg9o86Tw9qczE0j0CdcRnr6J337RGHQg58PZ7j+hnUmK
wgyclyvjE10ZFBgToMGSnzYp5UeRcOFZ3bnK6LOsGC75mIvz2OQgSQeO5VQASEnO
9uhygNyo91sK4BtVroloit8ZCa82LlsHSCj/mMzPAgMBAAGgZTBjBgkqhkiG9w0B
CQ4xVjBUMFIGA1UdEQRLMEmCC2Fuc2libGUuY29thwR/AAABhxAAAAAAAAAAAAAA
AAAAAAABhxAgAQ2IrBD+AQAAAAAAAAAAhxAgARI0VnirzZh2VDIQ/ty6MA0GCSqG
SIb3DQEBCwUAA4ICAQBFRuANzVRcze+iur0YevjtYIXDa03GoWWkgnLuE8u8epTM
2248duG3TmvVvxWPN4iFrvFcZIvNsevBo+Z7kXJ24m3YldtXvwfAYmCZ062apSoh
yzgo3Q0KfDehwLcoJPe5bh+jbbgJVGGvJug/QFyHSVl+iGyFUXE7pwafl9LuNDi3
yfOYZLIQ34mBH4Rsvymj9xSTYliWDEEU/o7RrrZeEqkOxNeLh64LbnifdrYUputz
yBURg2xs9hpAsytZJX90iJW8aYPM1aQ7eetqTViIRoqUAmIQobnKlNnpOliBHl+p
RY+AtTnsfAetKUP7OsAZkHRTGAXx0JHJQ1ITY8w5Dcw/v1bDCbAfkDubBP3X+us9
RQk2h6m74hWFFNu9xOfkNejPf7h4gywfDjo/wGZFSWKyi6avB9V53znZgRUwc009
p5MM9e37MH8pyBqfnbSwOj4hUoyecRCIAFdywjMb9akP2u15XP3MOtJOEvecyCxN
TZBxupTg65zB47GeSAufnc8FaTZkE8xPuCtbvqOVOkWYqzlqNdCfK8f3AZdlpwLh
38wdUm5G7LIu6aQNiY66aQs9qVpoGvqdmxHRkuSwqwZxGgzcY1yJaWGXQ6R4jgC3
VKlMTUVs1WYV6jrYLHcVt6Rn/2FVTOns3Jn6cTPOdKViYoqF+yW8yCEAqAskZw==
-----END CERTIFICATE REQUEST-----
""",
        set([
            ('dns', 'ansible.com'),
            ('ip', '127.0.0.1'),
            ('ip', '::1'),
            ('ip', '2001:d88:ac10:fe01::'),
            ('ip', '2001:1234:5678:abcd:9876:5432:10fe:dcba')
        ]),
        r"""
Certificate Request:
    Data:
        Version: 1 (0x0)
        Subject: 
        Subject Public Key Info:
            Public Key Algorithm: rsaEncryption
                RSA Public-Key: (4096 bit)
                Modulus:
                    00:db:f5:57:b8:03:b2:1e:fa:3b:ff:dd:f7:07:25:
                    05:c5:ba:90:da:56:79:1e:9e:02:08:33:4e:1c:1b:
                    31:98:dc:3b:b1:85:1d:0b:01:64:26:46:19:57:72:
                    4b:7e:ee:85:e8:dc:46:b2:01:76:d0:c3:59:78:68:
                    87:70:f3:f8:64:31:0f:ee:86:bb:00:04:17:22:f5:
                    17:73:1f:4f:4b:f5:1c:7a:0e:f1:f1:3b:e0:6e:66:
                    0f:af:99:03:61:d1:0d:e5:3d:8d:ff:01:3f:25:56:
                    1c:1b:4d:6c:29:89:19:29:52:34:e1:5e:8d:60:a6:
                    c2:fb:0b:01:14:31:a8:50:6e:4f:24:63:82:8b:38:
                    06:42:f2:58:ca:99:46:e9:2b:cc:ed:4f:cf:b2:01:
                    86:e1:6b:07:ad:3c:b7:e0:06:e2:f1:a7:3d:76:4d:
                    33:bc:5e:7e:1c:ce:f1:b3:ce:89:ea:53:d1:84:b6:
                    11:13:e4:16:63:b2:f7:b4:a7:c1:31:9d:2b:29:30:
                    65:83:3d:a0:ab:a4:62:11:38:67:ec:8e:69:31:69:
                    24:c0:4d:5f:00:c2:23:94:cc:9e:1b:5c:e9:e2:6b:
                    7f:9b:0e:14:7f:76:9f:61:3d:f9:85:8c:a1:a8:54:
                    3a:24:f0:1b:a5:d5:e4:77:d2:a7:24:a9:c0:e4:54:
                    69:32:13:41:1b:0f:00:cf:9b:98:af:5f:d6:30:7a:
                    72:d7:c5:57:0a:5a:f2:e5:bf:87:ca:52:81:b1:e0:
                    66:f9:1e:0f:ab:3a:ac:52:e1:f5:34:36:e2:dd:2f:
                    ad:19:a1:9d:8e:ff:00:c1:60:6e:02:68:05:30:6a:
                    d2:5d:25:11:74:b8:14:21:8a:0c:6a:90:3a:a4:b0:
                    b3:e7:87:47:fa:47:03:8b:98:bf:c7:78:f7:c4:90:
                    97:d7:d8:b1:3f:dc:ed:48:f7:fc:99:cc:49:15:4d:
                    f7:8d:b2:41:41:42:cf:02:df:d3:f5:b3:58:28:b6:
                    1d:3a:8f:33:c0:8f:87:9a:f2:88:9d:f4:18:03:76:
                    79:bd:36:eb:f9:e8:c9:33:97:9b:8e:fd:4e:0f:68:
                    f3:a4:f0:f6:a7:33:13:48:f4:09:d7:11:9e:be:89:
                    df:7e:d1:18:74:20:e7:c3:d9:ee:3f:a1:9d:49:8a:
                    c2:0c:9c:97:2b:e3:13:5d:19:14:18:13:a0:c1:92:
                    9f:36:29:e5:47:91:70:e1:59:dd:b9:ca:e8:b3:ac:
                    18:2e:f9:98:8b:f3:d8:e4:20:49:07:8e:e5:54:00:
                    48:49:ce:f6:e8:72:80:dc:a8:f7:5b:0a:e0:1b:55:
                    ae:89:68:8a:df:19:09:af:36:2e:5b:07:48:28:ff:
                    98:cc:cf
                Exponent: 65537 (0x10001)
        Attributes:
        Requested Extensions:
            X509v3 Subject Alternative Name: 
                DNS:ansible.com, IP Address:127.0.0.1, IP Address:0:0:0:0:0:0:0:1, IP Address:2001:D88:AC10:FE01:0:0:0:0, IP Address:2001:1234:5678:ABCD:9876:5432:10FE:DCBA
    Signature Algorithm: sha256WithRSAEncryption
         45:46:e0:0d:cd:54:5c:cd:ef:a2:ba:bd:18:7a:f8:ed:60:85:
         c3:6b:4d:c6:a1:65:a4:82:72:ee:13:cb:bc:7a:94:cc:db:6e:
         3c:76:e1:b7:4e:6b:d5:bf:15:8f:37:88:85:ae:f1:5c:64:8b:
         cd:b1:eb:c1:a3:e6:7b:91:72:76:e2:6d:d8:95:db:57:bf:07:
         c0:62:60:99:d3:ad:9a:a5:2a:21:cb:38:28:dd:0d:0a:7c:37:
         a1:c0:b7:28:24:f7:b9:6e:1f:a3:6d:b8:09:54:61:af:26:e8:
         3f:40:5c:87:49:59:7e:88:6c:85:51:71:3b:a7:06:9f:97:d2:
         ee:34:38:b7:c9:f3:98:64:b2:10:df:89:81:1f:84:6c:bf:29:
         a3:f7:14:93:62:58:96:0c:41:14:fe:8e:d1:ae:b6:5e:12:a9:
         0e:c4:d7:8b:87:ae:0b:6e:78:9f:76:b6:14:a6:eb:73:c8:15:
         11:83:6c:6c:f6:1a:40:b3:2b:59:25:7f:74:88:95:bc:69:83:
         cc:d5:a4:3b:79:eb:6a:4d:58:88:46:8a:94:02:62:10:a1:b9:
         ca:94:d9:e9:3a:58:81:1e:5f:a9:45:8f:80:b5:39:ec:7c:07:
         ad:29:43:fb:3a:c0:19:90:74:53:18:05:f1:d0:91:c9:43:52:
         13:63:cc:39:0d:cc:3f:bf:56:c3:09:b0:1f:90:3b:9b:04:fd:
         d7:fa:eb:3d:45:09:36:87:a9:bb:e2:15:85:14:db:bd:c4:e7:
         e4:35:e8:cf:7f:b8:78:83:2c:1f:0e:3a:3f:c0:66:45:49:62:
         b2:8b:a6:af:07:d5:79:df:39:d9:81:15:30:73:4d:3d:a7:93:
         0c:f5:ed:fb:30:7f:29:c8:1a:9f:9d:b4:b0:3a:3e:21:52:8c:
         9e:71:10:88:00:57:72:c2:33:1b:f5:a9:0f:da:ed:79:5c:fd:
         cc:3a:d2:4e:12:f7:9c:c8:2c:4d:4d:90:71:ba:94:e0:eb:9c:
         c1:e3:b1:9e:48:0b:9f:9d:cf:05:69:36:64:13:cc:4f:b8:2b:
         5b:be:a3:95:3a:45:98:ab:39:6a:35:d0:9f:2b:c7:f7:01:97:
         65:a7:02:e1:df:cc:1d:52:6e:46:ec:b2:2e:e9:a4:0d:89:8e:
         ba:69:0b:3d:a9:5a:68:1a:fa:9d:9b:11:d1:92:e4:b0:ab:06:
         71:1a:0c:dc:63:5c:89:69:61:97:43:a4:78:8e:00:b7:54:a9:
         4c:4d:45:6c:d5:66:15:ea:3a:d8:2c:77:15:b7:a4:67:ff:61:
         55:4c:e9:ec:dc:99:fa:71:33:ce:74:a5:62:62:8a:85:fb:25:
         bc:c8:21:00:a8:0b:24:67
""",
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
