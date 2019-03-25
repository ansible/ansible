# (c) 2018-2019, NetApp, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

""" unit tests for Ansible module: na_ontap_aggregate """

from __future__ import print_function
import json
import pytest

from units.compat import unittest
from units.compat.mock import patch, Mock
from ansible.module_utils import basic
from ansible.module_utils._text import to_bytes
import ansible.module_utils.netapp as netapp_utils

from ansible.modules.storage.netapp.na_ontap_aggregate \
    import NetAppOntapAggregate as my_module  # module under test

if not netapp_utils.has_netapp_lib():
    pytestmark = pytest.mark.skip('skipping as missing required netapp_lib')


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


class MockONTAPConnection(object):
    ''' mock server connection to ONTAP host '''

    def __init__(self, kind=None, parm1=None, parm2=None):
        ''' save arguments '''
        self.type = kind
        self.parm1 = parm1
        self.parm2 = parm2
        self.xml_in = None
        self.xml_out = None

    def invoke_successfully(self, xml, enable_tunneling):  # pylint: disable=unused-argument
        ''' mock invoke_successfully returning xml data '''
        self.xml_in = xml
        if self.type == 'aggregate':
            xml = self.build_aggregate_info(self.parm1, self.parm2)
        elif self.type == 'aggregate_fail':
            raise netapp_utils.zapi.NaApiError(code='TEST', message="This exception is from the unit test")
        self.xml_out = xml
        return xml

    @staticmethod
    def build_aggregate_info(vserver, aggregate):
        ''' build xml data for aggregatte and vserser-info '''
        xml = netapp_utils.zapi.NaElement('xml')
        data = {'num-records': 2,
                'attributes-list':
                    {'aggr-attributes':
                        {'aggregate-name': aggregate,
                         'aggr-raid-attributes':
                             {'state': 'offline'
                              }
                         },
                     },
                'vserver-info':
                    {'vserver-name': vserver
                     }
                }
        xml.translate_struct(data)
        print(xml.to_string())
        return xml


class TestMyModule(unittest.TestCase):
    ''' a group of related Unit Tests '''

    def setUp(self):
        self.mock_module_helper = patch.multiple(basic.AnsibleModule,
                                                 exit_json=exit_json,
                                                 fail_json=fail_json)
        self.mock_module_helper.start()
        self.addCleanup(self.mock_module_helper.stop)
        self.server = MockONTAPConnection('aggregate', '12', 'name')
        # whether to use a mock or a simulator
        self.onbox = False

    def set_default_args(self):
        if self.onbox:
            hostname = '10.193.74.78'
            username = 'admin'
            password = 'netapp1!'
            name = 'name'
        else:
            hostname = 'hostname'
            username = 'username'
            password = 'password'
            name = 'name'
        return dict({
            'hostname': hostname,
            'username': username,
            'password': password,
            'name': name
        })

    def call_command(self, module_args):
        ''' utility function to call apply '''
        module_args.update(self.set_default_args())
        set_module_args(module_args)
        my_obj = my_module()
        my_obj.asup_log_for_cserver = Mock(return_value=None)
        if not self.onbox:
            # mock the connection
            my_obj.server = MockONTAPConnection('aggregate', '12', 'test_name')
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        return exc.value.args[0]['changed']

    def test_module_fail_when_required_args_missing(self):
        ''' required arguments are reported as errors '''
        with pytest.raises(AnsibleFailJson) as exc:
            set_module_args({})
            my_module()
        print('Info: %s' % exc.value.args[0]['msg'])

    def test_is_mirrored(self):
        module_args = {
            'disk_count': '2',
            'is_mirrored': 'true',
        }
        changed = self.call_command(module_args)
        assert not changed

    def test_disks_list(self):
        module_args = {
            'disk_count': '2',
            'disks': ['1', '2'],
        }
        changed = self.call_command(module_args)
        assert not changed

    def test_mirror_disks(self):
        module_args = {
            'disk_count': '2',
            'disks': ['1', '2'],
            'mirror_disks': ['3', '4']
        }
        changed = self.call_command(module_args)
        assert not changed

    def test_spare_pool(self):
        module_args = {
            'disk_count': '2',
            'spare_pool': 'Pool1'
        }
        changed = self.call_command(module_args)
        assert not changed

    def test_rename(self):
        module_args = {
            'from_name': 'test_name2'
        }
        changed = self.call_command(module_args)
        assert not changed

    def test_if_all_methods_catch_exception(self):
        module_args = {}
        module_args.update(self.set_default_args())
        module_args.update({'service_state': 'online'})
        module_args.update({'unmount_volumes': 'True'})
        module_args.update({'from_name': 'test_name2'})
        set_module_args(module_args)
        my_obj = my_module()
        if not self.onbox:
            my_obj.server = MockONTAPConnection('aggregate_fail')
        with pytest.raises(AnsibleFailJson) as exc:
            my_obj.aggr_get_iter(module_args.get('name'))
        assert '' in exc.value.args[0]['msg']
        with pytest.raises(AnsibleFailJson) as exc:
            my_obj.aggregate_online()
        assert 'Error changing the state of aggregate' in exc.value.args[0]['msg']
        with pytest.raises(AnsibleFailJson) as exc:
            my_obj.aggregate_offline()
        assert 'Error changing the state of aggregate' in exc.value.args[0]['msg']
        with pytest.raises(AnsibleFailJson) as exc:
            my_obj.create_aggr()
        assert 'Error provisioning aggregate' in exc.value.args[0]['msg']
        with pytest.raises(AnsibleFailJson) as exc:
            my_obj.delete_aggr()
        assert 'Error removing aggregate' in exc.value.args[0]['msg']
        with pytest.raises(AnsibleFailJson) as exc:
            my_obj.rename_aggregate()
            assert 'Error renaming aggregate' in exc.value.args[0]['msg']
        with pytest.raises(AnsibleFailJson) as exc:
            my_obj.asup_log_for_cserver = Mock(return_value=None)
            my_obj.apply()
            assert 'Error renaming: aggregate test_name2 does not exist' in exc.value.args[0]['msg']
