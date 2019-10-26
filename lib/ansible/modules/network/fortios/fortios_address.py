#!/usr/bin/python
#
# Ansible module to manage IP addresses on fortios devices
# (c) 2016, Benjamin Jolivot <bjolivot@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = """
---
module: fortios_address
version_added: "2.4"
author: "Benjamin Jolivot (@bjolivot)"
short_description: Manage fortios firewall address objects
description:
  - This module provide management of firewall addresses on FortiOS devices.
extends_documentation_fragment: fortios
options:
  state:
    description:
      - Specifies if address need to be added or deleted.
    required: true
    choices: ['present', 'absent']
  name:
    description:
      - Name of the address to add or delete.
    required: true
  type:
    description:
      - Type of the address.
    choices: ['iprange', 'fqdn', 'ipmask', 'geography']
  value:
    description:
      - Address value, based on type.
        If type=fqdn, something like www.google.com.
        If type=ipmask, you can use simple ip (192.168.0.1), ip+mask (192.168.0.1 255.255.255.0) or CIDR (192.168.0.1/32).
  start_ip:
    description:
      - First ip in range (used only with type=iprange).
  end_ip:
    description:
      - Last ip in range (used only with type=iprange).
  country:
    description:
      - 2 letter country code (like FR).
  interface:
    description:
      - interface name the address apply to.
    default: any
  comment:
    description:
      - free text to describe address.
notes:
  - This module requires netaddr python library.
"""

EXAMPLES = """
- name: Register french addresses
  fortios_address:
    host: 192.168.0.254
    username: admin
    password: p4ssw0rd
    state: present
    name: "fromfrance"
    type: geography
    country: FR
    comment: "French geoip address"

- name: Register some fqdn
  fortios_address:
    host: 192.168.0.254
    username: admin
    password: p4ssw0rd
    state: present
    name: "Ansible"
    type: fqdn
    value: www.ansible.com
    comment: "Ansible website"

- name: Register google DNS
  fortios_address:
    host: 192.168.0.254
    username: admin
    password: p4ssw0rd
    state: present
    name: "google_dns"
    type: ipmask
    value: 8.8.8.8

"""

RETURN = """
firewall_address_config:
  description: full firewall addresses config string.
  returned: always
  type: str
change_string:
  description: The commands executed by the module.
  returned: only if config changed
  type: str
