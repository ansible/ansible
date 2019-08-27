from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


def testtest(data):
    return data == 'from_user'


class TestModule(object):
    def tests(self):
        return {
            'testtest': testtest
        }
