import os
import tempfile

import unittest
from nose.tools import raises

from ansible import errors
from ansible.module_common import ModuleReplacer
from ansible.utils import md5 as utils_md5

TEST_MODULE_DATA = """
from ansible.module_utils.basic import *

def get_module():
    return AnsibleModule(
        argument_spec = dict(),
        supports_check_mode = True,
        no_log = True,
    )

get_module()

"""

class TestModuleUtilsBasic(unittest.TestCase):
 
    def cleanup_temp_file(self, fd, path):
        try:
            os.close(fd)
            os.remove(path)
        except:
            pass

    def cleanup_temp_dir(self, path):
        try:
            os.rmdir(path)
        except:
            pass

    def setUp(self):
        # create a temporary file for the test module 
        # we're about to generate
        self.tmp_fd, self.tmp_path = tempfile.mkstemp()
        os.write(self.tmp_fd, TEST_MODULE_DATA)

        # template the module code and eval it
        module_data, module_style, shebang = ModuleReplacer().modify_module(self.tmp_path, {}, "", {})

        d = {}
        exec(module_data, d, d)
        self.module = d['get_module']()

        # module_utils/basic.py screws with CWD, let's save it and reset
        self.cwd = os.getcwd()

    def tearDown(self):
        self.cleanup_temp_file(self.tmp_fd, self.tmp_path)
        # Reset CWD back to what it was before basic.py changed it
        os.chdir(self.cwd)

    #################################################################################
    # run_command() tests

    # test run_command with a string command
    def test_run_command_string(self):
        (rc, out, err) = self.module.run_command("/bin/echo -n 'foo bar'")
        self.assertEqual(rc, 0)
        self.assertEqual(out, 'foo bar')
        (rc, out, err) = self.module.run_command("/bin/echo -n 'foo bar'", use_unsafe_shell=True)
        self.assertEqual(rc, 0)
        self.assertEqual(out, 'foo bar')

    # test run_command with an array of args (with both use_unsafe_shell=True|False)
    def test_run_command_args(self):
        (rc, out, err) = self.module.run_command(['/bin/echo', '-n', "foo bar"])
        self.assertEqual(rc, 0)
        self.assertEqual(out, 'foo bar')
        (rc, out, err) = self.module.run_command(['/bin/echo', '-n', "foo bar"], use_unsafe_shell=True)
        self.assertEqual(rc, 0)
        self.assertEqual(out, 'foo bar')

    # test run_command with leading environment variables
    @raises(SystemExit)
    def test_run_command_string_with_env_variables(self):
        self.module.run_command('FOO=bar /bin/echo -n "foo bar"')
        
    @raises(SystemExit)
    def test_run_command_args_with_env_variables(self):
        self.module.run_command(['FOO=bar', '/bin/echo', '-n', 'foo bar'])

    def test_run_command_string_unsafe_with_env_variables(self):
        (rc, out, err) = self.module.run_command('FOO=bar /bin/echo -n "foo bar"', use_unsafe_shell=True)
        self.assertEqual(rc, 0)
        self.assertEqual(out, 'foo bar')

    # test run_command with a command pipe (with both use_unsafe_shell=True|False)
    def test_run_command_string_unsafe_with_pipe(self):
        (rc, out, err) = self.module.run_command('echo "foo bar" | cat', use_unsafe_shell=True)
        self.assertEqual(rc, 0)
        self.assertEqual(out, 'foo bar\n')

    # test run_command with a shell redirect in (with both use_unsafe_shell=True|False)
    def test_run_command_string_unsafe_with_redirect_in(self):
        (rc, out, err) = self.module.run_command('cat << EOF\nfoo bar\nEOF', use_unsafe_shell=True)
        self.assertEqual(rc, 0)
        self.assertEqual(out, 'foo bar\n')

    # test run_command with a shell redirect out (with both use_unsafe_shell=True|False)
    def test_run_command_string_unsafe_with_redirect_out(self):
        tmp_fd, tmp_path = tempfile.mkstemp()
        try:
            (rc, out, err) = self.module.run_command('echo "foo bar" > %s' % tmp_path, use_unsafe_shell=True)
            self.assertEqual(rc, 0)
            self.assertTrue(os.path.exists(tmp_path))
            md5sum = utils_md5(tmp_path)
            self.assertEqual(md5sum, '5ceaa7ed396ccb8e959c02753cb4bd18')
        except:
            raise
        finally:
            self.cleanup_temp_file(tmp_fd, tmp_path)

    # test run_command with a double shell redirect out (append) (with both use_unsafe_shell=True|False)
    def test_run_command_string_unsafe_with_double_redirect_out(self):
        tmp_fd, tmp_path = tempfile.mkstemp()
        try:
            (rc, out, err) = self.module.run_command('echo "foo bar" >> %s' % tmp_path, use_unsafe_shell=True)
            self.assertEqual(rc, 0)
            self.assertTrue(os.path.exists(tmp_path))
            md5sum = utils_md5(tmp_path)
            self.assertEqual(md5sum, '5ceaa7ed396ccb8e959c02753cb4bd18')
        except:
            raise
        finally:
            self.cleanup_temp_file(tmp_fd, tmp_path)

    # test run_command with data
    def test_run_command_string_with_data(self):
        (rc, out, err) = self.module.run_command('cat', data='foo bar')
        self.assertEqual(rc, 0)
        self.assertEqual(out, 'foo bar\n')

    # test run_command with binary data
    def test_run_command_string_with_binary_data(self):
        (rc, out, err) = self.module.run_command('cat', data='\x41\x42\x43\x44', binary_data=True)
        self.assertEqual(rc, 0)
        self.assertEqual(out, 'ABCD')

    # test run_command with a cwd set
    def test_run_command_string_with_cwd(self):
        tmp_path = tempfile.mkdtemp()
        try:
            (rc, out, err) = self.module.run_command('pwd', cwd=tmp_path)
            self.assertEqual(rc, 0)
            self.assertTrue(os.path.exists(tmp_path))
            self.assertEqual(out.strip(), os.path.realpath(tmp_path))
        except:
            raise
        finally:
            self.cleanup_temp_dir(tmp_path)


