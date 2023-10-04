# Copyright: (c) 2019, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

from ansible.playbook.conditional import Conditional
from ansible.template import Templar

from units.mock.loader import DictDataLoader


def test_cond_eval():
    fake_loader = DictDataLoader({})
    # True must be stored in a variable to trigger templating. Using True
    # directly would be caught by optimization for bools to short-circuit
    # templating.
    variables = {"foo": True}
    templar = Templar(loader=fake_loader, variables=variables)
    cond = Conditional(loader=fake_loader)
    cond.when = ["foo"]

    with templar.set_temporary_context(jinja2_native=True):
        assert cond.evaluate_conditional(templar, variables)
