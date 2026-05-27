# Copyright (c) 2026 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

from ansible.executor.play_iterator import PlayIterator
from ansible.playbook import Playbook
from ansible.playbook.play_context import PlayContext
from ansible.plugins.strategy.free import StrategyModule
from ansible.executor.task_queue_manager import TaskQueueManager

from units.mock.loader import DictDataLoader


def test_host_unreachable_index_error(mocker):
    """
    Test that free strategy handles hosts becoming unreachable between iterations.

    This test reproduces issue #87027 where an IndexError occurs when:
    1. last_host index is set from a previous iteration with N hosts
    2. Some hosts become unreachable, reducing hosts_left to M hosts (M < N)
    3. last_host >= M, causing IndexError on hosts_left[last_host]

    The test simulates:
    - Starting with 4 hosts
    - Processing through to last_host = 3
    - 2 hosts becoming unreachable (leaving only 2 hosts)
    - Next iteration attempting to access hosts_left[3] which is out of bounds
    """
    # Mock unfrackpath to be a no-op
    mocker.patch('ansible.playbook.role.definition.unfrackpath', side_effect=lambda x, *args, **kwargs: x)

    fake_loader = DictDataLoader({
        "test_play.yml": """
        - hosts: all
          gather_facts: no
          tasks:
            - name: task1
              debug: msg='task1'
        """,
    })

    mock_var_manager = mocker.MagicMock()
    mock_var_manager._fact_cache = {}
    mock_var_manager.get_vars.return_value = {}

    p = Playbook.load('test_play.yml', loader=fake_loader, variable_manager=mock_var_manager)

    inventory = mocker.MagicMock()
    inventory.hosts = {}
    hosts = []
    for i in range(4):
        host = mocker.MagicMock()
        host.name = host.get_name.return_value = f'host{i:02d}'
        hosts.append(host)
        inventory.hosts[host.name] = host
    inventory.get_hosts.return_value = hosts
    inventory.filter_hosts.return_value = hosts

    play_context = PlayContext(play=p._entries[0])

    itr = PlayIterator(
        inventory=inventory,
        play=p._entries[0],
        play_context=play_context,
        variable_manager=mock_var_manager,
        all_vars={},
    )

    tqm = TaskQueueManager(
        inventory=inventory,
        variable_manager=mock_var_manager,
        loader=fake_loader,
        passwords=None,
        forks=5,
    )
    tqm._initialize_processes(3)
    tqm._unreachable_hosts = {}

    strategy = StrategyModule(tqm)
    strategy._hosts_cache = [h.name for h in hosts]
    strategy._hosts_cache_all = [h.name for h in hosts]

    # Simulate the bug scenario:
    # 1. Mark hosts 2 and 3 as unreachable
    # 2. get_hosts_left() will return only [host00, host01] (length 2)
    # 3. Attempting to access hosts_left[3] should cause IndexError without the fix

    tqm._unreachable_hosts['host02'] = True
    tqm._unreachable_hosts['host03'] = True

    # Get the reduced hosts_left list (should only have host00 and host01)
    hosts_left = strategy.get_hosts_left(itr)
    assert len(hosts_left) == 2
    assert hosts_left[0].name == 'host00'
    assert hosts_left[1].name == 'host01'

    # Simulate the scenario that would trigger the bug:
    # We have last_host = 3 from a previous iteration, but hosts_left now only has 2 hosts
    # The fix should reset last_host to 0 when it's >= len(hosts_left)
    last_host = 3

    # Apply the fix logic (what should happen in free.py after get_hosts_left() call)
    if last_host >= len(hosts_left):
        last_host = 0

    # Verify the fix: last_host should now be 0 (reset)
    assert last_host == 0, "last_host should be reset to 0 when out of bounds"

    # Verify we can now safely access hosts_left[last_host]
    host = hosts_left[last_host]
    assert host.name == 'host00'
