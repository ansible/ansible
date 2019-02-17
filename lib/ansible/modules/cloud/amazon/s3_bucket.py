#!/usr/bin/python
#
# This is a free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This Ansible library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this library.  If not, see <http://www.gnu.org/licenses/>.

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['stableinterface'],
                    'supported_by': 'core'}


DOCUMENTATION = '''
---
module: s3_bucket
short_description: Manage S3 buckets in AWS, DigitalOcean, Ceph, Walrus and FakeS3
description:
    - Manage S3 buckets in AWS, DigitalOcean, Ceph, Walrus and FakeS3
version_added: "2.0"
requirements: [ boto3 ]
author: "Rob White (@wimnat)"
options:
  force:
    description:
      - When trying to delete a bucket, delete all keys (including versions and delete markers)
        in the bucket first (an s3 bucket must be empty for a successful deletion)
    type: bool
    default: 'no'
  name:
    description:
      - Name of the s3 bucket
    required: true
  policy:
    description:
      - The JSON policy as a string.
  s3_url:
    description:
      - S3 URL endpoint for usage with DigitalOcean, Ceph, Eucalyptus and fakes3 etc.
      - Assumes AWS if not specified.
      - For Walrus, use FQDN of the endpoint without scheme nor path.
    aliases: [ S3_URL ]
  ceph:
    description:
      - Enable API compatibility with Ceph. It takes into account the S3 API subset working
        with Ceph in order to provide the same module behaviour where possible.
    type: bool
    version_added: "2.2"
  requester_pays:
    description:
      - With Requester Pays buckets, the requester instead of the bucket owner pays the cost
        of the request and the data download from the bucket.
    type: bool
    default: False
  state:
    description:
      - Create or remove the s3 bucket
    required: false
    default: present
    choices: [ 'present', 'absent' ]
  tags:
    description:
      - tags dict to apply to bucket
  versioning:
    description:
      - Whether versioning is enabled or disabled (note that once versioning is enabled, it can only be suspended)
    type: bool
extends_documentation_fragment:
    - aws
    - ec2
notes:
    - If C(requestPayment), C(policy), C(tagging) or C(versioning)
      operations/API aren't implemented by the endpoint, module doesn't fail
      if related parameters I(requester_pays), I(policy), I(tags) or
      I(versioning) are C(None).
'''

EXAMPLES = '''
# Note: These examples do not set authentication details, see the AWS Guide for details.

# Create a simple s3 bucket
- s3_bucket:
    name: mys3bucket

# Create a simple s3 bucket on Ceph Rados Gateway
- s3_bucket:
    name: mys3bucket
    s3_url: http://your-ceph-rados-gateway-server.xxx
    ceph: true

# Remove an s3 bucket and any keys it contains
- s3_bucket:
    name: mys3bucket
    state: absent
    force: yes

# Create a bucket, add a policy from a file, enable requester pays, enable versioning and tag
- s3_bucket:
    name: mys3bucket
    policy: "{{ lookup('file','policy.json') }}"
    requester_pays: yes
    versioning: yes
    tags:
      example: tag1
      another: tag2

# Create a simple DigitalOcean Spaces bucket using their provided regional endpoint
- s3_bucket:
    name: mydobucket
    s3_url: 'https://nyc3.digitaloceanspaces.com'

'''

import json
import os
import time

from ansible.module_utils.six.moves.urllib.parse import urlparse
from ansible.module_utils.six import string_types
from ansible.module_utils.basic import to_text
from ansible.module_utils.aws.core import AnsibleAWSModule, is_boto3_error_code
from ansible.module_utils.ec2 import compare_policies, ec2_argument_spec, boto3_tag_list_to_ansible_dict, ansible_dict_to_boto3_tag_list
from ansible.module_utils.ec2 import get_aws_connection_info, boto3_conn, AWSRetry

try:
    from botocore.exceptions import BotoCoreError, ClientError, EndpointConnectionError, WaiterError
except ImportError:
    pass  # handled by AnsibleAWSModule


