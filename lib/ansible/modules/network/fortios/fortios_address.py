#!/usr/bin/python
#
# Ansible module to manage IP addresses on fortios devices
# (c) 2016, Benjamin Jolivot <bjolivot@gmail.com>
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.
#

ANSIBLE_METADATA = {
    'status': ['preview'],
    'supported_by': 'community',
    'version': '1.0'
}

DOCUMENTATION = """
---
module: fortios_address
version_added: "2.3"
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
      - Address value, absed on type.
        If type=fqdn, somthing like www.google.com.
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
  - This module requires pyFG and netaddr python library.
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
  description: full firewall adresses config string.
  returned: always
  type: string
change_string:
  description: The commands executed by the module.
  returned: only if config changed
  type: string
"""

from ansible.module_utils.fortios import fortios_argument_spec, fortios_required_if
from ansible.module_utils.fortios import backup

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.pycompat24 import get_exception

#check for pyFG lib
try:
    from pyFG import FortiOS, FortiConfig
    from pyFG.fortios import logger
    from pyFG.exceptions import CommandExecutionException, FailedCommit, ForcedCommit
    HAS_PYFG=True
except:
    HAS_PYFG=False

#check for netaddr lib
try:
    from netaddr import IPNetwork
    HAS_NETADDR=True
except:
    HAS_NETADDR=False


#define valid country list for GEOIP address type
FG_COUNTRY_LIST=('ZZ','A1','A2','O1','AD','AE','AF','AG','AI','AL','AM','AN','AO',
'AP','AQ','AR','AS','AT','AU','AW','AX','AZ','BA','BB','BD','BE',
'BF','BG','BH','BI','BJ','BL','BM','BN','BO','BQ','BR','BS','BT',
'BV','BW','BY','BZ','CA','CC','CD','CF','CG','CH','CI','CK','CL',
'CM','CN','CO','CR','CU','CV','CW','CX','CY','CZ','DE','DJ','DK',
'DM','DO','DZ','EC','EE','EG','EH','ER','ES','ET','EU','FI','FJ',
'FK','FM','FO','FR','GA','GB','GD','GE','GF','GG','GH','GI','GL',
'GM','GN','GP','GQ','GR','GS','GT','GU','GW','GY','HK','HM','HN',
'HR','HT','HU','ID','IE','IL','IM','IN','IO','IQ','IR','IS','IT',
'JE','JM','JO','JP','KE','KG','KH','KI','KM','KN','KP','KR','KW',
'KY','KZ','LA','LB','LC','LI','LK','LR','LS','LT','LU','LV','LY',
'MA','MC','MD','ME','MF','MG','MH','MK','ML','MM','MN','MO','MP',
'MQ','MR','MS','MT','MU','MV','MW','MX','MY','MZ','NA','NC','NE',
'NF','NG','NI','NL','NO','NP','NR','NU','NZ','OM','PA','PE','PF',
'PG','PH','PK','PL','PM','PN','PR','PS','PT','PW','PY','QA','RE',
'RO','RS','RU','RW','SA','SB','SC','SD','SE','SG','SH','SI','SJ',
'SK','SL','SM','SN','SO','SR','SS','ST','SV','SX','SY','SZ','TC',
'TD','TF','TG','TH','TJ','TK','TL','TM','TN','TO','TR','TT','TV',
'TW','TZ','UA','UG','UM','US','UY','UZ','VA','VC','VE','VG','VI',
'VN','VU','WF','WS','YE','YT','ZA','ZM','ZW')


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
            return "{0} {1}".format(str_ip, str_netmask)
        else:
            ip = IPNetwork(input_ip)
            return "{0} {1}".format(str(ip.ip), str(ip.netmask))
    except:
        return False

    return False


