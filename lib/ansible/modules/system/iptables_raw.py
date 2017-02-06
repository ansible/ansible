#!/usr/bin/python
# -*- coding: utf-8 -*-

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

"""
(c) 2016, Strahinja Kustudic <strahinjak@nordeus.com>
(c) 2016, Damir Markovic <damir@damirda.com>

This file is part of Ansible

Ansible is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Ansible is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Ansible.  If not, see <http://www.gnu.org/licenses/>.
"""

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: iptables_raw
short_description: Manage iptables rules
version_added: "2.5"
description:
  - Add/remove iptables rules while keeping state.
options:
  backup:
    description:
      - Create a backup of the iptables state file before overwriting it.
    required: false
    choices: ["yes", "no"]
    default: "no"
  ipversion:
    description:
      - Target the IP version this rule is for.
    required: false
    default: "4"
    choices: ["4", "6"]
  keep_unmanaged:
    description:
      - If set to C(yes) keeps active iptables (unmanaged) rules for the target
        C(table) and gives them C(weight=90). This means these rules will be
        ordered after most of the rules, since default priority is 40, so they
        shouldn't be able to block any allow rules. If set to C(no) deletes all
        rules which are not set by this module.
      - "WARNING: Be very careful when running C(keep_unmanaged=no) for the
        first time, since if you don't specify correct rules, you can block
        yourself out of the managed host."
    required: false
    choices: ["yes", "no"]
    default: "yes"
  name:
    description:
      - Name that will be used as an identifier for these rules. It can contain
        alphanumeric characters, underscore, hyphen, dot, or a space; has to be
        UNIQUE for a specified C(table). You can also pass C(name=*) with
        C(state=absent) to flush all rules in the selected table, or even all
        tables with C(table=*).
    required: true
  rules:
    description:
      - The rules that we want to add. Accepts multiline values.
      - "Note: You can only use C(-A)/C(--append), C(-N)/C(--new-chain), and
        C(-P)/C(--policy) to specify rules."
    required: false
  state:
    description:
      - The state this rules fragment should be in.
    choices: ["present", "absent"]
    required: false
    default: present
  table:
    description:
      - The table this rule applies to. You can specify C(table=*) only with
        with C(name=*) and C(state=absent) to flush all rules in all tables.
    choices: ["filter", "nat", "mangle", "raw", "security", "*"]
    required: false
    default: filter
  weight:
    description:
      - Determines the order of the rules. Lower C(weight) means higher
        priority. Supported range is C(0 - 99)
    choices: ["0 - 99"]
    required: false
    default: 40
notes:
  - Requires C(iptables) package. Debian-based distributions additionally
    require C(iptables-persistent).
  - "Depending on the distribution, iptables rules are saved in different
    locations, so that they can be loaded on boot. Red Hat distributions (RHEL,
    CentOS, etc): C(/etc/sysconfig/iptables) and C(/etc/sysconfig/ip6tables);
    Debian distributions (Debian, Ubuntu, etc): C(/etc/iptables/rules.v4) and
    C(/etc/iptables/rules.v6); other distributions: C(/etc/sysconfig/iptables)
    and C(/etc/sysconfig/ip6tables)."
  - This module saves state in C(/etc/ansible-iptables) directory, so don't
    modify this directory!
author:
  - "Strahinja Kustudic (@kustodian)"
  - "Damir Markovic (@damirda)"
'''

EXAMPLES = '''
# Allow all IPv4 traffic coming in on port 80 (http)
- iptables_raw:
    name: allow_tcp_80
    rules: '-A INPUT -p tcp -m tcp --dport 80 -j ACCEPT'

# Set default rules with weight 10 and disregard all unmanaged rules
- iptables_raw:
    name: default_rules
    weight: 10
    keep_unmanaged: no
    rules: |
      -A INPUT -m state --state RELATED,ESTABLISHED -j ACCEPT
      -A INPUT -i lo -j ACCEPT
      -A INPUT -p tcp -m state --state NEW -m tcp --dport 22 -j ACCEPT
      -P INPUT DROP
      -P FORWARD DROP
      -P OUTPUT ACCEPT

# Allow all IPv6 traffic coming in on port 443 (https) with weight 50
- iptables_raw:
    ipversion: 6
    weight: 50
    name: allow_tcp_443
    rules: '-A INPUT -p tcp -m tcp --dport 443 -j ACCEPT'

# Remove the above rule
- iptables_raw:
    state: absent
    ipversion: 6
    name: allow_tcp_443

# Define rules with a custom chain
- iptables_raw:
    name: custom1_rules
    rules: |
      -N CUSTOM1
      -A CUSTOM1 -s 192.168.0.0/24 -j ACCEPT

# Reset all IPv4 iptables rules in all tables and allow all traffic
- iptables_raw:
    name: '*'
    table: '*'
    state: absent
'''

RETURN = '''
state:
    description: state of the rules
    returned: success
    type: string
    sample: present
