# Copyright: (c) 2019, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import fnmatch
import json
import operator
import os
import shutil
import tarfile
import tempfile
import time
import uuid
import yaml

from contextlib import contextmanager
from distutils.version import LooseVersion, StrictVersion
from hashlib import sha256
from io import BytesIO
from yaml.error import YAMLError

import ansible.constants as C
from ansible.errors import AnsibleError
from ansible.galaxy import get_collections_galaxy_meta_info
from ansible.module_utils._text import to_bytes, to_native, to_text
from ansible.module_utils import six
from ansible.utils.display import Display
from ansible.utils.hashing import secure_hash, secure_hash_s
from ansible.module_utils.urls import open_url

urlparse = six.moves.urllib.parse.urlparse
urllib_error = six.moves.urllib.error


display = Display()

MANIFEST_FORMAT = 1


class CollectionRequirement:

    _FILE_MAPPING = [(b'MANIFEST.json', 'manifest_file'), (b'FILES.json', 'files_file')]

    def __init__(self, namespace, name, b_path, source, versions, requirement, force, parent=None, validate_certs=True,
                 metadata=None, files=None, skip=False):
        """
        Represents a collection requirement, the versions that are available to be installed as well as any
        dependencies the collection has.

        :param namespace: The collection namespace.
        :param name: The collection name.
        :param b_path: Byte str of the path to the collection tarball if it has already been downloaded.
        :param source: The Galaxy server URL to download if the collection is from Galaxy.
        :param versions: A list of versions of the collection that are available.
        :param requirement: The version requirement string used to verify the list of versions fit the requirements.
        :param force: Whether the force flag applied to the collection.
        :param parent: The name of the parent the collection is a dependency of.
        :param validate_certs: Whether to validate the Galaxy server certificate.
        :param metadata: The collection metadata dict if it has already been retrieved.
        :param files: The files that exist inside the collection. This is based on the FILES.json file inside the
            collection artifact.
        :param skip: Whether to skip installing the collection. Should be set if the collection is already installed
            and force is not set.
        """
        self.namespace = namespace
        self.name = name
        self.b_path = b_path
        self.source = source
        self.versions = set(versions)
        self.force = force
        self.skip = skip
        self.required_by = []
        self._validate_certs = validate_certs

        self._metadata = metadata
        self._files = files
        self._galaxy_info = None

        self.add_requirement(parent, requirement)

    def __str__(self):
        return to_native("%s.%s" % (self.namespace, self.name))

    def __unicode__(self):
        return u"%s.%s" % (self.namespace, self.name)

    @property
    def latest_version(self):
        try:
            return max([v for v in self.versions if v != '*'], key=LooseVersion)
        except ValueError:  # ValueError: max() arg is an empty sequence
            return '*'

    @property
    def dependencies(self):
        if self._metadata:
            return self._metadata['dependencies']
        elif len(self.versions) > 1:
            return None

        self._get_metadata()
        return self._metadata['dependencies']

    def add_requirement(self, parent, requirement):
        self.required_by.append((parent, requirement))
        new_versions = set(v for v in self.versions if self._meets_requirements(v, requirement, parent))
        if len(new_versions) == 0:
            if self.skip:
                force_flag = '--force-with-deps' if parent else '--force'
                version = self.latest_version if self.latest_version != '*' else 'unknown'
                msg = "Cannot meet requirement %s:%s as it is already installed at version '%s'. Use %s to overwrite" \
                      % (to_text(self), requirement, version, force_flag)
                raise AnsibleError(msg)
            elif parent is None:
                msg = "Cannot meet requirement %s for dependency %s" % (requirement, to_text(self))
            else:
                msg = "Cannot meet dependency requirement '%s:%s' for collection %s" \
                      % (to_text(self), requirement, parent)

            collection_source = to_text(self.b_path, nonstring='passthru') or self.source
            req_by = "\n".join(
                "\t%s - '%s:%s'" % (to_text(p) if p else 'base', to_text(self), r)
                for p, r in self.required_by
            )

            versions = ", ".join(sorted(self.versions, key=LooseVersion))
            raise AnsibleError(
                "%s from source '%s'. Available versions before last requirement added: %s\nRequirements from:\n%s"
                % (msg, collection_source, versions, req_by)
            )

        self.versions = new_versions

    def install(self, path, b_temp_path):
        if self.skip:
            display.display("Skipping '%s' as it is already installed" % to_text(self))
            return

        # Install if it is not
        collection_path = os.path.join(path, self.namespace, self.name)
        b_collection_path = to_bytes(collection_path, errors='surrogate_or_strict')
        display.display("Installing '%s:%s' to '%s'" % (to_text(self), self.latest_version, collection_path))

        if self.b_path is None:
            download_url = self._galaxy_info['download_url']
            artifact_hash = self._galaxy_info['artifact']['sha256']
            self.b_path = _download_file(download_url, b_temp_path, artifact_hash, self._validate_certs)

        if os.path.exists(b_collection_path):
            shutil.rmtree(b_collection_path)
        os.makedirs(b_collection_path)

        with tarfile.open(self.b_path, mode='r') as collection_tar:
            files_member_obj = collection_tar.getmember('FILES.json')
            with _tarfile_extract(collection_tar, files_member_obj) as files_obj:
                files = json.loads(to_text(files_obj.read(), errors='surrogate_or_strict'))

            _extract_tar_file(collection_tar, 'MANIFEST.json', b_collection_path, b_temp_path)
            _extract_tar_file(collection_tar, 'FILES.json', b_collection_path, b_temp_path)

            for file_info in files['files']:
                file_name = file_info['name']
                if file_name == '.':
                    continue

                if file_info['ftype'] == 'file':
                    _extract_tar_file(collection_tar, file_name, b_collection_path, b_temp_path,
                                      expected_hash=file_info['chksum_sha256'])
                else:
                    os.makedirs(os.path.join(b_collection_path, to_bytes(file_name, errors='surrogate_or_strict')))

    def set_latest_version(self):
        self.versions = set([self.latest_version])
        self._get_metadata()

    def _get_metadata(self):
        if self._metadata:
            return

        n_collection_url = _urljoin(self.source, 'api', 'v2', 'collections', self.namespace, self.name, 'versions',
                                    self.latest_version)
        details = json.load(open_url(n_collection_url, validate_certs=self._validate_certs))
        self._galaxy_info = details
        self._metadata = details['metadata']

    def _meets_requirements(self, version, requirements, parent):
        """
        Supports version identifiers can be '==', '!=', '>', '>=', '<', '<=', '*'. Each requirement is delimited by ','
        """
        op_map = {
            '!=': operator.ne,
            '==': operator.eq,
            '=': operator.eq,
            '>=': operator.ge,
            '>': operator.gt,
            '<=': operator.le,
            '<': operator.lt,
        }

        for req in list(requirements.split(',')):
            op_pos = 2 if len(req) > 1 and req[1] == '=' else 1
            op = op_map.get(req[:op_pos])

            requirement = req[op_pos:]
            if not op:
                requirement = req
                op = operator.eq

                # In the case we are checking a new requirement on a base requirement (parent != None) we can't accept
                # version as '*' (unknown version) unless the requirement is also '*'.
                if parent and version == '*' and requirement != '*':
                    break
                elif requirement == '*' or version == '*':
                    continue

            if not op(LooseVersion(version), LooseVersion(requirement)):
                break
        else:
            return True

        # The loop was broken early, it does not meet all the requirements
        return False

    @staticmethod
    def from_tar(b_path, validate_certs, force, parent=None):
        if not tarfile.is_tarfile(b_path):
            raise AnsibleError("Collection artifact at '%s' is not a valid tar file." % to_native(b_path))

        info = {}
        with tarfile.open(b_path, mode='r') as collection_tar:
            for b_member_name, property_name in CollectionRequirement._FILE_MAPPING:
                n_member_name = to_native(b_member_name)
                try:
                    member = collection_tar.getmember(n_member_name)
                except KeyError:
                    raise AnsibleError("Collection at '%s' does not contain the required file %s."
                                       % (to_native(b_path), n_member_name))

                with _tarfile_extract(collection_tar, member) as member_obj:
                    try:
                        info[property_name] = json.loads(to_text(member_obj.read(), errors='surrogate_or_strict'))
                    except ValueError:
                        raise AnsibleError("Collection tar file member %s does not contain a valid json string."
                                           % n_member_name)

        meta = info['manifest_file']['collection_info']
        files = info['files_file']['files']

        namespace = meta['namespace']
        name = meta['name']
        version = meta['version']

        return CollectionRequirement(namespace, name, b_path, None, [version], version, force, parent=parent,
                                     validate_certs=validate_certs, metadata=meta, files=files)

    @staticmethod
    def from_path(b_path, validate_certs, force, parent=None):
        info = {}
        for b_file_name, property_name in CollectionRequirement._FILE_MAPPING:
            b_file_path = os.path.join(b_path, b_file_name)
            if not os.path.exists(b_file_path):
                continue

            with open(b_file_path, 'rb') as file_obj:
                try:
                    info[property_name] = json.loads(to_text(file_obj.read(), errors='surrogate_or_strict'))
                except ValueError:
                    raise AnsibleError("Collection file at '%s' does not contain a valid json string."
                                       % to_native(b_file_path))

        if 'manifest_file' in info:
            meta = info['manifest_file']['collection_info']
        else:
            display.warning("Collection at '%s' does not have a MANIFEST.json file, cannot detect version."
                            % to_text(b_path))
            parent_dir, name = os.path.split(to_text(b_path, errors='surrogate_or_strict'))
            namespace = os.path.split(parent_dir)[1]
            meta = {
                'namespace': namespace,
                'name': name,
                'version': '*',
                'dependencies': {},
            }

        namespace = meta['namespace']
        name = meta['name']
        version = meta['version']

        files = info.get('files_file', {}).get('files', {})

        return CollectionRequirement(namespace, name, b_path, None, [version], version, force, parent=parent,
                                     validate_certs=validate_certs, metadata=meta, files=files, skip=True)

    @staticmethod
    def from_name(collection, servers, requirement, validate_certs, force, parent=None):
        namespace, name = collection.split('.', 1)
        galaxy_info = None
        galaxy_meta = None

        for server in servers:
            collection_url_paths = [server, 'api', 'v2', 'collections', namespace, name, 'versions']

            is_single = False
            if not (requirement == '*' or requirement.startswith('<') or requirement.startswith('>') or
                    requirement.startswith('!=')):
                if requirement.startswith('='):
                    requirement = requirement.lstrip('=')

                collection_url_paths.append(requirement)
                is_single = True

            n_collection_url = _urljoin(*collection_url_paths)
            try:
                resp = json.load(open_url(n_collection_url, validate_certs=validate_certs))
            except urllib_error.HTTPError as err:
                if err.code == 404:
                    continue
                raise

            if is_single:
                galaxy_info = resp
                galaxy_meta = resp['metadata']
                versions = [resp['version']]
            else:
                versions = []
                while True:
                    # Galaxy supports semver but ansible-galaxy does not. We ignore any versions that don't match
                    # StrictVersion (x.y.z) and only support pre-releases if an explicit version was set (done above).
                    versions += [v['version'] for v in resp['results'] if StrictVersion.version_re.match(v['version'])]
                    if resp['next'] is None:
                        break
                    resp = json.load(open_url(to_native(resp['next'], errors='surrogate_or_strict'),
                                              validate_certs=validate_certs))

            break
        else:
            raise AnsibleError("Failed to find collection %s:%s" % (collection, requirement))

        req = CollectionRequirement(namespace, name, None, server, versions, requirement, force, parent=parent,
                                    validate_certs=validate_certs, metadata=galaxy_meta)
        req._galaxy_info = galaxy_info
        return req


