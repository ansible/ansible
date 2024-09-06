# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import annotations

from units.modules.utils import AnsibleExitJson, AnsibleFailJson, set_module_args, fail_json, exit_json
import pytest

from ansible.modules import iptables

IPTABLES_CMD = "/sbin/iptables"
IPTABLES_VERSION = "1.8.2"
CONST_INPUT_FILTER = [IPTABLES_CMD, "-t", "filter", "-L", "INPUT",]


@pytest.fixture
def _mock_basic_commands(mocker):
    """Mock basic commands like get_bin_path and get_iptables_version."""
    mocker.patch(
        "ansible.module_utils.basic.AnsibleModule.get_bin_path",
        return_value=IPTABLES_CMD,
    )
    mocker.patch("ansible.modules.iptables.get_iptables_version", return_value=IPTABLES_VERSION)


@pytest.mark.usefixtures('_mock_basic_commands')
def test_flush_table_without_chain(mocker):
    """Test flush without chain, flush the table."""
    set_module_args(
        {
            "flush": True,
        }
    )
    run_command = mocker.patch(
        "ansible.module_utils.basic.AnsibleModule.run_command", return_value=(0, "", "")
    )
    with pytest.raises(SystemExit):
        iptables.main()

    assert run_command.call_count == 1
    first_cmd_args_list = run_command.call_args[0][0]
    assert first_cmd_args_list[0], IPTABLES_CMD
    assert first_cmd_args_list[1], "-t"
    assert first_cmd_args_list[2], "filter"
    assert first_cmd_args_list[3], "-F"


@pytest.mark.usefixtures('_mock_basic_commands')
def test_flush_table_check_true(mocker):
    """Test flush without parameters and check == true."""
    set_module_args(
        {
            "flush": True,
            "_ansible_check_mode": True,
        }
    )
    run_command = mocker.patch(
        "ansible.module_utils.basic.AnsibleModule.run_command", return_value=(0, "", "")
    )
    with pytest.raises(SystemExit):
        iptables.main()

    assert run_command.call_count == 0


@pytest.mark.usefixtures('_mock_basic_commands')
def test_policy_table(mocker):
    """Test change policy of a chain."""
    set_module_args(
        {
            "policy": "ACCEPT",
            "chain": "INPUT",
        }
    )
    commands_results = [(0, "Chain INPUT (policy DROP)\n", ""), (0, "", "")]
    run_command = mocker.patch(
        "ansible.module_utils.basic.AnsibleModule.run_command",
        side_effect=commands_results,
    )
    with pytest.raises(SystemExit):
        iptables.main()

    assert run_command.call_count == 2
    first_cmd_args_list = run_command.call_args_list[0]
    second_cmd_args_list = run_command.call_args_list[1]
    assert first_cmd_args_list[0][0] == CONST_INPUT_FILTER
    assert second_cmd_args_list[0][0] == [
        IPTABLES_CMD,
        "-t",
        "filter",
        "-P",
        "INPUT",
        "ACCEPT",
    ]


@pytest.mark.usefixtures('_mock_basic_commands')
@pytest.mark.parametrize(
    ("test_input", "commands_results"),
    [
        pytest.param(
            {
                "policy": "ACCEPT",
                "chain": "INPUT",
                "_ansible_check_mode": True,
            },
            [
                (0, "Chain INPUT (policy DROP)\n", ""),
            ],
            id="policy-table-no-change",
        ),
        pytest.param(
            {
                "policy": "ACCEPT",
                "chain": "INPUT",
            },
            [
                (0, "Chain INPUT (policy ACCEPT)\n", ""),
                (0, "", ""),
            ],
            id="policy-table-change-false",
        )
    ]
)
def test_policy_table_flush(mocker, test_input, commands_results):
    """Test flush without parameters and change == false."""
    set_module_args(test_input)
    run_command = mocker.patch(
        "ansible.module_utils.basic.AnsibleModule.run_command",
        side_effect=commands_results,
    )
    with pytest.raises(SystemExit):
        iptables.main()

    assert run_command.call_count == 1
    first_cmd_args_list = run_command.call_args_list[0]
    assert first_cmd_args_list[0][0] == CONST_INPUT_FILTER


# TODO ADD test policy without chain fail
# TODO ADD test policy with chain don't exists
# TODO ADD test policy with wrong choice fail

