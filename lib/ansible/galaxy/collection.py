# Copyright: (c) 2019, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import fnmatch
import json
import os
import re
import shutil
import tarfile
import tempfile
import time
import yaml

from hashlib import sha256
from io import BytesIO
from yaml.error import YAMLError

import ansible.constants as C
from ansible.errors import AnsibleError
from ansible.module_utils._text import to_bytes, to_native, to_text
from ansible.utils.display import Display
from ansible.utils.hashing import secure_hash, secure_hash_s


display = Display()

MANIFEST_FORMAT = 1

AUTHOR_REGEX = re.compile(r'^(?:(?P<name>.*)\s+<)(?:(?P<email>.*)>\s*)?(?:\((?P<url>.*)\))?')


def build_collection(collection_path, output_path, force):
    """
    Creates the Ansible collection artifact in a .tar.gz file.

    :param collection_path: The path to the collection to build. This should be the directory that contains the
        galaxy.yml file.
    :param output_path: The path to create the collection build artifact. This should be a directory.
    :param force: Whether to overwrite an existing collection build artifact or fail.
    :return: The path to the collection build artifact.
    """
    galaxy_path = os.path.join(collection_path, 'galaxy.yml')
    if not os.path.exists(galaxy_path):
        raise AnsibleError("The collection galaxy.yml path %s does not exist." % galaxy_path)

    collection_meta = _get_galaxy_yml(galaxy_path)
    file_manifest = _build_files_manifest(collection_path)
    collection_manifest = _build_manifest(**collection_meta)

    collection_output = os.path.join(output_path, "%s-%s-%s.tar.gz" % (collection_meta['namespace'],
                                                                       collection_meta['name'],
                                                                       collection_meta['version']))

    if os.path.exists(collection_output):
        if os.path.isdir(collection_output):
            raise AnsibleError("The output collection artifact %s already exists, "
                               "but is a directory - aborting" % collection_output)
        elif not force:
            raise AnsibleError("The file %s already exists. You can use --force to re-create "
                               "the collection artifact." % collection_output)

    _build_collection_tar(collection_path, collection_output, collection_manifest, file_manifest)


def _get_galaxy_yml(galaxy_yml_path):
    mandatory_keys = frozenset(['namespace', 'name', 'version', 'authors'])
    optional_strings = ('description', 'repository', 'documentation', 'homepage', 'issues')
    optional_lists = ('license', 'tags', 'authors')  # authors isn't optional but this will ensure it is list
    optional_dicts = ('dependencies',)
    all_keys = frozenset(list(mandatory_keys) + list(optional_strings) + list(optional_lists) + list(optional_dicts) +
                         ['repository', 'documentation', 'homepage_url', 'issues'])

    try:
        with open(to_bytes(galaxy_yml_path), 'rb') as g_yaml:
            galaxy_yml = yaml.safe_load(g_yaml)
    except YAMLError as err:
        raise AnsibleError("Failed to parse the galaxy.yml at %s with the following error:\n%s"
                           % (to_native(galaxy_yml_path), to_native(err)))

    set_keys = set(galaxy_yml.keys())
    missing_keys = mandatory_keys.difference(set_keys)
    if len(missing_keys) > 0:
        raise AnsibleError("The collection galaxy.yml at %s is missing the following mandatory keys: %s"
                           % (to_native(galaxy_yml_path), ", ".join(missing_keys)))

    extra_keys = set_keys.difference(all_keys)
    if len(extra_keys) > 0:
        display.warning("Found unknown keys in collection galaxy.yml at %s: %s"
                        % (to_native(galaxy_yml_path), ", ".join(extra_keys)))

    # Add the defaults if they have not been set
    for optional_string in optional_strings:
        if optional_string not in galaxy_yml:
            galaxy_yml[optional_string] = ""

    for optional_list in optional_lists:
        list_val = galaxy_yml.get(optional_list, None)

        if list_val is None:
            galaxy_yml[optional_list] = []
        elif not isinstance(list_val, list):
            galaxy_yml[optional_list] = [list_val]

    for optional_dict in optional_dicts:
        if optional_dict not in galaxy_yml:
            galaxy_yml[optional_dict] = {}

    # license is a builtin var in Python, to avoid confusion we just rename it to license_ids
    galaxy_yml['license_ids'] = galaxy_yml['license']
    del galaxy_yml['license']

    return galaxy_yml


