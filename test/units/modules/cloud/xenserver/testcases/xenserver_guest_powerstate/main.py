# -*- coding: utf-8 -*-
#
# Copyright: (c) 2019, Bojan Vitnik <bvitnik@mainstream.rs>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


from ..xenserver_guest_common import testcase_vm_found
from ..xenserver_guest_powerstate_common import (testcase_powerstate_change,
                                                 testcase_powerstate_change_wait_for_ip_address,
                                                 testcase_no_powerstate_change_wait_for_ip_address)


# For testing main(), we reuse most of the testcases used to test individial functions.
testcase_powerstate = {
    "params": ([(testcase[0], testcase[1], False) for testcase in testcase_vm_found['params']] +
               testcase_powerstate_change['params'] +
               testcase_powerstate_change_wait_for_ip_address['params'] +
               testcase_no_powerstate_change_wait_for_ip_address['params']),
    "ids": (testcase_vm_found['ids'] +
            testcase_powerstate_change['ids'] +
            testcase_powerstate_change_wait_for_ip_address['ids'] +
            testcase_no_powerstate_change_wait_for_ip_address['ids']),
}
