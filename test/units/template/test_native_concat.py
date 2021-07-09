# Copyright: (c) 2019, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import importlib
import sys

import pytest

from ansible import constants as C
from ansible.errors import AnsibleUndefinedVariable
from ansible.playbook.conditional import Conditional

from units.mock.loader import DictDataLoader


@pytest.fixture
def enable_jinja2_native(monkeypatch):
    monkeypatch.delitem(sys.modules, 'ansible.template')
    monkeypatch.setattr(C, 'DEFAULT_JINJA2_NATIVE', True)
    mod = importlib.import_module('ansible.template')
    globals()['Templar'] = mod.Templar
    globals()['AnsibleNativeEnvironment'] = mod.AnsibleNativeEnvironment


@pytest.mark.usefixtures("enable_jinja2_native")
class TestNativeConcat:
    # https://github.com/ansible/ansible/issues/52158
    def test_undefined_variable(self):
        fake_loader = DictDataLoader({})
        variables = {}
        templar = Templar(loader=fake_loader, variables=variables)  # pylint: disable=undefined-variable
        assert isinstance(templar.environment, AnsibleNativeEnvironment)  # pylint: disable=undefined-variable

        with pytest.raises(AnsibleUndefinedVariable):
            templar.template("{{ missing }}")

    def test_cond_eval(self):
        fake_loader = DictDataLoader({})
        # True must be stored in a variable to trigger templating. Using True
        # directly would be caught by optimization for bools to short-circuit
        # templating.
        variables = {"foo": True}
        templar = Templar(loader=fake_loader, variables=variables)  # pylint: disable=undefined-variable
        assert isinstance(templar.environment, AnsibleNativeEnvironment)  # pylint: disable=undefined-variable

        cond = Conditional(loader=fake_loader)
        cond.when = ["foo"]
        assert cond.evaluate_conditional(templar, variables)
