from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import base64
import importlib
import inspect
import io
import json
import logging
import os.path
import pytest
import ssl
import sys

from units.compat.mock import Mock

import ansible.module_utils.basic
import ansible.module_utils.vmware_httpapi.VmwareRestModule
import ansible.plugins.httpapi.vmware

from ansible.module_utils.six.moves.urllib.request import urlopen
from ansible.module_utils.six.moves.urllib.request import Request


if sys.version_info >= (2, 7):
    import vcr

logging.basicConfig()
vcr_log = logging.getLogger("vcr")
vcr_log.setLevel(logging.DEBUG)

vcenter_url = 'https://vcenter.test'
username = 'administrator@vsphere.local'
password = '!234AaAa56'


def skip_py26(a):
    pytest.mark.skip("vmware_guest Ansible modules require Python >= 2.7")


def enable_vcr():
    if sys.version_info < (2, 7):
        return skip_py26
    stack = inspect.stack()
    frame = stack[1]
    if hasattr(frame, 'filename'):
        test_file_name = os.path.basename(stack[1].filename)
    else:
        test_file_name = frame[1].split('/')[-1]
    module_name = test_file_name.split('.')[0]

    my_vcr = vcr.VCR(
        cassette_library_dir='test/units/modules/cloud/vmware_httpapi/' + module_name,
        path_transformer=vcr.VCR.ensure_suffix('.yaml'),
        # switch the record_mode to 'all' if you want to switch to the
        # record mode. VCR will just act as a proxy and record the communication between
        # the vcenter server and pytest.
        # record_mode='all',
        record_mode='none',
    )
    return my_vcr.use_cassette


class ConnectionPlugin():
    def __init__(self):
        self._url = ''
        self._token = None

    def send(self, path, data, method=None, headers=None, force_basic_auth=True):
        url = vcenter_url + path
        if str(Request) == 'urllib2.Request':
            if method == 'POST':
                req = Request(url, headers=headers, data=data.encode())
            elif method == 'GET':
                req = Request(url, headers=headers)
        else:
            req = Request(url, headers=headers, data=data.encode(), method=method)
        if self._token:
            req.add_header("vmware-api-session-id", self._token)
        else:
            auth_text = "%s:%s" % (username, password)
            b64auth = base64.standard_b64encode(auth_text.encode())
            req.add_header("Authorization", "Basic %s" % b64auth.decode())
        gcontext = ssl.SSLContext(ssl.PROTOCOL_TLS)
        r = urlopen(req, context=gcontext)
        return (r, io.BytesIO(r.read()))

    def queue_message(self, *args, **kwargs):
        pass


class ConnectionLite(ansible.plugins.httpapi.vmware.HttpApi):

    def __init__(self, socket_path):
        self.connection = ConnectionPlugin()
        self.login(username, password)


@pytest.fixture()
def run_module(monkeypatch):

    def func(module, params):
        exit_json = Mock()
        monkeypatch.setattr(ansible.module_utils.basic.AnsibleModule, "exit_json", exit_json)
        ansible.module_utils.basic._ANSIBLE_ARGS = json.dumps({'ANSIBLE_MODULE_ARGS': params}).encode()
        monkeypatch.setattr(ansible.module_utils.vmware_httpapi.VmwareRestModule, "Connection", ConnectionLite)
        loaded_m = importlib.import_module('ansible.modules.cloud.vmware_httpapi.' + module)
        loaded_m.main()
        return exit_json
    return func
