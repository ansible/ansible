#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2013, Scott Anderson <scottanderson42@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: django_manage
short_description: Manages a Django application.
description:
    - Manages a Django application using the I(manage.py) application frontend to I(django-admin). With the I(virtualenv) parameter, all
      management commands will be executed by the given I(virtualenv) installation.
version_added: "1.1"
options:
  command:
    choices: [ 'cleanup', 'collectstatic', 'flush', 'loaddata', 'migrate', 'runfcgi', 'syncdb', 'test', 'validate', ]
    description:
      - The name of the Django management command to run. Built in commands are cleanup, collectstatic, flush, loaddata, migrate, runfcgi, syncdb,
        test, and validate.
      - Other commands can be entered, but will fail if they're unknown to Django.  Other commands that may prompt for user input should be run
        with the I(--noinput) flag.
    required: true
  app_path:
    description:
      - The path to the root of the Django application where B(manage.py) lives.
    required: true
  settings:
    description:
      - The Python path to the application's settings module, such as 'myapp.settings'.
    required: false
  pythonpath:
    description:
      - A directory to add to the Python path. Typically used to include the settings module if it is located external to the application directory.
    required: false
  virtualenv:
    description:
      - An optional path to a I(virtualenv) installation to use while running the manage application.
    required: false
  apps:
    description:
      - A list of space-delimited apps to target. Used by the 'test' command.
    required: false
  cache_table:
    description:
      - The name of the table used for database-backed caching. Used by the 'createcachetable' command.
    required: false
  database:
    description:
      - The database to target. Used by the 'createcachetable', 'flush', 'loaddata', and 'syncdb' commands.
    required: false
  failfast:
    description:
      - Fail the command immediately if a test fails. Used by the 'test' command.
    required: false
    default: "no"
    choices: [ "yes", "no" ]
  fixtures:
    description:
      - A space-delimited list of fixture file names to load in the database. B(Required) by the 'loaddata' command.
    required: false
  skip:
    description:
     - Will skip over out-of-order missing migrations, you can only use this parameter with I(migrate)
    required: false
    version_added: "1.3"
  merge:
    description:
     - Will run out-of-order or missing migrations as they are not rollback migrations, you can only use this parameter with 'migrate' command
    required: false
    version_added: "1.3"
  link:
    description:
     - Will create links to the files instead of copying them, you can only use this parameter with 'collectstatic' command
    required: false
    version_added: "1.3"