@pytest.mark.usefixtures('_mock_basic_commands')
def test_insert_rule_change_false(mocker):
    """Test flush without parameters."""
    set_module_args(
        {
            "chain": "OUTPUT",
            "source": "1.2.3.4/32",
            "destination": "7.8.9.10/42",
            "jump": "ACCEPT",
            "action": "insert",
            "_ansible_check_mode": True,
        }
    )
    commands_results = [
        (1, "", ""),  # check_rule_present
        (0, "", ""),  # check_chain_present
    ]
    run_command = mocker.patch(
        "ansible.module_utils.basic.AnsibleModule.run_command",
        side_effect=commands_results,
    )

    with pytest.raises(SystemExit):
        iptables.main()

    assert run_command.call_count == 1
    first_cmd_args_list = run_command.call_args_list[0]
    assert first_cmd_args_list[0][0] == [
        IPTABLES_CMD,
        "-t",
        "filter",
        "-C",
        "OUTPUT",
        "-s",
        "1.2.3.4/32",
        "-d",
        "7.8.9.10/42",
        "-j",
        "ACCEPT",
    ]


@pytest.mark.usefixtures('_mock_basic_commands')
def test_insert_rule(mocker):
    """Test flush without parameters."""
    set_module_args(
        {
            "chain": "OUTPUT",
            "source": "1.2.3.4/32",
            "destination": "7.8.9.10/42",
            "jump": "ACCEPT",
            "action": "insert",
        }
    )
    commands_results = [
        (1, "", ""),  # check_rule_present
        (0, "", ""),
    ]
    run_command = mocker.patch(
        "ansible.module_utils.basic.AnsibleModule.run_command",
        side_effect=commands_results,
    )

    with pytest.raises(SystemExit):
        iptables.main()

    assert run_command.call_count == 2
    first_cmd_args_list = run_command.call_args_list[0]
    second_cmd_args_list = run_command.call_args_list[1]
    assert first_cmd_args_list[0][0] == [
        IPTABLES_CMD,
        "-t",
        "filter",
        "-C",
        "OUTPUT",
        "-s",
        "1.2.3.4/32",
        "-d",
        "7.8.9.10/42",
        "-j",
        "ACCEPT",
    ]
    assert second_cmd_args_list[0][0] == [
        IPTABLES_CMD,
        "-t",
        "filter",
        "-I",
        "OUTPUT",
        "-s",
        "1.2.3.4/32",
        "-d",
        "7.8.9.10/42",
        "-j",
        "ACCEPT",
    ]


@pytest.mark.usefixtures('_mock_basic_commands')
def test_append_rule_check_mode(mocker):
    """Test append a redirection rule in check mode."""
    set_module_args(
        {
            "chain": "PREROUTING",
            "source": "1.2.3.4/32",
            "destination": "7.8.9.10/42",
            "jump": "REDIRECT",
            "table": "nat",
            "to_destination": "5.5.5.5/32",
            "protocol": "udp",
            "destination_port": "22",
            "to_ports": "8600",
            "_ansible_check_mode": True,
        }
    )

    commands_results = [
        (1, "", ""),  # check_rule_present
        (0, "", ""),  # check_chain_present
    ]
    run_command = mocker.patch(
        "ansible.module_utils.basic.AnsibleModule.run_command",
        side_effect=commands_results,
    )

    with pytest.raises(SystemExit):
        iptables.main()

    assert run_command.call_count == 1
    first_cmd_args_list = run_command.call_args_list[0]
    assert first_cmd_args_list[0][0] == [
        IPTABLES_CMD,
        "-t",
        "nat",
        "-C",
        "PREROUTING",
        "-p",
        "udp",
        "-s",
        "1.2.3.4/32",
        "-d",
        "7.8.9.10/42",
        "-j",
        "REDIRECT",
        "--to-destination",
        "5.5.5.5/32",
        "--destination-port",
        "22",
        "--to-ports",
        "8600",
    ]


