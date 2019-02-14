#!/usr/bin/python

# (c) 2018, NetApp, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = """
---
module: netapp_e_asup
short_description: NetApp E-Series manage auto-support settings
description:
    - Allow the auto-support settings to be configured for an individual E-Series storage-system
version_added: '2.7'
author: Michael Price (@lmprice)
extends_documentation_fragment:
    - netapp.eseries
options:
    state:
        description:
            - Enable/disable the E-Series auto-support configuration.
            - When this option is enabled, configuration, logs, and other support-related information will be relayed
              to NetApp to help better support your system. No personally identifiable information, passwords, etc, will
              be collected.
        default: enabled
        choices:
            - enabled
            - disabled
        aliases:
            - asup
            - auto_support
            - autosupport
    active:
        description:
            - Enable active/proactive monitoring for ASUP. When a problem is detected by our monitoring systems, it's
              possible that the bundle did not contain all of the required information at the time of the event.
              Enabling this option allows NetApp support personnel to manually request transmission or re-transmission
              of support data in order ot resolve the problem.
            - Only applicable if I(state=enabled).
        default: yes
        type: bool
    start:
        description:
            - A start hour may be specified in a range from 0 to 23 hours.
            - ASUP bundles will be sent daily between the provided start and end time (UTC).
            - I(start) must be less than I(end).
        aliases:
            - start_time
        default: 0
    end:
        description:
            - An end hour may be specified in a range from 1 to 24 hours.
            - ASUP bundles will be sent daily between the provided start and end time (UTC).
            - I(start) must be less than I(end).
        aliases:
            - end_time
        default: 24
    days:
        description:
            - A list of days of the week that ASUP bundles will be sent. A larger, weekly bundle will be sent on one
              of the provided days.
        choices:
            - monday
            - tuesday
            - wednesday
            - thursday
            - friday
            - saturday
            - sunday
        required: no
        aliases:
            - days_of_week
            - schedule_days
    verbose:
        description:
            - Provide the full ASUP configuration in the return.
        default: no
        required: no
        type: bool
    log_path:
        description:
            - A local path to a file to be used for debug logging
        required: no
notes:
    - Check mode is supported.
    - Enabling ASUP will allow our support teams to monitor the logs of the storage-system in order to proactively
      respond to issues with the system. It is recommended that all ASUP-related options be enabled, but they may be
      disabled if desired.
    - This API is currently only supported with the Embedded Web Services API v2.0 and higher.
"""

EXAMPLES = """
    - name: Enable ASUP and allow pro-active retrieval of bundles
      netapp_e_asup:
        state: enabled
        active: yes
        api_url: "10.1.1.1:8443"
        api_username: "admin"
        api_password: "myPass"

    - name: Set the ASUP schedule to only send bundles from 12 AM CST to 3 AM CST.
      netapp_e_asup:
        start: 17
        end: 20
        api_url: "10.1.1.1:8443"
        api_username: "admin"
        api_password: "myPass"
"""

RETURN = """
msg:
    description: Success message
    returned: on success
    type: str
    sample: The settings have been updated.
asup:
    description:
        - True if ASUP is enabled.
    returned: on success
    sample: True
    type: bool
active:
    description:
        - True if the active option has been enabled.
    returned: on success
    sample: True
    type: bool
cfg:
    description:
        - Provide the full ASUP configuration.
    returned: on success when I(verbose=true).
    type: complex
    contains:
        asupEnabled:
            description:
                    - True if ASUP has been enabled.
            type: bool
        onDemandEnabled:
            description:
                    - True if ASUP active monitoring has been enabled.
            type: bool
        daysOfWeek:
            description:
                - The days of the week that ASUP bundles will be sent.
            type: list
