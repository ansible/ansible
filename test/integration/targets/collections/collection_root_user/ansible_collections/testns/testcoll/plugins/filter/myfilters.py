from __future__ import annotations


def testfilter(data):
    return "{0}_via_testfilter_from_userdir".format(data)


class FilterModule(object):

    def filters(self):
        return {
            'testfilter': testfilter
        }
