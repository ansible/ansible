# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
import pytest

from mock import Mock, patch
from lxca_module_loader import LXCA_MODULE_UTILS_PATH
from pylxca import connect


@pytest.fixture
def mock_lxca_connection():
    connection = patch(connect)
    return connection


@pytest.fixture
def mock_ansible_module():
    patcher_ansible = patch(LXCA_MODULE_UTILS_PATH + '.AnsibleModule')
    patcher_ansible = patcher_ansible.start()
    ansible_module = Mock()
    patcher_ansible.return_value = ansible_module
    return ansible_module
