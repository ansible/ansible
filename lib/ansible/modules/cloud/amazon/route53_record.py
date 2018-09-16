#!/usr/bin/python

# Copyright: (c) Ansible Project
# Copyright: (c) 2018, Shuang Wang <ooocamel@icloud.com>

# This code refactors the module route53.py of Ansible in order to support boto3.
# Rename route53 to route53_record for the consistency with other route53_xxx modules.

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

 __metaclass__ = type

 ANSIBLE_METADATA = {'status': ['preview'],
                     'supported_by': 'community',
                     'metadata_version': '1.1'}

 DOCUMENTATION = '''
 ---
 module: route53_record
 version_added: "2.8"
 author: Shuang Wang (@ptux)
 short_description: add or delete entries in Amazons Route53 DNS service
requirements:
  - botocore
  - boto3
  - python >= 2.7
extends_documentation_fragment:
  - aws
  - ec2
'''

EXAMPLES = '''
'''

RETURN = '''
'''