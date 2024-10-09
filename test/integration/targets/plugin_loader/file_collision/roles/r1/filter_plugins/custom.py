from __future__ import annotations


def do_nothing(myval):
    return myval


class FilterModule(object):
    """ Ansible core jinja2 filters """

    def filters(self):
        return {
            'filter1': do_nothing,
            'filter3': do_nothing,
        }
