
# tests are fairly 'live' (but safe to run)
# setup authorized_keys for logged in user such
# that the user can log in as themselves before running tests

import unittest
import getpass
import ansible.playbook
import os
import shutil
import time
try:
   import json
except:
   import simplejson as json

class TestCallbacks(object):

    def __init__(self):
        self.tasks_started = []
        self.plays_started = []
        self.unreachable = {}
        self.failed = {}
        self.ok_counts = {}
        self.poll_events = []
        self.dark = []

    def results(self):
        return dict(
            tasks_started = self.tasks_started,
            plays_started = self.plays_started,
            unreachable   = self.unreachable,
            failed        = self.failed,
            ok_counts     = self.ok_counts,
            poll_events   = self.poll_events,
            dark          = self.dark
        )

    def set_playbook(self, playbook):
        self.playbook = playbook

    def on_start(self):
        pass

    def on_task_start(self, name, is_conditional):
        self.tasks_started.append(name)

    def on_unreachable(self, host, msg):
        self.unreachable[host] = msg

    def on_failed(self, host, results):
        self.failed[host] = results

    def on_ok(self, host):
        ok = self.ok_counts.get(host, 0)
        self.ok_counts[host] = ok + 1

    def on_play_start(self, pattern):
        self.plays_started.append(pattern)

    def on_async_confused(self, msg):
        raise Exception("confused: %s" % msg)

    def on_async_poll(self, jid, host, clock, host_result):
        self.poll_events.append([jid,host,clock.host_result])

    def on_dark_host(self, host, msg):
        self.dark.append([host,msg])


class TestRunner(unittest.TestCase):

   def setUp(self):
       self.user = getpass.getuser()
       self.cwd = os.getcwd()
       self.test_dir = os.path.join(self.cwd, 'test')
       self.stage_dir = self._prepare_stage_dir()

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
           callbacks    = self.test_callbacks
       )
       results = self.playbook.run()
       return dict(
           results   = results,
           callbacks = self.test_callbacks.results(),
       ) 

   def test_one(self):
       pb = os.path.join(self.test_dir, 'playbook1.yml')
       print self._run(pb)

