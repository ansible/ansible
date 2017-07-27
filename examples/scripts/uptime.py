#!/usr/bin/env python

from collections import namedtuple

from ansible.executor.task_queue_manager import TaskQueueManager
from ansible.inventory import Inventory
from ansible.parsing.dataloader import DataLoader
from ansible.playbook.play import Play
from ansible.plugins.callback import CallbackBase
from ansible.vars.manager import VariableManager


# Create a callback object so we can capture the output
class ResultsCollector(CallbackBase):

    def __init__(self, *args, **kwargs):
        super(ResultsCollector, self).__init__(*args, **kwargs)
        self.host_ok = {}
        self.host_unreachable = {}
        self.host_failed = {}

    def v2_runner_on_unreachable(self, result):
        self.host_unreachable[result._host.get_name()] = result

    def v2_runner_on_ok(self, result, *args, **kwargs):
        self.host_ok[result._host.get_name()] = result

    def v2_runner_on_failed(self, result, *args, **kwargs):
        self.host_failed[result._host.get_name()] = result


def main():
    host_list = ['localhost', 'www.example.com', 'www.google.com']
    Options = namedtuple('Options', ['connection', 'module_path', 'forks', 'remote_user',
                                     'private_key_file', 'ssh_common_args', 'ssh_extra_args', 'sftp_extra_args',
                                     'scp_extra_args', 'become', 'become_method', 'become_user', 'verbosity', 'check'])

    # initialize needed objects
    variable_manager = VariableManager()
    loader = DataLoader()
    options = Options(connection='smart', module_path='/usr/share/ansible', forks=100,
                      remote_user=None, private_key_file=None, ssh_common_args=None, ssh_extra_args=None,
                      sftp_extra_args=None, scp_extra_args=None, become=None, become_method=None,
                      become_user=None, verbosity=None, check=False)

    passwords = dict()

    # create inventory and pass to var manager
    inventory = Inventory(loader=loader, variable_manager=variable_manager, host_list=host_list)
    variable_manager.set_inventory(inventory)

    # create play with tasks
    play_source = dict(
        name="Ansible Play",
        hosts=host_list,
        gather_facts='no',
        tasks=[dict(action=dict(module='command', args=dict(cmd='/usr/bin/uptime')))]
    )
    play = Play().load(play_source, variable_manager=variable_manager, loader=loader)

    # actually run it
    tqm = None
    callback = ResultsCollector()
    try:
        tqm = TaskQueueManager(
            inventory=inventory,
            variable_manager=variable_manager,
            loader=loader,
            options=options,
            passwords=passwords,
        )
        tqm._stdout_callback = callback
        result = tqm.run(play)
    finally:
        if tqm is not None:
            tqm.cleanup()

    print("UP ***********")
    for host, result in callback.host_ok.items():
        print('{} >>> {}'.format(host, result._result['stdout']))

    print("FAILED *******")
    for host, result in callback.host_failed.items():
        print('{} >>> {}'.format(host, result._result['msg']))

    print("DOWN *********")
    for host, result in callback.host_unreachable.items():
        print('{} >>> {}'.format(host, result._result['msg']))

if __name__ == '__main__':
    main()
