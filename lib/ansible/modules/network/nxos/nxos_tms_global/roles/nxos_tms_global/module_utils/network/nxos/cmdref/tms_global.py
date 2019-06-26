TMS_CMD_REF = """
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
  getval: certificate (?P<key>\S+) (?P<hostname>\S+)$
  setval: certificate {key} {hostname}
  default:
    key: ~
    hostname: ~
destination_profile_compression:
  _exclude: ['N3K', 'N5K', 'N6k', 'N7k']
  kind: str
  getval: use-compression (\S+)$
  setval: 'use-compression {0}'
  default: ~
  context: &dpcontext
    - telemetry
    - destination-profile
destination_profile_source_interface:
  _exclude: ['N3K', 'N5K', 'N6k', 'N7k']
  kind: str
  getval: source-interface (\S+)$
  setval: 'source-interface {0}'
  default: ~
  context: *dpcontext
destination_profile_vrf:
  _exclude: ['N3K', 'N5K', 'N6k', 'N7k']
  kind: str
  getval: use-vrf (\S+)$
  setval: 'use-vrf {0}'
  default: ~
  context: *dpcontext
"""
