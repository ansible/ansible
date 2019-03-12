from __future__ import (absolute_import, division, print_function)

from ansible import constants as C
from ansible.executor.play_iterator import PlayIterator
from ansible.executor.task_queue_manager import TaskQueueManager
from ansible.inventory.manager import InventoryManager
from ansible.parsing.dataloader import DataLoader
from ansible.playbook import Playbook
from ansible.playbook.play_context import PlayContext
from ansible.plugins.strategy.free import StrategyModule as FSM
from ansible.plugins.strategy.linear import StrategyModule as LSM
from ansible.vars.manager import VariableManager

import pytest


base_test_case = {
    'roles/with_handler/tasks/main.yml': """
        - name: role task
          shell: echo "hello world"
          notify: myhandler
    """,
    'roles/with_handler/handlers/main.yml': """
        - name: myhandler
          command: echo a
    """,
    'playbook.yml': """
        - hosts: localhost
          gather_facts: no
          tasks:
          - include_role: name=with_handler
            loop: [1, 2, 3]
    """,
}


def handlers_to_trigger(p):
    play = p._entries[0]
    names = []
    for h in play.handlers:
        for b in h.block:
            names.append(b.get_name())
    return names


@pytest.fixture()
def setup_test_env(tmpdir, monkeypatch):
    role_dir = tmpdir.mkdir("roles")
    monkeypatch.setattr(C, 'DEFAULT_ROLES_PATH', [str(role_dir)])

    def creator(files):
        for f in files:
            tmpdir.ensure(f).write(files[f])
        return str(tmpdir.join('playbook.yml'))
    return creator


def run_playbook(test_env, strategy_class, monkeypatch):
    loader = DataLoader()
    inventory = InventoryManager(loader=loader, sources='localhost')
    var_manager = VariableManager(loader=loader, inventory=inventory)

    p = Playbook.load(test_env, loader=loader, variable_manager=var_manager)
    play = p._entries[0]

    play_context = PlayContext(play=play)

    itr = PlayIterator(
        inventory=inventory,
        play=play,
        play_context=play_context,
        variable_manager=var_manager,
        all_vars=dict(),
    )

    tqm = TaskQueueManager(
        inventory=inventory,
        variable_manager=var_manager,
        loader=loader,
        passwords=None,
    )
    tqm._initialize_processes(1)
    strategy = strategy_class(tqm)

    for handler in play.compile_roles_handlers():
        play.add_handler(handler)

    results = []
    handlers = []

    def record_handler_calls(*args, **kwargs):
        if args[1] == 'v2_playbook_on_handler_task_start':
            handler = args[2].get_name()  # Remove the "HANDLER: " prefix
            handlers.append(handler)
        elif args[1] == 'v2_runner_on_ok':
            results.append(args[2]._result)
    monkeypatch.setattr(TaskQueueManager, 'send_callback', record_handler_calls)
    assert strategy.run(itr, play_context) == TaskQueueManager.RUN_OK
    return handlers, results


@pytest.mark.parametrize('strategy_class', [LSM, FSM])
def test_import_role_loop(setup_test_env, strategy_class, monkeypatch):
    test_case = base_test_case.copy()

    playbook_file = setup_test_env(test_case)
    handlers, dummy = run_playbook(playbook_file, strategy_class, monkeypatch)
    assert handlers == ['with_handler : myhandler']


@pytest.mark.parametrize('strategy_class', [LSM, FSM])
def test_include_role_loop(setup_test_env, strategy_class, monkeypatch):
    test_case = base_test_case.copy()
    test_case.update({
        'playbook.yml': """
        - hosts: localhost
          gather_facts: no
          tasks:
          - include_role: name=with_handler
            loop: [1, 2, 3]
        """,
    })

    playbook_file = setup_test_env(test_case)
    handlers, dummy = run_playbook(playbook_file, strategy_class, monkeypatch)
    assert handlers == ['with_handler : myhandler']


