import os
import unittest
from nose.tools import raises

from ansible import errors
from ansible.inventory import Inventory

class TestInventory(unittest.TestCase):

    def setUp(self):

        self.cwd = os.getcwd()
        self.test_dir = os.path.join(self.cwd, 'inventory_test_data')

        self.inventory_file             = os.path.join(self.test_dir, 'simple_hosts')
        self.large_range_inventory_file = os.path.join(self.test_dir, 'large_range')
        self.complex_inventory_file     = os.path.join(self.test_dir, 'complex_hosts')
        self.inventory_script           = os.path.join(self.test_dir, 'inventory_api.py')
        self.inventory_dir              = os.path.join(self.test_dir, 'inventory_dir')

        os.chmod(self.inventory_script, 0755)

    def tearDown(self):
        os.chmod(self.inventory_script, 0644)

    def compare(self, left, right, sort=True):
        if sort:
            left = sorted(left)
            right = sorted(right)
        print left
        print right
        assert left == right

    def empty_inventory(self):
        return Inventory(None)

    def simple_inventory(self):
        return Inventory(self.inventory_file)

    def large_range_inventory(self):
        return Inventory(self.large_range_inventory_file)

    def script_inventory(self):
        return Inventory(self.inventory_script)

    def complex_inventory(self):
        return Inventory(self.complex_inventory_file)

    def dir_inventory(self):
        return Inventory(self.inventory_dir)

    all_simple_hosts=['jupiter', 'saturn', 'zeus', 'hera',
            'cerberus001','cerberus002','cerberus003',
            'cottus99', 'cottus100',
            'poseidon', 'thor', 'odin', 'loki',
            'thrudgelmir0', 'thrudgelmir1', 'thrudgelmir2',
            'thrudgelmir3', 'thrudgelmir4', 'thrudgelmir5',
            'Hotep-a', 'Hotep-b', 'Hotep-c',
            'BastC', 'BastD', 'neptun', ]

    #####################################
    ### Empty inventory format tests

    def test_empty(self):
        inventory = self.empty_inventory()
        hosts = inventory.list_hosts()
        self.assertEqual(hosts, [])

    #####################################
    ### Simple inventory format tests

    def test_simple(self):
        inventory = self.simple_inventory()
        hosts = inventory.list_hosts()
        self.assertEqual(sorted(hosts), sorted(self.all_simple_hosts))

    def test_simple_all(self):
        inventory = self.simple_inventory()
        hosts = inventory.list_hosts('all')
        self.assertEqual(sorted(hosts), sorted(self.all_simple_hosts))

    def test_get_hosts(self):
        inventory = Inventory('127.0.0.1,192.168.1.1')
        hosts = inventory.get_hosts('!10.0.0.1')
        hosts_all = inventory.get_hosts('all')
        self.assertEqual(sorted(hosts), sorted(hosts_all))

    def test_no_src(self):
        inventory = Inventory('127.0.0.1,')
        self.assertEqual(inventory.src(), None)

    def test_simple_norse(self):
        inventory = self.simple_inventory()
        hosts = inventory.list_hosts("norse")

        expected_hosts=['thor', 'odin', 'loki']
        assert sorted(hosts) == sorted(expected_hosts)

    def test_simple_ungrouped(self):
        inventory = self.simple_inventory()
        hosts = inventory.list_hosts("ungrouped")

        expected_hosts=['jupiter', 'saturn',
                        'thrudgelmir0', 'thrudgelmir1', 'thrudgelmir2',
                        'thrudgelmir3', 'thrudgelmir4', 'thrudgelmir5']
        assert sorted(hosts) == sorted(expected_hosts)

    def test_simple_combined(self):
        inventory = self.simple_inventory()
        hosts = inventory.list_hosts("norse:greek")

        expected_hosts=['zeus', 'hera', 'poseidon',
                        'cerberus001','cerberus002','cerberus003',
                        'cottus99','cottus100',
                        'thor', 'odin', 'loki']
        assert sorted(hosts) == sorted(expected_hosts)

    def test_simple_restrict(self):
        inventory = self.simple_inventory()

        restricted_hosts = ['hera', 'poseidon', 'thor']
        expected_hosts=['zeus', 'hera', 'poseidon',
                        'cerberus001','cerberus002','cerberus003',
                        'cottus99', 'cottus100',
                        'thor', 'odin', 'loki']

        inventory.restrict_to(restricted_hosts)
        hosts = inventory.list_hosts("norse:greek")

        assert sorted(hosts) == sorted(restricted_hosts)

        inventory.lift_restriction()
        hosts = inventory.list_hosts("norse:greek")

        assert sorted(hosts) == sorted(expected_hosts)

    def test_simple_string_ipv4(self):
        inventory = Inventory('127.0.0.1,192.168.1.1')
        hosts = inventory.list_hosts()
        self.assertEqual(sorted(hosts), sorted(['127.0.0.1','192.168.1.1']))

    def test_simple_string_ipv4_port(self):
        inventory = Inventory('127.0.0.1:2222,192.168.1.1')
        hosts = inventory.list_hosts()
        self.assertEqual(sorted(hosts), sorted(['127.0.0.1','192.168.1.1']))

    def test_simple_string_ipv4_vars(self):
        inventory = Inventory('127.0.0.1:2222,192.168.1.1')
        var = inventory.get_variables('127.0.0.1')
        self.assertEqual(var['ansible_ssh_port'], 2222)

    def test_simple_string_ipv6(self):
        inventory = Inventory('FE80:EF45::12:1,192.168.1.1')
        hosts = inventory.list_hosts()
        self.assertEqual(sorted(hosts), sorted(['FE80:EF45::12:1','192.168.1.1']))

    def test_simple_string_ipv6_port(self):
        inventory = Inventory('[FE80:EF45::12:1]:2222,192.168.1.1')
        hosts = inventory.list_hosts()
        self.assertEqual(sorted(hosts), sorted(['FE80:EF45::12:1','192.168.1.1']))

    def test_simple_string_ipv6_vars(self):
        inventory = Inventory('[FE80:EF45::12:1]:2222,192.168.1.1')
        var = inventory.get_variables('FE80:EF45::12:1')
        self.assertEqual(var['ansible_ssh_port'], 2222)

    def test_simple_string_fqdn(self):
        inventory = Inventory('foo.example.com,bar.example.com')
        hosts = inventory.list_hosts()
        self.assertEqual(sorted(hosts), sorted(['foo.example.com','bar.example.com']))

    def test_simple_string_fqdn_port(self):
        inventory = Inventory('foo.example.com:2222,bar.example.com')
        hosts = inventory.list_hosts()
        self.assertEqual(sorted(hosts), sorted(['foo.example.com','bar.example.com']))

    def test_simple_string_fqdn_vars(self):
        inventory = Inventory('foo.example.com:2222,bar.example.com')
        var = inventory.get_variables('foo.example.com')
        self.assertEqual(var['ansible_ssh_port'], 2222)

    def test_simple_vars(self):
        inventory = self.simple_inventory()
        vars = inventory.get_variables('thor')

        assert vars == {'group_names': ['norse'],
                        'inventory_hostname': 'thor',
                        'inventory_hostname_short': 'thor'}

    def test_simple_port(self):
        inventory = self.simple_inventory()
        vars = inventory.get_variables('hera')

        expected = { 'ansible_ssh_port': 3000,
                     'group_names': ['greek'],
                     'inventory_hostname': 'hera',
                     'inventory_hostname_short': 'hera' }
        assert vars == expected

    def test_large_range(self):
        inventory = self.large_range_inventory()
        hosts = inventory.list_hosts()
        self.assertEqual(sorted(hosts),  sorted('bob%03i' %i  for i in range(0, 143)))

    def test_subset(self):
        inventory = self.simple_inventory()
        inventory.subset('odin;thor,loki')
        self.assertEqual(sorted(inventory.list_hosts()),  sorted(['thor','odin','loki']))

    def test_subset_range(self):
        inventory = self.simple_inventory()
        inventory.subset('greek[0-2];norse[0]')
        self.assertEqual(sorted(inventory.list_hosts()),  sorted(['zeus','hera','thor']))

    def test_subet_range_empty_group(self):
        inventory = self.simple_inventory()
        inventory.subset('missing[0]')
        self.assertEqual(sorted(inventory.list_hosts()), sorted([]))

    def test_subset_filename(self):
        inventory = self.simple_inventory()
        inventory.subset('@' + os.path.join(self.test_dir, 'restrict_pattern'))
        self.assertEqual(sorted(inventory.list_hosts()),  sorted(['thor','odin']))

    @raises(errors.AnsibleError)
    def testinvalid_entry(self):
       Inventory('1234')

    ###################################################
    ### INI file advanced tests

    def test_complex_vars(self):
        inventory = self.complex_inventory()

        vars = inventory.get_variables('rtp_a')
        print vars

        expected = dict(
            a=1, b=2, c=3, d=10002, e=10003, f='10004 != 10005',
            g='  g  ', h='  h  ', i="'  i  \"", j='"  j',
            k=[ 'k1', 'k2' ],
            rga=1, rgb=2, rgc=3,
            inventory_hostname='rtp_a', inventory_hostname_short='rtp_a',
            group_names=[ 'eastcoast', 'nc', 'redundantgroup', 'redundantgroup2', 'redundantgroup3', 'rtp', 'us' ]
        )
        print vars
        print expected
        assert vars == expected

    def test_complex_group_names(self):
        inventory = self.complex_inventory()
        tests = {
            'host1': [ 'role1', 'role3' ],
            'host2': [ 'role1', 'role2' ],
            'host3': [ 'role2', 'role3' ]
        }
        for host, roles in tests.iteritems():
            group_names = inventory.get_variables(host)['group_names']
            assert sorted(group_names) == sorted(roles)

    def test_complex_exclude(self):
        inventory = self.complex_inventory()
        hosts = inventory.list_hosts("nc:florida:!triangle:!orlando")
        expected_hosts = ['miami', 'rtp_a', 'rtp_b', 'rtp_c']
        print "HOSTS=%s" % sorted(hosts)
        print "EXPECTED=%s" % sorted(expected_hosts)
        assert sorted(hosts) == sorted(expected_hosts)

    def test_regex_exclude(self):
        inventory = self.complex_inventory()
        hosts = inventory.list_hosts("~rtp_[ac]")
        expected_hosts = ['rtp_a', 'rtp_c']
        print "HOSTS=%s" % sorted(hosts)
        print "EXPECTED=%s" % sorted(expected_hosts)
        assert sorted(hosts) == sorted(expected_hosts)

    def test_regex_grouping(self):
        inventory = self.simple_inventory()
        hosts = inventory.list_hosts("~(cer[a-z]|berc)(erus00[13])")
        expected_hosts = ['cerberus001', 'cerberus003']
        print "HOSTS=%s" % sorted(hosts)
        print "EXPECTED=%s" % sorted(expected_hosts)
        assert sorted(hosts) == sorted(expected_hosts)

    def test_complex_enumeration(self):


        expected1 = ['rtp_b']
        expected2 = ['rtp_a', 'rtp_b']
        expected3 = ['rtp_a', 'rtp_b', 'rtp_c', 'tri_a', 'tri_b', 'tri_c']
        expected4 = ['rtp_b', 'orlando' ]
        expected5 = ['blade-a-1']

        inventory = self.complex_inventory()
        hosts = inventory.list_hosts("nc[1]")
        self.compare(hosts, expected1, sort=False)
        hosts = inventory.list_hosts("nc[0-2]")
        self.compare(hosts, expected2, sort=False)
        hosts = inventory.list_hosts("nc[0-99999]")
        self.compare(hosts, expected3, sort=False)
        hosts = inventory.list_hosts("nc[1-2]:florida[0-1]")
        self.compare(hosts, expected4, sort=False)
        hosts = inventory.list_hosts("blade-a-1")
        self.compare(hosts, expected5, sort=False)

    def test_complex_intersect(self):
        inventory = self.complex_inventory()
        hosts = inventory.list_hosts("nc:&redundantgroup:!rtp_c")
        self.compare(hosts, ['rtp_a'])
        hosts = inventory.list_hosts("nc:&triangle:!tri_c")
        self.compare(hosts, ['tri_a', 'tri_b'])

    @raises(errors.AnsibleError)
    def test_invalid_range(self):
        Inventory(os.path.join(self.test_dir, 'inventory','test_incorrect_range'))

    @raises(errors.AnsibleError)
    def test_missing_end(self):
        Inventory(os.path.join(self.test_dir, 'inventory','test_missing_end'))

    @raises(errors.AnsibleError)
    def test_incorrect_format(self):
        Inventory(os.path.join(self.test_dir, 'inventory','test_incorrect_format'))

    @raises(errors.AnsibleError)
    def test_alpha_end_before_beg(self):
        Inventory(os.path.join(self.test_dir, 'inventory','test_alpha_end_before_beg'))

    def test_combined_range(self):
        i = Inventory(os.path.join(self.test_dir, 'inventory','test_combined_range'))
        hosts = i.list_hosts('test')
        expected_hosts=['host1A','host2A','host1B','host2B']
        assert sorted(hosts) == sorted(expected_hosts)

    def test_leading_range(self):
        i = Inventory(os.path.join(self.test_dir, 'inventory','test_leading_range'))
        hosts = i.list_hosts('test')
        expected_hosts=['1.host','2.host','A.host','B.host']
        assert sorted(hosts) == sorted(expected_hosts)

        hosts2 = i.list_hosts('test2')
        expected_hosts2=['1.host','2.host','3.host']
        assert sorted(hosts2) == sorted(expected_hosts2)

    ###################################################
    ### Inventory API tests

    def test_script(self):
        inventory = self.script_inventory()
        hosts = inventory.list_hosts()

        expected_hosts=['jupiter', 'saturn', 'zeus', 'hera', 'poseidon', 'thor', 'odin', 'loki']

        print "Expected: %s"%(expected_hosts)
        print "Got     : %s"%(hosts)
        assert sorted(hosts) == sorted(expected_hosts)

    def test_script_all(self):
        inventory = self.script_inventory()
        hosts = inventory.list_hosts('all')

        expected_hosts=['jupiter', 'saturn', 'zeus', 'hera', 'poseidon', 'thor', 'odin', 'loki']
        assert sorted(hosts) == sorted(expected_hosts)

    def test_script_norse(self):
        inventory = self.script_inventory()
        hosts = inventory.list_hosts("norse")

        expected_hosts=['thor', 'odin', 'loki']
        assert sorted(hosts) == sorted(expected_hosts)

    def test_script_combined(self):
        inventory = self.script_inventory()
        hosts = inventory.list_hosts("norse:greek")

        expected_hosts=['zeus', 'hera', 'poseidon', 'thor', 'odin', 'loki']
        assert sorted(hosts) == sorted(expected_hosts)

    def test_script_restrict(self):
        inventory = self.script_inventory()

        restricted_hosts = ['hera', 'poseidon', 'thor']
        expected_hosts=['zeus', 'hera', 'poseidon', 'thor', 'odin', 'loki']

        inventory.restrict_to(restricted_hosts)
        hosts = inventory.list_hosts("norse:greek")

        assert sorted(hosts) == sorted(restricted_hosts)

        inventory.lift_restriction()
        hosts = inventory.list_hosts("norse:greek")

        assert sorted(hosts) == sorted(expected_hosts)

    def test_script_vars(self):
        inventory = self.script_inventory()
        vars = inventory.get_variables('thor')

        print "VARS=%s" % vars

        assert vars == {'hammer':True,
                        'group_names': ['norse'],
                        'inventory_hostname': 'thor',
                        'inventory_hostname_short': 'thor'}

    def test_hosts_list(self):
        # Test the case when playbook 'hosts' var is a list.
        inventory = self.script_inventory()
        host_names = sorted(['thor', 'loki', 'odin'])       # Not sure if sorting is in the contract or not
        actual_hosts = inventory.get_hosts(host_names)
        actual_host_names = [host.name for host in actual_hosts]
        assert host_names == actual_host_names

    def test_script_multiple_groups(self):
        inventory = self.script_inventory()
        vars = inventory.get_variables('zeus')

        print "VARS=%s" % vars

        assert vars == {'inventory_hostname': 'zeus',
                        'inventory_hostname_short': 'zeus',
                        'group_names': ['greek', 'major-god']}

    def test_allows_equals_sign_in_var(self):
        inventory = self.simple_inventory()
        auth = inventory.get_variables('neptun')['auth']
        assert auth == 'YWRtaW46YWRtaW4='

    def test_dir_inventory(self):
        inventory = self.dir_inventory()

        host_vars = inventory.get_variables('zeus')

        expected_vars = {'inventory_hostname': 'zeus',
                         'inventory_hostname_short': 'zeus',
                         'group_names': ['greek', 'major-god'],
                         'var_a': '3#4'}

        print "HOST     VARS=%s" % host_vars
        print "EXPECTED VARS=%s" % expected_vars

        assert host_vars == expected_vars

    def test_dir_inventory_multiple_groups(self):
        inventory = self.dir_inventory()
        group_greek = inventory.get_hosts('greek')
        actual_host_names = [host.name for host in group_greek]
        print "greek : %s " % actual_host_names
        assert actual_host_names == ['zeus', 'morpheus']

    def test_dir_inventory_skip_extension(self):
        inventory = self.dir_inventory()
        assert 'skipme' not in [h.name for h in inventory.get_hosts()]

    def test_dir_inventory_group_hosts(self):
        inventory = self.dir_inventory()
        expected_groups = {'all': ['morpheus', 'thor', 'zeus'],
                           'major-god': ['thor', 'zeus'],
                           'minor-god': ['morpheus'],
                           'norse': ['thor'],
                           'greek': ['morpheus', 'zeus'],
                           'ungrouped': []}

        actual_groups = {}
        for group in inventory.get_groups():
            actual_groups[group.name] = sorted([h.name for h in group.get_hosts()])
            print "INVENTORY groups[%s].hosts=%s" % (group.name, actual_groups[group.name])
            print "EXPECTED  groups[%s].hosts=%s" % (group.name, expected_groups[group.name])

        assert actual_groups == expected_groups

    def test_dir_inventory_groups_for_host(self):
        inventory = self.dir_inventory()
        expected_groups_for_host = {'morpheus': ['all', 'greek', 'minor-god'],
                                    'thor': ['all', 'major-god', 'norse'],
                                    'zeus': ['all', 'greek', 'major-god']}

        actual_groups_for_host = {}
        for (host, expected) in expected_groups_for_host.iteritems():
            groups = inventory.groups_for_host(host)
            names = sorted([g.name for g in groups])
            actual_groups_for_host[host] = names
            print "INVENTORY groups_for_host(%s)=%s" % (host, names)
            print "EXPECTED  groups_for_host(%s)=%s" % (host, expected)

        assert actual_groups_for_host == expected_groups_for_host

    def test_dir_inventory_groups_list(self):
        inventory = self.dir_inventory()
        inventory_groups = inventory.groups_list()

        expected_groups = {'all': ['morpheus', 'thor', 'zeus'],
                           'major-god': ['thor', 'zeus'],
                           'minor-god': ['morpheus'],
                           'norse': ['thor'],
                           'greek': ['morpheus', 'zeus'],
                           'ungrouped': []}

        for (name, expected_hosts) in expected_groups.iteritems():
            inventory_groups[name] = sorted(inventory_groups.get(name, []))
            print "INVENTORY groups_list['%s']=%s" % (name, inventory_groups[name])
            print "EXPECTED  groups_list['%s']=%s" % (name, expected_hosts)

        assert inventory_groups == expected_groups

