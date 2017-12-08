# -*- coding: utf-8 -*-
#
# Copyright (c) 2017 F5 Networks Inc.
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


try:
    from f5.bigip import ManagementRoot as BigipManagementRoot
    from f5.bigip.contexts import TransactionContextManager as BigipTransactionContextManager
    from f5.bigiq import ManagementRoot as BigiqManagementRoot
    from f5.iworkflow import ManagementRoot as IworkflowManagementRoot
    from icontrol.exceptions import iControlUnexpectedHTTPError
    HAS_F5SDK = True
except ImportError:
    HAS_F5SDK = False


def cleanup_tokens(client):
    try:
        resource = client.api.shared.authz.tokens_s.token.load(
            name=client.api.icrs.token
        )
        resource.delete()
    except Exception:
        pass
