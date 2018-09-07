# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import sys
from ansible.compat.tests.mock import patch, Mock

#sys.modules['pylxca'] = Mock()
#sys.modules['pylxca.connect'] = Mock()
sys.modules['future'] = Mock()
sys.modules['__future__'] = Mock()

LXCA_MODULE_UTILS_PATH = 'ansible.module_utils.remote_management.lxca_common'

