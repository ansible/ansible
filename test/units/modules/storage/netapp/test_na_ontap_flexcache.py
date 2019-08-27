# (c) 2018, NetApp, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

''' unit test for ONTAP FlexCache Ansible module '''

from __future__ import print_function
import json
import pytest

from units.compat import unittest
from units.compat.mock import patch
from ansible.module_utils import basic
from ansible.module_utils._text import to_bytes
import ansible.module_utils.netapp as netapp_utils

from ansible.modules.storage.netapp.na_ontap_flexcache \
    import NetAppONTAPFlexCache as my_module  # module under test

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

    def __init__(self, kind=None, parm1=None, api_error=None, job_error=None):
        ''' save arguments '''
        self.type = kind
        self.parm1 = parm1
        self.api_error = api_error
        self.job_error = job_error
        self.xml_in = None
        self.xml_out = None

    def invoke_successfully(self, xml, enable_tunneling):  # pylint: disable=unused-argument
        ''' mock invoke_successfully returning xml data '''
        self.xml_in = xml
        tag = xml.get_name()
        if tag == 'flexcache-get-iter' and self.type == 'vserver':
            xml = self.build_flexcache_info(self.parm1)
        elif tag == 'flexcache-create-async':
            xml = self.build_flexcache_create_destroy_rsp()
        elif tag == 'flexcache-destroy-async':
            if self.api_error:
                code, message = self.api_error.split(':', 2)
                raise netapp_utils.zapi.NaApiError(code, message)
            xml = self.build_flexcache_create_destroy_rsp()
        elif tag == 'job-get':
            xml = self.build_job_info(self.job_error)
        self.xml_out = xml
        return xml

    @staticmethod
    def build_flexcache_info(vserver):
        ''' build xml data for vserser-info '''
        xml = netapp_utils.zapi.NaElement('xml')
        attributes = netapp_utils.zapi.NaElement('attributes-list')
        count = 2 if vserver == 'repeats' else 1
        for dummy in range(count):
            attributes.add_node_with_children('flexcache-info', **{
                'vserver': vserver,
                'origin-vserver': 'ovserver',
                'origin-volume': 'ovolume',
                'origin-cluster': 'ocluster',
                'volume': 'volume',
            })
        xml.add_child_elem(attributes)
        xml.add_new_child('num-records', str(count))
        return xml

    @staticmethod
    def build_flexcache_create_destroy_rsp():
        ''' build xml data for a create or destroy response '''
        xml = netapp_utils.zapi.NaElement('xml')
        xml.add_new_child('result-status', 'in_progress')
        xml.add_new_child('result-jobid', '1234')
        return xml

    @staticmethod
    def build_job_info(error):
        ''' build xml data for a job '''
        xml = netapp_utils.zapi.NaElement('xml')
        attributes = netapp_utils.zapi.NaElement('attributes')
        if error is None:
            state = 'success'
        elif error == 'time_out':
            state = 'running'
        else:
            state = 'failure'
        attributes.add_node_with_children('job-info', **{
            'job-state': state,
            'job-progress': 'dummy',
            'job-completion': error,
        })
        xml.add_child_elem(attributes)
        xml.add_new_child('result-status', 'in_progress')
        xml.add_new_child('result-jobid', '1234')
        return xml


