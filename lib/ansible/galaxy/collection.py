# Copyright: (c) 2019, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import errno
import fnmatch
import json
import operator
import os
import shutil
import stat
import sys
import tarfile
import tempfile
import threading
import time
import yaml

from contextlib import contextmanager
from distutils.version import LooseVersion, StrictVersion
from hashlib import sha256
from io import BytesIO
from yaml.error import YAMLError

try:
    import queue
except ImportError:
    import Queue as queue  # Python 2

import ansible.constants as C
from ansible.errors import AnsibleError
from ansible.galaxy import get_collections_galaxy_meta_info
from ansible.galaxy.api import CollectionVersionMetadata, GalaxyError
from ansible.galaxy.user_agent import user_agent
from ansible.module_utils import six
from ansible.module_utils._text import to_bytes, to_native, to_text
from ansible.utils.collection_loader import AnsibleCollectionRef
from ansible.utils.display import Display
from ansible.utils.hashing import secure_hash, secure_hash_s
from ansible.module_utils.urls import open_url

urlparse = six.moves.urllib.parse.urlparse
urllib_error = six.moves.urllib.error


display = Display()

MANIFEST_FORMAT = 1


class CollectionRequirement:

    _FILE_MAPPING = [(b'MANIFEST.json', 'manifest_file'), (b'FILES.json', 'files_file')]

    def __init__(self, namespace, name, b_path, api, versions, requirement, force, parent=None, metadata=None,
                 files=None, skip=False):
        """
        Represents a collection requirement, the versions that are available to be installed as well as any
        dependencies the collection has.

        :param namespace: The collection namespace.
        :param name: The collection name.
        :param b_path: Byte str of the path to the collection tarball if it has already been downloaded.
        :param api: The GalaxyAPI to use if the collection is from Galaxy.
        :param versions: A list of versions of the collection that are available.
        :param requirement: The version requirement string used to verify the list of versions fit the requirements.
        :param force: Whether the force flag applied to the collection.
        :param parent: The name of the parent the collection is a dependency of.
        :param metadata: The galaxy.api.CollectionVersionMetadata that has already been retrieved from the Galaxy
            server.
        :param files: The files that exist inside the collection. This is based on the FILES.json file inside the
            collection artifact.
        :param skip: Whether to skip installing the collection. Should be set if the collection is already installed
            and force is not set.
        """
        self.namespace = namespace
        self.name = name
        self.b_path = b_path
        self.api = api
        self.versions = set(versions)
        self.force = force
        self.skip = skip
        self.required_by = []

        self._metadata = metadata
        self._files = files

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
        if not self._metadata:
            if len(self.versions) > 1:
                return {}
            self._get_metadata()

        dependencies = self._metadata.dependencies

        if dependencies is None:
            return {}

        return dependencies

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

            collection_source = to_text(self.b_path, nonstring='passthru') or self.api.api_server
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
            download_url = self._metadata.download_url
            artifact_hash = self._metadata.artifact_sha256
            headers = {}
            self.api._add_auth_token(headers, download_url, required=False)

            self.b_path = _download_file(download_url, b_temp_path, artifact_hash, self.api.validate_certs,
                                         headers=headers)

        if os.path.exists(b_collection_path):
            shutil.rmtree(b_collection_path)
        os.makedirs(b_collection_path)

        try:
            with tarfile.open(self.b_path, mode='r') as collection_tar:
                files_member_obj = collection_tar.getmember('FILES.json')
                with _tarfile_extract(collection_tar, files_member_obj) as (dummy, files_obj):
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
                        _extract_tar_dir(collection_tar, file_name, b_collection_path)

        except Exception:
            # Ensure we don't leave the dir behind in case of a failure.
            shutil.rmtree(b_collection_path)

            b_namespace_path = os.path.dirname(b_collection_path)
            if not os.listdir(b_namespace_path):
                os.rmdir(b_namespace_path)

            raise

    def set_latest_version(self):
        self.versions = set([self.latest_version])
        self._get_metadata()

    def _get_metadata(self):
        if self._metadata:
            return
        self._metadata = self.api.get_collection_version_metadata(self.namespace, self.name, self.latest_version)

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
                display.warning("Failed to validate the collection requirement '%s:%s' for %s when the existing "
                                "install does not have a version set, the collection may not work."
                                % (to_text(self), req, parent))
                continue
            elif requirement == '*' or version == '*':
                continue

            if not op(LooseVersion(version), LooseVersion(requirement)):
                break
        else:
            return True

        # The loop was broken early, it does not meet all the requirements
        return False

    @staticmethod
    def from_tar(b_path, force, parent=None):
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

                with _tarfile_extract(collection_tar, member) as (dummy, member_obj):
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
        meta = CollectionVersionMetadata(namespace, name, version, None, None, meta['dependencies'])

        return CollectionRequirement(namespace, name, b_path, None, [version], version, force, parent=parent,
                                     metadata=meta, files=files)

    @staticmethod
    def from_path(b_path, force, parent=None):
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
            manifest = info['manifest_file']['collection_info']
            namespace = manifest['namespace']
            name = manifest['name']
            version = to_text(manifest['version'], errors='surrogate_or_strict')

            if not hasattr(LooseVersion(version), 'version'):
                display.warning("Collection at '%s' does not have a valid version set, falling back to '*'. Found "
                                "version: '%s'" % (to_text(b_path), version))
                version = '*'

            dependencies = manifest['dependencies']
        else:
            display.warning("Collection at '%s' does not have a MANIFEST.json file, cannot detect version."
                            % to_text(b_path))
            parent_dir, name = os.path.split(to_text(b_path, errors='surrogate_or_strict'))
            namespace = os.path.split(parent_dir)[1]

            version = '*'
            dependencies = {}

        meta = CollectionVersionMetadata(namespace, name, version, None, None, dependencies)

        files = info.get('files_file', {}).get('files', {})

        return CollectionRequirement(namespace, name, b_path, None, [version], version, force, parent=parent,
                                     metadata=meta, files=files, skip=True)

    @staticmethod
    def from_name(collection, apis, requirement, force, parent=None):
        namespace, name = collection.split('.', 1)
        galaxy_meta = None

        for api in apis:
            try:
                if not (requirement == '*' or requirement.startswith('<') or requirement.startswith('>') or
                        requirement.startswith('!=')):
                    if requirement.startswith('='):
                        requirement = requirement.lstrip('=')

                    resp = api.get_collection_version_metadata(namespace, name, requirement)

                    galaxy_meta = resp
                    versions = [resp.version]
                else:
                    resp = api.get_collection_versions(namespace, name)

                    # Galaxy supports semver but ansible-galaxy does not. We ignore any versions that don't match
                    # StrictVersion (x.y.z) and only support pre-releases if an explicit version was set (done above).
                    versions = [v for v in resp if StrictVersion.version_re.match(v)]
            except GalaxyError as err:
                if err.http_code != 404:
                    raise

                versions = []

            # Automation Hub doesn't return a 404 but an empty version list so we check that to align both AH and
            # Galaxy when the collection is not available on that server.
            if not versions:
                display.vvv("Collection '%s' is not available from server %s %s" % (collection, api.name,
                                                                                    api.api_server))
                continue

            display.vvv("Collection '%s' obtained from server %s %s" % (collection, api.name, api.api_server))
            break
        else:
            raise AnsibleError("Failed to find collection %s:%s" % (collection, requirement))

        req = CollectionRequirement(namespace, name, None, api, versions, requirement, force, parent=parent,
                                    metadata=galaxy_meta)
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


