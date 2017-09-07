#!/usr/bin/python
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

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'metadata_version': '1.1'}

DOCUMENTATION = '''
---
module: nomad_job
short_description: submit or delete a job to Hashicorps nomad
description:
    - The M(nomad_job) module manages submitting and deleting of jobs in the Hashicorp nomad scheduler and cluster manager.
    - This module uses the nomad API (https://www.nomadproject.io/api/).
    - Supported nomad versions are 0.5.* and 0.6.* .
    - This module takes a json input describing a nomad job (https://www.nomadproject.io/api/json-jobs.html) when the desired state is C(present)'.
    - By default the module will wait for all allocations of a submited job to be in 'running' state unless specified otherwise (I(wait_for_completion=False)),
      the count is 0 or the type is 'batch'.
    - The module will fail if a job (all its allocations) does not enter the 'running' state within the specified I(timeout) (default 120 sec).
version_added: "2.5"
author:
    - Sirk Johannsen (sirkjohannsen)
    - Moeen Mirjalili (momirjalili)
options:
    state:
        description:
            - If C(present), the job is submitted to the nomad API, if C(absent) the job is deleted via the nomad API.
        required: no
        default: present
        choices: [present, absent]
    name:
        description:
            - The name of the job to be handled (needs to match the Job-ID in the jobs json description I(jobdesc) when the desired I(state=present)).
        required: yes
        aliases: ['job']
    jobdesc:
        description:
           - The nomad job description in json (https://www.nomadproject.io/api/json-jobs.html).
           - Required if I(state=present)
        required: no
        default: ""
        aliases: ['jobjson', 'desc']
    url:
        description:
            - The nomad server URL.
        required: no
        default: "http://localhost:4646"
        aliases: ['server']
    timeout:
        description:
            - The timeout in seconds for the allocations created by a job to enter the 'running' state.
        required: no
        default: 120
    wait_for_completion:
        description:
            - If set to C(False) (default C(True)) this module will not wait for the allocations of a job to enter the 'running' state.
        required: no
        type: bool
        default: True
notes:
    - check_mode is not supported yet.
    - the I(purge) option on deletion of a job is not implemented yet.
    - The returned value of "changed" is C(True) even if the job submittid is identical to the job already registered in Nomad.
'''

EXAMPLES = '''
- name: Create / Update a job from a template that should be running within 30 seconds
  nomad_job:
    name: my-job
    state: present
    jobdesc: "{{ lookup('template', 'my-job.json.j2') }}"
    timeout: 30

- name: Delete / Stop a job
  nomad_job:
    name: my-unwanted-job
    state: absent

- name: Create / Update a job and don't wait for its completion
  nomad_job:
    name: my-2nd-job
    jobdesc: "{{ lookup('file', 'my-2nd-job.json') }}"
    wait_for_completion: False
'''

RETURN = '''
evaluation:
    description: the json object return by the nomad API when evaluating the job.
    returned: success, changed
    type: dict
job:
    description: the json object of the previous job (in case it existed)
    returned: success, changed
    type: dict
total_jobs:
    description: the total number of jobs that were handled.
    returned: success, changed
    type: int
    sample: 1
total_allocations:
    description: the total number of allocations that were handled.
    returned: success, changed
    type: int
    sample: 2
allocations:
    description: a json object with all handled allocations
    returned: success, changed
    type: dict
info:
    description: the info returned by the fetch_url function when submitting the new job
    returned: success, changed
    type: list
'''

# Import Ansible module
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.urls import fetch_url

# Import other modules
import json
from time import sleep


class ResponseErrors:
    JOB_DESC_ERROR = "A job description in json (jobdesc) needs to be provided for the state 'present'!"
    EVALUATION_ERROR = "Evaluation failure!"
    CONNECTION_ERROR = "Cannot connect to Nomad Server!"
    JOB_LIST_ERROR = "Error on getting the current job-list from Nomad"
    DELETE_ERROR = "Deleting job failed!"
    CURRENT_ALLOCATION_ERROR = "Failed to get current allocations!"
    SUBMISSION_ERROR = "Failed to submit job!"
    DEFERRED_EVALUATION_ERROR = 'Evaluation was deferred and did not complete!'
    INCOMPLETE_EVALUATION_ERROR = 'Evaluation did not complete!'
    ALLOCATION_STATUS_ERROR = "Failed to get allocation status!"
    ALLOCATION_FAILURE_ERROR = "Allocation failed!"
    ALLOCATION_TIMEOUT_ERROR = "Timeout while waiting for allocations to be running. Please check the jobs logs!"


