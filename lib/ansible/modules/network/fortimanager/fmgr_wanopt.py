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

ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'metadata_version': '1.1'}

DOCUMENTATION = '''
---
module: fmgr_wanopt
version_added: "2.8"
author:
    - Luke Weighall (@lweighall)
    - Andrew Welsh (@Ghilli3)
    - Jim Huber (@p4r4n0y1ng)
short_description: WAN optimization
description:
  -  Manage WanOpt security profiles in FortiManager via API

options:
  adom:
    description:
      - The ADOM the configuration should belong to.
    required: false
    default: root

  host:
    description:
      - The FortiManager's Address.
    required: true

  username:
    description:
      - The username associated with the account.
    required: true

  password:
    description:
      - The password associated with the username account.
    required: true

  mode:
    description:
      - Sets one of three modes for managing the object.
      - Allows use of soft-adds instead of overwriting existing values
    choices: ['add', 'set', 'delete', 'update']
    required: false
    default: add

  transparent:
    description:
      - Enable/disable transparent mode.
      - choice | disable | Disable transparent mode. Client packets source addresses are changed to the source addres
      - choice | enable | Determine if WAN Optimization changes client packet source addresses. Affects the routing
    required: false
    choices: ["disable", "enable"]

  name:
    description:
      - Profile name.
    required: false

  comments:
    description:
      - Comment.
    required: false

  auth_group:
    description:
      - Optionally add an authentication group to restrict access to the WAN Optimization tunnel to peers in the authe
      - ntication group.
    required: false

  cifs:
    description:
      - EXPERTS ONLY! KNOWLEDGE OF FMGR JSON API IS REQUIRED!
      - List of multiple child objects to be added. Expects a list of dictionaries.
      - Dictionaries must use FortiManager API parameters, not the ansible ones listed below.
      - If submitted, all other prefixed sub-parameters ARE IGNORED.
      - This object is MUTUALLY EXCLUSIVE with its options.
      - We expect that you know what you are doing with these list parameters, and are leveraging the JSON API Guide.
      - WHEN IN DOUBT, USE THE SUB OPTIONS BELOW INSTEAD TO CREATE OBJECTS WITH MULTIPLE TASKS
    required: false

  cifs_byte_caching:
    description:
      - Enable/disable byte-caching for HTTP. Byte caching reduces the amount of traffic by caching file data sent acr
      - oss the WAN and in future serving if from the cache.
      - choice | disable | Disable HTTP byte-caching.
      - choice | enable | Enable HTTP byte-caching.
    required: false
    choices: ["disable", "enable"]

  cifs_log_traffic:
    description:
      - Enable/disable logging.
      - choice | disable | Disable logging.
      - choice | enable | Enable logging.
    required: false
    choices: ["disable", "enable"]

  cifs_port:
    description:
      - Single port number or port number range for CIFS. Only packets with a destination port number that matches thi
      - s port number or range are accepted by this profile.
    required: false

  cifs_prefer_chunking:
    description:
      - Select dynamic or fixed-size data chunking for HTTP WAN Optimization.
      - choice | dynamic | Select dynamic data chunking to help to detect persistent data chunks in a changed file or
      - choice | fix | Select fixed data chunking.
    required: false
    choices: ["dynamic", "fix"]

  cifs_secure_tunnel:
    description:
      - Enable/disable securing the WAN Opt tunnel using SSL. Secure and non-secure tunnels use the same TCP port (781
      - 0).
      - choice | disable | Disable SSL-secured tunnelling.
      - choice | enable | Enable SSL-secured tunnelling.
    required: false
    choices: ["disable", "enable"]

  cifs_status:
    description:
      - Enable/disable HTTP WAN Optimization.
      - choice | disable | Disable HTTP WAN Optimization.
      - choice | enable | Enable HTTP WAN Optimization.
    required: false
    choices: ["disable", "enable"]

  cifs_tunnel_sharing:
    description:
      - Tunnel sharing mode for aggressive/non-aggressive and/or interactive/non-interactive protocols.
      - choice | private | For profiles that accept aggressive protocols such as HTTP and FTP so that these aggressiv
      - choice | shared | For profiles that accept nonaggressive and non-interactive protocols.
      - choice | express-shared | For profiles that accept interactive protocols such as Telnet.
    required: false
    choices: ["private", "shared", "express-shared"]

  ftp:
    description:
      - EXPERTS ONLY! KNOWLEDGE OF FMGR JSON API IS REQUIRED!
      - List of multiple child objects to be added. Expects a list of dictionaries.
      - Dictionaries must use FortiManager API parameters, not the ansible ones listed below.
      - If submitted, all other prefixed sub-parameters ARE IGNORED.
      - This object is MUTUALLY EXCLUSIVE with its options.
      - We expect that you know what you are doing with these list parameters, and are leveraging the JSON API Guide.
      - WHEN IN DOUBT, USE THE SUB OPTIONS BELOW INSTEAD TO CREATE OBJECTS WITH MULTIPLE TASKS
    required: false

  ftp_byte_caching:
    description:
      - Enable/disable byte-caching for HTTP. Byte caching reduces the amount of traffic by caching file data sent acr
      - oss the WAN and in future serving if from the cache.
      - choice | disable | Disable HTTP byte-caching.
      - choice | enable | Enable HTTP byte-caching.
    required: false
    choices: ["disable", "enable"]

  ftp_log_traffic:
    description:
      - Enable/disable logging.
      - choice | disable | Disable logging.
      - choice | enable | Enable logging.
    required: false
    choices: ["disable", "enable"]

  ftp_port:
    description:
      - Single port number or port number range for FTP. Only packets with a destination port number that matches this
      -  port number or range are accepted by this profile.
    required: false

  ftp_prefer_chunking:
    description:
      - Select dynamic or fixed-size data chunking for HTTP WAN Optimization.
      - choice | dynamic | Select dynamic data chunking to help to detect persistent data chunks in a changed file or
      - choice | fix | Select fixed data chunking.
    required: false
    choices: ["dynamic", "fix"]

  ftp_secure_tunnel:
    description:
      - Enable/disable securing the WAN Opt tunnel using SSL. Secure and non-secure tunnels use the same TCP port (781
      - 0).
      - choice | disable | Disable SSL-secured tunnelling.
      - choice | enable | Enable SSL-secured tunnelling.
    required: false
    choices: ["disable", "enable"]

  ftp_status:
    description:
      - Enable/disable HTTP WAN Optimization.
      - choice | disable | Disable HTTP WAN Optimization.
      - choice | enable | Enable HTTP WAN Optimization.
    required: false
    choices: ["disable", "enable"]

  ftp_tunnel_sharing:
    description:
      - Tunnel sharing mode for aggressive/non-aggressive and/or interactive/non-interactive protocols.
      - choice | private | For profiles that accept aggressive protocols such as HTTP and FTP so that these aggressiv
      - choice | shared | For profiles that accept nonaggressive and non-interactive protocols.
      - choice | express-shared | For profiles that accept interactive protocols such as Telnet.
    required: false
    choices: ["private", "shared", "express-shared"]

  http:
    description:
      - EXPERTS ONLY! KNOWLEDGE OF FMGR JSON API IS REQUIRED!
      - List of multiple child objects to be added. Expects a list of dictionaries.
      - Dictionaries must use FortiManager API parameters, not the ansible ones listed below.
      - If submitted, all other prefixed sub-parameters ARE IGNORED.
      - This object is MUTUALLY EXCLUSIVE with its options.
      - We expect that you know what you are doing with these list parameters, and are leveraging the JSON API Guide.
      - WHEN IN DOUBT, USE THE SUB OPTIONS BELOW INSTEAD TO CREATE OBJECTS WITH MULTIPLE TASKS
    required: false

  http_byte_caching:
    description:
      - Enable/disable byte-caching for HTTP. Byte caching reduces the amount of traffic by caching file data sent acr
      - oss the WAN and in future serving if from the cache.
      - choice | disable | Disable HTTP byte-caching.
      - choice | enable | Enable HTTP byte-caching.
    required: false
    choices: ["disable", "enable"]

  http_log_traffic:
    description:
      - Enable/disable logging.
      - choice | disable | Disable logging.
      - choice | enable | Enable logging.
    required: false
    choices: ["disable", "enable"]

  http_port:
    description:
      - Single port number or port number range for HTTP. Only packets with a destination port number that matches thi
      - s port number or range are accepted by this profile.
    required: false

  http_prefer_chunking:
    description:
      - Select dynamic or fixed-size data chunking for HTTP WAN Optimization.
      - choice | dynamic | Select dynamic data chunking to help to detect persistent data chunks in a changed file or
      - choice | fix | Select fixed data chunking.
    required: false
    choices: ["dynamic", "fix"]

  http_secure_tunnel:
    description:
      - Enable/disable securing the WAN Opt tunnel using SSL. Secure and non-secure tunnels use the same TCP port (781
      - 0).
      - choice | disable | Disable SSL-secured tunnelling.
      - choice | enable | Enable SSL-secured tunnelling.
    required: false
    choices: ["disable", "enable"]

  http_ssl:
    description:
      - Enable/disable SSL/TLS offloading (hardware acceleration) for HTTPS traffic in this tunnel.
      - choice | disable | Disable SSL/TLS offloading.
      - choice | enable | Enable SSL/TLS offloading.
    required: false
    choices: ["disable", "enable"]

  http_ssl_port:
    description:
      - Port on which to expect HTTPS traffic for SSL/TLS offloading.
    required: false

  http_status:
    description:
      - Enable/disable HTTP WAN Optimization.
      - choice | disable | Disable HTTP WAN Optimization.
      - choice | enable | Enable HTTP WAN Optimization.
    required: false
    choices: ["disable", "enable"]

  http_tunnel_non_http:
    description:
      - Configure how to process non-HTTP traffic when a profile configured for HTTP traffic accepts a non-HTTP sessio
      - n. Can occur if an application sends non-HTTP traffic using an HTTP destination port.
      - choice | disable | Drop or tear down non-HTTP sessions accepted by the profile.
      - choice | enable | Pass non-HTTP sessions through the tunnel without applying protocol optimization, byte-cac
    required: false
    choices: ["disable", "enable"]

  http_tunnel_sharing:
    description:
      - Tunnel sharing mode for aggressive/non-aggressive and/or interactive/non-interactive protocols.
      - choice | private | For profiles that accept aggressive protocols such as HTTP and FTP so that these aggressiv
      - choice | shared | For profiles that accept nonaggressive and non-interactive protocols.
      - choice | express-shared | For profiles that accept interactive protocols such as Telnet.
    required: false
    choices: ["private", "shared", "express-shared"]

  http_unknown_http_version:
    description:
      - How to handle HTTP sessions that do not comply with HTTP 0.9, 1.0, or 1.1.
      - choice | best-effort | Assume all HTTP sessions comply with HTTP 0.9, 1.0, or 1.1. If a session uses a different
      - choice | reject | Reject or tear down HTTP sessions that do not use HTTP 0.9, 1.0, or 1.1.
      - choice | tunnel | Pass HTTP traffic that does not use HTTP 0.9, 1.0, or 1.1 without applying HTTP protocol o
    required: false
    choices: ["best-effort", "reject", "tunnel"]

  mapi:
    description:
      - EXPERTS ONLY! KNOWLEDGE OF FMGR JSON API IS REQUIRED!
      - List of multiple child objects to be added. Expects a list of dictionaries.
      - Dictionaries must use FortiManager API parameters, not the ansible ones listed below.
      - If submitted, all other prefixed sub-parameters ARE IGNORED.
      - This object is MUTUALLY EXCLUSIVE with its options.
      - We expect that you know what you are doing with these list parameters, and are leveraging the JSON API Guide.
      - WHEN IN DOUBT, USE THE SUB OPTIONS BELOW INSTEAD TO CREATE OBJECTS WITH MULTIPLE TASKS
    required: false

  mapi_byte_caching:
    description:
      - Enable/disable byte-caching for HTTP. Byte caching reduces the amount of traffic by caching file data sent acr
      - oss the WAN and in future serving if from the cache.
      - choice | disable | Disable HTTP byte-caching.
      - choice | enable | Enable HTTP byte-caching.
    required: false
    choices: ["disable", "enable"]

  mapi_log_traffic:
    description:
      - Enable/disable logging.
      - choice | disable | Disable logging.
      - choice | enable | Enable logging.
    required: false
    choices: ["disable", "enable"]

  mapi_port:
    description:
      - Single port number or port number range for MAPI. Only packets with a destination port number that matches thi
      - s port number or range are accepted by this profile.
    required: false

  mapi_secure_tunnel:
    description:
      - Enable/disable securing the WAN Opt tunnel using SSL. Secure and non-secure tunnels use the same TCP port (781
      - 0).
      - choice | disable | Disable SSL-secured tunnelling.
      - choice | enable | Enable SSL-secured tunnelling.
    required: false
    choices: ["disable", "enable"]

  mapi_status:
    description:
      - Enable/disable HTTP WAN Optimization.
      - choice | disable | Disable HTTP WAN Optimization.
      - choice | enable | Enable HTTP WAN Optimization.
    required: false
    choices: ["disable", "enable"]

  mapi_tunnel_sharing:
    description:
      - Tunnel sharing mode for aggressive/non-aggressive and/or interactive/non-interactive protocols.
      - choice | private | For profiles that accept aggressive protocols such as HTTP and FTP so that these aggressiv
      - choice | shared | For profiles that accept nonaggressive and non-interactive protocols.
      - choice | express-shared | For profiles that accept interactive protocols such as Telnet.
    required: false
    choices: ["private", "shared", "express-shared"]

  tcp:
    description:
      - EXPERTS ONLY! KNOWLEDGE OF FMGR JSON API IS REQUIRED!
      - List of multiple child objects to be added. Expects a list of dictionaries.
      - Dictionaries must use FortiManager API parameters, not the ansible ones listed below.
      - If submitted, all other prefixed sub-parameters ARE IGNORED.
      - This object is MUTUALLY EXCLUSIVE with its options.
      - We expect that you know what you are doing with these list parameters, and are leveraging the JSON API Guide.
      - WHEN IN DOUBT, USE THE SUB OPTIONS BELOW INSTEAD TO CREATE OBJECTS WITH MULTIPLE TASKS
    required: false

  tcp_byte_caching:
    description:
      - Enable/disable byte-caching for HTTP. Byte caching reduces the amount of traffic by caching file data sent acr
      - oss the WAN and in future serving if from the cache.
      - choice | disable | Disable HTTP byte-caching.
      - choice | enable | Enable HTTP byte-caching.
    required: false
    choices: ["disable", "enable"]

  tcp_byte_caching_opt:
    description:
      - Select whether TCP byte-caching uses system memory only or both memory and disk space.
      - choice | mem-only | Byte caching with memory only.
      - choice | mem-disk | Byte caching with memory and disk.
    required: false
    choices: ["mem-only", "mem-disk"]

  tcp_log_traffic:
    description:
      - Enable/disable logging.
      - choice | disable | Disable logging.
      - choice | enable | Enable logging.
    required: false
    choices: ["disable", "enable"]

  tcp_port:
    description:
      - Single port number or port number range for TCP. Only packets with a destination port number that matches this
      -  port number or range are accepted by this profile.
    required: false

  tcp_secure_tunnel:
    description:
      - Enable/disable securing the WAN Opt tunnel using SSL. Secure and non-secure tunnels use the same TCP port (781
      - 0).
      - choice | disable | Disable SSL-secured tunnelling.
      - choice | enable | Enable SSL-secured tunnelling.
    required: false
    choices: ["disable", "enable"]

  tcp_ssl:
    description:
      - Enable/disable SSL/TLS offloading.
      - choice | disable | Disable SSL/TLS offloading.
      - choice | enable | Enable SSL/TLS offloading.
    required: false
    choices: ["disable", "enable"]

  tcp_ssl_port:
    description:
      - Port on which to expect HTTPS traffic for SSL/TLS offloading.
    required: false

  tcp_status:
    description:
      - Enable/disable HTTP WAN Optimization.
      - choice | disable | Disable HTTP WAN Optimization.
      - choice | enable | Enable HTTP WAN Optimization.
    required: false
    choices: ["disable", "enable"]

  tcp_tunnel_sharing:
    description:
      - Tunnel sharing mode for aggressive/non-aggressive and/or interactive/non-interactive protocols.
      - choice | private | For profiles that accept aggressive protocols such as HTTP and FTP so that these aggressiv
      - choice | shared | For profiles that accept nonaggressive and non-interactive protocols.
      - choice | express-shared | For profiles that accept interactive protocols such as Telnet.
    required: false
    choices: ["private", "shared", "express-shared"]


'''

