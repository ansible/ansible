from __future__ import annotations


def test_subdir_filter(data):
    return "{0}_via_testfilter_from_subdir".format(data)


class FilterModule(object):

    def filters(self):
        return {
            'test_subdir_filter': test_subdir_filter
        }
