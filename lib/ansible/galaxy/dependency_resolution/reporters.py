# -*- coding: utf-8 -*-
# Copyright: (c) 2020-2021, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""Requirement reporter implementations."""

from __future__ import annotations

from collections import defaultdict

try:
    from resolvelib import BaseReporter
except ImportError:
    class BaseReporter:  # type: ignore[no-redef]
        pass

try:
    from resolvelib.resolvers import Criterion
except ImportError:
    class Criterion:  # type: ignore[no-redef]
        pass

from ansible.utils.display import Display
from .dataclasses import Candidate, Requirement


display = Display()


_CLI_APP_NAME = 'ansible-galaxy'
_MESSAGES_AT_REJECT_COUNT = {
    1: (
        f'{_CLI_APP_NAME} is looking at multiple versions of {{fqcn}} to '
        'determine which version is compatible with other '
        'requirements. This could take a while.'
    ),
    8: (
        f'{_CLI_APP_NAME} is looking at multiple versions of {{fqcn}} to '
        'determine which version is compatible with other '
        'requirements. This could take a while.'
    ),
    13: (
        'This is taking longer than usual. You might need to provide '
        'the dependency resolver with stricter constraints to reduce '
        'runtime. If you want to abort this run, press Ctrl + C.'
    ),
}


class CollectionDependencyReporter(BaseReporter):
    """A dependency reporter for Ansible Collections.

    This is a proxy class allowing us to abstract away importing resolvelib
    outside of the `ansible.galaxy.dependency_resolution` Python package.
    """

    def __init__(self) -> None:
        """Initialize the collection rejection counter."""
        super().__init__()

        self.reject_count_by_fqcn: defaultdict[str, int] = defaultdict(int)

    def _maybe_log_rejection_message(self, candidate: Candidate) -> bool:
        """Print out rejection messages on pre-defined limit hits."""
        # Inspired by https://github.com/pypa/pip/commit/9731131
        self.reject_count_by_fqcn[candidate.fqcn] += 1

        collection_rejections_count = self.reject_count_by_fqcn[candidate.fqcn]

        if collection_rejections_count not in _MESSAGES_AT_REJECT_COUNT:
            return False

        collection_rejection_message = _MESSAGES_AT_REJECT_COUNT[
            collection_rejections_count
        ]
        display.display(collection_rejection_message.format(fqcn=candidate.fqcn))

        return True

    def rejecting_candidate(  # resolvelib >= 0.9.0
            self,
            criterion: Criterion[Candidate, Requirement],
            candidate: Candidate,
    ) -> None:
        """Augment rejection messages with conflict details."""
        if not self._maybe_log_rejection_message(candidate):
            return

        msg = 'Will try a different candidate, due to conflict:'
        for req_info in criterion.information:
            req, parent = req_info.requirement, req_info.parent
            msg += '\n    '
            if parent:
                msg += f'{parent !s} depends on '
            else:
                msg += 'The user requested '
            msg += str(req)
        display.v(msg)

    def backtracking(self, candidate: Candidate) -> None:  # resolvelib < 0.9.0
        """Print out rejection messages on pre-defined limit hits."""
        self._maybe_log_rejection_message(candidate)
