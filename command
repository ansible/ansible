#!/usr/bin/python

try:
    import json
except ImportError:
    import simplejson as json

import subprocess
import sys
import datetime
import traceback

args = sys.argv[1:]
startd = datetime.datetime.now()

try:
    cmd = subprocess.Popen(args, shell=False, 
        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = cmd.communicate()
except:
    print json.dumps({
        "failed" : 1,
        "traceback" : traceback.format_exc()
    })   
    sys.exit(1)

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
