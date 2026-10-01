# Copyright: (c) 2026, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

from unittest.mock import patch
from units.mock.loader import DictDataLoader

from ansible.template import Templar


DEPRECATION_MSG = 'Direct access to the `_available_variables` internal attribute is deprecated. Use `available_variables` instead.'


def test_available_variables_get_deprecation():
    templar = Templar(loader=DictDataLoader({}), variables={'foo': 'bar'})

    with patch('ansible.template.display.deprecated') as mock_deprecated:
        assert templar._available_variables == {'foo': 'bar'}

    mock_deprecated.assert_called_once_with(msg=DEPRECATION_MSG, version='2.23')


def test_available_variables_set_deprecation():
    templar = Templar(loader=DictDataLoader({}), variables={'foo': 'bar'})

    with patch('ansible.template.display.deprecated') as mock_deprecated:
        templar._available_variables = {'foo': 'bar'}

    mock_deprecated.assert_called_once_with(msg=DEPRECATION_MSG, version='2.23')
    assert templar.available_variables == {'foo': 'bar'}


def test_available_variables_no_deprecation():
    """The public property must not emit the deprecation warning."""
    templar = Templar(loader=DictDataLoader({}))

    with patch('ansible.template.display.deprecated') as mock_deprecated:
        templar.available_variables = {'foo': 'bar'}
        assert templar.available_variables == {'foo': 'bar'}

    mock_deprecated.assert_not_called()
