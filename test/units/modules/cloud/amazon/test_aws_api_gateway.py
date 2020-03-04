#
# (c) 2016 Michael De La Rue
#
# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import sys

import pytest

from ansible.module_utils.ec2 import HAS_BOTO3
from units.modules.utils import set_module_args

if not HAS_BOTO3:
    pytestmark = pytest.mark.skip("test_api_gateway.py requires the `boto3` and `botocore` modules")

import ansible.modules.cloud.amazon.aws_api_gateway as agw
from ansible.module_utils.aws import core


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

    monkeypatch.setattr(core, "boto3_conn", return_fake_connection)
    monkeypatch.setattr(core.AnsibleAWSModule, "exit_json", fake_exit_json)

    set_module_args({
        "api_id": "fred",
        "state": "present",
        "swagger_text": "the-swagger-text-is-fake",
        "region": 'mars-north-1',
        "_ansible_tmpdir": "/tmp/ansibl-abcdef",
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
