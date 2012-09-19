
# tests are fairly 'live' (but safe to run)
# setup authorized_keys for logged in user such
# that the user can log in as themselves before running tests

import unittest
import getpass
import ansible.playbook
import ansible.utils as utils
import ansible.callbacks as ans_callbacks
import os
import shutil

EVENTS = []

class TestCallbacks(object):
    # using same callbacks class for both runner and playbook

    def __init__(self):
        pass

    def set_playbook(self, playbook):
        self.playbook = playbook

    def on_start(self):
        EVENTS.append('start')

    def on_skipped(self, host, item=None):
        EVENTS.append([ 'skipped', [ host ]])

    def on_import_for_host(self, host, filename):
        EVENTS.append([ 'import', [ host, filename ]])

    def on_error(self, host, msg):
        EVENTS.append([ 'stderr', [ host, msg ]])

    def on_not_import_for_host(self, host, missing_filename):
        pass

    def on_notify(self, host, handler):
        EVENTS.append([ 'notify', [ host, handler ]])

    def on_task_start(self, name, is_conditional):
        EVENTS.append([ 'task start', [ name, is_conditional ]])

    def on_failed(self, host, results, ignore_errors):
        EVENTS.append([ 'failed', [ host, results, ignore_errors ]])

    def on_ok(self, host, result):
        # delete certain info from host_result to make test comparisons easier
        host_result = result.copy()
        for k in [ 'ansible_job_id', 'results_file', 'md5sum', 'delta', 'start', 'end' ]:
            if k in host_result:
                del host_result[k]
        for k in host_result.keys():
            if k.startswith('facter_') or k.startswith('ohai_'):
                del host_result[k]
        EVENTS.append([ 'ok', [ host, host_result ]])

    def on_play_start(self, pattern):
        EVENTS.append([ 'play start', [ pattern ]])

    def on_async_ok(self, host, res, jid):
        EVENTS.append([ 'async ok', [ host ]])

    def on_async_poll(self, host, res, jid, clock):
        EVENTS.append([ 'async poll', [ host ]])

    def on_async_failed(self, host, res, jid):
        EVENTS.append([ 'async failed', [ host ]])

    def on_unreachable(self, host, msg):
        EVENTS.append([ 'failed/dark', [ host, msg ]])

    def on_setup(self):
        pass

    def on_no_hosts(self):
        pass

class TestPlaybook(unittest.TestCase):

   def setUp(self):
       self.user = getpass.getuser()
       self.cwd = os.getcwd()
       self.test_dir = os.path.join(self.cwd, 'test')
       self.stage_dir = self._prepare_stage_dir()

       if os.path.exists('/tmp/ansible_test_data_copy.out'):
           os.unlink('/tmp/ansible_test_data_copy.out')
       if os.path.exists('/tmp/ansible_test_data_template.out'):
           os.unlink('/tmp/ansible_test_data_template.out')

   def _prepare_stage_dir(self):
       stage_path = os.path.join(self.test_dir, 'test_data')
       if os.path.exists(stage_path):
           shutil.rmtree(stage_path, ignore_errors=False)
           assert not os.path.exists(stage_path)
       os.makedirs(stage_path)
       assert os.path.exists(stage_path)
       return stage_path

   def _get_test_file(self, filename):
       # get a file inside the test input directory
       filename = os.path.join(self.test_dir, filename)
       assert os.path.exists(filename)
       return filename

   def _get_stage_file(self, filename):
       # get a file inside the test output directory
       filename = os.path.join(self.stage_dir, filename)
       return filename

   def _run(self, test_playbook):
       ''' run a module and get the localhost results '''
       self.test_callbacks = TestCallbacks()
       self.playbook = ansible.playbook.PlayBook(
           playbook     = test_playbook,
           host_list    = 'test/ansible_hosts',
           module_path  = 'library/',
           forks        = 1,
           timeout      = 5,
           remote_user  = self.user,
           remote_pass  = None,
           stats            = ans_callbacks.AggregateStats(),
           callbacks        = self.test_callbacks,
           runner_callbacks = self.test_callbacks
       )
       result = self.playbook.run()
       return result

   def test_one(self):
       pb = os.path.join(self.test_dir, 'playbook1.yml')
       actual = self._run(pb)

       # if different, this will output to screen
       print "**ACTUAL**"
       print utils.jsonify(actual, format=True)
       expected =  {
            "localhost": {
                "changed": 9,
                "failures": 0,
                "ok": 11,
                "skipped": 1,
                "unreachable": 0
            }
       }
       print "**EXPECTED**"
       print utils.jsonify(expected, format=True)

       assert utils.jsonify(expected, format=True) == utils.jsonify(actual,format=True)

       # make sure the template module took options from the vars section
       data = file('/tmp/ansible_test_data_template.out').read()
       print data
       assert data.find("ears") != -1, "template success"

   def test_playbook_vars(self): 
       test_callbacks = TestCallbacks()
       playbook = ansible.playbook.PlayBook(
           playbook=os.path.join(self.test_dir, 'test_playbook_vars', 'playbook.yml'),
           host_list='test/test_playbook_vars/hosts',
           stats=ans_callbacks.AggregateStats(),
           callbacks=test_callbacks,
           runner_callbacks=test_callbacks
       )
       playbook.run()
       assert playbook.SETUP_CACHE['host1'] == {'attr2': 2, 'attr1': 1}
       assert playbook.SETUP_CACHE['host2'] == {'attr2': 2}

   def test_yaml_hosts_list(self):
       # Make sure playbooks support hosts: [host1, host2]
       # TODO: Actually run the play on more than one host
       test_callbacks = TestCallbacks()
       playbook = ansible.playbook.PlayBook(
           playbook=os.path.join(self.test_dir, 'hosts_list.yml'),
           host_list='test/ansible_hosts',
           stats=ans_callbacks.AggregateStats(),
           callbacks=test_callbacks,
           runner_callbacks=test_callbacks
       )
       play = ansible.playbook.Play(playbook, playbook.playbook[0], os.getcwd())
       assert play.hosts == ';'.join(('host1', 'host2', 'host3'))

   def test_results_list(self):
       # Test that we can iterate over the lines of a command's stdout in a register variable.
       test_callbacks = TestCallbacks()
       playbook = ansible.playbook.PlayBook(
           playbook=os.path.join(self.test_dir, 'results_list.yml'),
           host_list='test/ansible_hosts',
           stats=ans_callbacks.AggregateStats(),
           callbacks=test_callbacks,
           runner_callbacks=test_callbacks
       )
       result = playbook.run()
       self.assertIn('localhost', result)
       self.assertIn('ok', result['localhost'])
       self.assertEqual(result['localhost']['ok'], 6)
       self.assertIn('failures', result['localhost'])
       self.assertEqual(result['localhost']['failures'], 0)
