#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# (c) 2017, Tyler Gates <tgates81@gmail.com>
#
# This module is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This software is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this software.  If not, see <http://www.gnu.org/licenses/>.


from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'metadata_version': '1.1'}

DOCUMENTATION = """
---
module: iptables_raw
short_description: Modify runtime iptables rules
requirements: []
version_added: "2.6"
author: Tyler Gates <tgates81@gmail.com>
description:
  - Iptables manages the system firewall backed by netfilter in the kernel.
  - This module allows one to manage the chains and rules in a way that is
    consistent to the existing iptables cli/saved rules syntax.
  - This, along with task ordering and robust chain and rule actions, allows for
    great flexibility and power.
  - Complex rules can be achieved through a single task, eliminating potential
    mid-flight lockout induced by multiple module calls while building the
    rules.
notes:
  - chain_* and rule_* options require a list of dictionary values. The key
    should designate the task number and the value will be the rule or chain.
options:
  ipv:
    description:
      - Use protocol 4 or 6 when creating rules.
    required: false
    default: "4"
    choices: [ "4", "6" ]
    version_added: "2.6"
  table:
    description:
      - The netfilter table to work on.
    required: false
    choices: ["filter", "nat", "mangle", "raw", "security"]
    default: "filter"
    version_added: "2.6"
  chains_present:
    description:
      - List of chains to be present.
    required: false
    default: null
    version_added: "2.6"
  chains_absent:
    description:
      - List of chains to be absent.
    required: false
    default: null
    version_added: "2.6"
  chains_policy:
    description:
      - List of chains and policy, separated by space in that order, to enforce.
    required: false
    default: null
    version_added: "2.6"
  chains_rename:
    description:
      - List of source chains and destination chains, separated by space in that
        order, to rename. If source is not present but destination is, it is
        assumed the operation has been previously run and will NOT set change or
        failure. If neither source or destination are found, failure is set.
        Similarly, failure is also set if both are present at the same time.
    required: false
    default: null
    version_added: "2.6"
  chains_flush:
    description:
      - List of chains to flush. When there are no underlying rules, nothing
        will be done and therefore change will not be set.
    required: false
    default: null
    version_added: "2.6"
  rules_append:
    description:
      - List of rules to append into the chain, if not present. This should
        look exactly as you would type out via iptables cli, without the
        preceding '-A '.
    required: false
    default: null
    version_added: "2.6"
  rules_insert:
    description:
      - List of rules to insert into the chain, if not present. This should
        look exactly as you would type out via iptables cli, without the
        preceding '-I '.
    required: false
    default: null
    version_added: "2.6"
  rules_absent:
    description:
      - List of rules that should be absent from the chain.
    required: false
    default: null
    version_added: "2.6"
"""

EXAMPLES = """
# Allow port 22 tcp (SSH) from anywhere, appended at the bottom of the chain.
- iptables_raw:
    ipv: 4
    table: filter
    rules_append:
      - { 1: "INPUT -p tcp -m state --state NEW -m tcp --dport 22 -j ACCEPT" }

# Remove SSH rule
- iptables_raw:
    rules_absent:
      - { 1: "INPUT -p tcp -m state --state NEW -m tcp --dport 22 -j ACCEPT" }

# The following will do, in order:
# 1) Add chain 'WWW_SERVICES'.
# 2) Append -j DROP to WWW_SERVICES (at the very bottom).
# 3) Insert tcp port 80 rule to WWW_SERVICES (above the DROP rule).
# 4) Insert tcp port 443 rule to WWW_SERVICES (above the port 80 rule).
# 5) Set default policy for INPUT to 'ACCEPT'.
# 6) Append -j DROP to INPUT.
# 7) Insert tcp port 22 rule to INPUT.
# 8) Remove tcp port 21 rule from INPUT.
# 9) Flush the 'TESTING' table.
# 10) Remove 'OLD_CHAIN' chain.
# 11) Rename chain 'SRC_CHAIN' to 'DST_CHAIN'.
# 12) Append -j MASQUERADE for eth0 on the POSTROUTING chain on the nat table.

- iptables_raw:
    chains_present:
      - { 1: "WWW_SERVICES" }
    chains_policy:
      - { 5: "INPUT ACCEPT" }
    chains_absent:
      - { 10: "OLD_CHAIN" }
    chains_rename:
      - { 11: "SRC_CHAIN DST_CHAIN" }
    chains_flush:
      - { 9: "TESTING" }
    rules_insert:
      - { 7: "INPUT -p tcp -m state --state NEW -m tcp --dport 22 -j ACCEPT" }
      - { 3: "WWW_SERVICES -p tcp -m state --state NEW -m tcp --dport 80 -j ACCEPT" }
      - { 4: "WWW_SERVICES -p tcp -m state --state NEW -m tcp --dport 443 -j ACCEPT" }
    rules_append:
      - { 6: "INPUT -j DROP" }
      - { 2: "WWW_SERVICES -j DROP" }
    rules_absent:
      - { 8: "INPUT -p tcp -m state --state NEW -m tcp --dport 21 -j ACCEPT" }

- iptables_raw:
    table: nat
    rules_append:
      - { 1: "POSTROUTING -o eth0 -j MASQUERADE" }
"""

