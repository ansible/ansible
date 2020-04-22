#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2020, quidame <quidame@poivron.org>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: iptables_state
short_description: Save iptables state into a file or restore it from a file
version_added: "2.10"
author:
  - quidame (@quidame)
description:
  - C(iptables) is used to set up, maintain, and inspect the tables of IP
    packet filter rules in the Linux kernel.
  - This module handles the saving and/or loading of rules. This is the same
    as the behaviour of the C(iptables-save) and C(iptables-restore) (or
    C(ip6tables-save) and C(ip6tables-restore) for IPv6) commands which this
    module uses internally.
  - Modifying the state of the firewall remotely may lead to loose access to
    the host in case of mistake in new ruleset. This module embeds a rollback
    feature to avoid this, by telling the host to restore previous rules if a
    cookie is still there after a given delay, and all this time telling the
    controller to try to remove this cookie on the host through a new
    connection.
notes:
  - The rollback feature is not a module option and depends on task's
    attributes. To enable it, the module must be played asynchronously, i.e.
    by setting task attributes I(poll) to I(0), and I(async) to a value less
    or equal to C(ANSIBLE_TIMEOUT). If I(async) is greater, the rollback will
    still happen if it shall happen, but you will experience a connection
    timeout instead of more relevant info returned by the module after its
    failure.
options:
  counters:
    description:
      - Save or restore the values of all packet and byte counters.
      - When I(True), the module is not idempotent.
    type: bool
    default: false
  ip_version:
    description:
      - Which version of the IP protocol this module should apply to.
    type: str
    choices: [ ipv4, ipv6 ]
    default: ipv4
  modprobe:
    description:
      - Specify the path to the modprobe program internally used by iptables
        related commands to load kernel modules.
      - By default, /proc/sys/kernel/modprobe is inspected to determine the
        executable's path.
    type: path
  noflush:
    description:
      - For I(state=restored), ignored otherwise.
      - If I(False), restoring iptables rules from a file flushes (deletes)
        all previous contents of the respective table(s). If I(True), the
        previous rules are left untouched (but policies are updated if they're
        specified in the file to restore state from).
    type: bool
    default: false
  path:
    description:
      - The file the iptables state should be saved to.
      - The file the iptables state should be restored from.
      - Required when I(state=saved) or I(state=restored).
    type: path
  state:
    description:
      - Whether the firewall state should be saved (into a file) or restored
        (from a file).
      - When this option is not set, the current iptables state is returned.
    type: str
    choices: [ saved, restored ]
  table:
    description:
      - When C(state=restored), restore only the named table even if the input
        file contains other tables.
      - When C(state=saved) (or left unset), restrict output to only one table.
        If not specified, output includes all active tables.
    type: str
    choices: [ filter, nat, mangle, raw, security ]
  _timeout:
    description:
      - Internal parameter passed in to the module by its action plugin.
      - Delay, in seconds, before rolling back to the previous rules if the
        action plugin is unable to remove the backup/cookie storing these rules.
      - Gets the same value than C(async) task attribute.
    type: int
  _back:
    description:
      - Internal parameter passed in to the module by its action plugin.
      - Path of the backup/cookie storing rules to restore if the action plugin
        is unable to remove it.
      - Gets a value built from C(async_dir).
    type: path
requirements: [iptables, ip6tables]
'''

EXAMPLES = r'''
# This will only retrieve information
- name: get current state of the firewall
  iptables_state:
  register: iptables_state

- name: show current state of the firewall
  debug:
    var: iptables_state.initial_state

# This will apply to all loaded/active IPv4 tables.
- name: Save current state of the firewall in system file
  iptables_state:
    state: saved
    path: /etc/sysconfig/iptables

# This will apply only to IPv6 filter table.
- name: save current state of the firewall in system file
  iptables_state:
    ip_version: ipv6
    table: filter
    state: saved
    path: /etc/iptables/rules.v6

# This will load a state from a file, with a rollback in case of access loss
- name: restore firewall state from a file
  iptables_state:
    state: restored
    path: /run/iptables.apply
  async: "{{ ansible_timeout }}"
  poll: 0

# This will load new rules by appending them to the current ones
- name: restore firewall state from a file
  iptables_state:
    state: restored
    path: /run/iptables.apply
    noflush: true
  async: "{{ ansible_timeout }}"
  poll: 0
'''

RETURN = r'''
applied:
    description: whether or not the wanted state has been successfully applied
    type: bool
    returned: always
initial_state:
    description: the current state of the firewall when module starts
    type: list
    returned: always
restored_state:
    description: the state the module restored, whenever it is applied or not
    type: list
    returned: always
