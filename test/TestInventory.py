import os
import unittest

from ansible.inventory import Inventory
from ansible.runner import Runner
# from nose.plugins.skip import SkipTest

class TestInventory(unittest.TestCase):

    def setUp(self):
        self.cwd = os.getcwd()
        self.test_dir = os.path.join(self.cwd, 'test')

        self.inventory_file         = os.path.join(self.test_dir, 'simple_hosts')
        self.complex_inventory_file = os.path.join(self.test_dir, 'complex_hosts')
        self.inventory_script       = os.path.join(self.test_dir, 'inventory_api.py')
        self.inventory_yaml         = os.path.join(self.test_dir, 'yaml_hosts')

        os.chmod(self.inventory_script, 0755)

    def tearDown(self):
        os.chmod(self.inventory_script, 0644)

    def compare(self, left, right):
        left = sorted(left)
        right = sorted(right)
        print left
        print right
        assert left == right


    def simple_inventory(self):
        return Inventory(self.inventory_file)

    def script_inventory(self):
        return Inventory(self.inventory_script)

    def yaml_inventory(self):
        return Inventory(self.inventory_yaml)

    def complex_inventory(self):
        return Inventory(self.complex_inventory_file)

    #####################################
    ### Simple inventory format tests

    def test_simple(self):
        inventory = self.simple_inventory()
        hosts = inventory.list_hosts()

        expected_hosts=['jupiter', 'saturn', 'zeus', 'hera', 'poseidon', 'thor', 'odin', 'loki']
        assert sorted(hosts) == sorted(expected_hosts)

    def test_simple_all(self):
        inventory = self.simple_inventory()
        hosts = inventory.list_hosts('all')

        expected_hosts=['jupiter', 'saturn', 'zeus', 'hera', 'poseidon', 'thor', 'odin', 'loki']
        assert sorted(hosts) == sorted(expected_hosts)

    def test_simple_norse(self):
        inventory = self.simple_inventory()
        hosts = inventory.list_hosts("norse")

        expected_hosts=['thor', 'odin', 'loki']
        assert sorted(hosts) == sorted(expected_hosts)

    def test_simple_ungrouped(self):
        inventory = self.simple_inventory()
        hosts = inventory.list_hosts("ungrouped")

        expected_hosts=['jupiter', 'saturn']
        assert sorted(hosts) == sorted(expected_hosts)

    def test_simple_combined(self):
        inventory = self.simple_inventory()
        hosts = inventory.list_hosts("norse:greek")

        expected_hosts=['zeus', 'hera', 'poseidon', 'thor', 'odin', 'loki']
        assert sorted(hosts) == sorted(expected_hosts)

    def test_simple_restrict(self):
        inventory = self.simple_inventory()

        restricted_hosts = ['hera', 'poseidon', 'thor']
        expected_hosts=['zeus', 'hera', 'poseidon', 'thor', 'odin', 'loki']

        inventory.restrict_to(restricted_hosts)
        hosts = inventory.list_hosts("norse:greek")

        print "Hosts=%s" % hosts
        print "Restricted=%s" % restricted_hosts
        assert sorted(hosts) == sorted(restricted_hosts)

        inventory.lift_restriction()
        hosts = inventory.list_hosts("norse:greek")

        print hosts
        print expected_hosts
        assert sorted(hosts) == sorted(expected_hosts)

    def test_simple_exclude(self):
        inventory = self.simple_inventory()

        hosts = inventory.list_hosts("all:!greek")
        expected_hosts=['jupiter', 'saturn', 'thor', 'odin', 'loki']
        assert sorted(hosts) == sorted(expected_hosts)

        hosts = inventory.list_hosts("all:!norse:!greek")
        expected_hosts=['jupiter', 'saturn']
        assert sorted(hosts) == sorted(expected_hosts)

    def test_simple_vars(self):
        inventory = self.simple_inventory()
        vars = inventory.get_variables('thor')

        print vars
        assert vars == {'group_names': ['norse'],
                        'inventory_hostname': 'thor'}

    def test_simple_port(self):
        inventory = self.simple_inventory()
        vars = inventory.get_variables('hera')

        print vars
        expected = {'ansible_ssh_port': 3000,
                        'group_names': ['greek'],
                        'inventory_hostname': 'hera'}
        print expected
        assert vars == expected

    ###################################################
    ### INI file advanced tests

    def test_complex_vars(self):
        inventory = self.complex_inventory()

        vars = inventory.get_variables('rtp_a')
        print vars

        expected = dict(
            a='1', b='2', c='3', d='100002', rga='1', rgb='2', rgc='3', 
            inventory_hostname='rtp_a', 
            group_names=[ 'eastcoast', 'nc', 'redundantgroup', 'redundantgroup2', 'redundantgroup3', 'rtp', 'us' ]
        )
        print vars
        print expected
        assert vars == expected

    def test_complex_exclude(self):
        inventory = self.complex_inventory()

        hosts = inventory.list_hosts("nc:!triangle:florida:!orlando")
        expected_hosts=['rtp_a', 'rtp_b', 'rtb_c', 'miami']
        assert sorted(hosts) == sorted(expected_hosts)



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
                        'inventory_hostname': 'thor'}

    ### Tests for yaml inventory file

    def test_yaml(self):
        inventory = self.yaml_inventory()
        hosts = inventory.list_hosts()
        expected_hosts=['garfield', 'goofy', 'hera', 'jerry', 'jupiter', 'loki', 'mars', 'mickey', 'odie', 'odin', 'poseidon', 'saturn', 'thor', 'tom', 'zeus']
        self.compare(hosts, expected_hosts)

    def test_yaml_all(self):
        inventory = self.yaml_inventory()
        hosts = inventory.list_hosts('all')

        expected_hosts=['garfield', 'goofy', 'hera', 'jerry', 'jupiter', 'loki', 'mars', 'mickey', 'odie', 'odin', 'poseidon', 'saturn', 'thor', 'tom', 'zeus']
        self.compare(hosts, expected_hosts)

    def test_yaml_norse(self):
        inventory = self.yaml_inventory()
        hosts = inventory.list_hosts("norse")

        expected_hosts=['thor', 'odin', 'loki']
        self.compare(hosts, expected_hosts)

    def test_yaml_ungrouped(self):
        inventory = self.yaml_inventory()
        hosts = inventory.list_hosts("ungrouped")

        expected_hosts=['jupiter', 'mars']
        self.compare(hosts, expected_hosts)

    def test_yaml_combined(self):
        inventory = self.yaml_inventory()
        hosts = inventory.list_hosts("norse:greek")

        expected_hosts=['zeus', 'hera', 'poseidon', 'thor', 'odin', 'loki']
        self.compare(hosts, expected_hosts)

    def test_yaml_restrict(self):
        inventory = self.yaml_inventory()

        restricted_hosts = ['hera', 'poseidon', 'thor']
        expected_hosts=['zeus', 'hera', 'poseidon', 'thor', 'odin', 'loki']

        inventory.restrict_to(restricted_hosts)
        hosts = inventory.list_hosts("norse:greek")

        self.compare(hosts, restricted_hosts)

        inventory.lift_restriction()
        hosts = inventory.list_hosts("norse:greek")

        self.compare(hosts, expected_hosts)

    def test_yaml_vars(self):
        inventory = self.yaml_inventory()
        vars = inventory.get_variables('thor')
        assert vars == {'group_names': ['norse'],
                        'hammer':True,
                        'inventory_hostname': 'thor'}

    def test_yaml_list_vars(self):
        inventory = self.yaml_inventory()
        vars = inventory.get_variables('zeus')
        assert vars == {'ansible_ssh_port': 3001,
                        'group_names': ['greek', 'ruler'],
                        'inventory_hostname': 'zeus',
                        'ntp_server': 'olympus.example.com'}

    def test_yaml_change_vars(self):
        inventory = self.yaml_inventory()
        vars = inventory.get_variables('thor')

        vars["hammer"] = False

        vars = inventory.get_variables('thor')
        print vars
        assert vars == {'hammer':True,
                        'inventory_hostname': 'thor',
                        'group_names': ['norse']}

    def test_yaml_host_vars(self):
        inventory = self.yaml_inventory()
        vars = inventory.get_variables('saturn')

        print vars
        assert vars == {'inventory_hostname': 'saturn',
                        'moon': 'titan',
                        'moon2': 'enceladus',
                        'group_names': ['multiple']}

    def test_yaml_port(self):
        inventory = self.yaml_inventory()
        vars = inventory.get_variables('hera')

        print vars
        assert vars == {'ansible_ssh_port': 3000,
                        'inventory_hostname': 'hera',
                        'ntp_server': 'olympus.example.com',
                        'group_names': ['greek']}

    def test_yaml_multiple_groups(self):
        inventory = self.yaml_inventory()
        vars = inventory.get_variables('odin')

        assert 'group_names' in vars
        assert sorted(vars['group_names']) == [ 'norse', 'ruler' ]

    def test_yaml_some_animals(self):
        inventory = self.yaml_inventory()
        hosts = inventory.list_hosts("cat:mouse")
        expected_hosts=['garfield', 'jerry', 'mickey', 'tom']
        self.compare(hosts, expected_hosts)

    def test_yaml_comic(self):
        inventory = self.yaml_inventory()
        hosts = inventory.list_hosts("comic")
        expected_hosts=['garfield', 'odie']
        self.compare(hosts, expected_hosts)

    def test_yaml_orange(self):
        inventory = self.yaml_inventory()
        hosts = inventory.list_hosts("orange")
        expected_hosts=['garfield', 'goofy']
        self.compare(hosts, expected_hosts)

    def test_yaml_garfield_vars(self):
        inventory = self.yaml_inventory()
        vars = inventory.get_variables('garfield')
        assert vars == {'ears': 'pointy',
                        'inventory_hostname': 'garfield',
                        'group_names': ['cat', 'comic', 'orange'],
                        'nose': 'pink'}
 
