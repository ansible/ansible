#!/usr/bin/env python
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import fnmatch
import os
import re
import subprocess
import sys
import tarfile
import tempfile


def assemble_files_in_repository():
    """All of the files in the repository"""
    file_list = []
    for path in sys.argv[1:] or sys.stdin.read().splitlines():
        file_list.append(path)
    return file_list


def assemble_files_to_ship(complete_file_list):
    """
    This looks for all files which should be shipped in the sdist
    """
    # All files which are in the repository except these:
    ignore_patterns = (
        # Developer-only tools
        '.github/*',
        '.github/*/*',
        'changelogs/fragments/*',
        'hacking/aws_config/*',
        'hacking/aws_config/*/*',
        'hacking/tests/*',
        'hacking/ticket_stubs/*',
        'test/sanity/code-smell/botmeta.*',
        '.git*',
        # Consciously left out
        'examples/playbooks/*',
        # Possibly should be included
        'contrib/vault/*',
    )
    ignore_files = frozenset((
        # Developer-only tools
        'changelogs/config.yaml',
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
        'shippable.yml',
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
    generated_files = (
        'SYMLINK_CACHE.json',
        'PKG-INFO',
    )
    shipped_files = list(generated_files)

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


def create_sdist(tmp_dir):
    _dummy = subprocess.Popen(
        ['python', 'setup.py', 'sdist', '--dist-dir=%s' % tmp_dir],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
    ).communicate()

    # Determine path to sdist
    tmp_dir_files = os.listdir(tmp_dir)

    if not tmp_dir_files:
        raise Exception('sdist was not created in the temp dir')
    elif len(tmp_dir_files) > 1:
        raise Exception('Unexpected extra files in the temp dir')

    return os.path.join(tmp_dir, tmp_dir_files[0])


def extract_sdist(sdist_path, tmp_dir):
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


def main():
    complete_file_list = assemble_files_in_repository()
    to_ship_files = assemble_files_to_ship(complete_file_list)
    to_install_files = assemble_files_to_install(complete_file_list)

    with tempfile.TemporaryDirectory() as tmp_dir:
        sdist_path = create_sdist(tmp_dir)
        sdist_dir = extract_sdist(sdist_path, tmp_dir)

        # Check that the files that are supposed to be in the sdist are there
        for filename in to_ship_files:
            path = os.path.join(sdist_dir, filename)
            if not os.path.exists(path):
                print('%s: File was not added to sdist' % filename)

        # Check that the files that are in the sdist are in the repository
        for dirname, directories, files in os.walk(sdist_dir):
            dirname = os.path.relpath(dirname, start=sdist_dir)
            if dirname == '.':
                dirname = ''

            for filename in files:
                path = os.path.join(dirname, filename)
                if path not in to_ship_files:
                    # FIXME: ansible-test doesn't pass the paths of symlinks to us so we can't check those
                    if not os.path.islink(os.path.join(sdist_dir, path)):
                        print('%s: File in sdist was not in the repository' % path)

        # python setup.py install from the sdist
        stdout, _dummy = subprocess.Popen(
            ['python', 'setup.py', 'install', '--root=%s' % tmp_dir],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            cwd=os.path.join(tmp_dir, sdist_dir),
        ).communicate()

        # Determine the prefix for the installed files
        match = re.search('^creating (%s/.*?/(?:site|dist)-packages)/ansible$' %
                          tmp_dir, stdout, flags=re.M)
        install_dir = match.group(1)

        # Check that the files that are supposed to be installed are there
        for filename in to_install_files:
            path = os.path.join(install_dir, filename)
            if not os.path.exists(path):
                print('%s: File not installed' % os.path.join('lib', filename))

        # Check that the files that are installed are supposed to be
        EGG_RE = re.compile('ansible[^/]+\\.egg-info/(PKG-INFO|SOURCES.txt|'
                            'dependency_links.txt|not-zip-safe|requires.txt|top_level.txt)$')
        for dirname, directories, files in os.walk(install_dir):
            dirname = os.path.relpath(dirname, start=install_dir)
            if dirname == '.':
                dirname = ''

            for filename in files:
                path = os.path.join(dirname, filename)
                # If this is a byte code cache, look for the basename
                if path.endswith('.pyc') or path.endswith('.pyo'):
                    path = path[:-1]

                if path not in to_install_files:
                    # FIXME: ansible-test doesn't pass the paths of symlinks to us so we can't check those
                    if not os.path.islink(os.path.join(install_dir, path)):
                        if not EGG_RE.match(path):
                            print('%s: File was installed but was not supposed to' % path)


if __name__ == '__main__':
    main()
