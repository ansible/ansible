# -*- coding: utf-8 -*-
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

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pytest
from ansible.plugins.loader import lookup_loader
from ansible.template import Templar
from units.mock.loader import DictDataLoader

fake_loader = DictDataLoader()
templar = Templar(loader=fake_loader, variables={})

def test_env_var_overrides_omission(monkeypatch):
    user_arguments = {'attribute': 'has-ec2-classic', 'region': 'us-east-1'}
    instance = lookup_loader.get('aws_account_attribute', fake_loader, templar)
    monkeypatch.setenv('AWS_PROFILE', 'env_test_profile')
    instance.set_options(direct=user_arguments)

    assert instance.get_option('aws_profile') == 'env_test_profile'
    assert len(instance._options) == 6

def test_env_var_precedence(monkeypatch):
    user_arguments = {'attribute': 'has-ec2-classic', 'region': 'us-east-2'}
    instance = lookup_loader.get('aws_account_attribute', fake_loader, templar)
    monkeypatch.setenv('AWS_REGION', 'us-east-1')
    instance.set_options(direct=user_arguments)

    assert instance.get_option('region') == 'us-east-2'
    assert len(instance._options) == 6

def test_all_options_available(monkeypatch):
    user_arguments = {}
    instance = lookup_loader.get('aws_account_attribute', fake_loader, templar)
    instance.set_options(direct=user_arguments)

    assert instance._options == dict.fromkeys(['attribute', 'aws_profile', 'aws_access_key',
                                               'aws_secret_key', 'aws_security_token', 'region'])