notes:
  - I(virtualenv) (U(http://www.virtualenv.org)) must be installed on the remote host if the virtualenv parameter is specified.
  - This module will create a virtualenv if the virtualenv parameter is specified and a virtualenv does not already exist at the given location.
  - This module assumes English error messages for the 'createcachetable' command to detect table existence, unfortunately.
  - To be able to use the migrate command with django versions < 1.7, you must have south installed and added as an app in your settings.
  - To be able to use the collectstatic command, you must have enabled staticfiles in your settings.
  - As of ansible 2.x, your I(manage.py) application must be executable (rwxr-xr-x), and must have a valid I(shebang), i.e. "#!/usr/bin/env python",
    for invoking the appropriate Python interpreter.
requirements: [ "virtualenv", "django" ]
author: "Scott Anderson (@tastychutney)"
'''

EXAMPLES = """
# Run cleanup on the application installed in 'django_dir'.
- django_manage:
    command: cleanup
    app_path: "{{ django_dir }}"

# Load the initial_data fixture into the application
- django_manage:
    command: loaddata
    app_path: "{{ django_dir }}"
    fixtures: "{{ initial_data }}"

# Run syncdb on the application
- django_manage:
    command: syncdb
    app_path: "{{ django_dir }}"
    settings: "{{ settings_app_name }}"
    pythonpath: "{{ settings_dir }}"
    virtualenv: "{{ virtualenv_dir }}"

# Run the SmokeTest test case from the main app. Useful for testing deploys.
- django_manage:
    command: test
    app_path: "{{ django_dir }}"
    apps: main.SmokeTest

# Create an initial superuser.
- django_manage:
    command: "createsuperuser --noinput --username=admin --email=admin@example.com"
    app_path: "{{ django_dir }}"
"""

import os
import sys

from ansible.module_utils.basic import AnsibleModule


def _fail(module, cmd, out, err, **kwargs):
    msg = ''
    if out:
        msg += "stdout: %s" % (out, )
    if err:
        msg += "\n:stderr: %s" % (err, )
    module.fail_json(cmd=cmd, msg=msg, **kwargs)


def _ensure_virtualenv(module):

    venv_param = module.params['virtualenv']
    if venv_param is None:
        return

    vbin = os.path.join(os.path.expanduser(venv_param), 'bin')
    activate = os.path.join(vbin, 'activate')

    if not os.path.exists(activate):
        virtualenv = module.get_bin_path('virtualenv', True)
        vcmd = '%s %s' % (virtualenv, venv_param)
        vcmd = [virtualenv, venv_param]
        rc, out_venv, err_venv = module.run_command(vcmd)
        if rc != 0:
            _fail(module, vcmd, out_venv, err_venv)

    os.environ["PATH"] = "%s:%s" % (vbin, os.environ["PATH"])
    os.environ["VIRTUAL_ENV"] = venv_param


def createcachetable_filter_output(line):
    return "Already exists" not in line


def flush_filter_output(line):
    return "Installed" in line and "Installed 0 object" not in line


def loaddata_filter_output(line):
    return "Installed" in line and "Installed 0 object" not in line


def syncdb_filter_output(line):
    return ("Creating table " in line) or ("Installed" in line and "Installed 0 object" not in line)


def migrate_filter_output(line):
    return ("Migrating forwards " in line) or ("Installed" in line and "Installed 0 object" not in line) or ("Applying" in line)


def collectstatic_filter_output(line):
    return line and "0 static files" not in line


def main():
    command_allowed_param_map = dict(
        cleanup=(),
        createcachetable=('cache_table', 'database', ),
        flush=('database', ),
        loaddata=('database', 'fixtures', ),
        syncdb=('database', ),
        test=('failfast', 'testrunner', 'liveserver', 'apps', ),
        validate=(),
        migrate=('apps', 'skip', 'merge', 'database',),
        collectstatic=('clear', 'link', ),
    )

    command_required_param_map = dict(
        loaddata=('fixtures', ),
    )

    # forces --noinput on every command that needs it
    noinput_commands = (
        'flush',
        'syncdb',
        'migrate',
        'test',
        'collectstatic',
    )

    # These params are allowed for certain commands only
    specific_params = ('apps', 'clear', 'database', 'failfast', 'fixtures', 'liveserver', 'testrunner')

    # These params are automatically added to the command if present
    general_params = ('settings', 'pythonpath', 'database',)
    specific_boolean_params = ('clear', 'failfast', 'skip', 'merge', 'link')
    end_of_command_params = ('apps', 'cache_table', 'fixtures')

    module = AnsibleModule(
        argument_spec=dict(
            command=dict(default=None, required=True),
            app_path=dict(default=None, required=True),
            settings=dict(default=None, required=False),
            pythonpath=dict(default=None, required=False, aliases=['python_path']),
            virtualenv=dict(default=None, required=False, aliases=['virtual_env']),

            apps=dict(default=None, required=False),
            cache_table=dict(default=None, required=False),
            clear=dict(default=None, required=False, type='bool'),
            database=dict(default=None, required=False),
            failfast=dict(default='no', required=False, type='bool', aliases=['fail_fast']),
            fixtures=dict(default=None, required=False),
            liveserver=dict(default=None, required=False, aliases=['live_server']),
            testrunner=dict(default=None, required=False, aliases=['test_runner']),
            skip=dict(default=None, required=False, type='bool'),
            merge=dict(default=None, required=False, type='bool'),
            link=dict(default=None, required=False, type='bool'),
        ),
    )

    command = module.params['command']
    app_path = os.path.expanduser(module.params['app_path'])
    virtualenv = module.params['virtualenv']

    for param in specific_params:
        value = module.params[param]
        if param in specific_boolean_params:
            value = module.boolean(value)
        if value and param not in command_allowed_param_map[command]:
            module.fail_json(msg='%s param is incompatible with command=%s' % (param, command))

    for param in command_required_param_map.get(command, ()):
        if not module.params[param]:
            module.fail_json(msg='%s param is required for command=%s' % (param, command))

    _ensure_virtualenv(module)

    cmd = "./manage.py %s" % (command, )

    if command in noinput_commands:
        cmd = '%s --noinput' % cmd

    for param in general_params:
        if module.params[param]:
            cmd = '%s --%s=%s' % (cmd, param, module.params[param])

    for param in specific_boolean_params:
        if module.boolean(module.params[param]):
            cmd = '%s --%s' % (cmd, param)

    # these params always get tacked on the end of the command
    for param in end_of_command_params:
        if module.params[param]:
            cmd = '%s %s' % (cmd, module.params[param])

    rc, out, err = module.run_command(cmd, cwd=os.path.expanduser(app_path))
    if rc != 0:
        if command == 'createcachetable' and 'table' in err and 'already exists' in err:
            out = 'Already exists.'
        else:
            if "Unknown command:" in err:
                _fail(module, cmd, err, "Unknown django command: %s" % command)
            _fail(module, cmd, out, err, path=os.environ["PATH"], syspath=sys.path)

    changed = False

    lines = out.split('\n')
    filt = globals().get(command + "_filter_output", None)
    if filt:
        filtered_output = list(filter(filt, lines))
        if len(filtered_output):
            changed = filtered_output

    module.exit_json(changed=changed, out=out, cmd=cmd, app_path=app_path, virtualenv=virtualenv,
                     settings=module.params['settings'], pythonpath=module.params['pythonpath'])


if __name__ == '__main__':
    main()
