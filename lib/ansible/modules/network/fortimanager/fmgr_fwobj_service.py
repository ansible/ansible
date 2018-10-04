#!/usr/bin/python
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

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {
    "metadata_version": "1.1",
    "status": ["preview"],
    "supported_by": "community"
}

DOCUMENTATION = '''
---
module: fmgr_fwobj_service
version_added: "2.8"
author:
    - Luke Weighall (@lweighall)
    - Andrew Welsh (@Ghilli3)
    - Jim Huber (@p4r4n0y1ng)
short_description: Manages FortiManager Firewall Service Objects
description:
  -  Manages FortiManager Firewall Service Objects

options:
  adom:
    description:
     -The ADOM the configuration should belong to.
    required: false
    default: root
  host:
    description:
     -The FortiManager's Address.
    required: true
  username:
    description:
     -The username used to authenticate with the FortiManager.
    required: true
  password:
    description:
     -The password associated with the username account.
    required: true

  app_category:
    description:
      - Application category ID.
    required: false

  app_service_type:
    description:
      - Application service type.
    required: false

  application:
    description:
      - Application ID.
    required: false

  category:
    description:
      - Service category.
    required: false

  check_reset_range:
    description:
      - Enable disable RST check.
    required: false

  color:
    description:
      - GUI icon color.
    required: false
    default: 22

  comment:
    description:
      - Comment.
    required: false

  custom_type:
    description:
      - Tells module what kind of custom service to be added
    choices: ['tcp_udp_sctp', 'icmp', 'icmp6', 'ip', 'http', 'ftp', 'connect', 'socks_tcp', 'socks_udp', 'all']
    default: all
    required: false

  explicit_proxy:
    description:
      - Enable/disable explicit web proxy service.
    choices: ['enable', 'disable']
    default: 'disable'
    required: false

  fqdn:
    description:
      - Fully qualified domain name.
    required: false
    default: ""

  group_name:
    description:
      - Name of the Service Group.
    required: false

  group_member:
    description:
      - Comma Seperated list of members' names.
    required: false

  icmp_code:
    description:
      - ICMP code.
    required: false

  icmp_type:
    description:
      - ICMP type.
    required: false

  iprange:
    description:
      - Start IP-End IP.
    required: false
    default: "0.0.0.0"

  name:
    description:
      - Custom service name.
    required: false

  mode:
    description:
      - Sets one of three modes for managing the object
    choices: ['add', 'set', 'delete']
    default: add
    required: false

  object_type:
    description:
      - Tells module if we are adding a custom service, category, or group
    choices: ['custom', 'group', 'category']
    required: false

  protocol:
    description:
      - Protocol type.
    required: false

  protocol_number:
    description:
      - IP protocol number.
    required: false

  sctp_portrange:
    description:
      - Multiple SCTP port ranges. Comma separated list of destination ports to add (i.e. '443,80')
      - Syntax is <destPort:sourcePort>
      - If no sourcePort is defined, it assumes all of them.
      - Ranges can be defined with a hyphen -
      - Examples -- '443' (destPort 443 only)  '443:1000-2000' (destPort 443 from source ports 1000-2000)
      - String multiple together in same quotes, comma separated. ('443:1000-2000, 80:1000-2000')
    required: false

  session_ttl:
    description:
      - Session TTL (300 - 604800, 0 = default).
    required: false
    default: 0

  tcp_halfclose_timer:
    description:
      - TCP half close timeout (1 - 86400 sec, 0 = default).
    required: false
    default: 0

  tcp_halfopen_timer:
    description:
      - TCP half close timeout (1 - 86400 sec, 0 = default).
    required: false
    default: 0

  tcp_portrange:
    description:
      - Comma separated list of destination ports to add (i.e. '443,80')
      - Syntax is <destPort:sourcePort>
      - If no sourcePort is defined, it assumes all of them.
      - Ranges can be defined with a hyphen -
      - Examples -- '443' (destPort 443 only)  '443:1000-2000' (destPort 443 from source ports 1000-2000)
      - String multiple together in same quotes, comma separated. ('443:1000-2000, 80:1000-2000')
    required: false

  tcp_timewait_timer:
    description:
      - TCP half close timeout (1 - 300 sec, 0 = default).
    required: false
    default: 0

  udp_idle_timer:
    description:
      - TCP half close timeout (0 - 86400 sec, 0 = default).
    required: false
    default: 0

  udp_portrange:
    description:
      - Comma separated list of destination ports to add (i.e. '443,80')
      - Syntax is <destPort:sourcePort>
      - If no sourcePort is defined, it assumes all of them.
      - Ranges can be defined with a hyphen -
      - Examples -- '443' (destPort 443 only)  '443:1000-2000' (destPort 443 from source ports 1000-2000)
      - String multiple together in same quotes, comma separated. ('443:1000-2000, 80:1000-2000')
    required: false

  visibility:
    description:
      - Enable/disable service visibility.
    required: false
    choices: ["enable", "disable"]
    default: "enable"

'''

