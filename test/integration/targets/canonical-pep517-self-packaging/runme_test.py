"""Smoke tests for the in-tree PEP 517 backend."""

from __future__ import annotations

from filecmp import dircmp
from os import chdir, environ, PathLike
from pathlib import Path
from shutil import rmtree
from subprocess import check_call, check_output, PIPE
from sys import executable as current_interpreter, version_info
from tarfile import TarFile
import typing as t

try:
    from contextlib import chdir as _chdir_cm
except ImportError:
    from contextlib import contextmanager as _contextmanager

    @_contextmanager
    def _chdir_cm(path: PathLike) -> t.Iterator[None]:
        original_wd = Path.cwd()
        chdir(path)
        try:
            yield
        finally:
            chdir(original_wd)

import pytest


DIST_NAME = 'ansible_core'
DIST_FILENAME_BASE = 'ansible-core'
OUTPUT_DIR = Path(environ['OUTPUT_DIR']).resolve().absolute()
SRC_ROOT_DIR = OUTPUT_DIR.parents[3]
GENERATED_MANPAGES_SUBDIR = SRC_ROOT_DIR / 'docs' / 'man' / 'man1'
LOWEST_SUPPORTED_BUILD_DEPS_FILE = (
    Path(__file__).parent / 'minimum-build-constraints.txt'
).resolve().absolute()
MODERNISH_BUILD_DEPS_FILE = (
    Path(__file__).parent / 'modernish-build-constraints.txt'
).resolve().absolute()
RELEASE_MODULE = SRC_ROOT_DIR / 'lib' / 'ansible' / 'release.py'
VERSION_LINE_PREFIX = "__version__ = '"
PKG_DIST_VERSION = next(
    line[len(VERSION_LINE_PREFIX):-1]
    for line in RELEASE_MODULE.read_text().splitlines()
    if line.startswith(VERSION_LINE_PREFIX)
)
EXPECTED_SDIST_NAME_BASE = f'{DIST_FILENAME_BASE}-{PKG_DIST_VERSION}'
EXPECTED_SDIST_NAME = f'{EXPECTED_SDIST_NAME_BASE}.tar.gz'
EXPECTED_WHEEL_NAME = f'{DIST_NAME}-{PKG_DIST_VERSION}-py3-none-any.whl'

IS_PYTHON310_PLUS = version_info[:2] >= (3, 10)


def wipe_generated_manpages() -> None:
    """Ensure man1 pages aren't present in the source checkout."""
    # Cleaning up the gitignored manpages...
    if not GENERATED_MANPAGES_SUBDIR.exists():
        return

    rmtree(GENERATED_MANPAGES_SUBDIR)
    # Removed the generated manpages...


def contains_man1_pages(sdist_tarball: Path) -> Path:
    """Check if the man1 pages are present in given tarball."""
    with sdist_tarball.open(mode='rb') as tarball_fd:
        with TarFile.gzopen(fileobj=tarball_fd, name=None) as tarball:
            try:
                tarball.getmember(
                    name=f'{EXPECTED_SDIST_NAME_BASE}/docs/man/man1',
                )
            except KeyError:
                return False

    return True


def unpack_sdist(sdist_tarball: Path, target_directory: Path) -> Path:
    """Unarchive given tarball.

    :returns: Path of the package source checkout.
    """
    with sdist_tarball.open(mode='rb') as tarball_fd:
        with TarFile.gzopen(fileobj=tarball_fd, name=None) as tarball:
            tarball.extractall(path=target_directory)
    return target_directory / EXPECTED_SDIST_NAME_BASE


def assert_dirs_equal(*dir_paths: t.List[Path]) -> None:
    dir_comparison = dircmp(*dir_paths)
    assert not dir_comparison.left_only
    assert not dir_comparison.right_only
    assert not dir_comparison.diff_files
    assert not dir_comparison.funny_files


