#!/usr/bin/env python3
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
to_do:
    lorem ipsum
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
    https = module.params.get('https')
    ssh = module.params.get('ssh')
    # accept_hostkey = module.params.get('accept_hostkey')

    if not ssh and not https:
        if url.startswith('git@'):
            ssh = True
            https = False
        if url.startswith('https://'):
            ssh = False
            https = True

    if https:
        ssh = False
        cmd = 'git -C {folder_path} https://{user}:{token}@{url} HEAD:{branch}'.format(
            folder_path=folder_path,
            option=push_option,
            user=user,
            token=token,
            url=url[8:],
            branch=branch
        )

        if push_option:
            index = cmd.find(folder_path)
            commands.append(cmd[:index] + '--push-option={option}'.format(option=push_option) + cmd[index:])
        if not push_option:
            commands.append(cmd)

    if ssh:
        cmd = 'git -C {folder_path} {url} HEAD:{branch}'.format(
            folder_path=folder_path,
            option=push_option,
            user=user,
            token=token,
            url=url,
            branch=branch
        )

        if push_option:
            index = cmd.find(folder_path)
            commands.append(cmd[:index] + '--push-option={option}'.format(option=push_option) + cmd[index:])
        if not push_option:
            commands.append(cmd)

    return commands


def main():

    argument_spec = dict(
        folder_path=dict(required=True),
        user=dict(),
        token=dict(),
        comment=dict(),
        add=dict(type="list", default=[ "." ]),
        branch=dict(required=True),
        push=dict(type="bool", default=True),
        commit=dict(type="bool", default=True),
        push_option=dict(),
        mode=dict(choices=["ssh","https"], default="ssh", required=True),
        url=dict(),
        accept_hostkey=dict(type='bool', default=False)
    )


    mutually_exclusive = [("ssh", "https")]
    required_if = [
        ("commit", True, ["comment", "add"]),
        ("mode", "https", ["user", "token"]),
        ("push", True, ["branch"]),
        ]


    module = AnsibleModule(
        argument_spec=argument_spec,
        mutually_exclusive=mutually_exclusive,
        required_if=required_if,
    )


    folder_path = module.params.get('folder_path')
    url = module.params.get('url')

    if folder_path and not url:
        if os.path.isdir("{0}/.git".format(folder_path)):
            git_path = "{0}/.git".format(folder_path)
        else:
            module.fail_json(msg='".git/" folder not found in {0}.'.format(folder_path))
   
        if os.path.isfile('{0}/config'.format(git_path)):       
            with open('{0}/config'.format(git_path)) as config:
                content = config.readlines()
            for line in content:
                if 'url =' in line:
                    url = line.split()[2]
                    updated_url = {'url': url}
                    module.params.update(updated_url)
        else:
            module.fail_json(msg='"config" file not found in {0}.'.format(git_path))


    result = dict(changed=False, warnings=list())


    if module.params.get('commit'):
        result['git_commit'] = git_commit(module)

    if module.params.get('push'):
        result['git_push'] = git_push(module)


    module.exit_json(**result)
    # if module.params['accept_hostkey']:
    #     if ssh_opts is not None:
    #         if "-o StrictHostKeyChecking=no" not in ssh_opts:
    #             ssh_opts += " -o StrictHostKeyChecking=no"
    #     else:
    #         ssh_opts = "-o StrictHostKeyChecking=no"1
