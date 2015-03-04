# (C) 2012-2014, Michael DeHaan, <michael.dehaan@gmail.com>

# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

import utils
import sys
import getpass
import os
import subprocess
import random
import fnmatch
import tempfile
import fcntl
import constants
import locale
from ansible.color import stringc
from ansible.module_utils import basic
from ansible.utils.unicode import to_unicode, to_bytes

import logging
if constants.DEFAULT_LOG_PATH != '':
    path = constants.DEFAULT_LOG_PATH

    if (os.path.exists(path) and not os.access(path, os.W_OK)) and not os.access(os.path.dirname(path), os.W_OK):
        sys.stderr.write("log file at %s is not writeable, aborting\n" % path)
        sys.exit(1)


    logging.basicConfig(filename=path, level=logging.DEBUG, format='%(asctime)s %(name)s %(message)s')
    mypid = str(os.getpid())
    user = getpass.getuser()
    logger = logging.getLogger("p=%s u=%s | " % (mypid, user))

callback_plugins = []

def load_callback_plugins():
    global callback_plugins
    callback_plugins = [x for x in utils.plugins.callback_loader.all()]

def get_cowsay_info():
    if constants.ANSIBLE_NOCOWS:
        return (None, None)
    cowsay = None
    if os.path.exists("/usr/bin/cowsay"):
        cowsay = "/usr/bin/cowsay"
    elif os.path.exists("/usr/games/cowsay"):
        cowsay = "/usr/games/cowsay"
    elif os.path.exists("/usr/local/bin/cowsay"):
        # BSD path for cowsay
        cowsay = "/usr/local/bin/cowsay"
    elif os.path.exists("/opt/local/bin/cowsay"):
        # MacPorts path for cowsay
        cowsay = "/opt/local/bin/cowsay"

    noncow = os.getenv("ANSIBLE_COW_SELECTION",None)
    if cowsay and noncow == 'random':
        cmd = subprocess.Popen([cowsay, "-l"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        (out, err) = cmd.communicate()
        cows = out.split()
        cows.append(False)
        noncow = random.choice(cows)
    return (cowsay, noncow)

cowsay, noncow = get_cowsay_info()

def log_lockfile():
    # create the path for the lockfile and open it
    tempdir = tempfile.gettempdir()
    uid = os.getuid()
    path = os.path.join(tempdir, ".ansible-lock.%s" % uid)
    lockfile = open(path, 'w')
    # use fcntl to set FD_CLOEXEC on the file descriptor, 
    # so that we don't leak the file descriptor later
    lockfile_fd = lockfile.fileno()
    old_flags = fcntl.fcntl(lockfile_fd, fcntl.F_GETFD)
    fcntl.fcntl(lockfile_fd, fcntl.F_SETFD, old_flags | fcntl.FD_CLOEXEC)
    return lockfile
    
LOG_LOCK = log_lockfile()

def log_flock(runner):
    if runner is not None:
        try:
            fcntl.lockf(runner.output_lockfile, fcntl.LOCK_EX)
        except OSError:
            # already got closed?
            pass
    else:
        try:
            fcntl.lockf(LOG_LOCK, fcntl.LOCK_EX)
        except OSError:
            pass


def log_unflock(runner):
    if runner is not None:
        try:
            fcntl.lockf(runner.output_lockfile, fcntl.LOCK_UN)
        except OSError:
            # already got closed?
            pass
    else:
        try:
            fcntl.lockf(LOG_LOCK, fcntl.LOCK_UN)
        except OSError:
            pass

def set_playbook(callback, playbook):
    ''' used to notify callback plugins of playbook context '''
    callback.playbook = playbook
    for callback_plugin in callback_plugins:
        callback_plugin.playbook = playbook

def set_play(callback, play):
    ''' used to notify callback plugins of context '''
    callback.play = play
    for callback_plugin in callback_plugins:
        callback_plugin.play = play

def set_task(callback, task):
    ''' used to notify callback plugins of context '''
    callback.task = task
    for callback_plugin in callback_plugins:
        callback_plugin.task = task

def display(msg, color=None, stderr=False, screen_only=False, log_only=False, runner=None):
    # prevent a very rare case of interlaced multiprocess I/O
    log_flock(runner)
    msg2 = msg
    if color:
        msg2 = stringc(msg, color)
    if not log_only:
        if not stderr:
            try:
                print msg2
            except UnicodeEncodeError:
                print msg2.encode('utf-8')
        else:
            try:
                print >>sys.stderr, msg2
            except UnicodeEncodeError:
                print >>sys.stderr, msg2.encode('utf-8')
    if constants.DEFAULT_LOG_PATH != '':
        while msg.startswith("\n"):
            msg = msg.replace("\n","")
        if not screen_only:
            if color == 'red':
                logger.error(msg)
            else:
                logger.info(msg)
    log_unflock(runner)

def call_callback_module(method_name, *args, **kwargs):

    for callback_plugin in callback_plugins:
        # a plugin that set self.disabled to True will not be called
        # see osx_say.py example for such a plugin
        if getattr(callback_plugin, 'disabled', False):
            continue
        methods = [
            getattr(callback_plugin, method_name, None),
            getattr(callback_plugin, 'on_any', None)
        ]
        for method in methods:
            if method is not None:
                method(*args, **kwargs)

def vv(msg, host=None):
    return verbose(msg, host=host, caplevel=1)

def vvv(msg, host=None):
    return verbose(msg, host=host, caplevel=2)

def vvvv(msg, host=None):
    return verbose(msg, host=host, caplevel=3)

def verbose(msg, host=None, caplevel=2):
    msg = utils.sanitize_output(msg)
    if utils.VERBOSITY > caplevel:
        if host is None:
            display(msg, color='blue')
        else:
            display("<%s> %s" % (host, msg), color='blue')

class AggregateStats(object):
    ''' holds stats about per-host activity during playbook runs '''

    def __init__(self):

        self.processed   = {}
        self.failures    = {}
        self.ok          = {}
        self.dark        = {}
        self.changed     = {}
        self.skipped     = {}

    def _increment(self, what, host):
        ''' helper function to bump a statistic '''

        self.processed[host] = 1
        prev = (getattr(self, what)).get(host, 0)
        getattr(self, what)[host] = prev+1

    def compute(self, runner_results, setup=False, poll=False, ignore_errors=False):
        ''' walk through all results and increment stats '''

        for (host, value) in runner_results.get('contacted', {}).iteritems():
            if not ignore_errors and (('failed' in value and bool(value['failed'])) or
                ('failed_when_result' in value and [value['failed_when_result']] or ['rc' in value and value['rc'] != 0])[0]):
                self._increment('failures', host)
            elif 'skipped' in value and bool(value['skipped']):
                self._increment('skipped', host)
            elif 'changed' in value and bool(value['changed']):
                if not setup and not poll:
                    self._increment('changed', host)
                self._increment('ok', host)
            else:
                if not poll or ('finished' in value and bool(value['finished'])):
                    self._increment('ok', host)

        for (host, value) in runner_results.get('dark', {}).iteritems():
            self._increment('dark', host)


    def summarize(self, host):
        ''' return information about a particular host '''

        return dict(
            ok          = self.ok.get(host, 0),
            failures    = self.failures.get(host, 0),
            unreachable = self.dark.get(host,0),
            changed     = self.changed.get(host, 0),
            skipped     = self.skipped.get(host, 0)
        )

########################################################################

def regular_generic_msg(hostname, result, oneline, caption):
    ''' output on the result of a module run that is not command '''

    if not oneline:
        return "%s | %s >> %s\n" % (hostname, caption, utils.jsonify(result,format=True))
    else:
        return "%s | %s >> %s\n" % (hostname, caption, utils.jsonify(result))


def banner_cowsay(msg):

    if ": [" in msg:
        msg = msg.replace("[","")
        if msg.endswith("]"):
            msg = msg[:-1]
    runcmd = [cowsay,"-W", "60"]
    if noncow:
        runcmd.append('-f')
        runcmd.append(noncow)
    runcmd.append(msg)
    cmd = subprocess.Popen(runcmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (out, err) = cmd.communicate()
    return "%s\n" % out

def banner_normal(msg):

    width = 78 - len(msg)
    if width < 3:
        width = 3
    filler = "*" * width
    return "\n%s %s " % (msg, filler)

def banner(msg):
    if cowsay:
        try:
            return banner_cowsay(msg)
        except OSError:
            # somebody cleverly deleted cowsay or something during the PB run.  heh.
            return banner_normal(msg)
    return banner_normal(msg)

def command_generic_msg(hostname, result, oneline, caption):
    ''' output the result of a command run '''

    rc     = result.get('rc', '0')
    stdout = result.get('stdout','')
    stderr = result.get('stderr', '')
    msg    = result.get('msg', '')

    hostname = hostname.encode('utf-8')
    caption  = caption.encode('utf-8')

    if not oneline:
        buf = "%s | %s | rc=%s >>\n" % (hostname, caption, result.get('rc',0))
        if stdout:
            buf += stdout
        if stderr:
            buf += stderr
        if msg:
            buf += msg
        return buf + "\n"
    else:
        if stderr:
            return "%s | %s | rc=%s | (stdout) %s (stderr) %s" % (hostname, caption, rc, stdout, stderr)
        else:
            return "%s | %s | rc=%s | (stdout) %s" % (hostname, caption, rc, stdout)

def host_report_msg(hostname, module_name, result, oneline):
    ''' summarize the JSON results for a particular host '''

    failed = utils.is_failed(result)
    msg = ('', None)
    if module_name in [ 'command', 'shell', 'raw' ] and 'ansible_job_id' not in result and result.get('parsed',True) != False:
        if not failed:
            msg = (command_generic_msg(hostname, result, oneline, 'success'), 'green')
        else:
            msg = (command_generic_msg(hostname, result, oneline, 'FAILED'), 'red')
    else:
        if not failed:
            msg = (regular_generic_msg(hostname, result, oneline, 'success'), 'green')
        else:
            msg = (regular_generic_msg(hostname, result, oneline, 'FAILED'), 'red')
    return msg

###############################################

class DefaultRunnerCallbacks(object):
    ''' no-op callbacks for API usage of Runner() if no callbacks are specified '''

    def __init__(self):
        pass

    def on_failed(self, host, res, ignore_errors=False):
        call_callback_module('runner_on_failed', host, res, ignore_errors=ignore_errors)

    def on_ok(self, host, res):
        call_callback_module('runner_on_ok', host, res)

    def on_skipped(self, host, item=None):
        call_callback_module('runner_on_skipped', host, item=item)

    def on_unreachable(self, host, res):
        call_callback_module('runner_on_unreachable', host, res)

    def on_no_hosts(self):
        call_callback_module('runner_on_no_hosts')

    def on_async_poll(self, host, res, jid, clock):
        call_callback_module('runner_on_async_poll', host, res, jid, clock)

    def on_async_ok(self, host, res, jid):
        call_callback_module('runner_on_async_ok', host, res, jid)

    def on_async_failed(self, host, res, jid):
        call_callback_module('runner_on_async_failed', host, res, jid)

    def on_file_diff(self, host, diff):
        call_callback_module('runner_on_file_diff', host, diff)

########################################################################

class CliRunnerCallbacks(DefaultRunnerCallbacks):
    ''' callbacks for use by /usr/bin/ansible '''

    def __init__(self):
        # set by /usr/bin/ansible later
        self.options = None
        self._async_notified = {}

    def on_failed(self, host, res, ignore_errors=False):
        self._on_any(host,res)
        super(CliRunnerCallbacks, self).on_failed(host, res, ignore_errors=ignore_errors)

    def on_ok(self, host, res):
        # hide magic variables used for ansible-playbook
        res.pop('verbose_override', None)
        res.pop('verbose_always', None)

        self._on_any(host,res)
        super(CliRunnerCallbacks, self).on_ok(host, res)

    def on_unreachable(self, host, res):
        if type(res) == dict:
            res = res.get('msg','')
        display("%s | FAILED => %s" % (host, res), stderr=True, color='red', runner=self.runner)
        if self.options.tree:
            utils.write_tree_file(
                self.options.tree, host,
                utils.jsonify(dict(failed=True, msg=res),format=True)
            )
        super(CliRunnerCallbacks, self).on_unreachable(host, res)

    def on_skipped(self, host, item=None):
        display("%s | skipped" % (host), runner=self.runner)
        super(CliRunnerCallbacks, self).on_skipped(host, item)

    def on_no_hosts(self):
        display("no hosts matched\n", stderr=True, runner=self.runner)
        super(CliRunnerCallbacks, self).on_no_hosts()

    def on_async_poll(self, host, res, jid, clock):
        if jid not in self._async_notified:
            self._async_notified[jid] = clock + 1
        if self._async_notified[jid] > clock:
            self._async_notified[jid] = clock
            display("<job %s> polling on %s, %ss remaining" % (jid, host, clock), runner=self.runner)
        super(CliRunnerCallbacks, self).on_async_poll(host, res, jid, clock)

    def on_async_ok(self, host, res, jid):
        if jid:
            display("<job %s> finished on %s => %s"%(jid, host, utils.jsonify(res,format=True)), runner=self.runner)
        super(CliRunnerCallbacks, self).on_async_ok(host, res, jid)

    def on_async_failed(self, host, res, jid):
        display("<job %s> FAILED on %s => %s"%(jid, host, utils.jsonify(res,format=True)), color='red', stderr=True, runner=self.runner)
        super(CliRunnerCallbacks, self).on_async_failed(host,res,jid)

    def _on_any(self, host, result):
        result2 = result.copy()
        result2.pop('invocation', None)
        (msg, color) = host_report_msg(host, self.options.module_name, result2, self.options.one_line)
        display(msg, color=color, runner=self.runner)
        if self.options.tree:
            utils.write_tree_file(self.options.tree, host, utils.jsonify(result2,format=True))

    def on_file_diff(self, host, diff):
        display(utils.get_diff(diff), runner=self.runner)
        super(CliRunnerCallbacks, self).on_file_diff(host, diff)

########################################################################

class PlaybookRunnerCallbacks(DefaultRunnerCallbacks):
    ''' callbacks used for Runner() from /usr/bin/ansible-playbook '''

    def __init__(self, stats, verbose=None):

        if verbose is None:
            verbose = utils.VERBOSITY

        self.verbose = verbose
        self.stats = stats
        self._async_notified = {}

    def on_unreachable(self, host, results):
        if self.runner.delegate_to:
            host = '%s -> %s' % (host, self.runner.delegate_to)

        item = None
        if type(results) == dict:
            item = results.get('item', None)
            if isinstance(item, unicode):
                item = utils.unicode.to_bytes(item)
            results = basic.json_dict_unicode_to_bytes(results)
        else:
            results = utils.unicode.to_bytes(results)
        host = utils.unicode.to_bytes(host)
        if item:
            msg = "fatal: [%s] => (item=%s) => %s" % (host, item, results)
        else:
            msg = "fatal: [%s] => %s" % (host, results)
        display(msg, color='red', runner=self.runner)
        super(PlaybookRunnerCallbacks, self).on_unreachable(host, results)

    def on_failed(self, host, results, ignore_errors=False):
        if self.runner.delegate_to:
            host = '%s -> %s' % (host, self.runner.delegate_to)

        results2 = results.copy()
        results2.pop('invocation', None)

        item = results2.get('item', None)
        parsed = results2.get('parsed', True)
        module_msg = ''
        if not parsed:
            module_msg  = results2.pop('msg', None)
        stderr = results2.pop('stderr', None)
        stdout = results2.pop('stdout', None)
        returned_msg = results2.pop('msg', None)

        if item:
            msg = "failed: [%s] => (item=%s) => %s" % (host, item, utils.jsonify(results2))
        else:
            msg = "failed: [%s] => %s" % (host, utils.jsonify(results2))
        display(msg, color='red', runner=self.runner)

        if stderr:
            display("stderr: %s" % stderr, color='red', runner=self.runner)
        if stdout:
            display("stdout: %s" % stdout, color='red', runner=self.runner)
        if returned_msg:
            display("msg: %s" % returned_msg, color='red', runner=self.runner)
        if not parsed and module_msg:
            display(module_msg, color='red', runner=self.runner)
        if ignore_errors:
            display("...ignoring", color='cyan', runner=self.runner)
        super(PlaybookRunnerCallbacks, self).on_failed(host, results, ignore_errors=ignore_errors)

    def on_ok(self, host, host_result):
        if self.runner.delegate_to:
            host = '%s -> %s' % (host, self.runner.delegate_to)

        item = host_result.get('item', None)

        host_result2 = host_result.copy()
        host_result2.pop('invocation', None)
        verbose_always = host_result2.pop('verbose_always', False)
        changed = host_result.get('changed', False)
        ok_or_changed = 'ok'
        if changed:
            ok_or_changed = 'changed'

        # show verbose output for non-setup module results if --verbose is used
        msg = ''
        if (not self.verbose or host_result2.get("verbose_override",None) is not
                None) and not verbose_always:
            if item:
                msg = "%s: [%s] => (item=%s)" % (ok_or_changed, host, item)
            else:
                if 'ansible_job_id' not in host_result or 'finished' in host_result:
                    msg = "%s: [%s]" % (ok_or_changed, host)
        else:
            # verbose ...
            if item:
                msg = "%s: [%s] => (item=%s) => %s" % (ok_or_changed, host, item, utils.jsonify(host_result2, format=verbose_always))
            else:
                if 'ansible_job_id' not in host_result or 'finished' in host_result2:
                    msg = "%s: [%s] => %s" % (ok_or_changed, host, utils.jsonify(host_result2, format=verbose_always))

        if msg != '':
            if not changed:
                display(msg, color='green', runner=self.runner)
            else:
                display(msg, color='yellow', runner=self.runner)
        if constants.COMMAND_WARNINGS and 'warnings' in host_result2 and host_result2['warnings']:
            for warning in host_result2['warnings']:
                display("warning: %s" % warning, color='purple', runner=self.runner)
        super(PlaybookRunnerCallbacks, self).on_ok(host, host_result)

    def on_skipped(self, host, item=None):
        if self.runner.delegate_to:
            host = '%s -> %s' % (host, self.runner.delegate_to)

        if constants.DISPLAY_SKIPPED_HOSTS:
            msg = ''
            if item:
                msg = "skipping: [%s] => (item=%s)" % (host, item)
            else:
                msg = "skipping: [%s]" % host
            display(msg, color='cyan', runner=self.runner)
            super(PlaybookRunnerCallbacks, self).on_skipped(host, item)

    def on_no_hosts(self):
        display("FATAL: no hosts matched or all hosts have already failed -- aborting\n", color='red', runner=self.runner)
        super(PlaybookRunnerCallbacks, self).on_no_hosts()

    def on_async_poll(self, host, res, jid, clock):
        if jid not in self._async_notified:
            self._async_notified[jid] = clock + 1
        if self._async_notified[jid] > clock:
            self._async_notified[jid] = clock
            msg = "<job %s> polling, %ss remaining"%(jid, clock)
            display(msg, color='cyan', runner=self.runner)
        super(PlaybookRunnerCallbacks, self).on_async_poll(host,res,jid,clock)

    def on_async_ok(self, host, res, jid):
        if jid:
            msg = "<job %s> finished on %s"%(jid, host)
            display(msg, color='cyan', runner=self.runner)
        super(PlaybookRunnerCallbacks, self).on_async_ok(host, res, jid)

    def on_async_failed(self, host, res, jid):
        msg = "<job %s> FAILED on %s" % (jid, host)
        display(msg, color='red', stderr=True, runner=self.runner)
        super(PlaybookRunnerCallbacks, self).on_async_failed(host,res,jid)

    def on_file_diff(self, host, diff):
        display(utils.get_diff(diff), runner=self.runner)
        super(PlaybookRunnerCallbacks, self).on_file_diff(host, diff)

########################################################################

class PlaybookCallbacks(object):
    ''' playbook.py callbacks used by /usr/bin/ansible-playbook '''

    def __init__(self, verbose=False):

        self.verbose = verbose

    def on_start(self):
        call_callback_module('playbook_on_start')

    def on_notify(self, host, handler):
        call_callback_module('playbook_on_notify', host, handler)

    def on_no_hosts_matched(self):
        display("skipping: no hosts matched", color='cyan')
        call_callback_module('playbook_on_no_hosts_matched')

    def on_no_hosts_remaining(self):
        display("\nFATAL: all hosts have already failed -- aborting", color='red')
        call_callback_module('playbook_on_no_hosts_remaining')

    def on_task_start(self, name, is_conditional):
        name = utils.unicode.to_bytes(name)
        msg = "TASK: [%s]" % name
        if is_conditional:
            msg = "NOTIFIED: [%s]" % name

        if hasattr(self, 'start_at'):
            self.start_at = utils.unicode.to_bytes(self.start_at)
            if name == self.start_at or fnmatch.fnmatch(name, self.start_at):
                # we found out match, we can get rid of this now
                del self.start_at
            elif self.task.role_name:
                # handle tasks prefixed with rolenames
                actual_name = name.split('|', 1)[1].lstrip()
                if actual_name == self.start_at or fnmatch.fnmatch(actual_name, self.start_at):
                    del self.start_at

        if hasattr(self, 'start_at'): # we still have start_at so skip the task
            self.skip_task = True
        elif hasattr(self, 'step') and self.step:
            if isinstance(name, str):
                name = utils.unicode.to_unicode(name)
            msg = u'Perform task: %s (y/n/c): ' % name
            if sys.stdout.encoding:
                msg = to_bytes(msg, sys.stdout.encoding)
            else:
                msg = to_bytes(msg)
            resp = raw_input(msg)
            if resp.lower() in ['y','yes']:
                self.skip_task = False
                display(banner(msg))
            elif resp.lower() in ['c', 'continue']:
                self.skip_task = False
                self.step = False
                display(banner(msg))
            else:
                self.skip_task = True
        else:
            self.skip_task = False
            display(banner(msg))

        call_callback_module('playbook_on_task_start', name, is_conditional)

    def on_vars_prompt(self, varname, private=True, prompt=None, encrypt=None, confirm=False, salt_size=None, salt=None, default=None):

        if prompt and default is not None:
            msg = "%s [%s]: " % (prompt, default)
        elif prompt:
            msg = "%s: " % prompt
        else:
            msg = 'input for %s: ' % varname

        def do_prompt(prompt, private):
            if sys.stdout.encoding:
                msg = prompt.encode(sys.stdout.encoding)
            else:
                # when piping the output, or at other times when stdout
                # may not be the standard file descriptor, the stdout
                # encoding may not be set, so default to something sane
                msg = prompt.encode(locale.getpreferredencoding())
            if private:
                return getpass.getpass(msg)
            return raw_input(msg)


        if confirm:
            while True:
                result = do_prompt(msg, private)
                second = do_prompt("confirm " + msg, private)
                if result == second:
                    break
                display("***** VALUES ENTERED DO NOT MATCH ****")
        else:
            result = do_prompt(msg, private)

        # if result is false and default is not None
        if not result and default is not None:
            result = default


        if encrypt:
            result = utils.do_encrypt(result, encrypt, salt_size, salt)

        # handle utf-8 chars
        result = to_unicode(result, errors='strict')
        call_callback_module( 'playbook_on_vars_prompt', varname, private=private, prompt=prompt,
                               encrypt=encrypt, confirm=confirm, salt_size=salt_size, salt=None, default=default
                            )

        return result

    def on_setup(self):
        display(banner("GATHERING FACTS"))
        call_callback_module('playbook_on_setup')

    def on_import_for_host(self, host, imported_file):
        msg = "%s: importing %s" % (host, imported_file)
        display(msg, color='cyan')
        call_callback_module('playbook_on_import_for_host', host, imported_file)

    def on_not_import_for_host(self, host, missing_file):
        msg = "%s: not importing file: %s" % (host, missing_file)
        display(msg, color='cyan')
        call_callback_module('playbook_on_not_import_for_host', host, missing_file)

    def on_play_start(self, name):
        display(banner("PLAY [%s]" % name))
        call_callback_module('playbook_on_play_start', name)

    def on_stats(self, stats):
        call_callback_module('playbook_on_stats', stats)


