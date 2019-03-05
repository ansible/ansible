# (c) 2018, NetApp, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

''' unit test template for ONTAP Ansible module '''

from __future__ import print_function
import json
import pytest

from units.compat import unittest
from units.compat.mock import patch, Mock
from ansible.module_utils import basic
from ansible.module_utils._text import to_bytes
import ansible.module_utils.netapp as netapp_utils

from ansible.modules.storage.netapp.na_ontap_nfs \
    import NetAppONTAPNFS as nfs_module  # module under test

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

    def __init__(self, kind=None, data=None, job_error=None):
        ''' save arguments '''
        self.kind = kind
        self.params = data
        self.xml_in = None
        self.xml_out = None

    def invoke_successfully(self, xml, enable_tunneling):  # pylint: disable=unused-argument
        ''' mock invoke_successfully returning xml data '''
        self.xml_in = xml
        if self.kind == 'nfs':
            xml = self.build_nfs_info(self.params)
        self.xml_out = xml
        if self.kind == 'nfs_status':
            xml = self.build_nfs_status_info(self.params)
        return xml

    @staticmethod
    def build_nfs_info(nfs_details):
        ''' build xml data for volume-attributes '''
        xml = netapp_utils.zapi.NaElement('xml')
        attributes = {
            "attributes-list": {
                "nfs-info": {
                    "auth-sys-extended-groups": "false",
                    "cached-cred-harvest-timeout": "86400000",
                    "cached-cred-negative-ttl": "7200000",
                    "cached-cred-positive-ttl": "86400000",
                    "cached-transient-err-ttl": "30000",
                    "chown-mode": "use_export_policy",
                    "enable-ejukebox": "true",
                    "extended-groups-limit": "32",
                    "file-session-io-grouping-count": "5000",
                    "file-session-io-grouping-duration": "120",
                    "ignore-nt-acl-for-root": "false",
                    "is-checksum-enabled-for-replay-cache": "true",
                    "is-mount-rootonly-enabled": "true",
                    "is-netgroup-dns-domain-search": "true",
                    "is-nfs-access-enabled": "false",
                    "is-nfs-rootonly-enabled": "false",
                    "is-nfsv2-enabled": "false",
                    "is-nfsv3-64bit-identifiers-enabled": "false",
                    "is-nfsv3-connection-drop-enabled": "true",
                    "is-nfsv3-enabled": "true",
                    "is-nfsv3-fsid-change-enabled": "true",
                    "is-nfsv4-fsid-change-enabled": "true",
                    "is-nfsv4-numeric-ids-enabled": "true",
                    "is-nfsv40-acl-enabled": "false",
                    "is-nfsv40-enabled": "true",
                    "is-nfsv40-migration-enabled": "false",
                    "is-nfsv40-read-delegation-enabled": "false",
                    "is-nfsv40-referrals-enabled": "false",
                    "is-nfsv40-req-open-confirm-enabled": "false",
                    "is-nfsv40-write-delegation-enabled": "false",
                    "is-nfsv41-acl-enabled": "false",
                    "is-nfsv41-acl-preserve-enabled": "true",
                    "is-nfsv41-enabled": "true",
                    "is-nfsv41-migration-enabled": "false",
                    "is-nfsv41-pnfs-enabled": "true",
                    "is-nfsv41-read-delegation-enabled": "false",
                    "is-nfsv41-referrals-enabled": "false",
                    "is-nfsv41-state-protection-enabled": "true",
                    "is-nfsv41-write-delegation-enabled": "false",
                    "is-qtree-export-enabled": "false",
                    "is-rquota-enabled": "false",
                    "is-tcp-enabled": "false",
                    "is-udp-enabled": "false",
                    "is-v3-ms-dos-client-enabled": "false",
                    "is-validate-qtree-export-enabled": "true",
                    "is-vstorage-enabled": "false",
                    "map-unknown-uid-to-default-windows-user": "true",
                    "mountd-port": "635",
                    "name-service-lookup-protocol": "udp",
                    "netgroup-trust-any-ns-switch-no-match": "false",
                    "nfsv4-acl-max-aces": "400",
                    "nfsv4-grace-seconds": "45",
                    "nfsv4-id-domain": "defaultv4iddomain.com",
                    "nfsv4-lease-seconds": "30",
                    "nfsv41-implementation-id-domain": "netapp.com",
                    "nfsv41-implementation-id-name": "NetApp Release Kalyaniblack__9.4.0",
                    "nfsv41-implementation-id-time": "1541070767",
                    "nfsv4x-session-num-slots": "180",
                    "nfsv4x-session-slot-reply-cache-size": "640",
                    "nlm-port": "4045",
                    "nsm-port": "4046",
                    "ntacl-display-permissive-perms": "false",
                    "ntfs-unix-security-ops": "use_export_policy",
                    "permitted-enc-types": {
                        "string": ["des", "des3", "aes_128", "aes_256"]
                    },
                    "rpcsec-ctx-high": "0",
                    "rpcsec-ctx-idle": "0",
                    "rquotad-port": "4049",
                    "showmount": "true",
                    "showmount-timestamp": "1548372452",
                    "skip-root-owner-write-perm-check": "false",
                    "tcp-max-xfer-size": "1048576",
                    "udp-max-xfer-size": "32768",
                    "v3-search-unconverted-filename": "false",
                    "v4-inherited-acl-preserve": "false",
                    "vserver": "ansible"
                }
            },
            "num-records": "1"
        }
        xml.translate_struct(attributes)
        return xml

    @staticmethod
    def build_nfs_status_info(nfs_status_details):
        ''' build xml data for volume-attributes '''
        xml = netapp_utils.zapi.NaElement('xml')
        attributes = {
            'is-enabled': "true"
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
        self.mock_nfs_group = {
            'vserver': 'nfs_vserver',
        }

    def mock_args(self):
        return {
            'vserver': self.mock_nfs_group['vserver'],
            'hostname': 'test',
            'username': 'test_user',
            'password': 'test_pass!',
            'https': 'False'
        }

    def get_nfs_mock_object(self, kind=None):
        """
        Helper method to return an na_ontap_volume object
        :param kind: passes this param to MockONTAPConnection()
        :return: na_ontap_volume object
        """
        nfsy_obj = nfs_module()
        nfsy_obj.asup_log_for_cserver = Mock(return_value=None)
        nfsy_obj.cluster = Mock()
        nfsy_obj.cluster.invoke_successfully = Mock()
        if kind is None:
            nfsy_obj.server = MockONTAPConnection()
        else:
            nfsy_obj.server = MockONTAPConnection(kind=kind, data=self.mock_nfs_group)
        return nfsy_obj

    def test_module_fail_when_required_args_missing(self):
        ''' required arguments are reported as errors '''
        with pytest.raises(AnsibleFailJson) as exc:
            set_module_args({})
            nfs_module()
        print('Info: %s' % exc.value.args[0]['msg'])

    def test_get_nonexistent_nfs(self):
        ''' Test if get_nfs_service returns None for non-existent nfs '''
        set_module_args(self.mock_args())
        result = self.get_nfs_mock_object().get_nfs_service()
        assert result is None

    def test_get_existing_nfs(self):
        ''' Test if get_policy_group returns details for existing nfs '''
        set_module_args(self.mock_args())
        result = self.get_nfs_mock_object('nfs').get_nfs_service()
        assert result['is_nfsv3_enabled']

    def test_get_nonexistent_nfs_status(self):
        ''' Test if get__nfs_status returns None for non-existent nfs '''
        set_module_args(self.mock_args())
        result = self.get_nfs_mock_object().get_nfs_status()
        assert result is None

    def test_get_existing_nfs_status(self):
        ''' Test if get__nfs_status returns details for nfs '''
        set_module_args(self.mock_args())
        result = self.get_nfs_mock_object('nfs_status').get_nfs_status()
        assert result

    def test_modify_nfs(self):
        ''' Test if modify_nfs runs for existing nfs '''
        data = self.mock_args()
        data['nfsv3'] = 'enabled'
        data['nfsv3_fsid_change'] = 'enabled'
        data['nfsv4'] = 'enabled'
        data['nfsv41'] = 'enabled'
        data['vstorage_state'] = 'enabled'
        data['tcp'] = 'enabled'
        data['udp'] = 'enabled'
        data['nfsv4_id_domain'] = 'nfsv4_id_domain'
        data['nfsv40_acl'] = 'enabled'
        data['nfsv40_read_delegation'] = 'enabled'
        data['nfsv40_write_delegation'] = 'enabled'
        data['nfsv41_acl'] = 'enabled'
        data['nfsv41_read_delegation'] = 'enabled'
        data['nfsv41_write_delegation'] = 'enabled'
        data['showmount'] = 'enabled'
        data['tcp_max_xfer_size'] = '1048576'
        set_module_args(data)
        self.get_nfs_mock_object('nfs_status').modify_nfs()

    def test_successfully_modify_nfs(self):
        ''' Test modify nfs successful for modifying tcp max xfer size. '''
        data = self.mock_args()
        data['tcp_max_xfer_size'] = '8192'
        set_module_args(data)
        with pytest.raises(AnsibleExitJson) as exc:
            self.get_nfs_mock_object('nfs').apply()
        assert exc.value.args[0]['changed']

    def test_modify_nfs_idempotency(self):
        ''' Test modify nfs idempotency '''
        data = self.mock_args()
        data['tcp_max_xfer_size'] = '1048576'
        set_module_args(data)
        with pytest.raises(AnsibleExitJson) as exc:
            self.get_nfs_mock_object('nfs').apply()
        assert not exc.value.args[0]['changed']

    @patch('ansible.modules.storage.netapp.na_ontap_nfs.NetAppONTAPNFS.delete_nfs')
    def test_successfully_delete_nfs(self, delete_nfs):
        ''' Test successfully delete nfs '''
        data = self.mock_args()
        data['state'] = 'absent'
        set_module_args(data)
        obj = self.get_nfs_mock_object('nfs')
        with pytest.raises(AnsibleExitJson) as exc:
            obj.apply()
        assert exc.value.args[0]['changed']
        delete_nfs.assert_called_with()

    @patch('ansible.modules.storage.netapp.na_ontap_nfs.NetAppONTAPNFS.get_nfs_service')
    def test_successfully_enable_nfs(self, get_nfs_service):
        ''' Test successfully enable nfs on non-existent nfs '''
        data = self.mock_args()
        data['state'] = 'present'
        set_module_args(data)
        get_nfs_service.side_effect = [
            None,
            {}
        ]
        obj = self.get_nfs_mock_object('nfs')
        with pytest.raises(AnsibleExitJson) as exc:
            obj.apply()
        assert exc.value.args[0]['changed']
