from __future__ import annotations


def filter_name(a):
    return __name__


class FilterModule(object):
    def filters(self):
        filters = {
            'filter_name': filter_name,
        }

        return filters
