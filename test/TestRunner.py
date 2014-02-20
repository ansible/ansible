
# tests are fairly 'live' (but safe to run)
# setup authorized_keys for logged in user such
# that the user can log in as themselves before running tests

import unittest
import getpass
import ansible.runner
import os
import shutil
import time
import tempfile

from nose.plugins.skip import SkipTest


def get_binary(name):
    for directory in os.environ["PATH"].split(os.pathsep):
        path = os.path.join(directory, name)
        if os.path.isfile(path) and os.access(path, os.X_OK):
            return path
    return None


class TestRunner(unittest.TestCase):

    def setUp(self):
        self.user = getpass.getuser()
        self.runner = ansible.runner.Runner(
            basedir='test/',
            module_name='ping',
            module_path='library/',
            module_args='',
            remote_user=self.user,
            remote_pass=None,
            host_list='test/ansible_hosts',
            timeout=5,
            forks=1,
            background=0,
            pattern='all',
            transport='local',
        )
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

    def _run(self, module_name, module_args, background=0, check_mode=False):
        ''' run a module and get the localhost results '''
        self.runner.module_name = module_name
        args = ' '.join(module_args)
        self.runner.module_args = args
        self.runner.background = background
        self.runner.check = check_mode
        results = self.runner.run()
        # when using nosetests this will only show up on failure
        # which is pretty useful
        assert "localhost" in results['contacted']
        return results['contacted']['localhost']

    def test_action_plugins(self):
        result = self._run("uncategorized_plugin", [])
        assert result.get("msg") == "uncategorized"
        result = self._run("categorized_plugin", [])
        assert result.get("msg") == "categorized"

    def test_ping(self):
        result = self._run('ping', [])
        assert "ping" in result

    def test_async(self):
        # test async launch and job status
        # of any particular module
        result = self._run('command', [get_binary("sleep"), "3"], background=20)
        assert 'ansible_job_id' in result
        assert 'started' in result
        jid = result['ansible_job_id']
        # no real chance of this op taking a while, but whatever
        time.sleep(5)
        # CLI will abstract this (when polling), but this is how it works internally
        result = self._run('async_status', ["jid=%s" % jid])
        # TODO: would be nice to have tests for supervisory process
        # killing job after X seconds
        assert 'finished' in result
        assert 'failed' not in result
        assert 'rc' in result
        assert 'stdout' in result
        assert result['ansible_job_id'] == jid

    def test_assemble(self):
        input = self._get_test_file('assemble.d')
        output = self._get_stage_file('sample.out')
        result = self._run('assemble', [
            "src=%s" % input,
            "dest=%s" % output,
        ])
        assert os.path.exists(output)
        out = file(output).read()
        assert out.find("first") != -1
        assert out.find("second") != -1
        assert out.find("third") != -1
        assert result['changed'] is True
        assert 'md5sum' in result
        assert 'failed' not in result
        result = self._run('assemble', [
            "src=%s" % input,
            "dest=%s" % output,
        ])
        assert result['changed'] is False