def build_collection(collection_path, output_path, force):
    """
    Creates the Ansible collection artifact in a .tar.gz file.

    :param collection_path: The path to the collection to build. This should be the directory that contains the
        galaxy.yml file.
    :param output_path: The path to create the collection build artifact. This should be a directory.
    :param force: Whether to overwrite an existing collection build artifact or fail.
    :return: The path to the collection build artifact.
    """
    b_collection_path = to_bytes(collection_path, errors='surrogate_or_strict')
    b_galaxy_path = os.path.join(b_collection_path, b'galaxy.yml')
    if not os.path.exists(b_galaxy_path):
        raise AnsibleError("The collection galaxy.yml path '%s' does not exist." % to_native(b_galaxy_path))

    collection_meta = _get_galaxy_yml(b_galaxy_path)
    file_manifest = _build_files_manifest(b_collection_path, collection_meta['namespace'], collection_meta['name'])
    collection_manifest = _build_manifest(**collection_meta)

    collection_output = os.path.join(output_path, "%s-%s-%s.tar.gz" % (collection_meta['namespace'],
                                                                       collection_meta['name'],
                                                                       collection_meta['version']))

    b_collection_output = to_bytes(collection_output, errors='surrogate_or_strict')
    if os.path.exists(b_collection_output):
        if os.path.isdir(b_collection_output):
            raise AnsibleError("The output collection artifact '%s' already exists, "
                               "but is a directory - aborting" % to_native(collection_output))
        elif not force:
            raise AnsibleError("The file '%s' already exists. You can use --force to re-create "
                               "the collection artifact." % to_native(collection_output))

    _build_collection_tar(b_collection_path, b_collection_output, collection_manifest, file_manifest)


