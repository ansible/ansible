# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import annotations

import hashlib
import tempfile

from ansible.module_utils.common.text.converters import to_bytes
from ansible.module_utils.common import hashing

import pytest


secure_hash_testdata = [
    pytest.param("sha1", "a94a8fe5ccb19ba61c4c0873d391e987982fbbd3", id="sha1_str"),
    pytest.param(
        "sha224",
        "90a3ed9e32b2aaf4c61c410eb925426119e1a9dc53d4286ade99a809",
        id="sha224_str",
    ),
    pytest.param(
        "sha256",
        "9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08",
        id="sha256_str",
    ),
    pytest.param(
        "sha384",
        "768412320f7b0aa5812fce428dc4706b3cae50e02a64caa16a782249bfe8efc4b7ef1ccb126255d196047dfedf17a0a9",
        id="sha384_str",
    ),
    pytest.param(
        hashlib.sha1, "a94a8fe5ccb19ba61c4c0873d391e987982fbbd3", id="sha1_call"
    ),
    pytest.param(
        hashlib.sha224,
        "90a3ed9e32b2aaf4c61c410eb925426119e1a9dc53d4286ade99a809",
        id="sha224_call",
    ),
    pytest.param(
        hashlib.sha256,
        "9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08",
        id="sha256_call",
    ),
    pytest.param(
        hashlib.sha384,
        "768412320f7b0aa5812fce428dc4706b3cae50e02a64caa16a782249bfe8efc4b7ef1ccb126255d196047dfedf17a0a9",
        id="sha384_call",
    ),
]


@pytest.mark.parametrize("hash_func,expected", secure_hash_testdata)
def test_generate_secure_checksum(hash_func, expected):
    test_str = "test"
    assert hashing.generate_secure_checksum(test_str, hash_func) == expected


def test_generate_secure_file_checksum_none():
    assert hashing.generate_secure_file_checksum("/path/to/non-existent-file") is None


@pytest.mark.parametrize("hash_func,expected", secure_hash_testdata)
def test_generate_secure_file_checksum(hash_func, expected):
    with tempfile.NamedTemporaryFile() as text_file:
        text_file.write(to_bytes("test"))
        text_file.flush()

        assert (
            hashing.generate_secure_file_checksum(text_file.name, hash_func) == expected
        )


def test_generate_secure_checksum_fail_none():
    with pytest.raises(ValueError, match=r"^The parameter 'hash_func'"):
        hashing.generate_secure_checksum("test", hash_func=None)


def test_generate_secure_file_checksum_fail_none():
    with pytest.raises(ValueError, match=r"^The parameter 'hash_func'"):
        with tempfile.NamedTemporaryFile() as text_file:
            text_file.write(to_bytes("test"))
            text_file.flush()
            hashing.generate_secure_file_checksum(text_file.name, hash_func=None)
