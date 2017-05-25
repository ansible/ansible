# (c) 2014, Kent R. Spillner <kspillner@acm.org>
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

import collections

from ansible.errors import AnsibleError
from ansible.plugins.lookup import LookupBase

class LookupModule(LookupBase):

    def run(self, terms, variables=None, **kwargs):

        # Expect any type of Mapping, notably hostvars
        if not isinstance(terms, collections.Mapping):
            raise AnsibleError("with_dict expects a dict")

        return self._flatten_hash_to_list(terms)
