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

from __future__ import annotations

from jinja2.nativetypes import NativeTemplate

__all__ = ['AnsibleJ2Template']


class AnsibleJ2Template(NativeTemplate):
    '''
    A helper class to prevent Jinja2 from processing AnsibleJ2Vars through dict().
    
    The default behavior of {% include %} and similar functions creates new contexts,
    which are different from the special context created in Templar.template. This class ensures 
    that all contexts are similar, except for specific local variables.

    Attributes:
        name: Name of the template.
        blocks: Blocks defined in the template.
        environment: The Jinja2 environment where the template is rendered.
    '''

    def new_context(self, vars=None, shared=False, locals=None):
    # Initialize vars with an empty dictionary or a copy of self.globals
    vars = dict(self.globals or ()) if vars is None else vars.copy()

    # Adding variables locals, if exists
    if locals:
        vars.update(locals)

    return self.environment.context_class(self.environment, vars, self.name, self.blocks)