@pytest.mark.parametrize('strategy_class', [LSM, FSM])
def test_include_role_loop_listen(setup_test_env, strategy_class, monkeypatch):
    test_case = base_test_case.copy()
    test_case.update({
        'playbook.yml': """
        - hosts: localhost
          gather_facts: no
          tasks:
          - include_role: name=with_handler
            loop: [1, 2, 3]
        """,
        'roles/with_handler/handlers/main.yml': """
        - name: first
          debug: msg=myhandler
          listen: myhandler
        - name: second
          debug: msg=myhandler
          listen: myhandler
        """,
    })

    playbook_file = setup_test_env(test_case)
    handlers, dummy = run_playbook(playbook_file, strategy_class, monkeypatch)
    # Call are duplicated. for more details, see:
    # https://github.com/ansible/ansible/pull/53644
    assert handlers == [
        'with_handler : first',
        'with_handler : second',
        'with_handler : first',
        'with_handler : second',
        'with_handler : first',
        'with_handler : second']


@pytest.mark.parametrize('strategy_class', [LSM, FSM])
def test_notify_in_handler(setup_test_env, strategy_class, monkeypatch):
    test_case = base_test_case.copy()
    test_case.update({
        'roles/with_handler/handlers/main.yml': """
        - name: myhandler
          command: echo a
          notify: myhandler2
        - name: myhandler2
          command: echo a
        """,
    })

    playbook_file = setup_test_env(test_case)
    handlers, dummy = run_playbook(playbook_file, strategy_class, monkeypatch)
    assert handlers == ['with_handler : myhandler', 'with_handler : myhandler2']


@pytest.mark.parametrize('strategy_class', [LSM, FSM])
def test_include_task_in_handler(setup_test_env, strategy_class, monkeypatch):
    test_case = base_test_case.copy()
    test_case.update({
        'roles/with_handler/tasks/my_tasks.yml': """
        - name: role task
          command: echo a
        """,
        'roles/with_handler/handlers/main.yml': """
        - name: myhandler
          include_tasks: my_tasks.yml
        """,
    })

    playbook_file = setup_test_env(test_case)
    handlers, dummy = run_playbook(playbook_file, strategy_class, monkeypatch)
    assert handlers == ['with_handler : myhandler', 'with_handler : role task']


@pytest.mark.parametrize('strategy_class', [LSM, FSM])
def test_first_handler_dup_win(setup_test_env, strategy_class, monkeypatch):
    test_case = base_test_case.copy()
    test_case.update({
        'roles/with_handler/handlers/main.yml': """
        - name: myhandler
          debug:
            msg: first win
        - name: myhandler
          debug:
            msg: last is ignored
        """,
    })

    playbook_file = setup_test_env(test_case)
    handlers, results = run_playbook(playbook_file, strategy_class, monkeypatch)
    assert handlers == ['with_handler : myhandler']
    assert results[-1]['msg'] == 'first win'


@pytest.mark.parametrize('strategy_class', [LSM, FSM])
def test_first_listen_dup_win(setup_test_env, strategy_class, monkeypatch):
    test_case = base_test_case.copy()
    test_case.update({
        'roles/with_handler/handlers/main.yml': """
        - name: first
          debug:
            msg: first win
          listen: myhandler
        - name: second
          debug:
            msg: last is second
          listen: myhandler
        - name: myhandler
          debug:
            msg: myhandler by name
        """,
    })

    playbook_file = setup_test_env(test_case)
    handlers, results = run_playbook(playbook_file, strategy_class, monkeypatch)
    assert results[-3]['msg'] == 'first win'
    assert results[-2]['msg'] == 'last is second'
    assert results[-1]['msg'] == 'myhandler by name'


@pytest.mark.parametrize('strategy_class', [LSM, FSM])
def test_play_handlers_before_role(setup_test_env, strategy_class, monkeypatch):
    test_case = base_test_case.copy()
    test_case.update({
        'playbook.yml': """
        - hosts: localhost
          gather_facts: no
          handlers:
          - name: handler_from_playbook
            debug:
              msg: foo
          tasks:
          - include_role: name=with_handler
          - command: echo a
            notify: handler_from_playbook
        """,
    })

    playbook_file = setup_test_env(test_case)
    handlers, results = run_playbook(playbook_file, strategy_class, monkeypatch)
    assert handlers == ['handler_from_playbook', 'with_handler : myhandler']
