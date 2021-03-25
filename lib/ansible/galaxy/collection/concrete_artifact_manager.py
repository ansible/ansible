# -*- coding: utf-8 -*-
# Copyright: (c) 2020-2021, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""Concrete collection candidate management helper module."""

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import json
import os
import tarfile
import subprocess
from contextlib import contextmanager
from hashlib import sha256
from shutil import rmtree
from tempfile import mkdtemp

try:
    from typing import TYPE_CHECKING
except ImportError:
    TYPE_CHECKING = False

if TYPE_CHECKING:
    from typing import (
        Any,  # FIXME: !!!111
        BinaryIO, Dict, IO,
        Iterator, List, Optional,
        Set, Tuple, Type, Union,
    )

    from ansible.galaxy.dependency_resolution.dataclasses import (
        Candidate, Requirement,
    )
    from ansible.galaxy.token import GalaxyToken

from ansible.errors import AnsibleError
from ansible.galaxy import get_collections_galaxy_meta_info
from ansible.galaxy.dependency_resolution.dataclasses import _GALAXY_YAML
from ansible.galaxy.user_agent import user_agent
from ansible.module_utils._text import to_bytes, to_native, to_text
from ansible.module_utils.six.moves.urllib.error import URLError
from ansible.module_utils.six.moves.urllib.parse import urldefrag
from ansible.module_utils.six import raise_from
from ansible.module_utils.urls import open_url
from ansible.utils.display import Display

import yaml


display = Display()

MANIFEST_FILENAME = 'MANIFEST.json'


