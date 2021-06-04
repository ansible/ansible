# unit tests for ansible fact collectors
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

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from units.compat.mock import Mock, patch

from . base import BaseFactsTest

from ansible.module_utils.facts import collector

from ansible.module_utils.facts.system.apparmor import ApparmorFactCollector
from ansible.module_utils.facts.system.caps import SystemCapabilitiesFactCollector
from ansible.module_utils.facts.system.cmdline import CmdLineFactCollector
from ansible.module_utils.facts.system.distribution import DistributionFactCollector
from ansible.module_utils.facts.system.dns import DnsFactCollector
from ansible.module_utils.facts.system.env import EnvFactCollector
from ansible.module_utils.facts.system.fips import FipsFactCollector
from ansible.module_utils.facts.system.pkg_mgr import PkgMgrFactCollector, OpenBSDPkgMgrFactCollector
from ansible.module_utils.facts.system.platform import PlatformFactCollector
from ansible.module_utils.facts.system.python import PythonFactCollector
from ansible.module_utils.facts.system.selinux import SelinuxFactCollector
from ansible.module_utils.facts.system.service_mgr import ServiceMgrFactCollector
from ansible.module_utils.facts.system.ssh_pub_keys import SshPubKeyFactCollector
from ansible.module_utils.facts.system.user import UserFactCollector

from ansible.module_utils.facts.virtual.base import VirtualCollector
from ansible.module_utils.facts.network.base import NetworkCollector
from ansible.module_utils.facts.hardware.base import HardwareCollector


class CollectorException(Exception):
    pass


class ExceptionThrowingCollector(collector.BaseFactCollector):
    name = 'exc_throwing'

    def __init__(self, collectors=None, namespace=None, exception=None):
        super(ExceptionThrowingCollector, self).__init__(collectors, namespace)
        self._exception = exception or CollectorException('collection failed')

    def collect(self, module=None, collected_facts=None):
        raise self._exception


class TestExceptionThrowingCollector(BaseFactsTest):
    __test__ = True
    gather_subset = ['exc_throwing']
    valid_subsets = ['exc_throwing']
    collector_class = ExceptionThrowingCollector

    def test_collect(self):
        module = self._mock_module()
        fact_collector = self.collector_class()
        self.assertRaises(CollectorException,
                          fact_collector.collect,
                          module=module,
                          collected_facts=self.collected_facts)

    def test_collect_with_namespace(self):
        module = self._mock_module()
        fact_collector = self.collector_class()
        self.assertRaises(CollectorException,
                          fact_collector.collect_with_namespace,
                          module=module,
                          collected_facts=self.collected_facts)


class TestApparmorFacts(BaseFactsTest):
    __test__ = True
    gather_subset = ['!all', 'apparmor']
    valid_subsets = ['apparmor']
    fact_namespace = 'ansible_apparmor'
    collector_class = ApparmorFactCollector

    def test_collect(self):
        facts_dict = super(TestApparmorFacts, self).test_collect()
        self.assertIn('status', facts_dict['apparmor'])


class TestCapsFacts(BaseFactsTest):
    __test__ = True
    gather_subset = ['!all', 'caps']
    valid_subsets = ['caps']
    fact_namespace = 'ansible_system_capabilities'
    collector_class = SystemCapabilitiesFactCollector

    def _mock_module(self):
        mock_module = Mock()
        mock_module.params = {'gather_subset': self.gather_subset,
                              'gather_timeout': 10,
                              'filter': '*'}
        mock_module.get_bin_path = Mock(return_value='/usr/sbin/capsh')
        mock_module.run_command = Mock(return_value=(0, 'Current: =ep', ''))
        return mock_module


