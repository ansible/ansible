# (c) 2012, Michael DeHaan <michael.dehaan@gmail.com>
#
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

import multiprocessing
import signal
import os
import pwd
import Queue
import random
import traceback
import tempfile
import time
import collections
import socket
import base64
import sys

import ansible.constants as C
import ansible.inventory
from ansible import utils
from ansible import errors
from ansible import module_common
import poller
import connection
from return_data import ReturnData
from ansible.callbacks import DefaultRunnerCallbacks, vv

HAS_ATFORK=True
try:
    from Crypto.Random import atfork
except ImportError:
    HAS_ATFORK=False

multiprocessing_runner = None

################################################


def _executor_hook(job_queue, result_queue):

    # attempt workaround of https://github.com/newsapps/beeswithmachineguns/issues/17
    # this function also not present in CentOS 6
    if HAS_ATFORK:
        atfork()

    signal.signal(signal.SIGINT, signal.SIG_IGN)
    while not job_queue.empty():
        try:
            host = job_queue.get(block=False)
            result_queue.put(multiprocessing_runner._executor(host))
        except Queue.Empty:
            pass
        except:
            traceback.print_exc()

class HostVars(dict):
    ''' A special view of setup_cache that adds values from the inventory when needed. '''

    def __init__(self, setup_cache, inventory):
        self.setup_cache = setup_cache
        self.inventory = inventory
        self.lookup = {}

        self.update(setup_cache)

    def __getitem__(self, host):
        if not host in self.lookup:
            result = self.inventory.get_variables(host)
            result.update(self.setup_cache.get(host, {}))
            self.lookup[host] = result
        return self.lookup[host]

