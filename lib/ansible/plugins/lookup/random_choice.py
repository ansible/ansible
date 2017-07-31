# (c) 2013, Michael DeHaan <michael.dehaan@gmail.com>
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

import random

from ansible.errors import AnsibleError
from ansible.module_utils._text import to_native
from ansible.plugins.lookup import LookupBase

# useful for introducing chaos ... or just somewhat reasonably fair selection
# amongst available mirrors
#
#    tasks:
#        - debug: msg=$item
#          with_random_choice:
#             - one
#             - two
#             - three


class LookupModule(LookupBase):

    def run(self, terms, inject=None, **kwargs):

        ret = terms
        if terms:
            try:
                ret = [random.choice(terms)]
            except Exception as e:
                raise AnsibleError("Unable to choose random term: %s" % to_native(e))

        return ret
