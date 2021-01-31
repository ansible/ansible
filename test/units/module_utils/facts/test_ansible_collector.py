# -*- coding: utf-8 -*-
#
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

# for testing
from units.compat import unittest
from units.compat.mock import Mock, patch

from ansible.module_utils.facts import collector
from ansible.module_utils.facts import ansible_collector
from ansible.module_utils.facts import namespace

from ansible.module_utils.facts.other.facter import FacterFactCollector
from ansible.module_utils.facts.other.ohai import OhaiFactCollector

from ansible.module_utils.facts.system.apparmor import ApparmorFactCollector
from ansible.module_utils.facts.system.caps import SystemCapabilitiesFactCollector
from ansible.module_utils.facts.system.date_time import DateTimeFactCollector
from ansible.module_utils.facts.system.env import EnvFactCollector
from ansible.module_utils.facts.system.distribution import DistributionFactCollector
from ansible.module_utils.facts.system.dns import DnsFactCollector
from ansible.module_utils.facts.system.fips import FipsFactCollector
from ansible.module_utils.facts.system.local import LocalFactCollector
from ansible.module_utils.facts.system.lsb import LSBFactCollector
from ansible.module_utils.facts.system.pkg_mgr import PkgMgrFactCollector, OpenBSDPkgMgrFactCollector
from ansible.module_utils.facts.system.platform import PlatformFactCollector
from ansible.module_utils.facts.system.python import PythonFactCollector
from ansible.module_utils.facts.system.selinux import SelinuxFactCollector
from ansible.module_utils.facts.system.service_mgr import ServiceMgrFactCollector
from ansible.module_utils.facts.system.user import UserFactCollector

# from ansible.module_utils.facts.hardware.base import HardwareCollector
from ansible.module_utils.facts.network.base import NetworkCollector
from ansible.module_utils.facts.virtual.base import VirtualCollector

ALL_COLLECTOR_CLASSES = \
    [PlatformFactCollector,
     DistributionFactCollector,
     SelinuxFactCollector,
     ApparmorFactCollector,
     SystemCapabilitiesFactCollector,
     FipsFactCollector,
     PkgMgrFactCollector,
     OpenBSDPkgMgrFactCollector,
     ServiceMgrFactCollector,
     LSBFactCollector,
     DateTimeFactCollector,
     UserFactCollector,
     LocalFactCollector,
     EnvFactCollector,
     DnsFactCollector,
     PythonFactCollector,
     # FIXME: re-enable when hardware doesnt Hardware() doesnt munge self.facts
     #                         HardwareCollector
     NetworkCollector,
     VirtualCollector,
     OhaiFactCollector,
     FacterFactCollector]


def mock_module(gather_subset=None,
                filter=None):
    if gather_subset is None:
        gather_subset = ['all', '!facter', '!ohai']
    if filter is None:
        filter = '*'
    mock_module = Mock()
    mock_module.params = {'gather_subset': gather_subset,
                          'gather_timeout': 5,
                          'filter': filter}
    mock_module.get_bin_path = Mock(return_value=None)
    return mock_module


def _collectors(module,
                all_collector_classes=None,
                minimal_gather_subset=None):
    gather_subset = module.params.get('gather_subset')
    if all_collector_classes is None:
        all_collector_classes = ALL_COLLECTOR_CLASSES
    if minimal_gather_subset is None:
        minimal_gather_subset = frozenset([])

    collector_classes = \
        collector.collector_classes_from_gather_subset(all_collector_classes=all_collector_classes,
                                                       minimal_gather_subset=minimal_gather_subset,
                                                       gather_subset=gather_subset)

    collectors = []
    for collector_class in collector_classes:
        collector_obj = collector_class()
        collectors.append(collector_obj)

    # Add a collector that knows what gather_subset we used so it it can provide a fact
    collector_meta_data_collector = \
        ansible_collector.CollectorMetaDataCollector(gather_subset=gather_subset,
                                                     module_setup=True)
    collectors.append(collector_meta_data_collector)

    return collectors


ns = namespace.PrefixFactNamespace('ansible_facts', 'ansible_')


