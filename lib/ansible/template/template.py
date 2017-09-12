# (c) 2012, Michael DeHaan <michael.dehaan@gmail.com>
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

import jinja2

__all__ = ['AnsibleJ2Template']


class AnsibleJ2Template(jinja2.environment.Template):
    '''
    A helper class, which prevents Jinja2 from running _jinja2_vars through dict().
    Without this, {% include %} and similar will create new contexts unlike the special
    one created in template_from_file. This ensures they are all alike, except for
    potential locals.
    '''

    def new_context(self, vars=None, shared=False, locals=None):
        if vars is not None:
            if isinstance(vars, dict):
                vars = vars.copy()
                if locals is not None:
                    vars.update(locals)
            else:
                vars = vars.add_locals(locals)
        return self.environment.context_class(self.environment, vars, self.name, self.blocks)
