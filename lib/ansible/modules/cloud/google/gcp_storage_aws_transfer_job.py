#!/usr/bin/python

# Copyright: (c) 2018, Terry Jones <terry.jones@example.org>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {
    'metadata_version': '1.0',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: gcp_storage_aws_transfer_job
version_added: 2.10
short_description: Creates GCP Transfer Jobs between AWS S3 and GCP Storage.
description: This module will create GCP Storage Transfer Jobs which transfers AWS S3 Bucket objects into the specified
             GCP Bucket. If there is an existing Transfer Job with the same Description it will delete it and create a new job.
             If you include the parameter aws_s3_bucket_prefix, it will transfer that prefix only, otherwise it will transfer all
             objects in the bucket. The Transfer Jobs will only pull changed or new objects when they execute.

options:
    project_id:
        description:
            - GCP account project id.
        required: true
        type: str
    scheduled_start_date_utc:
        description:
            - Start date of transfer job in YYYY-MM-DD format.
            - For details on how transfer job schedules work see https://cloud.google.com/storage-transfer/docs/reference/rest/v1/transferJobs#schedule.
        required: true
        type: str
    scheduled_end_date_utc:
        description:
            - End date of transfer job in YYYY-MM-DD format .
        required: true
        type: str
    scheduled_start_time_utc:
        description:
            - Transfer job start time in HH:SS format.
        required: true
        type: str
    gcp_storage_bucket:
        description:
            - The GCP storage bucket to transfer objects into.
        required: true
        type: str
    service_account_file:
        description:
            - GCP credentails file.
        required: true
        type: str
    aws_s3_bucket:
        description:
            - AWS S3 bucket which contains the source objects.
        required: true
        type: str
    aws_s3_bucket_prefix:
        description:
            - Prefix within the S3 bucket which contains the source objects.
        required: false
        type: str
    description:
        description:
            - This is used as a unique name for the transfer job. If a job with the same description exists, it is replaced, or deleted depending on state.
        required: true
        type: str
    state:
        description:
            - Whether to create/update or delete a transfer job. Options are present and absent.
        required: true
        type: str
    aws_access_key:
        description:
            - The AWS IAM account access key used by the transfer job to retreive S3 objects.
        required: true
        type: str
    aws_secret_key:
        description:
            - The AWS IAM account access key secret used by the transfer job to retreive S3 objects.
        required: true
        type: str

author:
    - Chanaka Samarajeewa (@csamarajeewa)
'''

EXAMPLES = '''

# Create a new job / replace existing job

- name: Create Bucket Transfer Job
  gcp_storage_aws_transfer_job:
    project_id: "{{ item.project_id }}"
    scheduled_start_date_utc: "{{ item.scheduled_start_date_utc }}"
    scheduled_end_date_utc: "{{ item.scheduled_end_date_utc }}"
    scheduled_start_time_utc: "{{ item.scheduled_start_time_utc }}"
    gcp_storage_bucket: "{{ item.gcp_storage_bucket }}"
    service_account_file: "{{ lookup('env','GCE_CREDENTIALS_FILE_PATH') }}"
    aws_s3_bucket: "{{ item.aws_s3_bucket }}"
    aws_s3_bucket_prefix: "{{ item.aws_s3_bucket_prefix | default(omit) }}"
    aws_access_key: "{{ item.aws_access_key }}"
    aws_secret_key: "{{ item.aws_secret_key }}"
    description: "{{ item.description }}"
    state: present
  loop: "{{ gcp_create_transfer_jobs }}"

# Delete an existing job

- name: Delete Bucket Transfer Job
  gcp_storage_aws_transfer_job:
    project_id: "{{ item.project_id }}"
    scheduled_start_date_utc: "{{ item.scheduled_start_date_utc }}"
    scheduled_end_date_utc: "{{ item.scheduled_end_date_utc }}"
    scheduled_start_time_utc: "{{ item.scheduled_start_time_utc }}"
    gcp_storage_bucket: "{{ item.gcp_storage_bucket }}"
    service_account_file: "{{ lookup('env','GCE_CREDENTIALS_FILE_PATH') }}"
    aws_s3_bucket: "{{ item.aws_s3_bucket }}"
    aws_s3_bucket_prefix: "{{ item.aws_s3_bucket_prefix | default(omit) }}"
    aws_access_key: "{{ item.aws_access_key }}"
    aws_secret_key: "{{ item.aws_secret_key }}"
    description: "{{ item.description }}"
    state: absent
  loop: "{{ gcp_create_transfer_jobs }}"


