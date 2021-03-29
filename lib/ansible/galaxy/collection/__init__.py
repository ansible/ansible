# -*- coding: utf-8 -*-
# Copyright: (c) 2019-2021, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""Installed collections management package."""

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import errno
import fnmatch
import functools
import json
import os
import shutil
import stat
import sys
import tarfile
import tempfile
import threading
import time
import yaml

from collections import namedtuple
from contextlib import contextmanager
from distutils.version import LooseVersion
from hashlib import sha256
from io import BytesIO
from itertools import chain
from yaml.error import YAMLError

# NOTE: Adding type ignores is a hack for mypy to shut up wrt bug #1153
try:
    import queue  # type: ignore[import]
except ImportError:  # Python 2
    import Queue as queue  # type: ignore[import,no-redef]

try:
    # NOTE: It's in Python 3 stdlib and can be installed on Python 2
    # NOTE: via `pip install typing`. Unnecessary in runtime.
    # NOTE: `TYPE_CHECKING` is True during mypy-typecheck-time.
    from typing import TYPE_CHECKING
except ImportError:
    TYPE_CHECKING = False

if TYPE_CHECKING:
    from typing import Dict, Iterable, List, Optional, Text, Union
    if sys.version_info[:2] >= (3, 8):
        from typing import Literal
    else:  # Python 2 + Python 3.4-3.7
        from typing_extensions import Literal

    from ansible.galaxy.api import GalaxyAPI
    from ansible.galaxy.collection.concrete_artifact_manager import (
        ConcreteArtifactsManager,
    )

    ManifestKeysType = Literal[
        'collection_info', 'file_manifest_file', 'format',
    ]
    FileMetaKeysType = Literal[
        'name',
        'ftype',
        'chksum_type',
        'chksum_sha256',
        'format',
    ]
    CollectionInfoKeysType = Literal[
        # collection meta:
        'namespace', 'name', 'version',
        'authors', 'readme',
        'tags', 'description',
        'license', 'license_file',
        'dependencies',
        'repository', 'documentation',
        'homepage', 'issues',

        # files meta:
        FileMetaKeysType,
    ]
    ManifestValueType = Dict[
        CollectionInfoKeysType,
        Optional[
            Union[
                int, str,  # scalars, like name/ns, schema version
                List[str],  # lists of scalars, like tags
                Dict[str, str],  # deps map
            ],
        ],
    ]
    CollectionManifestType = Dict[ManifestKeysType, ManifestValueType]
    FileManifestEntryType = Dict[FileMetaKeysType, Optional[Union[str, int]]]
    FilesManifestType = Dict[
        Literal['files', 'format'],
        Union[List[FileManifestEntryType], int],
    ]

import ansible.constants as C
from ansible.errors import AnsibleError
from ansible.galaxy import get_collections_galaxy_meta_info
from ansible.galaxy.collection.concrete_artifact_manager import (
    _consume_file,
    _download_file,
    _get_json_from_installed_dir,
    _get_meta_from_src_dir,
    _tarfile_extract,
)
from ansible.galaxy.collection.galaxy_api_proxy import MultiGalaxyAPIProxy
from ansible.galaxy.dependency_resolution import (
    build_collection_dependency_resolver,
)
from ansible.galaxy.dependency_resolution.dataclasses import (
    Candidate, Requirement, _is_installed_collection_dir,
)
from ansible.galaxy.dependency_resolution.errors import (
    CollectionDependencyResolutionImpossible,
)
from ansible.galaxy.dependency_resolution.versioning import meets_requirements
from ansible.module_utils.six import raise_from
from ansible.module_utils._text import to_bytes, to_native, to_text
from ansible.utils.collection_loader import AnsibleCollectionRef
from ansible.utils.display import Display
from ansible.utils.hashing import secure_hash, secure_hash_s
from ansible.utils.version import SemanticVersion


display = Display()

MANIFEST_FORMAT = 1
MANIFEST_FILENAME = 'MANIFEST.json'

ModifiedContent = namedtuple('ModifiedContent', ['filename', 'expected', 'installed'])


# FUTURE: expose actual verify result details for a collection on this object, maybe reimplement as dataclass on py3.8+
class CollectionVerifyResult:
    def __init__(self, collection_name):  # type: (str) -> None
        self.collection_name = collection_name  # type: str
        self.success = True  # type: bool


