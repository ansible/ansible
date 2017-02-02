# This file is part of Ansible
# -*- coding: utf-8 -*-
#
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
#

# Make coding more python3-ish
from __future__ import (absolute_import, division)
__metaclass__ = type

# for testing
from ansible.compat.tests import unittest

from ansible.module_utils.facts import collector

from ansible.module_utils.facts import default_collectors


class TestGetCollectorNames(unittest.TestCase):
    def test_none(self):
        res = collector.get_collector_names()
        self.assertIsInstance(res, set)
        self.assertEqual(res, set([]))

    def test_empty_sets(self):
        res = collector.get_collector_names(valid_subsets=frozenset([]),
                                            minimal_gather_subset=frozenset([]),
                                            gather_subset=set([]))
        self.assertIsInstance(res, set)
        self.assertEqual(res, set([]))

    def test_empty_valid_and_min_with_all_gather_subset(self):
        res = collector.get_collector_names(valid_subsets=frozenset([]),
                                            minimal_gather_subset=frozenset([]),
                                            gather_subset=set(['all']))
        self.assertIsInstance(res, set)
        self.assertEqual(res, set([]))

    def test_one_valid_with_all_gather_subset(self):
        valid_subsets = frozenset(['my_fact'])
        res = collector.get_collector_names(valid_subsets=valid_subsets,
                                            minimal_gather_subset=frozenset([]),
                                            gather_subset=set(['all']))
        self.assertIsInstance(res, set)
        self.assertEqual(res, set(['my_fact']))

    def test_one_minimal_with_all_gather_subset(self):
        my_fact = 'my_fact'
        valid_subsets = frozenset([my_fact])
        minimal_gather_subset = valid_subsets

        res = collector.get_collector_names(valid_subsets=valid_subsets,
                                            minimal_gather_subset=minimal_gather_subset,
                                            gather_subset=set(['all']))
        self.assertIsInstance(res, set)
        self.assertEqual(res, set(['my_fact']))

    def test_with_all_gather_subset(self):
        valid_subsets = frozenset(['my_fact', 'something_else', 'whatever'])
        minimal_gather_subset = frozenset(['my_fact'])

        # even with '!all', the minimal_gather_subset should be returned
        res = collector.get_collector_names(valid_subsets=valid_subsets,
                                            minimal_gather_subset=minimal_gather_subset,
                                            gather_subset=set(['all']))
        self.assertIsInstance(res, set)
        self.assertEqual(res, set(['my_fact', 'something_else', 'whatever']))

    def test_one_minimal_with_not_all_gather_subset(self):
        valid_subsets = frozenset(['my_fact', 'something_else', 'whatever'])
        minimal_gather_subset = frozenset(['my_fact'])

        # even with '!all', the minimal_gather_subset should be returned
        res = collector.get_collector_names(valid_subsets=valid_subsets,
                                            minimal_gather_subset=minimal_gather_subset,
                                            gather_subset=set(['!all']))
        self.assertIsInstance(res, set)
        self.assertEqual(res, set(['my_fact']))

    def test_gather_subset_excludes(self):
        valid_subsets = frozenset(['my_fact', 'something_else', 'whatever'])
        minimal_gather_subset = frozenset(['my_fact'])

        # even with '!all', the minimal_gather_subset should be returned
        res = collector.get_collector_names(valid_subsets=valid_subsets,
                                            minimal_gather_subset=minimal_gather_subset,
                                            gather_subset=set(['all', '!my_fact', '!whatever']))
        self.assertIsInstance(res, set)
        # my_facts is in minimal_gather_subset, so always returned
        self.assertEqual(res, set(['my_fact', 'something_else']))

    def test_gather_subset_excludes_ordering(self):
        valid_subsets = frozenset(['my_fact', 'something_else', 'whatever'])
        minimal_gather_subset = frozenset(['my_fact'])

        res = collector.get_collector_names(valid_subsets=valid_subsets,
                                            minimal_gather_subset=minimal_gather_subset,
                                            gather_subset=set(['!all', 'whatever']))
        self.assertIsInstance(res, set)
        # excludes are higher precedence than includes, so !all excludes everything
        # and then minimal_gather_subset is added. so '!all', 'other' == '!all'
        self.assertEqual(res, set(['my_fact']))

    def test_invaid_gather_subset(self):
        valid_subsets = frozenset(['my_fact', 'something_else'])
        minimal_gather_subset = frozenset(['my_fact'])

        self.assertRaisesRegexp(TypeError,
                                'Bad subset .* given to Ansible.*allowed\:.*all,.*my_fact.*',
                                collector.get_collector_names,
                                valid_subsets=valid_subsets,
                                minimal_gather_subset=minimal_gather_subset,
                                gather_subset=set(['my_fact', 'not_a_valid_gather_subset']))


class TestCollectorClassesFromGatherSubset(unittest.TestCase):
    def _classes(self,
                 all_collector_classes=None,
                 valid_subsets=None,
                 minimal_gather_subset=None,
                 gather_subset=None,
                 gather_timeout=None):
        return collector.collector_classes_from_gather_subset(all_collector_classes=all_collector_classes,
                                                              valid_subsets=valid_subsets,
                                                              minimal_gather_subset=minimal_gather_subset,
                                                              gather_subset=gather_subset,
                                                              gather_timeout=gather_timeout)

    def test_no_args(self):
        res = self._classes()
        self.assertIsInstance(res, list)
        self.assertEqual(res, [])

    def test(self):
        res = self._classes(all_collector_classes=default_collectors.collectors,
                            gather_subset=set(['!all']))
        self.assertIsInstance(res, list)
        self.assertEqual(res, [])

    def test_env(self):
        res = self._classes(all_collector_classes=default_collectors.collectors,
                            gather_subset=set(['env']))
        self.assertIsInstance(res, list)
        self.assertEqual(res, [default_collectors.EnvFactCollector])

    def test_collector_specified_multiple_times(self):
        res = self._classes(all_collector_classes=default_collectors.collectors,
                            gather_subset=set(['platform', 'all', 'machine']))
        self.assertIsInstance(res, list)
        self.assertIn(default_collectors.PlatformFactCollector,
                      res)

    def test_unknown_collector(self):
        # something claims 'unknown_collector' is a valid gather_subset, but there is
        # no FactCollector mapped to 'unknown_collector'
        self.assertRaisesRegexp(TypeError,
                                'Bad subset.*unknown_collector.*given to Ansible.*allowed\:.*all,.*env.*',
                                self._classes,
                                all_collector_classes=default_collectors.collectors,
                                gather_subset=set(['env', 'unknown_collector']))