def get_response_or_fail(ansible_module, url, fail_msg=None, **kwargs):
    resp, info = fetch_url(ansible_module, url, **kwargs)
    status = info['status']
    if status != 200:
        ansible_module.fail_json(msg=fail_msg if fail_msg else info, meta=info)
    return status, info, json.loads(resp.read())


def check_evaluation(ansible_module, url, job_evaluation, timeout):
    evaluation_url = url + '/v1/evaluation/' + job_evaluation
    evaluation_done = False
    for i in range(timeout):
        status, info, body = get_response_or_fail(ansible_module, evaluation_url, ResponseErrors.EVALUATION_ERROR)
        if body['Status'] == 'complete':
            evaluation_done = True
            break
        else:
            sleep(1)
    return evaluation_done, body


def get_evaluation_or_fail(ansible_module, url, job_evaluation, timeout, fail_msg):
    evaluation_done, eval_response = check_evaluation(ansible_module, url, job_evaluation, timeout)
    if not evaluation_done:
        ansible_module.fail_json(msg=fail_msg, meta=eval_response)
    return eval_response


def delete_job(ansible_module, jobs_url, job):
    resp, info = fetch_url(ansible_module, jobs_url, method='DELETE')
    status = info['status']

    if status != 200:
        ansible_module.fail_json(msg=ResponseErrors.DELETE_ERROR, meta=info['msg'])
    ansible_module.exit_json(changed=True, status=status, job=job, info=info)


