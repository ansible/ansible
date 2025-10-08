"""Verify the contents of the built sdist and wheel."""

from __future__ import annotations

import contextlib
import fnmatch
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import typing as t
import zipfile

from ansible.release import __version__

fuzzy_match_basenames: set[str] = {'COPYING'}
"""Account for PEP639 differences in the placement of some files."""


def collect_sdist_files(complete_file_list: list[str]) -> list[str]:
    """Return a list of files which should be present in the sdist."""
    ignore_patterns = (
        '.azure-pipelines/*',
        '.cherry_picker.toml',
        '.git*',
        '.mailmap',
        'bin/*',
        'changelogs/README.md',
        'changelogs/config.yaml',
        'changelogs/fragments/*',
        'hacking/*',
    )

    sdist_files = [path for path in complete_file_list if not any(fnmatch.fnmatch(path, ignore) for ignore in ignore_patterns)]

    egg_info = (
        'PKG-INFO',
        'SOURCES.txt',
        'dependency_links.txt',
        'entry_points.txt',
        'requires.txt',
        'top_level.txt',
    )

    sdist_files.append('PKG-INFO')
    sdist_files.append('setup.cfg')
    sdist_files.extend(f'ansible_core.egg-info/{name}' for name in egg_info)

    return sdist_files


def collect_wheel_files(complete_file_list: list[str]) -> list[str]:
    """Return a list of files which should be present in the wheel."""
    wheel_files = []
    license_files = []

    for path in complete_file_list:
        if path.startswith('licenses/'):
            license_files.append(os.path.relpath(path, 'licenses'))
            fuzzy_match_basenames.add(os.path.basename(path))

        if path.startswith('lib/ansible/'):
            prefix = 'lib'
        elif path.startswith('test/lib/ansible_test/'):
            prefix = 'test/lib'
        else:
            continue

        wheel_files.append(os.path.relpath(path, prefix))

    dist_info = [
        'COPYING',
        'METADATA',
        'RECORD',
        'WHEEL',
        'entry_points.txt',
        'top_level.txt',
    ] + license_files

    wheel_files.extend(f'ansible_core-{__version__}.dist-info/{name}' for name in dist_info)

    return wheel_files


@contextlib.contextmanager
def clean_repository(complete_file_list: list[str]) -> t.Generator[str, None, None]:
    """Copy the files to a temporary directory and yield the path."""
    directories = sorted(set(os.path.dirname(path) for path in complete_file_list))
    directories.remove('')

    with tempfile.TemporaryDirectory() as temp_dir:
        for directory in directories:
            os.makedirs(os.path.join(temp_dir, directory))

        for path in complete_file_list:
            shutil.copy2(path, os.path.join(temp_dir, path), follow_symlinks=False)

        yield temp_dir


def build(source_dir: str, tmp_dir: str) -> tuple[pathlib.Path, pathlib.Path]:
    """Create a sdist and wheel."""
    create = subprocess.run(  # pylint: disable=subprocess-run-check
        [sys.executable, '-m', 'build', '--outdir', tmp_dir],
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        cwd=source_dir,
    )

    if create.returncode != 0:
        raise RuntimeError(f'build failed:\n{create.stderr}\n{create.stdout}')

    tmp_dir_files = list(pathlib.Path(tmp_dir).iterdir())

    if len(tmp_dir_files) != 2:
        raise RuntimeError(f'build resulted in {len(tmp_dir_files)} items instead of 2')

    sdist_path = [path for path in tmp_dir_files if path.suffix == '.gz'][0]
    wheel_path = [path for path in tmp_dir_files if path.suffix == '.whl'][0]

    return sdist_path, wheel_path


def list_sdist(path: pathlib.Path) -> list[str]:
    """Return a list of the files in the sdist."""
    item: tarfile.TarInfo

    with tarfile.open(path) as sdist:
        paths = ['/'.join(pathlib.Path(item.path).parts[1:]) for item in sdist.getmembers() if not item.isdir()]

    return paths


def list_wheel(path: pathlib.Path) -> list[str]:
    """Return a list of the files in the wheel."""
    with zipfile.ZipFile(path) as wheel:
        paths = [item.filename for item in wheel.filelist if not item.is_dir()]

    return paths


