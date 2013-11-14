
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

    def test_facter(self):
        if not get_binary("facter"):
            raise SkipTest
        result = self._run('facter', [])
        assert "hostname" in result

    # temporarily disbabled since it occasionally hangs
    # ohai's fault, setup module doesn't actually run this
    # to get ohai's "facts" anyway
    #
    #def test_ohai(self):
    #    if not get_binary("facter"):
    #            raise SkipTest
    #    result = self._run('ohai',[])
    #    assert "hostname" in result

    def test_copy(self):
        # test copy module, change trigger, etc
        input_ = self._get_test_file('sample.j2')
        output = self._get_stage_file('sample.out')
        assert not os.path.exists(output)
        result = self._run('copy', [
            "src=%s" % input_,
            "dest=%s" % output,
        ])
        assert os.path.exists(output)
        data_in = file(input_).read()
        data_out = file(output).read()
        assert data_in == data_out
        assert 'failed' not in result
        assert result['changed'] is True
        assert 'md5sum' in result
        result = self._run('copy', [
            "src=%s" % input_,
            "dest=%s" % output,
        ])
        assert result['changed'] is False
        with open(output, "a") as output_stream:
            output_stream.write("output file now differs from input")
        result = self._run('copy',
                           ["src=%s" % input_, "dest=%s" % output, "force=no"],
                           check_mode=True)
        assert result['changed'] is False

    def test_command(self):
        # test command module, change trigger, etc
        result = self._run('command', ["/bin/echo", "hi"])
        assert "failed" not in result
        assert "msg" not in result
        assert result['rc'] == 0
        assert result['stdout'] == 'hi'
        assert result['stderr'] == ''

        result = self._run('command', ["false"])
        assert result['rc'] == 1
        assert 'failed' not in result

        result = self._run('command', ["/usr/bin/this_does_not_exist", "splat"])
        assert 'msg' in result
        assert 'failed' in result

        result = self._run('shell', ["/bin/echo", "$HOME"])
        assert 'failed' not in result
        assert result['rc'] == 0

        result = self._run('command', ["creates='/tmp/ansible command test'", "chdir=/tmp", "touch", "'ansible command test'"])
        assert 'changed' in result
        assert result['rc'] == 0

        result = self._run('command', ["creates='/tmp/ansible command test'", "false"])
        assert 'skipped' in result

        result = self._run('shell', ["removes=/tmp/ansible\\ command\\ test", "chdir=/tmp", "rm -f 'ansible command test'; echo $?"])
        assert 'changed' in result
        assert result['rc'] == 0
        assert result['stdout'] == '0'

        result = self._run('shell', ["removes=/tmp/ansible\\ command\\ test", "false"])
        assert 'skipped' in result

    def test_git(self):
        self._run('file', ['path=/tmp/gitdemo', 'state=absent'])
        self._run('file', ['path=/tmp/gd', 'state=absent'])
        self._run('file', ['path=/tmp/gdbare', 'state=absent'])
        self._run('file', ['path=/tmp/gdreference', 'state=absent'])
        self._run('file', ['path=/tmp/gdreftest', 'state=absent'])
        self._run('command', ['git init gitdemo', 'chdir=/tmp'])
        self._run('command', ['touch a', 'chdir=/tmp/gitdemo'])
        self._run('command', ['git add *', 'chdir=/tmp/gitdemo'])
        self._run('command', ['git commit -m "test commit 1"', 'chdir=/tmp/gitdemo'])
        self._run('command', ['touch b', 'chdir=/tmp/gitdemo'])
        self._run('command', ['git add *', 'chdir=/tmp/gitdemo'])
        self._run('command', ['git commit -m "test commit 2"', 'chdir=/tmp/gitdemo'])
        result = self._run('git', ["repo=\"file:///tmp/gitdemo\"", "dest=/tmp/gd"])
        assert result['changed']
        # test the force option not set
        self._run('file', ['path=/tmp/gd/a', 'state=absent'])
        result = self._run('git', ["repo=\"file:///tmp/gitdemo\"", "dest=/tmp/gd", "force=no"])
        assert result['failed']
        # test the force option when set
        result = self._run('git', ["repo=\"file:///tmp/gitdemo\"", "dest=/tmp/gd", "force=yes"])
        assert result['changed']
        # test the bare option
        result = self._run('git', ["repo=\"file:///tmp/gitdemo\"", "dest=/tmp/gdbare", "bare=yes", "remote=test"])
        assert result['changed']
        # test a no-op fetch, add origin for el6 versions of git
        self._run('command', ['git remote add origin file:///tmp/gitdemo', 'chdir=/tmp/gdbare'])
        result = self._run('git', ["repo=\"file:///tmp/gitdemo\"", "dest=/tmp/gdbare", "bare=yes"])
        assert not result['changed']
        # test whether fetch is working for bare repos
        self._run('command', ['touch c', 'chdir=/tmp/gitdemo'])
        self._run('command', ['git add *', 'chdir=/tmp/gitdemo'])
        self._run('command', ['git commit -m "test commit 3"', 'chdir=/tmp/gitdemo'])
        result = self._run('git', ["repo=\"file:///tmp/gitdemo\"", "dest=/tmp/gdbare", "bare=yes"])
        assert result['changed']
        # test reference repos
        result = self._run('git', ["repo=\"file:///tmp/gdbare\"", "dest=/tmp/gdreference", "bare=yes"])
        assert result['changed']
        result = self._run('git', ["repo=\"file:///tmp/gitdemo\"", "dest=/tmp/gdreftest", "reference=/tmp/gdreference/"])
        assert result['changed']
        assert os.path.isfile('/tmp/gdreftest/a')
        result = self._run('command', ['ls', 'chdir=/tmp/gdreference/objects/pack'])
        assert result['stdout'] != ''
        result = self._run('command', ['ls', 'chdir=/tmp/gdreftest/.git/objects/pack'])
        assert result['stdout'] == ''

    def test_file(self):
        filedemo = tempfile.mkstemp()[1]
        assert self._run('file', ['dest=' + filedemo, 'state=directory'])['failed']
        assert os.path.isfile(filedemo)

        assert self._run('file', ['dest=' + filedemo, 'src=/dev/null', 'state=link'])['failed']
        assert os.path.isfile(filedemo)

        res = self._run('file', ['dest=' + filedemo, 'mode=604', 'state=file'])
        assert res['changed']
        assert os.path.isfile(filedemo) and os.stat(filedemo).st_mode == 0100604

        assert self._run('file', ['dest=' + filedemo, 'state=absent'])['changed']
        assert not os.path.exists(filedemo)
        assert not self._run('file', ['dest=' + filedemo, 'state=absent'])['changed']

        filedemo = tempfile.mkdtemp()
        assert self._run('file', ['dest=' + filedemo, 'state=file'])['failed']
        assert os.path.isdir(filedemo)

        # this used to fail but will now make a 'null' symlink in the directory pointing to dev/null.
        # I feel this is ok but don't want to enforce it with a test.
        #result = self._run('file', ['dest=' + filedemo, 'src=/dev/null', 'state=link'])
        #assert result['failed']
        #assert os.path.isdir(filedemo)

        assert self._run('file', ['dest=' + filedemo, 'mode=701', 'state=directory'])['changed']
        assert os.path.isdir(filedemo) and os.stat(filedemo).st_mode == 040701

        assert self._run('file', ['dest=' + filedemo, 'state=absent'])['changed']
        assert not os.path.exists(filedemo)
        assert not self._run('file', ['dest=' + filedemo, 'state=absent'])['changed']

        tmp_dir = tempfile.mkdtemp()
        filedemo = os.path.join(tmp_dir, 'link')
        os.symlink('/dev/zero', filedemo)
        assert self._run('file', ['dest=' + filedemo, 'state=file'])['failed']
        assert os.path.islink(filedemo)

        assert self._run('file', ['dest=' + filedemo, 'state=directory'])['failed']
        assert os.path.islink(filedemo)

        assert self._run('file', ['dest=' + filedemo, 'src=/dev/null', 'state=link'])['changed']
        assert os.path.islink(filedemo) and os.path.realpath(filedemo) == '/dev/null'

        assert self._run('file', ['dest=' + filedemo, 'state=absent'])['changed']
        assert not os.path.exists(filedemo)
        assert not self._run('file', ['dest=' + filedemo, 'state=absent'])['changed']

        # Make sure that we can deal safely with bad symlinks
        os.symlink('/tmp/non_existent_target', filedemo)
        assert self._run('file', ['dest=' + tmp_dir, 'state=directory recurse=yes mode=701'])['changed']
        assert not self._run('file', ['dest=' + tmp_dir, 'state=directory', 'recurse=yes', 'owner=' + str(os.getuid())])['changed']
        assert os.path.islink(filedemo)
        assert self._run('file', ['dest=' + filedemo, 'state=absent'])['changed']
        assert not os.path.exists(filedemo)
        os.rmdir(tmp_dir)

    def test_large_output(self):
        large_path = "/usr/share/dict/words"
        if not os.path.exists(large_path):
            large_path = "/usr/share/dict/cracklib-small"
            if not os.path.exists(large_path):
                raise SkipTest
        # Ensure reading a large amount of output from a command doesn't hang.
        result = self._run('command', ["/bin/cat", large_path])
        assert "failed" not in result
        assert "msg" not in result
        assert result['rc'] == 0
        assert len(result['stdout']) > 100000
        assert result['stderr'] == ''

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

    def test_fetch(self):
        input_ = self._get_test_file('sample.j2')
        output = os.path.join(self.stage_dir, 'localhost', input_)
        self._run('fetch', ["src=%s" % input_, "dest=%s" % self.stage_dir])
        assert os.path.exists(output)
        assert open(input_).read() == open(output).read()

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

    def test_lineinfile(self):
        # Unit tests for the lineinfile module, without backref features.
        sampleroot = 'rocannon'
        sample_origin = self._get_test_file(sampleroot + '.txt')
        sample = self._get_stage_file(sampleroot + '.out' + '.txt')
        shutil.copy(sample_origin, sample)
        # The order of the test cases is important

        # defaults to insertafter at the end of the file
        testline = 'First: Line added by default at the end of the file.'
        testcase = ('lineinfile', [
                    "dest=%s" % sample,
                    "regexp='^First: '",
                    "line='%s'" % testline
                    ])
        result = self._run(*testcase)
        assert result['changed']
        assert result['msg'] == 'line added'
        artifact = [x.strip() for x in open(sample)]
        assert artifact[-1] == testline
        assert artifact.count(testline) == 1

        # run a second time, verify only one line has been added
        result = self._run(*testcase)
        assert not result['changed']
        assert result['msg'] == ''
        artifact = [x.strip() for x in open(sample)]
        assert artifact.count(testline) == 1

        # insertafter with EOF
        testline = 'Second: Line added with insertafter=EOF'
        testcase = ('lineinfile', [
                    "dest=%s" % sample,
                    "insertafter=EOF",
                    "regexp='^Second: '",
                    "line='%s'" % testline
                    ])
        result = self._run(*testcase)
        assert result['changed']
        assert result['msg'] == 'line added'
        artifact = [x.strip() for x in open(sample)]
        assert artifact[-1] == testline
        assert artifact.count(testline) == 1

        # with invalid insertafter regex
        # If the regexp doesn't match and the insertafter doesn't match,
        # do nothing.
        testline = 'Third: Line added with an invalid insertafter regex'
        testcase = ('lineinfile', [
                    "dest=%s" % sample,
                    "insertafter='^abcdefgh'",
                    "regexp='^Third: '",
                    "line='%s'" % testline
                    ])
        result = self._run(*testcase)
        assert not result['changed']

        # with an insertafter regex
        # The regexp doesn't match, but the insertafter is specified and does,
        # so insert after insertafter.
        testline = 'Fourth: Line added with a valid insertafter regex'
        testcase = ('lineinfile', [
                    "dest=%s" % sample,
                    "insertafter='^receive messages to '",
                    "regexp='^Fourth: '",
                    "line='%s'" % testline
                    ])
        result = self._run(*testcase)
        assert result['changed']
        assert result['msg'] == 'line added'
        artifact = [x.strip() for x in open(sample)]
        assert artifact.count(testline) == 1
        idx = artifact.index('receive messages to and from a corresponding device over any distance')
        assert artifact[idx + 1] == testline

        # replacement of a line from a regex
        # we replace the line, so we need to get its idx before the run
        artifact = [x.strip() for x in open(sample)]
        target_line = 'combination of microphone, speaker, keyboard and display. It can send and'
        idx = artifact.index(target_line)

        testline = 'Fith: replacement of a line: combination of microphone'
        testcase = ('lineinfile', [
                    "dest=%s" % sample,
                    "regexp='combination of microphone'",
                    "line='%s'" % testline
                    ])
        result = self._run(*testcase)
        assert result['changed']
        assert result['msg'] == 'line replaced'
        artifact = [x.strip() for x in open(sample)]
        assert artifact.count(testline) == 1
        assert artifact.index(testline) == idx
        assert target_line not in artifact

        # removal of a line
        # we replace the line, so we need to get its idx before the run
        artifact = [x.strip() for x in open(sample)]
        target_line = 'receive messages to and from a corresponding device over any distance'
        idx = artifact.index(target_line)

        testcase = ('lineinfile', [
                    "dest=%s" % sample,
                    "regexp='^receive messages to and from '",
                    "state=absent"
                    ])
        result = self._run(*testcase)
        assert result['changed']
        artifact = [x.strip() for x in open(sample)]
        assert target_line not in artifact

        # with both insertafter and insertbefore (should fail)
        testline = 'Seventh: this line should not be there'
        testcase = ('lineinfile', [
                    "dest=%s" % sample,
                    "insertafter='BOF'",
                    "insertbefore='BOF'",
                    "regexp='^communication. '",
                    "line='%s'" % testline
                    ])
        result = self._run(*testcase)
        assert result['failed']

        # insertbefore with BOF
        testline = 'Eighth: insertbefore BOF'
        testcase = ('lineinfile', [
                    "dest=%s" % sample,
                    "insertbefore=BOF",
                    "regexp='^Eighth: '",
                    "line='%s'" % testline
                    ])
        result = self._run(*testcase)
        assert result['changed']
        assert result['msg'] == 'line added'
        artifact = [x.strip() for x in open(sample)]
        assert artifact.count(testline) == 1
        assert artifact[0] == testline

        # insertbefore with regex
        testline = 'Ninth: insertbefore with a regex'
        testcase = ('lineinfile', [
                    "dest=%s" % sample,
                    "insertbefore='^communication. Typically '",
                    "regexp='^Ninth: '",
                    "line='%s'" % testline
                    ])
        result = self._run(*testcase)
        assert result['changed']
        assert result['msg'] == 'line added'
        artifact = [x.strip() for x in open(sample)]
        assert artifact.count(testline) == 1
        idx = artifact.index('communication. Typically it is depicted as a lunch-box sized object with some')
        assert artifact[idx - 1] == testline

        # Testing validate
        testline = 'Tenth: Testing with validate'
        testcase = ('lineinfile', [
                        "dest=%s" % sample,
                        "regexp='^Tenth: '",
                        "line='%s'" % testline,
                        "validate='grep -q Tenth %s'",
                    ])
        result = self._run(*testcase)
        assert result['changed'], "File wasn't changed when it should have been"
        assert result['msg'] == 'line added', "msg was incorrect"
        artifact = [ x.strip() for x in open(sample) ]
        assert artifact[-1] == testline


        # Testing validate
        testline = '#11: Testing with validate'
        testcase = ('lineinfile', [
                        "dest=%s" % sample,
                        "regexp='^#11: '",
                        "line='%s'" % testline,
                        "validate='grep -q #12# %s'",
                    ])
        result = self._run(*testcase)
        assert result['failed']

        # cleanup
        os.unlink(sample)

    def test_lineinfile_backrefs(self):
        # Unit tests for the lineinfile module, with backref features.
        sampleroot = 'rocannon'
        sample_origin = self._get_test_file(sampleroot + '.txt')
        origin_lines = [line.strip() for line in open(sample_origin)]
        sample = self._get_stage_file(sampleroot + '.out' + '.txt')
        shutil.copy(sample_origin, sample)
        # The order of the test cases is important

        # The regexp doesn't match, so the line will not be added anywhere.
        testline = r'\1: Line added by default at the end of the file.'
        testcase = ('lineinfile', [
                    "dest=%s" % sample,
                    "regexp='^(First): '",
                    "line='%s'" % testline,
                    "backrefs=yes",
                    ])
        result = self._run(*testcase)
        assert not result['changed']
        assert result['msg'] == ''
        artifact = [x.strip() for x in open(sample)]
        assert artifact == origin_lines

        # insertafter with EOF
        # The regexp doesn't match, so the line will not be added anywhere.
        testline = r'\1: Line added with insertafter=EOF'
        testcase = ('lineinfile', [
                    "dest=%s" % sample,
                    "insertafter=EOF",
                    "regexp='^(Second): '",
                    "line='%s'" % testline,
                    "backrefs=yes",
                    ])
        result = self._run(*testcase)
        assert not result['changed']
        assert result['msg'] == ''
        artifact = [x.strip() for x in open(sample)]
        assert artifact == origin_lines

        # with invalid insertafter regex
        # The regexp doesn't match, so do nothing.
        testline = r'\1: Line added with an invalid insertafter regex'
        testcase = ('lineinfile', [
                    "dest=%s" % sample,
                    "insertafter='^abcdefgh'",
                    "regexp='^(Third): '",
                    "line='%s'" % testline,
                    "backrefs=yes",
                    ])
        result = self._run(*testcase)
        assert not result['changed']
        assert artifact == origin_lines

        # with an insertafter regex
        # The regexp doesn't match, so do nothing.
        testline = r'\1: Line added with a valid insertafter regex'
        testcase = ('lineinfile', [
                    "dest=%s" % sample,
                    "insertafter='^receive messages to '",
                    "regexp='^(Fourth): '",
                    "line='%s'" % testline,
                    "backrefs=yes",
                    ])
        result = self._run(*testcase)
        assert not result['changed']
        assert result['msg'] == ''
        assert artifact == origin_lines

        # replacement of a line from a regex
        # we replace the line, so we need to get its idx before the run
        artifact = [x.strip() for x in open(sample)]
        target_line = 'combination of microphone, speaker, keyboard and display. It can send and'
        idx = artifact.index(target_line)

        testline = r'\1 of megaphone'
        testline_after = 'combination of megaphone'
        testcase = ('lineinfile', [
                    "dest=%s" % sample,
                    "regexp='(combination) of microphone'",
                    "line='%s'" % testline,
                    "backrefs=yes",
                    ])
        result = self._run(*testcase)
        assert result['changed']
        assert result['msg'] == 'line replaced'
        artifact = [x.strip() for x in open(sample)]
        assert artifact.count(testline_after) == 1
        assert artifact.index(testline_after) == idx
        assert target_line not in artifact

        # Go again, should be unchanged now.
        testline = r'\1 of megaphone'
        testline_after = 'combination of megaphone'
        testcase = ('lineinfile', [
                    "dest=%s" % sample,
                    "regexp='(combination) of megaphone'",
                    "line='%s'" % testline,
                    "backrefs=yes",
                    ])
        result = self._run(*testcase)
        assert not result['changed']
        assert result['msg'] == ''

        # Try a numeric, named capture group example.
        f = open(sample, 'a+')
        f.write("1 + 1 = 3" + os.linesep)
        f.close()
        testline = r"2 + \g<num> = 3"
        testline_after = "2 + 1 = 3"
        testcase = ('lineinfile', [
                    "dest=%s" % sample,
                    r"regexp='1 \+ (?P<num>\d) = 3'",
                    "line='%s'" % testline,
                    "backrefs=yes",
                    ])
        result = self._run(*testcase)
        artifact = [x.strip() for x in open(sample)]
        assert result['changed']
        assert result['msg'] == 'line replaced'
        artifact = [x.strip() for x in open(sample)]
        assert '1 + 1 = 3' not in artifact
        assert testline_after == artifact[-1]

        # with both insertafter and insertbefore (should fail)
        testline = 'Seventh: this line should not be there'
        testcase = ('lineinfile', [
                    "dest=%s" % sample,
                    "insertafter='BOF'",
                    "insertbefore='BOF'",
                    "regexp='^communication. '",
                    "line='%s'" % testline
                    ])
        result = self._run(*testcase)
        assert result['failed']

        os.unlink(sample)
