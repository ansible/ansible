# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import typing as t

import pytest
import pytest_mock

from ansible.utils.display import Display
from ansible.utils.listify import listify_lookup_plugin_terms


@pytest.mark.parametrize("test_input, expected", (
    ([], []),
    ("foo", ["foo"]),
    (["foo"], ["foo"]),
), ids=str)
def test_listify_lookup_plugin_terms(test_input: t.Any, expected: t.Any, mocker: pytest_mock.MockerFixture) -> None:
    with mocker.patch.object(Display(), 'deprecated'):  # as deprecated:
        assert listify_lookup_plugin_terms(test_input) == expected

    # deprecated: description="Calling listify_lookup_plugin_terms function is not necessary; the function should be deprecated." core_version="2.23"
    # deprecated.assert_called_once_with(
    #     msg='"listify_lookup_plugin_terms" is obsolete and in most cases unnecessary',
    #     version='2.23',
    # )
