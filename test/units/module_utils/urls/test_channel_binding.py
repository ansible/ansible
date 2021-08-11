# -*- coding: utf-8 -*-
# (c) 2020 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import base64
import os.path
import pytest

from ansible.module_utils import urls


@pytest.mark.skipif(not urls.HAS_CRYPTOGRAPHY, reason='Requires cryptography to be installed')
@pytest.mark.parametrize('certificate, expected', [
    ('rsa_md5.pem', b'\x23\x34\xB8\x47\x6C\xBF\x4E\x6D'
                    b'\xFC\x76\x6A\x5D\x5A\x30\xD6\x64'
                    b'\x9C\x01\xBA\xE1\x66\x2A\x5C\x3A'
                    b'\x13\x02\xA9\x68\xD7\xC6\xB0\xF6'),
    ('rsa_sha1.pem', b'\x14\xCF\xE8\xE4\xB3\x32\xB2\x0A'
                     b'\x34\x3F\xC8\x40\xB1\x8F\x9F\x6F'
                     b'\x78\x92\x6A\xFE\x7E\xC3\xE7\xB8'
                     b'\xE2\x89\x69\x61\x9B\x1E\x8F\x3E'),
    ('rsa_sha256.pem', b'\x99\x6F\x3E\xEA\x81\x2C\x18\x70'
                       b'\xE3\x05\x49\xFF\x9B\x86\xCD\x87'
                       b'\xA8\x90\xB6\xD8\xDF\xDF\x4A\x81'
                       b'\xBE\xF9\x67\x59\x70\xDA\xDB\x26'),
    ('rsa_sha384.pem', b'\x34\xF3\x03\xC9\x95\x28\x6F\x4B'
                       b'\x21\x4A\x9B\xA6\x43\x5B\x69\xB5'
                       b'\x1E\xCF\x37\x58\xEA\xBC\x2A\x14'
                       b'\xD7\xA4\x3F\xD2\x37\xDC\x2B\x1A'
                       b'\x1A\xD9\x11\x1C\x5C\x96\x5E\x10'
                       b'\x75\x07\xCB\x41\x98\xC0\x9F\xEC'),
    ('rsa_sha512.pem', b'\x55\x6E\x1C\x17\x84\xE3\xB9\x57'
                       b'\x37\x0B\x7F\x54\x4F\x62\xC5\x33'
                       b'\xCB\x2C\xA5\xC1\xDA\xE0\x70\x6F'
                       b'\xAE\xF0\x05\x44\xE1\xAD\x2B\x76'
                       b'\xFF\x25\xCF\xBE\x69\xB1\xC4\xE6'
                       b'\x30\xC3\xBB\x02\x07\xDF\x11\x31'
                       b'\x4C\x67\x38\xBC\xAE\xD7\xE0\x71'
                       b'\xD7\xBF\xBF\x2C\x9D\xFA\xB8\x5D'),
    ('rsa-pss_sha256.pem', b'\xF2\x31\xE6\xFF\x3F\x9E\x16\x1B'
                           b'\xC2\xDC\xBB\x89\x8D\x84\x47\x4E'
                           b'\x58\x9C\xD7\xC2\x7A\xDB\xEF\x8B'
                           b'\xD9\xC0\xC0\x68\xAF\x9C\x36\x6D'),
    ('rsa-pss_sha512.pem', b'\x85\x85\x19\xB9\xE1\x0F\x23\xE2'
                           b'\x1D\x2C\xE9\xD5\x47\x2A\xAB\xCE'
                           b'\x42\x0F\xD1\x00\x75\x9C\x53\xA1'
                           b'\x7B\xB9\x79\x86\xB2\x59\x61\x27'),
    ('ecdsa_sha256.pem', b'\xFE\xCF\x1B\x25\x85\x44\x99\x90'
                         b'\xD9\xE3\xB2\xC9\x2D\x3F\x59\x7E'
                         b'\xC8\x35\x4E\x12\x4E\xDA\x75\x1D'
                         b'\x94\x83\x7C\x2C\x89\xA2\xC1\x55'),
    ('ecdsa_sha512.pem', b'\xE5\xCB\x68\xB2\xF8\x43\xD6\x3B'
                         b'\xF4\x0B\xCB\x20\x07\x60\x8F\x81'
                         b'\x97\x61\x83\x92\x78\x3F\x23\x30'
                         b'\xE5\xEF\x19\xA5\xBD\x8F\x0B\x2F'
                         b'\xAA\xC8\x61\x85\x5F\xBB\x63\xA2'
                         b'\x21\xCC\x46\xFC\x1E\x22\x6A\x07'
                         b'\x24\x11\xAF\x17\x5D\xDE\x47\x92'
                         b'\x81\xE0\x06\x87\x8B\x34\x80\x59'),
])
def test_cbt_with_cert(certificate, expected):
    with open(os.path.join(os.path.dirname(__file__), 'fixtures', 'cbt', certificate)) as fd:
        cert_der = base64.b64decode("".join([l.strip() for l in fd.readlines()[1:-1]]))

    actual = urls.get_channel_binding_cert_hash(cert_der)
    assert actual == expected


def test_cbt_no_cryptography(monkeypatch):
    monkeypatch.setattr(urls, 'HAS_CRYPTOGRAPHY', False)
    assert urls.get_channel_binding_cert_hash(None) is None
