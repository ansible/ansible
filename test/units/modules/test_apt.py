# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import annotations

import collections
from unittest.mock import Mock, patch, MagicMock

import pytest
from ansible.modules.apt import (
    expand_pkgspec_from_fnmatches,
    install_deb,
)

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


def test_install_deb_filters_virtual_packages():
    """Test that install_deb filters virtual packages correctly."""

    with patch('ansible.modules.apt.apt') as mock_apt, \
         patch('ansible.modules.apt.apt_pkg') as mock_apt_pkg:

        cache = MagicMock()
        cache.is_virtual_package.side_effect = lambda x: x == 'libglib2.0-0'
        cache.get_providing_packages.side_effect = lambda x: ['libglib2.0-0t64'] if x == 'libglib2.0-0' else []
        cache.__contains__.side_effect = lambda x: x in ['libglib2.0-0t64', 'real-package']
        cache.__getitem__.side_effect = lambda x: Mock(installed=True) if x == 'libglib2.0-0t64' else Mock(installed=False)

        mock_debfile = Mock()
        mock_pkg = Mock()
        mock_pkg.missing_deps = ['libglib2.0-0', 'real-package']
        mock_pkg.check.return_value = True
        mock_debfile.DebPackage.return_value = mock_pkg
        mock_apt.debfile = mock_debfile

        mock_apt.Cache.return_value = cache
        mock_apt_pkg.get_architectures.return_value = ['amd64']

        with patch('ansible.modules.apt.get_field_of_deb') as mock_get_field:
            mock_get_field.return_value = 'test-package'

            with patch('ansible.modules.apt.install') as mock_install:
                mock_install.return_value = (True, {})

                m = Mock()
                m.params = {"policy_rc_d": None}
                m.get_bin_path.return_value = "/usr/bin/apt-mark"
                m.run_command.return_value = (0, "", "")
                m.warn = Mock()
                m.fail_json = Mock(side_effect=AssertionError("Unexpected fail_json call"))

                install_deb(
                    m=m,
                    debs='/tmp/test.deb',
                    cache=cache,
                    force=False,
                    fail_on_autoremove=False,
                    install_recommends=False,
                    allow_unauthenticated=False,
                    allow_downgrade=False,
                    allow_change_held_packages=False,
                    dpkg_options='force-confnew',
                    lock_timeout=60
                )

                call_args = mock_install.call_args
                installed_deps = call_args[1]['pkgspec']

                print("deps_to_install:", installed_deps)
                assert 'libglib2.0-0' not in installed_deps
                assert 'real-package' in installed_deps
