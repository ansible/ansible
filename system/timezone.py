#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2016, Shinichi TAMURA (@tmshn)
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

import os
import re
from ansible.module_utils.basic import AnsibleModule, get_platform
from ansible.module_utils.six import iteritems


DOCUMENTATION = '''
---
module: timezone
short_description: Configure timezone setting
description:
  - This module configures the timezone setting, both of the system clock
    and of the hardware clock. I(Currently only Linux platform is supported.)
    It is recommended to restart C(crond) after changing the timezone,
    otherwise the jobs may run at the wrong time.
    It uses the C(timedatectl) command if available. Otherwise, it edits
    C(/etc/sysconfig/clock) or C(/etc/timezone) for the system clock,
    and uses the C(hwclock) command for the hardware clock.
    If you want to set up the NTP, use M(service) module.
version_added: "2.2.0"
options:
  name:
    description:
      - Name of the timezone for the system clock.
        Default is to keep current setting.
    required: false
  hwclock:
    description:
      - Whether the hardware clock is in UTC or in local timezone.
        Default is to keep current setting.
        Note that this option is recommended not to change and may fail
        to configure, especially on virtual environments such as AWS.
    required: false
    aliases: ['rtc']
author: "Shinichi TAMURA (@tmshn)"
'''

RETURN = '''
diff:
  description: The differences about the given arguments.
  returned: success
  type: dictionary
  contains:
    before:
      description: The values before change
      type: dict
    after:
      description: The values after change
      type: dict
'''

EXAMPLES = '''
- name: set timezone to Asia/Tokyo
  timezone: name=Asia/Tokyo
'''


class Timezone(object):
    """This is a generic Timezone manipulation class that is subclassed based on platform.

    A subclass may wish to override the following action methods:
        - get(key, phase)   ... get the value from the system at `phase`
        - set(key, value)   ... set the value to the current system
    """

    def __new__(cls, module):
        """Return the platform-specific subclass.

        It does not use load_platform_subclass() because it need to judge based
        on whether the `timedatectl` command exists.

        Args:
            module: The AnsibleModule.
        """
        if get_platform() == 'Linux':
            if module.get_bin_path('timedatectl') is not None:
                return super(Timezone, SystemdTimezone).__new__(SystemdTimezone)
            else:
                return super(Timezone, NosystemdTimezone).__new__(NosystemdTimezone)
        else:
            # Not supported yet
            return super(Timezone, Timezone).__new__(Timezone)

    def __init__(self, module):
        """Initialize of the class.

        Args:
            module: The AnsibleModule.
        """
        super(Timezone, self).__init__()
        self.msg = []
        # `self.value` holds the values for each params on each phases.
        # Initially there's only info of "planned" phase, but the
        # `self.check()` function will fill out it.
        self.value = dict()
        for key in module.argument_spec:
            value = module.params[key]
            if value is not None:
                self.value[key] = dict(planned=value)
        self.module = module

    def abort(self, msg):
        """Abort the process with error message.

        This is just the wrapper of module.fail_json().

        Args:
            msg: The error message.
        """
        error_msg = ['Error message:', msg]
        if len(self.msg) > 0:
            error_msg.append('Other message(s):')
            error_msg.extend(self.msg)
        self.module.fail_json(msg='\n'.join(error_msg))

    def execute(self, *commands, **kwargs):
        """Execute the shell command.

        This is just the wrapper of module.run_command().

        Args:
            *commands: The command to execute.
                It will be concatenated with single space.
            **kwargs:  Only 'log' key is checked.
                If kwargs['log'] is true, record the command to self.msg.

        Returns:
            stdout: Standard output of the command.
        """
        command = ' '.join(commands)
        (rc, stdout, stderr) = self.module.run_command(command, check_rc=True)
        if kwargs.get('log', False):
            self.msg.append('executed `%s`' % command)
        return stdout

    def diff(self, phase1='before', phase2='after'):
        """Calculate the difference between given 2 phases.

        Args:
            phase1, phase2: The names of phase to compare.

        Returns:
            diff: The difference of value between phase1 and phase2.
                This is in the format which can be used with the
                `--diff` option of ansible-playbook.
        """
        diff = {phase1: {}, phase2: {}}
        for key, value in iteritems(self.value):
            diff[phase1][key] = value[phase1]
            diff[phase2][key] = value[phase2]
        return diff

    def check(self, phase):
        """Check the state in given phase and set it to `self.value`.

        Args:
            phase: The name of the phase to check.

        Returns:
            NO RETURN VALUE
        """
        if phase == 'planned':
            return
        for key, value in iteritems(self.value):
            value[phase] = self.get(key, phase)

    def change(self):
        """Make the changes effect based on `self.value`."""
        for key, value in iteritems(self.value):
            if value['before'] != value['planned']:
                self.set(key, value['planned'])

    # ===========================================
    # Platform specific methods (must be replaced by subclass).

    def get(self, key, phase):
        """Get the value for the key at the given phase.

        Called from self.check().

        Args:
            key:   The key to get the value
            phase: The phase to get the value

        Return:
            value: The value for the key at the given phase.
        """
        self.abort('get(key, phase) is not implemented on target platform')

    def set(self, key, value):
        """Set the value for the key (of course, for the phase 'after').

        Called from self.change().

        Args:
            key: Key to set the value
            value: Value to set
        """
        self.abort('set(key, value) is not implemented on target platform')

    def _verify_timezone(self):
        tz = self.value['name']['planned']
        tzfile = '/usr/share/zoneinfo/%s' % tz
        if not os.path.isfile(tzfile):
            self.abort('given timezone "%s" is not available' % tz)


