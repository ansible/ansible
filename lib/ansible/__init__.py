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
from multiprocessing import Process, Pipe
from itertools import izip
import os
import json

# non-core 
import paramiko

# TODO -- library should have defaults, not just CLI
# update Runner constructor below to use

DEFAULT_HOST_LIST      = '~/.ansible_hosts'
DEFAULT_MODULE_PATH    = '~/ansible'
DEFAULT_MODULE_NAME    = 'ping'
DEFAULT_PATTERN        = '*'
DEFAULT_FORKS          = 3
DEFAULT_MODULE_ARGS    = ''

class Pooler(object):

    # credit: http://stackoverflow.com/questions/3288595/multiprocessing-using-pool-map-on-a-function-defined-in-a-class

    @classmethod
    def spawn(cls, f):
        def fun(pipe,x):
            pipe.send(f(x))
            pipe.close()
        return fun

    @classmethod
    def parmap(cls, f, X):
        pipe=[Pipe() for x in X]
        proc=[Process(target=cls.spawn(f),args=(c,x)) for x,(p,c) in izip(X,pipe)]
        [p.start() for p in proc]
        [p.join() for p in proc]
        return [p.recv() for (p,c) in pipe]

class Runner(object):

   def __init__(self, host_list=[], module_path=None,
       module_name=None, module_args=[], 
       forks=3, timeout=60, pattern='*'):

       self.host_list   = host_list
       self.module_path = module_path
       self.module_name = module_name
       self.forks       = forks
       self.pattern     = pattern
       self.module_args = module_args
       self.timeout     = timeout
 

   def _matches(self, host_name):
       if host_name == '':
           return False
       if fnmatch.fnmatch(host_name, self.pattern):
           return True
       return False

   def _connect(self, host):
       ssh = paramiko.SSHClient()
       ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
       try:
          ssh.connect(host, username='root',
              allow_agent=True, look_for_keys=True)
          return ssh
       except:
          return None

   def _executor(self, host):
       # TODO: try/catch returning none
       conn = self._connect(host)
       if not conn:
           return [ host, None ]
       if self.module_name != "copy":
           outpath = self._copy_module(conn)
           self._exec_command(conn, "chmod +x %s" % outpath)
           cmd = self._command(outpath)
           result = self._exec_command(conn, cmd)
           result = json.loads(result)
       else:
           ftp = conn.open_sftp()
           ftp.put(self.module_args[0], self.module_args[1])
           ftp.close()
           return [ host, 1 ]
           
       return [ host, result ]

   def _command(self, outpath):
       cmd = "%s %s" % (outpath, " ".join(self.module_args))
       return cmd

   def _exec_command(self, conn, cmd):
       stdin, stdout, stderr = conn.exec_command(cmd)
       results = stdout.read()
       return results

   def _copy_module(self, conn):
       inpath = os.path.expanduser(os.path.join(self.module_path, self.module_name))
       outpath = os.path.join("/var/spool/", "ansible_%s" % self.module_name)
       ftp = conn.open_sftp()
       ftp.put(inpath, outpath)
       ftp.close()
       return outpath

   def run(self):
       hosts = [ h for h in self.host_list if self._matches(h) ]
       def executor(x):
           return self._executor(x)
       results = Pooler.parmap(executor, hosts)
       by_host = dict(results)
       return by_host


if __name__ == '__main__':


    # TODO: if host list is string load from file

    r = Runner(
       host_list = [ '127.0.0.1' ],
       module_path='~/ansible',
       module_name='ping',
       module_args='',
       pattern='*',
       forks=3
    )   
    print r.run()

 

