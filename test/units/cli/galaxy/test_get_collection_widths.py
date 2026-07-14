# -*- coding: utf-8 -*-
# Copyright (c) 2020 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import pytest

from ansible.cli.galaxy import _get_collection_widths
from ansible.galaxy.dependency_resolution.dataclasses import Requirement


@pytest.fixture
def collection_objects():
    collection_ham = Requirement('sandwiches.ham', '1.5.0', None, 'galaxy', None)

    collection_pbj = Requirement('sandwiches.pbj', '2.5', None, 'galaxy', None)

    collection_reuben = Requirement('sandwiches.reuben', '4', None, 'galaxy', None)

    return [collection_ham, collection_pbj, collection_reuben]


def test_get_collection_widths(collection_objects):
    assert _get_collection_widths(collection_objects) == (17, 5)


def test_get_collection_widths_single_collection(mocker):
    mocked_collection = Requirement('sandwiches.club', '3.0.0', None, 'galaxy', None)
    # Make this look like it is not iterable
    mocker.patch('ansible.cli.galaxy.is_iterable', return_value=False)

    assert _get_collection_widths(mocked_collection) == (15, 5)
