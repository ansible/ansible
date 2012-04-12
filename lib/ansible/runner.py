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
#

################################################

import fnmatch
import multiprocessing
import signal
import os
import Queue
import random
import traceback
import tempfile
import subprocess

import ansible.constants as C 
import ansible.connection
from ansible import utils
from ansible import errors
from ansible import callbacks as ans_callbacks
    
HAS_ATFORK=True
try:
    from Crypto.Random import atfork
except ImportError:
    HAS_ATFORK=False

################################################

def _executor_hook(job_queue, result_queue):
    ''' callback used by multiprocessing pool '''

    # attempt workaround of https://github.com/newsapps/beeswithmachineguns/issues/17
    # does not occur for everyone, some claim still occurs on newer paramiko
    # this function not present in CentOS 6
    if HAS_ATFORK:
        atfork()

    signal.signal(signal.SIGINT, signal.SIG_IGN)
    while not job_queue.empty():
        try:
            job = job_queue.get(block=False)
            runner, host = job
            result_queue.put(runner._executor(host))
        except Queue.Empty:
            pass
        except:
            traceback.print_exc()
 
################################################

class Runner(object):

    _external_variable_script = None

    def __init__(self, host_list=C.DEFAULT_HOST_LIST, module_path=C.DEFAULT_MODULE_PATH,
        module_name=C.DEFAULT_MODULE_NAME, module_args=C.DEFAULT_MODULE_ARGS, 
        forks=C.DEFAULT_FORKS, timeout=C.DEFAULT_TIMEOUT, pattern=C.DEFAULT_PATTERN,
        remote_user=C.DEFAULT_REMOTE_USER, remote_pass=C.DEFAULT_REMOTE_PASS,
        remote_port=C.DEFAULT_REMOTE_PORT, background=0, basedir=None, setup_cache=None,
        transport='paramiko', conditional='True', groups={}, callbacks=None, verbose=False,
        debug=False, sudo=False, extra_vars=None, module_vars=None):
   
        if setup_cache is None:
            setup_cache = {}
        if basedir is None: 
            basedir = os.getcwd()

        if callbacks is None:
            callbacks = ans_callbacks.DefaultRunnerCallbacks()
        self.callbacks = callbacks

        self.generated_jid = str(random.randint(0, 999999999999))
        self.connector = ansible.connection.Connection(self, transport)

        if type(host_list) == str:
            self.host_list, self.groups = self.parse_hosts(host_list)
        else:
            self.host_list = host_list
            self.groups    = groups

        self.setup_cache = setup_cache
        self.conditional = conditional
        self.module_path = module_path
        self.module_name = module_name
        self.forks       = int(forks)
        self.pattern     = pattern
        self.module_args = module_args
        self.module_vars = module_vars
        self.extra_vars  = extra_vars
        self.timeout     = timeout
        self.debug       = debug
        self.verbose     = verbose
        self.remote_user = remote_user
        self.remote_pass = remote_pass
        self.remote_port = remote_port
        self.background  = background
        self.basedir     = basedir
        self.sudo        = sudo

        if type(self.module_args) != str and type(self.module_args) != dict:
            raise Exception("module_args must be a string or dict: %s" % self.module_args)

        self._tmp_paths  = {}
        random.seed()


    # *****************************************************

    @classmethod
    def parse_hosts_from_regular_file(cls, host_list):
        ''' parse a textual host file '''

        results = []
        groups = dict(ungrouped=[])
        lines = file(host_list).read().split("\n")
        group_name = 'ungrouped'
        for item in lines:
            item = item.lstrip().rstrip()
            if item.startswith("#"):
                # ignore commented out lines
                pass
            elif item.startswith("["):
                # looks like a group
                group_name = item.replace("[","").replace("]","").lstrip().rstrip()
                groups[group_name] = []
            elif item != "":
                # looks like a regular host
                groups[group_name].append(item)
                if not item in results:
                    results.append(item)
        return (results, groups)

    # *****************************************************

    @classmethod
    def parse_hosts_from_script(cls, host_list, extra_vars):
        ''' evaluate a script that returns list of hosts by groups '''

        results = []
        groups = dict(ungrouped=[])
        host_list = os.path.abspath(host_list)
        cls._external_variable_script = host_list
        cmd = [host_list, '--list']
        if extra_vars:
            cmd.extend(['--extra-vars', extra_vars])
        cmd = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False)
        out, err = cmd.communicate()
        rc = cmd.returncode
        if rc:
            raise errors.AnsibleError("%s: %s" % (host_list, err))
        try:
            groups = utils.json_loads(out)
        except:
            raise errors.AnsibleError("invalid JSON response from script: %s" % host_list)
        for (groupname, hostlist) in groups.iteritems():
            for host in hostlist:
                if host not in results:
                    results.append(host)
        return (results, groups)

    # *****************************************************

    @classmethod
    def parse_hosts(cls, host_list, override_hosts=None, extra_vars=None):
        ''' parse the host inventory file, returns (hosts, groups) '''

        if override_hosts is not None:
            if type(override_hosts) != list:
                raise errors.AnsibleError("override hosts must be a list")
            return (override_hosts, dict(ungrouped=override_hosts))

        if type(host_list) == list:
            raise Exception("function can only be called on inventory files")

        host_list = os.path.expanduser(host_list)
        if not os.path.exists(host_list):
            raise errors.AnsibleFileNotFound("inventory file not found: %s" % host_list)

        if not os.access(host_list, os.X_OK):
            return Runner.parse_hosts_from_regular_file(host_list)
        else:
            return Runner.parse_hosts_from_script(host_list, extra_vars)

    # *****************************************************

    def _matches(self, host_name, pattern):
        ''' returns if a hostname is matched by the pattern '''

        # a pattern is in fnmatch format but more than one pattern
        # can be strung together with semicolons. ex:
        #   atlanta-web*.example.com;dc-web*.example.com

        if host_name == '':
            return False
        pattern = pattern.replace(";",":")
        subpatterns = pattern.split(":")
        for subpattern in subpatterns:
            if subpattern == 'all':
                return True
            if fnmatch.fnmatch(host_name, subpattern):
                return True
            elif subpattern in self.groups:
                if host_name in self.groups[subpattern]:
                    return True
        return False

    # *****************************************************

    def _connect(self, host):
        ''' connects to a host, returns (is_successful, connection_object OR traceback_string) '''

        try:
            return [ True, self.connector.connect(host) ]
        except errors.AnsibleConnectionFailed, e:
            return [ False, "FAILED: %s" % str(e) ]

    # *****************************************************

    def _return_from_module(self, conn, host, result, err, executed=None):
        ''' helper function to handle JSON parsing of results '''

        try:
            result = utils.parse_json(result) 
            if executed is not None:
                result['invocation'] = executed
                if 'stderr' in result:
                    err="%s%s"%(err,result['stderr'])
            return [host, True, result, err]
        except Exception, e:
            return [host, False, "%s/%s/%s" % (str(e), result, executed), err]

    # *****************************************************

    def _delete_remote_files(self, conn, files):
        ''' deletes one or more remote files '''

        if type(files) == str:
            files = [ files ]
        for filename in files:
            if not filename.startswith('/tmp/'):
                raise Exception("not going to happen")
            self._exec_command(conn, "rm -rf %s" % filename, None)

    # *****************************************************

    def _transfer_module(self, conn, tmp, module):
        ''' transfers a module file to the remote side to execute it, but does not execute it yet '''

        outpath = self._copy_module(conn, tmp, module)
        self._exec_command(conn, "chmod +x %s" % outpath, tmp)
        return outpath

    # *****************************************************

    def _transfer_str(self, conn, tmp, name, args_str):
        ''' transfer arguments as a single file to be fed to the module. '''

        if type(args_str) == dict:
            args_str = utils.smjson(args_str)

        args_fd, args_file = tempfile.mkstemp()
        args_fo = os.fdopen(args_fd, 'w')
        args_fo.write(args_str)
        args_fo.flush()
        args_fo.close()

        args_remote = os.path.join(tmp, name)
        conn.put_file(args_file, args_remote)
        os.unlink(args_file)

        return args_remote

    # *****************************************************

    def _add_variables_from_script(self, conn, inject):
        ''' support per system variabes from external variable scripts, see web docs '''

        host = conn.host

        cmd = [Runner._external_variable_script, '--host', host]
        if self.extra_vars:
            cmd.extend(['--extra-vars', self.extra_vars])

        cmd = subprocess.Popen(cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=False
        )
        out, err = cmd.communicate()
        inject2 = {}
        try:
            inject2 = utils.json_loads(out)
        except:
            raise errors.AnsibleError("%s returned invalid result when called with hostname %s" % (
                Runner._external_variable_script,
                host
            ))
        # store injected variables in the templates
        inject.update(inject2)

    # *****************************************************

    def _add_setup_vars(self, inject, args):
        ''' setup module variables need special handling '''

        is_dict = False
        if type(args) == dict:
            is_dict = True

        # TODO: keep this as a dict through the whole path to simplify this code
        for (k,v) in inject.iteritems():
            if not k.startswith('facter_') and not k.startswith('ohai_'):
                if not is_dict:
                    if str(v).find(" ") != -1:
                        v = "\"%s\"" % v
                    args += " %s=%s" % (k, str(v).replace(" ","~~~"))
                else:
                    args[k]=v
        return args   
 
    # *****************************************************

    def _add_setup_metadata(self, args):
        ''' automatically determine where to store variables for the setup module '''
        
        is_dict = False
        if type(args) == dict:
            is_dict = True

        # TODO: keep this as a dict through the whole path to simplify this code
        if not is_dict:
            if args.find("metadata=") == -1:
                if self.remote_user == 'root':
                    args = "%s metadata=/etc/ansible/setup" % args
                else:
                    args = "%s metadata=/home/%s/.ansible/setup" % (args, self.remote_user)
        else:
            if not 'metadata' in args:
                if self.remote_user == 'root':
                    args['metadata'] = '/etc/ansible/setup'
                else:
                    args['metadata'] = "/home/%s/.ansible/setup" % (self.remote_user)
        return args   
 
    # *****************************************************

    def _execute_module(self, conn, tmp, remote_module_path, args, 
        async_jid=None, async_module=None, async_limit=None):
        ''' runs a module that has already been transferred '''

        inject = self.setup_cache.get(conn.host,{})
        conditional = utils.double_template(self.conditional, inject)
        if not eval(conditional):
            return [ utils.smjson(dict(skipped=True)), None, 'skipped' ]

        if Runner._external_variable_script is not None:
            self._add_variables_from_script(conn, inject)
        if self.module_name == 'setup':
            args = self._add_setup_vars(inject, args)
            args = self._add_setup_metadata(args)

        if type(args) == dict:
           args = utils.bigjson(args)
        args = utils.template(args, inject)

        module_name_tail = remote_module_path.split("/")[-1]

        argsfile = self._transfer_str(conn, tmp, 'arguments', args)
        if async_jid is None:
            cmd = "%s %s" % (remote_module_path, argsfile)
        else:
            cmd = " ".join([str(x) for x in [remote_module_path, async_jid, async_limit, async_module, argsfile]])

        res, err = self._exec_command(conn, cmd, tmp, sudoable=True)
        client_executed_str = "%s %s" % (module_name_tail, args.strip())
        return ( res, err, client_executed_str )

    # *****************************************************

    def _add_result_to_setup_cache(self, conn, result):
        ''' allows discovered variables to be used in templates and action statements '''

        host = conn.host
        try:
            var_result = utils.parse_json(result)
        except:
            var_result = {}

        # note: do not allow variables from playbook to be stomped on
        # by variables coming up from facter/ohai/etc.  They
        # should be prefixed anyway
        if not host in self.setup_cache:
            self.setup_cache[host] = {}
        for (k, v) in var_result.iteritems():
            if not k in self.setup_cache[host]:
                self.setup_cache[host][k] = v

    # *****************************************************

    def _execute_normal_module(self, conn, host, tmp, module_name):
        ''' transfer & execute a module that is not 'copy' or 'template' '''

        # shell and command are the same module
        if module_name == 'shell':
            module_name = 'command'
            self.module_args += " #USE_SHELL"

        module = self._transfer_module(conn, tmp, module_name)
        (result, err, executed) = self._execute_module(conn, tmp, module, self.module_args)

        if module_name == 'setup':
            self._add_result_to_setup_cache(conn, result)

        return self._return_from_module(conn, host, result, err, executed)

    # *****************************************************

    def _execute_async_module(self, conn, host, tmp, module_name):
        ''' transfer the given module name, plus the async module, then run it '''

        # hack to make the 'shell' module keyword really be executed
        # by the command module
        module_args = self.module_args
        if module_name == 'shell':
            module_name = 'command'
            module_args += " #USE_SHELL"

        async  = self._transfer_module(conn, tmp, 'async_wrapper')
        module = self._transfer_module(conn, tmp, module_name)
        (result, err, executed) = self._execute_module(conn, tmp, async, module_args,
           async_module=module, 
           async_jid=self.generated_jid, 
           async_limit=self.background
        )

        return self._return_from_module(conn, host, result, err, executed)

    # *****************************************************

    def _execute_copy(self, conn, host, tmp):
        ''' handler for file transfer operations '''

        # load up options
        options = utils.parse_kv(self.module_args)
        source = options.get('src', None)
        dest   = options.get('dest', None)
        if source is None or dest is None:
            return (host, True, dict(failed=True, msg="src and dest are required"), '')
        
        # transfer the file to a remote tmp location
        tmp_src = tmp + source.split('/')[-1]
        conn.put_file(utils.path_dwim(self.basedir, source), tmp_src)

        # install the copy  module
        self.module_name = 'copy'
        module = self._transfer_module(conn, tmp, 'copy')

        # run the copy module
        args = "src=%s dest=%s" % (tmp_src, dest)
        (result1, err, executed) = self._execute_module(conn, tmp, module, args)
        (host, ok, data, err) = self._return_from_module(conn, host, result1, err, executed)

        if ok:
            return self._chain_file_module(conn, tmp, data, err, options, executed)
        else:
            return (host, ok, data, err) 

    # *****************************************************

    def _execute_fetch(self, conn, host, tmp):
        ''' handler for fetch operations '''

        # load up options
        options = utils.parse_kv(self.module_args)
        source = options.get('src', None)
        dest = options.get('dest', None)
        if source is None or dest is None:
            return (host, True, dict(failed=True, msg="src and dest are required"), '')

        # files are saved in dest dir, with a subdir for each host, then the filename
        filename = os.path.basename(source)
        dest   = "%s/%s/%s" % (utils.path_dwim(self.basedir, dest), host, filename)

        # compare old and new md5 for support of change hooks
        local_md5 = None
        if os.path.exists(dest):
            local_md5 = os.popen("md5sum %s" % dest).read().split()[0]
        remote_md5 = self._exec_command(conn, "md5sum %s" % source, tmp, True)[0].split()[0]

        if remote_md5 != local_md5:
            # create the containing directories, if needed
            os.makedirs(os.path.dirname(dest))
            # fetch the file and check for changes
            conn.fetch_file(source, dest)
            new_md5 = os.popen("md5sum %s" % dest).read().split()[0]
            changed = (new_md5 != local_md5)
            if new_md5 != remote_md5:
                return (host, True, dict(failed=True, msg="md5 mismatch", md5sum=new_md5), '')
            return (host, True, dict(changed=True, md5sum=new_md5), '')
        else:
            return (host, True, dict(changed=False, md5sum=local_md5), '')
        
        
    # *****************************************************

    def _chain_file_module(self, conn, tmp, data, err, options, executed):
        ''' handles changing file attribs after copy/template operations '''

        old_changed = data.get('changed', False)
        module = self._transfer_module(conn, tmp, 'file')
        args = ' '.join([ "%s=%s" % (k,v) for (k,v) in options.items() ])
        (result2, err2, executed2) = self._execute_module(conn, tmp, module, args)
        results2 = self._return_from_module(conn, conn.host, result2, err2, executed)
        (host, ok, data2, err2) = results2
        new_changed = data2.get('changed', False)
        data.update(data2)
        if old_changed or new_changed:
            data['changed'] = True
        return (host, ok, data, "%s%s"%(err,err2))

    # *****************************************************

    def _execute_template(self, conn, host, tmp):
        ''' handler for template operations '''

        # load up options
        options  = utils.parse_kv(self.module_args)
        source   = options.get('src', None)
        dest     = options.get('dest', None)
        metadata = options.get('metadata', None)
        if source is None or dest is None:
            return (host, True, dict(failed=True, msg="src and dest are required"), '')

        if metadata is None:
            if self.remote_user == 'root':
                metadata = '/etc/ansible/setup'
            else:
                metadata = '~/.ansible/setup'

        # first copy the source template over
        temppath = tmp + os.path.split(source)[-1]
        conn.put_file(utils.path_dwim(self.basedir, source), temppath)

        # install the template module
        template_module = self._transfer_module(conn, tmp, 'template')

        # transfer module vars
        if self.module_vars:
            vars = utils.bigjson(self.module_vars)
            vars_path = self._transfer_str(conn, tmp, 'module_vars', vars)
            vars_arg=" vars=%s"%(vars_path)
        else:
            vars_arg=""
        
        # run the template module
        args = "src=%s dest=%s metadata=%s%s" % (temppath, dest, metadata, vars_arg)
        (result1, err, executed) = self._execute_module(conn, tmp, template_module, args)
        (host, ok, data, err) = self._return_from_module(conn, host, result1, err, executed)

        if ok:
            return self._chain_file_module(conn, tmp, data, err, options, executed)
        else:
            return (host, ok, data, err)

    # *****************************************************

    def _executor(self, host):
        try:
            (host, ok, data, err) = self._executor_internal(host)
            if not ok:
                self.callbacks.on_unreachable(host, data)
            return (host, ok, data)
        except errors.AnsibleError, ae:
            msg = str(ae)
            self.callbacks.on_unreachable(host, msg)
            return [host, False, msg]
        except Exception:
            msg = traceback.format_exc()
            self.callbacks.on_unreachable(host, msg)
            return [host, False, msg]

    def _executor_internal(self, host):
        ''' callback executed in parallel for each host. returns (hostname, connected_ok, extra) '''

        ok, conn = self._connect(host)
        if not ok:
            return [ host, False, conn , None]
        
        cache = self.setup_cache.get(host, {})
        module_name = utils.template(self.module_name, cache)

        tmp = self._get_tmp_path(conn)
        result = None

        if self.module_name == 'copy':
            result = self._execute_copy(conn, host, tmp)
        elif self.module_name == 'fetch':
            result = self._execute_fetch(conn, host, tmp)
        elif self.module_name == 'template':
            result = self._execute_template(conn, host, tmp)
        else:
            if self.background == 0:
                result = self._execute_normal_module(conn, host, tmp, module_name)
            else:
                result = self._execute_async_module(conn, host, tmp, module_name)

        self._delete_remote_files(conn, tmp)
        conn.close()

        (host, connect_ok, data, err) = result
        if not connect_ok:
            self.callbacks.on_unreachable(host, data)
        else:
            if 'failed' in data or 'rc' in data and str(data['rc']) != '0':
                self.callbacks.on_failed(host, data)
            elif 'skipped' in data:
                self.callbacks.on_skipped(host)
            else:
                self.callbacks.on_ok(host, data)

            if self.debug and err:
                self.callbacks.on_error(host, err)

        return result

    # *****************************************************

    def _exec_command(self, conn, cmd, tmp, sudoable=False):
        ''' execute a command string over SSH, return the output '''

        stdin, stdout, stderr = conn.exec_command(cmd, tmp, sudoable=sudoable)

        if type(stderr) != str:
            err="\n".join(stderr.readlines())
        else:
            err=stderr

        if type(stdout) != str:
            return "\n".join(stdout.readlines()), err
        else:
            return stdout, err

    # *****************************************************

    def _get_tmp_path(self, conn):
        ''' gets a temporary path on a remote box '''

        result, err = self._exec_command(conn, "mktemp -d /tmp/ansible.XXXXXX", None, sudoable=False)
        cleaned = result.split("\n")[0].strip() + '/'
        return cleaned


    # *****************************************************

    def _copy_module(self, conn, tmp, module):
        ''' transfer a module over SFTP, does not run it '''

        if module.startswith("/"):
            raise errors.AnsibleFileNotFound("%s is not a module" % module)
        in_path = os.path.expanduser(os.path.join(self.module_path, module))
        if not os.path.exists(in_path):
            raise errors.AnsibleFileNotFound("module not found: %s" % in_path)

        out_path = tmp + module
        conn.put_file(in_path, out_path)
        return out_path

    # *****************************************************

    def _match_hosts(self, pattern):
        ''' return all matched hosts fitting a pattern '''

        return [ h for h in self.host_list if self._matches(h, pattern) ]

    # *****************************************************

    def _parallel_exec(self, hosts):
        ''' handles mulitprocessing when more than 1 fork is required '''

        job_queue = multiprocessing.Manager().Queue()
        [job_queue.put(i) for i in hosts]

        result_queue = multiprocessing.Manager().Queue()

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
        while not result_queue.empty():
            results.append(result_queue.get(block=False))
        return results

    # *****************************************************

    def _partition_results(self, results):
        ''' seperate results by ones we contacted & ones we didn't '''

        results2 = dict(contacted={}, dark={})

        if results is None:
            return None

        for result in results:
            (host, contacted_ok, result) = result
            if contacted_ok:
                results2["contacted"][host] = result
            else:
                results2["dark"][host] = result

        # hosts which were contacted but never got a chance to return
        for host in self._match_hosts(self.pattern):
            if not (host in results2['dark'] or host in results2['contacted']):
                results2["dark"][host] = {}

        return results2

    # *****************************************************

    def run(self):
        ''' xfer & run module on all matched hosts '''
       
        # find hosts that match the pattern
        hosts = self._match_hosts(self.pattern)
        if len(hosts) == 0:
            return dict(contacted={}, dark={})
 
        hosts = [ (self,x) for x in hosts ]
        results = None
        if self.forks > 1:
            results = self._parallel_exec(hosts)
        else:
            results = [ self._executor(h[1]) for h in hosts ]
        return self._partition_results(results)


