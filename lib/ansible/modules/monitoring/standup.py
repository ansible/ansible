#!/usr/bin/python

# Copyright (c) 2017, Thomas K. Theakanath <thomastk@gmail.com>

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

from __future__ import absolute_import, division, print_function
__metaclass__ = type

from ansible.module_utils.basic import AnsibleModule
import os
import re
import subprocess

try:
    import yaml

    HAS_YAML = True
except:
    HAS_YAML = False
    
ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
author: "Thomas Kurian Theakanath (thomastk@)"
module: standup
short_description: Runs a suite of checks to validate a host and heals state if needed.
description:
    - The standup module runs a set of checks and evaluate the results to determine if a host stands up right. The
      checks are specified in YAML format. A check contains a command that can be run on the host being verified, and,
      directives to evaluate the command output. Optionally, another command can be specified with a check to heal the
      state that the check verifies and it is run if the check fails.
version_added: "2.5"
options:
    checks_file_path:
        description:
            - Path to the YAML file in which the checks are defined. For format of checks YAML file and syntax of check
              refer U(https://github.com/thomastk/ansible-module-standup/blob/master/README.md)
        required: true
    checks_format:
        description:
            - The format of checks_file_path.
        required: false
        choices: ['yaml']
        default: yaml
    roles:
        description:
            - A role is a tag that indicates the application role of a host and a check can be tagged using those. If
              roles are specified, only matching roles from checks_file_path are executed by the module.
        required: false
    heal_state:
        description:
            - Indicates that heal command, if that is specified, be run if a check fails.
        required: false
        choices: [true, false]
        default: false
    continue_on_failure:
        description:
            - Indicates that the validation process will continue if a check fails. A check status can be ignored at
              the check level also.
        required: false
        choices: [true, false]
        default: true
notes:
    - Tested on Mac, Ubuntu and CentOS.
requirements: ['yaml']
'''

EXAMPLES = '''
# Run all the checks specified in a checks file.
- name: Run all the checks in verify-app-cluster.yml
  standup:
    checks_file_path: verify-app-cluster.yml

# Run only checks that are tagged with roles db and web from verify-app-cluster.yml
- name: Run all the checks in verify-app-cluster.yml
  standup:
    checks_file_path: verify-app-cluster.yml
    roles: db,web

# Run only checks that are tagged with roles db and web from verify-app-cluster.yml and
# run heal command, check status fails.
- name: Run all the checks in verify-app-cluster.yml and run heal command, if needed
  standup:
    checks_file_path: verify-app-cluster.yml
    roles: db,web
    heal_state: true

# A sample check. Multiple checks can be specified in a checks file.
# Refer U(https://github.com/thomastk/ansible-module-standup/blob/master/README.md)
# for complete documentation of checks YAML file syntax.
- name: "Test db 1"
  description: Check if mysql service is running
  roles: db
  command: ps -ef |grep mariadb|wc -l
  heal: sudo service mariadb start
  output_compare:
     type: number
     value: 3
     operator: EQ
'''

RETURN = '''
checks:
    description: The checks with results of running check and heal commands.
    type: dict
    returned: always
    sample: {
        "checks": {
            "Test db 1": {
                "check": {
                    "command": "ps -ef |grep mariadb|wc -l",
                    "description": "Check if mysql service is running",
                    "heal": "sudo service mariadb start",
                    "name": "Test db 1",
                    "output_compare": {
                        "operator": "GT",
                        "type": "number",
                        "value": 2
                    },
                    "roles": "db"
                },
                "check_status": true,
                "cmd_output": {
                    "output": "3",
                    "sys_status": 0
                },
                "command_ran": "ps -ef |grep mariadb|wc -l",
                "heal_output": null,
                "heal_ran": null,
                "healed": false,
                "last_error": null,
                "validated": true
            }
        }
    }
changed:
    description: Indicates if any heal steps are run successfully.
    type: boolean
    returned: success
    sample: True
result:
    description: Note regarding the validation run.
    type: string
    returned: always
    sample: "Validation checks succeeded."
'''

global module


# Class for comparing command outputs
class StandupOutputCompare:
    COMPARE_TYPES = ['str', 'number']
    OPERATORS = ['GE', 'EQ', 'GT', 'LE', 'LT']

    def __init__(self, opts):
        self.input_validated = False
        self.type = 'str'
        if 'type' in opts:
            if opts['type'] not in StandupOutputCompare.COMPARE_TYPES:
                return
            self.type = opts['type']
        self.ref_value = None
        if 'value' in opts:
            self.ref_value = opts['value']
        self.operator = 'EQ'
        if 'operator' in opts:
            if opts['operator'] not in StandupOutputCompare.OPERATORS:
                return
            self.operator = opts['operator']

        self.input_validated = True

        return

    def inputValidated(self):
        return self.input_validated

    def compare(self, out_value):
        if self.type == 'number':
            if re.match('^.*\.', str(self.ref_value)):  # float
                ref = float(self.ref_value)
                val = float(out_value)
            else:
                ref = int(self.ref_value)
                val = int(out_value)
            return StandupOutputCompare.compareNumber(self.operator, val, ref)
        elif type == "str":
            return self.ref_value == out_value
        else:
            return False

    @staticmethod
    def compareNumber(opr, val_in, val_ref):
        if opr == 'GE':
            return val_in >= val_ref
        elif opr == 'EQ':
            return val_in == val_ref
        elif opr == 'GT':
            return val_in > val_ref
        elif opr == 'LE':
            return val_in <= val_ref
        elif opr == 'LT':
            return val_in < val_ref
        else:
            return False


# Class for processing check.
class StandupCheck:
    CHECK_FORMATS = ['yaml']

    def __init__(self, check):
        self.check_spec = check
        self.input_validated = False

        self.has_heal = False
        self.ran_heal = False
        self.healed = False

        self.cmd_output = None
        self.heal_output = None
        self.check_status = None
        self.last_error = None

        if 'name' not in check or 'description' not in check or 'command' not in check:
            self.last_error = "name,description and command are need in check specification."
            return

        # The vars correspond to check options.
        self.name = check['name']
        self.description = check['description']
        self.command = check['command']
        self.roles = ['*']
        if 'roles' in check:
            self.roles = check['roles'].split(',')
        self.ignore_status = False
        if 'ignore_status' in check:
            self.ignore_status = check['ignore_status']
        self.output_compare = None
        if 'output_compare' in check:
            self.output_compare = StandupOutputCompare(check['output_compare'])
            if not self.output_compare.inputValidated():
                self.last_error = "Problem in the output_compare specification."
                return
        self.register = None
        if 'register' in check:
            self.register = check['register']
        self.heal = None
        if 'heal' in check:
            self.has_heal = True
            self.heal = check['heal']

        self.input_validated = True

        return

    def getName(self):
        return self.name

    def getCheckSpec(self):
        return self.check_spec

    def getCheckStatus(self):
        return self.check_status

    def getCmdOutput(self):
        return self.cmd_output

    def getHealOutput(self):
        return self.heal_output

    def getSysStatus(self):
        return self.cmd_output['sys_status']

    def getLastError(self):
        return self.last_error

    def getCmdRan(self):
        return self.command

    def getHealCmdRan(self):
        if self.ran_heal:
            return self.heal
        else:
            return None

    def hasHealed(self):
        return self.healed

    def getRoles(self):
        return self.roles

    def getRegisterVar(self):
        return self.register

    # A check can be marked with roles/tags, and this method
    # verifies if the given list of roles has any match in them.
    def isCompatibleRole(self, roles):
        # if the default * is specified, don't even bother to look at roles
        # specified on the check.
        if '*' in roles:
            return True
        return set(self.roles).intersection(roles)

    def isValidated(self):
        return self.input_validated

    # The given string is resolved with vars available in the registry passed in.
    @staticmethod
    def resolveStr(str, registry):
        vars = re.findall(r"_REGISTER\.(.+?)\b", str)
        for var in vars:
            if var in registry:
                str = str.replace('_REGISTER.' + var, registry[var])

        return str

    # Resolve registry entries in main command in a check
    def resolveCommand(self, registry):
        self.command = StandupCheck.resolveStr(self.command, registry)

    # Resolve registry entries in heal command of a check
    def resolveHeal(self, registry):
        if self.heal:
            self.heal = StandupCheck.resolveStr(self.heal, registry)

    # Executes the main command of check
    def execCommand(self):
        self.cmd_output = dict()
        status, output = StandupCheck.getstatusoutput(self.command)
        self.cmd_output['sys_status'] = status
        self.cmd_output['output'] = output

        return status == 0

    # Executes the heal step specified in check, which also involves rerunning check command
    def execHeal(self):
        self.heal_output = dict()
        status, output = StandupCheck.getstatusoutput(self.heal)
        self.heal_output['sys_status'] = status
        self.heal_output['output'] = output

        # Rerun check if the heal command succeeds
        if status == 0:
            return self.execCommand()

        return status == 0

    # Evaluate the execution result of command output passed in.
    # If the sys status is not 0, try running the heal command and check command before output validation.
    # If the output comparison fails, try running the heal command and check command before output validation.
    def evalCmdOutput(self, heal_state=False):
        self.check_status = True
        if not self.ignore_status and self.getSysStatus() != 0:
            self.check_status = False
            if heal_state and self.has_heal and not self.ran_heal:
                self.ran_heal = True
                if self.execHeal():
                    self.check_status = True

        # Check the command output if a validation of that is specified.
        if self.output_compare:
            if not self.output_compare.compare(self.getCmdOutput()['output']):
                self.check_status = False
                # If heal step is specified and not run already, try it.
                if heal_state and self.has_heal and not self.ran_heal:
                    self.ran_heal = True
                    if self.execHeal():
                        self.healed = True
                        self.check_status = self.evalCmdOutput(True)
                    else:
                        return False

        return self.check_status

    @staticmethod
    def getstatusoutput(cmd):
        try:
            output = subprocess.check_output(cmd, shell=True, universal_newlines=True, stderr=subprocess.STDOUT)
            status = 0
        except subprocess.CalledProcessError as ex:
            output = ex.output
            status = ex.returncode
        if output[-1:] == '\n':
            output = output[:-1]

        return status, output


class Standup:
    def __init__(self):
        # Set the module variables with defaults.
        self.checks_file_path = None
        self.title = None
        self.checks_format = "yaml"
        self.roles = ["*"]
        self.continue_on_failure = True
        self.heal_state = False

        self.checks = None
        self.heal_steps = None
        self.checks_succeeded = True
        self.state_changed = False
        self.result = None
        self.registry = dict()  # To store "register" values

    def setStateChanged(self):
        self.state_changed = True

    def hasStateChanged(self):
        return self.state_changed

    def setChecksFile(self, f):
        self.checks_file_path = f

    def setRoles(self, roles):
        self.roles = roles

    def setContinueOnFailure(self, c):
        self.continue_on_failure = c

    def setHealState(self, h):
        self.heal_state = h

    def getChecks(self):
        return self.checks

    def continueOnFailure(self):
        return self.continue_on_failure

    def healState(self):
        return self.heal_state

    def push2Registry(self, var_name, var_value):
        self.registry[var_name] = var_value

    def loadChecks(self):
        load_status = True
        f = open(self.checks_file_path, "r")
        yaml_str = f.read()
        f.close()
        checks = yaml.safe_load(yaml_str)
        self.checks = list()
        for check in checks['checks']:
            checkObj = StandupCheck(check)
            if not checkObj.isCompatibleRole(self.roles):
                continue
            if not checkObj.isValidated():
                load_status = False
            self.checks.append(checkObj)

        return load_status

    def execChecks(self):
        exec_status = True
        for check in self.checks:
            check.resolveCommand(self.registry)
            check.resolveHeal(self.registry)
            if not check.execCommand():
                exec_status = False
            else:
                if check.getRegisterVar():
                    self.push2Registry(check.getRegisterVar(), check.getCmdOutput()['output'])

        return exec_status

    def getChecksRunStatus(self):
        if not self.getChecks():
            return None
        r = dict()
        for check in self.getChecks():
            check_name = check.getName()
            r[check_name] = dict()
            r[check_name]['check'] = check.getCheckSpec()
            r[check_name]['command_ran'] = check.getCmdRan()
            r[check_name]['cmd_output'] = check.getCmdOutput()
            r[check_name]['heal_ran'] = check.getHealCmdRan()
            r[check_name]['heal_output'] = check.getHealOutput()
            r[check_name]['check_status'] = check.getCheckStatus()
            r[check_name]['healed'] = check.hasHealed()
            r[check_name]['validated'] = check.isValidated()
            r[check_name]['last_error'] = check.getLastError()

        return r

    def exit(self, msg=''):
        global module

        self.result["changed"] = self.state_changed
        self.result["checks"] = self.getChecksRunStatus()

        if msg == "":
            if self.checks_succeeded:
                msg = "Validation checks succeeded."
            else:
                msg = "One or more validation checks failed."

        self.result['result'] = msg

        if not self.checks_succeeded:
            module.fail_json(msg=msg, **self.result)
        else:
            module.exit_json(**self.result)

    # Default is marked succeeded.
    def markFailed(self):
        self.checks_succeeded = False


# Function to process the module action.
# Keeping this separate from the execution of checks.
def run_module():
    global module

    standup = Standup()

    standup.checks_succeeded = True
    standup.heal_steps = dict()

    # arguments/parameters to the module
    module_args = dict(
        checks_file_path=dict(type='str', required=True),
        checks_format=dict(type='str', required=False, default='yaml'),
        roles=dict(type='list', required=False, default=['*']),
        continue_on_failure=dict(type='bool', required=False, default=True),
        heal_state=dict(type='bool', required=False, default=False)
    )

    # seed the result dict in the object
    standup.result = dict(
        changed=False,
        result=''
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    # check the states defined in checks and test the status
    # store that info in current_state as serialized json string.
    current_state = ''

    # if the user is working with this module in only check mode we do not
    # want to make any changes to the environment, just return the current
    # state with no modifications
    if module.check_mode:
        return current_state

    # Set param related vars for brevity
    standup.setRoles(module.params['roles'])
    standup.setContinueOnFailure(module.params['continue_on_failure'])
    standup.setHealState(module.params['heal_state'])

    # Check if yaml module is installed
    if not HAS_YAML:
        standup.markFailed()
        standup.exit('Python module yaml is needed on the target hosts for standup to work.')

    # manipulate or modify the state as needed (this is going to be the
    # part where your module will do what it needs to do)
    checks_file_path = module.params['checks_file_path']
    if not os.path.exists(checks_file_path):
        standup.markFailed()
        standup.exit(checks_file_path + ' not found.')

    checks_file_format = module.params['checks_format']
    if checks_file_format not in StandupCheck.CHECK_FORMATS:
        standup.markFailed()
        standup.exit(checks_file_format + ' not supported.')

    standup.setChecksFile(checks_file_path)
    if not standup.loadChecks():
        standup.markFailed()
        standup.exit("Checks could not be loaded.")

    # Run the checks first and populate the registry etc.
    # Do validation of the command outputs after that.
    standup.execChecks()

    # Evaluate the output and if allowed, run heal steps
    for check in standup.getChecks():
        if not check.evalCmdOutput(standup.healState()):
            standup.markFailed()
            if not standup.continueOnFailure():
                standup.exit('Aborting as the last check failed.')
        if check.hasHealed():
            standup.setStateChanged()

    standup.exit()


# Main and running main
def main():
    run_module()


if __name__ == '__main__':
    main()
