# -*- coding: utf-8 -*-
# Copyright (c) 2020 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import pytest

from ansible.cli.galaxy import _get_collection_widths


@pytest.fixture
def collection_objects(mocker):
    collection_ham = mocker.MagicMock(latest_version='1.5.0')
    collection_ham.__str__.return_value = 'sandwiches.ham'

    collection_pbj = mocker.MagicMock(latest_version='2.5')
    collection_pbj.__str__.return_value = 'sandwiches.pbj'

    collection_reuben = mocker.MagicMock(latest_version='4')
    collection_reuben.__str__.return_value = 'sandwiches.reuben'

    return [collection_ham, collection_pbj, collection_reuben]


def test_get_collection_widths(collection_objects):
    assert _get_collection_widths(collection_objects) == (17, 5)


def test_get_collection_widths_single_collection(mocker):
    mocked_collection = mocker.MagicMock(latest_version='3.0.0')
    mocked_collection.__str__.return_value = 'sandwiches.club'
    # Make this look like it is not iterable
    mocker.patch('ansible.cli.galaxy.is_iterable', return_value=False)

    assert _get_collection_widths(mocked_collection) == (15, 5)