@pytest.mark.usefixtures('_mock_basic_commands')
def test_append_rule(mocker):
    """Test append a redirection rule."""
    set_module_args(
        {
            "chain": "PREROUTING",
            "source": "1.2.3.4/32",
            "destination": "7.8.9.10/42",
            "jump": "REDIRECT",
            "table": "nat",
            "to_destination": "5.5.5.5/32",
            "protocol": "udp",
            "destination_port": "22",
            "to_ports": "8600",
        }
    )

    commands_results = [
        (1, "", ""),  # check_rule_present
        (0, "", ""),  # check_chain_present
        (0, "", ""),
    ]
    run_command = mocker.patch(
        "ansible.module_utils.basic.AnsibleModule.run_command",
        side_effect=commands_results,
    )

    with pytest.raises(SystemExit):
        iptables.main()

    assert run_command.call_count == 2
    first_cmd_args_list = run_command.call_args_list[0]
    second_cmd_args_list = run_command.call_args_list[1]
    assert first_cmd_args_list[0][0] == [
        IPTABLES_CMD,
        "-t",
        "nat",
        "-C",
        "PREROUTING",
        "-p",
        "udp",
        "-s",
        "1.2.3.4/32",
        "-d",
        "7.8.9.10/42",
        "-j",
        "REDIRECT",
        "--to-destination",
        "5.5.5.5/32",
        "--destination-port",
        "22",
        "--to-ports",
        "8600",
    ]
    assert second_cmd_args_list[0][0] == [
        IPTABLES_CMD,
        "-t",
        "nat",
        "-A",
        "PREROUTING",
        "-p",
        "udp",
        "-s",
        "1.2.3.4/32",
        "-d",
        "7.8.9.10/42",
        "-j",
        "REDIRECT",
        "--to-destination",
        "5.5.5.5/32",
        "--destination-port",
        "22",
        "--to-ports",
        "8600",
    ]


@pytest.mark.usefixtures('_mock_basic_commands')
def test_remove_rule(mocker):
    """Test flush without parameters."""
    set_module_args(
        {
            "chain": "PREROUTING",
            "source": "1.2.3.4/32",
            "destination": "7.8.9.10/42",
            "jump": "SNAT",
            "table": "nat",
            "to_source": "5.5.5.5/32",
            "protocol": "udp",
            "source_port": "22",
            "to_ports": "8600",
            "state": "absent",
            "in_interface": "eth0",
            "out_interface": "eth1",
            "comment": "this is a comment",
        }
    )

    commands_results = [
        (0, "", ""),
        (0, "", ""),
    ]
    run_command = mocker.patch(
        "ansible.module_utils.basic.AnsibleModule.run_command",
        side_effect=commands_results,
    )

    with pytest.raises(SystemExit):
        iptables.main()

    assert run_command.call_count == 2
    first_cmd_args_list = run_command.call_args_list[0]
    second_cmd_args_list = run_command.call_args_list[1]
    assert first_cmd_args_list[0][0] == [
        IPTABLES_CMD,
        "-t",
        "nat",
        "-C",
        "PREROUTING",
        "-p",
        "udp",
        "-s",
        "1.2.3.4/32",
        "-d",
        "7.8.9.10/42",
        "-j",
        "SNAT",
        "--to-source",
        "5.5.5.5/32",
        "-i",
        "eth0",
        "-o",
        "eth1",
        "--source-port",
        "22",
        "--to-ports",
        "8600",
        "-m",
        "comment",
        "--comment",
        "this is a comment",
    ]
    assert second_cmd_args_list[0][0] == [
        IPTABLES_CMD,
        "-t",
        "nat",
        "-D",
        "PREROUTING",
        "-p",
        "udp",
        "-s",
        "1.2.3.4/32",
        "-d",
        "7.8.9.10/42",
        "-j",
        "SNAT",
        "--to-source",
        "5.5.5.5/32",
        "-i",
        "eth0",
        "-o",
        "eth1",
        "--source-port",
        "22",
        "--to-ports",
        "8600",
        "-m",
        "comment",
        "--comment",
        "this is a comment",
    ]


@pytest.mark.usefixtures('_mock_basic_commands')
def test_remove_rule_check_mode(mocker):
    """Test flush without parameters check mode."""
    set_module_args(
        {
            "chain": "PREROUTING",
            "source": "1.2.3.4/32",
            "destination": "7.8.9.10/42",
            "jump": "SNAT",
            "table": "nat",
            "to_source": "5.5.5.5/32",
            "protocol": "udp",
            "source_port": "22",
            "to_ports": "8600",
            "state": "absent",
            "in_interface": "eth0",
            "out_interface": "eth1",
            "comment": "this is a comment",
            "_ansible_check_mode": True,
        }
    )

    commands_results = [
        (0, "", ""),
    ]

    run_command = mocker.patch(
        "ansible.module_utils.basic.AnsibleModule.run_command",
        side_effect=commands_results,
    )

    with pytest.raises(SystemExit):
        iptables.main()

    assert run_command.call_count == 1
    first_cmd_args_list = run_command.call_args_list[0]
    assert first_cmd_args_list[0][0] == [
        IPTABLES_CMD,
        "-t",
        "nat",
        "-C",
        "PREROUTING",
        "-p",
        "udp",
        "-s",
        "1.2.3.4/32",
        "-d",
        "7.8.9.10/42",
        "-j",
        "SNAT",
        "--to-source",
        "5.5.5.5/32",
        "-i",
        "eth0",
        "-o",
        "eth1",
        "--source-port",
        "22",
        "--to-ports",
        "8600",
        "-m",
        "comment",
        "--comment",
        "this is a comment",
    ]


