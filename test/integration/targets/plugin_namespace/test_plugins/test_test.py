from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


def test_package_ok(value):
    return __package__ == 'ansible.plugins.test'


def test_name_ok(value):
    return __name__ == 'ansible.plugins.test.test_test'


class TestModule:
    def tests(self):
        return {
            'test_package_ok': test_package_ok,
            'test_name_ok': test_name_ok,
        }
