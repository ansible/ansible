# (c) Ansible Project

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from urllib.parse import urlparse

def is_uri(value, schemas=None):

    try:
        x = urlparse(value)
        isit = all([x.scheme, x.netloc, not schemas or x.scheme in schemas])
    except Exception as e:
        isit = False
    return isit

def is_url(value):
    return is_uri(value, ['http', 'ftp', 'https', 'ftps'])

class TestModule(object):
    ''' Ansible uri jinja2 tests '''

    def tests(self):
        return {
            # file testing
            'url': is_url,
            'uri': is_uri,
        }
