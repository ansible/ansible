# Copyright: (c) 2016-2017, Hewlett Packard Enterprise Development LP
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import pytest

from mock import Mock, patch
from oneview_module_loader import ONEVIEW_MODULE_UTILS_PATH
from hpOneView.oneview_client import OneViewClient


@pytest.fixture
def mock_ov_client():
    client = Mock()
    OneViewClient.from_json_file = lambda x: client
    client.api_version = 300
    return client


@pytest.fixture
def mock_ansible_module():
    patcher_ansible = patch(ONEVIEW_MODULE_UTILS_PATH + '.AnsibleModule')
    patcher_ansible = patcher_ansible.start()
    ansible_module = Mock()
    patcher_ansible.return_value = ansible_module
    return ansible_module
