import base64
import importlib
import logging
import os.path
import pytest
import ssl
import sys
import urllib.request

from units.compat.mock import Mock
import vcr

import ansible.module_utils.basic
import ansible.module_utils.vmware_httpapi.VmwareRestModule
import ansible.plugins.httpapi.vmware

logging.basicConfig()
vcr_log = logging.getLogger("vcr")
vcr_log.setLevel(logging.DEBUG)

vcenter_url = 'https://vcenter.test'
username = 'administrator@vsphere.local'
password = '!234AaAa56'


def enable_vcr():
    import inspect
    stack = inspect.stack()
    test_file_name = os.path.basename(stack[1].filename)
    module_name = test_file_name.split('.')[0]

    my_vcr = vcr.VCR(
        cassette_library_dir='test/units/modules/cloud/vmware_httpapi/' + module_name,
        path_transformer=vcr.VCR.ensure_suffix('.yaml'),
        # switch the record_mode to 'all' if you want to switch to the
        # record mode. VCR will just act as a proxy and record the communication between
        # the vcenter server and pytest.
        record_mode='all',
        #record_mode='once',
    )
    return my_vcr.use_cassette


class ConnectionPlugin():
    def __init__(self):
        self._url = ''
        self._token = None

    def send(self, path, data, method=None, headers=None, force_basic_auth=True):
        url = vcenter_url + path
        req = urllib.request.Request(url, headers=headers, data=data.encode(), method=method)
        if self._token:
            req.add_header("vmware-api-session-id", self._token)
        else:
            auth_text = "%s:%s" % (username,password)
            b64auth = base64.standard_b64encode(auth_text.encode())
            req.add_header("Authorization", "Basic %s" % b64auth.decode())
        gcontext = ssl.SSLContext()
        r = urllib.request.urlopen(req, context=gcontext)
        import io
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
        def fake_load_params():
            return params

        exit_json = Mock()
        fail_json = Mock()
        monkeypatch.setattr(ansible.module_utils.basic.AnsibleModule, "exit_json", exit_json)
        monkeypatch.setattr(ansible.module_utils.basic.AnsibleModule, "fail_json", fail_json)
        monkeypatch.setattr(sys, "exit", Mock())
        monkeypatch.setattr(ansible.module_utils.basic, "_load_params", fake_load_params)
        monkeypatch.setattr(ansible.module_utils.vmware_httpapi.VmwareRestModule, "Connection", ConnectionLite)
        loaded_m = importlib.import_module('ansible.modules.cloud.vmware_httpapi.' + module)
        loaded_m.main()
        return (exit_json, fail_json)
    return func
