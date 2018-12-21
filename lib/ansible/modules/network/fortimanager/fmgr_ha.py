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
author:
    - Luke Weighall (@lweighall)
    - Andrew Welsh (@Ghilli3)
    - Jim Huber (@p4r4n0y1ng)
short_description: Manages the High-Availability State of FortiManager Clusters and Nodes.
description: Change HA state or settings of FortiManager nodes (Standalone/Master/Slave).

options:
  host:
    description:
      - The FortiManager's address.
    required: true
  username:
    description:
      - The username to log into the FortiManager.
    required: true
  password:
    description:
      - The password associated with the username account.
    required: false
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
    host: "{{inventory_hostname}}"
    username: "{{ username }}"
    password: "{{ password }}"
    fmgr_ha_mode: "master"

- name: SET FORTIMANAGER HA NODE TO SLAVE
  fmgr_ha:
    host: "{{inventory_hostname}}"
    username: "{{ username }}"
    password: "{{ password }}"
    fmgr_ha_mode: "slave"

- name: SET FORTIMANAGER HA NODE TO STANDALONE
  fmgr_ha:
    host: "{{inventory_hostname}}"
    username: "{{ username }}"
    password: "{{ password }}"
    fmgr_ha_mode: "standalone"

- name: ADD FORTIMANAGER HA PEER
  fmgr_ha:
    host: "{{ inventory_hostname }}"
    username: "{{ username }}"
    password: "{{ password }}"
    fmgr_ha_peer_ipv4: "192.168.1.254"
    fmgr_ha_peer_sn: "FMG-VM1234567890"
    fmgr_ha_peer_status: "enable"

- name: CREATE CLUSTER ON MASTER
  fmgr_ha:
    host: "{{ inventory_hostname }}"
    username: "{{ username }}"
    password: "{{ password }}"
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

from ansible.module_utils.basic import AnsibleModule, env_fallback
from ansible.module_utils.network.fortimanager.fortimanager import AnsibleFortiManager

# Check for pyFMG lib
try:
    from pyFMG.fortimgr import FortiManager
    HAS_PYFMGR = True
except ImportError:
    HAS_PYFMGR = False


def fmgr_set_ha_mode(fmg, paramgram):
    """
    This method is used set the HA mode of a FortiManager Node
    """

    if paramgram["fmgr_ha_cluster_pw"] is not None and str.lower(paramgram["fmgr_ha_mode"]) != "standalone":
        datagram = {
            "mode": paramgram["fmgr_ha_mode"],
            "file-quota": paramgram["fmgr_ha_file_quota"],
            "hb-interval": paramgram["fmgr_ha_hb_interval"],
            "hb-lost-threshold": paramgram["fmgr_ha_hb_threshold"],
            "password": paramgram["fmgr_ha_cluster_pw"],
            "clusterid": paramgram["fmgr_ha_cluster_id"]
        }
    elif str.lower(paramgram["fmgr_ha_mode"]) == "standalone":
        datagram = {
            "mode": paramgram["fmgr_ha_mode"],
            "file-quota": paramgram["fmgr_ha_file_quota"],
            "hb-interval": paramgram["fmgr_ha_hb_interval"],
            "hb-lost-threshold": paramgram["fmgr_ha_hb_threshold"],
            "clusterid": paramgram["fmgr_ha_cluster_id"]
        }

    url = '/cli/global/system/ha'
    response = fmg.set(url, datagram)
    return response


def fmgr_get_ha_peer_list(fmg):
    """
    This method is used GET the HA PEERS of a FortiManager Node
    """

    datagram = {
        "method": "get"
    }

    url = '/cli/global/system/ha/peer/'
    response = fmg.get(url, datagram)
    return response


def fmgr_set_ha_peer(fmg, paramgram):
    """
    This method is used GET the HA PEERS of a FortiManager Node
    """

    datagram = {
        "ip": paramgram["fmgr_ha_peer_ipv4"],
        "ip6": paramgram["fmgr_ha_peer_ipv6"],
        "serial-number": paramgram["fmgr_ha_peer_sn"],
        "status": paramgram["fmgr_ha_peer_status"],
        "id": paramgram["peer_id"]
    }

    url = '/cli/global/system/ha/peer/'
    response = fmg.set(url, datagram)
    return response


# ADDITIONAL COMMON FUNCTIONS
# FUNCTION/METHOD FOR LOGGING OUT AND ANALYZING ERROR CODES
def fmgr_logout(fmg, module, msg="NULL", results=(), good_codes=(0,), logout_on_fail=True, logout_on_success=False):
    """
    THIS METHOD CONTROLS THE LOGOUT AND ERROR REPORTING AFTER AN METHOD OR FUNCTION RUNS
    """

    # VALIDATION ERROR (NO RESULTS, JUST AN EXIT)
    if msg != "NULL" and len(results) == 0:
        try:
            fmg.logout()
        except Exception:
            pass
        module.fail_json(msg=msg)

    # SUBMISSION ERROR
    if len(results) > 0:
        if msg == "NULL":
            try:
                msg = results[1]['status']['message']
            except Exception:
                msg = "No status message returned from pyFMG. Possible that this was a GET with a tuple result."

            if results[0] not in good_codes:
                if logout_on_fail:
                    fmg.logout()
                    module.fail_json(msg=msg, **results[1])
                else:
                    return
            else:
                if logout_on_success:
                    fmg.logout()
                    module.exit_json(msg=msg, **results[1])
                else:
                    return


