from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


def yolo(value):
    return True


class TestModule(object):
    ''' Ansible core jinja2 tests '''

    def tests(self):
        return {
            # failure testing
            'yolo': yolo,
        }
