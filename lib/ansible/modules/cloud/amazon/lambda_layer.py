#!/usr/bin/python
# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: lambda_layer
short_description: Manage AWS Lambda layers
description:
  - Allows for the management of Lambda layers.
version_added: '2.10'
requirements: [ boto3 ]
options:
  name:
    description:
      - The name you want to assign to the layer you are publishing.
    required: true
    type: str
  state:
    description:
      - Create or delete Lambda layer.
    default: present
    choices: [ 'present', 'absent' ]
    type: str
  runtime:
    description:
      - The runtime environment for the Lambda layer you are publishing.
      - Required when creating a layer. Uses parameters as described in boto3 docs.
      - Required when I(state=present).
      - For supported list of runtimes, see U(https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtimes.html).
    type: str
  zip_file:
    description:
      - A .zip file containing your deployment package.
      - If I(state=present) then either I(zip_file) or I(s3_bucket) must be present.
    aliases: [ 'src' ]
    type: str
  s3_bucket:
    description:
      - Amazon S3 bucket name where the .zip file containing your deployment package is stored.
      - If I(state=present) then either I(zip_file) or I(s3_bucket) must be present.
      - I(s3_bucket) and I(s3_key) are required together.
    type: str
  s3_key:
    description:
      - The Amazon S3 object (the deployment package) key name you want to upload.
      - I(s3_bucket) and I(s3_key) are required together.
    type: str
  s3_object_version:
    description:
      - The Amazon S3 object (the deployment package) version you want to upload.
    type: str
  description:
    description:
      - A short, user-defined layer description.
    type: str
  version:
    description:
      - Used with I(state=absent) to remove specific version of the layer.
      - Can be a specific numeric version or one of relative keywords: oldest, latest.
      - If version is not provided, all of the layer versions will be removed.
    type: str
author:
  - Andrej Svenke (@anryko)
extends_documentation_fragment:
  - aws
  - ec2
'''

EXAMPLES = '''
- name: publish layer from zip
  lambda_layer:
    name: test_layer
    state: present
    zip_file: /home/user/layer.zip
    runtimes:
    - python3.7
    - python3.8

- name: publish layer from s3
  lambda_layer:
    name: test_layer
    state: present
    s3_bucket: bucket-name
    s3_key: /path/to/layer.zip
    runtimes:
    - python3.7
    - python3.8

- name: delete some layer vestions
  lambda_layer:
    name: test_layer
    state: absent
    version: "{{ item }}"
  loop:
  - oldest
  - 3
  - 4
  - latest

- name: delete all layer vestions
  lambda_layer:
    name: test_layer
    state: absent
'''

RETURN = '''
changed:
  description: Whether the state of the lambda layed has changed.
  returned: always
  type: bool
  sample: false
layer_arn:
  description: ARN of the lambda layer.
  returned: when lambda layer present
  type: str
  sample: arn:aws:lambda:us-east-1:111111111111:layer:test_layer
layer_version_arn:
  description: ARN of the lambda layer with version.
  returned: when lambda layer present
  type: str
  sample: arn:aws:lambda:us-east-1:111111111111:layer:test_layer:19
version:
  description: Lambda layer version.
  returned: when lambda layer present
  type: int
  sample: 19
compatible_runtimes:
  description: Lambda layer compatible runtimes.
  returned: when lambda layer present
  type: list
  sample: ["python3.7", "python3.8"]
content:
  description: Lambda layer content metadata.
  returned: when lambda layer present
  type: dict
  sample: {
      "code_sha256": "7yu+6dHtpmbNzIehSzUQb7QvWzEQoYHtPcIXoGve3bg=",
      "code_size": 42222
    }
created_date:
  description: The creation date and time of the lambda layer.
  returned: when lambda layer present
  type: str
  sample: 2020-01-15T12:09:03.602+0000
description:
  description: Description of lambda layer provided on publishing.
  returned: when lambda layer present
  type: str
  sample: test layer