def publish_collection(collection_path, server, key, ignore_certs, wait):
    """
    Publish an Ansible collection tarball into an Ansible Galaxy server.

    :param collection_path: The path to the collection tarball to publish.
    :param server: A native string of the Ansible Galaxy server to publish to.
    :param key: The API key to use for authorization.
    :param ignore_certs: Whether to ignore certificate validation when interacting with the server.
    """
    b_collection_path = to_bytes(collection_path, errors='surrogate_or_strict')
    if not os.path.exists(b_collection_path):
        raise AnsibleError("The collection path specified '%s' does not exist." % to_native(collection_path))
    elif not tarfile.is_tarfile(b_collection_path):
        raise AnsibleError("The collection path specified '%s' is not a tarball, use 'ansible-galaxy collection "
                           "build' to create a proper release artifact." % to_native(collection_path))

    display.display("Publishing collection artifact '%s' to %s" % (collection_path, server))

    n_url = _urljoin(server, 'api', 'v2', 'collections')

    data, content_type = _get_mime_data(b_collection_path)
    headers = {
        'Content-type': content_type,
        'Content-length': len(data),
    }
    if key:
        headers['Authorization'] = "Token %s" % key
    validate_certs = not ignore_certs

    try:
        resp = json.load(open_url(n_url, data=data, headers=headers, method='POST', validate_certs=validate_certs))
    except urllib_error.HTTPError as err:
        try:
            err_info = json.load(err)
        except (AttributeError, ValueError):
            err_info = {}

        code = to_native(err_info.get('code', 'Unknown'))
        message = to_native(err_info.get('message', 'Unknown error returned by Galaxy server.'))

        raise AnsibleError("Error when publishing collection (HTTP Code: %d, Message: %s Code: %s)"
                           % (err.code, message, code))

    display.vvv("Collection has been pushed to the Galaxy server %s" % server)
    import_uri = resp['task']
    if wait:
        _wait_import(import_uri, key, validate_certs)
        display.display("Collection has been successfully published to the Galaxy server")
    else:
        display.display("Collection has been pushed to the Galaxy server, not waiting until import has completed "
                        "due to --no-wait being set. Import task results can be found at %s" % import_uri)


