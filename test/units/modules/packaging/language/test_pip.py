# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import pytest

from ansible.modules.packaging.language import pip


pytestmark = pytest.mark.usefixtures('patch_ansible_module')


@pytest.mark.parametrize('patch_ansible_module', [{'name': 'six'}], indirect=['patch_ansible_module'])
def test_failure_when_pip_absent(mocker):
    get_bin_path = mocker.patch('ansible.module_utils.basic.AnsibleModule.get_bin_path')
    get_bin_path.return_value = None

    with pytest.raises(SystemExit):
        pip.main()
