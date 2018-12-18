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
module: netapp_e_iscsi_interface
short_description: NetApp E-Series manage iSCSI interface configuration
description:
    - Configure settings of an E-Series iSCSI interface
version_added: '2.7'
author: Michael Price (@lmprice)
extends_documentation_fragment:
    - netapp.eseries
options:
    controller:
        description:
            - The controller that owns the port you want to configure.
            - Controller names are presented alphabetically, with the first controller as A,
             the second as B, and so on.
            - Current hardware models have either 1 or 2 available controllers, but that is not a guaranteed hard
             limitation and could change in the future.
        required: yes
        choices:
            - A
            - B
    name:
        description:
            - The channel of the port to modify the configuration of.
            - The list of choices is not necessarily comprehensive. It depends on the number of ports
              that are available in the system.
            - The numerical value represents the number of the channel (typically from left to right on the HIC),
              beginning with a value of 1.
        required: yes
        aliases:
            - channel
    state:
        description:
            - When enabled, the provided configuration will be utilized.
            - When disabled, the IPv4 configuration will be cleared and IPv4 connectivity disabled.
        choices:
            - enabled
            - disabled
        default: enabled
    address:
        description:
            - The IPv4 address to assign to the interface.
            - Should be specified in xx.xx.xx.xx form.
            - Mutually exclusive with I(config_method=dhcp)
    subnet_mask:
        description:
            - The subnet mask to utilize for the interface.
            - Should be specified in xx.xx.xx.xx form.
            - Mutually exclusive with I(config_method=dhcp)
    gateway:
        description:
            - The IPv4 gateway address to utilize for the interface.
            - Should be specified in xx.xx.xx.xx form.
            - Mutually exclusive with I(config_method=dhcp)
    config_method:
        description:
            - The configuration method type to use for this interface.
            - dhcp is mutually exclusive with I(address), I(subnet_mask), and I(gateway).
        choices:
            - dhcp
            - static
        default: dhcp
    mtu:
        description:
            - The maximum transmission units (MTU), in bytes.
            - This allows you to configure a larger value for the MTU, in order to enable jumbo frames
              (any value > 1500).
            - Generally, it is necessary to have your host, switches, and other components not only support jumbo
              frames, but also have it configured properly. Therefore, unless you know what you're doing, it's best to
              leave this at the default.
        default: 1500
        aliases:
            - max_frame_size
    log_path:
        description:
            - A local path to a file to be used for debug logging
        required: no
notes:
    - Check mode is supported.
    - The interface settings are applied synchronously, but changes to the interface itself (receiving a new IP address
      via dhcp, etc), can take seconds or minutes longer to take effect.
    - This module will not be useful/usable on an E-Series system without any iSCSI interfaces.
    - This module requires a Web Services API version of >= 1.3.
"""

EXAMPLES = """
    - name: Configure the first port on the A controller with a static IPv4 address
      netapp_e_iscsi_interface:
        name: "1"
        controller: "A"
        config_method: static
        address: "192.168.1.100"
        subnet_mask: "255.255.255.0"
        gateway: "192.168.1.1"
        ssid: "1"
        api_url: "10.1.1.1:8443"
        api_username: "admin"
        api_password: "myPass"

    - name: Disable ipv4 connectivity for the second port on the B controller
      netapp_e_iscsi_interface:
        name: "2"
        controller: "B"
        state: disabled
        ssid: "{{ ssid }}"
        api_url: "{{ netapp_api_url }}"
        api_username: "{{ netapp_api_username }}"
        api_password: "{{ netapp_api_password }}"

    - name: Enable jumbo frames for the first 4 ports on controller A
      netapp_e_iscsi_interface:
        name: "{{ item | int }}"
        controller: "A"
        state: enabled
        mtu: 9000
        config_method: dhcp
        ssid: "{{ ssid }}"
        api_url: "{{ netapp_api_url }}"
        api_username: "{{ netapp_api_username }}"
        api_password: "{{ netapp_api_password }}"
      loop:
        - 1
        - 2
        - 3
        - 4
"""

RETURN = """
msg:
    description: Success message
    returned: on success
    type: str
    sample: The interface settings have been updated.