def publish_collection(collection_path, api, wait, timeout):
    """
    Publish an Ansible collection tarball into an Ansible Galaxy server.

    :param collection_path: The path to the collection tarball to publish.
    :param api: A GalaxyAPI to publish the collection to.
    :param wait: Whether to wait until the import process is complete.
    :param timeout: The time in seconds to wait for the import process to finish, 0 is indefinite.
    """
    import_uri = api.publish_collection(collection_path)

    if wait:
        # Galaxy returns a url fragment which differs between v2 and v3.  The second to last entry is
        # always the task_id, though.
        # v2: {"task": "https://galaxy-dev.ansible.com/api/v2/collection-imports/35573/"}
        # v3: {"task": "/api/automation-hub/v3/imports/collections/838d1308-a8f4-402c-95cb-7823f3806cd8/"}
        task_id = None
        for path_segment in reversed(import_uri.split('/')):
            if path_segment:
                task_id = path_segment
                break

        if not task_id:
            raise AnsibleError("Publishing the collection did not return valid task info. Cannot wait for task status. Returned task info: '%s'" % import_uri)

        display.display("Collection has been published to the Galaxy server %s %s" % (api.name, api.api_server))
        with _display_progress():
            api.wait_import_task(task_id, timeout)
        display.display("Collection has been successfully published and imported to the Galaxy server %s %s"
                        % (api.name, api.api_server))
    else:
        display.display("Collection has been pushed to the Galaxy server %s %s, not waiting until import has "
                        "completed due to --no-wait being set. Import task results can be found at %s"
                        % (api.name, api.api_server, import_uri))


