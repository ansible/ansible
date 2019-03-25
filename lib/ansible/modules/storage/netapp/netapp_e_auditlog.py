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
module: netapp_e_auditlog
short_description: NetApp E-Series manage audit-log configuration
description:
    - This module allows an e-series storage system owner to set audit-log configuration parameters.
version_added: '2.7'
author: Nathan Swartz (@ndswartz)
extends_documentation_fragment:
    - netapp.eseries
options:
    max_records:
        description:
            - The maximum number log messages audit-log will retain.
            - Max records must be between and including 100 and 50000.
        default: 50000
    log_level:
        description: Filters the log messages according to the specified log level selection.
        choices:
            - all
            - writeOnly
        default: writeOnly
    full_policy:
        description: Specifies what audit-log should do once the number of entries approach the record limit.
        choices:
            - overWrite
            - preventSystemAccess
        default: overWrite
    threshold:
        description:
            - This is the memory full percent threshold that audit-log will start issuing warning messages.
            - Percent range must be between and including 60 and 90.
        default: 90
    force:
        description:
            - Forces the audit-log configuration to delete log history when log messages fullness cause immediate
              warning or full condition.
            - Warning! This will cause any existing audit-log messages to be deleted.
            - This is only applicable for I(full_policy=preventSystemAccess).
        type: bool
        default: no
    log_path:
        description: A local path to a file to be used for debug logging.
        required: no
notes:
    - Check mode is supported.
    - This module is currently only supported with the Embedded Web Services API v3.0 and higher.
"""

EXAMPLES = """
- name: Define audit-log to prevent system access if records exceed 50000 with warnings occurring at 60% capacity.
  netapp_e_auditlog:
     api_url: "https://{{ netapp_e_api_host }}/devmgr/v2"
     api_username: "{{ netapp_e_api_username }}"
     api_password: "{{ netapp_e_api_password }}"
     ssid: "{{ netapp_e_ssid }}"
     validate_certs: no
     max_records: 50000
     log_level: all
     full_policy: preventSystemAccess
     threshold: 60
     log_path: /path/to/log_file.log
- name: Define audit-log utilize the default values.
  netapp_e_auditlog:
     api_url: "https://{{ netapp_e_api_host }}/devmgr/v2"
     api_username: "{{ netapp_e_api_username }}"
     api_password: "{{ netapp_e_api_password }}"
     ssid: "{{ netapp_e_ssid }}"
- name: Force audit-log configuration when full or warning conditions occur while enacting preventSystemAccess policy.
  netapp_e_auditlog:
     api_url: "https://{{ netapp_e_api_host }}/devmgr/v2"
     api_username: "{{ netapp_e_api_username }}"
     api_password: "{{ netapp_e_api_password }}"
     ssid: "{{ netapp_e_ssid }}"
     max_records: 5000
     log_level: all
     full_policy: preventSystemAccess
     threshold: 60
     force: yes
"""

RETURN = """
msg:
    description: Success message
    returned: on success
    type: str
    sample: The settings have been updated.
