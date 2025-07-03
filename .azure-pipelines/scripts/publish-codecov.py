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
import shlex
import subprocess
import tempfile
import typing as t
import venv


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


def run(*args: str | pathlib.Path) -> None:
    cmd = [str(arg) for arg in args]
    print(f'==> {shlex.join(cmd)}', flush=True)
    subprocess.run(cmd, check=True)


def install_codecov(dest: pathlib.Path) -> pathlib.Path:
    package = 'codecov-cli'
    version = '11.0.3'

    venv_dir = dest / 'venv'
    python_bin = venv_dir / 'bin' / 'python'
    codecov_bin = venv_dir / 'bin' / 'codecovcli'

    venv.create(venv_dir, with_pip=True)

    run(python_bin, '-m', 'pip', 'install', f'{package}=={version}', '--disable-pip-version-check')

    return codecov_bin


def process_files(directory: pathlib.Path) -> t.Tuple[CoverageFile, ...]:
    processed = []
    for file in directory.joinpath('reports').glob('coverage*.xml'):
        name = file.stem.replace('coverage=', '')

        # Get flags from name
        flags = name.replace('-powershell', '').split('=')  # Drop '-powershell' suffix
        flags = [flag if not flag.startswith('stub') else flag.split('-')[0] for flag in flags]  # Remove "-01" from stub files

        processed.append(CoverageFile(name, file, flags))

    return tuple(processed)


def upload_files(codecov_bin: pathlib.Path, config_file: pathlib.Path, files: t.Tuple[CoverageFile, ...], dry_run: bool = False) -> None:
    for file in files:
        cmd = [
            codecov_bin,
            '--disable-telem',
            '--codecov-yml-path',
            config_file,
            'upload-process',
            '--disable-search',
            '--disable-file-fixes',
            '--plugin',
            'noop',
            '--name',
            file.name,
            '--file',
            file.path,
        ]

        for flag in file.flags:
            cmd.extend(['--flag', flag])

        if dry_run:
            cmd.append('--dry-run')

        run(*cmd)


def main() -> None:
    args = parse_args()

    with tempfile.TemporaryDirectory(prefix='codecov-') as tmpdir:
        config_file = pathlib.Path(tmpdir) / 'config.yml'
        config_file.write_text('')

        codecov_bin = install_codecov(pathlib.Path(tmpdir))
        files = process_files(args.path)
        upload_files(codecov_bin, config_file, files, args.dry_run)


if __name__ == '__main__':
    main()
