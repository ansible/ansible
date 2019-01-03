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
module: netapp_e_mgmt_interface
short_description: NetApp E-Series management interface configuration
description:
    - Configure the E-Series management interfaces
version_added: '2.7'
author:
    - Michael Price (@lmprice)
    - Nathan Swartz (@ndswartz)
extends_documentation_fragment:
    - netapp.eseries
options:
    state:
        description:
            - Enable or disable IPv4 network interface configuration.
            - Either IPv4 or IPv6 must be enabled otherwise error will occur.
            - Only required when enabling or disabling IPv4 network interface
        choices:
            - enable
            - disable
        required: no
        aliases:
            - enable_interface
    controller:
        description:
            - The controller that owns the port you want to configure.
            - Controller names are represented alphabetically, with the first controller as A,
             the second as B, and so on.
            - Current hardware models have either 1 or 2 available controllers, but that is not a guaranteed hard
             limitation and could change in the future.
        required: yes
        choices:
            - A
            - B
    name:
        description:
            - The port to modify the configuration for.
            - The list of choices is not necessarily comprehensive. It depends on the number of ports
              that are present in the system.
            - The name represents the port number (typically from left to right on the controller),
              beginning with a value of 1.
            - Mutually exclusive with I(channel).
        aliases:
            - port
            - iface
    channel:
        description:
            - The port to modify the configuration for.
            - The channel represents the port number (typically from left to right on the controller),
              beginning with a value of 1.
            - Mutually exclusive with I(name).
    address:
        description:
            - The IPv4 address to assign to the interface.
            - Should be specified in xx.xx.xx.xx form.
            - Mutually exclusive with I(config_method=dhcp)
        required: no
    subnet_mask:
        description:
            - The subnet mask to utilize for the interface.
            - Should be specified in xx.xx.xx.xx form.
            - Mutually exclusive with I(config_method=dhcp)
        required: no
    gateway:
        description:
            - The IPv4 gateway address to utilize for the interface.
            - Should be specified in xx.xx.xx.xx form.
            - Mutually exclusive with I(config_method=dhcp)
        required: no
    config_method:
        description:
            - The configuration method type to use for network interface ports.
            - dhcp is mutually exclusive with I(address), I(subnet_mask), and I(gateway).
        choices:
            - dhcp
            - static
        required: no
    dns_config_method:
        description:
            - The configuration method type to use for DNS services.
            - dhcp is mutually exclusive with I(dns_address), and I(dns_address_backup).
        choices:
            - dhcp
            - static
        required: no
    dns_address:
        description:
            - Primary IPv4 DNS server address
        required: no
    dns_address_backup:
        description:
            - Backup IPv4 DNS server address
            - Queried when primary DNS server fails
        required: no
    ntp_config_method:
        description:
            - The configuration method type to use for NTP services.
            - disable is mutually exclusive with I(ntp_address) and I(ntp_address_backup).
            - dhcp is mutually exclusive with I(ntp_address) and I(ntp_address_backup).
        choices:
            - disable
            - dhcp
            - static
        required: no
    ntp_address:
        description:
            - Primary IPv4 NTP server address
        required: no
    ntp_address_backup:
        description:
            - Backup IPv4 NTP server address
            - Queried when primary NTP server fails
        required: no
    ssh:
        type: bool
        description:
            - Enable ssh access to the controller for debug purposes.
            - This is a controller-level setting.
            - rlogin/telnet will be enabled for ancient equipment where ssh is not available.
        required: no
    log_path:
        description:
            - A local path to a file to be used for debug logging
        required: no
notes:
    - Check mode is supported.
    - The interface settings are applied synchronously, but changes to the interface itself (receiving a new IP address
      via dhcp, etc), can take seconds or minutes longer to take effect.
    - "Known issue: Changes specifically to down ports will result in a failure. However, this may not be the case in up
      coming NetApp E-Series firmware releases (released after firmware version 11.40.2)."
