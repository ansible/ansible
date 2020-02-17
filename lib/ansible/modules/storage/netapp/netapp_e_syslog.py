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
module: netapp_e_syslog
short_description: NetApp E-Series manage syslog settings
description:
    - Allow the syslog settings to be configured for an individual E-Series storage-system
version_added: '2.7'
author: Nathan Swartz (@ndswartz)
extends_documentation_fragment:
    - netapp.eseries
options:
    state:
        description:
            - Add or remove the syslog server configuration for E-Series storage array.
            - Existing syslog server configuration will be removed or updated when its address matches I(address).
            - Fully qualified hostname that resolve to an IPv4 address that matches I(address) will not be
              treated as a match.
        choices:
            - present
            - absent
        default: present
    address:
        description:
            - The syslog server's IPv4 address or a fully qualified hostname.
            - All existing syslog configurations will be removed when I(state=absent) and I(address=None).
    port:
        description:
            - This is the port the syslog server is using.
        default: 514
    protocol:
        description:
            - This is the transmission protocol the syslog server's using to receive syslog messages.
        choices:
            - udp
            - tcp
            - tls
        default: udp
    components:
        description:
            - The e-series logging components define the specific logs to transfer to the syslog server.
            - At the time of writing, 'auditLog' is the only logging component but more may become available.
        default: ["auditLog"]
    test:
        description:
            - This forces a test syslog message to be sent to the stated syslog server.
            - Only attempts transmission when I(state=present).
        type: bool
        default: no
    log_path:
        description:
            - This argument specifies a local path for logging purposes.
        required: no
notes:
    - Check mode is supported.
    - This API is currently only supported with the Embedded Web Services API v2.12 (bundled with
      SANtricity OS 11.40.2) and higher.
"""

EXAMPLES = """
    - name: Add two syslog server configurations to NetApp E-Series storage array.
      netapp_e_syslog:
        state: present
        address: "{{ item }}"
        port: 514
        protocol: tcp
        component: "auditLog"
        api_url: "10.1.1.1:8443"
        api_username: "admin"
        api_password: "myPass"
      loop:
        - "192.168.1.1"
        - "192.168.1.100"
"""

RETURN = """
msg:
    description: Success message
    returned: on success
    type: str
    sample: The settings have been updated.
syslog:
    description:
        - True if syslog server configuration has been added to e-series storage array.
    returned: on success
    sample: True
    type: bool
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