def main():
    argument_spec = dict(
        host=dict(required=True, type="str"),
        password=dict(fallback=(env_fallback, ["ANSIBLE_NET_PASSWORD"]), no_log=True),
        username=dict(fallback=(env_fallback, ["ANSIBLE_NET_USERNAME"]), no_log=True),
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

    module = AnsibleModule(argument_spec, supports_check_mode=True,)

    # VALIDATE PARAMS BEFORE ATTEMPTING TO CONNECT
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
    # INIT FLAGS AND COUNTERS
    get_ha_peers = 0
    # validate required arguments are passed; not used in argument_spec to allow params to be called from provider
    # check if params are set
    if module.params["host"] is None or module.params["username"] is None:
        module.fail_json(msg="Host and username are required for connection")
    # CHECK IF LOGIN FAILED
    fmg = AnsibleFortiManager(module, module.params["host"], module.params["username"], module.params["password"],)
    response = fmg.login()
    if response[1]['status']['code'] != 0:
        module.fail_json(msg="Connection to FortiManager Failed")
    else:
        # START SESSION LOGIC
        # IF THE PEER SN DEFINED, BUT THE IPS ARE NOT, THEN QUIT
        if paramgram["fmgr_ha_peer_sn"] is not None:
            # CHANGE GET_HA_PEERS TO SHOW INTENT TO EDIT PEERS
            get_ha_peers = 1
            # DOUBLE CHECK THAT THE REST OF THE NEEDED PARAMETERS ARE THERE
            if paramgram["fmgr_ha_peer_ipv4"] is None and paramgram["fmgr_ha_peer_ipv6"] is None:
                fmgr_logout(fmg, module, msg="HA Peer Serial Number is defined but the "
                                             "IPv4 and IPv6 fields are empty."
                                             " Fill in the IPv4 or v6 parameters in the playbook")

        # IF THE PEER IPS ARE DEFINED, BUT NOT THE SERIAL NUMBER, THEN QUIT
        if paramgram["fmgr_ha_peer_ipv4"] is not None or paramgram["fmgr_ha_peer_ipv6"] is not None:
            # CHANGE GET_HA_PEERS TO SHOW INTENT TO EDIT PEERS
            get_ha_peers = 1
            # DOUBLE CHECK THAT THE REST OF THE NEEDED PARAMETERS ARE THERE
            if paramgram["fmgr_ha_peer_sn"] is None:
                fmgr_logout(fmg, module, msg="HA Peer IP Address is defined, but not the Peer Serial Number. "
                                             "Fill in the SN parameter in the playbook.")

        # IF THE PEER STATUS IS SET, BUT THE SERIAL NUMBER OR IP FIELDS AREN'T THERE, THEN EXIT
        if paramgram["fmgr_ha_peer_status"] is not None:
            # CHANGE GET_HA_PEERS TO SHOW INTENT TO EDIT PEERS
            get_ha_peers = 1
            # DOUBLE CHECK THAT THE REST OF THE NEEDED PARAMETERS ARE THERE
            if paramgram["fmgr_ha_peer_ipv4"] is None and paramgram["fmgr_ha_peer_sn"] is None:
                if paramgram["fmgr_ha_peer_sn"] is None and paramgram["fmgr_ha_peer_ipv6"] is None:
                    fmgr_logout(fmg, module, msg="HA Peer Status was defined, but nothing "
                                                 "to identify the peer was set. "
                                                 "Fill in one of"
                                                 " three parameters peer_ipv4 or v6 or serial_num")

        # IF HA MODE IS NOT NULL, SWITCH THAT
        if paramgram["fmgr_ha_mode"] is not None:
            if (str.lower(paramgram["fmgr_ha_mode"]) != "standalone" and paramgram["fmgr_ha_cluster_pw"] is not None)\
                    or str.lower(paramgram["fmgr_ha_mode"]) == "standalone":
                results = fmgr_set_ha_mode(fmg, paramgram)
                if results[0] != 0:
                    fmgr_logout(fmg, module, results=results, good_codes=[0],
                                msg="Failed to edit HA configuration the HA Peer")
            elif str.lower(paramgram["fmgr_ha_mode"]) != "standalone" and \
                    paramgram["fmgr_ha_mode"] is not None and paramgram["fmgr_ha_cluster_pw"] is None:
                fmgr_logout(fmg, module, msg="If setting HA Mode of MASTER or SLAVE, "
                                             "you must specify a cluster password")

        # IF GET_HA_PEERS IS ENABLED, LETS PROCESS THE PEERS

        if get_ha_peers == 1:
            # GET THE CURRENT LIST OF PEERS FROM THE NODE
            peers = fmgr_get_ha_peer_list(fmg)
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
                    except Exception:
                        pass
                    # ADVANCE THE LOOP AND REPEAT UNTIL DONE
                    peer_loopcount += 1

            # IF THE PEER STATUS ISN'T IN THE PLAYBOOK, ASSUME ITS ENABLE
            if paramgram["fmgr_ha_peer_status"] is None:
                paramgram["fmgr_ha_peer_status"] = "enable"

            # IF THE PEER STATUS IS ENABLE, USE THE next_peer_id IN THE API CALL FOR THE ID
            if paramgram["fmgr_ha_peer_status"] == "enable":
                results = fmgr_set_ha_peer(fmg, paramgram)
                if results[0] != 0:
                    fmgr_logout(fmg, module, results=results, good_codes=[0], msg="Failed to Enable the HA Peer")

            # IF THE PEER STATUS IS DISABLE, WE HAVE TO HANDLE THAT A BIT DIFFERENTLY
            # JUST USING TWO DIFFERENT peer_id 's HERE
            if paramgram["fmgr_ha_peer_status"] == "disable":
                results = fmgr_set_ha_peer(fmg, paramgram)
                if results[0] != 0:
                    fmgr_logout(fmg, module, results=results, good_codes=[0], msg="Failed to Disable the HA Peer")

        fmg.logout()
        return module.exit_json(**results[1])


if __name__ == "__main__":
    main()
