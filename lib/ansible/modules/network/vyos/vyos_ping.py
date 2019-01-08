#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2017, Ansible by Red Hat, inc
#
# This file is part of Ansible by Red Hat
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

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = """
---
module: vyos_ping
short_description: Tests reachability using ping from VyOS network devices
description:
  - Tests reachability using ping from a VyOS device to a remote destination.
  - Tested against VyOS 1.1.8 (helium)
  - For a general purpose network module, see the M(net_ping) module.
  - For Windows targets, use the M(win_ping) module instead.
  - For targets running Python, use the M(ping) module instead.
author:
  - Nilashish Chakraborty (@nilashishc)
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
      - The source interface or IP Address to use while sending the ping packet(s).
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
extends_documentation_fragment: vyos
"""

EXAMPLES = """
- name: Test reachability to 10.10.10.10
  vyos_ping:
    dest: 10.10.10.10

- name: Test reachability to 10.20.20.20 using source and ttl set
  vyos_ping:
    dest: 10.20.20.20
    source: eth0
    ttl: 128

- name: Test unreachability to 10.30.30.30 using interval
  vyos_ping:
    dest: 10.30.30.30
    interval: 3
    state: absent

- name: Test reachability to 10.40.40.40 setting count and source
  vyos_ping:
    dest: 10.40.40.40
    source: eth1
    count: 20
    size: 512
"""

RETURN = """
commands:
  description: List of commands sent.
  returned: always
  type: list
  sample: ["ping 10.8.38.44 count 10 interface eth0 ttl 128"]
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
  sample: {"avg": 2, "max": 8, "min": 1, "mdev": 24}
"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.vyos.vyos import run_commands
from ansible.module_utils.network.vyos.vyos import vyos_argument_spec
import re


def main():
    """ main entry point for module execution
    """
    argument_spec = dict(
        count=dict(type="int", default=5),
        dest=dict(type="str", required=True),
        source=dict(type="str"),
        ttl=dict(type='int'),
        size=dict(type='int'),
        interval=dict(type='int'),
        state=dict(type="str", choices=["absent", "present"], default="present"),
    )

    argument_spec.update(vyos_argument_spec)

    module = AnsibleModule(argument_spec=argument_spec)

    count = module.params["count"]
    dest = module.params["dest"]
    source = module.params["source"]
    size = module.params["size"]
    ttl = module.params["ttl"]
    interval = module.params["interval"]

    warnings = list()

    results = {}
    if warnings:
        results["warnings"] = warnings

    results["commands"] = [build_ping(dest, count, size, interval, source, ttl)]

    ping_results = run_commands(module, commands=results["commands"])
    ping_results_list = ping_results[0].split("\n")

    rtt_info, rate_info = None, None
    for line in ping_results_list:
        if line.startswith('rtt'):
            rtt_info = line
        if line.startswith('%s packets transmitted' % count):
            rate_info = line

    if rtt_info:
        rtt = parse_rtt(rtt_info)
        for k, v in rtt.items():
            if rtt[k] is not None:
                rtt[k] = int(v)
        results["rtt"] = rtt

    pkt_loss, rx, tx = parse_rate(rate_info)
    results["packet_loss"] = str(pkt_loss) + "%"
    results["packets_rx"] = int(rx)
    results["packets_tx"] = int(tx)

    validate_results(module, pkt_loss, results)

    module.exit_json(**results)


def build_ping(dest, count, size=None, interval=None, source=None, ttl=None):
    cmd = "ping {0} count {1}".format(dest, str(count))

    if source:
        cmd += " interface {0}".format(source)

    if ttl:
        cmd += " ttl {0}".format(str(ttl))

    if size:
        cmd += " size {0}".format(str(size))

    if interval:
        cmd += " interval {0}".format(str(interval))

    return cmd


def parse_rate(rate_info):
    rate_re = re.compile(
        r"(?P<tx>\d+) (?:\w+) (?:\w+), (?P<rx>\d+) (?:\w+), (?P<pkt_loss>\d+)% (?:\w+) (?:\w+), (?:\w+) (?P<time>\d+)")
    rate_err_re = re.compile(
        r"(?P<tx>\d+) (?:\w+) (?:\w+), (?P<rx>\d+) (?:\w+), (?:[+-])(?P<err>\d+) (?:\w+), (?P<pkt_loss>\d+)% (?:\w+) (?:\w+), (?:\w+) (?P<time>\d+)")

    if rate_re.match(rate_info):
        rate = rate_re.match(rate_info)
    elif rate_err_re.match(rate_info):
        rate = rate_err_re.match(rate_info)

    return rate.group("pkt_loss"), rate.group("rx"), rate.group("tx")


def parse_rtt(rtt_info):
    rtt_re = re.compile(
        r"rtt (?:.*)=(?:\s*)(?P<min>\d*).(?:\d*)/(?P<avg>\d*).(?:\d*)/(?P<max>\d+).(?:\d*)/(?P<mdev>\d*)")
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
