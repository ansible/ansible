from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


def override_formerly_core_masked_filter(*args, **kwargs):
    return 'hello from overridden formerly_core_masked_filter'


class FilterModule(object):
    def filters(self):
        return {
            'formerly_core_masked_filter': override_formerly_core_masked_filter
        }
