# unit tests for ansible other facter fact collector
# -*- coding: utf-8 -*-
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

from __future__ import annotations

from unittest.mock import Mock, patch

from .. base import BaseFactsTest

from ansible.module_utils.facts.other.facter import FacterFactCollector

facter_json_output = '''
{
  "operatingsystemmajrelease": "25",
  "hardwareisa": "x86_64",
  "kernel": "Linux",
  "path": "/home/testuser/src/ansible/bin:/home/testuser/perl5/bin:/home/testuser/perl5/bin:/home/testuser/bin:/home/testuser/.local/bin:/home/testuser/pythons/bin:/usr/lib64/qt-3.3/bin:/usr/local/bin:/usr/bin:/usr/local/sbin:/usr/sbin:/home/testuser/.cabal/bin:/home/testuser/gopath/bin:/home/testuser/.rvm/bin",
  "memorysize": "15.36 GB",
  "memoryfree": "4.88 GB",
  "swapsize": "7.70 GB",
  "swapfree": "6.75 GB",
  "swapsize_mb": "7880.00",
  "swapfree_mb": "6911.41",
  "memorysize_mb": "15732.95",
  "memoryfree_mb": "4997.68",
  "lsbmajdistrelease": "25",
  "macaddress": "02:42:ea:15:d8:84",
  "id": "testuser",
  "domain": "example.com",
  "augeasversion": "1.7.0",
  "os": {
    "name": "Fedora",
    "family": "RedHat",
    "release": {
      "major": "25",
      "full": "25"
    },
    "lsb": {
      "distcodename": "TwentyFive",
      "distid": "Fedora",
      "distdescription": "Fedora release 25 (Twenty Five)",
      "release": ":core-4.1-amd64:core-4.1-noarch:cxx-4.1-amd64:cxx-4.1-noarch:desktop-4.1-amd64:desktop-4.1-noarch:languages-4.1-amd64:languages-4.1-noarch:printing-4.1-amd64:printing-4.1-noarch",
      "distrelease": "25",
      "majdistrelease": "25"
    }
  },
  "processors": {
    "models": [
      "Intel(R) Core(TM) i7-4800MQ CPU @ 2.70GHz",
      "Intel(R) Core(TM) i7-4800MQ CPU @ 2.70GHz",
      "Intel(R) Core(TM) i7-4800MQ CPU @ 2.70GHz",
      "Intel(R) Core(TM) i7-4800MQ CPU @ 2.70GHz",
      "Intel(R) Core(TM) i7-4800MQ CPU @ 2.70GHz",
      "Intel(R) Core(TM) i7-4800MQ CPU @ 2.70GHz",
      "Intel(R) Core(TM) i7-4800MQ CPU @ 2.70GHz",
      "Intel(R) Core(TM) i7-4800MQ CPU @ 2.70GHz"
    ],
    "count": 8,
    "physicalcount": 1
  },
  "architecture": "x86_64",
  "hardwaremodel": "x86_64",
  "operatingsystem": "Fedora",
  "processor0": "Intel(R) Core(TM) i7-4800MQ CPU @ 2.70GHz",
  "processor1": "Intel(R) Core(TM) i7-4800MQ CPU @ 2.70GHz",
  "processor2": "Intel(R) Core(TM) i7-4800MQ CPU @ 2.70GHz",
  "processor3": "Intel(R) Core(TM) i7-4800MQ CPU @ 2.70GHz",
  "processor4": "Intel(R) Core(TM) i7-4800MQ CPU @ 2.70GHz",
  "processor5": "Intel(R) Core(TM) i7-4800MQ CPU @ 2.70GHz",
  "processor6": "Intel(R) Core(TM) i7-4800MQ CPU @ 2.70GHz",
  "processor7": "Intel(R) Core(TM) i7-4800MQ CPU @ 2.70GHz",
  "processorcount": 8,
  "uptime_seconds": 1558090,
  "fqdn": "myhostname.example.com",
  "rubyversion": "2.3.3",
  "gid": "testuser",
  "physicalprocessorcount": 1,
  "netmask": "255.255.0.0",
  "uniqueid": "a8c01301",
  "uptime_days": 18,
  "interfaces": "docker0,em1,lo,vethf20ff12,virbr0,virbr1,virbr0_nic,virbr1_nic,wlp4s0",
  "ipaddress_docker0": "172.17.0.1",
  "macaddress_docker0": "02:42:ea:15:d8:84",
  "netmask_docker0": "255.255.0.0",
  "mtu_docker0": 1500,
  "macaddress_em1": "3c:97:0e:e9:28:8e",
  "mtu_em1": 1500,
  "ipaddress_lo": "127.0.0.1",
  "netmask_lo": "255.0.0.0",
  "mtu_lo": 65536,
  "macaddress_vethf20ff12": "ae:6e:2b:1e:a1:31",
  "mtu_vethf20ff12": 1500,
  "ipaddress_virbr0": "192.168.137.1",
  "macaddress_virbr0": "52:54:00:ce:82:5e",
  "netmask_virbr0": "255.255.255.0",
  "mtu_virbr0": 1500,
  "ipaddress_virbr1": "192.168.121.1",
  "macaddress_virbr1": "52:54:00:b4:68:a9",
  "netmask_virbr1": "255.255.255.0",
  "mtu_virbr1": 1500,
  "macaddress_virbr0_nic": "52:54:00:ce:82:5e",
  "mtu_virbr0_nic": 1500,
  "macaddress_virbr1_nic": "52:54:00:b4:68:a9",
  "mtu_virbr1_nic": 1500,
  "ipaddress_wlp4s0": "192.168.1.19",
  "macaddress_wlp4s0": "5c:51:4f:e6:a8:e3",
  "netmask_wlp4s0": "255.255.255.0",
  "mtu_wlp4s0": 1500,
  "virtual": "physical",
  "is_virtual": false,
  "partitions": {
    "sda2": {
      "size": "499091456"
    },
    "sda1": {
      "uuid": "32caaec3-ef40-4691-a3b6-438c3f9bc1c0",
      "size": "1024000",
      "mount": "/boot"
    }
  },
  "lsbdistcodename": "TwentyFive",
  "lsbrelease": ":core-4.1-amd64:core-4.1-noarch:cxx-4.1-amd64:cxx-4.1-noarch:desktop-4.1-amd64:desktop-4.1-noarch:languages-4.1-amd64:languages-4.1-noarch:printing-4.1-amd64:printing-4.1-noarch",  # noqa
  "filesystems": "btrfs,ext2,ext3,ext4,xfs",
  "system_uptime": {
    "seconds": 1558090,
    "hours": 432,
    "days": 18,
    "uptime": "18 days"
  },
  "ipaddress": "172.17.0.1",
  "timezone": "EDT",
  "ps": "ps -ef",
  "rubyplatform": "x86_64-linux",
  "rubysitedir": "/usr/local/share/ruby/site_ruby",
  "uptime": "18 days",
  "lsbdistrelease": "25",
  "operatingsystemrelease": "25",
  "facterversion": "2.4.3",
  "kernelrelease": "4.9.14-200.fc25.x86_64",
  "lsbdistdescription": "Fedora release 25 (Twenty Five)",
  "network_docker0": "172.17.0.0",
  "network_lo": "127.0.0.0",
  "network_virbr0": "192.168.137.0",
  "network_virbr1": "192.168.121.0",
  "network_wlp4s0": "192.168.1.0",
  "lsbdistid": "Fedora",
  "selinux": true,
  "selinux_enforced": false,
  "selinux_policyversion": "30",
  "selinux_current_mode": "permissive",
  "selinux_config_mode": "permissive",
  "selinux_config_policy": "targeted",
  "hostname": "myhostname",
  "osfamily": "RedHat",
  "kernelmajversion": "4.9",
  "blockdevice_sr0_size": 1073741312,
  "blockdevice_sr0_vendor": "MATSHITA",
  "blockdevice_sr0_model": "DVD-RAM UJ8E2",
  "blockdevice_sda_size": 256060514304,
  "blockdevice_sda_vendor": "ATA",
  "blockdevice_sda_model": "SAMSUNG MZ7TD256",
  "blockdevices": "sda,sr0",
  "uptime_hours": 432,
  "kernelversion": "4.9.14"
}
'''


