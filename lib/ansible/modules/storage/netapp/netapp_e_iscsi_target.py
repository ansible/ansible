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
module: netapp_e_iscsi_target
short_description: NetApp E-Series manage iSCSI target configuration
description:
    - Configure the settings of an E-Series iSCSI target
version_added: '2.7'
author: Michael Price (@lmprice)
extends_documentation_fragment:
    - netapp.eseries
options:
    name:
        description:
            - The name/alias to assign to the iSCSI target.
            - This alias is often used by the initiator software in order to make an iSCSI target easier to identify.
        aliases:
            - alias
    ping:
        description:
            - Enable ICMP ping responses from the configured iSCSI ports.
        type: bool
        default: yes
    chap_secret:
        description:
            - Enable Challenge-Handshake Authentication Protocol (CHAP), utilizing this value as the password.
            - When this value is specified, we will always trigger an update (changed=True). We have no way of verifying
              whether or not the password has changed.
            - The chap secret may only use ascii characters with values between 32 and 126 decimal.
            - The chap secret must be no less than 12 characters, but no more than 16 characters in length.
        aliases:
            - chap
            - password
    unnamed_discovery:
        description:
            - When an initiator initiates a discovery session to an initiator port, it is considered an unnamed
              discovery session if the iSCSI target iqn is not specified in the request.
            - This option may be disabled to increase security if desired.
        type: bool
        default: yes
    log_path:
        description:
            - A local path (on the Ansible controller), to a file to be used for debug logging.
        required: no
notes:
    - Check mode is supported.
    - Some of the settings are dependent on the settings applied to the iSCSI interfaces. These can be configured using
      M(netapp_e_iscsi_interface).
    - This module requires a Web Services API version of >= 1.3.
"""

EXAMPLES = """
    - name: Enable ping responses and unnamed discovery sessions for all iSCSI ports
      netapp_e_iscsi_target:
        api_url: "https://localhost:8443/devmgr/v2"
        api_username: admin
        api_password: myPassword
        ssid: "1"
        validate_certs: no
        name: myTarget
        ping: yes
        unnamed_discovery: yes

    - name: Set the target alias and the CHAP secret
      netapp_e_iscsi_target:
        ssid: "{{ ssid }}"
        api_url: "{{ netapp_api_url }}"
        api_username: "{{ netapp_api_username }}"
        api_password: "{{ netapp_api_password }}"
        name: myTarget
        chap: password1234
"""

RETURN = """
msg:
    description: Success message
    returned: on success
    type: str
    sample: The iSCSI target settings have been updated.
alias:
    description:
        - The alias assigned to the iSCSI target.
    returned: on success
    sample: myArray
    type: str
iqn:
    description:
        - The iqn (iSCSI Qualified Name), assigned to the iSCSI target.
    returned: on success
    sample: iqn.1992-08.com.netapp:2800.000a132000b006d2000000005a0e8f45
    type: str
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


