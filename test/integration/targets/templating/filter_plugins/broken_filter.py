from __future__ import annotations


class Broken:
    @property
    def accept_args_markers(self):
        raise Exception('boom')


class FilterModule:
    def filters(self):
        return {
            'broken': Broken(),
        }
