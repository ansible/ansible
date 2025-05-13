# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import annotations

import collections

from ansible.modules.apt import expand_pkgspec_from_fnmatches
import pytest

FakePackage = collections.namedtuple("Package", ("name",))
fake_cache = [
    FakePackage("apt"),
    FakePackage("apt-utils"),
    FakePackage("not-selected"),
]


@pytest.mark.parametrize(
    ("test_input", "expected"),
    [
        pytest.param(
            ["apt"],
            ["apt"],
            id="trivial",
        ),
        pytest.param(
            ["apt=1.0*"],
            ["apt=1.0*"],
            id="version-wildcard",
        ),
        pytest.param(
            ["apt*=1.0*"],
            ["apt", "apt-utils"],
            id="pkgname-wildcard-version",
        ),
        pytest.param(
            ["apt*"],
            ["apt", "apt-utils"],
            id="pkgname-expands",
        ),
    ],
)
def test_expand_pkgspec_from_fnmatches(test_input, expected):
    """Test positive cases of ``expand_pkgspec_from_fnmatches``."""
    assert expand_pkgspec_from_fnmatches(None, test_input, fake_cache) == expected
