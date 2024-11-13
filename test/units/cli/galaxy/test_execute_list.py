# -*- coding: utf-8 -*-
# Copyright (c) 2020 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import pytest

from ansible import context
from ansible.cli.galaxy import GalaxyCLI


@pytest.mark.parametrize(
    ("installable_content_type", "expected"),
    [
        pytest.param("role", (1, 0), id="list-role-called"),
        pytest.param("collection", (0, 1), id="list-collection-called"),
    ],
)
def test_execute_list(mocker, installable_content_type, expected):
    """Make sure the correct method is called for a role"""

    gc = GalaxyCLI(["ansible-galaxy", installable_content_type, "list"])
    context.CLIARGS._store = {"type": installable_content_type}
    execute_list_role_mock = mocker.patch(
        "ansible.cli.galaxy.GalaxyCLI.execute_list_role",
        side_effect=AttributeError("raised intentionally"),
    )
    execute_list_collection_mock = mocker.patch(
        "ansible.cli.galaxy.GalaxyCLI.execute_list_collection",
        side_effect=AttributeError("raised intentionally"),
    )
    with pytest.raises(AttributeError):
        gc.execute_list()

    assert execute_list_role_mock.call_count == expected[0]
    assert execute_list_collection_mock.call_count == expected[1]
