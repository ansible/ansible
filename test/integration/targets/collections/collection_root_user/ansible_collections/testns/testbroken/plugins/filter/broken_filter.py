from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


class FilterModule(object):

    def filters(self):
        return {
            'broken': lambda x: 'broken',
        }


raise Exception('This is a broken filter plugin.')