def main():
    argument_spec = dict(
        state     = dict(required=True, choices=['present', 'absent']),
        name      = dict(required=True, type='str'),
        type      = dict(choices=['iprange', 'fqdn', 'ipmask', 'geography'], default='ipmask'),
        value     = dict(type='str'),
        start_ip  = dict(type='str'),
        end_ip    = dict(type='str'),
        country   = dict(type='str'),
        interface = dict(type='str', default='any'),
        comment   = dict(type='str'),
    )

    fortios_address_required_if = [
        ['type',   'ipmask'   , ['value']             ],
        ['type',   'fqdn'     , ['value']             ],
        ['type',   'iprange'  , ['start_ip', 'end_ip']],
        ['type',   'geography', ['country']           ],
    ]

    #merge global required_if & argument_spec from module_utils/fortios.py
    argument_spec.update(fortios_argument_spec)
    required_if = fortios_required_if + fortios_address_required_if


    module = AnsibleModule(
        argument_spec=argument_spec,
        required_if=required_if,
        supports_check_mode=True,
    )

    result = dict(changed=False)

    # fail if libs not present
    msg = ""
    if not HAS_PYFG:
        msg += 'Could not import the python library pyFG required by this module'

    if not HAS_NETADDR:
        msg += 'Could not import the python library netaddr required by this module'

    if msg != "":
        module.fail_json(msg=msg)

    #validate country
    if module.params['type'] == "geography":
        if module.params['country'] not in FG_COUNTRY_LIST:
            module.fail_json(msg="Invalid country arg, need to be in `diagnose firewall ipgeo country-list`")

    # rewrite ip address in case of CIDR format
    if module.params['type'] == "ipmask":
        formated_ip = get_formated_ipaddr(module.params['value'])
        if formated_ip is not False:
            module.params['value'] = get_formated_ipaddr(module.params['value'])
        else:
            module.fail_json(msg="Bad ip address format")

    #define device
    f = FortiOS( module.params['host'],
        username=module.params['username'],
        password=module.params['password'],
        timeout=module.params['username'],
        vdom=module.params['vdom'])

    #Config path
    path = 'firewall address'

    #connect
    try:
        f.open()
    except:
        module.fail_json(msg='Error connecting device')


    #get  config
    try:
        f.load_config(path=path)
        result['firewall_address_config'] = f.running_config.to_text()

    except:
        module.fail_json(msg='Error reading running config')

    #Absent State
    if module.params['state'] == 'absent':
        f.candidate_config[path].del_block(module.params['name'])
        change_string = f.compare_config()
        if change_string != "":
            result['change_string'] = change_string
            result['changed'] = True


    #Present state
    if module.params['state'] == 'present':
        #define address params
        new_addr = FortiConfig(module.params['name'], 'edit')

        if module.params['comment'] is not None:
            new_addr.set_param('comment', '"{0}"'.format(module.params['comment']))

        if module.params['type'] == 'iprange':
            new_addr.set_param('iprange', module.params['start_ip'])
            new_addr.set_param('start-ip', module.params['start_ip'])
            new_addr.set_param('end-ip', module.params['end_ip'])

        if module.params['type'] == 'geography':
            new_addr.set_param('type', 'geography')
            new_addr.set_param('country', '"{0}"'.format(module.params['country']))

        if module.params['interface'] != 'any':
            new_addr.set_param('associated-interface', '"{0}"'.format(module.params['interface']))

        if module.params['value'] is not None:
            if module.params['type'] == 'fqdn':
                new_addr.set_param('type', 'fqdn')
                new_addr.set_param('fqdn', '"{0}"'.format(module.params['value']))
            if module.params['type'] == 'ipmask':
                new_addr.set_param('subnet', module.params['value'])

        #add to candidate config
        f.candidate_config[path][module.params['name']] = new_addr

        #check if change needed
        change_string = f.compare_config()
        if change_string != "":
            result['change_string'] = change_string
            result['changed'] = True

    #Commit if not check mode
    if module.check_mode is False and change_string != "":
        try:
            f.commit()
        except FailedCommit:
            #rollback
            e = get_exception()
            module.fail_json(msg="Unable to commit change, check your args, the error was {0}".format(e.message))

    module.exit_json(**result)

if __name__ == '__main__':
    main()

