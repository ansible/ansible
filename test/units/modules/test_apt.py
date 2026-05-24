# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import annotations

import collections

from ansible.modules.apt import expand_pkgspec_from_fnmatches
from ansible.modules import apt as apt_module
from unittest.mock import MagicMock, patch
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

    from unittest.mock import MagicMock, patch

    from ansible.modules import apt as apt_module


def test_remove_passes_allow_downgrades_flag():
    """Regression test for https://github.com/ansible/ansible/issues/85804."""
    module = MagicMock()
    module.check_mode = False
    module.run_command.return_value = (0, '', '')

    with patch.object(apt_module, 'expand_pkgspec_from_fnmatches', return_value=['foo']), \
            patch.object(apt_module, 'package_split', return_value=('foo', None, None)), \
            patch.object(apt_module, 'package_status', return_value=(True, '1.0', False, False)), \
            patch.object(apt_module, 'PolicyRcD'), \
            patch.object(apt_module, 'parse_diff', return_value={}), \
            patch.object(apt_module, 'APT_GET_CMD', '/usr/bin/apt-get', create=True):
        apt_module.remove(module, ['foo'], MagicMock(), allow_downgrade=True)

    cmd = module.run_command.call_args[0][0]
    assert '--allow-downgrades' in cmd
    assert '--allow-downgrade ' not in cmd  # guard against singular-flag regression