# FIXME: this is brute force, but hopefully enough to get some refactoring to make facts testable
class TestInPlace(unittest.TestCase):
    def _mock_module(self, gather_subset=None):
        return mock_module(gather_subset=gather_subset)

    def _collectors(self, module,
                    all_collector_classes=None,
                    minimal_gather_subset=None):
        return _collectors(module=module,
                           all_collector_classes=all_collector_classes,
                           minimal_gather_subset=minimal_gather_subset)

    def test(self):
        gather_subset = ['all']
        mock_module = self._mock_module(gather_subset=gather_subset)
        all_collector_classes = [EnvFactCollector]
        collectors = self._collectors(mock_module,
                                      all_collector_classes=all_collector_classes)

        fact_collector = \
            ansible_collector.AnsibleFactCollector(collectors=collectors,
                                                   namespace=ns)

        res = fact_collector.collect(module=mock_module)
        self.assertIsInstance(res, dict)
        self.assertIn('env', res)
        self.assertIn('gather_subset', res)
        self.assertEqual(res['gather_subset'], ['all'])

    def test1(self):
        gather_subset = ['all']
        mock_module = self._mock_module(gather_subset=gather_subset)
        collectors = self._collectors(mock_module)

        fact_collector = \
            ansible_collector.AnsibleFactCollector(collectors=collectors,
                                                   namespace=ns)

        res = fact_collector.collect(module=mock_module)
        self.assertIsInstance(res, dict)
        # just assert it's not almost empty
        # with run_command and get_file_content mock, many facts are empty, like network
        self.assertGreater(len(res), 20)

    def test_empty_all_collector_classes(self):
        mock_module = self._mock_module()
        all_collector_classes = []

        collectors = self._collectors(mock_module,
                                      all_collector_classes=all_collector_classes)

        fact_collector = \
            ansible_collector.AnsibleFactCollector(collectors=collectors,
                                                   namespace=ns)

        res = fact_collector.collect()
        self.assertIsInstance(res, dict)
        # just assert it's not almost empty
        self.assertLess(len(res), 3)

#    def test_facts_class(self):
#        mock_module = self._mock_module()
#        Facts(mock_module)

#    def test_facts_class_load_on_init_false(self):
#        mock_module = self._mock_module()
#        Facts(mock_module, load_on_init=False)
#        # FIXME: assert something


class TestCollectedFacts(unittest.TestCase):
    gather_subset = ['all', '!facter', '!ohai']
    min_fact_count = 30
    max_fact_count = 1000

    # TODO: add ansible_cmdline, ansible_*_pubkey* back when TempFactCollector goes away
    expected_facts = ['date_time',
                      'user_id', 'distribution',
                      'gather_subset', 'module_setup',
                      'env']
    not_expected_facts = ['facter', 'ohai']

    collected_facts = {}

    def _mock_module(self, gather_subset=None):
        return mock_module(gather_subset=self.gather_subset)

    @patch('platform.system', return_value='Linux')
    @patch('ansible.module_utils.facts.system.service_mgr.get_file_content', return_value='systemd')
    def setUp(self, mock_gfc, mock_ps):
        mock_module = self._mock_module()
        collectors = self._collectors(mock_module)

        fact_collector = \
            ansible_collector.AnsibleFactCollector(collectors=collectors,
                                                   namespace=ns)
        self.facts = fact_collector.collect(module=mock_module,
                                            collected_facts=self.collected_facts)

    def _collectors(self, module,
                    all_collector_classes=None,
                    minimal_gather_subset=None):
        return _collectors(module=module,
                           all_collector_classes=all_collector_classes,
                           minimal_gather_subset=minimal_gather_subset)

    def test_basics(self):
        self._assert_basics(self.facts)

    def test_expected_facts(self):
        self._assert_expected_facts(self.facts)

    def test_not_expected_facts(self):
        self._assert_not_expected_facts(self.facts)

    def _assert_basics(self, facts):
        self.assertIsInstance(facts, dict)
        # just assert it's not almost empty
        self.assertGreaterEqual(len(facts), self.min_fact_count)
        # and that is not huge number of keys
        self.assertLess(len(facts), self.max_fact_count)

    # everything starts with ansible_ namespace
    def _assert_ansible_namespace(self, facts):

        # FIXME: kluge for non-namespace fact
        facts.pop('module_setup', None)
        facts.pop('gather_subset', None)

        for fact_key in facts:
            self.assertTrue(fact_key.startswith('ansible_'),
                            'The fact name "%s" does not startwith "ansible_"' % fact_key)

    def _assert_expected_facts(self, facts):

        facts_keys = sorted(facts.keys())
        for expected_fact in self.expected_facts:
            self.assertIn(expected_fact, facts_keys)

    def _assert_not_expected_facts(self, facts):

        facts_keys = sorted(facts.keys())
        for not_expected_fact in self.not_expected_facts:
            self.assertNotIn(not_expected_fact, facts_keys)


