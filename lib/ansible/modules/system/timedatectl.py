#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2018, Susant Sahani <susant@redhat.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['stableinterface'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: timedatectl
short_description: Automates timedatectl
description:
    - Allows you to configure timedated.
version_added: "2.8"
options:
    time:
           description:
               - Set the system clock to the specified time.
    timezone:
           description:
               - Set the system time zone to the specified value
    ntp:
           description:
               - A boolean. This enables and starts, or disables and stops the systemd-timesyncd.service unit
    local_rtc:
           description:
               - A boolean. If "yes", the system is configured to maintain the RTC in universal time. If "no",
                 it will maintain the RTC in local time.

author: "Susant Sahani (@ssahani) <susant@redhat.com>"
'''

EXAMPLES = '''
# Set time
- timedatectl:
       time: "2018-10-03 21:25:16"
- timedatectl:
       ntp: yes
'''

RETURN = r'''
'''

from ansible.module_utils.basic import get_platform, AnsibleModule


class TimedatectlModule(object):

    def __init__(self, module):
        self.module = module
        self.args = self.module.params
        self.bin_path = module.get_bin_path('timedatectl', required=True)
        self.time = module.params['time']
        self.timezone = module.params['timezone']
        self.ntp = module.params['ntp']
        self.local_rtc = module.params['local_rtc']
        self.changed = False

    def bool_to_str(self, value):
        if value:
            return "yes"
        else:
            return "no"

    def configure_timedated(self):
        rc = False

        if self.time:
            command = "%s set-time %s" % (self.bin_path, self.time)
        if self.timezone:
            command = "%s set-timezone %s" % (self.bin_path, self.timezone)
        if self.ntp:
            command = "%s set-ntp %s" % (self.bin_path, self.bool_to_str(self.ntp))
        if self.local_rtc:
            command = "%s set-local-rtc %s" % (self.bin_path, self.bool_to_str(self.local_rtc))

        rc, out, err = self.module.run_command(command)
        if rc != 0:
            self.module.fail_json(msg='Failed to configure timedated %s: %s' % (self.command, out + err))

        self.changed = rc
        return rc


def main():
    module = AnsibleModule(
        argument_spec=dict(
            time=dict(required=False, type=str),
            timezone=dict(required=False, type=str),
            ntp=dict(required=False, type=bool),
            local_rtc=dict(required=False, type=bool),
        ),
        supports_check_mode=False
    )

    time = module.params['time']
    timezone = module.params['timezone']
    ntp = module.params['ntp']
    local_rtc = module.params['local_rtc']

    timedatectl = TimedatectlModule(module)
    result = timedatectl.configure_timedated()

    module.exit_json(changed=result)


if __name__ == '__main__':
    main()
