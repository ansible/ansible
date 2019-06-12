# Copyright: (c) 2019, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import fnmatch
import json
import os
import shutil
import tarfile
import tempfile
import time
import uuid
import yaml

from hashlib import sha256
from io import BytesIO
from yaml.error import YAMLError

import ansible.constants as C
import ansible.module_utils.six.moves.urllib.error as urllib_error
from ansible.errors import AnsibleError
from ansible.module_utils._text import to_bytes, to_native, to_text
from ansible.utils.display import Display
from ansible.utils.hashing import secure_hash, secure_hash_s

from ansible.module_utils.urls import open_url


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
        raise AnsibleError("The collection galaxy.yml path '%s' does not exist." % galaxy_path)

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


def publish_collection(collection_path, server, key, ignore_certs, wait):
    """
    Publish an Ansible collection tarball into an Ansible Galaxy server.

    :param collection_path: The path to the collection tarball to publish.
    :param server: A native string of the Ansible Galaxy server to publish to.
    :param key: The API key to use for authorization.
    :param ignore_certs: Whether to ignore certificate validation when interacting with the server.
    """
    if not os.path.exists(collection_path):
        raise AnsibleError("The collection path specified '%s' does not exist." % collection_path)
    elif not tarfile.is_tarfile(collection_path):
        raise AnsibleError("The collection path specified '%s' is not a tarball, use 'ansible-galaxy collection "
                           "build' to create a proper release artifact." % collection_path)

    display.display("Publishing collection artifact '%s' to %s" % (collection_path, server))

    url = "%s/api/v2/collections/" % server

    data, content_type = _get_mime_data(collection_path)
    headers = {
        'Content-type': content_type,
        'Content-length': len(data),
    }
    if key:
        headers['Authorization'] = "Token %s" % key
    validate_certs = not ignore_certs

    try:
        resp = json.load(open_url(url, data=data, headers=headers, method='POST', validate_certs=validate_certs))
    except urllib_error.HTTPError as err:
        try:
            err_info = json.load(err)
        except (AttributeError, json.JSONDecodeError):
            err_info = {}

        code = err_info.get('code', 'Unknown')
        message = err_info.get('message', 'Unknown error returned by Galaxy server.')

        raise AnsibleError("Error when publishing collection (HTTP Code: %d, Message: %s Code: %s)"
                           % (err.status, message, code))

    display.vvv("Collection has been pushed to Galaxy server")
    if wait:
        _wait_import(resp['task'], key, validate_certs)

    display.display("Collection has been successfully publish to the Galaxy server")


def _get_galaxy_yml(galaxy_yml_path):
    mandatory_keys = frozenset(['namespace', 'name', 'version', 'authors', 'readme'])
    optional_strings = ('description', 'repository', 'documentation', 'homepage', 'issues')
    optional_lists = ('license', 'tags', 'authors')  # authors isn't optional but this will ensure it is list
    optional_dicts = ('dependencies',)
    all_keys = frozenset(list(mandatory_keys) + list(optional_strings) + list(optional_lists) + list(optional_dicts))

    try:
        with open(to_bytes(galaxy_yml_path), 'rb') as g_yaml:
            galaxy_yml = yaml.safe_load(g_yaml)
    except YAMLError as err:
        raise AnsibleError("Failed to parse the galaxy.yml at '%s' with the following error:\n%s"
                           % (to_native(galaxy_yml_path), to_native(err)))

    set_keys = set(galaxy_yml.keys())
    missing_keys = mandatory_keys.difference(set_keys)
    if len(missing_keys) > 0:
        raise AnsibleError("The collection galaxy.yml at '%s' is missing the following mandatory keys: %s"
                           % (to_native(galaxy_yml_path), ", ".join(sorted(missing_keys))))

    extra_keys = set_keys.difference(all_keys)
    if len(extra_keys) > 0:
        display.warning("Found unknown keys in collection galaxy.yml at '%s': %s"
                        % (to_native(galaxy_yml_path), ", ".join(extra_keys)))

    # Add the defaults if they have not been set
    for optional_string in optional_strings:
        if optional_string not in galaxy_yml:
            galaxy_yml[optional_string] = None

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
        'format': MANIFEST_FORMAT
    }
    manifest = {
        'files': [
            {
                'name': '.',
                'ftype': 'dir',
                'chksum_type': None,
                'chksum_sha256': None,
                'format': MANIFEST_FORMAT,
            },
        ],
        'format': MANIFEST_FORMAT,
    }

    def _walk(path, top_level_dir):
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

                manifest['files'].append(manifest_entry)

                _walk(abs_path, top_level_dir)
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

                manifest['files'].append(manifest_entry)

    _walk(collection_path, collection_path)

    return manifest