@pytest.mark.usefixtures('_mock_basic_commands')
@pytest.mark.parametrize(
    ("test_input", "expected"),
    [
        pytest.param(
            {
                "chain": "INPUT",
                "protocol": "tcp",
                "reject_with": "tcp-reset",
                "ip_version": "ipv4",
            },
            [
                IPTABLES_CMD,
                "-t",
                "filter",
                "-C",
                "INPUT",
                "-p",
                "tcp",
                "-j",
                "REJECT",
                "--reject-with",
                "tcp-reset",
            ],
            id="insert-reject-with",
        ),
        pytest.param(
            {
                "chain": "INPUT",
                "protocol": "tcp",
                "jump": "REJECT",
                "reject_with": "tcp-reset",
                "ip_version": "ipv4",
            },
            [
                IPTABLES_CMD,
                "-t",
                "filter",
                "-C",
                "INPUT",
                "-p",
                "tcp",
                "-j",
                "REJECT",
                "--reject-with",
                "tcp-reset",
            ],
            id="update-reject-with",
        ),
    ]
)
def test_insert_with_reject(mocker, test_input, expected):
    """Using reject_with with a previously defined jump: REJECT results in two Jump statements #18988."""
    set_module_args(test_input)
    commands_results = [
        (0, "", ""),
    ]

    run_command = mocker.patch(
        "ansible.module_utils.basic.AnsibleModule.run_command",
        side_effect=commands_results,
    )

    with pytest.raises(SystemExit):
        iptables.main()

    assert run_command.call_count == 1
    first_cmd_args_list = run_command.call_args_list[0]
    assert first_cmd_args_list[0][0] == expected


@pytest.mark.usefixtures('_mock_basic_commands')
def test_jump_tee_gateway_negative(mocker):
    """Missing gateway when JUMP is set to TEE."""
    set_module_args(
        {
            "table": "mangle",
            "chain": "PREROUTING",
            "in_interface": "eth0",
            "protocol": "udp",
            "match": "state",
            "jump": "TEE",
            "ctstate": ["NEW"],
            "destination_port": "9521",
            "destination": "127.0.0.1",
        }
    )
    mocker.patch(
        "ansible.module_utils.basic.AnsibleModule.fail_json",
        side_effect=fail_json,
    )
    jump_err_msg = "jump is TEE but all of the following are missing: gateway"
    with pytest.raises(AnsibleFailJson, match=jump_err_msg) as exc:
        iptables.main()
    assert exc.value.args[0]["failed"]


@pytest.mark.usefixtures('_mock_basic_commands')
def test_jump_tee_gateway(mocker):
    """Using gateway when JUMP is set to TEE."""
    set_module_args(
        {
            "table": "mangle",
            "chain": "PREROUTING",
            "in_interface": "eth0",
            "protocol": "udp",
            "match": "state",
            "jump": "TEE",
            "ctstate": ["NEW"],
            "destination_port": "9521",
            "gateway": "192.168.10.1",
            "destination": "127.0.0.1",
        }
    )
    commands_results = [
        (0, "", ""),
    ]
    run_command = mocker.patch(
        "ansible.module_utils.basic.AnsibleModule.run_command",
        side_effect=commands_results,
    )

    with pytest.raises(SystemExit):
        iptables.main()

    assert run_command.call_count == 1
    first_cmd_args_list = run_command.call_args_list[0]
    assert first_cmd_args_list[0][0] == [
        IPTABLES_CMD,
        "-t",
        "mangle",
        "-C",
        "PREROUTING",
        "-p",
        "udp",
        "-d",
        "127.0.0.1",
        "-m",
        "state",
        "-j",
        "TEE",
        "--gateway",
        "192.168.10.1",
        "-i",
        "eth0",
        "--destination-port",
        "9521",
        "--state",
        "NEW",
    ]