EXAMPLES = '''
- name: ADD A CUSTOM SERVICE FOR TCP/UDP/SCP
  fmgr_fwobj_service:
    host: "{{ inventory_hostname }}"
    username: "{{ username }}"
    password: "{{ password }}"
    adom: "ansible"
    name: "ansible_custom_service"
    object_type: "custom"
    custom_type: "tcp_udp_sctp"
    tcp_portrange: "443"
    udp_portrange: "51"
    sctp_portrange: "100"

- name: ADD A CUSTOM SERVICE FOR TCP/UDP/SCP WITH SOURCE RANGES AND MULTIPLES
  fmgr_fwobj_service:
    host: "{{ inventory_hostname }}"
    username: "{{ username }}"
    password: "{{ password }}"
    adom: "ansible"
    name: "ansible_custom_serviceWithSource"
    object_type: "custom"
    custom_type: "tcp_udp_sctp"
    tcp_portrange: "443:2000-1000,80-82:10000-20000"
    udp_portrange: "51:100-200,162:200-400"
    sctp_portrange: "100:2000-2500"

- name: ADD A CUSTOM SERVICE FOR ICMP
  fmgr_fwobj_service:
    host: "{{ inventory_hostname }}"
    username: "{{ username }}"
    password: "{{ password }}"
    adom: "ansible"
    name: "ansible_custom_icmp"
    object_type: "custom"
    custom_type: "icmp"
    icmp_type: "8"
    icmp_code: "3"

- name: ADD A CUSTOM SERVICE FOR ICMP6
  fmgr_fwobj_service:
    host: "{{ inventory_hostname }}"
    username: "{{ username }}"
    password: "{{ password }}"
    adom: "ansible"
    name: "ansible_custom_icmp6"
    object_type: "custom"
    custom_type: "icmp6"
    icmp_type: "5"
    icmp_code: "1"

- name: ADD A CUSTOM SERVICE FOR IP - GRE
  fmgr_fwobj_service:
    host: "{{ inventory_hostname }}"
    username: "{{ username }}"
    password: "{{ password }}"
    adom: "ansible"
    name: "ansible_custom_icmp6"
    object_type: "custom"
    custom_type: "ip"
    protocol_number: "47"

- name: ADD A CUSTOM PROXY FOR ALL WITH SOURCE RANGES AND MULTIPLES
  fmgr_fwobj_service:
    host: "{{ inventory_hostname }}"
    username: "{{ username }}"
    password: "{{ password }}"
    adom: "ansible"
    name: "ansible_custom_proxy_all"
    object_type: "custom"
    custom_type: "all"
    explicit_proxy: "enable"
    tcp_portrange: "443:2000-1000,80-82:10000-20000"
    iprange: "www.ansible.com"
'''

RETURN = """
api_result:
  description: full API response, includes status code and message
  returned: always
  type: string
"""

