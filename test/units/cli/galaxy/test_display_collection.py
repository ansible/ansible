# -*- coding: utf-8 -*-
# Copyright (c) 2020 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import pytest

from ansible.cli.galaxy import _display_collection


@pytest.fixture
def collection_object(mocker):
    cobj = mocker.MagicMock(latest_version='1.5.0')
    cobj.__str__.return_value = 'sandwiches.ham'
    return cobj


def test_display_collection(capsys, collection_object):
    _display_collection(collection_object)
    out, err = capsys.readouterr()

    assert out == 'sandwiches.ham                             1.5.0                 \n'


def test_display_collections_small_widths(capsys, collection_object):
    _display_collection(collection_object, 1, 1)
    out, err = capsys.readouterr()

    assert out == 'sandwiches.ham 1.5.0\n'


def test_display_collections_large_widths(capsys, collection_object):
    _display_collection(collection_object, 15, 20)
    out, err = capsys.readouterr()

    assert out == 'sandwiches.ham  1.5.0               \n'