@pytest.mark.usefixtures('_mock_basic_commands')
@pytest.mark.parametrize(
    ("test_input"),
    [
        pytest.param(
            'flags=ALL flags_set="ACK,RST,SYN,FIN"',
            id="tcp-flags-str"
        ),
        pytest.param(
            {
                "flags": "ALL", "flags_set": "ACK,RST,SYN,FIN"
            },
            id="tcp-flags-dict"
        ),
        pytest.param(
            {
                "flags": ["ALL"], "flags_set": ["ACK", "RST", "SYN", "FIN"]
            },
            id="tcp-flags-list"
        ),
    ],
)
def test_tcp_flags(mocker, test_input):
    """Test various ways of inputting tcp_flags."""
    rule_data = {
        "chain": "OUTPUT",
        "protocol": "tcp",
        "jump": "DROP",
        "tcp_flags": test_input,
    }

    set_module_args(rule_data)

    commands_results = [
        (0, "", ""),
    ]

    run_command = mocker.patch(
        "ansible.module_utils.basic.AnsibleModule.run_command",
        side_effect=commands_results,
    )

    with pytest.raises(SystemExit):
        iptables.main()

    assert run_command.call_count == 1
    first_cmd_args_list = run_command.call_args_list[0]
    assert first_cmd_args_list[0][0] == [
        IPTABLES_CMD,
        "-t",
        "filter",
        "-C",
        "OUTPUT",
        "-p",
        "tcp",
        "--tcp-flags",
        "ALL",
        "ACK,RST,SYN,FIN",
        "-j",
        "DROP",
    ]


@pytest.mark.usefixtures('_mock_basic_commands')
@pytest.mark.parametrize(
    "log_level",
    [
        "0",
        "1",
        "2",
        "3",
        "4",
        "5",
        "6",
        "7",
        "emerg",
        "alert",
        "crit",
        "error",
        "warning",
        "notice",
        "info",
        "debug",
    ],
)
def test_log_level(mocker, log_level):
    """Test various ways of log level flag."""

    set_module_args(
        {
            "chain": "INPUT",
            "jump": "LOG",
            "log_level": log_level,
            "source": "1.2.3.4/32",
            "log_prefix": "** DROP-this_ip **",
        }
    )
    commands_results = [
        (0, "", ""),
    ]

    run_command = mocker.patch(
        "ansible.module_utils.basic.AnsibleModule.run_command",
        side_effect=commands_results,
    )

    with pytest.raises(SystemExit):
        iptables.main()

    assert run_command.call_count == 1
    first_cmd_args_list = run_command.call_args_list[0]
    assert first_cmd_args_list[0][0] == [
        IPTABLES_CMD,
        "-t",
        "filter",
        "-C",
        "INPUT",
        "-s",
        "1.2.3.4/32",
        "-j",
        "LOG",
        "--log-prefix",
        "** DROP-this_ip **",
        "--log-level",
        log_level,
    ]


@pytest.mark.usefixtures('_mock_basic_commands')
@pytest.mark.parametrize(
    ("test_input", "expected"),
    [
        pytest.param(
            {
                "chain": "INPUT",
                "match": ["iprange"],
                "src_range": "192.168.1.100-192.168.1.199",
                "jump": "ACCEPT",
            },
            [
                IPTABLES_CMD,
                "-t",
                "filter",
                "-C",
                "INPUT",
                "-m",
                "iprange",
                "-j",
                "ACCEPT",
                "--src-range",
                "192.168.1.100-192.168.1.199",
            ],
            id="src-range",
        ),
        pytest.param(
            {
                "chain": "INPUT",
                "src_range": "192.168.1.100-192.168.1.199",
                "dst_range": "10.0.0.50-10.0.0.100",
                "jump": "ACCEPT",
            },
            [
                IPTABLES_CMD,
                "-t",
                "filter",
                "-C",
                "INPUT",
                "-j",
                "ACCEPT",
                "-m",
                "iprange",
                "--src-range",
                "192.168.1.100-192.168.1.199",
                "--dst-range",
                "10.0.0.50-10.0.0.100",
            ],
            id="src-range-dst-range",
        ),
        pytest.param(
            {
                "chain": "INPUT",
                "dst_range": "10.0.0.50-10.0.0.100",
                "jump": "ACCEPT"
            },
            [
                IPTABLES_CMD,
                "-t",
                "filter",
                "-C",
                "INPUT",
                "-j",
                "ACCEPT",
                "-m",
                "iprange",
                "--dst-range",
                "10.0.0.50-10.0.0.100",
            ],
            id="dst-range"
        ),
    ],
)
def test_iprange(mocker, test_input, expected):
    """Test iprange module with its flags src_range and dst_range."""
    set_module_args(test_input)

    commands_results = [
        (0, "", ""),
    ]

    run_command = mocker.patch(
        "ansible.module_utils.basic.AnsibleModule.run_command",
        side_effect=commands_results,
    )

    with pytest.raises(SystemExit):
        iptables.main()

    assert run_command.call_count == 1
    first_cmd_args_list = run_command.call_args_list[0]
    assert first_cmd_args_list[0][0] == expected