class TestMyModule(unittest.TestCase):
    ''' a group of related Unit Tests '''

    def setUp(self):
        self.mock_module_helper = patch.multiple(basic.AnsibleModule,
                                                 exit_json=exit_json,
                                                 fail_json=fail_json)
        self.mock_module_helper.start()
        self.addCleanup(self.mock_module_helper.stop)
        # make sure to change this to False before submitting
        self.onbox = False
        self.dummy_args = dict()
        for arg in ('hostname', 'username', 'password'):
            self.dummy_args[arg] = arg
        if self.onbox:
            self.args = {
                'hostname': '10.193.78.219',
                'username': 'admin',
                'password': 'netapp1!',
            }
        else:
            self.args = self.dummy_args
        self.server = MockONTAPConnection()

    def create_flexcache(self, vserver, volume, junction_path):
        ''' create flexcache '''
        if not self.onbox:
            return
        args = {
            'state': 'present',
            'volume': volume,
            'size': '90',       # 80MB minimum
            'size_unit': 'mb',  # 80MB minimum
            'vserver': vserver,
            'aggr_list': 'aggr1',
            'origin_volume': 'fc_vol_origin',
            'origin_vserver': 'ansibleSVM',
            'junction_path': junction_path,
        }
        args.update(self.args)
        set_module_args(args)
        my_obj = my_module()
        try:
            my_obj.apply()
        except AnsibleExitJson as exc:
            print('Create util: ' + repr(exc))
        except AnsibleFailJson as exc:
            print('Create util: ' + repr(exc))

    def delete_flexcache(self, vserver, volume):
        ''' delete flexcache '''
        if not self.onbox:
            return
        args = {'volume': volume, 'vserver': vserver, 'state': 'absent', 'force_offline': 'true'}
        args.update(self.args)
        set_module_args(args)
        my_obj = my_module()
        try:
            my_obj.apply()
        except AnsibleExitJson as exc:
            print('Delete util: ' + repr(exc))
        except AnsibleFailJson as exc:
            print('Delete util: ' + repr(exc))

    def test_module_fail_when_required_args_missing(self):
        ''' required arguments are reported as errors '''
        with pytest.raises(AnsibleFailJson) as exc:
            set_module_args({})
            my_module()
        print('Info: %s' % exc.value.args[0]['msg'])

    def test_missing_parameters(self):
        ''' fail if origin volume and origin verser are missing '''
        args = {
            'vserver': 'vserver',
            'volume': 'volume'
        }
        args.update(self.dummy_args)
        set_module_args(args)
        my_obj = my_module()
        my_obj.server = self.server
        with pytest.raises(AnsibleFailJson) as exc:
            # It may not be a good idea to start with apply
            # More atomic methods can be easier to mock
            # Hint: start with get methods, as they are called first
            my_obj.apply()
        msg = 'Missing parameters: origin_volume, origin_vserver'
        assert exc.value.args[0]['msg'] == msg

    def test_missing_parameter(self):
        ''' fail if origin verser parameter is missing '''
        args = {
            'vserver': 'vserver',
            'origin_volume': 'origin_volume',
            'volume': 'volume'
        }
        args.update(self.dummy_args)
        set_module_args(args)
        my_obj = my_module()
        my_obj.server = self.server
        with pytest.raises(AnsibleFailJson) as exc:
            my_obj.apply()
        msg = 'Missing parameter: origin_vserver'
        assert exc.value.args[0]['msg'] == msg

    def test_get_flexcache(self):
        ''' get flexcache info '''
        args = {
            'vserver': 'ansibleSVM',
            'origin_volume': 'origin_volume',
            'volume': 'volume'
        }
        args.update(self.args)
        set_module_args(args)
        my_obj = my_module()
        if not self.onbox:
            my_obj.server = MockONTAPConnection('vserver')
        info = my_obj.flexcache_get()
        print('info: ' + repr(info))

    def test_get_flexcache_double(self):
        ''' get flexcache info returns 2 entries! '''
        args = {
            'vserver': 'ansibleSVM',
            'origin_volume': 'origin_volume',
            'volume': 'volume'
        }
        args.update(self.dummy_args)
        set_module_args(args)
        my_obj = my_module()
        my_obj.server = MockONTAPConnection('vserver', 'repeats')
        with pytest.raises(AnsibleFailJson) as exc:
            my_obj.flexcache_get()
        msg = 'Error fetching FlexCache info: Multiple records found for %s:' % args['volume']
        assert exc.value.args[0]['msg'] == msg

    def test_create_flexcache(self):
        ''' create flexcache '''
        args = {
            'volume': 'volume',
            'size': '90',       # 80MB minimum
            'size_unit': 'mb',  # 80MB minimum
            'vserver': 'ansibleSVM',
            'aggr_list': 'aggr1',
            'origin_volume': 'fc_vol_origin',
            'origin_vserver': 'ansibleSVM',
        }
        self.delete_flexcache(args['vserver'], args['volume'])
        args.update(self.args)
        set_module_args(args)
        my_obj = my_module()
        if not self.onbox:
            my_obj.server = MockONTAPConnection()
        with patch.object(my_module, 'flexcache_create', wraps=my_obj.flexcache_create) as mock_create:
            # with patch('__main__.my_module.flexcache_create', wraps=my_obj.flexcache_create) as mock_create:
            with pytest.raises(AnsibleExitJson) as exc:
                my_obj.apply()
            print('Create: ' + repr(exc.value))
            assert exc.value.args[0]['changed']
            mock_create.assert_called_with()

    def test_create_flexcache_idempotent(self):
        ''' create flexcache - already exists '''
        args = {
            'volume': 'volume',
            'vserver': 'ansibleSVM',
            'aggr_list': 'aggr1',
            'origin_volume': 'fc_vol_origin',
            'origin_vserver': 'ansibleSVM',
        }
        args.update(self.args)
        set_module_args(args)
        my_obj = my_module()
        if not self.onbox:
            my_obj.server = MockONTAPConnection('vserver')
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        print('Create: ' + repr(exc.value))
        assert exc.value.args[0]['changed'] is False

    def test_create_flexcache_autoprovision(self):
        ''' create flexcache with autoprovision'''
        args = {
            'volume': 'volume',
            'size': '90',       # 80MB minimum
            'size_unit': 'mb',  # 80MB minimum
            'vserver': 'ansibleSVM',
            'auto_provision_as': 'flexgroup',
            'origin_volume': 'fc_vol_origin',
            'origin_vserver': 'ansibleSVM',
        }
        self.delete_flexcache(args['vserver'], args['volume'])
        args.update(self.args)
        set_module_args(args)
        my_obj = my_module()
        if not self.onbox:
            my_obj.server = MockONTAPConnection()
        with patch.object(my_module, 'flexcache_create', wraps=my_obj.flexcache_create) as mock_create:
            with pytest.raises(AnsibleExitJson) as exc:
                my_obj.apply()
            print('Create: ' + repr(exc.value))
            assert exc.value.args[0]['changed']
            mock_create.assert_called_with()

    def test_create_flexcache_autoprovision_idempotent(self):
        ''' create flexcache with autoprovision - already exists '''
        args = {
            'volume': 'volume',
            'vserver': 'ansibleSVM',
            'origin_volume': 'fc_vol_origin',
            'origin_vserver': 'ansibleSVM',
            'auto_provision_as': 'flexgroup',
        }
        args.update(self.args)
        set_module_args(args)
        my_obj = my_module()
        if not self.onbox:
            my_obj.server = MockONTAPConnection('vserver')
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        print('Create: ' + repr(exc.value))
        assert exc.value.args[0]['changed'] is False

    def test_create_flexcache_multiplier(self):
        ''' create flexcache with aggregate multiplier'''
        args = {
            'volume': 'volume',
            'size': '90',       # 80MB minimum
            'size_unit': 'mb',  # 80MB minimum
            'vserver': 'ansibleSVM',
            'aggr_list': 'aggr1',
            'origin_volume': 'fc_vol_origin',
            'origin_vserver': 'ansibleSVM',
            'aggr_list_multiplier': '2',
        }
        self.delete_flexcache(args['vserver'], args['volume'])
        args.update(self.args)
        set_module_args(args)
        my_obj = my_module()
        if not self.onbox:
            my_obj.server = MockONTAPConnection()
        with patch.object(my_module, 'flexcache_create', wraps=my_obj.flexcache_create) as mock_create:
            with pytest.raises(AnsibleExitJson) as exc:
                my_obj.apply()
            print('Create: ' + repr(exc.value))
            assert exc.value.args[0]['changed']
            mock_create.assert_called_with()

    def test_create_flexcache_multiplier_idempotent(self):
        ''' create flexcache with aggregate multiplier - already exists '''
        args = {
            'volume': 'volume',
            'vserver': 'ansibleSVM',
            'aggr_list': 'aggr1',
            'origin_volume': 'fc_vol_origin',
            'origin_vserver': 'ansibleSVM',
            'aggr_list_multiplier': '2',
        }
        args.update(self.args)
        set_module_args(args)
        my_obj = my_module()
        if not self.onbox:
            my_obj.server = MockONTAPConnection('vserver')
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        print('Create: ' + repr(exc.value))
        assert exc.value.args[0]['changed'] is False

    def test_delete_flexcache_exists_no_force(self):
        ''' delete flexcache '''
        args = {'volume': 'volume', 'vserver': 'ansibleSVM', 'state': 'absent'}
        args.update(self.args)
        set_module_args(args)
        my_obj = my_module()
        error = '13001:Volume volume in Vserver ansibleSVM must be offline to be deleted. ' \
                'Use "volume offline -vserver ansibleSVM -volume volume" command to offline ' \
                'the volume'
        if not self.onbox:
            my_obj.server = MockONTAPConnection('vserver', 'flex', api_error=error)
        with patch.object(my_module, 'flexcache_delete', wraps=my_obj.flexcache_delete) as mock_delete:
            with pytest.raises(AnsibleFailJson) as exc:
                my_obj.apply()
            print('Delete: ' + repr(exc.value))
            msg = 'Error deleting FlexCache : NetApp API failed. Reason - %s' % error
            assert exc.value.args[0]['msg'] == msg
            mock_delete.assert_called_with()

    def test_delete_flexcache_exists_with_force(self):
        ''' delete flexcache '''
        args = {'volume': 'volume', 'vserver': 'ansibleSVM', 'state': 'absent', 'force_offline': 'true'}
        args.update(self.args)
        set_module_args(args)
        my_obj = my_module()
        if not self.onbox:
            my_obj.server = MockONTAPConnection('vserver', 'flex')
        with patch.object(my_module, 'flexcache_delete', wraps=my_obj.flexcache_delete) as mock_delete:
            with pytest.raises(AnsibleExitJson) as exc:
                my_obj.apply()
            print('Delete: ' + repr(exc.value))
            assert exc.value.args[0]['changed']
            mock_delete.assert_called_with()

    def test_delete_flexcache_exists_junctionpath_no_force(self):
        ''' delete flexcache '''
        args = {'volume': 'volume', 'vserver': 'ansibleSVM', 'junction_path': 'jpath', 'state': 'absent', 'force_offline': 'true'}
        self.create_flexcache(args['vserver'], args['volume'], args['junction_path'])
        args.update(self.args)
        set_module_args(args)
        my_obj = my_module()
        error = '160:Volume volume on Vserver ansibleSVM must be unmounted before being taken offline or restricted.'
        if not self.onbox:
            my_obj.server = MockONTAPConnection('vserver', 'flex', api_error=error)
        with patch.object(my_module, 'flexcache_delete', wraps=my_obj.flexcache_delete) as mock_delete:
            with pytest.raises(AnsibleFailJson) as exc:
                my_obj.apply()
            print('Delete: ' + repr(exc.value))
            msg = 'Error deleting FlexCache : NetApp API failed. Reason - %s' % error
            assert exc.value.args[0]['msg'] == msg
            mock_delete.assert_called_with()

    def test_delete_flexcache_exists_junctionpath_with_force(self):
        ''' delete flexcache '''
        args = {'volume': 'volume', 'vserver': 'ansibleSVM', 'junction_path': 'jpath', 'state': 'absent', 'force_offline': 'true', 'force_unmount': 'true'}
        self.create_flexcache(args['vserver'], args['volume'], args['junction_path'])
        args.update(self.args)
        set_module_args(args)
        my_obj = my_module()
        if not self.onbox:
            my_obj.server = MockONTAPConnection('vserver', 'flex')
        with patch.object(my_module, 'flexcache_delete', wraps=my_obj.flexcache_delete) as mock_delete:
            with pytest.raises(AnsibleExitJson) as exc:
                my_obj.apply()
            print('Delete: ' + repr(exc.value))
            assert exc.value.args[0]['changed']
            mock_delete.assert_called_with()

    def test_delete_flexcache_not_exist(self):
        ''' delete flexcache '''
        args = {'volume': 'volume', 'vserver': 'ansibleSVM', 'state': 'absent'}
        args.update(self.args)
        set_module_args(args)
        my_obj = my_module()
        if not self.onbox:
            my_obj.server = MockONTAPConnection()
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        print('Delete: ' + repr(exc.value))
        assert exc.value.args[0]['changed'] is False

    def test_create_flexcache_size_error(self):
        ''' create flexcache '''
        args = {
            'volume': 'volume_err',
            'size': '50',       # 80MB minimum
            'size_unit': 'mb',  # 80MB minimum
            'vserver': 'ansibleSVM',
            'aggr_list': 'aggr1',
            'origin_volume': 'fc_vol_origin',
            'origin_vserver': 'ansibleSVM',
        }
        args.update(self.args)
        set_module_args(args)
        my_obj = my_module()
        error = 'Size "50MB" ("52428800B") is too small.  Minimum size is "80MB" ("83886080B"). '
        if not self.onbox:
            my_obj.server = MockONTAPConnection(job_error=error)
        with patch.object(my_module, 'flexcache_create', wraps=my_obj.flexcache_create) as mock_create:
            with pytest.raises(AnsibleFailJson) as exc:
                my_obj.apply()
            print('Create: ' + repr(exc.value))
            msg = 'Error when creating flexcache: %s' % error
            assert exc.value.args[0]['msg'] == msg
            mock_create.assert_called_with()

    @patch('time.sleep')
    def test_create_flexcache_time_out(self, mock_sleep):
        ''' create flexcache '''
        args = {
            'volume': 'volume_err',
            'size': '50',       # 80MB minimum
            'size_unit': 'mb',  # 80MB minimum
            'vserver': 'ansibleSVM',
            'aggr_list': 'aggr1',
            'origin_volume': 'fc_vol_origin',
            'origin_vserver': 'ansibleSVM',
            'time_out': '2'
        }
        args.update(self.args)
        set_module_args(args)
        my_obj = my_module()
        if not self.onbox:
            my_obj.server = MockONTAPConnection(job_error='time_out')
        with patch.object(my_module, 'flexcache_create', wraps=my_obj.flexcache_create) as mock_create:
            with pytest.raises(AnsibleFailJson) as exc:
                my_obj.apply()
            print('Create: ' + repr(exc.value))
            msg = 'Error when creating flexcache: job completion exceeded expected timer of: %s seconds' \
                % args['time_out']
            assert exc.value.args[0]['msg'] == msg
            mock_create.assert_called_with()
