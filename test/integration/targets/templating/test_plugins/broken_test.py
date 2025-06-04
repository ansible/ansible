from __future__ import annotations


class Broken:
    @property
    def accept_args_markers(self):
        raise Exception('boom')


class TestModule:
    def tests(self):
        return {
            'broken': Broken(),
        }