@pytest.mark.usefixtures('_mock_basic_commands')
def test_insert_rule_with_wait(mocker):
    """Test flush without parameters."""
    set_module_args(
        {
            "chain": "OUTPUT",
            "source": "1.2.3.4/32",
            "destination": "7.8.9.10/42",
            "jump": "ACCEPT",
            "action": "insert",
            "wait": "10",
        }
    )

    commands_results = [
        (0, "", ""),
    ]

    run_command = mocker.patch(
        "ansible.module_utils.basic.AnsibleModule.run_command",
        side_effect=commands_results,
    )

    with pytest.raises(SystemExit):
        iptables.main()

    assert run_command.call_count == 1
    first_cmd_args_list = run_command.call_args_list[0]
    assert first_cmd_args_list[0][0] == [
        IPTABLES_CMD,
        "-t",
        "filter",
        "-C",
        "OUTPUT",
        "-w",
        "10",
        "-s",
        "1.2.3.4/32",
        "-d",
        "7.8.9.10/42",
        "-j",
        "ACCEPT",
    ]


@pytest.mark.usefixtures('_mock_basic_commands')
def test_comment_position_at_end(mocker):
    """Test comment position to make sure it is at the end of command."""
    set_module_args(
        {
            "chain": "INPUT",
            "jump": "ACCEPT",
            "action": "insert",
            "ctstate": ["NEW"],
            "comment": "this is a comment",
            "_ansible_check_mode": True,
        }
    )

    commands_results = [
        (0, "", ""),
    ]

    run_command = mocker.patch(
        "ansible.module_utils.basic.AnsibleModule.run_command",
        side_effect=commands_results,
    )

    with pytest.raises(SystemExit):
        iptables.main()

    assert run_command.call_count == 1
    first_cmd_args_list = run_command.call_args_list[0]
    assert first_cmd_args_list[0][0] == [
        IPTABLES_CMD,
        "-t",
        "filter",
        "-C",
        "INPUT",
        "-j",
        "ACCEPT",
        "-m",
        "conntrack",
        "--ctstate",
        "NEW",
        "-m",
        "comment",
        "--comment",
        "this is a comment",
    ]
    assert run_command.call_args[0][0][14] == "this is a comment"


@pytest.mark.usefixtures('_mock_basic_commands')
def test_destination_ports(mocker):
    """Test multiport module usage with multiple ports."""
    set_module_args(
        {
            "chain": "INPUT",
            "protocol": "tcp",
            "in_interface": "eth0",
            "source": "192.168.0.1/32",
            "destination_ports": ["80", "443", "8081:8085"],
            "jump": "ACCEPT",
            "comment": "this is a comment",
        }
    )
    commands_results = [
        (0, "", ""),
    ]
    run_command = mocker.patch(
        "ansible.module_utils.basic.AnsibleModule.run_command",
        side_effect=commands_results,
    )

    with pytest.raises(SystemExit):
        iptables.main()

    assert run_command.call_count == 1
    first_cmd_args_list = run_command.call_args_list[0]
    assert first_cmd_args_list[0][0] == [
        IPTABLES_CMD,
        "-t",
        "filter",
        "-C",
        "INPUT",
        "-p",
        "tcp",
        "-s",
        "192.168.0.1/32",
        "-j",
        "ACCEPT",
        "-m",
        "multiport",
        "--dports",
        "80,443,8081:8085",
        "-i",
        "eth0",
        "-m",
        "comment",
        "--comment",
        "this is a comment",
    ]


