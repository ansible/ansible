from __future__ import annotations

import importlib.abc
import importlib.util

import ansible
import pathlib
import pytest

from ansible.module_utils.common.messages import PluginInfo
from ansible.module_utils._internal import _deprecator


class FakePathLoader(importlib.abc.SourceLoader):
    """A test loader that can fake out the code/frame paths to simulate callers of various types without relying on actual files on disk."""
    def get_filename(self, fullname):
        if fullname.startswith('ansible.'):
            basepath = pathlib.Path(ansible.__file__).parent.parent
        else:
            basepath = '/x/y'

        return f'{basepath}/{fullname.replace(".", "/")}'

    def get_data(self, path):
        return b'''
from ansible.module_utils._internal import _deprecator

def do_stuff():
    return _deprecator.get_caller_plugin_info()
'''

    def exec_module(self, module):
        return super().exec_module(module)


@pytest.mark.parametrize("python_fq_name,expected_resolved_name,expected_plugin_type", (
    # legacy module callers
    ('ansible.legacy.blah', 'ansible.legacy.blah', 'module'),
    # core callers
    ('ansible.modules.ping', 'ansible.builtin.ping', 'module'),
    ('ansible.plugins.filters.core', _deprecator.ANSIBLE_CORE_DEPRECATOR.resolved_name, _deprecator.ANSIBLE_CORE_DEPRECATOR.type),
    ('ansible.plugins.tests.core', _deprecator.ANSIBLE_CORE_DEPRECATOR.resolved_name, _deprecator.ANSIBLE_CORE_DEPRECATOR.type),
    ('ansible.nonplugin_something', _deprecator.ANSIBLE_CORE_DEPRECATOR.resolved_name, _deprecator.ANSIBLE_CORE_DEPRECATOR.type),
    # collections plugin callers
    ('ansible_collections.foo.bar.plugins.modules.module_thing', 'foo.bar.module_thing', 'module'),
    ('ansible_collections.foo.bar.plugins.filter.somefilter', 'foo.bar', PluginInfo._COLLECTION_ONLY_TYPE),
    ('ansible_collections.foo.bar.plugins.test.sometest', 'foo.bar', PluginInfo._COLLECTION_ONLY_TYPE),
    # indeterminate callers (e.g. collection module_utils- must specify since they might be calling on behalf of another
    ('ansible_collections.foo.bar.plugins.module_utils.something',
     _deprecator.INDETERMINATE_DEPRECATOR.resolved_name, _deprecator.INDETERMINATE_DEPRECATOR.type),
    # other callers
    ('something.else', None, None),
    ('ansible_collections.foo.bar.nonplugin_something', None, None),
))
def test_get_caller_plugin_info(python_fq_name: str, expected_resolved_name: str, expected_plugin_type: str):
    """Validates the expected `PluginInfo` values received from various types of core/non-core/collection callers."""
    # invoke a standalone fake loader that generates a Python module with the specified FQ python name (converted to a corresponding __file__ entry) that
    # pretends as if it called `get_caller_plugin_info()` and returns its result
    loader = FakePathLoader()
    spec = importlib.util.spec_from_loader(name=python_fq_name, loader=loader)
    mod = importlib.util.module_from_spec(spec)

    loader.exec_module(mod)

    pi: PluginInfo = mod.do_stuff()

    if not expected_resolved_name and not expected_plugin_type:
        assert pi is None
        return

    assert pi is not None
    assert pi.resolved_name == expected_resolved_name
    assert pi.type == expected_plugin_type
