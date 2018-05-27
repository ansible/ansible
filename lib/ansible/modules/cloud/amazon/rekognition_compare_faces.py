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
module: rekognition_compare_faces
short_description: Retrieve facial recognition results using the AWS Rekognition service.
description:
    - Compares a face in the source input image with each of the 100 largest faces detected in the target input image.
    - This action is stateless.  The data resulting from this operation does not persist.
    - Successful matches will return a `changed` state to Ansible.
    - Ansible does not currently support looking up binary files.  Comparisons are done against files hosted on S3.
author: "Aaron Smith (@slapula)"
version_added: "2.7"
requirements: [ 'botocore', 'boto3' ]
options:
  source_image:
    description:
    - The input image as an S3 object.
    required: true
    suboptions:
      s3_object:
        description:
        - Identifies an S3 object as the image source.
        suboptions:
          bucket:
            description:
            - Name of the S3 bucket.
            required: true
          name:
            description:
            - S3 object key name.
            required: true
          version:
            description:
            - If the bucket is versioning enabled, you can specify the object version.
  target_image:
    description:
    - The target image as an S3 object.
    required: true
    suboptions:
      s3_object:
        description:
        - Identifies an S3 object as the image source.
        suboptions:
          bucket:
            description:
            - Name of the S3 bucket.
            required: true
          name:
            description:
            - S3 object key name.
            required: true
          version:
            description:
            - If the bucket is versioning enabled, you can specify the object version.
  similarity_threshold:
    description:
    - The minimum level of confidence in the face matches that a match must meet to be included in the FaceMatches array.
extends_documentation_fragment:
    - ec2
    - aws
'''


EXAMPLES = r'''
- name: Compare source file to target file
  rekognition_compare_faces:
    source_image:
        s3_object:
            bucket: 'fake-image-repository'
            name: 'me.jpeg'
    target_image:
        s3_object:
            bucket: 'fake-image-repository'
            name: 'crowd.jpeg'
    similarity_threshold: 95.0
'''


RETURN = r'''
source_image_face:
  description: The face in the source image that was used for comparison.
  returned: always
  type: complex
  contains:
    bounding_box:
      description: Bounding box of the face.
      returned: always
      type: complex
      contains:
        width:
          description: Width of the bounding box as a ratio of the overall image width.
          returned: always
          type: float
        height:
          description: Height of the bounding box as a ratio of the overall image height.
          returned: always
          type: float
        left:
          description: Left coordinate of the bounding box as a ratio of overall image width.
          returned: always
          type: float
        top:
          description: Top coordinate of the bounding box as a ratio of overall image height.
          returned: always
          type: float
    confidence:
      description: Confidence level that the selected bounding box contains a face.
      returned: always
      type: float
face_matches:
  description:
    - An array of faces in the target image that match the source image face.
    - Each CompareFacesMatch object provides the bounding box, the confidence level that the bounding box contains a face,
      and the similarity score for the face in the bounding box and the face in the source image.
  returned: always
  type: complex
  contains:
    similarity:
      description: Level of confidence that the faces match.
      returned: always
      type: float
    face:
      description: Provides face metadata (bounding box and confidence that the bounding box actually contains a face).
      returned: always
      type: complex
      contains:
        bounding_box:
          description: Bounding box of the face.
          returned: always
          type: complex
          contains:
            width:
              description: Width of the bounding box as a ratio of the overall image width.
              returned: always
              type: float
            height:
              description: Height of the bounding box as a ratio of the overall image height.
              returned: always
              type: float
            left:
              description: Left coordinate of the bounding box as a ratio of overall image width.
              returned: always
              type: float
            top:
              description: Top coordinate of the bounding box as a ratio of overall image height.
              returned: always
              type: float
        confidence:
          description: Confidence level that the selected bounding box contains a face.
          returned: always
          type: float
        landmarks:
          description: An array of facial landmarks.
          returned: always
          type: complex
          contains:
            type:
              description: Type of the landmark.
              returned: always
              type: string
            x:
              description: x-coordinate from the top left of the landmark expressed as the ratio of the width of the image.
              returned: always
              type: float
            y:
              description: y-coordinate from the top left of the landmark expressed as the ratio of the height of the image.
              returned: always
              type: float
        pose:
          description: Indicates the pose of the face as determined by its pitch, roll, and yaw.
          returned: always
          type: complex
          contains:
            roll:
              description: Value representing the face rotation on the roll axis.
              returned: always
              type: float
            yaw:
              description: Value representing the face rotation on the yaw axis.
              returned: always
              type: float
            pitch:
              description: Value representing the face rotation on the pitch axis.
              returned: always
              type: float
        quality:
          description: Identifies face image brightness and sharpness.
          returned: always
          type: complex
          contains:
            brightness:
              description:
                - Value representing brightness of the face.
                - The service returns a value between 0 and 100 (inclusive).
                - A higher value indicates a brighter face image.
              returned: always
              type: float
            sharpness:
              description:
                - Value representing sharpness of the face.
                - The service returns a value between 0 and 100 (inclusive).
                - A higher value indicates a sharper face image.
              returned: always
              type: float
