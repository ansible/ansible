# -*- coding: utf-8 -*-
# Copyright: (c) 2019-2021, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""Installed collections management package."""

from __future__ import annotations

import errno
import fnmatch
import functools
import glob
import inspect
import json
import os
import pathlib
import queue
import re
import shutil
import stat
import sys
import tarfile
import tempfile
import textwrap
import threading
import time
import typing as t

from collections import namedtuple
from contextlib import contextmanager
from dataclasses import dataclass
from hashlib import sha256
from io import BytesIO
from importlib.metadata import distribution
from itertools import chain

try:
    from packaging.requirements import Requirement as PkgReq
except ImportError:
    class PkgReq:  # type: ignore[no-redef]
        pass

    HAS_PACKAGING = False
else:
    HAS_PACKAGING = True

try:
    from distlib.manifest import Manifest  # type: ignore[import]
    from distlib import DistlibException  # type: ignore[import]
except ImportError:
    HAS_DISTLIB = False
else:
    HAS_DISTLIB = True

if t.TYPE_CHECKING:
    from ansible.galaxy.collection.concrete_artifact_manager import (
        ConcreteArtifactsManager,
    )

    ManifestKeysType = t.Literal[
        'collection_info', 'file_manifest_file', 'format',
    ]
    FileMetaKeysType = t.Literal[
        'name',
        'ftype',
        'chksum_type',
        'chksum_sha256',
        'format',
    ]
    CollectionInfoKeysType = t.Literal[
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
    ManifestValueType = t.Dict[CollectionInfoKeysType, t.Union[int, str, t.List[str], t.Dict[str, str], None]]
    CollectionManifestType = t.Dict[ManifestKeysType, ManifestValueType]
    FileManifestEntryType = t.Dict[FileMetaKeysType, t.Union[str, int, None]]
    FilesManifestType = t.Dict[t.Literal['files', 'format'], t.Union[t.List[FileManifestEntryType], int]]

import ansible.constants as C
from ansible.compat.importlib_resources import files
from ansible.errors import AnsibleError
from ansible.galaxy.api import GalaxyAPI
from ansible.galaxy.collection.concrete_artifact_manager import (
    _consume_file,
    _download_file,
    _get_json_from_installed_dir,
    _get_meta_from_src_dir,
    _tarfile_extract,
)
from ansible.galaxy.collection.galaxy_api_proxy import MultiGalaxyAPIProxy
from ansible.galaxy.collection.gpg import (
    run_gpg_verify,
    parse_gpg_errors,
    get_signature_from_source,
    GPG_ERROR_MAP,
)
try:
    from ansible.galaxy.dependency_resolution import (
        build_collection_dependency_resolver,
    )
    from ansible.galaxy.dependency_resolution.errors import (
        CollectionDependencyResolutionImpossible,
        CollectionDependencyInconsistentCandidate,
    )
    from ansible.galaxy.dependency_resolution.providers import (
        RESOLVELIB_VERSION,
        RESOLVELIB_LOWERBOUND,
        RESOLVELIB_UPPERBOUND,
    )
except ImportError:
    HAS_RESOLVELIB = False
else:
    HAS_RESOLVELIB = True

from ansible.galaxy.dependency_resolution.dataclasses import (
    Candidate, Requirement, _is_installed_collection_dir,
)
from ansible.galaxy.dependency_resolution.versioning import meets_requirements
from ansible.plugins.loader import get_all_plugin_loaders
from ansible.module_utils.common.file import S_IRWU_RG_RO, S_IRWXU_RXG_RXO, S_IXANY
from ansible.module_utils.common.text.converters import to_bytes, to_native, to_text
from ansible.module_utils.common.collections import is_sequence
from ansible.module_utils.common.yaml import yaml_dump
from ansible.utils.collection_loader import AnsibleCollectionRef
from ansible.utils.display import Display
from ansible.utils.hashing import secure_hash, secure_hash_s
from ansible.utils.sentinel import Sentinel


display = Display()

MANIFEST_FORMAT = 1
MANIFEST_FILENAME = 'MANIFEST.json'

ModifiedContent = namedtuple('ModifiedContent', ['filename', 'expected', 'installed'])

SIGNATURE_COUNT_RE = r"^(?P<strict>\+)?(?:(?P<count>\d+)|(?P<all>all))$"


@dataclass
class ManifestControl:
    directives: list[str] = None
    omit_default_directives: bool = False

    def __post_init__(self):
        # Allow a dict representing this dataclass to be splatted directly.
        # Requires attrs to have a default value, so anything with a default
        # of None is swapped for its, potentially mutable, default
        for field_name, field_type in inspect.get_annotations(type(self), eval_str=True).items():
            if getattr(self, field_name) is None:
                super().__setattr__(field_name, field_type())


class CollectionSignatureError(Exception):
    def __init__(self, reasons=None, stdout=None, rc=None, ignore=False):
        self.reasons = reasons
        self.stdout = stdout
        self.rc = rc
        self.ignore = ignore

        self._reason_wrapper = None

    def _report_unexpected(self, collection_name):
        return (
            f"Unexpected error for '{collection_name}': "
            f"GnuPG signature verification failed with the return code {self.rc} and output {self.stdout}"
        )

    def _report_expected(self, collection_name):
        header = f"Signature verification failed for '{collection_name}' (return code {self.rc}):"
        return header + self._format_reasons()

    def _format_reasons(self):
        if self._reason_wrapper is None:
            self._reason_wrapper = textwrap.TextWrapper(
                initial_indent="    * ",  # 6 chars
                subsequent_indent="      ",  # 6 chars
            )

        wrapped_reasons = [
            '\n'.join(self._reason_wrapper.wrap(reason))
            for reason in self.reasons
        ]

        return '\n' + '\n'.join(wrapped_reasons)

    def report(self, collection_name):
        if self.reasons:
            return self._report_expected(collection_name)

        return self._report_unexpected(collection_name)


# FUTURE: expose actual verify result details for a collection on this object, maybe reimplement as dataclass on py3.8+
class CollectionVerifyResult:
    def __init__(self, collection_name):  # type: (str) -> None
        self.collection_name = collection_name  # type: str
        self.success = True  # type: bool


def verify_local_collection(local_collection, remote_collection, artifacts_manager):
    # type: (Candidate, t.Optional[Candidate], ConcreteArtifactsManager) -> CollectionVerifyResult
    """Verify integrity of the locally installed collection.

    :param local_collection: Collection being checked.
    :param remote_collection: Upstream collection (optional, if None, only verify local artifact)
    :param artifacts_manager: Artifacts manager.
    :return: a collection verify result object.
    """
    result = CollectionVerifyResult(local_collection.fqcn)

    b_collection_path = to_bytes(local_collection.src, errors='surrogate_or_strict')

    display.display("Verifying '{coll!s}'.".format(coll=local_collection))
    display.display(
        u"Installed collection found at '{path!s}'".
        format(path=to_text(local_collection.src)),
    )

    modified_content = []  # type: list[ModifiedContent]

    verify_local_only = remote_collection is None

    # partial away the local FS detail so we can just ask generically during validation
    get_json_from_validation_source = functools.partial(_get_json_from_installed_dir, b_collection_path)
    get_hash_from_validation_source = functools.partial(_get_file_hash, b_collection_path)

    if not verify_local_only:
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

    manifest_file = os.path.join(to_text(b_collection_path, errors='surrogate_or_strict'), MANIFEST_FILENAME)
    signatures = list(local_collection.signatures)
    if verify_local_only and local_collection.source_info is not None:
        signatures = [info["signature"] for info in local_collection.source_info["signatures"]] + signatures
    elif not verify_local_only and remote_collection.signatures:
        signatures = list(remote_collection.signatures) + signatures

    keyring_configured = artifacts_manager.keyring is not None
    if not keyring_configured and signatures:
        display.warning(
            "The GnuPG keyring used for collection signature "
            "verification was not configured but signatures were "
            "provided by the Galaxy server. "
            "Configure a keyring for ansible-galaxy to verify "
            "the origin of the collection. "
            "Skipping signature verification."
        )
    elif keyring_configured:
        if not verify_file_signatures(
            local_collection.fqcn,
            manifest_file,
            signatures,
            artifacts_manager.keyring,
            artifacts_manager.required_successful_signature_count,
            artifacts_manager.ignore_signature_errors,
        ):
            result.success = False
            return result
        display.vvvv(f"GnuPG signature verification succeeded, verifying contents of {local_collection}")

    if verify_local_only:
        # since we're not downloading this, just seed it with the value from disk
        manifest_hash = get_hash_from_validation_source(MANIFEST_FILENAME)
    elif keyring_configured and remote_collection.signatures:
        manifest_hash = get_hash_from_validation_source(MANIFEST_FILENAME)
    else:
        # fetch remote
        # NOTE: AnsibleError is raised on URLError
        b_temp_tar_path = artifacts_manager.get_artifact_path_from_unknown(remote_collection)

        display.vvv(
            u"Remote collection cached as '{path!s}'".format(path=to_text(b_temp_tar_path))
        )

        # partial away the tarball details so we can just ask generically during validation
        get_json_from_validation_source = functools.partial(_get_json_from_tar_file, b_temp_tar_path)
        get_hash_from_validation_source = functools.partial(_get_tar_file_hash, b_temp_tar_path)

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

    collection_dirs = set()
    collection_files = {
        os.path.join(b_collection_path, b'MANIFEST.json'),
        os.path.join(b_collection_path, b'FILES.json'),
    }

    # Use the file manifest to verify individual file checksums
    for manifest_data in file_manifest['files']:
        name = manifest_data['name']

        if manifest_data['ftype'] == 'file':
            collection_files.add(
                os.path.join(b_collection_path, to_bytes(name, errors='surrogate_or_strict'))
            )
            expected_hash = manifest_data['chksum_%s' % manifest_data['chksum_type']]
            _verify_file_hash(b_collection_path, name, expected_hash, modified_content)

        if manifest_data['ftype'] == 'dir':
            collection_dirs.add(
                os.path.join(b_collection_path, to_bytes(name, errors='surrogate_or_strict'))
            )

    b_ignore_patterns = [
        b'*.pyc',
    ]

    # Find any paths not in the FILES.json
    for root, dirs, files in os.walk(b_collection_path):
        for name in files:
            full_path = os.path.join(root, name)
            path = to_text(full_path[len(b_collection_path) + 1::], errors='surrogate_or_strict')
            if any(fnmatch.fnmatch(full_path, b_pattern) for b_pattern in b_ignore_patterns):
                display.v("Ignoring verification for %s" % full_path)
                continue

            if full_path not in collection_files:
                modified_content.append(
                    ModifiedContent(filename=path, expected='the file does not exist', installed='the file exists')
                )
        for name in dirs:
            full_path = os.path.join(root, name)
            path = to_text(full_path[len(b_collection_path) + 1::], errors='surrogate_or_strict')

            if full_path not in collection_dirs:
                modified_content.append(
                    ModifiedContent(filename=path, expected='the directory does not exist', installed='the directory exists')
                )

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


def verify_file_signatures(fqcn, manifest_file, detached_signatures, keyring, required_successful_count, ignore_signature_errors):
    # type: (str, str, list[str], str, str, list[str]) -> bool
    successful = 0
    error_messages = []

    signature_count_requirements = re.match(SIGNATURE_COUNT_RE, required_successful_count).groupdict()

    strict = signature_count_requirements['strict'] or False
    require_all = signature_count_requirements['all']
    require_count = signature_count_requirements['count']
    if require_count is not None:
        require_count = int(require_count)

    for signature in detached_signatures:
        signature = to_text(signature, errors='surrogate_or_strict')
        try:
            verify_file_signature(manifest_file, signature, keyring, ignore_signature_errors)
        except CollectionSignatureError as error:
            if error.ignore:
                # Do not include ignored errors in either the failed or successful count
                continue
            error_messages.append(error.report(fqcn))
        else:
            successful += 1

            if require_all:
                continue

            if successful == require_count:
                break

    if strict and not successful:
        verified = False
        display.display(f"Signature verification failed for '{fqcn}': no successful signatures")
    elif require_all:
        verified = not error_messages
        if not verified:
            display.display(f"Signature verification failed for '{fqcn}': some signatures failed")
    else:
        verified = not detached_signatures or require_count == successful
        if not verified:
            display.display(f"Signature verification failed for '{fqcn}': fewer successful signatures than required")

    if not verified:
        for msg in error_messages:
            display.vvvv(msg)

    return verified


def verify_file_signature(manifest_file, detached_signature, keyring, ignore_signature_errors):
    # type: (str, str, str, list[str]) -> None
    """Run the gpg command and parse any errors. Raises CollectionSignatureError on failure."""
    gpg_result, gpg_verification_rc = run_gpg_verify(manifest_file, detached_signature, keyring, display)

    if gpg_result:
        errors = parse_gpg_errors(gpg_result)
        try:
            error = next(errors)
        except StopIteration:
            pass
        else:
            reasons = []
            ignored_reasons = 0

            for error in chain([error], errors):
                # Get error status (dict key) from the class (dict value)
                status_code = list(GPG_ERROR_MAP.keys())[list(GPG_ERROR_MAP.values()).index(error.__class__)]
                if status_code in ignore_signature_errors:
                    ignored_reasons += 1
                reasons.append(error.get_gpg_error_description())

            ignore = len(reasons) == ignored_reasons
            raise CollectionSignatureError(reasons=set(reasons), stdout=gpg_result, rc=gpg_verification_rc, ignore=ignore)

    if gpg_verification_rc:
        raise CollectionSignatureError(stdout=gpg_result, rc=gpg_verification_rc)

    # No errors and rc is 0, verify was successful
    return None


def build_collection(u_collection_path, u_output_path, force):
    # type: (str, str, bool) -> str
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
        raise AnsibleError(to_native(lookup_err)) from lookup_err

    collection_manifest = _build_manifest(**collection_meta)
    file_manifest = _build_files_manifest(
        b_collection_path,
        collection_meta['namespace'],  # type: ignore[arg-type]
        collection_meta['name'],  # type: ignore[arg-type]
        collection_meta['build_ignore'],  # type: ignore[arg-type]
        collection_meta['manifest'],  # type: ignore[arg-type]
        collection_meta['license_file'],  # type: ignore[arg-type]
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
        collections,  # type: t.Iterable[Requirement]
        output_path,  # type: str
        apis,  # type: t.Iterable[GalaxyAPI]
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
            # Avoid overhead getting signatures since they are not currently applicable to downloaded collections
            include_signatures=False,
            offline=False,
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
                    '{coll!s} is not downloadable'.
                    format(coll=to_text(concrete_coll_pin)),
                )
                continue

            display.display(
                u"Downloading collection '{coll!s}' to '{path!s}'".
                format(coll=to_text(concrete_coll_pin), path=to_text(b_output_path)),
            )

            b_src_path = artifacts_manager.get_artifact_path_from_unknown(concrete_coll_pin)

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
            yaml_dump({'collections': requirements}),
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
        collections,  # type: t.Iterable[Requirement]
        output_path,  # type: str
        apis,  # type: t.Iterable[GalaxyAPI]
        ignore_errors,  # type: bool
        no_deps,  # type: bool
        force,  # type: bool
        force_deps,  # type: bool
        upgrade,  # type: bool
        allow_pre_release,  # type: bool
        artifacts_manager,  # type: ConcreteArtifactsManager
        disable_gpg_verify,  # type: bool
        offline,  # type: bool
        read_requirement_paths,  # type: set[str]
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
        Requirement(coll.fqcn, coll.ver, coll.src, coll.type, None)
        for path in {output_path} | read_requirement_paths
        for coll in find_existing_collections(path, artifacts_manager)
    }

    unsatisfied_requirements = set(
        chain.from_iterable(
            (
                Requirement.from_dir_path(to_bytes(sub_coll), artifacts_manager)
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
        # NOTE: No need to include signatures if the collection is already installed
        Candidate(coll.fqcn, coll.ver, coll.src, coll.type, None)
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
            include_signatures=not disable_gpg_verify,
            offline=offline,
        )

    keyring_exists = artifacts_manager.keyring is not None
    with _display_progress("Starting collection install process"):
        for fqcn, concrete_coll_pin in dependency_map.items():
            if concrete_coll_pin.is_virtual:
                display.vvvv(
                    "Encountered {coll!s}, skipping.".
                    format(coll=to_text(concrete_coll_pin)),
                )
                continue

            if concrete_coll_pin in preferred_collections:
                display.display(
                    "'{coll!s}' is already installed, skipping.".
                    format(coll=to_text(concrete_coll_pin)),
                )
                continue

            if not disable_gpg_verify and concrete_coll_pin.signatures and not keyring_exists:
                # Duplicate warning msgs are not displayed
                display.warning(
                    "The GnuPG keyring used for collection signature "
                    "verification was not configured but signatures were "
                    "provided by the Galaxy server to verify authenticity. "
                    "Configure a keyring for ansible-galaxy to use "
                    "or disable signature verification. "
                    "Skipping signature verification."
                )

            if concrete_coll_pin.type == 'galaxy':
                concrete_coll_pin = concrete_coll_pin.with_signatures_repopulated()

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
        collections,  # type: t.Iterable[Requirement]
        search_paths,  # type: t.Iterable[str]
        apis,  # type: t.Iterable[GalaxyAPI]
        ignore_errors,  # type: bool
        local_verify_only,  # type: bool
        artifacts_manager,  # type: ConcreteArtifactsManager
):  # type: (...) -> list[CollectionVerifyResult]
    r"""Verify the integrity of locally installed collections.

    :param collections: The collections to check.
    :param search_paths: Locations for the local collection lookup.
    :param apis: A list of GalaxyAPIs to query when searching for a collection.
    :param ignore_errors: Whether to ignore any errors when verifying the collection.
    :param local_verify_only: When True, skip downloads and only verify local manifests.
    :param artifacts_manager: Artifacts manager.
    :return: list of CollectionVerifyResult objects describing the results of each collection verification
    """
    results = []  # type: list[CollectionVerifyResult]

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
                    supplemental_signatures = [
                        get_signature_from_source(source, display)
                        for source in collection.signature_sources or []
                    ]
                    local_collection = Candidate(
                        local_collection.fqcn,
                        local_collection.ver,
                        local_collection.src,
                        local_collection.type,
                        signatures=frozenset(supplemental_signatures),
                    )

                    break
                else:
                    raise AnsibleError(message=default_err)

                if local_verify_only:
                    remote_collection = None
                else:
                    signatures = api_proxy.get_signatures(local_collection)
                    signatures.extend([
                        get_signature_from_source(source, display)
                        for source in collection.signature_sources or []
                    ])

                    remote_collection = Candidate(
                        collection.fqcn,
                        collection.ver if collection.ver != '*'
                        else local_collection.ver,
                        None, 'galaxy',
                        frozenset(signatures),
                    )

                    # Download collection on a galaxy server for comparison
                    try:
                        # NOTE: If there are no signatures, trigger the lookup. If found,
                        # NOTE: it'll cache download URL and token in artifact manager.
                        # NOTE: If there are no Galaxy server signatures, only user-provided signature URLs,
                        # NOTE: those alone validate the MANIFEST.json and the remote collection is not downloaded.
                        # NOTE: The remote MANIFEST.json is only used in verification if there are no signatures.
                        if artifacts_manager.keyring is None or not signatures:
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

                result = verify_local_collection(local_collection, remote_collection, artifacts_manager)

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


def _make_manifest():
    return {
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


def _make_entry(name, ftype, chksum_type='sha256', chksum=None):
    return {
        'name': name,
        'ftype': ftype,
        'chksum_type': chksum_type if chksum else None,
        f'chksum_{chksum_type}': chksum,
        'format': MANIFEST_FORMAT
    }


def _build_files_manifest(b_collection_path, namespace, name, ignore_patterns,
                          manifest_control, license_file):
    # type: (bytes, str, str, list[str], dict[str, t.Any], t.Optional[str]) -> FilesManifestType
    if ignore_patterns and manifest_control is not Sentinel:
        raise AnsibleError('"build_ignore" and "manifest" are mutually exclusive')

    if manifest_control is not Sentinel:
        return _build_files_manifest_distlib(
            b_collection_path,
            namespace,
            name,
            manifest_control,
            license_file,
        )

    return _build_files_manifest_walk(b_collection_path, namespace, name, ignore_patterns)


def _build_files_manifest_distlib(b_collection_path, namespace, name, manifest_control,
                                  license_file):
    # type: (bytes, str, str, dict[str, t.Any], t.Optional[str]) -> FilesManifestType
    if not HAS_DISTLIB:
        raise AnsibleError('Use of "manifest" requires the python "distlib" library')

    if manifest_control is None:
        manifest_control = {}

    try:
        control = ManifestControl(**manifest_control)
    except TypeError as ex:
        raise AnsibleError(f'Invalid "manifest" provided: {ex}')

    if not is_sequence(control.directives):
        raise AnsibleError(f'"manifest.directives" must be a list, got: {control.directives.__class__.__name__}')

    if not isinstance(control.omit_default_directives, bool):
        raise AnsibleError(
            '"manifest.omit_default_directives" is expected to be a boolean, got: '
            f'{control.omit_default_directives.__class__.__name__}'
        )

    if control.omit_default_directives and not control.directives:
        raise AnsibleError(
            '"manifest.omit_default_directives" was set to True, but no directives were defined '
            'in "manifest.directives". This would produce an empty collection artifact.'
        )

    directives = []
    if control.omit_default_directives:
        directives.extend(control.directives)
    else:
        directives.extend([
            'include meta/*.yml',
            'include *.txt *.md *.rst *.license COPYING LICENSE',
            'recursive-include .reuse **',
            'recursive-include LICENSES **',
            'recursive-include tests **',
            'recursive-include docs **.rst **.yml **.yaml **.json **.j2 **.txt **.license',
            'recursive-include roles **.yml **.yaml **.json **.j2 **.license',
            'recursive-include playbooks **.yml **.yaml **.json **.license',
            'recursive-include changelogs **.yml **.yaml **.license',
            'recursive-include plugins */**.py */**.license',
        ])

        if license_file:
            directives.append(f'include {license_file}')

        plugins = set(l.package.split('.')[-1] for d, l in get_all_plugin_loaders())
        for plugin in sorted(plugins):
            if plugin in ('modules', 'module_utils'):
                continue
            elif plugin in C.DOCUMENTABLE_PLUGINS:
                directives.append(
                    f'recursive-include plugins/{plugin} **.yml **.yaml'
                )

        directives.extend([
            'recursive-include plugins/modules **.ps1 **.yml **.yaml **.license',
            'recursive-include plugins/module_utils **.ps1 **.psm1 **.cs **.license',
        ])

        directives.extend(control.directives)

        directives.extend([
            f'exclude galaxy.yml galaxy.yaml MANIFEST.json FILES.json {namespace}-{name}-*.tar.gz',
            'recursive-exclude tests/output **',
            'global-exclude /.* /__pycache__ *.pyc *.pyo *.bak *~ *.swp',
        ])

    display.vvv('Manifest Directives:')
    display.vvv(textwrap.indent('\n'.join(directives), '    '))

    u_collection_path = to_text(b_collection_path, errors='surrogate_or_strict')
    m = Manifest(u_collection_path)
    for directive in directives:
        try:
            m.process_directive(directive)
        except DistlibException as e:
            raise AnsibleError(f'Invalid manifest directive: {e}')
        except Exception as e:
            raise AnsibleError(f'Unknown error processing manifest directive: {e}')

    manifest = _make_manifest()

    for abs_path in m.sorted(wantdirs=True):
        rel_path = os.path.relpath(abs_path, u_collection_path)
        if os.path.isdir(abs_path):
            manifest_entry = _make_entry(rel_path, 'dir')
        else:
            manifest_entry = _make_entry(
                rel_path,
                'file',
                chksum_type='sha256',
                chksum=secure_hash(abs_path, hash_func=sha256)
            )

        manifest['files'].append(manifest_entry)

    return manifest


def _build_files_manifest_walk(b_collection_path, namespace, name, ignore_patterns):
    # type: (bytes, str, str, list[str]) -> FilesManifestType
    # We always ignore .pyc and .retry files as well as some well known version control directories. The ignore
    # patterns can be extended by the build_ignore key in galaxy.yml
    b_ignore_patterns = [
        b'MANIFEST.json',
        b'FILES.json',
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

    manifest = _make_manifest()

    def _discover_relative_base_directory(b_path: bytes, b_top_level_dir: bytes) -> bytes:
        if b_path == b_top_level_dir:
            return b''
        common_prefix = os.path.commonpath((b_top_level_dir, b_path))
        b_rel_base_dir = os.path.relpath(b_path, common_prefix)
        return b_rel_base_dir.lstrip(os.path.sep.encode())

    def _walk(b_path, b_top_level_dir):
        b_rel_base_dir = _discover_relative_base_directory(b_path, b_top_level_dir)
        for b_item in os.listdir(b_path):
            b_abs_path = os.path.join(b_path, b_item)
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

                manifest['files'].append(_make_entry(rel_path, 'dir'))

                if not os.path.islink(b_abs_path):
                    _walk(b_abs_path, b_top_level_dir)
            else:
                if any(fnmatch.fnmatch(b_rel_path, b_pattern) for b_pattern in b_ignore_patterns):
                    display.vvv("Skipping '%s' for collection build" % to_text(b_abs_path))
                    continue

                # Handling of file symlinks occur in _build_collection_tar, the manifest for a symlink is the same for
                # a normal file.
                manifest['files'].append(
                    _make_entry(
                        rel_path,
                        'file',
                        chksum_type='sha256',
                        chksum=secure_hash(b_abs_path, hash_func=sha256)
                    )
                )

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
):  # type: (...) -> str
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
                tar_info.mode = S_IRWU_RG_RO
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
                        tarinfo.mode = S_IRWXU_RXG_RXO if existing_is_exec or tarinfo.isdir() else S_IRWU_RG_RO
                    tarinfo.uid = tarinfo.gid = 0
                    tarinfo.uname = tarinfo.gname = ''

                    return tarinfo

                if os.path.islink(b_src_path):
                    b_link_target = os.path.realpath(b_src_path)
                    if not os.path.exists(b_link_target):
                        raise AnsibleError(f"Failed to find the target path '{to_native(b_link_target)}' for the symlink '{to_native(b_src_path)}'.")
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
    os.makedirs(b_collection_output, mode=S_IRWXU_RXG_RXO)

    files_manifest_json = to_bytes(json.dumps(file_manifest, indent=True), errors='surrogate_or_strict')
    collection_manifest['file_manifest_file']['chksum_sha256'] = secure_hash_s(files_manifest_json, hash_func=sha256)
    collection_manifest_json = to_bytes(json.dumps(collection_manifest, indent=True), errors='surrogate_or_strict')

    # Write contents to the files
    for name, b in [(MANIFEST_FILENAME, collection_manifest_json), ('FILES.json', files_manifest_json)]:
        b_path = os.path.join(b_collection_output, to_bytes(name, errors='surrogate_or_strict'))
        with open(b_path, 'wb') as file_obj, BytesIO(b) as b_io:
            shutil.copyfileobj(b_io, file_obj)

        os.chmod(b_path, S_IRWU_RG_RO)

    base_directories = []
    for file_info in sorted(file_manifest['files'], key=lambda x: x['name']):
        if file_info['name'] == '.':
            continue

        src_file = os.path.join(b_collection_path, to_bytes(file_info['name'], errors='surrogate_or_strict'))
        dest_file = os.path.join(b_collection_output, to_bytes(file_info['name'], errors='surrogate_or_strict'))

        existing_is_exec = os.stat(src_file, follow_symlinks=False).st_mode & stat.S_IXUSR
        mode = S_IRWXU_RXG_RXO if existing_is_exec else S_IRWU_RG_RO

        # ensure symlinks to dirs are not translated to empty dirs
        if os.path.isdir(src_file) and not os.path.islink(src_file):
            mode = S_IRWXU_RXG_RXO
            base_directories.append(src_file)
            os.mkdir(dest_file, mode)
        else:
            # do not follow symlinks to ensure the original link is used
            shutil.copyfile(src_file, dest_file, follow_symlinks=False)

        # avoid setting specific permission on symlinks since it does not
        # support avoid following symlinks and will thrown an exception if the
        # symlink target does not exist
        if not os.path.islink(dest_file):
            os.chmod(dest_file, mode)

    collection_output = to_text(b_collection_output)
    return collection_output


def _normalize_collection_path(path):
    str_path = path.as_posix() if isinstance(path, pathlib.Path) else path
    return pathlib.Path(
        # This is annoying, but GalaxyCLI._resolve_path did it
        os.path.expandvars(str_path)
    ).expanduser().absolute()


def find_existing_collections(path_filter, artifacts_manager, namespace_filter=None, collection_filter=None, dedupe=True):
    """Locate all collections under a given path.

    :param path: Collection dirs layout search path.
    :param artifacts_manager: Artifacts manager.
    """
    if files is None:
        raise AnsibleError('importlib_resources is not installed and is required')

    if path_filter and not is_sequence(path_filter):
        path_filter = [path_filter]
    if namespace_filter and not is_sequence(namespace_filter):
        namespace_filter = [namespace_filter]
    if collection_filter and not is_sequence(collection_filter):
        collection_filter = [collection_filter]

    paths = set()
    for path in files('ansible_collections').glob('*/*/'):
        path = _normalize_collection_path(path)
        if not path.is_dir():
            continue
        if path_filter:
            for pf in path_filter:
                try:
                    path.relative_to(_normalize_collection_path(pf))
                except ValueError:
                    continue
                break
            else:
                continue
        paths.add(path)

    seen = set()
    for path in paths:
        namespace = path.parent.name
        name = path.name
        if namespace_filter and namespace not in namespace_filter:
            continue
        if collection_filter and name not in collection_filter:
            continue

        if dedupe:
            try:
                collection_path = files(f'ansible_collections.{namespace}.{name}')
            except ImportError:
                continue
            if collection_path in seen:
                continue
            seen.add(collection_path)
        else:
            collection_path = path

        b_collection_path = to_bytes(collection_path.as_posix())

        try:
            req = Candidate.from_dir_path_as_unknown(b_collection_path, artifacts_manager)
        except ValueError as val_err:
            display.warning(f'{val_err}')
            continue

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
    b_artifact_path = artifacts_manager.get_artifact_path_from_unknown(collection)

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
        install_artifact(
            b_artifact_path,
            b_collection_path,
            artifacts_manager._b_working_directory,
            collection.signatures,
            artifacts_manager.keyring,
            artifacts_manager.required_successful_signature_count,
            artifacts_manager.ignore_signature_errors,
        )
        remove_source_metadata(collection, b_collection_path)
        if (collection.is_online_index_pointer and isinstance(collection.src, GalaxyAPI)):
            write_source_metadata(
                collection,
                b_collection_path,
                artifacts_manager
            )

    display.display(
        '{coll!s} was installed successfully'.
        format(coll=to_text(collection)),
    )


def write_source_metadata(collection, b_collection_path, artifacts_manager):
    # type: (Candidate, bytes, ConcreteArtifactsManager) -> None
    source_data = artifacts_manager.get_galaxy_artifact_source_info(collection)

    b_yaml_source_data = to_bytes(yaml_dump(source_data), errors='surrogate_or_strict')
    b_info_dest = collection.construct_galaxy_info_path(b_collection_path)
    b_info_dir = os.path.split(b_info_dest)[0]

    if os.path.exists(b_info_dir):
        shutil.rmtree(b_info_dir)

    try:
        os.mkdir(b_info_dir, mode=S_IRWXU_RXG_RXO)
        with open(b_info_dest, mode='w+b') as fd:
            fd.write(b_yaml_source_data)
        os.chmod(b_info_dest, S_IRWU_RG_RO)
    except Exception:
        # Ensure we don't leave the dir behind in case of a failure.
        if os.path.isdir(b_info_dir):
            shutil.rmtree(b_info_dir)
        raise


def remove_source_metadata(collection, b_collection_path):
    pattern = f"{collection.namespace}.{collection.name}-*.info"
    info_path = os.path.join(
        b_collection_path,
        b'../../',
        to_bytes(pattern, errors='surrogate_or_strict')
    )
    if (outdated_info := glob.glob(info_path)):
        display.vvvv(f"Removing {pattern} metadata from previous installations")
    for info_dir in outdated_info:
        try:
            shutil.rmtree(info_dir)
        except Exception:
            pass


def verify_artifact_manifest(manifest_file, signatures, keyring, required_signature_count, ignore_signature_errors):
    # type: (str, list[str], str, str, list[str]) -> None
    failed_verify = False
    coll_path_parts = to_text(manifest_file, errors='surrogate_or_strict').split(os.path.sep)
    collection_name = '%s.%s' % (coll_path_parts[-3], coll_path_parts[-2])  # get 'ns' and 'coll' from /path/to/ns/coll/MANIFEST.json
    if not verify_file_signatures(collection_name, manifest_file, signatures, keyring, required_signature_count, ignore_signature_errors):
        raise AnsibleError(f"Not installing {collection_name} because GnuPG signature verification failed.")
    display.vvvv(f"GnuPG signature verification succeeded for {collection_name}")


def install_artifact(b_coll_targz_path, b_collection_path, b_temp_path, signatures, keyring, required_signature_count, ignore_signature_errors):
    """Install a collection from tarball under a given path.

    :param b_coll_targz_path: Collection tarball to be installed.
    :param b_collection_path: Collection dirs layout path.
    :param b_temp_path: Temporary dir path.
    :param signatures: frozenset of signatures to verify the MANIFEST.json
    :param keyring: The keyring used during GPG verification
    :param required_signature_count: The number of signatures that must successfully verify the collection
    :param ignore_signature_errors: GPG errors to ignore during signature verification
    """
    try:
        with tarfile.open(b_coll_targz_path, mode='r') as collection_tar:
            # Verify the signature on the MANIFEST.json before extracting anything else
            _extract_tar_file(collection_tar, MANIFEST_FILENAME, b_collection_path, b_temp_path)

            if keyring is not None:
                manifest_file = os.path.join(to_text(b_collection_path, errors='surrogate_or_strict'), MANIFEST_FILENAME)
                verify_artifact_manifest(manifest_file, signatures, keyring, required_signature_count, ignore_signature_errors)

            files_member_obj = collection_tar.getmember('FILES.json')
            with _tarfile_extract(collection_tar, files_member_obj) as (dummy, files_obj):
                files = json.loads(to_text(files_obj.read(), errors='surrogate_or_strict'))

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


def install_src(collection, b_collection_path, b_collection_output_path, artifacts_manager):
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
        collection_meta['manifest'] = Sentinel
    collection_manifest = _build_manifest(**collection_meta)
    file_manifest = _build_files_manifest(
        b_collection_path,
        collection_meta['namespace'], collection_meta['name'],
        collection_meta['build_ignore'],
        collection_meta['manifest'],
        collection_meta['license_file'],
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
    dirname = to_native(dirname, errors='surrogate_or_strict')

    try:
        tar_member = tar.getmember(dirname)
    except KeyError:
        raise AnsibleError("Unable to extract '%s' from collection" % dirname)

    b_dir_path = os.path.join(b_dest, to_bytes(dirname, errors='surrogate_or_strict'))

    b_parent_path = os.path.dirname(b_dir_path)
    try:
        os.makedirs(b_parent_path, mode=S_IRWXU_RXG_RXO)
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
            os.mkdir(b_dir_path, S_IRWXU_RXG_RXO)


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
            os.makedirs(b_parent_dir, mode=S_IRWXU_RXG_RXO)

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
            new_mode = S_IRWU_RG_RO
            if stat.S_IMODE(tar_member.mode) & stat.S_IXUSR:
                new_mode |= S_IXANY

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
        requested_requirements,  # type: t.Iterable[Requirement]
        galaxy_apis,  # type: t.Iterable[GalaxyAPI]
        concrete_artifacts_manager,  # type: ConcreteArtifactsManager
        preferred_candidates,  # type: t.Iterable[Candidate] | None
        no_deps,  # type: bool
        allow_pre_release,  # type: bool
        upgrade,  # type: bool
        include_signatures,  # type: bool
        offline,  # type: bool
):  # type: (...) -> dict[str, Candidate]
    """Return the resolved dependency map."""
    if not HAS_RESOLVELIB:
        raise AnsibleError("Failed to import resolvelib, check that a supported version is installed")
    if not HAS_PACKAGING:
        raise AnsibleError("Failed to import packaging, check that a supported version is installed")

    req = None

    try:
        dist = distribution('ansible-core')
    except Exception:
        pass
    else:
        req = next((rr for r in (dist.requires or []) if (rr := PkgReq(r)).name == 'resolvelib'), None)
    finally:
        if req is None:
            # TODO: replace the hardcoded versions with a warning if the dist info is missing
            # display.warning("Unable to find 'ansible-core' distribution requirements to verify the resolvelib version is supported.")
            if not RESOLVELIB_LOWERBOUND <= RESOLVELIB_VERSION < RESOLVELIB_UPPERBOUND:
                raise AnsibleError(
                    f"ansible-galaxy requires resolvelib<{RESOLVELIB_UPPERBOUND.vstring},>={RESOLVELIB_LOWERBOUND.vstring}"
                )
        elif not req.specifier.contains(RESOLVELIB_VERSION.vstring):
            raise AnsibleError(f"ansible-galaxy requires {req.name}{req.specifier}")

    pre_release_hint = '' if allow_pre_release else (
        'Hint: Pre-releases hosted on Galaxy or Automation Hub are not '
        'installed by default unless a specific version is requested. '
        'To enable pre-releases globally, use --pre.'
    )

    collection_dep_resolver = build_collection_dependency_resolver(
        galaxy_apis=galaxy_apis,
        concrete_artifacts_manager=concrete_artifacts_manager,
        preferred_candidates=preferred_candidates,
        with_deps=not no_deps,
        with_pre_releases=allow_pre_release,
        upgrade=upgrade,
        include_signatures=include_signatures,
        offline=offline,
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
        error_msg_lines = list(chain(
            (
                'Failed to resolve the requested '
                'dependencies map. Could not satisfy the following '
                'requirements:',
            ),
            conflict_causes,
        ))
        error_msg_lines.append(pre_release_hint)
        raise AnsibleError('\n'.join(error_msg_lines)) from dep_exc
    except CollectionDependencyInconsistentCandidate as dep_exc:
        parents = [
            str(p) for p in dep_exc.criterion.iter_parent()
            if p is not None
        ]

        error_msg_lines = [
            (
                'Failed to resolve the requested dependencies map. '
                'Got the candidate {req.fqcn!s}:{req.ver!s} ({dep_origin!s}) '
                'which didn\'t satisfy all of the following requirements:'.
                format(
                    req=dep_exc.candidate,
                    dep_origin='direct request'
                    if not parents else 'dependency of {parent!s}'.
                    format(parent=', '.join(parents))
                )
            )
        ]

        for req in dep_exc.criterion.iter_requirement():
            error_msg_lines.append(
                f'* {req.fqcn!s}:{req.ver!s}'
            )
        error_msg_lines.append(pre_release_hint)

        raise AnsibleError('\n'.join(error_msg_lines)) from dep_exc
    except ValueError as exc:
        raise AnsibleError(to_native(exc)) from exc
