# -*- coding: utf-8 -*-
# Copyright: (c) 2022, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""Signature verification helpers."""

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.errors import AnsibleError
from ansible.module_utils.common.text.converters import to_text
from ansible.module_utils.urls import open_url
from ansible.utils.display import Display

import os
import subprocess
import textwrap

from dataclasses import dataclass, fields as dc_fields
from urllib.error import HTTPError

display = Display()


def run_gpg_verify(b_manifest_file, signature, keyring):
    status_fd_read, status_fd_write = os.pipe()

    cmd = [
        'gpg',
        f'--status-fd={status_fd_write}',
        '--verify',
        '--batch',
        '--no-tty',
        '--no-default-keyring',
        f'--keyring={keyring}',
        '-',
        b_manifest_file,
    ]

    try:
        p = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            pass_fds=(status_fd_write,),
        )
        stdout, stderr = p.communicate(input=signature)
    except subprocess.SubprocessError as err:
        cmd_str = ' '.join([to_text(arg) for arg in cmd])
        display.error(f"Failed during GnuPG verification with command '{cmd_str}':\n{err}")
        p = None
    finally:
        os.close(status_fd_write)

    if p is None:
        return

    rc = p.returncode
    with os.fdopen(status_fd_read) as f:
        return f.read(), p.returncode


def parse_gpg_errors(status_out, rc):
    errors = []
    for line in status_out.splitlines():
        if not line:
            continue
        try:
            _dummy, status, remainder = line.split(None, 2)
        except ValueError:
            _dummy, status = line.split(None, 1)
            remainder = None
        try:
            cls = GPG_ERROR_MAP[status]
        except KeyError:
            continue

        fields = [status]
        if remainder:
            fields.extend(
                remainder.split(
                    None,
                    len(dc_fields(cls)) - 2
                )
            )

        yield cls(*fields)


def get_signature_from_url(url, quiet=False):
    if not quiet:
        display.vvvv(f"Using signature at {url}")
    try:
        resp = open_url(url, follow_redirects='safe')
    except HTTPError as e:
        raise AnsibleError(
            "Failed to open signature URL '{url}' for collection verification"
        ) from e
    return resp.read()


@dataclass
class GpgBaseError(Exception):
    status: str

    def __post_init__(self):
        for field in dc_fields(self):
            setattr(self, field.name, field.type(getattr(self, field.name)))


@dataclass
class GpgExpSig(GpgBaseError):
    keyid: str
    username: str

    @staticmethod
    def explain():
        return 'The signature with the keyid is good, but the signature is expired'


@dataclass
class GpgExpKeySig(GpgBaseError):
    keyid: str
    username: str

    @staticmethod
    def explain():
        return 'The signature with the keyid is good, but the signature was made by an expired key'


@dataclass
class GpgRevKeySig(GpgBaseError):
    keyid: str
    username: str

    @staticmethod
    def explain():
        return 'The signature with the keyid is good, but the signature was made by a revoked key'


@dataclass
class GpgBadSig(GpgBaseError):
    keyid: str
    username: str

    @staticmethod
    def explain():
        return 'The signature with the keyid has not been verified okay'


@dataclass
class GpgErrSig(GpgBaseError):
    keyid: str
    pkalgo: int
    hashalgo: int
    sig_class: str
    time: int
    rc: int
    fpr: str

    @staticmethod
    def explain():
        return (
            'It was not possible to check the signature.  This may be caused by '
            'a missing public key or an unsupported algorithm.  A RC of 4 '
            'indicates unknown algorithm, a 9 indicates a missing public '
            'key.'
        )


@dataclass
class GpgNoPubkey(GpgBaseError):
    keyid: str

    @staticmethod
    def explain():
        return 'The public key is not available'


@dataclass
class GpgMissingPassPhrase(GpgBaseError):
    @staticmethod
    def explain():
        return 'No passphrase was supplied'


@dataclass
class GpgBadPassphrase(GpgBaseError):
    keyid: str

    @staticmethod
    def explain():
        return 'The supplied passphrase was wrong or not given'


@dataclass
class GpgNoData(GpgBaseError):
    what: str

    @staticmethod
    def explain():
        return textwrap.dedent('''
            No data has been found.  Codes for WHAT are:
            - 1 :: No armored data.
            - 2 :: Expected a packet but did not found one.
            - 3 :: Invalid packet found, this may indicate a non OpenPGP
                   message.
            - 4 :: Signature expected but not found
        ''').strip()


@dataclass
class GpgUnexpected(GpgBaseError):
    what: str

    @staticmethod
    def explain():
        return textwrap.dedent('''
            No data has been found.  Codes for WHAT are:
            - 1 :: No armored data.
            - 2 :: Expected a packet but did not found one.
            - 3 :: Invalid packet found, this may indicate a non OpenPGP
                   message.
            - 4 :: Signature expected but not found
        ''').strip()


@dataclass
class GpgError(GpgBaseError):
    location: str
    code: int
    more: str

    @staticmethod
    def explain():
        return 'This is a generic error status message, it might be followed by error location specific data'


@dataclass
class GpgFailure(GpgBaseError):
    location: str
    code: int

    @staticmethod
    def explain():
        return 'This is the counterpart to SUCCESS and used to indicate a program failure'


@dataclass
class GpgBadArmor(GpgBaseError):
    @staticmethod
    def explain():
        return 'The ASCII armor is corrupted'


@dataclass
class GpgKeyExpired(GpgBaseError):
    timestamp: int

    @staticmethod
    def explain():
        return 'The key has expired'


@dataclass
class GpgKeyRevoked(GpgBaseError):
    @staticmethod
    def explain():
        return 'The used key has been revoked by its owner'


@dataclass
class GpgNoSecKey(GpgBaseError):
    keyid: str

    @staticmethod
    def explain():
        return 'The secret key is not available'


GPG_ERROR_MAP = {
    'EXPSIG': GpgExpSig,
    'EXPKEYSIG': GpgExpKeySig,
    'REVKEYSIG': GpgRevKeySig,
    'BADSIG': GpgBadSig,
    'ERRSIG': GpgErrSig,
    'NO_PUBKEY': GpgNoPubkey,
    'MISSING_PASSPHRASE': GpgMissingPassPhrase,
    'BAD_PASSPHRASE': GpgBadPassphrase,
    'NODATA': GpgNoData,
    'UNEXPECTED': GpgUnexpected,
    'ERROR': GpgError,
    'FAILURE': GpgFailure,
    'BADARMOR': GpgBadArmor,
    'KEYEXPIRED': GpgKeyExpired,
    'KEYREVOKED': GpgKeyRevoked,
    'NO_SECKEY': GpgNoSecKey,
}