rollback_complete:
    description: whether or not firewall state is the same than the initial one
    type: bool
    returned: failure
'''


import re
import os
import time
import tempfile
import filecmp
import shutil

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_bytes, to_native


IPTABLES = dict(
    ipv4='iptables',
    ipv6='ip6tables',
)

SAVE = dict(
    ipv4='iptables-save',
    ipv6='ip6tables-save',
)

RESTORE = dict(
    ipv4='iptables-restore',
    ipv6='ip6tables-restore',
)

TABLES = dict(
    filter=['INPUT', 'FORWARD', 'OUTPUT'],
    mangle=['PREROUTING', 'INPUT', 'FORWARD', 'OUTPUT', 'POSTROUTING'],
    nat=['PREROUTING', 'INPUT', 'OUTPUT', 'POSTROUTING'],
    raw=['PREROUTING', 'OUTPUT'],
    security=['INPUT', 'FORWARD', 'OUTPUT'],
)


def write_state(b_path, b_lines, validator, changed=False):
    '''
    Write given contents to the given path, and return changed status.
    '''
    # Populate a temporary file
    tmpfd, tmpfile = tempfile.mkstemp()
    with os.fdopen(tmpfd, 'wb') as f:
        for b_line in b_lines:
            f.write('%s\n' % b_line)

    # Test it, i.e. ensure it is in good shape (not a oneliner, no litteral '\n'
    # at EOL, and so on).
    (rc, out, err) = module.run_command([validator, '--test', tmpfile], check_rc=True)

    # Prepare to copy temporary file to the final destination
    if not os.path.exists(b_path):
        b_destdir = os.path.dirname(b_path)
        destdir = to_native(b_destdir, errors='surrogate_or_strict')
        if b_destdir and not os.path.exists(b_destdir) and not module.check_mode:
            try:
                os.makedirs(b_destdir)
            except Exception as e:
                module.fail_json(msg='Error creating %s. Error code: %s. Error description: %s' % (destdir, e[0], e[1]))
        changed = True

    elif not filecmp.cmp(tmpfile, b_path):
        changed = True

    # Do it
    if not module.check_mode:
        shutil.copyfile(tmpfile, b_path)

    return changed


def initialize_from_null_state(bin_iptables, initcommand, table=None):
    '''
    This ensures iptables-state output is suitable for iptables-restore to roll
    back to it, i.e. iptables-save output is not empty. This also works for the
    iptables-nft-save alternative.
    '''
    if table is None:
        table = 'filter'
    PARTCOMMAND = [bin_iptables, '-t', table, '-P']

    for chain in TABLES[table]:
        RESETPOLICY = list(PARTCOMMAND)
        RESETPOLICY.append(chain)
        RESETPOLICY.append('ACCEPT')
        (rc, out, err) = module.run_command(RESETPOLICY, check_rc=True)

    (rc, out, err) = module.run_command(initcommand, check_rc=True)
    return (rc, out, err)


def string_to_filtered_b_lines(string, counters):
    '''
    Remove timestamps to ensure idempotency between runs. Also remove counters
    by default. And return the result as a list of bytes.
    '''
    b_string = to_bytes(string, errors='surrogate_or_strict')
    b_string = re.sub('((^|\n)# (Generated|Completed)[^\n]*) on [^\n]*', '\\1', b_string)
    if not counters:
        b_string = re.sub('[[][0-9]+:[0-9]+[]]', '[0:0]', b_string)
    b_lines = b_string.splitlines()
    while '' in b_lines:
        b_lines.remove('')
    return b_lines


def main():

    global module

    module = AnsibleModule(
        supports_check_mode=True,
        argument_spec=dict(
            path=dict(type='path'),
            state=dict(type='str', choices=['saved', 'restored']),
            table=dict(type='str', choices=['filter', 'nat', 'mangle', 'raw', 'security']),
            noflush=dict(type='bool', default=False),
            counters=dict(type='bool', default=False),
            modprobe=dict(type='path'),
            ip_version=dict(type='str', choices=['ipv4', 'ipv6'], default='ipv4'),
            _timeout=dict(type='int'),
            _back=dict(type='path'),
        ),
        required_together=[
            ['state', 'path'],
            ['_timeout', '_back'],
        ],
    )

    path = module.params['path']
    state = module.params['state']
    table = module.params['table']
    noflush = module.params['noflush']
    counters = module.params['counters']
    modprobe = module.params['modprobe']
    ip_version = module.params['ip_version']
    _timeout = module.params['_timeout']
    _back = module.params['_back']

    bin_iptables = module.get_bin_path(IPTABLES[ip_version], True)
    bin_iptables_save = module.get_bin_path(SAVE[ip_version], True)
    bin_iptables_restore = module.get_bin_path(RESTORE[ip_version], True)

    os.umask(0o077)
    changed = False
    COMMANDARGS = []

    if counters:
        COMMANDARGS.append('--counters')

    if modprobe is not None:
        COMMANDARGS.append('--modprobe')
        COMMANDARGS.append(modprobe)

    if table is not None:
        COMMANDARGS.append('--table')
        COMMANDARGS.append(table)

    INITCOMMAND = list(COMMANDARGS)
    INITCOMMAND.insert(0, bin_iptables_save)

    for chance in (1, 2):
        (rc, stdout, stderr) = module.run_command(INITCOMMAND, check_rc=True)
        if stdout and (table is None or len(stdout.splitlines()) >= len(TABLES[table]) + 4):
            break
        (rc, stdout, stderr) = initialize_from_null_state(bin_iptables, INITCOMMAND, table=table)

    initial_state = string_to_filtered_b_lines(stdout, counters)
    if initial_state is None:
        module.fail_json(msg="Unable to initialize firewall from NULL state.")

    if path is not None:
        b_path = to_bytes(path, errors='surrogate_or_strict')

    if state == 'saved':
        changed = write_state(b_path, initial_state, bin_iptables_restore, changed=changed)

    if state != 'restored':
        cmd = ' '.join(INITCOMMAND)
        module.exit_json(changed=changed, cmd=cmd, initial_state=initial_state)

    #
    # All remaining code is for state=restored
    #
    if not os.path.exists(b_path):
        module.fail_json(msg="Source %s not found" % (path))
    if not os.path.isfile(b_path):
        module.fail_json(msg="Source %s not a file" % (path))
    if not os.access(b_path, os.R_OK):
        module.fail_json(msg="Source %s not readable" % (path))

    MAINCOMMAND = list(COMMANDARGS)
    MAINCOMMAND.insert(0, bin_iptables_restore)

    if _back is not None:
        b_back = to_bytes(_back, errors='surrogate_or_strict')
        garbage = write_state(b_back, initial_state, bin_iptables_restore)
        BACKCOMMAND = list(MAINCOMMAND)
        BACKCOMMAND.append(_back)

    if noflush:
        MAINCOMMAND.append('--noflush')

    MAINCOMMAND.append(path)
    cmd = ' '.join(MAINCOMMAND)

    TESTCOMMAND = list(MAINCOMMAND)
    TESTCOMMAND.insert(1, '--test')

    (rc, stdout, stderr) = module.run_command(TESTCOMMAND)
    if rc != 0:
        module.fail_json(
            msg="Source %s is not suitable for input to %s" % (path, os.path.basename(bin_iptables_restore)),
            rc=rc,
            stdout=stdout,
            stderr=stderr)

    (rc, stdout, stderr) = module.run_command(MAINCOMMAND, check_rc=True)
    (rc, stdout, stderr) = module.run_command(INITCOMMAND, check_rc=True)
    restored_state = string_to_filtered_b_lines(stdout, counters)
    if restored_state != initial_state:
        changed = True

    if _back is None:
        module.exit_json(
            applied=True,
            changed=changed,
            cmd=cmd,
            initial_state=initial_state,
            restored_state=restored_state)

    # The rollback implementation currently needs:
    # Here:
    # * test existence of the backup file, exit with success if it doesn't exist
    # * otherwise, restore iptables from this file and return failure
    # Action plugin:
    # * try to remove the backup file
    # * wait async task is finished and retrieve its final status
    # * modify it and return the result
    # Task:
    # * task attribute 'async' set to the same value (or lower) than ansible
    #   timeout
    # * task attribute 'poll' equals 0
    #
    for x in range(_timeout):
        if os.path.exists(b_back):
            time.sleep(1)
            continue
        module.exit_json(
            applied=True,
            changed=changed,
            cmd=cmd,
            initial_state=initial_state,
            restored_state=restored_state)

    # Here we are: for whatever reason, but probably due to the current ruleset,
    # the action plugin (i.e. on the controller) was unable to remove the backup
    # cookie, so we restore initial state from it.
    (rc, stdout, stderr) = module.run_command(BACKCOMMAND, check_rc=True)
    os.remove(b_back)

    (rc, stdout, stderr) = module.run_command(INITCOMMAND, check_rc=True)
    backed_state = string_to_filtered_b_lines(stdout, counters)

    module.fail_json(
        rollback_complete=(backed_state == initial_state),
        applied=False,
        msg="Failed to confirm state restored from %s. Firewall has been rolled back to initial state." % (path),
        cmd=cmd,
        initial_state=initial_state,
        restored_state=restored_state)


if __name__ == '__main__':
    main()
