# -*- coding: utf-8 -*-
#
# Copyright (2016-2017) Hewlett Packard Enterprise Development LP
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

import sys
from ansible.compat.tests.mock import patch, Mock
sys.modules['hpOneView'] = Mock()
sys.modules['hpOneView.oneview_client'] = Mock()
sys.modules['hpOneView.exceptions'] = Mock()
sys.modules['future'] = Mock()
sys.modules['__future__'] = Mock()

ONEVIEW_MODULE_UTILS_PATH = 'ansible.module_utils.oneview'
from ansible.module_utils.oneview import (HPOneViewException,
                                          HPOneViewTaskError,
                                          OneViewModuleBase)

from ansible.modules.remote_management.hpe.oneview_fc_network import FcNetworkModule
