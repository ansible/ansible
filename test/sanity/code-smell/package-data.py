#!/usr/bin/env python
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import contextlib
import fnmatch
import glob
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile


def assemble_files_to_ship(complete_file_list):
    """
    This looks for all files which should be shipped in the sdist
    """
    # All files which are in the repository except these:
    ignore_patterns = (
        # Developer-only tools
        '.azure-pipelines/*',
        '.github/*',
        '.github/*/*',
        'changelogs/fragments/*',
        'hacking/aws_config/*',
        'hacking/aws_config/*/*',
        'hacking/tests/*',
        'hacking/ticket_stubs/*',
        'test/legacy/*',
        'test/legacy/*/*',
        'test/legacy/*/*/*',
        'test/legacy/*/*/*/*',
        'test/legacy/*/*/*/*/*',
        'test/legacy/*/*/*/*/*/*',
        'test/sanity/code-smell/botmeta.*',
        'test/utils/*',
        'test/utils/*/*',
        'test/utils/*/*/*',
        '.git*',
        # Consciously left out
        'examples/playbooks/*',
        # Possibly should be included
        'contrib/vault/*',
    )
    ignore_files = frozenset((
        # Developer-only tools
        'changelogs/config.yaml',
        'changelogs/.changes.yaml',
        'hacking/README.md',
        'hacking/ansible-profile',
        'hacking/cgroup_perf_recap_graph.py',
        'hacking/create_deprecated_issues.py',
        'hacking/deprecated_issue_template.md',
        'hacking/fix_test_syntax.py',
        'hacking/get_library.py',
        'hacking/metadata-tool.py',
        'hacking/report.py',
        'hacking/return_skeleton_generator.py',
        'hacking/test-module',
        'hacking/test-module.py',
        '.cherry_picker.toml',
        '.mailmap',
        # Possibly should be included
        'examples/scripts/uptime.py',
        'examples/DOCUMENTATION.yml',
        'examples/hosts.yaml',
        'examples/hosts.yml',
        'examples/inventory_script_schema.json',
        'examples/plugin_filters.yml',
        'hacking/env-setup',
        'hacking/env-setup.fish',
        'CODING_GUIDELINES.md',
        'MANIFEST',
        'MODULE_GUIDELINES.md',
    ))

    # These files are generated and then intentionally added to the sdist

    # Manpages
    manpages = ['docs/man/man1/ansible.1']
    for dirname, dummy, files in os.walk('bin'):
        for filename in files:
            path = os.path.join(dirname, filename)
            if os.path.islink(path):
                if os.readlink(path) == 'ansible':
                    manpages.append('docs/man/man1/%s.1' % filename)

    # Misc
    misc_generated_files = [
        'SYMLINK_CACHE.json',
        'PKG-INFO',
    ]

    shipped_files = manpages + misc_generated_files

    for path in complete_file_list:
        if path not in ignore_files:
            for ignore in ignore_patterns:
                if fnmatch.fnmatch(path, ignore):
                    break
            else:
                shipped_files.append(path)

    return shipped_files


def assemble_files_to_install(complete_file_list):
    """
    This looks for all of the files which should show up in an installation of ansible
    """
    ignore_patterns = tuple()

    pkg_data_files = []
    for path in complete_file_list:

        if path.startswith("lib/ansible"):
            prefix = 'lib'
        elif path.startswith("test/lib/ansible_test"):
            prefix = 'test/lib'
        else:
            continue

        for ignore in ignore_patterns:
            if fnmatch.fnmatch(path, ignore):
                break
        else:
            pkg_data_files.append(os.path.relpath(path, prefix))

    return pkg_data_files