from ansible.module_utils.basic import AnsibleModule, env_fallback
from ansible.module_utils.network.fortimanager.fortimanager import AnsibleFortiManager

# check for pyFMG lib
try:
    from pyFMG.fortimgr import FortiManager
    HAS_PYFMGR = True
except ImportError:
    HAS_PYFMGR = False


# FUNCTION/METHOD FOR CONVERTING CIDR TO A NETMASK
def cidr_to_netmask(cidr):
    cidr = int(cidr)
    mask = (0xffffffff >> (32 - cidr)) << (32 - cidr)
    return(str((0xff000000 & mask) >> 24) + '.' +
           str((0x00ff0000 & mask) >> 16) + '.' +
           str((0x0000ff00 & mask) >> 8) + '.' +
           str((0x000000ff & mask)))


def fmgr_fwobj_service_custom(fmg, paramgram):
    """
    # NOTES!
    -- the tcp and udp-portrange parameters are in a list when there are multiple. they are not in a list when they
        singular or by themselves (only 1 was listed)
        -- the syntax for this is (destPort:sourcePort). Ranges are (xxxx-xxxx) i.e. 443:443, or 443:1000-2000.
        -- if you leave out the second field after the colon (source port) it assumes any source port (which is usual)
        -- multiples would look like ['443:1000-2000','80']
        -- a single would look simple like "443:1000-2000" without the list around it ( a string!)

    -- the protocol parameter is the protocol NUMBER, not the string of it.
    """

    if paramgram["mode"] in ['set', 'add']:
        # SET THE URL FOR ADD / SET
        url = '/pm/config/adom/{adom}/obj/firewall/service/custom'.format(adom=paramgram["adom"])
        # BUILD THE DEFAULT DATAGRAM
        datagram = {
            # ADVANCED OPTIONS
            "app-category": paramgram["app-category"],
            "app-service-type": paramgram["app-service-type"],
            "application": paramgram["application"],
            "category": paramgram["category"],
            "check-reset-range": paramgram["check-reset-range"],
            "color": paramgram["color"],
            "session-ttl": paramgram["session-ttl"],
            "tcp-halfclose-timer": paramgram["tcp-halfclose-timer"],
            "tcp-halfopen-timer": paramgram["tcp-halfopen-timer"],
            "tcp-timewait-timer": paramgram["tcp-timewait-timer"],
            "udp-idle-timer": paramgram["udp-idle-timer"],
            "visibility": paramgram["visibility"],
            "comment": paramgram["comment"],
            "proxy": paramgram["explicit-proxy"],
            "name": paramgram["name"]
        }

        if datagram["proxy"] == "disable":
            #######################################
            # object-type = "TCP/UDP/SCTP"
            #######################################
            if paramgram["custom_type"] == "tcp_udp_sctp":
                datagram["protocol"] = "TCP/UDP/SCTP"
                # PROCESS PORT RANGES TO PUT INTO THE PROPER SYNTAX
                if paramgram["tcp-portrange"] is not None:
                    tcp_list = []
                    for tcp in paramgram["tcp-portrange"].split(","):
                        tcp = tcp.strip()
                        tcp_list.append(tcp)
                    datagram["tcp-portrange"] = tcp_list

                if paramgram["udp-portrange"] is not None:
                    udp_list = []
                    for udp in paramgram["udp-portrange"].split(","):
                        udp = udp.strip()
                        udp_list.append(udp)
                    datagram["udp-portrange"] = udp_list

                if paramgram["sctp-portrange"] is not None:
                    sctp_list = []
                    for sctp in paramgram["sctp-portrange"].split(","):
                        sctp = sctp.strip()
                        sctp_list.append(sctp)
                    datagram["sctp-portrange"] = sctp_list

            #######################################
            # object-type = "ICMP"
            #######################################
            if paramgram["custom_type"] == "icmp":
                datagram["icmpcode"] = paramgram["icmp_code"]
                datagram["icmptype"] = paramgram["icmp_type"]
                datagram["protocol"] = "ICMP"

            #######################################
            # object-type = "ICMP6"
            #######################################
            if paramgram["custom_type"] == "icmp6":
                datagram["icmpcode"] = paramgram["icmp_code"]
                datagram["icmptype"] = paramgram["icmp_type"]
                datagram["protocol"] = "ICMP6"

            #######################################
            # object-type = "IP"
            #######################################
            if paramgram["custom_type"] == "ip":
                datagram["protocol"] = "IP"
                datagram["protocol-number"] = paramgram["protocol-number"]

        #######################################
        # object-type in any of the explicit proxy options
        #######################################
        if datagram["proxy"] == "enable":
            datagram["protocol"] = paramgram["custom_type"].upper()
            datagram["iprange"] = paramgram["iprange"]

            # PROCESS PROXY TCP PORT RANGES TO PUT INTO THE PROPER SYNTAX
            if paramgram["tcp-portrange"] is not None:
                tcp_list = []
                for tcp in paramgram["tcp-portrange"].split(","):
                    tcp = tcp.strip()
                    tcp_list.append(tcp)
                datagram["tcp-portrange"] = tcp_list

    if paramgram["mode"] == "delete":
        datagram = {
            "name": paramgram["name"]
        }
        # SET DELETE URL
        url = '/pm/config/adom/{adom}/obj/firewall/service/custom' \
              '/{name}'.format(adom=paramgram["adom"], name=paramgram["name"])

    datagram = fmgr_del_none(datagram)

    if paramgram["mode"] == "set":
        response = fmg.set(url, datagram)
        # IF MODE = ADD  -- USE THE 'ADD' API CALL MODE
    if paramgram["mode"] == "add":
        response = fmg.add(url, datagram)
        # IF MODE = DELETE  -- USE THE DELETE URL AND API CALL MODE
    if paramgram["mode"] == "delete":
        response = fmg.delete(url, datagram)
    
    return response


