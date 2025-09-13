# (c) 2018, Matthias Fuchs <matthias.s.fuchs@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import warnings

import pytest

from ansible.errors import AnsibleError

from ansible.plugins.filter.core import get_encrypted_password
from ansible.utils import encrypt


def assert_hash(expected, secret, algorithm, **settings):
    assert encrypt.do_encrypt(secret, algorithm, **settings) == expected
    assert encrypt.PasslibHash(algorithm).hash(secret, **settings) == expected


@pytest.mark.parametrize(
    ("algorithm", "ident", "salt", "rounds", "expected"),
    [
        pytest.param(
            "bcrypt",
            None,
            "1234567890123456789012",
            None,
            "$2b$12$123456789012345678901ugbM1PeTfRQ0t6dCJu5lQA8hwrZOYgDu",
            id="bcrypt_default",
        ),
        pytest.param(
            "bcrypt",
            "2",
            "1234567890123456789012",
            None,
            "$2$12$123456789012345678901ufd3hZRrev.WXCbemqGIV/gmWaTGLImm",
            id="bcrypt_ident_2",
        ),
        pytest.param(
            "bcrypt",
            "2y",
            "1234567890123456789012",
            None,
            "$2y$12$123456789012345678901ugbM1PeTfRQ0t6dCJu5lQA8hwrZOYgDu",
            id="bcrypt_ident_2y",
        ),
        pytest.param(
            "bcrypt",
            "2a",
            "1234567890123456789012",
            None,
            "$2a$12$123456789012345678901ugbM1PeTfRQ0t6dCJu5lQA8hwrZOYgDu",
            id="bcrypt_ident_2a",
        ),
        pytest.param(
            "bcrypt",
            "2b",
            "1234567890123456789012",
            None,
            "$2b$12$123456789012345678901ugbM1PeTfRQ0t6dCJu5lQA8hwrZOYgDu",
            id="bcrypt_ident_2b",
        ),
        pytest.param(
            "sha256_crypt",
            "invalid_ident",
            "12345678",
            5000,
            "$5$12345678$uAZsE3BenI2G.nA8DpTl.9Dc8JiqacI53pEqRr5ppT7",
            id="sha256_crypt_invalid_ident",
        ),
        pytest.param(
            "crypt16",
            None,
            "12",
            None,
            "12pELHK2ME3McUFlHxel6uMM",
            id="crypt16_no_ident",
        ),
    ],
)
@pytest.mark.skipif(not encrypt.PASSLIB_AVAILABLE, reason='passlib must be installed to run this test')
def test_encrypt_with_ident(algorithm, ident, salt, rounds, expected):
    assert_hash(expected, secret="123", algorithm=algorithm, salt=salt, rounds=rounds, ident=ident)


# If passlib is not installed. this is identical to the test_encrypt_with_rounds_no_passlib() test
@pytest.mark.parametrize(
    ("algorithm", "rounds", "expected"),
    [
        pytest.param(
            "sha256_crypt",
            None,
            "$5$rounds=535000$12345678$uy3TurUPaY71aioJi58HvUY8jkbhSQU8HepbyaNngv.",
            id="sha256_crypt_default_rounds",
        ),
        pytest.param(
            "sha256_crypt",
            5000,
            "$5$12345678$uAZsE3BenI2G.nA8DpTl.9Dc8JiqacI53pEqRr5ppT7",
            id="sha256_crypt_rounds_5000",
        ),
        pytest.param(
            "sha256_crypt",
            10000,
            "$5$rounds=10000$12345678$JBinliYMFEcBeAXKZnLjenhgEhTmJBvZn3aR8l70Oy/",
            id="sha256_crypt_rounds_10000",
        ),
        pytest.param(
            "sha512_crypt",
            None,
            "$6$rounds=656000$12345678$InMy49UwxyCh2pGJU1NpOhVSElDDzKeyuC6n6E9O34BCUGVNYADnI.rcA3m.Vro9BiZpYmjEoNhpREqQcbvQ80",
            id="sha512_crypt_default_rounds",
        ),
        pytest.param(
            "sha512_crypt",
            5000,
            "$6$12345678$LcV9LQiaPekQxZ.OfkMADjFdSO2k9zfbDQrHPVcYjSLqSdjLYpsgqviYvTEP/R41yPmhH3CCeEDqVhW1VHr3L.",
            id="sha512_crypt_rounds_5000",
        ),
        pytest.param(
            "md5_crypt",
            None,
            "$1$12345678$tRy4cXc3kmcfRZVj4iFXr/",
            id="md5_crypt_default_rounds",
        ),
    ],
)
@pytest.mark.skipif(not encrypt.PASSLIB_AVAILABLE, reason='passlib must be installed to run this test')
def test_encrypt_with_rounds(algorithm, rounds, expected):
    assert_hash(expected, secret="123", algorithm=algorithm, salt="12345678", rounds=rounds)


