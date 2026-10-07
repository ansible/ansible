# Copyright: (c) 2026, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

from units.mock.loader import DictDataLoader

from ansible.plugins.loader import init_plugin_loader
from ansible.template import Templar, AnsibleEnvironment, AnsibleNativeEnvironment


DEPRECATION_MSG_AVAILABLE_VARIABLES = 'Direct access to the `_available_variables` internal attribute is deprecated. Use `available_variables` instead.'
DEPRECATION_MSG_LOADER = 'Direct access to the `_loader` internal attribute is deprecated. Use `copy_with_new_env` to create a new instance.'
DEPRECATION_MSG_ENVIRONMENT = ('Direct access to the `environment` attribute is deprecated. '
                               'Consider using `copy_with_new_env` or passing `overrides` to `template`.')


def test_available_variables_get_deprecation(mocker):
    templar = Templar(loader=DictDataLoader({}), variables={'foo': 'bar'})
    mock_deprecated = mocker.patch('ansible.template.display.deprecated')
    assert templar._available_variables == {'foo': 'bar'}

    mock_deprecated.assert_called_once_with(msg=DEPRECATION_MSG_AVAILABLE_VARIABLES, version='2.23')


def test_loader_get_deprecation(mocker):
    loader = DictDataLoader({})
    templar = Templar(loader=loader)
    mock_deprecated = mocker.patch('ansible.template.display.deprecated')

    assert templar._loader is loader

    mock_deprecated.assert_called_once_with(msg=DEPRECATION_MSG_LOADER, version='2.23')


def test_available_variables_set_deprecation(mocker):
    templar = Templar(loader=DictDataLoader({}))
    mock_deprecated = mocker.patch('ansible.template.display.deprecated')

    templar._available_variables = {'foo': 'bar'}

    mock_deprecated.assert_called_once_with(msg=DEPRECATION_MSG_AVAILABLE_VARIABLES, version='2.23')
    assert templar._available_variables == {'foo': 'bar'}


def test_environment_get_deprecation(mocker):
    templar = Templar(loader=DictDataLoader({}))
    mock_deprecated = mocker.patch('ansible.template.display.deprecated')

    assert templar.environment is templar._environment

    mock_deprecated.assert_called_once_with(msg=DEPRECATION_MSG_ENVIRONMENT, version='2.23')


def test_available_variables_no_deprecation(mocker):
    """The public property must not emit the deprecation warning."""
    templar = Templar(loader=DictDataLoader({}))
    mock_deprecated = mocker.patch('ansible.template.display.deprecated')

    templar.available_variables = {'foo': 'bar'}
    assert templar.available_variables == {'foo': 'bar'}

    mock_deprecated.assert_not_called()


def test_loader_set_deprecation(mocker):
    templar = Templar(loader=DictDataLoader({}))
    new_loader = DictDataLoader({'/path/to/my_file.txt': 'foo\n'})
    mock_deprecated = mocker.patch('ansible.template.display.deprecated')

    templar._loader = new_loader

    mock_deprecated.assert_called_once_with(msg=DEPRECATION_MSG_LOADER, version='2.23')
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


def test_environment_set_deprecation(mocker):
    templar = Templar(loader=DictDataLoader({}))
    new_environment = AnsibleEnvironment()
    mock_deprecated = mocker.patch('ansible.template.display.deprecated')
    templar.environment = new_environment

    mock_deprecated.assert_called_once_with(msg=DEPRECATION_MSG_ENVIRONMENT, version='2.23')
    assert templar._environment is new_environment


def test_environment_mutation_via_deprecated_property(mocker):
    """Callers reach through the property to register filters, that must keep working."""
    templar = Templar(loader=DictDataLoader({}), variables={'foo': 'bar'})
    mocker.patch('ansible.template.display.deprecated')

    mock_deprecated = mocker.patch('ansible.template.display.deprecated')
    templar.environment.filters['comment_ify'] = lambda value: '# %s' % value

    mock_deprecated.assert_called_once_with(msg=DEPRECATION_MSG_ENVIRONMENT, version='2.23')
    assert templar.template('{{ foo | comment_ify }}') == '# bar'


def test_private_environment_no_deprecation(mocker):
    """The replacement attribute must not emit the deprecation warning."""
    mock_deprecated = mocker.patch('ansible.template.display.deprecated')
    templar = Templar(loader=DictDataLoader({}))
    assert isinstance(templar._environment, AnsibleEnvironment)

    templar._environment = new_environment = AnsibleEnvironment()
    assert templar._environment is new_environment

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
    assert new_templar._environment is not templar._environment
    assert isinstance(new_templar._environment, AnsibleNativeEnvironment)


def test_template_no_deprecation(mocker):
    """Templating must use `_environment` internally, not the deprecated property."""
    templar = Templar(loader=DictDataLoader({}), variables={'foo': 'bar'})
    mock_deprecated = mocker.patch('ansible.template.display.deprecated')

    assert templar.template('{{ foo }}') == 'bar'
    assert templar.is_template('{{ foo }}')
    assert templar.is_possibly_template('{{ foo }}')

    mock_deprecated.assert_not_called()


def test_template_overrides_no_deprecation(mocker):
    """`overrides` is a documented alternative, so it must not warn."""
    templar = Templar(loader=DictDataLoader({}), variables={'foo': 'bar'})
    overrides = {'variable_start_string': '<<', 'variable_end_string': '>>'}
    mock_deprecated = mocker.patch('ansible.template.display.deprecated')
    assert templar.template('<< foo >>', overrides=overrides) == 'bar'

    mock_deprecated.assert_not_called()
    assert templar._environment.variable_start_string == '{{'


def test_set_temporary_context_no_deprecation(mocker):
    """`set_temporary_context` mutates the environment and must not warn."""
    templar = Templar(loader=DictDataLoader({}))
    mock_deprecated = mocker.patch('ansible.template.display.deprecated')

    with templar.set_temporary_context(variable_start_string='<<'):
        assert templar._environment.variable_start_string == '<<'

    mock_deprecated.assert_not_called()
    assert templar._environment.variable_start_string == '{{'
