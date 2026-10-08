from __future__ import annotations


class UnknownType:
    """A type the templating system knows nothing about."""

    def __str__(self):
        return 'unknown-type-result'


def unknown_type(value):
    return UnknownType()


class FilterModule(object):
    def filters(self):
        return {
            'unknown_type': unknown_type,
        }
