#!/usr/bin/env python
"""
Upload code coverage reports to codecov.io.
Multiple coverage files from multiple languages are accepted and aggregated after upload.
Python coverage, as well as PowerShell and Python stubs can all be uploaded.
"""
from __future__ import annotations

import argparse
import dataclasses
import pathlib
import shutil
import subprocess
import tempfile
import typing as t
import urllib.request


@dataclasses.dataclass(frozen=True)
class CoverageFile:
    name: str
    path: pathlib.Path
    flags: t.List[str]


@dataclasses.dataclass(frozen=True)
class Args:
    dry_run: bool
    path: pathlib.Path


def parse_args() -> Args:
    parser = argparse.ArgumentParser()
    parser.add_argument('-n', '--dry-run', action='store_true')
    parser.add_argument('path', type=pathlib.Path)

    args = parser.parse_args()

    # Store arguments in a typed dataclass
    fields = dataclasses.fields(Args)
    kwargs = {field.name: getattr(args, field.name) for field in fields}

    return Args(**kwargs)


def process_files(directory: pathlib.Path) -> t.Tuple[CoverageFile, ...]:
    processed = []
    for file in directory.joinpath('reports').glob('coverage*.xml'):
        name = file.stem.replace('coverage=', '')

        # Get flags from name
        flags = name.replace('-powershell', '').split('=')  # Drop '-powershell' suffix
        flags = [flag if not flag.startswith('stub') else flag.split('-')[0] for flag in flags]  # Remove "-01" from stub files

        processed.append(CoverageFile(name, file, flags))

    return tuple(processed)


def upload_files(codecov_bin: pathlib.Path, files: t.Tuple[CoverageFile, ...], dry_run: bool = False) -> None:
    for file in files:
        cmd = [
            str(codecov_bin),
            '--name', file.name,
            '--file', str(file.path),
        ]
        for flag in file.flags:
            cmd.extend(['--flags', flag])

        if dry_run:
            print(f'DRY-RUN: Would run command: {cmd}')
            continue

        subprocess.run(cmd, check=True)


def download_file(url: str, dest: pathlib.Path, flags: int, dry_run: bool = False) -> None:
    if dry_run:
        print(f'DRY-RUN: Would download {url} to {dest} and set mode to {flags:o}')
        return

    with urllib.request.urlopen(url) as resp:
        with dest.open('w+b') as f:
            # Read data in chunks rather than all at once
            shutil.copyfileobj(resp, f, 64 * 1024)

    dest.chmod(flags)


def main():
    args = parse_args()
    url = 'https://ci-files.testing.ansible.com/codecov/linux/codecov'
    with tempfile.TemporaryDirectory(prefix='codecov-') as tmpdir:
        codecov_bin = pathlib.Path(tmpdir) / 'codecov'
        download_file(url, codecov_bin, 0o755, args.dry_run)

        files = process_files(args.path)
        upload_files(codecov_bin, files, args.dry_run)


if __name__ == '__main__':
    main()
