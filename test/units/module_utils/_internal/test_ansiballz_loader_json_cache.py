"""Tests for ansiballz loader JSON profile eager-loading fix.

Verifies that calling get_module_encoder() caches the JSON serialization
profile module in sys.modules, so subsequent importlib.util.find_spec()
calls succeed even when the source zip is no longer available.
"""

from __future__ import annotations

import importlib.util
import sys

import pytest

from ansible.module_utils.common.json import get_module_encoder, Direction
from ansible.module_utils._internal._json import (
    get_module_serialization_profile_name,
    get_serialization_module_name,
)


class TestJsonProfileEagerLoad:
    """Verify that eager-loading the JSON profile populates sys.modules."""

    @pytest.fixture(autouse=True)
    def _clear_profile_cache(self):
        """Remove cached JSON profile modules from sys.modules before each test."""
        profile_prefix = 'ansible.module_utils._internal._json._profiles.'
        cached = [k for k in sys.modules if k.startswith(profile_prefix)]
        saved = {k: sys.modules.pop(k) for k in cached}
        yield
        # Restore after test to avoid side effects on other tests
        sys.modules.update(saved)

    @pytest.mark.parametrize('profile', ['legacy', 'modern'])
    def test_get_module_encoder_caches_profile_in_sys_modules(self, profile):
        """After calling get_module_encoder(), the profile module must be in sys.modules."""
        # Derive the expected fully-qualified module name for module-to-controller direction
        profile_name = get_module_serialization_profile_name(profile, controller_to_module=False)
        expected_module_name = get_serialization_module_name(profile_name)

        # Ensure it is NOT in sys.modules before the call
        sys.modules.pop(expected_module_name, None)
        assert expected_module_name not in sys.modules

        # This is the call the fix adds to run_module() -- it should cache the profile
        get_module_encoder(profile, Direction.MODULE_TO_CONTROLLER)

        # Now the profile module must be cached
        assert expected_module_name in sys.modules

    @pytest.mark.parametrize('profile', ['legacy', 'modern'])
    def test_find_spec_succeeds_after_eager_load(self, profile):
        """After eager-loading, importlib.util.find_spec() must succeed for the profile module."""
        profile_name = get_module_serialization_profile_name(profile, controller_to_module=False)
        expected_module_name = get_serialization_module_name(profile_name)

        # Eager-load (simulates the fix in run_module)
        get_module_encoder(profile, Direction.MODULE_TO_CONTROLLER)

        # find_spec must resolve without touching the filesystem
        spec = importlib.util.find_spec(expected_module_name)
        assert spec is not None
        assert spec.name == expected_module_name