def create_or_update_bucket(s3_client, module, location):

    policy = module.params.get("policy")
    name = module.params.get("name")
    requester_pays = module.params.get("requester_pays")
    tags = module.params.get("tags")
    versioning = module.params.get("versioning")
    changed = False
    result = {}

    try:
        bucket_is_present = bucket_exists(s3_client, name)
    except EndpointConnectionError as e:
        module.fail_json_aws(e, msg="Invalid endpoint provided: %s" % to_text(e))
    except (BotoCoreError, ClientError) as e:
        module.fail_json_aws(e, msg="Failed to check bucket presence")

    if not bucket_is_present:
        try:
            bucket_changed = create_bucket(s3_client, name, location)
            s3_client.get_waiter('bucket_exists').wait(Bucket=name)
            changed = changed or bucket_changed
        except WaiterError as e:
            module.fail_json_aws(e, msg='An error occurred waiting for the bucket to become available')
        except (BotoCoreError, ClientError) as e:
            module.fail_json_aws(e, msg="Failed while creating bucket")

    # Versioning
    try:
        versioning_status = get_bucket_versioning(s3_client, name)
    except BotoCoreError as exp:
        module.fail_json_aws(exp, msg="Failed to get bucket versioning")
    except ClientError as exp:
        if exp.response['Error']['Code'] != 'NotImplemented' or versioning is not None:
            module.fail_json_aws(exp, msg="Failed to get bucket versioning")
    else:
        if versioning is not None:
            required_versioning = None
            if versioning and versioning_status.get('Status') != "Enabled":
                required_versioning = 'Enabled'
            elif not versioning and versioning_status.get('Status') == "Enabled":
                required_versioning = 'Suspended'

            if required_versioning:
                try:
                    put_bucket_versioning(s3_client, name, required_versioning)
                    changed = True
                except (BotoCoreError, ClientError) as e:
                    module.fail_json_aws(e, msg="Failed to update bucket versioning")

                versioning_status = wait_versioning_is_applied(module, s3_client, name, required_versioning)

        # This output format is there to ensure compatibility with previous versions of the module
        result['versioning'] = {
            'Versioning': versioning_status.get('Status', 'Disabled'),
            'MfaDelete': versioning_status.get('MFADelete', 'Disabled'),
        }

    # Requester pays
    try:
        requester_pays_status = get_bucket_request_payment(s3_client, name)
    except BotoCoreError as exp:
        module.fail_json_aws(exp, msg="Failed to get bucket request payment")
    except ClientError as exp:
        if exp.response['Error']['Code'] != 'NotImplemented' or requester_pays is not None:
            module.fail_json_aws(exp, msg="Failed to get bucket request payment")
    else:
        if requester_pays:
            payer = 'Requester' if requester_pays else 'BucketOwner'
            if requester_pays_status != payer:
                put_bucket_request_payment(s3_client, name, payer)
                requester_pays_status = wait_payer_is_applied(module, s3_client, name, payer, should_fail=False)
                if requester_pays_status is None:
                    # We have seen that it happens quite a lot of times that the put request was not taken into
                    # account, so we retry one more time
                    put_bucket_request_payment(s3_client, name, payer)
                    requester_pays_status = wait_payer_is_applied(module, s3_client, name, payer, should_fail=True)
                changed = True

        result['requester_pays'] = requester_pays

    # Policy
    try:
        current_policy = get_bucket_policy(s3_client, name)
    except BotoCoreError as exp:
        module.fail_json_aws(exp, msg="Failed to get bucket policy")
    except ClientError as exp:
        if exp.response['Error']['Code'] != 'NotImplemented' or policy is not None:
            module.fail_json_aws(exp, msg="Failed to get bucket policy")
    else:
        if policy is not None:
            if isinstance(policy, string_types):
                policy = json.loads(policy)

            if not policy and current_policy:
                try:
                    delete_bucket_policy(s3_client, name)
                except (BotoCoreError, ClientError) as e:
                    module.fail_json_aws(e, msg="Failed to delete bucket policy")
                current_policy = wait_policy_is_applied(module, s3_client, name, policy)
                changed = True
            elif compare_policies(current_policy, policy):
                try:
                    put_bucket_policy(s3_client, name, policy)
                except (BotoCoreError, ClientError) as e:
                    module.fail_json_aws(e, msg="Failed to update bucket policy")
                current_policy = wait_policy_is_applied(module, s3_client, name, policy, should_fail=False)
                if current_policy is None:
                    # As for request payement, it happens quite a lot of times that the put request was not taken into
                    # account, so we retry one more time
                    put_bucket_policy(s3_client, name, policy)
                    current_policy = wait_policy_is_applied(module, s3_client, name, policy, should_fail=True)
                changed = True

        result['policy'] = current_policy

    # Tags
    try:
        current_tags_dict = get_current_bucket_tags_dict(s3_client, name)
    except BotoCoreError as exp:
        module.fail_json_aws(exp, msg="Failed to get bucket tags")
    except ClientError as exp:
        if exp.response['Error']['Code'] != 'NotImplemented' or tags is not None:
            module.fail_json_aws(exp, msg="Failed to get bucket tags")
    else:
        if tags is not None:
            # Tags are always returned as text
            tags = dict((to_text(k), to_text(v)) for k, v in tags.items())
            if current_tags_dict != tags:
                if tags:
                    try:
                        put_bucket_tagging(s3_client, name, tags)
                    except (BotoCoreError, ClientError) as e:
                        module.fail_json_aws(e, msg="Failed to update bucket tags")
                else:
                    try:
                        delete_bucket_tagging(s3_client, name)
                    except (BotoCoreError, ClientError) as e:
                        module.fail_json_aws(e, msg="Failed to delete bucket tags")
                current_tags_dict = wait_tags_are_applied(module, s3_client, name, tags)
                changed = True

        result['tags'] = current_tags_dict

    module.exit_json(changed=changed, name=name, **result)


