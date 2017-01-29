#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2017, Dawid Wolski <dawidtomaszwolski@gmail.com>
#
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
#

ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'version': '1.0'}

DOCUMENTATION = '''
module: sqitch
short_description: Manage databases using sqitch
description:
  - Manage PostgreSQL, SQLite, Oracle, MySQL, Firebird and Vertica database changes using sqitch
version_added: "2.3"
author: "Dawid Wolski, @merito"
requirements:
  - sqitch
notes:
  - Requires sqitch installed on the remote host. There are many ways you can install it, all are described on
    sqitch.org
options:
  command:
    description:
      - A sqitch command, tells sqitch what kind of action it should take
    required: true
    default: deploy
    choices: ["deploy", "rebase", "revert", "status", "verify"]
  plan_file:
    description:
      - Path to deployment plan file
    required: no
  target:
    description:
      - Database to which to connect
    required: no
  engine:
    description:
      - Database engine.
    required: no
  cwd:
    description:
      - Path to directory with config file.
    required: no
  to_change:
    description:
      - Change to which to do action. (deploy, verify)
    required: no
  from_change:
    description:
      - Change from which to do action. (verify)
  verify:
    description:
      - Run verify scripts after each change. Set to false to disable verification.
        There is no default, if not set it depends on the content od the conf file.
    required: no
  mode:
    description:
      - Specify the reversion mode to use in case of deploy or verify failure. (deploy, rebase)
    required: no
  set:
    description:
      - Attach a list of a variables name and value for use by the database engine client, if it supports variables.
        The format must be name=value, e.g., defuser='Homer Simpson'. Overrides any values loaded from the deploy.variables configuration.
    required: no
    default: []
  log_only:
    description:
      - Log the changes as if they were deployed, but without actually running the deploy scripts.
        Useful for an existing database that is being converted to Sqitch, and you need to log changes as deployed
        because they have been deployed by other means in the past.
    required: no
  onto:
    description:
      - Specify the reversion change. Defaults to reverting all changes. (rebase)
    required: no
  upto:
    description:
      - Specify the deployment change. Defaults to the last point in the plan. (rebase)
    required: no
  set_revert:
    description:
      - Attach a list of a variables name and value to be used by the database engine client when reverting, if it supports variables.
        The format must be name=value, e.g., defuser='Homer Simpson'.
        Overrides any values from set or loaded from the deploy.variables and revert.variables configurations. (rebase)
    required: no
    default: []
  set_deploy:
    description:
      - Attach a list of a variables name and value for use by the database engine client when deploying, if it supports variables.
        The format must be name=value, e.g., defuser='Homer Simpson'.
        Overrides any values from set or loaded from the deploy.variables configuration. (rebase)
    required: no
    default: []
'''

EXAMPLES = '''
- name: Deploy changes from sqitch.plan file located in /opt/sqitch to test_db database
  sqitch:
    command: deploy
    plan_file: sqitch.plan
    top_dir: /opt/sqitch
    target: test_db

- name: Revert all changes in test_db database
  sqitch:
    command: revert
    target: test_db

- name: Revert changes up to chng1 change in test_db database
  sqitch:
    command: revert
    target: test_db
    to_change: chng1

- name: Rebase (revert all changes and deploy) test_db database from sqitch.plan file located in /opt/sqitch
  sqitch:
    command: rebase
    plan_file: sqitch.plan
    top_dir: /opt/sqitch
    target: test_db
    set:
      - defuser='Homer Simpson'
'''

from ansible.module_utils.basic import AnsibleModule


def get_target(cmd, target):
    if target is not None:
        cmd.append('--target')
        cmd.append(target)


def get_to_change(cmd, to_change):
    if to_change is not None:
        cmd.append('--to-change')
        cmd.append(to_change)


def get_verify(cmd, verify):
    if verify:
        cmd.append('--verify')
    elif verify is not None and not verify:
        cmd.append('--no-verify')


def get_from_change(cmd, from_change):
    if from_change is not None:
        cmd.append('--to-change')
        cmd.append(from_change)


def get_mode(cmd, mode):
    if mode is not None:
        cmd.append('--mode')
        cmd.append(mode)


def get_set(cmd, set):
    if len(set) > 0:
        for variable in set:
            cmd.append('--set')
            cmd.append(variable)


def get_log_only(cmd, log_only):
    if log_only:
        cmd.append('--log-only')