def install_collections(collections, output_path, servers, validate_certs, ignore_errors, no_deps, force, force_deps):
    """
    Install Ansible collections to the path specified.

    :param collections: The collections to install, should be a list of tuples with (name, requirement, Galaxy server).
    :param output_path: The path to install the collections to.
    :param servers: A list of Galaxy servers to query when searching for a collection.
    :param validate_certs: Whether to validate the Galaxy server certificates.
    :param ignore_errors: Whether to ignore any errors when installing the collection.
    :param no_deps: Ignore any collection dependencies and only install the base requirements.
    :param force: Re-install a collection if it has already been installed.
    :param force_deps: Re-install a collection as well as its dependencies if they have already been installed.
    """
    existing_collections = _find_existing_collections(output_path)

    with _tempdir() as b_temp_path:
        dependency_map = _build_dependency_map(collections, existing_collections, b_temp_path, servers, validate_certs,
                                               force, force_deps, no_deps)

        for collection in dependency_map.values():
            try:
                collection.install(output_path, b_temp_path)
            except AnsibleError as err:
                if ignore_errors:
                    display.warning("Failed to install collection %s but skipping due to --ignore-errors being set. "
                                    "Error: %s" % (to_text(collection), to_text(err)))
                else:
                    raise


def parse_collections_requirements_file(requirements_file):
    """
    Parses an Ansible requirement.yml file and returns all the collections defined in it. This value ca be used with
    install_collection(). The requirements file is in the form:

        ---
        collections:
        - namespace.collection
        - name: namespace.collection
          version: version identifier, multiple identifiers are separated by ','
          source: the URL or prededefined source name in ~/.ansible_galaxy to pull the collection from

    :param requirements_file: The path to the requirements file.
    :return: A list of tuples (name, version, source).
    """
    collection_info = []

    b_requirements_file = to_bytes(requirements_file, errors='surrogate_or_strict')
    if not os.path.exists(b_requirements_file):
        raise AnsibleError("The requirements file '%s' does not exist." % to_native(requirements_file))

    display.vvv("Reading collection requirement file at '%s'" % requirements_file)
    with open(b_requirements_file, 'rb') as req_obj:
        try:
            requirements = yaml.safe_load(req_obj)
        except YAMLError as err:
            raise AnsibleError("Failed to parse the collection requirements yml at '%s' with the following error:\n%s"
                               % (to_native(requirements_file), to_native(err)))

    if not isinstance(requirements, dict) or 'collections' not in requirements:
        # TODO: Link to documentation page that documents the requirements.yml format for collections.
        raise AnsibleError("Expecting collections requirements file to be a dict with the key "
                           "collections that contains a list of collections to install.")

    for collection_req in requirements['collections']:
        if isinstance(collection_req, dict):
            req_name = collection_req.get('name', None)
            if req_name is None:
                raise AnsibleError("Collections requirement entry should contain the key name.")

            req_version = collection_req.get('version', '*')
            req_source = collection_req.get('source', None)

            collection_info.append((req_name, req_version, req_source))
        else:
            collection_info.append((collection_req, '*', None))

    return collection_info