class TestCmdLineFacts(BaseFactsTest):
    __test__ = True
    gather_subset = ['!all', 'cmdline']
    valid_subsets = ['cmdline']
    fact_namespace = 'ansible_cmdline'
    collector_class = CmdLineFactCollector

    def test_parse_proc_cmdline_uefi(self):
        uefi_cmdline = r'initrd=\70ef65e1a04a47aea04f7b5145ea3537\4.10.0-19-generic\initrd root=UUID=50973b75-4a66-4bf0-9764-2b7614489e64 ro quiet'
        expected = {'initrd': r'\70ef65e1a04a47aea04f7b5145ea3537\4.10.0-19-generic\initrd',
                    'root': 'UUID=50973b75-4a66-4bf0-9764-2b7614489e64',
                    'quiet': True,
                    'ro': True}
        fact_collector = self.collector_class()
        facts_dict = fact_collector._parse_proc_cmdline(uefi_cmdline)

        self.assertDictEqual(facts_dict, expected)

    def test_parse_proc_cmdline_fedora(self):
        cmdline_fedora = r'BOOT_IMAGE=/vmlinuz-4.10.16-200.fc25.x86_64 root=/dev/mapper/fedora-root ro rd.lvm.lv=fedora/root rd.luks.uuid=luks-c80b7537-358b-4a07-b88c-c59ef187479b rd.lvm.lv=fedora/swap rhgb quiet LANG=en_US.UTF-8'   # noqa

        expected = {'BOOT_IMAGE': '/vmlinuz-4.10.16-200.fc25.x86_64',
                    'LANG': 'en_US.UTF-8',
                    'quiet': True,
                    'rd.luks.uuid': 'luks-c80b7537-358b-4a07-b88c-c59ef187479b',
                    'rd.lvm.lv': 'fedora/swap',
                    'rhgb': True,
                    'ro': True,
                    'root': '/dev/mapper/fedora-root'}

        fact_collector = self.collector_class()
        facts_dict = fact_collector._parse_proc_cmdline(cmdline_fedora)

        self.assertDictEqual(facts_dict, expected)

    def test_parse_proc_cmdline_dup_console(self):
        example = r'BOOT_IMAGE=/boot/vmlinuz-4.4.0-72-generic root=UUID=e12e46d9-06c9-4a64-a7b3-60e24b062d90 ro console=tty1 console=ttyS0'

        # FIXME: Two 'console' keywords? Using a dict for the fact value here loses info. Currently the 'last' one wins
        expected = {'BOOT_IMAGE': '/boot/vmlinuz-4.4.0-72-generic',
                    'root': 'UUID=e12e46d9-06c9-4a64-a7b3-60e24b062d90',
                    'ro': True,
                    'console': 'ttyS0'}

        fact_collector = self.collector_class()
        facts_dict = fact_collector._parse_proc_cmdline(example)

        # TODO: fails because we lose a 'console'
        self.assertDictEqual(facts_dict, expected)


class TestDistributionFacts(BaseFactsTest):
    __test__ = True
    gather_subset = ['!all', 'distribution']
    valid_subsets = ['distribution']
    fact_namespace = 'ansible_distribution'
    collector_class = DistributionFactCollector


class TestDnsFacts(BaseFactsTest):

    __test__ = True
    gather_subset = ['!all', 'dns']
    valid_subsets = ['dns']
    fact_namespace = 'ansible_dns'
    collector_class = DnsFactCollector


class TestEnvFacts(BaseFactsTest):

    __test__ = True
    gather_subset = ['!all', 'env']
    valid_subsets = ['env']
    fact_namespace = 'ansible_env'
    collector_class = EnvFactCollector

    def test_collect(self):
        facts_dict = super(TestEnvFacts, self).test_collect()
        self.assertIn('HOME', facts_dict['env'])


class TestFipsFacts(BaseFactsTest):
    __test__ = True
    gather_subset = ['!all', 'fips']
    valid_subsets = ['fips']
    fact_namespace = 'ansible_fips'
    collector_class = FipsFactCollector


class TestHardwareCollector(BaseFactsTest):
    __test__ = True
    gather_subset = ['!all', 'hardware']
    valid_subsets = ['hardware']
    fact_namespace = 'ansible_hardware'
    collector_class = HardwareCollector
    collected_facts = {'ansible_architecture': 'x86_64'}


class TestNetworkCollector(BaseFactsTest):
    __test__ = True
    gather_subset = ['!all', 'network']
    valid_subsets = ['network']
    fact_namespace = 'ansible_network'
    collector_class = NetworkCollector


class TestPkgMgrFacts(BaseFactsTest):
    __test__ = True
    gather_subset = ['!all', 'pkg_mgr']
    valid_subsets = ['pkg_mgr']
    fact_namespace = 'ansible_pkgmgr'
    collector_class = PkgMgrFactCollector
    collected_facts = {
        "ansible_distribution": "Fedora",
        "ansible_distribution_major_version": "28",
        "ansible_os_family": "RedHat"
    }

    def test_collect(self):
        module = self._mock_module()
        fact_collector = self.collector_class()
        facts_dict = fact_collector.collect(module=module, collected_facts=self.collected_facts)
        self.assertIsInstance(facts_dict, dict)
        self.assertIn('pkg_mgr', facts_dict)


