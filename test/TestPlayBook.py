
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
import time
try:
   import json
except:
   import simplejson as json

EVENTS = []

class TestCallbacks(object):
    # using same callbacks class for both runner and playbook

    def __init__(self):
        pass

    def set_playbook(self, playbook):
        self.playbook = playbook

    def on_start(self):
        EVENTS.append('start')

    def on_setup_primary(self):
        EVENTS.append([ 'primary_setup' ])
 
    def on_setup_secondary(self):
        EVENTS.append([ 'secondary_setup' ])

    def on_skipped(self, host):
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

    def on_unreachable(self, host, msg):
        EVENTS.append([ 'unreachable', [ host, msg ]])

    def on_failed(self, host, results):
        EVENTS.append([ 'failed', [ host, results ]])

    def on_ok(self, host, result):
        # delete certain info from host_result to make test comparisons easier
        host_result = result.copy()
        for k in [ 'ansible_job_id', 'results_file', 'invocation', 'md5sum', 'delta', 'start', 'end' ]:
            if k in host_result:
                del host_result[k]
        for k in host_result.keys():
            if k.startswith('facter_') or k.startswith('ohai_'):
                del host_result[k] 
        EVENTS.append([ 'ok', [ host, host_result ]])

    def on_play_start(self, pattern):
        EVENTS.append([ 'play start', [ pattern ]])

    def on_async_confused(self, msg):
        EVENTS.append([ 'async confused', [ msg ]])

    def on_async_poll(self, jid, host, clock, host_result):
        EVENTS.append([ 'async poll', [ host ]])

    def on_unreachable(self, host, msg):
        EVENTS.append([ 'failed/dark', [ host, msg ]])

    def on_setup_primary(self):
        pass
    
    def on_setup_secondary(self):
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
           verbose      = False,
           stats            = ans_callbacks.AggregateStats(),
           callbacks        = self.test_callbacks,
           runner_callbacks = self.test_callbacks
       )
       results = self.playbook.run()
       return dict(
           results = results,
           events = EVENTS
       ) 

   def test_one(self):
       pb = os.path.join(self.test_dir, 'playbook1.yml')
       expected = os.path.join(self.test_dir, 'playbook1.events')
       expected = utils.json_loads(file(expected).read())
       actual = self._run(pb)
       # if different, this will output to screen 
       print utils.bigjson(actual)
       assert cmp(expected, actual) == 0, "expected events match actual events"

       # make sure the template module took options from the vars section
       data = file('/tmp/ansible_test_data_template.out').read()
       assert data.find("ears") != -1, "template success"

