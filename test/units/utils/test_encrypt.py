# (c) 2018, Matthias Fuchs <matthias.s.fuchs@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import pytest

from ansible.errors import AnsibleError, AnsibleFilterError
from ansible.plugins.filter.core import get_encrypted_password
from ansible.utils import encrypt


def assert_hash(expected, secret, algorithm, **settings):
    assert encrypt.do_encrypt(secret, algorithm, **settings) == expected
    assert encrypt.PasslibHash(algorithm).hash(secret, **settings) == expected


@pytest.mark.skipif(not encrypt.PASSLIB_AVAILABLE, reason='passlib must be installed to run this test')
def test_passlib():
    expected = "$5$12345678$uAZsE3BenI2G.nA8DpTl.9Dc8JiqacI53pEqRr5ppT7"
    assert encrypt.passlib_or_crypt("123", "sha256_crypt", salt="12345678", rounds=5000) == expected


@pytest.mark.skipif(not encrypt.PASSLIB_AVAILABLE, reason='passlib must be installed to run this test')
def test_encrypt_with_ident():
    assert_hash("$2$12$123456789012345678901ufd3hZRrev.WXCbemqGIV/gmWaTGLImm",
                secret="123", algorithm="bcrypt", salt='1234567890123456789012', ident='2')
    assert_hash("$2y$12$123456789012345678901ugbM1PeTfRQ0t6dCJu5lQA8hwrZOYgDu",
                secret="123", algorithm="bcrypt", salt='1234567890123456789012', ident='2y')
    assert_hash("$2a$12$123456789012345678901ugbM1PeTfRQ0t6dCJu5lQA8hwrZOYgDu",
                secret="123", algorithm="bcrypt", salt='1234567890123456789012', ident='2a')
    assert_hash("$2b$12$123456789012345678901ugbM1PeTfRQ0t6dCJu5lQA8hwrZOYgDu",
                secret="123", algorithm="bcrypt", salt='1234567890123456789012', ident='2b')
    assert_hash("$2b$12$123456789012345678901ugbM1PeTfRQ0t6dCJu5lQA8hwrZOYgDu",
                secret="123", algorithm="bcrypt", salt='1234567890123456789012')
    # negative test: sha256_crypt does not take ident as parameter so ignore it
    assert_hash("$5$12345678$uAZsE3BenI2G.nA8DpTl.9Dc8JiqacI53pEqRr5ppT7",
                secret="123", algorithm="sha256_crypt", salt="12345678", rounds=5000, ident='invalid_ident')


# If passlib is not installed. this is identical to the test_encrypt_with_rounds_no_passlib() test
@pytest.mark.skipif(not encrypt.PASSLIB_AVAILABLE, reason='passlib must be installed to run this test')
def test_encrypt_with_rounds():
    assert_hash("$5$12345678$uAZsE3BenI2G.nA8DpTl.9Dc8JiqacI53pEqRr5ppT7",
                secret="123", algorithm="sha256_crypt", salt="12345678", rounds=5000)
    assert_hash("$5$rounds=10000$12345678$JBinliYMFEcBeAXKZnLjenhgEhTmJBvZn3aR8l70Oy/",
                secret="123", algorithm="sha256_crypt", salt="12345678", rounds=10000)
    assert_hash("$6$12345678$LcV9LQiaPekQxZ.OfkMADjFdSO2k9zfbDQrHPVcYjSLqSdjLYpsgqviYvTEP/R41yPmhH3CCeEDqVhW1VHr3L.",
                secret="123", algorithm="sha512_crypt", salt="12345678", rounds=5000)


# If passlib is not installed. this is identical to the test_encrypt_default_rounds_no_passlib() test
@pytest.mark.skipif(not encrypt.PASSLIB_AVAILABLE, reason='passlib must be installed to run this test')
def test_encrypt_default_rounds():
    assert_hash("$1$12345678$tRy4cXc3kmcfRZVj4iFXr/",
                secret="123", algorithm="md5_crypt", salt="12345678")
    assert_hash("$5$rounds=535000$12345678$uy3TurUPaY71aioJi58HvUY8jkbhSQU8HepbyaNngv.",
                secret="123", algorithm="sha256_crypt", salt="12345678")
    assert_hash("$6$rounds=656000$12345678$InMy49UwxyCh2pGJU1NpOhVSElDDzKeyuC6n6E9O34BCUGVNYADnI.rcA3m.Vro9BiZpYmjEoNhpREqQcbvQ80",
                secret="123", algorithm="sha512_crypt", salt="12345678")

    assert encrypt.PasslibHash("md5_crypt").hash("123")


