
import unittest
import getpass
import os
import shutil
import time
import tempfile
from nose.plugins.skip import SkipTest

from ansible.runner.action_plugins.synchronize import ActionModule as Synchronize

class FakeRunner(object):
    def __init__(self):
        self.connection = None
        self.transport = None
        self.basedir = None
        self.sudo = None
        self.remote_user = None
        self.private_key_file = None
        self.check = False

    def _execute_module(self, conn, tmp, module_name, args,
        async_jid=None, async_module=None, async_limit=None, inject=None, 
        persist_files=False, complex_args=None, delete_remote_tmp=True):
        self.executed_conn = conn
        self.executed_tmp = tmp
        self.executed_module_name = module_name
        self.executed_args = args
        self.executed_async_jid = async_jid
        self.executed_async_module = async_module
        self.executed_async_limit = async_limit
        self.executed_inject = inject
        self.executed_persist_files = persist_files
        self.executed_complex_args = complex_args
        self.executed_delete_remote_tmp = delete_remote_tmp

    def noop_on_check(self, inject):
        return self.check

class FakeConn(object):
    def __init__(self):
        self.host = None
        self.delegate = None

class TestSynchronize(unittest.TestCase):


    def test_synchronize_action_basic(self):

        """ verify the synchronize action plugin sets 
            the delegate to 127.0.0.1 and remote path to user@[host]:/path """

        runner = FakeRunner()
        runner.remote_user = "root"
        runner.transport = "ssh"
        conn = FakeConn()
        inject = {
                    'inventory_hostname': "el6.lab.net",
                    'inventory_hostname_short': "el6",
                    'ansible_connection': None,
                    'ansible_ssh_user': 'root',
                    'delegate_to': None,
                    'playbook_dir': '.',
                 }

        x = Synchronize(runner)
        x.setup("synchronize", inject)
        x.run(conn, "/tmp", "synchronize", "src=/tmp/foo dest=/tmp/bar", inject)

        assert runner.executed_inject['delegate_to'] == "127.0.0.1", "was not delegated to 127.0.0.1"
        assert runner.executed_complex_args == {"dest":"root@[el6.lab.net]:/tmp/bar", "src":"/tmp/foo"}, "wrong args used"
        assert runner.sudo == None, "sudo was not reset to None" 

    def test_synchronize_action_ipv6(self):

        """ verify the synchronize action plugin sets
            the IPv6 remote path to user@[host]:/path """

        runner = FakeRunner()
        runner.remote_user = "root"
        runner.transport = "ssh"
        conn = FakeConn()
        inject = {
                    'inventory_hostname': "2001:470:1f05:1a07::1",
                    'inventory_hostname_short': "2001:470:1f05:1a07::1",
                    'ansible_connection': None,
                    'ansible_ssh_user': 'root',
                    'delegate_to': None,
                    'playbook_dir': '.',
                 }

        x = Synchronize(runner)
        x.setup("synchronize", inject)
        x.run(conn, "/tmp", "synchronize", "src=/tmp/foo dest=/tmp/bar", inject)

        assert runner.executed_inject['delegate_to'] == "127.0.0.1", "was not delegated to 127.0.0.1"
        assert runner.executed_complex_args == {"dest":"root@[2001:470:1f05:1a07::1]:/tmp/bar", "src":"/tmp/foo"}, "wrong args used"
        assert runner.sudo == None, "sudo was not reset to None"


    def test_synchronize_action_sudo(self):

        """ verify the synchronize action plugin unsets and then sets sudo """ 

        runner = FakeRunner()
        runner.sudo = True
        runner.remote_user = "root"
        runner.transport = "ssh"
        conn = FakeConn()
        inject = {
                    'inventory_hostname': "el6.lab.net",
                    'inventory_hostname_short': "el6",
                    'ansible_connection': None,
                    'ansible_ssh_user': 'root',
                    'delegate_to': None,
                    'playbook_dir': '.',
                 }

        x = Synchronize(runner)
        x.setup("synchronize", inject)
        x.run(conn, "/tmp", "synchronize", "src=/tmp/foo dest=/tmp/bar", inject)

        assert runner.executed_inject['delegate_to'] == "127.0.0.1", "was not delegated to 127.0.0.1"
        assert runner.executed_complex_args == {'dest':'root@[el6.lab.net]:/tmp/bar',
                                                'src':'/tmp/foo',
                                                'rsync_path':'"sudo rsync"'}, "wrong args used"
        assert runner.sudo == True, "sudo was not reset to True" 


    def test_synchronize_action_local(self):

        """ verify the synchronize action plugin sets 
            the delegate to 127.0.0.1 and does not alter the dest """

        runner = FakeRunner()
        runner.remote_user = "jtanner"
        runner.transport = "paramiko"
        conn = FakeConn()
        conn.host = "127.0.0.1"
        conn.delegate = "thishost"
        inject = {
                    'inventory_hostname': "thishost",
                    'ansible_ssh_host': '127.0.0.1',
                    'ansible_connection': 'local',
                    'delegate_to': None,
                    'playbook_dir': '.',
                 }

        x = Synchronize(runner)
        x.setup("synchronize", inject)
        x.run(conn, "/tmp", "synchronize", "src=/tmp/foo dest=/tmp/bar", inject)

        assert runner.transport == "paramiko", "runner transport was changed"
        assert runner.remote_user == "jtanner", "runner remote_user was changed"
        assert runner.executed_inject['delegate_to'] == "127.0.0.1", "was not delegated to 127.0.0.1"
        assert "dest_port" not in runner.executed_complex_args, "dest_port should not have been set"
        assert runner.executed_complex_args.get("src") == "/tmp/foo", "source was set incorrectly"
        assert runner.executed_complex_args.get("dest") == "/tmp/bar", "dest was set incorrectly"


    def test_synchronize_action_vagrant(self):

        """ Verify the action plugin accommodates the common
            scenarios for vagrant boxes. """

        runner = FakeRunner()
        runner.remote_user = "jtanner"
        runner.transport = "ssh"
        conn = FakeConn()
        conn.host = "127.0.0.1"
        conn.delegate = "thishost"
        inject = {
                    'inventory_hostname': "thishost",
                    'ansible_ssh_user': 'vagrant',
                    'ansible_ssh_host': '127.0.0.1',
                    'ansible_ssh_port': '2222',
                    'delegate_to': None,
                    'playbook_dir': '.',
                    'hostvars': {
                        'thishost': {
                            'inventory_hostname': 'thishost',
                            'ansible_ssh_port': '2222',
                            'ansible_ssh_host': '127.0.0.1',
                            'ansible_ssh_user': 'vagrant'
                        }
                    }
                 }

        x = Synchronize(runner)
        x.setup("synchronize", inject)
        x.run(conn, "/tmp", "synchronize", "src=/tmp/foo dest=/tmp/bar", inject)

        assert runner.transport == "ssh", "runner transport was changed"
        assert runner.remote_user == "jtanner", "runner remote_user was changed"
        assert runner.executed_inject['delegate_to'] == "127.0.0.1", "was not delegated to 127.0.0.1"
        assert runner.executed_inject['ansible_ssh_user'] == "vagrant", "runner user was changed"
        assert runner.executed_complex_args.get("dest_port") == "2222", "remote port was not set to 2222"
        assert runner.executed_complex_args.get("src") == "/tmp/foo", "source was set incorrectly"
        assert runner.executed_complex_args.get("dest") == "vagrant@[127.0.0.1]:/tmp/bar", "dest was set incorrectly"