"""

import json
import logging
from pprint import pformat

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.netapp import request, eseries_host_argument_spec
from ansible.module_utils._text import to_native

HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json",
}


class Asup(object):
    DAYS_OPTIONS = ['sunday', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday']

    def __init__(self):
        argument_spec = eseries_host_argument_spec()
        argument_spec.update(dict(
            state=dict(type='str', required=False, default='enabled', aliases=['asup', 'auto_support', 'autosupport'],
                       choices=['enabled', 'disabled']),
            active=dict(type='bool', required=False, default=True, ),
            days=dict(type='list', required=False, aliases=['schedule_days', 'days_of_week'],
                      choices=self.DAYS_OPTIONS),
            start=dict(type='int', required=False, default=0, aliases=['start_time']),
            end=dict(type='int', required=False, default=24, aliases=['end_time']),
            verbose=dict(type='bool', required=False, default=False),
            log_path=dict(type='str', required=False),
        ))

        self.module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True, )
        args = self.module.params
        self.asup = args['state'] == 'enabled'
        self.active = args['active']
        self.days = args['days']
        self.start = args['start']
        self.end = args['end']
        self.verbose = args['verbose']

        self.ssid = args['ssid']
        self.url = args['api_url']
        self.creds = dict(url_password=args['api_password'],
                          validate_certs=args['validate_certs'],
                          url_username=args['api_username'], )

        self.check_mode = self.module.check_mode

        log_path = args['log_path']

        # logging setup
        self._logger = logging.getLogger(self.__class__.__name__)

        if log_path:
            logging.basicConfig(
                level=logging.DEBUG, filename=log_path, filemode='w',
                format='%(relativeCreated)dms %(levelname)s %(module)s.%(funcName)s:%(lineno)d\n %(message)s')

        if not self.url.endswith('/'):
            self.url += '/'

        if self.start >= self.end:
            self.module.fail_json(msg="The value provided for the start time is invalid."
                                      " It must be less than the end time.")
        if self.start < 0 or self.start > 23:
            self.module.fail_json(msg="The value provided for the start time is invalid. It must be between 0 and 23.")
        else:
            self.start = self.start * 60
        if self.end < 1 or self.end > 24:
            self.module.fail_json(msg="The value provided for the end time is invalid. It must be between 1 and 24.")
        else:
            self.end = min(self.end * 60, 1439)

        if not self.days:
            self.days = self.DAYS_OPTIONS

    def get_configuration(self):
        try:
            (rc, result) = request(self.url + 'device-asup', headers=HEADERS, **self.creds)

            if not (result['asupCapable'] and result['onDemandCapable']):
                self.module.fail_json(msg="ASUP is not supported on this device. Array Id [%s]." % (self.ssid))
            return result

        except Exception as err:
            self.module.fail_json(msg="Failed to retrieve ASUP configuration! Array Id [%s]. Error [%s]."
                                      % (self.ssid, to_native(err)))

    def update_configuration(self):
        config = self.get_configuration()
        update = False
        body = dict()

        if self.asup:
            body = dict(asupEnabled=True)
            if not config['asupEnabled']:
                update = True

            if (config['onDemandEnabled'] and config['remoteDiagsEnabled']) != self.active:
                update = True
                body.update(dict(onDemandEnabled=self.active,
                                 remoteDiagsEnabled=self.active))
            self.days.sort()
            config['schedule']['daysOfWeek'].sort()

            body['schedule'] = dict(daysOfWeek=self.days,
                                    dailyMinTime=self.start,
                                    dailyMaxTime=self.end,
                                    weeklyMinTime=self.start,
                                    weeklyMaxTime=self.end)

            if self.days != config['schedule']['daysOfWeek']:
                update = True
            if self.start != config['schedule']['dailyMinTime'] or self.start != config['schedule']['weeklyMinTime']:
                update = True
            elif self.end != config['schedule']['dailyMaxTime'] or self.end != config['schedule']['weeklyMaxTime']:
                update = True

        elif config['asupEnabled']:
            body = dict(asupEnabled=False)
            update = True

        self._logger.info(pformat(body))

        if update and not self.check_mode:
            try:
                (rc, result) = request(self.url + 'device-asup', method='POST',
                                       data=json.dumps(body), headers=HEADERS, **self.creds)
            # This is going to catch cases like a connection failure
            except Exception as err:
                self.module.fail_json(msg="We failed to set the storage-system name! Array Id [%s]. Error [%s]."
                                          % (self.ssid, to_native(err)))

        return update

    def update(self):
        update = self.update_configuration()
        cfg = self.get_configuration()
        if self.verbose:
            self.module.exit_json(msg="The ASUP settings have been updated.", changed=update,
                                  asup=cfg['asupEnabled'], active=cfg['onDemandEnabled'], cfg=cfg)
        else:
            self.module.exit_json(msg="The ASUP settings have been updated.", changed=update,
                                  asup=cfg['asupEnabled'], active=cfg['onDemandEnabled'])

    def __call__(self, *args, **kwargs):
        self.update()


def main():
    settings = Asup()
    settings()


if __name__ == '__main__':
    main()
