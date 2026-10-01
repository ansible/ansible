# Copyright: (c) 2026, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

from unittest.mock import patch
from units.mock.loader import DictDataLoader

from ansible.template import Templar, AnsibleEnvironment, AnsibleNativeEnvironment


DEPRECATION_MSG = ('Direct access to the `environment` attribute is deprecated. '
                   'Consider using `copy_with_new_env` or passing `overrides` to `template`.')


def test_environment_get_deprecation():
    templar = Templar(loader=DictDataLoader({}))

    with patch('ansible.template.display.deprecated') as mock_deprecated:
        assert templar.environment is templar._environment

    mock_deprecated.assert_called_once_with(msg=DEPRECATION_MSG, version='2.23')


def test_environment_set_deprecation():
    templar = Templar(loader=DictDataLoader({}))
    new_environment = AnsibleEnvironment()

    with patch('ansible.template.display.deprecated') as mock_deprecated:
        templar.environment = new_environment

    mock_deprecated.assert_called_once_with(msg=DEPRECATION_MSG, version='2.23')
    assert templar._environment is new_environment


def test_environment_mutation_via_deprecated_property():
    """Callers reach through the property to register filters, that must keep working."""
    templar = Templar(loader=DictDataLoader({}), variables={'foo': 'bar'})

    with patch('ansible.template.display.deprecated'):
        templar.environment.filters['comment_ify'] = lambda value: '# %s' % value

    assert templar.template('{{ foo | comment_ify }}') == '# bar'


def test_private_environment_no_deprecation():
    """The replacement attribute must not emit the deprecation warning."""
    with patch('ansible.template.display.deprecated') as mock_deprecated:
        templar = Templar(loader=DictDataLoader({}))
        assert isinstance(templar._environment, AnsibleEnvironment)

        templar._environment = new_environment = AnsibleEnvironment()
        assert templar._environment is new_environment

    mock_deprecated.assert_not_called()


def test_template_no_deprecation():
    """Templating must use `_environment` internally, not the deprecated property."""
    templar = Templar(loader=DictDataLoader({}), variables={'foo': 'bar'})

    with patch('ansible.template.display.deprecated') as mock_deprecated:
        assert templar.template('{{ foo }}') == 'bar'
        assert templar.is_template('{{ foo }}')
        assert templar.is_possibly_template('{{ foo }}')

    mock_deprecated.assert_not_called()


def test_template_overrides_no_deprecation():
    """`overrides` is a documented alternative, so it must not warn."""
    templar = Templar(loader=DictDataLoader({}), variables={'foo': 'bar'})
    overrides = {'variable_start_string': '<<', 'variable_end_string': '>>'}

    with patch('ansible.template.display.deprecated') as mock_deprecated:
        assert templar.template('<< foo >>', overrides=overrides) == 'bar'

    mock_deprecated.assert_not_called()
    assert templar._environment.variable_start_string == '{{'


def test_set_temporary_context_no_deprecation():
    """`set_temporary_context` mutates the environment and must not warn."""
    templar = Templar(loader=DictDataLoader({}))

    with patch('ansible.template.display.deprecated') as mock_deprecated:
        with templar.set_temporary_context(variable_start_string='<<'):
            assert templar._environment.variable_start_string == '<<'

    mock_deprecated.assert_not_called()
    assert templar._environment.variable_start_string == '{{'


def test_copy_with_new_env_no_deprecation():
    """`copy_with_new_env` is the documented replacement, so it must not warn."""
    templar = Templar(loader=DictDataLoader({}))

    with patch('ansible.template.display.deprecated') as mock_deprecated:
        new_templar = templar.copy_with_new_env(environment_class=AnsibleNativeEnvironment)

    mock_deprecated.assert_not_called()
    assert new_templar is not templar
    assert new_templar._environment is not templar._environment
    assert isinstance(new_templar._environment, AnsibleNativeEnvironment)
