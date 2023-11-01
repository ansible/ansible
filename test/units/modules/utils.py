from __future__ import annotations

import json

import unittest
from unittest.mock import patch
from ansible.module_utils import basic
from ansible.module_utils.common.text.converters import to_bytes


def set_module_args(args):
    args['_ansible_remote_tmp'] = '/tmp'
    args['_ansible_keep_remote_files'] = False

    args = json.dumps({'ANSIBLE_MODULE_ARGS': args})
    basic._ANSIBLE_ARGS = to_bytes(args)


class AnsibleExitJson(Exception):
    pass


class AnsibleFailJson(Exception):
    pass


def exit_json(*args, **kwargs):
    raise AnsibleExitJson(kwargs)


def fail_json(*args, **kwargs):
    kwargs['failed'] = True
    raise AnsibleFailJson(kwargs)


class ModuleTestCase(unittest.TestCase):

    def setUp(self):
        self.mock_module = patch.multiple(basic.AnsibleModule, exit_json=exit_json, fail_json=fail_json)
        self.mock_module.start()
        self.mock_sleep = patch('time.sleep')
        self.mock_sleep.start()
        set_module_args({})
        self.addCleanup(self.mock_module.stop)
        self.addCleanup(self.mock_sleep.stop)
