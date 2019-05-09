# -*- coding: utf-8 -*-

from units.compat import unittest
from ansible.module_utils.hwc_utils import (HwcModuleException, navigate_value)


class HwcUtilsTestCase(unittest.TestCase):
    def test_navigate_value(self):
        value = {
            'foo': {
                'quiet': {
                    'tree': 'test',
                    "trees": [0, 1]
                },
            }
        }

        self.assertEquals(navigate_value(value, ["foo", "quiet", "tree"]),
                          "test")

        self.assertEquals(
            navigate_value(value, ["foo", "quiet", "trees"],
                           {"foo.quiet.trees": 1}),
            1)

        self.assertRaisesRegexp(HwcModuleException,
                                r".* key\(q\) is not exist in dict",
                                navigate_value, value, ["foo", "q", "tree"])

        self.assertRaisesRegexp(HwcModuleException,
                                r".* the index is out of list",
                                navigate_value, value,
                                ["foo", "quiet", "trees"],
                                {"foo.quiet.trees": 2})
