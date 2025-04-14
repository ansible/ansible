# -*- coding: utf-8 -*-
# (c) 2015, Toshio Kuratomi <tkuratomi@ansible.com>
# (c) 2017, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import typing as t
import pytest

from ansible.module_utils.basic import remove_values
from ansible.module_utils.common.parameters import _return_datastructure_name


class TestReturnValues:
    dataset: tuple[tuple[t.Any, frozenset[str]], ...] = (
        ('string', frozenset(['string'])),
        ('', frozenset()),
        (1, frozenset(['1'])),
        (1.0, frozenset(['1.0'])),
        (False, frozenset()),
        (['1', '2', '3'], frozenset(['1', '2', '3'])),
        (('1', '2', '3'), frozenset(['1', '2', '3'])),
        ({'one': 1, 'two': 'dos'}, frozenset(['1', 'dos'])),
        (
            {
                'one': 1,
                'two': 'dos',
                'three': [
                    'amigos', 'musketeers', None, {
                        'ping': 'pong',
                        'base': (
                            'balls', 'raquets'
                        )
                    }
                ]
            },
            frozenset(['1', 'dos', 'amigos', 'musketeers', 'pong', 'balls', 'raquets'])
        ),
        (u'Toshio くらとみ', frozenset(['Toshio くらとみ'])),
        ('Toshio くらとみ', frozenset(['Toshio くらとみ'])),
    )

    def test_return_datastructure_name(self):
        for data, expected in self.dataset:
            assert frozenset(_return_datastructure_name(data)) == expected

    def test_unknown_type(self):
        with pytest.raises(Exception):
            frozenset(_return_datastructure_name(object()))


class TestRemoveValues:
    OMIT = 'VALUE_SPECIFIED_IN_NO_LOG_PARAMETER'
    dataset_no_remove = (
        ('string', frozenset(['nope'])),
        (1234, frozenset(['4321'])),
        (False, frozenset(['4321'])),
        (1.0, frozenset(['4321'])),
        (['string', 'strang', 'strung'], frozenset(['nope'])),
        ({'one': 1, 'two': 'dos', 'secret': 'key'}, frozenset(['nope'])),
        (
            {
                'one': 1,
                'two': 'dos',
                'three': [
                    'amigos', 'musketeers', None, {
                        'ping': 'pong', 'base': ['balls', 'raquets']
                    }
                ]
            },
            frozenset(['nope'])
        ),
        (u'Toshio くら'.encode('utf-8'), frozenset([u'とみ'.encode('utf-8')])),
        (u'Toshio くら', frozenset([u'とみ'])),
    )
    dataset_remove = (
        ('string', frozenset(['string']), OMIT),
        (1234, frozenset(['1234']), OMIT),
        (1234, frozenset(['23']), OMIT),
        (1.0, frozenset(['1.0']), OMIT),
        (['string', 'strang', 'strung'], frozenset(['strang']), ['string', OMIT, 'strung']),
        (['string', 'strang', 'strung'], frozenset(['strang', 'string', 'strung']), [OMIT, OMIT, OMIT]),
        (('string', 'strang', 'strung'), frozenset(['string', 'strung']), [OMIT, 'strang', OMIT]),
        ((1234567890, 345678, 987654321), frozenset(['1234567890']), [OMIT, 345678, 987654321]),
        ((1234567890, 345678, 987654321), frozenset(['345678']), [OMIT, OMIT, 987654321]),
        ({'one': 1, 'two': 'dos', 'secret': 'key'}, frozenset(['key']), {'one': 1, 'two': 'dos', 'secret': OMIT}),
        ({'one': 1, 'two': 'dos', 'secret': 'key'}, frozenset(['key', 'dos', '1']), {'one': OMIT, 'two': OMIT, 'secret': OMIT}),
        ({'one': 1, 'two': 'dos', 'secret': 'key'}, frozenset(['key', 'dos', '1']), {'one': OMIT, 'two': OMIT, 'secret': OMIT}),
        (
            {
                'one': 1,
                'two': 'dos',
                'three': [
                    'amigos', 'musketeers', None, {
                        'ping': 'pong', 'base': [
                            'balls', 'raquets'
                        ]
                    }
                ]
            },
            frozenset(['balls', 'base', 'pong', 'amigos']),
            {
                'one': 1,
                'two': 'dos',
                'three': [
                    OMIT, 'musketeers', None, {
                        'ping': OMIT,
                        'base': [
                            OMIT, 'raquets'
                        ]
                    }
                ]
            }
        ),
        (
            'This sentence has an enigma wrapped in a mystery inside of a secret. - mr mystery',
            frozenset(['enigma', 'mystery', 'secret']),
            'This sentence has an ******** wrapped in a ******** inside of a ********. - mr ********'
        ),
        (u'Toshio くらとみ'.encode('utf-8'), frozenset([u'くらとみ'.encode('utf-8')]), u'Toshio ********'.encode('utf-8')),
        (u'Toshio くらとみ', frozenset([u'くらとみ']), u'Toshio ********'),
    )

    def test_no_removal(self):
        for value, no_log_strings in self.dataset_no_remove:
            assert remove_values(value, no_log_strings) == value

    def test_strings_to_remove(self):
        for value, no_log_strings, expected in self.dataset_remove:
            assert remove_values(value, no_log_strings) == expected

    def test_unknown_type(self):
        with pytest.raises(TypeError):
            remove_values(object(), frozenset())

    def test_hit_recursion_limit(self):
        """ Check that we do not hit a recursion limit"""
        data_list = []
        inner_list = data_list
        for i in range(0, 10000):
            new_list = []
            inner_list.append(new_list)
            inner_list = new_list
        inner_list.append('secret')

        # Check that this does not hit a recursion limit
        actual_data_list = remove_values(data_list, frozenset(('secret',)))

        levels = 0
        inner_list = actual_data_list
        while True:
            if isinstance(inner_list, list):
                assert len(inner_list) == 1
            else:
                levels -= 1
                break
            inner_list = inner_list[0]
            levels += 1

        assert inner_list == self.OMIT
        assert levels == 10000
