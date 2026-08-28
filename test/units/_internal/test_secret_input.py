from __future__ import annotations

import pathlib
import stat

from ansible._internal._secret_input import load_secret_input_files
from ansible.errors import AnsibleError
from ansible.module_utils.secrets import mask_secrets

import pytest


def _write(tmp_path: pathlib.Path, name: str, content: str) -> str:
    path = tmp_path / name
    path.write_text(content)
    return str(path)


def _write_executable(tmp_path: pathlib.Path, name: str, content: str) -> str:
    path = tmp_path / name
    path.write_text(content)
    path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

    return str(path)


def test_yaml_secrets_are_masked(tmp_path: pathlib.Path) -> None:
    path = _write(tmp_path, 'secrets.yml', 'version: 1\nsecrets:\n  - yaml-secret-alpha\n  - yaml-secret-beta\n')

    load_secret_input_files([path])

    assert mask_secrets('a yaml-secret-alpha and yaml-secret-beta z') == 'a $REDACTED$ and $REDACTED$ z'


def test_json_secrets_are_masked(tmp_path: pathlib.Path) -> None:
    path = _write(tmp_path, 'secrets.json', '{"version": 1, "secrets": ["json-secret-value"]}')

    load_secret_input_files([path])

    assert mask_secrets('a json-secret-value z') == 'a $REDACTED$ z'


def test_multiple_files_are_masked(tmp_path: pathlib.Path) -> None:
    p1 = _write(tmp_path, 's1.yml', 'version: 1\nsecrets:\n  - multi-file-one\n')
    p2 = _write(tmp_path, 's2.json', '{"version": 1, "secrets": ["multi-file-two"]}')

    load_secret_input_files([p1, p2])

    assert mask_secrets('a multi-file-one and multi-file-two z') == 'a $REDACTED$ and $REDACTED$ z'


def test_executable_secrets_are_masked(tmp_path: pathlib.Path) -> None:
    path = _write_executable(
        tmp_path, 'secrets.sh',
        '#!/bin/sh\nprintf \'version: 1\\nsecrets:\\n  - exec-secret-value\\n\'\n',
    )

    load_secret_input_files([path])

    assert mask_secrets('a exec-secret-value z') == 'a $REDACTED$ z'


def test_empty_secrets_list_is_accepted(tmp_path: pathlib.Path) -> None:
    path = _write(tmp_path, 'secrets.yml', 'version: 1\nsecrets: []\n')

    # nothing to register, but the file is valid and must not raise
    load_secret_input_files([path])


def test_not_a_mapping(tmp_path: pathlib.Path) -> None:
    path = _write(tmp_path, 'secrets.yml', '- abcd\n- efgh\n')
    with pytest.raises(AnsibleError, match='must contain a mapping, not a list'):
        load_secret_input_files([path])


@pytest.mark.parametrize('version', ['2', 'true', '"1"'])
def test_unsupported_version(tmp_path: pathlib.Path, version: str) -> None:
    path = _write(tmp_path, 'secrets.yml', f'version: {version}\nsecrets: [abcd]\n')
    with pytest.raises(AnsibleError, match='unsupported version'):
        load_secret_input_files([path])


def test_missing_version(tmp_path: pathlib.Path) -> None:
    path = _write(tmp_path, 'secrets.yml', 'secrets: [abcd]\n')
    with pytest.raises(AnsibleError, match='unsupported version'):
        load_secret_input_files([path])


def test_secrets_not_a_list(tmp_path: pathlib.Path) -> None:
    path = _write(tmp_path, 'secrets.yml', 'version: 1\nsecrets: notalist\n')
    with pytest.raises(AnsibleError, match="must contain a 'secrets' list"):
        load_secret_input_files([path])


def test_secrets_missing(tmp_path: pathlib.Path) -> None:
    path = _write(tmp_path, 'secrets.yml', 'version: 1\n')
    with pytest.raises(AnsibleError, match="must contain a 'secrets' list"):
        load_secret_input_files([path])


@pytest.mark.parametrize('entry', ['12345', 'true', '1.5'])
def test_non_string_secret_not_cast(tmp_path: pathlib.Path, entry: str) -> None:
    path = _write(tmp_path, 'secrets.yml', f'version: 1\nsecrets:\n  - abcd\n  - {entry}\n')
    # raising before registration proves the value is neither cast nor registered
    with pytest.raises(AnsibleError, match='must be a string'):
        load_secret_input_files([path])


def test_executable_non_zero_exit(tmp_path: pathlib.Path) -> None:
    path = _write_executable(tmp_path, 'secrets.sh', '#!/bin/sh\nexit 3\n')
    with pytest.raises(AnsibleError, match='returned non-zero exit status 3'):
        load_secret_input_files([path])