class TestMacOSXPkgMgrFacts(BaseFactsTest):
    __test__ = True
    gather_subset = ['!all', 'pkg_mgr']
    valid_subsets = ['pkg_mgr']
    fact_namespace = 'ansible_pkgmgr'
    collector_class = PkgMgrFactCollector
    collected_facts = {
        "ansible_distribution": "MacOSX",
        "ansible_distribution_major_version": "11",
        "ansible_os_family": "Darwin"
    }

    @patch('ansible.module_utils.facts.system.pkg_mgr.os.path.exists', side_effect=lambda x: x == '/opt/homebrew/bin/brew')
    def test_collect_opt_homebrew(self, p_exists):
        module = self._mock_module()
        fact_collector = self.collector_class()
        facts_dict = fact_collector.collect(module=module, collected_facts=self.collected_facts)
        self.assertIsInstance(facts_dict, dict)
        self.assertIn('pkg_mgr', facts_dict)
        self.assertEqual(facts_dict['pkg_mgr'], 'homebrew')

    @patch('ansible.module_utils.facts.system.pkg_mgr.os.path.exists', side_effect=lambda x: x == '/usr/local/bin/brew')
    def test_collect_usr_homebrew(self, p_exists):
        module = self._mock_module()
        fact_collector = self.collector_class()
        facts_dict = fact_collector.collect(module=module, collected_facts=self.collected_facts)
        self.assertIsInstance(facts_dict, dict)
        self.assertIn('pkg_mgr', facts_dict)
        self.assertEqual(facts_dict['pkg_mgr'], 'homebrew')

    @patch('ansible.module_utils.facts.system.pkg_mgr.os.path.exists', side_effect=lambda x: x == '/opt/local/bin/port')
    def test_collect_macports(self, p_exists):
        module = self._mock_module()
        fact_collector = self.collector_class()
        facts_dict = fact_collector.collect(module=module, collected_facts=self.collected_facts)
        self.assertIsInstance(facts_dict, dict)
        self.assertIn('pkg_mgr', facts_dict)
        self.assertEqual(facts_dict['pkg_mgr'], 'macports')


def _sanitize_os_path_apt_get(path):
    if path == '/usr/bin/apt-get':
        return True
    else:
        return False


class TestPkgMgrFactsAptFedora(BaseFactsTest):
    __test__ = True
    gather_subset = ['!all', 'pkg_mgr']
    valid_subsets = ['pkg_mgr']
    fact_namespace = 'ansible_pkgmgr'
    collector_class = PkgMgrFactCollector
    collected_facts = {
        "ansible_distribution": "Fedora",
        "ansible_distribution_major_version": "28",
        "ansible_os_family": "RedHat",
        "ansible_pkg_mgr": "apt"
    }

    @patch('ansible.module_utils.facts.system.pkg_mgr.os.path.exists', side_effect=_sanitize_os_path_apt_get)
    def test_collect(self, mock_os_path_exists):
        module = self._mock_module()
        fact_collector = self.collector_class()
        facts_dict = fact_collector.collect(module=module, collected_facts=self.collected_facts)
        self.assertIsInstance(facts_dict, dict)
        self.assertIn('pkg_mgr', facts_dict)


class TestOpenBSDPkgMgrFacts(BaseFactsTest):
    __test__ = True
    gather_subset = ['!all', 'pkg_mgr']
    valid_subsets = ['pkg_mgr']
    fact_namespace = 'ansible_pkgmgr'
    collector_class = OpenBSDPkgMgrFactCollector

    def test_collect(self):
        module = self._mock_module()
        fact_collector = self.collector_class()
        facts_dict = fact_collector.collect(module=module, collected_facts=self.collected_facts)
        self.assertIsInstance(facts_dict, dict)
        self.assertIn('pkg_mgr', facts_dict)
        self.assertEqual(facts_dict['pkg_mgr'], 'openbsd_pkg')


class TestPlatformFactCollector(BaseFactsTest):
    __test__ = True
    gather_subset = ['!all', 'platform']
    valid_subsets = ['platform']
    fact_namespace = 'ansible_platform'
    collector_class = PlatformFactCollector


class TestPythonFactCollector(BaseFactsTest):
    __test__ = True
    gather_subset = ['!all', 'python']
    valid_subsets = ['python']
    fact_namespace = 'ansible_python'
    collector_class = PythonFactCollector