def bucket_exists(s3_client, bucket_name):
    # head_bucket appeared to be really inconsistent, so we use list_buckets instead,
    # and loop over all the buckets, even if we know it's less performant :(
    all_buckets = s3_client.list_buckets(Bucket=bucket_name)['Buckets']
    return any(bucket['Name'] == bucket_name for bucket in all_buckets)


@AWSRetry.exponential_backoff(max_delay=120)
def create_bucket(s3_client, bucket_name, location):
    try:
        configuration = {}
        if location not in ('us-east-1', None):
            configuration['LocationConstraint'] = location
        if len(configuration) > 0:
            s3_client.create_bucket(Bucket=bucket_name, CreateBucketConfiguration=configuration)
        else:
            s3_client.create_bucket(Bucket=bucket_name)
        return True
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'BucketAlreadyOwnedByYou':
            # We should never get there since we check the bucket presence before calling the create_or_update_bucket
            # method. However, the AWS Api sometimes fails to report bucket presence, so we catch this exception
            return False
        else:
            raise e


@AWSRetry.exponential_backoff(max_delay=120, catch_extra_error_codes=['NoSuchBucket'])
def put_bucket_tagging(s3_client, bucket_name, tags):
    s3_client.put_bucket_tagging(Bucket=bucket_name, Tagging={'TagSet': ansible_dict_to_boto3_tag_list(tags)})


@AWSRetry.exponential_backoff(max_delay=120, catch_extra_error_codes=['NoSuchBucket'])
def put_bucket_policy(s3_client, bucket_name, policy):
    s3_client.put_bucket_policy(Bucket=bucket_name, Policy=json.dumps(policy))


@AWSRetry.exponential_backoff(max_delay=120, catch_extra_error_codes=['NoSuchBucket'])
def delete_bucket_policy(s3_client, bucket_name):
    s3_client.delete_bucket_policy(Bucket=bucket_name)


@AWSRetry.exponential_backoff(max_delay=120, catch_extra_error_codes=['NoSuchBucket'])
def get_bucket_policy(s3_client, bucket_name):
    try:
        current_policy = json.loads(s3_client.get_bucket_policy(Bucket=bucket_name).get('Policy'))
    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchBucketPolicy':
            current_policy = None
        else:
            raise e
    return current_policy


@AWSRetry.exponential_backoff(max_delay=120, catch_extra_error_codes=['NoSuchBucket'])
def put_bucket_request_payment(s3_client, bucket_name, payer):
    s3_client.put_bucket_request_payment(Bucket=bucket_name, RequestPaymentConfiguration={'Payer': payer})


@AWSRetry.exponential_backoff(max_delay=120, catch_extra_error_codes=['NoSuchBucket'])
def get_bucket_request_payment(s3_client, bucket_name):
    return s3_client.get_bucket_request_payment(Bucket=bucket_name).get('Payer')


@AWSRetry.exponential_backoff(max_delay=120, catch_extra_error_codes=['NoSuchBucket'])
def get_bucket_versioning(s3_client, bucket_name):
    return s3_client.get_bucket_versioning(Bucket=bucket_name)


@AWSRetry.exponential_backoff(max_delay=120, catch_extra_error_codes=['NoSuchBucket'])
def put_bucket_versioning(s3_client, bucket_name, required_versioning):
    s3_client.put_bucket_versioning(Bucket=bucket_name, VersioningConfiguration={'Status': required_versioning})


