from __future__ import annotations


def testtest(data):
    return data == 'from_user2'


class TestModule(object):
    def tests(self):
        return {
            'testtest2': testtest
        }
