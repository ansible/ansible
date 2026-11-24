from __future__ import annotations


def adjacent_marker(value):
    return 'adjacent-%s' % (value,)


class FilterModule(object):
    def filters(self):
        return {
            'adjacent_marker': adjacent_marker,
        }
