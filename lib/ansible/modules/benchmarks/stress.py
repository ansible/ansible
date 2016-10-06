#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2016, Hugh Ma <Hugh.Ma@flextronics.com>
#
# This module is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This software is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this software.  If not, see <http://www.gnu.org/licenses/>.

DOCUMENTATION = '''
---
module: stress
short_description: Execute the Stress benchmark
description:
 - Use this module to run the Stress benchmark
 - https://people.seas.harvard.edu/~apw/stress/
version_added: "2.3"
options:
  chdir:
    description:
     - change working directory
    required: false
    default: null
  cpu:
    description:
     - number of cpus to stress
    required: true
  delay:
    description:
     - piggybacks off the at module as a action plugin to run benchmark at a schedule time
    required: false
  executable:
    description:
     - path to stress executable if running from source
    required: false
  dest:
    description:
     - absolute path of file to write stdout to
    required: false
  timeout:
    description:
     - Total time to run stress for.
    required: True
requirements:
 - stress
author: "Hugh Ma <Hugh.Ma@flextronics.com>"
'''

EXAMPLES = '''
# Run stress for 10 seconds on 1 cpu
- stress: timeout=10 cpu=1

# Run stress for 10 seconds on 1 cpu and output results to /tmp/stress.out
- stress: timeout=10 cpu=1 dest=/tmp/stress.out

# Schedule stress to execute in 10 minutes
- stress: timeout=10 cpu=1 dest=/tmp/stress.out delay=10
'''

RETURN = '''
changed:
  description: response to whether or not the benchmark completed successfully
  returned: always
  type: boolean
  sample: true

stdout:
  description: the set of responses from the commands
  returned: always
  type: list
  sample: ['...', '...']

stdout_lines:
  description: the value of stdout split into a list
  returned: always
  type: list
  sample: [['...', '...'], ['...'], ['...']]

exec_cmd:
  description: Exact command executed to launch the benchmark with parameters
  returned: success
  type: string
  sample: "/path/to/stress ..."
'''

import os
import re
import tempfile


def benchmark(module, result, bin, params):

    cpu         = params['cpu']
    timeout     = params['timeout']
    dest        = params['dest']

    benchmark_command = None

    if dest:
        benchmark_command = "{} --cpu {} --timeout {} > {}"\
            .format(bin, cpu, timeout, dest)
    else:
        benchmark_command = "{} --cpu {} --timeout {}"\
            .format(bin, cpu, timeout)

    rc, out, err = module.run_command(benchmark_command,
                                      use_unsafe_shell=True,
                                      check_rc=True)

    if dest:
        out += "; Output located on targeted hosts at: {}".format(dest)

    result['changed']   = True
    result['exec_cmd']  = benchmark_command
    result['stdout']    = out.rstrip("\r\n")
    result['stderr']    = err.rstrip("\r\n")
    result['rc']        = rc

def parse(module, result, params):

    dest        = params['dest']

    if not os.path.exists(dest):
        module.fail_json(msg="{} does not exist".format(dest))

    result_file = open(dest, 'r')
    data = result_file.readlines()
    result_file.close()

    json_result = dict()

    for line in data:
        if "hogs" in line:
            match = re.search('(\d+)\s+cpu,\s+(\d+)\s+io,\s+(\d+)\s+vm,\s+(\d+)\s+hdd', line)
            if match:
                json_result['cpu_hogs'] = match.group(1)
                json_result['io_hogs'] = match.group(2)
                json_result['vm_hogs'] = match.group(3)
                json_result['hdd_hogs'] = match.group(4)
        elif "successful" in line:
            match = re.search('completed\s+in\s+(\d+)', line)
            if match:
                json_result['completion_time'] = match.group(1)
    if not json_result:
        module.fail_json(msg="Invalid result file at {}: {}".format(dest, line))

    result['changed'] = True
    result['results'] = json.dumps(json_result)


def main():

    module = AnsibleModule(
        argument_spec = dict(
            chdir=dict(required=False,
                       type='str'),
            cpu=dict(required=False,
                     type='int'),
            delay=dict(required=False,
                       type='int'),
            dest=dict(required=False,
                      type='str',
                      default=None),
            executable=dict(required=False,
                            type='str'),
            state=dict(type='str',
                       default="benchmark",
                       choices=['benchmark', 'parse']),
            timeout=dict(required=False,
                         type='int'),

        ),
        supports_check_mode=False
    )

    stress_bin = None
    result = {'changed': False, 'bench_config': dict()}

    if module.params['state'] == 'parse':
        if not module.params['dest']:
            module.fail_json(msg='dest= is required for state=parse')
        parse(module, result, module.params)

    if module.params['state'] == 'benchmark':
        missing_params = list()
        for param in ['timeout', 'cpu']:
            if not module.params[param]:
                missing_params.append(param)
        if len(missing_params) > 0:
            module.fail_json(msg="missing required arguments: {}".format(missing_params))
        if module.params['executable']:
            stress_bin = module.params['executable']
        else:
            stress_bin = module.get_bin_path('stress', True, ['/usr/bin/local'])

        benchmark(module, result, stress_bin, module.params)

    for param in ['timeout', 'cpu']:
        result['bench_config'][param] = module.params[param]

    module.exit_json(**result)

# import module snippets
from ansible.module_utils.basic import *
main()
