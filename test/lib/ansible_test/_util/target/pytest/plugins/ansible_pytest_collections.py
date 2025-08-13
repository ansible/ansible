"""Enable unit testing of Ansible collections. PYTEST_DONT_REWRITE"""

from __future__ import annotations

import os

# set by ansible-test to a single directory, rather than a list of directories as supported by Ansible itself
ANSIBLE_COLLECTIONS_PATH = os.path.join(os.environ['ANSIBLE_COLLECTIONS_PATH'], 'ansible_collections')

# set by ansible-test to the minimum python version supported on the controller
ANSIBLE_CONTROLLER_MIN_PYTHON_VERSION = tuple(int(x) for x in os.environ['ANSIBLE_CONTROLLER_MIN_PYTHON_VERSION'].split('.'))


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


def enable_assertion_rewriting_hook():  # type: () -> None
    """
    Enable pytest's AssertionRewritingHook on Python 3.x.
    This is necessary because the Ansible collection loader intercepts imports before the pytest provided loader ever sees them.
    """
    import sys

    hook_name = '_pytest.assertion.rewrite.AssertionRewritingHook'
    hooks = [hook for hook in sys.meta_path if hook.__class__.__module__ + '.' + hook.__class__.__qualname__ == hook_name]

    if len(hooks) != 1:
        raise Exception('Found {} instance(s) of "{}" in sys.meta_path.'.format(len(hooks), hook_name))

    assertion_rewriting_hook = hooks[0]

    # This is based on `_AnsibleCollectionPkgLoaderBase.exec_module` from `ansible/utils/collection_loader/_collection_finder.py`.
    def exec_module(self, module):
        # short-circuit redirect; avoid reinitializing existing modules
        if self._redirect_module:  # pylint: disable=protected-access
            return

        # execute the module's code in its namespace
        code_obj = self.get_code(self._fullname)  # pylint: disable=protected-access

        if code_obj is not None:  # things like NS packages that can't have code on disk will return None
            # This logic is loosely based on `AssertionRewritingHook._should_rewrite` from pytest.
            # See: https://github.com/pytest-dev/pytest/blob/779a87aada33af444f14841a04344016a087669e/src/_pytest/assertion/rewrite.py#L209
            should_rewrite = self._package_to_load == 'conftest' or self._package_to_load.startswith('test_')  # pylint: disable=protected-access

            if should_rewrite:
                # noinspection PyUnresolvedReferences
                assertion_rewriting_hook.exec_module(module)
            else:
                exec(code_obj, module.__dict__)  # pylint: disable=exec-used

    # noinspection PyProtectedMember
    from ansible.utils.collection_loader._collection_finder import _AnsibleCollectionPkgLoaderBase

    _AnsibleCollectionPkgLoaderBase.exec_module = exec_module  # type: ignore[method-assign]


def pytest_configure():
    """Configure this pytest plugin."""
    try:
        if pytest_configure.executed:
            return
    except AttributeError:
        pytest_configure.executed = True

    enable_assertion_rewriting_hook()

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
