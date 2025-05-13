# (c) Ansible Project

from __future__ import annotations

from urllib.parse import urlparse


def is_uri(value, schemes=None):
    """ Will verify that the string passed is a valid 'URI', if given a list of valid schemes it will match those """
    try:
        x = urlparse(value)
        isit = all([x.scheme is not None, x.path is not None, not schemes or x.scheme in schemes])
    except Exception as e:
        isit = False
    return isit


def is_url(value, schemes=None):
    """ Will verify that the string passed is a valid 'URL' """

    isit = is_uri(value, schemes)
    if isit:
        x = urlparse(value)
        isit = bool(x.netloc or x.scheme == 'file')
    return isit


def is_urn(value):
    return is_uri(value, ['urn'])


class TestModule(object):
    """ Ansible URI jinja2 test """

    def tests(self):
        return {
            # file testing
            'uri': is_uri,
            'url': is_url,
            'urn': is_urn,
        }
