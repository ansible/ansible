#!/usr/bin/python
# coding: utf-8 -*-

# (c) 2017, Wayne Witzel III <wayne@riotousliving.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: tower_job_list
author: "Wayne Witzel III (@wwitzel3)"
version_added: "2.3"
short_description: List Ansible Tower jobs.
description:
    - List Ansible Tower jobs. See
      U(https://www.ansible.com/tower) for an overview.
options:
    status:
      description:
        - Only list jobs with this status.
      choices: ['pending', 'waiting', 'running', 'error', 'failed', 'canceled', 'successful']
    page:
      description:
        - Page number of the results to fetch.
    all_pages:
      description:
        - Fetch all the pages and return a single result.
      type: bool
      default: 'no'
    query:
      description:
        - Query used to further filter the list of jobs. C({"foo":"bar"}) will be passed at C(?foo=bar)
extends_documentation_fragment: tower
'''


EXAMPLES = '''
- name: List running jobs for the testing.yml playbook
  tower_job_list:
    status: running
    query: {"playbook": "testing.yml"}
    register: testing_jobs
    tower_config_file: "~/tower_cli.cfg"
'''

RETURN = '''
count:
    description: Total count of objects return
    returned: success
    type: int
    sample: 51
next:
    description: next page available for the listing
    returned: success
    type: int
    sample: 3
previous:
    description: previous page available for the listing
    returned: success
    type: int
    sample: 1
results:
    description: a list of job objects represented as dictionaries
    returned: success
    type: list
    sample: [{"allow_simultaneous": false, "artifacts": {}, "ask_credential_on_launch": false,
              "ask_inventory_on_launch": false, "ask_job_type_on_launch": false, "failed": false,
              "finished": "2017-02-22T15:09:05.633942Z", "force_handlers": false, "forks": 0, "id": 2,
              "inventory": 1, "job_explanation": "", "job_tags": "", "job_template": 5, "job_type": "run"}, ...]
'''


from ansible.module_utils.basic import AnsibleModule

from ansible.module_utils.ansible_tower import tower_auth_config, tower_check_mode, tower_argument_spec, HAS_TOWER_CLI

try:
    import tower_cli
    import tower_cli.utils.exceptions as exc

    from tower_cli.conf import settings
except ImportError:
    pass


def main():
    argument_spec = tower_argument_spec()
    argument_spec.update(dict(
        status=dict(choices=['pending', 'waiting', 'running', 'error', 'failed', 'canceled', 'successful']),
        page=dict(type='int'),
        all_pages=dict(type='bool', default=False),
        query=dict(type='dict'),
    ))

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True
    )

    if not HAS_TOWER_CLI:
        module.fail_json(msg='ansible-tower-cli required for this module')

    json_output = {}

    query = module.params.get('query')
    status = module.params.get('status')
    page = module.params.get('page')
    all_pages = module.params.get('all_pages')

    tower_auth = tower_auth_config(module)
    with settings.runtime_values(**tower_auth):
        tower_check_mode(module)
        try:
            job = tower_cli.get_resource('job')
            params = {'status': status, 'page': page, 'all_pages': all_pages}
            if query:
                params['query'] = query.items()
            json_output = job.list(**params)
        except (exc.ConnectionError, exc.BadRequest) as excinfo:
            module.fail_json(msg='Failed to list jobs: {0}'.format(excinfo), changed=False)

    module.exit_json(**json_output)


if __name__ == '__main__':
    main()
