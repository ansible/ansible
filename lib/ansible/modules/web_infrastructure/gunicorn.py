#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2017, Alejandro Gomez <alexgomez2202@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: gunicorn
version_added: "2.4"
short_description: Run gunicorn with various settings.
description:
     - Starts gunicorn with the parameters specified. Common settings for gunicorn
       configuration are supported. For additional configuration use a config file
       See U(https://gunicorn-docs.readthedocs.io/en/latest/settings.html) for more
       options. It's recommended to always use the chdir option to avoid problems
       with the location of the app.
requirements: [gunicorn]
author:
    - "Alejandro Gomez (@agmezr)"
options:
  app:
    required: true
    aliases: ['name']
    description:
      - The app module. A name refers to a WSGI callable that should be found in the specified module.
  venv:
    aliases: ['virtualenv']
    description:
      - 'Path to the virtualenv directory.'
  config:
    description:
      - 'Path to the gunicorn configuration file.'
  chdir:
    description:
      - 'Chdir to specified directory before apps loading.'
  pid:
    description:
      - 'A filename to use for the PID file. If not set and not found on the configuration file a tmp
         pid file will be created to check a successful run of gunicorn.'
  worker:
    choices: ['sync', 'eventlet', 'gevent', 'tornado ', 'gthread', 'gaiohttp']
    description:
      - 'The type of workers to use. The default class (sync) should handle most “normal” types of workloads.'
  user:
    description:
      -  'Switch worker processes to run as this user.'
notes:
  - If not specified on config file, a temporary error log will be created on /tmp dir.
    Please make sure you have write access in /tmp dir. Not needed but will help you to
    identify any problem with configuration.
'''

EXAMPLES = '''
- name: simple gunicorn run example
  gunicorn:
    app: 'wsgi'
    chdir: '/workspace/example'

- name: run gunicorn on a virtualenv
  gunicorn:
    app: 'wsgi'
    chdir: '/workspace/example'
    venv: '/workspace/example/venv'

- name: run gunicorn with a config file
  gunicorn:
    app: 'wsgi'
    chdir: '/workspace/example'
    conf: '/workspace/example/gunicorn.cfg'

- name: run gunicorn as ansible user with specified pid and config file
  gunicorn:
    app: 'wsgi'
    chdir: '/workspace/example'
    conf: '/workspace/example/gunicorn.cfg'
    venv: '/workspace/example/venv'
    pid: '/workspace/example/gunicorn.pid'
    user: 'ansible'
'''

RETURN = '''
gunicorn:
    description: process id of gunicorn
    returned: changed
    type: string
    sample: "1234"
'''

import os
import time

# import ansible utils
from ansible.module_utils.basic import AnsibleModule


def search_existing_config(config, option):
    ''' search in config file for specified option '''
    if config and os.path.isfile(config):
        data_config = None
        with open(config, 'r') as f:
            for line in f:
                if option in line:
                    return line
    return None


def remove_tmp_file(file_path):
    ''' remove temporary files '''
    if os.path.isfile(file_path):
        os.remove(file_path)


def main():

    # available gunicorn options on module
    gunicorn_options = {
        'config': '-c',
        'chdir': '--chdir',
        'worker': '-k',
        'user': '-u',
    }

    # temporary files in case no option provided
    tmp_error_log = '/tmp/gunicorn.temp.error.log'
    tmp_pid_file = '/tmp/gunicorn.temp.pid'

    # remove temp file if exists
    remove_tmp_file(tmp_pid_file)
    remove_tmp_file(tmp_error_log)

    module = AnsibleModule(
        argument_spec=dict(
            app=dict(required=True, type='str', aliases=['name']),
            venv=dict(required=False, type='path', default=None, aliases=['virtualenv']),
            config=dict(required=False, default=None, type='path', aliases=['conf']),
            chdir=dict(required=False, type='path', default=None),
            pid=dict(required=False, type='path', default=None),
            user=dict(required=False, type='str'),
            worker=dict(required=False,
                        type='str',
                        choices=['sync', 'eventlet', 'gevent', 'tornado ', 'gthread', 'gaiohttp']
                        ),
        )
    )

    # obtain app name and venv
    params = module.params
    app = params['app']
    venv = params['venv']
    pid = params['pid']

    # use venv path if exists
    if venv:
        gunicorn_command = "/".join((venv, 'bin', 'gunicorn'))
    else:
        gunicorn_command = 'gunicorn'

    # to daemonize the process
    options = ["-D"]

    # fill options
    for option in gunicorn_options:
        param = params[option]
        if param:
            options.append(gunicorn_options[option])
            options.append(param)

    error_log = search_existing_config(params['config'], 'errorlog')
    if not error_log:
        # place error log somewhere in case of fail
        options.append("--error-logfile")
        options.append(tmp_error_log)

    pid_file = search_existing_config(params['config'], 'pid')
    if not params['pid'] and not pid_file:
        pid = tmp_pid_file

    # add option for pid file if not found on config file
    if not pid_file:
        options.append('--pid')
        options.append(pid)

    # put args together
    args = [gunicorn_command] + options + [app]
    rc, out, err = module.run_command(args, use_unsafe_shell=False, encoding=None)

    if not err:
        # wait for gunicorn to dump to log
        time.sleep(0.5)
        if os.path.isfile(pid):
            with open(pid, 'r') as f:
                result = f.readline().strip()

            if not params['pid']:
                os.remove(pid)

            module.exit_json(changed=True, pid=result, debug=" ".join(args))
        else:
            # if user defined own error log, check that
            if error_log:
                error = 'Please check your {0}'.format(error_log.strip())
            else:
                if os.path.isfile(tmp_error_log):
                    with open(tmp_error_log, 'r') as f:
                        error = f.read()
                    # delete tmp log
                    os.remove(tmp_error_log)
                else:
                    error = "Log not found"

            module.fail_json(msg='Failed to start gunicorn. {0}'.format(error), error=err)

    else:
        module.fail_json(msg='Failed to start gunicorn {0}'.format(err), error=err)

if __name__ == '__main__':
    main()
