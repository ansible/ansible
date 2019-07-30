#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2019, Ansible by Red Hat, inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'network'}

DOCUMENTATION = """
---
module: junos_ping
short_description: Tests reachability using ping from devices running Juniper JUNOS
description:
  - Tests reachability using ping from devices running Juniper JUNOS to a remote destination.
  - Tested against Junos (17.3R1.10)
  - For a general purpose network module, see the M(net_ping) module.
  - For Windows targets, use the M(win_ping) module instead.
  - For targets running Python, use the M(ping) module instead.
author:
  - Nilashish Chakraborty (@NilashishC)
version_added: '2.8'
options:
  dest:
    description:
      - The IP Address or hostname (resolvable by the device) of the remote node.
    required: true
  count:
    description:
      - Number of packets to send to check reachability.
    type: int
    default: 5
  source:
    description:
      - The IP Address to use while sending the ping packet(s).
  interface:
    description:
      - The source interface to use while sending the ping packet(s).
  ttl:
    description:
      - The time-to-live value for the ICMP packet(s).
    type: int
  size:
    description:
      - Determines the size (in bytes) of the ping packet(s).
    type: int
  interval:
    description:
      - Determines the interval (in seconds) between consecutive pings.
    type: int
  state:
    description:
      - Determines if the expected result is success or fail.
    choices: [ absent, present ]
    default: present
notes:
  - For a general purpose network module, see the M(net_ping) module.
  - For Windows targets, use the M(win_ping) module instead.
  - For targets running Python, use the M(ping) module instead.
  - This module works only with connection C(network_cli).
extends_documentation_fragment: junos
"""

EXAMPLES = """
- name: Test reachability to 10.10.10.10
  junos_ping:
    dest: 10.10.10.10

- name: Test reachability to 10.20.20.20 using source and size set
  junos_ping:
    dest: 10.20.20.20
    size: 1024
    ttl: 128

- name: Test unreachability to 10.30.30.30 using interval
  junos_ping:
    dest: 10.30.30.30
    interval: 3
    state: absent

- name: Test reachability to 10.40.40.40 setting count and interface
  junos_ping:
    dest: 10.40.40.40
    interface: fxp0
    count: 20
    size: 512
"""

RETURN = """
commands:
  description: List of commands sent.
  returned: always
  type: list
  sample: ["ping 10.8.38.44 count 10 source 10.8.38.38 ttl 128"]
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
  description: The round trip time (RTT) stats.
  returned: when ping succeeds
  type: dict
  sample: {"avg": 2, "max": 8, "min": 1, "stddev": 24}
"""

import re
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.junos.junos import junos_argument_spec, get_connection


def main():
    """ main entry point for module execution
    """
    argument_spec = dict(
        count=dict(type="int", default=5),
        dest=dict(type="str", required=True),
        source=dict(),
        interface=dict(),
        ttl=dict(type='int'),
        size=dict(type='int'),
        interval=dict(type='int'),
        state=dict(type="str", choices=["absent", "present"], default="present"),
    )

    argument_spec.update(junos_argument_spec)

    module = AnsibleModule(argument_spec=argument_spec)

    count = module.params["count"]
    dest = module.params["dest"]
    source = module.params["source"]
    size = module.params["size"]
    ttl = module.params["ttl"]
    interval = module.params["interval"]
    interface = module.params['interface']
    warnings = list()

    results = {'changed': False}
    if warnings:
        results["warnings"] = warnings

    results["commands"] = build_ping(dest, count, size, interval, source, ttl, interface)
    conn = get_connection(module)

    ping_results = conn.get(results["commands"])

    rtt_info, rate_info = None, None
    for line in ping_results.split("\n"):
        if line.startswith('round-trip'):
            rtt_info = line
        if line.startswith('%s packets transmitted' % count):
            rate_info = line

    if rtt_info:
        rtt = parse_rtt(rtt_info)
        for k, v in rtt.items():
            if rtt[k] is not None:
                rtt[k] = float(v)
        results["rtt"] = rtt

    pkt_loss, rx, tx = parse_rate(rate_info)
    results["packet_loss"] = str(pkt_loss) + "%"
    results["packets_rx"] = int(rx)
    results["packets_tx"] = int(tx)

    validate_results(module, pkt_loss, results)

    module.exit_json(**results)


def build_ping(dest, count, size=None, interval=None, source=None, ttl=None, interface=None):
    cmd = "ping {0} count {1}".format(dest, str(count))

    if source:
        cmd += " source {0}".format(source)

    if interface:
        cmd += " interface {0}".format(interface)

    if ttl:
        cmd += " ttl {0}".format(str(ttl))

    if size:
        cmd += " size {0}".format(str(size))

    if interval:
        cmd += " interval {0}".format(str(interval))

    return cmd


def parse_rate(rate_info):
    rate_re = re.compile(
        r"(?P<tx>\d*) packets transmitted,(?:\s*)(?P<rx>\d*) packets received,(?:\s*)(?P<pkt_loss>\d*)% packet loss")
    rate = rate_re.match(rate_info)

    return rate.group("pkt_loss"), rate.group("rx"), rate.group("tx")


def parse_rtt(rtt_info):
    rtt_re = re.compile(
        r"round-trip (?:.*)=(?:\s*)(?P<min>\d+\.\d+).(?:\d*)/(?P<avg>\d+\.\d+).(?:\d*)/(?P<max>\d*\.\d*).(?:\d*)/(?P<stddev>\d*\.\d*)")
    rtt = rtt_re.match(rtt_info)

    return rtt.groupdict()


def validate_results(module, loss, results):
    state = module.params["state"]
    if state == "present" and int(loss) == 100:
        module.fail_json(msg="Ping failed unexpectedly", **results)
    elif state == "absent" and int(loss) < 100:
        module.fail_json(msg="Ping succeeded unexpectedly", **results)


if __name__ == "__main__":
    main()
