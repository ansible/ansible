#
# -*- coding: utf-8 -*-
# Copyright 2019 Cisco and/or its affiliates.
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
#
# Telemetry Command Reference File

from __future__ import absolute_import, division, print_function
__metaclass__ = type

TMS_GLOBAL = '''
# The cmd_ref is a yaml formatted list of module commands.
# A leading underscore denotes a non-command variable; e.g. _template.
# TMS does not have convenient global json data so this cmd_ref uses raw cli configs.
---
_template: # _template holds common settings for all commands
  # Enable feature telemetry if disabled
  feature: telemetry
  # Common get syntax for TMS commands
  get_command: show run telemetry all
  # Parent configuration for TMS commands
  context:
    - telemetry
certificate:
  _exclude: ['N3K', 'N5K', 'N6k', 'N7k']
  kind: dict
  getval: certificate (?P<key>\\S+) (?P<hostname>\\S+)$
  setval: certificate {key} {hostname}
  default:
    key: ~
    hostname: ~
compression:
  _exclude: ['N3K', 'N5K', 'N6k', 'N7k']
  kind: str
  getval: use-compression (\\S+)$
  setval: 'use-compression {0}'
  default: ~
  context: &dpcontext
    - telemetry
    - destination-profile
source_interface:
  _exclude: ['N3K', 'N5K', 'N6k', 'N7k']
  kind: str
  getval: source-interface (\\S+)$
  setval: 'source-interface {0}'
  default: ~
  context: *dpcontext
vrf:
  _exclude: ['N3K', 'N5K', 'N6k', 'N7k']
  kind: str
  getval: use-vrf (\\S+)$
  setval: 'use-vrf {0}'
  default: ~
  context: *dpcontext
'''

TMS_DESTGROUP = '''
# The cmd_ref is a yaml formatted list of module commands.
# A leading underscore denotes a non-command variable; e.g. _template.
# TBD: Use Structured Where Possible
---
_template: # _template holds common settings for all commands
  # Enable feature telemetry if disabled
  feature: telemetry
  # Common get syntax for TMS commands
  get_command: show run telemetry all
  # Parent configuration for TMS commands
  context:
    - telemetry
destination:
  _exclude: ['N3K', 'N5K', 'N6k', 'N7k']
  multiple: true
  kind: dict
  getval: ip address (?P<ip>\\S+) port (?P<port>\\S+) protocol (?P<protocol>\\S+) encoding (?P<encoding>\\S+)
  setval: ip address {ip} port {port} protocol {protocol} encoding {encoding}
  default:
    ip: ~
    port: ~
    protocol: ~
    encoding: ~
'''

TMS_SENSORGROUP = '''
# The cmd_ref is a yaml formatted list of module commands.
# A leading underscore denotes a non-command variable; e.g. _template.
# TBD: Use Structured Where Possible
---
_template: # _template holds common settings for all commands
  # Enable feature telemetry if disabled
  feature: telemetry
  # Common get syntax for TMS commands
  get_command: show run telemetry all
  # Parent configuration for TMS commands
  context:
    - telemetry
data_source:
  _exclude: ['N3K', 'N5K', 'N6k', 'N7k']
  kind: str
  getval: data-source (\\S+)$
  setval: 'data-source {0}'
  default: ~
path:
  _exclude: ['N3K', 'N5K', 'N6k', 'N7k']
  multiple: true
  kind: dict
  getval: path (?P<name>(\\S+|".*"))( depth (?P<depth>\\S+))?( query-condition (?P<query_condition>\\S+))?( filter-condition (?P<filter_condition>\\S+))?$
  setval: path {name} depth {depth} query-condition {query_condition} filter-condition {filter_condition}
  default:
    name: ~
    depth: ~
    query_condition: ~
    filter_condition: ~
'''

TMS_SUBSCRIPTION = '''
# The cmd_ref is a yaml formatted list of module commands.
# A leading underscore denotes a non-command variable; e.g. _template.
# TBD: Use Structured Where Possible
---
_template: # _template holds common settings for all commands
  # Enable feature telemetry if disabled
  feature: telemetry
  # Common get syntax for TMS commands
  get_command: show run telemetry all
  # Parent configuration for TMS commands
  context:
    - telemetry
destination_group:
  _exclude: ['N3K', 'N5K', 'N6k', 'N7k']
  multiple: true
  kind: int
  getval: dst-grp (\\S+)$
  setval: 'dst-grp {0}'
  default: ~
sensor_group:
  _exclude: ['N3K', 'N5K', 'N6k', 'N7k']
  multiple: true
  kind: dict
  getval: snsr-grp (?P<id>\\S+) sample-interval (?P<sample_interval>\\S+)$
  setval: snsr-grp {id} sample-interval {sample_interval}
  default:
    id: ~
    sample_interval: ~
'''