class ConcreteArtifactsManager:
    """Manager for on-disk collection artifacts.

    It is responsible for:
        * downloading remote collections from Galaxy-compatible servers and
          direct links to tarballs or SCM repositories
        * keeping track of local ones
        * keeping track of Galaxy API tokens for downloads from Galaxy'ish
          as well as the artifact hashes
        * caching all of above
        * retrieving the metadata out of the downloaded artifacts
    """

    def __init__(self, b_working_directory, validate_certs=True):
        # type: (bytes, bool) -> None
        """Initialize ConcreteArtifactsManager caches and costraints."""
        self._validate_certs = validate_certs  # type: bool
        self._artifact_cache = {}  # type: Dict[bytes, bytes]
        self._galaxy_artifact_cache = {}  # type: Dict[Union[Candidate, Requirement], bytes]
        self._artifact_meta_cache = {}  # type: Dict[bytes, Dict[str, Optional[Union[str, List[str], Dict[str, str]]]]]
        self._galaxy_collection_cache = {}  # type: Dict[Union[Candidate, Requirement], Tuple[str, str, GalaxyToken]]
        self._b_working_directory = b_working_directory  # type: bytes

    def get_galaxy_artifact_path(self, collection):
        # type: (Union[Candidate, Requirement]) -> bytes
        """Given a Galaxy-stored collection, return a cached path.

        If it's not yet on disk, this method downloads the artifact first.
        """
        try:
            return self._galaxy_artifact_cache[collection]
        except KeyError:
            pass

        try:
            url, sha256_hash, token = self._galaxy_collection_cache[collection]
        except KeyError as key_err:
            raise_from(
                RuntimeError(
                    'The is no known source for {coll!s}'.
                    format(coll=collection),
                ),
                key_err,
            )

        display.vvvv(
            "Fetching a collection tarball for '{collection!s}' from "
            'Ansible Galaxy'.format(collection=collection),
        )

        try:
            b_artifact_path = _download_file(
                url,
                self._b_working_directory,
                expected_hash=sha256_hash,
                validate_certs=self._validate_certs,
                token=token,
            )  # type: bytes
        except URLError as err:
            raise_from(
                AnsibleError(
                    'Failed to download collection tar '
                    "from '{coll_src!s}': {download_err!s}".
                    format(
                        coll_src=to_native(collection.src),
                        download_err=to_native(err),
                    ),
                ),
                err,
            )
        else:
            display.vvv(
                "Collection '{coll!s}' obtained from "
                'server {server!s} {url!s}'.format(
                    coll=collection, server=collection.src or 'Galaxy',
                    url=collection.src.api_server if collection.src is not None
                    else '',
                )
            )

        self._galaxy_artifact_cache[collection] = b_artifact_path
        return b_artifact_path

    def get_artifact_path(self, collection):
        # type: (Union[Candidate, Requirement]) -> bytes
        """Given a concrete collection pointer, return a cached path.

        If it's not yet on disk, this method downloads the artifact first.
        """
        try:
            return self._artifact_cache[collection.src]
        except KeyError:
            pass

        # NOTE: SCM needs to be special-cased as it may contain either
        # NOTE: one collection in its root, or a number of top-level
        # NOTE: collection directories instead.
        # NOTE: The idea is to store the SCM collection as unpacked
        # NOTE: directory structure under the temporary location and use
        # NOTE: a "virtual" collection that has pinned requirements on
        # NOTE: the directories under that SCM checkout that correspond
        # NOTE: to collections.
        # NOTE: This brings us to the idea that we need two separate
        # NOTE: virtual Requirement/Candidate types --
        # NOTE: (single) dir + (multidir) subdirs
        if collection.is_url:
            display.vvvv(
                "Collection requirement '{collection!s}' is a URL "
                'to a tar artifact'.format(collection=collection.fqcn),
            )
            try:
                b_artifact_path = _download_file(
                    collection.src,
                    self._b_working_directory,
                    expected_hash=None,  # NOTE: URLs don't support checksums
                    validate_certs=self._validate_certs,
                )
            except URLError as err:
                raise_from(
                    AnsibleError(
                        'Failed to download collection tar '
                        "from '{coll_src!s}': {download_err!s}".
                        format(
                            coll_src=to_native(collection.src),
                            download_err=to_native(err),
                        ),
                    ),
                    err,
                )
        elif collection.is_scm:
            b_artifact_path = _extract_collection_from_git(
                collection.src,
                collection.ver,
                self._b_working_directory,
            )
        elif collection.is_file or collection.is_dir or collection.is_subdirs:
            b_artifact_path = to_bytes(collection.src)
        else:
            # NOTE: This may happen `if collection.is_online_index_pointer`
            raise RuntimeError(
                'The artifact is of an unexpected type {art_type!s}'.
                format(art_type=collection.type)
            )

        self._artifact_cache[collection.src] = b_artifact_path
        return b_artifact_path

    def _get_direct_collection_namespace(self, collection):
        # type: (Candidate) -> Optional[str]
        return self.get_direct_collection_meta(collection)['namespace']  # type: ignore[return-value]

    def _get_direct_collection_name(self, collection):
        # type: (Candidate) -> Optional[str]
        return self.get_direct_collection_meta(collection)['name']  # type: ignore[return-value]

    def get_direct_collection_fqcn(self, collection):
        # type: (Candidate) -> Optional[str]
        """Extract FQCN from the given on-disk collection artifact.

        If the collection is virtual, ``None`` is returned instead
        of a string.
        """
        if collection.is_virtual:
            # NOTE: should it be something like "<virtual>"?
            return None

        return '.'.join((  # type: ignore[type-var]
            self._get_direct_collection_namespace(collection),  # type: ignore[arg-type]
            self._get_direct_collection_name(collection),
        ))

    def get_direct_collection_version(self, collection):
        # type: (Union[Candidate, Requirement]) -> str
        """Extract version from the given on-disk collection artifact."""
        return self.get_direct_collection_meta(collection)['version']  # type: ignore[return-value]

    def get_direct_collection_dependencies(self, collection):
        # type: (Union[Candidate, Requirement]) -> Dict[str, str]
        """Extract deps from the given on-disk collection artifact."""
        return self.get_direct_collection_meta(collection)['dependencies']  # type: ignore[return-value]

    def get_direct_collection_meta(self, collection):
        # type: (Union[Candidate, Requirement]) -> Dict[str, Optional[Union[str, Dict[str, str], List[str]]]]
        """Extract meta from the given on-disk collection artifact."""
        try:  # FIXME: use unique collection identifier as a cache key?
            return self._artifact_meta_cache[collection.src]
        except KeyError:
            b_artifact_path = self.get_artifact_path(collection)

        if collection.is_url or collection.is_file:
            collection_meta = _get_meta_from_tar(b_artifact_path)
        elif collection.is_dir:  # should we just build a coll instead?
            # FIXME: what if there's subdirs?
            try:
                collection_meta = _get_meta_from_dir(b_artifact_path)
            except LookupError as lookup_err:
                raise_from(
                    AnsibleError(
                        'Failed to find the collection dir deps: {err!s}'.
                        format(err=to_native(lookup_err)),
                    ),
                    lookup_err,
                )
        elif collection.is_scm:
            collection_meta = {
                'name': None,
                'namespace': None,
                'dependencies': {to_native(b_artifact_path): '*'},
                'version': '*',
            }
        elif collection.is_subdirs:
            collection_meta = {
                'name': None,
                'namespace': None,
                # NOTE: Dropping b_artifact_path since it's based on src anyway
                'dependencies': dict.fromkeys(
                    map(to_native, collection.namespace_collection_paths),
                    '*',
                ),
                'version': '*',
            }
        else:
            raise RuntimeError

        self._artifact_meta_cache[collection.src] = collection_meta
        return collection_meta

    def save_collection_source(self, collection, url, sha256_hash, token):
        # type: (Candidate, str, str, GalaxyToken) -> None
        """Store collection URL, SHA256 hash and Galaxy API token.

        This is a hook that is supposed to be called before attempting to
        download Galaxy-based collections with ``get_galaxy_artifact_path()``.
        """
        self._galaxy_collection_cache[collection] = url, sha256_hash, token

    @classmethod
    @contextmanager
    def under_tmpdir(
            cls,  # type: Type[ConcreteArtifactsManager]
            temp_dir_base,  # type: str
            validate_certs=True,  # type: bool
    ):  # type: (...) -> Iterator[ConcreteArtifactsManager]
        """Custom ConcreteArtifactsManager constructor with temp dir.

        This method returns a context manager that allocates and cleans
        up a temporary directory for caching the collection artifacts
        during the dependency resolution process.
        """
        # NOTE: Can't use `with tempfile.TemporaryDirectory:`
        # NOTE: because it's not in Python 2 stdlib.
        temp_path = mkdtemp(
            dir=to_bytes(temp_dir_base, errors='surrogate_or_strict'),
        )
        b_temp_path = to_bytes(temp_path, errors='surrogate_or_strict')
        try:
            yield cls(b_temp_path, validate_certs)
        finally:
            rmtree(b_temp_path)


