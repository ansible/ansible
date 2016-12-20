#!/usr/bin/python

# (c) 2017, Tal Shafir

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
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: os_tempest_run
short_description: Runs Tempest
description:
    - Runs Tempest according to the configuration file in the given workspace 

version_added: "2.4"

author: "Tal Shafir , @TalShafir"
requirements: ["Tempest"]
options:
    workspace:
        description:
            The workspace as was configured in 'Tempest init <I(workspace)>'
        required: True
    dest:
        description:
            Path for the output from Tempest, if not given the result will be printed in the exit json under 'out' and 'err'
        required: True
    regex:
        description:
            Selection regex for tests, Tempest will run any tests that match on the I(regex)
            must use format for python's re.match()
        required: False
        default: ""
    whitelist_file:
        description:
            - Path for a file with a line separated list of regex, Tempest will run only tests that match at least one regex.
            - Cannot work with the I(blacklist_file) argument
        required: False
        default: ""
    blacklist_file:
        description:
            - Path for a file with a line separated list of regex, Tempest won't run tests that match at least one regex.
            - Cannot work with the I(whitelist_file) argument
        required: False
        default: ""
    concurrency:
        description:
            Number of workers to use(the default is one worker for each CPU core), set to C(1) in case you want to run serially
        required: False
        default: None
    force:
        description:
            When C(True) override output file if already exists
        required: False
        default: 'False'
    subunit:
        description:
            When C(True) show the output as subunit v2
        required: False
        default: 'False'