'''

RETURN = '''
original_message:
    description: The original name param that was passed in
    type: str
    returned: always
message:
    description: The output message that the sample module generates
    type: str
    returned: always
'''

import datetime
import json
import googleapiclient.discovery

from google.oauth2 import service_account
from ansible.module_utils.basic import AnsibleModule


def run_module():

    module_args = dict(
        project_id=dict(type='str', required=True),
        scheduled_start_date_utc=dict(type='str', required=True),
        scheduled_end_date_utc=dict(type='str', required=True),
        scheduled_start_time_utc=dict(type='str', required=True),
        gcp_storage_bucket=dict(type='str', required=True),
        service_account_file=dict(type='str', required=True),
        aws_s3_bucket=dict(type='str', required=True),
        aws_s3_bucket_prefix=dict(type='str', required=False),
        aws_access_key=dict(type='str', required=True),
        aws_secret_key=dict(type='str', required=True),
        description=dict(type='str', required=True),
        state=dict(type='str', required=True)
    )

    result = dict(
        changed=False,
        original_message='',
        message=''
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    if module.check_mode:
        module.exit_json(**result)

    start_date = datetime.datetime.strptime(module.params['scheduled_start_date_utc'], '%Y/%m/%d')
    end_date = datetime.datetime.strptime(module.params['scheduled_end_date_utc'], '%Y/%m/%d')
    start_time = datetime.datetime.strptime(module.params['scheduled_start_time_utc'], '%H:%M')

    delete_transfer_job = {
        'project_id': module.params['project_id'],
        'transfer_job': {
            'status': 'DELETED'
        }
    }

    transfer_job = {
        'description': module.params['description'],
        'status': 'ENABLED',
        'projectId': module.params['project_id'],
        'schedule': {
            'scheduleStartDate': {
                'day': start_date.day,
                'month': start_date.month,
                'year': start_date.year
            },
            'scheduleEndDate': {
                'day': start_date.day,
                'month': end_date.month,
                'year': end_date.year
            },
            'startTimeOfDay': {
                'hours': start_time.hour,
                'minutes': start_time.minute,
                'seconds': start_time.second
            }
        },
        'transferSpec': {
            'objectConditions': {
                'includePrefixes': module.params['aws_s3_bucket_prefix']
            },
            'transferOptions': {
                'overwriteObjectsAlreadyExistingInSink': 'False',
                'deleteObjectsUniqueInSink': 'False',
                'deleteObjectsFromSourceAfterTransfer': 'False'
            },
            'awsS3DataSource': {
                'bucketName': module.params['aws_s3_bucket'],
                'awsAccessKey': {
                    'accessKeyId': module.params['aws_access_key'],
                    'secretAccessKey': module.params['aws_secret_key']
                }
            },
            'gcsDataSink': {
                'bucketName': module.params['gcp_storage_bucket']
            }
        }
    }

    credentials = service_account.Credentials.from_service_account_file(module.params['service_account_file'])
    storagetransfer = googleapiclient.discovery.build('storagetransfer', 'v1', credentials=credentials)

    filterString = (
        '{{"project_id": "{project_id}"}}'
    ).format(project_id=module.params['project_id'])

    queryResult = storagetransfer.transferJobs().list(filter=filterString).execute()
    result['message'] = queryResult

    # Delete existing job if exists, then create new job
    if 'transferJobs' in queryResult:
        for transferJob in queryResult['transferJobs']:
            if transferJob['description'] == module.params['description']:
                storagetransfer.transferJobs().patch(body=delete_transfer_job, jobName=transferJob['name']).execute()
                result['message'] = 'Deleted existing Transfer Jobs with the same Description'

    if 'present' in module.params['state']:
        storagetransfer.transferJobs().create(body=transfer_job).execute()
        result['message'] = 'Created new Transfer Job'

    result['original_message'] = module.params
    result['changed'] = 'True'

    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