def parse_scm(collection, version):
    """Extract name, version, path and subdir out of the SCM pointer."""
    if ',' in collection:
        collection, version = collection.split(',', 1)
    elif version == '*' or not version:
        version = 'HEAD'

    if collection.startswith('git+'):
        path = collection[4:]
    else:
        path = collection

    path, fragment = urldefrag(path)
    fragment = fragment.strip(os.path.sep)

    if path.endswith(os.path.sep + '.git'):
        name = path.split(os.path.sep)[-2]
    elif '://' not in path and '@' not in path:
        name = path
    else:
        name = path.split('/')[-1]
        if name.endswith('.git'):
            name = name[:-4]

    return name, version, path, fragment


def _extract_collection_from_git(repo_url, coll_ver, b_path):
    name, version, git_url, fragment = parse_scm(repo_url, coll_ver)
    b_checkout_path = mkdtemp(
        dir=b_path,
        prefix=to_bytes(name, errors='surrogate_or_strict'),
    )  # type: bytes
    git_clone_cmd = 'git', 'clone', git_url, to_text(b_checkout_path)
    # FIXME: '--depth', '1', '--branch', version
    try:
        subprocess.check_call(git_clone_cmd)
    except subprocess.CalledProcessError as proc_err:
        raise_from(
            AnsibleError(  # should probably be LookupError
                'Failed to clone a Git repository from `{repo_url!s}`.'.
                format(repo_url=to_native(git_url)),
            ),
            proc_err,
        )

    git_switch_cmd = 'git', 'checkout', to_text(version)
    try:
        subprocess.check_call(git_switch_cmd, cwd=b_checkout_path)
    except subprocess.CalledProcessError as proc_err:
        raise_from(
            AnsibleError(  # should probably be LookupError
                'Failed to switch a cloned Git repo `{repo_url!s}` '
                'to the requested revision `{commitish!s}`.'.
                format(
                    commitish=to_native(version),
                    repo_url=to_native(git_url),
                ),
            ),
            proc_err,
        )

    return (
        os.path.join(b_checkout_path, to_bytes(fragment))
        if fragment else b_checkout_path
    )