class ProvidesOtherFactCollector(collector.BaseFactCollector):
    name = 'provides_something'
    _fact_ids = set(['needed_fact'])

    def collect(self, module=None, collected_facts=None):
        return {'needed_fact': 'THE_NEEDED_FACT_VALUE'}


class RequiresOtherFactCollector(collector.BaseFactCollector):
    name = 'requires_something'

    def collect(self, module=None, collected_facts=None):
        collected_facts = collected_facts or {}
        fact_dict = {}
        fact_dict['needed_fact'] = collected_facts['needed_fact']
        fact_dict['compound_fact'] = "compound-%s" % collected_facts['needed_fact']
        return fact_dict


class ConCatFactCollector(collector.BaseFactCollector):
    name = 'concat_collected'

    def collect(self, module=None, collected_facts=None):
        collected_facts = collected_facts or {}
        fact_dict = {}
        con_cat_list = []
        for key, value in collected_facts.items():
            con_cat_list.append(value)

        fact_dict['concat_fact'] = '-'.join(con_cat_list)
        return fact_dict


class TestCollectorDepsWithFilter(unittest.TestCase):
    gather_subset = ['all', '!facter', '!ohai']

    def _mock_module(self, gather_subset=None, filter=None):
        return mock_module(gather_subset=self.gather_subset,
                           filter=filter)

    def setUp(self):
        self.mock_module = self._mock_module()
        self.collectors = self._collectors(mock_module)

    def _collectors(self, module,
                    all_collector_classes=None,
                    minimal_gather_subset=None):
        return [ProvidesOtherFactCollector(),
                RequiresOtherFactCollector()]

    def test_no_filter(self):
        _mock_module = mock_module(gather_subset=['all', '!facter', '!ohai'])

        facts_dict = self._collect(_mock_module)

        expected = {'needed_fact': 'THE_NEEDED_FACT_VALUE',
                    'compound_fact': 'compound-THE_NEEDED_FACT_VALUE'}

        self.assertEqual(expected, facts_dict)

    def test_with_filter_on_compound_fact(self):
        _mock_module = mock_module(gather_subset=['all', '!facter', '!ohai'],
                                   filter='compound_fact')

        facts_dict = self._collect(_mock_module)

        expected = {'compound_fact': 'compound-THE_NEEDED_FACT_VALUE'}

        self.assertEqual(expected, facts_dict)

    def test_with_filter_on_needed_fact(self):
        _mock_module = mock_module(gather_subset=['all', '!facter', '!ohai'],
                                   filter='needed_fact')

        facts_dict = self._collect(_mock_module)

        expected = {'needed_fact': 'THE_NEEDED_FACT_VALUE'}

        self.assertEqual(expected, facts_dict)

    def test_with_filter_on_compound_gather_compound(self):
        _mock_module = mock_module(gather_subset=['!all', '!any', 'compound_fact'],
                                   filter='compound_fact')

        facts_dict = self._collect(_mock_module)

        expected = {'compound_fact': 'compound-THE_NEEDED_FACT_VALUE'}

        self.assertEqual(expected, facts_dict)

    def test_with_filter_no_match(self):
        _mock_module = mock_module(gather_subset=['all', '!facter', '!ohai'],
                                   filter='ansible_this_doesnt_exist')

        facts_dict = self._collect(_mock_module)

        expected = {}
        self.assertEqual(expected, facts_dict)

    def test_concat_collector(self):
        _mock_module = mock_module(gather_subset=['all', '!facter', '!ohai'])

        _collectors = self._collectors(_mock_module)
        _collectors.append(ConCatFactCollector())

        fact_collector = \
            ansible_collector.AnsibleFactCollector(collectors=_collectors,
                                                   namespace=ns,
                                                   filter_spec=_mock_module.params['filter'])

        collected_facts = {}
        facts_dict = fact_collector.collect(module=_mock_module,
                                            collected_facts=collected_facts)
        self.assertIn('concat_fact', facts_dict)
        self.assertTrue('THE_NEEDED_FACT_VALUE' in facts_dict['concat_fact'])

    def test_concat_collector_with_filter_on_concat(self):
        _mock_module = mock_module(gather_subset=['all', '!facter', '!ohai'],
                                   filter='concat_fact')

        _collectors = self._collectors(_mock_module)
        _collectors.append(ConCatFactCollector())

        fact_collector = \
            ansible_collector.AnsibleFactCollector(collectors=_collectors,
                                                   namespace=ns,
                                                   filter_spec=_mock_module.params['filter'])

        collected_facts = {}
        facts_dict = fact_collector.collect(module=_mock_module,
                                            collected_facts=collected_facts)
        self.assertIn('concat_fact', facts_dict)
        self.assertTrue('THE_NEEDED_FACT_VALUE' in facts_dict['concat_fact'])
        self.assertTrue('compound' in facts_dict['concat_fact'])

    def _collect(self, _mock_module, collected_facts=None):
        _collectors = self._collectors(_mock_module)

        fact_collector = \
            ansible_collector.AnsibleFactCollector(collectors=_collectors,
                                                   namespace=ns,
                                                   filter_spec=_mock_module.params['filter'])
        facts_dict = fact_collector.collect(module=_mock_module,
                                            collected_facts=collected_facts)
        return facts_dict


