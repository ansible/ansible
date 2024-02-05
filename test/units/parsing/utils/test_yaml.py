# -*- coding: utf-8 -*-
# (c) 2017, Ansible Project
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

from __future__ import annotations

import pytest

from ansible.errors import AnsibleParserError
from ansible.parsing.utils.yaml import from_yaml


def test_from_yaml_simple():
    assert from_yaml(u'---\n- test: 1\n  test2: "2"\n- caf\xe9: "caf\xe9"') == [{u'test': 1, u'test2': u"2"}, {u"caf\xe9": u"caf\xe9"}]


def test_bad_yaml():
    with pytest.raises(AnsibleParserError):
        from_yaml(u'foo: bar: baz')
