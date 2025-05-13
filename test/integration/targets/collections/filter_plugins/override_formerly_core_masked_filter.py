from __future__ import annotations


def override_formerly_core_masked_filter(*args, **kwargs):
    return 'hello from overridden formerly_core_masked_filter'


class FilterModule(object):
    def filters(self):
        return {
            'formerly_core_masked_filter': override_formerly_core_masked_filter
        }