enabled:
    description:
        - Indicates whether IPv4 connectivity has been enabled or disabled.
        - This does not necessarily indicate connectivity. If dhcp was enabled without a dhcp server, for instance,
          it is unlikely that the configuration will actually be valid.
    returned: on success
    sample: True
    type: bool
"""
import json
import logging
from pprint import pformat
import re

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.netapp import request, eseries_host_argument_spec
from ansible.module_utils._text import to_native

HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json",
}


class IscsiInterface(object):
    def __init__(self):
        argument_spec = eseries_host_argument_spec()
        argument_spec.update(dict(
            controller=dict(type='str', required=True, choices=['A', 'B']),
            name=dict(type='int', aliases=['channel']),
            state=dict(type='str', required=False, default='enabled', choices=['enabled', 'disabled']),
            address=dict(type='str', required=False),
            subnet_mask=dict(type='str', required=False),
            gateway=dict(type='str', required=False),
            config_method=dict(type='str', required=False, default='dhcp', choices=['dhcp', 'static']),
            mtu=dict(type='int', default=1500, required=False, aliases=['max_frame_size']),
            log_path=dict(type='str', required=False),
        ))

        required_if = [
            ["config_method", "static", ["address", "subnet_mask"]],
        ]

        self.module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True, required_if=required_if, )
        args = self.module.params
        self.controller = args['controller']
        self.name = args['name']
        self.mtu = args['mtu']
        self.state = args['state']
        self.address = args['address']
        self.subnet_mask = args['subnet_mask']
        self.gateway = args['gateway']
        self.config_method = args['config_method']

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

        if self.mtu < 1500 or self.mtu > 9000:
            self.module.fail_json(msg="The provided mtu is invalid, it must be > 1500 and < 9000 bytes.")

        if self.config_method == 'dhcp' and any([self.address, self.subnet_mask, self.gateway]):
            self.module.fail_json(msg='A config_method of dhcp is mutually exclusive with the address,'
                                      ' subnet_mask, and gateway options.')

        # A relatively primitive regex to validate that the input is formatted like a valid ip address
        address_regex = re.compile(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}')

        if self.address and not address_regex.match(self.address):
            self.module.fail_json(msg="An invalid ip address was provided for address.")

        if self.subnet_mask and not address_regex.match(self.subnet_mask):
            self.module.fail_json(msg="An invalid ip address was provided for subnet_mask.")

        if self.gateway and not address_regex.match(self.gateway):
            self.module.fail_json(msg="An invalid ip address was provided for gateway.")

    @property
    def interfaces(self):
        ifaces = list()
        try:
            (rc, ifaces) = request(self.url + 'storage-systems/%s/graph/xpath-filter?query=/controller/hostInterfaces'
                                   % self.ssid, headers=HEADERS, **self.creds)
        except Exception as err:
            self.module.fail_json(
                msg="Failed to retrieve defined host interfaces. Array Id [%s]. Error [%s]."
                    % (self.ssid, to_native(err)))

        # Filter out non-iSCSI interfaces
        ifaces = [iface['iscsi'] for iface in ifaces if iface['interfaceType'] == 'iscsi']

        return ifaces

    def get_controllers(self):
        """Retrieve a mapping of controller labels to their references
        {
            'A': '070000000000000000000001',
            'B': '070000000000000000000002',
        }
        :return: the controllers defined on the system
        """
        controllers = list()
        try:
            (rc, controllers) = request(self.url + 'storage-systems/%s/graph/xpath-filter?query=/controller/id'
                                        % self.ssid, headers=HEADERS, **self.creds)
        except Exception as err:
            self.module.fail_json(
                msg="Failed to retrieve controller list! Array Id [%s]. Error [%s]."
                    % (self.ssid, to_native(err)))

        controllers.sort()

        controllers_dict = {}
        i = ord('A')
        for controller in controllers:
            label = chr(i)
            controllers_dict[label] = controller
            i += 1

        return controllers_dict

    def fetch_target_interface(self):
        interfaces = self.interfaces

        for iface in interfaces:
            if iface['channel'] == self.name and self.controllers[self.controller] == iface['controllerId']:
                return iface

        channels = sorted(set((str(iface['channel'])) for iface in interfaces
                              if self.controllers[self.controller] == iface['controllerId']))

        self.module.fail_json(msg="The requested channel of %s is not valid. Valid channels include: %s."
                                  % (self.name, ", ".join(channels)))

    def make_update_body(self, target_iface):
        body = dict(iscsiInterface=target_iface['id'])
        update_required = False

        self._logger.info("Requested state=%s.", self.state)
        self._logger.info("config_method: current=%s, requested=%s",
                          target_iface['ipv4Data']['ipv4AddressConfigMethod'], self.config_method)

        if self.state == 'enabled':
            settings = dict()
            if not target_iface['ipv4Enabled']:
                update_required = True
                settings['ipv4Enabled'] = [True]
            if self.mtu != target_iface['interfaceData']['ethernetData']['maximumFramePayloadSize']:
                update_required = True
                settings['maximumFramePayloadSize'] = [self.mtu]
            if self.config_method == 'static':
                ipv4Data = target_iface['ipv4Data']['ipv4AddressData']

                if ipv4Data['ipv4Address'] != self.address:
                    update_required = True
                    settings['ipv4Address'] = [self.address]
                if ipv4Data['ipv4SubnetMask'] != self.subnet_mask:
                    update_required = True
                    settings['ipv4SubnetMask'] = [self.subnet_mask]
                if self.gateway is not None and ipv4Data['ipv4GatewayAddress'] != self.gateway:
                    update_required = True
                    settings['ipv4GatewayAddress'] = [self.gateway]

                if target_iface['ipv4Data']['ipv4AddressConfigMethod'] != 'configStatic':
                    update_required = True
                    settings['ipv4AddressConfigMethod'] = ['configStatic']

            elif (target_iface['ipv4Data']['ipv4AddressConfigMethod'] != 'configDhcp'):
                update_required = True
                settings.update(dict(ipv4Enabled=[True],
                                     ipv4AddressConfigMethod=['configDhcp']))
            body['settings'] = settings

        else:
            if target_iface['ipv4Enabled']:
                update_required = True
                body['settings'] = dict(ipv4Enabled=[False])

        self._logger.info("Update required ?=%s", update_required)
        self._logger.info("Update body: %s", pformat(body))

        return update_required, body

    def update(self):
        self.controllers = self.get_controllers()
        if self.controller not in self.controllers:
            self.module.fail_json(msg="The provided controller name is invalid. Valid controllers: %s."
                                      % ", ".join(self.controllers.keys()))

        iface_before = self.fetch_target_interface()
        update_required, body = self.make_update_body(iface_before)
        if update_required and not self.check_mode:
            try:
                url = (self.url +
                       'storage-systems/%s/symbol/setIscsiInterfaceProperties' % self.ssid)
                (rc, result) = request(url, method='POST', data=json.dumps(body), headers=HEADERS, timeout=300,
                                       ignore_errors=True, **self.creds)
                # We could potentially retry this a few times, but it's probably a rare enough case (unless a playbook
                #  is cancelled mid-flight), that it isn't worth the complexity.
                if rc == 422 and result['retcode'] in ['busy', '3']:
                    self.module.fail_json(
                        msg="The interface is currently busy (probably processing a previously requested modification"
                            " request). This operation cannot currently be completed. Array Id [%s]. Error [%s]."
                            % (self.ssid, result))
                # Handle authentication issues, etc.
                elif rc != 200:
                    self.module.fail_json(
                        msg="Failed to modify the interface! Array Id [%s]. Error [%s]."
                            % (self.ssid, to_native(result)))
                self._logger.debug("Update request completed successfully.")
            # This is going to catch cases like a connection failure
            except Exception as err:
                self.module.fail_json(
                    msg="Connection failure: we failed to modify the interface! Array Id [%s]. Error [%s]."
                        % (self.ssid, to_native(err)))

        iface_after = self.fetch_target_interface()

        self.module.exit_json(msg="The interface settings have been updated.", changed=update_required,
                              enabled=iface_after['ipv4Enabled'])

    def __call__(self, *args, **kwargs):
        self.update()


def main():
    iface = IscsiInterface()
    iface()


if __name__ == '__main__':
    main()
