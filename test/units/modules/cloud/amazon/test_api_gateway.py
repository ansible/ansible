#
# (c) 2016 Michael De La Rue
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

from nose.plugins.skip import SkipTest
import pytest
import sys
import json
from ansible.module_utils._text import to_bytes
from ansible.module_utils import basic
from ansible.module_utils.ec2 import HAS_BOTO3

if not HAS_BOTO3:
    raise SkipTest("test_api_gateway.py requires the `boto3` and `botocore` modules")

import ansible.modules.cloud.amazon.aws_api_gateway as agw


def set_module_args(args):
    args = json.dumps({'ANSIBLE_MODULE_ARGS': args})
    basic._ANSIBLE_ARGS = to_bytes(args)


exit_return_dict = {}


def fake_exit_json(self, **kwargs):
    """ store the kwargs given to exit_json rather than putting them out to stdout"""
    global exit_return_dict
    exit_return_dict = kwargs
    sys.exit(0)


def test_upload_api(monkeypatch):
    class FakeConnection:

        def put_rest_api(self, *args, **kwargs):
            assert kwargs["body"] == "the-swagger-text-is-fake"
            return {"msg": "success!"}

    def return_fake_connection(*args, **kwargs):
        return FakeConnection()

    monkeypatch.setattr(agw, "boto3_conn", return_fake_connection)
    monkeypatch.setattr(agw.AnsibleModule, "exit_json", fake_exit_json)

    set_module_args({
        "api_id": "fred",
        "state": "present",
        "swagger_text": "the-swagger-text-is-fake",
        "region": 'mars-north-1',
    })
    with pytest.raises(SystemExit):
        agw.main()
    assert exit_return_dict["changed"]


def test_warn_if_region_not_specified():

    set_module_args({
        "name": "aws_api_gateway",
        "state": "present",
        "runtime": 'python2.7',
        "role": 'arn:aws:iam::987654321012:role/lambda_basic_execution',
        "handler": 'lambda_python.my_handler'})
    with pytest.raises(SystemExit):
        print(agw.main())
