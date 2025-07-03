from __future__ import annotations

import re


def test_name_ok(value):
    # test names include a unique hash value to prevent shadowing of other plugins
    return bool(re.match(r'^ansible\.plugins\.test\.test_test_[0-9]+$', __name__))


class TestModule:
    def tests(self):
        return {
            'test_name_ok': test_name_ok,
        }