def fmgr_fwobj_service_group(fmg, paramgram):
    """
    # NOTES
    only advanced option is color
    when explicit proxy is set no other options are presented
    add members list and boom
    explicit-proxy = 0 is default
    meta fields = {}
    color =
    comment
    """

    if paramgram["mode"] in ['set', 'add']:
        url = '/pm/config/adom/{adom}/obj/firewall/service/group'.format(adom=paramgram["adom"])
        datagram = {
            "name": paramgram["group-name"],
            "comment": paramgram["comment"],
            "proxy": paramgram["explicit-proxy"],
            "color": paramgram["color"]
        }

        members = paramgram["group-member"]
        member = []
        for obj in members.split(","):
            member.append(obj.strip())
        datagram["member"] = member

    if paramgram["mode"] == "delete":
        datagram = {
            "name": paramgram["name"]
        }
        # SET DELETE URL
        url = '/pm/config/adom/{adom}/obj/firewall/service/group' \
              '/{name}'.format(adom=paramgram["adom"], name=paramgram["group-name"])

    datagram = fmgr_del_none(datagram)

    if paramgram["mode"] == "set":
        response = fmg.set(url, datagram)
        # IF MODE = ADD  -- USE THE 'ADD' API CALL MODE
    if paramgram["mode"] == "add":
        response = fmg.add(url, datagram)
        # IF MODE = DELETE  -- USE THE DELETE URL AND API CALL MODE
    if paramgram["mode"] == "delete":
        response = fmg.delete(url, datagram)
    
    return response