"""

EXAMPLES = """
    - name: Configure the first port on the A controller with a static IPv4 address
      netapp_e_mgmt_interface:
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
      netapp_e_mgmt_interface:
        name: "2"
        controller: "B"
        enable_interface: no
        ssid: "{{ ssid }}"
        api_url: "{{ netapp_api_url }}"
        api_username: "{{ netapp_api_username }}"
        api_password: "{{ netapp_api_password }}"

    - name: Enable ssh access for ports one and two on controller A
      netapp_e_mgmt_interface:
        name: "{{ item }}"
        controller: "A"
        ssh: yes
        ssid: "{{ ssid }}"
        api_url: "{{ netapp_api_url }}"
        api_username: "{{ netapp_api_username }}"
        api_password: "{{ netapp_api_password }}"
      loop:
        - 1
        - 2

    - name: Configure static DNS settings for the first port on controller A
      netapp_e_mgmt_interface:
        name: "1"
        controller: "A"
        dns_config_method: static
        dns_address: "192.168.1.100"
        dns_address_backup: "192.168.1.1"
        ssid: "{{ ssid }}"
        api_url: "{{ netapp_api_url }}"
        api_username: "{{ netapp_api_username }}"
        api_password: "{{ netapp_api_password }}"

    - name: Configure static NTP settings for ports one and two on controller B
      netapp_e_mgmt_interface:
        name: "{{ item }}"
        controller: "B"
        ntp_config_method: static
        ntp_address: "129.100.1.100"
        ntp_address_backup: "127.100.1.1"
        ssid: "{{ ssid }}"
        api_url: "{{ netapp_api_url }}"
        api_username: "{{ netapp_api_username }}"
        api_password: "{{ netapp_api_password }}"
      loop:
        - 1
        - 2
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
        - This does not necessarily indicate connectivity. If dhcp was enabled absent a dhcp server, for instance,
          it is unlikely that the configuration will actually be valid.
    returned: on success
    sample: True
    type: bool
