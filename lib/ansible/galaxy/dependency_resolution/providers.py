# -*- coding: utf-8 -*-
# Copyright: (c) 2020-2021, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""Requirement provider interfaces."""

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import functools
import typing as t

if t.TYPE_CHECKING:
    from ansible.galaxy.collection.concrete_artifact_manager import (
        ConcreteArtifactsManager,
    )
    from ansible.galaxy.collection.galaxy_api_proxy import MultiGalaxyAPIProxy
    from ansible.galaxy.api import GalaxyAPI

from ansible.galaxy.collection.gpg import get_signature_from_source
from ansible.galaxy.dependency_resolution.dataclasses import (
    Candidate,
    Requirement,
)
from ansible.galaxy.dependency_resolution.versioning import (
    is_pre_release,
    meets_requirements,
)
from ansible.module_utils.six import string_types
from ansible.utils.version import SemanticVersion, LooseVersion

try:
    from resolvelib import AbstractProvider
    from resolvelib import __version__ as resolvelib_version
except ImportError:
    class AbstractProvider:  # type: ignore[no-redef]
        pass

    resolvelib_version = '0.0.0'


# TODO: add python requirements to ansible-test's ansible-core distribution info and remove the hardcoded lowerbound/upperbound fallback
RESOLVELIB_LOWERBOUND = SemanticVersion("0.5.3")
RESOLVELIB_UPPERBOUND = SemanticVersion("1.1.0")
RESOLVELIB_VERSION = SemanticVersion.from_loose_version(LooseVersion(resolvelib_version))