def install_collections(collections, output_path, apis, validate_certs, ignore_errors, no_deps, force, force_deps):
    """
    Install Ansible collections to the path specified.

    :param collections: The collections to install, should be a list of tuples with (name, requirement, Galaxy server).
    :param output_path: The path to install the collections to.
    :param apis: A list of GalaxyAPIs to query when searching for a collection.
    :param validate_certs: Whether to validate the certificates if downloading a tarball.
    :param ignore_errors: Whether to ignore any errors when installing the collection.
    :param no_deps: Ignore any collection dependencies and only install the base requirements.
    :param force: Re-install a collection if it has already been installed.
    :param force_deps: Re-install a collection as well as its dependencies if they have already been installed.
    """
    existing_collections = _find_existing_collections(output_path)

    with _tempdir() as b_temp_path:
        display.display("Process install dependency map")
        with _display_progress():
            dependency_map = _build_dependency_map(collections, existing_collections, b_temp_path, apis,
                                                   validate_certs, force, force_deps, no_deps)

        display.display("Starting collection install process")
        with _display_progress():
            for collection in dependency_map.values():
                try:
                    collection.install(output_path, b_temp_path)
                except AnsibleError as err:
                    if ignore_errors:
                        display.warning("Failed to install collection %s but skipping due to --ignore-errors being set. "
                                        "Error: %s" % (to_text(collection), to_text(err)))
                    else:
                        raise


def validate_collection_name(name):
    """
    Validates the collection name as an input from the user or a requirements file fit the requirements.

    :param name: The input name with optional range specifier split by ':'.
    :return: The input value, required for argparse validation.
    """
    collection, dummy, dummy = name.partition(':')
    if AnsibleCollectionRef.is_valid_collection_name(collection):
        return name

    raise AnsibleError("Invalid collection name '%s', "
                       "name must be in the format <namespace>.<collection>. "
                       "Please make sure namespace and collection name contains "
                       "characters from [a-zA-Z0-9_] only." % name)


@contextmanager
def _tempdir():
    b_temp_path = tempfile.mkdtemp(dir=to_bytes(C.DEFAULT_LOCAL_TMP, errors='surrogate_or_strict'))
    yield b_temp_path
    shutil.rmtree(b_temp_path)


@contextmanager
def _tarfile_extract(tar, member):
    tar_obj = tar.extractfile(member)
    yield member, tar_obj
    tar_obj.close()


