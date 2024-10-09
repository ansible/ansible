from __future__ import annotations


def do_nothing(myval):
    return myval


class FilterModule(object):
    """ Ansible core jinja2 filters """

    def filters(self):
        return {
            'filter2': do_nothing,
        }