@contextmanager
def _tempdir():
    b_temp_path = tempfile.mkdtemp(dir=to_bytes(C.DEFAULT_LOCAL_TMP, errors='surrogate_or_strict'))
    yield b_temp_path
    shutil.rmtree(b_temp_path)


@contextmanager
def _tarfile_extract(tar, member):
    tar_obj = tar.extractfile(member)
    yield tar_obj
    tar_obj.close()


def _get_galaxy_yml(b_galaxy_yml_path):
    meta_info = get_collections_galaxy_meta_info()

    mandatory_keys = set()
    string_keys = set()
    list_keys = set()
    dict_keys = set()

    for info in meta_info:
        if info.get('required', False):
            mandatory_keys.add(info['key'])

        key_list_type = {
            'str': string_keys,
            'list': list_keys,
            'dict': dict_keys,
        }[info.get('type', 'str')]
        key_list_type.add(info['key'])

    all_keys = frozenset(list(mandatory_keys) + list(string_keys) + list(list_keys) + list(dict_keys))

    try:
        with open(b_galaxy_yml_path, 'rb') as g_yaml:
            galaxy_yml = yaml.safe_load(g_yaml)
    except YAMLError as err:
        raise AnsibleError("Failed to parse the galaxy.yml at '%s' with the following error:\n%s"
                           % (to_native(b_galaxy_yml_path), to_native(err)))

    set_keys = set(galaxy_yml.keys())
    missing_keys = mandatory_keys.difference(set_keys)
    if missing_keys:
        raise AnsibleError("The collection galaxy.yml at '%s' is missing the following mandatory keys: %s"
                           % (to_native(b_galaxy_yml_path), ", ".join(sorted(missing_keys))))

    extra_keys = set_keys.difference(all_keys)
    if len(extra_keys) > 0:
        display.warning("Found unknown keys in collection galaxy.yml at '%s': %s"
                        % (to_text(b_galaxy_yml_path), ", ".join(extra_keys)))

    # Add the defaults if they have not been set
    for optional_string in string_keys:
        if optional_string not in galaxy_yml:
            galaxy_yml[optional_string] = None

    for optional_list in list_keys:
        list_val = galaxy_yml.get(optional_list, None)

        if list_val is None:
            galaxy_yml[optional_list] = []
        elif not isinstance(list_val, list):
            galaxy_yml[optional_list] = [list_val]

    for optional_dict in dict_keys:
        if optional_dict not in galaxy_yml:
            galaxy_yml[optional_dict] = {}

    # license is a builtin var in Python, to avoid confusion we just rename it to license_ids
    galaxy_yml['license_ids'] = galaxy_yml['license']
    del galaxy_yml['license']

    return galaxy_yml


