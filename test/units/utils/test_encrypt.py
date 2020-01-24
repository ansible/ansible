# (c) 2018, Matthias Fuchs <matthias.s.fuchs@gmail.com>
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

import sys

import pytest

from ansible.errors import AnsibleError, AnsibleFilterError
from ansible.plugins.filter.core import get_encrypted_password
from ansible.utils import encrypt


class passlib_off(object):
    def __init__(self):
        self.orig = encrypt.PASSLIB_AVAILABLE

    def __enter__(self):
        encrypt.PASSLIB_AVAILABLE = False
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        encrypt.PASSLIB_AVAILABLE = self.orig


def assert_hash(expected, secret, algorithm, **settings):

    if encrypt.PASSLIB_AVAILABLE:
        assert encrypt.passlib_or_crypt(secret, algorithm, **settings) == expected
        assert encrypt.PasslibHash(algorithm).hash(secret, **settings) == expected
    else:
        assert encrypt.passlib_or_crypt(secret, algorithm, **settings) == expected
        with pytest.raises(AnsibleError) as excinfo:
            encrypt.PasslibHash(algorithm).hash(secret, **settings)
        assert excinfo.value.args[0] == "passlib must be installed to hash with '%s'" % algorithm


@pytest.mark.skipif(sys.platform.startswith('darwin'), reason='macOS requires passlib')
def test_encrypt_with_rounds_no_passlib():
    with passlib_off():
        assert_hash("$5$12345678$uAZsE3BenI2G.nA8DpTl.9Dc8JiqacI53pEqRr5ppT7",
                    secret="123", algorithm="sha256_crypt", salt="12345678", rounds=5000)
        assert_hash("$5$rounds=10000$12345678$JBinliYMFEcBeAXKZnLjenhgEhTmJBvZn3aR8l70Oy/",
                    secret="123", algorithm="sha256_crypt", salt="12345678", rounds=10000)
        assert_hash("$6$12345678$LcV9LQiaPekQxZ.OfkMADjFdSO2k9zfbDQrHPVcYjSLqSdjLYpsgqviYvTEP/R41yPmhH3CCeEDqVhW1VHr3L.",
                    secret="123", algorithm="sha512_crypt", salt="12345678", rounds=5000)


# If passlib is not installed. this is identical to the test_encrypt_with_rounds_no_passlib() test
@pytest.mark.skipif(not encrypt.PASSLIB_AVAILABLE, reason='passlib must be installed to run this test')
def test_encrypt_with_rounds():
    assert_hash("$5$12345678$uAZsE3BenI2G.nA8DpTl.9Dc8JiqacI53pEqRr5ppT7",
                secret="123", algorithm="sha256_crypt", salt="12345678", rounds=5000)
    assert_hash("$5$rounds=10000$12345678$JBinliYMFEcBeAXKZnLjenhgEhTmJBvZn3aR8l70Oy/",
                secret="123", algorithm="sha256_crypt", salt="12345678", rounds=10000)
    assert_hash("$6$12345678$LcV9LQiaPekQxZ.OfkMADjFdSO2k9zfbDQrHPVcYjSLqSdjLYpsgqviYvTEP/R41yPmhH3CCeEDqVhW1VHr3L.",
                secret="123", algorithm="sha512_crypt", salt="12345678", rounds=5000)


@pytest.mark.skipif(sys.platform.startswith('darwin'), reason='macOS requires passlib')
def test_encrypt_default_rounds_no_passlib():
    with passlib_off():
        assert_hash("$1$12345678$tRy4cXc3kmcfRZVj4iFXr/",
                    secret="123", algorithm="md5_crypt", salt="12345678")
        assert_hash("$5$12345678$uAZsE3BenI2G.nA8DpTl.9Dc8JiqacI53pEqRr5ppT7",
                    secret="123", algorithm="sha256_crypt", salt="12345678")
        assert_hash("$6$12345678$LcV9LQiaPekQxZ.OfkMADjFdSO2k9zfbDQrHPVcYjSLqSdjLYpsgqviYvTEP/R41yPmhH3CCeEDqVhW1VHr3L.",
                    secret="123", algorithm="sha512_crypt", salt="12345678")

        assert encrypt.CryptHash("md5_crypt").hash("123")


