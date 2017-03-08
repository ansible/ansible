# file: ./ansible/plugins/strategy/task_firewall.py

# A strategy plugin for Ansible (2.2+) to enforce task action restrictions
# by policy.
#
# NOTE: Enforcement of the plugin itself can be implemented in various ways,
# but currently needs to be done outside of Ansible itself (eg, git commit
# hook to modify playbooks, etc). If you need this sort of plugin then that
# won't be an issue.
#
# Copyright (C) 2017  Doug Bridgens, https://github.com/thisdougb
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301  USA

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import sys
import yaml

from ansible.plugins.strategy.linear import StrategyModule as LinearStrategyModule
from ansible.errors import AnsibleError

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()

class TaskFirewallAnsibleError(AnsibleError):
    ''' a task policy rule has been matched '''
    pass

class StrategyModule(LinearStrategyModule):
    def __init__(self, tqm):

        # NOTE: hard coded because, being a firewall, this should not
        #       be overriden by a local ansible.cfg var.   Still feels
        #       a dirty way to do it.
        self.firewall = Firewall('/etc/ansible/task_firewall_policy.yml')

        self.curr_tqm = tqm
        super(StrategyModule, self).__init__(tqm)

    def _queue_task(self, host, task, task_vars, play_context):
        self.curr_host = host
        self.curr_task = task
        self.curr_task_vars = task_vars
        self.curr_play_context = play_context

        # call firewall check, which will raise() on failure
        self.firewall.reject_task(self.curr_task, self.curr_task_vars)

        # task passed the firewall check, run as usual
        super(StrategyModule, self)._queue_task(host, task, task_vars, play_context)

class Firewall:
    '''
    Enforces a security policy (/etc/ansible/task_firewall_policy.yml) by halting playbook
    execution if a task matching a policy rule attempts to run.

    Policy file format, a dictionary defining what should be blocked:

    # file: /etc/ansible/task_firewall_policy.yml
    # module_name:
    #     arg_name:
    #     arg_name:
    user:
        password:
    '''

    def __init__(self, firewall_policy_path=None):
        '''
        Attempts to load the policy file.   If a policy exists but fails because of
        yaml errors, then fail because I assume the user intention was to include a
        policy.
        '''

        self.policy = {}

        try:
            with open(firewall_policy_path, 'r') as stream:
                self.policy = yaml.load(stream)
        except yaml.YAMLError as exc:
            display.warning('%s badly formatted' % firewall_policy_path)
            raise
        except IOError:
            display.warning('%s missing, no firewall policy will be applied' % firewall_policy_path)
            pass
        else:
            display.v("firewall policy loaded: %s" % firewall_policy_path)


    def reject_task(self, task, task_vars):
        '''
        Checks the current task action and action arguments against the policy
        dictionary, raising an error if the current action or action:arg matches.
        '''

        # is the task action capture by our policy?
        if task.action in self.policy:

            # is the entire action blocked?
            # NOTE: we expect a dict, but future-proof and check for list too
            if not isinstance(self.policy[task.action], dict) and not isinstance(self.policy[task.action], list):
                raise TaskFirewallAnsibleError('firewall policy: module [%s] blocked' % task.action)

            display.v('firewall rule passed: module [%s] generally allowed' % task.action)

            # now check the action args
            for key in self.policy[task.action]:

                # is an arg of this action blocked?
                if key in task.args:
                    raise TaskFirewallAnsibleError('firewall policy: module [%s] arg [%s] blocked' % (task.action, key))

                display.v('firewall rule passed: [%s:%s] against %s' % (task.action, key, task.args))
