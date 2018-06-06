from nose.plugins.skip import SkipTest
try:
    import vcr
except ImportError:
    raise SkipTest('vcr is needed.')
try:
    import avi.sdk
except ImportError:
    raise SkipTest('avisdk is needed.')
import json
import os
from ansible.compat.tests import unittest
from ansible.compat.tests.mock import patch
from ansible.module_utils._text import to_bytes
from ansible.module_utils import basic
from ansible.modules.network.avi import avi_healthmonitor
dir_path = os.path.dirname(os.path.realpath(__file__))

my_vcr = vcr.VCR(
    cassette_library_dir='%s%sfixtures%scassettes' % (
        dir_path, os.path.sep, os.path.sep),
    record_mode='once'
)


def set_module_args(args):
    args = json.dumps({'ANSIBLE_MODULE_ARGS': args})
    basic._ANSIBLE_ARGS = to_bytes(args)


class AnsibleExitJson(Exception):
    """Exception class to be raised by module.exit_json and caught by the test case"""
    pass


class AnsibleFailJson(Exception):
    """Exception class to be raised by module.fail_json and caught by the test case"""
    pass


def exit_json(*args, **kwargs):
    """function to patch over exit_json; package return data into an exception"""
    if 'changed' not in kwargs:
        kwargs['changed'] = False
    raise AnsibleExitJson(kwargs)


def fail_json(*args, **kwargs):
    """function to patch over fail_json; package return data into an exception"""
    kwargs['failed'] = True
    raise AnsibleFailJson(kwargs)


def get_bin_path(self, arg, required=False):
    """Mock AnsibleModule.get_bin_path"""
    if arg.endswith('my_command'):
        return '/usr/bin/my_command'
    else:
        if required:
            fail_json(msg='%r not found !' % arg)


class TestHealthmonitor(unittest.TestCase):
    def setUp(self):
        self.mock_module_helper = patch.multiple(basic.AnsibleModule,
                                                 exit_json=exit_json,
                                                 fail_json=fail_json,
                                                 get_bin_path=get_bin_path)
        self.mock_module_helper.start()
        self.addCleanup(self.mock_module_helper.stop)

    @my_vcr.use_cassette()
    def test1_create_http_hm(self):
        set_module_args({

            "controller": "10.10.26.133",
            "username": "admin",
            "password": "avi123$%",
            "api_version": "17.2.1",
            "https_monitor": {
                "http_request": "HEAD / HTTP/1.0",
                "http_response_code": ["HTTP_2XX", "HTTP_3XX"]
            },
            "receive_timeout": 4,
            "failed_checks": 3,
            "send_interval": 10,
            "successful_checks": 3,
            "type": "HEALTH_MONITOR_HTTPS",
            "name": "MyWebsite-HTTPS"
        })

        with self.assertRaises(AnsibleExitJson) as result:
            avi_healthmonitor.main()
        self.assertTrue(result.exception.args[0]['changed'])

    @my_vcr.use_cassette()
    def test2_create_http_hm_re_run(self):
        set_module_args({

            "controller": "10.10.26.133",
            "username": "admin",
            "password": "avi123$%",
            "api_version": "17.2.1",
            "https_monitor": {
                "http_request": "HEAD / HTTP/1.0",
                "http_response_code": ["HTTP_2XX", "HTTP_3XX"]
            },
            "receive_timeout": 4,
            "failed_checks": 3,
            "send_interval": 10,
            "successful_checks": 3,
            "type": "HEALTH_MONITOR_HTTPS",
            "name": "MyWebsite-HTTPS"
        })

        with self.assertRaises(AnsibleExitJson) as result:
            avi_healthmonitor.main()
        self.assertFalse(result.exception.args[0]['changed'])

    @my_vcr.use_cassette()
    def test3_update_http_hm(self):
        set_module_args({

            "controller": "10.10.26.133",
            "username": "admin",
            "password": "avi123$%",
            "api_version": "17.2.1",
            "https_monitor": {
                "http_request": "HEAD / HTTP/1.0",
                "http_response_code": ["HTTP_2XX", "HTTP_3XX"]
            },
            "receive_timeout": 5,
            "failed_checks": 3,
            "send_interval": 10,
            "successful_checks": 3,
            "type": "HEALTH_MONITOR_HTTPS",
            "name": "MyWebsite-HTTPS"
        })

        with self.assertRaises(AnsibleExitJson) as result:
            avi_healthmonitor.main()
        self.assertTrue(result.exception.args[0]['changed'])

    @my_vcr.use_cassette()
    def test4_update_http_hm_re_run(self):
        set_module_args({

            "controller": "10.10.26.133",
            "username": "admin",
            "password": "avi123$%",
            "api_version": "17.2.1",
            "https_monitor": {
                "http_request": "HEAD / HTTP/1.0",
                "http_response_code": ["HTTP_2XX", "HTTP_3XX"]
            },
            "receive_timeout": 5,
            "failed_checks": 3,
            "send_interval": 10,
            "successful_checks": 3,
            "type": "HEALTH_MONITOR_HTTPS",
            "name": "MyWebsite-HTTPS"
        })

        with self.assertRaises(AnsibleExitJson) as result:
            avi_healthmonitor.main()
        self.assertFalse(result.exception.args[0]['changed'])

    @my_vcr.use_cassette()
    def test5_delete_http_hm(self):
        set_module_args({
            "state": "absent",
            "controller": "10.10.26.133",
            "username": "admin",
            "password": "avi123$%",
            "api_version": "17.2.1",
            "https_monitor": {
                "http_request": "HEAD / HTTP/1.0",
                "http_response_code": ["HTTP_2XX", "HTTP_3XX"]
            },
            "receive_timeout": 5,
            "failed_checks": 3,
            "send_interval": 10,
            "successful_checks": 3,
            "type": "HEALTH_MONITOR_HTTPS",
            "name": "MyWebsite-HTTPS"
        })

        with self.assertRaises(AnsibleExitJson) as result:
            avi_healthmonitor.main()
        self.assertTrue(result.exception.args[0]['changed'])

    @my_vcr.use_cassette()
    def test6_delete_http_hm_re_run(self):
        set_module_args({
            "state": "absent",
            "controller": "10.10.26.133",
            "username": "admin",
            "password": "avi123$%",
            "api_version": "17.2.1",
            "https_monitor": {
                "http_request": "HEAD / HTTP/1.0",
                "http_response_code": ["HTTP_2XX", "HTTP_3XX"]
            },
            "receive_timeout": 5,
            "failed_checks": 3,
            "send_interval": 10,
            "successful_checks": 3,
            "type": "HEALTH_MONITOR_HTTPS",
            "name": "MyWebsite-HTTPS"
        })
        with self.assertRaises(AnsibleExitJson) as result:
            avi_healthmonitor.main()
        self.assertFalse(result.exception.args[0]['changed'])

    @my_vcr.use_cassette()
    def test7_hm_fail_for_missing_name(self):
        set_module_args({
            "controller": "10.10.26.133",
            "username": "admin",
            "password": "avi123$%",
            "api_version": "17.2.1",
            "https_monitor":
                {
                    "http_request": "HEAD / HTTP/1.0",
                    "http_response_code": ["HTTP_2XX", "HTTP_3XX"]
                },
            "receive_timeout": 4,
            "failed_checks": 3,
            "send_interval": 10,
            "successful_checks": 3,
            "type": "HEALTH_MONITOR_HTTPS"
        })
        with self.assertRaises(AnsibleFailJson) as result:
            avi_healthmonitor.main()
