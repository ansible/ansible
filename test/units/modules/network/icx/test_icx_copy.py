# Copyright: (c) 2019, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from units.compat.mock import patch
from ansible.modules.network.icx import icx_copy
from units.modules.utils import set_module_args
from .icx_module import TestICXModule, load_fixture


class TestICXSCPModule(TestICXModule):

    module = icx_copy

    def setUp(self):
        super(TestICXSCPModule, self).setUp()
        self.mock_exec_scp = patch('ansible.modules.network.icx.icx_copy.exec_scp')
        self.mock_run_commands = patch('ansible.modules.network.icx.icx_copy.run_commands')
        self.exec_command = self.mock_exec_scp.start()
        self.run_commands = self.mock_run_commands.start()
        self.mock_exec_command = patch('ansible.modules.network.icx.icx_copy.exec_command')
        self.exec_commands = self.mock_exec_command.start()

    def tearDown(self):
        super(TestICXSCPModule, self).tearDown()
        self.mock_exec_scp.stop()
        self.mock_run_commands.stop()
        self.mock_exec_command.stop()

    def load_fixtures(self, commands=None):
        self.exec_commands.return_value = (0, load_fixture('icx_copy.txt').strip(), None)
        # self.exec_command.return_value = (0, load_fixture('icx_banner_show_banner.txt').strip(), None)
        if(commands is not None):
            fixtureName = commands[0].replace(" ", "_") + ".txt"
            # print("loading fixture: ",load_fixture(fixtureName).strip())
            self.mock_exec_scp.return_value = load_fixture("icx_copy.txt").strip()
            self.mock_run_commands.return_value = load_fixture("icx_copy.txt").strip()
        else:
            self.exec_command.return_value = ""

    def test_icx_scp_upload_running(self):
        set_module_args(
            dict(
                upload='running-config',
                protocol='scp',
                remote_server='172.16.10.49',
                remote_filename='running.conf',
                remote_user='alethea',
                remote_pass='alethea123'))
        commands = ['copy running-config scp 172.16.10.49 running.conf']
        self.execute_module(commands=commands)

    def test_icx_scp_download_running(self):
        set_module_args(
            dict(
                download='running-config',
                protocol='scp',
                remote_server='172.16.10.49',
                remote_filename='running.conf',
                remote_user='alethea',
                remote_pass='alethea123'))
        commands = ['copy scp running-config 172.16.10.49 running.conf']
        self.execute_module(commands=commands, changed=True)

    def test_icx_scp_upload_startup(self):
        set_module_args(
            dict(
                upload='startup-config',
                protocol='scp',
                remote_server='172.16.10.49',
                remote_filename='running.conf',
                remote_user='alethea',
                remote_pass='alethea123'))
        commands = ['copy startup-config scp 172.16.10.49 running.conf']
        self.execute_module(commands=commands, changed=False)

    def test_icx_scp_download_startup(self):
        set_module_args(
            dict(
                download='startup-config',
                protocol='scp',
                remote_server='172.16.10.49',
                remote_filename='running.conf',
                remote_user='alethea',
                remote_pass='alethea123'))
        commands = ['copy scp startup-config 172.16.10.49 running.conf']
        self.execute_module(commands=commands, changed=True)

    def test_icx_scp_upload_primary(self):
        set_module_args(
            dict(
                upload='flash_primary',
                protocol='scp',
                remote_server='172.16.10.49',
                remote_filename='SPS08080b.bin',
                remote_user='alethea',
                remote_pass='alethea123'))
        commands = ['copy flash scp 172.16.10.49 SPS08080b.bin primary']
        self.execute_module(commands=commands, changed=False)

    def test_icx_scp_download_primary(self):
        set_module_args(
            dict(
                download='flash_primary',
                protocol='scp',
                remote_server='172.16.10.49',
                remote_filename='SPS08080b.bin',
                remote_user='alethea',
                remote_pass='alethea123'))
        commands = ['copy scp flash 172.16.10.49 SPS08080b.bin primary']
        self.execute_module(commands=commands, changed=True)

    # HTTPS tests

    def test_icx_https_upload_running(self):
        set_module_args(
            dict(
                upload='running-config',
                protocol='https',
                remote_server='fileserver.alethea.in',
                remote_filename='filestorage/test/upload_running'))
        commands = ['copy running-config https fileserver.alethea.in filestorage/test/upload_running']
        self.execute_module(commands=commands)

    def test_icx_https_download_running(self):
        set_module_args(
            dict(
                download='running-config',
                protocol='https',
                remote_server='fileserver.alethea.in',
                remote_filename='filestorage/test/running.conf'))
        commands = ['copy https running-config fileserver.alethea.in filestorage/test/running.conf']
        self.execute_module(failed=True)

    def test_icx_https_upload_startup(self):
        set_module_args(
            dict(
                upload='startup-config',
                protocol='https',
                remote_server='fileserver.alethea.in',
                remote_filename='filestorage/test/upload_startup'))
        commands = ['copy startup-config https fileserver.alethea.in filestorage/test/upload_startup']
        self.execute_module(commands=commands)

    def test_icx_https_download_startup(self):
        set_module_args(
            dict(
                download='startup-config',
                protocol='https',
                remote_server='fileserver.alethea.in',
                remote_filename='filestorage/test/startup.conf'))
        commands = ['copy https startup-config fileserver.alethea.in filestorage/test/startup.conf']
        self.execute_module(commands=commands, changed=True)

    def test_icx_https_upload_primary(self):
        set_module_args(
            dict(
                upload='flash_primary',
                protocol='https',
                remote_server='fileserver.alethea.in',
                remote_filename='filestorage/test/upload_primary'))
        commands = ['copy startup-config https fileserver.alethea.in filestorage/test/upload_primary']
        self.execute_module(failed=True)

    def test_icx_https_download_primary(self):
        set_module_args(dict(download='flash_primary', protocol='https', remote_server='fileserver.alethea.in', remote_filename='filestorage/test/primary.bin'))
        commands = ['copy https flash fileserver.alethea.in filestorage/test/primary.bin primary']
        self.execute_module(commands=commands, changed=True)

    def test_icx_https_upload_secondary(self):
        set_module_args(
            dict(
                upload='flash_secondary',
                protocol='https',
                remote_server='fileserver.alethea.in',
                remote_filename='filestorage/test/upload_secondary'))
        commands = ['copy flash https fileserver.alethea.in filestorage/test/upload_secondary secondary']
        self.execute_module(failed=True)

    def test_icx_https_download_secondary(self):
        set_module_args(
            dict(
                download='flash_secondary',
                protocol='https',
                remote_server='fileserver.alethea.in',
                remote_filename='filestorage/test/secondary.bin'))
        commands = ['copy https flash fileserver.alethea.in filestorage/test/secondary.bin secondary']
        self.execute_module(commands=commands, changed=True)

    def test_icx_https_upload_download(self):
        set_module_args(
            dict(
                upload='flash_secondary',
                download='flash_secondary',
                protocol='https',
                remote_server='fileserver.alethea.in',
                remote_filename='filestorage/test/secondary.bin'))
        self.execute_module(failed=True)

    def test_icx_scp_no_user(self):
        set_module_args(dict(upload='running-config', protocol='scp', remote_server='172.16.10.49', remote_filename='running.conf'))
        self.execute_module(failed=True)
