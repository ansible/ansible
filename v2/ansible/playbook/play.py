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

from ansible.errors import AnsibleError, AnsibleParserError

from ansible.parsing.yaml import DataLoader

from ansible.playbook.attribute import Attribute, FieldAttribute
from ansible.playbook.base import Base
from ansible.playbook.helpers import load_list_of_blocks, load_list_of_roles, compile_block_list
from ansible.playbook.role import Role


__all__ = ['Play']


class Play(Base):

    """
    A play is a language feature that represents a list of roles and/or
    task/handler blocks to execute on a given set of hosts.

    Usage:

       Play.load(datastructure) -> Play
       Play.something(...)
    """

    # =================================================================================
    # Connection-Related Attributes
    _accelerate          = FieldAttribute(isa='bool', default=False)
    _accelerate_ipv6     = FieldAttribute(isa='bool', default=False)
    _accelerate_port     = FieldAttribute(isa='int', default=5099)
    _connection          = FieldAttribute(isa='string', default='smart')
    _gather_facts        = FieldAttribute(isa='string', default='smart')
    _hosts               = FieldAttribute(isa='list', default=[])
    _name                = FieldAttribute(isa='string', default='<no name specified>')
    _port                = FieldAttribute(isa='int', default=22)
    _remote_user         = FieldAttribute(isa='string', default='root')
    _su                  = FieldAttribute(isa='bool', default=False)
    _su_user             = FieldAttribute(isa='string', default='root')
    _sudo                = FieldAttribute(isa='bool', default=False)
    _sudo_user           = FieldAttribute(isa='string', default='root')
    _tags                = FieldAttribute(isa='list', default=[])

    # Variable Attributes
    _vars                = FieldAttribute(isa='dict', default=dict())
    _vars_files          = FieldAttribute(isa='list', default=[])
    _vars_prompt         = FieldAttribute(isa='dict', default=dict())
    _vault_password      = FieldAttribute(isa='string')

    # Block (Task) Lists Attributes
    _handlers            = FieldAttribute(isa='list', default=[])
    _pre_tasks           = FieldAttribute(isa='list', default=[])
    _post_tasks          = FieldAttribute(isa='list', default=[])
    _tasks               = FieldAttribute(isa='list', default=[])

    # Role Attributes
    _roles               = FieldAttribute(isa='list', default=[])

    # Flag/Setting Attributes
    _any_errors_fatal    = FieldAttribute(isa='bool', default=False)
    _max_fail_percentage = FieldAttribute(isa='string', default='0')
    _no_log              = FieldAttribute(isa='bool', default=False)
    _serial              = FieldAttribute(isa='int', default=0)

    # =================================================================================

    def __init__(self):
        super(Play, self).__init__()

    def __repr__(self):
        return self.get_name()

    def get_name(self):
       ''' return the name of the Play '''
       return "PLAY: %s" % self._attributes.get('name')

    @staticmethod
    def load(data, loader=None):
        p = Play()
        return p.load_data(data, loader=loader)

    def munge(self, ds):
        '''
        Adjusts play datastructure to cleanup old/legacy items
        '''

        assert isinstance(ds, dict)

        # The use of 'user' in the Play datastructure was deprecated to
        # line up with the same change for Tasks, due to the fact that
        # 'user' conflicted with the user module.
        if 'user' in ds:
            # this should never happen, but error out with a helpful message
            # to the user if it does...
            if 'remote_user' in ds:
                raise AnsibleParserError("both 'user' and 'remote_user' are set for %s. The use of 'user' is deprecated, and should be removed" % self.get_name(), obj=ds)

            ds['remote_user'] = ds['user']
            del ds['user']

        return ds

    def _load_tasks(self, attr, ds):
        '''
        Loads a list of blocks from a list which may be mixed tasks/blocks.
        Bare tasks outside of a block are given an implicit block.
        '''
        return load_list_of_blocks(ds, loader=self._loader)

    def _load_pre_tasks(self, attr, ds):
        '''
        Loads a list of blocks from a list which may be mixed tasks/blocks.
        Bare tasks outside of a block are given an implicit block.
        '''
        return load_list_of_blocks(ds, loader=self._loader)

    def _load_post_tasks(self, attr, ds):
        '''
        Loads a list of blocks from a list which may be mixed tasks/blocks.
        Bare tasks outside of a block are given an implicit block.
        '''
        return load_list_of_blocks(ds, loader=self._loader)

    def _load_handlers(self, attr, ds):
        '''
        Loads a list of blocks from a list which may be mixed handlers/blocks.
        Bare handlers outside of a block are given an implicit block.
        '''
        return load_list_of_blocks(ds, loader=self._loader)

    def _load_roles(self, attr, ds):
        '''
        Loads and returns a list of RoleInclude objects from the datastructure
        list of role definitions
        '''
        return load_list_of_roles(ds, loader=self._loader)

    # FIXME: post_validation needs to ensure that su/sudo are not both set

    def _compile_roles(self):
        '''
        Handles the role compilation step, returning a flat list of tasks
        with the lowest level dependencies first. For example, if a role R
        has a dependency D1, which also has a dependency D2, the tasks from
        D2 are merged first, followed by D1, and lastly by the tasks from
        the parent role R last. This is done for all roles in the Play.
        '''

        task_list = []

        if len(self.roles) > 0:
            for ri in self.roles:
                # The internal list of roles are actually RoleInclude objects,
                # so we load the role from that now
                role = Role.load(ri)

                # FIXME: evauluate conditional of roles here?
                task_list.extend(role.compile())

        return task_list

    def compile(self):
        '''
        Compiles and returns the task list for this play, compiled from the
        roles (which are themselves compiled recursively) and/or the list of
        tasks specified in the play.
        '''

        task_list = []

        task_list.extend(compile_block_list(self.pre_tasks))
        task_list.extend(self._compile_roles())
        task_list.extend(compile_block_list(self.tasks))
        task_list.extend(compile_block_list(self.post_tasks))

        return task_list
