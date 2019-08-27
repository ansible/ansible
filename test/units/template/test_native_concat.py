# Copyright: (c) 2019, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pytest

from ansible import constants as C
from ansible.errors import AnsibleUndefinedVariable

# need to mock DEFAULT_JINJA2_NATIVE here so native modules are imported
# correctly within the template module
C.DEFAULT_JINJA2_NATIVE = True
from ansible.template import Templar

from units.mock.loader import DictDataLoader


# https://github.com/ansible/ansible/issues/52158
def test_undefined_variable():
    fake_loader = DictDataLoader({})
    variables = {}
    templar = Templar(loader=fake_loader, variables=variables)

    with pytest.raises(AnsibleUndefinedVariable):
        templar.template("{{ missing }}")
