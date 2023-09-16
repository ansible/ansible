# -*- coding: utf-8 -*-
# Copyright: (c) 2020-2021, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""Requiement reporter implementations."""

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import typing as t
from collections import defaultdict
from logging import getLogger

try:
    from resolvelib import BaseReporter
except ImportError:
    class BaseReporter:  # type: ignore[no-redef]
        pass

from .dataclasses import Candidate


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

_logger = getLogger(__name__)


class CollectionDependencyReporter(BaseReporter):
    """A dependency reporter for Ansible Collections.

    This is a proxy class allowing us to abstract away importing resolvelib
    outside of the `ansible.galaxy.dependency_resolution` Python package.
    """

    def __init__(self) -> None:
        super().__init__()

        self.reject_count_by_fqcn: t.DefaultDict[str, int] = defaultdict(int)

    def rejecting_candidate(
            self,
            criterion: t.Any,
            candidate: Candidate,
    ) -> None:
        # Inspired by https://github.com/pypa/pip/commit/9731131
        self.reject_count_by_fqcn[candidate.fqcn] += 1

        collection_rejections_count = self.reject_count_by_fqcn[candidate.fqcn]
        try:
            collection_rejection_message = _MESSAGES_AT_REJECT_COUNT[
                collection_rejections_count
            ]
        except KeyError:
            return

        _logger.info(collection_rejection_message.format(fqcn=candidate.fqcn))

        msg = 'Will try a different candidate, due to conflict:'
        for req_info in criterion.information:
            req, parent = req_info.requirement, req_info.parent
            msg += '\n    '
            if parent:
                msg += f'{parent !r} depends on '
            else:
                msg += 'The user requested '
            msg += repr(req)
        _logger.debug(msg)

    backtracking = rejecting_candidate
