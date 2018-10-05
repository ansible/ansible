# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
import json

import pytest

from ansible.modules.packaging.language import pip


pytestmark = pytest.mark.usefixtures('patch_ansible_module')


@pytest.mark.parametrize('patch_ansible_module', [{'name': 'six'}], indirect=['patch_ansible_module'])
def test_failure_when_pip_absent(mocker, capfd):
    get_bin_path = mocker.patch('ansible.module_utils.basic.AnsibleModule.get_bin_path')
    get_bin_path.return_value = None

    with pytest.raises(SystemExit):
        pip.main()

    out, err = capfd.readouterr()
    results = json.loads(out)
    assert results['failed']
    assert 'pip needs to be installed' in results['msg']


@pytest.mark.parametrize('patch_ansible_module, test_input, expected', [
    [None, ['django>1.11.1', '<1.11.2', 'ipaddress', 'simpleproject<2.0.0', '>1.1.0'],
        ['django>1.11.1,<1.11.2', 'ipaddress', 'simpleproject<2.0.0,>1.1.0']],
    [None, ['django>1.11.1,<1.11.2,ipaddress', 'simpleproject<2.0.0,>1.1.0'],
        ['django>1.11.1,<1.11.2', 'ipaddress', 'simpleproject<2.0.0,>1.1.0']],
    [None, ['django>1.11.1', '<1.11.2', 'ipaddress,simpleproject<2.0.0,>1.1.0'],
        ['django>1.11.1,<1.11.2', 'ipaddress', 'simpleproject<2.0.0,>1.1.0']]])
def test_recover_package_name(test_input, expected):
    assert pip._recover_package_name(test_input) == expected
