#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2016, Shinichi TAMURA (@tmshn)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: timezone
short_description: Configure timezone setting
description:
  - This module configures the timezone setting, both of the system clock and of the hardware clock. If you want to set up the NTP, use M(service) module.
  - It is recommended to restart C(crond) after changing the timezone, otherwise the jobs may run at the wrong time.
  - Several different tools are used depending on the OS/Distribution involved.
    For Linux it can use C(timedatectl)  or edit C(/etc/sysconfig/clock) or C(/etc/timezone) andC(hwclock).
    On SmartOS , C(sm-set-timezone), for BSD, C(/etc/localtime) is modified.
  - As of version 2.3 support was added for SmartOS and BSDs.
  - Windows, AIX and HPUX are not supported, please let us know if you find any other OS/distro in which this fails.
version_added: "2.2"
options:
  name:
    description:
      - Name of the timezone for the system clock.
        Default is to keep current setting. B(At least one of name and
        hwclock are required.)
    required: false
  hwclock:
    description:
      - Whether the hardware clock is in UTC or in local timezone.
        Default is to keep current setting.
        Note that this option is recommended not to change and may fail
        to configure, especially on virtual environments such as AWS.
        B(At least one of name and hwclock are required.)
        I(Only used on Linux.)
    required: false
    aliases: ['rtc']
notes:
  - On SmartOS the C(sm-set-timezone) utility (part of the smtools package) is required to set the zone timezone
author:
  - "Shinichi TAMURA (@tmshn)"
  - "Jasper Lievisse Adriaanse (@jasperla)"
'''

RETURN = '''
diff:
  description: The differences about the given arguments.
  returned: success
  type: complex
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
  timezone:
    name: Asia/Tokyo
