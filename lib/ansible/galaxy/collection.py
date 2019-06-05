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
    optional_lists = ('license', 'tags')
    optional_dicts = ('dependencies',)

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

    # TODO: should the galaxy.yml be strict and fail on extra keys

    # Add the defaults if they have not been set
    for optional_string in optional_strings:
        if optional_string not in galaxy_yml:
            galaxy_yml[optional_string] = ""

    for optional_list in optional_lists:
        if optional_list not in galaxy_yml:
            galaxy_yml[optional_list] = []

    for optional_dict in optional_dicts:
        if optional_dict not in galaxy_yml:
            galaxy_yml[optional_dict] = {}

    return galaxy_yml


def _build_files_manifest(collection_path):
    ignore_files = frozenset(['*.pyc', '*.retry', 'galaxy.yml'])
    ignore_dirs = frozenset(['CVS', '.bzr', '.hg', '.git', '.svn', '__pycache__', '.tox'])

    entry_template = {
        'name': None,
        'ftype': None,
        'chksum_type': None,
        'chksum_sha256': None,
        '_format': MANIFEST_FORMAT
    }

    # TODO: This was in the docs, is it actually required?
    current_dir_entry = entry_template.copy()
    current_dir_entry['name'] = '.'
    current_dir_entry['ftype'] = 'dir'
    manifest = [current_dir_entry]

    for root, dirs, files in os.walk(collection_path, followlinks=False):  # TODO: should we follow symlinks

        # Get the relative basedir path within the collection
        basedir = root[len(collection_path) + 1:] if root != collection_path else ''

        for filename in files:
            if any([fnmatch.fnmatch(filename, pattern) for pattern in ignore_files]):
                continue

            manifest_entry = entry_template.copy()
            manifest_entry['name'] = os.path.join(basedir, filename)
            manifest_entry['ftype'] = 'file'
            manifest_entry['chksum_type'] = 'sha256'
            manifest_entry['chksum_sha256'] = secure_hash(os.path.join(root, filename), hash_func=sha256)

            manifest.append(manifest_entry)

        for dirname in dirs:
            if dirname in ignore_dirs:
                continue

            manifest_entry = entry_template.copy()
            manifest_entry['name'] = os.path.join(basedir, dirname)
            manifest_entry['ftype'] = 'dir'

            manifest.append(manifest_entry)

    return manifest


def _build_manifest(namespace, name, version, authors, tags, description, license,
                    dependencies, **kwargs):

    def _parse_author_info(author):
        # TODO: can we set the standard to be a dict instead of a string, saves on regex parsing
        # TODO: parse with regex
        # temp regex: ^(?P<name>[\w\s]*)\s+\<(?P<email>[\w_.+-]+@[\w-]+\.[\w-.]+)\>\s+
        return {
            'name': author,
            'email': None,
            'url': None
        }
    authors = [_parse_author_info(info) for info in authors]

    # TODO: figure out dependencies dict

    manifest = {
        'format': MANIFEST_FORMAT,
        'name': "%s.%s" % (namespace, name),
        'version': version,
        'authors': authors,
        'keywords': tags,
        'description': description,
        'license': license,
        'license_file': None,  # TODO: verify this meeting
        'readme': None,  # TODO: verify this in meeting
        'dependencies': dependencies,
        'file_manifest': {
            'name': 'FILES.json',
            'chksum_type': 'sha256',
            'chksum_sha256': None,  # Filled out in _build_collection_tar
        },
    }

    return manifest


def _build_collection_tar(collection_path, tar_path, collection_manifest, file_manifest):
    files_manifest_json = to_bytes(json.dumps(file_manifest), errors='surrogate_or_strict')
    collection_manifest['file_manifest']['chksum_sha256'] = secure_hash_s(files_manifest_json, hash_func=sha256)
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
            tar_file.addfile(tarinfo=tar_info, fileobj=b_io)

        for file_info in file_manifest:
            if file_info['name'] == '.':
                continue
            elif file_info['ftype'] == 'dir':
                t = tarfile.TarInfo(file_info['name'])
                t.type = tarfile.DIRTYPE
                tar_file.addfile(t)
            else:
                filename = to_text(file_info['name'], errors='surrogate_or_strict')
                src_path = os.path.join(to_text(collection_path, errors='surrogate_or_strict'), filename)
                tar_file.add(src_path, arcname=filename)

        tar_file.close()
        shutil.copy(tar_filepath, tar_path)
    finally:
        shutil.rmtree(tempdir)
