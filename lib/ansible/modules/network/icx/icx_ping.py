#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = """
---
module: icx_ping
version_added: "2.9"
author: "Ruckus Wireless (@Commscope)"
short_description: Tests reachability using ping from Ruckus ICX 7000 series switches
description:
  - Tests reachability using ping from switch to a remote destination.
notes:
  - Tested against ICX 10.1
options:
    count:
      description:
        - Number of packets to send. Default is 1.
      type: int
    dest:
      description:
        - ip-addr | host-name | vrf vrf-name | ipv6 [ ipv6-addr | host-name | vrf vrf-name]  (resolvable by switch) of the remote node.
      required: true
      type: str
    timeout:
      description:
        - Specifies the time, in milliseconds for which the device waits for a reply from the pinged device.
          The value can range from 1 to 4294967296. The default is 5000 (5 seconds).
      type: int
    ttl:
      description:
        - Specifies the time to live as a maximum number of hops. The value can range from 1 to 255. The default is 64.
      type: int
    size:
      description:
        - Specifies the size of the ICMP data portion of the packet, in bytes. This is the payload and does not include the header.
          The value can range from 0 to 10000. The default is 16..
      type: int
    source:
      description:
        - IP address to be used as the origin of the ping packets.
      type: str
    vrf:
      description:
        - Specifies the Virtual Routing and Forwarding (VRF) instance of the device to be pinged.
      type: str
    state:
      description:
        - Determines if the expected result is success or fail.
      type: str
      choices: [ absent, present ]
      default: present
