from __future__ import annotations


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