@pytest.mark.skipif(not encrypt.PASSLIB_AVAILABLE, reason='passlib must be installed to run this test')
def test_password_hash_filter_passlib():

    with pytest.raises(AnsibleFilterError):
        get_encrypted_password("123", "sha257", salt="12345678")

    # Uses passlib default rounds value for sha256 matching crypt behaviour
    assert get_encrypted_password("123", "sha256", salt="12345678") == "$5$rounds=535000$12345678$uy3TurUPaY71aioJi58HvUY8jkbhSQU8HepbyaNngv."
    assert get_encrypted_password("123", "sha256", salt="12345678", rounds=5000) == "$5$12345678$uAZsE3BenI2G.nA8DpTl.9Dc8JiqacI53pEqRr5ppT7"

    assert (get_encrypted_password("123", "sha256", salt="12345678", rounds=10000) ==
            "$5$rounds=10000$12345678$JBinliYMFEcBeAXKZnLjenhgEhTmJBvZn3aR8l70Oy/")

    assert (get_encrypted_password("123", "sha512", salt="12345678", rounds=6000) ==
            "$6$rounds=6000$12345678$l/fC67BdJwZrJ7qneKGP1b6PcatfBr0dI7W6JLBrsv8P1wnv/0pu4WJsWq5p6WiXgZ2gt9Aoir3MeORJxg4.Z/")

    assert (get_encrypted_password("123", "sha512", salt="12345678", rounds=5000) ==
            "$6$12345678$LcV9LQiaPekQxZ.OfkMADjFdSO2k9zfbDQrHPVcYjSLqSdjLYpsgqviYvTEP/R41yPmhH3CCeEDqVhW1VHr3L.")

    assert get_encrypted_password("123", "crypt16", salt="12") == "12pELHK2ME3McUFlHxel6uMM"

    # Try algorithm that uses a raw salt
    assert get_encrypted_password("123", "pbkdf2_sha256")
    # Try algorithm with ident
    assert get_encrypted_password("123", "pbkdf2_sha256", ident='invalid_ident')


@pytest.mark.skipif(not encrypt.PASSLIB_AVAILABLE, reason='passlib must be installed to run this test')
def test_do_encrypt_passlib():
    with pytest.raises(AnsibleError):
        encrypt.do_encrypt("123", "sha257_crypt", salt="12345678")

    # Uses passlib default rounds value for sha256 matching crypt behaviour.
    assert encrypt.do_encrypt("123", "sha256_crypt", salt="12345678") == "$5$rounds=535000$12345678$uy3TurUPaY71aioJi58HvUY8jkbhSQU8HepbyaNngv."

    assert encrypt.do_encrypt("123", "md5_crypt", salt="12345678") == "$1$12345678$tRy4cXc3kmcfRZVj4iFXr/"

    assert encrypt.do_encrypt("123", "crypt16", salt="12") == "12pELHK2ME3McUFlHxel6uMM"

    assert encrypt.do_encrypt("123", "bcrypt",
                              salt='1234567890123456789012',
                              ident='2a') == "$2a$12$123456789012345678901ugbM1PeTfRQ0t6dCJu5lQA8hwrZOYgDu"


def test_random_salt():
    res = encrypt.random_salt()
    expected_salt_candidate_chars = u'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789./'
    assert len(res) == 8
    for res_char in res:
        assert res_char in expected_salt_candidate_chars


def test_passlib_bcrypt_salt(recwarn):
    passlib_exc = pytest.importorskip("passlib.exc")

    secret = 'foo'
    salt = '1234567890123456789012'
    repaired_salt = '123456789012345678901u'
    expected = '$2b$12$123456789012345678901uMv44x.2qmQeefEGb3bcIRc1mLuO7bqa'
    ident = '2b'

    p = encrypt.PasslibHash('bcrypt')

    result = p.hash(secret, salt=salt, ident=ident)
    passlib_warnings = [w.message for w in recwarn if isinstance(w.message, passlib_exc.PasslibHashWarning)]
    assert len(passlib_warnings) == 0
    assert result == expected

    recwarn.clear()

    result = p.hash(secret, salt=repaired_salt, ident=ident)
    assert result == expected
