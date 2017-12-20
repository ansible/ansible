# Copyright: (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import pytest
import json

from ansible.modules.net_tools import nmcli

pytestmark = pytest.mark.usefixtures('patch_ansible_module')

TESTCASE = [
    {
        'type': 'ethernet',
        'conn_name': 'non_existent_nw_device',
        'state': 'absent',
        '_ansible_check_mode': True,
    }
]


@pytest.fixture
def mocked_connection_exists(mocker):
    mocker.patch('ansible.modules.net_tools.nmcli.HAVE_DBUS', True)
    mocker.patch('ansible.modules.net_tools.nmcli.HAVE_NM_CLIENT', True)

    get_bin_path = mocker.patch('ansible.module_utils.basic.AnsibleModule.get_bin_path')
    get_bin_path.return_value = '/usr/bin/nmcli'

    connection = mocker.patch.object(nmcli.Nmcli, 'connection_exists')
    connection.return_value = True
    return connection


@pytest.mark.parametrize('patch_ansible_module', TESTCASE, indirect=['patch_ansible_module'])
def test_dns4_none(mocked_connection_exists, capfd):
    """
    Test if DNS4 param is None
    """
    with pytest.raises(SystemExit):
        nmcli.main()

    out, err = capfd.readouterr()
    results = json.loads(out)
    assert results['changed']
