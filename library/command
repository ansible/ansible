#!/usr/bin/python

# (c) 2012, Michael DeHaan <michael.dehaan@gmail.com>, and others
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

import subprocess
import sys
import datetime
import traceback
import shlex
import os
import syslog

argfile = sys.argv[1]
args = open(argfile, 'r').read()
syslog.openlog('ansible-%s' % os.path.basename(__file__))
syslog.syslog(syslog.LOG_NOTICE, 'Invoked with %s' % args)

shell = False

if args.find("#USE_SHELL") != -1:
   args = args.replace("#USE_SHELL", "")
   shell = True

check_args = shlex.split(args)
for x in check_args:
   if x.startswith("creates="):
       # do not run the command if the line contains creates=filename
       # and the filename already exists.  This allows idempotence 
       # of command executions.
       (k,v) = x.split("=",1)
       if os.path.exists(v):
           print json.dumps({
               "cmd"     : args,
               "stdout"  : "skipped, since %s exists" % v,
               "skipped" : True,
               "changed" : False,
               "stderr"  : "",
               "rc"      : 0,
           })
           sys.exit(0)
       args = args.replace(x,'')
       

if not shell:
    args = shlex.split(args)

startd = datetime.datetime.now()

try:
    cmd = subprocess.Popen(args, shell=shell, 
        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = cmd.communicate()
except (OSError, IOError), e:
    print json.dumps({
        "cmd"    : args,
        "failed" : 1,
        "msg"    : str(e),
        })
    sys.exit(1)
except:
    print json.dumps({
        "failed" : 1,
        "msg" : traceback.format_exc()
    })   
    sys.exit(1)

endd = datetime.datetime.now()
delta = endd - startd

if out is None:
   out = ''
if err is None:
   err = ''

result = {
   "cmd"     : args,
   "stdout"  : out.strip(),
   "stderr"  : err.strip(),
   "rc"      : cmd.returncode,
   "start"   : str(startd),
   "end"     : str(endd),
   "delta"   : str(delta),
   "changed" : True
}

print json.dumps(result)
