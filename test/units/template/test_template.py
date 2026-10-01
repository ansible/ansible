# Copyright: (c) 2026, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

from units.mock.loader import DictDataLoader

from ansible.plugins.loader import init_plugin_loader
from ansible.template import Templar, AnsibleNativeEnvironment


DEPRECATION_MSG = 'Direct access to the `_loader` internal attribute is deprecated. Use `copy_with_new_env` to create a new instance.'


def test_loader_get_deprecation(mocker):
    loader = DictDataLoader({})
    templar = Templar(loader=loader)
    mock_deprecated = mocker.patch('ansible.template.display.deprecated')

    assert templar._loader is loader

    mock_deprecated.assert_called_once_with(msg=DEPRECATION_MSG, version='2.23')


def test_loader_set_deprecation(mocker):
    templar = Templar(loader=DictDataLoader({}))
    new_loader = DictDataLoader({'/path/to/my_file.txt': 'foo\n'})
    mock_deprecated = mocker.patch('ansible.template.display.deprecated')

    templar._loader = new_loader

    mock_deprecated.assert_called_once_with(msg=DEPRECATION_MSG, version='2.23')
    assert templar._dataloader is new_loader


def test_dataloader_no_deprecation(mocker):
    """The replacement attribute must not emit the deprecation warning."""
    loader = DictDataLoader({})
    mock_deprecated = mocker.patch('ansible.template.display.deprecated')

    templar = Templar(loader=loader)
    assert templar._dataloader is loader

    templar._dataloader = new_loader = DictDataLoader({})
    assert templar._dataloader is new_loader

    mock_deprecated.assert_not_called()


def test_lookup_no_deprecation(mocker):
    """Internal lookup handling must use `_dataloader`, not the deprecated property."""
    init_plugin_loader()
    templar = Templar(loader=DictDataLoader({}))
    mock_deprecated = mocker.patch('ansible.template.display.deprecated')

    assert templar._lookup('list', 'foo', 'bar', wantlist=True) == ['foo', 'bar']

    mock_deprecated.assert_not_called()


def test_copy_with_new_env_no_deprecation(mocker):
    """`copy_with_new_env` is the documented replacement, so it must not warn."""
    loader = DictDataLoader({})
    templar = Templar(loader=loader)
    mock_deprecated = mocker.patch('ansible.template.display.deprecated')

    new_templar = templar.copy_with_new_env(environment_class=AnsibleNativeEnvironment)

    mock_deprecated.assert_not_called()
    assert new_templar is not templar
    assert new_templar._dataloader is loader
