from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from units.compat.mock import patch
from ansible.module_utils import basic
from ansible.modules import iptables
from units.modules.utils import AnsibleExitJson, AnsibleFailJson, ModuleTestCase, set_module_args


def get_bin_path(*args, **kwargs):
    return "/sbin/iptables"


def get_iptables_version(iptables_path, module):
    return "1.8.2"


class TestIptables(ModuleTestCase):

    def setUp(self):
        super(TestIptables, self).setUp()
        self.mock_get_bin_path = patch.object(basic.AnsibleModule, 'get_bin_path', get_bin_path)
        self.mock_get_bin_path.start()
        self.addCleanup(self.mock_get_bin_path.stop)  # ensure that the patching is 'undone'
        self.mock_get_iptables_version = patch.object(iptables, 'get_iptables_version', get_iptables_version)
        self.mock_get_iptables_version.start()
        self.addCleanup(self.mock_get_iptables_version.stop)  # ensure that the patching is 'undone'

    def test_without_required_parameters(self):
        """Failure must occurs when all parameters are missing"""
        with self.assertRaises(AnsibleFailJson):
            set_module_args({})
            iptables.main()

    def test_flush_table_without_chain(self):
        """Test flush without chain, flush the table"""
        set_module_args({
            'flush': True,
        })

        with patch.object(basic.AnsibleModule, 'run_command') as run_command:
            run_command.return_value = 0, '', ''  # successful execution, no output
            with self.assertRaises(AnsibleExitJson) as result:
                iptables.main()
                self.assertTrue(result.exception.args[0]['changed'])

        self.assertEqual(run_command.call_count, 1)
        self.assertEqual(run_command.call_args[0][0][0], '/sbin/iptables')
        self.assertEqual(run_command.call_args[0][0][1], '-t')
        self.assertEqual(run_command.call_args[0][0][2], 'filter')
        self.assertEqual(run_command.call_args[0][0][3], '-F')

    def test_flush_table_check_true(self):
        """Test flush without parameters and check == true"""
        set_module_args({
            'flush': True,
            '_ansible_check_mode': True,
        })

        with patch.object(basic.AnsibleModule, 'run_command') as run_command:
            run_command.return_value = 0, '', ''  # successful execution, no output
            with self.assertRaises(AnsibleExitJson) as result:
                iptables.main()
                self.assertTrue(result.exception.args[0]['changed'])

        self.assertEqual(run_command.call_count, 0)

# TODO ADD test flush table nat
# TODO ADD test flush with chain
# TODO ADD test flush with chain and table nat

    def test_policy_table(self):
        """Test change policy of a chain"""
        set_module_args({
            'policy': 'ACCEPT',
            'chain': 'INPUT',
        })
        commands_results = [
            (0, 'Chain INPUT (policy DROP)\n', ''),
            (0, '', '')
        ]

        with patch.object(basic.AnsibleModule, 'run_command') as run_command:
            run_command.side_effect = commands_results
            with self.assertRaises(AnsibleExitJson) as result:
                iptables.main()
                self.assertTrue(result.exception.args[0]['changed'])

        self.assertEqual(run_command.call_count, 2)
        # import pdb
        # pdb.set_trace()
        self.assertEqual(run_command.call_args_list[0][0][0], [
            '/sbin/iptables',
            '-t',
            'filter',
            '-L',
            'INPUT',
        ])
        self.assertEqual(run_command.call_args_list[1][0][0], [
            '/sbin/iptables',
            '-t',
            'filter',
            '-P',
            'INPUT',
            'ACCEPT',
        ])

    def test_policy_table_no_change(self):
        """Test don't change policy of a chain if the policy is right"""
        set_module_args({
            'policy': 'ACCEPT',
            'chain': 'INPUT',
        })
        commands_results = [
            (0, 'Chain INPUT (policy ACCEPT)\n', ''),
            (0, '', '')
        ]

        with patch.object(basic.AnsibleModule, 'run_command') as run_command:
            run_command.side_effect = commands_results
            with self.assertRaises(AnsibleExitJson) as result:
                iptables.main()
                self.assertFalse(result.exception.args[0]['changed'])

        self.assertEqual(run_command.call_count, 1)
        # import pdb
        # pdb.set_trace()
        self.assertEqual(run_command.call_args_list[0][0][0], [
            '/sbin/iptables',
            '-t',
            'filter',
            '-L',
            'INPUT',
        ])

    def test_policy_table_changed_false(self):
        """Test flush without parameters and change == false"""
        set_module_args({
            'policy': 'ACCEPT',
            'chain': 'INPUT',
            '_ansible_check_mode': True,
        })
        commands_results = [
            (0, 'Chain INPUT (policy DROP)\n', ''),
        ]

        with patch.object(basic.AnsibleModule, 'run_command') as run_command:
            run_command.side_effect = commands_results
            with self.assertRaises(AnsibleExitJson) as result:
                iptables.main()
                self.assertTrue(result.exception.args[0]['changed'])

        self.assertEqual(run_command.call_count, 1)
        # import pdb
        # pdb.set_trace()
        self.assertEqual(run_command.call_args_list[0][0][0], [
            '/sbin/iptables',
            '-t',
            'filter',
            '-L',
            'INPUT',
        ])

