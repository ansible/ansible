#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2018, Hans-Christian Halfbrodt <ansible-hc at halfbrodt.org>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
# see also https://github.com/hc42/ansible-ezjail

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}


DOCUMENTATION = '''
---
module: ezjail
version_added: "2.5"
author:
  - Hans-Christian Halfbrodt (@hc42)
short_description: Manage jails with Ezjail
description:
  - The purpose of this module is to manage jails with Ezjail. Ezjail must
    be installed and configured to use this module. There is currently no
    support for provisioning. You can create jails, delete jails, change
    the ip config, start and stop jails and set if jails are runnable.
notes:
  - Developed for FreeBSD jails creation. You have to setup and install the
    basejail yourself with your own playbook. This way you can decide if
    e.g. you want to use zfs or ufs.
options:
  name:
    description: The jail name (used as identifier)
    required: true
  state:
    description:
      - The state the jail should have
      - C(started) creates jail if not present and starts it.
      - C(stopped) creates a jail if not present and stops the jail
        if running.
      - C(restarted) also creates the jail if not present
        and starts or restarts it.
      - C(absent) will delete the jail if
        present (Caution This will also wipe the jailroot. Consider
        stopping and disabling the jail if you want to keep the jailroot.)
    required: true
  enabled:
    description:
      - Sets the runnable state of the jail (Does not stop the jail if
        set to false. I(state)=C(started) I(enabled)=C(no) is
        considered a valid combination.)
    required: false
  ip_addr:
    description:
      - Ip address string to use for the jail. The string will not be
        validated. An invalid valid value will result in an unstartable
        jail. This parameter is technically only required on jail creation.
        Nevertheless is it a good idea always provide it except for
        I(state)=C(absent). If the current ip address of the jail differs
        (according to the jail config file) the ip will be updated and the
        jail will be restarted if I(state)=C(started) or I(state)=C(restarted).
    required: false
'''

EXAMPLES = '''
- name: www is created
  ezjail:
    name: www
    state: started
    ip_addr: em0|203.0.113.123,em0|2001:db8::1
- name: database is created
  ezjail:
    name: database
    state: started
    ip_addr: lo0|127.0.0.1,lo0|::1

- name: old gets deleted if present
  ezjail:
    name: oldjail
    state: absent

- name: test is running now but wont be after reboot
  ezjail:
    name: test
    state: started
    enabled: no

- name: otherjail is stopped and marked as not runnable
  ezjail:
    name: otherjail
    state: stopped
    enabled: no

- name: lastjail is restarted
  ezjail:
    name: otherjail
    state: restarted
    enabled: yes
'''

RETURN = '''
changed:
    description: if the jail has been modified or state has changed
    type: bool
    returned: success
msg:
    description: The performed action or error message
    type: str
    returned: always
'''

from ansible.module_utils.basic import AnsibleModule
import re
import fileinput

MODULE_SPECS = dict(
    argument_spec=dict(
        name=dict(required=True, type='str'),
        state=dict(default='present', choices=['stopped', 'started', 'restarted', 'absent'], type='str'),
        ip_addr=dict(required=False, type='str'),
        enabled=dict(default=True, required=False, type='bool'),
    ),
    supports_check_mode=True
)


class FailedException(Exception):
    ''' raised if any action fails '''

    def __init__(self, msg):
        self.msg = msg


def ezjail_admin(module, *params, **cmd_options):
    ''' execute ezjail-admin command '''

    cmd = module.get_bin_path('ezjail-admin', required=True)
    if 'check_rc' not in cmd_options:
        cmd_options['check_rc'] = True
    return module.run_command(' '.join([cmd] + list(params)), **cmd_options)


def get_current_ip_addr(module):
    name = module.params['name']
    alphanumname = ''.join([c if c.isalnum() else '_' for c in name])
    filename = '/usr/local/etc/ezjail/' + alphanumname
    ip_addr = None
    try:
        conf_file = open(filename, 'r')
        for line in conf_file:
            if re.search(
                    '^export jail_' + alphanumname + '_ip=".*"$',
                    line) is not None:
                ip_addr = re.sub(
                    '^export jail_' + alphanumname + '_ip="(.*)"$',
                    '\\1', line).rstrip()
                break
        conf_file.close()
    except IOError:
        raise FailedException(
            'Could not open jail config file %s of jail %s'
            % (filename, name))
    if ip_addr is None:
        raise FailedException('ip_addr for jail %s not found in file %s' % (name, filename))
    return ip_addr


def set_ip_addr(module):
    name = module.params['name']
    ip_addr = module.params['ip_addr']
    alphanumname = ''.join([c if c.isalnum() else '_' for c in name])
    filename = '/usr/local/etc/ezjail/' + alphanumname
    try:
        for line in fileinput.input(filename, inplace=True):
            if re.search(
                    '^export jail_' + alphanumname + '_ip=".*"$',
                    line) is not None:
                old_ip_addr = re.sub(
                    '^export jail_' + alphanumname +
                    '_ip="(.*)"$', '\\1', line).rstrip()
                line = line.replace(
                    '"' + old_ip_addr + '"',
                    '"' + ip_addr + '"')
            print(line)
    except IOError:
        raise FailedException(
            'Could not write ip_addr %s into config file %s of jail %s'
            % (ip_addr, filename, name))