'''

import base64
import hashlib
import traceback
from functools import partial

from ansible.module_utils.aws.core import AnsibleAWSModule
from ansible.module_utils.ec2 import (
    AWSRetry,
    camel_dict_to_snake_dict,
)

try:
    import boto3
    from botocore.exceptions import (
        ClientError,
        ParamValidationError,
        ValidationError,
    )
except ImportError:
    pass  # protected by AnsibleAWSModule


class LambdaLayer:
    def __init__(
        self,
        name,
        runtimes=None,
        description=None,
        license_info=None,
        client=None,
    ):
        self.name = name
        self.runtimes = runtimes
        self.description = description
        self.license_info = license_info
        self.client = client or boto3.client('lambda')

    @property
    def versions(self):
        """
        Get a list of all the version numbers.
        """
        return list(self.fetch_versions())

    def fetch_versions(self, max_items=None, marker=None):
        """
        Get generator of published version numbers.
        """
        opts = {'LayerName': self.name}

        if max_items:
            opts['MaxItems'] = max_items

        if marker:
            opts['Marker'] = marker

        response = self.client.list_layer_versions(**opts)
        versions = response['LayerVersions']
        next_marker = response.get('NextMarker')

        for version in versions:
            yield version['Version']

        if next_marker:
            for version in self.fetch_versions(marker=next_marker):
                yield version

    @property
    def version(self):
        """
        Get latest version number.
        """
        return next(self.fetch_versions(max_items=1), None)

    def _resolve_version(self, version):
        """
        Get version number or None if version is not valid.
        """
        if not version:
            return None

        if version == 'latest':
            return self.version

        all_versions = self.versions
        if not all_versions:
            return None

        if version == 'oldest':
            return all_versions[-1]

        if version not in all_versions:
            return None

        return version

    @staticmethod
    def _format(response):
        """
        Cleanup the output.
        """
        if 'Content' in response:
            response['Content'].pop('ZipFile', None)
            response['Content'].pop('Location', None)

        return response

    def fetch_layer(self, version):
        """
        Get layer configuration by version.
        """
        version_number = self._resolve_version(version)
        if not version_number:
            return {}

        return self._format(
            self.client.get_layer_version(
                LayerName=self.name,
                VersionNumber=version_number
            )
        )

    @property
    def latest(self):
        """
        Get latest layer configuration.
        """
        return self.fetch_layer('latest')

    def _publish(self, opts, dry_run=False):
        """
        Wrapper for boto3 publish_layer_version to handle dry_run and format output.
        """
        response = (
            self.client.publish_layer_version(**opts)
            if not dry_run
            else self.latest
        )

        result = {'changed': True}
        result.update(self._format(response))

        if dry_run:
            result.update(self._format(opts))

        return result

    def publish_zip(self, path, dry_run=False):
        """
        Publish a new lambda layer from a zip file on local file system.
        """
        with open(path, 'rb') as f:
            encoded_zip = f.read()

        latest_layer = self.latest

        if latest_layer:
            hasher = hashlib.sha256()
            hasher.update(encoded_zip)
            zip_sha256 = base64.b64encode(hasher.digest()).decode('utf-8')

            if (
                latest_layer['Content']['CodeSha256'] == zip_sha256
                and latest_layer['CompatibleRuntimes'] == self.runtimes
            ):
                result = {'changed': False}
                result.update(latest_layer)
                return result

        opts = {
            'LayerName': self.name,
            'Content': {}
        }

        if self.runtimes:
            opts['CompatibleRuntimes'] = self.runtimes
        if self.license_info:
            opts['LicenseInfo'] = self.license_info
        if self.description:
            opts['Description'] = self.description

        opts['Content']['ZipFile'] = encoded_zip

        return self._publish(opts, dry_run)

    def publish_s3(self, bucket, key, version=None, dry_run=False):
        """
        Publish a new lambda layer from S3.
        """
        # If layer zip is stored in S3 always update.
        opts = {
            'LayerName': self.name,
            'Content': {
                'S3Bucket': bucket,
                'S3Key': key
            }
        }

        if version:
            opts['Content']['S3ObjectVersion'] = version
        if self.runtimes:
            opts['CompatibleRuntimes'] = self.runtimes
        if self.license_info:
            opts['LicenseInfo'] = self.license_info
        if self.description:
            opts['Description'] = self.description

        return self._publish(opts, dry_run)

    def delete(self, version=None, dry_run=False):
        """
        Delete layer version or all of the versions if version is None.
        """
        all_versions = self.versions

        if not all_versions:
            return {'changed': False}

        if version:
            version_number = self._resolve_version(version)
            if not version_number:
                return {'changed': False}

            versions_delete = [version_number]
            result = self.fetch_layer(version_number)
        else:
            versions_delete = all_versions
            # When deleting all layer versions return only latest config.
            result = self.latest

        if not dry_run:
            for number in versions_delete:
                self.client.delete_layer_version(
                    LayerName=self.name,
                    VersionNumber=number
                )

        result.update({'changed': True})
        return result


def main():
    argument_spec = dict(
        name=dict(required=True),
        state=dict(default='present', choices=['present', 'absent']),
        runtimes=dict(type='list'),
        zip_file=dict(aliases=['src']),
        s3_bucket=dict(),
        s3_key=dict(),
        s3_object_version=dict(),
        description=dict(),
        license_info=dict(),
        version=dict(),
    )

    mutually_exclusive = [
        ['zip_file', 's3_key'],
        ['zip_file', 's3_bucket'],
        ['zip_file', 's3_object_version'],
    ]

    required_together = [
        ['s3_key', 's3_bucket'],
    ]

    required_if = [
        ['state', 'present', ['runtimes']],
    ]

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        mutually_exclusive=mutually_exclusive,
        required_together=required_together,
        required_if=required_if,
    )

    name = module.params.get('name')
    state = module.params.get('state').lower()
    runtimes = module.params.get('runtimes')
    s3_bucket = module.params.get('s3_bucket')
    s3_key = module.params.get('s3_key')
    s3_object_version = module.params.get('s3_object_version')
    zip_file = module.params.get('zip_file')
    description = module.params.get('description')
    license_info = module.params.get('license_info')
    version = module.params.get('version')

    check_mode = module.check_mode

    client = module.client('lambda', retry_decorator=AWSRetry.jittered_backoff())
    for method in (
        'list_layer_versions',
        'get_layer_version',
        'publish_layer_version',
        'delete_layer_version',
    ):
        if hasattr(client, method):
            setattr(client, method, partial(getattr(client, method), aws_retry=True))

    layer = LambdaLayer(
        name,
        runtimes,
        description,
        license_info,
        client,
    )

    result = {'changed': False}

    try:
        if state == 'present':
            if zip_file:
                try:
                    result.update(
                        layer.publish_zip(zip_file, dry_run=check_mode)
                    )
                except IOError as e:
                    module.fail_json(msg=str(e), exception=traceback.format_exc())

            elif s3_bucket:
                result.update(
                    layer.publish_s3(s3_bucket, s3_key, s3_object_version, dry_run=check_mode)
                )

        if state == 'absent':
            result.update(
                layer.delete(version, dry_run=check_mode)
            )

    except (ParamValidationError, ClientError) as e:
        module.fail_json_aws(e, msg='Managing lambda layer')

    module.exit_json(**camel_dict_to_snake_dict(result))


if __name__ == '__main__':
    main()