"""
import json
import logging
from pprint import pformat, pprint
import time
import socket

try:
    import urlparse
except ImportError:
    import urllib.parse as urlparse

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.netapp import request, eseries_host_argument_spec
from ansible.module_utils._text import to_native

HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json",
}


class MgmtInterface(object):
    MAX_RETRIES = 15

    def __init__(self):
        argument_spec = eseries_host_argument_spec()
        argument_spec.update(dict(
            state=dict(type="str", choices=["enable", "disable"],
                       aliases=["enable_interface"], required=False),
            controller=dict(type="str", required=True, choices=["A", "B"]),
            name=dict(type="str", aliases=["port", "iface"]),
            channel=dict(type="int"),
            address=dict(type="str", required=False),
            subnet_mask=dict(type="str", required=False),
            gateway=dict(type="str", required=False),
            config_method=dict(type="str", required=False, choices=["dhcp", "static"]),
            dns_config_method=dict(type="str", required=False, choices=["dhcp", "static"]),
            dns_address=dict(type="str", required=False),
            dns_address_backup=dict(type="str", required=False),
            ntp_config_method=dict(type="str", required=False, choices=["disable", "dhcp", "static"]),
            ntp_address=dict(type="str", required=False),
            ntp_address_backup=dict(type="str", required=False),
            ssh=dict(type="bool", required=False),
            log_path=dict(type="str", required=False),
        ))

        required_if = [
            ["state", "enable", ["config_method"]],
            ["config_method", "static", ["address", "subnet_mask"]],
            ["dns_config_method", "static", ["dns_address"]],
            ["ntp_config_method", "static", ["ntp_address"]],
        ]

        mutually_exclusive = [
            ["name", "channel"],
        ]

        self.module = AnsibleModule(argument_spec=argument_spec,
                                    supports_check_mode=True,
                                    required_if=required_if,
                                    mutually_exclusive=mutually_exclusive)
        args = self.module.params

        self.controller = args["controller"]
        self.name = args["name"]
        self.channel = args["channel"]

        self.config_method = args["config_method"]
        self.address = args["address"]
        self.subnet_mask = args["subnet_mask"]
        self.gateway = args["gateway"]
        self.enable_interface = None if args["state"] is None else args["state"] == "enable"

        self.dns_config_method = args["dns_config_method"]
        self.dns_address = args["dns_address"]
        self.dns_address_backup = args["dns_address_backup"]

        self.ntp_config_method = args["ntp_config_method"]
        self.ntp_address = args["ntp_address"]
        self.ntp_address_backup = args["ntp_address_backup"]

        self.ssh = args["ssh"]

        self.ssid = args["ssid"]
        self.url = args["api_url"]
        self.creds = dict(url_password=args["api_password"],
                          validate_certs=args["validate_certs"],
                          url_username=args["api_username"], )

        self.retries = 0

        self.check_mode = self.module.check_mode
        self.post_body = dict()

        log_path = args["log_path"]

        # logging setup
        self._logger = logging.getLogger(self.__class__.__name__)

        if log_path:
            logging.basicConfig(
                level=logging.DEBUG, filename=log_path, filemode='w',
                format='%(relativeCreated)dms %(levelname)s %(module)s.%(funcName)s:%(lineno)d\n %(message)s')

        if not self.url.endswith('/'):
            self.url += '/'

    @property
    def controllers(self):
        """Retrieve a mapping of controller labels to their references
        {
            'A': '070000000000000000000001',
            'B': '070000000000000000000002',
        }
        :return: the controllers defined on the system
        """
        try:
            (rc, controllers) = request(self.url + 'storage-systems/%s/controllers'
                                        % self.ssid, headers=HEADERS, **self.creds)
        except Exception as err:
            controllers = list()
            self.module.fail_json(
                msg="Failed to retrieve the controller settings. Array Id [%s]. Error [%s]."
                    % (self.ssid, to_native(err)))

        controllers.sort(key=lambda c: c['physicalLocation']['slot'])

        controllers_dict = dict()
        i = ord('A')
        for controller in controllers:
            label = chr(i)
            settings = dict(controllerSlot=controller['physicalLocation']['slot'],
                            controllerRef=controller['controllerRef'],
                            ssh=controller['networkSettings']['remoteAccessEnabled'])
            controllers_dict[label] = settings
            i += 1

        return controllers_dict

    @property
    def interface(self):
        net_interfaces = list()
        try:
            (rc, net_interfaces) = request(self.url + 'storage-systems/%s/configuration/ethernet-interfaces'
                                           % self.ssid, headers=HEADERS, **self.creds)
        except Exception as err:
            self.module.fail_json(
                msg="Failed to retrieve defined management interfaces. Array Id [%s]. Error [%s]."
                    % (self.ssid, to_native(err)))

        controllers = self.controllers
        controller = controllers[self.controller]

        net_interfaces = [iface for iface in net_interfaces if iface["controllerRef"] == controller["controllerRef"]]

        # Find the correct interface
        iface = None
        for net in net_interfaces:
            if self.name:
                if net["alias"] == self.name or net["interfaceName"] == self.name:
                    iface = net
                    break
            elif self.channel:
                if net["channel"] == self.channel:
                    iface = net
                    break

        if iface is None:
            identifier = self.name if self.name is not None else self.channel
            self.module.fail_json(msg="We could not find an interface matching [%s] on Array=[%s]."
                                      % (identifier, self.ssid))

        return dict(alias=iface["alias"],
                    channel=iface["channel"],
                    link_status=iface["linkStatus"],
                    enabled=iface["ipv4Enabled"],
                    address=iface["ipv4Address"],
                    gateway=iface["ipv4GatewayAddress"],
                    subnet_mask=iface["ipv4SubnetMask"],
                    dns_config_method=iface["dnsProperties"]["acquisitionProperties"]["dnsAcquisitionType"],
                    dns_servers=iface["dnsProperties"]["acquisitionProperties"]["dnsServers"],
                    ntp_config_method=iface["ntpProperties"]["acquisitionProperties"]["ntpAcquisitionType"],
                    ntp_servers=iface["ntpProperties"]["acquisitionProperties"]["ntpServers"],
                    config_method=iface["ipv4AddressConfigMethod"],
                    controllerRef=iface["controllerRef"],
                    controllerSlot=iface["controllerSlot"],
                    ipv6Enabled=iface["ipv6Enabled"],
                    id=iface["interfaceRef"], )

    def get_enable_interface_settings(self, iface, expected_iface, update, body):
        """Enable or disable the IPv4 network interface."""
        if self.enable_interface:
            if not iface["enabled"]:
                update = True
            body["ipv4Enabled"] = True
        else:
            if iface["enabled"]:
                update = True
            body["ipv4Enabled"] = False

        expected_iface["enabled"] = body["ipv4Enabled"]
        return update, expected_iface, body

    def get_interface_settings(self, iface, expected_iface, update, body):
        """Update network interface settings."""

        if self.config_method == "dhcp":
            if iface["config_method"] != "configDhcp":
                update = True
            body["ipv4AddressConfigMethod"] = "configDhcp"

        else:
            if iface["config_method"] != "configStatic":
                update = True
            body["ipv4AddressConfigMethod"] = "configStatic"

            if iface["address"] != self.address:
                update = True
            body["ipv4Address"] = self.address

            if iface["subnet_mask"] != self.subnet_mask:
                update = True
            body["ipv4SubnetMask"] = self.subnet_mask

            if self.gateway and iface["gateway"] != self.gateway:
                update = True
            body["ipv4GatewayAddress"] = self.gateway

            expected_iface["address"] = body["ipv4Address"]
            expected_iface["subnet_mask"] = body["ipv4SubnetMask"]
            expected_iface["gateway"] = body["ipv4GatewayAddress"]

        expected_iface["config_method"] = body["ipv4AddressConfigMethod"]

        return update, expected_iface, body

    def get_dns_server_settings(self, iface, expected_iface, update, body):
        """Add DNS server information to the request body."""
        if self.dns_config_method == "dhcp":
            if iface["dns_config_method"] != "dhcp":
                update = True
            body["dnsAcquisitionDescriptor"] = dict(dnsAcquisitionType="dhcp")

        elif self.dns_config_method == "static":
            dns_servers = [dict(addressType="ipv4", ipv4Address=self.dns_address)]
            if self.dns_address_backup:
                dns_servers.append(dict(addressType="ipv4", ipv4Address=self.dns_address_backup))

            body["dnsAcquisitionDescriptor"] = dict(dnsAcquisitionType="stat", dnsServers=dns_servers)

            if (iface["dns_config_method"] != "stat" or
                    len(iface["dns_servers"]) != len(dns_servers) or
                    (len(iface["dns_servers"]) == 2 and
                     (iface["dns_servers"][0]["ipv4Address"] != self.dns_address or
                      iface["dns_servers"][1]["ipv4Address"] != self.dns_address_backup)) or
                    (len(iface["dns_servers"]) == 1 and
                     iface["dns_servers"][0]["ipv4Address"] != self.dns_address)):
                update = True

            expected_iface["dns_servers"] = dns_servers

        expected_iface["dns_config_method"] = body["dnsAcquisitionDescriptor"]["dnsAcquisitionType"]
        return update, expected_iface, body

    def get_ntp_server_settings(self, iface, expected_iface, update, body):
        """Add NTP server information to the request body."""
        if self.ntp_config_method == "disable":
            if iface["ntp_config_method"] != "disabled":
                update = True
            body["ntpAcquisitionDescriptor"] = dict(ntpAcquisitionType="disabled")

        elif self.ntp_config_method == "dhcp":
            if iface["ntp_config_method"] != "dhcp":
                update = True
            body["ntpAcquisitionDescriptor"] = dict(ntpAcquisitionType="dhcp")

        elif self.ntp_config_method == "static":
            ntp_servers = [dict(addrType="ipvx", ipvxAddress=dict(addressType="ipv4", ipv4Address=self.ntp_address))]
            if self.ntp_address_backup:
                ntp_servers.append(dict(addrType="ipvx",
                                        ipvxAddress=dict(addressType="ipv4", ipv4Address=self.ntp_address_backup)))

            body["ntpAcquisitionDescriptor"] = dict(ntpAcquisitionType="stat", ntpServers=ntp_servers)

            if (iface["ntp_config_method"] != "stat" or
                    len(iface["ntp_servers"]) != len(ntp_servers) or
                    ((len(iface["ntp_servers"]) == 2 and
                      (iface["ntp_servers"][0]["ipvxAddress"]["ipv4Address"] != self.ntp_address or
                      iface["ntp_servers"][1]["ipvxAddress"]["ipv4Address"] != self.ntp_address_backup)) or
                     (len(iface["ntp_servers"]) == 1 and
                      iface["ntp_servers"][0]["ipvxAddress"]["ipv4Address"] != self.ntp_address))):
                update = True

            expected_iface["ntp_servers"] = ntp_servers

        expected_iface["ntp_config_method"] = body["ntpAcquisitionDescriptor"]["ntpAcquisitionType"]
        return update, expected_iface, body

    def get_remote_ssh_settings(self, settings, update, body):
        """Configure network interface ports for remote ssh access."""
        if self.ssh != settings["ssh"]:
            update = True

        body["enableRemoteAccess"] = self.ssh
        return update, body

    def update_array(self, settings, iface):
        """Update controller with new interface, dns service, ntp service and/or remote ssh access information.

        :returns: whether information passed will modify the controller's current state
        :rtype: bool
        """
        update = False
        body = dict(controllerRef=settings['controllerRef'],
                    interfaceRef=iface['id'])
        expected_iface = iface.copy()

        # Check if api url is using the effected management interface to change itself
        update_used_matching_address = False
        if self.enable_interface and self.config_method:
            netloc = list(urlparse.urlparse(self.url))[1]
            address = netloc.split(":")[0]
            address_info = socket.getaddrinfo(address, 8443)
            url_address_info = socket.getaddrinfo(iface["address"], 8443)
            update_used_matching_address = any(info in url_address_info for info in address_info)

        self._logger.info("update_used_matching_address: %s", update_used_matching_address)

        # Populate the body of the request and check for changes
        if self.enable_interface is not None:
            update, expected_iface, body = self.get_enable_interface_settings(iface, expected_iface, update, body)

        if self.config_method is not None:
            update, expected_iface, body = self.get_interface_settings(iface, expected_iface, update, body)

        if self.dns_config_method is not None:
            update, expected_iface, body = self.get_dns_server_settings(iface, expected_iface, update, body)

        if self.ntp_config_method is not None:
            update, expected_iface, body = self.get_ntp_server_settings(iface, expected_iface, update, body)

        if self.ssh is not None:
            update, body = self.get_remote_ssh_settings(settings, update, body)
            iface["ssh"] = self.ssh
            expected_iface["ssh"] = self.ssh

        # debug information
        self._logger.info(pformat(body))
        self._logger.info(pformat(iface))
        self._logger.info(pformat(expected_iface))

        if self.check_mode:
            return update

        if update and not self.check_mode:
            if not update_used_matching_address:
                try:
                    (rc, data) = request(self.url + 'storage-systems/%s/configuration/ethernet-interfaces'
                                         % self.ssid, method='POST', data=json.dumps(body), headers=HEADERS,
                                         timeout=300, ignore_errors=True, **self.creds)
                    if rc == 422:
                        if data['retcode'] == "4" or data['retcode'] == "illegalParam":
                            if not (body['ipv4Enabled'] or iface['ipv6Enabled']):
                                self.module.fail_json(msg="This storage-system already has IPv6 connectivity disabled. "
                                                          "DHCP configuration for IPv4 is required at a minimum."
                                                          " Array Id [%s] Message [%s]."
                                                          % (self.ssid, data['errorMessage']))
                            else:
                                self.module.fail_json(msg="We failed to configure the management interface. Array Id "
                                                          "[%s] Message [%s]." % (self.ssid, data))
                    elif rc >= 300:
                        self.module.fail_json(
                            msg="We failed to configure the management interface. Array Id [%s] Message [%s]." %
                                (self.ssid, data))

                # This is going to catch cases like a connection failure
                except Exception as err:
                    self.module.fail_json(
                        msg="Connection failure: we failed to modify the network settings! Array Id [%s]. Error [%s]."
                            % (self.ssid, to_native(err)))
            else:
                self.update_api_address_interface_match(body)

        return self.validate_changes(expected_iface) if update and iface["link_status"] != "up" else update

    def update_api_address_interface_match(self, body):
        """Change network interface address which matches the api_address"""
        try:
            try:
                (rc, data) = request(self.url + 'storage-systems/%s/configuration/ethernet-interfaces' % self.ssid,
                                     use_proxy=False, force=True, ignore_errors=True, method='POST',
                                     data=json.dumps(body), headers=HEADERS, timeout=10, **self.creds)
            except Exception:
                url_parts = list(urlparse.urlparse(self.url))
                domain = url_parts[1].split(":")
                domain[0] = self.address
                url_parts[1] = ":".join(domain)
                expected_url = urlparse.urlunparse(url_parts)
                self._logger.info(pformat(expected_url))

                (rc, data) = request(expected_url + 'storage-systems/%s/configuration/ethernet-interfaces' % self.ssid,
                                     headers=HEADERS, timeout=300, **self.creds)
                return
        except Exception as err:
            self._logger.info(type(err))
            self.module.fail_json(
                msg="Connection failure: we failed to modify the network settings! Array Id [%s]. Error [%s]."
                    % (self.ssid, to_native(err)))

    def validate_changes(self, expected_iface, retry=6):
        """Validate interface changes were applied to the controller interface port. 30 second timeout"""
        if self.interface != expected_iface:
            time.sleep(5)
            if retry:
                return self.validate_changes(expected_iface, retry - 1)

            self.module.fail_json(msg="Update failure: we failed to verify the necessary state change.")

        return True

    def check_health(self):
        """It's possible, due to a previous operation, for the API to report a 424 (offline) status for the
         storage-system. Therefore, we run a manual check with retries to attempt to contact the system before we
         continue.
        """
        try:
            (rc, data) = request(self.url + 'storage-systems/%s/controllers'
                                 % self.ssid, headers=HEADERS,
                                 ignore_errors=True, **self.creds)

            # We've probably recently changed the interface settings and it's still coming back up: retry.
            if rc == 424:
                if self.retries < self.MAX_RETRIES:
                    self.retries += 1
                    self._logger.info("We hit a 424, retrying in 5s.")
                    time.sleep(5)
                    self.check_health()
                else:
                    self.module.fail_json(
                        msg="We failed to pull storage-system information. Array Id [%s] Message [%s]." %
                            (self.ssid, data))
            elif rc >= 300:
                self.module.fail_json(
                    msg="We failed to pull storage-system information. Array Id [%s] Message [%s]." %
                        (self.ssid, data))
        # This is going to catch cases like a connection failure
        except Exception as err:
            if self.retries < self.MAX_RETRIES:
                self._logger.info("We hit a connection failure, retrying in 5s.")
                self.retries += 1
                time.sleep(5)
                self.check_health()
            else:
                self.module.fail_json(
                    msg="Connection failure: we failed to modify the network settings! Array Id [%s]. Error [%s]."
                        % (self.ssid, to_native(err)))

    def update(self):
        """Update storage system with necessary changes."""
        # Check if the storage array can be contacted
        self.check_health()

        # make the necessary changes to the storage system
        settings = self.controllers[self.controller]
        iface = self.interface
        self._logger.info(pformat(settings))
        self._logger.info(pformat(iface))
        update = self.update_array(settings, iface)

        self.module.exit_json(msg="The interface settings have been updated.", changed=update)

    def __call__(self, *args, **kwargs):
        self.update()


def main():
    iface = MgmtInterface()
    iface()


if __name__ == '__main__':
    main()
