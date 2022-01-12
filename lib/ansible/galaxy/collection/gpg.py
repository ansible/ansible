# -*- coding: utf-8 -*-
# Copyright: (c) 2022, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""Signature verification helpers."""

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.errors import AnsibleError
from ansible.galaxy.user_agent import user_agent
from ansible.module_utils.common.text.converters import to_text
from ansible.module_utils.urls import open_url

import os
import subprocess
import textwrap

from dataclasses import dataclass, fields as dc_fields
from urllib.error import HTTPError, URLError


def run_gpg_verify(b_manifest_file, signature, keyring, display):
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
    cmd_str = ' '.join(to_text(arg) for arg in cmd)
    display.vvvv(f"Running command '{cmd}'")

    try:
        p = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            pass_fds=(status_fd_write,),
        )
    except FileNotFoundError as err:
        raise AnsibleError(
            f"Failed during GnuPG verification with command '{cmd_str}': {exception}"
        ) from err
    except subprocess.SubprocessError as err:
        raise AnsibleError(
            f"Failed during GnuPG verification with command '{cmd_str}': {exception}"
        ) from err
    else:
        stdout, stderr = p.communicate(input=signature)
    finally:
        os.close(status_fd_write)

    with os.fdopen(status_fd_read) as f:
        stdout = f.read()
        display.vvvv(f"{stdout} (exit code {p.returncode})")
        return stdout, p.returncode


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


def get_signature_from_source(source, display=None):
    if display is not None:
        display.vvvv(f"Using signature at {source}")
    try:
        with open_url(
            to_text(source),
            http_agent=user_agent(),
            follow_redirects='safe'
        ) as resp:
            return resp.read()
    except (HTTPError, URLError) as e:
        raise AnsibleError(
            f"Failed to get signature for collection verification from '{source}': {e}"
        ) from e


# TODO: Optimize with slots=True when the min Python version for the controller is >= 3.10
@dataclass(frozen=True)
class GpgBaseError(Exception):
    status: str

    def __post_init__(self):
        for field in dc_fields(self):
            super().__setattr__(field.name, field.type(getattr(self, field.name)))


@dataclass(frozen=True)
class GpgExpSig(GpgBaseError):
    keyid: str
    username: str

    @staticmethod
    def explain():
        return 'The signature with the keyid is good, but the signature is expired'


@dataclass(frozen=True)
class GpgExpKeySig(GpgBaseError):
    keyid: str
    username: str

    @staticmethod
    def explain():
        return 'The signature with the keyid is good, but the signature was made by an expired key'


@dataclass(frozen=True)
class GpgRevKeySig(GpgBaseError):
    keyid: str
    username: str

    @staticmethod
    def explain():
        return 'The signature with the keyid is good, but the signature was made by a revoked key'


@dataclass(frozen=True)
class GpgBadSig(GpgBaseError):
    keyid: str
    username: str

    @staticmethod
    def explain():
        return 'The signature with the keyid has not been verified okay'


@dataclass(frozen=True)
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


@dataclass(frozen=True)
class GpgNoPubkey(GpgBaseError):
    keyid: str

    @staticmethod
    def explain():
        return 'The public key is not available'


@dataclass(frozen=True)
class GpgMissingPassPhrase(GpgBaseError):
    @staticmethod
    def explain():
        return 'No passphrase was supplied'


@dataclass(frozen=True)
class GpgBadPassphrase(GpgBaseError):
    keyid: str

    @staticmethod
    def explain():
        return 'The supplied passphrase was wrong or not given'


@dataclass(frozen=True)
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


@dataclass(frozen=True)
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


@dataclass(frozen=True)
class GpgError(GpgBaseError):
    location: str
    code: int
    more: str

    @staticmethod
    def explain():
        return 'This is a generic error status message, it might be followed by error location specific data'


@dataclass(frozen=True)
class GpgFailure(GpgBaseError):
    location: str
    code: int

    @staticmethod
    def explain():
        return 'This is the counterpart to SUCCESS and used to indicate a program failure'


@dataclass(frozen=True)
class GpgBadArmor(GpgBaseError):
    @staticmethod
    def explain():
        return 'The ASCII armor is corrupted'


@dataclass(frozen=True)
class GpgKeyExpired(GpgBaseError):
    timestamp: int

    @staticmethod
    def explain():
        return 'The key has expired'


@dataclass(frozen=True)
class GpgKeyRevoked(GpgBaseError):
    @staticmethod
    def explain():
        return 'The used key has been revoked by its owner'


@dataclass(frozen=True)
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
