# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

from ansible.module_utils.facts.network import linux

# ip -4 route show table local
IP4_ROUTE_SHOW_LOCAL = """
broadcast 127.0.0.0 dev lo proto kernel scope link src 127.0.0.1
local 127.0.0.0/8 dev lo proto kernel scope host src 127.0.0.1
local 127.0.0.1 dev lo proto kernel scope host src 127.0.0.1
broadcast 127.255.255.255 dev lo proto kernel scope link src 127.0.0.1
local 192.168.1.0/24 dev lo scope host
"""

# ip -6 route show table local
IP6_ROUTE_SHOW_LOCAL = """
local ::1 dev lo proto kernel metric 0 pref medium
local 2a02:123:3:1::e dev enp94s0f0np0 proto kernel metric 0 pref medium
local 2a02:123:15::/48 dev lo metric 1024 pref medium
local 2a02:123:16::/48 dev lo metric 1024 pref medium
local fe80::2eea:7fff:feca:fe68 dev enp94s0f0np0 proto kernel metric 0 pref medium
multicast ff00::/8 dev enp94s0f0np0 proto kernel metric 256 pref medium
"""

# Hash returned by get_locally_reachable_ips()
IP_ROUTE_SHOW_LOCAL_EXPECTED = {
    'ipv4': [
        '127.0.0.0/8',
        '127.0.0.1',
        '192.168.1.0/24'
    ],
    'ipv6': [
        '::1',
        '2a02:123:3:1::e',
        '2a02:123:15::/48',
        '2a02:123:16::/48',
        'fe80::2eea:7fff:feca:fe68'
    ]
}


def mock_get_bin_path(command):
    cmds = {"ip": "fake/ip"}
    return cmds.get(command, None)


def test_linux_local_routes(mocker):
    module = mocker.MagicMock()
    mocker.patch.object(module, "get_bin_path", side_effect=mock_get_bin_path)
    mocker.patch.object(
        module,
        "run_command",
        side_effect=[(0, IP4_ROUTE_SHOW_LOCAL, ""), (0, IP6_ROUTE_SHOW_LOCAL, "")],
    )

    net = linux.LinuxNetwork(module)
    res = net.get_locally_reachable_ips(mock_get_bin_path("ip"))
    assert res == IP_ROUTE_SHOW_LOCAL_EXPECTED