@contextmanager
def _display_progress():
    def progress(display_queue, actual_display):
        actual_display.debug("Starting display_progress display thread")
        t = threading.current_thread()

        while True:
            for c in "|/-\\":
                actual_display.display(c + "\b", newline=False)
                time.sleep(0.1)

                # Display a message from the main thread
                while True:
                    try:
                        method, args, kwargs = display_queue.get(block=False, timeout=0.1)
                    except queue.Empty:
                        break
                    else:
                        func = getattr(actual_display, method)
                        func(*args, **kwargs)

                if getattr(t, "finish", False):
                    actual_display.debug("Received end signal for display_progress display thread")
                    return

    class DisplayThread(object):

        def __init__(self, display_queue):
            self.display_queue = display_queue

        def __getattr__(self, attr):
            def call_display(*args, **kwargs):
                self.display_queue.put((attr, args, kwargs))

            return call_display

    # Temporary override the global display class with our own which add the calls to a queue for the thread to call.
    global display
    old_display = display
    try:
        display_queue = queue.Queue()
        display = DisplayThread(display_queue)
        t = threading.Thread(target=progress, args=(display_queue, old_display))
        t.daemon = True
        t.start()

        try:
            yield
        finally:
            t.finish = True
            t.join()
    except Exception:
        # The exception is re-raised so we can sure the thread is finished and not using the display anymore
        raise
    finally:
        display = old_display


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
    b_ignore_files = frozenset([(b'*.pyc', False), (b'*.retry', False), (b'.git', True),
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

                    if not _is_child_path(b_link_target, b_top_level_dir):
                        display.warning("Skipping '%s' as it is a symbolic link to a directory outside the collection"
                                        % to_text(b_abs_path))
                        continue

                manifest_entry = entry_template.copy()
                manifest_entry['name'] = rel_path
                manifest_entry['ftype'] = 'dir'

                manifest['files'].append(manifest_entry)

                if not os.path.islink(b_abs_path):
                    _walk(b_abs_path, b_top_level_dir)
            else:
                if b_item == b'galaxy.yml':
                    continue
                elif any(fnmatch.fnmatch(b_item, b_pattern) for b_pattern, root_only in b_ignore_files
                         if not root_only or root_only == is_root):
                    display.vvv("Skipping '%s' for collection build" % to_text(b_abs_path))
                    continue

                # Handling of file symlinks occur in _build_collection_tar, the manifest for a symlink is the same for
                # a normal file.
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
                    if tarinfo.type != tarfile.SYMTYPE:
                        existing_is_exec = tarinfo.mode & stat.S_IXUSR
                        tarinfo.mode = 0o0755 if existing_is_exec or tarinfo.isdir() else 0o0644
                    tarinfo.uid = tarinfo.gid = 0
                    tarinfo.uname = tarinfo.gname = ''

                    return tarinfo

                if os.path.islink(b_src_path):
                    b_link_target = os.path.realpath(b_src_path)
                    if _is_child_path(b_link_target, b_collection_path):
                        b_rel_path = os.path.relpath(b_link_target, start=os.path.dirname(b_src_path))

                        tar_info = tarfile.TarInfo(filename)
                        tar_info.type = tarfile.SYMTYPE
                        tar_info.linkname = to_native(b_rel_path, errors='surrogate_or_strict')
                        tar_info = reset_stat(tar_info)
                        tar_file.addfile(tarinfo=tar_info)

                        continue

                # Dealing with a normal file, just add it by name.
                tar_file.add(os.path.realpath(b_src_path), arcname=filename, recursive=False, filter=reset_stat)

        shutil.copy(b_tar_filepath, b_tar_path)
        collection_name = "%s.%s" % (collection_manifest['collection_info']['namespace'],
                                     collection_manifest['collection_info']['name'])
        display.display('Created collection for %s at %s' % (collection_name, to_text(b_tar_path)))


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
                req = CollectionRequirement.from_path(b_collection_path, False)
                display.vvv("Found installed collection %s:%s at '%s'" % (to_text(req), req.latest_version,
                                                                          to_text(b_collection_path)))
                collections.append(req)

    return collections


def _build_dependency_map(collections, existing_collections, b_temp_path, apis, validate_certs, force, force_deps,
                          no_deps):
    dependency_map = {}

    # First build the dependency map on the actual requirements
    for name, version, source in collections:
        _get_collection_info(dependency_map, existing_collections, name, version, source, b_temp_path, apis,
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
                                             None, b_temp_path, apis, validate_certs, force_deps,
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


def _get_collection_info(dep_map, existing_collections, collection, requirement, source, b_temp_path, apis,
                         validate_certs, force, parent=None):
    dep_msg = ""
    if parent:
        dep_msg = " - as dependency of %s" % parent
    display.vvv("Processing requirement collection '%s'%s" % (to_text(collection), dep_msg))

    b_tar_path = None
    if os.path.isfile(to_bytes(collection, errors='surrogate_or_strict')):
        display.vvvv("Collection requirement '%s' is a tar artifact" % to_text(collection))
        b_tar_path = to_bytes(collection, errors='surrogate_or_strict')
    elif urlparse(collection).scheme.lower() in ['http', 'https']:
        display.vvvv("Collection requirement '%s' is a URL to a tar artifact" % collection)
        try:
            b_tar_path = _download_file(collection, b_temp_path, None, validate_certs)
        except urllib_error.URLError as err:
            raise AnsibleError("Failed to download collection tar from '%s': %s"
                               % (to_native(collection), to_native(err)))

    if b_tar_path:
        req = CollectionRequirement.from_tar(b_tar_path, force, parent=parent)

        collection_name = to_text(req)
        if collection_name in dep_map:
            collection_info = dep_map[collection_name]
            collection_info.add_requirement(None, req.latest_version)
        else:
            collection_info = req
    else:
        validate_collection_name(collection)

        display.vvvv("Collection requirement '%s' is the name of a collection" % collection)
        if collection in dep_map:
            collection_info = dep_map[collection]
            collection_info.add_requirement(parent, requirement)
        else:
            apis = [source] if source else apis
            collection_info = CollectionRequirement.from_name(collection, apis, requirement, force, parent=parent)

    existing = [c for c in existing_collections if to_text(c) == to_text(collection_info)]
    if existing and not collection_info.force:
        # Test that the installed collection fits the requirement
        existing[0].add_requirement(parent, requirement)
        collection_info = existing[0]

    dep_map[to_text(collection_info)] = collection_info


def _download_file(url, b_path, expected_hash, validate_certs, headers=None):
    bufsize = 65536
    digest = sha256()

    urlsplit = os.path.splitext(to_text(url.rsplit('/', 1)[1]))
    b_file_name = to_bytes(urlsplit[0], errors='surrogate_or_strict')
    b_file_ext = to_bytes(urlsplit[1], errors='surrogate_or_strict')
    b_file_path = tempfile.NamedTemporaryFile(dir=b_path, prefix=b_file_name, suffix=b_file_ext, delete=False).name

    display.vvv("Downloading %s to %s" % (url, to_text(b_path)))
    # Galaxy redirs downloads to S3 which reject the request if an Authorization header is attached so don't redir that
    resp = open_url(to_native(url, errors='surrogate_or_strict'), validate_certs=validate_certs, headers=headers,
                    unredirected_headers=['Authorization'], http_agent=user_agent())

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


def _extract_tar_dir(tar, dirname, b_dest):
    """ Extracts a directory from a collection tar. """
    member_names = [to_native(dirname, errors='surrogate_or_strict')]

    # Create list of members with and without trailing separator
    if not member_names[-1].endswith(os.path.sep):
        member_names.append(member_names[-1] + os.path.sep)

    # Try all of the member names and stop on the first one that are able to successfully get
    for member in member_names:
        try:
            tar_member = tar.getmember(member)
        except KeyError:
            continue
        break
    else:
        # If we still can't find the member, raise a nice error.
        raise AnsibleError("Unable to extract '%s' from collection" % to_native(member, errors='surrogate_or_strict'))

    b_dir_path = os.path.join(b_dest, to_bytes(dirname, errors='surrogate_or_strict'))

    b_parent_path = os.path.dirname(b_dir_path)
    try:
        os.makedirs(b_parent_path, mode=0o0755)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise

    if tar_member.type == tarfile.SYMTYPE:
        b_link_path = to_bytes(tar_member.linkname, errors='surrogate_or_strict')
        if not _is_child_path(b_link_path, b_dest, link_name=b_dir_path):
            raise AnsibleError("Cannot extract symlink '%s' in collection: path points to location outside of "
                               "collection '%s'" % (to_native(dirname), b_link_path))

        os.symlink(b_link_path, b_dir_path)

    else:
        if not os.path.isdir(b_dir_path):
            os.mkdir(b_dir_path, 0o0755)


def _extract_tar_file(tar, filename, b_dest, b_temp_path, expected_hash=None):
    """ Extracts a file from a collection tar. """
    n_filename = to_native(filename, errors='surrogate_or_strict')
    with _get_tar_file_member(tar, filename) as (tar_member, tar_obj):
        if tar_member.type == tarfile.SYMTYPE:
            actual_hash = _consume_file(tar_obj)

        else:
            with tempfile.NamedTemporaryFile(dir=b_temp_path, delete=False) as tmpfile_obj:
                actual_hash = _consume_file(tar_obj, tmpfile_obj)

        if expected_hash and actual_hash != expected_hash:
            raise AnsibleError("Checksum mismatch for '%s' inside collection at '%s'"
                               % (n_filename, to_native(tar.name)))

        b_dest_filepath = os.path.abspath(os.path.join(b_dest, to_bytes(filename, errors='surrogate_or_strict')))
        b_parent_dir = os.path.dirname(b_dest_filepath)
        if not _is_child_path(b_parent_dir, b_dest):
            raise AnsibleError("Cannot extract tar entry '%s' as it will be placed outside the collection directory"
                               % to_native(filename, errors='surrogate_or_strict'))

        if not os.path.exists(b_parent_dir):
            # Seems like Galaxy does not validate if all file entries have a corresponding dir ftype entry. This check
            # makes sure we create the parent directory even if it wasn't set in the metadata.
            os.makedirs(b_parent_dir, mode=0o0755)

        if tar_member.type == tarfile.SYMTYPE:
            b_link_path = to_bytes(tar_member.linkname, errors='surrogate_or_strict')
            if not _is_child_path(b_link_path, b_dest, link_name=b_dest_filepath):
                raise AnsibleError("Cannot extract symlink '%s' in collection: path points to location outside of "
                                   "collection '%s'" % (to_native(filename), b_link_path))

            os.symlink(b_link_path, b_dest_filepath)

        else:
            shutil.move(to_bytes(tmpfile_obj.name, errors='surrogate_or_strict'), b_dest_filepath)

            # Default to rw-r--r-- and only add execute if the tar file has execute.
            tar_member = tar.getmember(to_native(filename, errors='surrogate_or_strict'))
            new_mode = 0o644
            if stat.S_IMODE(tar_member.mode) & stat.S_IXUSR:
                new_mode |= 0o0111

            os.chmod(b_dest_filepath, new_mode)


def _get_tar_file_member(tar, filename):
    n_filename = to_native(filename, errors='surrogate_or_strict')
    try:
        member = tar.getmember(n_filename)
    except KeyError:
        raise AnsibleError("Collection tar at '%s' does not contain the expected file '%s'." % (
            to_native(tar.name),
            n_filename))

    return _tarfile_extract(tar, member)


def _is_child_path(path, parent_path, link_name=None):
    """ Checks that path is a path within the parent_path specified. """
    b_path = to_bytes(path, errors='surrogate_or_strict')

    if link_name and not os.path.isabs(b_path):
        # If link_name is specified, path is the source of the link and we need to resolve the absolute path.
        b_link_dir = os.path.dirname(to_bytes(link_name, errors='surrogate_or_strict'))
        b_path = os.path.abspath(os.path.join(b_link_dir, b_path))

    b_parent_path = to_bytes(parent_path, errors='surrogate_or_strict')
    return b_path == b_parent_path or b_path.startswith(b_parent_path + to_bytes(os.path.sep))


def _consume_file(read_from, write_to=None):
    bufsize = 65536
    sha256_digest = sha256()
    data = read_from.read(bufsize)
    while data:
        if write_to is not None:
            write_to.write(data)
            write_to.flush()
        sha256_digest.update(data)
        data = read_from.read(bufsize)

    return sha256_digest.hexdigest()
