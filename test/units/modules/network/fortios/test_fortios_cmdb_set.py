#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2017 Fortinet, Inc.
#
# Author: Miguel Angel Munoz (magonzalez at fortinet.com) and 
#         Nicolas Thomas (nthomas at fortinet.com)
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import sys
from nose.plugins.skip import SkipTest
if sys.version_info < (2, 7):
    raise SkipTest("Python >= 2.7 is required for running unit tests")

try:
	import library.fortios_cmdb_set as sut
except ImportError:
	try:
		import ansible.modules.network.fortios.fortios_cmdb_set as sut
	except ImportError:
		raise SkipTest("FortiOS Ansible module not found")

try:
	from fortiosapi import FortiOSAPI
except ImportError:
	raise SkipTest("FortiOS Ansible module requires FortiOSapi")

import ansible.module_utils.basic
import requests


def test_cmdb_set(monkeypatch):
    def set(self, path, name, vdom=None,
            mkey=None, parameters=None, data=None):
        return {'status': 'success', 'version': '5.6.2'}

    monkeypatch.setattr(FortiOSAPI,
                        'login',
                        lambda self, host, username, password: True)
    monkeypatch.setattr(FortiOSAPI, 'set', set)
    monkeypatch.setattr(FortiOSAPI, 'logout', lambda _: True)

    is_error, is_changed, result = sut.fortios_cmdb_set(
        {"host": "192.168.122.40",
         "username": "admin",
         "password": "",
         "endpoint": "router static",
         "vdom": "global",
         "config_parameters": {"seq-num": 8,
                               "dst": "10.10.32.0 255.255.255.0",
                               "device": "port2",
                               "gateway": "192.168.40.252"}
         })
    assert not is_error
    assert is_changed
    assert result is not None


def test_cmdb_set_failed(monkeypatch):
    def set(self, path, name, vdom=None,
            mkey=None, parameters=None, data=None):
        return {'status': 'error', 'version': '5.6.2'}

    monkeypatch.setattr(FortiOSAPI,
                        'login',
                        lambda self, host, username, password: True)
    monkeypatch.setattr(FortiOSAPI, 'set', set)
    monkeypatch.setattr(FortiOSAPI, 'logout', lambda _: True)

    is_error, is_changed, result = sut.fortios_cmdb_set(
        {"host": "192.168.122.40",
         "username": "admin",
         "password": "",
         "endpoint": "router static",
         "vdom": "global",
         "config_parameters": {"seq-num": 8,
                               "dst": "10.10.32.0 255.255.255.0",
                               "device": "port2",
                               "gateway": "192.168.40.252"}
         })
    assert is_error
    assert not is_changed
    assert result is not None


def test_required_params(monkeypatch):
    def ansible_constructor(self, argument_spec, bypass_checks=False,
                            no_log=False, check_invalid_arguments=True,
                            mutually_exclusive=None, required_together=None,
                            required_one_of=None, add_file_common_args=False,
                            supports_check_mode=False, required_if=None):
        self.params = ""
        self.cleanup_files = ""
        self._warnings = ""
        self._deprecations = ""
        self.no_log_values = ""

        assert 'host' in argument_spec
        assert argument_spec['host']['required']
        assert 'username' in argument_spec
        assert argument_spec['username']['required']
        assert 'endpoint' in argument_spec
        assert argument_spec['endpoint']['required']
        assert 'config_parameters' in argument_spec
        assert argument_spec['config_parameters']['required']

    monkeypatch.setattr(ansible.module_utils.basic.AnsibleModule,
                        '__init__',
                        ansible_constructor)
    monkeypatch.setattr(sut,
                        'fortios_cmdb_set',
                        lambda _: (False,
                                   True,
                                   {'status': 'error', 'version': '5.6.2'}))
    monkeypatch.setattr(sys, 'exit', lambda x: True)

    sut.main()


def test_optional_params(monkeypatch):
    def ansible_constructor(self, argument_spec, bypass_checks=False,
                            no_log=False, check_invalid_arguments=True,
                            mutually_exclusive=None, required_together=None,
                            required_one_of=None, add_file_common_args=False,
                            supports_check_mode=False, required_if=None):
        self.params = ""
        self.cleanup_files = ""
        self._warnings = ""
        self._deprecations = ""
        self.no_log_values = ""

        assert 'password' in argument_spec
        assert not argument_spec['password']['required']
        assert 'vdom' in argument_spec
        assert not argument_spec['vdom']['required']
        assert 'mkey' in argument_spec
        assert not argument_spec['mkey']['required']

        return

    monkeypatch.setattr(ansible.module_utils.basic.AnsibleModule,
                        '__init__',
                        ansible_constructor)
    monkeypatch.setattr(sut,
                        'fortios_cmdb_set',
                        lambda _: (False,
                                   True,
                                   {'status': 'error', 'version': '5.6.2'}))
    monkeypatch.setattr(sys, 'exit', lambda x: True)

    sut.main()


def test_endpoint_properly_built(monkeypatch):
    class Result():

        content = ""
        x = 0

        def calculate_result(self):
            if Result.x == 0:
                self.content = b'1document.location="/ng/prompt?viewOnly&redir'
                Result.x += 1
            else:
                self.content = b'[{ "result":"200", ' \
                               b'"http_status":200, ' \
                               b'"status":"success", ' \
                               b'"version":"5.6.2"}]'

    def get(self, path, name, vdom=None, mkey=None, parameters=None):
        return {'version': '5.6.2.'}

    def post(self, url, data=None, json=None, **kwargs):
        if url != 'https://192.168.122.40/logincheck' and \
                        url != 'https://192.168.122.40/api/v2/cmdb/' \
                               'firewall/policy?global=1':
            assert False, "Url not properly built: %s" % url
        result = Result()
        result.calculate_result()
        return result

    monkeypatch.setattr(requests.Session, 'post', post)
    monkeypatch.setattr(FortiOSAPI, 'get', get)
    monkeypatch.setattr(FortiOSAPI, 'logout', lambda _: True)

    is_error, is_changed, result = sut.fortios_cmdb_set(
        {"host": "192.168.122.40",
         "username": "admin",
         "password": "",
         "endpoint": "firewall policy",
         "vdom": "global",
         "config_parameters": {"seq-num": 8,
                               "dst": "10.10.32.0 255.255.255.0",
                               "device": "port2",
                               "gateway": "192.168.40.252"}
         })
    assert not is_error
    assert is_changed
    assert result is not None


def test_failed_login(monkeypatch):
    def login(self, host, username, password):
        raise Exception("Failed Login")

    def set(self, path, name, vdom=None,
            mkey=None, parameters=None, data=None):
        return {'status': 'error', 'version': '5.6.2'}

    monkeypatch.setattr(FortiOSAPI, 'login', login)
    monkeypatch.setattr(FortiOSAPI, 'set', set)
    monkeypatch.setattr(FortiOSAPI, 'logout', lambda _: True)

    try:
        sut.fortios_cmdb_set(
            {"host": "192.168.122.40",
             "username": "admin",
             "password": "",
             "endpoint": "router static",
             "vdom": "global",
             "config_parameters": {"seq-num": 8,
                                   "dst": "10.10.32.0 255.255.255.0",
                                   "device": "port2",
                                   "gateway": "192.168.40.252"}
             })
        assert False, "Error: No exception raised when failed login"
    except Exception:
        pass
