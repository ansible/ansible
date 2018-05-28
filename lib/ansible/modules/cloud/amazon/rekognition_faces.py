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
module: rekognition_faces
short_description: Index face data using the AWS Rekognition service.
description:
    - Detects faces in the input image and adds them to the specified collection.
    - Faces are not actually stored on AWS as a result of actions taken by this module.
    - Only data gathered from detected faces persist on Rekognition's backend.
    - Ansible does not currently support looking up binary files.  Indexing is done against files hosted on S3.
author: "Aaron Smith (@slapula)"
version_added: "2.7"
requirements: [ 'botocore', 'boto3' ]
options:
  index_id:
    description:
    - ID you want to assign to all the faces detected in the image.
    required: true
  state:
    description:
    - Whether the face index should be exist or not.
    choices: ['present', 'absent']
    default: 'present'
  collection:
    description:
    - The ID of an existing collection to which you want to add the faces that are detected in the input images.
    required: true
  image:
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
  detection_attributes:
    description:
    - An array of facial attributes that you want to be returned
    choices: ['DEFAULT', 'ALL']
    default: 'DEFAULT'
extends_documentation_fragment:
    - ec2
    - aws
'''


EXAMPLES = r'''
- name: Index source image and assign detected faces to a collection
  rekognition_faces:
    index_id: 'crowd1'
    state: present
    collection: 'myfaces'
    source_image:
      s3_object:
        bucket: 'fake-image-repository'
        name: 'crowd.jpeg'
'''


RETURN = r'''
face_records:
  description: An array of faces detected and added to the collection.
  returned: always
  type: complex
  contains:
    face:
      description:
        - Describes the face properties such as the bounding box, face ID, image ID of the input image,
          and external image ID that you assigned.
      returned: always
      type: complex
      contains:
        face_id:
          description: Unique identifier that Amazon Rekognition assigns to the face.
          returned: always
          type: string
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
        image_id:
          description: Unique identifier that Amazon Rekognition assigns to the input image.
          returned: always
          type: string
        external_image_id:
          description: Identifier that you assign to all the faces in the input image.
          returned: always
          type: string
        confidence:
          description: Confidence level that the bounding box contains a face.
          returned: always
          type: string
    face_detail:
      description: Structure containing attributes of the face that the algorithm detected.
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
        age_range:
          description: The estimated age range, in years, for the face.
          returned: always
          type: complex
          contains:
            low:
              description: The lowest estimated age.
              returned: always
              type: integer
            high:
              description: The highest estimated age.
              returned: always
              type: integer
        smile:
          description: Indicates whether or not the face is smiling, and the confidence level in the determination.
          returned: always
          type: complex
          contains:
            value:
              description: Boolean value that indicates whether the face is smiling or not.
              returned: always
              type: boolean
            confidence:
              description: Level of confidence in the determination.
              returned: always
              type: float
        eyeglasses:
          description: Indicates whether or not the face is wearing eye glasses, and the confidence level in the determination.
          returned: always
          type: complex
          contains:
            value:
              description: Boolean value that indicates whether the face is wearing eye glasses or not.
              returned: always
              type: boolean
            confidence:
              description: Level of confidence in the determination.
              returned: always
              type: float
        sunglasses:
          description: Indicates whether or not the face is wearing sunglasses, and the confidence level in the determination.
          returned: always
          type: complex
          contains:
            value:
              description: Boolean value that indicates whether the face is wearing sunglasses or not.
              returned: always
              type: boolean
            confidence:
              description: Level of confidence in the determination.
              returned: always
              type: float
        gender:
          description: Gender of the face and the confidence level in the determination.
          returned: always
          type: complex
          contains:
            value:
              description: Gender of the face.
              returned: always
              type: string
            confidence:
              description: Level of confidence in the determination.
              returned: always
              type: float
        beard:
          description: Indicates whether or not the face has a beard, and the confidence level in the determination.
          returned: always
          type: complex
          contains:
            value:
              description: Boolean value that indicates whether the face has a beard or not.
              returned: always
              type: boolean
            confidence:
              description: Level of confidence in the determination.
              returned: always
              type: float
        mustache:
          description: Indicates whether or not the face has a mustache, and the confidence level in the determination.
          returned: always
          type: complex
          contains:
            value:
              description: Boolean value that indicates whether the face has a mustache or not.
              returned: always
              type: boolean
            confidence:
              description: Level of confidence in the determination.
              returned: always
              type: float
        eyes_open:
          description: Indicates whether or not the eyes on the face are open, and the confidence level in the determination.
          returned: always
          type: complex
          contains:
            value:
              description: Boolean value that indicates whether the eyes on the face are open.
              returned: always
              type: boolean
            confidence:
              description: Level of confidence in the determination.
              returned: always
              type: float
        mouth_open:
          description: Indicates whether or not the mouth on the face are open, and the confidence level in the determination.
          returned: always
          type: complex
          contains:
            value:
              description: Boolean value that indicates whether the mouth on the face are open.
              returned: always
              type: boolean
            confidence:
              description: Level of confidence in the determination.
              returned: always
              type: float
        emotions:
          description: The emotions detected on the face, and the confidence level in the determination.
          returned: always
          type: complex
          contains:
            type:
              description: Type of emotion detected.
              returned: always
              type: string
            confidence:
              description: Level of confidence in the determination.
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
        confidence:
          description: Confidence level that the selected bounding box contains a face.
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


