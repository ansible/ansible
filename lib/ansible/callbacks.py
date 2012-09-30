# (C) 2012, Michael DeHaan, <michael.dehaan@gmail.com>

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
import os.path
from ansible.color import stringc

dirname = os.path.dirname(__file__)
callbacks = utils.import_plugins(os.path.join(dirname, 'callback_plugins'))
callbacks = [ c.CallbackModule() for c in callbacks.values() ]

cowsay = None
if os.path.exists("/usr/bin/cowsay"):
    cowsay = "/usr/bin/cowsay"
elif os.path.exists("/usr/games/cowsay"):
    cowsay = "/usr/games/cowsay"

def call_callback_module(method_name, *args, **kwargs):
   
    for callback_plugin in callbacks:
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

def verbose(msg, host=None, caplevel=2):
    if utils.VERBOSITY > caplevel:
        if host is None:
            print stringc(msg, 'blue')
        else:
            print stringc("<%s> %s" % (host, msg), 'blue')

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
                ('rc' in value and value['rc'] != 0)):
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


def banner(msg):

    if cowsay != None:
        cmd = subprocess.Popen([cowsay, "-W", "60", msg],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        (out, err) = cmd.communicate()
        return "%s\n" % out
    else:
        return "\n%s ********************* " % msg

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
            return "%s | %s | rc=%s | (stdout) %s (stderr) %s\n" % (hostname, caption, rc, stdout, stderr)
        else:
            return "%s | %s | rc=%s | (stdout) %s\n" % (hostname, caption, rc, stdout)

def host_report_msg(hostname, module_name, result, oneline):
    ''' summarize the JSON results for a particular host '''

    failed = utils.is_failed(result)
    msg = ''
    if module_name in [ 'command', 'shell', 'raw' ] and 'ansible_job_id' not in result and result.get('parsed',True) != False:
        if not failed:
            msg = command_generic_msg(hostname, result, oneline, 'success')
        else:
            msg = command_generic_msg(hostname, result, oneline, 'FAILED')
    else:
        if not failed:
            msg = regular_generic_msg(hostname, result, oneline, 'success')
        else:
            msg = regular_generic_msg(hostname, result, oneline, 'FAILED')
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

    def on_error(self, host, msg):
        call_callback_module('runner_on_error', host, msg)

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
        self._on_any(host,res)
        super(CliRunnerCallbacks, self).on_ok(host, res)

    def on_unreachable(self, host, res):
        if type(res) == dict:
            res = res.get('msg','')
        print "%s | FAILED => %s" % (host, res)
        if self.options.tree:
            utils.write_tree_file(
                self.options.tree, host,
                utils.jsonify(dict(failed=True, msg=res),format=True)
            )
        super(CliRunnerCallbacks, self).on_unreachable(host, res)

    def on_skipped(self, host, item=None):
        print "%s | skipped" % (host)
        super(CliRunnerCallbacks, self).on_skipped(host, item)

    def on_error(self, host, err):
        print >>sys.stderr, "err: [%s] => %s\n" % (host, err)
        super(CliRunnerCallbacks, self).on_error(host, err)

    def on_no_hosts(self):
        print >>sys.stderr, "no hosts matched\n"
        super(CliRunnerCallbacks, self).on_no_hosts()

    def on_async_poll(self, host, res, jid, clock):
        if jid not in self._async_notified:
            self._async_notified[jid] = clock + 1
        if self._async_notified[jid] > clock:
            self._async_notified[jid] = clock
            print "<job %s> polling, %ss remaining"%(jid, clock)
        super(CliRunnerCallbacks, self).on_async_poll(host, res, jid, clock)

    def on_async_ok(self, host, res, jid):
        print "<job %s> finished on %s => %s"%(jid, host, utils.jsonify(res,format=True))
        super(CliRunnerCallbacks, self).on_async_ok(host, res, jid)

    def on_async_failed(self, host, res, jid):
        print "<job %s> FAILED on %s => %s"%(jid, host, utils.jsonify(res,format=True))
        super(CliRunnerCallbacks, self).on_async_failed(host,res,jid)

    def _on_any(self, host, result):
        result2 = result.copy()
        result2.pop('invocation', None)
        print host_report_msg(host, self.options.module_name, result2, self.options.one_line)
        if self.options.tree:
            utils.write_tree_file(self.options.tree, host, utils.jsonify(result2,format=True))

########################################################################

class PlaybookRunnerCallbacks(DefaultRunnerCallbacks):
    ''' callbacks used for Runner() from /usr/bin/ansible-playbook '''

    def __init__(self, stats, verbose=utils.VERBOSITY):
        self.verbose = verbose
        self.stats = stats
        self._async_notified = {}

    def on_unreachable(self, host, msg):
        item = None
        if type(msg) == dict:
            item = msg.get('item', None)
        if item:
            print "fatal: [%s] => (item=%s) => %s" % (host, item, msg)
        else:
            print "fatal: [%s] => %s" % (host, msg)
        super(PlaybookRunnerCallbacks, self).on_unreachable(host, msg)

    def on_failed(self, host, results, ignore_errors=False):

        results2 = results.copy()
        results2.pop('invocation', None)

        item = results2.get('item', None)
        parsed = results2.get('parsed', True)
        module_msg = ''
        if not parsed:
            module_msg  = results2.pop('msg', None)
        stderr = results2.pop('stderr', None)
        stdout = results2.pop('stdout', None)

        if item:
            msg = "failed: [%s] => (item=%s) => %s" % (host, item, utils.jsonify(results2))
        else:
            msg = "failed: [%s] => %s" % (host, utils.jsonify(results2))
        print stringc(msg, 'red')

        if stderr:
            print stringc("stderr: %s" % stderr, 'red')
        if stdout:
            print stringc("stdout: %s" % stdout, 'red')
        if not parsed and module_msg:
            print stringc("invalid output was: %s" % module_msg, 'red')
        if ignore_errors:
            print stringc("...ignoring", 'yellow')
        super(PlaybookRunnerCallbacks, self).on_failed(host, results, ignore_errors=ignore_errors)

    def on_ok(self, host, host_result):
        item = host_result.get('item', None)

        host_result2 = host_result.copy()
        host_result2.pop('invocation', None)
        changed = host_result.get('changed', False)
        ok_or_changed = 'ok'
        if changed:
            ok_or_changed = 'changed'

        # show verbose output for non-setup module results if --verbose is used
        msg = ''
        if not self.verbose or host_result2.get("verbose_override",None) is not None:
            if item:
                msg = "%s: [%s] => (item=%s)" % (ok_or_changed, host, item)
            else:
                if 'ansible_job_id' not in host_result or 'finished' in host_result:
                    msg = "%s: [%s]" % (ok_or_changed, host)
        else:
            # verbose ...
            if item:
                msg = "%s: [%s] => (item=%s) => %s" % (ok_or_changed, host, item, utils.jsonify(host_result2))
            else:
                if 'ansible_job_id' not in host_result or 'finished' in host_result2:
                    msg = "%s: [%s] => %s" % (ok_or_changed, host, utils.jsonify(host_result2))

        if msg != '':
            if not changed:
                print stringc(msg, 'green')
            else:
                print stringc(msg, 'yellow')
        super(PlaybookRunnerCallbacks, self).on_ok(host, host_result)

    def on_error(self, host, err):

        item = err.get('item', None)
        msg = ''
        if item:
            msg = "err: [%s] => (item=%s) => %s" % (host, item, err)
        else:
            msg = "err: [%s] => %s" % (host, err)

        msg = stringc(msg, 'red')
        print >>sys.stderr, msg
        super(PlaybookRunnerCallbacks, self).on_error(host, err)

    def on_skipped(self, host, item=None):
        msg = ''
        if item:
            msg = "skipping: [%s] => (item=%s)" % (host, item)
        else:
            msg = "skipping: [%s]" % host
        print stringc(msg, 'yellow')
        super(PlaybookRunnerCallbacks, self).on_skipped(host, item)

    def on_no_hosts(self):
        print stringc("no hosts matched or remaining\n", 'red')
        super(PlaybookRunnerCallbacks, self).on_no_hosts()

    def on_async_poll(self, host, res, jid, clock):
        if jid not in self._async_notified:
            self._async_notified[jid] = clock + 1
        if self._async_notified[jid] > clock:
            self._async_notified[jid] = clock
            msg = "<job %s> polling, %ss remaining"%(jid, clock)
            print stringc(msg, 'cyan')
        super(PlaybookRunnerCallbacks, self).on_async_poll(host,res,jid,clock)

    def on_async_ok(self, host, res, jid):
        msg = "<job %s> finished on %s"%(jid, host)
        print stringc(msg, 'cyan')
        super(PlaybookRunnerCallbacks, self).on_async_ok(host, res, jid)

    def on_async_failed(self, host, res, jid):
        msg = "<job %s> FAILED on %s"%(jid, host)
        print stringc(msg, 'red')
        super(PlaybookRunnerCallbacks, self).on_async_failed(host,res,jid)


########################################################################

class PlaybookCallbacks(object):
    ''' playbook.py callbacks used by /usr/bin/ansible-playbook '''

    def __init__(self, verbose=False):

        self.verbose = verbose

    def on_start(self):
        call_callback_module('playbook_on_start')

    def on_notify(self, host, handler):
        call_callback_module('playbook_on_notify', host, handler)

    def on_task_start(self, name, is_conditional):
        msg = "TASK: [%s]" % name
        if is_conditional:
            msg = "NOTIFIED: [%s]" % name
        print banner(msg)
        call_callback_module('playbook_on_task_start', name, is_conditional)

    def on_vars_prompt(self, varname, private=True, prompt=None, encrypt=None, confirm=False, salt_size=None, salt=None):

        if prompt:
            msg = prompt
        else:
            msg = 'input for %s: ' % varname

        def prompt(prompt, private):
            if private:
                return getpass.getpass(prompt)
            return raw_input(prompt)


        if confirm:
            while True:
                result = prompt(msg, private)
                second = prompt("confirm " + msg, private)
                if result == second: 
                    break
                print "***** VALUES ENTERED DO NOT MATCH ****"
        else:
            result = prompt(msg, private)

        if encrypt:
            result = utils.do_encrypt(result,encrypt,salt_size,salt)

        call_callback_module('playbook_on_vars_prompt', varname, private=private, prompt=prompt, encrypt=encrypt, confirm=confirm, salt_size=salt_size, salt=None)

        return result

    def on_setup(self):
        print banner("GATHERING FACTS")
        call_callback_module('playbook_on_setup')

    def on_import_for_host(self, host, imported_file):
        msg = "%s: importing %s" % (host, imported_file)
        print stringc(msg, 'cyan')
        call_callback_module('playbook_on_import_for_host', host, imported_file)

    def on_not_import_for_host(self, host, missing_file):
        msg = "%s: not importing file: %s" % (host, missing_file)
        print stringc(msg, 'cyan')
        call_callback_module('playbook_on_not_import_for_host', host, missing_file)

    def on_play_start(self, pattern):
        print banner("PLAY [%s]" % pattern)
        call_callback_module('playbook_on_play_start', pattern)

    def on_stats(self, stats):
        call_callback_module('playbook_on_stats', stats)


