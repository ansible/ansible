# -*- coding: utf-8 -*-

import os
import sys

from units.compat import unittest
from ansible.module_utils.hwc_utils import (navigate_hash,
                                            remove_empty_from_dict,
                                            remove_nones_from_dict,
                                            replace_resource_dict)


class HwcUtilsTestCase(unittest.TestCase):
    def test_navigate_hash(self):
        value = {
            'foo': {
                'quiet': {
                    'tree': 'test'
                },
            }
        }

        self.assertEquals(navigate_hash(value, ["foo", "quiet", "tree"]),
                          "test")

        self.assertEquals(navigate_hash(value, ["foo", "q", "tree"], 123),
                          123)

        self.assertIsNone(navigate_hash(value, [], 123))

    def test_remove_empty_from_dict(self):
        value = {
            'foo': {
                'quiet': {
                    'tree': 'test',
                    'tree1': [
                        None,
                        {},
                        [],
                        'test'
                    ],
                    'tree2': {},
                    'tree3': []
                },
            },
            'foo1': [],
            'foo2': {},
            'foo3': None,
        }

        expect = {
            'foo': {
                'quiet': {
                    'tree': 'test',
                    'tree1': [
                        'test'
                    ]
                },
            },
        }

        self.assertEqual(remove_empty_from_dict(value), expect)

    def test_remove_nones_from_dict(self):
        value = {
            'foo': {
                'quiet': {
                    'tree': 'test',
                    'tree1': [
                        None,
                        {},
                        [],
                        'test'
                    ],
                    'tree2': {},
                    'tree3': []
                },
            },
            'foo1': [],
            'foo2': {},
            'foo3': None,
        }

        expect = {
            'foo': {
                'quiet': {
                    'tree': 'test',
                    'tree1': [
                        {},
                        [],
                        'test'
                    ],
                    'tree2': {},
                    'tree3': []
                },
            },
            'foo1': [],
            'foo2': {},
        }

        self.assertEqual(remove_nones_from_dict(value), expect)

    def test_replace_resource_dict(self):
        self.assertEqual(replace_resource_dict({'foo': 'quiet'}, 'foo'), 'quiet')

        self.assertEqual(replace_resource_dict({}, 'foo'), {})

        self.assertEqual(replace_resource_dict([[{'foo': 'quiet'}]], 'foo'),
                         [['quiet']])
