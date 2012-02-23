#!/usr/bin/python

import json
import subprocess
import sys
import datetime

args = sys.argv[1:]
startd = datetime.datetime.now()

cmd = subprocess.Popen(args, shell=True, 
    stdout=subprocess.PIPE, stderr=subprocess.PIPE)

out, err = cmd.communicate()
endd = datetime.datetime.now()
delta = endd - startd

result = {
   "stdout" : out,
   "stderr" : err,
   "rc"     : cmd.returncode,
   "start"  : str(startd),
   "end"    : str(endd),
   "delta"  : str(delta),
}

print json.dumps(result)
