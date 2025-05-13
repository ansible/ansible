from __future__ import annotations


def subdir_test(data):
    return data == 'subdir_from_user'


class TestModule(object):
    def tests(self):
        return {
            'subdir_test': subdir_test
        }