class CollectionDependencyProviderBase(AbstractProvider):
    """Delegate providing a requirement interface for the resolver."""

    def __init__(
            self,  # type: CollectionDependencyProviderBase
            apis,  # type: MultiGalaxyAPIProxy
            concrete_artifacts_manager=None,  # type: ConcreteArtifactsManager
            preferred_candidates=None,  # type: t.Iterable[Candidate]
            with_deps=True,  # type: bool
            with_pre_releases=False,  # type: bool
            upgrade=False,  # type: bool
            include_signatures=True,  # type: bool
    ):  # type: (...) -> None
        r"""Initialize helper attributes.

        :param api: An instance of the multiple Galaxy APIs wrapper.

        :param concrete_artifacts_manager: An instance of the caching \
                                           concrete artifacts manager.

        :param with_deps: A flag specifying whether the resolver \
                          should attempt to pull-in the deps of the \
                          requested requirements. On by default.

        :param with_pre_releases: A flag specifying whether the \
                                  resolver should skip pre-releases. \
                                  Off by default.

        :param upgrade: A flag specifying whether the resolver should \
                        skip matching versions that are not upgrades. \
                        Off by default.

        :param include_signatures: A flag to determine whether to retrieve \
                                   signatures from the Galaxy APIs and \
                                   include signatures in matching Candidates. \
                                   On by default.
        """
        self._api_proxy = apis
        self._make_req_from_dict = functools.partial(
            Requirement.from_requirement_dict,
            art_mgr=concrete_artifacts_manager,
        )
        self._preferred_candidates = set(preferred_candidates or ())
        self._with_deps = with_deps
        self._with_pre_releases = with_pre_releases
        self._upgrade = upgrade
        self._include_signatures = include_signatures

    def identify(self, requirement_or_candidate):
        # type: (t.Union[Candidate, Requirement]) -> str
        """Given requirement or candidate, return an identifier for it.

        This is used to identify a requirement or candidate, e.g.
        whether two requirements should have their specifier parts
        (version ranges or pins) merged, whether two candidates would
        conflict with each other (because they have same name but
        different versions).
        """
        return requirement_or_candidate.canonical_package_id

    def get_preference(self, *args, **kwargs):
        # type: (t.Any, t.Any) -> t.Union[float, int]
        """Return sort key function return value for given requirement.

        This result should be based on preference that is defined as
        "I think this requirement should be resolved first".
        The lower the return value is, the more preferred this
        group of arguments is.

        resolvelib >=0.5.3, <0.7.0

        :param resolution: Currently pinned candidate, or ``None``.

        :param candidates: A list of possible candidates.

        :param information: A list of requirement information.

        Each ``information`` instance is a named tuple with two entries:

          * ``requirement`` specifies a requirement contributing to
            the current candidate list

          * ``parent`` specifies the candidate that provides
            (dependend on) the requirement, or `None`
            to indicate a root requirement.

        resolvelib >=0.7.0, < 0.8.0

        :param identifier: The value returned by ``identify()``.

        :param resolutions: Mapping of identifier, candidate pairs.

        :param candidates: Possible candidates for the identifer.
            Mapping of identifier, list of candidate pairs.

        :param information: Requirement information of each package.
            Mapping of identifier, list of named tuple pairs.
            The named tuples have the entries ``requirement`` and ``parent``.

        resolvelib >=0.8.0, <= 1.0.1

        :param identifier: The value returned by ``identify()``.

        :param resolutions: Mapping of identifier, candidate pairs.

        :param candidates: Possible candidates for the identifer.
            Mapping of identifier, list of candidate pairs.

        :param information: Requirement information of each package.
            Mapping of identifier, list of named tuple pairs.
            The named tuples have the entries ``requirement`` and ``parent``.

        :param backtrack_causes: Sequence of requirement information that were
            the requirements that caused the resolver to most recently backtrack.

        The preference could depend on a various of issues, including
        (not necessarily in this order):

          * Is this package pinned in the current resolution result?

          * How relaxed is the requirement? Stricter ones should
            probably be worked on first? (I don't know, actually.)

          * How many possibilities are there to satisfy this
            requirement? Those with few left should likely be worked on
            first, I guess?

          * Are there any known conflicts for this requirement?
            We should probably work on those with the most
            known conflicts.

        A sortable value should be returned (this will be used as the
        `key` parameter of the built-in sorting function). The smaller
        the value is, the more preferred this requirement is (i.e. the
        sorting function is called with ``reverse=False``).
        """
        raise NotImplementedError

    def _get_preference(self, candidates):
        # type: (list[Candidate]) -> t.Union[float, int]
        if any(
                candidate in self._preferred_candidates
                for candidate in candidates
        ):
            # NOTE: Prefer pre-installed candidates over newer versions
            # NOTE: available from Galaxy or other sources.
            return float('-inf')
        return len(candidates)

    def find_matches(self, *args, **kwargs):
        # type: (t.Any, t.Any) -> list[Candidate]
        r"""Find all possible candidates satisfying given requirements.

        This tries to get candidates based on the requirements' types.

        For concrete requirements (SCM, dir, namespace dir, local or
        remote archives), the one-and-only match is returned

        For a "named" requirement, Galaxy-compatible APIs are consulted
        to find concrete candidates for this requirement. Of theres a
        pre-installed candidate, it's prepended in front of others.

        resolvelib >=0.5.3, <0.6.0

        :param requirements: A collection of requirements which all of \
                             the returned candidates must match. \
                             All requirements are guaranteed to have \
                             the same identifier. \
                             The collection is never empty.

        resolvelib >=0.6.0

        :param identifier: The value returned by ``identify()``.

        :param requirements: The requirements all returned candidates must satisfy.
            Mapping of identifier, iterator of requirement pairs.

        :param incompatibilities: Incompatible versions that must be excluded
            from the returned list.

        :returns: An iterable that orders candidates by preference, \
                  e.g. the most preferred candidate comes first.
        """
        raise NotImplementedError

    def _find_matches(self, requirements):
        # type: (list[Requirement]) -> list[Candidate]
        # FIXME: The first requirement may be a Git repo followed by
        # FIXME: its cloned tmp dir. Using only the first one creates
        # FIXME: loops that prevent any further dependency exploration.
        # FIXME: We need to figure out how to prevent this.
        first_req = requirements[0]
        fqcn = first_req.fqcn
        # The fqcn is guaranteed to be the same
        version_req = "A SemVer-compliant version or '*' is required. See https://semver.org to learn how to compose it correctly. "
        version_req += "This is an issue with the collection."

        # If we're upgrading collections, we can't calculate preinstalled_candidates until the latest matches are found.
        # Otherwise, we can potentially avoid a Galaxy API call by doing this first.
        preinstalled_candidates = set()
        if not self._upgrade and first_req.type == 'galaxy':
            preinstalled_candidates = {
                candidate for candidate in self._preferred_candidates
                if candidate.fqcn == fqcn and
                all(self.is_satisfied_by(requirement, candidate) for requirement in requirements)
            }
        try:
            coll_versions = [] if preinstalled_candidates else self._api_proxy.get_collection_versions(first_req)  # type: t.Iterable[t.Tuple[str, GalaxyAPI]]
        except TypeError as exc:
            if first_req.is_concrete_artifact:
                # Non hashable versions will cause a TypeError
                raise ValueError(
                    f"Invalid version found for the collection '{first_req}'. {version_req}"
                ) from exc
            # Unexpected error from a Galaxy server
            raise

        if first_req.is_concrete_artifact:
            # FIXME: do we assume that all the following artifacts are also concrete?
            # FIXME: does using fqcn==None cause us problems here?

            # Ensure the version found in the concrete artifact is SemVer-compliant
            for version, req_src in coll_versions:
                version_err = f"Invalid version found for the collection '{first_req}': {version} ({type(version)}). {version_req}"
                # NOTE: The known cases causing the version to be a non-string object come from
                # NOTE: the differences in how the YAML parser normalizes ambiguous values and
                # NOTE: how the end-users sometimes expect them to be parsed. Unless the users
                # NOTE: explicitly use the double quotes of one of the multiline string syntaxes
                # NOTE: in the collection metadata file, PyYAML will parse a value containing
                # NOTE: two dot-separated integers as `float`, a single integer as `int`, and 3+
                # NOTE: integers as a `str`. In some cases, they may also use an empty value
                # NOTE: which is normalized as `null` and turned into `None` in the Python-land.
                # NOTE: Another known mistake is setting a minor part of the SemVer notation
                # NOTE: skipping the "patch" bit like "1.0" which is assumed non-compliant even
                # NOTE: after the conversion to string.
                if not isinstance(version, string_types):
                    raise ValueError(version_err)
                elif version != '*':
                    try:
                        SemanticVersion(version)
                    except ValueError as ex:
                        raise ValueError(version_err) from ex

            return [
                Candidate(fqcn, version, _none_src_server, first_req.type, None)
                for version, _none_src_server in coll_versions
            ]

        latest_matches = []
        signatures = []
        extra_signature_sources = []  # type: list[str]

        discarding_pre_releases_acceptable = any(
            not is_pre_release(candidate_version)
            for candidate_version, _src_server in coll_versions
        )

        # NOTE: The optimization of conditionally looping over the requirements
        # NOTE: is used to skip having to compute the pinned status of all
        # NOTE: requirements and apply version normalization to the found ones.
        all_pinned_requirement_version_numbers = {
            # NOTE: Pinned versions can start with a number, but also with an
            # NOTE: equals sign. Stripping it at the beginning should be
            # NOTE: enough. If there's a space after equals, the second strip
            # NOTE: will take care of it.
            # NOTE: Without this conversion, requirements versions like
            # NOTE: '1.2.3-alpha.4' work, but '=1.2.3-alpha.4' don't.
            requirement.ver.lstrip('=').strip()
            for requirement in requirements
            if requirement.is_pinned
        } if discarding_pre_releases_acceptable else set()

        for version, src_server in coll_versions:
            tmp_candidate = Candidate(fqcn, version, src_server, 'galaxy', None)

            for requirement in requirements:
                candidate_satisfies_requirement = self.is_satisfied_by(
                    requirement, tmp_candidate,
                )
                if not candidate_satisfies_requirement:
                    break

                should_disregard_pre_release_candidate = (
                    # NOTE: Do not discard pre-release candidates in the
                    # NOTE: following cases:
                    # NOTE:   * the end-user requested pre-releases explicitly;
                    # NOTE:   * the candidate is a concrete artifact (e.g. a
                    # NOTE:     Git repository, subdirs, a tarball URL, or a
                    # NOTE:     local dir or file etc.);
                    # NOTE:   * the candidate's pre-release version exactly
                    # NOTE:     matches a version specifically requested by one
                    # NOTE:     of the requirements in the current match
                    # NOTE:     discovery round (i.e. matching a requirement
                    # NOTE:     that is not a range but an explicit specific
                    # NOTE:     version pin). This works when some requirements
                    # NOTE:     request version ranges but others (possibly on
                    # NOTE:     different dependency tree level depths) demand
                    # NOTE:     pre-release dependency versions, even if those
                    # NOTE:     dependencies are transitive.
                    is_pre_release(tmp_candidate.ver)
                    and discarding_pre_releases_acceptable
                    and not (
                        self._with_pre_releases
                        or tmp_candidate.is_concrete_artifact
                        or version in all_pinned_requirement_version_numbers
                    )
                )
                if should_disregard_pre_release_candidate:
                    break

                # FIXME
                # candidate_is_from_requested_source = (
                #    requirement.src is None  # if this is true for some candidates but not all it will break key param - Nonetype can't be compared to str
                #    or requirement.src == candidate.src
                # )
                # if not candidate_is_from_requested_source:
                #     break

                if not self._include_signatures:
                    continue

                extra_signature_sources.extend(requirement.signature_sources or [])

            else:  # candidate satisfies requirements, `break` never happened
                if self._include_signatures:
                    for extra_source in extra_signature_sources:
                        signatures.append(get_signature_from_source(extra_source))
                latest_matches.append(
                    Candidate(fqcn, version, src_server, 'galaxy', frozenset(signatures))
                )

        latest_matches.sort(
            key=lambda candidate: (
                SemanticVersion(candidate.ver), candidate.src,
            ),
            reverse=True,  # prefer newer versions over older ones
        )

        if not preinstalled_candidates:
            preinstalled_candidates = {
                candidate for candidate in self._preferred_candidates
                if candidate.fqcn == fqcn and
                (
                    # check if an upgrade is necessary
                    all(self.is_satisfied_by(requirement, candidate) for requirement in requirements) and
                    (
                        not self._upgrade or
                        # check if an upgrade is preferred
                        all(SemanticVersion(latest.ver) <= SemanticVersion(candidate.ver) for latest in latest_matches)
                    )
                )
            }

        return list(preinstalled_candidates) + latest_matches

    def is_satisfied_by(self, requirement, candidate):
        # type: (Requirement, Candidate) -> bool
        r"""Whether the given requirement is satisfiable by a candidate.

        :param requirement: A requirement that produced the `candidate`.

        :param candidate: A pinned candidate supposedly matchine the \
                          `requirement` specifier. It is guaranteed to \
                          have been generated from the `requirement`.

        :returns: Indication whether the `candidate` is a viable \
                  solution to the `requirement`.
        """
        # NOTE: This is a set of Pipenv-inspired optimizations. Ref:
        # https://github.com/sarugaku/passa/blob/2ac00f1/src/passa/models/providers.py#L58-L74
        if (
                requirement.is_virtual or
                candidate.is_virtual or
                requirement.ver == '*'
        ):
            return True

        return meets_requirements(
            version=candidate.ver,
            requirements=requirement.ver,
        )

    def get_dependencies(self, candidate):
        # type: (Candidate) -> list[Candidate]
        r"""Get direct dependencies of a candidate.

        :returns: A collection of requirements that `candidate` \
                  specifies as its dependencies.
        """
        # FIXME: If there's several galaxy servers set, there may be a
        # FIXME: situation when the metadata of the same collection
        # FIXME: differs. So how do we resolve this case? Priority?
        # FIXME: Taking into account a pinned hash? Exploding on
        # FIXME: any differences?
        # NOTE: The underlying implmentation currently uses first found
        req_map = self._api_proxy.get_collection_dependencies(candidate)

        # NOTE: This guard expression MUST perform an early exit only
        # NOTE: after the `get_collection_dependencies()` call because
        # NOTE: internally it polulates the artifact URL of the candidate,
        # NOTE: its SHA hash and the Galaxy API token. These are still
        # NOTE: necessary with `--no-deps` because even with the disabled
        # NOTE: dependency resolution the outer layer will still need to
        # NOTE: know how to download and validate the artifact.
        #
        # NOTE: Virtual candidates should always return dependencies
        # NOTE: because they are ephemeral and non-installable.
        if not self._with_deps and not candidate.is_virtual:
            return []

        return [
            self._make_req_from_dict({'name': dep_name, 'version': dep_req})
            for dep_name, dep_req in req_map.items()
        ]