# FIXME: use random subdirs while preserving the file names
def _download_file(url, b_path, expected_hash, validate_certs, token=None):
    # type: (str, bytes, Optional[str], bool, GalaxyToken) -> bytes
    # ^ NOTE: used in download and verify_collections ^
    b_tarball_name = to_bytes(
        url.rsplit('/', 1)[1], errors='surrogate_or_strict',
    )
    b_file_name = b_tarball_name[:-len('.tar.gz')]

    b_tarball_dir = mkdtemp(
        dir=b_path,
        prefix=b'-'.join((b_file_name, b'')),
    )  # type: bytes

    b_file_path = os.path.join(b_tarball_dir, b_tarball_name)

    display.display("Downloading %s to %s" % (url, to_text(b_tarball_dir)))
    # NOTE: Galaxy redirects downloads to S3 which rejects the request
    # NOTE: if an Authorization header is attached so don't redirect it
    resp = open_url(
        to_native(url, errors='surrogate_or_strict'),
        validate_certs=validate_certs,
        headers=None if token is None else token.headers(),
        unredirected_headers=['Authorization'], http_agent=user_agent(),
    )

    with open(b_file_path, 'wb') as download_file:  # type: BinaryIO
        actual_hash = _consume_file(resp, write_to=download_file)

    if expected_hash:
        display.vvvv(
            'Validating downloaded file hash {actual_hash!s} with '
            'expected hash {expected_hash!s}'.
            format(actual_hash=actual_hash, expected_hash=expected_hash)
        )
        if expected_hash != actual_hash:
            raise AnsibleError('Mismatch artifact hash with downloaded file')

    return b_file_path


def _consume_file(read_from, write_to=None):
    # type: (BinaryIO, BinaryIO) -> str
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


def _normalize_galaxy_yml_manifest(
        galaxy_yml,  # type: Dict[str, Optional[Union[str, List[str], Dict[str, str]]]]
        b_galaxy_yml_path,  # type: bytes
):
    # type: (...) -> Dict[str, Optional[Union[str, List[str], Dict[str, str]]]]
    galaxy_yml_schema = (
        get_collections_galaxy_meta_info()
    )  # type: List[Dict[str, Any]]  # FIXME: <--
    # FIXME: 👆maybe precise type: List[Dict[str, Union[bool, str, List[str]]]]

    mandatory_keys = set()
    string_keys = set()  # type: Set[str]
    list_keys = set()  # type: Set[str]
    dict_keys = set()  # type: Set[str]

    for info in galaxy_yml_schema:
        if info.get('required', False):
            mandatory_keys.add(info['key'])

        key_list_type = {
            'str': string_keys,
            'list': list_keys,
            'dict': dict_keys,
        }[info.get('type', 'str')]
        key_list_type.add(info['key'])

    all_keys = frozenset(list(mandatory_keys) + list(string_keys) + list(list_keys) + list(dict_keys))

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
            galaxy_yml[optional_list] = [list_val]  # type: ignore[list-item]

    for optional_dict in dict_keys:
        if optional_dict not in galaxy_yml:
            galaxy_yml[optional_dict] = {}

    # NOTE: `version: null` is only allowed for `galaxy.yml`
    # NOTE: and not `MANIFEST.json`. The use-case for it is collections
    # NOTE: that generate the version from Git before building a
    # NOTE: distributable tarball artifact.
    if not galaxy_yml.get('version'):
        galaxy_yml['version'] = '*'

    return galaxy_yml


def _get_meta_from_dir(
        b_path,  # type: bytes
):  # type: (...) -> Dict[str, Optional[Union[str, List[str], Dict[str, str]]]]
    try:
        return _get_meta_from_installed_dir(b_path)
    except LookupError:
        return _get_meta_from_src_dir(b_path)


