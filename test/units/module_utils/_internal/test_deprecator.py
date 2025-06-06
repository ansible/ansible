from __future__ import annotations

import importlib.abc
import importlib.util

import ansible
import pathlib
import pytest

from ansible.module_utils._internal import _messages
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


@pytest.mark.parametrize("python_fq_name,expected_plugin_info", (
    # legacy module callers
    ('ansible.legacy.blah', _messages.PluginInfo(resolved_name='ansible.legacy.blah', type=_messages.PluginType.MODULE)),
    # core callers
    ('ansible.modules.ping', _messages.PluginInfo(resolved_name='ansible.builtin.ping', type=_messages.PluginType.MODULE)),
    ('ansible.plugins.filter.core', _deprecator.ANSIBLE_CORE_DEPRECATOR),
    ('ansible.plugins.test.core', _deprecator.ANSIBLE_CORE_DEPRECATOR),
    ('ansible.nonplugin_something', _deprecator.ANSIBLE_CORE_DEPRECATOR),
    # collections plugin callers
    ('ansible_collections.foo.bar.plugins.modules.module_thing', _messages.PluginInfo(resolved_name='foo.bar.module_thing', type=_messages.PluginType.MODULE)),
    ('ansible_collections.foo.bar.plugins.filter.somefilter', _messages.PluginInfo(resolved_name='foo.bar', type=None)),
    ('ansible_collections.foo.bar.plugins.test.sometest', _messages.PluginInfo(resolved_name='foo.bar', type=None)),
    # indeterminate callers (e.g. collection module_utils- must specify since they might be calling on behalf of another
    ('ansible_collections.foo.bar.plugins.module_utils.something', _deprecator.INDETERMINATE_DEPRECATOR),
    # other callers
    ('something.else', None),
    ('ansible_collections.foo.bar.nonplugin_something', None),
))
def test_get_caller_plugin_info(python_fq_name: str, expected_plugin_info: _messages.PluginInfo):
    """Validates the expected `PluginInfo` values received from various types of core/non-core/collection callers."""
    # invoke a standalone fake loader that generates a Python module with the specified FQ python name (converted to a corresponding __file__ entry) that
    # pretends as if it called `get_caller_plugin_info()` and returns its result
    loader = FakePathLoader()
    spec = importlib.util.spec_from_loader(name=python_fq_name, loader=loader)
    mod = importlib.util.module_from_spec(spec)

    loader.exec_module(mod)

    pi: _messages.PluginInfo = mod.do_stuff()

    assert pi == expected_plugin_info