@contextlib.contextmanager
def clean_repository(file_list):
    """Copy the repository to clean it of artifacts"""
    # Create a tempdir that will be the clean repo
    with tempfile.TemporaryDirectory() as repo_root:
        directories = set((repo_root + os.path.sep,))

        for filename in file_list:
            # Determine if we need to create the directory
            directory = os.path.dirname(filename)
            dest_dir = os.path.join(repo_root, directory)
            if dest_dir not in directories:
                os.makedirs(dest_dir)

                # Keep track of all the directories that now exist
                path_components = directory.split(os.path.sep)
                path = repo_root
                for component in path_components:
                    path = os.path.join(path, component)
                    if path not in directories:
                        directories.add(path)

            # Copy the file
            shutil.copy2(filename, dest_dir, follow_symlinks=False)

        yield repo_root


def create_sdist(tmp_dir):
    """Create an sdist in the repository"""
    create = subprocess.Popen(
        ['make', 'snapshot', 'SDIST_DIR=%s' % tmp_dir],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
    )

    stderr = create.communicate()[1]

    if create.returncode != 0:
        raise Exception('make snapshot failed:\n%s' % stderr)

    # Determine path to sdist
    tmp_dir_files = os.listdir(tmp_dir)

    if not tmp_dir_files:
        raise Exception('sdist was not created in the temp dir')
    elif len(tmp_dir_files) > 1:
        raise Exception('Unexpected extra files in the temp dir')

    return os.path.join(tmp_dir, tmp_dir_files[0])


def extract_sdist(sdist_path, tmp_dir):
    """Untar the sdist"""
    # Untar the sdist from the tmp_dir
    with tarfile.open(os.path.join(tmp_dir, sdist_path), 'r|*') as sdist:
        sdist.extractall(path=tmp_dir)

    # Determine the sdist directory name
    sdist_filename = os.path.basename(sdist_path)
    tmp_dir_files = os.listdir(tmp_dir)
    try:
        tmp_dir_files.remove(sdist_filename)
    except ValueError:
        # Unexpected could not find original sdist in temp dir
        raise

    if len(tmp_dir_files) > 1:
        raise Exception('Unexpected extra files in the temp dir')
    elif len(tmp_dir_files) < 1:
        raise Exception('sdist extraction did not occur i nthe temp dir')

    return os.path.join(tmp_dir, tmp_dir_files[0])


def install_sdist(tmp_dir, sdist_dir):
    """Install the extracted sdist into the temporary directory"""
    install = subprocess.Popen(
        ['python', 'setup.py', 'install', '--root=%s' % tmp_dir],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
        cwd=os.path.join(tmp_dir, sdist_dir),
    )

    stdout, stderr = install.communicate()

    if install.returncode != 0:
        raise Exception('sdist install failed:\n%s' % stderr)

    # Determine the prefix for the installed files
    match = re.search('^creating (%s/.*?/(?:site|dist)-packages)/ansible$' %
                      tmp_dir, stdout, flags=re.M)
    return match.group(1)


def check_sdist_contains_expected(sdist_dir, to_ship_files):
    """Check that the files we expect to ship are present in the sdist"""
    results = []
    for filename in to_ship_files:
        path = os.path.join(sdist_dir, filename)
        if not os.path.exists(path):
            results.append('%s: File was not added to sdist' % filename)

    # Also changelog
    changelog_files = glob.glob(os.path.join(sdist_dir, 'changelogs/CHANGELOG-v2.[0-9]*.rst'))
    if not changelog_files:
        results.append('changelogs/CHANGELOG-v2.*.rst: Changelog file was not added to the sdist')
    elif len(changelog_files) > 1:
        results.append('changelogs/CHANGELOG-v2.*.rst: Too many changelog files: %s'
                       % changelog_files)

    return results


def check_sdist_files_are_wanted(sdist_dir, to_ship_files):
    """Check that all files in the sdist are desired"""
    results = []
    for dirname, dummy, files in os.walk(sdist_dir):
        dirname = os.path.relpath(dirname, start=sdist_dir)
        if dirname == '.':
            dirname = ''

        for filename in files:
            path = os.path.join(dirname, filename)
            if path not in to_ship_files:
                if fnmatch.fnmatch(path, 'changelogs/CHANGELOG-v2.[0-9]*.rst'):
                    # changelog files are expected
                    continue

                # FIXME: ansible-test doesn't pass the paths of symlinks to us so we aren't
                # checking those
                if not os.path.islink(os.path.join(sdist_dir, path)):
                    results.append('%s: File in sdist was not in the repository' % path)

    return results


