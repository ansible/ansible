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

ANSIBLE_METADATA = {'status': ['stableinterface'],
                    'supported_by': 'committer',
                    'version': '1.0'}

DOCUMENTATION = '''
---
module: s3_cors
short_description: Manage CORS for S3 buckets in AWS, Ceph, Walrus and FakeS3
description:
    - Manage CORS for S3 buckets in AWS, Ceph, Walrus and FakeS3
version_added: "2.3"
author: "Oyvind Saltvik (@fivethreeo)"
options:
  name:
    description:
      - Name of the s3 bucket
    required: true
    default: null
  rules:
    description:
      - Cors rules to put on the s3 bucket
    required: false
    default: []
  s3_url:
    description:
      - S3 URL endpoint for usage with Ceph, Eucalypus, fakes3, etc. Otherwise assumes AWS
    default: null
    aliases: [ S3_URL ]
  ceph:
    description:
      - Enable API compatibility with Ceph. It takes into account the S3 API subset working
        with Ceph in order to provide the same module behaviour where possible.
    version_added: "2.2"
  state:
    description:
      - Create or remove cors on the s3 bucket
    required: false
    default: present
    choices: [ 'present', 'absent' ]
extends_documentation_fragment:
    - aws
    - ec2
'''

EXAMPLES = '''
# Note: These examples do not set authentication details, see the AWS Guide for details.

# Create a simple cors for s3 bucket
- s3_cors:
    name: mys3bucket
    rules:
        - allowed_origins:
            - http://www.example.com/
          allowed_methods:
            - GET
            - POST
          expose_headers:
            - x-amz-server-side-encryption
            - x-amz-request-id
          max_age_seconds: 30000

# Remove cors for s3 bucket
- s3_cors:
    name: mys3bucket
    state: absent
'''

import json
import os
import traceback
import xml.etree.ElementTree as ET
import xml.sax

import ansible.module_utils.six.moves.urllib.parse as urlparse
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ec2 import get_aws_connection_info, ec2_argument_spec

try:
    import boto.ec2
    from boto.s3.connection import OrdinaryCallingFormat, Location, S3Connection
    from boto.s3.tagging import Tags, TagSet
    from boto.exception import BotoServerError, S3CreateError, S3ResponseError
    from boto.handler import XmlHandler
    from boto.s3.cors import CORSConfiguration
    HAS_BOTO = True
except ImportError:
    HAS_BOTO = False

def tagwrap(tag, content):
    return '    <%s>%s</%s>\n' % (tag, content, tag)

def build_cors_xml(rules):

    rules_xml = []
    for rule in rules:
        ruleoptions_xml = []
        for origin in rule.get('allowed_origins', []):
            ruleoptions_xml.append(tagwrap('AllowedOrigin', origin))
        for method in rule.get('allowed_methods', []):
            ruleoptions_xml.append(tagwrap('AllowedMethod', method))
        max_age_seconds = rule.get('max_age_seconds', False)
        if max_age_seconds:
            ruleoptions_xml.append(tagwrap('MaxAgeSeconds', max_age_seconds))
        for method in rule.get('allowed_headers', []):
            ruleoptions_xml.append(tagwrap('AllowedHeader', method))
        for method in rule.get('expose_headers', []):
            ruleoptions_xml.append(tagwrap('ExposeHeader', method))
        rules_xml.append('  <CORSRule>\n%s  </CORSRule>\n' % ''.join(ruleoptions_xml))

    return '''<?xml version="1.0" encoding="UTF-8"?>
<CORSConfiguration xmlns="http://s3.amazonaws.com/doc/2006-03-01/">
%s</CORSConfiguration>''' % ''.join(rules_xml)

def _create_or_update_bucket_cors(connection, module, location):

    name = module.params.get("name")
    rules = module.params.get("rules")
    changed = False

    try:
        bucket = connection.get_bucket(name)
    except S3ResponseError as e:
        module.fail_json(msg=e.message)

    # CORS xml
    cors_xml = build_cors_xml(rules)

    try:
        current_cors_config = bucket.get_cors()
        current_cors_xml = current_cors_config.to_xml()
    except S3ResponseError as e:
        if e.error_code == "NoSuchCORSConfiguration":
            current_cors_xml = None
        else:
            module.fail_json(msg=e.message)

    if cors_xml is not None:
        cors_rule_change = False
        if current_cors_xml is None:
            cors_rule_change = True  # Create
        else:
            # Convert cors_xml to a Boto CorsConfiguration object for comparison
            cors_config = CORSConfiguration()
            h = XmlHandler(cors_config, bucket)
            xml.sax.parseString(cors_xml, h)
            if cors_config.to_xml() != current_cors_config.to_xml():
                cors_rule_change = True  # Update

        if cors_rule_change:
            try:
                bucket.set_cors_xml(cors_xml)
                changed = True
                current_cors_xml = bucket.get_cors().to_xml()
            except S3ResponseError, e:
                module.fail_json(msg=e.message)


    module.exit_json(changed=changed, name=bucket.name, cors_xml=cors_xml)


