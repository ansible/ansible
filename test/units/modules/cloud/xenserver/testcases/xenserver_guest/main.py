# -*- coding: utf-8 -*-
#
# Copyright: (c) 2019, Bojan Vitnik <bvitnik@mainstream.rs>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


from ..xenserver_guest_common import testcase_vm_found
from ..xenserver_guest_powerstate_common import testcase_powerstate_change_wait_for_ip_address as testcase_powerstate
from .deploy import testcase_deploy
from .destroy import testcase_destroy
from .reconfigure import testcase_reconfigure


# We reuse most of the testcases used to test individial functions by
# extending them with expect_changed flag.
testcase_guest = {
    "params": ([(testcase[0], testcase[1], True) for testcase in testcase_destroy['params']] +
               [(testcase[0], testcase[1], False) for testcase in testcase_vm_found['params']] +
               [(testcase[0], testcase[1], True) for testcase in testcase_reconfigure['params']] +
               [(dict(testcase[0], state="poweredon"), testcase[1], testcase[2]) for testcase in testcase_powerstate['params']] +
               [(testcase[0], testcase[1], True) for testcase in testcase_deploy['params']]),
    "ids": (testcase_destroy['ids'] +
            testcase_vm_found['ids'] +
            testcase_reconfigure['ids'] +
            testcase_powerstate['ids'] +
            testcase_deploy['ids']),
}
