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
module: systemd_timer
short_description: automates systemd.timer configuration.
description:
    - Allows you to generate systemd.timer configuration files.
version_added: "2.8"
options:
    conf_path:
        description:
            - Specifies the path where to write the configuration files.
        default: "/var/run/systemd/system"
        choices: [ "/usr/lib/systemd/system", "/var/run/systemd/system", "/etc/systemd/system" ]
    file_name:
        description:
            - This configuration file name where the configurations will be written. Note the file name will be
              automatically have the extension .timer.
    description:
        description:
            - Specifies the descrition of the unit.
    on_active_sec:
        description:
            - Defines a timer relative to the moment the timer itself is activated.
    on_boot_sec:
        description:
            - Defines a timer relative to when the machine was booted up.
    on_startup_sec:
        description:
            - Defines a defines a timer relative to when systemd was first started.
    on_unit_active_sec:
        description:
            - Defines a timer relative to when the unit the timer is activating was last activated.
    on_unit_inactive_sec:
        description:
            - Defines a timer relative to when the unit the timer is activating was last deactivated.
    on_calendar:
        description:
            - Defines realtime timers with calendar event expressions. See systemd.time(7) for
              more information on the syntax of calendar event expressions.
    unit:
        description:
            - The unit to activate when this timer elapses.
    action:
        description:
            - Whether configuration files should be added or removed.
        choices: [ "create", "remove" ]
author: "Susant Sahani (@ssahani) <susant@redhat.com>"
'''

EXAMPLES = '''
# Create calender timer
- systemd_timer:
       file_name=timer-test
       description="Example timer"
       on_calendar=daily
       action=create
# Remove config file
- systemd_timer:
       file_name: timer-test
       action: remove
'''

RETURN = r'''
'''

import os
from ansible.module_utils.basic import get_platform, AnsibleModule


UNIT_PATH_SYSTEMD = '/usr/lib/systemd/system'
UNIT_PATH_SYSTEMD_SYSTEM = '/etc/systemd/system'
UNIT_PATH_SYSTEMD_RUN = '/var/run/systemd/system'


class SystemdTimer(object):

    def __init__(self, module):
        self.module = module
        self.args = self.module.params
        self.conf_path = module.params['conf_path']
        self.file_name = module.params['file_name']
        self.description = module.params['description']
        self.on_active_sec = module.params['on_active_sec']
        self.on_boot_sec = module.params['on_boot_sec']
        self.on_startup_sec = module.params['on_startup_sec']
        self.on_unit_active_sec = module.params['on_unit_active_sec']
        self.on_unit_inactive_sec = module.params['on_unit_inactive_sec']
        self.on_calendar = module.params['on_calendar']
        self.unit = module.params['unit']
        self.action = module.params['action']
        self.changed = False

    def remove_files(self):
        paths = [UNIT_PATH_SYSTEMD_RUN, UNIT_PATH_SYSTEMD_SYSTEM, UNIT_PATH_SYSTEMD]

        list_conf_files = self.file_name.split(' ')
        for conf_file in list_conf_files:
            for path in paths:
                conf_file += '.timer'
                if os.path.exists(os.path.join(path, conf_file)):
                    os.remove(os.path.join(path, conf_file))
                    rc = True

        return rc

    def write_configs_to_file(self, conf):
        rc = False

        if not os.path.exists(self.conf_path):
            os.makedirs(self.conf_path, exist_ok=True)

        self.file_name += '.timer'
        with open(os.path.join(self.conf_path, self.file_name), "w") as f:
                f.write(conf + '\n')
                rc = True

        return rc

    def create_config_timer_unit(self):
        conf = "[Unit]\nDescription={0}\n\n[Timer]\n".format(self.description)

        if self.on_active_sec:
            conf += "OnActiveSec={0}\n".format(self.on_active_sec)
        if self.on_boot_sec:
            conf += "OnBootSec={0}\n".format(self.on_boot_sec)
        if self.on_startup_sec:
            conf += " OnStartupSec={0}\n".format(self.on_active_sec)
        if self.on_unit_active_sec:
            conf += "OnUnitActiveSec={0}\n".format(self.on_unit_active_sec)
        if self.on_unit_inactive_sec:
            conf += "OnUnitInactiveSec={0}\n".format(self.on_unit_inactive_sec)
        if self.on_calendar:
            conf += "OnCalendar={0}\n".format(self.on_calendar)
        if self.unit:
            conf += "Unit={0}\n".format(self.unit)

        conf += "\n[Install]\nWantedBy=timers.target\n"

        return self.write_configs_to_file(conf)

    def configure_systemd_timer(self):
        rc = False

        if self.action == 'create':
            rc = self.create_config_timer_unit()
        elif self.action == 'remove':
            rc = self.remove_files()

        return rc


def main():
    module = AnsibleModule(
        argument_spec=dict(
            conf_path=dict(default=UNIT_PATH_SYSTEMD_RUN, type='str',
                           choices=[UNIT_PATH_SYSTEMD, UNIT_PATH_SYSTEMD_RUN, UNIT_PATH_SYSTEMD_SYSTEM]),
            file_name=dict(default=None, type='str'),
            description=dict(default=None, type='str'),
            on_active_sec=dict(required=False, default=None, type='str'),
            on_boot_sec=dict(required=False, default=None, type='str'),
            on_startup_sec=dict(required=False, default=None, type='str'),
            on_unit_active_sec=dict(required=False, default=None, type='str'),
            on_unit_inactive_sec=dict(required=False, default=None, type='str'),
            on_calendar=dict(required=False, default=None, type='str'),
            unit=dict(required=False, default=None, type='str'),
            action=dict(choices=['create', 'remove'], required=True),
        ),
        supports_check_mode=True
    )

    conf_path = module.params['conf_path']
    file_name = module.params['file_name']
    description = module.params['description']
    on_active_sec = module.params['on_active_sec']
    on_boot_sec = module.params['on_boot_sec']
    on_startup_sec = module.params['on_startup_sec']
    on_unit_active_sec = module.params['on_unit_active_sec']
    on_unit_inactive_sec = module.params['on_unit_inactive_sec']
    on_calendar = module.params['on_calendar']
    action = module.params['action']

    if file_name is None:
        module.fail_json(msg='file_name cannot be None')

    timer = SystemdTimer(module)
    result = timer.configure_systemd_timer()

    module.exit_json(changed=result)


if __name__ == '__main__':
    main()
