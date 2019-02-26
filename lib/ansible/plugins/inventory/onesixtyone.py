# Copyright (c) 2019, Victor da Costa <vdacosta@redhat.com>
# Copyright (c) 2019 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = '''
    name: onesixtyone
    plugin_type: inventory
    version_added: "2.9"
    short_description: Uses onesityone to find hosts to target
    description:
        - Uses a YAML configuration file with a valid YAML extension.
    extends_documentation_fragment:
      - constructed
      - inventory_cache
    requirements:
      - onesixtyone CLI installed
      - python-gevent installed
    options:
        addresses:
            description: List of CIDRs and IPs to scan.
            type: list
            required: false
            default:
              - 192.168.0.0/24
        communities:
            description: List of communities to query per device.
            type: list
            required: false
            default:
              - "public"
        wait:
          description: wait n milliseconds (1/1000 of a second) between sending packets.
          type: int
          default: 10
          required: false
        platform:
          description: Dict containing additional mappings between Platform (key) and regex to match in sysDescr (value).
          type: dict
          default: {}
          required: false
    notes:
      - Only discover devices running SNMPv2.
      - TODO: Add cache support.
'''
EXAMPLES = '''
    # onesixtyone.yaml or any other YAML file-extension
    plugin: onesixtyone
    strict: False
    addresses:
      - 192.168.0.0/24
'''


import os
import re
import tempfile
import subprocess

from ansible import constants as C
from ansible.errors import AnsibleParserError
from ansible.module_utils._text import to_native
from ansible.plugins.inventory import BaseInventoryPlugin, Constructable, Cacheable

try:
  import gevent
  from gevent import socket
except:
  raise Exception('this inventory plugin requires the gevent library. Try: yum install python-gevent')


class InventoryModule(BaseInventoryPlugin, Constructable, Cacheable):

    NAME = 'onesixtyone'

    def __init__(self):

        self._onesixtyone = None
        for path in os.environ.get('PATH').split(':'):
            candidate = os.path.join(path, 'onesixtyone')
            if os.path.exists(candidate):
                self._onesixtyone = candidate
                break

        super(InventoryModule, self).__init__()

    def verify_file(self, path):

        if super(InventoryModule, self).verify_file(path):
          for fn in ('onesixtyone'):
              for suffix in ('yaml', 'yml'):
                  maybe = '{fn}.{suffix}'.format(fn=fn, suffix=suffix)
                  if path.endswith(maybe):
                      return True

        return False

    def parse(self, inventory, loader, path, cache=False):
        super(InventoryModule, self).parse(inventory, loader, path, cache=cache)
        self._read_config_data(path)

        try:
          jobs = [ gevent.spawn(self._add_device, self, device) for device in self._discovery() ]
          gevent.joinall(jobs, timeout=20)

        except Exception as e:
            raise AnsibleParserError("failed to parse %s: %s " % (to_native(path), to_native(e)))

    def _match_platform(self, text):
        ''' Matches platforms against text in sysDescr
        '''
        platforms = {
            'asa': re.compile(r'^Cisco\sAdaptive\sSecurity\sAppliance'),
            'ios': re.compile(r'^Cisco\sIOS\sSoftware'),
            'iosxr': re.compile(r'^Cisco\sIOS\sXR\sSoftware'),
            'nxos': re.compile(r'^Cisco\sNexus\sOperating\sSystem'),
            'dellos': re.compile(r'^Dell\sApplication\sSoftware'),
            'junos': re.compile(r'^JUNOS'),
            'aruba': re.compile(r'^Aruba\sOperating\sSystem\sSoftware'),
            'eos': re.compile(r'^Arista')
        }

        platforms.update(self.get_option('platform'))

        for platform, rule in platforms.items():
            if rule.match(text):
              return platform
        
        return 'unknown'

    def _discovery(self):
        if self._onesixtyone is None:
            raise AnsibleParserError('onesixtyone inventory plugin requires the onesixtyone cli tool to work')

        # setup command
        cmd = [self._onesixtyone]

        #                                ip.ip.ip                       [community] <text>
        find_entry = re.compile(r'^(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\s\[(\w+)\]\s(.*)')

        # Create communities temporary file
        with tempfile.NamedTemporaryFile() as communities_tempfile:
          communities = self._options.get("communities")
          communities_tempfile.write("\n".join(communities) + "\n")
          communities_tempfile.flush()
          cmd.append('-c')
          cmd.append(communities_tempfile.name)

          # Create hosts temporary file
          with tempfile.NamedTemporaryFile() as addresses_tempfile:
            addresses = self.get_option("addresses")
            addresses_tempfile.write("\n".join(addresses) + "\n")
            addresses_tempfile.flush()
            cmd.append('-i')
            cmd.append(addresses_tempfile.name)

            cmd.append('-w')
            cmd.append("%s" % self.get_option("wait"))

            self.display.vvv("command: {cmd})".format(cmd=cmd))

            # execute
            try:
              cmd_output = subprocess.check_output(" ".join(cmd), stderr=subprocess.STDOUT, shell=True)

            except subprocess.CalledProcessError as p:
                raise AnsibleParserError('Failed to run onesixtyone, rc=%s: %s' % (p.returncode, to_native(p.output)))

            # parse command output
            entries = []
            matches = None
            for line in cmd_output.splitlines():
              self.display.vvv("output (line): {output}".format(output=line))
              matches = find_entry.match(line)
              if matches is not None:
                entries.append({
                  'host': matches.group(1),
                  'community': matches.group(2),
                  'sysdescr': matches.group(3),
                })

        return entries

    @staticmethod
    def _add_device(obj, device):

      # Inventory Group
      platform = obj._match_platform(device.get('sysdescr'))
      obj.display.vvv("platform: {platform}".format(platform=platform))

      obj.inventory.add_group(platform)
      obj.inventory.set_variable(platform, 'ansible_network_os', platform)

      # Inventory Host
      ansible_host = device.get('host')
      host = socket.gethostbyaddr(ansible_host)[0] or ansible_host
      obj.display.vvv("host: {host}".format(host=host))
      obj.inventory.add_host(host, group=platform)
      obj.inventory.set_variable(host, 'ansible_host', ansible_host)
      obj.inventory.set_variable(host, 'snmp_community', device.get('community'))
      obj.inventory.set_variable(host, 'snmp_sysdescr', device.get('sysdescr'))