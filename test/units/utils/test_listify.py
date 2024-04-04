# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import pytest

from ansible.template import Templar
from ansible.utils.listify import listify_lookup_plugin_terms

from units.mock.loader import DictDataLoader


@pytest.mark.parametrize(
    ("test_input", "expected"),
    [
        pytest.param(
            [],
            [],
            id="empty-list",
        ),
        pytest.param(
            "foo",
            ["foo"],
            id="string-types",
        ),
        pytest.param(
            ["foo"],
            ["foo"],
            id="list-types",
        ),
    ],
)
def test_listify_lookup_plugin_terms(test_input, expected):
    fake_loader = DictDataLoader({})
    templar = Templar(loader=fake_loader)

    terms = listify_lookup_plugin_terms(
        test_input, templar=templar, fail_on_undefined=False
    )
    assert terms == expected


def test_negative_listify_lookup_plugin_terms():
    fake_loader = DictDataLoader({})
    templar = Templar(loader=fake_loader)

    with pytest.raises(TypeError, match=".*got an unexpected keyword argument 'loader'"):
        listify_lookup_plugin_terms(
            "foo", templar=templar, loader=fake_loader, fail_on_undefined=False
        )