@AWSRetry.exponential_backoff(max_delay=120, catch_extra_error_codes=['NoSuchBucket'])
def delete_bucket_tagging(s3_client, bucket_name):
    s3_client.delete_bucket_tagging(Bucket=bucket_name)


@AWSRetry.exponential_backoff(max_delay=120)
def delete_bucket(s3_client, bucket_name):
    try:
        s3_client.delete_bucket(Bucket=bucket_name)
    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchBucket':
            # This means bucket should have been in a deleting state when we checked it existence
            # We just ignore the error
            pass
        else:
            raise e


def wait_policy_is_applied(module, s3_client, bucket_name, expected_policy, should_fail=True):
    for dummy in range(0, 12):
        try:
            current_policy = get_bucket_policy(s3_client, bucket_name)
        except (ClientError, BotoCoreError) as e:
            module.fail_json_aws(e, msg="Failed to get bucket policy")

        if compare_policies(current_policy, expected_policy):
            time.sleep(5)
        else:
            return current_policy
    if should_fail:
        module.fail_json(msg="Bucket policy failed to apply in the expected time")
    else:
        return None


def wait_payer_is_applied(module, s3_client, bucket_name, expected_payer, should_fail=True):
    for dummy in range(0, 12):
        try:
            requester_pays_status = get_bucket_request_payment(s3_client, bucket_name)
        except (BotoCoreError, ClientError) as e:
            module.fail_json_aws(e, msg="Failed to get bucket request payment")
        if requester_pays_status != expected_payer:
            time.sleep(5)
        else:
            return requester_pays_status
    if should_fail:
        module.fail_json(msg="Bucket request payment failed to apply in the expected time")
    else:
        return None


def wait_versioning_is_applied(module, s3_client, bucket_name, required_versioning):
    for dummy in range(0, 24):
        try:
            versioning_status = get_bucket_versioning(s3_client, bucket_name)
        except (BotoCoreError, ClientError) as e:
            module.fail_json_aws(e, msg="Failed to get updated versioning for bucket")
        if versioning_status.get('Status') != required_versioning:
            time.sleep(5)
        else:
            return versioning_status
    module.fail_json(msg="Bucket versioning failed to apply in the expected time")


def wait_tags_are_applied(module, s3_client, bucket_name, expected_tags_dict):
    for dummy in range(0, 12):
        try:
            current_tags_dict = get_current_bucket_tags_dict(s3_client, bucket_name)
        except (ClientError, BotoCoreError) as e:
            module.fail_json_aws(e, msg="Failed to get bucket policy")
        if current_tags_dict != expected_tags_dict:
            time.sleep(5)
        else:
            return current_tags_dict
    module.fail_json(msg="Bucket tags failed to apply in the expected time")


def get_current_bucket_tags_dict(s3_client, bucket_name):
    try:
        current_tags = s3_client.get_bucket_tagging(Bucket=bucket_name).get('TagSet')
    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchTagSet':
            return {}
        raise e

    return boto3_tag_list_to_ansible_dict(current_tags)


def paginated_list(s3_client, **pagination_params):
    pg = s3_client.get_paginator('list_objects_v2')
    for page in pg.paginate(**pagination_params):
        yield [data['Key'] for data in page.get('Contents', [])]


def paginated_versions_list(s3_client, **pagination_params):
    try:
        pg = s3_client.get_paginator('list_object_versions')
        for page in pg.paginate(**pagination_params):
            # We have to merge the Versions and DeleteMarker lists here, as DeleteMarkers can still prevent a bucket deletion
            yield [(data['Key'], data['VersionId']) for data in (page.get('Versions', []) + page.get('DeleteMarkers', []))]
    except is_boto3_error_code('NoSuchBucket'):
        yield []