class SystemdTimezone(Timezone):
    """This is a Timezone manipulation class systemd-powered Linux.

    It uses the `timedatectl` command to check/set all arguments.
    """

    regexps = dict(
        hwclock=re.compile(r'^\s*RTC in local TZ\s*:\s*([^\s]+)', re.MULTILINE),
        name   =re.compile(r'^\s*Time ?zone\s*:\s*([^\s]+)', re.MULTILINE)
    )

    subcmds = dict(
        hwclock='set-local-rtc',
        name   ='set-timezone'
    )

    def __init__(self, module):
        super(SystemdTimezone, self).__init__(module)
        self.timedatectl = module.get_bin_path('timedatectl', required=True)
        self.status = dict()
        # Validate given timezone
        if 'name' in self.value:
            self._verify_timezone()

    def _get_status(self, phase):
        if phase not in self.status:
            self.status[phase] = self.execute(self.timedatectl, 'status')
        return self.status[phase]

    def get(self, key, phase):
        status = self._get_status(phase)
        value = self.regexps[key].search(status).group(1)
        if key == 'hwclock':
            # For key='hwclock'; convert yes/no -> local/UTC
            if self.module.boolean(value):
                value = 'local'
            else:
                value = 'UTC'
        return value

    def set(self, key, value):
        # For key='hwclock'; convert UTC/local -> yes/no
        if key == 'hwclock':
            if value == 'local':
                value = 'yes'
            else:
                value = 'no'
        self.execute(self.timedatectl, self.subcmds[key], value, log=True)


