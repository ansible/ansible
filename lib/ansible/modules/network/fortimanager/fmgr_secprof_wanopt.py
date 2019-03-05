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
module: fmgr_secprof_wanopt
version_added: "2.8"
notes:
    - Full Documentation at U(https://ftnt-ansible-docs.readthedocs.io/en/latest/).
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
    required: false
    choices:
      - disable
      - enable

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
      - Optionally add an authentication group to restrict access to the WAN Optimization tunnel to
        peers in the authentication group.
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
      - Enable/disable byte-caching for HTTP. Byte caching reduces the amount of traffic by caching
        file data sent across the WAN and in future serving if from the cache.
    required: false
    choices:
      - disable
      - enable

  cifs_log_traffic:
    description:
      - Enable/disable logging.
    required: false
    choices:
      - disable
      - enable

  cifs_port:
    description:
      - Single port number or port number range for CIFS. Only packets with a destination port number
        that matches this port number or range are accepted by this profile.
    required: false

  cifs_prefer_chunking:
    description:
      - Select dynamic or fixed-size data chunking for HTTP WAN Optimization.
    required: false
    choices:
      - dynamic
      - fix

  cifs_secure_tunnel:
    description:
      - Enable/disable securing the WAN Opt tunnel using SSL. Secure and non-secure tunnels use the
        same TCP port (7810).
    required: false
    choices:
      - disable
      - enable

  cifs_status:
    description:
      - Enable/disable HTTP WAN Optimization.
    required: false
    choices:
      - disable
      - enable

  cifs_tunnel_sharing:
    description:
      - Tunnel sharing mode for aggressive/non-aggressive and/or interactive/non-interactive protocols.
    required: false
    choices:
      - private
      - shared
      - express-shared

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
      - Enable/disable byte-caching for HTTP. Byte caching reduces the amount of traffic by caching
        file data sent across the WAN and in future serving if from the cache.
    required: false
    choices:
      - disable
      - enable

  ftp_log_traffic:
    description:
      - Enable/disable logging.
    required: false
    choices:
      - disable
      - enable

  ftp_port:
    description:
      - Single port number or port number range for FTP. Only packets with a destination port number
        that matches this port number or range are accepted by this profile.
    required: false

  ftp_prefer_chunking:
    description:
      - Select dynamic or fixed-size data chunking for HTTP WAN Optimization.
    required: false
    choices:
      - dynamic
      - fix

  ftp_secure_tunnel:
    description:
      - Enable/disable securing the WAN Opt tunnel using SSL. Secure and non-secure tunnels use the
        same TCP port (7810).
    required: false
    choices:
      - disable
      - enable

  ftp_status:
    description:
      - Enable/disable HTTP WAN Optimization.
    required: false
    choices:
      - disable
      - enable

  ftp_tunnel_sharing:
    description:
      - Tunnel sharing mode for aggressive/non-aggressive and/or interactive/non-interactive protocols.
    required: false
    choices:
      - private
      - shared
      - express-shared

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
      - Enable/disable byte-caching for HTTP. Byte caching reduces the amount of traffic by caching
        file data sent across the WAN and in future serving if from the cache.
    required: false
    choices:
      - disable
      - enable

  http_log_traffic:
    description:
      - Enable/disable logging.
    required: false
    choices:
      - disable
      - enable

  http_port:
    description:
      - Single port number or port number range for HTTP. Only packets with a destination port number
        that matches this port number or range are accepted by this profile.
    required: false

  http_prefer_chunking:
    description:
      - Select dynamic or fixed-size data chunking for HTTP WAN Optimization.
    required: false
    choices:
      - dynamic
      - fix

  http_secure_tunnel:
    description:
      - Enable/disable securing the WAN Opt tunnel using SSL. Secure and non-secure tunnels use the
        same TCP port (7810).
    required: false
    choices:
      - disable
      - enable

  http_ssl:
    description:
      - Enable/disable SSL/TLS offloading (hardware acceleration) for HTTPS traffic in this tunnel.
    required: false
    choices:
      - disable
      - enable

  http_ssl_port:
    description:
      - Port on which to expect HTTPS traffic for SSL/TLS offloading.
    required: false

  http_status:
    description:
      - Enable/disable HTTP WAN Optimization.
    required: false
    choices:
      - disable
      - enable

  http_tunnel_non_http:
    description:
      - Configure how to process non-HTTP traffic when a profile configured for HTTP traffic accepts
        a non-HTTP session. Can occur if an application sends non-HTTP traffic using an HTTP destination port.
    required: false
    choices:
      - disable
      - enable

  http_tunnel_sharing:
    description:
      - Tunnel sharing mode for aggressive/non-aggressive and/or interactive/non-interactive protocols.
    required: false
    choices:
      - private
      - shared
      - express-shared

  http_unknown_http_version:
    description:
      - How to handle HTTP sessions that do not comply with HTTP 0.9, 1.0, or 1.1.
    required: false
    choices:
      - best-effort
      - reject
      - tunnel

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
      - Enable/disable byte-caching for HTTP. Byte caching reduces the amount of traffic by caching
        file data sent across the WAN and in future serving if from the cache.
    required: false
    choices:
      - disable
      - enable

  mapi_log_traffic:
    description:
      - Enable/disable logging.
    required: false
    choices:
      - disable
      - enable

  mapi_port:
    description:
      - Single port number or port number range for MAPI. Only packets with a destination port number
        that matches this port number or range are accepted by this profile.
    required: false

  mapi_secure_tunnel:
    description:
      - Enable/disable securing the WAN Opt tunnel using SSL. Secure and non-secure tunnels use the
        same TCP port (7810).
    required: false
    choices:
      - disable
      - enable

  mapi_status:
    description:
      - Enable/disable HTTP WAN Optimization.
    required: false
    choices:
      - disable
      - enable

  mapi_tunnel_sharing:
    description:
      - Tunnel sharing mode for aggressive/non-aggressive and/or interactive/non-interactive protocols.
    required: false
    choices:
      - private
      - shared
      - express-shared

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
      - Enable/disable byte-caching for HTTP. Byte caching reduces the amount of traffic by caching
        file data sent across the WAN and in future serving if from the cache.
    required: false
    choices:
      - disable
      - enable

  tcp_byte_caching_opt:
    description:
      - Select whether TCP byte-caching uses system memory only or both memory and disk space.
    required: false
    choices:
      - mem-only
      - mem-disk

  tcp_log_traffic:
    description:
      - Enable/disable logging.
    required: false
    choices:
      - disable
      - enable

  tcp_port:
    description:
      - Single port number or port number range for TCP. Only packets with a destination port number
        that matches this port number or range are accepted by this profile.
    required: false

  tcp_secure_tunnel:
    description:
      - Enable/disable securing the WAN Opt tunnel using SSL. Secure and non-secure tunnels use the
        same TCP port (7810).
    required: false
    choices:
      - disable
      - enable

  tcp_ssl:
    description:
      - Enable/disable SSL/TLS offloading.
    required: false
    choices:
      - disable
      - enable

  tcp_ssl_port:
    description:
      - Port on which to expect HTTPS traffic for SSL/TLS offloading.
    required: false

  tcp_status:
    description:
      - Enable/disable HTTP WAN Optimization.
    required: false
    choices:
      - disable
      - enable

  tcp_tunnel_sharing:
    description:
      - Tunnel sharing mode for aggressive/non-aggressive and/or interactive/non-interactive protocols.
    required: false
    choices:
      - private
      - shared
      - express-shared

'''

EXAMPLES = '''
  - name: DELETE Profile
    fmgr_secprof_wanopt:
      name: "Ansible_WanOpt_Profile"
      mode: "delete"

  - name: Create FMGR_WANOPT_PROFILE
    fmgr_secprof_wanopt:
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
  type: str
"""

from ansible.module_utils.basic import AnsibleModule, env_fallback
from ansible.module_utils.connection import Connection
from ansible.module_utils.network.fortimanager.fortimanager import FortiManagerHandler
from ansible.module_utils.network.fortimanager.common import FMGBaseException
from ansible.module_utils.network.fortimanager.common import FMGRCommon
from ansible.module_utils.network.fortimanager.common import DEFAULT_RESULT_OBJ
from ansible.module_utils.network.fortimanager.common import FAIL_SOCKET_MSG
from ansible.module_utils.network.fortimanager.common import prepare_dict
from ansible.module_utils.network.fortimanager.common import scrub_dict


###############
# START METHODS
###############


def fmgr_wanopt_profile_modify(fmgr, paramgram):
    """
    :param fmgr: The fmgr object instance from fortimanager.py
    :type fmgr: class object
    :param paramgram: The formatted dictionary of options to process
    :type paramgram: dict
    :return: The response from the FortiManager
    :rtype: dict
    """

    mode = paramgram["mode"]
    adom = paramgram["adom"]

    response = DEFAULT_RESULT_OBJ
    url = ""
    datagram = {}

    # EVAL THE MODE PARAMETER FOR SET OR ADD
    if mode in ['set', 'add', 'update']:
        url = '/pm/config/adom/{adom}/obj/wanopt/profile'.format(adom=adom)
        datagram = scrub_dict(prepare_dict(paramgram))

    # EVAL THE MODE PARAMETER FOR DELETE
    elif mode == "delete":
        # SET THE CORRECT URL FOR DELETE
        url = '/pm/config/adom/{adom}/obj/wanopt/profile/{name}'.format(adom=adom, name=paramgram["name"])
        datagram = {}

    response = fmgr.process_request(url, datagram, paramgram["mode"])

    return response


#############
# END METHODS
#############


def main():
    argument_spec = dict(
        adom=dict(type="str", default="root"),
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

    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=False, )
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
    module.paramgram = paramgram
    fmgr = None
    if module._socket_path:
        connection = Connection(module._socket_path)
        fmgr = FortiManagerHandler(connection, module)
        fmgr.tools = FMGRCommon()
    else:
        module.fail_json(**FAIL_SOCKET_MSG)

    list_overrides = ['cifs', 'ftp', 'http', 'mapi', 'tcp']
    paramgram = fmgr.tools.paramgram_child_list_override(list_overrides=list_overrides,
                                                         paramgram=paramgram, module=module)

    results = DEFAULT_RESULT_OBJ

    try:
        results = fmgr_wanopt_profile_modify(fmgr, paramgram)
        fmgr.govern_response(module=module, results=results,
                             ansible_facts=fmgr.construct_ansible_facts(results, module.params, paramgram))

    except Exception as err:
        raise FMGBaseException(err)

    return module.exit_json(**results[1])


if __name__ == "__main__":
    main()
