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

from ansible.errors import AnsibleError, AnsibleFilterError

try:
    import jmespath
    HAS_LIB = True
except ImportError:
    HAS_LIB = False


def json_query(data, expr):
    '''Query data using jmespath query language ( http://jmespath.org ). Example:
    - debug: msg="{{ instance | json_query(tagged_instances[*].block_device_mapping.*.volume_id') }}"
    '''
    if not HAS_LIB:
        raise AnsibleError('You need to install "jmespath" prior to running '
                           'json_query filter')

    try:
        return jmespath.search(expr, data)
    except jmespath.exceptions.JMESPathError as e:
        raise AnsibleFilterError('JMESPathError in json_query filter plugin:\n%s' % e)
    except Exception as e:
        # For older jmespath, we can get ValueError and TypeError without much info.
        raise AnsibleFilterError('Error in jmespath.search in json_query filter plugin:\n%s' % e)


class FilterModule(object):
    ''' Query filter '''

    def filters(self):
        return {
            'json_query': json_query
        }
