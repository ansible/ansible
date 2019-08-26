''' unit tests ONTAP Ansible module: na_ontap_snapmirror '''

from __future__ import print_function
import json
import pytest

from units.compat import unittest
from units.compat.mock import patch, Mock
from ansible.module_utils import basic
from ansible.module_utils._text import to_bytes
import ansible.module_utils.netapp as netapp_utils

from ansible.modules.storage.netapp.na_ontap_snapmirror \
    import NetAppONTAPSnapmirror as my_module

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

    def __init__(self, kind=None, parm=None, status=None):
        ''' save arguments '''
        self.type = kind
        self.xml_in = None
        self.xml_out = None
        self.parm = parm
        self.status = status

    def invoke_successfully(self, xml, enable_tunneling):  # pylint: disable=unused-argument
        ''' mock invoke_successfully returning xml data '''
        self.xml_in = xml
        if self.type == 'snapmirror':
            xml = self.build_snapmirror_info(self.parm, self.status)
        elif self.type == 'snapmirror_fail':
            raise netapp_utils.zapi.NaApiError(code='TEST', message="This exception is from the unit test")
        self.xml_out = xml
        return xml

    @staticmethod
    def build_snapmirror_info(mirror_state, status):
        ''' build xml data for snapmirror-entry '''
        xml = netapp_utils.zapi.NaElement('xml')
        data = {'num-records': 1,
                'attributes-list': {'snapmirror-info': {'mirror-state': mirror_state, 'schedule': None,
                                                        'source-location': 'ansible:ansible',
                                                        'relationship-status': status, 'policy': 'ansible',
                                                        'relationship-type': 'data_protection',
                                                        'max-transfer-rate': 1000,
                                                        'identity-preserve': 'true'},
                                    'snapmirror-destination-info': {'destination-location': 'ansible'}}}
        xml.translate_struct(data)
        return xml


