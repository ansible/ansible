#!/usr/bin/env python
# Upload code coverage reports to codecov.io.
# Multiple coverage files from multiple languages are accepted and aggregated after upload.
# Python coverage, as well as PowerShell and Python stubs can all be uploaded.

import argparse
import dataclasses
import os
import shutil
import subprocess
import urllib.request

import typing as t

from pathlib import Path
from tempfile import NamedTemporaryFile


@dataclasses.dataclass(frozen=True)
class CoverageFile:
    name: str
    path: Path
    flags: t.List[str]


@dataclasses.dataclass(frozen=True)
class Args:
    dry_run: bool
    path: Path


def parse_args() -> Args:
    parser = argparse.ArgumentParser()
    parser.add_argument('-n', '--dry-run', action='store_true')
    parser.add_argument('path', type=Path)

    args = parser.parse_args()

    # Store arguments in a typed dataclass
    fields = dataclasses.fields(Args)
    kwargs = {field.name: getattr(args, field.name) for field in fields}

    return Args(**kwargs)


def process_files(directory: Path) -> t.Tuple[CoverageFile, ...]:
    processed = []
    for file in directory.joinpath('reports').glob('coverage*.xml'):
        name = file.stem.replace('coverage=', '')

        # Get flags from name
        flags = name.replace('-powershell', '').split('=')  # Drop '-powershell' suffix
        flags = [flag.split('-')[0] if flag.startswith('stub') else flag for flag in flags]  # Remove "-01" from stub files

        processed.append(CoverageFile(name, file, flags))

    return tuple(processed)


def upload_files(codecov_bin: str, files: t.Tuple[CoverageFile], dry_run: bool = False) -> None:
    for file in files:
        cmd = [
            codecov_bin,
            '--name', file.name,
            '--file', str(file.path),
        ]
        for flag in file.flags:
            cmd.extend(['--flags', flag])

        if dry_run:
            print(f'DRY-RUN: Would run command: {cmd}')
            continue

        subprocess.run(cmd, check=True)


def download_file(url: str, dest: t.IO[bytes], flags: t.Optional[int] = None, dry_run: bool = False) -> None:
    if dry_run:
        print(f'DRY-RUN: Would download {url} to {dest} and set mode to {flags:o}')
        return

    with urllib.request.urlopen(url) as resp:
        # Read data in chunks rather than all at once
        shutil.copyfileobj(resp, dest, 64 * 1024)

    if flags is not None:
        os.chmod(dest.name, flags)


def main():
    args = parse_args()
    url = 'https://ansible-ci-files.s3.amazonaws.com/codecov/linux/codecov'
    with NamedTemporaryFile(prefix='codecov-') as codecov_bin:
        download_file(url, codecov_bin, 0o755, args.dry_run)

        files = process_files(args.path)
        upload_files(codecov_bin.name, files, args.dry_run)


if __name__ == '__main__':
    main()
