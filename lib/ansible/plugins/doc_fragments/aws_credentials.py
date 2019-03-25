# -*- coding: utf-8 -*-

# Copyright: (c) 2017,  Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


class ModuleDocFragment(object):

    # Plugin options for AWS credentials
    DOCUMENTATION = r'''
options:
  aws_profile:
    description: The AWS profile
    type: str
    aliases: [ boto_profile ]
    env:
      - name: AWS_DEFAULT_PROFILE
      - name: AWS_PROFILE
  aws_access_key:
    description: The AWS access key to use.
    type: str
    aliases: [ aws_access_key_id ]
    env:
      - name: EC2_ACCESS_KEY
      - name: AWS_ACCESS_KEY
      - name: AWS_ACCESS_KEY_ID
  aws_secret_key:
    description: The AWS secret key that corresponds to the access key.
    type: str
    aliases: [ aws_secret_access_key ]
    env:
      - name: EC2_SECRET_KEY
      - name: AWS_SECRET_KEY
      - name: AWS_SECRET_ACCESS_KEY
  aws_security_token:
    description: The AWS security token if using temporary access and secret keys.
    type: str
    env:
      - name: EC2_SECURITY_TOKEN
      - name: AWS_SESSION_TOKEN
      - name: AWS_SECURITY_TOKEN
'''
