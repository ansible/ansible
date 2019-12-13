# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

# This file is nested in a directory under filter_plugins to test that extra directories
# are added to the search path recursively. See https://github.com/ansible/ansible/issues/65565.


def do_flag(myval):
    return 'flagged'


class FilterModule(object):
    ''' Ansible core jinja2 filters '''

    def filters(self):
        return {
            # jinja2 overrides
            'flag': do_flag,
            'flatten': do_flag,
        }
