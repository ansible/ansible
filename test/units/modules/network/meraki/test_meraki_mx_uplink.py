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

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import json
import os
import pytest

from copy import deepcopy
from units.compat import unittest, mock
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.meraki.meraki import (MerakiModule,
                                                        meraki_argument_spec,
                                                        )
from ansible.modules.network.meraki.meraki_mx_uplink import (clean_custom_format,
                                                             meraki_struct_to_custom_format,
                                                             )
from ansible.module_utils.six import PY2, PY3
from ansible.module_utils._text import to_native, to_bytes
from units.modules.utils import set_module_args

fixture_path = os.path.join(os.path.dirname(__file__), 'fixtures')
fixture_data = {}
testcase_data = {
    "params": {'orgs': ['orgs.json'],
               }
}


def load_fixture(name):
    path = os.path.join(fixture_path, name)

    if path in fixture_data:
        return fixture_data[path]

    with open(path) as f:
        data = f.read()

    # try:
    data = json.loads(data)
    # except Exception:
    #     pass

    fixture_data[path] = data
    return data


@pytest.fixture(scope="module")
def module():
    argument_spec = meraki_argument_spec()
    set_module_args({'auth_key': 'abc123',
                     })
    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=False)
    return MerakiModule(module)


def test_meraki_struct_to_custom_format():
    input = load_fixture('mx_uplink_args.json')
    input['ansible_format']['cellular']['bandwidth_limits']['limit_down'] = 0
    input['ansible_format']['cellular']['bandwidth_limits']['limit_up'] = 0
    input['meraki_format']['bandwidthLimits']['cellular']['limitDown'] = 0
    input['meraki_format']['bandwidthLimits']['cellular']['limitUp'] = 0
    meraki_data = deepcopy(input['meraki_format'])
    print(meraki_data)
    meraki_data = meraki_struct_to_custom_format(meraki_data)
    assert meraki_data == input['ansible_format']


def test_clean_custom_format():
    data = load_fixture('mx_uplink_args.json')
    meraki_data = deepcopy(data['ansible_format'])
    cleaned_data = clean_custom_format(meraki_data)
    print(cleaned_data)
    assert cleaned_data['cellular']['bandwidth_limits']['limit_up'] == 0
    assert cleaned_data['cellular']['bandwidth_limits']['limit_down'] == 0
