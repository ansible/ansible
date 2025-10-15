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


SCRIPTS_DIR = pathlib.Path(__file__).parent.resolve()
DEPS_DIR = SCRIPTS_DIR / 'dependencies'


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


def run(
    *args: str | pathlib.Path,
    dry_run: bool = False,
) -> None:
    """
    Log and run given command.

    The command is not actually executed if ``dry_run`` is truthy.
    """
    cmd = [str(arg) for arg in args]

    dry_prefix = '[would run] ' if dry_run else ''
    print(f'==> {dry_prefix}{shlex.join(cmd)}', flush=True)

    if not dry_run:
        subprocess.run(cmd, check=True)


def install_codecov(dest: pathlib.Path, dry_run: bool = False) -> pathlib.Path:
    """Populate a transitively pinned venv with ``codecov-cli``."""
    requirement_file = DEPS_DIR / 'codecov.in'
    constraint_file = requirement_file.with_suffix('.txt')

    venv_dir = dest / 'venv'
    python_bin = venv_dir / 'bin' / 'python'
    codecov_bin = venv_dir / 'bin' / 'codecovcli'

    venv.create(venv_dir, with_pip=True)

    run(
        python_bin,
        '-m',
        'pip',
        'install',
        f'--constraint={constraint_file!s}',
        f'--requirement={requirement_file!s}',
        '--disable-pip-version-check',
        dry_run=dry_run,
    )

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


def report_upload_completion(
    codecov_bin: pathlib.Path,
    config_file: pathlib.Path,
    dry_run: bool = False,
) -> None:
    """Notify Codecov backend that all reports we wanted are in."""
    cmd = [
        codecov_bin,
        '--disable-telem',
        f'--codecov-yml-path={config_file}',
        'send-notifications',
    ]

    run(*cmd, dry_run=dry_run)


def main() -> None:
    args = parse_args()

    with tempfile.TemporaryDirectory(prefix='codecov-') as tmpdir:
        config_file = pathlib.Path(tmpdir) / 'config.yml'
        # Refs:
        # * https://docs.codecov.com/docs/codecovyml-reference#codecovnotifymanual_trigger
        # * https://docs.codecov.com/docs/notifications#preventing-notifications-until-youre-ready-to-send-notifications
        config_file.write_text('codecov:\n  notify:\n    manual_trigger: true')

        codecov_bin = install_codecov(
            pathlib.Path(tmpdir),
            dry_run=args.dry_run,
        )
        files = process_files(args.path)
        upload_files(codecov_bin, config_file, files, args.dry_run)
        # Ref: https://docs.codecov.com/docs/cli-options#send-notifications
        report_upload_completion(codecov_bin, config_file, args.dry_run)


if __name__ == '__main__':
    main()