name:
    description: name of the rules
    returned: success
    type: string
    sample: open_tcp_80
weight:
    description: weight of the rules
    returned: success
    type: int
    sample: 40
ipversion:
    description: IP version of iptables used
    returned: success
    type: int
    sample: 6
rules:
    description: passed rules
    returned: success
    type: string
    sample: "-A INPUT -p tcp -m tcp --dport 80 -j ACCEPT"
table:
    description: iptables table used
    returned: success
    type: string
    sample: filter
backup:
    description: if the iptables file should backed up
    returned: success
    type: boolean
    sample: False
keep_unmanaged:
    description: if it should keep unmanaged rules
    returned: success
    type: boolean
    sample: True
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.basic import json

import time
import fcntl
import re
import shlex
import os
import tempfile

try:
    from collections import defaultdict
except ImportError:
    # This is a workaround for Python 2.4 which doesn't have defaultdict.
    class defaultdict(dict):
        def __init__(self, default_factory, *args, **kwargs):
            super(defaultdict, self).__init__(*args, **kwargs)
            self.default_factory = default_factory

        def __getitem__(self, key):
            try:
                return super(defaultdict, self).__getitem__(key)
            except KeyError:
                return self.__missing__(key)

        def __missing__(self, key):
            try:
                self[key] = self.default_factory()
            except TypeError:
                raise KeyError("Missing key %s" % (key, ))
            else:
                return self[key]


# Genereates a diff dictionary from an old and new table dump.
def generate_diff(dump_old, dump_new):
    diff = dict()
    if dump_old != dump_new:
        diff['before'] = dump_old
        diff['after'] = dump_new
    return diff


def compare_dictionaries(dict1, dict2):
    if dict1 is None or dict2 is None:
        return False
    if not (isinstance(dict1, dict) and isinstance(dict2, dict)):
        return False
    shared_keys = set(dict2.keys()) & set(dict2.keys())
    if not (len(shared_keys) == len(dict1.keys()) and len(shared_keys) == len(dict2.keys())):
        return False
    dicts_are_equal = True
    for key in dict1.keys():
        if isinstance(dict1[key], dict):
            dicts_are_equal = dicts_are_equal and compare_dictionaries(dict1[key], dict2[key])
        else:
            dicts_are_equal = dicts_are_equal and (dict1[key] == dict2[key])
        if not dicts_are_equal:
            break
    return dicts_are_equal


