# -*- coding: utf-8 -*-

#
# Dell EMC OpenManage Ansible Modules
# Version 1.0
# Copyright (C) 2018 Dell Inc.

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
# All rights reserved. Dell, EMC, and other trademarks are trademarks of Dell Inc. or its subsidiaries.
# Other trademarks may be trademarks of their respective owners.
#

from __future__ import (absolute_import, division,
                        print_function)
__metaclass__ = type

try:
    from omsdk.sdkinfra import sdkinfra
    from omsdk.sdkcreds import UserCredentials
    from omsdk.sdkfile import FileOnShare, file_share_manager
    from omsdk.sdkprotopref import ProtoPreference, ProtocolEnum
    from omsdk.http.sdkwsmanbase import WsManOptions
    HAS_OMSDK = True
except ImportError:
    HAS_OMSDK = False


class iDRACConnection:

    def __init__(self, module):
        if not HAS_OMSDK:
            results = {}
            results['msg'] = "Dell EMC OMSDK library is required for this module"
            module.fail_json(**results)
        self.module = module
        self.idrac_ip = self.module.params['idrac_ip']
        self.idrac_user = self.module.params['idrac_user']
        self.idrac_pwd = self.module.params['idrac_pwd']
        self.idrac_port = self.module.params['idrac_port']
        if not all((self.idrac_ip, self.idrac_user, self.idrac_pwd)):
            self.module.fail_json(msg="hostname, username and password required")

    def __enter__(self):
        self.handle = None
        results = {}
        try:
            sd = sdkinfra()
            sd.importPath()
        except Exception as e:
            results['msg'] = "Could not initialize drivers"
            results['exception'] = str(e)
            self.module.fail_json(**results)
        creds = UserCredentials(self.idrac_user, self.idrac_pwd)
        pOp = WsManOptions(port=self.idrac_port)
        idrac = sd.get_driver(sd.driver_enum.iDRAC, self.idrac_ip, creds, pOptions=pOp)
        if idrac is None:
            msg = "Could not find device driver for iDRAC with IP Address: {}".format(self.idrac_ip)
            self.module.fail_json(msg=msg)
        self.handle = idrac
        return self.handle

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.handle:
            self.handle.disconnect()
            return True
        return False
