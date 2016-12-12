#!/usr/bin/env python
#coding: utf-8 -*-

# (c) 2016, Wayne Witzel III <wayne@riotousliving.com>
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
module: tower_job_wait
version_added: "2.3"
short_description: Wait for Ansible Tower job to finish.
description:
    - Wait for Ansible Tower job to finish and report success or failure. See
      U(https://www.ansible.com/tower) for an overview.
options:
    job_id:
      description:
        - ID string of the job to monitor.
      required: True
      default: null
    min_interval:
      description:
        - Minimum interval to request an update from Tower.
      required: False
      default: 1
    max_interval:
      description:
        - Maximum interval to request an update from Tower.
      required: False
      default: 30
    timeout:
      description:
        - Maximum time in seconds to wait for a job to finish.
      required: False
      default: null
    config_file:
      description:
        - Path to the Tower config file. See notes.
      required: False
      default: null


requirements:
  - "ansible-tower-cli >= 3.0.3"

notes:
  - If no I(config_file) is provided we will attempt to use the tower-cli library
    defaults to find your Tower host information.
  - I(config_file) should contain Tower configuration in the following format:
      host=hostname
      username=username
      password=password
'''


EXAMPLES = '''
    tower_job_wait:
        job_id: 5
        timeout: 120
        config_file: "~/tower_cli.cfg"
'''

import os
import sys
import contextlib

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

try:
    import tower_cli
    import tower_cli.utils.exceptions as exc
    from tower_cli.utils import parser
    from tower_cli.conf import settings

    HAS_TOWER_CLI = True
except ImportError:
    HAS_TOWER_CLI = False


@contextlib.contextmanager
def nostdout():
    _stdout = sys.stdout
    sys.stdout = StringIO()
    yield
    sys.stdout = _stdout


def tower_auth_config(module):
    config_file = module.params.get('config_file')
    if not config_file:
        return {}

    config_file = os.path.expanduser(config_file)
    if not os.path.exists(config_file):
        module.fail_json(msg='file not found: %s' % config_file)
    if os.path.isdir(config_file):
        module.fail_json(msg='directory can not be used as config file: %s' % config_file)

    with open(config_file, 'rb') as f:
        return parser.string_to_dict(f.read())


def main():
    module = AnsibleModule(
        argument_spec = dict(
            job_id = dict(type='int', required=True),
            timeout = dict(),
            min_interval = dict(type='float', default=1),
            max_interval = dict(type='float', default=30),
            config_file = dict(),
        ),
        supports_check_mode=False
    )

    if not HAS_TOWER_CLI:
        module.fail_json(msg='ansible-tower-cli required for this module')

    json_output = {}
    fail_json = None

    # tower-cli gets very noisy when monitoring.
    # We use nostdout to surppress the stdout during our monitor call.
    tower_auth = tower_auth_config(module)
    with nostdout():
        with settings.runtime_values(**tower_auth):
            job = tower_cli.get_resource('job')
            params = module.params.copy()
            job_id = params.get('job_id')
            try:
                result = job.monitor(job_id, **params)
            except exc.NotFound as excinfo:
                fail_json = dict(msg='{} job_id: {}'.format(excinfo, job_id), changed=False)
            except (exc.ConnectionError, exc.BadRequest) as excinfo:
                fail_json = dict(msg='{}'.format(excinfo), changed=False)

    if fail_json is not None:
        module.fail_json(**fail_json)

    for k in ('id', 'status', 'elapsed', 'started', 'finished'):
        json_output[k] = result.get(k)

    module.exit_json(**json_output)


from ansible.module_utils.basic import AnsibleModule
if __name__ == '__main__':
    main()