unmatched_faces:
  description: An array of faces in the target image that did not match the source image face.
  returned: always
  type: complex
  contains:
    bounding_box:
      description: Bounding box of the face.
      returned: always
      type: complex
      contains:
        width:
          description: Width of the bounding box as a ratio of the overall image width.
          returned: always
          type: float
        height:
          description: Height of the bounding box as a ratio of the overall image height.
          returned: always
          type: float
        left:
          description: Left coordinate of the bounding box as a ratio of overall image width.
          returned: always
          type: float
        top:
          description: Top coordinate of the bounding box as a ratio of overall image height.
          returned: always
          type: float
    confidence:
      description: Confidence level that the selected bounding box contains a face.
      returned: always
      type: float
    landmarks:
      description: An array of facial landmarks.
      returned: always
      type: complex
      contains:
        type:
          description: Type of the landmark.
          returned: always
          type: string
        x:
          description: x-coordinate from the top left of the landmark expressed as the ratio of the width of the image.
          returned: always
          type: float
        y:
          description: y-coordinate from the top left of the landmark expressed as the ratio of the height of the image.
          returned: always
          type: float
    pose:
      description: Indicates the pose of the face as determined by its pitch, roll, and yaw.
      returned: always
      type: complex
      contains:
        roll:
          description: Value representing the face rotation on the roll axis.
          returned: always
          type: float
        yaw:
          description: Value representing the face rotation on the yaw axis.
          returned: always
          type: float
        pitch:
          description: Value representing the face rotation on the pitch axis.
          returned: always
          type: float
    quality:
      description: Identifies face image brightness and sharpness.
      returned: always
      type: complex
      contains:
        brightness:
          description:
            - Value representing brightness of the face.
            - The service returns a value between 0 and 100 (inclusive).
            - A higher value indicates a brighter face image.
          returned: always
          type: float
        sharpness:
          description:
            - Value representing sharpness of the face.
            - The service returns a value between 0 and 100 (inclusive).
            - A higher value indicates a sharper face image.
          returned: always
          type: float
'''

import locale
from io import BytesIO

from ansible.module_utils.aws.core import AnsibleAWSModule
from ansible.module_utils.ec2 import boto3_conn, get_aws_connection_info, AWSRetry
from ansible.module_utils.ec2 import camel_dict_to_snake_dict, boto3_tag_list_to_ansible_dict

try:
    from botocore.exceptions import BotoCoreError, ClientError
except ImportError:
    pass  # handled by AnsibleAWSModule


def compare_images(client, module, params, result):
    if module.check_mode:
        module.exit_json(changed=True)
    try:
        response = client.compare_faces(**params)
        result['source_image_face'] = camel_dict_to_snake_dict(response['SourceImageFace'])
        result['face_matches'] = [camel_dict_to_snake_dict(i) for i in response['FaceMatches']]
        result['unmatched_faces'] = [camel_dict_to_snake_dict(i) for i in response['UnmatchedFaces']]
        return result
    except (BotoCoreError, ClientError) as e:
        module.fail_json_aws(e, msg="Failed to compare images for facial recognition analysis")

    return result


def main():
    module = AnsibleAWSModule(
        argument_spec={
            'source_image': dict(type='dict', required=True),
            'target_image': dict(type='dict', required=True),
            'similarity_threshold': dict(type='float'),
        },
        supports_check_mode=True,
    )

    result = {
        'changed': False
    }

    source_s3 = {}
    source_s3['S3Object'] = {}
    source_s3['S3Object'].update({
        'Bucket': module.params.get('source_image').get('s3_object').get('bucket')
    })
    source_s3['S3Object'].update({
        'Name': module.params.get('source_image').get('s3_object').get('name')
    })
    if module.params.get('source_image').get('s3_object').get('version'):
        source_s3['S3Object'].update({
            'Version': module.params.get('source_image').get('s3_object').get('version')
        })

    target_s3 = {}
    target_s3['S3Object'] = {}
    target_s3['S3Object'].update({
        'Bucket': module.params.get('target_image').get('s3_object').get('bucket')
    })
    target_s3['S3Object'].update({
        'Name': module.params.get('target_image').get('s3_object').get('name')
    })
    if module.params.get('target_image').get('s3_object').get('version'):
        target_s3['S3Object'].update({
            'Version': module.params.get('target_image').get('s3_object').get('version')
        })

    params = {}
    params['SourceImage'] = {}
    params['SourceImage'].update(source_s3)
    params['TargetImage'] = {}
    params['TargetImage'].update(target_s3)
    if module.params.get('similarity_threshold'):
        params['SimilarityThreshold'] = module.params.get('similarity_threshold')

    client = module.client('rekognition')

    compare_images(client, module, params, result)

    if result['face_matches']:
        result['changed'] = True

    module.exit_json(
        changed=result['changed'],
        source_image_face=result['source_image_face'],
        face_matches=result['face_matches'],
        unmatched_faces=result['unmatched_faces']
    )


if __name__ == '__main__':
    main()
