#!/usr/bin/python

from __future__ import absolute_import, division, print_function

__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
author: Vasiliy Gokoyev (@k3it)
module: aix_dumpdevice
short_description: Checks and expands AIX dump device
description:
  - Set the largest dump device to equal or greater than the estimated dump size.  check_mode is supported
version_added: "2.7"
options:
  ratio:
    description:
      - If the largest dump device is too small set dump device to at least ratio x estimated dump size.
    required: false
    default: 1.0
''' 

EXAMPLES = '''
- name: Expand the largerst AIX dump device to at least 1.1 x estimated dump size
  aix_dumpdevice:
    ratio: 1.1
'''

RETURN = '''
changed:
  description: Return true if the dump device was expanded
  returned: always
  type: boolean
  version_added: 2.7
msg:
  description: Return message regarding the state of the dump device.
  returned: always
  type: string
  version_added: 2.7
'''

from ansible.module_utils.basic import *

import subprocess 

import datetime, math
import os, glob, re

def main():
	
	fields = {
		"ratio" : {"required": False, "type": 'float', "default": 1.0},
	}

	module = AnsibleModule(argument_spec=fields, supports_check_mode=True)

	timestamp = str(datetime.datetime.now())
	ratio = module.params['ratio']

	check, dumplv, dump_shortage = _check_dump_dev(ratio)

	msg = ("Dump device {0} shortage {1} MB".format(dumplv, dump_shortage))

	if dump_shortage < 0:
		module.fail_json(msg = ("Failed to execute /usr/lib/ras/dumpcheck -p or dump dev is not set"))

    	if module.check_mode:
		changed = check
        	module.exit_json(changed=changed, msg=msg)

	if dump_shortage > 0:
		result, msg = _increase_dump_size(dumplv,dump_shortage)

	else:
		msg=''
		result = False


        module.exit_json(changed=result, msg=msg)

def _increase_dump_size(dumplv, dump_shortage):
	# find the partion size
	command = ["lslv"]
	command.extend([dumplv])
	result = subprocess.Popen(command, stderr=subprocess.STDOUT, stdout=subprocess.PIPE, stdin=subprocess.PIPE)
	output = result.communicate()[0]

        returncode = result.returncode
        if returncode is not 0:
                return False

	pp_size = int(re.findall('PP SIZE:.+?(\d+)', output)[0])
	lvs = math.ceil(dump_shortage/pp_size) 

	# extend the lv
	command = ["extendlv"]
	command.extend([dumplv, str(lvs)])
	result = subprocess.Popen(command, stderr=subprocess.STDOUT, stdout=subprocess.PIPE, stdin=subprocess.PIPE)
	output = result.communicate()[0]

        returncode = result.returncode
        if returncode is 0:
		msg = ("Extended {0} by {1} MB".format(dumplv, lvs*pp_size))
		return True, msg
	else:
		msg = ("Failed while running {0}".format(command))
		return False, msg


def _check_dump_dev(ratio):
	# checks dumpdev and returns estimate
	command = ["/usr/lib/ras/dumpcheck"]
	command.extend(["-p"])
	result = subprocess.Popen(command, stderr=subprocess.STDOUT, stdout=subprocess.PIPE, stdin=subprocess.PIPE)
	output = result.communicate()[0]
	
	check = False
	dumplv = None
	dump_size_shortage = 0


	if output.find("too small.") > 0:
		dumpinfo = output.splitlines()
		dumplv = dumpinfo[3].strip()
		dump_size_mb = int(dumpinfo[5].strip())/1024
		dump_estimate_mb = int(dumpinfo[7].strip())*ratio/1024
		dump_size_shortage = dump_estimate_mb - dump_size_mb
		check = True

	returncode = result.returncode
	if returncode is 0:
		return check, dumplv, dump_size_shortage
	else:
		return check, dumplv, -1

	

if __name__ == '__main__':
	main()