class TestMyModule(unittest.TestCase):
    ''' a group of related Unit Tests '''

    def setUp(self):
        self.mock_module_helper = patch.multiple(basic.AnsibleModule,
                                                 exit_json=exit_json,
                                                 fail_json=fail_json)
        self.mock_module_helper.start()
        self.addCleanup(self.mock_module_helper.stop)
        self.server = MockONTAPConnection()
        self.source_server = MockONTAPConnection()
        self.onbox = False

    def set_default_args(self):
        if self.onbox:
            hostname = '10.10.10.10'
            username = 'admin'
            password = 'password'
            source_path = 'ansible:ansible'
            destination_path = 'ansible:ansible'
            policy = 'ansible'
            source_vserver = 'ansible'
            destination_vserver = 'ansible'
            relationship_type = 'data_protection'
            schedule = None
            source_username = 'admin'
            source_password = 'password'
        else:
            hostname = '10.10.10.10'
            username = 'admin'
            password = 'password'
            source_path = 'ansible:ansible'
            destination_path = 'ansible:ansible'
            policy = 'ansible'
            source_vserver = 'ansible'
            destination_vserver = 'ansible'
            relationship_type = 'data_protection'
            schedule = None
            source_username = 'admin'
            source_password = 'password'
        return dict({
            'hostname': hostname,
            'username': username,
            'password': password,
            'source_path': source_path,
            'destination_path': destination_path,
            'policy': policy,
            'source_vserver': source_vserver,
            'destination_vserver': destination_vserver,
            'relationship_type': relationship_type,
            'schedule': schedule,
            'source_username': source_username,
            'source_password': source_password
        })

    def test_module_fail_when_required_args_missing(self):
        ''' required arguments are reported as errors '''
        with pytest.raises(AnsibleFailJson) as exc:
            set_module_args({})
            my_module()
        print('Info: %s' % exc.value.args[0]['msg'])

    def test_ensure_get_called(self):
        ''' test snapmirror_get for non-existent snapmirror'''
        set_module_args(self.set_default_args())
        my_obj = my_module()
        my_obj.server = self.server
        assert my_obj.snapmirror_get is not None

    def test_ensure_get_called_existing(self):
        ''' test snapmirror_get for existing snapmirror'''
        set_module_args(self.set_default_args())
        my_obj = my_module()
        my_obj.server = MockONTAPConnection(kind='snapmirror', status='idle')
        assert my_obj.snapmirror_get()

    @patch('ansible.modules.storage.netapp.na_ontap_snapmirror.NetAppONTAPSnapmirror.snapmirror_create')
    def test_successful_create(self, snapmirror_create):
        ''' creating snapmirror and testing idempotency '''
        data = self.set_default_args()
        data['schedule'] = 'abc'
        data['identity_preserve'] = True
        set_module_args(data)
        my_obj = my_module()
        my_obj.asup_log_for_cserver = Mock(return_value=None)
        if not self.onbox:
            my_obj.server = self.server
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        assert exc.value.args[0]['changed']
        snapmirror_create.assert_called_with()
        # to reset na_helper from remembering the previous 'changed' value
        set_module_args(self.set_default_args())
        my_obj = my_module()
        my_obj.asup_log_for_cserver = Mock(return_value=None)
        if not self.onbox:
            my_obj.server = MockONTAPConnection('snapmirror', 'snapmirrored', status='idle')
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        assert not exc.value.args[0]['changed']

    @patch('ansible.modules.storage.netapp.na_ontap_snapmirror.NetAppONTAPSnapmirror.snapmirror_create')
    @patch('ansible.modules.storage.netapp.na_ontap_snapmirror.NetAppONTAPSnapmirror.check_elementsw_parameters')
    def test_successful_element_ontap_create(self, check_param, snapmirror_create):
        ''' creating ElementSW to ONTAP snapmirror '''
        data = self.set_default_args()
        data['schedule'] = 'abc'
        data['connection_type'] = 'elementsw_ontap'
        data['source_hostname'] = '10.10.10.10'
        set_module_args(data)
        my_obj = my_module()
        my_obj.asup_log_for_cserver = Mock(return_value=None)
        if not self.onbox:
            my_obj.server = self.server
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        assert exc.value.args[0]['changed']
        snapmirror_create.assert_called_with()
        check_param.assert_called_with()

    @patch('ansible.modules.storage.netapp.na_ontap_snapmirror.NetAppONTAPSnapmirror.snapmirror_create')
    @patch('ansible.modules.storage.netapp.na_ontap_snapmirror.NetAppONTAPSnapmirror.check_elementsw_parameters')
    @patch('ansible.modules.storage.netapp.na_ontap_snapmirror.NetAppONTAPSnapmirror.snapmirror_get')
    def test_successful_ontap_element_create(self, snapmirror_get, check_param, snapmirror_create):
        ''' creating ONTAP to ElementSW snapmirror '''
        data = self.set_default_args()
        data['schedule'] = 'abc'
        data['connection_type'] = 'ontap_elementsw'
        data['source_hostname'] = '10.10.10.10'
        set_module_args(data)
        my_obj = my_module()
        my_obj.asup_log_for_cserver = Mock(return_value=None)
        snapmirror_get.side_effect = [
            Mock(),
            None
        ]
        if not self.onbox:
            my_obj.server = self.server
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        assert exc.value.args[0]['changed']
        snapmirror_create.assert_called_with()
        check_param.assert_called_with('destination')

    @patch('ansible.modules.storage.netapp.na_ontap_snapmirror.NetAppONTAPSnapmirror.delete_snapmirror')
    def test_successful_delete(self, delete_snapmirror):
        ''' deleting snapmirror and testing idempotency '''
        data = self.set_default_args()
        data['state'] = 'absent'
        data['source_hostname'] = '10.10.10.10'
        set_module_args(data)
        my_obj = my_module()
        my_obj.asup_log_for_cserver = Mock(return_value=None)
        my_obj.get_destination = Mock(return_value=True)
        if not self.onbox:
            my_obj.server = MockONTAPConnection('snapmirror', status='idle')
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        assert exc.value.args[0]['changed']
        delete_snapmirror.assert_called_with(False, 'data_protection')
        # to reset na_helper from remembering the previous 'changed' value
        my_obj = my_module()
        my_obj.asup_log_for_cserver = Mock(return_value=None)
        if not self.onbox:
            my_obj.server = self.server
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        assert not exc.value.args[0]['changed']

    def test_successful_delete_error_check(self):
        ''' check required parameter source cluster hostname deleting snapmirror'''
        data = self.set_default_args()
        data['state'] = 'absent'
        set_module_args(data)
        my_obj = my_module()
        my_obj.asup_log_for_cserver = Mock(return_value=None)
        if not self.onbox:
            my_obj.server = MockONTAPConnection('snapmirror', status='idle')
        with pytest.raises(AnsibleFailJson) as exc:
            my_obj.apply()
        assert 'Missing parameters for delete:' in exc.value.args[0]['msg']

    def test_successful_delete_check_get_destination(self):
        ''' check required parameter source cluster hostname deleting snapmirror'''
        data = self.set_default_args()
        data['state'] = 'absent'
        data['source_hostname'] = '10.10.10.10'
        set_module_args(data)
        my_obj = my_module()
        my_obj.asup_log_for_cserver = Mock(return_value=None)
        if not self.onbox:
            my_obj.server = MockONTAPConnection('snapmirror', status='idle')
            my_obj.source_server = MockONTAPConnection('snapmirror', status='idle')
        res = my_obj.get_destination()
        assert res is True

    def test_snapmirror_release(self):
        data = self.set_default_args()
        set_module_args(data)
        my_obj = my_module()
        my_obj.asup_log_for_cserver = Mock(return_value=None)
        if not self.onbox:
            my_obj.source_server = MockONTAPConnection('snapmirror', status='idle', parm='snapmirrored')
        my_obj.snapmirror_release()
        assert my_obj.source_server.xml_in['destination-location'] == data['destination_path']

    @patch('ansible.modules.storage.netapp.na_ontap_snapmirror.NetAppONTAPSnapmirror.snapmirror_abort')
    def test_successful_abort(self, snapmirror_abort):
        ''' deleting snapmirror and testing idempotency '''
        data = self.set_default_args()
        data['state'] = 'absent'
        data['source_hostname'] = '10.10.10.10'
        set_module_args(data)
        my_obj = my_module()
        my_obj.asup_log_for_cserver = Mock(return_value=None)
        if not self.onbox:
            my_obj.server = MockONTAPConnection('snapmirror', status='transferring')
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        assert exc.value.args[0]['changed']
        snapmirror_abort.assert_called_with()
        # to reset na_helper from remembering the previous 'changed' value
        my_obj = my_module()
        my_obj.asup_log_for_cserver = Mock(return_value=None)
        if not self.onbox:
            my_obj.server = self.server
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        assert not exc.value.args[0]['changed']

    @patch('ansible.modules.storage.netapp.na_ontap_snapmirror.NetAppONTAPSnapmirror.snapmirror_modify')
    def test_successful_modify(self, snapmirror_modify):
        ''' modifying snapmirror and testing idempotency '''
        data = self.set_default_args()
        data['policy'] = 'ansible2'
        data['schedule'] = 'abc2'
        data['max_transfer_rate'] = 2000
        set_module_args(data)
        my_obj = my_module()
        my_obj.asup_log_for_cserver = Mock(return_value=None)
        if not self.onbox:
            my_obj.server = MockONTAPConnection('snapmirror', status='idle')
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        assert exc.value.args[0]['changed']
        snapmirror_modify.assert_called_with({'policy': 'ansible2', 'schedule': 'abc2', 'max_transfer_rate': 2000})
        # to reset na_helper from remembering the previous 'changed' value
        data = self.set_default_args()
        set_module_args(data)
        my_obj = my_module()
        my_obj.asup_log_for_cserver = Mock(return_value=None)
        if not self.onbox:
            my_obj.server = MockONTAPConnection('snapmirror', status='idle', parm='snapmirrored')
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        assert not exc.value.args[0]['changed']

    @patch('ansible.modules.storage.netapp.na_ontap_snapmirror.NetAppONTAPSnapmirror.snapmirror_initialize')
    def test_successful_initialize(self, snapmirror_initialize):
        ''' initialize snapmirror and testing idempotency '''
        data = self.set_default_args()
        set_module_args(data)
        my_obj = my_module()
        my_obj.asup_log_for_cserver = Mock(return_value=None)
        if not self.onbox:
            my_obj.server = MockONTAPConnection('snapmirror', status='transferring')
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        assert exc.value.args[0]['changed']
        snapmirror_initialize.assert_called_with()
        # to reset na_helper from remembering the previous 'changed' value
        data = self.set_default_args()
        set_module_args(data)
        my_obj = my_module()
        my_obj.asup_log_for_cserver = Mock(return_value=None)
        if not self.onbox:
            my_obj.server = MockONTAPConnection('snapmirror', status='idle', parm='snapmirrored')
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        assert not exc.value.args[0]['changed']

    @patch('ansible.modules.storage.netapp.na_ontap_snapmirror.NetAppONTAPSnapmirror.snapmirror_update')
    def test_successful_update(self, snapmirror_update):
        ''' update snapmirror and testing idempotency '''
        data = self.set_default_args()
        set_module_args(data)
        my_obj = my_module()
        my_obj.asup_log_for_cserver = Mock(return_value=None)
        if not self.onbox:
            my_obj.server = MockONTAPConnection('snapmirror', status='idle', parm='snapmirrored')
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        assert not exc.value.args[0]['changed']
        snapmirror_update.assert_called_with()

    def test_elementsw_volume_exists(self):
        ''' elementsw_volume_exists '''
        data = self.set_default_args()
        set_module_args(data)
        my_obj = my_module()
        my_obj.asup_log_for_cserver = Mock(return_value=None)
        mock_helper = Mock()
        mock_helper.volume_id_exists.side_effect = [1000, None]
        if not self.onbox:
            my_obj.server = MockONTAPConnection('snapmirror', status='idle', parm='snapmirrored')
        res = my_obj.check_if_elementsw_volume_exists('10.10.10.10:/lun/1000', mock_helper)
        assert res is None
        with pytest.raises(AnsibleFailJson) as exc:
            my_obj.check_if_elementsw_volume_exists('10.10.10.10:/lun/1000', mock_helper)
        assert 'Error: Source volume does not exist in the ElementSW cluster' in exc.value.args[0]['msg']

    def test_elementsw_svip_exists(self):
        ''' svip_exists '''
        data = self.set_default_args()
        set_module_args(data)
        my_obj = my_module()
        my_obj.asup_log_for_cserver = Mock(return_value=None)
        mock_helper = Mock()
        mock_helper.get_cluster_info.return_value.cluster_info.svip = '10.10.10.10'
        if not self.onbox:
            my_obj.server = MockONTAPConnection('snapmirror', status='idle', parm='snapmirrored')
        res = my_obj.validate_elementsw_svip('10.10.10.10:/lun/1000', mock_helper)
        assert res is None

    def test_elementsw_svip_exists_negative(self):
        ''' svip_exists negative testing'''
        data = self.set_default_args()
        set_module_args(data)
        my_obj = my_module()
        my_obj.asup_log_for_cserver = Mock(return_value=None)
        mock_helper = Mock()
        mock_helper.get_cluster_info.return_value.cluster_info.svip = '10.10.10.10'
        if not self.onbox:
            my_obj.server = MockONTAPConnection('snapmirror', status='idle', parm='snapmirrored')
        with pytest.raises(AnsibleFailJson) as exc:
            my_obj.validate_elementsw_svip('10.10.10.11:/lun/1000', mock_helper)
        assert 'Error: Invalid SVIP' in exc.value.args[0]['msg']

    @patch('ansible.modules.storage.netapp.na_ontap_snapmirror.NetAppONTAPSnapmirror.set_element_connection')
    @patch('ansible.modules.storage.netapp.na_ontap_snapmirror.NetAppONTAPSnapmirror.validate_elementsw_svip')
    @patch('ansible.modules.storage.netapp.na_ontap_snapmirror.NetAppONTAPSnapmirror.check_if_elementsw_volume_exists')
    def test_check_elementsw_params_source(self, validate_volume, validate_svip, connection):
        ''' check elementsw parameters for source '''
        data = self.set_default_args()
        data['source_path'] = '10.10.10.10:/lun/1000'
        set_module_args(data)
        my_obj = my_module()
        my_obj.asup_log_for_cserver = Mock(return_value=None)
        mock_elem, mock_helper = Mock(), Mock()
        connection.return_value = mock_helper, mock_elem
        if not self.onbox:
            my_obj.server = MockONTAPConnection('snapmirror', status='idle', parm='snapmirrored')
        my_obj.check_elementsw_parameters('source')
        connection.called_once_with('source')
        validate_svip.called_once_with(data['source_path'], mock_elem)
        validate_volume.called_once_with(data['source_path'], mock_helper)

    def test_check_elementsw_params_negative(self):
        ''' check elementsw parameters for source negative testing '''
        data = self.set_default_args()
        del data['source_path']
        set_module_args(data)
        my_obj = my_module()
        my_obj.asup_log_for_cserver = Mock(return_value=None)
        if not self.onbox:
            my_obj.server = MockONTAPConnection('snapmirror', status='idle', parm='snapmirrored')
        with pytest.raises(AnsibleFailJson) as exc:
            my_obj.check_elementsw_parameters('source')
        assert 'Error: Missing required parameter source_path' in exc.value.args[0]['msg']

    def test_check_elementsw_params_invalid(self):
        ''' check elementsw parameters for source invalid testing '''
        data = self.set_default_args()
        set_module_args(data)
        my_obj = my_module()
        my_obj.asup_log_for_cserver = Mock(return_value=None)
        if not self.onbox:
            my_obj.server = MockONTAPConnection('snapmirror', status='idle', parm='snapmirrored')
        with pytest.raises(AnsibleFailJson) as exc:
            my_obj.check_elementsw_parameters('source')
        assert 'Error: invalid source_path' in exc.value.args[0]['msg']

    def test_elementsw_source_path_format(self):
        ''' test element_source_path_format_matches '''
        data = self.set_default_args()
        set_module_args(data)
        my_obj = my_module()
        my_obj.asup_log_for_cserver = Mock(return_value=None)
        if not self.onbox:
            my_obj.server = MockONTAPConnection('snapmirror', status='idle', parm='snapmirrored')
        match = my_obj.element_source_path_format_matches('1.1.1.1:dummy')
        assert match is None
        match = my_obj.element_source_path_format_matches('10.10.10.10:/lun/10')
        assert match is not None

    @patch('ansible.module_utils.netapp.create_sf_connection')
    def test_set_elem_connection(self, create_sf_connection):
        ''' test set_elem_connection '''
        data = self.set_default_args()
        data['source_hostname'] = 'test_source'
        set_module_args(data)
        my_obj = my_module()
        my_obj.asup_log_for_cserver = Mock(return_value=None)
        create_sf_connection.return_value = Mock()
        if not self.onbox:
            my_obj.server = MockONTAPConnection('snapmirror', status='idle', parm='snapmirrored')
        my_obj.set_element_connection('source')
        assert my_obj.module.params['hostname'] == data['source_hostname']
        assert my_obj.module.params['username'] == data['source_username']
        assert my_obj.module.params['password'] == data['source_password']

    def test_remote_volume_exists(self):
        ''' test check_if_remote_volume_exists '''
        data = self.set_default_args()
        data['source_volume'] = 'test_vol'
        data['destination_volume'] = 'test_vol2'
        set_module_args(data)
        my_obj = my_module()
        my_obj.set_source_cluster_connection = Mock(return_value=None)
        my_obj.asup_log_for_cserver = Mock(return_value=None)
        if not self.onbox:
            my_obj.server = MockONTAPConnection('snapmirror', status='idle', parm='snapmirrored')
            my_obj.source_server = MockONTAPConnection('snapmirror', status='idle', parm='snapmirrored')
        res = my_obj.check_if_remote_volume_exists()
        assert res

    @patch('ansible.module_utils.netapp.create_sf_connection')
    def test_set_elem_connection_destination(self, create_sf_connection):
        ''' test set_elem_connection for destination'''
        data = self.set_default_args()
        data['source_hostname'] = 'test_source'
        set_module_args(data)
        my_obj = my_module()
        my_obj.asup_log_for_cserver = Mock(return_value=None)
        create_sf_connection.return_value = Mock()
        if not self.onbox:
            my_obj.server = MockONTAPConnection('snapmirror', status='idle', parm='snapmirrored')
        my_obj.set_element_connection('destination')
        assert my_obj.module.params['hostname'] == data['hostname']
        assert my_obj.module.params['username'] == data['username']
        assert my_obj.module.params['password'] == data['password']

    def test_if_all_methods_catch_exception(self):
        data = self.set_default_args()
        data['source_hostname'] = '10.10.10.10'
        data['source_volume'] = 'ansible'
        data['destination_volume'] = 'ansible2'
        set_module_args(data)
        my_obj = my_module()
        if not self.onbox:
            my_obj.server = MockONTAPConnection('snapmirror_fail')
        with pytest.raises(AnsibleFailJson) as exc:
            my_obj.snapmirror_get()
        assert 'Error fetching snapmirror info: ' in exc.value.args[0]['msg']
        with pytest.raises(AnsibleFailJson) as exc:
            my_obj.snapmirror_abort()
        assert 'Error aborting SnapMirror relationship :' in exc.value.args[0]['msg']
        with pytest.raises(AnsibleFailJson) as exc:
            my_obj.snapmirror_break()
        assert 'Error breaking SnapMirror relationship :' in exc.value.args[0]['msg']
        with pytest.raises(AnsibleFailJson) as exc:
            my_obj.snapmirror_get = Mock(return_value={'mirror_state': 'transferring'})
            my_obj.snapmirror_initialize()
        assert 'Error initializing SnapMirror :' in exc.value.args[0]['msg']
        with pytest.raises(AnsibleFailJson) as exc:
            my_obj.snapmirror_update()
        assert 'Error updating SnapMirror :' in exc.value.args[0]['msg']
        with pytest.raises(AnsibleFailJson) as exc:
            my_obj.set_source_cluster_connection = Mock(return_value=True)
            my_obj.source_server = MockONTAPConnection('snapmirror_fail')
            my_obj.check_if_remote_volume_exists()
        assert 'Error fetching source volume details' in exc.value.args[0]['msg']
        with pytest.raises(AnsibleFailJson) as exc:
            my_obj.check_if_remote_volume_exists = Mock(return_value=True)
            my_obj.source_server = MockONTAPConnection()
            my_obj.snapmirror_create()
        assert 'Error creating SnapMirror ' in exc.value.args[0]['msg']
        with pytest.raises(AnsibleFailJson) as exc:
            my_obj.snapmirror_quiesce()
        assert 'Error Quiescing SnapMirror :' in exc.value.args[0]['msg']
        with pytest.raises(AnsibleFailJson) as exc:
            my_obj.snapmirror_quiesce = Mock(return_value=None)
            my_obj.get_destination = Mock(return_value=None)
            my_obj.snapmirror_break = Mock(return_value=None)
            my_obj.delete_snapmirror(False, 'data_protection')
        assert 'Error deleting SnapMirror :' in exc.value.args[0]['msg']
        with pytest.raises(AnsibleFailJson) as exc:
            my_obj.snapmirror_modify({'policy': 'ansible2', 'schedule': 'abc2'})
        assert 'Error modifying SnapMirror schedule or policy :' in exc.value.args[0]['msg']
