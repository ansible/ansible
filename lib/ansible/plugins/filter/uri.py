# (c) 2017, Andrea Scarpino <me@andreascarpino.it>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}


try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse

from ansible import errors


def _hostname_query(value):
    ''' Fetch the hostname from an URI '''

    return urlparse(value).hostname


def _path_query(value):
    ''' Fetch the path from an URI '''

    return urlparse(value).path


def _port_query(value):
    ''' Fetch the port from an URI '''

    return urlparse(value).port


def _scheme_query(value):
    ''' Fetch the scheme from an URI '''

    return urlparse(value).scheme


def _default_query(value):
    ''' Return the URL minus the file by default '''

    default_url = urlparse(value).scheme + '://' + urlparse(value).netloc

    return default_url


def uri(value, query='', alias='uri'):
    ''' Check if string is an URI and filter it '''

    query_func_map = {
        'hostname': _hostname_query,
        'path': _path_query,
        'port': _port_query,
        'scheme': _scheme_query,
        '': _default_query
    }

    try:
        return query_func_map[query](value)
    except KeyError:
        raise errors.AnsibleFilterError(alias + ': unknown filter type: %s' % query)
    return False


# ---- Ansible filters ----
class FilterModule(object):
    ''' URI filter '''

    def filters(self):
        return {
            'uri': uri
        }