# TODO ADD test policy without chain fail
# TODO ADD test policy with chain don't exists
# TODO ADD test policy with wrong choice fail

    def test_insert_rule_change_false(self):
        """Test flush without parameters"""
        set_module_args({
            'chain': 'OUTPUT',
            'source': '1.2.3.4/32',
            'destination': '7.8.9.10/42',
            'jump': 'ACCEPT',
            'action': 'insert',
            '_ansible_check_mode': True,
        })

        commands_results = [
            (1, '', ''),
            (0, '', '')
        ]

        with patch.object(basic.AnsibleModule, 'run_command') as run_command:
            run_command.side_effect = commands_results
            with self.assertRaises(AnsibleExitJson) as result:
                iptables.main()
                self.assertTrue(result.exception.args[0]['changed'])

        self.assertEqual(run_command.call_count, 1)
        # import pdb
        # pdb.set_trace()
        self.assertEqual(run_command.call_args_list[0][0][0], [
            '/sbin/iptables',
            '-t',
            'filter',
            '-C',
            'OUTPUT',
            '-s',
            '1.2.3.4/32',
            '-d',
            '7.8.9.10/42',
            '-j',
            'ACCEPT'
        ])

    def test_insert_rule(self):
        """Test flush without parameters"""
        set_module_args({
            'chain': 'OUTPUT',
            'source': '1.2.3.4/32',
            'destination': '7.8.9.10/42',
            'jump': 'ACCEPT',
            'action': 'insert'
        })

        commands_results = [
            (1, '', ''),
            (0, '', '')
        ]

        with patch.object(basic.AnsibleModule, 'run_command') as run_command:
            run_command.side_effect = commands_results
            with self.assertRaises(AnsibleExitJson) as result:
                iptables.main()
                self.assertTrue(result.exception.args[0]['changed'])

        self.assertEqual(run_command.call_count, 2)
        # import pdb
        # pdb.set_trace()
        self.assertEqual(run_command.call_args_list[0][0][0], [
            '/sbin/iptables',
            '-t',
            'filter',
            '-C',
            'OUTPUT',
            '-s',
            '1.2.3.4/32',
            '-d',
            '7.8.9.10/42',
            '-j',
            'ACCEPT'
        ])
        self.assertEqual(run_command.call_args_list[1][0][0], [
            '/sbin/iptables',
            '-t',
            'filter',
            '-I',
            'OUTPUT',
            '-s',
            '1.2.3.4/32',
            '-d',
            '7.8.9.10/42',
            '-j',
            'ACCEPT'
        ])

    def test_append_rule_check_mode(self):
        """Test append a redirection rule in check mode"""
        set_module_args({
            'chain': 'PREROUTING',
            'source': '1.2.3.4/32',
            'destination': '7.8.9.10/42',
            'jump': 'REDIRECT',
            'table': 'nat',
            'to_destination': '5.5.5.5/32',
            'protocol': 'udp',
            'destination_port': '22',
            'to_ports': '8600',
            '_ansible_check_mode': True,
        })

        commands_results = [
            (1, '', ''),
        ]

        with patch.object(basic.AnsibleModule, 'run_command') as run_command:
            run_command.side_effect = commands_results
            with self.assertRaises(AnsibleExitJson) as result:
                iptables.main()
                self.assertTrue(result.exception.args[0]['changed'])

        self.assertEqual(run_command.call_count, 1)
        self.assertEqual(run_command.call_args_list[0][0][0], [
            '/sbin/iptables',
            '-t',
            'nat',
            '-C',
            'PREROUTING',
            '-p',
            'udp',
            '-s',
            '1.2.3.4/32',
            '-d',
            '7.8.9.10/42',
            '-j',
            'REDIRECT',
            '--to-destination',
            '5.5.5.5/32',
            '--destination-port',
            '22',
            '--to-ports',
            '8600'
        ])

    def test_append_rule(self):
        """Test append a redirection rule"""
        set_module_args({
            'chain': 'PREROUTING',
            'source': '1.2.3.4/32',
            'destination': '7.8.9.10/42',
            'jump': 'REDIRECT',
            'table': 'nat',
            'to_destination': '5.5.5.5/32',
            'protocol': 'udp',
            'destination_port': '22',
            'to_ports': '8600'
        })

        commands_results = [
            (1, '', ''),
            (0, '', '')
        ]

        with patch.object(basic.AnsibleModule, 'run_command') as run_command:
            run_command.side_effect = commands_results
            with self.assertRaises(AnsibleExitJson) as result:
                iptables.main()
                self.assertTrue(result.exception.args[0]['changed'])

        self.assertEqual(run_command.call_count, 2)
        self.assertEqual(run_command.call_args_list[0][0][0], [
            '/sbin/iptables',
            '-t',
            'nat',
            '-C',
            'PREROUTING',
            '-p',
            'udp',
            '-s',
            '1.2.3.4/32',
            '-d',
            '7.8.9.10/42',
            '-j',
            'REDIRECT',
            '--to-destination',
            '5.5.5.5/32',
            '--destination-port',
            '22',
            '--to-ports',
            '8600'
        ])
        self.assertEqual(run_command.call_args_list[1][0][0], [
            '/sbin/iptables',
            '-t',
            'nat',
            '-A',
            'PREROUTING',
            '-p',
            'udp',
            '-s',
            '1.2.3.4/32',
            '-d',
            '7.8.9.10/42',
            '-j',
            'REDIRECT',
            '--to-destination',
            '5.5.5.5/32',
            '--destination-port',
            '22',
            '--to-ports',
            '8600'
        ])

    def test_remove_rule(self):
        """Test flush without parameters"""
        set_module_args({
            'chain': 'PREROUTING',
            'source': '1.2.3.4/32',
            'destination': '7.8.9.10/42',
            'jump': 'SNAT',
            'table': 'nat',
            'to_source': '5.5.5.5/32',
            'protocol': 'udp',
            'source_port': '22',
            'to_ports': '8600',
            'state': 'absent',
            'in_interface': 'eth0',
            'out_interface': 'eth1',
            'comment': 'this is a comment'
        })

        commands_results = [
            (0, '', ''),
            (0, '', ''),
        ]

        with patch.object(basic.AnsibleModule, 'run_command') as run_command:
            run_command.side_effect = commands_results
            with self.assertRaises(AnsibleExitJson) as result:
                iptables.main()
                self.assertTrue(result.exception.args[0]['changed'])

        self.assertEqual(run_command.call_count, 2)
        self.assertEqual(run_command.call_args_list[0][0][0], [
            '/sbin/iptables',
            '-t',
            'nat',
            '-C',
            'PREROUTING',
            '-p',
            'udp',
            '-s',
            '1.2.3.4/32',
            '-d',
            '7.8.9.10/42',
            '-j',
            'SNAT',
            '--to-source',
            '5.5.5.5/32',
            '-i',
            'eth0',
            '-o',
            'eth1',
            '--source-port',
            '22',
            '--to-ports',
            '8600',
            '-m',
            'comment',
            '--comment',
            'this is a comment'
        ])
        self.assertEqual(run_command.call_args_list[1][0][0], [
            '/sbin/iptables',
            '-t',
            'nat',
            '-D',
            'PREROUTING',
            '-p',
            'udp',
            '-s',
            '1.2.3.4/32',
            '-d',
            '7.8.9.10/42',
            '-j',
            'SNAT',
            '--to-source',
            '5.5.5.5/32',
            '-i',
            'eth0',
            '-o',
            'eth1',
            '--source-port',
            '22',
            '--to-ports',
            '8600',
            '-m',
            'comment',
            '--comment',
            'this is a comment'
        ])

    def test_remove_rule_check_mode(self):
        """Test flush without parameters check mode"""
        set_module_args({
            'chain': 'PREROUTING',
            'source': '1.2.3.4/32',
            'destination': '7.8.9.10/42',
            'jump': 'SNAT',
            'table': 'nat',
            'to_source': '5.5.5.5/32',
            'protocol': 'udp',
            'source_port': '22',
            'to_ports': '8600',
            'state': 'absent',
            'in_interface': 'eth0',
            'out_interface': 'eth1',
            'comment': 'this is a comment',
            '_ansible_check_mode': True,
        })

        commands_results = [
            (0, '', ''),
        ]

        with patch.object(basic.AnsibleModule, 'run_command') as run_command:
            run_command.side_effect = commands_results
            with self.assertRaises(AnsibleExitJson) as result:
                iptables.main()
                self.assertTrue(result.exception.args[0]['changed'])

        self.assertEqual(run_command.call_count, 1)
        self.assertEqual(run_command.call_args_list[0][0][0], [
            '/sbin/iptables',
            '-t',
            'nat',
            '-C',
            'PREROUTING',
            '-p',
            'udp',
            '-s',
            '1.2.3.4/32',
            '-d',
            '7.8.9.10/42',
            '-j',
            'SNAT',
            '--to-source',
            '5.5.5.5/32',
            '-i',
            'eth0',
            '-o',
            'eth1',
            '--source-port',
            '22',
            '--to-ports',
            '8600',
            '-m',
            'comment',
            '--comment',
            'this is a comment'
        ])

    def test_insert_with_reject(self):
        """ Using reject_with with a previously defined jump: REJECT results in two Jump statements #18988 """
        set_module_args({
            'chain': 'INPUT',
            'protocol': 'tcp',
            'reject_with': 'tcp-reset',
            'ip_version': 'ipv4',
        })
        commands_results = [
            (0, '', ''),
        ]

        with patch.object(basic.AnsibleModule, 'run_command') as run_command:
            run_command.side_effect = commands_results
            with self.assertRaises(AnsibleExitJson) as result:
                iptables.main()
                self.assertTrue(result.exception.args[0]['changed'])

        self.assertEqual(run_command.call_count, 1)
        self.assertEqual(run_command.call_args_list[0][0][0], [
            '/sbin/iptables',
            '-t',
            'filter',
            '-C',
            'INPUT',
            '-p',
            'tcp',
            '-j',
            'REJECT',
            '--reject-with',
            'tcp-reset',
        ])

    def test_insert_jump_reject_with_reject(self):
        """ Using reject_with with a previously defined jump: REJECT results in two Jump statements #18988 """
        set_module_args({
            'chain': 'INPUT',
            'protocol': 'tcp',
            'jump': 'REJECT',
            'reject_with': 'tcp-reset',
            'ip_version': 'ipv4',
        })
        commands_results = [
            (0, '', ''),
        ]

        with patch.object(basic.AnsibleModule, 'run_command') as run_command:
            run_command.side_effect = commands_results
            with self.assertRaises(AnsibleExitJson) as result:
                iptables.main()
                self.assertTrue(result.exception.args[0]['changed'])

        self.assertEqual(run_command.call_count, 1)
        self.assertEqual(run_command.call_args_list[0][0][0], [
            '/sbin/iptables',
            '-t',
            'filter',
            '-C',
            'INPUT',
            '-p',
            'tcp',
            '-j',
            'REJECT',
            '--reject-with',
            'tcp-reset',
        ])

    def test_jump_tee_gateway_negative(self):
        """ Missing gateway when JUMP is set to TEE """
        set_module_args({
            'table': 'mangle',
            'chain': 'PREROUTING',
            'in_interface': 'eth0',
            'protocol': 'udp',
            'match': 'state',
            'jump': 'TEE',
            'ctstate': ['NEW'],
            'destination_port': '9521',
            'destination': '127.0.0.1'
        })

        with self.assertRaises(AnsibleFailJson) as e:
            iptables.main()
        self.assertTrue(e.exception.args[0]['failed'])
        self.assertEqual(e.exception.args[0]['msg'], 'jump is TEE but all of the following are missing: gateway')

    def test_jump_tee_gateway(self):
        """ Using gateway when JUMP is set to TEE """
        set_module_args({
            'table': 'mangle',
            'chain': 'PREROUTING',
            'in_interface': 'eth0',
            'protocol': 'udp',
            'match': 'state',
            'jump': 'TEE',
            'ctstate': ['NEW'],
            'destination_port': '9521',
            'gateway': '192.168.10.1',
            'destination': '127.0.0.1'
        })
        commands_results = [
            (0, '', ''),
        ]

        with patch.object(basic.AnsibleModule, 'run_command') as run_command:
            run_command.side_effect = commands_results
            with self.assertRaises(AnsibleExitJson) as result:
                iptables.main()
                self.assertTrue(result.exception.args[0]['changed'])

        self.assertEqual(run_command.call_count, 1)
        self.assertEqual(run_command.call_args_list[0][0][0], [
            '/sbin/iptables',
            '-t', 'mangle',
            '-C', 'PREROUTING',
            '-p', 'udp',
            '-d', '127.0.0.1',
            '-m', 'state',
            '-j', 'TEE',
            '--gateway', '192.168.10.1',
            '-i', 'eth0',
            '--destination-port', '9521',
            '--state', 'NEW'
        ])

    def test_tcp_flags(self):
        """ Test various ways of inputting tcp_flags """
        args = [
            {
                'chain': 'OUTPUT',
                'protocol': 'tcp',
                'jump': 'DROP',
                'tcp_flags': 'flags=ALL flags_set="ACK,RST,SYN,FIN"'
            },
            {
                'chain': 'OUTPUT',
                'protocol': 'tcp',
                'jump': 'DROP',
                'tcp_flags': {
                    'flags': 'ALL',
                    'flags_set': 'ACK,RST,SYN,FIN'
                }
            },
            {
                'chain': 'OUTPUT',
                'protocol': 'tcp',
                'jump': 'DROP',
                'tcp_flags': {
                    'flags': ['ALL'],
                    'flags_set': ['ACK', 'RST', 'SYN', 'FIN']
                }
            },

        ]

        for item in args:
            set_module_args(item)

            commands_results = [
                (0, '', ''),
            ]

            with patch.object(basic.AnsibleModule, 'run_command') as run_command:
                run_command.side_effect = commands_results
                with self.assertRaises(AnsibleExitJson) as result:
                    iptables.main()
                    self.assertTrue(result.exception.args[0]['changed'])

            self.assertEqual(run_command.call_count, 1)
            self.assertEqual(run_command.call_args_list[0][0][0], [
                '/sbin/iptables',
                '-t',
                'filter',
                '-C',
                'OUTPUT',
                '-p',
                'tcp',
                '--tcp-flags',
                'ALL',
                'ACK,RST,SYN,FIN',
                '-j',
                'DROP'
            ])

    def test_log_level(self):
        """ Test various ways of log level flag """

        log_levels = ['0', '1', '2', '3', '4', '5', '6', '7',
                      'emerg', 'alert', 'crit', 'error', 'warning', 'notice', 'info', 'debug']

        for log_lvl in log_levels:
            set_module_args({
                'chain': 'INPUT',
                'jump': 'LOG',
                'log_level': log_lvl,
                'source': '1.2.3.4/32',
                'log_prefix': '** DROP-this_ip **'
            })
            commands_results = [
                (0, '', ''),
            ]

            with patch.object(basic.AnsibleModule, 'run_command') as run_command:
                run_command.side_effect = commands_results
                with self.assertRaises(AnsibleExitJson) as result:
                    iptables.main()
                    self.assertTrue(result.exception.args[0]['changed'])

                self.assertEqual(run_command.call_count, 1)
                self.assertEqual(run_command.call_args_list[0][0][0], [
                    '/sbin/iptables',
                    '-t', 'filter',
                    '-C', 'INPUT',
                    '-s', '1.2.3.4/32',
                    '-j', 'LOG',
                    '--log-prefix', '** DROP-this_ip **',
                    '--log-level', log_lvl
                ])

    def test_iprange(self):
        """ Test iprange module with its flags src_range and dst_range """
        set_module_args({
            'chain': 'INPUT',
            'match': ['iprange'],
            'src_range': '192.168.1.100-192.168.1.199',
            'jump': 'ACCEPT'
        })

        commands_results = [
            (0, '', ''),
        ]

        with patch.object(basic.AnsibleModule, 'run_command') as run_command:
            run_command.side_effect = commands_results
            with self.assertRaises(AnsibleExitJson) as result:
                iptables.main()
                self.assertTrue(result.exception.args[0]['changed'])

        self.assertEqual(run_command.call_count, 1)
        self.assertEqual(run_command.call_args_list[0][0][0], [
            '/sbin/iptables',
            '-t',
            'filter',
            '-C',
            'INPUT',
            '-m',
            'iprange',
            '-j',
            'ACCEPT',
            '--src-range',
            '192.168.1.100-192.168.1.199',
        ])

        set_module_args({
            'chain': 'INPUT',
            'src_range': '192.168.1.100-192.168.1.199',
            'dst_range': '10.0.0.50-10.0.0.100',
            'jump': 'ACCEPT'
        })

        commands_results = [
            (0, '', ''),
        ]

        with patch.object(basic.AnsibleModule, 'run_command') as run_command:
            run_command.side_effect = commands_results
            with self.assertRaises(AnsibleExitJson) as result:
                iptables.main()
                self.assertTrue(result.exception.args[0]['changed'])

        self.assertEqual(run_command.call_count, 1)
        self.assertEqual(run_command.call_args_list[0][0][0], [
            '/sbin/iptables',
            '-t',
            'filter',
            '-C',
            'INPUT',
            '-j',
            'ACCEPT',
            '-m',
            'iprange',
            '--src-range',
            '192.168.1.100-192.168.1.199',
            '--dst-range',
            '10.0.0.50-10.0.0.100'
        ])

        set_module_args({
            'chain': 'INPUT',
            'dst_range': '10.0.0.50-10.0.0.100',
            'jump': 'ACCEPT'
        })

        commands_results = [
            (0, '', ''),
        ]

        with patch.object(basic.AnsibleModule, 'run_command') as run_command:
            run_command.side_effect = commands_results
            with self.assertRaises(AnsibleExitJson) as result:
                iptables.main()
                self.assertTrue(result.exception.args[0]['changed'])

        self.assertEqual(run_command.call_count, 1)
        self.assertEqual(run_command.call_args_list[0][0][0], [
            '/sbin/iptables',
            '-t',
            'filter',
            '-C',
            'INPUT',
            '-j',
            'ACCEPT',
            '-m',
            'iprange',
            '--dst-range',
            '10.0.0.50-10.0.0.100'
        ])

    def test_insert_rule_with_wait(self):
        """Test flush without parameters"""
        set_module_args({
            'chain': 'OUTPUT',
            'source': '1.2.3.4/32',
            'destination': '7.8.9.10/42',
            'jump': 'ACCEPT',
            'action': 'insert',
            'wait': '10'
        })

        commands_results = [
            (0, '', ''),
        ]

        with patch.object(basic.AnsibleModule, 'run_command') as run_command:
            run_command.side_effect = commands_results
            with self.assertRaises(AnsibleExitJson) as result:
                iptables.main()
                self.assertTrue(result.exception.args[0]['changed'])

        self.assertEqual(run_command.call_count, 1)
        self.assertEqual(run_command.call_args_list[0][0][0], [
            '/sbin/iptables',
            '-t',
            'filter',
            '-C',
            'OUTPUT',
            '-w',
            '10',
            '-s',
            '1.2.3.4/32',
            '-d',
            '7.8.9.10/42',
            '-j',
            'ACCEPT'
        ])

    def test_comment_position_at_end(self):
        """Test flush without parameters"""
        set_module_args({
            'chain': 'INPUT',
            'jump': 'ACCEPT',
            'action': 'insert',
            'ctstate': ['NEW'],
            'comment': 'this is a comment',
            '_ansible_check_mode': True,
        })

        commands_results = [
            (0, '', ''),
        ]

        with patch.object(basic.AnsibleModule, 'run_command') as run_command:
            run_command.side_effect = commands_results
            with self.assertRaises(AnsibleExitJson) as result:
                iptables.main()
                self.assertTrue(result.exception.args[0]['changed'])

        self.assertEqual(run_command.call_count, 1)
        self.assertEqual(run_command.call_args_list[0][0][0], [
            '/sbin/iptables',
            '-t',
            'filter',
            '-C',
            'INPUT',
            '-j',
            'ACCEPT',
            '-m',
            'conntrack',
            '--ctstate',
            'NEW',
            '-m',
            'comment',
            '--comment',
            'this is a comment'
        ])
        self.assertEqual(run_command.call_args[0][0][14], 'this is a comment')
