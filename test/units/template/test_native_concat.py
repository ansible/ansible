# Copyright: (c) 2019, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pytest

from ansible import constants as C
# NOTE DEFAULT_JINJA2_NATIVE must be mocked here first so native
# modules are imported correctly within the template module.
# Any imports that would import ansible.template at any level
# must not be imported before setting DEFAULT_JINJA2_NATIVE.
C.DEFAULT_JINJA2_NATIVE = True
from ansible.template import Templar, AnsibleNativeEnvironment

from ansible.errors import AnsibleUndefinedVariable
from ansible.playbook.conditional import Conditional

from units.mock.loader import DictDataLoader


# https://github.com/ansible/ansible/issues/52158
def test_undefined_variable():
    fake_loader = DictDataLoader({})
    variables = {}
    templar = Templar(loader=fake_loader, variables=variables)
    assert isinstance(templar.environment, AnsibleNativeEnvironment)

    with pytest.raises(AnsibleUndefinedVariable):
        templar.template("{{ missing }}")


def test_cond_eval():
    fake_loader = DictDataLoader({})
    variables = {"foo": True}
    templar = Templar(loader=fake_loader, variables=variables)
    assert isinstance(templar.environment, AnsibleNativeEnvironment)

    cond = Conditional(loader=fake_loader)
    cond.when = ["foo"]
    assert cond.evaluate_conditional(templar, variables)
