# (c) 2017, Andrea Scarpino <me@andreascarpino.it>
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.
# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from functools import partial
import types

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


def uri(value, query = ''):
    ''' Check if string is an URI and filter it '''

    query_func_map = {
        'hostname': _hostname_query,
        'path': _path_query,
        'port': _port_query,
        'scheme': _scheme_query,
    }

    try:
        return query_func_map[query](value)
    except KeyError:
        return False


# ---- Ansible filters ----
class FilterModule(object):
    ''' URI filter '''


    def filters(self):
        return {
            'uri': uri
        }
