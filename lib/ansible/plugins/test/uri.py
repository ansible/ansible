# (c) Ansible Project

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from urllib.parse import urlparse


def is_uri(value, schemas=None):
    ''' Will verify that the string passed is a valid 'uri' according to spec, if passed a list of valid schemas it will even match those '''
    try:
        x = urlparse(value)
        isit = all([x.scheme, x.netloc, not schemas or x.scheme in schemas])
    except Exception as e:
        isit = False
    return isit


def is_url(value):
    ''' Will verify that the string passed is a valid 'url' according to spec '''
    return is_uri(value, ['http', 'ftp', 'https', 'ftps'])


class TestModule(object):
    ''' Ansible uri jinja2 tests '''

    def tests(self):
        return {
            # file testing
            'url': is_url,
            'uri': is_uri,
        }
