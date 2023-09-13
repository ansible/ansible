# -*- coding: utf-8 -*-
# Copyright: (c) 2020-2021, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""Requiement reporter implementations."""

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

try:
    from resolvelib import BaseReporter
except ImportError:
    class BaseReporter:  # type: ignore[no-redef]
        pass


class CollectionDependencyReporter(BaseReporter):
    """A dependency reporter for Ansible Collections.

    This is a proxy class allowing us to abstract away importing resolvelib
    outside of the `ansible.galaxy.dependency_resolution` Python package.
    """


from logging import basicConfig, DEBUG, getLogger
from sys import stdout


basicConfig(stream=stdout, level=DEBUG)
logger = getLogger(__name__)
logger.info('INFO THING')
logger.debug('DEBUG THING')

from typing import Any
from .dataclasses import Candidate, Requirement


class CollectionDependencyDebuggingReporter(CollectionDependencyReporter):
    """A reporter that does an info log for every event it sees."""

    def starting(self) -> None:
        logger.info("Reporter.starting()")

    def starting_round(self, index: int) -> None:
        logger.info("Reporter.starting_round(%r)", index)

    def ending_round(self, index: int, state: Any) -> None:
        logger.info("Reporter.ending_round(%r, %r)", index, state)

    def ending(self, state: Any) -> None:
        logger.info("Reporter.ending(%r)", state)

    def adding_requirement(self, requirement: Requirement, parent: Candidate) -> None:
        logger.info("Reporter.adding_requirement(%r, %r)", requirement, parent)

    def rejecting_candidate(self, criterion: Any, candidate: Candidate) -> None:
        logger.info("Reporter.rejecting_candidate(%r, %r)", criterion, candidate)

    backtracking = rejecting_candidate  # Old pre-v0.9.0 resolvelib hook name

    def pinning(self, candidate: Candidate) -> None:
        logger.info("Reporter.pinning(%r)", candidate)

    def pinning(self, candidate: Candidate) -> None:
        logger.info("Reporter.pinning(%r)", candidate)