RETURN = """
ipv:
  description: IP version used
  type: str
  returned: always
failed_chain:
  description: failed chain causing exit
  type: str
  returned: failure
succeeded_chains:
  description: list of succeeded chains
  type: list
  returned: changed
failed_rule:
  description: failed rule causing exit
  type: str
  returned: failure
succeeded_rules:
  description: list of succeeded rules
  type: list
  returned: changed
last_cmd:
  description: last command run
  type: str
  returned: when supported
last_cmd_err:
  description: stderr message from last command run
  type: str
  returned: failure
"""


from ansible.module_utils.basic import AnsibleModule


class iptables_raw(object):
    def __init__(self):
        self.module = AnsibleModule(
            supports_check_mode=True,
            required_one_of=[
                [
                    "rules_append", "rules_insert", "rules_absent",
                    "chains_present", "chains_absent", "chains_policy",
                    "chains_rename", "chains_flush"
                ],
            ],
            argument_spec=dict(
                ipv=dict(
                    required=False,
                    default="4",
                    choices=["4", "6"],
                    type="str",
                ),
                table=dict(
                    required=False,
                    default="filter",
                    choices=["filter", "nat", "mangle", "raw", "security"],
                    type="str",
                ),
                chains_present=dict(
                    required=False,
                    type="list",
                    default=None,
                ),
                chains_absent=dict(
                    required=False,
                    type="list",
                    default=None,
                ),
                chains_policy=dict(
                    required=False,
                    type="list",
                    default=None,
                ),
                chains_rename=dict(
                    required=False,
                    type="list",
                    default=None,
                ),
                chains_flush=dict(
                    required=False,
                    type="list",
                    default=None,
                ),
                rules_append=dict(
                    required=False,
                    type="list",
                    default=None,
                ),
                rules_insert=dict(
                    required=False,
                    type="list",
                    default=None,
                ),
                rules_absent=dict(
                    required=False,
                    type="list",
                    default=None,
                ),
            )
        )

        # return dict
        self.result = dict(
            changed=False,
            failed=False,
            msg="",
            ipv=self.module.params["ipv"],
            failed_chain="",
            succeeded_chains=[],
            failed_rule="",
            succeeded_rules=[],
            last_cmd_err="",
            last_cmd=""
        )

        # Generate initial iptables command.
        iptables_path = []
        if self.result["ipv"] == "4":
            iptables_path = self.module.get_bin_path("iptables", True)
        elif self.result["ipv"] == "6":
            iptables_path = self.module.get_bin_path("ip6tables", True)
        # convert to immutable tuple
        self.iptables_cmd = tuple([iptables_path])

        # Define an ordered task list according to the user defined dictionary
        # key values.
        self.tasks = self.order_tasks()

    def check_chain_present(self, chain):
        cmd = list(self.iptables_cmd)
        cmd.extend(["--table", self.module.params["table"], "--list", chain])
        self.result["last_cmd"] = str(cmd)
        rc, stdout, stderr = self.module.run_command(cmd, check_rc=False)
        self.result["last_cmd_err"] = stderr
        return (rc == 0)

    def chain_policy_set(self, chain, policy):
        policy = policy.upper()
        cmd = list(self.iptables_cmd)
        cmd.extend(["--table", self.module.params["table"], "--list", chain])
        self.result["last_cmd"] = str(cmd)
        rc, stdout, stderr = self.module.run_command(cmd, check_rc=False)
        self.result["last_cmd_err"] = stderr
        if "(policy " + policy + ")" in stdout:
            return True
        return False

    def set_policy_chain(self, chain, policy):
        policy = policy.upper()
        cmd = list(self.iptables_cmd)
        cmd.extend(["--table", self.module.params["table"], "--policy", chain,
                   policy])
        self.result["last_cmd"] = str(cmd)
        rc, stdout, stderr = self.module.run_command(cmd, check_rc=False)
        self.result["last_cmd_err"] = stderr
        return (rc == 0)

    def rename_chain(self, chain_src, chain_dst):
        cmd = list(self.iptables_cmd)
        cmd.extend(["--table", self.module.params["table"], "--rename-chain",
                   chain_src, chain_dst])
        self.result["last_cmd"] = str(cmd)
        rc, stdout, stderr = self.module.run_command(cmd, check_rc=False)
        self.result["last_cmd_err"] = stderr
        return (rc == 0)

    def new_chain(self, chain):
        cmd = list(self.iptables_cmd)
        cmd.extend(["--table", self.module.params["table"], "--new-chain",
                   chain])
        self.result["last_cmd"] = str(cmd)
        rc, stdout, stderr = self.module.run_command(cmd, check_rc=False)
        self.result["last_cmd_err"] = stderr
        return (rc == 0)

    def chain_flushable(self, chain_line):
        cmd = list(self.iptables_cmd)
        cmd.extend(["--table", self.module.params["table"], "--list",
                   chain_line])
        self.result["last_cmd"] = str(cmd)
        rc, stdout, stderr = self.module.run_command(cmd, check_rc=False)
        self.result["last_cmd_err"] = stderr
        if len(stdout.split('\n')) > 3:
            return True
        return False

    def delete_chain(self, chain):
        cmd = list(self.iptables_cmd)
        cmd.extend(["--table", self.module.params["table"], "--delete-chain",
                   chain])
        self.result["last_cmd"] = str(cmd)
        rc, stdout, stderr = self.module.run_command(cmd, check_rc=False)
        self.result["last_cmd_err"] = stderr
        return (rc == 0)

    def flush_chain(self, chain):
        cmd = list(self.iptables_cmd)
        cmd.extend(["--table", self.module.params["table"], "--flush", chain])
        self.result["last_cmd"] = str(cmd)
        rc, stdout, stderr = self.module.run_command(cmd, check_rc=False)
        self.result["last_cmd_err"] = stderr
        return (rc == 0)

    def check_rule_present(self, rule):
        cmd = list(self.iptables_cmd)
        cmd.extend(["--table", self.module.params["table"], "--check"])
        cmd.extend(rule.split())
        self.result["last_cmd"] = str(cmd)
        rc, stdout, stderr = self.module.run_command(cmd, check_rc=False)
        self.result["last_cmd_err"] = stderr
        return (rc == 0)

    def append_rule(self, rule):
        cmd = list(self.iptables_cmd)
        cmd.extend(["--table", self.module.params["table"], "--append"])
        cmd.extend(rule.split())
        self.result["last_cmd"] = str(cmd)
        rc, stdout, stderr = self.module.run_command(cmd, check_rc=False)
        self.result["last_cmd_err"] = stderr
        return (rc == 0)

    def insert_rule(self, rule):
        cmd = list(self.iptables_cmd)
        cmd.extend(["--table", self.module.params["table"], "--insert"])
        cmd.extend(rule.split())
        self.result["last_cmd"] = str(cmd)
        rc, stdout, stderr = self.module.run_command(cmd, check_rc=False)
        self.result["last_cmd_err"] = stderr
        return (rc == 0)

    def delete_rule(self, rule):
        cmd = list(self.iptables_cmd)
        cmd.extend(["--table", self.module.params["table"], "--delete"])
        cmd.extend(rule.split())
        self.result["last_cmd"] = str(cmd)
        rc, stdout, stderr = self.module.run_command(cmd, check_rc=False)
        self.result["last_cmd_err"] = stderr
        return (rc == 0)

    def order_tasks(self):
        """order_tasks - Reorder module parameters and return in custom format.

        Example:
        self.module.params.items() = {
          "chains_present": [{"1": "NEW_CHAIN2"}, {"4": "NEW_CHAIN1"}],
          "rules_insert": [{"2": "INSERT1"}, {"3": "INSERT2"}]
        }
        Returns as: [
        ('1', ['chains_present', 'NEW_CHAIN2']), ('2', ['rules_insert', 'INSERT1']),
        ('3', ['rules_insert', INSERT2']), ('4', ['chains_present', 'NEW_CHAIN1'])
        ]"""

        new_order = {}
        for opt, val in self.module.params.items():
            if not val:
                continue
            if "chains_" not in opt and "rules_" not in opt:
                continue
            for item in val:  # the list of opt values (items).
                if not isinstance(item, dict):
                    self.result["failed"] = True
                    self.result["msg"] = str(item) + ": Not dictionary format, pre-checks failed."
                    self.module.exit_json(**self.result)
                for task_num, opt_val in item.items():
                    # list items broken into dictionary key, value pair.
                    new_order[int(task_num)] = [opt, opt_val]

        return sorted(new_order.items())

    def run_module(self):
        for task_num, (action, item) in self.tasks:
            # Group specific stuff.
            if "chains_" in action:
                def chain_success(chain):
                    self.result["succeeded_chains"].append(action + ": " + chain)
                    self.result["changed"] = True

                def chain_failure(chain, msg=""):
                    self.result["failed"] = True
                    self.result["failed_chain"] = chain
                    self.result["msg"] = msg
                    self.module.exit_json(**self.result)
            elif "rules_" in action:
                rule = item
                rule_present = self.check_rule_present(rule)

                def rule_success(rule):
                    self.result["succeeded_rules"].append(action + ": " + rule)
                    self.result["changed"] = True

                def rule_failure(rule, msg=""):
                    self.result["failed"] = True
                    self.result["failed_rule"] = rule
                    self.result["msg"] = msg
                    self.module.exit_json(**self.result)

            # Individual processing.
            if action == "chains_flush":
                chain = item
                chain_present = self.check_chain_present(chain)
                chain_flushable = self.chain_flushable(chain)

                # Halting sanity checks.
                if not chain_present:
                    chain_failure(chain, chain + ": Chain not present.")

                if chain_flushable and self.module.check_mode:
                    # changeable but in check_mode
                    chain_success(chain)
                elif chain_flushable and not self.module.check_mode:
                    # changeable
                    chain_success(chain) if self.flush_chain(chain) else chain_failure(chain)
            elif action == "chains_present":
                chain = item
                chain_present = self.check_chain_present(chain)

                if not chain_present and self.module.check_mode:
                    chain_success(chain)
                elif not chain_present and not self.module.check_mode:
                    chain_success(chain) if self.new_chain(chain) else chain_failure(chain)
            elif action == "chains_absent":
                chain = item
                chain_present = self.check_chain_present(chain)

                if chain_present and self.module.check_mode:
                    chain_success(chain)
                elif chain_present and not self.module.check_mode:
                    chain_success(chain) if self.delete_chain(chain) else chain_failure(chain)
            elif action == "chains_policy":
                chain, policy = item.split(" ")
                chain_present = self.check_chain_present(chain)
                chain_policy_set = self.chain_policy_set(chain, policy)

                if not chain_present:
                    chain_failure(chain, chain + ": Chain not present.")

                if not chain_policy_set and self.module.check_mode:
                    chain_success(chain)
                elif not chain_policy_set and not self.module.check_mode:
                    chain_success(chain) if self.set_policy_chain(chain, policy) else chain_failure(chain)
            elif action == "chains_rename":
                chain_src, chain_dst = item.split(" ")
                chain_src_present = self.check_chain_present(chain_src)
                chain_dst_present = self.check_chain_present(chain_dst)

                if not chain_src_present and not chain_dst_present:
                    # Neither source or destination (previously moved) are
                    # present, set failure.
                    chain_failure(chain_src, chain_src + ": Chain source is not present.")
                if chain_src_present and chain_dst_present:
                    # Source and destination are both present, set failure.
                    chain_failure(chain_src, chain_src + " -> " + chain_dst + ": Both chain source and destination are already present.")

                if chain_src_present and not chain_dst_present and self.module.check_mode:
                    chain_success(chain_dst)
                elif chain_src_present and not chain_dst_present and not self.module.check_mode:
                    chain_success(chain_dst) if self.rename_chain(chain_src, chain_dst) else chain_failure(chain_src)
            elif action == "rules_insert":
                if not rule_present and self.module.check_mode:
                    rule_success(rule)
                elif not rule_present and not self.module.check_mode:
                    rule_success(rule) if self.insert_rule(rule) else rule_failure(rule)
            elif action == "rules_absent":
                if rule_present and self.module.check_mode:
                    rule_success(rule)
                elif rule_present and not self.module.check_mode:
                    rule_success(rule) if self.delete_rule(rule) else rule_failure(rule)
            elif action == "rules_append":
                if not rule_present and self.module.check_mode:
                    rule_success(rule)
                elif not rule_present and not self.module.check_mode:
                    rule_success(rule) if self.append_rule(rule) else rule_failure(rule)


def main():
    ipt = iptables_raw()
    ipt.run_module()
    ipt.module.exit_json(**ipt.result)


if __name__ == "__main__":
    main()
