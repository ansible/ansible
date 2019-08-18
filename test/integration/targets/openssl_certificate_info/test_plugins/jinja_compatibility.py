from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


def compatibility_in_test(a, b):
    return a in b


class TestModule:
    ''' Ansible math jinja2 tests '''

    def tests(self):
        return {
            'in': compatibility_in_test,
        }
