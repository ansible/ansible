from __future__ import annotations

import unittest
from unittest.mock import patch

import sys
import importlib.util
from pathlib import Path
import json
from types import ModuleType, SimpleNamespace


def load_cache_module_with_stubs(path: str):
    # Prepare minimal stub modules to satisfy relative imports used by the cache module
    # Create ansible and parent packages as empty modules if not present
    for pkg in ("ansible", "ansible._internal", "ansible._internal._plugins"):
        if pkg not in sys.modules:
            sys.modules[pkg] = ModuleType(pkg)

    # Stub for ansible._internal._wrapt providing ObjectProxy
    wrapt_mod = ModuleType("ansible._internal._wrapt")
    
    class _ObjectProxy:
        def __init__(self, wrapped):
            self.__wrapped__ = wrapped

    wrapt_mod.ObjectProxy = _ObjectProxy
    sys.modules["ansible._internal._wrapt"] = wrapt_mod

    # Stub for ansible._internal._json._profiles providing minimal _cache_persistence
    profiles_mod = ModuleType("ansible._internal._json._profiles")
    
    class _Profile:
        schema_id = 1

    
    class _Encoder(json.JSONEncoder):
        pass

    
    class _Decoder(json.JSONDecoder):
        pass

    # _cache_persistence must provide _Profile, Encoder and Decoder attributes used by the cache module
    cache_persistence = SimpleNamespace(_Profile=_Profile, Encoder=_Encoder, Decoder=_Decoder)
    profiles_mod._cache_persistence = cache_persistence
    sys.modules["ansible._internal._json._profiles"] = profiles_mod

    # Stub ansible.utils.display to avoid importing platform-specific real display
    display_mod = ModuleType("ansible.utils.display")
    
    class _StubDisplay:
        def __init__(self, *args, **kwargs):
            pass

        def vvv(self, msg, host=None):
            # no-op for tests
            return None

    display_mod.Display = _StubDisplay
    sys.modules["ansible.utils.display"] = display_mod

    # Load the module under package name so relative imports resolve
    mod_name = "ansible._internal._plugins._cache"
    spec = importlib.util.spec_from_file_location(mod_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load module spec for {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = module
    # Execute module
    spec.loader.exec_module(module)
    return module


# Load the cache module using local file path and stubs
# Build a cross-platform path to the lib module based on repository root
repo_root = Path(__file__).resolve().parents[3]
cache_module_path = str(repo_root.joinpath('lib', 'ansible', '_internal', '_plugins', '_cache.py'))
_module = load_cache_module_with_stubs(cache_module_path)
PluginInterposer = _module.PluginInterposer


class DummyBackend:
    def __init__(self):
        self.storage = {}

    def get(self, key):
        return self.storage.get(key)

    def set(self, key, value):
        self.storage[key] = value

    def keys(self):
        return list(self.storage.keys())

    def contains(self, key):
        return key in self.storage

    def delete(self, key):
        if key in self.storage:
            del self.storage[key]


class TestCacheVersionInvalidation(unittest.TestCase):
    def setUp(self):
        self.backend = DummyBackend()
        # wrap the dummy backend in the interposer
        self.plugin = PluginInterposer(self.backend)

    def test_version_mismatch_results_in_miss(self):
        # Simulate setting under version 2.15.0
        with patch('ansible.release.__version__', '2.15.0'):
            # patch config to enable version invalidation
            with patch('ansible.constants.config.get_config_value', return_value=True):
                # Clear any cached prefix so the patched version is used
                PluginInterposer._get_wrapped_key_prefix.cache_clear()
                self.plugin.set('host1', {'foo': 'bar'})
                # direct backend key should include version prefix
                backend_keys = self.backend.keys()
                assert any('2.15.0' in k for k in backend_keys)

        # Now simulate different running version 2.16.0
        with patch('ansible.release.__version__', '2.16.0'):
            with patch('ansible.constants.config.get_config_value', return_value=True):
                PluginInterposer._get_wrapped_key_prefix.cache_clear()
                result = self.plugin.get('host1')
                self.assertIsNone(result)

    def test_version_match_results_in_hit(self):
        with patch('ansible.release.__version__', '2.20.0'):
            with patch('ansible.constants.config.get_config_value', return_value=True):
                PluginInterposer._get_wrapped_key_prefix.cache_clear()
                self.plugin.set('host2', {'baz': 'qux'})
                PluginInterposer._get_wrapped_key_prefix.cache_clear()
                val = self.plugin.get('host2')
                self.assertIsInstance(val, dict)
                self.assertEqual(val.get('baz'), 'qux')

    def test_disabled_config_allows_cross_version(self):
        # Set under version A
        with patch('ansible.release.__version__', '2.0.0'):
            with patch('ansible.constants.config.get_config_value', return_value=False):
                PluginInterposer._get_wrapped_key_prefix.cache_clear()
                self.plugin.set('host3', {'x': 'y'})
                # ensure backend has a key (no version prefix expected)
                backend_keys = self.backend.keys()
                # As config disabled, prefix should be only schema id (not version)
                assert all('2.0.0' not in k for k in backend_keys)

        # Switch to version B but config still disabled
        with patch('ansible.release.__version__', '3.0.0'):
            with patch('ansible.constants.config.get_config_value', return_value=False):
                PluginInterposer._get_wrapped_key_prefix.cache_clear()
                val = self.plugin.get('host3')
                # Should still be found
                self.assertIsInstance(val, dict)
                self.assertEqual(val.get('x'), 'y')


if __name__ == '__main__':
    unittest.main()