class ExceptionThrowingCollector(collector.BaseFactCollector):
    def collect(self, module=None, collected_facts=None):
        raise Exception('A collector failed')


class TestExceptionCollectedFacts(TestCollectedFacts):

    def _collectors(self, module,
                    all_collector_classes=None,
                    minimal_gather_subset=None):
        collectors = _collectors(module=module,
                                 all_collector_classes=all_collector_classes,
                                 minimal_gather_subset=minimal_gather_subset)

        c = [ExceptionThrowingCollector()] + collectors
        return c


class TestOnlyExceptionCollector(TestCollectedFacts):
    expected_facts = []
    min_fact_count = 0

    def _collectors(self, module,
                    all_collector_classes=None,
                    minimal_gather_subset=None):
        return [ExceptionThrowingCollector()]


class TestMinimalCollectedFacts(TestCollectedFacts):
    gather_subset = ['!all']
    min_fact_count = 1
    max_fact_count = 10
    expected_facts = ['gather_subset',
                      'module_setup']
    not_expected_facts = ['lsb']


class TestFacterCollectedFacts(TestCollectedFacts):
    gather_subset = ['!all', 'facter']
    min_fact_count = 1
    max_fact_count = 10
    expected_facts = ['gather_subset',
                      'module_setup']
    not_expected_facts = ['lsb']


class TestOhaiCollectedFacts(TestCollectedFacts):
    gather_subset = ['!all', 'ohai']
    min_fact_count = 1
    max_fact_count = 10
    expected_facts = ['gather_subset',
                      'module_setup']
    not_expected_facts = ['lsb']


class TestPkgMgrFacts(TestCollectedFacts):
    gather_subset = ['pkg_mgr']
    min_fact_count = 1
    max_fact_count = 20
    expected_facts = ['gather_subset',
                      'module_setup',
                      'pkg_mgr']
    collected_facts = {
        "ansible_distribution": "Fedora",
        "ansible_distribution_major_version": "28",
        "ansible_os_family": "RedHat"
    }


class TestPkgMgrOSTreeFacts(TestPkgMgrFacts):
    @patch(
        'ansible.module_utils.facts.system.pkg_mgr.os.path.exists',
        side_effect=lambda x: x == '/run/ostree-booted')
    def _recollect_facts(self, distribution, version, mock_exists):
        self.collected_facts['ansible_distribution'] = distribution
        self.collected_facts['ansible_distribution_major_version'] = \
            str(version)
        # Recollect facts
        self.setUp()
        self.assertIn('pkg_mgr', self.facts)
        self.assertEqual(self.facts['pkg_mgr'], 'atomic_container')

    def test_is_rhel_edge_ostree(self):
        self._recollect_facts('RedHat', 8)

    def test_is_fedora_ostree(self):
        self._recollect_facts('Fedora', 33)


class TestOpenBSDPkgMgrFacts(TestPkgMgrFacts):
    def test_is_openbsd_pkg(self):
        self.assertIn('pkg_mgr', self.facts)
        self.assertEqual(self.facts['pkg_mgr'], 'openbsd_pkg')

    def setUp(self):
        self.patcher = patch('platform.system')
        mock_platform = self.patcher.start()
        mock_platform.return_value = 'OpenBSD'

        mock_module = self._mock_module()
        collectors = self._collectors(mock_module)

        fact_collector = \
            ansible_collector.AnsibleFactCollector(collectors=collectors,
                                                   namespace=ns)
        self.facts = fact_collector.collect(module=mock_module)

    def tearDown(self):
        self.patcher.stop()