def fmgr_fwobj_service_category(fmg, paramgram):
    """
    # NOTES
    """
    if paramgram["mode"] in ['set', 'add']:
        url = '/pm/config/adom/{adom}/obj/firewall/service/category'.format(adom=paramgram["adom"])
        # GET RID OF ANY WHITESPACE
        category = paramgram["category"]
        category = category.strip()

        datagram = {
            "name": paramgram["category"],
            "comment": "Created by Ansible"
        }

    # IF MODE = DELETE
    if paramgram["mode"] == "delete":
        datagram = {
            "name": paramgram["name"]
        }
        # SET DELETE URL
        url = '/pm/config/adom/{adom}/obj/firewall/service/category' \
              '/{name}'.format(adom=paramgram["adom"], name=paramgram["category"])

    datagram = fmgr_del_none(datagram)

    if paramgram["mode"] == "set":
        response = fmg.set(url, datagram)
        # IF MODE = ADD  -- USE THE 'ADD' API CALL MODE
    if paramgram["mode"] == "add":
        response = fmg.add(url, datagram)
        # IF MODE = DELETE  -- USE THE DELETE URL AND API CALL MODE
    if paramgram["mode"] == "delete":
        response = fmg.delete(url, datagram)
    
    return response


def fmgr_del_none(obj):
    if isinstance(obj, dict):
        return type(obj)((fmgr_del_none(k), fmgr_del_none(v))
                         for k, v in obj.items() if k is not None and (v is not None and not fmgr_is_empty_dict(v)))
    else:
        return obj


def fmgr_is_empty_dict(obj):
    return_val = False
    if isinstance(obj, dict):
        if len(obj) > 0:
            for k, v in obj.items():
                if isinstance(v, dict):
                    if len(v) == 0:
                        return_val = True
                    elif len(v) > 0:
                        for k1, v1 in v.items():
                            if v1 is None:
                                return_val = True
                            elif v1 is not None:
                                return_val = False
                                return return_val
                elif v is None:
                    return_val = True
                elif v is not None:
                    return_val = False
                    return return_val
        elif len(obj) == 0:
            return_val = True

    return return_val


