from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


def filter_list_of_tuples_by_first_param(lst, search, startswith=False):
    out = []
    for element in lst:
        if startswith:
            if element[0].startswith(search):
                out.append(element)
        else:
            if search in element[0]:
                out.append(element)
    return out


class FilterModule(object):
    ''' filter '''

    def filters(self):
        return {
            'filter_list_of_tuples_by_first_param': filter_list_of_tuples_by_first_param,
        }