"""

EXAMPLES = r'''
- name: Test reachability to 10.10.10.10
  icx_ping:
    dest: 10.10.10.10

- name: Test reachability to ipv6 address from source with timeout
  icx_ping:
    dest: ipv6 2001:cdba:0000:0000:0000:0000:3257:9652
    source: 10.1.1.1
    timeout: 100000

- name: Test reachability to 10.1.1.1 through vrf using 5 packets
  icx_ping:
    dest: 10.1.1.1
    vrf: x.x.x.x
    count: 5

- name: Test unreachability to 10.30.30.30
  icx_ping:
    dest: 10.40.40.40
    state: absent

- name: Test reachability to ipv4 with ttl and packet size
  icx_ping:
    dest: 10.10.10.10
    ttl: 20
    size: 500
'''

RETURN = '''
commands:
  description: Show the command sent.
  returned: always
  type: list
  sample: ["ping 10.40.40.40 count 20 source loopback0", "ping 10.40.40.40"]
packet_loss:
  description: Percentage of packets lost.
  returned: always
  type: str
  sample: "0%"
packets_rx:
  description: Packets successfully received.
  returned: always
  type: int
  sample: 20
packets_tx:
  description: Packets successfully transmitted.
  returned: always
  type: int
  sample: 20
rtt:
  description: Show RTT stats.
  returned: always
  type: dict
  sample: {"avg": 2, "max": 8, "min": 1}
'''

from ansible.module_utils._text import to_text
from ansible.module_utils.network.icx.icx import run_commands
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.connection import Connection, ConnectionError
import re


def build_ping(dest, count=None, source=None, timeout=None, ttl=None, size=None, vrf=None):
    """
    Function to build the command to send to the terminal for the switch
    to execute. All args come from the module's unique params.
    """

    if vrf is not None:
        cmd = "ping vrf {0} {1}".format(vrf, dest)
    else:
        cmd = "ping {0}".format(dest)

    if count is not None:
        cmd += " count {0}".format(str(count))

    if timeout is not None:
        cmd += " timeout {0}".format(str(timeout))

    if ttl is not None:
        cmd += " ttl {0}".format(str(ttl))

    if size is not None:
        cmd += " size {0}".format(str(size))

    if source is not None:
        cmd += " source {0}".format(source)

    return cmd


def parse_ping(ping_stats):
    """
    Function used to parse the statistical information from the ping response.
    Example: "Success rate is 100 percent (5/5), round-trip min/avg/max=40/51/55 ms."
    Returns the percent of packet loss, received packets, transmitted packets, and RTT dict.
    """
    if ping_stats.startswith('Success'):
        rate_re = re.compile(r"^\w+\s+\w+\s+\w+\s+(?P<pct>\d+)\s+\w+\s+\((?P<rx>\d+)/(?P<tx>\d+)\)")
        rtt_re = re.compile(r".*,\s+\S+\s+\S+=(?P<min>\d+)/(?P<avg>\d+)/(?P<max>\d+)\s+\w+\.+\s*$|.*\s*$")

        rate = rate_re.match(ping_stats)
        rtt = rtt_re.match(ping_stats)
        return rate.group("pct"), rate.group("rx"), rate.group("tx"), rtt.groupdict()
    else:
        rate_re = re.compile(r"^Sending+\s+(?P<tx>\d+),")
        rate = rate_re.match(ping_stats)
        rtt = {'avg': 0, 'max': 0, 'min': 0}
        return 0, 0, rate.group('tx'), rtt


def validate_results(module, loss, results):
    """
    This function is used to validate whether the ping results were unexpected per "state" param.
    """
    state = module.params["state"]
    if state == "present" and loss == 100:
        module.fail_json(msg="Ping failed unexpectedly", **results)
    elif state == "absent" and loss < 100:
        module.fail_json(msg="Ping succeeded unexpectedly", **results)


def validate_fail(module, responses):
    if ("Success" in responses or "No reply" in responses) is False:
        module.fail_json(msg=responses)


def validate_parameters(module, timeout, count):
    if timeout and not 1 <= int(timeout) <= 4294967294:
        module.fail_json(msg="bad value for timeout - valid range (1-4294967294)")
    if count and not 1 <= int(count) <= 4294967294:
        module.fail_json(msg="bad value for count - valid range (1-4294967294)")


def main():
    """ main entry point for module execution
    """
    argument_spec = dict(
        count=dict(type="int"),
        dest=dict(type="str", required=True),
        timeout=dict(type="int"),
        ttl=dict(type="int"),
        size=dict(type="int"),
        source=dict(type="str"),
        state=dict(type="str", choices=["absent", "present"], default="present"),
        vrf=dict(type="str")
    )

    module = AnsibleModule(argument_spec=argument_spec)

    count = module.params["count"]
    dest = module.params["dest"]
    source = module.params["source"]
    timeout = module.params["timeout"]
    ttl = module.params["ttl"]
    size = module.params["size"]
    vrf = module.params["vrf"]
    results = {}
    warnings = list()

    if warnings:
        results["warnings"] = warnings

    response = ''
    try:
        validate_parameters(module, timeout, count)
        results["commands"] = [build_ping(dest, count, source, timeout, ttl, size, vrf)]
        ping_results = run_commands(module, commands=results["commands"])
        ping_results_list = ping_results[0].split("\n")

    except ConnectionError as exc:
        module.fail_json(msg=to_text(exc, errors='surrogate_then_replace'))

    validate_fail(module, ping_results[0])

    stats = ""
    statserror = ''
    for line in ping_results_list:
        if line.startswith('Sending'):
            statserror = line
        if line.startswith('Success'):
            stats = line
        elif line.startswith('No reply'):
            stats = statserror

    success, rx, tx, rtt = parse_ping(stats)
    loss = abs(100 - int(success))
    results["packet_loss"] = str(loss) + "%"
    results["packets_rx"] = int(rx)
    results["packets_tx"] = int(tx)

    # Convert rtt values to int
    for k, v in rtt.items():
        if rtt[k] is not None:
            rtt[k] = int(v)

    results["rtt"] = rtt

    validate_results(module, loss, results)

    module.exit_json(**results)


if __name__ == '__main__':
    main()
