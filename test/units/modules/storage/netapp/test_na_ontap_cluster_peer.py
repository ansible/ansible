''' unit tests ONTAP Ansible module: na_ontap_cluster_peer '''

from __future__ import print_function
import json
import pytest

from units.compat import unittest
from units.compat.mock import patch, Mock
from ansible.module_utils import basic
from ansible.module_utils._text import to_bytes
import ansible.module_utils.netapp as netapp_utils

from ansible.modules.storage.netapp.na_ontap_cluster_peer \
    import NetAppONTAPClusterPeer as my_module  # module under test

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

    def __init__(self, kind=None, parm1=None):
        ''' save arguments '''
        self.type = kind
        self.data = parm1
        self.xml_in = None
        self.xml_out = None

    def invoke_successfully(self, xml, enable_tunneling):  # pylint: disable=unused-argument
        ''' mock invoke_successfully returning xml data '''
        self.xml_in = xml
        if self.type == 'cluster_peer':
            xml = self.build_cluster_peer_info(self.data)
        self.xml_out = xml
        return xml

    @staticmethod
    def build_cluster_peer_info(parm1):
        ''' build xml data for vserser-info '''
        xml = netapp_utils.zapi.NaElement('xml')
        attributes = {
            'num-records': 1,
            'attributes-list': {
                'cluster-peer-info': {
                    'cluster-name': parm1['dest_cluster_name'],
                    'peer-addresses': parm1['dest_intercluster_lifs']
                }
            }
        }
        xml.translate_struct(attributes)
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
        self.mock_cluster_peer = {
            'source_intercluster_lifs': '1.2.3.4,1.2.3.5',
            'dest_intercluster_lifs': '1.2.3.6,1.2.3.7',
            'passphrase': 'netapp123',
            'dest_hostname': '10.20.30.40',
            'dest_cluster_name': 'cluster2',
            'hostname': 'hostname',
            'username': 'username',
            'password': 'password',

        }

    def mock_args(self):
        return {
            'source_intercluster_lifs': self.mock_cluster_peer['source_intercluster_lifs'],
            'dest_intercluster_lifs': self.mock_cluster_peer['dest_intercluster_lifs'],
            'passphrase': self.mock_cluster_peer['passphrase'],
            'dest_hostname': self.mock_cluster_peer['dest_hostname'],
            'dest_cluster_name': 'cluster2',
            'hostname': 'hostname',
            'username': 'username',
            'password': 'password',
        }

    def get_cluster_peer_mock_object(self, kind=None):
        """
        Helper method to return an na_ontap_cluster_peer object
        :param kind: passes this param to MockONTAPConnection()
        :return: na_ontap_cluster_peer object
        """
        cluster_peer_obj = my_module()
        cluster_peer_obj.asup_log_for_cserver = Mock(return_value=None)
        cluster_peer_obj.cluster = Mock()
        cluster_peer_obj.cluster.invoke_successfully = Mock()
        if kind is None:
            cluster_peer_obj.server = MockONTAPConnection()
            cluster_peer_obj.dest_server = MockONTAPConnection()
        else:
            cluster_peer_obj.server = MockONTAPConnection(kind=kind, parm1=self.mock_cluster_peer)
            cluster_peer_obj.dest_server = MockONTAPConnection(kind=kind, parm1=self.mock_cluster_peer)
        return cluster_peer_obj

    def test_module_fail_when_required_args_missing(self):
        ''' required arguments are reported as errors '''
        with pytest.raises(AnsibleFailJson) as exc:
            set_module_args({})
            my_module()
        print('Info: %s' % exc.value.args[0]['msg'])

    @patch('ansible.modules.storage.netapp.na_ontap_cluster_peer.NetAppONTAPClusterPeer.cluster_peer_get')
    def test_successful_create(self, cluster_peer_get):
        ''' Test successful create '''
        set_module_args(self.mock_args())
        cluster_peer_get.side_effect = [
            None,
            None
        ]
        with pytest.raises(AnsibleExitJson) as exc:
            self.get_cluster_peer_mock_object().apply()
        assert exc.value.args[0]['changed']

    @patch('ansible.modules.storage.netapp.na_ontap_cluster_peer.NetAppONTAPClusterPeer.cluster_peer_get')
    def test_create_idempotency(self, cluster_peer_get):
        ''' Test create idempotency '''
        set_module_args(self.mock_args())
        current1 = {
            'cluster_name': 'cluster1',
            'peer-addresses': '1.2.3.6,1.2.3.7'
        }
        current2 = {
            'cluster_name': 'cluster2',
            'peer-addresses': '1.2.3.4,1.2.3.5'
        }
        cluster_peer_get.side_effect = [
            current1,
            current2
        ]
        with pytest.raises(AnsibleExitJson) as exc:
            self.get_cluster_peer_mock_object('cluster_peer').apply()
        assert not exc.value.args[0]['changed']

    @patch('ansible.modules.storage.netapp.na_ontap_cluster_peer.NetAppONTAPClusterPeer.cluster_peer_get')
    def test_successful_delete(self, cluster_peer_get):
        ''' Test delete existing interface '''
        data = self.mock_args()
        data['state'] = 'absent'
        data['source_cluster_name'] = 'cluster1'
        set_module_args(data)
        current1 = {
            'cluster_name': 'cluster1',
            'peer-addresses': '1.2.3.6,1.2.3.7'
        }
        current2 = {
            'cluster_name': 'cluster2',
            'peer-addresses': '1.2.3.4,1.2.3.5'
        }
        cluster_peer_get.side_effect = [
            current1,
            current2
        ]
        with pytest.raises(AnsibleExitJson) as exc:
            self.get_cluster_peer_mock_object('cluster_peer').apply()
        assert exc.value.args[0]['changed']

    @patch('ansible.modules.storage.netapp.na_ontap_cluster_peer.NetAppONTAPClusterPeer.cluster_peer_get')
    def test_delete_idempotency(self, cluster_peer_get):
        ''' Test delete idempotency '''
        data = self.mock_args()
        data['state'] = 'absent'
        data['source_cluster_name'] = 'cluster2'
        set_module_args(data)
        cluster_peer_get.side_effect = [
            None,
            None
        ]
        with pytest.raises(AnsibleExitJson) as exc:
            self.get_cluster_peer_mock_object().apply()
        assert not exc.value.args[0]['changed']
