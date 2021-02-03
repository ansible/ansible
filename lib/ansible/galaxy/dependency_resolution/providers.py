# -*- coding: utf-8 -*-
# Copyright: (c) 2020-2021, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""Requirement provider interfaces."""

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import functools

try:
    from typing import TYPE_CHECKING
except ImportError:
    TYPE_CHECKING = False

if TYPE_CHECKING:
    from typing import Iterable, List, NamedTuple, Optional, Union
    from ansible.galaxy.collection.concrete_artifact_manager import (
        ConcreteArtifactsManager,
    )
    from ansible.galaxy.collection.galaxy_api_proxy import MultiGalaxyAPIProxy

from ansible.galaxy.dependency_resolution.dataclasses import (
    Candidate,
    Requirement,
)
from ansible.galaxy.dependency_resolution.versioning import (
    is_pre_release,
    meets_requirements,
)
from ansible.utils.version import SemanticVersion

from resolvelib import AbstractProvider


class CollectionDependencyProvider(AbstractProvider):
    """Delegate providing a requirement interface for the resolver."""

    def __init__(
            self,  # type: CollectionDependencyProvider
            apis,  # type: MultiGalaxyAPIProxy
            concrete_artifacts_manager=None,  # type: ConcreteArtifactsManager
            user_requirements=None,  # type: Iterable[Requirement]
            preferred_candidates=None,  # type: Iterable[Candidate]
            with_deps=True,  # type: bool
            with_pre_releases=False,  # type: bool
            upgrade=False,  # type: bool
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
        """
        self._api_proxy = apis
        self._make_req_from_dict = functools.partial(
            Requirement.from_requirement_dict,
            art_mgr=concrete_artifacts_manager,
        )
        self._pinned_candidate_requests = set(
            Candidate(req.fqcn, req.ver, req.src, req.type)
            for req in (user_requirements or ())
            if req.is_concrete_artifact or (
                req.ver != '*' and
                not req.ver.startswith(('<', '>', '!='))
            )
        )
        self._preferred_candidates = set(preferred_candidates or ())
        self._with_deps = with_deps
        self._with_pre_releases = with_pre_releases
        self._upgrade = upgrade

    def _is_user_requested(self, candidate):  # type: (Candidate) -> bool
        """Check if the candidate is requested by the user."""
        if candidate in self._pinned_candidate_requests:
            return True

        if candidate.is_online_index_pointer and candidate.src is not None:
            # NOTE: Candidate is a namedtuple, it has a source server set
            # NOTE: to a specific GalaxyAPI instance or `None`. When the
            # NOTE: user runs
            # NOTE:
            # NOTE:     $ ansible-galaxy collection install ns.coll
            # NOTE:
            # NOTE: then it's saved in `self._pinned_candidate_requests`
            # NOTE: as `('ns.coll', '*', None, 'galaxy')` but then
            # NOTE: `self.find_matches()` calls `self.is_satisfied_by()`
            # NOTE: with Candidate instances bound to each specific
            # NOTE: server available, those look like
            # NOTE: `('ns.coll', '*', GalaxyAPI(...), 'galaxy')` and
            # NOTE: wouldn't match the user requests saved in
            # NOTE: `self._pinned_candidate_requests`. This is why we
            # NOTE: normalize the collection to have `src=None` and try
            # NOTE: again.
            # NOTE:
            # NOTE: When the user request comes from `requirements.yml`
            # NOTE: with the `source:` set, it'll match the first check
            # NOTE: but it still can have entries with `src=None` so this
            # NOTE: normalized check is still necessary.
            return Candidate(
                candidate.fqcn, candidate.ver, None, candidate.type,
            ) in self._pinned_candidate_requests

        return False

    def identify(self, requirement_or_candidate):
        # type: (Union[Candidate, Requirement]) -> str
        """Given requirement or candidate, return an identifier for it.

        This is used to identify a requirement or candidate, e.g.
        whether two requirements should have their specifier parts
        (version ranges or pins) merged, whether two candidates would
        conflict with each other (because they have same name but
        different versions).
        """
        return requirement_or_candidate.canonical_package_id

    def get_preference(
            self,  # type: CollectionDependencyProvider
            resolution,  # type: Optional[Candidate]
            candidates,  # type: List[Candidate]
            information,  # type: List[NamedTuple]
    ):  # type: (...) -> Union[float, int]
        """Return sort key function return value for given requirement.

        This result should be based on preference that is defined as
        "I think this requirement should be resolved first".
        The lower the return value is, the more preferred this
        group of arguments is.

        :param resolution: Currently pinned candidate, or ``None``.

        :param candidates: A list of possible candidates.

        :param information: A list of requirement information.

        Each ``information`` instance is a named tuple with two entries:

          * ``requirement`` specifies a requirement contributing to
            the current candidate list

          * ``parent`` specifies the candidate that provides
            (dependend on) the requirement, or `None`
            to indicate a root requirement.

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
        if any(
                candidate in self._preferred_candidates
                for candidate in candidates
        ):
            # NOTE: Prefer pre-installed candidates over newer versions
            # NOTE: available from Galaxy or other sources.
            return float('-inf')
        return len(candidates)

    def find_matches(self, requirements):
        # type: (List[Requirement]) -> List[Candidate]
        r"""Find all possible candidates satisfying given requirements.

        This tries to get candidates based on the requirements' types.

        For concrete requirements (SCM, dir, namespace dir, local or
        remote archives), the one-and-only match is returned

        For a "named" requirement, Galaxy-compatible APIs are consulted
        to find concrete candidates for this requirement. Of theres a
        pre-installed candidate, it's prepended in front of others.

        :param requirements: A collection of requirements which all of \
                             the returned candidates must match. \
                             All requirements are guaranteed to have \
                             the same identifier. \
                             The collection is never empty.

        :returns: An iterable that orders candidates by preference, \
                  e.g. the most preferred candidate comes first.
        """
        # FIXME: The first requirement may be a Git repo followed by
        # FIXME: its cloned tmp dir. Using only the first one creates
        # FIXME: loops that prevent any further dependency exploration.
        # FIXME: We need to figure out how to prevent this.
        first_req = requirements[0]
        fqcn = first_req.fqcn
        # The fqcn is guaranteed to be the same
        coll_versions = self._api_proxy.get_collection_versions(first_req)
        if first_req.is_concrete_artifact:
            # FIXME: do we assume that all the following artifacts are also concrete?
            # FIXME: does using fqcn==None cause us problems here?

            return [
                Candidate(fqcn, version, _none_src_server, first_req.type)
                for version, _none_src_server in coll_versions
            ]

        latest_matches = sorted(
            {
                candidate for candidate in (
                    Candidate(fqcn, version, src_server, 'galaxy')
                    for version, src_server in coll_versions
                )
                if all(self.is_satisfied_by(requirement, candidate) for requirement in requirements)
                # FIXME
                # if all(self.is_satisfied_by(requirement, candidate) and (
                #     requirement.src is None or  # if this is true for some candidates but not all it will break key param - Nonetype can't be compared to str
                #     requirement.src == candidate.src
                # ))
            },
            key=lambda candidate: (
                SemanticVersion(candidate.ver), candidate.src,
            ),
            reverse=True,  # prefer newer versions over older ones
        )

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
        # NOTE: Only allow pre-release candidates if we want pre-releases
        # NOTE: or the req ver was an exact match with the pre-release
        # NOTE: version. Another case where we'd want to allow
        # NOTE: pre-releases is when there are several user requirements
        # NOTE: and one of them is a pre-release that also matches a
        # NOTE: transitive dependency of another requirement.
        allow_pre_release = self._with_pre_releases or not (
            requirement.ver == '*' or
            requirement.ver.startswith('<') or
            requirement.ver.startswith('>') or
            requirement.ver.startswith('!=')
        ) or self._is_user_requested(candidate)
        if is_pre_release(candidate.ver) and not allow_pre_release:
            return False

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
        # type: (Candidate) -> List[Candidate]
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