notes:
    - You can find out more about Tempest at U(http://docs.openstack.org/developer/tempest/)
    - The module requires to tempest init <I(workspace)> before usage
    - The options I(whitelist_file) and I(blacklist_file) are mutually exclusive, if they are both given only the I(whitelist_file) will be used 
'''

EXAMPLES = '''
# Run all tests with default number of workers
- os_tempest_run:
    dest: DEST
    workspace: cloud

# Run all tests matching to a regex with default number of workers
- os_tempest_run:
    dest: DEST
    workspace: cloud
    regex: REGEX

# Run all tests serially
- os_tempest_run:
    dest: DEST
    workspace: cloud
    concurrency: 1

# Run all tests with 4 workers
- os_tempest_run:
    dest: DEST
    workspace: cloud
    concurrency: 4

# Run all tests that their REGEX is in the whitelist file
- os_tempest_run:
    dest: DEST
    workspace: cloud
    whitelist_file: /path/to/whitelist

# Run all tests that their REGEX is not in the blacklist file
- os_tempest_run:
    dest: DEST
    workspace: cloud
    blacklist_file: /path/to/blacklist
'''
RETURN = '''
stdout:
    description: Tempest's stdout
    returned: fail
    type: string
    sample: ""
stderr:
    description: Tempest's stderr
    returned: fail
    type: string
    sample: ""
command:
    description: the command executed to run Tempest
    returned: fail
    type: string
    sample: "tempest run --workspace cloud"
output:
    description: path to the file containing the output from Tempest
    returned: success
    type: string
    sample: "/path/to/file.subunit"
'''
from ansible.module_utils.basic import AnsibleModule
import os
import sys

# imports for the code copied from ansible.utils.path
from errno import EEXIST
from ansible.module_utils._text import to_bytes
from ansible.module_utils._text import to_native
from ansible.module_utils._text import to_text


def main():
    ansible_module = AnsibleModule(argument_spec=dict(
        workspace=dict(type="str", required=True),
        dest=dict(type="path", required=True),
        regex=dict(type="str", required=False, default=""),
        whitelist_file=dict(type="path", required=False, default=""),
        blacklist_file=dict(type="path", required=False, default=""),
        concurrency=dict(type="int", required=False, default=None),
        force=dict(type="bool", required=False, default=False),
        subunit=dict(type="bool", required=False, default=True),
    ))

    # check if the arguments are valid
    if ansible_module.params['whitelist_file']:
        whitelist_file_path = unfrackpath(ansible_module.params['whitelist_file'])
    if ansible_module.params['blacklist_file']:
        blacklist_file_path = unfrackpath(ansible_module.params['blacklist_file'])

    if ansible_module.params["whitelist_file"] and ansible_module.params["blacklist_file"]:
        ansible_module.fail_json(msg="whitelist and blacklist files cannot be used together")
    if ansible_module.params["whitelist_file"] and not os.path.isfile(whitelist_file_path):
        ansible_module.fail_json(msg="'whitelist_file' is not a path to a file: '%s'" % whitelist_file_path)
    if ansible_module.params["blacklist_file"] and not os.path.isfile(blacklist_file_path):
        ansible_module.fail_json(msg="'blacklist_file' is not a path to a file: '%s'" % blacklist_file_path)

    if ansible_module.params['dest']:
        output_path = unfrackpath(ansible_module.params['dest'])
        if os.path.isdir(output_path):
            output_path = os.path.join(output_path, 'tempest-results.subunit')
    else:
        ansible_module.fail_json(msg="the dest parameter cannot be empty")

    if output_path and os.path.isfile(output_path) and not ansible_module.params['force']:
        ansible_module.exit_json(changed=False, msg="The output file already exists")

    # initial must-have args
    tempest_args = ['run']

    if ansible_module.params["subunit"]:
        tempest_args.extend(['--subunit'])

    # check if the user wants to choose tests using regex
    if ansible_module.params["regex"]:
        tempest_args.extend(['--regex', ansible_module.params["regex"]])

    # check if the user wants either blacklist or whitelist
    if ansible_module.params["whitelist_file"]:
        tempest_args.extend(['--whitelist-file', whitelist_file_path])

    elif ansible_module.params["blacklist_file"]:
        tempest_args.extend(['--blacklist-file', blacklist_file_path])

    # add the workspace to the execution
    if ansible_module.params["workspace"]:
        tempest_args.extend(['--workspace', ansible_module.params['workspace']])
    else:
        ansible_module.fail_json(msg="The workspace name cannot be empty")

    if ansible_module.params["concurrency"] and ansible_module.params["concurrency"] > 0:
        tempest_args.extend(['--concurrency', ansible_module.params["concurrency"]])

    # add virtualenv's bin directory to PATH
    env_update = dict()
    if os.path.dirname(sys.executable) not in os.environ.get('PATH', ''):
        env_update['PATH'] = os.path.dirname(sys.executable) + os.pathsep + os.environ.get('PATH', '')

    rc, tempest_stdout, tempest_stderr = ansible_module.run_command(['tempest'] + tempest_args,
                                                                    environ_update=env_update)

    if rc != 0:
        ansible_module.fail_json(msg="Tempest running has failed", stdout=tempest_stdout, stderr=tempest_stderr,
                                 changed=False, command=' '.join(['tempest'] + tempest_args), rc=rc)

    # create path if doesn't exists
    prepare_path(output_path)

    with open(output_path, 'w') as output_file:
        output_file.write(tempest_stdout)

    ansible_module.exit_json(msg="Tempest has ran successfully", output=output_path, changed=True)


def prepare_path(file_path):
    """
    Creates the path to the dir that contains the file if it doesn't exists
    
    :arg file_path: A path to a file, will create the dir containing the file if it doesn't already exists.
    :type file_path: str
    """

    dir_name = os.path.dirname(file_path)
    if not os.path.isdir(dir_name):
        makedirs_safe(dir_name)


# copied from ansible.utils.path
def unfrackpath(path, follow=True):
    """
    Returns a path that is free of symlinks (if follow=True), environment variables, relative path traversals and symbols (~)

    :arg path: A byte or text string representing a path to be canonicalized
    :arg follow: A boolean to indicate of symlinks should be resolved or not
    :raises UnicodeDecodeError: If the canonicalized version of the path
        contains non-utf8 byte sequences.
    :rtype: A text string (unicode on pyyhon2, str on python3).
    :returns: An absolute path with symlinks, environment variables, and tilde
        expanded.  Note that this does not check whether a path exists.

    example::
        '$HOME/../../var/mail' becomes '/var/spool/mail'
    """

    if follow:
        final_path = os.path.normpath(
            os.path.realpath(os.path.expanduser(os.path.expandvars(to_bytes(path, errors='surrogate_or_strict')))))
    else:
        final_path = os.path.normpath(
            os.path.abspath(os.path.expanduser(os.path.expandvars(to_bytes(path, errors='surrogate_or_strict')))))

    return to_text(final_path, errors='surrogate_or_strict')


def makedirs_safe(path, mode=None):
    """Safe way to create dirs in muliprocess/thread environments.

    :arg path: A byte or text string representing a directory to be created
    :kwarg mode: If given, the mode to set the directory to
    :raises Exception: If the directory cannot be created and does not already exists.
    :raises UnicodeDecodeError: if the path is not decodable in the utf-8 encoding.
    """

    rpath = unfrackpath(path)
    b_rpath = to_bytes(rpath)
    if not os.path.exists(b_rpath):
        try:
            if mode:
                os.makedirs(b_rpath, mode)
            else:
                os.makedirs(b_rpath)
        except OSError as e:
            if e.errno != EEXIST:
                raise Exception("Unable to create local directories(%s): %s" % (to_native(rpath), to_native(e)))


if __name__ == '__main__':
    main()
