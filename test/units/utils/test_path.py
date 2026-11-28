from __future__ import annotations

import os

from ansible.utils.path import is_subpath


def test_is_subpath_of_filesystem_root():
    root = os.path.abspath(os.sep)
    child = os.path.join(root, 'ansible-subpath-test')

    assert is_subpath(child, root) is True


def test_is_subpath_rejects_sibling_prefix():
    parent = os.path.join(os.path.abspath(os.sep), 'ansible-subpath-parent')
    sibling = parent + '-sibling'

    assert is_subpath(sibling, parent) is False
