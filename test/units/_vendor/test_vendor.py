# (c) 2020 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
import pkgutil
import pytest
import sys

from units.compat.mock import MagicMock, NonCallableMagicMock, patch


def reset_internal_vendor_package():
    import ansible
    ansible_vendor_path = os.path.join(os.path.dirname(ansible.__file__), '_vendor')

    if ansible_vendor_path in sys.path:
        sys.path.remove(ansible_vendor_path)

    for pkg in ['ansible._vendor', 'ansible']:
        if pkg in sys.modules:
            del sys.modules[pkg]


def test_package_path_masking():
    from ansible import _vendor

    assert hasattr(_vendor, '__path__') and _vendor.__path__ == []


def test_no_vendored():
    reset_internal_vendor_package()
    with patch.object(pkgutil, 'iter_modules', return_value=[]):
        previous_path = list(sys.path)
        import ansible
        ansible_vendor_path = os.path.join(os.path.dirname(ansible.__file__), '_vendor')

        assert ansible_vendor_path not in sys.path
        assert sys.path == previous_path


def test_vendored(vendored_pkg_names=None):
    if not vendored_pkg_names:
        vendored_pkg_names = ['boguspkg']
    reset_internal_vendor_package()
    with patch.object(pkgutil, 'iter_modules', return_value=list((None, p, None) for p in vendored_pkg_names)):
        previous_path = list(sys.path)
        import ansible
        ansible_vendor_path = os.path.join(os.path.dirname(ansible.__file__), '_vendor')
        assert sys.path[0] == ansible_vendor_path

        if ansible_vendor_path in previous_path:
            previous_path.remove(ansible_vendor_path)

        assert sys.path[1:] == previous_path


def test_vendored_conflict():
    with pytest.warns(UserWarning) as w:
        import pkgutil
        import sys
        test_vendored(vendored_pkg_names=['sys', 'pkgutil'])  # pass a real package we know is already loaded
        assert 'pkgutil, sys' in str(w[0].message)  # ensure both conflicting modules are listed and sorted
