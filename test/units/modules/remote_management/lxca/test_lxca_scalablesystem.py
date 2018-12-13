import json

import pytest
from units.compat import mock
from ansible.modules.remote_management.lxca import lxca_scalablesystem


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
    @mock.patch("ansible.modules.remote_management.lxca.lxca_scalablesystem.execute_module", autospec=True)
    def test_without_required_parameters(self, _setup_conn, _execute_module,
                                         mocker, capfd, setup_module):
        """Failure must occurs when all parameters are missing"""
        with pytest.raises(SystemExit):
            _setup_conn.return_value = "Fake connection"
            _execute_module.return_value = "Fake execution"
            lxca_scalablesystem.main()
        out, err = capfd.readouterr()
        results = json.loads(out)
        assert results['failed']
        assert 'missing required arguments' in results['msg']

    @mock.patch("ansible.module_utils.remote_management.lxca.common.setup_conn", autospec=True)
    @mock.patch("ansible.modules.remote_management.lxca.lxca_scalablesystem.execute_module", autospec=True)
    @mock.patch("ansible.modules.remote_management.lxca.lxca_scalablesystem.AnsibleModule", autospec=True)
    def test__argument_spec(self, ansible_mod_cls, _execute_module, _setup_conn, setup_module):
        expected_arguments_spec = dict(
            login_user=dict(required=True),
            login_password=dict(required=True, no_log=True),
            command_options=dict(default='scalablesystem', choices=['scalablesystem']),
            auth_url=dict(required=True),
            uuid=dict(default=None),
            device_type=dict(default=None, choices=[None, 'flex', 'rackserver'])
        )
        _setup_conn.return_value = "Fake connection"
        _execute_module.return_value = []
        mod_obj = ansible_mod_cls.return_value
        args = {
            "auth_url": "https://10.243.30.195",
            "login_user": "USERID",
            "login_password": "password",
            "command_options": "scalablesystem",
        }
        mod_obj.params = args
        lxca_scalablesystem.main()
        assert(mock.call(argument_spec=expected_arguments_spec,
                         supports_check_mode=False) == ansible_mod_cls.call_args)

    @mock.patch("ansible.module_utils.remote_management.lxca.common.setup_conn", autospec=True)
    @mock.patch("ansible.modules.remote_management.lxca.lxca_scalablesystem._scalablesystem",
                autospec=True)
    @mock.patch("ansible.modules.remote_management.lxca.lxca_scalablesystem.AnsibleModule",
                autospec=True)
    def test__scalablesystem_empty_list(self, ansible_mod_cls, _get_scalablesystem, _setup_conn, setup_module):
        mod_obj = ansible_mod_cls.return_value
        args = {
            "auth_url": "https://10.243.30.195",
            "login_user": "USERID",
            "login_password": "password",
            "uuid": "3C737AA5E31640CE949B10C129A8B01F",
            "command_options": "scalablesystem",
        }
        mod_obj.params = args
        _setup_conn.return_value = "Fake connection"
        empty_scalablesystem_list = []
        _get_scalablesystem.return_value = empty_scalablesystem_list
        ret_scalablesystem = _get_scalablesystem(mod_obj, args)
        assert mock.call(mod_obj, mod_obj.params) == _get_scalablesystem.call_args
        assert _get_scalablesystem.return_value == ret_scalablesystem
