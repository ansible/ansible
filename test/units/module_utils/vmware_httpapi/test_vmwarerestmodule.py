from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import logging

import pytest

from ansible.module_utils.connection import Connection
import ansible.module_utils.vmware_httpapi.VmwareRestModule as VmwareRestModule
import ansible.module_utils.basic
from ansible.plugins.httpapi.vmware import HttpApi


class ConnectionLite(Connection):

    _url = 'https://vcenter.test'
    _messages = []
    _auth = False

    def __init__(self, socket):
        pass


def test_get_url_with_filter(monkeypatch):
    argument_spec = VmwareRestModule.VmwareRestModule.create_argument_spec(use_filters=True)
    argument_spec.update(
        object_type=dict(type='str', default='datacenter'),
    )

    def fake_load_params():
        return {'object_type': 'vm', 'filters': [{'names': 'a'}]}

    monkeypatch.setattr(ansible.module_utils.basic, "_load_params", fake_load_params)
    monkeypatch.setattr(VmwareRestModule, "Connection", ConnectionLite)
    module = VmwareRestModule.VmwareRestModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        use_object_handler=True)
    object_type = module.params['object_type']

    url = module.get_url_with_filter(object_type)
    assert url == '/rest/vcenter/vm?filter.names=a'
