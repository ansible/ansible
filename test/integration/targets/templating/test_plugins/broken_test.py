from __future__ import annotations


class Broken:
    @property
    def accept_marker(self):
        raise Exception('boom')


class TestModule:
    def tests(self):
        return {
            'broken': Broken(),
        }
