# (c) 2015, Filipe Niero Felisbino <filipenf@gmail.com>
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

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.errors import AnsibleError
from ansible.plugins.lookup import LookupBase
from ansible.utils.listify import listify_lookup_plugin_terms

try:
    from jsonpath_rw import jsonpath, parse
    HAS_LIB = True
except ImportError:
    HAS_LIB = False


def json_query(data, expr):
    '''Query data using json-path based query language. Example:
    - debug: msg="{{ instance | .tagged_instances[*].block_device_mapping..volume_id') }}"
    '''
    if not HAS_LIB:
        raise AnsibleError('You need to install "jsonpath_rw" prior to running '
                           'query filter')

    return [match.value for match in parse(expr).find(data)]

class FilterModule(object):
    ''' Query filter '''

    def filters(self):
        return {
            'json_query': json_query
        }
