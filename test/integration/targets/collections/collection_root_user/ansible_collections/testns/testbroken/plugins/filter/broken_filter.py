from __future__ import annotations


class FilterModule(object):

    def filters(self):
        return {
            'broken': lambda x: 'broken',
        }


raise Exception('This is a broken filter plugin.')