def normalize_unpacked_rebuilt_sdist(sdist_path: Path) -> None:
    top_pkg_info_path = sdist_path / 'PKG-INFO'
    nested_pkg_info_path = (
        sdist_path / 'lib' / f'{DIST_NAME}.egg-info' / 'PKG-INFO'
    )
    entry_points_path = nested_pkg_info_path.parent / 'entry_points.txt'

    # setuptools v39 write out two trailing empty lines and an unknown platform
    # while the recent don't
    top_pkg_info_path.write_text(
        top_pkg_info_path.read_text().replace(
            'Classifier: Development Status :: 5',
            'Platform: UNKNOWN\nClassifier: Development Status :: 5',
        ) + '\n\n'
    )
    nested_pkg_info_path.write_text(
        nested_pkg_info_path.read_text().replace(
            'Classifier: Development Status :: 5',
            'Platform: UNKNOWN\nClassifier: Development Status :: 5',
        ) + '\n\n'
    )

    # setuptools v39 write out one trailing empty line while the recent don't
    entry_points_path.write_text(entry_points_path.read_text() + '\n')


@pytest.fixture
def venv_python_exe(tmp_path: Path) -> t.Iterator[Path]:
    venv_path = tmp_path / 'pytest-managed-venv'
    mkvenv_cmd = (
        current_interpreter, '-m', 'venv', str(venv_path),
    )
    check_call(mkvenv_cmd, env={}, stderr=PIPE, stdout=PIPE)
    yield venv_path / 'bin' / 'python'
    rmtree(venv_path)


def run_with_venv_python(
        python_exe: Path, *cli_args: t.Iterable[str],
        env_vars: t.Dict[str, str] = None,
) -> str:
    if env_vars is None:
        env_vars = {}
    full_cmd = str(python_exe), *cli_args
    return check_output(full_cmd, env=env_vars, stderr=PIPE)


def build_dists(
        python_exe: Path, *cli_args: t.Iterable[str],
        env_vars: t.Dict[str, str],
) -> str:
    return run_with_venv_python(
        python_exe, '-m', 'build',
        *cli_args, env_vars=env_vars,
    )


def pip_install(
        python_exe: Path, *cli_args: t.Iterable[str],
        env_vars: t.Dict[str, str] = None,
) -> str:
    return run_with_venv_python(
        python_exe, '-m', 'pip', 'install',
        *cli_args, env_vars=env_vars,
    )


def test_installing_sdist_build_with_modern_deps_to_old_env(
        venv_python_exe: Path, tmp_path: Path,
) -> None:
    pip_install(venv_python_exe, 'build ~= 0.10.0')
    tmp_dir_sdist_w_modern_tools = tmp_path / 'sdist-w-modern-tools'
    build_dists(
        venv_python_exe, '--sdist',
        f'--outdir={tmp_dir_sdist_w_modern_tools!s}',
        str(SRC_ROOT_DIR),
        env_vars={
            'PIP_CONSTRAINT': str(MODERNISH_BUILD_DEPS_FILE),
            'ANSIBLE_PEP517_BUILD_MANPAGES': '1',
        },
    )
    tmp_path_sdist_w_modern_tools = (
        tmp_dir_sdist_w_modern_tools / EXPECTED_SDIST_NAME
    )

    # Downgrading pip, because v20+ supports in-tree build backends
    pip_install(venv_python_exe, 'pip ~= 19.3.1')

    # Smoke test — installing an sdist with pip that does not support
    # in-tree build backends.
    pip_install(
        venv_python_exe, str(tmp_path_sdist_w_modern_tools), '--no-deps',
    )

    # Downgrading pip, because versions that support PEP 517 don't allow
    # disabling it with `--no-use-pep517` when `build-backend` is set in
    # the `[build-system]` section of `pyproject.toml`, considering this
    # an explicit opt-in.
    if not IS_PYTHON310_PLUS:
        pip_install(venv_python_exe, 'pip == 18.0')

    # Smoke test — installing an sdist with pip that does not support invoking
    # PEP 517 interface at all.
    # In this scenario, pip will run `setup.py install` since `wheel` is not in
    # the environment.
    if IS_PYTHON310_PLUS:
        tmp_dir_unpacked_sdist_root = tmp_path / 'unpacked-sdist'
        tmp_dir_unpacked_sdist_path = tmp_dir_unpacked_sdist_root / EXPECTED_SDIST_NAME_BASE
        with TarFile.gzopen(tmp_path_sdist_w_modern_tools) as sdist_fd:
            sdist_fd.extractall(path=tmp_dir_unpacked_sdist_root)

        pip_install(
            venv_python_exe, 'setuptools',
            env_vars={
                'PIP_CONSTRAINT': str(LOWEST_SUPPORTED_BUILD_DEPS_FILE),
            },
        )
        with _chdir_cm(tmp_dir_unpacked_sdist_path):
            run_with_venv_python(
                venv_python_exe, 'setup.py', 'sdist',
                env_vars={'PATH': environ['PATH']},
            )
    else:
        pip_install(
            venv_python_exe, str(tmp_path_sdist_w_modern_tools), '--no-deps',
            env_vars={
                'PIP_CONSTRAINT': str(LOWEST_SUPPORTED_BUILD_DEPS_FILE),
            },
        )

    # Smoke test — installing an sdist with pip that does not support invoking
    # PEP 517 interface at all.
    # With `wheel` present, pip will run `setup.py bdist_wheel` and then,
    # unpack the result.
    pip_install(venv_python_exe, 'wheel')
    if IS_PYTHON310_PLUS:
        with _chdir_cm(tmp_dir_unpacked_sdist_path):
            run_with_venv_python(
                venv_python_exe, 'setup.py', 'bdist_wheel',
                env_vars={'PATH': environ['PATH']},
            )
    else:
        pip_install(
            venv_python_exe, str(tmp_path_sdist_w_modern_tools), '--no-deps',
        )


