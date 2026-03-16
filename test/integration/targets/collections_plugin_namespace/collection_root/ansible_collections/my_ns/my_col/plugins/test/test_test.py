from __future__ import annotations


def test_name_ok(value):
    return __name__ == 'ansible_collections.my_ns.my_col.plugins.test.test_test'


class TestModule:
    def tests(self):
        return {
            'test_name_ok': test_name_ok,
        }
