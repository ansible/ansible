# (c) 2012-2014, Michael DeHaan <michael.dehaan@gmail.com>
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

from ansible.compat.six import string_types

from ansible.errors import AnsibleParserError

from ansible.playbook.attribute import FieldAttribute
from ansible.playbook.base import Base
from ansible.playbook.become import Become
from ansible.playbook.block import Block
from ansible.playbook.helpers import load_list_of_blocks, load_list_of_roles
from ansible.playbook.role import Role
from ansible.playbook.taggable import Taggable
from ansible.vars import preprocess_vars

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()


__all__ = ['VarsScope']


class VarsScope(Base):

    """
    A vars scope is a container for global variables, defined using any
    of vars, vars_files, or vars_prompt attributes.

    """

    # Variable Attributes
    _vars_files          = FieldAttribute(isa='list', default=[], priority=99)
    _vars_prompt         = FieldAttribute(isa='list', default=[], always_post_validate=True)
    _vault_password      = FieldAttribute(isa='string', always_post_validate=True)

    def get_name(self):
        ''' return the name of the Play '''
        return self._attributes.get('name')

    def _load_vars_prompt(self, attr, ds):
        new_ds = preprocess_vars(ds)
        vars_prompts = []
        for prompt_data in new_ds:
            if 'name' not in prompt_data:
                display.deprecated("Using the 'short form' for vars_prompt has been deprecated")
                for vname, prompt in prompt_data.iteritems():
                    vars_prompts.append(dict(
                        name      = vname,
                        prompt    = prompt,
                        default   = None,
                        private   = None,
                        confirm   = None,
                        encrypt   = None,
                        salt_size = None,
                        salt      = None,
                    ))
            else:
                vars_prompts.append(prompt_data)
        return vars_prompts

    def get_vars(self):
        return self.vars.copy()

    def get_vars_files(self):
        return self.vars_files

    def copy(self):
        new_me = super(VarsScope, self).copy()
        new_me.vars = self.vars.copy()
        return new_me
