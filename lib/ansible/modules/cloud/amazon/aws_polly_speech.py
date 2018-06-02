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
module: aws_polly_speech
short_description: Synthesize speech using AWS Polly.
description:
    - Synthesizes UTF-8 input, plain text or SSML, to a stream of bytes. SSML input must be valid, well-formed SSML.
author: "Aaron Smith (@slapula)"
version_added: "2.7"
requirements: [ 'botocore', 'boto3' ]
options:
  lexicons:
    description:
    - List of one or more pronunciation lexicon names you want the service to apply during synthesis.
  output_format:
    description:
    - The format in which the returned output will be encoded.
    choices: ['json', 'mp3', 'ogg_vorbis', 'pcm']
    required: true
  sample_rate:
    description:
    - The audio frequency specified in Hz.
    default: '16000'
  speech_mark_types:
    description:
    - The type of speech marks returned for the input text.
    choices: ['sentence', 'ssml', 'viseme', 'word']
  text_type:
    description:
    - Specifies whether the input text is plain text or SSML.
    choices: ['ssml', 'text']
    default: 'text'
  voice_id:
    description:
    - Voice ID to use for the synthesis.
    choices: ['Geraint', 'Gwyneth', 'Mads', 'Naja', 'Hans', 'Marlene', 'Nicole', 'Russell', 'Amy', 'Brian', 'Emma', 'Raveena', 'Ivy', 'Joanna',
        'Joey', 'Justin', 'Kendra', 'Kimberly', 'Matthew', 'Salli', 'Conchita', 'Enrique', 'Miguel', 'Penelope', 'Chantal', 'Celine', 'Mathieu',
        'Dora', 'Karl', 'Carla', 'Giorgio', 'Mizuki', 'Liv', 'Lotte', 'Ruben', 'Ewa', 'Jacek', 'Jan', 'Maja', 'Ricardo', 'Vitoria', 'Cristiano',
        'Ines', 'Carmen', 'Maxim', 'Tatyana', 'Astrid', 'Filiz', 'Vicki', 'Takumi', 'Seoyeon', 'Aditi']
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
- name: synthesize provided text into an audio stream
  aws_polly_speech:
    output_format: 'mp3'
    voice_id: 'Brian'
    source: 'local'
    src_path: "{{ lookup('file', 'tmp/migration_instructions.txt') }}"
    destination: 'local'
    dst_path: 'migration_instructions.mp3'
'''


RETURN = r'''#'''

from contextlib import closing

from ansible.module_utils.aws.core import AnsibleAWSModule

try:
    from botocore.exceptions import BotoCoreError, ClientError
except ImportError:
    pass  # handled by AnsibleAWSModule


def create_synthesis(client, s3_client, module, params):
    if module.check_mode:
        module.exit_json(changed=True)
    try:
        response = client.synthesize_speech(**params)
        if module.params.get('destination') == 'local':
            f = open(module.params.get('dst_path'), 'wb')
            with closing(response['AudioStream']) as stream:
                while True:
                    data = stream.read()
                    f.write(b"%X\r\n%s\r\n" % (len(data), data))
                    if not data:
                        break
                f.flush()
        if module.params.get('destination') == 's3':
            s3_client.upload_fileobj(
                response['AudioStream'],
                module.params.get('dst_bucket'),
                module.params.get('dst_path')
            )
    except (BotoCoreError, ClientError) as e:
        module.fail_json_aws(e, msg="Failed to synthesize text into audio file")


def main():
    requirements = [
        ('source', 'local', ['src_path']),
        ('source', 's3', ['src_bucket', 'src_path']),
        ('destination', 'local', ['dst_path']),
        ('destination', 's3', ['dst_bucket', 'dst_path'])
    ]

    module = AnsibleAWSModule(
        argument_spec={
            'lexicons': dict(type='list'),
            'output_format': dict(type='str', choices=['json', 'mp3', 'ogg_vorbis', 'pcm'], required=True),
            'sample_rate': dict(type='str', default='16000'),
            'speech_mark_types': dict(type='list', choices=['sentence', 'ssml', 'viseme', 'word']),
            'text_type': dict(type='str', choices=['ssml', 'text'], default='text'),
            'voice_id': dict(
                type='str',
                choices=[
                    'Geraint', 'Gwyneth', 'Mads', 'Naja', 'Hans', 'Marlene', 'Nicole', 'Russell', 'Amy', 'Brian',
                    'Emma', 'Raveena', 'Ivy', 'Joanna', 'Joey', 'Justin', 'Kendra', 'Kimberly', 'Matthew', 'Salli', 'Conchita',
                    'Enrique', 'Miguel', 'Penelope', 'Chantal', 'Celine', 'Mathieu', 'Dora', 'Karl', 'Carla', 'Giorgio',
                    'Mizuki', 'Liv', 'Lotte', 'Ruben', 'Ewa', 'Jacek', 'Jan', 'Maja', 'Ricardo', 'Vitoria', 'Cristiano',
                    'Ines', 'Carmen', 'Maxim', 'Tatyana', 'Astrid', 'Filiz', 'Vicki', 'Takumi', 'Seoyeon', 'Aditi'
                ],
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

    client = module.client('polly')
    s3_client = module.client('s3')

    params = {}
    if module.params.get('lexicons'):
        params['LexiconNames'] = module.params.get('lexicons')
    params['OutputFormat'] = module.params.get('output_format')
    if module.params.get('sample_rate'):
        params['SampleRate'] = module.params.get('sample_rate')
    if module.params.get('speech_mark_types'):
        params['SpeechMarkTypes'] = module.params.get('speech_mark_types')
    if module.params.get('text_type'):
        params['TextType'] = module.params.get('text_type')
    params['VoiceId'] = module.params.get('voice_id')

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

    create_synthesis(client, s3_client, module, params)

    module.exit_json(changed=True)


if __name__ == '__main__':
    main()