class TestFacterCollector(BaseFactsTest):
    __test__ = True
    gather_subset = ['!all', 'facter']
    valid_subsets = ['facter']
    fact_namespace = 'ansible_facter'
    collector_class = FacterFactCollector

    def _mock_module(self):
        mock_module = Mock()
        mock_module.params = {'gather_subset': self.gather_subset,
                              'gather_timeout': 10,
                              'filter': '*'}
        mock_module.get_bin_path = Mock(return_value='/not/actually/facter')
        mock_module.run_command = Mock(return_value=(0, facter_json_output, ''))
        return mock_module

    @patch('ansible.module_utils.facts.other.facter.FacterFactCollector.get_facter_output')
    def test_bogus_json(self, mock_get_facter_output):
        module = self._mock_module()

        # bogus json
        mock_get_facter_output.return_value = '{'

        fact_collector = self.collector_class()
        facts_dict = fact_collector.collect(module=module)

        self.assertIsInstance(facts_dict, dict)
        self.assertEqual(facts_dict, {})

    @patch('ansible.module_utils.facts.other.facter.FacterFactCollector.run_facter')
    def test_facter_non_zero_return_code(self, mock_run_facter):
        module = self._mock_module()

        # bogus json
        mock_run_facter.return_value = (1, '{}', '')

        fact_collector = self.collector_class()
        facts_dict = fact_collector.collect(module=module)

        self.assertIsInstance(facts_dict, dict)

        # This assumes no 'facter' entry at all is correct
        self.assertNotIn('facter', facts_dict)
        self.assertEqual(facts_dict, {})
