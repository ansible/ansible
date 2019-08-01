from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import re


def test_package_ok(value):
    return __package__ == 'ansible.plugins.test'


def test_name_ok(value):
    # test names are prefixed with a unique hash value to prevent shadowing of other plugins
    return bool(re.match(r'^ansible\.plugins\.test\.[0-9]+_test_test$', __name__))


class TestModule:
    def tests(self):
        return {
            'test_package_ok': test_package_ok,
            'test_name_ok': test_name_ok,
        }
