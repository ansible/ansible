#!/usr/bin/env python
# (c) 2012, Gregory Duchatelet <greg@2lm.fr>
######################################################################


import sys
import xmlrpclib
import shlex

try:
	import json
except:
	import simplejson as json

import os
import logging
sys.path.insert (1, os.path.abspath("%s/svn_sysadmin/ezscripts/lib/python"%os.environ["HOME"]))
sys.path.insert (2, '/usr/local/ez/lib/python')
from ez_admin import *


###################################################
# executed with no parameters, return the list of
# all groups and hosts

if len(sys.argv) == 2 and (sys.argv[1] == '--list'):
	logging.root.setLevel(logging.INFO)
	server = EzServer(None, False)
	print json.dumps(server.list_ansible())
	sys.exit(0)

#####################################################
# executed with a hostname as a parameter, return the
# variables for that host

elif len(sys.argv) == 3 and (sys.argv[1] == '--host'):
	# TODO: not yet implemented...
	print json.dumps({})
	#server.set_list_format("json")
	#print server.list_hosts(sys.argv[2]) 
	sys.exit(0)

else:
	print "usage: --list  ..OR.. --host <hostname>"
	sys.exit(1)

