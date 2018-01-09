# -*- coding: utf-8 -*-
#
# Copyright (c) 2017 F5 Networks Inc.
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


try:
    from f5.bigip import ManagementRoot
    from icontrol.exceptions import iControlUnexpectedHTTPError
    HAS_F5SDK = True
except ImportError:
    HAS_F5SDK = False

try:
    from library.module_utils.network.f5.common import F5BaseClient
except ImportError:
    from ansible.module_utils.network.f5.common import F5BaseClient


class F5Client(F5BaseClient):
    @property
    def api(self):
        result = ManagementRoot(
            self.params['server'],
            self.params['user'],
            self.params['password'],
            port=self.params['server_port'],
            verify=self.params['validate_certs'],
            token='tmos'
        )
        return result
