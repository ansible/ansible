#!/usr/bin/python
# Copyright: (c) 2018, Pluribus Networks
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = """
---
module: pn_switch_setup
author: "Pluribus Networks (@rajaspachipulusu17)"
version_added: "2.8"
short_description: CLI command to modify switch-setup
description:
  - This module can be used to modify switch setup.
options:
  pn_cliswitch:
    description:
      - Target switch to run the CLI on.
    required: false
    type: str
  state:
    description:
      - State the action to perform. Use C(update) to modify the switch-setup.
    required: true
    type: str
    choices: ['update']
  pn_force:
    description:
      - Force analytics-store change even if it involves removing data.
    required: false
    type: bool
  pn_dns_ip:
    description:
      - DNS IP address.
    required: false
    type: str
  pn_mgmt_netmask:
    description:
      - Netmask.
    required: false
    type: str
  pn_gateway_ip6:
    description:
      - Gateway IPv6 address.
    required: false
    type: str
  pn_in_band_ip6_assign:
    description:
      - Data IPv6 address assignment.
    required: false
    type: str
    choices: ['none', 'autoconf']
  pn_domain_name:
    description:
      - Domain name.
    required: false
    type: str
  pn_timezone:
    description:
      - Timezone to be configured.
    required: false
    type: str
  pn_in_band_netmask:
    description:
      - Data in-band netmask.
    required: false
    type: str
  pn_in_band_ip6:
    description:
      - Data in-band IPv6 address.
    required: false
    type: str
  pn_in_band_netmask_ip6:
    description:
      - Data in-band IPv6 netmask.
    required: false
    type: str
  pn_motd:
    description:
      - Message of the Day.
    required: false
    type: str
  pn_loopback_ip6:
    description:
      - loopback IPv6 address.
    required: false
    type: str
  pn_mgmt_ip6_assignment:
    description:
      - IPv6 address assignment.
    required: false
    choices: ['none', 'autoconf']
  pn_ntp_secondary_server:
    description:
      - Secondary NTP server.
    required: false
    type: str
  pn_in_band_ip:
    description:
      - data in-band IP address.
    required: false
    type: str
  pn_eula_accepted:
    description:
      - Accept EULA.
    required: false
    type: str
    choices: ['true', 'false']
  pn_mgmt_ip:
    description:
      - Management IP address.
    required: false
    type: str
  pn_ntp_server:
    description:
      - NTP server.
    required: false
    type: str
  pn_mgmt_ip_assignment:
    description:
      - IP address assignment.
    required: false
    type: str
    choices: ['none', 'dhcp']
  pn_date:
    description:
      - Date.
    required: false
    type: str
  pn_password:
    description:
      - plain text password.
    required: false
    type: str
  pn_banner:
    description:
      - Banner to display on server-switch.
    required: false
    type: str
  pn_loopback_ip:
    description:
      - loopback IPv4 address.
    required: false
    type: str
  pn_dns_secondary_ip:
    description:
      - secondary DNS IP address.
    required: false
    type: str
  pn_switch_name:
    description:
      - switch name.
    required: false
    type: str
  pn_eula_timestamp:
    description:
      - EULA timestamp.
    required: false
    type: str
  pn_mgmt_netmask_ip6:
    description:
      - IPv6 netmask.
    required: false
    type: str
  pn_enable_host_ports:
    description:
      - Enable host ports by default.
    required: false
    type: bool
  pn_mgmt_ip6:
    description:
      - IPv6 address.
    required: false
    type: str
  pn_analytics_store:
    description:
      - type of disk storage for analytics.
    required: false
    type: str
    choices: ['default', 'optimized']
  pn_gateway_ip:
    description:
      - gateway IPv4 address.
    required: false
    type: str
"""

EXAMPLES = """
- name: Modify switch
  pn_switch_setup:
    pn_cliswitch: "sw01"
    state: "update"
    pn_timezone: "America/New_York"
    pn_in_band_ip: "20.20.1.1"
    pn_in_band_netmask: "24"

- name: Modify switch
  pn_switch_setup:
    pn_cliswitch: "sw01"
    state: "update"
    pn_in_band_ip6: "2001:0db8:85a3::8a2e:0370:7334"
    pn_in_band_netmask_ip6: "127"
"""