# If passlib is not installed. this is identical to the test_encrypt_default_rounds_no_passlib() test
@pytest.mark.skipif(not encrypt.PASSLIB_AVAILABLE, reason='passlib must be installed to run this test')
def test_encrypt_default_rounds():
    assert_hash("$1$12345678$tRy4cXc3kmcfRZVj4iFXr/",
                secret="123", algorithm="md5_crypt", salt="12345678")
    assert_hash("$5$12345678$uAZsE3BenI2G.nA8DpTl.9Dc8JiqacI53pEqRr5ppT7",
                secret="123", algorithm="sha256_crypt", salt="12345678")
    assert_hash("$6$12345678$LcV9LQiaPekQxZ.OfkMADjFdSO2k9zfbDQrHPVcYjSLqSdjLYpsgqviYvTEP/R41yPmhH3CCeEDqVhW1VHr3L.",
                secret="123", algorithm="sha512_crypt", salt="12345678")

    assert encrypt.PasslibHash("md5_crypt").hash("123")


@pytest.mark.skipif(sys.platform.startswith('darwin'), reason='macOS requires passlib')
def test_password_hash_filter_no_passlib():
    with passlib_off():
        assert not encrypt.PASSLIB_AVAILABLE
        assert get_encrypted_password("123", "md5", salt="12345678") == "$1$12345678$tRy4cXc3kmcfRZVj4iFXr/"

        with pytest.raises(AnsibleFilterError):
            get_encrypted_password("123", "crypt16", salt="12")


def test_password_hash_filter_passlib():
    if not encrypt.PASSLIB_AVAILABLE:
        pytest.skip("passlib not available")

    with pytest.raises(AnsibleFilterError):
        get_encrypted_password("123", "sha257", salt="12345678")

    # Uses 5000 rounds by default for sha256 matching crypt behaviour
    assert get_encrypted_password("123", "sha256", salt="12345678") == "$5$12345678$uAZsE3BenI2G.nA8DpTl.9Dc8JiqacI53pEqRr5ppT7"
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


@pytest.mark.skipif(sys.platform.startswith('darwin'), reason='macOS requires passlib')
def test_do_encrypt_no_passlib():
    with passlib_off():
        assert not encrypt.PASSLIB_AVAILABLE
        assert encrypt.do_encrypt("123", "md5_crypt", salt="12345678") == "$1$12345678$tRy4cXc3kmcfRZVj4iFXr/"

        with pytest.raises(AnsibleError):
            encrypt.do_encrypt("123", "crypt16", salt="12")


def test_do_encrypt_passlib():
    if not encrypt.PASSLIB_AVAILABLE:
        pytest.skip("passlib not available")

    with pytest.raises(AnsibleError):
        encrypt.do_encrypt("123", "sha257_crypt", salt="12345678")

    # Uses 5000 rounds by default for sha256 matching crypt behaviour.
    assert encrypt.do_encrypt("123", "sha256_crypt", salt="12345678") == "$5$12345678$uAZsE3BenI2G.nA8DpTl.9Dc8JiqacI53pEqRr5ppT7"

    assert encrypt.do_encrypt("123", "md5_crypt", salt="12345678") == "$1$12345678$tRy4cXc3kmcfRZVj4iFXr/"

    assert encrypt.do_encrypt("123", "crypt16", salt="12") == "12pELHK2ME3McUFlHxel6uMM"


def test_random_salt():
    res = encrypt.random_salt()
    expected_salt_candidate_chars = u'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789./'
    assert len(res) == 8
    for res_char in res:
        assert res_char in expected_salt_candidate_chars
