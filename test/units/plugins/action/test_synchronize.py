'''
(Epdb) pprint(DeepDiff(self.final_task_vars, out_task_vars), indent=2)
{ 'dic_item_added': set([u"root['ansible_python_interpreter']"]),
  'dic_item_removed': set([ u"root['hostvars']['127.0.0.1']",
                            u"root['hostvars']['::1']",
                            u"root['hostvars']['localhost']"]),
  'iterable_item_added': { u"root['hostvars']['el6host']['groups']['all'][1]": u'::1',
                           u"root['hostvars']['el6host']['groups']['ungrouped'][1]": u'::1',
                           u"root['vars']['hostvars']['el6host']['groups']['all'][1]": u'::1',
                           u"root['vars']['hostvars']['el6host']['groups']['ungrouped'][1]": u'::1'}}
'''

import json
import os
import sys
import unittest
import yaml

from pprint import pprint

import ansible.plugins
from ansible.compat.tests.mock import patch, MagicMock
from ansible.plugins.action.synchronize import ActionModule


# Getting the incoming and outgoing task vars from the plugin's run method

'''
import copy
safe_vars = {}
for k,v in task_vars.items():
    if k not in ['vars', 'hostvars']:
        safe_vars[k] = copy.deepcopy(v)
    else:
        sdata = str(v)
        newv = eval(sdata)
        safe_vars[k] = newv

import json
with open('task_vars.json', 'wb') as f:
    f.write(json.dumps(safe_vars, indent=2))
'''


class BreakPoint(Exception):
    pass


class TaskMock(object):
    args = {'src': u'/tmp/deleteme',
            'dest': '/tmp/deleteme',
            'rsync_path': 'rsync'}
    async_val = None
    become = None
    become_user = None
    become_method = None


class StdinMock(object):
    shell = None


class ConnectionMock(object):
    ismock = True
    _play_context = None
    # transport = 'ssh'
    transport = None
    _new_stdin = StdinMock()

    get_option = MagicMock(return_value='root')

    # my shell
    _shell = MagicMock()
    _shell.mkdtemp.return_value = 'mkdir command'
    _shell.join_path.side_effect = os.path.join
    _shell.get_option = MagicMock(return_value=['root', 'toor'])


class PlayContextMock(object):
    shell = None
    private_key_file = None
    become = False
    become_user = 'root'
    become_method = None
    check_mode = False
    no_log = None
    diff = None
    remote_addr = None
    remote_user = None
    password = None


class ModuleLoaderMock(object):
    def find_plugin(self, module_name, mod_type):
        pass


class SharedLoaderMock(object):
    module_loader = ModuleLoaderMock()


class SynchronizeTester(object):

    ''' A wrapper for mocking out synchronize environments '''

    task = TaskMock()
    connection = ConnectionMock()
    _play_context = PlayContextMock()
    loader = None
    templar = None
    shared_loader_obj = SharedLoaderMock()

    final_task_vars = None
    execute_called = False

    def _execute_module(self, module_name, module_args=None, task_vars=None):
        self.execute_called = True
        self.final_module_args = module_args
        self.final_task_vars = task_vars
        return {}

    def runtest(self, fixturepath='fixtures/synchronize/basic'):

        metapath = os.path.join(fixturepath, 'meta.yaml')
        with open(metapath, 'rb') as f:
            fdata = f.read()
        test_meta = yaml.load(fdata)

        # load initial play context vars
        if '_play_context' in test_meta:
            if test_meta['_play_context']:
                self.task.args = {}
                for (k, v) in test_meta['_play_context'].items():
                    if v == 'None':
                        v = None
                    setattr(self._play_context, k, v)

        # load initial task context vars
        if '_task' in test_meta:
            if test_meta['_task']:
                self.task.args = {}
                for (k, v) in test_meta['_task'].items():
                    # import epdb; epdb.st()
                    if v == 'None':
                        v = None
                    setattr(self.task, k, v)

        # load initial task vars
        if 'task_args' in test_meta:
            if test_meta['task_args']:
                self.task.args = {}
                for (k, v) in test_meta['task_args'].items():
                    self.task.args[k] = v

        # load initial task vars
        invarspath = os.path.join(fixturepath, test_meta.get('fixtures', {}).get('taskvars_in', 'taskvars_in.json'))
        with open(invarspath, 'rb') as f:
            fdata = f.read()
        fdata = fdata.decode("utf-8")
        in_task_vars = json.loads(fdata)

        # load expected final task vars
        outvarspath = os.path.join(fixturepath, test_meta.get('fixtures', {}).get('taskvars_out', 'taskvars_out.json'))
        with open(outvarspath, 'rb') as f:
            fdata = f.read()
        fdata = fdata.decode("utf-8")
        out_task_vars = json.loads(fdata)

        # fixup the connection
        for (k, v) in test_meta['connection'].items():
            setattr(self.connection, k, v)

        # fixup the hostvars
        if test_meta['hostvars']:
            for (k, v) in test_meta['hostvars'].items():
                in_task_vars['hostvars'][k] = v

        # initialize and run the module
        SAM = ActionModule(self.task, self.connection, self._play_context,
                           self.loader, self.templar, self.shared_loader_obj)
        SAM._execute_module = self._execute_module
        result = SAM.run(task_vars=in_task_vars)

        # run assertions
        for check in test_meta['asserts']:
            value = eval(check)
            # if not value:
            #     print(check, value)
            #     import epdb; epdb.st()
            assert value, check


