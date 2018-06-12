#!/usr/bin/python

# Copyright: (c) 2018, Aaron Smith <ajsmith10381@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = r'''
---
module: aws_translate_text
short_description: Translate text using AWS Translate.
description:
    - Translate text from local storage or S3 using AWS Translate service.
author: "Aaron Smith (@slapula)"
version_added: "2.7"
requirements: [ 'botocore', 'boto3' ]
options:
  source_lang:
    description:
    - One of the supported language codes for the target text.
    - If the `target_language` is not "en", the `source_language` must be "en".
    choices: ['ar', 'zh', 'fr', 'de', 'pt', 'es', 'en']
    required: true
  target_lang:
    description:
    - One of the supported language codes for the target text.
    - If the `sourc_language` is not "en", the `target_language` must be "en".
    choices: ['ar', 'zh', 'fr', 'de', 'pt', 'es', 'en']
    required: true
  source:
    description:
    - Input text to synthesize.
    - Specifies where to get the text file needed for processing.
    - If you specify ssml as the `text_type`, follow the SSML format for the input text.
    choices: ['local', 's3']
    required: true
  src_bucket:
    description:
    - Specifies the S3 bucket that stores the text file.
  src_path:
    description:
    - Specifies the local path or S3 key path where the text file resides.
  destination:
    description:
    - Specifies where to save the resulting audio file.
    choices: ['local', 's3']
    required: true
  dst_bucket:
    description:
    - Specifies the S3 bucket where the resulting audio file will reside.
  dst_path:
    description:
    - Specifies the local path or S3 key path for where the resulting audio file.
extends_documentation_fragment:
    - ec2
    - aws
'''


EXAMPLES = r'''
- name: translate provided text from English to French
  aws_translate_text:
    source_lang: 'en'
    target_lang: 'fr'
    source: 'local'
    src_path: "{{ lookup('file', 'tmp/migration_instructions.txt') }}"
    destination: 'local'
    dst_path: 'migration_instructions_fr.txt'
'''


RETURN = r'''#'''

import os
from tempfile import NamedTemporaryFile

from ansible.module_utils.aws.core import AnsibleAWSModule

try:
    from botocore.exceptions import BotoCoreError, ClientError
except ImportError:
    pass  # handled by AnsibleAWSModule


def create_translation(client, s3_client, module, params):
    if module.check_mode:
        module.exit_json(changed=True)
    try:
        response = client.translate_text(**params)
        if module.params.get('destination') == 'local':
            f = open(module.params.get('dst_path'), 'w')
            f.write(response['TranslatedText'])
            f.close()
        if module.params.get('destination') == 's3':
            f = NamedTemporaryFile(mode='w+', delete=False)
            f.write(response['TranslatedText'])
            s3_client.upload_fileobj(
                f,
                module.params.get('dst_bucket'),
                module.params.get('dst_path')
            )
            f.close()
            os.unlink(f.name)
    except (BotoCoreError, ClientError) as e:
        module.fail_json_aws(e, msg="Failed to translate text")


def main():
    requirements = [
        ('source', 'local', ['src_path']),
        ('source', 's3', ['src_bucket', 'src_path']),
        ('destination', 'local', ['dst_path']),
        ('destination', 's3', ['dst_bucket', 'dst_path'])
    ]

    module = AnsibleAWSModule(
        argument_spec={
            'source_lang': dict(
                type='str',
                choices=['ar', 'zh', 'fr', 'de', 'pt', 'es', 'en'],
                required=True
            ),
            'target_lang': dict(
                type='str',
                choices=['ar', 'zh', 'fr', 'de', 'pt', 'es', 'en'],
                required=True
            ),
            'source': dict(type='str', choices=['local', 's3'], required=True),
            'src_bucket': dict(type='str'),
            'src_path': dict(type='str'),
            'destination': dict(type='str', choices=['local', 's3'], required=True),
            'dst_bucket': dict(type='str'),
            'dst_path': dict(type='str')
        },
        supports_check_mode=True,
        required_if=requirements,
    )

    client = module.client('translate')
    s3_client = module.client('s3')

    params = {}
    params['SourceLanguageCode'] = module.params.get('source_lang')
    params['TargetLanguageCode'] = module.params.get('target_lang')

    if module.params.get('source') == 'local':
        params['Text'] = module.params.get('src_path')
    if module.params.get('source') == 's3':
        try:
            response = s3_client.get_object(
                Bucket=module.params.get('src_bucket'),
                Key=module.params.get('src_path')
            )
            params['Text'] = response['Body'].read().decode("utf-8")
        except (BotoCoreError, ClientError) as e:
            module.fail_json_aws(e, msg="Failed to get text file from S3")

    create_translation(client, s3_client, module, params)

    module.exit_json(changed=True)


if __name__ == '__main__':
    main()