"""

from ansible.module_utils.network.fortios.fortios import fortios_argument_spec, fortios_required_if
from ansible.module_utils.network.fortios.fortios import backup, AnsibleFortios

from ansible.module_utils.basic import AnsibleModule


# check for netaddr lib
try:
    from netaddr import IPNetwork
    HAS_NETADDR = True
except Exception:
    HAS_NETADDR = False


# define valid country list for GEOIP address type
FG_COUNTRY_LIST = (
    'ZZ', 'A1', 'A2', 'O1', 'AD', 'AE', 'AF', 'AG', 'AI', 'AL', 'AM', 'AN', 'AO',
    'AP', 'AQ', 'AR', 'AS', 'AT', 'AU', 'AW', 'AX', 'AZ', 'BA', 'BB', 'BD', 'BE',
    'BF', 'BG', 'BH', 'BI', 'BJ', 'BL', 'BM', 'BN', 'BO', 'BQ', 'BR', 'BS', 'BT',
    'BV', 'BW', 'BY', 'BZ', 'CA', 'CC', 'CD', 'CF', 'CG', 'CH', 'CI', 'CK', 'CL',
    'CM', 'CN', 'CO', 'CR', 'CU', 'CV', 'CW', 'CX', 'CY', 'CZ', 'DE', 'DJ', 'DK',
    'DM', 'DO', 'DZ', 'EC', 'EE', 'EG', 'EH', 'ER', 'ES', 'ET', 'EU', 'FI', 'FJ',
    'FK', 'FM', 'FO', 'FR', 'GA', 'GB', 'GD', 'GE', 'GF', 'GG', 'GH', 'GI', 'GL',
    'GM', 'GN', 'GP', 'GQ', 'GR', 'GS', 'GT', 'GU', 'GW', 'GY', 'HK', 'HM', 'HN',
    'HR', 'HT', 'HU', 'ID', 'IE', 'IL', 'IM', 'IN', 'IO', 'IQ', 'IR', 'IS', 'IT',
    'JE', 'JM', 'JO', 'JP', 'KE', 'KG', 'KH', 'KI', 'KM', 'KN', 'KP', 'KR', 'KW',
    'KY', 'KZ', 'LA', 'LB', 'LC', 'LI', 'LK', 'LR', 'LS', 'LT', 'LU', 'LV', 'LY',
    'MA', 'MC', 'MD', 'ME', 'MF', 'MG', 'MH', 'MK', 'ML', 'MM', 'MN', 'MO', 'MP',
    'MQ', 'MR', 'MS', 'MT', 'MU', 'MV', 'MW', 'MX', 'MY', 'MZ', 'NA', 'NC', 'NE',
    'NF', 'NG', 'NI', 'NL', 'NO', 'NP', 'NR', 'NU', 'NZ', 'OM', 'PA', 'PE', 'PF',
    'PG', 'PH', 'PK', 'PL', 'PM', 'PN', 'PR', 'PS', 'PT', 'PW', 'PY', 'QA', 'RE',
    'RO', 'RS', 'RU', 'RW', 'SA', 'SB', 'SC', 'SD', 'SE', 'SG', 'SH', 'SI', 'SJ',
    'SK', 'SL', 'SM', 'SN', 'SO', 'SR', 'SS', 'ST', 'SV', 'SX', 'SY', 'SZ', 'TC',
    'TD', 'TF', 'TG', 'TH', 'TJ', 'TK', 'TL', 'TM', 'TN', 'TO', 'TR', 'TT', 'TV',
    'TW', 'TZ', 'UA', 'UG', 'UM', 'US', 'UY', 'UZ', 'VA', 'VC', 'VE', 'VG', 'VI',
    'VN', 'VU', 'WF', 'WS', 'YE', 'YT', 'ZA', 'ZM', 'ZW'
)


def get_formated_ipaddr(input_ip):
    """
    Format given ip address string to fortigate format (ip netmask)
    Args:
        * **ip_str** (string) : string representing ip address
        accepted format:
          - ip netmask  (ex: 192.168.0.10 255.255.255.0)
          - ip (ex: 192.168.0.10)
          - CIDR (ex: 192.168.0.10/24)

    Returns:
        formated ip if ip is valid (ex: "192.168.0.10 255.255.255.0")
        False if ip is not valid
    """
    try:
        if " " in input_ip:
            # ip netmask format
            str_ip, str_netmask = input_ip.split(" ")
            ip = IPNetwork(str_ip)
            mask = IPNetwork(str_netmask)
            return "%s %s" % (str_ip, str_netmask)
        else:
            ip = IPNetwork(input_ip)
            return "%s %s" % (str(ip.ip), str(ip.netmask))
    except Exception:
        return False

    return False


def main():
    argument_spec = dict(
        state=dict(required=True, choices=['present', 'absent']),
        name=dict(required=True),
        type=dict(choices=['iprange', 'fqdn', 'ipmask', 'geography'], default='ipmask'),
        value=dict(),
        start_ip=dict(),
        end_ip=dict(),
        country=dict(),
        interface=dict(default='any'),
        comment=dict(),
    )

    # merge argument_spec from module_utils/fortios.py
    argument_spec.update(fortios_argument_spec)

    # Load module
    module = AnsibleModule(
        argument_spec=argument_spec,
        required_if=fortios_required_if,
        supports_check_mode=True,
    )
    result = dict(changed=False)

    if not HAS_NETADDR:
        module.fail_json(msg='Could not import the python library netaddr required by this module')

    # check params
    if module.params['state'] == 'absent':
        if module.params['type'] != "ipmask":
            module.fail_json(msg='Invalid argument type=%s when state=absent' % module.params['type'])
        if module.params['value'] is not None:
            module.fail_json(msg='Invalid argument `value` when state=absent')
        if module.params['start_ip'] is not None:
            module.fail_json(msg='Invalid argument `start_ip` when state=absent')
        if module.params['end_ip'] is not None:
            module.fail_json(msg='Invalid argument `end_ip` when state=absent')
        if module.params['country'] is not None:
            module.fail_json(msg='Invalid argument `country` when state=absent')
        if module.params['interface'] != "any":
            module.fail_json(msg='Invalid argument `interface` when state=absent')
        if module.params['comment'] is not None:
            module.fail_json(msg='Invalid argument `comment` when state=absent')
    else:
        # state=present
        # validate IP
        if module.params['type'] == "ipmask":
            formated_ip = get_formated_ipaddr(module.params['value'])
            if formated_ip is not False:
                module.params['value'] = get_formated_ipaddr(module.params['value'])
            else:
                module.fail_json(msg="Bad ip address format")

        # validate country
        if module.params['type'] == "geography":
            if module.params['country'] not in FG_COUNTRY_LIST:
                module.fail_json(msg="Invalid country argument, need to be in `diagnose firewall ipgeo country-list`")

        # validate iprange
        if module.params['type'] == "iprange":
            if module.params['start_ip'] is None:
                module.fail_json(msg="Missing argument 'start_ip' when type is iprange")
            if module.params['end_ip'] is None:
                module.fail_json(msg="Missing argument 'end_ip' when type is iprange")

    # init forti object
    fortigate = AnsibleFortios(module)

    # Config path
    config_path = 'firewall address'

    # load config
    fortigate.load_config(config_path)

    # Absent State
    if module.params['state'] == 'absent':
        fortigate.candidate_config[config_path].del_block(module.params['name'])

    # Present state
    if module.params['state'] == 'present':
        # define address params
        new_addr = fortigate.get_empty_configuration_block(module.params['name'], 'edit')

        if module.params['comment'] is not None:
            new_addr.set_param('comment', '"%s"' % (module.params['comment']))

        if module.params['type'] == 'iprange':
            new_addr.set_param('type', 'iprange')
            new_addr.set_param('start-ip', module.params['start_ip'])
            new_addr.set_param('end-ip', module.params['end_ip'])

        if module.params['type'] == 'geography':
            new_addr.set_param('type', 'geography')
            new_addr.set_param('country', '"%s"' % (module.params['country']))

        if module.params['interface'] != 'any':
            new_addr.set_param('associated-interface', '"%s"' % (module.params['interface']))

        if module.params['value'] is not None:
            if module.params['type'] == 'fqdn':
                new_addr.set_param('type', 'fqdn')
                new_addr.set_param('fqdn', '"%s"' % (module.params['value']))
            if module.params['type'] == 'ipmask':
                new_addr.set_param('subnet', module.params['value'])

        # add the new address object to the device
        fortigate.add_block(module.params['name'], new_addr)

    # Apply changes (check mode is managed directly by the fortigate object)
    fortigate.apply_changes()


if __name__ == '__main__':
    main()