def verify_local_collection(
        local_collection, remote_collection,
        artifacts_manager,
):  # type: (Candidate, Optional[Candidate], ConcreteArtifactsManager) -> CollectionVerifyResult
    """Verify integrity of the locally installed collection.

    :param local_collection: Collection being checked.
    :param remote_collection: Upstream collection (optional, if None, only verify local artifact)
    :param artifacts_manager: Artifacts manager.
    :return: a collection verify result object.
    """
    result = CollectionVerifyResult(local_collection.fqcn)

    b_collection_path = to_bytes(
        local_collection.src, errors='surrogate_or_strict',
    )

    display.display("Verifying '{coll!s}'.".format(coll=local_collection))
    display.display(
        u"Installed collection found at '{path!s}'".
        format(path=to_text(local_collection.src)),
    )

    modified_content = []  # type: List[ModifiedContent]

    verify_local_only = remote_collection is None
    if verify_local_only:
        # partial away the local FS detail so we can just ask generically during validation
        get_json_from_validation_source = functools.partial(_get_json_from_installed_dir, b_collection_path)
        get_hash_from_validation_source = functools.partial(_get_file_hash, b_collection_path)

        # since we're not downloading this, just seed it with the value from disk
        manifest_hash = get_hash_from_validation_source(MANIFEST_FILENAME)
    else:
        # fetch remote
        b_temp_tar_path = (  # NOTE: AnsibleError is raised on URLError
            artifacts_manager.get_artifact_path
            if remote_collection.is_concrete_artifact
            else artifacts_manager.get_galaxy_artifact_path
        )(remote_collection)

        display.vvv(
            u"Remote collection cached as '{path!s}'".format(path=to_text(b_temp_tar_path))
        )

        # partial away the tarball details so we can just ask generically during validation
        get_json_from_validation_source = functools.partial(_get_json_from_tar_file, b_temp_tar_path)
        get_hash_from_validation_source = functools.partial(_get_tar_file_hash, b_temp_tar_path)

        # Compare installed version versus requirement version
        if local_collection.ver != remote_collection.ver:
            err = (
                "{local_fqcn!s} has the version '{local_ver!s}' but "
                "is being compared to '{remote_ver!s}'".format(
                    local_fqcn=local_collection.fqcn,
                    local_ver=local_collection.ver,
                    remote_ver=remote_collection.ver,
                )
            )
            display.display(err)
            result.success = False
            return result

        # Verify the downloaded manifest hash matches the installed copy before verifying the file manifest
        manifest_hash = get_hash_from_validation_source(MANIFEST_FILENAME)
        _verify_file_hash(b_collection_path, MANIFEST_FILENAME, manifest_hash, modified_content)

    display.display('MANIFEST.json hash: {manifest_hash}'.format(manifest_hash=manifest_hash))

    manifest = get_json_from_validation_source(MANIFEST_FILENAME)

    # Use the manifest to verify the file manifest checksum
    file_manifest_data = manifest['file_manifest_file']
    file_manifest_filename = file_manifest_data['name']
    expected_hash = file_manifest_data['chksum_%s' % file_manifest_data['chksum_type']]

    # Verify the file manifest before using it to verify individual files
    _verify_file_hash(b_collection_path, file_manifest_filename, expected_hash, modified_content)
    file_manifest = get_json_from_validation_source(file_manifest_filename)

    # Use the file manifest to verify individual file checksums
    for manifest_data in file_manifest['files']:
        if manifest_data['ftype'] == 'file':
            expected_hash = manifest_data['chksum_%s' % manifest_data['chksum_type']]
            _verify_file_hash(b_collection_path, manifest_data['name'], expected_hash, modified_content)

    if modified_content:
        result.success = False
        display.display(
            'Collection {fqcn!s} contains modified content '
            'in the following files:'.
            format(fqcn=to_text(local_collection.fqcn)),
        )
        for content_change in modified_content:
            display.display('    %s' % content_change.filename)
            display.v("    Expected: %s\n    Found: %s" % (content_change.expected, content_change.installed))
    else:
        what = "are internally consistent with its manifest" if verify_local_only else "match the remote collection"
        display.display(
            "Successfully verified that checksums for '{coll!s}' {what!s}.".
            format(coll=local_collection, what=what),
        )

    return result


def build_collection(u_collection_path, u_output_path, force):
    # type: (Text, Text, bool) -> Text
    """Creates the Ansible collection artifact in a .tar.gz file.

    :param u_collection_path: The path to the collection to build. This should be the directory that contains the
        galaxy.yml file.
    :param u_output_path: The path to create the collection build artifact. This should be a directory.
    :param force: Whether to overwrite an existing collection build artifact or fail.
    :return: The path to the collection build artifact.
    """
    b_collection_path = to_bytes(u_collection_path, errors='surrogate_or_strict')
    try:
        collection_meta = _get_meta_from_src_dir(b_collection_path)
    except LookupError as lookup_err:
        raise_from(AnsibleError(to_native(lookup_err)), lookup_err)

    collection_manifest = _build_manifest(**collection_meta)
    file_manifest = _build_files_manifest(
        b_collection_path,
        collection_meta['namespace'],  # type: ignore[arg-type]
        collection_meta['name'],  # type: ignore[arg-type]
        collection_meta['build_ignore'],  # type: ignore[arg-type]
    )

    artifact_tarball_file_name = '{ns!s}-{name!s}-{ver!s}.tar.gz'.format(
        name=collection_meta['name'],
        ns=collection_meta['namespace'],
        ver=collection_meta['version'],
    )
    b_collection_output = os.path.join(
        to_bytes(u_output_path),
        to_bytes(artifact_tarball_file_name, errors='surrogate_or_strict'),
    )

    if os.path.exists(b_collection_output):
        if os.path.isdir(b_collection_output):
            raise AnsibleError("The output collection artifact '%s' already exists, "
                               "but is a directory - aborting" % to_native(b_collection_output))
        elif not force:
            raise AnsibleError("The file '%s' already exists. You can use --force to re-create "
                               "the collection artifact." % to_native(b_collection_output))

    collection_output = _build_collection_tar(b_collection_path, b_collection_output, collection_manifest, file_manifest)
    return collection_output