'''

import os
import platform
import random
import re
import string

from ansible.module_utils.basic import AnsibleModule, get_platform
from ansible.module_utils.six import iteritems


class Timezone(object):
    """This is a generic Timezone manipulation class that is subclassed based on platform.

    A subclass may wish to override the following action methods:
        - get(key, phase)   ... get the value from the system at `phase`
        - set(key, value)   ... set the value to the current system
    """

    def __new__(cls, module):
        """Return the platform-specific subclass.

        It does not use load_platform_subclass() because it needs to judge based
        on whether the `timedatectl` command exists and is available.

        Args:
            module: The AnsibleModule.
        """
        if get_platform() == 'Linux':
            timedatectl = module.get_bin_path('timedatectl')
            if timedatectl is not None and module.run_command(timedatectl)[0] == 0:
                return super(Timezone, SystemdTimezone).__new__(SystemdTimezone)
            else:
                return super(Timezone, NosystemdTimezone).__new__(NosystemdTimezone)
        elif re.match('^joyent_.*Z', platform.version()):
            # get_platform() returns SunOS, which is too broad. So look at the
            # platform version instead. However we have to ensure that we're not
            # running in the global zone where changing the timezone has no effect.
            zonename_cmd = module.get_bin_path('zonename')
            if zonename_cmd is not None:
                (rc, stdout, _ ) = module.run_command(zonename_cmd)
                if rc == 0 and stdout.strip() == 'global':
                    module.fail_json(msg='Adjusting timezone is not supported in Global Zone')

            return super(Timezone, SmartOSTimezone).__new__(SmartOSTimezone)
        elif re.match('^(Free|Net|Open)BSD', platform.platform()):
            return super(Timezone, BSDTimezone).__new__(BSDTimezone)
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
        return tzfile


class SystemdTimezone(Timezone):
    """This is a Timezone manipulation class for systemd-powered Linux.

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
            tzfile = self._verify_timezone()
            self.update_timezone  = self.module.get_bin_path('cp', required=True)
            self.update_timezone += ' %s /etc/localtime' % tzfile
        self.update_hwclock = self.module.get_bin_path('hwclock', required=True)
        # Distribution-specific configurations
        if self.module.get_bin_path('dpkg-reconfigure') is not None:
            # Debian/Ubuntu
            self.update_timezone       = self.module.get_bin_path('dpkg-reconfigure', required=True)
            self.update_timezone      += ' --frontend noninteractive tzdata'
            self.conf_files['name']    = '/etc/timezone'
            self.conf_files['hwclock'] = '/etc/default/rcS'
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


class SmartOSTimezone(Timezone):
    """This is a Timezone manipulation class for SmartOS instances.

    It uses the C(sm-set-timezone) utility to set the timezone, and
    inspects C(/etc/default/init) to determine the current timezone.

    NB: A zone needs to be rebooted in order for the change to be
    activated.
    """

    def __init__(self, module):
        super(SmartOSTimezone, self).__init__(module)
        self.settimezone = self.module.get_bin_path('sm-set-timezone', required=False)
        if not self.settimezone:
            module.fail_json(msg='sm-set-timezone not found. Make sure the smtools package is installed.')

    def get(self, key, phase):
        """Lookup the current timezone name in `/etc/default/init`. If anything else
        is requested, or if the TZ field is not set we fail.
        """
        if key == 'name':
            try:
                f = open('/etc/default/init', 'r')
                for line in f:
                    m = re.match('^TZ=(.*)$', line.strip())
                    if m:
                        return m.groups()[0]
            except:
                self.module.fail_json(msg='Failed to read /etc/default/init')
        else:
            self.module.fail_json(msg='{0} is not a supported option on target platform'.format(key))

    def set(self, key, value):
        """Set the requested timezone through sm-set-timezone, an invalid timezone name
        will be rejected and we have no further input validation to perform.
        """
        if key == 'name':
            cmd = 'sm-set-timezone {0}'.format(value)

            (rc, stdout, stderr) = self.module.run_command(cmd)

            if rc != 0:
                self.module.fail_json(msg=stderr)

            # sm-set-timezone knows no state and will always set the timezone.
            # XXX: https://github.com/joyent/smtools/pull/2
            m = re.match('^\* Changed (to)? timezone (to)? ({0}).*'.format(value), stdout.splitlines()[1])
            if not (m and m.groups()[-1] == value):
                self.module.fail_json(msg='Failed to set timezone')
        else:
            self.module.fail_json(msg='{0} is not a supported option on target platform'.
                                  format(key))


class BSDTimezone(Timezone):
    """This is the timezone implementation for *BSD which works simply through
    updating the `/etc/localtime` symlink to point to a valid timezone name under
    `/usr/share/zoneinfo`.
    """

    def __init__(self, module):
        super(BSDTimezone, self).__init__(module)

    def get(self, key, phase):
        """Lookup the current timezone by resolving `/etc/localtime`."""
        if key == 'name':
            try:
                tz = os.readlink('/etc/localtime')
                return tz.replace('/usr/share/zoneinfo/', '')
            except:
                self.module.warn('Could not read /etc/localtime. Assuming UTC')
                return 'UTC'
        else:
            self.module.fail_json(msg='{0} is not a supported option on target platform'.
                                  format(key))

    def set(self, key, value):
        if key == 'name':
            # First determine if the requested timezone is valid by looking in
            # the zoneinfo directory.
            zonefile = '/usr/share/zoneinfo/' + value
            try:
                if not os.path.isfile(zonefile):
                    self.module.fail_json(msg='{0} is not a recognized timezone'.format(value))
            except:
                self.module.fail_json(msg='Failed to stat {0}'.format(zonefile))

            # Now (somewhat) atomically update the symlink by creating a new
            # symlink and move it into place. Otherwise we have to remove the
            # original symlink and create the new symlink, however that would
            # create a race condition in case another process tries to read
            # /etc/localtime between removal and creation.
            suffix = "".join([random.choice(string.ascii_letters + string.digits) for x in range(0, 10)])
            new_localtime = '/etc/localtime.' + suffix

            try:
                os.symlink(zonefile, new_localtime)
                os.rename(new_localtime, '/etc/localtime')
            except:
                os.remove(new_localtime)
                self.module.fail_json(msg='Could not update /etc/localtime')
        else:
            self.module.fail_json(msg='{0} is not a supported option on target platform'.format(key))


def main():
    # Construct 'module' and 'tz'
    module = AnsibleModule(
        argument_spec=dict(
            hwclock=dict(choices=['UTC', 'local'], aliases=['rtc']),
            name=dict(),
        ),
        required_one_of=[['hwclock', 'name']],
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
