#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2017, Ansible by Red Hat, inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = r'''
---
module: net_ping
version_added: "2.4"
author: "Jacob McGill (@jmcgill298)"
short_description: Tests reachability using ping from a network device
description:
  - Tests reachability using ping from network device to a remote destination.
  - For Windows targets, use the M(win_ping) module instead.
  - For targets running Python, use the M(ping) module instead.
options:
  count:
    description:
    - Number of packets to send.
    default: 5
  dest:
    description:
    - The IP Address or hostname (resolvable by switch) of the remote node.
    required: true
  source:
    description:
    - The source IP Address.
  state:
    description:
    - Determines if the expected result is success or fail.
    choices: [ absent, present ]
    default: present
  vrf:
    description:
    - The VRF to use for forwarding.
    default: default
notes:
  - For Windows targets, use the M(win_ping) module instead.
  - For targets running Python, use the M(ping) module instead.
'''


EXAMPLES = r'''
- name: Test reachability to 10.10.10.10 using default vrf
  net_ping:
    dest: 10.10.10.10

- name: Test reachability to 10.20.20.20 using prod vrf
  net_ping:
    dest: 10.20.20.20
    vrf: prod

- name: Test unreachability to 10.30.30.30 using default vrf
  net_ping:
    dest: 10.30.30.30
    state: absent

- name: Test reachability to 10.40.40.40 using prod vrf and setting count and source
  net_ping:
    dest: 10.40.40.40
    source: loopback0
    vrf: prod
    count: 20
'''

RETURN = r'''
commands:
  description: Show the command sent.
  returned: always
  type: list
  sample: ["ping vrf prod 10.40.40.40 count 20 source loopback0"]
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
