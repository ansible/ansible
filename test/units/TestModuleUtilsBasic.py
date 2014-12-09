import os
import tempfile

import unittest
from nose.tools import raises
from nose.tools import timed

from ansible import errors
from ansible.module_common import ModuleReplacer
from ansible.utils import checksum as utils_checksum

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
            checksum = utils_checksum(tmp_path)
            self.assertEqual(checksum, 'd53a205a336e07cf9eac45471b3870f9489288ec')
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
            checksum = utils_checksum(tmp_path)
            self.assertEqual(checksum, 'd53a205a336e07cf9eac45471b3870f9489288ec')
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


class TestModuleUtilsBasicHelpers(unittest.TestCase):
    ''' Test some implementation details of AnsibleModule

    Some pieces of AnsibleModule are implementation details but they have
    potential cornercases that we need to check.  Go ahead and test at
    this level that the functions are behaving even though their API may
    change and we'd have to rewrite these tests so that we know that we
    need to check for those problems in any rewrite.

    In the future we might want to restructure higher level code to be
    friendlier to unittests so that we can test at the level that the public
    is interacting with the APIs.
    '''

    MANY_RECORDS = 7000
    URL_SECRET = 'http://username:pas:word@foo.com/data'
    SSH_SECRET = 'username:pas:word@foo.com/data'

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

    def _gen_data(self, records, per_rec, top_level, secret_text):
        hostvars = {'hostvars': {}}
        for i in range(1, records, 1):
            host_facts = {'host%s' % i:
                            {'pstack':
                                {'running': '875.1',
                                 'symlinked': '880.0',
                                 'tars': [],
                                 'versions': ['885.0']},
                         }}

            if per_rec:
                host_facts['host%s' % i]['secret'] = secret_text
            hostvars['hostvars'].update(host_facts)
        if top_level:
            hostvars['secret'] = secret_text
        return hostvars

    def setUp(self):
        self.many_url = repr(self._gen_data(self.MANY_RECORDS, True, True,
            self.URL_SECRET))
        self.many_ssh = repr(self._gen_data(self.MANY_RECORDS, True, True,
            self.SSH_SECRET))
        self.one_url = repr(self._gen_data(self.MANY_RECORDS, False, True,
            self.URL_SECRET))
        self.one_ssh = repr(self._gen_data(self.MANY_RECORDS, False, True,
            self.SSH_SECRET))
        self.zero_secrets = repr(self._gen_data(self.MANY_RECORDS, False,
            False, ''))
        self.few_url = repr(self._gen_data(2, True, True, self.URL_SECRET))
        self.few_ssh = repr(self._gen_data(2, True, True, self.SSH_SECRET))

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

    #
    # Speed tests
    #

    # Previously, we used regexes which had some pathologically slow cases for
    # parameters with large amounts of data with many ':' but no '@'.  The
    # present function gets slower when there are many replacements so we may
    # want to explore regexes in the future (for the speed when substituting
    # or flexibility).  These speed tests will hopefully tell us if we're
    # introducing code that has cases that are simply too slow.
    #
    # Some regex notes:
    # * re.sub() is faster than re.match() + str.join().
    # * We may be able to detect a large number of '@' symbols and then use
    #   a regex else use the present function.

    @timed(5)
    def test_log_sanitize_speed_many_url(self):
        self.module._heuristic_log_sanitize(self.many_url)

    @timed(5)
    def test_log_sanitize_speed_many_ssh(self):
        self.module._heuristic_log_sanitize(self.many_ssh)

    @timed(5)
    def test_log_sanitize_speed_one_url(self):
        self.module._heuristic_log_sanitize(self.one_url)

    @timed(5)
    def test_log_sanitize_speed_one_ssh(self):
        self.module._heuristic_log_sanitize(self.one_ssh)

    @timed(5)
    def test_log_sanitize_speed_zero_secrets(self):
        self.module._heuristic_log_sanitize(self.zero_secrets)

    #
    # Test that the password obfuscation sanitizes somewhat cleanly.
    #

    def test_log_sanitize_correctness(self):
        url_data = repr(self._gen_data(3, True, True, self.URL_SECRET))
        ssh_data = repr(self._gen_data(3, True, True, self.SSH_SECRET))

        url_output = self.module._heuristic_log_sanitize(url_data)
        ssh_output = self.module._heuristic_log_sanitize(ssh_data)

        # Basic functionality: Successfully hid the password
        try:
            self.assertNotIn('pas:word', url_output)
            self.assertNotIn('pas:word', ssh_output)

            # Slightly more advanced, we hid all of the password despite the ":"
            self.assertNotIn('pas', url_output)
            self.assertNotIn('pas', ssh_output)
        except AttributeError:
            # python2.6 or less's unittest
            self.assertFalse('pas:word' in url_output, '%s is present in %s' % ('"pas:word"', url_output))
            self.assertFalse('pas:word' in ssh_output, '%s is present in %s' % ('"pas:word"', ssh_output))

            self.assertFalse('pas' in url_output, '%s is present in %s' % ('"pas"', url_output))
            self.assertFalse('pas' in ssh_output, '%s is present in %s' % ('"pas"', ssh_output))

        # In this implementation we replace the password with 8 "*" which is
        # also the length of our password.  The url fields should be able to
        # accurately detect where the password ends so the length should be
        # the same:
        self.assertEqual(len(url_output), len(url_data))

        # ssh checking is harder as the heuristic is overzealous in many
        # cases.  Since the input will have at least one ":" present before
        # the password we can tell some things about the beginning and end of
        # the data, though:
        self.assertTrue(ssh_output.startswith("{'"))
        self.assertTrue(ssh_output.endswith("'}}}}"))
        try:
            self.assertIn(":********@foo.com/data',", ssh_output)
        except AttributeError:
            # python2.6 or less's unittest
            self.assertTrue(":********@foo.com/data'," in ssh_output, '%s is not present in %s' % (":********@foo.com/data',", ssh_output))

        # The overzealous-ness here may lead to us changing the algorithm in
        # the future.  We could make it consume less of the data (with the
        # possibility of leaving partial passwords exposed) and encourage
        # people to use no_log instead of relying on this obfuscation.