@pytest.mark.skipif(not encrypt.PASSLIB_AVAILABLE, reason='passlib must be installed to run this test')
def test_password_hash_filter_passlib_with_exception():

    with pytest.raises(AnsibleError):
        get_encrypted_password("123", "sha257", salt="12345678")


@pytest.mark.parametrize(
    ("algorithm", "rounds", "expected_hash"),
    [
        pytest.param(
            "sha256",
            None,
            "$5$rounds=535000$12345678$uy3TurUPaY71aioJi58HvUY8jkbhSQU8HepbyaNngv.",
            id="sha256_default_rounds",
        ),
        pytest.param(
            "sha256",
            5000,
            "$5$12345678$uAZsE3BenI2G.nA8DpTl.9Dc8JiqacI53pEqRr5ppT7",
            id="sha256_rounds_5000",
        ),
        pytest.param(
            "sha256",
            10000,
            "$5$rounds=10000$12345678$JBinliYMFEcBeAXKZnLjenhgEhTmJBvZn3aR8l70Oy/",
            id="sha256_rounds_10000",
        ),
        pytest.param(
            "sha512",
            5000,
            "$6$12345678$LcV9LQiaPekQxZ.OfkMADjFdSO2k9zfbDQrHPVcYjSLqSdjLYpsgqviYvTEP/R41yPmhH3CCeEDqVhW1VHr3L.",
            id="sha512_rounds_5000",
        ),
        pytest.param(
            "sha512",
            6000,
            "$6$rounds=6000$12345678$l/fC67BdJwZrJ7qneKGP1b6PcatfBr0dI7W6JLBrsv8P1wnv/0pu4WJsWq5p6WiXgZ2gt9Aoir3MeORJxg4.Z/",
            id="sha512_rounds_6000",
        ),
    ],
)
@pytest.mark.skipif(not encrypt.PASSLIB_AVAILABLE, reason='passlib must be installed to run this test')
def test_password_hash_filter_passlib(algorithm, rounds, expected_hash):
    assert get_encrypted_password("123", algorithm, salt="12345678", rounds=rounds) == expected_hash


@pytest.mark.skipif(not encrypt.PASSLIB_AVAILABLE, reason='passlib must be installed to run this test')
def test_do_encrypt_passlib_with_exception():
    with pytest.raises(AnsibleError):
        encrypt.do_encrypt("123", "sha257_crypt", salt="12345678")


def test_random_salt():
    res = encrypt.random_salt()
    expected_salt_candidate_chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789./'
    assert len(res) == 8
    for res_char in res:
        assert res_char in expected_salt_candidate_chars


def test_passlib_bcrypt_salt(recwarn):
    # deprecated: description='warning suppression only required for Python 3.12 and earlier' python_version='3.12'
    with warnings.catch_warnings():
        warnings.filterwarnings('ignore', message="'crypt' is deprecated and slated for removal in Python 3.13", category=DeprecationWarning)

        passlib_exc = pytest.importorskip("passlib.exc")

    secret = 'foo'
    salt = '1234567890123456789012'
    repaired_salt = '123456789012345678901u'
    expected = '$2b$12$123456789012345678901uMv44x.2qmQeefEGb3bcIRc1mLuO7bqa'
    ident = '2b'

    passlib_obj = encrypt.PasslibHash('bcrypt')

    result = passlib_obj.hash(secret, salt=salt, ident=ident)
    passlib_warnings = [w.message for w in recwarn if isinstance(w.message, passlib_exc.PasslibHashWarning)]
    assert len(passlib_warnings) == 0
    assert result == expected

    recwarn.clear()

    result = passlib_obj.hash(secret, salt=repaired_salt, ident=ident)
    assert result == expected
