# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import annotations

import json

import pytest

from ansible.modules import pip
from ansible.module_utils.testing import patch_module_args


def test_failure_when_pip_absent(mocker, capfd):
    mocker.patch('ansible.modules.pip._have_pip_module').return_value = False

    get_bin_path = mocker.patch('ansible.module_utils.basic.AnsibleModule.get_bin_path')
    get_bin_path.return_value = None

    with pytest.raises(SystemExit), patch_module_args(dict(name='six')):
        pip.main()

    out, err = capfd.readouterr()
    results = json.loads(out)
    assert results['failed']
    assert 'pip needs to be installed' in results['msg']


@pytest.mark.parametrize('test_input, expected', [
    [['django>1.11.1', '<1.11.2', 'ipaddress', 'simpleproject<2.0.0', '>1.1.0'],
        ['django>1.11.1,<1.11.2', 'ipaddress', 'simpleproject<2.0.0,>1.1.0']],
    [['django>1.11.1,<1.11.2,ipaddress', 'simpleproject<2.0.0,>1.1.0'],
        ['django>1.11.1,<1.11.2', 'ipaddress', 'simpleproject<2.0.0,>1.1.0']],
    [['django>1.11.1', '<1.11.2', 'ipaddress,simpleproject<2.0.0,>1.1.0'],
        ['django>1.11.1,<1.11.2', 'ipaddress', 'simpleproject<2.0.0,>1.1.0']]])
def test_recover_package_name(test_input, expected):
    assert pip._recover_package_name(test_input) == expected
