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
            - If C(present), the job is submitted to the nomad API, if C(absent) the job is deleted via the nomad API, if C(status) the health of the job is checked.
        required: no
        default: present
        choices: [present, absent, status]
    name:
        description:
            - The name of the job to be handled (needs to match the Job-ID in the jobs definition I(jobjson) or I(jobhcl) when the desired I(state=present)).
        required: yes
        aliases: ['job']
    jobjson:
        description:
           - The nomad job description in json (https://www.nomadproject.io/api/json-jobs.html).
           - Required if I(state=present)
        required: no
        default: ""
    jobhcl:
        description:
           - The nomad job description in HCL
           - Required if I(state=present)
        required: no
        default: ""
    url:
        description:
            - The nomad server URL.
        required: no
        default: "http://localhost:4646"
        aliases: ['server']
    timeout:
        description:
            - The timeout in I(retry_delay) for the allocations created by a job to enter the 'running' state.
        required: no
        default: 120
    retry_delay:
        description:
            - The time in seconds to wait between api requests. This times I(timeout) equals the total number of seconds.
        required: no
        default: 1
    wait_for_healthy:
        description:
            - If set to C(False) (default C(True)) this module will not wait for the allocations of a job to enter the 'healthy' state.
        required: no
        type: bool
        default: True
    wait_for_completion:
        description:
            - If set to C(False) (default C(True)) this module will not wait for the job to enter the 'running' state.
        required: no
        type: bool
        default: True
    check_deploy_health:
        description:
            - If set to C(True) (default C(False)) this module will check the deployment-health instead of the status of each allocation (>= 0.6)
        required: no
        type: bool
        default: False
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
    jobjson: "{{ lookup('template', 'my-job.json.j2') }}"
    timeout: 30

- name: Delete / Stop a job
  nomad_job:
    name: my-unwanted-job
    state: absent

- name: Create / Update a job and don't wait for its completion
  nomad_job:
    name: my-2nd-job
    jobhcl: "{{ lookup('file', 'my-2nd-job.hcl') }}"
    wait_for_completion: False
'''

RETURN = '''
evaluation:
    description: the json object return by the nomad API when evaluating the job.
    returned: success, changed
    type: dict
deployment:
    description: the deployment id.
    returned: success, changed
    type: string
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
import signal
from collections import Counter
from time import sleep


class NomadJobException(Exception):
    """Base exception for errors raised by ansible nomad job module"""
    def __init__(self, message, meta=None, *args):
        super(NomadJobException, self).__init__(*args)
        self.message = message
        self.meta = meta


class NomadException(NomadJobException):
    """responsible for errors returned from nomad"""


class JobDescriptionError(NomadJobException):
    """Raises when there is no job description."""
    def __init__(self):
        super(JobDescriptionError, self).__init__(
            "A job description in json (jobjson) or hcl (jobhcl) needs to be provided for the state 'present'!",
        )


class DoubleJobDescriptionError(NomadJobException):
    """Raises when there are multiple job descriptions."""
    def __init__(self):
        super(DoubleJobDescriptionError, self).__init__(
            "A job description in json (jobjson) OR hcl (jobhcl) needs to be provided. NOT both!",
        )


class JobNameMismatch(NomadJobException):
    """Raises when the name parameter does not match the ID in the job description."""
    def __init__(self):
        super(JobNameMismatch, self).__init__(
            "The Jobname specified does not match the Jobs ID in the jobdescription (jobjson) OR (jobhcl) !",
        )


class EvaluationError(NomadException):
    def __init__(self, msg, meta):
        super(EvaluationError, self).__init__(
            "Evaluation failure! nomad response: {}".format(msg),
            meta=meta
        )


class JobListError(NomadException):
    def __init__(self, msg, meta):
        super(JobListError, self).__init__(
            "Error on getting the current job-list from Nomad. nomad response: {}".format(msg),
            meta=meta
        )


class DeleteError(NomadException):
    def __init__(self, msg, meta):
        super(DeleteError, self).__init__(
            "Deleting job failed!. nomad response: {}".format(msg),
            meta=meta
        )


class SubmissionError(NomadException):
    def __init__(self, msg, meta):
        super(SubmissionError, self).__init__(
            "Failed to submit job!. nomad response: {}".format(msg),
            meta=meta
        )


class HCLConversionError(NomadException):
    def __init__(self, msg, meta):
        super(HCLConversionError, self).__init__(
            "Failed to convert job from HCL to JSON!. nomad response: {}".format(msg),
            meta=meta
        )


class JobStatusError(NomadException):
    def __init__(self, msg, meta):
        super(JobStatusError, self).__init__(
            "Failed to get job status! nomad response: {}".format(msg),
            meta=meta
        )


class AllocationFailureError(NomadException):
    def __init__(self, msg, meta):
        super(AllocationFailureError, self).__init__(
            "Allocation failed! nomad response: {}".format(msg),
            meta=meta
        )


class AllocationTimeoutError(NomadException):
    def __init__(self, msg, meta):
        super(AllocationTimeoutError, self).__init__(
            "Timeout while waiting for allocations to be running. Please check the jobs logs! {}".format(msg),
            meta=meta
        )


class Endpoint(object):
    """This class is used by Nomad class to send requests to nomad and get the
    response from nomad."""
    def __init__(self, ansible_module, base_url):
        self.ansible_module = ansible_module
        self.base_url = base_url

    def _endpoint_builder(self, *args):
        return '/'.join((self.base_url,) + args).strip('/')

    def _request(self, data=None, headers=None, method='GET', path=(), timeout=30):
        resp, info = fetch_url(
            self.ansible_module,
            self._endpoint_builder(*path),
            data=data,
            headers=headers,
            method=method,
            timeout=timeout
        )

        try:
            resp = json.loads(resp.read())
        except AttributeError:
            resp = ''

        return info['status'], info, resp

    def get(self, *args):
        return self._request(path=args)

    def post(self, data, headers=None, *args):
        return self._request(data=data, headers=headers, method='POST', path=args)

    def delete(self, *args):
        return self._request(method='DELETE', path=args)


class Nomad(object):
    """This class is a Wrapper for nomad restful api."""

    def __init__(self, ansible_module, url='http://127.0.0.1', token=None, timeout=5, version='v1', verify=False, cert=()):
        self.ansible_module = ansible_module
        self.url = url
        self.token = token
        self.timeout = timeout
        self.version = version
        self.verify = verify
        self.cert = cert
        self._endpoints = [
            'job',
            'jobs',
            'deployment',
            'deployments',
            'evaluation',
            'evaluations',
            'allocation',
            'allocations',
        ]

    def _endpoint_builder(self, *args):
        addr=""
        if args:
            addr = "/".join(args)
        return "{version}/{addr}".format(version=self.version, addr=addr)

    def _url_builder(self, endpoint):
        url = "{url}/{endpoint}".format(
            url=self.url,
            endpoint=self._endpoint_builder(endpoint)
        )
        return url

    def __getattr__(self, name):
        if name not in self._endpoints:
            # default behaviour
            raise AttributeError('attribute with name: "{}" is not defined'.format(name))

        return Endpoint(self.ansible_module, self._url_builder(name))

    def get_job_stable_status(self, name):
        """when a job is sent to nomad the first status is always running.
        in case we get the correct status we try a few times to check that
        the status we want to return is the most common status returned by
        api. in case of one failure we return the failed status. this doesn't
        guarantee the correct status, but it is a better measure for job status.
        """
        count = 6
        status_list = []

        while count > 1:
            status, info, body = self.job.get(name)
            if status == 200 and type(body) == dict:
                status_list.append(body['Status'])

            count -= 1
            sleep(0.5)
        counter = Counter(status_list)
        if counter['running'] > 2:
            return 'running'
        return counter.most_common(1)[0][0]

    def get_evaluation_or_fail(self, evaluation_id, retry_timeout_sec, retry_delay):
        with Timeout(retry_timeout_sec):
            while True:
                status, info, body = self.evaluation.get(evaluation_id)

                if body['Status'] == 'complete':
                    return body

                if body['Status'] not in ('complete', 'pending'):
                    raise EvaluationError(body, info)

                sleep(retry_delay)

    def get_allocations_or_fail(self, deployment_id, retry_timeout_sec, retry_delay):
        # Get all allocations
        status, info, allocation_list = None, None, []
        try:
            with Timeout(retry_timeout_sec):
                while len(allocation_list) < 1:
                    status, info, allocation_list = self.deployment.get('allocations', deployment_id)
                    if allocation_list:
                        break
                    sleep(retry_delay)

        except Timeout.Timeout:
            raise AllocationTimeoutError(allocation_list, info)

        return allocation_list


def run_module(ansible_module):

    jobjson = ansible_module.params['jobjson']
    jobhcl = ansible_module.params['jobhcl']
    url = ansible_module.params['url']
    name = ansible_module.params['name']
    state = ansible_module.params['state']
    timeout = ansible_module.params['timeout']
    retry_delay = ansible_module.params['retry_delay']
    wait_for_healthy = ansible_module.params['wait_for_healthy']
    wait_for_completion = ansible_module.params['wait_for_completion']
    check_deploy_health = ansible_module.params['check_deploy_health']
    wait_for_allocations_timeout = 20

    # Initialize some defaults
    job_deployment_id = None
    job_evaluation = ''
    new_job_info = None

    nomad_cli = Nomad(ansible_module, url=url, timeout=timeout)

    # Check if we have a job description when the desired state is 'present'
    if not jobjson and not jobhcl and state == 'present':
        raise JobDescriptionError()

    # Check if we have only one job description
    if jobjson and jobhcl:
        raise DoubleJobDescriptionError()

    # get possible running job
    status, info, job = nomad_cli.job.get(name)

    job_changed = True
    if status == 404:
        # if the job does not exist - exit here with no change
        if state == 'absent':
            ansible_module.exit_json(changed=job_changed, status=status, job=job, info=info)
        if state == 'status':
            raise JobStatusError(job, info['body'])

    elif status != 200:
        if type(body) == dict:
            raise JobListError(job, info['body'])
        else:
            raise JobListError(job, info)

    # Delete job if requested (TODO: implement purge option)
    if state == 'absent':
        status, info, body = nomad_cli.job.delete(name)
        if status != 200:
            raise DeleteError(body, info['msg'])

        ansible_module.exit_json(changed=True, status=status, job=job, info=info)

    if state == 'status':
        job_changed = False
        # Get jobs info
        if 'JobModifyIndex' in job:
            status, info, body = nomad_cli.job.get(name, 'evaluations')
            for evaluation in body:
                if evaluation['JobModifyIndex'] == job['JobModifyIndex']:
                    job_evaluation = evaluation['ID']
        else:
            raise JobStatusError(job, job)
    else:
        # Get job in correct format:
        if jobjson:
            # already json format
            jobdesc=jobjson
        elif jobhcl:
            # hcl that needs to be converted via the API
            jobdescrequest=json.dumps({"Canonicalize": True, "JobHCL": jobhcl})
            status, evaluation_response, convertedjob = nomad_cli.jobs.post(
                jobdescrequest, {}, 'parse')
            if status != 200:
                raise HCLConversionError(evaluation_response, convertedjob)
            jobdesc=json.dumps({ "Job": convertedjob})
        else:
            raise JobDescriptionError()
        
        # Check if the Jobs ID matches the specified name
        if name != json.loads(jobdesc)["Job"]["ID"]:
            raise JobNameMismatch()

        # Submit Job:
        status, new_job_info, evaluation_response = nomad_cli.jobs.post(
            data=jobdesc,
            headers={'Content-Type': 'application/json'}
        )
        if status != 200:
            raise SubmissionError(evaluation_response, new_job_info)

        job_evaluation = evaluation_response['EvalID']

    if not job_evaluation:
        # Must be a batch job ... nothing else to do here
        ansible_module.exit_json(
            changed=job_changed,
            status=status,
            job=job,
            info=new_job_info
        )
    eval_response = nomad_cli.get_evaluation_or_fail(
        job_evaluation,
        timeout,
        retry_delay
    )

    # Read possible deferred evaluation and check for completion
    if eval_response['BlockedEval']:
        job_evaluation = eval_response['BlockedEval']

    # If we don't want to wait for the completion of the job, exit here.
    if not wait_for_completion:
        ansible_module.exit_json(
            changed=job_changed,
            status=status,
            job=job,
            info=new_job_info)

    # if we don't want to check health get the stable status of the job and exit here
    if not wait_for_healthy:
        with Timeout(wait_for_allocations_timeout):
            while True:
                status = nomad_cli.get_job_stable_status(name)
                if status == "running":
                    ansible_module.exit_json(
                        changed=job_changed,
                        status=status,
                        job=job,
                        info=new_job_info
                    )

                if status == "dead":
                    raise JobStatusError(status, info)

                sleep(retry_delay)

    if not eval_response.get('DeploymentID'):
        # DeploymentID is empty when count = 0
        ansible_module.exit_json(changed=job_changed,
                                 status=status,
                                 job=job,
                                 total_jobs=0,
                                 total_allocations=0,
                                 allocations=[],
                                 info=new_job_info)

    # Work with the deployment ID from here on
    deployment_id = eval_response.get('DeploymentID')
    allocation_list = nomad_cli.get_allocations_or_fail(
        deployment_id,
        wait_for_allocations_timeout,
        retry_delay
    )

    # Check each allocation and each task for their status
    total_jobs = 0
    total_allocations = len(allocation_list)
    for allocation in allocation_list:
        allocation_id = allocation['ID']
        is_running = 0  # needs to get 2 successful "running" states within 2 seconds !
        allocation_info = None

        try:
            with Timeout(timeout):
                while True:
                    status, info, allocation_info = nomad_cli.allocation.get(allocation_id)
                    if status == 200 and type(allocation_info) == dict:
                        num_tasks = 0
                        if check_deploy_health:
                            if allocation_info['DeploymentStatus']:
                                if allocation_info['DeploymentStatus']['Healthy']:
                                    num_tasks = len(allocation_info['TaskStates'])
                                    is_running += 1
                                else:
                                    is_running = 0
                        else:
                            if allocation_info['ClientStatus'] == 'running':
                                num_tasks = len(allocation_info['TaskStates'])
                                is_running += 1
                            else:
                                is_running = 0

                        if is_running > 1:
                            total_jobs += num_tasks
                            break

                    sleep(retry_delay)
        except Timeout.Timeout:
            if is_running < 2:
                raise AllocationTimeoutError("timeout: {}".format(timeout), allocation_info)

    # Get new allocations
    status, info, new_job_allocations = nomad_cli.job.get(name, 'allocations')

    ansible_module.exit_json(
        changed=job_changed,
        evaluation=job_evaluation,
        deployment=deployment_id,
        job=job,
        total_jobs=total_jobs,
        total_allocations=total_allocations,
        allocations=new_job_allocations,
        info=new_job_info
    )


class Timeout:
    """Timeout class using ALARM signal."""

    class Timeout(NomadException):
        """raises when there is a timeout for getting response from nomad!
        Attention! DO NOT use this context manager within an already created
        Timeout context, otherwise you will end up in an infinit loop!
        """
        pass

    def __init__(self, sec):
        self.sec = sec

    def __enter__(self):
        signal.signal(signal.SIGALRM, self.raise_timeout)
        signal.alarm(self.sec)

    def __exit__(self, *args):
        signal.alarm(0)  # disable alarm

    def raise_timeout(self, *args):
        raise Timeout.Timeout("Time out! {} seconds passed and nothing happened".format(self.sec))


def main():
    ansible_module = AnsibleModule(
        argument_spec={
            "state": {"default": 'present', "choices": ['present', 'absent', 'status']},
            "name": {"required": True},
            "jobjson": {"default": "", "type": 'json'},
            "jobhcl": {"default": "", "type": 'str'},
            "job": {"aliases": ['name']},
            "url": {"default": 'http://localhost:4646'},
            "server": {"aliases": ['url']},
            "timeout": {"default": 120, "type": 'int'},
            "retry_delay": {"default": 1, "type": 'int'},
            "wait_for_healthy": {"default": True, "type": 'bool'},
            "wait_for_completion": {"default": True, "type": 'bool'},
            "check_deploy_health": {"default": False, "type": 'bool'}
        }
    )
    try:
        run_module(ansible_module)
    except NomadJobException as exc:
        ansible_module.fail_json(
            msg=exc.message,
            meta=exc.meta
        )


if __name__ == '__main__':
    main()