def download_collections(
        collections,  # type: Iterable[Requirement]
        output_path,  # type: str
        apis,  # type: Iterable[GalaxyAPI]
        no_deps,  # type: bool
        allow_pre_release,  # type: bool
        artifacts_manager,  # type: ConcreteArtifactsManager
):  # type: (...) -> None
    """Download Ansible collections as their tarball from a Galaxy server to the path specified and creates a requirements
    file of the downloaded requirements to be used for an install.

    :param collections: The collections to download, should be a list of tuples with (name, requirement, Galaxy Server).
    :param output_path: The path to download the collections to.
    :param apis: A list of GalaxyAPIs to query when search for a collection.
    :param validate_certs: Whether to validate the certificate if downloading a tarball from a non-Galaxy host.
    :param no_deps: Ignore any collection dependencies and only download the base requirements.
    :param allow_pre_release: Do not ignore pre-release versions when selecting the latest.
    """
    with _display_progress("Process download dependency map"):
        dep_map = _resolve_depenency_map(
            set(collections),
            galaxy_apis=apis,
            preferred_candidates=None,
            concrete_artifacts_manager=artifacts_manager,
            no_deps=no_deps,
            allow_pre_release=allow_pre_release,
            upgrade=False,
        )

    b_output_path = to_bytes(output_path, errors='surrogate_or_strict')

    requirements = []
    with _display_progress(
            "Starting collection download process to '{path!s}'".
            format(path=output_path),
    ):
        for fqcn, concrete_coll_pin in dep_map.copy().items():  # FIXME: move into the provider
            if concrete_coll_pin.is_virtual:
                display.display(
                    'Virtual collection {coll!s} is not downloadable'.
                    format(coll=to_text(concrete_coll_pin)),
                )
                continue

            display.display(
                u"Downloading collection '{coll!s}' to '{path!s}'".
                format(coll=to_text(concrete_coll_pin), path=to_text(b_output_path)),
            )

            b_src_path = (
                artifacts_manager.get_artifact_path
                if concrete_coll_pin.is_concrete_artifact
                else artifacts_manager.get_galaxy_artifact_path
            )(concrete_coll_pin)

            b_dest_path = os.path.join(
                b_output_path,
                os.path.basename(b_src_path),
            )

            if concrete_coll_pin.is_dir:
                b_dest_path = to_bytes(
                    build_collection(
                        to_text(b_src_path, errors='surrogate_or_strict'),
                        to_text(output_path, errors='surrogate_or_strict'),
                        force=True,
                    ),
                    errors='surrogate_or_strict',
                )
            else:
                shutil.copy(to_native(b_src_path), to_native(b_dest_path))

            display.display(
                "Collection '{coll!s}' was downloaded successfully".
                format(coll=concrete_coll_pin),
            )
            requirements.append({
                # FIXME: Consider using a more specific upgraded format
                # FIXME: having FQCN in the name field, with src field
                # FIXME: pointing to the file path, and explicitly set
                # FIXME: type. If version and name are set, it'd
                # FIXME: perform validation against the actual metadata
                # FIXME: in the artifact src points at.
                'name': to_native(os.path.basename(b_dest_path)),
                'version': concrete_coll_pin.ver,
            })

        requirements_path = os.path.join(output_path, 'requirements.yml')
        b_requirements_path = to_bytes(
            requirements_path, errors='surrogate_or_strict',
        )
        display.display(
            u'Writing requirements.yml file of downloaded collections '
            "to '{path!s}'".format(path=to_text(requirements_path)),
        )
        yaml_bytes = to_bytes(
            yaml.safe_dump({'collections': requirements}),
            errors='surrogate_or_strict',
        )
        with open(b_requirements_path, mode='wb') as req_fd:
            req_fd.write(yaml_bytes)


