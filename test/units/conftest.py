# Try to globally patch Templar trust check failures to be fatal for all unit tests

from __future__ import annotations

import pytest
import sys
import typing as t

import pytest_mock

try:
    from ansible import _internal  # sets is_controller=True in controller context
    from ansible.module_utils._internal import is_controller  # allow checking is_controller
    from ansible._internal._templating._jinja_common import _TemplateConfig
    from ansible._internal._errors._handler import ErrorHandler, ErrorAction
except ImportError:
    # likely doing only module_utils testing; ignore here and rely on test_templar::test_trust_fail_raises_in_tests to ensure the right behavior
    pass
else:
    assert _internal
    assert is_controller

    # Ensure unit tests fail when encountering untrusted templates to reduce mistakes in tests.
    # Tests that need to ignore or warn on untrusted templates will need to override this setting.
    _TemplateConfig.untrusted_template_handler = ErrorHandler(ErrorAction.ERROR)

    from .controller_only_conftest import *  # pylint: disable=wildcard-import,unused-wildcard-import

from ansible.module_utils import _internal as _module_utils_internal
from ansible.module_utils._internal import _traceback as _module_utils_internal_traceback


def pytest_configure(config: pytest.Config):
    config.addinivalue_line("markers", "autoparam(value): metadata-driven parametrization")
    config.addinivalue_line("markers", "allow_delazify: test will delazify the result")


@pytest.fixture
def collection_loader() -> t.Iterator[None]:
    """
    Provide a collection loader with no collections.
    Useful for tests that fail without a collection loader, but that don't actually depend on collections.
    """
    from ansible.utils.collection_loader._collection_finder import _AnsibleCollectionFinder

    _AnsibleCollectionFinder()._install()

    try:
        yield
    finally:
        _AnsibleCollectionFinder._remove()

        for module_to_nuke in [m for m in sys.modules if m.startswith('ansible_collections')]:
            sys.modules.pop(module_to_nuke)


# @pytest.fixture(autouse=True)
# def prevent_collection_loader_leak(request: pytest.FixtureRequest):
#     # DTFIX-FUTURE: enable this fixture to ensure the collection loader has not "leaked"
#     for finder in sys.meta_path:
#         if "_AnsibleCollectionFinder" in type(finder).__name__:
#             finder._remove()
#             assert False, f"a finder was active before test {request.node.name}"
#
#     yield
#
#     for finder in sys.meta_path:
#         if "_AnsibleCollectionFinder" in type(finder).__name__:
#             finder._remove()
#             assert False, f"a finder was active after test {request.node.name}"


def pytest_collection_finish(session: pytest.Session):
    """
    This hook ensures that a collection loader is not installed after test import/collection.
    The presence of a collection loader pollutes test state in various undesirable ways.
    """
    for finder in sys.meta_path:
        if "_AnsibleCollectionFinder" in type(finder).__name__:
            assert False, "a collection loader was active after collection"


@pytest.fixture
def as_target(mocker: pytest_mock.MockerFixture) -> None:
    """Force execution in the context of a target host instead of the controller."""
    mocker.patch.object(_module_utils_internal, 'is_controller', False)
    mocker.patch.object(_module_utils_internal_traceback, '_is_traceback_enabled', _module_utils_internal_traceback._is_module_traceback_enabled)
