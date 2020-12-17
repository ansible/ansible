"""Enable unit testing of Ansible collections. PYTEST_DONT_REWRITE"""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os

# set by ansible-test to a single directory, rather than a list of directories as supported by Ansible itself
ANSIBLE_COLLECTIONS_PATH = os.path.join(os.environ['ANSIBLE_COLLECTIONS_PATH'], 'ansible_collections')


# this monkeypatch to _pytest.pathlib.resolve_package_path fixes PEP420 resolution for collections in pytest >= 6.0.0
# NB: this code should never run under py2
def collection_resolve_package_path(path):
    """Configure the Python package path so that pytest can find our collections."""
    for parent in path.parents:
        if str(parent) == ANSIBLE_COLLECTIONS_PATH:
            return parent

    raise Exception('File "%s" not found in collection path "%s".' % (path, ANSIBLE_COLLECTIONS_PATH))


# this monkeypatch to py.path.local.LocalPath.pypkgpath fixes PEP420 resolution for collections in pytest < 6.0.0
def collection_pypkgpath(self):
    """Configure the Python package path so that pytest can find our collections."""
    for parent in self.parts(reverse=True):
        if str(parent) == ANSIBLE_COLLECTIONS_PATH:
            return parent

    raise Exception('File "%s" not found in collection path "%s".' % (self.strpath, ANSIBLE_COLLECTIONS_PATH))


def pytest_configure():
    """Configure this pytest plugin."""
    try:
        if pytest_configure.executed:
            return
    except AttributeError:
        pytest_configure.executed = True

    # noinspection PyProtectedMember
    from ansible.utils.collection_loader._collection_finder import _AnsibleCollectionFinder

    # allow unit tests to import code from collections

    # noinspection PyProtectedMember
    _AnsibleCollectionFinder(paths=[os.path.dirname(ANSIBLE_COLLECTIONS_PATH)])._install()  # pylint: disable=protected-access

    try:
        # noinspection PyProtectedMember
        from _pytest import pathlib as _pytest_pathlib
    except ImportError:
        _pytest_pathlib = None

    if hasattr(_pytest_pathlib, 'resolve_package_path'):
        _pytest_pathlib.resolve_package_path = collection_resolve_package_path
    else:
        # looks like pytest <= 6.0.0, use the old hack against py.path
        # noinspection PyProtectedMember
        import py._path.local

        # force collections unit tests to be loaded with the ansible_collections namespace
        # original idea from https://stackoverflow.com/questions/50174130/how-do-i-pytest-a-project-using-pep-420-namespace-packages/50175552#50175552
        # noinspection PyProtectedMember
        py._path.local.LocalPath.pypkgpath = collection_pypkgpath  # pylint: disable=protected-access


pytest_configure()
