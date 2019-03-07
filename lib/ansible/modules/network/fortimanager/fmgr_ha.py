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
module: fmgr_ha
version_added: "2.8"
notes:
    - Full Documentation at U(https://ftnt-ansible-docs.readthedocs.io/en/latest/).
author:
    - Luke Weighall (@lweighall)
    - Andrew Welsh (@Ghilli3)
    - Jim Huber (@p4r4n0y1ng)
short_description: Manages the High-Availability State of FortiManager Clusters and Nodes.
description: Change HA state or settings of FortiManager nodes (Standalone/Master/Slave).

options:
  fmgr_ha_mode:
    description:
      - Sets the role of the FortiManager host for HA.
    required: false
    choices: ["standalone", "master", "slave"]

  fmgr_ha_peer_ipv4:
    description:
      - Sets the IPv4 address of a HA peer.
    required: false

  fmgr_ha_peer_ipv6:
    description:
      - Sets the IPv6 address of a HA peer.
    required: false

  fmgr_ha_peer_sn:
    description:
      - Sets the HA Peer Serial Number.
    required: false

  fmgr_ha_peer_status:
    description:
      - Sets the peer status to enable or disable.
    required: false
    choices: ["enable", "disable"]

  fmgr_ha_cluster_pw:
    description:
      - Sets the password for the HA cluster. Only required once. System remembers between HA mode switches.
    required: false

  fmgr_ha_cluster_id:
    description:
      - Sets the ID number of the HA cluster. Defaults to 1.
    required: false
    default: 1

  fmgr_ha_hb_threshold:
    description:
      - Sets heartbeat lost threshold (1-255).
    required: false
    default: 3

  fmgr_ha_hb_interval:
    description:
      - Sets the heartbeat interval (1-255).
    required: false
    default: 5

  fmgr_ha_file_quota:
    description:
      - Sets the File quota in MB (2048-20480).
    required: false
    default: 4096
'''


EXAMPLES = '''
- name: SET FORTIMANAGER HA NODE TO MASTER
  fmgr_ha:
    fmgr_ha_mode: "master"
    fmgr_ha_cluster_pw: "fortinet"
    fmgr_ha_cluster_id: "1"

- name: SET FORTIMANAGER HA NODE TO SLAVE
  fmgr_ha:
    fmgr_ha_mode: "slave"
    fmgr_ha_cluster_pw: "fortinet"
    fmgr_ha_cluster_id: "1"

- name: SET FORTIMANAGER HA NODE TO STANDALONE
  fmgr_ha:
    fmgr_ha_mode: "standalone"

- name: ADD FORTIMANAGER HA PEER
  fmgr_ha:
    fmgr_ha_peer_ipv4: "192.168.1.254"
    fmgr_ha_peer_sn: "FMG-VM1234567890"
    fmgr_ha_peer_status: "enable"

- name: CREATE CLUSTER ON MASTER
  fmgr_ha:
    fmgr_ha_mode: "master"
    fmgr_ha_cluster_pw: "fortinet"
    fmgr_ha_cluster_id: "1"
    fmgr_ha_hb_threshold: "10"
    fmgr_ha_hb_interval: "15"
    fmgr_ha_file_quota: "2048"
'''
RETURN = """
api_result:
  description: full API response, includes status code and message
  returned: always
  type: str
"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.connection import Connection
from ansible.module_utils.network.fortimanager.fortimanager import FortiManagerHandler
from ansible.module_utils.network.fortimanager.common import FMGBaseException
from ansible.module_utils.network.fortimanager.common import FMGRCommon
from ansible.module_utils.network.fortimanager.common import FMGRMethods
from ansible.module_utils.network.fortimanager.common import DEFAULT_RESULT_OBJ
from ansible.module_utils.network.fortimanager.common import FAIL_SOCKET_MSG


def fmgr_set_ha_mode(fmgr, paramgram):
    """
    :param fmgr: The fmgr object instance from fortimanager.py
    :type fmgr: class object
    :param paramgram: The formatted dictionary of options to process
    :type paramgram: dict
    :return: The response from the FortiManager
    :rtype: dict
    """
    # INIT A BASIC OBJECTS
    response = DEFAULT_RESULT_OBJ
    url = ""
    datagram = {}

    if paramgram["fmgr_ha_cluster_pw"] is not None and str(paramgram["fmgr_ha_mode"].lower()) != "standalone":
        datagram = {
            "mode": paramgram["fmgr_ha_mode"],
            "file-quota": paramgram["fmgr_ha_file_quota"],
            "hb-interval": paramgram["fmgr_ha_hb_interval"],
            "hb-lost-threshold": paramgram["fmgr_ha_hb_threshold"],
            "password": paramgram["fmgr_ha_cluster_pw"],
            "clusterid": paramgram["fmgr_ha_cluster_id"]
        }
    elif str(paramgram["fmgr_ha_mode"].lower()) == "standalone":
        datagram = {
            "mode": paramgram["fmgr_ha_mode"],
            "file-quota": paramgram["fmgr_ha_file_quota"],
            "hb-interval": paramgram["fmgr_ha_hb_interval"],
            "hb-lost-threshold": paramgram["fmgr_ha_hb_threshold"],
            "clusterid": paramgram["fmgr_ha_cluster_id"]
        }

    url = '/cli/global/system/ha'
    response = fmgr.process_request(url, datagram, FMGRMethods.SET)
    return response


def fmgr_get_ha_peer_list(fmgr):
    """
    :param fmgr: The fmgr object instance from fortimanager.py
    :type fmgr: class object
    :param paramgram: The formatted dictionary of options to process
    :type paramgram: dict
    :return: The response from the FortiManager
    :rtype: dict
    """
    # INIT A BASIC OBJECTS
    response = DEFAULT_RESULT_OBJ

    datagram = {}
    paramgram = {}

    url = '/cli/global/system/ha/peer/'
    response = fmgr.process_request(url, datagram, FMGRMethods.GET)
    return response


def fmgr_set_ha_peer(fmgr, paramgram):
    """
    :param fmgr: The fmgr object instance from fortimanager.py
    :type fmgr: class object
    :param paramgram: The formatted dictionary of options to process
    :type paramgram: dict
    :return: The response from the FortiManager
    :rtype: dict
    """

    datagram = {
        "ip": paramgram["fmgr_ha_peer_ipv4"],
        "ip6": paramgram["fmgr_ha_peer_ipv6"],
        "serial-number": paramgram["fmgr_ha_peer_sn"],
        "status": paramgram["fmgr_ha_peer_status"],
        "id": paramgram["peer_id"]
    }

    url = '/cli/global/system/ha/peer/'
    response = fmgr.process_request(url, datagram, FMGRMethods.SET)
    return response


def main():
    argument_spec = dict(
        fmgr_ha_mode=dict(required=False, type="str", choices=["standalone", "master", "slave"]),
        fmgr_ha_cluster_pw=dict(required=False, type="str", no_log=True),
        fmgr_ha_peer_status=dict(required=False, type="str", choices=["enable", "disable"]),
        fmgr_ha_peer_sn=dict(required=False, type="str"),
        fmgr_ha_peer_ipv4=dict(required=False, type="str"),
        fmgr_ha_peer_ipv6=dict(required=False, type="str"),
        fmgr_ha_hb_threshold=dict(required=False, type="int", default=3),
        fmgr_ha_hb_interval=dict(required=False, type="int", default=5),
        fmgr_ha_file_quota=dict(required=False, type="int", default=4096),
        fmgr_ha_cluster_id=dict(required=False, type="int", default=1)
    )

    required_if = [
        ['fmgr_ha_peer_ipv4', 'present', ['fmgr_ha_peer_sn', 'fmgr_ha_peer_status']],
        ['fmgr_ha_peer_ipv6', 'present', ['fmgr_ha_peer_sn', 'fmgr_ha_peer_status']],
        ['fmgr_ha_mode', 'master', ['fmgr_ha_cluster_pw', 'fmgr_ha_cluster_id']],
        ['fmgr_ha_mode', 'slave', ['fmgr_ha_cluster_pw', 'fmgr_ha_cluster_id']],
    ]

    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=False, required_if=required_if)
    paramgram = {
        "fmgr_ha_mode": module.params["fmgr_ha_mode"],
        "fmgr_ha_cluster_pw": module.params["fmgr_ha_cluster_pw"],
        "fmgr_ha_peer_status": module.params["fmgr_ha_peer_status"],
        "fmgr_ha_peer_sn": module.params["fmgr_ha_peer_sn"],
        "fmgr_ha_peer_ipv4": module.params["fmgr_ha_peer_ipv4"],
        "fmgr_ha_peer_ipv6": module.params["fmgr_ha_peer_ipv6"],
        "fmgr_ha_hb_threshold": module.params["fmgr_ha_hb_threshold"],
        "fmgr_ha_hb_interval": module.params["fmgr_ha_hb_interval"],
        "fmgr_ha_file_quota": module.params["fmgr_ha_file_quota"],
        "fmgr_ha_cluster_id": module.params["fmgr_ha_cluster_id"],
    }
    module.paramgram = paramgram
    fmgr = None
    if module._socket_path:
        connection = Connection(module._socket_path)
        fmgr = FortiManagerHandler(connection, module)
        fmgr.tools = FMGRCommon()
    else:
        module.fail_json(**FAIL_SOCKET_MSG)

    # INIT FLAGS AND COUNTERS
    get_ha_peers = 0
    results = DEFAULT_RESULT_OBJ
    try:
        if any(v is not None for v in (paramgram["fmgr_ha_peer_sn"], paramgram["fmgr_ha_peer_ipv4"],
                                       paramgram["fmgr_ha_peer_ipv6"], paramgram["fmgr_ha_peer_status"])):
            get_ha_peers = 1
    except Exception as err:
        raise FMGBaseException(err)
    try:
        # IF HA MODE IS NOT NULL, SWITCH THAT
        if paramgram["fmgr_ha_mode"] is not None:
            if (str.lower(paramgram["fmgr_ha_mode"]) != "standalone" and paramgram["fmgr_ha_cluster_pw"] is not None)\
                    or str.lower(paramgram["fmgr_ha_mode"]) == "standalone":
                results = fmgr_set_ha_mode(fmgr, paramgram)
                fmgr.govern_response(module=module, results=results, stop_on_success=False,
                                     ansible_facts=fmgr.construct_ansible_facts(results, module.params, paramgram))

            elif str.lower(paramgram["fmgr_ha_mode"]) != "standalone" and\
                    paramgram["fmgr_ha_mode"] is not None and\
                    paramgram["fmgr_ha_cluster_pw"] is None:
                module.exit_json(msg="If setting HA Mode of MASTER or SLAVE, you must specify a cluster password")

    except Exception as err:
        raise FMGBaseException(err)
        # IF GET_HA_PEERS IS ENABLED, LETS PROCESS THE PEERS
    try:
        if get_ha_peers == 1:
            # GET THE CURRENT LIST OF PEERS FROM THE NODE
            peers = fmgr_get_ha_peer_list(fmgr)
            # GET LENGTH OF RETURNED PEERS LIST AND ADD ONE FOR THE NEXT ID
            paramgram["next_peer_id"] = len(peers[1]) + 1
            # SET THE ACTUAL NUMBER OF PEERS
            num_of_peers = len(peers[1])
            # SET THE PEER ID FOR DISABLE METHOD
            paramgram["peer_id"] = len(peers) - 1
            # SET THE PEER LOOPCOUNT TO 1 TO START THE LOOP
            peer_loopcount = 1

            # LOOP THROUGH PEERS TO FIND THE SERIAL NUMBER MATCH TO GET THE RIGHT PEER ID
            # IDEA BEING WE DON'T WANT TO SUBMIT A BAD peer_id THAT DOESN'T JIVE WITH CURRENT DB ON FMG
            # SO LETS SEARCH FOR IT, AND IF WE FIND IT, WE WILL CHANGE THE PEER ID VARIABLES TO MATCH
            # IF NOT FOUND, LIFE GOES ON AND WE ASSUME THAT WE'RE ADDING A PEER
            # AT WHICH POINT THE next_peer_id VARIABLE WILL HAVE THE RIGHT PRIMARY KEY

            if paramgram["fmgr_ha_peer_sn"] is not None:
                while peer_loopcount <= num_of_peers:
                    # GET THE SERIAL NUMBER FOR CURRENT PEER IN LOOP TO COMPARE TO SN IN PLAYBOOK
                    try:
                        sn_compare = peers[1][peer_loopcount - 1]["serial-number"]
                        # IF THE SN IN THE PEERS MATCHES THE PLAYBOOK SN, SET THE IDS
                        if sn_compare == paramgram["fmgr_ha_peer_sn"]:
                            paramgram["peer_id"] = peer_loopcount
                            paramgram["next_peer_id"] = paramgram["peer_id"]
                    except Exception as err:
                        raise FMGBaseException(err)
                    # ADVANCE THE LOOP AND REPEAT UNTIL DONE
                    peer_loopcount += 1

            # IF THE PEER STATUS ISN'T IN THE PLAYBOOK, ASSUME ITS ENABLE
            if paramgram["fmgr_ha_peer_status"] is None:
                paramgram["fmgr_ha_peer_status"] = "enable"

            # IF THE PEER STATUS IS ENABLE, USE THE next_peer_id IN THE API CALL FOR THE ID
            if paramgram["fmgr_ha_peer_status"] == "enable":
                results = fmgr_set_ha_peer(fmgr, paramgram)
                fmgr.govern_response(module=module, results=results, stop_on_success=True,
                                     ansible_facts=fmgr.construct_ansible_facts(results,
                                                                                module.params, paramgram))

            # IF THE PEER STATUS IS DISABLE, WE HAVE TO HANDLE THAT A BIT DIFFERENTLY
            # JUST USING TWO DIFFERENT peer_id 's HERE
            if paramgram["fmgr_ha_peer_status"] == "disable":
                results = fmgr_set_ha_peer(fmgr, paramgram)
                fmgr.govern_response(module=module, results=results, stop_on_success=True,
                                     ansible_facts=fmgr.construct_ansible_facts(results, module.params, paramgram))

    except Exception as err:
        raise FMGBaseException(err)

    return module.exit_json(**results[1])


if __name__ == "__main__":
    main()
