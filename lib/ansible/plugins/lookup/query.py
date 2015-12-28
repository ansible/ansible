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
    from dq import query
    HAS_DQ = True
except ImportError:
    HAS_DQ = False

class LookupModule(LookupBase):
    """Enables generic data structure querying by using a json-path based query
    language. This plugin is built on top of dq [https://github.com/mlamby/dq]

    example:
    - debug: "{{item}}"
      with_query:
       - "{{ instance }}"
       - ".tagged_instances[*].block_device_mapping..volume_id"

    or:

    - debug: msg="{{ lookup('query', instance,'.tagged_instances[*].block_device_mapping') }}"

    The instance variable above was registered by the ec2 module.
    """
    def run(self, terms, variables=None, **kwargs):
        if not HAS_DQ:
            raise AnsibleError('You need to install "dq" prior to running '
                               'this module')

        data = listify_lookup_plugin_terms(terms[0], templar=self._templar, loader=self._loader)
        if not isinstance(data, (list, dict)):
            raise AnsibleError("First parameter to query lookup should be a "
                               "list or a dict. %s found" % type(data))
        expr = terms[1]
        result = query(expr, data)
        if hasattr(result, '__iter__'):
            return list(result)
        else:
            return [result]