class IscsiTarget(object):
    def __init__(self):
        argument_spec = eseries_host_argument_spec()
        argument_spec.update(dict(
            name=dict(type='str', required=False, aliases=['alias']),
            ping=dict(type='bool', required=False, default=True),
            chap_secret=dict(type='str', required=False, aliases=['chap', 'password'], no_log=True),
            unnamed_discovery=dict(type='bool', required=False, default=True),
            log_path=dict(type='str', required=False),
        ))

        self.module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True, )
        args = self.module.params

        self.name = args['name']
        self.ping = args['ping']
        self.chap_secret = args['chap_secret']
        self.unnamed_discovery = args['unnamed_discovery']

        self.ssid = args['ssid']
        self.url = args['api_url']
        self.creds = dict(url_password=args['api_password'],
                          validate_certs=args['validate_certs'],
                          url_username=args['api_username'], )

        self.check_mode = self.module.check_mode
        self.post_body = dict()
        self.controllers = list()

        log_path = args['log_path']

        # logging setup
        self._logger = logging.getLogger(self.__class__.__name__)

        if log_path:
            logging.basicConfig(
                level=logging.DEBUG, filename=log_path, filemode='w',
                format='%(relativeCreated)dms %(levelname)s %(module)s.%(funcName)s:%(lineno)d\n %(message)s')

        if not self.url.endswith('/'):
            self.url += '/'

        if self.chap_secret is not None:
            if len(self.chap_secret) < 12 or len(self.chap_secret) > 16:
                self.module.fail_json(msg="The provided CHAP secret is not valid, it must be between 12 and 16"
                                          " characters in length.")

            for c in self.chap_secret:
                ordinal = ord(c)
                if ordinal < 32 or ordinal > 126:
                    self.module.fail_json(msg="The provided CHAP secret is not valid, it may only utilize ascii"
                                              " characters with decimal values between 32 and 126.")

    @property
    def target(self):
        """Provide information on the iSCSI Target configuration

        Sample:
        {
          'alias': 'myCustomName',
          'ping': True,
          'unnamed_discovery': True,
          'chap': False,
          'iqn': 'iqn.1992-08.com.netapp:2800.000a132000b006d2000000005a0e8f45',
        }
        """
        target = dict()
        try:
            (rc, data) = request(self.url + 'storage-systems/%s/graph/xpath-filter?query=/storagePoolBundle/target'
                                 % self.ssid, headers=HEADERS, **self.creds)
            # This likely isn't an iSCSI-enabled system
            if not data:
                self.module.fail_json(
                    msg="This storage-system doesn't appear to have iSCSI interfaces. Array Id [%s]." % (self.ssid))

            data = data[0]

            chap = any(
                [auth for auth in data['configuredAuthMethods']['authMethodData'] if auth['authMethod'] == 'chap'])

            target.update(dict(alias=data['alias']['iscsiAlias'],
                               iqn=data['nodeName']['iscsiNodeName'],
                               chap=chap))

            (rc, data) = request(self.url + 'storage-systems/%s/graph/xpath-filter?query=/sa/iscsiEntityData'
                                 % self.ssid, headers=HEADERS, **self.creds)

            data = data[0]
            target.update(dict(ping=data['icmpPingResponseEnabled'],
                               unnamed_discovery=data['unnamedDiscoverySessionsEnabled']))

        except Exception as err:
            self.module.fail_json(
                msg="Failed to retrieve the iSCSI target information. Array Id [%s]. Error [%s]."
                    % (self.ssid, to_native(err)))

        return target

    def apply_iscsi_settings(self):
        """Update the iSCSI target alias and CHAP settings"""
        update = False
        target = self.target

        body = dict()

        if self.name is not None and self.name != target['alias']:
            update = True
            body['alias'] = self.name

        # If the CHAP secret was provided, we trigger an update.
        if self.chap_secret is not None:
            update = True
            body.update(dict(enableChapAuthentication=True,
                             chapSecret=self.chap_secret))
        # If no secret was provided, then we disable chap
        elif target['chap']:
            update = True
            body.update(dict(enableChapAuthentication=False))

        if update and not self.check_mode:
            try:
                request(self.url + 'storage-systems/%s/iscsi/target-settings' % self.ssid, method='POST',
                        data=json.dumps(body), headers=HEADERS, **self.creds)
            except Exception as err:
                self.module.fail_json(
                    msg="Failed to update the iSCSI target settings. Array Id [%s]. Error [%s]."
                        % (self.ssid, to_native(err)))

        return update

    def apply_target_changes(self):
        update = False
        target = self.target

        body = dict()

        if self.ping != target['ping']:
            update = True
            body['icmpPingResponseEnabled'] = self.ping

        if self.unnamed_discovery != target['unnamed_discovery']:
            update = True
            body['unnamedDiscoverySessionsEnabled'] = self.unnamed_discovery

        self._logger.info(pformat(body))
        if update and not self.check_mode:
            try:
                request(self.url + 'storage-systems/%s/iscsi/entity' % self.ssid, method='POST',
                        data=json.dumps(body), timeout=60, headers=HEADERS, **self.creds)
            except Exception as err:
                self.module.fail_json(
                    msg="Failed to update the iSCSI target settings. Array Id [%s]. Error [%s]."
                        % (self.ssid, to_native(err)))
        return update

    def update(self):
        update = self.apply_iscsi_settings()
        update = self.apply_target_changes() or update

        target = self.target
        data = dict((key, target[key]) for key in target if key in ['iqn', 'alias'])

        self.module.exit_json(msg="The interface settings have been updated.", changed=update, **data)

    def __call__(self, *args, **kwargs):
        self.update()


def main():
    iface = IscsiTarget()
    iface()


if __name__ == '__main__':
    main()
