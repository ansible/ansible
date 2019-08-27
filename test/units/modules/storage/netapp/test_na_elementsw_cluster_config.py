# (c) 2019, NetApp, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

''' unit test for Ansible module: na_elementsw_cluster_config.py '''

from __future__ import print_function
import json
import pytest

from units.compat import unittest
from units.compat.mock import patch
from ansible.module_utils import basic
from ansible.module_utils._text import to_bytes
import ansible.module_utils.netapp as netapp_utils

if not netapp_utils.has_sf_sdk():
    pytestmark = pytest.mark.skip('skipping as missing required SolidFire Python SDK')

from ansible.modules.storage.netapp.na_elementsw_cluster_config \
    import ElementSWClusterConfig as my_module  # module under test


def set_module_args(args):
    """prepare arguments so that they will be picked up during module creation"""
    args = json.dumps({'ANSIBLE_MODULE_ARGS': args})
    basic._ANSIBLE_ARGS = to_bytes(args)  # pylint: disable=protected-access


class AnsibleExitJson(Exception):
    """Exception class to be raised by module.exit_json and caught by the test case"""
    pass


class AnsibleFailJson(Exception):
    """Exception class to be raised by module.fail_json and caught by the test case"""
    pass


def exit_json(*args, **kwargs):  # pylint: disable=unused-argument
    """function to patch over exit_json; package return data into an exception"""
    if 'changed' not in kwargs:
        kwargs['changed'] = False
    raise AnsibleExitJson(kwargs)


def fail_json(*args, **kwargs):  # pylint: disable=unused-argument
    """function to patch over fail_json; package return data into an exception"""
    kwargs['failed'] = True
    raise AnsibleFailJson(kwargs)


GET_ERROR = 'some_error_in_get_ntp_info'


class MockSFConnection(object):
    ''' mock connection to ElementSW host '''

    class Bunch(object):  # pylint: disable=too-few-public-methods
        ''' create object with arbitrary attributes '''

        def __init__(self, **kw):
            ''' called with (k1=v1, k2=v2), creates obj.k1, obj.k2 with values v1, v2 '''
            setattr(self, '__dict__', kw)

    def __init__(self, force_error=False, where=None):
        ''' save arguments '''
        self.force_error = force_error
        self.where = where


class TestMyModule(unittest.TestCase):
    ''' a group of related Unit Tests '''

    def setUp(self):
        self.mock_module_helper = patch.multiple(basic.AnsibleModule,
                                                 exit_json=exit_json,
                                                 fail_json=fail_json)
        self.mock_module_helper.start()
        self.addCleanup(self.mock_module_helper.stop)

    def set_default_args(self):
        return dict({
            'hostname': '10.253.168.129',
            'username': 'namburu',
            'password': 'SFlab1234',
        })

    @patch('ansible.module_utils.netapp.create_sf_connection')
    def test_module_fail_when_required_args_missing(self, mock_create_sf_connection):
        ''' required arguments are reported as errors '''
        with pytest.raises(AnsibleFailJson) as exc:
            set_module_args({})
            my_module()
        print('Info: %s' % exc.value.args[0]['msg'])

    @patch('ansible.module_utils.netapp.create_sf_connection')
    def test_ensure_setup_ntp_info_called(self, mock_create_sf_connection):
        ''' test if setup_ntp_info is called '''
        module_args = {}
        module_args.update(self.set_default_args())
        ntp_dict = {'set_ntp_info': {'broadcastclient': None,
                    'ntp_servers': ['1.1.1.1']}}
        module_args.update(ntp_dict)
        set_module_args(module_args)
        my_obj = my_module()
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        print('Info: test_setup_ntp_info: %s' % repr(exc.value))
        assert exc.value.args[0]['changed']

    @patch('ansible.module_utils.netapp.create_sf_connection')
    def test_ensure_set_encryption_at_rest_called(self, mock_create_sf_connection):
        ''' test if set_encryption_at_rest is called '''
        module_args = {}
        module_args.update(self.set_default_args())
        module_args.update({'encryption_at_rest': 'present'})
        set_module_args(module_args)
        my_obj = my_module()
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        print('Info: test_set_encryption_at_rest enable: %s' % repr(exc.value))
        assert not exc.value.args[0]['changed']
        module_args.update({'encryption_at_rest': 'absent'})
        set_module_args(module_args)
        my_obj = my_module()
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        print('Info: test_set_encryption_at_rest disable: %s' % repr(exc.value))
        assert not exc.value.args[0]['changed']

    @patch('ansible.module_utils.netapp.create_sf_connection')
    def test_ensure_enable_feature_called(self, mock_create_sf_connection):
        ''' test if enable_feature for vvols is called '''
        module_args = {}
        module_args.update(self.set_default_args())
        module_args.update({'enable_virtual_volumes': True})
        set_module_args(module_args)
        my_obj = my_module()
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        print('Info: test_enable_feature: %s' % repr(exc.value))
        assert not exc.value.args[0]['changed']

    @patch('ansible.module_utils.netapp.create_sf_connection')
    def test_ensure_set_cluster_full_threshold_called(self, mock_create_sf_connection):
        ''' test if set_cluster_full threshold is called '''
        module_args = {}
        module_args.update(self.set_default_args())
        cluster_mod_dict = \
            {'modify_cluster_full_threshold': {'stage2_aware_threshold': 2,
                                               'stage3_block_threshold_percent': 2,
                                               'max_metadata_over_provision_factor': 2}}
        module_args.update(cluster_mod_dict)
        set_module_args(module_args)
        my_obj = my_module()
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        print('Info: test_set_cluster_full_threshold: %s' % repr(exc.value))
        assert exc.value.args[0]['changed']