def index_exists(client, module, result):
    if module.check_mode:
        module.exit_json(changed=True)
    try:
        response = client.list_faces(
            CollectionId=module.params.get('collection')
        )
        index_bool = []
        result['face_ids'] = []
        for i in response['Faces']:
            if i['ExternalImageId'] == module.params.get('index_id'):
                result['face_ids'].append(i['FaceId'])
                index_bool.append(True)
            else:
                index_bool.append(False)
        if any(index_bool):
            return True
    except (BotoCoreError, ClientError) as e:
        module.fail_json_aws(e, msg="Failed to verify existence of face index")

    return False


def create_index(client, module, params, result):
    if module.check_mode:
        module.exit_json(changed=True)
    try:
        response = client.index_faces(**params)
        result['face_records'] = [camel_dict_to_snake_dict(i) for i in response['FaceRecords']]
        result['changed'] = True
        return result
    except (BotoCoreError, ClientError) as e:
        module.fail_json_aws(e, msg="Failed to index the provided image")

    return result


def update_index(client, module, params, result):
    if module.check_mode:
        module.exit_json(changed=True)
    try:
        response = client.index_faces(**params)
        result['face_records'] = [camel_dict_to_snake_dict(i) for i in response['FaceRecords']]
        updated_faces_list = []
        updated_faces = client.list_faces(
            CollectionId=params['CollectionId']
        )
        for i in updated_faces['Faces']:
            if i['ExternalImageId'] == module.params.get('index_id'):
                updated_faces_list.append(i['FaceId'])
        if updated_faces_list != result['face_ids']:
            result['changed'] = True
        return result
    except (BotoCoreError, ClientError) as e:
        module.fail_json_aws(e, msg="Failed to update face index")

    return result


def delete_index(client, module, result):
    if module.check_mode:
        module.exit_json(changed=True)
    try:
        response = client.delete_faces(
            CollectionId=module.params.get('collection'),
            FaceIds=result['face_ids']
        )
        result['changed'] = True
        return result
    except (BotoCoreError, ClientError) as e:
        module.fail_json_aws(e, msg="Failed to delete face index")

    return result


def main():
    module = AnsibleAWSModule(
        argument_spec={
            'index_id': dict(type='str', required=True),
            'state': dict(type='str', choices=['present', 'absent'], default='present'),
            'collection': dict(type='str', required=True),
            'image': dict(type='dict', required=True),
            'detection_attributes': dict(type='str', choices=['DEFAULT', 'ALL'], default='DEFAULT'),
        },
        supports_check_mode=True,
    )

    result = {
        'changed': False,
        'face_records': ''
    }

    image_s3 = {}
    image_s3['S3Object'] = {}
    image_s3['S3Object'].update({
        'Bucket': module.params.get('image').get('s3_object').get('bucket')
    })
    image_s3['S3Object'].update({
        'Name': module.params.get('image').get('s3_object').get('name')
    })
    if module.params.get('image').get('s3_object').get('version'):
        image_s3['S3Object'].update({
            'Version': module.params.get('image').get('s3_object').get('version')
        })

    params = {}
    params['ExternalImageId'] = module.params.get('index_id')
    params['CollectionId'] = module.params.get('collection')
    params['Image'] = {}
    params['Image'].update(image_s3)
    if module.params.get('detection_attributes'):
        params['DetectionAttributes'] = [module.params.get('detection_attributes')]

    client = module.client('rekognition')

    index_status = index_exists(client, module, result)

    desired_state = module.params.get('state')

    if desired_state == 'present':
        if not index_status:
            create_index(client, module, params, result)
        if index_status:
            update_index(client, module, params, result)

    if desired_state == 'absent':
        if index_status:
            delete_index(client, module, result)

    module.exit_json(changed=result['changed'], face_records=result['face_records'])


if __name__ == '__main__':
    main()
