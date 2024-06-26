# -*- coding: utf-8 -*-
# Copyright: (c) 2022, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""Signature verification helpers."""
from __future__ import annotations

from ansible.errors import AnsibleError
from ansible.galaxy.user_agent import user_agent
from ansible.module_utils.urls import open_url

import contextlib
import inspect
import os
import subprocess
import typing as t

from dataclasses import dataclass, fields as dc_fields
from urllib.error import HTTPError, URLError

if t.TYPE_CHECKING:
    from ansible.utils.display import Display


def get_signature_from_source(source, display=None):  # type: (str, t.Optional[Display]) -> str
    if display is not None:
        display.vvvv(f"Using signature at {source}")
    try:
        with open_url(
            source,
            http_agent=user_agent(),
            validate_certs=True,
            follow_redirects='safe'
        ) as resp:
            signature = resp.read()
    except (HTTPError, URLError) as e:
        raise AnsibleError(
            f"Failed to get signature for collection verification from '{source}': {e}"
        ) from e

    return signature


def run_gpg_verify(
    manifest_file,  # type: str
    signature,  # type: str
    keyring,  # type: str
    display,  # type: Display
):  # type: (...) -> tuple[str, int]
    status_fd_read, status_fd_write = os.pipe()

    # running the gpg command will create the keyring if it does not exist
    remove_keybox = not os.path.exists(keyring)

    cmd = [
        'gpg',
        f'--status-fd={status_fd_write}',
        '--verify',
        '--batch',
        '--no-tty',
        '--no-default-keyring',
        f'--keyring={keyring}',
        '-',
        manifest_file,
    ]
    cmd_str = ' '.join(cmd)
    display.vvvv(f"Running command '{cmd}'")

    try:
        p = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            pass_fds=(status_fd_write,),
            encoding='utf8',
        )
    except (FileNotFoundError, subprocess.SubprocessError) as err:
        raise AnsibleError(
            f"Failed during GnuPG verification with command '{cmd_str}': {err}"
        ) from err
    else:
        stdout, stderr = p.communicate(input=signature)
    finally:
        os.close(status_fd_write)

    if remove_keybox:
        with contextlib.suppress(OSError):
            os.remove(keyring)

    with os.fdopen(status_fd_read) as f:
        stdout = f.read()
        display.vvvv(
            f"stdout: \n{stdout}\nstderr: \n{stderr}\n(exit code {p.returncode})"
        )
        return stdout, p.returncode


def parse_gpg_errors(status_out):  # type: (str) -> t.Iterator[GpgBaseError]
    for line in status_out.splitlines():
        if not line:
            continue
        try:
            _dummy, status, remainder = line.split(maxsplit=2)
        except ValueError:
            _dummy, status = line.split(maxsplit=1)
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


@dataclass(frozen=True, slots=True)
class GpgBaseError(Exception):
    status: str

    @classmethod
    def get_gpg_error_description(cls) -> str:
        """Return the current class description."""
        return ' '.join(cls.__doc__.split())

    def __post_init__(self):
        for field_name, field_type in inspect.get_annotations(type(self), eval_str=True).items():
            super(GpgBaseError, self).__setattr__(field_name, field_type(getattr(self, field_name)))


@dataclass(frozen=True, slots=True)
class GpgExpSig(GpgBaseError):
    """The signature with the keyid is good, but the signature is expired."""
    keyid: str
    username: str


@dataclass(frozen=True, slots=True)
class GpgExpKeySig(GpgBaseError):
    """The signature with the keyid is good, but the signature was made by an expired key."""
    keyid: str
    username: str


@dataclass(frozen=True, slots=True)
class GpgRevKeySig(GpgBaseError):
    """The signature with the keyid is good, but the signature was made by a revoked key."""
    keyid: str
    username: str


@dataclass(frozen=True, slots=True)
class GpgBadSig(GpgBaseError):
    """The signature with the keyid has not been verified okay."""
    keyid: str
    username: str


@dataclass(frozen=True, slots=True)
class GpgErrSig(GpgBaseError):
    """"It was not possible to check the signature.  This may be caused by
    a missing public key or an unsupported algorithm.  A RC of 4
    indicates unknown algorithm, a 9 indicates a missing public
    key.
    """
    keyid: str
    pkalgo: int
    hashalgo: int
    sig_class: str
    time: int
    rc: int
    fpr: str


@dataclass(frozen=True, slots=True)
class GpgNoPubkey(GpgBaseError):
    """The public key is not available."""
    keyid: str


@dataclass(frozen=True, slots=True)
class GpgMissingPassPhrase(GpgBaseError):
    """No passphrase was supplied."""


@dataclass(frozen=True, slots=True)
class GpgBadPassphrase(GpgBaseError):
    """The supplied passphrase was wrong or not given."""
    keyid: str


@dataclass(frozen=True, slots=True)
class GpgNoData(GpgBaseError):
    """No data has been found.  Codes for WHAT are:
    - 1 :: No armored data.
    - 2 :: Expected a packet but did not find one.
    - 3 :: Invalid packet found, this may indicate a non OpenPGP
           message.
    - 4 :: Signature expected but not found.
    """
    what: str


@dataclass(frozen=True, slots=True)
class GpgUnexpected(GpgBaseError):
    """No data has been found.  Codes for WHAT are:
    - 1 :: No armored data.
    - 2 :: Expected a packet but did not find one.
    - 3 :: Invalid packet found, this may indicate a non OpenPGP
           message.
    - 4 :: Signature expected but not found.
    """
    what: str


@dataclass(frozen=True, slots=True)
class GpgError(GpgBaseError):
    """This is a generic error status message, it might be followed by error location specific data."""
    location: str
    code: int
    more: str = ""


@dataclass(frozen=True, slots=True)
class GpgFailure(GpgBaseError):
    """This is the counterpart to SUCCESS and used to indicate a program failure."""
    location: str
    code: int


@dataclass(frozen=True, slots=True)
class GpgBadArmor(GpgBaseError):
    """The ASCII armor is corrupted."""


@dataclass(frozen=True, slots=True)
class GpgKeyExpired(GpgBaseError):
    """The key has expired."""
    timestamp: int


@dataclass(frozen=True, slots=True)
class GpgKeyRevoked(GpgBaseError):
    """The used key has been revoked by its owner."""


@dataclass(frozen=True, slots=True)
class GpgNoSecKey(GpgBaseError):
    """The secret key is not available."""
    keyid: str


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
