#!/usr/bin/python
# -*- coding: utf-8 -*-
#
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

import re

from ansible.modules.network.mlnxos.mlnxos_lag import MlnxosLagApp


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'network'}


DOCUMENTATION = """
---
module: mlnxos_mlag
version_added: "2.5"
author: "Samer Deeb (@samerd)"
short_description: Manage Lags on MLNX-OS network devices
description:
  - This module provides declarative management of Lags
    on MLNX-OS network devices.
notes:
  -
options:
  lag_id:
    description:
      - port channel ID of the LAG (1-4096).
    required: true
  lag_mode:
    description:
      - LAG mode:
    choices: [on, passive, active].
  mtu:
    description:
      - Maximum size of transmit packet.
  aggregate:
    description: List of lags definitions.
  members:
    description:
      - ethernet interfaces MLAG members.
"""

EXAMPLES = """
- name: configure MLAG
  mlnxos_lag:
    lag_id: 5
    mtu: 1512
    members:
      - 1/6
      - 1/7
    lag_mode: on
"""

RETURN = """
commands:
  description: The list of configuration mode commands to send to the device.
  returned: always, except for the platforms that use Netconf transport to
  type: list
  sample:
    - interface port-channel 5
    - exit
    - interface port-channel 5 mtu 1500 force
    - interface ethernet 1/16 channel-group 5 mode on
    - interface ethernet 1/17 channel-group 5 mode on
"""


class MlnxosMLagApp(MlnxosLagApp):
    LAG_ID_REGEX = re.compile(r"^(.*)Mpo(\d+)(.*)$")
    PORT_CHANNEL = 'mlag-port-channel'
    CHANNEL_GROUP = 'mlag-channel-group'

    @classmethod
    def get_lag_members(cls, lag_item):
        lag_members = ""
        for attr, val in lag_item.iteritems():
            if attr.startswith("Local Ports"):
                lag_members = val
        lag_members = lag_members.split()
        return lag_members


if __name__ == '__main__':
    MlnxosMLagApp.main()
