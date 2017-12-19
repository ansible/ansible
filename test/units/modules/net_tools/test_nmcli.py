# Copyright: (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import pytest
import json

from ansible.modules.net_tools import nmcli

pytestmark = pytest.mark.usefixtures('patch_ansible_module')

TESTCASE = [
    {'type': 'ethernet',
     'conn_name': 'non_existent_nw_device',
     'state': 'absent'}
]


@pytest.mark.parametrize('patch_ansible_module', TESTCASE, indirect=['patch_ansible_module'])
def test_failure(mocker, capfd):
    with pytest.raises(SystemExit):
        nmcli.main()

    out, err = capfd.readouterr()
    results = json.loads(out)
    assert not results['changed']
