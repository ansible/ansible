# -*- coding: utf-8 -*-
# Copyright (c) 2020 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import pytest

from ansible.cli.galaxy import _display_collection
from ansible.galaxy.dependency_resolution.dataclasses import Requirement


@pytest.fixture
def collection_object():
    def _cobj(fqcn="sandwiches.ham"):
        return Requirement(fqcn, "1.5.0", None, "galaxy", None)

    return _cobj


@pytest.mark.parametrize(
    ("kwargs", "expected"),
    [
        pytest.param(
            {},
            "sandwiches.ham 1.5.0  \n",
            id="default",
        ),
        pytest.param(
            {"cwidth": 1, "vwidth": 1},
            "sandwiches.ham 1.5.0  \n",
            id="small-max-widths",
        ),
        pytest.param(
            {"cwidth": 20, "vwidth": 20},
            "sandwiches.ham       1.5.0               \n",
            id="large-max-widths",
        ),
        pytest.param(
            {"min_cwidth": 0, "min_vwidth": 0},
            "sandwiches.ham 1.5.0  \n",
            id="small-minimum-widths",
        ),
    ],
)
def test_display_collection(capsys, kwargs, expected, collection_object):
    _display_collection(collection_object(), **kwargs)
    out, dummy = capsys.readouterr()
    assert out == expected