def filter_fuzzy_matches(missing: set[str], extra: set[str]) -> None:
    """
    Removes entries from `missing` and `extra` that share a common basename that also appears in `fuzzy_match_basenames`.
    Accounts for variable placement of non-runtime files by different versions of setuptools.
    """
    if not (missing or extra):
        return

    # calculate a set of basenames that appear in both missing and extra that are also marked as possibly needing fuzzy matching
    corresponding_fuzzy_basenames = {os.path.basename(p) for p in missing}.intersection(os.path.basename(p) for p in extra).intersection(fuzzy_match_basenames)

    # filter successfully fuzzy-matched entries from missing and extra
    missing.difference_update({p for p in missing if os.path.basename(p) in corresponding_fuzzy_basenames})
    extra.difference_update({p for p in extra if os.path.basename(p) in corresponding_fuzzy_basenames})


def check_files(source: str, expected: list[str], actual: list[str]) -> list[str]:
    """Verify the expected files exist and no extra files exist."""
    missing = set(expected) - set(actual)
    extra = set(actual) - set(expected)

    filter_fuzzy_matches(missing, extra)

    errors = [f'{path}: missing from {source}' for path in sorted(missing)] + [f'{path}: unexpected in {source}' for path in sorted(extra)]

    return errors


def main() -> None:
    """Main program entry point."""
    complete_file_list = sys.argv[1:] or sys.stdin.read().splitlines()

    python_version = '.'.join(map(str, sys.version_info[:2]))
    python_min = os.environ['ANSIBLE_TEST_MIN_PYTHON']
    python_max = os.environ['ANSIBLE_TEST_MAX_PYTHON']

    if python_version == python_min:
        use_upper_setuptools_version = False
    elif python_version == python_max:
        use_upper_setuptools_version = True
    else:
        raise RuntimeError(f'Python version {python_version} is neither the minimum {python_min} or the maximum {python_max}.')

    errors = check_build(complete_file_list, use_upper_setuptools_version)

    for error in errors:
        print(error)


def set_setuptools_version(repo_dir: str, use_upper_version: bool) -> str:
    pyproject_toml = pathlib.Path(repo_dir) / 'pyproject.toml'

    current = pyproject_toml.read_text()
    pattern = re.compile(r'^(?P<begin>requires = \["setuptools >= )(?P<lower>[^,]+)(?P<middle>, <= )(?P<upper>[^"]+)(?P<end>".*)$', re.MULTILINE)
    match = pattern.search(current)

    if not match:
        raise RuntimeError(f"Unable to find the 'requires' entry in: {pyproject_toml}")

    lower_version = match.group('lower')
    upper_version = match.group('upper')

    requested_version = upper_version if use_upper_version else lower_version

    updated = pattern.sub(fr'\g<begin>{requested_version}\g<middle>{requested_version}\g<end>', current)

    if current == updated:
        raise RuntimeError("Failed to set the setuptools version.")

    pyproject_toml.write_text(updated)

    return requested_version


def check_build(complete_file_list: list[str], use_upper_setuptools_version: bool) -> list[str]:
    errors: list[str] = []
    complete_file_list = list(complete_file_list)  # avoid mutation of input

    # Limit visible files to those reported by ansible-test.
    # This avoids including files which are not committed to git.
    with clean_repository(complete_file_list) as clean_repo_dir:
        setuptools_version = set_setuptools_version(clean_repo_dir, use_upper_setuptools_version)

        if __version__.endswith('.dev0'):
            # Make sure a changelog exists for this version when testing from devel.
            # When testing from a stable branch the changelog will already exist.
            major_minor_version = '.'.join(__version__.split('.')[:2])
            changelog_path = f'changelogs/CHANGELOG-v{major_minor_version}.rst'
            pathlib.Path(clean_repo_dir, changelog_path).touch()
            complete_file_list.append(changelog_path)

        expected_sdist_files = collect_sdist_files(complete_file_list)
        expected_wheel_files = collect_wheel_files(complete_file_list)

        with tempfile.TemporaryDirectory() as tmp_dir:
            sdist_path, wheel_path = build(clean_repo_dir, tmp_dir)

            actual_sdist_files = list_sdist(sdist_path)
            actual_wheel_files = list_wheel(wheel_path)

            errors.extend(check_files('sdist', expected_sdist_files, actual_sdist_files))
            errors.extend(check_files('wheel', expected_wheel_files, actual_wheel_files))

    errors = [f'{msg} (setuptools=={setuptools_version})' for msg in errors]

    return errors


if __name__ == '__main__':
    main()
