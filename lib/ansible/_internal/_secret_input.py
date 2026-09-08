# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import collections.abc as _c
import os
import subprocess

from ansible.errors import AnsibleError
from ansible.module_utils.common.file import is_executable
from ansible.module_utils.datatag import native_type_name
from ansible.module_utils.secrets import register_secrets
from ansible.parsing.utils.yaml import from_yaml

_SUPPORTED_VERSIONS = frozenset((1,))


def load_secret_input_files(paths: _c.Iterable[os.PathLike], /) -> None:
    """Read each secret input file and register its secrets for output masking."""
    for path in paths:
        register_secrets(_read_secret_input_file(path))


def _read_secret_input_file(path: os.PathLike) -> _c.Iterable[str]:
    """Parse and validate a single secret input file, returning its list of secret values."""
    # Cannot use os.access(path, os.X_OK) because on macOS running as root any
    # non regular file (e.g. pipe) will always be True. Our is_executable
    # check does not suffer from this issue.
    if is_executable(str(path)):
        raw = _run_secret_input_command(path)
    else:
        with open(path, 'rb') as f:
            raw = f.read()

    data = from_yaml(
        raw.decode('utf-8'),
        file_name=str(path),
        show_content=False,
    )

    if not isinstance(data, _c.Mapping):
        raise AnsibleError(f"Secrets input file {path!r} must contain a mapping, not a {native_type_name(data)}.")

    version = data.get('version')

    # bool is a subclass of int, but `version: true` is not a valid version
    if isinstance(version, bool) or version not in _SUPPORTED_VERSIONS:
        raise AnsibleError(
            f"Secrets input file {path!r} has an unsupported version {version!r}; "
            f"supported versions are: {', '.join(str(v) for v in sorted(_SUPPORTED_VERSIONS))}."
        )

    secrets = data.get('secrets')

    # a str is a Sequence, guard against a bare string being treated as a list of characters
    if not isinstance(secrets, _c.Sequence) or isinstance(secrets, (str, bytes)):
        raise AnsibleError(f"Secrets input file {path!r} must contain a 'secrets' list.")

    for idx, secret in enumerate(secrets):
        # values are validated as strings without coercion, so non-string entries are an error
        # cannot show actual value in error message because it may be a secret, so show idx and type instead
        if not isinstance(secret, str):
            raise AnsibleError(f"Secrets input file {path!r} entry secrets[{idx}] must be a string, not a {native_type_name(secret)}.")

    return secrets


def _run_secret_input_command(path: os.PathLike) -> bytes:
    """Execute an executable secrets input file and return its stdout as bytes."""
    try:
        # stderr is passed through so the command can prompt or report errors to the user
        proc = subprocess.run([path], stdout=subprocess.PIPE, check=False)
    except OSError as ex:
        raise AnsibleError(f"Could not run secrets input file {path!r}: {ex}. If this is not an executable, remove the executable bit from the file.") from ex

    if proc.returncode != 0:
        raise AnsibleError(f"Secrets input file {path!r} returned non-zero exit status {proc.returncode}.")

    return proc.stdout