class Iptables:

    # Default chains for each table
    DEFAULT_CHAINS = {
        'filter': ['INPUT', 'FORWARD', 'OUTPUT'],
        'raw': ['PREROUTING', 'OUTPUT'],
        'nat': ['PREROUTING', 'INPUT', 'OUTPUT', 'POSTROUTING'],
        'mangle': ['PREROUTING', 'INPUT', 'FORWARD', 'OUTPUT', 'POSTROUTING'],
        'security': ['INPUT', 'FORWARD', 'OUTPUT']
    }

    # List of tables
    TABLES = list(DEFAULT_CHAINS.copy().keys())

    # Directory which will store the state file.
    STATE_DIR = '/etc/ansible-iptables'

    # Key used for unmanaged rules
    UNMANAGED_RULES_KEY_NAME = '$unmanaged_rules$'

    # Only allow alphanumeric characters, underscore, hyphen, dots, or a space for
    # now. We don't want to have problems while parsing comments using regular
    # expressions.
    RULE_NAME_ALLOWED_CHARS = 'a-zA-Z0-9_ .-'

    module = None

    def __init__(self, module, ipversion):
        # Create directory for json files.
        if not os.path.exists(self.STATE_DIR):
            os.makedirs(self.STATE_DIR)
        if Iptables.module is None:
            Iptables.module = module
        self.state_save_path = self._get_state_save_path(ipversion)
        self.system_save_path = self._get_system_save_path(ipversion)
        self.state_dict = self._read_state_file()
        self.bins = self._get_bins(ipversion)
        self.iptables_names_file = self._get_iptables_names_file(ipversion)
        # Check if we have a required iptables version.
        self._check_compatibility()
        # Save active iptables rules for all tables, so that we don't
        # need to fetch them every time using 'iptables-save' command.
        self._active_rules = {}
        self._refresh_active_rules(table='*')

    def __eq__(self, other):
        return (isinstance(other, self.__class__) and compare_dictionaries(other.state_dict, self.state_dict))

    def __ne__(self, other):
        return not self.__eq__(other)

    def _get_bins(self, ipversion):
        if ipversion == '4':
            return {'iptables': Iptables.module.get_bin_path('iptables'),
                    'iptables-save': Iptables.module.get_bin_path('iptables-save'),
                    'iptables-restore': Iptables.module.get_bin_path('iptables-restore')}
        else:
            return {'iptables': Iptables.module.get_bin_path('ip6tables'),
                    'iptables-save': Iptables.module.get_bin_path('ip6tables-save'),
                    'iptables-restore': Iptables.module.get_bin_path('ip6tables-restore')}

    def _get_iptables_names_file(self, ipversion):
        if ipversion == '4':
            return '/proc/net/ip_tables_names'
        else:
            return '/proc/net/ip6_tables_names'

    # Return a list of active iptables tables
    def _get_list_of_active_tables(self):
        if os.path.isfile(self.iptables_names_file):
            table_names = open(self.iptables_names_file, 'r').read()
            return table_names.splitlines()
        else:
            return []

    # If /etc/debian_version exist, this means this is a debian based OS (Ubuntu, Mint, etc...)
    def _is_debian(self):
        return os.path.isfile('/etc/debian_version')

    # Get the iptables system save path.
    # Supports RHEL/CentOS '/etc/sysconfig/' location.
    # Supports Debian/Ubuntu/Mint,  '/etc/iptables/' location.
    def _get_system_save_path(self, ipversion):
        # distro detection, path setting should be added
        if self._is_debian():
            # Check if iptables-persistent packages is installed
            if not os.path.isdir('/etc/iptables'):
                Iptables.module.fail_json(msg="This module requires 'iptables-persistent' package!")
            if ipversion == '4':
                return '/etc/iptables/rules.v4'
            else:
                return '/etc/iptables/rules.v6'
        else:
            if ipversion == '4':
                return '/etc/sysconfig/iptables'
            else:
                return '/etc/sysconfig/ip6tables'

    # Return path to json state file.
    def _get_state_save_path(self, ipversion):
        if ipversion == '4':
            return self.STATE_DIR + '/iptables.json'
        else:
            return self.STATE_DIR + '/ip6tables.json'

    # Checks if iptables is installed and if we have a correct version.
    def _check_compatibility(self):
        from distutils.version import StrictVersion
        cmd = [self.bins['iptables'], '--version']
        rc, stdout, stderr = Iptables.module.run_command(cmd, check_rc=False)
        if rc == 0:
            result = re.search(r'^ip6tables\s+v(\d+\.\d+)\.\d+$', stdout)
            if result:
                version = result.group(1)
                # CentOS 5 ip6tables (v1.3.x) doesn't support comments,
                # which means it cannot be used with this module.
                if StrictVersion(version) < StrictVersion('1.4'):
                    Iptables.module.fail_json(msg="This module isn't compatible with ip6tables versions older than 1.4.x")
        else:
            Iptables.module.fail_json(msg="Could not fetch iptables version! Is iptables installed?")

    # Read rules from the json state file and return a dict.
    def _read_state_file(self):
        json_str = '{}'
        if os.path.isfile(self.state_save_path):
            try:
                json_str = open(self.state_save_path, 'r').read()
            except:
                Iptables.module.fail_json(msg="Could not read the state file '%s'!" % self.state_save_path)
        try:
            read_dict = defaultdict(lambda: dict(dump='', rules_dict={}), json.loads(json_str))
        except:
            Iptables.module.fail_json(msg="Could not parse the state file '%s'! Please manually delete it to continue." % self.state_save_path)
        return read_dict

    # Checks if a table exists in the state_dict.
    def _has_table(self, tbl):
        return tbl in self.state_dict

    # Deletes table from the state_dict.
    def _delete_table(self, tbl):
        if self._has_table(tbl):
            del self.state_dict[tbl]

    # Acquires lock or exits after wait_for_seconds if it cannot be acquired.
    def acquire_lock_or_exit(self, wait_for_seconds=10):
        lock_file = self.STATE_DIR + '/.iptables.lock'
        i = 0
        f = open(lock_file, 'w+')
        while i < wait_for_seconds:
            try:
                fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
                return
            except IOError:
                i += 1
                time.sleep(1)
        Iptables.module.fail_json(msg="Could not acquire lock to continue execution! "
                                      "Probably another instance of this module is running.")

    # Check if a table has anything to flush (to check all tables pass table='*').
    def table_needs_flush(self, table):
        needs_flush = False
        if table == '*':
            for tbl in Iptables.TABLES:
                # If the table exists or if it needs to be flushed that means will make changes.
                if self._has_table(tbl) or self._single_table_needs_flush(tbl):
                    needs_flush = True
                    break
        # Only flush the specified table
        else:
            if self._has_table(table) or self._single_table_needs_flush(table):
                needs_flush = True
        return needs_flush

    # Check if a passed table needs to be flushed.
    def _single_table_needs_flush(self, table):
        needs_flush = False
        active_rules = self._get_active_rules(table)
        if active_rules:
            policies = self._filter_default_chain_policies(active_rules, table)
            chains = self._filter_custom_chains(active_rules, table)
            rules = self._filter_rules(active_rules, table)
            # Go over default policies and check if they are all ACCEPT.
            for line in policies.splitlines():
                if not re.search(r'\bACCEPT\b', line):
                    needs_flush = True
                    break
            # If there is at least one rule or custom chain, that means we need flush.
            if len(chains) > 0 or len(rules) > 0:
                needs_flush = True
        return needs_flush

    # Returns a copy of the rules dict of a passed table.
    def _get_table_rules_dict(self, table):
        return self.state_dict[table]['rules_dict'].copy()

    # Returns saved table dump.
    def get_saved_table_dump(self, table):
        return self.state_dict[table]['dump']

    # Sets saved table dump.
    def _set_saved_table_dump(self, table, dump):
        self.state_dict[table]['dump'] = dump

    # Updates saved table dump from the active rules.
    def refresh_saved_table_dump(self, table):
        active_rules = self._get_active_rules(table)
        self._set_saved_table_dump(table, active_rules)

    # Sets active rules of the passed table.
    def _set_active_rules(self, table, rules):
        self._active_rules[table] = rules

    # Return active rules of the passed table.
    def _get_active_rules(self, table, clean=True):
        active_rules = ''
        if table == '*':
            all_rules = []
            for tbl in Iptables.TABLES:
                if tbl in self._active_rules:
                    all_rules.append(self._active_rules[tbl])
            active_rules = '\n'.join(all_rules)
        else:
            active_rules = self._active_rules[table]
        if clean:
            return self._clean_save_dump(active_rules)
        else:
            return active_rules

    # Refresh active rules of a table ('*' for all tables).
    def _refresh_active_rules(self, table):
        if table == '*':
            for tbl in Iptables.TABLES:
                self._set_active_rules(tbl, self._get_system_active_rules(tbl))
        else:
            self._set_active_rules(table, self._get_system_active_rules(table))

    # Get iptables-save dump of active rules of one or all tables (pass '*') and return it as a string.
    def _get_system_active_rules(self, table):
        active_tables = self._get_list_of_active_tables()
        if table == '*':
            cmd = [self.bins['iptables-save']]
            # If there are no active tables, that means there are no rules
            if not active_tables:
                return ""
        else:
            cmd = [self.bins['iptables-save'], '-t', table]
            # If the table is not active, that means it has no rules
            if table not in active_tables:
                return ""
        rc, stdout, stderr = Iptables.module.run_command(cmd, check_rc=True)
        return stdout

    # Splits a rule into tokens
    def _split_rule_into_tokens(self, rule):
        try:
            return shlex.split(rule, comments=True)
        except:
            msg = "Could not parse the iptables rule:\n%s" % rule
            Iptables.module.fail_json(msg=msg)

    # Removes comment lines and empty lines from rules.
    @staticmethod
    def clean_up_rules(rules):
        cleaned_rules = []
        for line in rules.splitlines():
            # Remove lines with comments and empty lines.
            if not (Iptables.is_comment(line) or Iptables.is_empty_line(line)):
                cleaned_rules.append(line)
        return '\n'.join(cleaned_rules)

    # Checks if the line is a custom chain in specific iptables table.
    @staticmethod
    def is_custom_chain(line, table):
        default_chains = Iptables.DEFAULT_CHAINS[table]
        if re.match(r'\s*(:|(-N|--new-chain)\s+)[^\s]+', line) \
           and not re.match(r'\s*(:|(-N|--new-chain)\s+)\b(' + '|'.join(default_chains) + r')\b', line):
            return True
        else:
            return False

    # Checks if the line is a default chain of an iptables table.
    @staticmethod
    def is_default_chain(line, table):
        default_chains = Iptables.DEFAULT_CHAINS[table]
        if re.match(r'\s*(:|(-P|--policy)\s+)\b(' + '|'.join(default_chains) + r')\b\s+(ACCEPT|DROP)', line):
            return True
        else:
            return False

    # Checks if a line is an iptables rule.
    @staticmethod
    def is_rule(line):
        # We should only allow adding rules with '-A/--append', since others don't make any sense.
        if re.match(r'\s*(-A|--append)\s+[^\s]+', line):
            return True
        else:
            return False

    # Checks if a line starts with '#'.
    @staticmethod
    def is_comment(line):
        if re.match(r'\s*#', line):
            return True
        else:
            return False

    # Checks if a line is empty.
    @staticmethod
    def is_empty_line(line):
        if re.match(r'^$', line.strip()):
            return True
        else:
            return False

    # Return name of custom chain from the rule.
    def _get_custom_chain_name(self, line, table):
        if Iptables.is_custom_chain(line, table):
            return re.match(r'\s*(:|(-N|--new-chain)\s+)([^\s]+)', line).group(3)
        else:
            return ''

    # Return name of default chain from the rule.
    def _get_default_chain_name(self, line, table):
        if Iptables.is_default_chain(line, table):
            return re.match(r'\s*(:|(-N|--new-chain)\s+)([^\s]+)', line).group(3)
        else:
            return ''

    # Return target of the default chain from the rule.
    def _get_default_chain_target(self, line, table):
        if Iptables.is_default_chain(line, table):
            return re.match(r'\s*(:|(-N|--new-chain)\s+)([^\s]+)\s+([A-Z]+)', line).group(4)
        else:
            return ''

    # Removes duplicate custom chains from the table rules.
    def _remove_duplicate_custom_chains(self, rules, table):
        all_rules = []
        custom_chain_names = []
        for line in rules.splitlines():
            # Extract custom chains.
            if Iptables.is_custom_chain(line, table):
                chain_name = self._get_custom_chain_name(line, table)
                if chain_name not in custom_chain_names:
                    custom_chain_names.append(chain_name)
                    all_rules.append(line)
            else:
                all_rules.append(line)
        return '\n'.join(all_rules)

    # Returns current iptables-save dump cleaned from comments and packet/byte counters.
    def _clean_save_dump(self, simple_rules):
        cleaned_dump = []
        for line in simple_rules.splitlines():
            # Ignore comments.
            if Iptables.is_comment(line):
                continue
            # Reset counters for chains (begin with ':'), for easier comparing later on.
            if re.match(r'\s*:', line):
                cleaned_dump.append(re.sub(r'\[([0-9]+):([0-9]+)\]', '[0:0]', line))
            else:
                cleaned_dump.append(line)
        cleaned_dump.append('\n')
        return '\n'.join(cleaned_dump)

    # Returns lines with default chain policies.
    def _filter_default_chain_policies(self, rules, table):
        chains = []
        for line in rules.splitlines():
            if Iptables.is_default_chain(line, table):
                chains.append(line)
        return '\n'.join(chains)

    # Returns lines with iptables rules from an iptables-save table dump
    # (removes chain policies, custom chains, comments and everything else). By
    # default returns all rules, if 'only_unmanged=True' returns rules which
    # are not managed by Ansible.
    def _filter_rules(self, rules, table, only_unmanaged=False):
        filtered_rules = []
        for line in rules.splitlines():
            if Iptables.is_rule(line):
                if only_unmanaged:
                    tokens = self._split_rule_into_tokens(line)
                    # We need to check if a rule has a comment which starts with 'ansible[name]'
                    if '--comment' in tokens:
                        comment_index = tokens.index('--comment') + 1
                        if comment_index < len(tokens):
                            # Fetch the comment
                            comment = tokens[comment_index]
                            # Skip the rule if the comment starts with 'ansible[name]'
                            if not re.match(r'ansible\[[' + Iptables.RULE_NAME_ALLOWED_CHARS + r']+\]', comment):
                                filtered_rules.append(line)
                        else:
                            # Fail if there is no comment after the --comment parameter
                            msg = "Iptables rule is missing a comment after the '--comment' parameter:\n%s" % line
                            Iptables.module.fail_json(msg=msg)
                    # If it doesn't have comment, this means it is not managed by Ansible and we should append it.
                    else:
                        filtered_rules.append(line)
                else:
                    filtered_rules.append(line)
        return '\n'.join(filtered_rules)

    # Same as _filter_rules(), but returns custom chains
    def _filter_custom_chains(self, rules, table, only_unmanaged=False):
        filtered_chains = []
        # Get list of managed custom chains, which is needed to detect unmanaged custom chains
        managed_custom_chains_list = self._get_custom_chains_list(table)
        for line in rules.splitlines():
            if Iptables.is_custom_chain(line, table):
                if only_unmanaged:
                    # The chain is not managed by this module if it's not in the list of managed custom chains.
                    chain_name = self._get_custom_chain_name(line, table)
                    if chain_name not in managed_custom_chains_list:
                        filtered_chains.append(line)
                else:
                    filtered_chains.append(line)
        return '\n'.join(filtered_chains)

    # Returns list of custom chains of a table.
    def _get_custom_chains_list(self, table):
        custom_chains_list = []
        for key, value in self._get_table_rules_dict(table).items():
            # Ignore UNMANAGED_RULES_KEY_NAME key, since we only want managed custom chains.
            if key != Iptables.UNMANAGED_RULES_KEY_NAME:
                for line in value['rules'].splitlines():
                    if Iptables.is_custom_chain(line, table):
                        chain_name = self._get_custom_chain_name(line, table)
                        if chain_name not in custom_chains_list:
                            custom_chains_list.append(chain_name)
        return custom_chains_list

    # Prepends 'ansible[name]: ' to iptables rule '--comment' argument,
    # or adds 'ansible[name]' as a comment if there is no comment.
    def _prepend_ansible_comment(self, rules, name):
        commented_lines = []
        for line in rules.splitlines():
            # Extract rules only since we cannot add comments to custom chains.
            if Iptables.is_rule(line):
                tokens = self._split_rule_into_tokens(line)
                if '--comment' in tokens:
                    # If there is a comment parameter, we need to prepand 'ansible[name]: '.
                    comment_index = tokens.index('--comment') + 1
                    if comment_index < len(tokens):
                        # We need to remove double quotes from comments, since there
                        # is an incompatiblity with older iptables versions
                        comment_text = tokens[comment_index].replace('"', '')
                        tokens[comment_index] = 'ansible[' + name + ']: ' + comment_text
                    else:
                        # Fail if there is no comment after the --comment parameter
                        msg = "Iptables rule is missing a comment after the '--comment' parameter:\n%s" % line
                        Iptables.module.fail_json(msg=msg)
                else:
                    # If comment doesn't exist, we add a comment 'ansible[name]'
                    tokens += ['-m', 'comment', '--comment', 'ansible[' + name + ']']
                # Escape and quote tokens in case they have spaces
                tokens = [self._escape_and_quote_string(x) for x in tokens]
                commented_lines.append(" ".join(tokens))
            # Otherwise it's a chain, and we should just return it.
            else:
                commented_lines.append(line)
        return '\n'.join(commented_lines)

    # Double quote a string if it contains a space and escape double quotes.
    def _escape_and_quote_string(self, s):
        escaped = s.replace('"', r'\"')
        if re.search(r'\s', escaped):
            return '"' + escaped + '"'
        else:
            return escaped

    # Add table rule to the state_dict.
    def add_table_rule(self, table, name, weight, rules, prepend_ansible_comment=True):
        self._fail_on_bad_rules(rules, table)
        if prepend_ansible_comment:
            self.state_dict[table]['rules_dict'][name] = {'weight': weight, 'rules': self._prepend_ansible_comment(rules, name)}
        else:
            self.state_dict[table]['rules_dict'][name] = {'weight': weight, 'rules': rules}

    # Remove table rule from the state_dict.
    def remove_table_rule(self, table, name):
        if name in self.state_dict[table]['rules_dict']:
            del self.state_dict[table]['rules_dict'][name]

    # TODO: Add sorting of rules so that diffs in check_mode look nicer and easier to follow.
    #       Sorting would be done from top to bottom like this:
    #        * default chain policies
    #        * custom chains
    #        * rules
    #
    # Converts rules from a state_dict to an iptables-save readable format.
    def get_table_rules(self, table):
        generated_rules = ''
        # We first add a header e.g. '*filter'.
        generated_rules += '*' + table + '\n'
        rules_list = []
        custom_chains_list = []
        default_chain_policies = []
        dict_rules = self._get_table_rules_dict(table)
        # Return list of rule names sorted by ('weight', 'rules') tuple.
        for rule_name in sorted(dict_rules, key=lambda x: (dict_rules[x]['weight'], dict_rules[x]['rules'])):
            rules = dict_rules[rule_name]['rules']
            # Fail if some of the rules are bad
            self._fail_on_bad_rules(rules, table)
            rules_list.append(self._filter_rules(rules, table))
            custom_chains_list.append(self._filter_custom_chains(rules, table))
            default_chain_policies.append(self._filter_default_chain_policies(rules, table))
        # Clean up empty strings from these two lists.
        rules_list = list(filter(None, rules_list))
        custom_chains_list = list(filter(None, custom_chains_list))
        default_chain_policies = list(filter(None, default_chain_policies))
        if default_chain_policies:
            # Since iptables-restore applies the last chain policy it reads, we
            # have to reverse the order of chain policies so that those with
            # the lowest weight (higher priority) are read last.
            generated_rules += '\n'.join(reversed(default_chain_policies)) + '\n'
        if custom_chains_list:
            # We remove duplicate custom chains so that iptables-restore
            # doesn't fail because of that.
            generated_rules += self._remove_duplicate_custom_chains('\n'.join(sorted(custom_chains_list)), table) + '\n'
        if rules_list:
            generated_rules += '\n'.join(rules_list) + '\n'
        generated_rules += 'COMMIT\n'
        return generated_rules

    # Sets unmanaged rules for the passed table in the state_dict.
    def _set_unmanaged_rules(self, table, rules):
        self.add_table_rule(table, Iptables.UNMANAGED_RULES_KEY_NAME, 90, rules, prepend_ansible_comment=False)

    # Clears unmanaged rules of a table.
    def clear_unmanaged_rules(self, table):
        self._set_unmanaged_rules(table, '')

    # Updates unmanaged rules of a table from the active rules.
    def refresh_unmanaged_rules(self, table):
        # Get active iptables rules and clean them up.
        active_rules = self._get_active_rules(table)
        unmanaged_chains_and_rules = []
        unmanaged_chains_and_rules.append(self._filter_custom_chains(active_rules, table, only_unmanaged=True))
        unmanaged_chains_and_rules.append(self._filter_rules(active_rules, table, only_unmanaged=True))
        # Clean items which are empty strings
        unmanaged_chains_and_rules = list(filter(None, unmanaged_chains_and_rules))
        self._set_unmanaged_rules(table, '\n'.join(unmanaged_chains_and_rules))

    # Check if there are bad lines in the specified rules.
    def _fail_on_bad_rules(self, rules, table):
        for line in rules.splitlines():
            tokens = self._split_rule_into_tokens(line)
            if '-t' in tokens or '--table' in tokens:
                msg = ("Iptables rules cannot contain '-t/--table' parameter. "
                       "You should use the 'table' parameter of the module to set rules "
                       "for a specific table.")
                Iptables.module.fail_json(msg=msg)
            # Fail if the parameter --comment doesn't have a comment after
            if '--comment' in tokens and len(tokens) <= tokens.index('--comment') + 1:
                msg = "Iptables rule is missing a comment after the '--comment' parameter:\n%s" % line
                Iptables.module.fail_json(msg=msg)
            if not (Iptables.is_rule(line) or
                    Iptables.is_custom_chain(line, table) or
                    Iptables.is_default_chain(line, table) or
                    Iptables.is_comment(line)):
                msg = ("Bad iptables rule '%s'! You can only use -A/--append, -N/--new-chain "
                       "and -P/--policy to specify rules." % line)
                Iptables.module.fail_json(msg=msg)

    # Write rules to dest path.
    def _write_rules_to_file(self, rules, dest):
        tmp_path = self._write_to_temp_file(rules)
        Iptables.module.atomic_move(tmp_path, dest)

    # Write text to a temp file and return path to that file.
    def _write_to_temp_file(self, text):
        fd, path = tempfile.mkstemp()
        Iptables.module.add_cleanup_file(path)   # add file for cleanup later
        tmp = os.fdopen(fd, 'w')
        tmp.write(text)
        tmp.close()
        return path

    #
    # Public and private methods which make changes on the system
    # are named 'system_*' and '_system_*', respectively.
    #

    # Flush all rules in a passed table.
    def _system_flush_single_table_rules(self, table):
        # Set all default chain policies to ACCEPT.
        for chain in Iptables.DEFAULT_CHAINS[table]:
            cmd = [self.bins['iptables'], '-t', table, '-P', chain, 'ACCEPT']
            Iptables.module.run_command(cmd, check_rc=True)
        # Then flush all rules.
        cmd = [self.bins['iptables'], '-t', table, '-F']
        Iptables.module.run_command(cmd, check_rc=True)
        # And delete custom chains.
        cmd = [self.bins['iptables'], '-t', table, '-X']
        Iptables.module.run_command(cmd, check_rc=True)
        # Update active rules in the object.
        self._refresh_active_rules(table)

    # Save active iptables rules to the system path.
    def _system_save_active(self, backup=False):
        # Backup if needed
        if backup:
            Iptables.module.backup_local(self.system_save_path)
        # Get iptables-save dump of all tables
        all_active_rules = self._get_active_rules(table='*', clean=False)
        # Move iptables-save dump of all tables to the iptables_save_path
        self._write_rules_to_file(all_active_rules, self.system_save_path)

    # Apply table dict rules to the system.
    def system_apply_table_rules(self, table, test=False):
        dump_path = self._write_to_temp_file(self.get_table_rules(table))
        if test:
            cmd = [self.bins['iptables-restore'], '-t', dump_path]
        else:
            cmd = [self.bins['iptables-restore'], dump_path]
        rc, stdout, stderr = Iptables.module.run_command(cmd, check_rc=False)
        if rc != 0:
            if test:
                dump_contents_file = open(dump_path, 'r')
                dump_contents = dump_contents_file.read()
                dump_contents_file.close()
                msg = "There is a problem with the iptables rules:" \
                      + '\n\nError message:\n' \
                      + stderr \
                      + '\nGenerated rules:\n#######\n' \
                      + dump_contents + '#####'
            else:
                msg = "Could not load iptables rules:\n\n" + stderr
            Iptables.module.fail_json(msg=msg)
        self._refresh_active_rules(table)

    # Flush one or all tables (to flush all tables pass table='*').
    def system_flush_table_rules(self, table):
        if table == '*':
            for tbl in Iptables.TABLES:
                self._delete_table(tbl)
                if self._single_table_needs_flush(tbl):
                    self._system_flush_single_table_rules(tbl)
        # Only flush the specified table.
        else:
            self._delete_table(table)
            if self._single_table_needs_flush(table):
                self._system_flush_single_table_rules(table)

    # Saves state file and system iptables rules.
    def system_save(self, backup=False):
        self._system_save_active(backup=backup)
        rules = json.dumps(self.state_dict, sort_keys=True, indent=4, separators=(',', ': '))
        self._write_rules_to_file(rules, self.state_save_path)