"""

import json
import logging
from pprint import pformat

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.netapp import request, eseries_host_argument_spec
from ansible.module_utils._text import to_native

try:
    from urlparse import urlparse, urlunparse
except Exception:
    from urllib.parse import urlparse, urlunparse


class AuditLog(object):
    """Audit-log module configuration class."""
    MAX_RECORDS = 50000
    HEADERS = {"Content-Type": "application/json",
               "Accept": "application/json"}

    def __init__(self):
        argument_spec = eseries_host_argument_spec()
        argument_spec.update(dict(
            max_records=dict(type="int", default=50000),
            log_level=dict(type="str", default="writeOnly", choices=["all", "writeOnly"]),
            full_policy=dict(type="str", default="overWrite", choices=["overWrite", "preventSystemAccess"]),
            threshold=dict(type="int", default=90),
            force=dict(type="bool", default=False),
            log_path=dict(type='str', required=False)))

        self.module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True)
        args = self.module.params

        self.max_records = args["max_records"]
        if self.max_records < 100 or self.max_records > self.MAX_RECORDS:
            self.module.fail_json(msg="Audit-log max_records count must be between 100 and 50000: [%s]"
                                      % self.max_records)
        self.threshold = args["threshold"]
        if self.threshold < 60 or self.threshold > 90:
            self.module.fail_json(msg="Audit-log percent threshold must be between 60 and 90: [%s]" % self.threshold)
        self.log_level = args["log_level"]
        self.full_policy = args["full_policy"]
        self.force = args["force"]
        self.ssid = args['ssid']
        self.url = args['api_url']
        if not self.url.endswith('/'):
            self.url += '/'
        self.creds = dict(url_password=args['api_password'],
                          validate_certs=args['validate_certs'],
                          url_username=args['api_username'], )

        # logging setup
        log_path = args['log_path']
        self._logger = logging.getLogger(self.__class__.__name__)

        if log_path:
            logging.basicConfig(
                level=logging.DEBUG, filename=log_path, filemode='w',
                format='%(relativeCreated)dms %(levelname)s %(module)s.%(funcName)s:%(lineno)d\n %(message)s')

        self.proxy_used = self.is_proxy()
        self._logger.info(self.proxy_used)
        self.check_mode = self.module.check_mode

    def is_proxy(self):
        """Determine whether the API is embedded or proxy."""
        try:

            # replace http url path with devmgr/utils/about
            about_url = list(urlparse(self.url))
            about_url[2] = "devmgr/utils/about"
            about_url = urlunparse(about_url)

            rc, data = request(about_url, timeout=300, headers=self.HEADERS, **self.creds)

            return data["runningAsProxy"]
        except Exception as err:
            self.module.fail_json(msg="Failed to retrieve the webservices about information! Array Id [%s]. Error [%s]."
                                      % (self.ssid, to_native(err)))

    def get_configuration(self):
        """Retrieve the existing audit-log configurations.

        :returns: dictionary containing current audit-log configuration
        """
        try:
            if self.proxy_used:
                rc, data = request(self.url + "audit-log/config", timeout=300, headers=self.HEADERS, **self.creds)
            else:
                rc, data = request(self.url + "storage-systems/%s/audit-log/config" % self.ssid,
                                   timeout=300, headers=self.HEADERS, **self.creds)
            return data
        except Exception as err:
            self.module.fail_json(msg="Failed to retrieve the audit-log configuration! "
                                      "Array Id [%s]. Error [%s]."
                                      % (self.ssid, to_native(err)))

    def build_configuration(self):
        """Build audit-log expected configuration.

        :returns: Tuple containing update boolean value and dictionary of audit-log configuration
        """
        config = self.get_configuration()

        current = dict(auditLogMaxRecords=config["auditLogMaxRecords"],
                       auditLogLevel=config["auditLogLevel"],
                       auditLogFullPolicy=config["auditLogFullPolicy"],
                       auditLogWarningThresholdPct=config["auditLogWarningThresholdPct"])

        body = dict(auditLogMaxRecords=self.max_records,
                    auditLogLevel=self.log_level,
                    auditLogFullPolicy=self.full_policy,
                    auditLogWarningThresholdPct=self.threshold)

        update = current != body

        self._logger.info(pformat(update))
        self._logger.info(pformat(body))
        return update, body

    def delete_log_messages(self):
        """Delete all audit-log messages."""
        self._logger.info("Deleting audit-log messages...")
        try:
            if self.proxy_used:
                rc, result = request(self.url + "audit-log?clearAll=True", timeout=300,
                                     method="DELETE", headers=self.HEADERS, **self.creds)
            else:
                rc, result = request(self.url + "storage-systems/%s/audit-log?clearAll=True" % self.ssid, timeout=300,
                                     method="DELETE", headers=self.HEADERS, **self.creds)
        except Exception as err:
            self.module.fail_json(msg="Failed to delete audit-log messages! Array Id [%s]. Error [%s]."
                                  % (self.ssid, to_native(err)))

    def update_configuration(self, update=None, body=None, attempt_recovery=True):
        """Update audit-log configuration."""
        if update is None or body is None:
            update, body = self.build_configuration()

        if update and not self.check_mode:
            try:
                if self.proxy_used:
                    rc, result = request(self.url + "storage-systems/audit-log/config", timeout=300,
                                         data=json.dumps(body), method='POST', headers=self.HEADERS,
                                         ignore_errors=True, **self.creds)
                else:
                    rc, result = request(self.url + "storage-systems/%s/audit-log/config" % self.ssid, timeout=300,
                                         data=json.dumps(body), method='POST', headers=self.HEADERS,
                                         ignore_errors=True, **self.creds)

                if rc == 422:
                    if self.force and attempt_recovery:
                        self.delete_log_messages()
                        update = self.update_configuration(update, body, False)
                    else:
                        self.module.fail_json(msg="Failed to update audit-log configuration! Array Id [%s]. Error [%s]."
                                              % (self.ssid, to_native(rc, result)))

            except Exception as error:
                self.module.fail_json(msg="Failed to update audit-log configuration! Array Id [%s]. Error [%s]."
                                      % (self.ssid, to_native(error)))
        return update

    def update(self):
        """Update the audit-log configuration."""
        update = self.update_configuration()
        self.module.exit_json(msg="Audit-log update complete", changed=update)

    def __call__(self):
        self.update()


def main():
    auditlog = AuditLog()
    auditlog()


if __name__ == "__main__":
    main()