def check_installed_contains_expected(install_dir, to_install_files):
    """Check that all the files we expect to be installed are"""
    results = []
    for filename in to_install_files:
        path = os.path.join(install_dir, filename)
        if not os.path.exists(path):
            results.append('%s: File not installed' % os.path.join('lib', filename))

    return results


EGG_RE = re.compile('ansible[^/]+\\.egg-info/(PKG-INFO|SOURCES.txt|'
                    'dependency_links.txt|not-zip-safe|requires.txt|top_level.txt)$')


def check_installed_files_are_wanted(install_dir, to_install_files):
    """Check that all installed files were desired"""
    results = []

    for dirname, dummy, files in os.walk(install_dir):
        dirname = os.path.relpath(dirname, start=install_dir)
        if dirname == '.':
            dirname = ''

        for filename in files:
            # If this is a byte code cache, look for the python file's name
            directory = dirname
            if filename.endswith('.pyc') or filename.endswith('.pyo'):
                # Remove the trailing "o" or c"
                filename = filename[:-1]

                if directory.endswith('%s__pycache__' % os.path.sep):
                    # Python3 byte code cache, look for the basename of
                    # __pycache__/__init__.cpython-36.py
                    segments = filename.rsplit('.', 2)
                    if len(segments) >= 3:
                        filename = '.'.join((segments[0], segments[2]))
                        directory = os.path.dirname(directory)

            path = os.path.join(directory, filename)

            # Test that the file was listed for installation
            if path not in to_install_files:
                # FIXME: ansible-test doesn't pass the paths of symlinks to us so we
                # aren't checking those
                if not os.path.islink(os.path.join(install_dir, path)):
                    if not EGG_RE.match(path):
                        results.append('%s: File was installed but was not supposed to be' % path)

    return results


def _find_symlinks():
    symlink_list = []
    for dirname, directories, filenames in os.walk('.'):
        for filename in filenames:
            path = os.path.join(dirname, filename)
            # Strip off "./" from the front
            path = path[2:]
            if os.path.islink(path):
                symlink_list.append(path)

    return symlink_list


def main():
    """All of the files in the repository"""
    complete_file_list = []
    for path in sys.argv[1:] or sys.stdin.read().splitlines():
        complete_file_list.append(path)

    # ansible-test isn't currently passing symlinks to us so construct those ourselves for now
    for filename in _find_symlinks():
        if filename not in complete_file_list:
            # For some reason ansible-test is passing us lib/ansible/module_utils/ansible_release.py
            # which is a symlink even though it doesn't pass any others
            complete_file_list.append(filename)

    # We may run this after docs sanity tests so get a clean repository to run in
    with clean_repository(complete_file_list) as clean_repo_dir:
        os.chdir(clean_repo_dir)

        to_ship_files = assemble_files_to_ship(complete_file_list)
        to_install_files = assemble_files_to_install(complete_file_list)

        results = []
        with tempfile.TemporaryDirectory() as tmp_dir:
            sdist_path = create_sdist(tmp_dir)
            sdist_dir = extract_sdist(sdist_path, tmp_dir)

            # Check that the files that are supposed to be in the sdist are there
            results.extend(check_sdist_contains_expected(sdist_dir, to_ship_files))

            # Check that the files that are in the sdist are in the repository
            results.extend(check_sdist_files_are_wanted(sdist_dir, to_ship_files))

            # install the sdist
            install_dir = install_sdist(tmp_dir, sdist_dir)

            # Check that the files that are supposed to be installed are there
            results.extend(check_installed_contains_expected(install_dir, to_install_files))

            # Check that the files that are installed are supposed to be installed
            results.extend(check_installed_files_are_wanted(install_dir, to_install_files))

        for message in results:
            print(message)


if __name__ == '__main__':
    main()
