#!/usr/bin/python
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
"""
This module was created because the code in this repository is shared with Ansible Core.
So, to avoid merging issues, and maintaining the tests code equal, we create a unique file to
configure the imports that change from ansible.modules.cloud.hpe.one repository to another.
"""

ONEVIEW_MODULE_UTILS_PATH = 'ansible.module_utils.oneview'

from ansible.module_utils.oneview import (HPOneViewException,
                                          HPOneViewTaskError,
                                          OneViewModuleBase,
                                          SPKeys,
                                          ServerProfileMerger,
                                          ServerProfileReplaceNamesByUris,
                                          ResourceComparator)

from ansible.modules.cloud.hpe.oneview_fc_network import FcNetworkModule
from ansible.modules.cloud.hpe.oneview_fc_network_facts import FcNetworkFactsModule
