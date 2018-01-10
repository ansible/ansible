#!/usr/bin/env python

from ansible.module_utils._text import to_text


def make_text(data):
    try:
        return to_text(data)
    except:
        return str(data)


class FilterModule(object):
    def filters(self):
        return {
            'to_text': make_text
        }