def main():
    ansible_module = AnsibleModule(
        argument_spec={
            "state": {"default": 'present', "choices": ['present', 'absent']},
            "name": {"required": True},
            "jobdesc": {"default": "", "type": 'json'},
            "job": {"aliases": ['name']},
            "jobjson": {"aliases": ['jobdesc']},
            "desc": {"aliases": ['jobdesc']},
            "url": {"default": 'http://localhost:4646'},
            "server": {"aliases": ['url']},
            "timeout": {"default": 120, "type": 'int'},
            "wait_for_completion": {"default": True, "type": 'bool'}
        }
    )

    newjob = ansible_module.params['jobdesc']
    url = ansible_module.params['url']
    name = ansible_module.params['name']
    state = ansible_module.params['state']
    timeout = ansible_module.params['timeout']
    wait_for_completion = ansible_module.params['wait_for_completion']
    wait_for_allocations_timeout = 10

    # Check if we have a job description when the desired state is 'present'
    if not newjob and state == 'present':
        ansible_module.fail_json(msg=ResponseErrors.JOB_DESC_ERROR)

    # get possible running job
    jobs_url = url + '/v1/job/' + name
    resp, info = fetch_url(ansible_module, jobs_url)
    status = info['status']

    # couldn't connect to server
    if status < 0:
        ansible_module.fail_json(msg=ResponseErrors.CONNECTION_ERROR, meta=info['msg'])

    job_changed = True
    job = []
    if status == 404:
        # if the job does not exist - exit here with no change
        if state == 'absent':
            ansible_module.exit_json(changed=job_changed, status=status, job=job, info=info)
    elif status != 200:
        ansible_module.fail_json(msg=ResponseErrors.JOB_LIST_ERROR, meta=info['body'])
    else:
        job = json.loads(resp.read())

    # Delete job if requested (TODO: implement purge option)
    if state == 'absent':
        delete_job(ansible_module, jobs_url, job)

    # Submit Job:
    status, info, body = get_response_or_fail(ansible_module,
                                              jobs_url,
                                              fail_msg=ResponseErrors.SUBMISSION_ERROR,
                                              method='POST',
                                              data=newjob,
                                              headers={'Content-Type': 'application/json'})
    new_job_info = info
    evaluation_response = body
    job_evaluation = evaluation_response['EvalID']
    if not job_evaluation:
        # Must be a batch job ... nothing else to do here
        ansible_module.exit_json(changed=job_changed, status=status, job=job, info=new_job_info)

    # Wait for evluation to be complete
    eval_response = get_evaluation_or_fail(ansible_module,
                                           url,
                                           job_evaluation,
                                           timeout,
                                           fail_msg=ResponseErrors.INCOMPLETE_EVALUATION_ERROR)

    # Read possible deferred evaluation and check for completion
    if eval_response['BlockedEval']:
        job_evaluation = eval_response['BlockedEval']

    eval_response = get_evaluation_or_fail(ansible_module,
                                           url,
                                           job_evaluation,
                                           timeout,
                                           fail_msg=ResponseErrors.DEFERRED_EVALUATION_ERROR)

    # If we don't want to wait for the completion of the job, exit here.
    if not wait_for_completion:
        ansible_module.exit_json(
            changed=job_changed,
            status=status,
            job=job,
            info=new_job_info)

    # Set Deployment-ID if it exists (nomad >= 0.6.0)
    if 'DeploymentID' in eval_response:
        if eval_response['DeploymentID']:
            job_deployment_id = eval_response['DeploymentID']
            allocationsurl = url + '/v1/deployment/allocations/' + job_deployment_id
        else:
            # DeploymentID is empty when count = 0
            ansible_module.exit_json(changed=job_changed,
                                     status=status,
                                     job=job,
                                     total_jobs=0,
                                     total_allocations=0,
                                     allocations=[],
                                     info=new_job_info)
    else:
        allocationsurl = url + '/v1/evaluation/' + job_evaluation + '/allocations'

    # Get all allocations
    allocation_list = []
    for i in range(wait_for_allocations_timeout):
        status, info, body = get_response_or_fail(ansible_module, allocationsurl)
        allocation_list = body
        if len(allocation_list) > 0:
            break
        sleep(1)

    # We might not find any (count = 0)
    if len(allocation_list) <= 0:
        ansible_module.exit_json(
            changed=job_changed,
            status=status,
            job=job,
            total_jobs=0,
            total_allocations=0,
            allocations=allocation_list,
            info=new_job_info
        )

    # Check each allocation and each task for their status
    total_jobs = 0
    total_allocations = len(allocation_list)
    for allocation in allocation_list:
        allocation_id = allocation['ID']
        is_running = 0  # needs to get 2 successful "running" states within 2 seconds !
        for i in range(timeout):
            status, info, body = get_response_or_fail(
                ansible_module,
                url + '/v1/allocation/' + allocation_id,
                fail_msg=ResponseErrors.ALLOCATION_STATUS_ERROR
            )
            allocation_info = body
            if 'TaskStates' in allocation_info:
                num_tasks = len(allocation_info['TaskStates'])
                for task in allocation_info['TaskStates']:
                    task_state = allocation_info['TaskStates'][task]['State']
                    if (task_state == 'failed') or (task_state == 'dead'):
                        ansible_module.fail_json(msg=ResponseErrors.ALLOCATION_FAILURE_ERROR,
                                                 meta=allocation_info)
                    if task_state == 'running':
                        is_running += 1
                    else:
                        is_running = 0
            if is_running > 1:
                total_jobs += num_tasks
                break
            sleep(1)
        if is_running < 2:
            ansible_module.fail_json(msg=ResponseErrors.ALLOCATION_TIMEOUT_ERROR,
                                     meta=allocation_info)

    # Get new allocations
    status, info, body = get_response_or_fail(ansible_module,
                                              jobs_url + '/allocations')
    new_job_allocations = body

    ansible_module.exit_json(
        changed=job_changed,
        evaluation=job_evaluation,
        job=job,
        total_jobs=total_jobs,
        total_allocations=total_allocations,
        allocations=new_job_allocations,
        info=new_job_info
    )

if __name__ == '__main__':
    main()