def is_enabled(module):
    ''' is the jail enabled / runnable '''

    name = module.params['name']
    rc, out, err = ezjail_admin(module, 'config', '-r', 'test', name)
    return re.search('is not runnable', out) is None


def set_enabled(module, enabled):
    ''' set the jail enabled / runnable or not '''

    name = module.params['name']
    if enabled:
        action = 'run'
    else:
        action = 'norun'
    ezjail_admin(module, 'config', '-r', action, name)


def exists(module):
    ''' is the jailname known to ezjail '''

    name = module.params['name']
    rc, out, err = ezjail_admin(module, 'config', '-r', 'test', name, check_rc=False)
    return rc == 0


def started(module):
    ''' is the jail started '''

    name = module.params['name']
    rc, out, err = ezjail_admin(module, 'list')

    lines = out.strip().split('\n')
    if len(lines) > 2:
        # skip table headlines
        # expexted table format:
        expect_head = ['STA', 'JID', 'IP', 'Hostname', 'Root', 'Directory']
        table_head = lines.pop(0).split()
        if expect_head != table_head:
            raise FailedException(
                'Could not read jail list got %s expected %s'
                % (' '.join(table_head), ' '.join(expect_head)))
        del lines[0]
        for line in lines:
            values = line.split()
            # test if name equals hostname
            # and second letter of status is R for running
            if len(values) >= 4 and values[3] == name:
                return len(values[0]) > 1 and values[0][1] == 'R'
    raise FailedException('Jail %s not found in ezjail-admin list' % (name))


def start_or_stop(module, state):
    ''' starts or stops the jail '''

    name = module.params['name']
    should_be_enabled = True

    # enable to change run state
    if not is_enabled(module):
        should_be_enabled = False
        set_enabled(module, True)

    # change run state
    if state == 'started':
        action = 'start'
    else:
        action = 'stop'
    ezjail_admin(module, action, name)

    # reset enabled state
    if not should_be_enabled:
        set_enabled(module, False)


def create(module):
    ''' creates the jail if required and starts/stops '''

    name = module.params['name']
    state = module.params['state']
    enabled = module.params['enabled']

    change_msgs = []
    new_jail = not exists(module)

    # create if not exists
    if new_jail:
        change_msgs.append('created')
        if module.params['ip_addr'] is None:
            raise FailedException('Missing required parameter ip_addr')
        if not module.check_mode:
            ip_addr = module.params['ip_addr']
            ezjail_admin(module, 'create', name, ip_addr)

    if module.check_mode and not exists(module):
        is_started = False
    else:
        is_started = started(module)

    # update ip
    if not new_jail and 'ip_addr' in module.params and module.params['ip_addr'] is not None:
        ip_addr = module.params['ip_addr']
        if ip_addr != get_current_ip_addr(module):
            change_msgs.append('ip_addr updated')
            if not module.check_mode:
                set_ip_addr(module)
                if state == 'started' and is_started:
                    start_or_stop(module, 'stopped')
                    start_or_stop(module, 'started')

    # start or stop
    sould_be_started = state == 'started'
    if is_started != sould_be_started or state == 'restarted':
        change_msgs.append(state)
        if not module.check_mode:
            if (is_started and state == 'restarted') or state == 'stopped':
                start_or_stop(module, 'stopped')
            if state == 'started':
                start_or_stop(module, 'started')

    # set enabled / runnable state
    is_enabled_save = (module.check_mode and not exists(module)) or is_enabled(module)
    if enabled != is_enabled_save:
        if enabled:
            change_msgs.append('enabled')
        else:
            change_msgs.append('disabled')
        if not module.check_mode:
            set_enabled(module, enabled)

    if module.check_mode:
        msg = 'Jail %s would have been' % (name)
        changed = True
    else:
        msg = 'Jail %s' % (name)
        changed = True
    msg = msg + ' ' + ' and '.join(change_msgs)

    if len(change_msgs) == 0:
        msg = 'Jail %s not changed' % (name)
        changed = False

    return dict(changed=changed, msg=msg)


def delete(module):
    ''' deletes the jail and wipes the jailroot '''

    name = module.params['name']
    if not exists(module):
        return dict(changed=False, msg='Jail %s does not exist' % (name))
    if module.check_mode:
        return dict(changed=True, msg='Jail %s would have been deleted' % (name))

    ezjail_admin(module, 'delete', '-f', '-w', name)
    return dict(changed=True, msg='Jail %s deleted' % (name))


def main():
    ''' execute module '''

    module = AnsibleModule(**MODULE_SPECS)
    state = module.params['state']
    try:
        if state in ['stopped', 'started']:
            result = create(module)
        elif state == 'absent':
            result = delete(module)
        module.exit_json(**result)
    except FailedException as e:
        module.fail_json(msg=e.msg)


if __name__ == '__main__':
    main()