def publish_collection(collection_path, api, wait, timeout):
    """Publish an Ansible collection tarball into an Ansible Galaxy server.

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

        with _display_progress(
                "Collection has been published to the Galaxy server "
                "{api.name!s} {api.api_server!s}".format(api=api),
        ):
            api.wait_import_task(task_id, timeout)
        display.display("Collection has been successfully published and imported to the Galaxy server %s %s"
                        % (api.name, api.api_server))
    else:
        display.display("Collection has been pushed to the Galaxy server %s %s, not waiting until import has "
                        "completed due to --no-wait being set. Import task results can be found at %s"
                        % (api.name, api.api_server, import_uri))


def install_collections(
        collections,  # type: Iterable[Requirement]
        output_path,  # type: str
        apis,  # type: Iterable[GalaxyAPI]
        ignore_errors,  # type: bool
        no_deps,  # type: bool
        force,  # type: bool
        force_deps,  # type: bool
        upgrade,  # type: bool
        allow_pre_release,  # type: bool
        artifacts_manager,  # type: ConcreteArtifactsManager
):  # type: (...) -> None
    """Install Ansible collections to the path specified.

    :param collections: The collections to install.
    :param output_path: The path to install the collections to.
    :param apis: A list of GalaxyAPIs to query when searching for a collection.
    :param validate_certs: Whether to validate the certificates if downloading a tarball.
    :param ignore_errors: Whether to ignore any errors when installing the collection.
    :param no_deps: Ignore any collection dependencies and only install the base requirements.
    :param force: Re-install a collection if it has already been installed.
    :param force_deps: Re-install a collection as well as its dependencies if they have already been installed.
    """
    existing_collections = {
        Requirement(coll.fqcn, coll.ver, coll.src, coll.type)
        for coll in find_existing_collections(output_path, artifacts_manager)
    }

    unsatisfied_requirements = set(
        chain.from_iterable(
            (
                Requirement.from_dir_path(sub_coll, artifacts_manager)
                for sub_coll in (
                    artifacts_manager.
                    get_direct_collection_dependencies(install_req).
                    keys()
                )
            )
            if install_req.is_subdirs else (install_req, )
            for install_req in collections
        ),
    )
    requested_requirements_names = {req.fqcn for req in unsatisfied_requirements}

    # NOTE: Don't attempt to reevaluate already installed deps
    # NOTE: unless `--force` or `--force-with-deps` is passed
    unsatisfied_requirements -= set() if force or force_deps else {
        req
        for req in unsatisfied_requirements
        for exs in existing_collections
        if req.fqcn == exs.fqcn and meets_requirements(exs.ver, req.ver)
    }

    if not unsatisfied_requirements and not upgrade:
        display.display(
            'Nothing to do. All requested collections are already '
            'installed. If you want to reinstall them, '
            'consider using `--force`.'
        )
        return

    # FIXME: This probably needs to be improved to
    # FIXME: properly match differing src/type.
    existing_non_requested_collections = {
        coll for coll in existing_collections
        if coll.fqcn not in requested_requirements_names
    }

    preferred_requirements = (
        [] if force_deps
        else existing_non_requested_collections if force
        else existing_collections
    )
    preferred_collections = {
        Candidate(coll.fqcn, coll.ver, coll.src, coll.type)
        for coll in preferred_requirements
    }
    with _display_progress("Process install dependency map"):
        dependency_map = _resolve_depenency_map(
            collections,
            galaxy_apis=apis,
            preferred_candidates=preferred_collections,
            concrete_artifacts_manager=artifacts_manager,
            no_deps=no_deps,
            allow_pre_release=allow_pre_release,
            upgrade=upgrade,
        )

    with _display_progress("Starting collection install process"):
        for fqcn, concrete_coll_pin in dependency_map.items():
            if concrete_coll_pin.is_virtual:
                display.vvvv(
                    "Skipping '{coll!s}' as it is virtual".
                    format(coll=to_text(concrete_coll_pin)),
                )
                continue

            if concrete_coll_pin in preferred_collections:
                display.display(
                    "Skipping '{coll!s}' as it is already installed".
                    format(coll=to_text(concrete_coll_pin)),
                )
                continue

            try:
                install(concrete_coll_pin, output_path, artifacts_manager)
            except AnsibleError as err:
                if ignore_errors:
                    display.warning(
                        'Failed to install collection {coll!s} but skipping '
                        'due to --ignore-errors being set. Error: {error!s}'.
                        format(
                            coll=to_text(concrete_coll_pin),
                            error=to_text(err),
                        )
                    )
                else:
                    raise


# NOTE: imported in ansible.cli.galaxy
def validate_collection_name(name):  # type: (str) -> str
    """Validates the collection name as an input from the user or a requirements file fit the requirements.

    :param name: The input name with optional range specifier split by ':'.
    :return: The input value, required for argparse validation.
    """
    collection, dummy, dummy = name.partition(':')
    if AnsibleCollectionRef.is_valid_collection_name(collection):
        return name

    raise AnsibleError("Invalid collection name '%s', "
                       "name must be in the format <namespace>.<collection>. \n"
                       "Please make sure namespace and collection name contains "
                       "characters from [a-zA-Z0-9_] only." % name)


# NOTE: imported in ansible.cli.galaxy
def validate_collection_path(collection_path):  # type: (str) -> str
    """Ensure a given path ends with 'ansible_collections'

    :param collection_path: The path that should end in 'ansible_collections'
    :return: collection_path ending in 'ansible_collections' if it does not already.
    """

    if os.path.split(collection_path)[1] != 'ansible_collections':
        return os.path.join(collection_path, 'ansible_collections')

    return collection_path


def verify_collections(
        collections,  # type: Iterable[Requirement]
        search_paths,  # type: Iterable[str]
        apis,  # type: Iterable[GalaxyAPI]
        ignore_errors,  # type: bool
        local_verify_only,  # type: bool
        artifacts_manager,  # type: ConcreteArtifactsManager
):  # type: (...) -> List[CollectionVerifyResult]
    r"""Verify the integrity of locally installed collections.

    :param collections: The collections to check.
    :param search_paths: Locations for the local collection lookup.
    :param apis: A list of GalaxyAPIs to query when searching for a collection.
    :param ignore_errors: Whether to ignore any errors when verifying the collection.
    :param local_verify_only: When True, skip downloads and only verify local manifests.
    :param artifacts_manager: Artifacts manager.
    :return: list of CollectionVerifyResult objects describing the results of each collection verification
    """
    results = []  # type: List[CollectionVerifyResult]

    api_proxy = MultiGalaxyAPIProxy(apis, artifacts_manager)

    with _display_progress():
        for collection in collections:
            try:
                if collection.is_concrete_artifact:
                    raise AnsibleError(
                        message="'{coll_type!s}' type is not supported. "
                        'The format namespace.name is expected.'.
                        format(coll_type=collection.type)
                    )

                # NOTE: Verify local collection exists before
                # NOTE: downloading its source artifact from
                # NOTE: a galaxy server.
                default_err = 'Collection %s is not installed in any of the collection paths.' % collection.fqcn
                for search_path in search_paths:
                    b_search_path = to_bytes(
                        os.path.join(
                            search_path,
                            collection.namespace, collection.name,
                        ),
                        errors='surrogate_or_strict',
                    )
                    if not os.path.isdir(b_search_path):
                        continue
                    if not _is_installed_collection_dir(b_search_path):
                        default_err = (
                            "Collection %s does not have a MANIFEST.json. "
                            "A MANIFEST.json is expected if the collection has been built "
                            "and installed via ansible-galaxy" % collection.fqcn
                        )
                        continue

                    local_collection = Candidate.from_dir_path(
                        b_search_path, artifacts_manager,
                    )
                    break
                else:
                    raise AnsibleError(message=default_err)

                if local_verify_only:
                    remote_collection = None
                else:
                    remote_collection = Candidate(
                        collection.fqcn,
                        collection.ver if collection.ver != '*'
                        else local_collection.ver,
                        None, 'galaxy',
                    )

                    # Download collection on a galaxy server for comparison
                    try:
                        # NOTE: Trigger the lookup. If found, it'll cache
                        # NOTE: download URL and token in artifact manager.
                        api_proxy.get_collection_version_metadata(
                            remote_collection,
                        )
                    except AnsibleError as e:  # FIXME: does this actually emit any errors?
                        # FIXME: extract the actual message and adjust this:
                        expected_error_msg = (
                            'Failed to find collection {coll.fqcn!s}:{coll.ver!s}'.
                            format(coll=collection)
                        )
                        if e.message == expected_error_msg:
                            raise AnsibleError(
                                'Failed to find remote collection '
                                "'{coll!s}' on any of the galaxy servers".
                                format(coll=collection)
                            )
                        raise

                result = verify_local_collection(
                    local_collection, remote_collection,
                    artifacts_manager,
                )

                results.append(result)

            except AnsibleError as err:
                if ignore_errors:
                    display.warning(
                        "Failed to verify collection '{coll!s}' but skipping "
                        'due to --ignore-errors being set. '
                        'Error: {err!s}'.
                        format(coll=collection, err=to_text(err)),
                    )
                else:
                    raise

    return results


@contextmanager
def _tempdir():
    b_temp_path = tempfile.mkdtemp(dir=to_bytes(C.DEFAULT_LOCAL_TMP, errors='surrogate_or_strict'))
    try:
        yield b_temp_path
    finally:
        shutil.rmtree(b_temp_path)


@contextmanager
def _display_progress(msg=None):
    config_display = C.GALAXY_DISPLAY_PROGRESS
    display_wheel = sys.stdout.isatty() if config_display is None else config_display

    global display
    if msg is not None:
        display.display(msg)

    if not display_wheel:
        yield
        return

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


def _verify_file_hash(b_path, filename, expected_hash, error_queue):
    b_file_path = to_bytes(os.path.join(to_text(b_path), filename), errors='surrogate_or_strict')

    if not os.path.isfile(b_file_path):
        actual_hash = None
    else:
        with open(b_file_path, mode='rb') as file_object:
            actual_hash = _consume_file(file_object)

    if expected_hash != actual_hash:
        error_queue.append(ModifiedContent(filename=filename, expected=expected_hash, installed=actual_hash))


def _build_files_manifest(b_collection_path, namespace, name, ignore_patterns):
    # type: (bytes, str, str, List[str]) -> FilesManifestType
    # We always ignore .pyc and .retry files as well as some well known version control directories. The ignore
    # patterns can be extended by the build_ignore key in galaxy.yml
    b_ignore_patterns = [
        b'galaxy.yml',
        b'galaxy.yaml',
        b'.git',
        b'*.pyc',
        b'*.retry',
        b'tests/output',  # Ignore ansible-test result output directory.
        to_bytes('{0}-{1}-*.tar.gz'.format(namespace, name)),  # Ignores previously built artifacts in the root dir.
    ]
    b_ignore_patterns += [to_bytes(p) for p in ignore_patterns]
    b_ignore_dirs = frozenset([b'CVS', b'.bzr', b'.hg', b'.git', b'.svn', b'__pycache__', b'.tox'])

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
    }  # type: FilesManifestType

    def _walk(b_path, b_top_level_dir):
        for b_item in os.listdir(b_path):
            b_abs_path = os.path.join(b_path, b_item)
            b_rel_base_dir = b'' if b_path == b_top_level_dir else b_path[len(b_top_level_dir) + 1:]
            b_rel_path = os.path.join(b_rel_base_dir, b_item)
            rel_path = to_text(b_rel_path, errors='surrogate_or_strict')

            if os.path.isdir(b_abs_path):
                if any(b_item == b_path for b_path in b_ignore_dirs) or \
                        any(fnmatch.fnmatch(b_rel_path, b_pattern) for b_pattern in b_ignore_patterns):
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
                if any(fnmatch.fnmatch(b_rel_path, b_pattern) for b_pattern in b_ignore_patterns):
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


# FIXME: accept a dict produced from `galaxy.yml` instead of separate args
def _build_manifest(namespace, name, version, authors, readme, tags, description, license_file,
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
            'license': kwargs['license'],
            'license_file': license_file or None,  # Handle galaxy.yml having an empty string (None)
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


def _build_collection_tar(
        b_collection_path,  # type: bytes
        b_tar_path,  # type: bytes
        collection_manifest,  # type: CollectionManifestType
        file_manifest,  # type: FilesManifestType
):  # type: (...) -> Text
    """Build a tar.gz collection artifact from the manifest data."""
    files_manifest_json = to_bytes(json.dumps(file_manifest, indent=True), errors='surrogate_or_strict')
    collection_manifest['file_manifest_file']['chksum_sha256'] = secure_hash_s(files_manifest_json, hash_func=sha256)
    collection_manifest_json = to_bytes(json.dumps(collection_manifest, indent=True), errors='surrogate_or_strict')

    with _tempdir() as b_temp_path:
        b_tar_filepath = os.path.join(b_temp_path, os.path.basename(b_tar_path))

        with tarfile.open(b_tar_filepath, mode='w:gz') as tar_file:
            # Add the MANIFEST.json and FILES.json file to the archive
            for name, b in [(MANIFEST_FILENAME, collection_manifest_json), ('FILES.json', files_manifest_json)]:
                b_io = BytesIO(b)
                tar_info = tarfile.TarInfo(name)
                tar_info.size = len(b)
                tar_info.mtime = int(time.time())
                tar_info.mode = 0o0644
                tar_file.addfile(tarinfo=tar_info, fileobj=b_io)

            for file_info in file_manifest['files']:  # type: ignore[union-attr]
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
                tar_file.add(
                    to_native(os.path.realpath(b_src_path)),
                    arcname=filename,
                    recursive=False,
                    filter=reset_stat,
                )

        shutil.copy(to_native(b_tar_filepath), to_native(b_tar_path))
        collection_name = "%s.%s" % (collection_manifest['collection_info']['namespace'],
                                     collection_manifest['collection_info']['name'])
        tar_path = to_text(b_tar_path)
        display.display(u'Created collection for %s at %s' % (collection_name, tar_path))
        return tar_path


def _build_collection_dir(b_collection_path, b_collection_output, collection_manifest, file_manifest):
    """Build a collection directory from the manifest data.

    This should follow the same pattern as _build_collection_tar.
    """
    os.makedirs(b_collection_output, mode=0o0755)

    files_manifest_json = to_bytes(json.dumps(file_manifest, indent=True), errors='surrogate_or_strict')
    collection_manifest['file_manifest_file']['chksum_sha256'] = secure_hash_s(files_manifest_json, hash_func=sha256)
    collection_manifest_json = to_bytes(json.dumps(collection_manifest, indent=True), errors='surrogate_or_strict')

    # Write contents to the files
    for name, b in [(MANIFEST_FILENAME, collection_manifest_json), ('FILES.json', files_manifest_json)]:
        b_path = os.path.join(b_collection_output, to_bytes(name, errors='surrogate_or_strict'))
        with open(b_path, 'wb') as file_obj, BytesIO(b) as b_io:
            shutil.copyfileobj(b_io, file_obj)

        os.chmod(b_path, 0o0644)

    base_directories = []
    for file_info in file_manifest['files']:
        if file_info['name'] == '.':
            continue

        src_file = os.path.join(b_collection_path, to_bytes(file_info['name'], errors='surrogate_or_strict'))
        dest_file = os.path.join(b_collection_output, to_bytes(file_info['name'], errors='surrogate_or_strict'))

        if any(src_file.startswith(directory) for directory in base_directories):
            continue

        existing_is_exec = os.stat(src_file).st_mode & stat.S_IXUSR
        mode = 0o0755 if existing_is_exec else 0o0644

        if os.path.isdir(src_file):
            mode = 0o0755
            base_directories.append(src_file)
            shutil.copytree(src_file, dest_file)
        else:
            shutil.copyfile(src_file, dest_file)

        os.chmod(dest_file, mode)
    collection_output = to_text(b_collection_output)
    return collection_output


def find_existing_collections(path, artifacts_manager):
    """Locate all collections under a given path.

    :param path: Collection dirs layout search path.
    :param artifacts_manager: Artifacts manager.
    """
    b_path = to_bytes(path, errors='surrogate_or_strict')

    # FIXME: consider using `glob.glob()` to simplify looping
    for b_namespace in os.listdir(b_path):
        b_namespace_path = os.path.join(b_path, b_namespace)
        if os.path.isfile(b_namespace_path):
            continue

        # FIXME: consider feeding b_namespace_path to Candidate.from_dir_path to get subdirs automatically
        for b_collection in os.listdir(b_namespace_path):
            b_collection_path = os.path.join(b_namespace_path, b_collection)
            if not os.path.isdir(b_collection_path):
                continue

            try:
                req = Candidate.from_dir_path_as_unknown(
                    b_collection_path,
                    artifacts_manager,
                )
            except ValueError as val_err:
                raise_from(AnsibleError(val_err), val_err)

            display.vvv(
                u"Found installed collection {coll!s} at '{path!s}'".
                format(coll=to_text(req), path=to_text(req.src))
            )
            yield req


def install(collection, path, artifacts_manager):  # FIXME: mv to dataclasses?
    # type: (Candidate, str, ConcreteArtifactsManager) -> None
    """Install a collection under a given path.

    :param collection: Collection to be installed.
    :param path: Collection dirs layout path.
    :param artifacts_manager: Artifacts manager.
    """
    b_artifact_path = (
        artifacts_manager.get_artifact_path if collection.is_concrete_artifact
        else artifacts_manager.get_galaxy_artifact_path
    )(collection)

    collection_path = os.path.join(path, collection.namespace, collection.name)
    b_collection_path = to_bytes(collection_path, errors='surrogate_or_strict')
    display.display(
        u"Installing '{coll!s}' to '{path!s}'".
        format(coll=to_text(collection), path=collection_path),
    )

    if os.path.exists(b_collection_path):
        shutil.rmtree(b_collection_path)

    if collection.is_dir:
        install_src(collection, b_artifact_path, b_collection_path, artifacts_manager)
    else:
        install_artifact(b_artifact_path, b_collection_path, artifacts_manager._b_working_directory)

    display.display(
        '{coll!s} was installed successfully'.
        format(coll=to_text(collection)),
    )


def install_artifact(b_coll_targz_path, b_collection_path, b_temp_path):
    """Install a collection from tarball under a given path.

    :param b_coll_targz_path: Collection tarball to be installed.
    :param b_collection_path: Collection dirs layout path.
    :param b_temp_path: Temporary dir path.
    """
    try:
        with tarfile.open(b_coll_targz_path, mode='r') as collection_tar:
            files_member_obj = collection_tar.getmember('FILES.json')
            with _tarfile_extract(collection_tar, files_member_obj) as (dummy, files_obj):
                files = json.loads(to_text(files_obj.read(), errors='surrogate_or_strict'))

            _extract_tar_file(collection_tar, MANIFEST_FILENAME, b_collection_path, b_temp_path)
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


def install_src(
        collection,
        b_collection_path, b_collection_output_path,
        artifacts_manager,
):
    r"""Install the collection from source control into given dir.

    Generates the Ansible collection artifact data from a galaxy.yml and
    installs the artifact to a directory.
    This should follow the same pattern as build_collection, but instead
    of creating an artifact, install it.

    :param collection: Collection to be installed.
    :param b_collection_path: Collection dirs layout path.
    :param b_collection_output_path: The installation directory for the \
                                     collection artifact.
    :param artifacts_manager: Artifacts manager.

    :raises AnsibleError: If no collection metadata found.
    """
    collection_meta = artifacts_manager.get_direct_collection_meta(collection)

    if 'build_ignore' not in collection_meta:  # installed collection, not src
        # FIXME: optimize this? use a different process? copy instead of build?
        collection_meta['build_ignore'] = []
    collection_manifest = _build_manifest(**collection_meta)
    file_manifest = _build_files_manifest(
        b_collection_path,
        collection_meta['namespace'], collection_meta['name'],
        collection_meta['build_ignore'],
    )

    collection_output_path = _build_collection_dir(
        b_collection_path, b_collection_output_path,
        collection_manifest, file_manifest,
    )

    display.display(
        'Created collection for {coll!s} at {path!s}'.
        format(coll=collection, path=collection_output_path)
    )


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
    with _get_tar_file_member(tar, filename) as (tar_member, tar_obj):
        if tar_member.type == tarfile.SYMTYPE:
            actual_hash = _consume_file(tar_obj)

        else:
            with tempfile.NamedTemporaryFile(dir=b_temp_path, delete=False) as tmpfile_obj:
                actual_hash = _consume_file(tar_obj, tmpfile_obj)

        if expected_hash and actual_hash != expected_hash:
            raise AnsibleError("Checksum mismatch for '%s' inside collection at '%s'"
                               % (to_native(filename, errors='surrogate_or_strict'), to_native(tar.name)))

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


def _get_json_from_tar_file(b_path, filename):
    file_contents = ''

    with tarfile.open(b_path, mode='r') as collection_tar:
        with _get_tar_file_member(collection_tar, filename) as (dummy, tar_obj):
            bufsize = 65536
            data = tar_obj.read(bufsize)
            while data:
                file_contents += to_text(data)
                data = tar_obj.read(bufsize)

    return json.loads(file_contents)


def _get_tar_file_hash(b_path, filename):
    with tarfile.open(b_path, mode='r') as collection_tar:
        with _get_tar_file_member(collection_tar, filename) as (dummy, tar_obj):
            return _consume_file(tar_obj)


def _get_file_hash(b_path, filename):  # type: (bytes, str) -> str
    filepath = os.path.join(b_path, to_bytes(filename, errors='surrogate_or_strict'))
    with open(filepath, 'rb') as fp:
        return _consume_file(fp)


def _is_child_path(path, parent_path, link_name=None):
    """ Checks that path is a path within the parent_path specified. """
    b_path = to_bytes(path, errors='surrogate_or_strict')

    if link_name and not os.path.isabs(b_path):
        # If link_name is specified, path is the source of the link and we need to resolve the absolute path.
        b_link_dir = os.path.dirname(to_bytes(link_name, errors='surrogate_or_strict'))
        b_path = os.path.abspath(os.path.join(b_link_dir, b_path))

    b_parent_path = to_bytes(parent_path, errors='surrogate_or_strict')
    return b_path == b_parent_path or b_path.startswith(b_parent_path + to_bytes(os.path.sep))


def _resolve_depenency_map(
        requested_requirements,  # type: Iterable[Requirement]
        galaxy_apis,  # type: Iterable[GalaxyAPI]
        concrete_artifacts_manager,  # type: ConcreteArtifactsManager
        preferred_candidates,  # type: Optional[Iterable[Candidate]]
        no_deps,  # type: bool
        allow_pre_release,  # type: bool
        upgrade,  # type: bool
):  # type: (...) -> Dict[str, Candidate]
    """Return the resolved dependency map."""
    collection_dep_resolver = build_collection_dependency_resolver(
        galaxy_apis=galaxy_apis,
        concrete_artifacts_manager=concrete_artifacts_manager,
        user_requirements=requested_requirements,
        preferred_candidates=preferred_candidates,
        with_deps=not no_deps,
        with_pre_releases=allow_pre_release,
        upgrade=upgrade,
    )
    try:
        return collection_dep_resolver.resolve(
            requested_requirements,
            max_rounds=2000000,  # NOTE: same constant pip uses
        ).mapping
    except CollectionDependencyResolutionImpossible as dep_exc:
        conflict_causes = (
            '* {req.fqcn!s}:{req.ver!s} ({dep_origin!s})'.format(
                req=req_inf.requirement,
                dep_origin='direct request'
                if req_inf.parent is None
                else 'dependency of {parent!s}'.
                format(parent=req_inf.parent),
            )
            for req_inf in dep_exc.causes
        )
        error_msg_lines = chain(
            (
                'Failed to resolve the requested '
                'dependencies map. Could not satisfy the following '
                'requirements:',
            ),
            conflict_causes,
        )
        raise raise_from(  # NOTE: Leading "raise" is a hack for mypy bug #9717
            AnsibleError('\n'.join(error_msg_lines)),
            dep_exc,
        )