EXAMPLES = '''
  - name: DELETE Profile
    fmgr_wanopt:
      host: "{{inventory_hostname}}"
      username: "{{ username }}"
      password: "{{ password }}"
      name: "Ansible_WanOpt_Profile"
      mode: "delete"

  - name: Create FMGR_WANOPT_PROFILE
    fmgr_wanopt:
      host: "{{ inventory_hostname }}"
      username: "{{ username }}"
      password: "{{ password }}"
      mode: "set"
      adom: "root"
      transparent: "enable"
      name: "Ansible_WanOpt_Profile"
      comments: "Created by Ansible"
      cifs: {byte-caching: "enable",
              log-traffic: "enable",
              port: 80,
              prefer-chunking: "dynamic",
              status: "enable",
              tunnel-sharing: "private"}
      ftp: {byte-caching: "enable",
              log-traffic: "enable",
              port: 80,
              prefer-chunking: "dynamic",
              secure-tunnel: "disable",
              status: "enable",
              tunnel-sharing: "private"}
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

###############
# START METHODS
###############


def fmgr_wanopt_profile_addsetdelete(fmg, paramgram):
    """
    fmgr_wanopt_profile -- Your Description here, bruh
    """

    mode = paramgram["mode"]
    adom = paramgram["adom"]

    response = (-100000, {"msg": "Illegal or malformed paramgram discovered. System Exception"})
    url = ""
    datagram = {}

    # EVAL THE MODE PARAMETER FOR SET OR ADD
    if mode in ['set', 'add', 'update']:
        url = '/pm/config/adom/{adom}/obj/wanopt/profile'.format(adom=adom)
        datagram = fmgr_del_none(fmgr_prepare_dict(paramgram))

    # EVAL THE MODE PARAMETER FOR DELETE
    elif mode == "delete":
        # SET THE CORRECT URL FOR DELETE
        url = '/pm/config/adom/{adom}/obj/wanopt/profile/{name}'.format(adom=adom, name=paramgram["name"])
        datagram = {}

    # IF MODE = SET -- USE THE 'SET' API CALL MODE
    if mode == "set":
        response = fmg.set(url, datagram)
    # IF MODE = UPDATE -- USER THE 'UPDATE' API CALL MODE
    elif mode == "update":
        response = fmg.update(url, datagram)
    # IF MODE = ADD  -- USE THE 'ADD' API CALL MODE
    elif mode == "add":
        response = fmg.add(url, datagram)
    # IF MODE = DELETE  -- USE THE DELETE URL AND API CALL MODE
    elif mode == "delete":
        response = fmg.delete(url, datagram)

    return response


# ADDITIONAL COMMON FUNCTIONS
def fmgr_logout(fmg, module, msg="NULL", results=(), good_codes=(0,), logout_on_fail=True, logout_on_success=False):
    """
    THIS METHOD CONTROLS THE LOGOUT AND ERROR REPORTING AFTER AN METHOD OR FUNCTION RUNS
    """
    # VALIDATION ERROR (NO RESULTS, JUST AN EXIT)
    if msg != "NULL" and len(results) == 0:
        try:
            fmg.logout()
        except:
            pass
        module.fail_json(msg=msg)

    # SUBMISSION ERROR
    if len(results) > 0:
        if msg == "NULL":
            try:
                msg = results[1]['status']['message']
            except:
                msg = "No status message returned from pyFMG. Possible that this was a GET with a tuple result."

        if results[0] not in good_codes:
            if logout_on_fail:
                fmg.logout()
                module.fail_json(msg=msg, **results[1])
        else:
            if logout_on_success:
                fmg.logout()
                module.exit_json(msg="API Called worked, but logout handler has been asked to logout on success",
                                 **results[1])
    return msg


# FUNCTION/METHOD FOR CONVERTING CIDR TO A NETMASK
# DID NOT USE IP ADDRESS MODULE TO KEEP INCLUDES TO A MINIMUM
def fmgr_cidr_to_netmask(cidr):
    cidr = int(cidr)
    mask = (0xffffffff >> (32 - cidr)) << (32 - cidr)
    return(str((0xff000000 & mask) >> 24) + '.' +
           str((0x00ff0000 & mask) >> 16) + '.' +
           str((0x0000ff00 & mask) >> 8) + '.' +
           str((0x000000ff & mask)))


# utility function: removing keys wih value of None, nothing in playbook for that key
def fmgr_del_none(obj):
    if isinstance(obj, dict):
        return type(obj)((fmgr_del_none(k), fmgr_del_none(v))
                         for k, v in obj.items() if k is not None and (v is not None and not fmgr_is_empty_dict(v)))
    else:
        return obj


# utility function: remove keys that are need for the logic but the FMG API won't accept them
def fmgr_prepare_dict(obj):
    list_of_elems = ["mode", "adom", "host", "username", "password"]
    if isinstance(obj, dict):
        obj = dict((key, fmgr_prepare_dict(value)) for (key, value) in obj.items() if key not in list_of_elems)
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


def fmgr_split_comma_strings_into_lists(obj):
    if isinstance(obj, dict):
        if len(obj) > 0:
            for k, v in obj.items():
                if isinstance(v, str):
                    new_list = list()
                    if "," in v:
                        new_items = v.split(",")
                        for item in new_items:
                            new_list.append(item.strip())
                        obj[k] = new_list

    return obj


#############
# END METHODS
#############


def main():
    argument_spec = dict(
        adom=dict(type="str", default="root"),
        host=dict(required=True, type="str"),
        password=dict(fallback=(env_fallback, ["ANSIBLE_NET_PASSWORD"]), no_log=True, required=True),
        username=dict(fallback=(env_fallback, ["ANSIBLE_NET_USERNAME"]), no_log=True, required=True),
        mode=dict(choices=["add", "set", "delete", "update"], type="str", default="add"),

        transparent=dict(required=False, type="str", choices=["disable", "enable"]),
        name=dict(required=False, type="str"),
        comments=dict(required=False, type="str"),
        auth_group=dict(required=False, type="str"),
        cifs=dict(required=False, type="dict"),
        cifs_byte_caching=dict(required=False, type="str", choices=["disable", "enable"]),
        cifs_log_traffic=dict(required=False, type="str", choices=["disable", "enable"]),
        cifs_port=dict(required=False, type="str"),
        cifs_prefer_chunking=dict(required=False, type="str", choices=["dynamic", "fix"]),
        cifs_secure_tunnel=dict(required=False, type="str", choices=["disable", "enable"]),
        cifs_status=dict(required=False, type="str", choices=["disable", "enable"]),
        cifs_tunnel_sharing=dict(required=False, type="str", choices=["private", "shared", "express-shared"]),
        ftp=dict(required=False, type="dict"),
        ftp_byte_caching=dict(required=False, type="str", choices=["disable", "enable"]),
        ftp_log_traffic=dict(required=False, type="str", choices=["disable", "enable"]),
        ftp_port=dict(required=False, type="str"),
        ftp_prefer_chunking=dict(required=False, type="str", choices=["dynamic", "fix"]),
        ftp_secure_tunnel=dict(required=False, type="str", choices=["disable", "enable"]),
        ftp_status=dict(required=False, type="str", choices=["disable", "enable"]),
        ftp_tunnel_sharing=dict(required=False, type="str", choices=["private", "shared", "express-shared"]),
        http=dict(required=False, type="dict"),
        http_byte_caching=dict(required=False, type="str", choices=["disable", "enable"]),
        http_log_traffic=dict(required=False, type="str", choices=["disable", "enable"]),
        http_port=dict(required=False, type="str"),
        http_prefer_chunking=dict(required=False, type="str", choices=["dynamic", "fix"]),
        http_secure_tunnel=dict(required=False, type="str", choices=["disable", "enable"]),
        http_ssl=dict(required=False, type="str", choices=["disable", "enable"]),
        http_ssl_port=dict(required=False, type="str"),
        http_status=dict(required=False, type="str", choices=["disable", "enable"]),
        http_tunnel_non_http=dict(required=False, type="str", choices=["disable", "enable"]),
        http_tunnel_sharing=dict(required=False, type="str", choices=["private", "shared", "express-shared"]),
        http_unknown_http_version=dict(required=False, type="str", choices=["best-effort", "reject", "tunnel"]),
        mapi=dict(required=False, type="dict"),
        mapi_byte_caching=dict(required=False, type="str", choices=["disable", "enable"]),
        mapi_log_traffic=dict(required=False, type="str", choices=["disable", "enable"]),
        mapi_port=dict(required=False, type="str"),
        mapi_secure_tunnel=dict(required=False, type="str", choices=["disable", "enable"]),
        mapi_status=dict(required=False, type="str", choices=["disable", "enable"]),
        mapi_tunnel_sharing=dict(required=False, type="str", choices=["private", "shared", "express-shared"]),
        tcp=dict(required=False, type="dict"),
        tcp_byte_caching=dict(required=False, type="str", choices=["disable", "enable"]),
        tcp_byte_caching_opt=dict(required=False, type="str", choices=["mem-only", "mem-disk"]),
        tcp_log_traffic=dict(required=False, type="str", choices=["disable", "enable"]),
        tcp_port=dict(required=False, type="str"),
        tcp_secure_tunnel=dict(required=False, type="str", choices=["disable", "enable"]),
        tcp_ssl=dict(required=False, type="str", choices=["disable", "enable"]),
        tcp_ssl_port=dict(required=False, type="str"),
        tcp_status=dict(required=False, type="str", choices=["disable", "enable"]),
        tcp_tunnel_sharing=dict(required=False, type="str", choices=["private", "shared", "express-shared"]),

    )

    module = AnsibleModule(argument_spec, supports_check_mode=False)

    # MODULE PARAMGRAM
    paramgram = {
        "mode": module.params["mode"],
        "adom": module.params["adom"],
        "transparent": module.params["transparent"],
        "name": module.params["name"],
        "comments": module.params["comments"],
        "auth-group": module.params["auth_group"],
        "cifs": {
            "byte-caching": module.params["cifs_byte_caching"],
            "log-traffic": module.params["cifs_log_traffic"],
            "port": module.params["cifs_port"],
            "prefer-chunking": module.params["cifs_prefer_chunking"],
            "secure-tunnel": module.params["cifs_secure_tunnel"],
            "status": module.params["cifs_status"],
            "tunnel-sharing": module.params["cifs_tunnel_sharing"],
        },
        "ftp": {
            "byte-caching": module.params["ftp_byte_caching"],
            "log-traffic": module.params["ftp_log_traffic"],
            "port": module.params["ftp_port"],
            "prefer-chunking": module.params["ftp_prefer_chunking"],
            "secure-tunnel": module.params["ftp_secure_tunnel"],
            "status": module.params["ftp_status"],
            "tunnel-sharing": module.params["ftp_tunnel_sharing"],
        },
        "http": {
            "byte-caching": module.params["http_byte_caching"],
            "log-traffic": module.params["http_log_traffic"],
            "port": module.params["http_port"],
            "prefer-chunking": module.params["http_prefer_chunking"],
            "secure-tunnel": module.params["http_secure_tunnel"],
            "ssl": module.params["http_ssl"],
            "ssl-port": module.params["http_ssl_port"],
            "status": module.params["http_status"],
            "tunnel-non-http": module.params["http_tunnel_non_http"],
            "tunnel-sharing": module.params["http_tunnel_sharing"],
            "unknown-http-version": module.params["http_unknown_http_version"],
        },
        "mapi": {
            "byte-caching": module.params["mapi_byte_caching"],
            "log-traffic": module.params["mapi_log_traffic"],
            "port": module.params["mapi_port"],
            "secure-tunnel": module.params["mapi_secure_tunnel"],
            "status": module.params["mapi_status"],
            "tunnel-sharing": module.params["mapi_tunnel_sharing"],
        },
        "tcp": {
            "byte-caching": module.params["tcp_byte_caching"],
            "byte-caching-opt": module.params["tcp_byte_caching_opt"],
            "log-traffic": module.params["tcp_log_traffic"],
            "port": module.params["tcp_port"],
            "secure-tunnel": module.params["tcp_secure_tunnel"],
            "ssl": module.params["tcp_ssl"],
            "ssl-port": module.params["tcp_ssl_port"],
            "status": module.params["tcp_status"],
            "tunnel-sharing": module.params["tcp_tunnel_sharing"],
        }
    }

    list_overrides = ['cifs', 'ftp', 'http', 'mapi', 'tcp']
    for list_variable in list_overrides:
        override_data = list()
        try:
            override_data = module.params[list_variable]
        except:
            pass
        try:
            if override_data:
                del paramgram[list_variable]
                paramgram[list_variable] = override_data
        except:
            pass

    # CHECK IF THE HOST/USERNAME/PW EXISTS, AND IF IT DOES, LOGIN.
    host = module.params["host"]
    password = module.params["password"]
    username = module.params["username"]
    if host is None or username is None or password is None:
        module.fail_json(msg="Host and username and password are required")

    # CHECK IF LOGIN FAILED
    fmg = AnsibleFortiManager(module, module.params["host"], module.params["username"], module.params["password"])

    response = fmg.login()
    if response[1]['status']['code'] != 0:
        module.fail_json(msg="Connection to FortiManager Failed")

    results = fmgr_wanopt_profile_addsetdelete(fmg, paramgram)
    if results[0] != 0:
        fmgr_logout(fmg, module, results=results, good_codes=[0])

    fmg.logout()

    if results is not None:
        return module.exit_json(**results[1])
    else:
        return module.exit_json(msg="No results were returned from the API call.")


if __name__ == "__main__":
    main()
