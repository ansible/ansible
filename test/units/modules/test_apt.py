# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import annotations

import collections
import warnings

from ansible.modules.apt import expand_pkgspec_from_fnmatches, fetch_failed_reason
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


@pytest.mark.parametrize(
    ("exception", "apt_warnings", "expected"),
    [
        pytest.param(
            Exception("E:The repository is not signed."),
            ["W:Signature verification failed"],
            "E:The repository is not signed.",
            id="exception-text-before-warnings",
        ),
        pytest.param(
            Exception(),
            ["W:first", "W:second"],
            "W:first, W:second",
            id="warnings-joined",
        ),
        pytest.param(
            Exception(),
            [],
            "unknown reason",
            id="no-text",
        ),
    ],
)
def test_fetch_failed_reason(exception, apt_warnings, expected):
    """Test the cases of ``fetch_failed_reason`` that the integration tests don't cover."""
    with warnings.catch_warnings(record=True) as recorded:
        warnings.simplefilter("always")
        for apt_warning in apt_warnings:
            warnings.warn(apt_warning)

    assert fetch_failed_reason(exception, recorded) == expected