class Syslog(object):
    def __init__(self):
        argument_spec = eseries_host_argument_spec()
        argument_spec.update(dict(
            state=dict(choices=["present", "absent"], required=False, default="present"),
            address=dict(type="str", required=False),
            port=dict(type="int", default=514, required=False),
            protocol=dict(choices=["tcp", "tls", "udp"], default="udp", required=False),
            components=dict(type="list", required=False, default=["auditLog"]),
            test=dict(type="bool", default=False, required=False),
            log_path=dict(type="str", required=False),
        ))

        required_if = [
            ["state", "present", ["address", "port", "protocol", "components"]],
        ]

        mutually_exclusive = [
            ["test", "absent"],
        ]

        self.module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True, required_if=required_if,
                                    mutually_exclusive=mutually_exclusive)
        args = self.module.params

        self.syslog = args["state"] in ["present"]
        self.address = args["address"]
        self.port = args["port"]
        self.protocol = args["protocol"]
        self.components = args["components"]
        self.test = args["test"]
        self.ssid = args["ssid"]
        self.url = args["api_url"]
        self.creds = dict(url_password=args["api_password"],
                          validate_certs=args["validate_certs"],
                          url_username=args["api_username"], )

        self.components.sort()

        self.check_mode = self.module.check_mode

        # logging setup
        log_path = args["log_path"]
        self._logger = logging.getLogger(self.__class__.__name__)
        if log_path:
            logging.basicConfig(
                level=logging.DEBUG, filename=log_path, filemode='w',
                format='%(relativeCreated)dms %(levelname)s %(module)s.%(funcName)s:%(lineno)d\n %(message)s')

        if not self.url.endswith('/'):
            self.url += '/'

    def get_configuration(self):
        """Retrieve existing syslog configuration."""
        try:
            (rc, result) = request(self.url + "storage-systems/{0}/syslog".format(self.ssid),
                                   headers=HEADERS, **self.creds)
            return result
        except Exception as err:
            self.module.fail_json(msg="Failed to retrieve syslog configuration! Array Id [%s]. Error [%s]."
                                      % (self.ssid, to_native(err)))

    def test_configuration(self, body):
        """Send test syslog message to the storage array.

        Allows fix number of retries to occur before failure is issued to give the storage array time to create
        new syslog server record.
        """
        try:
            (rc, result) = request(self.url + "storage-systems/{0}/syslog/{1}/test".format(self.ssid, body["id"]),
                                   method='POST', headers=HEADERS, **self.creds)
        except Exception as err:
            self.module.fail_json(
                msg="We failed to send test message! Array Id [{0}]. Error [{1}].".format(self.ssid, to_native(err)))

    def update_configuration(self):
        """Post the syslog request to array."""
        config_match = None
        perfect_match = None
        update = False
        body = dict()

        # search existing configuration for syslog server entry match
        configs = self.get_configuration()
        if self.address:
            for config in configs:
                if config["serverAddress"] == self.address:
                    config_match = config
                    if (config["port"] == self.port and config["protocol"] == self.protocol and
                            len(config["components"]) == len(self.components) and
                            all([component["type"] in self.components for component in config["components"]])):
                        perfect_match = config_match
                        break

        # generate body for the http request
        if self.syslog:
            if not perfect_match:
                update = True
                if config_match:
                    body.update(dict(id=config_match["id"]))
                components = [dict(type=component_type) for component_type in self.components]
                body.update(dict(serverAddress=self.address, port=self.port,
                                 protocol=self.protocol, components=components))
                self._logger.info(body)
                self.make_configuration_request(body)

        # remove specific syslog server configuration
        elif self.address:
            update = True
            body.update(dict(id=config_match["id"]))
            self._logger.info(body)
            self.make_configuration_request(body)

        # if no address is specified, remove all syslog server configurations
        elif configs:
            update = True
            for config in configs:
                body.update(dict(id=config["id"]))
                self._logger.info(body)
                self.make_configuration_request(body)

        return update

    def make_configuration_request(self, body):
        # make http request(s)
        if not self.check_mode:
            try:
                if self.syslog:
                    if "id" in body:
                        (rc, result) = request(
                            self.url + "storage-systems/{0}/syslog/{1}".format(self.ssid, body["id"]),
                            method='POST', data=json.dumps(body), headers=HEADERS, **self.creds)
                    else:
                        (rc, result) = request(self.url + "storage-systems/{0}/syslog".format(self.ssid),
                                               method='POST', data=json.dumps(body), headers=HEADERS, **self.creds)
                        body.update(result)

                    # send syslog test message
                    if self.test:
                        self.test_configuration(body)

                elif "id" in body:
                    (rc, result) = request(self.url + "storage-systems/{0}/syslog/{1}".format(self.ssid, body["id"]),
                                           method='DELETE', headers=HEADERS, **self.creds)

            # This is going to catch cases like a connection failure
            except Exception as err:
                self.module.fail_json(msg="We failed to modify syslog configuration! Array Id [%s]. Error [%s]."
                                          % (self.ssid, to_native(err)))

    def update(self):
        """Update configuration and respond to ansible."""
        update = self.update_configuration()
        self.module.exit_json(msg="The syslog settings have been updated.", changed=update)

    def __call__(self, *args, **kwargs):
        self.update()


def main():
    settings = Syslog()
    settings()


if __name__ == "__main__":
    main()