def destroy_bucket(s3_client, module):

    force = module.params.get("force")
    name = module.params.get("name")
    try:
        bucket_is_present = bucket_exists(s3_client, name)
    except EndpointConnectionError as e:
        module.fail_json_aws(e, msg="Invalid endpoint provided: %s" % to_text(e))
    except (BotoCoreError, ClientError) as e:
        module.fail_json_aws(e, msg="Failed to check bucket presence")

    if not bucket_is_present:
        module.exit_json(changed=False)

    if force:
        # if there are contents then we need to delete them (including versions) before we can delete the bucket
        try:
            for key_version_pairs in paginated_versions_list(s3_client, Bucket=name):
                formatted_keys = [{'Key': key, 'VersionId': version} for key, version in key_version_pairs]
                for fk in formatted_keys:
                    # remove VersionId from cases where they are `None` so that
                    # unversioned objects are deleted using `DeleteObject`
                    # rather than `DeleteObjectVersion`, improving backwards
                    # compatibility with older IAM policies.
                    if not fk.get('VersionId'):
                        fk.pop('VersionId')

                if formatted_keys:
                    resp = s3_client.delete_objects(Bucket=name, Delete={'Objects': formatted_keys})
                    if resp.get('Errors'):
                        module.fail_json(
                            msg='Could not empty bucket before deleting. Could not delete objects: {0}'.format(
                                ', '.join([k['Key'] for k in resp['Errors']])
                            ),
                            errors=resp['Errors'], response=resp
                        )
        except (BotoCoreError, ClientError) as e:
            module.fail_json_aws(e, msg="Failed while deleting bucket")

    try:
        delete_bucket(s3_client, name)
        s3_client.get_waiter('bucket_not_exists').wait(Bucket=name)
    except WaiterError as e:
        module.fail_json_aws(e, msg='An error occurred waiting for the bucket to be deleted.')
    except (BotoCoreError, ClientError) as e:
        module.fail_json_aws(e, msg="Failed to delete bucket")

    module.exit_json(changed=True)


def is_fakes3(s3_url):
    """ Return True if s3_url has scheme fakes3:// """
    if s3_url is not None:
        return urlparse(s3_url).scheme in ('fakes3', 'fakes3s')
    else:
        return False


def get_s3_client(module, aws_connect_kwargs, location, ceph, s3_url):
    if s3_url and ceph:  # TODO - test this
        ceph = urlparse(s3_url)
        params = dict(module=module, conn_type='client', resource='s3', use_ssl=ceph.scheme == 'https', region=location, endpoint=s3_url, **aws_connect_kwargs)
    elif is_fakes3(s3_url):
        fakes3 = urlparse(s3_url)
        port = fakes3.port
        if fakes3.scheme == 'fakes3s':
            protocol = "https"
            if port is None:
                port = 443
        else:
            protocol = "http"
            if port is None:
                port = 80
        params = dict(module=module, conn_type='client', resource='s3', region=location,
                      endpoint="%s://%s:%s" % (protocol, fakes3.hostname, to_text(port)),
                      use_ssl=fakes3.scheme == 'fakes3s', **aws_connect_kwargs)
    else:
        params = dict(module=module, conn_type='client', resource='s3', region=location, endpoint=s3_url, **aws_connect_kwargs)
    return boto3_conn(**params)


def main():

    argument_spec = ec2_argument_spec()
    argument_spec.update(
        dict(
            force=dict(required=False, default='no', type='bool'),
            policy=dict(required=False, default=None, type='json'),
            name=dict(required=True, type='str'),
            requester_pays=dict(default=False, type='bool'),
            s3_url=dict(aliases=['S3_URL'], type='str'),
            state=dict(default='present', type='str', choices=['present', 'absent']),
            tags=dict(required=False, default=None, type='dict'),
            versioning=dict(default=None, type='bool'),
            ceph=dict(default='no', type='bool')
        )
    )

    module = AnsibleAWSModule(argument_spec=argument_spec)

    region, ec2_url, aws_connect_kwargs = get_aws_connection_info(module, boto3=True)

    if region in ('us-east-1', '', None):
        # default to US Standard region
        location = 'us-east-1'
    else:
        # Boto uses symbolic names for locations but region strings will
        # actually work fine for everything except us-east-1 (US Standard)
        location = region

    s3_url = module.params.get('s3_url')
    ceph = module.params.get('ceph')

    # allow eucarc environment variables to be used if ansible vars aren't set
    if not s3_url and 'S3_URL' in os.environ:
        s3_url = os.environ['S3_URL']

    if ceph and not s3_url:
        module.fail_json(msg='ceph flavour requires s3_url')

    # Look at s3_url and tweak connection settings
    # if connecting to Ceph RGW, Walrus or fakes3
    if s3_url:
        for key in ['validate_certs', 'security_token', 'profile_name']:
            aws_connect_kwargs.pop(key, None)
    s3_client = get_s3_client(module, aws_connect_kwargs, location, ceph, s3_url)

    if s3_client is None:  # this should never happen
        module.fail_json(msg='Unknown error, failed to create s3 connection, no information from boto.')

    state = module.params.get("state")

    if state == 'present':
        create_or_update_bucket(s3_client, module, location)
    elif state == 'absent':
        destroy_bucket(s3_client, module)


if __name__ == '__main__':
    main()
