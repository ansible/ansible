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
import ansible.constants as C 
import ansible.connection
import Queue
import random
import jinja2
import traceback
import tempfile
import subprocess

# FIXME: stop importing *, use as utils/errors
from ansible.utils import *
from ansible.errors import *

# should be True except in debug
CLEANUP_FILES = True
    
################################################

def _executor_hook(job_queue, result_queue):
    ''' callback used by multiprocessing pool '''

    signal.signal(signal.SIGINT, signal.SIG_IGN)
    while not job_queue.empty():
        try:
            job = job_queue.get(block=False)
            runner, host = job
            result_queue.put(runner._executor(host))
        except Queue.Empty:
            pass
        except AnsibleError, ae:
            result_queue.put([host, False, str(ae)])
        except Exception, ee:
            # probably should include the full trace
            result_queue.put([host, False, traceback.format_exc()])
            

################################################

class Runner(object):

    _external_variable_script = None

    def __init__(self, 
        host_list=C.DEFAULT_HOST_LIST, 
        module_path=C.DEFAULT_MODULE_PATH,
        module_name=C.DEFAULT_MODULE_NAME, 
        module_args=C.DEFAULT_MODULE_ARGS, 
        forks=C.DEFAULT_FORKS, 
        timeout=C.DEFAULT_TIMEOUT, 
        pattern=C.DEFAULT_PATTERN,
        remote_user=C.DEFAULT_REMOTE_USER,
        remote_pass=C.DEFAULT_REMOTE_PASS,
        background=0,
        basedir=None,
        setup_cache={},
        transport='paramiko',
        verbose=False):
    
        ''' 
        Constructor
        host_list   -- file on disk listing hosts to manage, or an array of hostnames
        pattern ------ a fnmatch pattern selecting some of the hosts in host_list
        module_path -- location of ansible library on disk
        module_name -- which module to run
        module_args -- arguments to pass to module
        forks -------- how parallel should we be? 1 is extra debuggable.
        remote_user -- who to login as (default root)
        remote_pass -- provide only if you don't want to use keys or ssh-agent
        background --- if non 0, run async, failing after X seconds, -1 == infinite
        setup_cache -- used only by playbook (complex explanation pending)
        '''

        self.setup_cache = setup_cache
       
        self.host_list, self.groups = self.parse_hosts(host_list)
        self.module_path = module_path
        self.module_name = module_name
        self.forks       = int(forks)
        self.pattern     = pattern
        self.module_args = module_args
        self.timeout     = timeout
        self.verbose     = verbose
        self.remote_user = remote_user
        self.remote_pass = remote_pass
        self.background          = background

        if basedir is None: 
            basedir = os.getcwd()
        self.basedir = basedir

        # hosts in each group name in the inventory file
        self._tmp_paths  = {}

        random.seed()
        self.generated_jid = str(random.randint(0, 999999999999))
        self.connector = ansible.connection.Connection(self, transport)

    # *****************************************************

    @classmethod
    def parse_hosts(cls, host_list):
        ''' 
        parse the host inventory file, returns (hosts, groups) 
        [groupname]
        host1
        host2
        '''

        if type(host_list) == list:
            return (host_list, {})

        host_list = os.path.expanduser(host_list)

        if not os.path.exists(host_list):
            raise AnsibleFileNotFound("inventory file not found: %s" % host_list)

        results    = []
        groups     = { 'ungrouped' : [] }
        if not os.access(host_list, os.X_OK):
            # it's a regular file
            lines = file(host_list).read().split("\n")
            group_name = 'ungrouped'
            results    = []
            for item in lines:
                item = item.lstrip().rstrip()
                if item.startswith("#"): 
                    # ignore commented out lines
                    continue
                if item.startswith("["):
                    # looks like a group
                    group_name = item.replace("[","").replace("]","").lstrip().rstrip()
                    groups[group_name] = []
                else:
                    # looks like a regular host
                    groups[group_name].append(item)
                    results.append(item)
        else:
            host_list = os.path.abspath(host_list)
            cls._external_variable_script = host_list
            # it's a script -- expect a return of a JSON hash with group names keyed
            # to lists of hosts
            cmd = subprocess.Popen([host_list], stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False)
            out, err = cmd.communicate()
            try:
                groups = json.loads(out)
            except:
                raise AnsibleError("invalid JSON response from script: %s" % host_list)
            for (groupname, hostlist) in groups.iteritems():
                for host in hostlist:
                    if host not in results:
                        results.append(host)

        return (results, groups)

    # *****************************************************

    def _matches(self, host_name, pattern=None):
        ''' returns if a hostname is matched by the pattern '''

        # a pattern is in fnmatch format but more than one pattern
        # can be strung together with semicolons. ex:
        #   atlanta-web*.example.com;dc-web*.example.com

        if host_name == '':
            return False
        pattern = pattern.replace(";",":")
        subpatterns = pattern.split(":")
        for subpattern in subpatterns:
            # the pattern could be a real glob
            if subpattern == 'all':
                return True
            if fnmatch.fnmatch(host_name, subpattern):
                return True
            # or it could be a literal group name instead
            if subpattern in self.groups:
                if host_name in self.groups[subpattern]:
                    return True
        return False

    # *****************************************************

    def _connect(self, host):
        ''' 
        obtains a connection to the host.
        on success, returns (True, connection) 
        on failure, returns (False, traceback str)
        '''

        try:
            return [ True, self.connector.connect(host) ]
        except AnsibleConnectionFailed, e:
            return [ False, "FAILED: %s" % str(e) ]

    # *****************************************************

    def _return_from_module(self, conn, host, result):
        ''' helper function to handle JSON parsing of results '''

        try:
            # try to parse the JSON response
            return [ host, True, parse_json(result) ]
        except Exception, e:
            # it failed, say so, but return the string anyway
            return [ host, False, "%s/%s" % (str(e), result) ]

    # *****************************************************

    def _delete_remote_files(self, conn, files):
        ''' deletes one or more remote files '''

        if type(files) == str:
            files = [ files ]
        for filename in files:
            if not filename.startswith('/tmp/'):
                raise Exception("not going to happen")
            if CLEANUP_FILES:
                self._exec_command(conn, "rm -rf %s" % filename)

    # *****************************************************

    def _transfer_file(self, conn, source, dest):
        ''' transfers a remote file '''

        conn.put_file(source, dest)

    # *****************************************************

    def _transfer_module(self, conn, tmp, module):
        ''' 
        transfers a module file to the remote side to execute it,
        but does not execute it yet
        '''

        outpath = self._copy_module(conn, tmp, module)
        self._exec_command(conn, "chmod +x %s" % outpath)
        return outpath

    # *****************************************************

    def _transfer_argsfile(self, conn, tmp, args_str):
        ''' 
        transfer arguments as a single file to be fed to the module.
        this is to avoid various shell things being eaten by SSH
        '''
        args_fd, args_file = tempfile.mkstemp()
        args_fo = os.fdopen(args_fd, 'w')
        args_fo.write(args_str)
        args_fo.flush()
        args_fo.close()
        args_remote = os.path.join(tmp, 'arguments')
        self._transfer_file(conn, args_file, args_remote)
        if CLEANUP_FILES:
            os.unlink(args_file)
        return args_remote

    # *****************************************************

    def _execute_module(self, conn, tmp, remote_module_path, module_args, 
        async_jid=None, async_module=None, async_limit=None):
        ''' 
        runs a module that has already been transferred, but first
        modifies the command using setup_cache variables (see playbook)
        '''

        args = module_args
        if type(args) == list:
            args = [ str(x) for x in module_args ]
            args = " ".join(args)
        inject_vars = self.setup_cache.get(conn.host,{})

        # if the host file was an external script, execute it with the hostname
        # as a first parameter to get the variables to use for the host
        if Runner._external_variable_script is not None:
            host = conn.host
            cmd = subprocess.Popen([Runner._external_variable_script, host],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=False
            )
            out, err = cmd.communicate()
            inject2 = {}
            try:
                inject2 = json.loads(out)
            except:
                raise AnsibleError("%s returned invalid result when called with hostname %s" % (
                    Runner._external_variable_script,
                    host
                ))
            inject_vars.update(inject2)    

        # store injected variables in the templates
        if self.module_name == 'setup':
            for (k,v) in inject2.iteritems():
                args = "%s %s=%s" % (args, k, v)

        # the metadata location for the setup module is transparently managed
        # since it's an 'internals' module, kind of a black box. See playbook
        # other modules are not allowed to have this kind of handling
        if remote_module_path.endswith("/setup") and args.find("metadata=") == -1:
            if self.remote_user == 'root':
                args = "%s metadata=/etc/ansible/setup" % args
            else:
                args = "%s metadata=~/.ansible/setup" % args

        template = jinja2.Template(args)
        args = template.render(inject_vars)

        argsfile = self._transfer_argsfile(conn, tmp, args)
        if async_jid is None:
            cmd = "%s %s" % (remote_module_path, argsfile)
        else:
            args = [str(x) for x in [remote_module_path, async_jid, async_limit, async_module, argsfile]]
            cmd = " ".join(args)
        result = self._exec_command(conn, cmd)
        return result

    # *****************************************************

    def _execute_normal_module(self, conn, host, tmp):
        ''' 
        transfer & execute a module that is not 'copy' or 'template'
        because those require extra work.
        '''

        # hack to make the 'shell' module keyword really be executed
        # by the command module
        if self.module_name == 'shell':
            self.module_name = 'command'
            self.module_args.append("#USE_SHELL")

        module = self._transfer_module(conn, tmp, self.module_name)
        result = self._execute_module(conn, tmp, module, self.module_args)

        # when running the setup module, which pushes vars to the host and ALSO
        # returns them (+factoids), store the variables that were returned such that commands
        # run AFTER setup use these variables for templating when executed
        # from playbooks
        if self.module_name == 'setup':
            host = conn.host
            try:
                var_result = parse_json(result)
            except:
                var_result = {}

        return self._return_from_module(conn, host, result)

    # *****************************************************

    def _execute_async_module(self, conn, host, tmp):
        ''' 
        transfer the given module name, plus the async module
        and then run the async module wrapping the other module
        '''

        async  = self._transfer_module(conn, tmp, 'async_wrapper')
        module = self._transfer_module(conn, tmp, self.module_name)
        result = self._execute_module(conn, tmp, async, self.module_args,
           async_module=module, 
           async_jid=self.generated_jid, 
           async_limit=self.background
        )
        return self._return_from_module(conn, host, result)

    # *****************************************************

    def _parse_kv(self, args):
        # FIXME: move to utils
        ''' helper function to convert a string of key/value items to a dict '''

        options = {}
        for x in args:
            if x.find("=") != -1:
                k, v = x.split("=")
                options[k]=v
        return options

    # *****************************************************

    def _execute_copy(self, conn, host, tmp):
        ''' handler for file transfer operations '''

        # load up options
        options = self._parse_kv(self.module_args)
        source = options['src']
        dest   = options['dest']
        
        # transfer the file to a remote tmp location
        tmp_path = tmp
        tmp_src = tmp_path + source.split('/')[-1]
        self._transfer_file(conn, path_dwim(self.basedir, source), tmp_src)

        # install the copy  module
        self.module_name = 'copy'
        module = self._transfer_module(conn, tmp, 'copy')

        # run the copy module
        args = [ "src=%s" % tmp_src, "dest=%s" % dest ]
        result1 = self._execute_module(conn, tmp, module, args)
        results1 = self._return_from_module(conn, host, result1)
        (host, ok, data) = results1

        # magically chain into the file module
        if ok:
            # unless failed, run the file module to adjust file aspects
            old_changed = data.get('changed', False)
            module = self._transfer_module(conn, tmp, 'file')
            args = [ "%s=%s" % (k,v) for (k,v) in options.items() ]
            result2 = self._execute_module(conn, tmp, module, args)
            results2 = self._return_from_module(conn, host, result2)
            (host, ok, data2) = results2
            new_changed = data2.get('changed', False)
            data['changed'] = old_changed or new_changed
            data.update(data2)
            return (host, ok, data)
        else:
            # copy failed, return orig result without going through 'file' module
            return results1  

    # *****************************************************

    def _execute_template(self, conn, host, tmp):
        ''' handler for template operations '''

        # load up options
        options  = self._parse_kv(self.module_args)
        source   = options['src']
        dest     = options['dest']
        metadata = options.get('metadata', None)

        if metadata is None:
            if self.remote_user == 'root':
                metadata = '/etc/ansible/setup'
            else:
                metadata = '~/.ansible/setup'

        # first copy the source template over
        tpath = tmp
        tempname = os.path.split(source)[-1]
        temppath = tpath + tempname
        self._transfer_file(conn, path_dwim(self.basedir, source), temppath)

        # install the template module
        template_module = self._transfer_module(conn, tmp, 'template')

        # run the template module
        args = [ "src=%s" % temppath, "dest=%s" % dest, "metadata=%s" % metadata ]
        result1 = self._execute_module(conn, tmp, template_module, args)
        results1 = self._return_from_module(conn, host, result1)
        (host, ok, data) = results1

        # magically chain into the file module
        if ok:
            # unless failed, run the file module to adjust file aspects
            old_changed = data.get('changed', False)
            module = self._transfer_module(conn, tmp, 'file')
            args = [ "%s=%s" % (k,v) for (k,v) in options.items() ]
            result2 = self._execute_module(conn, tmp, module, args)
            results2 = self._return_from_module(conn, host, result2)
            (host, ok, data2) = results2
            new_changed = data2.get('changed', False)
            data['changed'] = old_changed or new_changed
            data.update(data2)
            return (host, ok, data)
        else:
            # copy failed, return orig result without going through 'file' module
            return results1

    # *****************************************************

    def _executor(self, host):
        ''' 
        callback executed in parallel for each host.
        returns (hostname, connected_ok, extra)
        where extra is the result of a successful connect
        or a traceback string
        '''

        # depending on whether it's a normal module,
        # or a request to use the copy or template
        # module, call the appropriate executor function

        ok, conn = self._connect(host)
        if not ok:
            return [ host, False, conn ]

        tmp = self._get_tmp_path(conn)
        result = None
        if self.module_name not in [ 'copy', 'template' ]:
            if self.background == 0:
                result = self._execute_normal_module(conn, host, tmp)
            else:
                result = self._execute_async_module(conn, host, tmp)

        elif self.module_name == 'copy':
            result = self._execute_copy(conn, host, tmp)
        elif self.module_name == 'template':
            result = self._execute_template(conn, host, tmp)
        else:
            # this would be a coding error in THIS module
            # shouldn't occur
            raise Exception("???")

        self._delete_remote_files(conn, tmp)
        conn.close()
        
        return result

    # *****************************************************

    def _exec_command(self, conn, cmd):
        ''' execute a command string over SSH, return the output '''

        msg = '%s: %s' % (self.module_name, cmd)
        # log remote command execution
        conn.exec_command('/usr/bin/logger -t ansible -p auth.info "%s"' % msg)
        # now run actual command
        stdin, stdout, stderr = conn.exec_command(cmd)
        return "\n".join(stdout.readlines())

    # *****************************************************

    def _get_tmp_path(self, conn):
        ''' gets a temporary path on a remote box '''

        result = self._exec_command(conn, "mktemp -d /tmp/ansible.XXXXXX")
        return result.split("\n")[0] + '/'

    # *****************************************************

    def _copy_module(self, conn, tmp, module):
        ''' transfer a module over SFTP, does not run it '''

        if module.startswith("/"):
            raise AnsibleFileNotFound("%s is not a module" % module)
        in_path = os.path.expanduser(os.path.join(self.module_path, module))
        if not os.path.exists(in_path):
            raise AnsibleFileNotFound("module not found: %s" % in_path)

        out_path = tmp + module
        conn.put_file(in_path, out_path)
        return out_path

    # *****************************************************

    def match_hosts(self, pattern):
        ''' return all matched hosts fitting a pattern '''

        return [ h for h in self.host_list if self._matches(h, pattern) ]

    # *****************************************************

    def run(self):
        ''' xfer & run module on all matched hosts '''
       
        # find hosts that match the pattern
        hosts = self.match_hosts(self.pattern)
        if len(hosts) == 0:
            return {
                'contacted' : {},
                'dark'      : {}
            }

        # attack pool of hosts in N forks
        # _executor_hook does all of the work
        hosts = [ (self,x) for x in hosts ]

        if self.forks > 1:
            job_queue = multiprocessing.Manager().Queue()
            result_queue = multiprocessing.Manager().Queue()
 
            for i in hosts:
                job_queue.put(i)
 
            workers = []
            for i in range(self.forks):
                tmp = multiprocessing.Process(target=_executor_hook,
                                      args=(job_queue, result_queue))
                tmp.start()
                workers.append(tmp)
 
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
 
        else:
            results = [ x._executor(h) for (x,h) in hosts ]

        # sort hosts by ones we successfully contacted
        # and ones we did not so that we can return a 
        # dictionary containing results of everything

        results2 = {
          "contacted" : {},
          "dark"      : {}
        }
        hosts_with_results = []
        for x in results:
            (host, is_ok, result) = x
            hosts_with_results.append(host)
            if not is_ok:
                results2["dark"][host] = result
            else:
                results2["contacted"][host] = result
        # hosts which were contacted but never got a chance
        # to return a result before we exited/ctrl-c'd
        # perhaps these shouldn't be 'dark' but I'm not sure if they fit
        # anywhere else.
        for host in self.match_hosts(self.pattern):
            if host not in hosts_with_results:
                results2["dark"][host] = {}
                
        return results2