class TestSelinuxFacts(BaseFactsTest):
    __test__ = True
    gather_subset = ['!all', 'selinux']
    valid_subsets = ['selinux']
    fact_namespace = 'ansible_selinux'
    collector_class = SelinuxFactCollector

    def test_no_selinux(self):
        with patch('ansible.module_utils.facts.system.selinux.HAVE_SELINUX', False):
            module = self._mock_module()
            fact_collector = self.collector_class()
            facts_dict = fact_collector.collect(module=module)
            self.assertIsInstance(facts_dict, dict)
            self.assertEqual(facts_dict['selinux']['status'], 'Missing selinux Python library')
            return facts_dict


class TestServiceMgrFacts(BaseFactsTest):
    __test__ = True
    gather_subset = ['!all', 'service_mgr']
    valid_subsets = ['service_mgr']
    fact_namespace = 'ansible_service_mgr'
    collector_class = ServiceMgrFactCollector

    # TODO: dedupe some of this test code

    @patch('ansible.module_utils.facts.system.service_mgr.get_file_content', return_value=None)
    @patch('ansible.module_utils.facts.system.service_mgr.ServiceMgrFactCollector.is_systemd_managed', return_value=False)
    @patch('ansible.module_utils.facts.system.service_mgr.ServiceMgrFactCollector.is_systemd_managed_offline', return_value=False)
    @patch('ansible.module_utils.facts.system.service_mgr.os.path.exists', return_value=False)
    def test_service_mgr_runit(self, mock_gfc, mock_ism, mock_ismo, mock_ope):
        # no /proc/1/comm, ps returns non-0
        # should fallback to 'service'
        module = self._mock_module()
        module.run_command = Mock(return_value=(1, '', 'wat'))
        fact_collector = self.collector_class()
        facts_dict = fact_collector.collect(module=module)
        self.assertIsInstance(facts_dict, dict)
        self.assertEqual(facts_dict['service_mgr'], 'service')

    @patch('ansible.module_utils.facts.system.service_mgr.get_file_content', return_value=None)
    def test_no_proc1_ps_random_init(self, mock_gfc):
        # no /proc/1/comm, ps returns '/sbin/sys11' which we dont know
        # should end up return 'sys11'
        module = self._mock_module()
        module.run_command = Mock(return_value=(0, '/sbin/sys11', ''))
        fact_collector = self.collector_class()
        facts_dict = fact_collector.collect(module=module)
        self.assertIsInstance(facts_dict, dict)
        self.assertEqual(facts_dict['service_mgr'], 'sys11')

    @patch('ansible.module_utils.facts.system.service_mgr.get_file_content', return_value=None)
    @patch('ansible.module_utils.facts.system.service_mgr.ServiceMgrFactCollector.is_systemd_managed', return_value=False)
    @patch('ansible.module_utils.facts.system.service_mgr.ServiceMgrFactCollector.is_systemd_managed_offline', return_value=False)
    @patch('ansible.module_utils.facts.system.service_mgr.os.path.exists', return_value=False)
    def test_service_mgr_runit(self, mock_gfc, mock_ism, mock_ismo, mock_ope):
        # no /proc/1/comm, ps fails, distro and system are clowncar
        # should end up return 'sys11'
        module = self._mock_module()
        module.run_command = Mock(return_value=(1, '', ''))
        collected_facts = {'distribution': 'clowncar',
                           'system': 'ClownCarOS'}
        fact_collector = self.collector_class()
        facts_dict = fact_collector.collect(module=module,
                                            collected_facts=collected_facts)
        self.assertIsInstance(facts_dict, dict)
        self.assertEqual(facts_dict['service_mgr'], 'service')

    @patch('ansible.module_utils.facts.system.service_mgr.get_file_content', return_value='runit-init')
    @patch('ansible.module_utils.facts.system.service_mgr.os.path.islink', side_effect=lambda x: x == '/sbin/init')
    @patch('ansible.module_utils.facts.system.service_mgr.os.readlink', side_effect=lambda x: '/sbin/runit-init' if x == '/sbin/init' else '/bin/false')
    def test_service_mgr_runit(self, mock_gfc, mock_opl, mock_orl):
        # /proc/1/comm contains 'runit-init', ps fails, service manager is runit
        # should end up return 'runit'
        module = self._mock_module()
        module.run_command = Mock(return_value=(1, '', ''))
        collected_facts = {'ansible_system': 'Linux'}
        fact_collector = self.collector_class()
        facts_dict = fact_collector.collect(module=module,
                                            collected_facts=collected_facts)
        self.assertIsInstance(facts_dict, dict)
        self.assertEqual(facts_dict['service_mgr'], 'runit')

    @patch('ansible.module_utils.facts.system.service_mgr.get_file_content', return_value=None)
    @patch('ansible.module_utils.facts.system.service_mgr.os.path.islink', side_effect=lambda x: x == '/sbin/init')
    @patch('ansible.module_utils.facts.system.service_mgr.os.readlink', side_effect=lambda x: '/sbin/runit-init' if x == '/sbin/init' else '/bin/false')
    def test_service_mgr_runit_no_comm(self, mock_gfc, mock_opl, mock_orl):
        # no /proc/1/comm, ps returns 'COMMAND\n', service manager is runit
        # should end up return 'runit'
        module = self._mock_module()
        module.run_command = Mock(return_value=(1, 'COMMAND\n', ''))
        collected_facts = {'ansible_system': 'Linux'}
        fact_collector = self.collector_class()
        facts_dict = fact_collector.collect(module=module,
                                            collected_facts=collected_facts)
        self.assertIsInstance(facts_dict, dict)
        self.assertEqual(facts_dict['service_mgr'], 'runit')

    # TODO: reenable these tests when we can mock more easily

