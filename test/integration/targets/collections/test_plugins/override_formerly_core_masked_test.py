from __future__ import annotations


def override_formerly_core_masked_test(value, *args, **kwargs):
    if value != 'hello override':
        raise Exception('expected "hello override" only...')

    return True


class TestModule(object):
    def tests(self):
        return {
            'formerly_core_masked_test': override_formerly_core_masked_test
        }