def _build_files_manifest(collection_path):
    ignore_files = frozenset(['*.pyc', '*.retry'])
    ignore_dirs = frozenset(['CVS', '.bzr', '.hg', '.git', '.svn', '__pycache__', '.tox'])

    entry_template = {
        'name': None,
        'ftype': None,
        'chksum_type': None,
        'chksum_sha256': None,
        '_format': MANIFEST_FORMAT
    }
    manifest = []

    def _walk(path, top_level_dir, parent_dirs):
        for item in os.listdir(path):
            abs_path = os.path.join(path, item)
            rel_base_dir = '' if path == top_level_dir else path[len(top_level_dir) + 1:]
            rel_path = os.path.join(rel_base_dir, item)

            if os.path.isdir(abs_path):
                if item in ignore_dirs:
                    display.vvv("Skipping %s for collection build" % abs_path)
                    continue

                if os.path.islink(abs_path):
                    link_target = os.path.realpath(abs_path)

                    if not link_target.startswith(top_level_dir):
                        display.warning("Skipping %s as it is a symbolic link to a directory outside the collection"
                                        % abs_path)
                        continue

                manifest_entry = entry_template.copy()
                manifest_entry['name'] = rel_path
                manifest_entry['ftype'] = 'dir'

                manifest.append(manifest_entry)

                _walk(abs_path, top_level_dir, parent_dirs)
            else:
                if item == 'galaxy.yml':
                    continue
                elif any(fnmatch.fnmatch(item, pattern) for pattern in ignore_files):
                    display.vvv("Skipping %s for collection build" % abs_path)
                    continue

                manifest_entry = entry_template.copy()
                manifest_entry['name'] = rel_path
                manifest_entry['ftype'] = 'file'
                manifest_entry['chksum_type'] = 'sha256'
                manifest_entry['chksum_sha256'] = secure_hash(abs_path, hash_func=sha256)

                manifest.append(manifest_entry)

    dir_stats = os.stat(collection_path)
    parents = frozenset(((dir_stats.st_dev, dir_stats.st_ino),))
    _walk(collection_path, collection_path, parents)

    return manifest


def _build_manifest(namespace, name, version, authors, tags, description, license_ids, dependencies, **kwargs):

    def _parse_author_info(author):
        email = None
        url = None

        match = AUTHOR_REGEX.match(author)
        if match:
            author = match.group('name')
            email = match.group('email')
            url = match.group('url')

        return {
            'name': author,
            'email': email,
            'url': url
        }
    authors = [_parse_author_info(info) for info in authors]

    deps = {}
    for name, version in dependencies.items():
        deps[name] = {'version': version}

    manifest = {
        'format': MANIFEST_FORMAT,
        'name': "%s.%s" % (namespace, name),
        'version': version,
        'authors': authors,
        'keywords': tags,
        'description': description,
        'license': license_ids,
        'license_file': None,  # TODO: thaumos to verify the need for license_file and readme
        'readme': None,
        'dependencies': deps,
        'file_manifest_file': {
            'name': 'FILES.json',
            'chksum_type': 'sha256',
            'chksum_sha256': None,  # Filled out in _build_collection_tar
        },
    }

    return manifest


def _build_collection_tar(collection_path, tar_path, collection_manifest, file_manifest):
    files_manifest_json = to_bytes(json.dumps(file_manifest), errors='surrogate_or_strict')
    collection_manifest['file_manifest_file']['chksum_sha256'] = secure_hash_s(files_manifest_json, hash_func=sha256)
    collection_manifest_json = to_bytes(json.dumps(collection_manifest), errors='surrogate_or_strict')

    tempdir = tempfile.mkdtemp(dir=C.DEFAULT_LOCAL_TMP)
    try:
        tar_filepath = os.path.join(tempdir, os.path.basename(tar_path))
        tar_file = tarfile.open(tar_filepath, mode='w:gz')

        # Add the MANIFEST.json and FILES.json file to the archive
        for name, b in [('MANIFEST.json', collection_manifest_json), ('FILES.json', files_manifest_json)]:
            b_io = BytesIO(b)
            tar_info = tarfile.TarInfo(name)
            tar_info.size = len(b)
            tar_info.mtime = time.time()
            tar_info.mode = 0o0644
            tar_file.addfile(tarinfo=tar_info, fileobj=b_io)

        for file_info in file_manifest:
            filename = to_text(file_info['name'], errors='surrogate_or_strict')
            src_path = os.path.join(to_text(collection_path, errors='surrogate_or_strict'), filename)

            if os.path.islink(src_path) and os.path.isfile(src_path):
                src_path = os.path.realpath(src_path)

            def reset_stat(tarinfo):
                if tarinfo.issym() or tarinfo.islnk():
                    return None

                tarinfo.mode = 0o0755 if tarinfo.isdir() else 0o0644
                tarinfo.uid = tarinfo.gid = 0
                tarinfo.uname = tarinfo.gname = ''
                return tarinfo

            tar_file.add(src_path, arcname=filename, recursive=False, filter=reset_stat)

        tar_file.close()

        shutil.copy(tar_filepath, tar_path)
        display.display('Created collection for %s at %s' % (collection_manifest['name'], tar_path))
    finally:
        shutil.rmtree(tempdir)
