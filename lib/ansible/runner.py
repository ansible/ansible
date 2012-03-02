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

try:
    import json
except ImportError:
    import simplejson as json

import fnmatch
import multiprocessing
import signal
import os
import traceback
import paramiko # non-core dependency
import ansible.constants as C 
import Queue

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

class Runner(object):

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
        '''

        # save input values
       
        self.host_list, self.groups = self.parse_hosts(host_list)
        self.module_path = module_path
        self.module_name = module_name
        self.forks       = forks
        self.pattern     = pattern
        self.module_args = module_args
        self.timeout     = timeout
        self.verbose     = verbose
        self.remote_user = remote_user
        self.remote_pass = remote_pass
        # hosts in each group name in the inventory file
        self._tmp_paths  = {}

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
        lines = file(host_list).read().split("\n")
        groups     = {}
        group_name = 'ungrouped'
        results    = []
        for item in lines:
            if item.startswith("["):
                group_name = item.replace("[","").replace("]","").lstrip().rstrip()
                groups[group_name] = []
            else:
                groups[group_name].append(item)
                results.append(item)

        return (results, groups)


    def _matches(self, host_name, pattern=None):
        ''' returns if a hostname is matched by the pattern '''
        # a pattern is in fnmatch format but more than one pattern
        # can be strung together with semicolons. ex:
        #   atlanta-web*.example.com;dc-web*.example.com

        if host_name == '':
            return False
        subpatterns = pattern.split(";")
        for subpattern in subpatterns:
            # the pattern could be a real glob
            if fnmatch.fnmatch(host_name, subpattern):
                return True
            # or it could be a literal group name instead
            if self.groups.has_key(subpattern):
                if host_name in self.groups[subpattern]:
                    return True
        return False

    def _connect(self, host):
        ''' 
        obtains a paramiko connection to the host.
        on success, returns (True, connection) 
        on failure, returns (False, traceback str)
        '''
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            # try paramiko
            ssh.connect(host, username=self.remote_user, allow_agent=True, 
              look_for_keys=True, password=self.remote_pass, timeout=self.timeout)
            return [ True, ssh ]
        except Exception, e:
            # it failed somehow, return the failure string
            return [ False, str(e) ]

    def _return_from_module(self, conn, host, result):
        ''' helper function to handle JSON parsing of results '''
        # disconnect from paramiko/SSH
        conn.close()
        try:
            # try to parse the JSON response
            return [ host, True, json.loads(result) ]
        except:
            # it failed, say so, but return the string anyway
            return [ host, False, result ]

    def _delete_remote_files(self, conn, files):
        ''' deletes one or more remote files '''
        for filename in files:
            self._exec_command(conn, "rm -f %s" % filename)

    def _transfer_file(self, conn, source, dest):
        ''' transfers a remote file '''
        self.remote_log(conn, 'COPY remote:%s local:%s' % (source, dest))
        sftp = conn.open_sftp()
        sftp.put(source, dest)
        sftp.close()

    def _transfer_module(self, conn):
        ''' 
        transfers a module file to the remote side to execute it,
        but does not execute it yet
        '''
        outpath = self._copy_module(conn)
        self._exec_command(conn, "chmod +x %s" % outpath)
        return outpath

    def _execute_module(self, conn, outpath):
        ''' 
        runs a module that has already been transferred
        '''
        cmd = self._command(outpath)
        result = self._exec_command(conn, cmd)
        self._delete_remote_files(conn, [ outpath ])
        return result

    def _execute_normal_module(self, conn, host):
        ''' 
        transfer & execute a module that is not 'copy' or 'template'
        because those require extra work.
        '''
        module = self._transfer_module(conn)
        result = self._execute_module(conn, module)
        return self._return_from_module(conn, host, result)

    def _parse_kv(self, args):
        ''' helper function to convert a string of key/value items to a dict '''
        options = {}
        for x in args:
            if x.find("=") != -1:
               k, v = x.split("=")
               options[k]=v
        return options

    def _execute_copy(self, conn, host):
        ''' handler for file transfer operations '''

        # load up options
        options = self._parse_kv(self.module_args)
        source = options['src']
        dest   = options['dest']
        
        # transfer the file to a remote tmp location
        tmp_path = self._get_tmp_path(conn)
        tmp_src = tmp_path + source.split('/')[-1]
        self._transfer_file(conn, source, tmp_src)

        # install the copy  module
        self.module_name = 'copy'
        module = self._transfer_module(conn)

        # run the copy module
        self.module_args = [ "src=%s" % tmp_src, "dest=%s" % dest ]
        result = self._execute_module(conn, module)
        self._delete_remote_files(conn, tmp_src)
        return self._return_from_module(conn, host, result)

    def _execute_template(self, conn, host):
        ''' handler for template operations '''

        # load up options
        options  = self._parse_kv(self.module_args)
        source   = options['src']
        dest     = options['dest']
        metadata = options.get('metadata', '/etc/ansible/setup')

        # first copy the source template over
        tempname = os.path.split(source)[-1]
        temppath = self._get_tmp_path(conn) + tempname
        self._transfer_file(conn, source, temppath)

        # install the template module
        self.module_name = 'template'
        module = self._transfer_module(conn)

        # run the template module
        self.module_args = [ "src=%s" % temppath, "dest=%s" % dest, "metadata=%s" % metadata ]
        result = self._execute_module(conn, module)
        self._delete_remote_files(conn, [ temppath ])
        return self._return_from_module(conn, host, result)


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
        if self.module_name not in [ 'copy', 'template' ]:
            return self._execute_normal_module(conn, host)
        elif self.module_name == 'copy':
            return self._execute_copy(conn, host)
        elif self.module_name == 'template':
            return self._execute_template(conn, host)
        else:
            # this would be a coding error in THIS module
            # shouldn't occur
            raise Exception("???")

    def _command(self, outpath):
        ''' form up a command string for running over SSH '''
        cmd = "%s %s" % (outpath, " ".join(self.module_args))
        return cmd

    def remote_log(self, conn, msg):
        ''' this is the function we use to log things '''
        stdin, stdout, stderr = conn.exec_command('/usr/bin/logger -t ansible -p auth.info %r' % msg)
        # TODO: maybe make that optional

    def _exec_command(self, conn, cmd):
        ''' execute a command string over SSH, return the output '''
        msg = '%s: %s' % (self.module_name, cmd)
        self.remote_log(conn, msg)
        stdin, stdout, stderr = conn.exec_command(cmd)
        results = "\n".join(stdout.readlines())
        return results

    def _get_tmp_path(self, conn):
        ''' gets a temporary path on a remote box '''

        if conn not in self._tmp_paths:
            output = self._exec_command(conn, "mktemp -d /tmp/ansible.XXXXXX")
            self._tmp_paths[conn] = output.split("\n")[0] + '/'
            
        return self._tmp_paths[conn]

    def _copy_module(self, conn):
        ''' transfer a module over SFTP, does not run it '''
        in_path = os.path.expanduser(
            os.path.join(self.module_path, self.module_name)
        )
        out_path = self._get_tmp_path(conn) + self.module_name
        sftp = conn.open_sftp()
        sftp.put(in_path, out_path)
        sftp.close()
        return out_path

    def match_hosts(self, pattern):
        ''' return all matched hosts fitting a pattern '''
        return [ h for h in self.host_list if self._matches(h, pattern) ]

    def run(self):
        ''' xfer & run module on all matched hosts '''
        
        # find hosts that match the pattern
        hosts = self.match_hosts(self.pattern)
        
        # attack pool of hosts in N forks
        # _executor_hook does all of the work
        hosts = [ (self,x) for x in hosts ]
        if self.forks > 1:
            job_queue = multiprocessing.Queue()
            result_queue = multiprocessing.Queue()
 
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
                print 'parent received ctrl-c'
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