#    @patch('ansible.module_utils.facts.system.service_mgr.get_file_content', return_value=None)
#    def test_sunos_fallback(self, mock_gfc):
#        # no /proc/1/comm, ps fails, 'system' is SunOS
#        # should end up return 'smf'?
#        module = self._mock_module()
#        # FIXME: the result here is a kluge to at least cover more of service_mgr.collect
#        # TODO: remove
#        # FIXME: have to force a pid for results here to get into any of the system/distro checks
#        module.run_command = Mock(return_value=(1, ' 37 ', ''))
#        collected_facts = {'system': 'SunOS'}
#        fact_collector = self.collector_class(module=module)
#        facts_dict = fact_collector.collect(collected_facts=collected_facts)
#        print('facts_dict: %s' % facts_dict)
#        self.assertIsInstance(facts_dict, dict)
#        self.assertEqual(facts_dict['service_mgr'], 'smf')

#    @patch('ansible.module_utils.facts.system.service_mgr.get_file_content', return_value=None)
#    def test_aix_fallback(self, mock_gfc):
#        # no /proc/1/comm, ps fails, 'system' is SunOS
#        # should end up return 'smf'?
#        module = self._mock_module()
#        module.run_command = Mock(return_value=(1, '', ''))
#        collected_facts = {'system': 'AIX'}
#        fact_collector = self.collector_class(module=module)
#        facts_dict = fact_collector.collect(collected_facts=collected_facts)
#        print('facts_dict: %s' % facts_dict)
#        self.assertIsInstance(facts_dict, dict)
#        self.assertEqual(facts_dict['service_mgr'], 'src')

#    @patch('ansible.module_utils.facts.system.service_mgr.get_file_content', return_value=None)
#    def test_linux_fallback(self, mock_gfc):
#        # no /proc/1/comm, ps fails, 'system' is SunOS
#        # should end up return 'smf'?
#        module = self._mock_module()
#        module.run_command = Mock(return_value=(1, '  37 ', ''))
#        collected_facts = {'system': 'Linux'}
#        fact_collector = self.collector_class(module=module)
#        facts_dict = fact_collector.collect(collected_facts=collected_facts)
#        print('facts_dict: %s' % facts_dict)
#        self.assertIsInstance(facts_dict, dict)
#        self.assertEqual(facts_dict['service_mgr'], 'sdfadf')


class TestSshPubKeyFactCollector(BaseFactsTest):
    __test__ = True
    gather_subset = ['!all', 'ssh_pub_keys']
    valid_subsets = ['ssh_pub_keys']
    fact_namespace = 'ansible_ssh_pub_leys'
    collector_class = SshPubKeyFactCollector


class TestUserFactCollector(BaseFactsTest):
    __test__ = True
    gather_subset = ['!all', 'user']
    valid_subsets = ['user']
    fact_namespace = 'ansible_user'
    collector_class = UserFactCollector


class TestVirtualFacts(BaseFactsTest):
    __test__ = True
    gather_subset = ['!all', 'virtual']
    valid_subsets = ['virtual']
    fact_namespace = 'ansible_virtual'
    collector_class = VirtualCollector