@pytest.mark.usefixtures('_mock_basic_commands')
@pytest.mark.parametrize(
    ("test_input", "expected"),
    [
        pytest.param(
            {
                "chain": "INPUT",
                "protocol": "tcp",
                "match_set": "admin_hosts",
                "match_set_flags": "src",
                "destination_port": "22",
                "jump": "ACCEPT",
                "comment": "this is a comment",
            },
            [
                IPTABLES_CMD,
                "-t",
                "filter",
                "-C",
                "INPUT",
                "-p",
                "tcp",
                "-j",
                "ACCEPT",
                "--destination-port",
                "22",
                "-m",
                "set",
                "--match-set",
                "admin_hosts",
                "src",
                "-m",
                "comment",
                "--comment",
                "this is a comment",
            ],
            id="match-set-src",
        ),
        pytest.param(
            {
                "chain": "INPUT",
                "protocol": "udp",
                "match_set": "banned_hosts",
                "match_set_flags": "src,dst",
                "jump": "REJECT",
            },
            [
                IPTABLES_CMD,
                "-t",
                "filter",
                "-C",
                "INPUT",
                "-p",
                "udp",
                "-j",
                "REJECT",
                "-m",
                "set",
                "--match-set",
                "banned_hosts",
                "src,dst",
            ],
            id="match-set-src-dst",
        ),
        pytest.param(
            {
                "chain": "INPUT",
                "protocol": "udp",
                "match_set": "banned_hosts_dst",
                "match_set_flags": "dst,dst",
                "jump": "REJECT",
            },
            [
                IPTABLES_CMD,
                "-t",
                "filter",
                "-C",
                "INPUT",
                "-p",
                "udp",
                "-j",
                "REJECT",
                "-m",
                "set",
                "--match-set",
                "banned_hosts_dst",
                "dst,dst",
            ],
            id="match-set-dst-dst",
        ),
        pytest.param(
            {
                "chain": "INPUT",
                "protocol": "udp",
                "match_set": "banned_hosts",
                "match_set_flags": "src,src",
                "jump": "REJECT",
            },
            [
                IPTABLES_CMD,
                "-t",
                "filter",
                "-C",
                "INPUT",
                "-p",
                "udp",
                "-j",
                "REJECT",
                "-m",
                "set",
                "--match-set",
                "banned_hosts",
                "src,src",
            ],
            id="match-set-src-src",
        ),
    ],
)
def test_match_set(mocker, test_input, expected):
    """Test match_set together with match_set_flags."""
    set_module_args(test_input)
    commands_results = [
        (0, "", ""),
    ]
    run_command = mocker.patch(
        "ansible.module_utils.basic.AnsibleModule.run_command",
        side_effect=commands_results,
    )

    with pytest.raises(SystemExit):
        iptables.main()

    assert run_command.call_count == 1
    first_cmd_args_list = run_command.call_args_list[0]
    assert first_cmd_args_list[0][0] == expected


@pytest.mark.usefixtures('_mock_basic_commands')
def test_chain_creation(mocker):
    """Test chain creation when absent."""
    set_module_args(
        {
            "chain": "FOOBAR",
            "state": "present",
            "chain_management": True,
        }
    )

    commands_results = [
        (1, "", ""),  # check_chain_present
        (0, "", ""),  # create_chain
    ]

    run_command = mocker.patch(
        "ansible.module_utils.basic.AnsibleModule.run_command",
        side_effect=commands_results,
    )

    mocker.patch(
        "ansible.module_utils.basic.AnsibleModule.exit_json",
        side_effect=exit_json,
    )
    with pytest.raises(AnsibleExitJson):
        iptables.main()

    assert run_command.call_count == 2
    first_cmd_args_list = run_command.call_args_list[0]
    assert first_cmd_args_list[0][0] == [
        IPTABLES_CMD,
        "-t",
        "filter",
        "-L",
        "FOOBAR",
    ]

    second_cmd_args_list = run_command.call_args_list[1]
    assert second_cmd_args_list[0][0] == [
        IPTABLES_CMD,
        "-t",
        "filter",
        "-N",
        "FOOBAR",
    ]

    commands_results = [
        (0, "", ""),  # check_rule_present
    ]

    run_command = mocker.patch(
        "ansible.module_utils.basic.AnsibleModule.run_command",
        side_effect=commands_results,
    )

    with pytest.raises(AnsibleExitJson) as exc:
        iptables.main()
    assert not exc.value.args[0]["changed"]


