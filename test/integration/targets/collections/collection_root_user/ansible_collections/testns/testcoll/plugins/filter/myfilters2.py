from __future__ import annotations


def testfilter2(data):
    return "{0}_via_testfilter2_from_userdir".format(data)


class FilterModule(object):

    def filters(self):
        return {
            'testfilter2': testfilter2
        }
