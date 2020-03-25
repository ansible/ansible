#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'core'}


DOCUMENTATION = '''
---
module: git_cp
author:
    - "Federico Olivieri"
version_added: "2.10"
short_description: Perform git commiit and/or git push perations.
description:
    - Manage git commits and git push on local git directory
options:
    folder_path:
        description:
            - full folder path where .git/ is located.
        required: true
    user:
        description:
            - git username for https operations.
    token:
        description:
            - git API token for https operations.
    comment:
        description:
            - git commit comment. Same as "git commit -m".
    add:
        description:
            - list of files to be staged. Same as "git add ." 
              Asterisx values not accepted. i.e. "./*" or "*". 
        type: list
        default: "."
    branch:
        description:
            - git branch where perform git push.
        required: true
    push:
        description:
            - perform git push action. Same as "git push HEAD/branch".
        type: bool
        default: True
    commit:
        description:
            - git commit staged changes. Same as "git commit -m".
        type: bool
        default: True
    push_option:
        description:
            - git push options. Same as "git --push-option=option".
    mode:
        description:
            - git operations are performend eithr over ssh channel or https. 
              Same as "git@git..." or "https://user:token@git..."
        choices: [ 'ssh', 'https' ]
        default: ssh
        required: True
    url:
        description:
            - git repo URL. If not provided, the module will use the same mode used by "git clone"
    accept_hostkey:
        description:
            - Accept ssh fingerprint. if True, ensure that "-o StrictHostKeyChecking=no" is
              present as an ssh option.
        type: bool
requirements:
    - git>=2.19.0 (the command line tool)

notes:
    - "If the task seems to be hanging, first verify remote host is in known_hosts.
      SSH will prompt user to authorize the first contact with a remote host.  To avoid this prompt,
      one solution is to use the option accept_hostkey. Another solution is to
      add the remote host public key in C(/etc/ssh/ssh_known_hosts) before calling
      the git module, with the following command: ssh-keyscan -H remote_host.com >> /etc/ssh/ssh_known_hosts."
'''

EXAMPLES = '''

# Commit and push changes via https.
- git_cp:
    folder_path: /Users/federicoolivieri/git/git_test_module
    user: Federico87
    token: m1Ap!T0k3n!!!
    comment: My amazing backup
    add: ['test.txt', 'txt.test']
    branch: master
    push: true
    commit: true
    mode: https
    url: https://gitlab.com/networkAutomation/git_test_module           

# Push changes via ssh using some defaults.
- git_cp:
    folder_path: /Users/federicoolivieri/git/git_test_module
    comment: My amazing backup
    branch: master
    push: true
    commit: false
    url: git@gitlab.com/networkAutomation/git_test_module

# Commit and push changes using only defaults.
- git_cp:
    folder_path: /Users/federicoolivieri/git/git_test_module
    comment: My amazing backup
    branch: master
'''

RETURN = '''
output:
    description: list of git cli commands stdout
    type: list
    changed: true
    sample: [
        "[master 99830f4] Remove [ test.txt, tax.txt ]\n 4 files changed, 26 insertions(+), 31 deletions(-)\n delete mode 100644 tax.txt\n delete mode 100644 test.txt\n",
        "To https://gitlab.com/networkAutomation/git_test_module.git\n   372db19..99830f4  master -> master\n"
    ]
'''
import os
import subprocess

from ansible.module_utils.basic import AnsibleModule


def git_commit(module):

    commands = list()

    add = module.params.get('add')
    folder_path = module.params.get('folder_path')
    comment = module.params.get('comment')
    
    if add:
        commands.append('git -C {0} add {1}'.format(
            folder_path, 
            ' '.join(add)
            ))

    if comment:
        commands.append('git -C {0} commit -m "{1}"'.format(
            folder_path,
            comment
            ))

    return commands


def git_push(module):

    commands = list()

    folder_path = module.params.get('folder_path')
    url = module.params.get('url')
    user = module.params.get('user')
    token = module.params.get('token')
    branch = module.params.get('branch')
    push_option = module.params.get('push_option')
    mode = module.params.get('mode')

    def https(folder_path,user,token,url,branch,push_option):
        if url.startswith('https://'):
            remote_add = 'git -C {folder_path} remote set-url origin https://{user}:{token}@{url}'.format(
                folder_path=folder_path,
                url=url[8:],
                user=user,
                token=token,
                branch=branch,
            )
            cmd = 'git -C {folder_path} push origin {branch}'.format(
                folder_path=folder_path,
                branch=branch,
            )
        
        if push_option:
            index = cmd.find('origin')
            return [remote_add, cmd[:index] + '--push-option={option} '.format(option=push_option) + cmd[index:]]
        
        if not push_option:
            return [remote_add, cmd]

    if mode == 'https':
        for cmd in https(folder_path,user,token,url,branch,push_option):
            commands.append(cmd)


    if mode == 'ssh':
        if 'https' in url:
            module.fail_json(msg='SSH mode selected but HTTPS URL provided')

        remote_add = 'git -C {folder_path} remote set-url origin {url}'.format(
                        folder_path=folder_path,
                        url=url,
                        user=user,
                    )
        cmd = 'git -C {folder_path} push origin {branch}'.format(
            folder_path=folder_path,
            branch=branch
        )
        commands.append(remote_add)

        if push_option:
            index = cmd.find('origin')
            commands.append(cmd[:index] + '--push-option={option} '.format(option=push_option) + cmd[index:])

        if not push_option:
            commands.append(cmd)

    return commands


def send_commands(cmd):

    send_commands = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
        shell=True
        )
    send_commands.wait()
    output, error = send_commands.communicate()

    return output, error


def main():

    argument_spec = dict(
        folder_path=dict(required=True),
        user=dict(),
        token=dict(),
        comment=dict(required=True),
        add=dict(type="list", default=[ "." ]),
        branch=dict(required=True),
        push_option=dict(),
        mode=dict(choices=["ssh","https"]),
        url=dict(),
        accept_hostkey=dict(type='bool', default=False)
    )


    mutually_exclusive = [("ssh", "https")]
    required_if = [
        ("mode", "https", ["user", "token"]),
        ("mode", "ssh", ["accept_hostkey"]),
        ]


    module = AnsibleModule(
        argument_spec=argument_spec,
        mutually_exclusive=mutually_exclusive,
        required_if=required_if,
    )

    result = dict(
        changed=False, 
        # warnings=list()
        )
    
    git_commands = git_commit(module) + git_push(module)
        
    result_output = list()

    for cmd in git_commands:
        output, error = send_commands(cmd)

        if output:
            # no changes added by 'git commit'
            if 'no changes added to commit' in output:
                module.fail_json(msg=output)
            # if 'git add .' and nothing to commit
            elif 'nothing to commit, working tree clean' in output:
                module.fail_json(msg=output)
            else:
                result_output.append(output)

        if error:
            if 'error:' in error:
                module.fail_json(msg=error)
            # file not found by 'git add'
            elif 'did not match any files' in error:
                module.fail_json(msg=error)
            # don't error out for 'Everything up-to-date'
            elif 'Everything up-to-date':
                result_output.append(error)
                result.update(changed=False)
            else:
                module.fail_json(msg=error)
                result.update(changed=False)

    if result_output:
        result.update(output=result_output)
        result.update(changed=True)

    module.exit_json(**result)


if __name__ == "__main__":
    main()