#!/usr/bin/python
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
# Make coding more python3-ish

from __future__ import (absolute_import, division)
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: redhat_subsc_status
short_description: host redhat subscription status
description:
    - Show the status of redhat subscription
    - Can save in .csv file
version_added: "2.5"
options:
  status:
    description:
      - Show the status of redhat subscription
    required: true
    default: null
    type: bool
  export_csv:
    description:
      - Save the status output into /tmp/report_subscription_status.csv file generated automatically for the same module
    required: false
    default: null
    type: bool
      
author:
    - "Kevyn Perez (@Deathice)"
    - "Luis Perez (@dbinary)"
'''

RETURN = '''
msg:
    description: Return status from redhat subscription
    returned: always
    type: string
    sample: Subscribed
'''

EXAMPLES = '''
# Check the status for redhat subscription
- redhat_subsc_status:
    status: true

# Check the status for redhat subscription and export to /tmp/report_subscription_status.csv file
- redhat_subsc_status:
    status: true
    export_csv: true

'''


from ansible.module_utils.basic import *
import sys
import csv
import os
import subprocess
import re

def redhat_subsc_status(module):
  
  is_error = False
  has_changed = False
  
  sm = module.params['status']
  gen_csv = module.params['export_csv']

  if sm:
    output = module.run_command('/usr/sbin/subscription-manager list')

    if 'Subscribed' in output[1]:
      resp = {
        "Subscription_status": "True"
      }

    else:
      resp = {
        "Subscription_status": "False"
      }
    meta = {"status" : "OK", "response" : resp}

    if gen_csv:
      module.params = ["host", cmd]
      nm = "/tmp/report_subscription_status.csv"
      with open (nm, 'wb') as nm:
        wr = csv.writer(nm, quoting=csv.QUOTE_ALL)
        wr.writerow(module.params)

  return is_error, has_changed, meta
  

def main():

  fields = {
    "status": {
      "required": True,
      "type": "bool",
    },
    "export_csv": {
      "required": False,
      "type": "bool",
    },
  }

  module = AnsibleModule(argument_spec=fields)

  #is_error, has_changed, result = redhat_subsc_status(module.params)
  is_error, has_changed, result = redhat_subsc_status(module)

  if not is_error:
    module.exit_json(changed=has_changed, meta=result)
  else:
    module.fail_json(msg="Error when consult the subscription", meta=result)


if __name__ == '__main__':
  main()