def _get_meta_from_src_dir(
        b_path,  # type: bytes
):  # type: (...) -> Dict[str, Optional[Union[str, List[str], Dict[str, str]]]]
    galaxy_yml = os.path.join(b_path, _GALAXY_YAML)
    if not os.path.isfile(galaxy_yml):
        raise LookupError(
            "The collection galaxy.yml path '{path!s}' does not exist.".
            format(path=to_native(galaxy_yml))
        )

    with open(galaxy_yml, 'rb') as manifest_file_obj:
        try:
            manifest = yaml.safe_load(manifest_file_obj)
        except yaml.error.YAMLError as yaml_err:
            raise_from(
                AnsibleError(
                    "Failed to parse the galaxy.yml at '{path!s}' with "
                    'the following error:\n{err_txt!s}'.
                    format(
                        path=to_native(galaxy_yml),
                        err_txt=to_native(yaml_err),
                    ),
                ),
                yaml_err,
            )

    return _normalize_galaxy_yml_manifest(manifest, galaxy_yml)


def _get_json_from_installed_dir(
        b_path,  # type: bytes
        filename,  # type: str
):  # type: (...) -> Dict

    b_json_filepath = os.path.join(b_path, to_bytes(filename, errors='surrogate_or_strict'))

    try:
        with open(b_json_filepath, 'rb') as manifest_fd:
            b_json_text = manifest_fd.read()
    except (IOError, OSError):
        raise LookupError(
            "The collection {manifest!s} path '{path!s}' does not exist.".
            format(
                manifest=filename,
                path=to_native(b_json_filepath),
            )
        )

    manifest_txt = to_text(b_json_text, errors='surrogate_or_strict')

    try:
        manifest = json.loads(manifest_txt)
    except ValueError:
        raise AnsibleError(
            'Collection tar file member {member!s} does not '
            'contain a valid json string.'.
            format(member=filename),
        )

    return manifest


def _get_meta_from_installed_dir(
        b_path,  # type: bytes
):  # type: (...) -> Dict[str, Optional[Union[str, List[str], Dict[str, str]]]]
    manifest = _get_json_from_installed_dir(b_path, MANIFEST_FILENAME)
    collection_info = manifest['collection_info']

    version = collection_info.get('version')
    if not version:
        raise AnsibleError(
            u'Collection metadata file `{manifest_filename!s}` at `{meta_file!s}` is expected '
            u'to have a valid SemVer version value but got {version!s}'.
            format(
                manifest_filename=MANIFEST_FILENAME,
                meta_file=to_text(b_path),
                version=to_text(repr(version)),
            ),
        )

    return collection_info


def _get_meta_from_tar(
        b_path,  # type: bytes
):  # type: (...) -> Dict[str, Optional[Union[str, List[str], Dict[str, str]]]]
    if not tarfile.is_tarfile(b_path):
        raise AnsibleError(
            "Collection artifact at '{path!s}' is not a valid tar file.".
            format(path=to_native(b_path)),
        )

    with tarfile.open(b_path, mode='r') as collection_tar:  # type: tarfile.TarFile
        try:
            member = collection_tar.getmember(MANIFEST_FILENAME)
        except KeyError:
            raise AnsibleError(
                "Collection at '{path!s}' does not contain the "
                'required file {manifest_file!s}.'.
                format(
                    path=to_native(b_path),
                    manifest_file=MANIFEST_FILENAME,
                ),
            )

        with _tarfile_extract(collection_tar, member) as (_member, member_obj):
            if member_obj is None:
                raise AnsibleError(
                    'Collection tar file does not contain '
                    'member {member!s}'.format(member=MANIFEST_FILENAME),
                )

            text_content = to_text(
                member_obj.read(),
                errors='surrogate_or_strict',
            )

            try:
                manifest = json.loads(text_content)
            except ValueError:
                raise AnsibleError(
                    'Collection tar file member {member!s} does not '
                    'contain a valid json string.'.
                    format(member=MANIFEST_FILENAME),
                )
            return manifest['collection_info']


@contextmanager
def _tarfile_extract(
        tar,  # type: tarfile.TarFile
        member,  # type: tarfile.TarInfo
):
    # type: (...) -> Iterator[Tuple[tarfile.TarInfo, Optional[IO[bytes]]]]
    tar_obj = tar.extractfile(member)
    try:
        yield member, tar_obj
    finally:
        if tar_obj is not None:
            tar_obj.close()
