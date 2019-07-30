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
module: netapp_e_global
short_description: NetApp E-Series manage global settings configuration
description:
    - Allow the user to configure several of the global settings associated with an E-Series storage-system
version_added: '2.7'
author: Michael Price (@lmprice)
extends_documentation_fragment:
    - netapp.eseries
options:
    name:
        description:
            - Set the name of the E-Series storage-system
            - This label/name doesn't have to be unique.
            - May be up to 30 characters in length.
        aliases:
            - label
    log_path:
        description:
            - A local path to a file to be used for debug logging
        required: no
notes:
    - Check mode is supported.
    - This module requires Web Services API v1.3 or newer.
"""

EXAMPLES = """
    - name: Set the storage-system name
      netapp_e_global:
        name: myArrayName
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
name:
    description:
        - The current name/label of the storage-system.
    returned: on success
    sample: myArrayName
    type: str
"""
import json
import logging

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.netapp import request, eseries_host_argument_spec
from ansible.module_utils._text import to_native

HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json",
}


class GlobalSettings(object):
    def __init__(self):
        argument_spec = eseries_host_argument_spec()
        argument_spec.update(dict(
            name=dict(type='str', required=False, aliases=['label']),
            log_path=dict(type='str', required=False),
        ))

        self.module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True, )
        args = self.module.params
        self.name = args['name']

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

        if self.name and len(self.name) > 30:
            self.module.fail_json(msg="The provided name is invalid, it must be < 30 characters in length.")

    def get_name(self):
        try:
            (rc, result) = request(self.url + 'storage-systems/%s' % self.ssid, headers=HEADERS, **self.creds)
            if result['status'] in ['offline', 'neverContacted']:
                self.module.fail_json(msg="This storage-system is offline! Array Id [%s]." % (self.ssid))
            return result['name']
        except Exception as err:
            self.module.fail_json(msg="Connection failure! Array Id [%s]. Error [%s]." % (self.ssid, to_native(err)))

    def update_name(self):
        name = self.get_name()
        update = False
        if self.name != name:
            update = True

        body = dict(name=self.name)

        if update and not self.check_mode:
            try:
                (rc, result) = request(self.url + 'storage-systems/%s/configuration' % self.ssid, method='POST',
                                       data=json.dumps(body), headers=HEADERS, **self.creds)
                self._logger.info("Set name to %s.", result['name'])
            # This is going to catch cases like a connection failure
            except Exception as err:
                self.module.fail_json(
                    msg="We failed to set the storage-system name! Array Id [%s]. Error [%s]."
                        % (self.ssid, to_native(err)))
        return update

    def update(self):
        update = self.update_name()
        name = self.get_name()

        self.module.exit_json(msg="The requested settings have been updated.", changed=update, name=name)

    def __call__(self, *args, **kwargs):
        self.update()


def main():
    settings = GlobalSettings()
    settings()


if __name__ == '__main__':
    main()