RETURN = """
command:
  description: the CLI command run on the target node.
  returned: always
  type: str
stdout:
  description: set of responses from the switch-setup command.
  returned: always
  type: list
stderr:
  description: set of error responses from the switch-setup command.
  returned: on error
  type: list
changed:
  description: indicates whether the CLI caused changes on the target.
  returned: always
  type: bool
"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.netvisor.pn_nvos import pn_cli, booleanArgs, run_cli


def main():
    """ This section is for arguments parsing """

    state_map = dict(
        update='switch-setup-modify'
    )

    module = AnsibleModule(
        argument_spec=dict(
            pn_cliswitch=dict(required=False, type='str'),
            state=dict(required=True, type='str',
                       choices=['update']),
            pn_force=dict(required=False, type='bool'),
            pn_dns_ip=dict(required=False, type='str'),
            pn_mgmt_netmask=dict(required=False, type='str'),
            pn_gateway_ip6=dict(required=False, type='str'),
            pn_in_band_ip6_assign=dict(required=False, type='str',
                                       choices=['none', 'autoconf']),
            pn_domain_name=dict(required=False, type='str'),
            pn_timezone=dict(required=False, type='str'),
            pn_in_band_netmask=dict(required=False, type='str'),
            pn_in_band_ip6=dict(required=False, type='str'),
            pn_in_band_netmask_ip6=dict(required=False, type='str'),
            pn_motd=dict(required=False, type='str'),
            pn_loopback_ip6=dict(required=False, type='str'),
            pn_mgmt_ip6_assignment=dict(required=False, type='str',
                                        choices=['none', 'autoconf']),
            pn_ntp_secondary_server=dict(required=False, type='str'),
            pn_in_band_ip=dict(required=False, type='str'),
            pn_eula_accepted=dict(required=False, type='str',
                                  choices=['true', 'false']),
            pn_mgmt_ip=dict(required=False, type='str'),
            pn_ntp_server=dict(required=False, type='str'),
            pn_mgmt_ip_assignment=dict(required=False, type='str',
                                       choices=['none', 'dhcp']),
            pn_date=dict(required=False, type='str'),
            pn_password=dict(required=False, type='str', no_log=True),
            pn_banner=dict(required=False, type='str'),
            pn_loopback_ip=dict(required=False, type='str'),
            pn_dns_secondary_ip=dict(required=False, type='str'),
            pn_switch_name=dict(required=False, type='str'),
            pn_eula_timestamp=dict(required=False, type='str'),
            pn_mgmt_netmask_ip6=dict(required=False, type='str'),
            pn_enable_host_ports=dict(required=False, type='bool'),
            pn_mgmt_ip6=dict(required=False, type='str'),
            pn_analytics_store=dict(required=False, type='str',
                                    choices=['default', 'optimized']),
            pn_gateway_ip=dict(required=False, type='str'),
        ),
        required_one_of=[['pn_force', 'pn_dns_ip', 'pn_mgmt_netmask',
                          'pn_gateway_ip6', 'pn_in_band_ip6_assign',
                          'pn_domain_name', 'pn_timezone',
                          'pn_in_band_netmask', 'pn_in_band_ip6',
                          'pn_in_band_netmask_ip6', 'pn_motd',
                          'pn_loopback_ip6', 'pn_mgmt_ip6_assignment',
                          'pn_ntp_secondary_server', 'pn_in_band_ip',
                          'pn_eula_accepted', 'pn_mgmt_ip',
                          'pn_ntp_server', 'pn_mgmt_ip_assignment',
                          'pn_date', 'pn_password',
                          'pn_banner', 'pn_loopback_ip',
                          'pn_dns_secondary_ip', 'pn_switch_name',
                          'pn_eula_timestamp', 'pn_mgmt_netmask_ip6',
                          'pn_enable_host_ports', 'pn_mgmt_ip6',
                          'pn_analytics_store', 'pn_gateway_ip']],
        required_together=[['pn_in_band_ip6', 'pn_in_band_netmask_ip6'],
                           ['pn_in_band_ip', 'pn_in_band_netmask'],
                           ['pn_mgmt_ip', 'pn_mgmt_netmask'],
                           ['pn_mgmt_ip6', 'pn_mgmt_netmask_ip6']],
    )

    # Accessing the arguments
    cliswitch = module.params['pn_cliswitch']
    state = module.params['state']
    force = module.params['pn_force']
    dns_ip = module.params['pn_dns_ip']
    mgmt_netmask = module.params['pn_mgmt_netmask']
    gateway_ip6 = module.params['pn_gateway_ip6']
    in_band_ip6_assign = module.params['pn_in_band_ip6_assign']
    domain_name = module.params['pn_domain_name']
    timezone = module.params['pn_timezone']
    in_band_netmask = module.params['pn_in_band_netmask']
    in_band_ip6 = module.params['pn_in_band_ip6']
    in_band_netmask_ip6 = module.params['pn_in_band_netmask_ip6']
    motd = module.params['pn_motd']
    loopback_ip6 = module.params['pn_loopback_ip6']
    mgmt_ip6_assignment = module.params['pn_mgmt_ip6_assignment']
    ntp_secondary_server = module.params['pn_ntp_secondary_server']
    in_band_ip = module.params['pn_in_band_ip']
    eula_accepted = module.params['pn_eula_accepted']
    mgmt_ip = module.params['pn_mgmt_ip']
    ntp_server = module.params['pn_ntp_server']
    mgmt_ip_assignment = module.params['pn_mgmt_ip_assignment']
    date = module.params['pn_date']
    password = module.params['pn_password']
    banner = module.params['pn_banner']
    loopback_ip = module.params['pn_loopback_ip']
    dns_secondary_ip = module.params['pn_dns_secondary_ip']
    switch_name = module.params['pn_switch_name']
    eula_timestamp = module.params['pn_eula_timestamp']
    mgmt_netmask_ip6 = module.params['pn_mgmt_netmask_ip6']
    enable_host_ports = module.params['pn_enable_host_ports']
    mgmt_ip6 = module.params['pn_mgmt_ip6']
    analytics_store = module.params['pn_analytics_store']
    gateway_ip = module.params['pn_gateway_ip']

    command = state_map[state]

    # Building the CLI command string
    cli = pn_cli(module, cliswitch)

    if command == 'switch-setup-modify':
        cli += ' %s ' % command
        if dns_ip:
            cli += ' dns-ip ' + dns_ip
        if mgmt_netmask:
            cli += ' mgmt-netmask ' + mgmt_netmask
        if gateway_ip6:
            cli += ' gateway-ip6 ' + gateway_ip6
        if in_band_ip6_assign:
            cli += ' in-band-ip6-assign ' + in_band_ip6_assign
        if domain_name:
            cli += ' domain-name ' + domain_name
        if timezone:
            cli += ' timezone ' + timezone
        if in_band_netmask:
            cli += ' in-band-netmask ' + in_band_netmask
        if in_band_ip6:
            cli += ' in-band-ip6 ' + in_band_ip6
        if in_band_netmask_ip6:
            cli += ' in-band-netmask-ip6 ' + in_band_netmask_ip6
        if motd:
            cli += ' motd ' + motd
        if loopback_ip6:
            cli += ' loopback-ip6 ' + loopback_ip6
        if mgmt_ip6_assignment:
            cli += ' mgmt-ip6-assignment ' + mgmt_ip6_assignment
        if ntp_secondary_server:
            cli += ' ntp-secondary-server ' + ntp_secondary_server
        if in_band_ip:
            cli += ' in-band-ip ' + in_band_ip
        if eula_accepted:
            cli += ' eula-accepted ' + eula_accepted
        if mgmt_ip:
            cli += ' mgmt-ip ' + mgmt_ip
        if ntp_server:
            cli += ' ntp-server ' + ntp_server
        if mgmt_ip_assignment:
            cli += ' mgmt-ip-assignment ' + mgmt_ip_assignment
        if date:
            cli += ' date ' + date
        if password:
            cli += ' password ' + password
        if banner:
            cli += ' banner ' + banner
        if loopback_ip:
            cli += ' loopback-ip ' + loopback_ip
        if dns_secondary_ip:
            cli += ' dns-secondary-ip ' + dns_secondary_ip
        if switch_name:
            cli += ' switch-name ' + switch_name
        if eula_timestamp:
            cli += ' eula_timestamp ' + eula_timestamp
        if mgmt_netmask_ip6:
            cli += ' mgmt-netmask-ip6 ' + mgmt_netmask_ip6
        if mgmt_ip6:
            cli += ' mgmt-ip6 ' + mgmt_ip6
        if analytics_store:
            cli += ' analytics-store ' + analytics_store
        if gateway_ip:
            cli += ' gateway-ip ' + gateway_ip

        cli += booleanArgs(force, 'force', 'no-force')
        cli += booleanArgs(enable_host_ports, 'enable-host-ports', 'disable-host-ports')

    run_cli(module, cli, state_map)


if __name__ == '__main__':
    main()
