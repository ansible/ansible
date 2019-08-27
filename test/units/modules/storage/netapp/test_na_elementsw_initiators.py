# (c) 2019, NetApp, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
''' unit test for Ansible module: na_elementsw_initiators.py '''

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

from ansible.modules.storage.netapp.na_elementsw_initiators \
    import ElementSWInitiators as my_module  # module under test


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


class MockSFConnection(object):
    ''' mock connection to ElementSW host '''

    class Bunch(object):  # pylint: disable=too-few-public-methods
        ''' create object with arbitrary attributes '''
        def __init__(self, **kw):
            ''' called with (k1=v1, k2=v2), creates obj.k1, obj.k2 with values v1, v2 '''
            setattr(self, '__dict__', kw)

    class Initiator(object):
        def __init__(self, entries):
            self.__dict__.update(entries)

    def list_initiators(self):
        ''' build initiator Obj '''
        all_initiators = {
            "initiators": [{
                "initiator_name": "a",
                "initiator_id": 13,
                "alias": "a2",
                "attributes": {"key": "value"}
            }]
        }
        return json.loads(json.dumps(all_initiators), object_hook=self.Initiator)

    def create_initiators(self, *args, **kwargs):  # pylint: disable=unused-argument
        ''' mock method '''
        pass

    def delete_initiators(self, *args, **kwargs):  # pylint: disable=unused-argument
        ''' mock method '''
        pass

    def modify_initiators(self, *args, **kwargs):  # pylint: disable=unused-argument
        ''' mock method '''
        pass


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
    def test_create_initiators(self, mock_create_sf_connection):
        ''' test if create initiator is called '''
        module_args = {}
        module_args.update(self.set_default_args())
        initiator_dict = {
            "state": "present",
            "initiators": [{
                "name": "newinitiator1",
                "alias": "newinitiator1alias",
                "attributes": {"key1": "value1"}
            }]
        }
        module_args.update(initiator_dict)
        set_module_args(module_args)
        mock_create_sf_connection.return_value = MockSFConnection()
        my_obj = my_module()
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        print('Info: test_create_initiators: %s' % repr(exc.value))
        assert exc.value.args[0]['changed']

    @patch('ansible.module_utils.netapp.create_sf_connection')
    def test_delete_initiators(self, mock_create_sf_connection):
        ''' test if delete initiator is called '''
        module_args = {}
        module_args.update(self.set_default_args())
        initiator_dict = {
            "state": "absent",
            "initiators": [{
                "name": "a"
            }]
        }
        module_args.update(initiator_dict)
        set_module_args(module_args)
        mock_create_sf_connection.return_value = MockSFConnection()
        my_obj = my_module()
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        print('Info: test_delete_initiators: %s' % repr(exc.value))
        assert exc.value.args[0]['changed']

    @patch('ansible.module_utils.netapp.create_sf_connection')
    def test_modify_initiators(self, mock_create_sf_connection):
        ''' test if modify initiator is called '''
        module_args = {}
        module_args.update(self.set_default_args())
        initiator_dict = {
            "state": "present",
            "initiators": [{
                "initiator_name": "a",
                "alias": "a3",
                "attributes": {"key": "value"}
            }]
        }
        module_args.update(initiator_dict)
        set_module_args(module_args)
        mock_create_sf_connection.return_value = MockSFConnection()
        my_obj = my_module()
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        print('Info: test_modify_initiators: %s' % repr(exc.value))
        assert exc.value.args[0]['changed']