def _build_files_manifest(b_collection_path, namespace, name):
    # Contains tuple of (b_filename, only root) where 'only root' means to only ignore the file in the root dir
    b_ignore_files = frozenset([(b'*.pyc', False), (b'*.retry', False),
                                (to_bytes('{0}-{1}-*.tar.gz'.format(namespace, name)), True)])
    b_ignore_dirs = frozenset([(b'CVS', False), (b'.bzr', False), (b'.hg', False), (b'.git', False), (b'.svn', False),
                               (b'__pycache__', False), (b'.tox', False)])

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

    def _walk(b_path, b_top_level_dir):
        is_root = b_path == b_top_level_dir

        for b_item in os.listdir(b_path):
            b_abs_path = os.path.join(b_path, b_item)
            b_rel_base_dir = b'' if b_path == b_top_level_dir else b_path[len(b_top_level_dir) + 1:]
            rel_path = to_text(os.path.join(b_rel_base_dir, b_item), errors='surrogate_or_strict')

            if os.path.isdir(b_abs_path):
                if any(b_item == b_path for b_path, root_only in b_ignore_dirs
                       if not root_only or root_only == is_root):
                    display.vvv("Skipping '%s' for collection build" % to_text(b_abs_path))
                    continue

                if os.path.islink(b_abs_path):
                    b_link_target = os.path.realpath(b_abs_path)

                    if not b_link_target.startswith(b_top_level_dir):
                        display.warning("Skipping '%s' as it is a symbolic link to a directory outside the collection"
                                        % to_text(b_abs_path))
                        continue

                manifest_entry = entry_template.copy()
                manifest_entry['name'] = rel_path
                manifest_entry['ftype'] = 'dir'

                manifest['files'].append(manifest_entry)

                _walk(b_abs_path, b_top_level_dir)
            else:
                if b_item == b'galaxy.yml':
                    continue
                elif any(fnmatch.fnmatch(b_item, b_pattern) for b_pattern, root_only in b_ignore_files
                         if not root_only or root_only == is_root):
                    display.vvv("Skipping '%s' for collection build" % to_text(b_abs_path))
                    continue

                manifest_entry = entry_template.copy()
                manifest_entry['name'] = rel_path
                manifest_entry['ftype'] = 'file'
                manifest_entry['chksum_type'] = 'sha256'
                manifest_entry['chksum_sha256'] = secure_hash(b_abs_path, hash_func=sha256)

                manifest['files'].append(manifest_entry)

    _walk(b_collection_path, b_collection_path)

    return manifest


