# Copyright (c) 2012 Michael DeHaan <michael.dehaan@gmail.com>
#
# Permission is hereby granted, free of charge, to any person 
# obtaining a copy of this software and associated documentation 
# files (the "Software"), to deal in the Software without restriction, 
# including without limitation the rights to use, copy, modify, merge, 
# publish, distribute, sublicense, and/or sell copies of the Software, 
# and to permit persons to whom the Software is furnished to do so, 
# subject to the following conditions:
#
# The above copyright notice and this permission notice shall be 
# included in all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, 
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF 
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. 
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR 
# ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF 
# CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION 
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

import fnmatch
import multiprocessing
from itertools import izip
import os
import json
import traceback
import select

# non-core 
import paramiko

DEFAULT_HOST_LIST      = '/etc/ansible/hosts'
DEFAULT_MODULE_PATH    = '/usr/share/ansible'
DEFAULT_MODULE_NAME    = 'ping'
DEFAULT_PATTERN        = '*'
DEFAULT_FORKS          = 3
DEFAULT_MODULE_ARGS    = ''
DEFAULT_TIMEOUT        = 60
DEFAULT_REMOTE_USER    = 'root'

def _executor_hook(x):
    (runner, host) = x
    return runner._executor(host)

class Runner(object):

   def __init__(self, 
       host_list=DEFAULT_HOST_LIST, 
       module_path=DEFAULT_MODULE_PATH,
       module_name=DEFAULT_MODULE_NAME, 
       module_args=DEFAULT_MODULE_ARGS, 
       forks=DEFAULT_FORKS, 
       timeout=DEFAULT_TIMEOUT, 
       pattern=DEFAULT_PATTERN,
       remote_user=DEFAULT_REMOTE_USER,
       verbose=False):
      

       '''
       Constructor.
       '''

       self.host_list   = self._parse_hosts(host_list)
       self.module_path = module_path
       self.module_name = module_name
       self.forks       = forks
       self.pattern     = pattern
       self.module_args = module_args
       self.timeout     = timeout
       self.verbose     = verbose
       self.remote_user = remote_user

   def _parse_hosts(self, host_list):
        ''' parse the host inventory file if not sent as an array '''
        if type(host_list) != list:
            host_list = os.path.expanduser(host_list)
            return file(host_list).read().split("\n")
        return host_list


   def _matches(self, host_name):
       ''' returns if a hostname is matched by the pattern '''
       if host_name == '':
           return False
       if fnmatch.fnmatch(host_name, self.pattern):
           return True
       return False

   def _connect(self, host):
       ''' obtains a paramiko connection to the host '''
       ssh = paramiko.SSHClient()
       ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
       try:
          ssh.connect(host, username=self.remote_user,
              allow_agent=True, look_for_keys=True)
          return [ True, ssh ]
       except:
          return [ False, traceback.format_exc() ]

   def _executor(self, host):
       ''' callback executed in parallel for each host '''
       # TODO: try/catch returning none

       ok, conn = self._connect(host)
       if not ok:
           return [ host, False, conn ]

       if self.module_name != "copy":
           # transfer a module, set it executable, and run it
           outpath = self._copy_module(conn)
           self._exec_command(conn, "chmod +x %s" % outpath)
           cmd = self._command(outpath)
           result = self._exec_command(conn, cmd)
           conn.close()
           return [ host, True, json.loads(result) ]
       else:
           # SFTP file copy module is not really a module
           ftp = conn.open_sftp()
           ftp.put(self.module_args[0], self.module_args[1])
           ftp.close()
           conn.close()
           return [ host, True, 1 ]
           

   def _command(self, outpath):
       ''' form up a command string '''
       cmd = "%s %s" % (outpath, " ".join(self.module_args))
       return cmd

   def _exec_command(self, conn, cmd):
       ''' execute a command over SSH '''
       stdin, stdout, stderr = conn.exec_command(cmd)
       results = "\n".join(stdout.readlines())
       return results

   def _copy_module(self, conn):
       ''' transfer a module over SFTP '''
       in_path = os.path.expanduser(
           os.path.join(self.module_path, self.module_name)
       )
       out_path = os.path.join(
           "/var/spool/", 
           "ansible_%s" % self.module_name
       )
       sftp = conn.open_sftp()
       sftp.put(in_path, out_path)
       sftp.close()
       return out_path

   def run(self):
       ''' xfer & run module on all matched hosts '''
       hosts = [ h for h in self.host_list if self._matches(h) ]
       pool = multiprocessing.Pool(self.forks)
       hosts = [ (self,x) for x in hosts ]
       results = pool.map(_executor_hook, hosts)
       results2 = {
          "contacted" : {},
          "dark"      : {}
       }
       for x in results:
           (host, is_ok, result) = x
           if not is_ok:
               results2["failed"][host] = result
           else:
               results2["successful"][host] = result
       return results2


if __name__ == '__main__':

    # test code...

    r = Runner(
       host_list = DEFAULT_HOST_LIST,
       module_name='ping',
       module_args='',
       pattern='*',
       forks=3
    )   
    print r.run()

 