class NosystemdTimezone(Timezone):
    """This is a Timezone manipulation class for non systemd-powered Linux.

    For timezone setting, it edits the following file and reflect changes:
        - /etc/sysconfig/clock  ... RHEL/CentOS
        - /etc/timezone         ... Debian/Ubuntu
    For hwclock setting, it executes `hwclock --systohc` command with the
    '--utc' or '--localtime' option.
    """

    conf_files = dict(
        name   =None,  # To be set in __init__
        hwclock=None,  # To be set in __init__
        adjtime='/etc/adjtime'
    )

    regexps = dict(
        name   =None,  # To be set in __init__
        hwclock=re.compile(r'^UTC\s*=\s*([^\s]+)', re.MULTILINE),
        adjtime=re.compile(r'^(UTC|LOCAL)$', re.MULTILINE)
    )

    def __init__(self, module):
        super(NosystemdTimezone, self).__init__(module)
        # Validate given timezone
        if 'name' in self.value:
            self._verify_timezone()
            self.update_timezone  = self.module.get_bin_path('cp', required=True)
            self.update_timezone += ' %s /etc/localtime' % tzfile
        self.update_hwclock = self.module.get_bin_path('hwclock', required=True)
        # Distribution-specific configurations
        if self.module.get_bin_path('dpkg-reconfigure') is not None:
            # Debian/Ubuntu
            self.update_timezone       = self.module.get_bin_path('dpkg-reconfigure', required=True)
            self.update_timezone      += ' --frontend noninteractive tzdata'
            self.conf_files['name']    = '/etc/timezone',
            self.conf_files['hwclock'] = '/etc/default/rcS',
            self.regexps['name']       = re.compile(r'^([^\s]+)', re.MULTILINE)
            self.tzline_format         = '%s\n'
        else:
            # RHEL/CentOS
            if self.module.get_bin_path('tzdata-update') is not None:
                self.update_timezone   = self.module.get_bin_path('tzdata-update', required=True)
            # else:
            #   self.update_timezone   = 'cp ...' <- configured above
            self.conf_files['name']    = '/etc/sysconfig/clock'
            self.conf_files['hwclock'] = '/etc/sysconfig/clock'
            self.regexps['name']       = re.compile(r'^ZONE\s*=\s*"?([^"\s]+)"?', re.MULTILINE)
            self.tzline_format         = 'ZONE="%s"\n'
        self.update_hwclock  = self.module.get_bin_path('hwclock', required=True)

    def _edit_file(self, filename, regexp, value):
        """Replace the first matched line with given `value`.

        If `regexp` matched more than once, other than the first line will be deleted.

        Args:
            filename: The name of the file to edit.
            regexp:   The regular expression to search with.
            value:    The line which will be inserted.
        """
        # Read the file
        try:
            file = open(filename, 'r')
        except IOError:
            self.abort('cannot read "%s"' % filename)
        else:
            lines = file.readlines()
            file.close()
        # Find the all matched lines
        matched_indices = []
        for i, line in enumerate(lines):
            if regexp.search(line):
                matched_indices.append(i)
        if len(matched_indices) > 0:
            insert_line = matched_indices[0]
        else:
            insert_line = 0
        # Remove all matched lines
        for i in matched_indices[::-1]:
            del lines[i]
        # ...and insert the value
        lines.insert(insert_line, value)
        # Write the changes
        try:
            file = open(filename, 'w')
        except IOError:
            self.abort('cannot write to "%s"' % filename)
        else:
            file.writelines(lines)
            file.close()
        self.msg.append('Added 1 line and deleted %s line(s) on %s' % (len(matched_indices), filename))

    def get(self, key, phase):
        if key == 'hwclock' and os.path.isfile('/etc/adjtime'):
            # If /etc/adjtime exists, use that file.
            key = 'adjtime'

        filename = self.conf_files[key]

        try:
            file = open(filename, mode='r')
        except IOError:
            self.abort('cannot read configuration file "%s" for %s' % (filename, key))
        else:
            status = file.read()
            file.close()
            try:
                value = self.regexps[key].search(status).group(1)
            except AttributeError:
                self.abort('cannot find the valid value from configuration file "%s" for %s' % (filename, key))
            else:
                if key == 'hwclock':
                    # For key='hwclock'; convert yes/no -> UTC/local
                    if self.module.boolean(value):
                        value = 'UTC'
                    else:
                        value = 'local'
                elif key == 'adjtime':
                    # For key='adjtime'; convert LOCAL -> local
                    if value != 'UTC':
                        value = value.lower()
                return value

    def set_timezone(self, value):
        self._edit_file(filename=self.conf_files['name'],
                        regexp=self.regexps['name'],
                        value=self.tzline_format % value)
        self.execute(self.update_timezone)

    def set_hwclock(self, value):
        if value == 'local':
            option = '--localtime'
        else:
            option = '--utc'
        self.execute(self.update_hwclock, '--systohc', option, log=True)

    def set(self, key, value):
        if key == 'name':
            self.set_timezone(value)
        elif key == 'hwclock':
            self.set_hwclock(value)
        else:
            self.abort('unknown parameter "%s"' % key)


def main():
    # Construct 'module' and 'tz'
    arg_spec = dict(
        hwclock=dict(choices=['UTC', 'local'], aliases=['rtc']),
        name   =dict(),
    )
    module = AnsibleModule(
        argument_spec=arg_spec,
        required_one_of=[arg_spec.keys()],
        supports_check_mode=True
    )
    tz = Timezone(module)

    # Check the current state
    tz.check(phase='before')
    if module.check_mode:
        diff = tz.diff('before', 'planned')
        # In check mode, 'planned' state is treated as 'after' state
        diff['after'] = diff.pop('planned')
    else:
        # Make change
        tz.change()
        # Check the current state
        tz.check(phase='after')
        # Examine if the current state matches planned state
        (after, planned) = tz.diff('after', 'planned').values()
        if after != planned:
            tz.abort('still not desired state, though changes have made')
        diff = tz.diff('before', 'after')

    changed = (diff['before'] != diff['after'])
    if len(tz.msg) > 0:
        module.exit_json(changed=changed, diff=diff, msg='\n'.join(tz.msg))
    else:
        module.exit_json(changed=changed, diff=diff)


if __name__ == '__main__':
    main()