class Runner(object):
    ''' core API interface to ansible '''

    # see bin/ansible for how this is used...

    def __init__(self,
        host_list=C.DEFAULT_HOST_LIST,      # ex: /etc/ansible/hosts, legacy usage
        module_path=None,                   # ex: /usr/share/ansible
        module_name=C.DEFAULT_MODULE_NAME,  # ex: copy
        module_args=C.DEFAULT_MODULE_ARGS,  # ex: "src=/tmp/a dest=/tmp/b"
        forks=C.DEFAULT_FORKS,              # parallelism level
        timeout=C.DEFAULT_TIMEOUT,          # SSH timeout
        pattern=C.DEFAULT_PATTERN,          # which hosts?  ex: 'all', 'acme.example.org'
        remote_user=C.DEFAULT_REMOTE_USER,  # ex: 'username'
        remote_pass=C.DEFAULT_REMOTE_PASS,  # ex: 'password123' or None if using key
        remote_port=None,                   # if SSH on different ports
        private_key_file=C.DEFAULT_PRIVATE_KEY_FILE, # if not using keys/passwords
        sudo_pass=C.DEFAULT_SUDO_PASS,      # ex: 'password123' or None
        background=0,                       # async poll every X seconds, else 0 for non-async
        basedir=None,                       # directory of playbook, if applicable
        setup_cache=None,                   # used to share fact data w/ other tasks
        transport=C.DEFAULT_TRANSPORT,      # 'ssh', 'paramiko', 'local'
        conditional='True',                 # run only if this fact expression evals to true
        callbacks=None,                     # used for output
        sudo=False,                         # whether to run sudo or not
        sudo_user=C.DEFAULT_SUDO_USER,      # ex: 'root'
        module_vars=None,                   # a playbooks internals thing
        is_playbook=False,                  # running from playbook or not?
        inventory=None,                     # reference to Inventory object
        subset=None                         # subset pattern
        ):

        # storage & defaults
        self.setup_cache      = utils.default(setup_cache, lambda: collections.defaultdict(dict))
        self.basedir          = utils.default(basedir, lambda: os.getcwd())
        self.callbacks        = utils.default(callbacks, lambda: DefaultRunnerCallbacks())
        self.generated_jid    = str(random.randint(0, 999999999999))
        self.transport        = transport
        self.inventory        = utils.default(inventory, lambda: ansible.inventory.Inventory(host_list))

        self.module_vars      = utils.default(module_vars, lambda: {})
        self.sudo_user        = sudo_user
        self.connector        = connection.Connection(self)
        self.conditional      = conditional
        self.module_name      = module_name
        self.forks            = int(forks)
        self.pattern          = pattern
        self.module_args      = module_args
        self.timeout          = timeout
        self.remote_user      = remote_user
        self.remote_pass      = remote_pass
        self.remote_port      = remote_port
        self.private_key_file = private_key_file
        self.background       = background
        self.sudo             = sudo
        self.sudo_pass        = sudo_pass
        self.is_playbook      = is_playbook

        # misc housekeeping
        if subset and self.inventory._subset is None:
            # don't override subset when passed from playbook
            self.inventory.subset(subset)

        if self.transport == 'local':
            self.remote_user = pwd.getpwuid(os.geteuid())[0]

        if module_path is not None:
            for i in module_path.split(os.pathsep):
                utils.plugins.module_finder.add_directory(i)

        utils.plugins.push_basedir(self.basedir)

        # ensure we are using unique tmp paths
        random.seed()

    # *****************************************************

    def _transfer_str(self, conn, tmp, name, data):
        ''' transfer string to remote file '''

        if type(data) == dict:
            data = utils.jsonify(data)

        afd, afile = tempfile.mkstemp()
        afo = os.fdopen(afd, 'w')
        try:
            afo.write(data.encode('utf8'))
        except:
            raise errors.AnsibleError("failure encoding into utf-8")
        afo.flush()
        afo.close()

        remote = os.path.join(tmp, name)
        try:
            conn.put_file(afile, remote)
        finally:
            os.unlink(afile)
        return remote

    # *****************************************************

    def _execute_module(self, conn, tmp, module_name, args,
        async_jid=None, async_module=None, async_limit=None, inject=None):

        ''' runs a module that has already been transferred '''

        # hack to support fireball mode
        if module_name == 'fireball':
            args = "%s password=%s" % (args, base64.b64encode(str(utils.key_for_hostname(conn.host))))
            if 'port' not in args:
                args += " port=%s" % C.ZEROMQ_PORT

        (remote_module_path, is_new_style, shebang) = self._copy_module(conn, tmp, module_name, args, inject)

        cmd_mod = ""
        if self.sudo and self.sudo_user != 'root':
            # deal with possible umask issues once sudo'ed to other user
            cmd_chmod = "chmod a+r %s" % remote_module_path
            self._low_level_exec_command(conn, cmd_chmod, tmp, sudoable=False)

        cmd = ""
        if not is_new_style:
            args = utils.template(self.basedir, args, inject)
            argsfile = self._transfer_str(conn, tmp, 'arguments', args)
            if async_jid is None:
                cmd = "%s %s" % (remote_module_path, argsfile)
            else:
                cmd = " ".join([str(x) for x in [remote_module_path, async_jid, async_limit, async_module, argsfile]])
        else:
            if async_jid is None:
                cmd = "%s" % (remote_module_path)
            else:
                cmd = " ".join([str(x) for x in [remote_module_path, async_jid, async_limit, async_module]])

        if not shebang:
            raise errors.AnsibleError("module is missing interpreter line")

        cmd = shebang.replace("#!","") + " " + cmd
        if tmp.find("tmp") != -1 and C.DEFAULT_KEEP_REMOTE_FILES != '1':
            cmd = cmd + "; rm -rf %s >/dev/null 2>&1" % tmp
        res = self._low_level_exec_command(conn, cmd, tmp, sudoable=True)
        return ReturnData(conn=conn, result=res)

    # *****************************************************

    def _executor(self, host):
        ''' handler for multiprocessing library '''

        try:
            exec_rc = self._executor_internal(host)
            if type(exec_rc) != ReturnData:
                raise Exception("unexpected return type: %s" % type(exec_rc))
            # redundant, right?
            if not exec_rc.comm_ok:
                self.callbacks.on_unreachable(host, exec_rc.result)
            return exec_rc
        except errors.AnsibleError, ae:
            msg = str(ae)
            self.callbacks.on_unreachable(host, msg)
            return ReturnData(host=host, comm_ok=False, result=dict(failed=True, msg=msg))
        except Exception:
            msg = traceback.format_exc()
            self.callbacks.on_unreachable(host, msg)
            return ReturnData(host=host, comm_ok=False, result=dict(failed=True, msg=msg))

    # *****************************************************

    def _executor_internal(self, host):
        ''' executes any module one or more times '''

        host_variables = self.inventory.get_variables(host)
        if self.transport in [ 'paramiko', 'ssh' ]:
            port = host_variables.get('ansible_ssh_port', self.remote_port)
            if port is None:
                port = C.DEFAULT_REMOTE_PORT
        else:
            # fireball, local, etc
            port = self.remote_port

        inject = {}
        inject.update(host_variables)
        inject.update(self.module_vars)
        inject.update(self.setup_cache[host])
        inject['hostvars'] = HostVars(self.setup_cache, self.inventory)
        inject['group_names'] = host_variables.get('group_names', [])
        inject['groups'] = self.inventory.groups_list()

        # allow with_foo to work in playbooks...
        items = None
        items_plugin = self.module_vars.get('items_lookup_plugin', None)
        if items_plugin is not None and items_plugin in utils.plugins.lookup_loader:
            items_terms = self.module_vars.get('items_lookup_terms', '')
            items_terms = utils.template_ds(self.basedir, items_terms, inject)
            items = utils.plugins.lookup_loader.get(items_plugin, runner=self, basedir=self.basedir).run(items_terms, inject=inject)
            if type(items) != list:
                raise errors.AnsibleError("lookup plugins have to return a list: %r" % items)

            if len(items) and self.module_name in [ 'apt', 'yum' ]:
                # hack for apt and soon yum, with_items maps back into a single module call
                inject['item'] = ",".join(items)
                items = None

        # logic to decide how to run things depends on whether with_items is used

        if items is None:
            return self._executor_internal_inner(host, self.module_name, self.module_args, inject, port)
        elif len(items) > 0:
            # executing using with_items, so make multiple calls
            # TODO: refactor
            aggregrate = {}
            all_comm_ok = True
            all_changed = False
            all_failed = False
            results = []
            for x in items:
                inject['item'] = x
                result = self._executor_internal_inner(host, self.module_name, self.module_args, inject, port)
                results.append(result.result)
                if result.comm_ok == False:
                    all_comm_ok = False
                    all_failed = True
                    break
                for x in results:
                    if x.get('changed') == True:
                        all_changed = True
                    if (x.get('failed') == True) or (('rc' in x) and (x['rc'] != 0)):
                        all_failed = True
                        break
            msg = 'All items completed'
            if all_failed:
                msg = "One or more items failed."
            rd_result = dict(failed=all_failed, changed=all_changed, results=results, msg=msg)
            if not all_failed:
                del rd_result['failed']
            return ReturnData(host=host, comm_ok=all_comm_ok, result=rd_result)
        else:
            self.callbacks.on_skipped(host, None)
            return ReturnData(host=host, comm_ok=True, result=dict(skipped=True))

    # *****************************************************

    def _executor_internal_inner(self, host, module_name, module_args, inject, port, is_chained=False):
        ''' decides how to invoke a module '''

        # allow module args to work as a dictionary
        # though it is usually a string
        new_args = ""
        if type(module_args) == dict:
            for (k,v) in module_args.iteritems():
                new_args = new_args + "%s='%s' " % (k,v)
            module_args = new_args

        module_name = utils.template(self.basedir, module_name, inject)
        module_args = utils.template(self.basedir, module_args, inject, expand_lists=True)

        if module_name in utils.plugins.action_loader:
            if self.background != 0:
                raise errors.AnsibleError("async mode is not supported with the %s module" % module_name)
            handler = utils.plugins.action_loader.get(module_name, self)
        elif self.background == 0:
            handler = utils.plugins.action_loader.get('normal', self)
        else:
            handler = utils.plugins.action_loader.get('async', self)

        conditional = utils.template(self.basedir, self.conditional, inject)
        if not getattr(handler, 'BYPASS_HOST_LOOP', False) and not utils.check_conditional(conditional):
            result = utils.jsonify(dict(skipped=True))
            self.callbacks.on_skipped(host, inject.get('item',None))
            return ReturnData(host=host, result=result)

        conn = None
        actual_host = inject.get('ansible_ssh_host', host)
        actual_port = port
        if self.transport in [ 'paramiko', 'ssh' ]:
            actual_port = inject.get('ansible_ssh_port', port)

        # the delegated host may have different SSH port configured, etc
        # and we need to transfer those, and only those, variables
        delegate_to = inject.get('delegate_to', None)
        if delegate_to is not None:
            delegate_to = utils.template(self.basedir, delegate_to, inject)
            inject = inject.copy()
            interpreters = []
            for i in inject:
                if i.startswith("ansible_") and i.endswith("_interpreter"):
                    interpreters.append(i)
            for i in interpreters:
                del inject[i]
            port = C.DEFAULT_REMOTE_PORT
            try:
                delegate_info = inject['hostvars'][delegate_to]
                actual_host = delegate_info.get('ansible_ssh_host', delegate_to)
                actual_port = delegate_info.get('ansible_ssh_port', port)
                for i in delegate_info:
                    if i.startswith("ansible_") and i.endswith("_interpreter"):
                        inject[i] = delegate_info[i]
            except errors.AnsibleError:
                actual_host = delegate_to
                actual_port = port

        try:
            if actual_port is not None:
                actual_port = int(actual_port)
        except ValueError, e:
            result = dict(failed=True, msg="FAILED: Configured port \"%s\" is not a valid port, expected integer" % actual_port)
            return ReturnData(host=host, comm_ok=False, result=result)

        try:
            conn = self.connector.connect(actual_host, actual_port)
            if delegate_to or host != actual_host:
                conn.delegate = host


        except errors.AnsibleConnectionFailed, e:
            result = dict(failed=True, msg="FAILED: %s" % str(e))
            return ReturnData(host=host, comm_ok=False, result=result)

        tmp = ''
        # all modules get a tempdir, action plugins get one unless they have NEEDS_TMPPATH set to False
        if getattr(handler, 'NEEDS_TMPPATH', True):
            tmp = self._make_tmp_path(conn)

        result = handler.run(conn, tmp, module_name, module_args, inject)

        conn.close()

        if not result.comm_ok:
            # connection or parsing errors...
            self.callbacks.on_unreachable(host, result.result)
        else:
            data = result.result
            if 'item' in inject:
                result.result['item'] = inject['item']

            result.result['invocation'] = dict(
                module_args=module_args,
                module_name=module_name
            )

            if is_chained:
                # no callbacks
                return result
            if 'skipped' in data:
                self.callbacks.on_skipped(host)
            elif not result.is_successful():
                ignore_errors = self.module_vars.get('ignore_errors', False)
                self.callbacks.on_failed(host, data, ignore_errors)
            else:
                self.callbacks.on_ok(host, data)
        return result

    # *****************************************************

    def _low_level_exec_command(self, conn, cmd, tmp, sudoable=False):
        ''' execute a command string over SSH, return the output '''

        sudo_user = self.sudo_user
        stdin, stdout, stderr = conn.exec_command(cmd, tmp, sudo_user, sudoable=sudoable)

        if type(stdout) not in [ str, unicode ]:
            out = "\n".join(stdout.readlines())
        else:
            out = stdout

        if type(stderr) not in [ str, unicode ]:
            err = "\n".join(stderr.readlines())
        else:
            err = stderr

        return out + err

    # *****************************************************

    def _remote_md5(self, conn, tmp, path):
        ''' takes a remote md5sum without requiring python, and returns 0 if no file '''

        test = "rc=0; [ -r \"%s\" ] || rc=2; [ -f \"%s\" ] || rc=1" % (path,path)
        md5s = [
            "(/usr/bin/md5sum %s 2>/dev/null)" % path,  # Linux
            "(/sbin/md5sum -q %s 2>/dev/null)" % path,  # ?
            "(/usr/bin/digest -a md5 %s 2>/dev/null)" % path,   # Solaris 10+
            "(/sbin/md5 -q %s 2>/dev/null)" % path,     # Freebsd
            "(/usr/bin/md5 -n %s 2>/dev/null)" % path,  # Netbsd
            "(/bin/md5 -q %s 2>/dev/null)" % path       # Openbsd
        ]

        cmd = " || ".join(md5s)
        cmd = "%s; %s || (echo \"${rc}  %s\")" % (test, cmd, path)
        data = self._low_level_exec_command(conn, cmd, tmp, sudoable=False)
        data2 = utils.last_non_blank_line(data)
        try:
            return data2.split()[0]
        except IndexError:
            sys.stderr.write("warning: md5sum command failed unusually, please report this to the list so it can be fixed\n")
            sys.stderr.write("command: %s\n" % md5s)
            sys.stderr.write("----\n")
            sys.stderr.write("output: %s\n" % data)
            sys.stderr.write("----\n")
            # this will signal that it changed and allow things to keep going
            return "INVALIDMD5SUM"

    # *****************************************************

    def _make_tmp_path(self, conn):
        ''' make and return a temporary path on a remote box '''

        basefile = 'ansible-%s-%s' % (time.time(), random.randint(0, 2**48))
        basetmp = os.path.join(C.DEFAULT_REMOTE_TMP, basefile)
        if self.sudo and self.sudo_user != 'root':
            basetmp = os.path.join('/tmp', basefile)

        cmd = 'mkdir -p %s' % basetmp
        if self.remote_user != 'root':
            cmd += ' && chmod a+rx %s' % basetmp
        cmd += ' && echo %s' % basetmp

        result = self._low_level_exec_command(conn, cmd, None, sudoable=False)
        rc = utils.last_non_blank_line(result).strip() + '/'
        return rc


    # *****************************************************

    def _copy_module(self, conn, tmp, module_name, module_args, inject):
        ''' transfer a module over SFTP, does not run it '''

        if module_name.startswith("/"):
            raise errors.AnsibleFileNotFound("%s is not a module" % module_name)

        # Search module path(s) for named module.
        in_path = utils.plugins.module_finder.find_plugin(module_name)
        if in_path is None:
            raise errors.AnsibleFileNotFound("module %s not found in %s" % (module_name, utils.plugins.module_finder.print_paths()))

        out_path = os.path.join(tmp, module_name)

        module_data = ""
        is_new_style=False

        with open(in_path) as f:
            module_data = f.read()
            if module_common.REPLACER in module_data:
                is_new_style=True
            module_data = module_data.replace(module_common.REPLACER, module_common.MODULE_COMMON)
            encoded_args = "\"\"\"%s\"\"\"" % module_args.replace("\"","\\\"")
            module_data = module_data.replace(module_common.REPLACER_ARGS, encoded_args)
            encoded_lang = "\"\"\"%s\"\"\"" % C.DEFAULT_MODULE_LANG
            module_data = module_data.replace(module_common.REPLACER_LANG, encoded_lang)
            if is_new_style:
                facility = C.DEFAULT_SYSLOG_FACILITY
                if 'ansible_syslog_facility' in inject:
                    facility = inject['ansible_syslog_facility']
                module_data = module_data.replace('syslog.LOG_USER', "syslog.%s" % facility)

        # use the correct python interpreter for the host
        if 'ansible_python_interpreter' in inject:
            interpreter = inject['ansible_python_interpreter']
            module_lines = module_data.split('\n')
            if '#!' and 'python' in module_lines[0]:
                module_lines[0] = "#!%s" % interpreter
            module_data = "\n".join(module_lines)

        self._transfer_str(conn, tmp, module_name, module_data)

        lines = module_data.split("\n")
        shebang = None
        if lines[0].startswith("#!"):
            shebang = lines[0]

        return (out_path, is_new_style, shebang)

    # *****************************************************


    def _parallel_exec(self, hosts):
        ''' handles mulitprocessing when more than 1 fork is required '''

        manager = multiprocessing.Manager()
        job_queue = manager.Queue()
        for host in hosts:
            job_queue.put(host)
        result_queue = manager.Queue()

        workers = []
        for i in range(self.forks):
            prc = multiprocessing.Process(target=_executor_hook,
                args=(job_queue, result_queue))
            prc.start()
            workers.append(prc)

        try:
            for worker in workers:
                worker.join()
        except KeyboardInterrupt:
            for worker in workers:
                worker.terminate()
                worker.join()

        results = []
        try:
            while not result_queue.empty():
                results.append(result_queue.get(block=False))
        except socket.error:
            raise errors.AnsibleError("<interrupted>")
        return results

    # *****************************************************

    def _partition_results(self, results):
        ''' seperate results by ones we contacted & ones we didn't '''

        if results is None:
            return None
        results2 = dict(contacted={}, dark={})

        for result in results:
            host = result.host
            if host is None:
                raise Exception("internal error, host not set")
            if result.communicated_ok():
                results2["contacted"][host] = result.result
            else:
                results2["dark"][host] = result.result

        # hosts which were contacted but never got a chance to return
        for host in self.inventory.list_hosts(self.pattern):
            if not (host in results2['dark'] or host in results2['contacted']):
                results2["dark"][host] = {}
        return results2

    # *****************************************************

    def run(self):
        ''' xfer & run module on all matched hosts '''

        # find hosts that match the pattern
        hosts = self.inventory.list_hosts(self.pattern)
        if len(hosts) == 0:
            self.callbacks.on_no_hosts()
            return dict(contacted={}, dark={})

        global multiprocessing_runner
        multiprocessing_runner = self
        results = None

        # Check if this is an action plugin. Some of them are designed
        # to be ran once per group of hosts. Example module: pause,
        # run once per hostgroup, rather than pausing once per each
        # host.
        p = utils.plugins.action_loader.get(self.module_name, self)
        if p and getattr(p, 'BYPASS_HOST_LOOP', None):
            # Expose the current hostgroup to the bypassing plugins
            self.host_set = hosts
            # We aren't iterating over all the hosts in this
            # group. So, just pick the first host in our group to
            # construct the conn object with.
            result_data = self._executor(hosts[0]).result
            # Create a ResultData item for each host in this group
            # using the returned result. If we didn't do this we would
            # get false reports of dark hosts.
            results = [ ReturnData(host=h, result=result_data, comm_ok=True) \
                           for h in hosts ]
            del self.host_set
        elif self.forks > 1:
            try:
                results = self._parallel_exec(hosts)
            except IOError, ie:
                print ie.errno
                if ie.errno == 32:
                    # broken pipe from Ctrl+C
                    raise errors.AnsibleError("interupted")
                raise
        else:
            results = [ self._executor(h) for h in hosts ]
        return self._partition_results(results)

    # *****************************************************

    def run_async(self, time_limit):
        ''' Run this module asynchronously and return a poller. '''

        self.background = time_limit
        results = self.run()
        return results, poller.AsyncPoller(results, self)
