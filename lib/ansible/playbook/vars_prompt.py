from __future__ import annotations

from ansible.playbook.attribute import NonInheritableFieldAttribute
from ansible.playbook.base import FieldAttributeBase


class VarsPrompt(FieldAttributeBase):

    name = NonInheritableFieldAttribute(isa='string', always_post_validate=True)
    prompt = NonInheritableFieldAttribute(isa='string')
    default = NonInheritableFieldAttribute(isa='raw')
    private = NonInheritableFieldAttribute(isa='bool', default=True)
    confirm = NonInheritableFieldAttribute(isa='bool')
    encrypt = NonInheritableFieldAttribute(isa='bool')
    salt_size = NonInheritableFieldAttribute(isa='int')
    salt = NonInheritableFieldAttribute(isa='string')
    unsafe = NonInheritableFieldAttribute(isa='bool')

    def __init__(self):
        super(VarsPrompt, self).__init__()

    @staticmethod
    def load(data, variable_manager=None, loader=None):
        t = LoopControl()
        return t.load_data(data, variable_manager=variable_manager, loader=loader)