def main():
    argument_spec = dict(
        adom=dict(required=False, type="str", default="root"),
        host=dict(required=True, type="str"),
        password=dict(fallback=(env_fallback, ["ANSIBLE_NET_PASSWORD"]), no_log=True),
        username=dict(fallback=(env_fallback, ["ANSIBLE_NET_USERNAME"]), no_log=True),
        mode=dict(required=False, type="str", choices=['add', 'set', 'delete'], default="add"),

        app_category=dict(required=False, type="str"),
        app_service_type=dict(required=False, type="str"),
        application=dict(required=False, type="str"),
        category=dict(required=False, type="str"),
        check_reset_range=dict(required=False, type="str"),
        color=dict(required=False, type="int", default=22),
        comment=dict(required=False, type="str"),
        custom_type=dict(required=False, type="str", choices=['tcp_udp_sctp', 'icmp', 'icmp6', 'ip', 'http', 'ftp',
                                                              'connect', 'socks_tcp', 'socks_udp', 'all'],
                         default="all"),
        explicit_proxy=dict(required=False, type="str", choices=['enable', 'disable'], default="disable"),
        fqdn=dict(required=False, type="str", default=""),
        group_name=dict(required=False, type="str"),
        group_member=dict(required=False, type="str"),
        icmp_code=dict(required=False, type="int"),
        icmp_type=dict(required=False, type="int"),
        iprange=dict(required=False, type="str", default="0.0.0.0"),
        name=dict(required=False, type="str"),
        protocol=dict(required=False, type="str"),
        protocol_number=dict(required=False, type="int"),
        sctp_portrange=dict(required=False, type="str"),
        session_ttl=dict(required=False, type="int", default=0),
        object_type=dict(required=False, type="str", choices=['custom', 'group', 'category']),
        tcp_halfclose_timer=dict(required=False, type="int", default=0),
        tcp_halfopen_timer=dict(required=False, type="int", default=0),
        tcp_portrange=dict(required=False, type="str"),
        tcp_timewait_timer=dict(required=False, type="int", default=0),
        udp_idle_timer=dict(required=False, type="int", default=0),
        udp_portrange=dict(required=False, type="str"),
        visibility=dict(required=False, type="str", default="enable", choices=["enable", "disable"]),

    )

    module = AnsibleModule(argument_spec, supports_check_mode=True, )

    # MODULE DATAGRAM
    paramgram = {
        "adom": module.params["adom"],
        "app-category": module.params["app_category"],
        "app-service-type": module.params["app_service_type"],
        "application": module.params["application"],
        "category": module.params["category"],
        "check-reset-range": module.params["check_reset_range"],
        "color": module.params["color"],
        "comment": module.params["comment"],
        "custom_type": module.params["custom_type"],
        "explicit-proxy": module.params["explicit_proxy"],
        "fqdn": module.params["fqdn"],
        "group-name": module.params["group_name"],
        "group-member": module.params["group_member"],
        "icmp_code": module.params["icmp_code"],
        "icmp_type": module.params["icmp_type"],
        "iprange": module.params["iprange"],
        "name": module.params["name"],
        "mode": module.params["mode"],
        "protocol": module.params["protocol"],
        "protocol-number": module.params["protocol_number"],
        "sctp-portrange": module.params["sctp_portrange"],
        "object_type": module.params["object_type"],
        "session-ttl": module.params["session_ttl"],
        "tcp-halfclose-timer": module.params["tcp_halfclose_timer"],
        "tcp-halfopen-timer": module.params["tcp_halfopen_timer"],
        "tcp-portrange": module.params["tcp_portrange"],
        "tcp-timewait-timer": module.params["tcp_timewait_timer"],
        "udp-idle-timer": module.params["udp_idle_timer"],
        "udp-portrange": module.params["udp_portrange"],
        "visibility": module.params["visibility"],
    }

    # CHECK IF THE HOST/USERNAME/PW EXISTS, AND IF IT DOES, LOGIN.
    host = module.params["host"]
    username = module.params["username"]
    if host is None or username is None:
        module.fail_json(msg="Host and username are required")

    # CHECK IF LOGIN FAILED
    fmg = AnsibleFortiManager(module, module.params["host"], module.params["username"], module.params["password"])
    response = fmg.login()

    if response[1]['status']['code'] != 0:
        module.fail_json(msg="Connection to FortiManager Failed")

    # CHECK FOR CATEGORIES TO ADD
    # THIS IS ONLY WHEN OBJECT_TYPE ISN'T SPECIFICALLY ADDING A CATEGORY!
    # WE NEED TO ADD THE CATEGORY BEFORE ADDING THE OBJECT
    # IF ANY category ARE DEFINED AND MODE IS ADD OR SET LETS ADD THOSE
    # THIS IS A "BLIND ADD" AND THE EXIT CODE FOR OBJECT ALREADY EXISTS IS TREATED AS A PASS
    if paramgram["category"] is not None and paramgram["mode"] in ['add', 'set']\
            and paramgram["object_type"] != "category":
        categoryAdd = fmgr_fwobj_service_category(fmg, paramgram)
        if not categoryAdd[0] in [0, -2, -3]:
            module.fail_json(msg="Failed to add/remove service category", **categoryAdd[1])

    # IF OBJECT_TYPE IS CATEGORY...
    if paramgram["object_type"] == 'category':
        results = fmgr_fwobj_service_category(fmg, paramgram)
        if not results[0] in [0, -2, -3]:
            module.fail_json(msg="Failed to add/remove service category", **results[1])

    # IF OBJECT_TYPE IS CUSTOM...
    if paramgram["object_type"] == 'custom':
        results = fmgr_fwobj_service_custom(fmg, paramgram)
        if not results[0] in [0, -2, -3]:
            module.fail_json(msg="Failed to add/remove custom service", **results[1])

    # IF OBJECT_TYPE IS GROUP...
    if paramgram["object_type"] == 'group':
        results = fmgr_fwobj_service_group(fmg, paramgram)
        if not results[0] in [0, -2, -3]:
            module.fail_json(msg="Failed to add/remove service group", **results[1])

    fmg.logout()

    if results is not None:
        return module.exit_json(**results[1])
    else:
        return module.exit_json(msg="The service_type parameter wasn't set to category, group, or custom. Exiting...")


if __name__ == "__main__":
    main()