def test_dist_rebuilds_with_manpages_premutations(
        venv_python_exe: Path, tmp_path: Path,
) -> None:
    """Test a series of sdist rebuilds under different conditions.

    This check builds sdists right from the Git checkout with and without
    the manpages. It also does this using different versions of the setuptools
    PEP 517 build backend being pinned. Finally, it builds a wheel out of one
    of the rebuilt sdists.
    As intermediate assertions, this test makes simple smoke tests along
    the way.
    """
    pip_install(venv_python_exe, 'build ~= 0.10.0')

    # Test building an sdist without manpages from the Git checkout
    tmp_dir_sdist_without_manpages = tmp_path / 'sdist-without-manpages'
    wipe_generated_manpages()
    build_dists(
        venv_python_exe, '--sdist',
        f'--outdir={tmp_dir_sdist_without_manpages!s}',
        str(SRC_ROOT_DIR),
        env_vars={
            'PIP_CONSTRAINT': str(MODERNISH_BUILD_DEPS_FILE),
        },
    )
    tmp_path_sdist_without_manpages = (
        tmp_dir_sdist_without_manpages / EXPECTED_SDIST_NAME
    )
    assert tmp_path_sdist_without_manpages.exists()
    assert not contains_man1_pages(tmp_path_sdist_without_manpages)
    sdist_without_manpages_path = unpack_sdist(
        tmp_path_sdist_without_manpages,
        tmp_dir_sdist_without_manpages / 'src',
    )

    # Test building an sdist with manpages from the Git checkout
    # and lowest supported build deps
    wipe_generated_manpages()
    tmp_dir_sdist_with_manpages = tmp_path / 'sdist-with-manpages'
    build_dists(
        venv_python_exe, '--sdist',
        f'--outdir={tmp_dir_sdist_with_manpages!s}',
        str(SRC_ROOT_DIR),
        env_vars={
            'PIP_CONSTRAINT': str(LOWEST_SUPPORTED_BUILD_DEPS_FILE),
            'ANSIBLE_PEP517_BUILD_MANPAGES': '1',
        },
    )
    tmp_path_sdist_with_manpages = (
        tmp_dir_sdist_with_manpages / EXPECTED_SDIST_NAME
    )
    assert tmp_path_sdist_with_manpages.exists()
    assert contains_man1_pages(tmp_path_sdist_with_manpages)
    sdist_with_manpages_path = unpack_sdist(
        tmp_path_sdist_with_manpages,
        tmp_dir_sdist_with_manpages / 'src',
    )

    # Test re-building an sdist with manpages from the
    # sdist contents that does not include the manpages
    tmp_dir_rebuilt_sdist = tmp_path / 'rebuilt-sdist'
    build_dists(
        venv_python_exe, '--sdist',
        f'--outdir={tmp_dir_rebuilt_sdist!s}',
        str(sdist_without_manpages_path),
        env_vars={
            'PIP_CONSTRAINT': str(MODERNISH_BUILD_DEPS_FILE),
            'ANSIBLE_PEP517_BUILD_MANPAGES': '1',
        },
    )
    tmp_path_rebuilt_sdist = tmp_dir_rebuilt_sdist / EXPECTED_SDIST_NAME
    # Checking that the expected sdist got created
    # from the previous unpacked sdist...
    assert tmp_path_rebuilt_sdist.exists()
    # NOTE: The following assertion is disabled due to the fact that, when
    # NOTE: building an sdist from the original source checkout, the build
    # NOTE: backend replaces itself with pure setuptools in the resulting
    # NOTE: sdist, and the following rebuilds from that sdist are no longer
    # NOTE: able to process the custom config settings that are implemented in
    # NOTE: the in-tree build backend. It is expected that said
    # NOTE: `pyproject.toml` mutation change will be reverted once all of the
    # NOTE: supported `ansible-core` versions ship wheels, meaning that the
    # NOTE: end-users won't be building the distribution from sdist on install.
    # NOTE: Another case, when it can be reverted is declaring pip below v20
    # NOTE: unsupported — it is the first version to support in-tree build
    # NOTE: backends natively.
    # assert contains_man1_pages(tmp_path_rebuilt_sdist)  # FIXME: See #80255
    rebuilt_sdist_path = unpack_sdist(
        tmp_path_rebuilt_sdist,
        tmp_dir_rebuilt_sdist / 'src',
    )
    assert rebuilt_sdist_path.exists()
    assert rebuilt_sdist_path.is_dir()
    normalize_unpacked_rebuilt_sdist(rebuilt_sdist_path)
    assert_dirs_equal(rebuilt_sdist_path, sdist_with_manpages_path)

    # Test building a wheel from the rebuilt sdist with manpages contents
    # and lowest supported build deps
    tmp_dir_rebuilt_wheel = tmp_path / 'rebuilt-wheel'
    build_dists(
        venv_python_exe, '--wheel',
        f'--outdir={tmp_dir_rebuilt_wheel!s}',
        str(sdist_with_manpages_path),
        env_vars={
            'PIP_CONSTRAINT': str(LOWEST_SUPPORTED_BUILD_DEPS_FILE),
        },
    )
    tmp_path_rebuilt_wheel = tmp_dir_rebuilt_wheel / EXPECTED_WHEEL_NAME
    # Checking that the expected wheel got created...
    assert tmp_path_rebuilt_wheel.exists()


def test_pep660_editable_install_smoke(venv_python_exe: Path) -> None:
    """Smoke-test PEP 660 editable install.

    This verifies that the in-tree build backend wrapper
    does not break any required interfaces.
    """
    pip_install(venv_python_exe, '-e', str(SRC_ROOT_DIR))

    pip_show_cmd = (
        str(venv_python_exe), '-m',
        'pip', 'show', DIST_FILENAME_BASE,
    )
    installed_ansible_meta = check_output(
        pip_show_cmd,
        env={}, stderr=PIPE, text=True,
    ).splitlines()
    assert f'Name: {DIST_FILENAME_BASE}' in installed_ansible_meta
    assert f'Version: {PKG_DIST_VERSION}' in installed_ansible_meta

    pip_runtime_version_cmd = (
        str(venv_python_exe), '-c',
        'from ansible import __version__; print(__version__)',
    )
    runtime_ansible_version = check_output(
        pip_runtime_version_cmd,
        env={}, stderr=PIPE, text=True,
    ).strip()
    assert runtime_ansible_version == PKG_DIST_VERSION