# Classes to handle resolvelib API changes between minor versions for 0.X
class CollectionDependencyProvider050(CollectionDependencyProviderBase):
    def find_matches(self, requirements):  # type: ignore[override]
        # type: (list[Requirement]) -> list[Candidate]
        return self._find_matches(requirements)

    def get_preference(self, resolution, candidates, information):  # type: ignore[override]
        # type: (t.Optional[Candidate], list[Candidate], list[t.NamedTuple]) -> t.Union[float, int]
        return self._get_preference(candidates)


class CollectionDependencyProvider060(CollectionDependencyProviderBase):
    def find_matches(self, identifier, requirements, incompatibilities):  # type: ignore[override]
        # type: (str, t.Mapping[str, t.Iterator[Requirement]], t.Mapping[str, t.Iterator[Requirement]]) -> list[Candidate]
        return [
            match for match in self._find_matches(list(requirements[identifier]))
            if not any(match.ver == incompat.ver for incompat in incompatibilities[identifier])
        ]

    def get_preference(self, resolution, candidates, information):  # type: ignore[override]
        # type: (t.Optional[Candidate], list[Candidate], list[t.NamedTuple]) -> t.Union[float, int]
        return self._get_preference(candidates)


class CollectionDependencyProvider070(CollectionDependencyProvider060):
    def get_preference(self, identifier, resolutions, candidates, information):  # type: ignore[override]
        # type: (str, t.Mapping[str, Candidate], t.Mapping[str, t.Iterator[Candidate]], t.Iterator[t.NamedTuple]) -> t.Union[float, int]
        return self._get_preference(list(candidates[identifier]))


class CollectionDependencyProvider080(CollectionDependencyProvider060):
    def get_preference(self, identifier, resolutions, candidates, information, backtrack_causes):  # type: ignore[override]
        # type: (str, t.Mapping[str, Candidate], t.Mapping[str, t.Iterator[Candidate]], t.Iterator[t.NamedTuple], t.Sequence) -> t.Union[float, int]
        return self._get_preference(list(candidates[identifier]))


def _get_provider():  # type () -> CollectionDependencyProviderBase
    if RESOLVELIB_VERSION >= SemanticVersion("0.8.0"):
        return CollectionDependencyProvider080
    if RESOLVELIB_VERSION >= SemanticVersion("0.7.0"):
        return CollectionDependencyProvider070
    if RESOLVELIB_VERSION >= SemanticVersion("0.6.0"):
        return CollectionDependencyProvider060
    return CollectionDependencyProvider050


CollectionDependencyProvider = _get_provider()