def main():

    module = AnsibleModule(
        argument_spec=dict(
            ipversion=dict(required=False, choices=["4", "6"], type='str', default="4"),
            state=dict(required=False, choices=['present', 'absent'], default='present', type='str'),
            weight=dict(required=False, type='int', default=40),
            name=dict(required=True, type='str'),
            table=dict(required=False, choices=Iptables.TABLES + ['*'], default="filter", type='str'),
            rules=dict(required=False, type='str', default=""),
            backup=dict(required=False, type='bool', default=False),
            keep_unmanaged=dict(required=False, type='bool', default=True),
        ),
        supports_check_mode=True,
    )

    check_mode = module.check_mode
    changed = False
    ipversion = module.params['ipversion']
    state = module.params['state']
    weight = module.params['weight']
    name = module.params['name']
    table = module.params['table']
    rules = module.params['rules']
    backup = module.params['backup']
    keep_unmanaged = module.params['keep_unmanaged']

    kw = dict(state=state, name=name, rules=rules, weight=weight, ipversion=ipversion,
              table=table, backup=backup, keep_unmanaged=keep_unmanaged)

    iptables = Iptables(module, ipversion)

    # Acquire lock so that only one instance of this object can exist.
    # Fail if the lock cannot be acquired within 10 seconds.
    iptables.acquire_lock_or_exit(wait_for_seconds=10)

    # Clean up rules of comments and empty lines.
    rules = Iptables.clean_up_rules(rules)

    # Check additional parameter requirements
    if state == 'present' and name == '*':
        module.fail_json(msg="Parameter 'name' can only be '*' if 'state=absent'")
    if state == 'present' and table == '*':
        module.fail_json(msg="Parameter 'table' can only be '*' if 'name=*' and 'state=absent'")
    if state == 'present' and not name:
        module.fail_json(msg="Parameter 'name' cannot be empty")
    if state == 'present' and not re.match('^[' + Iptables.RULE_NAME_ALLOWED_CHARS + ']+$', name):
        module.fail_json(msg="Parameter 'name' not valid! It can only contain alphanumeric characters, "
                             "underscore, hyphen, or a space, got: '%s'" % name)
    if weight < 0 or weight > 99:
        module.fail_json(msg="Parameter 'weight' can be 0-99, got: %d" % weight)
    if state == 'present' and rules == '':
        module.fail_json(msg="Parameter 'rules' cannot be empty when 'state=present'")

    # Flush rules of one or all tables
    if state == 'absent' and name == '*':
        # Check if table(s) need to be flushed
        if iptables.table_needs_flush(table):
            changed = True
        if not check_mode:
            # Flush table(s)
            iptables.system_flush_table_rules(table)
            # Save state and system iptables rules
            iptables.system_save(backup=backup)
        # Exit since there is nothing else to do
        kw['changed'] = changed
        module.exit_json(**kw)

    # Initialize new iptables object which will store new rules
    iptables_new = Iptables(module, ipversion)

    if state == 'present':
        iptables_new.add_table_rule(table, name, weight, rules)
    else:
        iptables_new.remove_table_rule(table, name)

    if keep_unmanaged:
        iptables_new.refresh_unmanaged_rules(table)
    else:
        iptables_new.clear_unmanaged_rules(table)

    # Refresh saved table dump with active iptables rules
    iptables_new.refresh_saved_table_dump(table)

    # Check if there are changes in iptables, and if yes load new rules
    if iptables != iptables_new:

        changed = True

        # Test generated rules
        iptables_new.system_apply_table_rules(table, test=True)

        if check_mode:
            # Create a predicted diff for check_mode.
            # Diff will be created from rules generated from the state dictionary.
            if hasattr(module, '_diff') and module._diff:
                # Update unmanaged rules in the old object so the generated diff
                # from the rules dictionaries is more accurate.
                iptables.refresh_unmanaged_rules(table)
                # Generate table rules from rules dictionaries.
                table_rules_old = iptables.get_table_rules(table)
                table_rules_new = iptables_new.get_table_rules(table)
                # If rules generated from dicts are not equal, we generate a diff from them.
                if table_rules_old != table_rules_new:
                    kw['diff'] = generate_diff(table_rules_old, table_rules_new)
                else:
                    # TODO: Update this comment to be better.
                    kw['diff'] = {'prepared': "System rules were not changed (e.g. rule "
                                              "weight changed, redundant rule, etc)"}
        else:
            # We need to fetch active table dump before we apply new rules
            # since we will need them to generate a diff.
            table_active_rules = iptables_new.get_saved_table_dump(table)

            # Apply generated rules.
            iptables_new.system_apply_table_rules(table)

            # Refresh saved table dump with active iptables rules.
            iptables_new.refresh_saved_table_dump(table)

            # Save state and system iptables rules.
            iptables_new.system_save(backup=backup)

            # Generate a diff.
            if hasattr(module, '_diff') and module._diff:
                table_active_rules_new = iptables_new.get_saved_table_dump(table)
                if table_active_rules != table_active_rules_new:
                    kw['diff'] = generate_diff(table_active_rules, table_active_rules_new)
                else:
                    # TODO: Update this comment to be better.
                    kw['diff'] = {'prepared': "System rules were not changed (e.g. rule "
                                              "weight changed, redundant rule, etc)"}

    kw['changed'] = changed
    module.exit_json(**kw)


if __name__ == '__main__':
    main()
