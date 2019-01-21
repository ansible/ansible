# -*- coding: utf-8 -*-
#
# Copyright: (c) 2018, Ansible Project
# Copyright: (c) 2018, Abhijeet Kasurde <akasurde@redhat.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import absolute_import, division, print_function
__metaclass__ = type

import os
import sys
import pytest
import json

pyvmomi = pytest.importorskip('pyVmomi')

if sys.version_info < (2, 7):
    pytestmark = pytest.mark.skip("vmware_guest Ansible modules require Python >= 2.7")


from ansible.modules.cloud.vmware import vmware_guest

curr_dir = os.path.dirname(__file__)
test_data_file = open(os.path.join(curr_dir, 'test_data', 'test_vmware_guest_with_parameters.json'), 'r')
TEST_CASES = json.loads(test_data_file.read())
test_data_file.close()


@pytest.mark.parametrize('patch_ansible_module', [{}], indirect=['patch_ansible_module'])
@pytest.mark.usefixtures('patch_ansible_module')
def test_vmware_guest_wo_parameters(capfd):
    with pytest.raises(SystemExit):
        vmware_guest.main()
    out, err = capfd.readouterr()
    results = json.loads(out)
    assert results['failed']
    assert "one of the following is required: name, uuid" in results['msg']


@pytest.mark.parametrize('patch_ansible_module, testcase', TEST_CASES, indirect=['patch_ansible_module'])
@pytest.mark.usefixtures('patch_ansible_module')
def test_vmware_guest_with_parameters(mocker, capfd, testcase):
    if testcase.get('test_ssl_context', None):
        class mocked_ssl:
            pass
        mocker.patch('ansible.module_utils.vmware.ssl', new=mocked_ssl)

    with pytest.raises(SystemExit):
        vmware_guest.main()
    out, err = capfd.readouterr()
    results = json.loads(out)
    assert str(results['failed']) == testcase['failed']
    assert testcase['msg'] in results['msg']
