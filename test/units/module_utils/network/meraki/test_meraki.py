# -*- coding: utf-8 -*-

# Copyright 2019 Kevin Breit <kevin.breit@kevinbreit.net>

# This file is part of Ansible by Red Hat
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

import sys

from units.compat import unittest
from ansible.module_utils.network.meraki.meraki import MerakiModule
from ansible.module_utils.six import PY2, PY3
from ansible.module_utils._text import to_native, to_bytes

import pytest

def set_module_args(args):
    args = json.dumps({'ANSIBLE_MODULE_ARGS': args})
    basic._ANSIBLE_ARGS = to_bytes(args)

def exit_json(*args, **kwargs):
    if 'changed' not in kwargs:
        kwargs['changed'] = False
    raise AnsibleExitJson(kwargs)

def fail_json(*args, **kwargs):
    if 'changed' not in kwargs:
        kwargs['changed'] = False
    raise AnsibleFailJson(kwargs)

class AltModule():
    params = dict(use_https='True',
                  state='present',
                  )

class AltMerakiModule(MerakiModule):
    def __init__(self):
        self.result = dict(changed=False)
        self.module = MerakiModule

meraki = AltMerakiModule()

class MerakiRest(unittest.TestCase):
    def test_define_protocol(self):
        set_module_args({'use_https': True,
                         })
        cdata = 'https'
        testdata = meraki.define_protocol()
        self.assertEqual(cdata, testdata)
