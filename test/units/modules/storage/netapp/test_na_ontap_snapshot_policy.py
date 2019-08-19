# (c) 2018, NetApp, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

''' unit tests ONTAP Ansible module: na_ontap_snapshot_policy'''

from __future__ import print_function
import json
import pytest

from units.compat import unittest
from units.compat.mock import patch, Mock
from ansible.module_utils import basic
from ansible.module_utils._text import to_bytes
import ansible.module_utils.netapp as netapp_utils

from ansible.modules.storage.netapp.na_ontap_snapshot_policy \
    import NetAppOntapSnapshotPolicy as my_module

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

    def __init__(self, kind=None):
        ''' save arguments '''
        self.type = kind
        self.xml_in = None
        self.xml_out = None

    def invoke_successfully(self, xml, enable_tunneling):  # pylint: disable=unused-argument
        ''' mock invoke_successfully returning xml data '''
        self.xml_in = xml
        if self.type == 'policy':
            xml = self.build_snapshot_policy_info()
        elif self.type == 'snapshot_policy_info_policy_disabled':
            xml = self.build_snapshot_policy_info_policy_disabled()
        elif self.type == 'snapshot_policy_info_comment_modified':
            xml = self.build_snapshot_policy_info_comment_modified()
        elif self.type == 'snapshot_policy_info_schedules_added':
            xml = self.build_snapshot_policy_info_schedules_added()
        elif self.type == 'snapshot_policy_info_schedules_deleted':
            xml = self.build_snapshot_policy_info_schedules_deleted()
        elif self.type == 'snapshot_policy_info_modified_schedule_counts':
            xml = self.build_snapshot_policy_info_modified_schedule_counts()
        elif self.type == 'policy_fail':
            raise netapp_utils.zapi.NaApiError(code='TEST', message="This exception is from the unit test")
        self.xml_out = xml
        return xml

    def asup_log_for_cserver(self):
        ''' mock autosupport log'''
        return None

    @staticmethod
    def build_snapshot_policy_info():
        ''' build xml data for snapshot-policy-info '''
        xml = netapp_utils.zapi.NaElement('xml')
        data = {'num-records': 1,
                'attributes-list': {
                    'snapshot-policy-info': {
                        'comment': 'new comment',
                        'enabled': 'true',
                        'policy': 'ansible',
                        'snapshot-policy-schedules': {
                            'snapshot-schedule-info': {
                                'count': 100,
                                'schedule': 'hourly',
                                'snapmirror-label': ''
                            }
                        },
                        'vserver-name': 'hostname'
                    }
                }}
        xml.translate_struct(data)
        return xml

    @staticmethod
    def build_snapshot_policy_info_comment_modified():
        ''' build xml data for snapshot-policy-info '''
        xml = netapp_utils.zapi.NaElement('xml')
        data = {'num-records': 1,
                'attributes-list': {
                    'snapshot-policy-info': {
                        'comment': 'modified comment',
                        'enabled': 'true',
                        'policy': 'ansible',
                        'snapshot-policy-schedules': {
                            'snapshot-schedule-info': {
                                'count': 100,
                                'schedule': 'hourly',
                                'snapmirror-label': ''
                            }
                        },
                        'vserver-name': 'hostname'
                    }
                }}
        xml.translate_struct(data)
        return xml

    @staticmethod
    def build_snapshot_policy_info_policy_disabled():
        ''' build xml data for snapshot-policy-info '''
        xml = netapp_utils.zapi.NaElement('xml')
        data = {'num-records': 1,
                'attributes-list': {
                    'snapshot-policy-info': {
                        'comment': 'new comment',
                        'enabled': 'false',
                        'policy': 'ansible',
                        'snapshot-policy-schedules': {
                            'snapshot-schedule-info': {
                                'count': 100,
                                'schedule': 'hourly',
                                'snapmirror-label': ''
                            }
                        },
                        'vserver-name': 'hostname'
                    }
                }}
        xml.translate_struct(data)
        return xml

    @staticmethod
    def build_snapshot_policy_info_schedules_added():
        ''' build xml data for snapshot-policy-info '''
        xml = netapp_utils.zapi.NaElement('xml')
        data = {'num-records': 1,
                'attributes-list': {
                    'snapshot-policy-info': {
                        'comment': 'new comment',
                        'enabled': 'true',
                        'policy': 'ansible',
                        'snapshot-policy-schedules': [
                            {
                                'snapshot-schedule-info': {
                                    'count': 100,
                                    'schedule': 'hourly',
                                    'snapmirror-label': ''
                                }
                            },
                            {
                                'snapshot-schedule-info': {
                                    'count': 5,
                                    'schedule': 'daily',
                                    'snapmirror-label': 'daily'
                                }
                            },
                            {
                                'snapshot-schedule-info': {
                                    'count': 10,
                                    'schedule': 'weekly',
                                    'snapmirror-label': ''
                                }
                            }
                        ],
                        'vserver-name': 'hostname'
                    }
                }}
        xml.translate_struct(data)
        return xml

    @staticmethod
    def build_snapshot_policy_info_schedules_deleted():
        ''' build xml data for snapshot-policy-info '''
        xml = netapp_utils.zapi.NaElement('xml')
        data = {'num-records': 1,
                'attributes-list': {
                    'snapshot-policy-info': {
                        'comment': 'new comment',
                        'enabled': 'true',
                        'policy': 'ansible',
                        'snapshot-policy-schedules': [
                            {
                                'snapshot-schedule-info': {
                                    'schedule': 'daily',
                                    'count': 5,
                                    'snapmirror-label': 'daily'
                                }
                            }
                        ],
                        'vserver-name': 'hostname'
                    }
                }}
        xml.translate_struct(data)
        return xml

    @staticmethod
    def build_snapshot_policy_info_modified_schedule_counts():
        ''' build xml data for snapshot-policy-info '''
        xml = netapp_utils.zapi.NaElement('xml')
        data = {'num-records': 1,
                'attributes-list': {
                    'snapshot-policy-info': {
                        'comment': 'new comment',
                        'enabled': 'true',
                        'policy': 'ansible',
                        'snapshot-policy-schedules': [
                            {
                                'snapshot-schedule-info': {
                                    'count': 10,
                                    'schedule': 'hourly',
                                    'snapmirror-label': ''
                                }
                            },
                            {
                                'snapshot-schedule-info': {
                                    'count': 50,
                                    'schedule': 'daily',
                                    'snapmirror-label': 'daily'
                                }
                            },
                            {
                                'snapshot-schedule-info': {
                                    'count': 100,
                                    'schedule': 'weekly',
                                    'snapmirror-label': ''
                                }
                            }
                        ],
                        'vserver-name': 'hostname'
                    }
                }}
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
        self.onbox = False

    def set_default_args(self):
        if self.onbox:
            hostname = '10.10.10.10'
            username = 'admin'
            password = '1234'
            name = 'ansible'
            enabled = True
            count = 100
            schedule = 'hourly'
            comment = 'new comment'
        else:
            hostname = 'hostname'
            username = 'username'
            password = 'password'
            name = 'ansible'
            enabled = True
            count = 100
            schedule = 'hourly'
            comment = 'new comment'
        return dict({
            'hostname': hostname,
            'username': username,
            'password': password,
            'name': name,
            'enabled': enabled,
            'count': count,
            'schedule': schedule,
            'comment': comment
        })

    def set_default_current(self):
        default_args = self.set_default_args()
        return dict({
            'name': default_args['name'],
            'enabled': default_args['enabled'],
            'count': [default_args['count']],
            'schedule': [default_args['schedule']],
            'snapmirror_label': [''],
            'comment': default_args['comment'],
            'vserver': default_args['hostname']
        })

    def test_module_fail_when_required_args_missing(self):
        ''' required arguments are reported as errors '''
        with pytest.raises(AnsibleFailJson) as exc:
            set_module_args({})
            my_module()
        print('Info: %s' % exc.value.args[0]['msg'])

    def test_ensure_get_called(self):
        ''' test get_snapshot_policy()  for non-existent snapshot policy'''
        set_module_args(self.set_default_args())
        my_obj = my_module()
        my_obj.server = self.server
        assert my_obj.get_snapshot_policy() is None

    def test_ensure_get_called_existing(self):
        ''' test get_snapshot_policy()  for existing snapshot policy'''
        set_module_args(self.set_default_args())
        my_obj = my_module()
        my_obj.server = MockONTAPConnection(kind='policy')
        assert my_obj.get_snapshot_policy()

    @patch('ansible.modules.storage.netapp.na_ontap_snapshot_policy.NetAppOntapSnapshotPolicy.create_snapshot_policy')
    def test_successful_create(self, create_snapshot):
        ''' creating snapshot policy and testing idempotency '''
        set_module_args(self.set_default_args())
        my_obj = my_module()
        my_obj.asup_log_for_cserver = Mock(return_value=None)
        if not self.onbox:
            my_obj.server = self.server
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        assert exc.value.args[0]['changed']
        create_snapshot.assert_called_with()
        # to reset na_helper from remembering the previous 'changed' value
        my_obj = my_module()
        my_obj.asup_log_for_cserver = Mock(return_value=None)
        if not self.onbox:
            my_obj.server = MockONTAPConnection('policy')
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        assert not exc.value.args[0]['changed']

    @patch('ansible.modules.storage.netapp.na_ontap_snapshot_policy.NetAppOntapSnapshotPolicy.modify_snapshot_policy')
    def test_successful_modify_comment(self, modify_snapshot):
        ''' modifying snapshot policy comment and testing idempotency '''
        data = self.set_default_args()
        data['comment'] = 'modified comment'
        set_module_args(data)
        my_obj = my_module()
        my_obj.asup_log_for_cserver = Mock(return_value=None)
        if not self.onbox:
            my_obj.server = MockONTAPConnection('policy')
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        assert exc.value.args[0]['changed']
        current = self.set_default_current()
        modify_snapshot.assert_called_with(current)
        # to reset na_helper from remembering the previous 'changed' value
        my_obj = my_module()
        my_obj.asup_log_for_cserver = Mock(return_value=None)
        if not self.onbox:
            my_obj.server = MockONTAPConnection('snapshot_policy_info_comment_modified')
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        assert not exc.value.args[0]['changed']

    @patch('ansible.modules.storage.netapp.na_ontap_snapshot_policy.NetAppOntapSnapshotPolicy.modify_snapshot_policy')
    def test_successful_disable_policy(self, modify_snapshot):
        ''' disabling snapshot policy and testing idempotency '''
        data = self.set_default_args()
        data['enabled'] = False
        set_module_args(data)
        my_obj = my_module()
        my_obj.asup_log_for_cserver = Mock(return_value=None)
        if not self.onbox:
            my_obj.server = MockONTAPConnection('policy')
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        assert exc.value.args[0]['changed']
        current = self.set_default_current()
        modify_snapshot.assert_called_with(current)
        # to reset na_helper from remembering the previous 'changed' value
        my_obj = my_module()
        my_obj.asup_log_for_cserver = Mock(return_value=None)
        if not self.onbox:
            my_obj.server = MockONTAPConnection('snapshot_policy_info_policy_disabled')
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        assert not exc.value.args[0]['changed']

    @patch('ansible.modules.storage.netapp.na_ontap_snapshot_policy.NetAppOntapSnapshotPolicy.modify_snapshot_policy')
    def test_successful_enable_policy(self, modify_snapshot):
        ''' enabling snapshot policy and testing idempotency '''
        data = self.set_default_args()
        data['enabled'] = True
        set_module_args(data)
        my_obj = my_module()
        my_obj.asup_log_for_cserver = Mock(return_value=None)
        if not self.onbox:
            my_obj.server = MockONTAPConnection('snapshot_policy_info_policy_disabled')
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        assert exc.value.args[0]['changed']
        current = self.set_default_current()
        current['enabled'] = False
        modify_snapshot.assert_called_with(current)
        # to reset na_helper from remembering the previous 'changed' value
        my_obj = my_module()
        my_obj.asup_log_for_cserver = Mock(return_value=None)
        if not self.onbox:
            my_obj.server = MockONTAPConnection('policy')
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        assert not exc.value.args[0]['changed']

    @patch('ansible.modules.storage.netapp.na_ontap_snapshot_policy.NetAppOntapSnapshotPolicy.modify_snapshot_policy')
    def test_successful_modify_schedules_add(self, modify_snapshot):
        ''' adding snapshot policy schedules and testing idempotency '''
        data = self.set_default_args()
        data['schedule'] = ['hourly', 'daily', 'weekly']
        data['count'] = [100, 5, 10]
        data['snapmirror_label'] = ['', 'daily', '']
        set_module_args(data)
        my_obj = my_module()
        my_obj.asup_log_for_cserver = Mock(return_value=None)
        if not self.onbox:
            my_obj.server = MockONTAPConnection('policy')
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        assert exc.value.args[0]['changed']
        current = self.set_default_current()
        modify_snapshot.assert_called_with(current)
        # to reset na_helper from remembering the previous 'changed' value
        my_obj = my_module()
        my_obj.asup_log_for_cserver = Mock(return_value=None)
        if not self.onbox:
            my_obj.server = MockONTAPConnection('snapshot_policy_info_schedules_added')
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        assert not exc.value.args[0]['changed']

    @patch('ansible.modules.storage.netapp.na_ontap_snapshot_policy.NetAppOntapSnapshotPolicy.modify_snapshot_policy')
    def test_successful_modify_schedules_delete(self, modify_snapshot):
        ''' deleting snapshot policy schedules and testing idempotency '''
        data = self.set_default_args()
        data['schedule'] = ['daily']
        data['count'] = [5]
        set_module_args(data)
        my_obj = my_module()
        my_obj.asup_log_for_cserver = Mock(return_value=None)
        if not self.onbox:
            my_obj.server = MockONTAPConnection('policy')
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        assert exc.value.args[0]['changed']
        current = self.set_default_current()
        modify_snapshot.assert_called_with(current)
        # to reset na_helper from remembering the previous 'changed' value
        my_obj = my_module()
        my_obj.asup_log_for_cserver = Mock(return_value=None)
        if not self.onbox:
            my_obj.server = MockONTAPConnection('snapshot_policy_info_schedules_deleted')
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        assert not exc.value.args[0]['changed']

    @patch('ansible.modules.storage.netapp.na_ontap_snapshot_policy.NetAppOntapSnapshotPolicy.modify_snapshot_policy')
    def test_successful_modify_schedules(self, modify_snapshot):
        ''' modifying snapshot policy schedule counts and testing idempotency '''
        data = self.set_default_args()
        data['schedule'] = ['hourly', 'daily', 'weekly']
        data['count'] = [10, 50, 100]
        set_module_args(data)
        my_obj = my_module()
        my_obj.asup_log_for_cserver = Mock(return_value=None)
        if not self.onbox:
            my_obj.server = MockONTAPConnection('policy')
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        assert exc.value.args[0]['changed']
        current = self.set_default_current()
        modify_snapshot.assert_called_with(current)
        # to reset na_helper from remembering the previous 'changed' value
        my_obj = my_module()
        my_obj.asup_log_for_cserver = Mock(return_value=None)
        if not self.onbox:
            my_obj.server = MockONTAPConnection('snapshot_policy_info_modified_schedule_counts')
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        assert not exc.value.args[0]['changed']

    @patch('ansible.modules.storage.netapp.na_ontap_snapshot_policy.NetAppOntapSnapshotPolicy.delete_snapshot_policy')
    def test_successful_delete(self, delete_snapshot):
        ''' deleting snapshot policy and testing idempotency '''
        data = self.set_default_args()
        data['state'] = 'absent'
        set_module_args(data)
        my_obj = my_module()
        my_obj.asup_log_for_cserver = Mock(return_value=None)
        if not self.onbox:
            my_obj.server = MockONTAPConnection('policy')
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        assert exc.value.args[0]['changed']
        delete_snapshot.assert_called_with()
        # to reset na_helper from remembering the previous 'changed' value
        my_obj = my_module()
        my_obj.asup_log_for_cserver = Mock(return_value=None)
        if not self.onbox:
            my_obj.server = self.server
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        assert not exc.value.args[0]['changed']

    def test_valid_schedule_count(self):
        ''' validate when schedule has same number of elements '''
        data = self.set_default_args()
        data['schedule'] = ['hourly', 'daily', 'weekly', 'monthly', '5min']
        data['count'] = [1, 2, 3, 4, 5]
        set_module_args(data)
        my_obj = my_module()
        my_obj.asup_log_for_cserver = Mock(return_value=None)
        if not self.onbox:
            my_obj.server = self.server
        my_obj.create_snapshot_policy()
        create_xml = my_obj.server.xml_in
        assert data['count'][2] == int(create_xml['count3'])
        assert data['schedule'][4] == create_xml['schedule5']

    def test_valid_schedule_count_with_snapmirror_labels(self):
        ''' validate when schedule has same number of elements with snapmirror labels '''
        data = self.set_default_args()
        data['schedule'] = ['hourly', 'daily', 'weekly', 'monthly', '5min']
        data['count'] = [1, 2, 3, 4, 5]
        data['snapmirror_label'] = ['hourly', 'daily', 'weekly', 'monthly', '5min']
        set_module_args(data)
        my_obj = my_module()
        my_obj.asup_log_for_cserver = Mock(return_value=None)
        if not self.onbox:
            my_obj.server = self.server
        my_obj.create_snapshot_policy()
        create_xml = my_obj.server.xml_in
        assert data['count'][2] == int(create_xml['count3'])
        assert data['schedule'][4] == create_xml['schedule5']
        assert data['snapmirror_label'][3] == create_xml['snapmirror-label4']

    def test_invalid_params(self):
        ''' validate error when schedule does not have same number of elements '''
        data = self.set_default_args()
        data['schedule'] = ['s1', 's2']
        data['count'] = [1, 2, 3]
        set_module_args(data)
        my_obj = my_module()
        my_obj.asup_log_for_cserver = Mock(return_value=None)
        if not self.onbox:
            my_obj.server = self.server
        with pytest.raises(AnsibleFailJson) as exc:
            my_obj.create_snapshot_policy()
        msg = 'Error: A Snapshot policy must have at least 1 ' \
              'schedule and can have up to a maximum of 5 schedules, with a count ' \
              'representing the maximum number of Snapshot copies for each schedule'
        assert exc.value.args[0]['msg'] == msg

    def test_invalid_schedule_count(self):
        ''' validate error when schedule has more than 5 elements '''
        data = self.set_default_args()
        data['schedule'] = ['s1', 's2', 's3', 's4', 's5', 's6']
        data['count'] = [1, 2, 3, 4, 5, 6]
        set_module_args(data)
        my_obj = my_module()
        my_obj.asup_log_for_cserver = Mock(return_value=None)
        if not self.onbox:
            my_obj.server = self.server
        with pytest.raises(AnsibleFailJson) as exc:
            my_obj.create_snapshot_policy()
        msg = 'Error: A Snapshot policy must have at least 1 ' \
              'schedule and can have up to a maximum of 5 schedules, with a count ' \
              'representing the maximum number of Snapshot copies for each schedule'
        assert exc.value.args[0]['msg'] == msg

    def test_invalid_schedule_count_less_than_one(self):
        ''' validate error when schedule has less than 1 element '''
        data = self.set_default_args()
        data['schedule'] = []
        data['count'] = []
        set_module_args(data)
        my_obj = my_module()
        my_obj.asup_log_for_cserver = Mock(return_value=None)
        if not self.onbox:
            my_obj.server = self.server
        with pytest.raises(AnsibleFailJson) as exc:
            my_obj.create_snapshot_policy()
        msg = 'Error: A Snapshot policy must have at least 1 ' \
              'schedule and can have up to a maximum of 5 schedules, with a count ' \
              'representing the maximum number of Snapshot copies for each schedule'
        assert exc.value.args[0]['msg'] == msg

    def test_invalid_schedule_count_is_none(self):
        ''' validate error when schedule is None '''
        data = self.set_default_args()
        data['schedule'] = None
        data['count'] = None
        set_module_args(data)
        my_obj = my_module()
        my_obj.asup_log_for_cserver = Mock(return_value=None)
        if not self.onbox:
            my_obj.server = self.server
        with pytest.raises(AnsibleFailJson) as exc:
            my_obj.create_snapshot_policy()
        msg = 'Error: A Snapshot policy must have at least 1 ' \
              'schedule and can have up to a maximum of 5 schedules, with a count ' \
              'representing the maximum number of Snapshot copies for each schedule'
        assert exc.value.args[0]['msg'] == msg

    def test_invalid_schedule_count_with_snapmirror_labels(self):
        ''' validate error when schedule with snapmirror labels does not have same number of elements '''
        data = self.set_default_args()
        data['schedule'] = ['s1', 's2', 's3']
        data['count'] = [1, 2, 3]
        data['snapmirror_label'] = ['sm1', 'sm2']
        set_module_args(data)
        my_obj = my_module()
        my_obj.asup_log_for_cserver = Mock(return_value=None)
        if not self.onbox:
            my_obj.server = self.server
        with pytest.raises(AnsibleFailJson) as exc:
            my_obj.create_snapshot_policy()
        msg = 'Error: Each Snapshot Policy schedule must have an accompanying SnapMirror Label'
        assert exc.value.args[0]['msg'] == msg

    def test_if_all_methods_catch_exception(self):
        module_args = {}
        module_args.update(self.set_default_args())
        set_module_args(module_args)
        my_obj = my_module()
        if not self.onbox:
            my_obj.server = MockONTAPConnection('policy_fail')
        with pytest.raises(AnsibleFailJson) as exc:
            my_obj.create_snapshot_policy()
        assert 'Error creating snapshot policy ansible:' in exc.value.args[0]['msg']
        with pytest.raises(AnsibleFailJson) as exc:
            my_obj.delete_snapshot_policy()
        assert 'Error deleting snapshot policy ansible:' in exc.value.args[0]['msg']
