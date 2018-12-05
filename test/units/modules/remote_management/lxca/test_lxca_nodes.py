import json

import pytest
from units.compat import mock
from ansible.module_utils import basic
from ansible.module_utils._text import to_bytes
from ansible.modules.remote_management.lxca import lxca_nodes
from ansible.module_utils.remote_management.lxca.common import setup_conn
from ansible.module_utils.remote_management.lxca.common import close_conn


@pytest.fixture(scope='module')
@mock.patch("ansible.module_utils.remote_management.lxca.common.close_conn", autospec=True)
def setup_module(close_conn):
    close_conn.return_value = True


class TestMyModule():
    @pytest.mark.parametrize('patch_ansible_module',
                             [
                                 {},
                                 {
                                     "auth_url": "https://10.240.14.195",
                                     "login_user": "USERID",
                                 },
                                 {
                                     "auth_url": "https://10.240.14.195",
                                     "login_password": "Password",
                                 },
                                 {
                                     "login_user": "USERID",
                                     "login_password": "Password",
                                 },
                             ],
                             indirect=['patch_ansible_module'])
    @pytest.mark.usefixtures('patch_ansible_module')
    @mock.patch("ansible.module_utils.remote_management.lxca.common.setup_conn", autospec=True)
    @mock.patch("ansible.modules.remote_management.lxca.lxca_nodes.execute_module", autospec=True)
    def test_without_required_parameters(self, _setup_conn, _execute_module,
                                         mocker, capfd, setup_module):
        """Failure must occurs when all parameters are missing"""
        with pytest.raises(SystemExit):
            _setup_conn.return_value = "Fake connection"
            _execute_module.return_value = "Fake execution"
            lxca_nodes.main()
        out, err = capfd.readouterr()
        results = json.loads(out)
        assert results['failed']
        assert 'missing required arguments' in results['msg']

    @mock.patch("ansible.module_utils.remote_management.lxca.common.setup_conn", autospec=True)
    @mock.patch("ansible.modules.remote_management.lxca.lxca_nodes.execute_module", autospec=True)
    @mock.patch("ansible.modules.remote_management.lxca.lxca_nodes.AnsibleModule", autospec=True)
    def test__argument_spec(self, ansible_mod_cls, _execute_module, _setup_conn, setup_module):
        expected_arguments_spec = dict(
            login_user=dict(required=True),
            login_password=dict(required=True, no_log=True),
            command_options=dict(default='nodes', choices=['nodes', 'nodes_by_uuid',
                                                           'nodes_by_chassis_uuid',
                                                           'nodes_status_managed',
                                                           'nodes_status_unmanaged']),
            auth_url=dict(required=True),
            uuid=dict(default=None),
            chassis=dict(default=None),
        )
        _setup_conn.return_value = "Fake connection"
        _execute_module.return_value = []
        mod_obj = ansible_mod_cls.return_value
        args = {
            "auth_url": "https://10.243.30.195",
            "login_user": "USERID",
            "login_password": "password",
            "command_options": "nodes",
        }
        mod_obj.params = args
        lxca_nodes.main()
        assert(mock.call(argument_spec=expected_arguments_spec,
                         supports_check_mode=False) == ansible_mod_cls.call_args)

    @mock.patch("ansible.module_utils.remote_management.lxca.common.setup_conn", autospec=True)
    @mock.patch("ansible.modules.remote_management.lxca.lxca_nodes._nodes_by_uuid",
                autospec=True)
    @mock.patch("ansible.modules.remote_management.lxca.lxca_nodes.AnsibleModule",
                autospec=True)
    def test__nodes_empty_list(self, ansible_mod_cls, _get_nodes, _setup_conn, setup_module):
        mod_obj = ansible_mod_cls.return_value
        args = {
            "auth_url": "https://10.243.30.195",
            "login_user": "USERID",
            "login_password": "password",
            "uuid": "3C737AA5E31640CE949B10C129A8B01F",
            "command_options": "nodes_by_uuid",
        }
        mod_obj.params = args
        _setup_conn.return_value = "Fake connection"
        empty_nodes_list = []
        _get_nodes.return_value = empty_nodes_list
        ret_nodes = _get_nodes(mod_obj, args)
        assert mock.call(mod_obj, mod_obj.params) == _get_nodes.call_args
        assert _get_nodes.return_value == ret_nodes
