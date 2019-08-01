from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


def filter_package(a):
    return __package__


def filter_name(a):
    return __name__


class FilterModule(object):
    def filters(self):
        filters = {
            'filter_package': filter_package,
            'filter_name': filter_name,
        }

        return filters