def _destroy_bucket_cors(connection, module):

    name = module.params.get("name")
    changed = False

    try:
        bucket = connection.get_bucket(name)
    except S3ResponseError as e:
        if e.error_code != "NoSuchBucket":
            module.fail_json(msg=e.message)
        else:
            # Bucket already absent
            module.exit_json(changed=changed)

    try:
        current_cors_config = bucket.get_cors()
        current_cors_xml = current_cors_config.to_xml()
    except S3ResponseError as e:
        if e.error_code == "NoSuchCORSConfiguration":
            current_cors_xml = None
        else:
            module.fail_json(msg=e.message)

    if current_cors_xml is not None:
        try:
            bucket.delete_cors()
            changed = True
            current_cors_xml = None
        except S3ResponseError, e:
            module.fail_json(msg=e.message)

    module.exit_json(changed=changed)


def _create_or_update_bucket_cors_ceph(connection, module, location):
    #TODO: add update
    _destroy_bucket_cors(connection, module)

def _destroy_bucket_cors_ceph(connection, module):

    _destroy_bucket_cors(connection, module)


def create_or_update_bucket_cors(connection, module, location, flavour='aws'):
    if flavour == 'ceph':
        _create_or_update_bucket_cors_ceph(connection, module, location)
    else:
        _create_or_update_bucket_cors(connection, module, location)


def destroy_bucket_cors(connection, module, flavour='aws'):
    if flavour == 'ceph':
        _destroy_bucket_cors_ceph(connection, module)
    else:
        _destroy_bucket_cors(connection, module)


def is_fakes3(s3_url):
    """ Return True if s3_url has scheme fakes3:// """
    if s3_url is not None:
        return urlparse.urlparse(s3_url).scheme in ('fakes3', 'fakes3s')
    else:
        return False


def is_walrus(s3_url):
    """ Return True if it's Walrus endpoint, not S3

    We assume anything other than *.amazonaws.com is Walrus"""
    if s3_url is not None:
        o = urlparse.urlparse(s3_url)
        return not o.hostname.endswith('amazonaws.com')
    else:
        return False

def main():

    argument_spec = ec2_argument_spec()
    argument_spec.update(
        dict(
            name=dict(required=True, type='str'),
            rules=dict(type='list'),
            s3_url=dict(aliases=['S3_URL'], type='str'),
            state=dict(default='present', type='str', choices=['present', 'absent']),
            ceph=dict(default='no', type='bool')
        )
    )

    module = AnsibleModule(argument_spec=argument_spec)

    if not HAS_BOTO:
        module.fail_json(msg='boto required for this module')

    region, ec2_url, aws_connect_params = get_aws_connection_info(module)

    if region in ('us-east-1', '', None):
        # S3ism for the US Standard region
        location = Location.DEFAULT
    else:
        # Boto uses symbolic names for locations but region strings will
        # actually work fine for everything except us-east-1 (US Standard)
        location = region

    s3_url = module.params.get('s3_url')

    # allow eucarc environment variables to be used if ansible vars aren't set
    if not s3_url and 'S3_URL' in os.environ:
        s3_url = os.environ['S3_URL']

    ceph = module.params.get('ceph')

    if ceph and not s3_url:
        module.fail_json(msg='ceph flavour requires s3_url')

    flavour = 'aws'

    # Look at s3_url and tweak connection settings
    # if connecting to Walrus or fakes3
    try:
        if s3_url and ceph:
            ceph = urlparse.urlparse(s3_url)
            connection = boto.connect_s3(
                host=ceph.hostname,
                port=ceph.port,
                is_secure=ceph.scheme == 'https',
                calling_format=OrdinaryCallingFormat(),
                **aws_connect_params
            )
            flavour = 'ceph'
        elif is_fakes3(s3_url):
            fakes3 = urlparse.urlparse(s3_url)
            connection = S3Connection(
                is_secure=fakes3.scheme == 'fakes3s',
                host=fakes3.hostname,
                port=fakes3.port,
                calling_format=OrdinaryCallingFormat(),
                **aws_connect_params
            )
        elif is_walrus(s3_url):
            walrus = urlparse.urlparse(s3_url).hostname
            connection = boto.connect_walrus(walrus, **aws_connect_params)
        else:
            connection = boto.s3.connect_to_region(location, is_secure=True, calling_format=OrdinaryCallingFormat(), **aws_connect_params)
            # use this as fallback because connect_to_region seems to fail in boto + non 'classic' aws accounts in some cases
            if connection is None:
                connection = boto.connect_s3(**aws_connect_params)

    except boto.exception.NoAuthHandlerFound as e:
        module.fail_json(msg='No Authentication Handler found: %s ' % str(e))
    except Exception as e:
        module.fail_json(msg='Failed to connect to S3: %s' % str(e))

    if connection is None: # this should never happen
        module.fail_json(msg ='Unknown error, failed to create s3 connection, no information from boto.')

    state = module.params.get("state")

    if state == 'present':
        create_or_update_bucket_cors(connection, module, location)
    elif state == 'absent':
        destroy_bucket_cors(connection, module, flavour=flavour)

if __name__ == '__main__':
    main()