@pytest.mark.usefixtures('_mock_basic_commands')
def test_chain_creation_check_mode(mocker):
    """Test chain creation when absent in check mode."""
    set_module_args(
        {
            "chain": "FOOBAR",
            "state": "present",
            "chain_management": True,
            "_ansible_check_mode": True,
        }
    )

    commands_results = [
        (1, "", ""),  # check_rule_present
    ]

    run_command = mocker.patch(
        "ansible.module_utils.basic.AnsibleModule.run_command",
        side_effect=commands_results,
    )

    mocker.patch(
        "ansible.module_utils.basic.AnsibleModule.exit_json",
        side_effect=exit_json,
    )
    with pytest.raises(AnsibleExitJson):
        iptables.main()

    assert run_command.call_count == 1
    first_cmd_args_list = run_command.call_args_list[0]
    assert first_cmd_args_list[0][0] == [
        IPTABLES_CMD,
        "-t",
        "filter",
        "-L",
        "FOOBAR",
    ]

    commands_results = [
        (0, "", ""),  # check_rule_present
    ]
    run_command = mocker.patch(
        "ansible.module_utils.basic.AnsibleModule.run_command",
        side_effect=commands_results,
    )
    with pytest.raises(AnsibleExitJson) as exc:
        iptables.main()

    assert not exc.value.args[0]["changed"]


@pytest.mark.usefixtures('_mock_basic_commands')
def test_chain_deletion(mocker):
    """Test chain deletion when present."""
    set_module_args(
        {
            "chain": "FOOBAR",
            "state": "absent",
            "chain_management": True,
        }
    )

    commands_results = [
        (0, "", ""),  # check_chain_present
        (0, "", ""),  # delete_chain
    ]

    run_command = mocker.patch(
        "ansible.module_utils.basic.AnsibleModule.run_command",
        side_effect=commands_results,
    )

    mocker.patch(
        "ansible.module_utils.basic.AnsibleModule.exit_json",
        side_effect=exit_json,
    )
    with pytest.raises(AnsibleExitJson) as exc:
        iptables.main()

    assert exc.value.args[0]["changed"]
    assert run_command.call_count == 2
    first_cmd_args_list = run_command.call_args_list[0]
    assert first_cmd_args_list[0][0] == [
        IPTABLES_CMD,
        "-t",
        "filter",
        "-L",
        "FOOBAR",
    ]
    second_cmd_args_list = run_command.call_args_list[1]
    assert second_cmd_args_list[0][0] == [
        IPTABLES_CMD,
        "-t",
        "filter",
        "-X",
        "FOOBAR",
    ]

    commands_results = [
        (1, "", ""),  # check_rule_present
    ]

    run_command = mocker.patch(
        "ansible.module_utils.basic.AnsibleModule.run_command",
        side_effect=commands_results,
    )

    with pytest.raises(AnsibleExitJson) as exc:
        iptables.main()

    assert not exc.value.args[0]["changed"]


@pytest.mark.usefixtures('_mock_basic_commands')
def test_chain_deletion_check_mode(mocker):
    """Test chain deletion when present in check mode."""
    set_module_args(
        {
            "chain": "FOOBAR",
            "state": "absent",
            "chain_management": True,
            "_ansible_check_mode": True,
        }
    )

    commands_results = [
        (0, "", ""),  # check_chain_present
    ]

    run_command = mocker.patch(
        "ansible.module_utils.basic.AnsibleModule.run_command",
        side_effect=commands_results,
    )

    mocker.patch(
        "ansible.module_utils.basic.AnsibleModule.exit_json",
        side_effect=exit_json,
    )
    with pytest.raises(AnsibleExitJson) as exc:
        iptables.main()

    assert exc.value.args[0]["changed"]
    assert run_command.call_count == 1
    first_cmd_args_list = run_command.call_args_list[0]
    assert first_cmd_args_list[0][0] == [
        IPTABLES_CMD,
        "-t",
        "filter",
        "-L",
        "FOOBAR",
    ]

    commands_results = [
        (1, "", ""),  # check_rule_present
    ]

    run_command = mocker.patch(
        "ansible.module_utils.basic.AnsibleModule.run_command",
        side_effect=commands_results,
    )

    with pytest.raises(AnsibleExitJson) as exc:
        iptables.main()

    assert not exc.value.args[0]["changed"]