class FakePluginLoader(object):
    mocked = True

    @staticmethod
    def get(transport, play_context, new_stdin):
        conn = ConnectionMock()
        conn.transport = transport
        conn._play_context = play_context
        conn._new_stdin = new_stdin
        return conn


class TestSynchronizeAction(unittest.TestCase):

    fixturedir = os.path.dirname(__file__)
    fixturedir = os.path.join(fixturedir, 'fixtures', 'synchronize')
    # print(basedir)

    @patch('ansible.plugins.action.synchronize.connection_loader', FakePluginLoader)
    def test_basic(self):
        x = SynchronizeTester()
        x.runtest(fixturepath=os.path.join(self.fixturedir, 'basic'))

    @patch('ansible.plugins.action.synchronize.connection_loader', FakePluginLoader)
    def test_basic_become(self):
        x = SynchronizeTester()
        x.runtest(fixturepath=os.path.join(self.fixturedir, 'basic_become'))

    @patch('ansible.plugins.action.synchronize.connection_loader', FakePluginLoader)
    def test_basic_become_cli(self):
        # --become on the cli sets _play_context.become
        x = SynchronizeTester()
        x.runtest(fixturepath=os.path.join(self.fixturedir, 'basic_become_cli'))

    @patch('ansible.plugins.action.synchronize.connection_loader', FakePluginLoader)
    def test_basic_vagrant(self):
        # simple vagrant example
        x = SynchronizeTester()
        x.runtest(fixturepath=os.path.join(self.fixturedir, 'basic_vagrant'))

    @patch('ansible.plugins.action.synchronize.connection_loader', FakePluginLoader)
    def test_basic_vagrant_sudo(self):
        # vagrant plus sudo
        x = SynchronizeTester()
        x.runtest(fixturepath=os.path.join(self.fixturedir, 'basic_vagrant_sudo'))

    @patch('ansible.plugins.action.synchronize.connection_loader', FakePluginLoader)
    def test_basic_vagrant_become_cli(self):
        # vagrant plus sudo
        x = SynchronizeTester()
        x.runtest(fixturepath=os.path.join(self.fixturedir, 'basic_vagrant_become_cli'))

    @patch('ansible.plugins.action.synchronize.connection_loader', FakePluginLoader)
    def test_delegate_remote(self):
        # delegate to other remote host
        x = SynchronizeTester()
        x.runtest(fixturepath=os.path.join(self.fixturedir, 'delegate_remote'))

    @patch('ansible.plugins.action.synchronize.connection_loader', FakePluginLoader)
    def test_delegate_remote_su(self):
        # delegate to other remote host with su enabled
        x = SynchronizeTester()
        x.runtest(fixturepath=os.path.join(self.fixturedir, 'delegate_remote_su'))

    @patch.object(ActionModule, '_low_level_execute_command', side_effect=BreakPoint)
    @patch.object(ActionModule, '_remote_expand_user', side_effect=ActionModule._remote_expand_user, autospec=True)
    def test_remote_user_not_in_local_tmpdir(self, spy_remote_expand_user, ll_ec):
        x = SynchronizeTester()
        SAM = ActionModule(x.task, x.connection, x._play_context,
                           x.loader, x.templar, x.shared_loader_obj)
        try:
            SAM.run(task_vars={'hostvars': {'foo': {}, 'localhost': {}}, 'inventory_hostname': 'foo'})
        except BreakPoint:
            pass
        self.assertEqual(spy_remote_expand_user.call_count, 0)