def get_onto(cmd, onto):
    if onto is not None:
        cmd.append('--onto')
        cmd.append(onto)


def get_upto(cmd, upto):
    if upto is not None:
        cmd.append('--upto')
        cmd.append(upto)


def get_set_revert(cmd, set_revert):
    if len(set_revert) > 0:
        for variable in set_revert:
            cmd.append('--set-revert')
            cmd.append(variable)


def get_set_deploy(cmd, set_deploy):
    if len(set_deploy) > 0:
        for variable in set_deploy:
            cmd.append('--set-deploy')
            cmd.append(variable)


def main():
    module = AnsibleModule(
        argument_spec = dict(
            command     = dict(default='deploy', choices=["deploy", "rebase", "revert",
                                                          "status", "verify"]),
            plan_file   = dict(),
            target      = dict(),
            engine      = dict(),
            cwd         = dict(),
            to_change   = dict(),
            from_change = dict(),
            dest_dir    = dict(),
            verify      = dict(type='bool'),
            mode        = dict(choices=["all", "tag", "change"]),
            set         = dict(default=[], type='list'),
            log_only    = dict(type='bool'),
            onto        = dict(),
            upto        = dict(),
            set_revert  = dict(default=[], type='list'),
            set_deploy  = dict(default=[], type='list')
        )
    )

    command = module.params['command']
    plan_file = module.params['plan_file']
    target = module.params['target']
    engine = module.params['engine']
    cwd = module.params['cwd']
    to_change = module.params['to_change']
    from_change = module.params['from_change']
    verify = module.params['verify']
    mode = module.params['mode']
    set = module.params['set']
    log_only = module.params['log_only']
    onto = module.params['onto']
    upto = module.params['upto']
    set_revert = module.params['set_revert']
    set_deploy = module.params['set_deploy']

    cmd = [module.get_bin_path('sqitch', True)]

    # common options
    if plan_file is not None:
        cmd.append('--plan-file')
        cmd.append(plan_file)
    if engine is not None:
        cmd.append('--engine')
        cmd.append(engine)

    cmd.append(command)

    # command options
    if command == 'deploy':
        if engine is None and target is None:
            module.fail_json(msg="You have to specify engine or target to deploy")
        get_target(cmd, target)
        get_to_change(cmd, to_change)
        get_verify(cmd, verify)
        get_mode(cmd, mode)
        get_set(cmd, set)
        get_log_only(cmd, log_only)
    elif command == 'rebase':
        if engine is None and target is None:
            module.fail_json(msg="You have to specify engine or target to deploy")
        get_target(cmd, target)
        get_verify(cmd, verify)
        get_onto(cmd, onto)
        get_upto(cmd, upto)
        get_mode(cmd, mode)
        get_set(cmd, set)
        get_log_only(cmd, log_only)
        get_set_revert(cmd, set_revert)
        get_set_deploy(cmd, set_deploy)
        cmd.append('-y')
    elif command == 'revert':
        if engine is None and target is None:
            module.fail_json(msg="You have to specify engine or target to deploy")
        get_target(cmd, target)
        get_to_change(cmd, to_change)
        get_set(cmd, set)
        get_log_only(cmd, log_only)
        cmd.append('-y')
    elif command == 'status':
        if engine is None and target is None:
            module.fail_json(msg="You have to specify engine or target to deploy")
        get_target(cmd, target)
    elif command == 'verify':
        if engine is None and target is None:
            module.fail_json(msg="You have to specify engine or target to deploy")
        get_target(cmd, target)
        get_to_change(cmd, to_change)
        get_from_change(cmd, from_change)
        get_set(cmd, set)

    (rc, out, err) = module.run_command(cmd, cwd=cwd)

    if rc is not None and rc != 0:
        module.fail_json(msg=err, rc=rc)

    result = {}

    if rc is None:
        result['changed'] = False
    else:
        if command == 'deploy':
            if 'Nothing to deploy' in out:
                result['changed'] = False
            else:
                result['changed'] = True
        elif command == 'rebase':
            result['changed'] = True
        elif command == 'revert':
            if 'Nothing to revert' in out:
                result['changed'] = False
            else:
                result['changed'] = True
        elif command == 'status':
            result['changed'] = True
        elif command == 'verify':
            result['changed'] = True

    if out:
        result['stdout'] = out
    if err:
        result['stderr'] = err

    module.exit_json(**result)


if __name__ == '__main__':
    main()
