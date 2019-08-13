# -*- coding: utf-8 -*-
#
# Copyright: (c) 2019, Bojan Vitnik <bvitnik@mainstream.rs>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


def test_xapi_to_module_vm_power_state_bad_power_state(xenserver):
    """Tests that None is returned on bad power state."""
    assert xenserver.xapi_to_module_vm_power_state("bad") is None


def test_module_to_xapi_vm_power_state_bad_power_state(xenserver):
    """Tests that None is returned on bad power state."""
    assert xenserver.module_to_xapi_vm_power_state("bad") is None
