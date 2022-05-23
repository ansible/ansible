# Copyright (c) 2022 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from ansible.playbook.attribute import FieldAttribute
from ansible.playbook.block import Block
from ansible.module_utils.six import string_types


class HandlerBlock(Block):

    _listen = FieldAttribute(isa='list', default=list, listof=string_types, static=True)

    def __init__(self, play=None, parent_block=None, role=None, task_include=None, implicit=False):
        self.cached_name = False

        super().__init__(
            play=play,
            parent_block=parent_block,
            role=role,
            task_include=task_include,
            implicit=implicit,
        )

        self._use_handlers = True

    def __repr__(self):
        return "HANDLERBLOCK(uuid=%s)(id=%s)(parent=%s)" % (self._uuid, id(self), self._parent)

    def get_name(self, include_role_fqcn=True):
        '''Return the name of the block'''
        if self._role:
            role_name = self._role.get_name(include_role_fqcn=include_role_fqcn)

        if self._role and self.name:
            return "%s : %s" % (role_name, self.name)

        return self.name

    @staticmethod
    def load(data, play=None, parent_block=None, role=None, task_include=None, variable_manager=None, loader=None):
        implicit = not HandlerBlock.is_block(data)
        b = HandlerBlock(play=play, parent_block=parent_block, role=role, task_include=task_include, implicit=implicit)
        return b.load_data(data, variable_manager=variable_manager, loader=loader)
