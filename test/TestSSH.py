import unittest
import tempfile
import os
import sys

from ansible.runner.connection_plugins.ssh import Connection


class FakeRunner(object):

    sudo = False



class TestSSHConnection(unittest.TestCase):

    def test_exec_command_allOutput(self):
        """
        ssh.Connection.exec_command should capture all output.
        """
        tmpdir = tempfile.mkdtemp()
        
        script_guts = ('''
import sys
import os
sys.stdout.write('a')
sys.stdout.flush()

os.write(2, 'b')
os.close(2)

sys.stdout.write('End')
''')
        script_name = os.path.join(tmpdir, 'script.py')
        fh = open(script_name, 'w')
        fh.write(script_guts)
        fh.close()

        runner = FakeRunner()
        runner.process_lockfile = open(os.path.join(tmpdir, 'process'), 'w')
        runner.output_lockfile = open(os.path.join(tmpdir, 'output'), 'w')

        conn = Connection(runner, '', '', '', '', '')
        conn._password_cmd = lambda: [sys.executable, script_name]
        conn._send_password = lambda: None
        conn.common_args = []

        tmpdir2 = tempfile.mkdtemp()
        rc, x, out, err = conn.exec_command('ignored', tmpdir2, 'root')
        self.assertEqual(out, 'aEnd', "All stdout should be read")
        self.assertEqual(err, 'b', "All stderr should be read")
        self.assertEqual(rc, 0, "Process should exit with success")        
