# (c) 2012-2014, Chris Meyers <chris.meyers.fsu@gmail.com>
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import types

from ansible.compat.tests import unittest
from ansible.compat.tests.mock import patch, mock_open, MagicMock


from ansible.plugins.callback import CallbackBase


class TestCallback(unittest.TestCase):
    # FIXME: This doesn't really test anything...
    def test_init(self):
        CallbackBase()

    def test_display(self):
        display_mock = MagicMock()
        display_mock.verbosity = 0
        cb = CallbackBase(display=display_mock)
        self.assertIs(cb._display, display_mock)

    def test_display_verbose(self):
        display_mock = MagicMock()
        display_mock.verbosity = 5
        cb = CallbackBase(display=display_mock)
        self.assertIs(cb._display, display_mock)

    # TODO: import callback module so we can patch callback.cli/callback.C


class TestCallbackResults(unittest.TestCase):
    def test_get_item(self):
        cb = CallbackBase()
        results = {'item': 'some_item'}
        res = cb._get_item(results)
        self.assertEquals(res, 'some_item')

    def test_get_item_no_log(self):
        cb = CallbackBase()
        results = {'item': 'some_item', '_ansible_no_log': True}
        res = cb._get_item(results)
        self.assertEquals(res, "(censored due to no_log)")

        results = {'item': 'some_item', '_ansible_no_log': False}
        res = cb._get_item(results)
        self.assertEquals(res, "some_item")

    def test_clean_results(self):
        cb = CallbackBase()
        result = {'item': 'some_item',
                  'invocation': 'foo --bar whatever [some_json]',
                  'changed': True}

        self.assertTrue('changed' in result)
        self.assertTrue('invocation' in result)
        cb._clean_results(result, 'debug')
        self.assertFalse('changed' in result)
        self.assertFalse('invocation' in result)


class TestCallbackDumpResults(unittest.TestCase):
    def test_internal_keys(self):
        cb = CallbackBase()
        result = {'item': 'some_item',
                  '_ansible_some_var': 'SENTINEL',
                  'testing_ansible_out': 'should_be_left_in LEFTIN',
                  'invocation': 'foo --bar whatever [some_json]',
                  'some_dict_key': {'a_sub_dict_for_key': 'baz'},
                  'bad_dict_key': {'_ansible_internal_blah': 'SENTINEL'},
                  'changed': True}
        json_out = cb._dump_results(result)
        self.assertFalse('"_ansible_' in json_out)
        self.assertFalse('SENTINEL' in json_out)
        self.assertTrue('LEFTIN' in json_out)

    def test_no_log(self):
        cb = CallbackBase()
        result = {'item': 'some_item',
                  '_ansible_no_log': True,
                  'some_secrets': 'SENTINEL'}
        json_out = cb._dump_results(result)
        self.assertFalse('SENTINEL' in json_out)
        self.assertTrue('no_log' in json_out)
        self.assertTrue('output has been hidden' in json_out)

    def test_exception(self):
        cb = CallbackBase()
        result = {'item': 'some_item LEFTIN',
                  'exception': ['frame1', 'SENTINEL']}
        json_out = cb._dump_results(result)
        self.assertFalse('SENTINEL' in json_out)
        self.assertFalse('exception' in json_out)
        self.assertTrue('LEFTIN' in json_out)

    def test_verbose(self):
        cb = CallbackBase()
        result = {'item': 'some_item LEFTIN',
                  '_ansible_verbose_always': 'chicane'}
        json_out = cb._dump_results(result)
        self.assertFalse('SENTINEL' in json_out)
        self.assertTrue('LEFTIN' in json_out)

    def test_diff(self):
        cb = CallbackBase()
        result = {'item': 'some_item LEFTIN',
                  'diff': ['remove stuff', 'added LEFTIN'],
                  '_ansible_verbose_always': 'chicane'}
        json_out = cb._dump_results(result)
        self.assertFalse('SENTINEL' in json_out)
        self.assertTrue('LEFTIN' in json_out)


# TODO: triggr the 'except UnicodeError' around _get_diff
#       that try except orig appeared in 61d01f549f2143fd9adfa4ffae42f09d24649c26
#       in 2013 so maybe a < py2.6 issue
class TestCallbackDiff(unittest.TestCase):
    def test_difflist(self):
        # TODO: split into smaller tests?
        cb = CallbackBase()
        difflist = [{'before': ['preface\nThe Before String\npostscript'],
                     'after': ['preface\nThe After String\npostscript'],
                     'before_header': 'just before',
                     'after_header': 'just after'
                     },
                    {'before': ['preface\nThe Before String\npostscript'],
                     'after': ['preface\nThe After String\npostscript'],
                     },
                    {'src_binary': 'chicane'},
                    {'dst_binary': 'chicanery'},
                    {'dst_larger': 1},
                    {'src_larger': 2},
                    {'prepared': 'what does prepared do?'},
                    {'before_header': 'just before'},
                    {'after_header': 'just after'}]

        res = cb._get_diff(difflist)

        self.assertIn('Before String', res)
        self.assertIn('After String', res)
        self.assertIn('just before', res)
        self.assertIn('just after', res)


class TestCallbackOnMethods(unittest.TestCase):
    def _find_on_methods(self, callback):
        cb_dir = dir(callback)
        method_names = [x for x in cb_dir if '_on_' in x]
        methods = [getattr(callback, mn) for mn in method_names]
        return methods

    def test_are_methods(self):
        cb = CallbackBase()
        for method in self._find_on_methods(cb):
            self.assertIsInstance(method, types.MethodType)

    def test_on_any(self):
        cb = CallbackBase()
        cb.v2_on_any('whatever', some_keyword='blippy')
        cb.on_any('whatever', some_keyword='blippy')