def _build_manifest(namespace, name, version, authors, readme, tags, description, license_ids, license_file,
                    dependencies, repository, documentation, homepage, issues, **kwargs):

    manifest = {
        'collection_info': {
            'namespace': namespace,
            'name': name,
            'version': version,
            'authors': authors,
            'readme': readme,
            'tags': tags,
            'description': description,
            'license': license_ids,
            'license_file': license_file if license_file else None,  # Handle galaxy.yml having an empty string (None)
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


def _build_collection_tar(b_collection_path, b_tar_path, collection_manifest, file_manifest):
    files_manifest_json = to_bytes(json.dumps(file_manifest, indent=True), errors='surrogate_or_strict')
    collection_manifest['file_manifest_file']['chksum_sha256'] = secure_hash_s(files_manifest_json, hash_func=sha256)
    collection_manifest_json = to_bytes(json.dumps(collection_manifest, indent=True), errors='surrogate_or_strict')

    with _tempdir() as b_temp_path:
        b_tar_filepath = os.path.join(b_temp_path, os.path.basename(b_tar_path))

        with tarfile.open(b_tar_filepath, mode='w:gz') as tar_file:
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

                # arcname expects a native string, cannot be bytes
                filename = to_native(file_info['name'], errors='surrogate_or_strict')
                b_src_path = os.path.join(b_collection_path, to_bytes(filename, errors='surrogate_or_strict'))

                def reset_stat(tarinfo):
                    tarinfo.mode = 0o0755 if tarinfo.isdir() else 0o0644
                    tarinfo.uid = tarinfo.gid = 0
                    tarinfo.uname = tarinfo.gname = ''
                    return tarinfo

                tar_file.add(os.path.realpath(b_src_path), arcname=filename, recursive=False, filter=reset_stat)

        shutil.copy(b_tar_filepath, b_tar_path)
        collection_name = "%s.%s" % (collection_manifest['collection_info']['namespace'],
                                     collection_manifest['collection_info']['name'])
        display.display('Created collection for %s at %s' % (collection_name, to_text(b_tar_path)))


def _get_mime_data(b_collection_path):
    with open(b_collection_path, 'rb') as collection_tar:
        data = collection_tar.read()

    boundary = '--------------------------%s' % uuid.uuid4().hex
    b_file_name = os.path.basename(b_collection_path)
    part_boundary = b"--" + to_bytes(boundary, errors='surrogate_or_strict')

    form = [
        part_boundary,
        b"Content-Disposition: form-data; name=\"sha256\"",
        to_bytes(secure_hash_s(data), errors='surrogate_or_strict'),
        part_boundary,
        b"Content-Disposition: file; name=\"file\"; filename=\"%s\"" % b_file_name,
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

    display.vvv('Waiting until galaxy import task %s has completed' % task_url)

    wait = 2
    while True:
        resp = json.load(open_url(to_native(task_url, errors='surrogate_or_strict'), headers=headers, method='GET',
                                  validate_certs=validate_certs))

        if resp.get('finished_at', None):
            break
        elif wait > 20:
            # We try for a maximum of ~60 seconds before giving up in case something has gone wrong on the server end.
            raise AnsibleError("Timeout while waiting for the Galaxy import process to finish, check progress at '%s'"
                               % to_native(task_url))

        status = resp.get('status', 'waiting')
        display.vvv('Galaxy import process has a status of %s, wait %d seconds before trying again' % (status, wait))
        time.sleep(wait)
        wait *= 1.5  # poor man's exponential backoff algo so we don't flood the Galaxy API.

    for message in resp.get('messages', []):
        level = message['level']
        if level == 'error':
            display.error("Galaxy import error message: %s" % message['message'])
        elif level == 'warning':
            display.warning("Galaxy import warning message: %s" % message['message'])
        else:
            display.vvv("Galaxy import message: %s - %s" % (level, message['message']))

    if resp['state'] == 'failed':
        code = to_native(resp['error'].get('code', 'UNKNOWN'))
        description = to_native(resp['error'].get('description', "Unknown error, see %s for more details" % task_url))
        raise AnsibleError("Galaxy import process failed: %s (Code: %s)" % (description, code))


def _find_existing_collections(path):
    collections = []

    b_path = to_bytes(path, errors='surrogate_or_strict')
    for b_namespace in os.listdir(b_path):
        b_namespace_path = os.path.join(b_path, b_namespace)
        if os.path.isfile(b_namespace_path):
            continue

        for b_collection in os.listdir(b_namespace_path):
            b_collection_path = os.path.join(b_namespace_path, b_collection)
            if os.path.isdir(b_collection_path):
                req = CollectionRequirement.from_path(b_collection_path, True, False)
                display.vvv("Found installed collection %s:%s at '%s'" % (to_text(req), req.latest_version,
                                                                          to_text(b_collection_path)))
                collections.append(req)

    return collections


def _build_dependency_map(collections, existing_collections, b_temp_path, servers, validate_certs, force, force_deps,
                          no_deps):
    dependency_map = {}

    # First build the dependency map on the actual requirements
    for name, version, source in collections:
        _get_collection_info(dependency_map, existing_collections, name, version, source, b_temp_path, servers,
                             validate_certs, (force or force_deps))

    checked_parents = set([to_text(c) for c in dependency_map.values() if c.skip])
    while len(dependency_map) != len(checked_parents):
        while not no_deps:  # Only parse dependencies if no_deps was not set
            parents_to_check = set(dependency_map.keys()).difference(checked_parents)

            deps_exhausted = True
            for parent in parents_to_check:
                parent_info = dependency_map[parent]

                if parent_info.dependencies:
                    deps_exhausted = False
                    for dep_name, dep_requirement in parent_info.dependencies.items():
                        _get_collection_info(dependency_map, existing_collections, dep_name, dep_requirement,
                                             parent_info.source, b_temp_path, servers, validate_certs, force_deps,
                                             parent=parent)

                    checked_parents.add(parent)

            # No extra dependencies were resolved, exit loop
            if deps_exhausted:
                break

        # Now we have resolved the deps to our best extent, now select the latest version for collections with
        # multiple versions found and go from there
        deps_not_checked = set(dependency_map.keys()).difference(checked_parents)
        for collection in deps_not_checked:
            dependency_map[collection].set_latest_version()
            if no_deps or len(dependency_map[collection].dependencies) == 0:
                checked_parents.add(collection)

    return dependency_map


def _get_collection_info(dep_map, existing_collections, collection, requirement, source, b_temp_path, server_list,
                         validate_certs, force, parent=None):
    dep_msg = ""
    if parent:
        dep_msg = " - as dependency of %s" % parent
    display.vvv("Processing requirement collection '%s'%s" % (to_text(collection), dep_msg))

    b_tar_path = None
    if os.path.isfile(to_bytes(collection, errors='surrogate_or_strict')):
        display.vvvv("Collection requirement '%s' is a tar artifact" % to_text(collection))
        b_tar_path = to_bytes(collection, errors='surrogate_or_strict')
    elif urlparse(collection).scheme:
        display.vvvv("Collection requirement '%s' is a URL to a tar artifact" % collection)
        b_tar_path = _download_file(collection, b_temp_path, None, validate_certs)

    if b_tar_path:
        req = CollectionRequirement.from_tar(b_tar_path, validate_certs, force, parent=parent)

        collection_name = to_text(req)
        if collection_name in dep_map:
            collection_info = dep_map[collection_name]
            collection_info.add_requirement(None, req.latest_version)
        else:
            collection_info = req
    else:
        display.vvvv("Collection requirement '%s' is the name of a collection" % collection)
        if collection in dep_map:
            collection_info = dep_map[collection]
            collection_info.add_requirement(parent, requirement)
        else:
            servers = [source] if source else server_list
            collection_info = CollectionRequirement.from_name(collection, servers, requirement, validate_certs, force,
                                                              parent=parent)

    existing = [c for c in existing_collections if to_text(c) == to_text(collection_info)]
    if existing and not collection_info.force:
        # Test that the installed collection fits the requirement
        existing[0].add_requirement(to_text(collection_info), requirement)
        collection_info = existing[0]

    dep_map[to_text(collection_info)] = collection_info


def _urljoin(*args):
    return '/'.join(to_native(a, errors='surrogate_or_strict').rstrip('/') for a in args + ('',))


def _download_file(url, b_path, expected_hash, validate_certs):
    bufsize = 65536
    digest = sha256()

    urlsplit = os.path.splitext(to_text(url.rsplit('/', 1)[1]))
    b_file_name = to_bytes(urlsplit[0], errors='surrogate_or_strict')
    b_file_ext = to_bytes(urlsplit[1], errors='surrogate_or_strict')
    b_file_path = tempfile.NamedTemporaryFile(dir=b_path, prefix=b_file_name, suffix=b_file_ext, delete=False).name

    display.vvv("Downloading %s to %s" % (url, to_text(b_path)))
    resp = open_url(to_native(url, errors='surrogate_or_strict'), validate_certs=validate_certs)

    with open(b_file_path, 'wb') as download_file:
        data = resp.read(bufsize)
        while data:
            digest.update(data)
            download_file.write(data)
            data = resp.read(bufsize)

    if expected_hash:
        actual_hash = digest.hexdigest()
        display.vvvv("Validating downloaded file hash %s with expected hash %s" % (actual_hash, expected_hash))
        if expected_hash != actual_hash:
            raise AnsibleError("Mismatch artifact hash with downloaded file")

    return b_file_path


def _extract_tar_file(tar, filename, b_dest, b_temp_path, expected_hash=None):
    n_filename = to_native(filename, errors='surrogate_or_strict')
    try:
        member = tar.getmember(n_filename)
    except KeyError:
        raise AnsibleError("Collection tar at '%s' does not contain the expected file '%s'." % (to_native(tar.name),
                                                                                                n_filename))

    with tempfile.NamedTemporaryFile(dir=b_temp_path, delete=False) as tmpfile_obj:
        bufsize = 65536
        sha256_digest = sha256()
        with _tarfile_extract(tar, member) as tar_obj:
            data = tar_obj.read(bufsize)
            while data:
                tmpfile_obj.write(data)
                tmpfile_obj.flush()
                sha256_digest.update(data)
                data = tar_obj.read(bufsize)

        actual_hash = sha256_digest.hexdigest()

        if expected_hash and actual_hash != expected_hash:
            raise AnsibleError("Checksum mismatch for '%s' inside collection at '%s'"
                               % (n_filename, to_native(tar.name)))

        b_dest_filepath = os.path.join(b_dest, to_bytes(filename, errors='surrogate_or_strict'))
        b_parent_dir = os.path.split(b_dest_filepath)[0]
        if not os.path.exists(b_parent_dir):
            # Seems like Galaxy does not validate if all file entries have a corresponding dir ftype entry. This check
            # makes sure we create the parent directory even if it wasn't set in the metadata.
            os.makedirs(b_parent_dir)

        shutil.move(to_bytes(tmpfile_obj.name, errors='surrogate_or_strict'), b_dest_filepath)
