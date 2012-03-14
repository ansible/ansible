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

if len(sys.argv) == 1:
    print json.dumps({
        "failed" : True,
        "msg"    : "the command module requires arguments (-a)"
    })
    sys.exit(1)

argfile = sys.argv[1]
if not os.path.exists(argfile):
    print json.dumps({
        "failed" : True,
        "msg"    : "Argument file not found"
    })
    sys.exit(1)

args = open(argfile, 'r').read()
args = shlex.split(args)

if not len(args):
    print json.dumps({
        "failed" : True,
        "msg"    : "the command module requires arguments (-a)"
    })
    sys.exit(1)


startd = datetime.datetime.now()

try:
    cmd = subprocess.Popen(args, shell=False, 
        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = cmd.communicate()
except (OSError, IOError), e:
    print json.dumps({
        "failed": 1,
        "msg": str(e),
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
   "stdout" : out.strip(),
   "stderr" : err.strip(),
   "rc"     : cmd.returncode,
   "start"  : str(startd),
   "end"    : str(endd),
   "delta"  : str(delta),
}

print json.dumps(result)