def _build_manifest(namespace, name, version, authors, readme, tags, description, license_ids, dependencies,
                    repository, documentation, homepage, issues, **kwargs):

    manifest = {
        'collection_info': {
            'namespace': namespace,
            'name': name,
            'version': version,
            'authors': authors,
            'readme': readme,
            'tags': tags,
            'description': description,
            # TODO: Either license or license_file needs to be set, need to verify with alikins how Mazer distinguishes
            # the 2 options.
            'license': license_ids,
            'license_file': None,
            'dependencies': dependencies,
            'repository': repository,
            'documentation': documentation,
            'homepage': homepage,
            'issues': issues,
        },
        'file_manifest_file': {
            'name': 'FILES.json',
            'ftype': 'file',
            'chksum_type': 'sha256',
            'chksum_sha256': None,  # Filled out in _build_collection_tar
            'format': MANIFEST_FORMAT
        },
        'format': MANIFEST_FORMAT,
    }

    return manifest


def _build_collection_tar(collection_path, tar_path, collection_manifest, file_manifest):
    files_manifest_json = to_bytes(json.dumps(file_manifest, indent=True), errors='surrogate_or_strict')
    collection_manifest['file_manifest_file']['chksum_sha256'] = secure_hash_s(files_manifest_json, hash_func=sha256)
    collection_manifest_json = to_bytes(json.dumps(collection_manifest, indent=True), errors='surrogate_or_strict')

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

        for file_info in file_manifest['files']:
            if file_info['name'] == '.':
                continue

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
        collection_name = "%s.%s" % (collection_manifest['collection_info']['namespace'],
                                     collection_manifest['collection_info']['name'])
        display.display('Created collection for %s at %s' % (collection_name, tar_path))
    finally:
        shutil.rmtree(tempdir)


def _get_mime_data(collection_path):
    with open(collection_path, 'rb') as collection_tar:
        data = collection_tar.read()

    boundary = '--------------------------%s' % uuid.uuid4().hex
    file_name = to_bytes(os.path.basename(collection_path), errors='surrogate_or_strict')
    part_boundary = b"--" + to_bytes(boundary, errors='surrogate_or_strict')

    form = [
        part_boundary,
        b"Content-Disposition: form-data; name=\"sha256\"",
        to_bytes(secure_hash_s(data), errors='surrogate_or_strict'),
        part_boundary,
        b"Content-Disposition: file; name=\"file\"; filename=\"%s\"" % file_name,
        b"Content-Type: application/octet-stream",
        b"",
        data,
        b"%s--" % part_boundary,
    ]

    content_type = 'multipart/form-data; boundary=%s' % boundary

    return b"\r\n".join(form), content_type


def _wait_import(task_url, key, validate_certs):
    headers = {}
    if key:
        headers['Authorization'] = "Token %s" % key

    task_id = [e for e in task_url.split('/') if e][-1]
    wait = 2
    display.vvv('Waiting until galaxy import task %s has completed' % task_id)

    while True:
        resp = json.load(open_url(task_url, headers=headers, method='GET', validate_certs=validate_certs))

        if resp.get('finished_at', None):
            break

        status = resp.get('status', 'waiting')
        display.vvv('Galaxy import process has status of %s, wait %d seconds before trying again' % (status, wait))
        time.sleep(wait)

    for message in resp.get('messages', []):
        display.vvv("Galaxy import message: %s - %s" % (message['level'], message['message']))

    if resp['state'] == 'failed':
        code = resp['error'].get('code', 'UNKNOWN')
        description = resp['error'].get('description', "Unknown error, see %s for more details" % task_url)
        raise AnsibleError("Galaxy import process failed: %s (Code: %s)" % (description, code))
