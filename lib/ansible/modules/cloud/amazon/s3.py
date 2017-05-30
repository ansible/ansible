#!/usr/bin/python
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['stableinterface'],
                    'supported_by': 'curated'}


DOCUMENTATION = '''
---
module: s3
short_description: manage objects in S3.
description:
    - This module allows the user to manage S3 buckets and the objects within them. Includes support for creating and
      deleting both objects and buckets, retrieving objects as files or strings and generating download links.
      This module has a dependency on python-boto.
version_added: "1.1"
options:
  aws_access_key:
    description:
      - AWS access key id. If not set then the value of the AWS_ACCESS_KEY environment variable is used.
    required: false
    default: null
    aliases: [ 'ec2_access_key', 'access_key' ]
  aws_secret_key:
    description:
      - AWS secret key. If not set then the value of the AWS_SECRET_KEY environment variable is used.
    required: false
    default: null
    aliases: ['ec2_secret_key', 'secret_key']
  bucket:
    description:
      - Bucket name.
    required: true
    default: null
    aliases: []
  dest:
    description:
      - The destination file path when downloading an object/key with a GET operation.
    required: false
    aliases: []
    version_added: "1.3"
  encrypt:
    description:
      - When set for PUT mode, asks for server-side encryption
    required: false
    default: no
    version_added: "2.0"
  expiration:
    description:
      - Time limit (in seconds) for the URL generated and returned by S3/Walrus when performing a mode=put or mode=geturl operation.
    required: false
    default: 600
    aliases: []
  headers:
    description:
      - Custom headers for PUT operation, as a dictionary of 'key=value' and 'key=value,key=value'.
    required: false
    default: null
    version_added: "2.0"
  marker:
    description:
      - Specifies the key to start with when using list mode. Object keys are returned in alphabetical order, starting with key after the marker in order.
    required: false
    default: null
    version_added: "2.0"
  max_keys:
    description:
      - Max number of results to return in list mode, set this if you want to retrieve fewer than the default 1000 keys.
    required: false
    default: 1000
    version_added: "2.0"
  metadata:
    description:
      - Metadata for PUT operation, as a dictionary of 'key=value' and 'key=value,key=value'.
    required: false
    default: null
    version_added: "1.6"
  mode:
    description:
      - Switches the module behaviour between put (upload), get (download), geturl (return download url, Ansible 1.3+),
        getstr (download object as string (1.3+)), list (list keys, Ansible 2.0+), create (bucket), delete (bucket),
        and delobj (delete object, Ansible 2.0+).
    required: true
    choices: ['get', 'put', 'delete', 'create', 'geturl', 'getstr', 'delobj', 'list']
  object:
    description:
      - Keyname of the object inside the bucket. Can be used to create "virtual directories", see examples.
    required: false
    default: null
  permission:
    description:
      - This option lets the user set the canned permissions on the object/bucket that are created.
        The permissions that can be set are 'private', 'public-read', 'public-read-write', 'authenticated-read' for a bucket or
        'private', 'public-read', 'public-read-write', 'aws-exec-read', 'authenticated-read', 'bucket-owner-read',
        'bucket-owner-full-control' for an object. Multiple permissions can be specified as a list.
    required: false
    default: private
    version_added: "2.0"
  prefix:
    description:
      - Limits the response to keys that begin with the specified prefix for list mode
    required: false
    default: null
    version_added: "2.0"
  version:
    description:
      - Version ID of the object inside the bucket. Can be used to get a specific version of a file if versioning is enabled in the target bucket.
    required: false
    default: null
    aliases: []
    version_added: "2.0"
  overwrite:
    description:
      - Force overwrite either locally on the filesystem or remotely with the object/key. Used with PUT and GET operations.
        Boolean or one of [always, never, different], true is equal to 'always' and false is equal to 'never', new in 2.0
    required: false
    default: 'always'
    version_added: "1.2"
  region:
    description:
     - "AWS region to create the bucket in. If not set then the value of the AWS_REGION and EC2_REGION environment variables
       are checked, followed by the aws_region and ec2_region settings in the Boto config file. If none of those are set the
       region defaults to the S3 Location: US Standard. Prior to ansible 1.8 this parameter could be specified but had no effect."
    required: false
    default: null
    version_added: "1.8"
  retries:
    description:
     - On recoverable failure, how many times to retry before actually failing.
    required: false
    default: 0
    version_added: "2.0"
  s3_url:
    description:
      - S3 URL endpoint for usage with Ceph, Eucalypus, fakes3, etc.  Otherwise assumes AWS
    default: null
    aliases: [ S3_URL ]
  rgw:
    description:
      - Enable Ceph RGW S3 support. This option requires an explicit url via s3_url.
    default: false
    version_added: "2.2"
  src:
    description:
      - The source file path when performing a PUT operation.
    required: false
    default: null
    aliases: []
    version_added: "1.3"
  ignore_nonexistent_bucket:
    description:
      - "Overrides initial bucket lookups in case bucket or iam policies are restrictive. Example: a user may have the
        GetObject permission but no other permissions. In this case using the option mode: get will fail without specifying
        ignore_nonexistent_bucket: True."
    default: false
    aliases: []
    version_added: "2.3"

requirements: [ "boto" ]
author:
    - "Lester Wade (@lwade)"
extends_documentation_fragment: aws
'''

EXAMPLES = '''
- name: Simple PUT operation
  s3:
    bucket: mybucket
    object: /my/desired/key.txt
    src: /usr/local/myfile.txt
    mode: put

- name: Simple PUT operation in Ceph RGW S3
  s3:
    bucket: mybucket
    object: /my/desired/key.txt
    src: /usr/local/myfile.txt
    mode: put
    rgw: true
    s3_url: "http://localhost:8000"

- name: Simple GET operation
  s3:
    bucket: mybucket
    object: /my/desired/key.txt
    dest: /usr/local/myfile.txt
    mode: get

- name: Get a specific version of an object.
  s3:
    bucket: mybucket
    object: /my/desired/key.txt
    version: 48c9ee5131af7a716edc22df9772aa6f
    dest: /usr/local/myfile.txt
    mode: get

- name: PUT/upload with metadata
  s3:
    bucket: mybucket
    object: /my/desired/key.txt
    src: /usr/local/myfile.txt
    mode: put
    metadata: 'Content-Encoding=gzip,Cache-Control=no-cache'

- name: PUT/upload with custom headers
  s3:
    bucket: mybucket
    object: /my/desired/key.txt
    src: /usr/local/myfile.txt
    mode: put
    headers: 'x-amz-grant-full-control=emailAddress=owner@example.com'

- name: List keys simple
  s3:
    bucket: mybucket
    mode: list

- name: List keys all options
  s3:
    bucket: mybucket
    mode: list
    prefix: /my/desired/
    marker: /my/desired/0023.txt
    max_keys: 472

- name: Create an empty bucket
  s3:
    bucket: mybucket
    mode: create
    permission: public-read

- name: Create a bucket with key as directory, in the EU region
  s3:
    bucket: mybucket
    object: /my/directory/path
    mode: create
    region: eu-west-1

- name: Delete a bucket and all contents
  s3:
    bucket: mybucket
    mode: delete

- name: GET an object but dont download if the file checksums match. New in 2.0
  s3:
    bucket: mybucket
    object: /my/desired/key.txt
    dest: /usr/local/myfile.txt
    mode: get
    overwrite: different

- name: Delete an object from a bucket
  s3:
    bucket: mybucket
    object: /my/desired/key.txt
    mode: delobj
'''

import os
import traceback
from ansible.module_utils.six.moves.urllib.parse import urlparse
from ssl import SSLError
from ansible.module_utils.basic import AnsibleModule, to_text
from ansible.module_utils.ec2 import ec2_argument_spec, camel_dict_to_snake_dict, get_aws_connection_info, boto3_conn, HAS_BOTO3

try:
    import boto3
    import botocore
    from botocore.utils import fix_s3_host
except ImportError:
    pass  # will be detected by imported HAS_BOTO3


def key_check(module, s3, bucket, obj, version=None, validate=True):
    exists = True
    try:
        if version:
            s3.head_object(Bucket=bucket, Key=obj, VersionId=verion)
        else:
            s3.head_object(Bucket=bucket, Key=obj)
    except botocore.exceptions.ClientError as e:
        # if a client error is thrown, check if it's a 404 error
        # if it's a 404 error, then the object does not exist
        error_code = int(e.response['Error']['Code'])
        if error_code == 404:
            exists = False
        elif error_code == 403 and validate is False:
            pass
        else:
            module.fail_json(msg="Failed while looking up object (during key check) %s." % obj,
                             exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))
    return exists


def keysum(module, s3, bucket, obj, version=None):
    if version:
        key_check = s3.get_object(Bucket=bucket, Key=obj, VersionId=version)
    else:
        key_check = s3.get_object(Bucket=bucket, Key=obj)
    if not key_check:
        return None
    md5_remote = key_check['ETag'][1:-1]
    etag_multipart = '-' in md5_remote  # Check for multipart, etag is not md5
    if etag_multipart is True:
        return None
    return md5_remote


def bucket_check(module, s3, bucket, validate=True):
    exists = True
    try:
        s3.head_bucket(Bucket=bucket)
    except botocore.exceptions.ClientError as e:
        # If a client error is thrown, then check that it was a 404 error.
        # If it was a 404 error, then the bucket does not exist.
        error_code = int(e.response['Error']['Code'])
        if error_code == 404:
            exists = False
        elif error_code == 403 and validate is False:
            pass
        else:
            module.fail_json(msg="Failed while looking up bucket (during bucket_check) %s." % bucket,
                             exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))
    except botocore.exceptions.EndpointConnectionError as e:
        module.fail_json(msg="Invalid endpoint provided: %s" % to_text(e), exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))
    return exists


def create_bucket(module, s3, bucket, location=None):
    if module.check_mode:
        module.exit_json(msg="PUT operation skipped - running in check mode", changed=True)
    if location is None:
        location = Location.DEFAULT
    configuration = {}
    if location != ('us-east-1' or None):
        configuration['LocationConstraint'] = location
    try:
        if len(configuration) > 0:
            s3.create_bucket(Bucket=bucket, CreateBucketConfiguration=configuration)
        else:
            s3.create_bucket(Bucket=bucket)
        for acl in module.params.get('permission'):
            s3.put_bucket_acl(ACL=acl, Bucket=bucket)
    except botocore.exceptions.ClientError as e:
        module.fail_json(msg="Failed while creating bucket or setting acl (check that you have CreateBucket and PutBucketAcl permission).",
                         exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))

    if bucket:
        return True


def list_keys(module, s3, bucket, prefix, marker, max_keys):
    all_keys = s3.list_objects(Bucket=bucket, Prefix=prefix, Marker=marker, MaxKeys=max_keys)
    keys = [x['Key'] for x in all_keys.get('Contents', [])]
    module.exit_json(msg="LIST operation complete", s3_keys=keys)


def delete_bucket(module, s3, bucket):
    if module.check_mode:
        module.exit_json(msg="DELETE operation skipped - running in check mode", changed=True)
    try:
        exists = bucket_check(module, s3, bucket)
        if exists is False:
            return False
        objects = s3.list_objects(Bucket=bucket)
        # if there are contents then we need to delete them before we can delete the bucket
        keys = [{'Key': data['Key']} for data in objects.get('Contents', [])]
        if keys:
            s3.delete_objects(Bucket=bucket, Delete={'Objects': keys})
        s3.delete_bucket(Bucket=bucket)
        return True
    except botocore.exceptions.ClientError as e:
        module.fail_json(msg="Failed while deleting bucket %s.", exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))


def delete_key(module, s3, bucket, obj):
    if module.check_mode:
        module.exit_json(msg="DELETE operation skipped - running in check mode", changed=True)
    try:
        s3.delete_object(Bucket=bucket, Key=obj)
        module.exit_json(msg="Object %s deleted from bucket %s." % (obj, bucket), changed=True)
    except botocore.exceptions.ClientError as e:
        module.fail_json(msg="Failed while trying to delete %s." % obj, exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))


def create_dirkey(module, s3, bucket, obj):
    if module.check_mode:
        module.exit_json(msg="PUT operation skipped - running in check mode", changed=True)
    try:
        bucket = s3.Bucket(bucket)
        key = bucket.new_key(obj)
        key.set_contents_from_string('')
        for acl in module.params.get('permission'):
            s3.put_object_acl(ACL=acl, Bucket=bucket, Key=obj)
        module.exit_json(msg="Virtual directory %s created in bucket %s" % (obj, bucket.name), changed=True)
    except botocore.exceptions.ClientError as e:
        module.fail_json(msg="Failed while creating object %s." % obj, exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))


def path_check(path):
    if os.path.exists(path):
        return True
    else:
        return False


def upload_s3file(module, s3, bucket, obj, src, expiry, metadata, encrypt, headers):
    if module.check_mode:
        module.exit_json(msg="PUT operation skipped - running in check mode", changed=True)
    try:
        if metadata:
            extra = {'Metadata': {}}
            for meta_key in metadata:
                extra['Metadata'][meta_key] = metadata[meta_key]
            s3.upload_file(Filename=src, Bucket=bucket, Key=obj, ExtraArgs=extra)
        else:
            s3.upload_file(Filename=src, Bucket=bucket, Key=obj)
        for acl in module.params.get('permission'):
            s3.put_object_acl(ACL=acl, Bucket=bucket, Key=obj)
        url = url = s3.generate_presigned_url(ClientMethod='put_object',
                                              Params={'Bucket': bucket, 'Key': obj},
                                              ExpiresIn=expiry)
        module.exit_json(msg="PUT operation complete", url=url, changed=True)
    except botocore.exceptions.ClientError as e:
        module.fail_json(msg="Unable to complete PUT operation.", exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))


def download_s3file(module, s3, bucket, obj, dest, retries, version=None):
    if module.check_mode:
        module.exit_json(msg="GET operation skipped - running in check mode", changed=True)
    # retries is the number of loops; range/xrange needs to be one
    # more to get that count of loops.
    try:
        if version:
            key = s3.get_object(Bucket=bucket, Key=obj, VersionId=version)
        else:
            key = s3.get_object(Bucket=bucket, Key=obj)
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] != "404":
            module.fail_json(msg="Could not find the key %s." % obj, exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))

    for x in range(0, retries + 1):
        try:
            s3.download_file(bucket, obj, dest)
            module.exit_json(msg="GET operation complete", changed=True)
        except botocore.exceptions.ClientError as e:
            # actually fail on last pass through the loop.
            if x >= retries:
                module.fail_json(msg="Failed while downloading %s." % obj, exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))
            # otherwise, try again, this may be a transient timeout.
            pass
        except SSLError as e:  # will ClientError catch SSLError?
            # actually fail on last pass through the loop.
            if x >= retries:
                module.fail_json(msg="s3 download failed: %s." % camel_dict_to_snake_dict(e.response),
                                 exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))
            # otherwise, try again, this may be a transient timeout.
            pass


def download_s3str(module, s3, bucket, obj, version=None, validate=True):
    if module.check_mode:
        module.exit_json(msg="GET operation skipped - running in check mode", changed=True)
    try:
        if version:
            contents = to_text(s3.get_object(Bucket=bucket, Key=obj, VersionId=version)["Body"].read())
        else:
            contents = to_text(s3.get_object(Bucket=bucket, Key=obj)["Body"].read())
        module.exit_json(msg="GET operation complete", contents=contents, changed=True)
    except botocore.exceptions.ClientError as e:
        module.fail_json(msg="Failed while getting contents of object %s as a string." % obj,
                         exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))


def get_download_url(module, s3, bucket, obj, expiry, changed=True):
    try:
        url = s3.generate_presigned_url(ClientMethod='get_object',
                                        Params={'Bucket': bucket, 'Key': obj},
                                        ExpiresIn=expiry)
        module.exit_json(msg="Download url:", url=url, expiry=expiry, changed=changed)
    except botocore.exceptions.ClientError as e:
        module.fail_json(msg="Failed while getting download url.", exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))


def is_fakes3(s3_url):
    """ Return True if s3_url has scheme fakes3:// """
    if s3_url is not None:
        return urlparse(s3_url).scheme in ('fakes3', 'fakes3s')
    else:
        return False


def is_walrus(s3_url):
    """ Return True if it's Walrus endpoint, not S3

    We assume anything other than *.amazonaws.com is Walrus"""
    if s3_url is not None:
        o = urlparse(s3_url)
        return not o.netloc.endswith('amazonaws.com')
    else:
        return False


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(
        dict(
            bucket=dict(required=True),
            dest=dict(default=None),
            encrypt=dict(default=True, type='bool'),
            expiry=dict(default=600, aliases=['expiration']),
            headers=dict(type='dict'),
            marker=dict(default=""),
            max_keys=dict(default=1000, type='int'),
            metadata=dict(type='dict'),
            mode=dict(choices=['get', 'put', 'delete', 'create', 'geturl', 'getstr', 'delobj', 'list'], required=True),
            object=dict(),
            permission=dict(type='list', default=['private']),
            version=dict(default=None),
            overwrite=dict(aliases=['force'], default='always'),
            prefix=dict(default=""),
            retries=dict(aliases=['retry'], type='int', default=0),
            s3_url=dict(aliases=['S3_URL']),
            rgw=dict(default='no', type='bool'),
            src=dict(),
            ignore_nonexistent_bucket=dict(default=False, type='bool')
        ),
    )
    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    if not HAS_BOTO3:
        module.fail_json(msg='boto3 and botocore required for this module')

    bucket = module.params.get('bucket')
    encrypt = module.params.get('encrypt')
    expiry = int(module.params['expiry'])
    dest = module.params.get('dest', '')
    headers = module.params.get('headers')
    marker = module.params.get('marker')
    max_keys = module.params.get('max_keys')
    metadata = module.params.get('metadata')
    mode = module.params.get('mode')
    obj = module.params.get('object')
    version = module.params.get('version')
    overwrite = module.params.get('overwrite')
    prefix = module.params.get('prefix')
    retries = module.params.get('retries')
    s3_url = module.params.get('s3_url')
    rgw = module.params.get('rgw')
    src = module.params.get('src')
    ignore_nonexistent_bucket = module.params.get('ignore_nonexistent_bucket')

    if dest:
        dest = os.path.expanduser(dest)

    object_canned_acl = ["private", "public-read", "public-read-write", "aws-exec-read", "authenticated-read", "bucket-owner-read", "bucket-owner-full-control"]
    bucket_canned_acl = ["private", "public-read", "public-read-write", "authenticated-read"]

    if overwrite not in ['always', 'never', 'different']:
        if module.boolean(overwrite):
            overwrite = 'always'
        else:
            overwrite = 'never'

    region, ec2_url, aws_connect_kwargs = get_aws_connection_info(module, boto3=True)

    if region in ('us-east-1', '', None):
        # S3ism for the US Standard region
        # need to find where to import Location.DEFAULT from
        # Before this was the equivalent of location = "" - TODO need to test this thoroughly
        location = 'us-east-1'
    else:
        # Boto uses symbolic names for locations but region strings will
        # actually work fine for everything except us-east-1 (US Standard)
        location = region

    if module.params.get('object'):
        obj = module.params['object']

    # Bucket deletion does not require obj.  Prevents ambiguity with delobj.
    if obj and mode == "delete":
        module.fail_json(msg='Parameter obj cannot be used with mode=delete')

    # allow eucarc environment variables to be used if ansible vars aren't set
    if not s3_url and 'S3_URL' in os.environ:
        s3_url = os.environ['S3_URL']

    # rgw requires an explicit url
    if rgw and not s3_url:
        module.fail_json(msg='rgw flavour requires s3_url')

    # Look at s3_url and tweak connection settings
    # if connecting to RGW, Walrus or fakes3
    for key in ['validate_certs', 'security_token', 'profile_name']:
        aws_connect_kwargs.pop(key, None)
    try:
        # s3 = boto3_conn(module, conn_type='client', resource='s3', region=region, endpoint=ec2_url, **aws_connect_kwargs)
        s3 = get_s3_connection(module, aws_connect_kwargs, location, rgw, s3_url)  # WIP - this function needs testing!
    except botocore.exceptions.ClientError as e:
        module.fail_json(msg="Failed while trying to connect to s3.", exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))
    except Exception as e:
        module.fail_json(msg="Failed to connect to s3.", exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))
    if s3 is None:  # this should never happen
        module.fail_json(msg='Unknown error, failed to create s3 connection, no information from boto3.')

    # First, we check to see if the bucket exists, we get "bucket" returned.
    bucketrtn = bucket_check(module, s3, bucket)

    if not ignore_nonexistent_bucket:
        validate = True
        if mode not in ('create', 'put', 'delete') and not bucketrtn:
            module.fail_json(msg="Source bucket cannot be found.")
    else:
        validate = False

    # If our mode is a GET operation (download), go through the procedure as appropriate ...
    if mode == 'get':
        # Next, we check to see if the key in the bucket exists. If it exists, it also returns key_matches md5sum check.
        keyrtn = key_check(module, s3, bucket, obj, version=version, validate=validate)
        if keyrtn is False:
            if version is not None:
                module.fail_json(msg="Key %s with version id %s does not exist." % (obj, version))
            else:
                module.fail_json(msg="Key %s or source bucket %s does not exist." % (obj, bucket))

        # If the destination path doesn't exist or overwrite is True, no need to do the md5um etag check, so just download.
        pathrtn = path_check(dest)

        # Compare the remote MD5 sum of the object with the local dest md5sum, if it already exists.
        if pathrtn is True:
            md5_remote = keysum(module, s3, bucket, obj, version=version)
            md5_local = module.md5(dest)
            if md5_local == md5_remote:
                sum_matches = True
                if overwrite == 'always':
                    download_s3file(module, s3, bucket, obj, dest, retries, version=version)
                else:
                    module.exit_json(msg="Local and remote object are identical, ignoring. Use overwrite=always parameter to force.", changed=False)
            else:
                sum_matches = False

                if overwrite in ('always', 'different'):
                    download_s3file(module, s3, bucket, obj, dest, retries, version=version)
                else:
                    module.exit_json(msg="WARNING: Checksums do not match. Use overwrite parameter to force download.")
        else:
            download_s3file(module, s3, bucket, obj, dest, retries, version=version)

        # Firstly, if key_matches is TRUE and overwrite is not enabled, we EXIT with a helpful message.
        if sum_matches and overwrite == 'never':
            module.exit_json(msg="Local and remote object are identical, ignoring. Use overwrite parameter to force.", changed=False)

    # if our mode is a PUT operation (upload), go through the procedure as appropriate ...
    if mode == 'put':

        # if putting an object in a bucket yet to be created, acls for the bucket and/or the object may be specified
        bucket_acl = []
        obj_acl = []
        for acl in module.params.get('permission'):
            if acl in bucket_canned_acl:
                bucket_acl.append(acl)
            if acl in object_canned_acl:
                obj_acl.append(acl)
            if acl not in (bucket_canned_acl and object_canned_acl):
                module.fail_json(msg='Unknown permission specified: %s' % str(acl))

        # Lets check the src path.
        pathrtn = path_check(src)
        if not pathrtn:
            module.fail_json(msg="Local object for PUT does not exist")

        # Lets check to see if bucket exists to get ground truth.
        if bucketrtn:
            keyrtn = key_check(module, s3, bucket, obj, version=version, validate=validate)

        # Lets check key state. Does it exist and if it does, compute the etag md5sum.
        if bucketrtn and keyrtn:
            md5_remote = keysum(module, s3, bucket, obj)
            md5_local = module.md5(src)

            if md5_local == md5_remote:
                sum_matches = True
                if overwrite == 'always':
                    # only use valid object acls for the upload_s3file function
                    module.params['permission'] = obj_acl
                    upload_s3file(module, s3, bucket, obj, src, expiry, metadata, encrypt, headers)
                else:
                    get_download_url(module, s3, bucket, obj, expiry, changed=False)
            else:
                sum_matches = False
                if overwrite in ('always', 'different'):
                    # only use valid object acls for the upload_s3file function
                    module.params['permission'] = obj_acl
                    upload_s3file(module, s3, bucket, obj, src, expiry, metadata, encrypt, headers)
                else:
                    module.exit_json(msg="WARNING: Checksums do not match. Use overwrite parameter to force upload.")

        # If neither exist (based on bucket existence), we can create both.
        if pathrtn and not bucketrtn:
            # only use valid bucket acls for create_bucket function
            module.params['permission'] = bucket_acl
            create_bucket(module, s3, bucket, location)
            # only use valid object acls for the upload_s3file function
            module.params['permission'] = obj_acl
            upload_s3file(module, s3, bucket, obj, src, expiry, metadata, encrypt, headers)

        # If bucket exists but key doesn't, just upload.
        if bucketrtn and pathrtn and not keyrtn:
            # only use valid object acls for the upload_s3file function
            module.params['permission'] = obj_acl
            upload_s3file(module, s3, bucket, obj, src, expiry, metadata, encrypt, headers)

    # Delete an object from a bucket, not the entire bucket
    if mode == 'delobj':
        if obj is None:
            module.fail_json(msg="object parameter is required")
        if bucket:
            deletertn = delete_key(module, s3, bucket, obj)
            if deletertn is True:
                module.exit_json(msg="Object %s deleted from bucket %s." % (obj, bucket), changed=True)
        else:
            module.fail_json(msg="Bucket parameter is required.")

    # Delete an entire bucket, including all objects in the bucket
    if mode == 'delete':
        if bucket:
            deletertn = delete_bucket(module, s3, bucket)
            if deletertn is True:
                module.exit_json(msg="Bucket %s and all keys have been deleted." % bucket, changed=True)
        else:
            module.fail_json(msg="Bucket parameter is required.")

    # Support for listing a set of keys
    if mode == 'list':
        exists = bucket_check(module, s3, bucket)

        # If the bucket does not exist then bail out
        if not exists:
            module.fail_json(msg="Target bucket (%s) cannot be found" % bucket)

        list_keys(module, s3, bucket, prefix, marker, max_keys)

    # Need to research how to create directories without "populating" a key, so this should just do bucket creation for now.
    # WE SHOULD ENABLE SOME WAY OF CREATING AN EMPTY KEY TO CREATE "DIRECTORY" STRUCTURE, AWS CONSOLE DOES THIS.
    if mode == 'create':
        # if both creating a bucket and putting an object in it, acls for the bucket and/or the object may be specified
        bucket_acl = []
        obj_acl = []
        for acl in module.params.get('permission'):
            if acl in bucket_canned_acl:
                bucket_acl.append(acl)
            if acl in object_canned_acl:
                obj_acl.append(acl)
            if acl not in (bucket_canned_acl and object_canned_acl):
                module.fail_json(msg='Unknown permission specified: %s' % str(acl))
        if bucket and not obj:
            if bucketrtn:
                module.exit_json(msg="Bucket already exists.", changed=False)
            else:
                # only use valid bucket acls when creating the bucket
                module.params['permission'] = bucket_acl
                module.exit_json(msg="Bucket created successfully", changed=create_bucket(module, s3, bucket, location))
        if bucket and obj:
            if obj.endswith('/'):
                dirobj = obj
            else:
                dirobj = obj + "/"
            if bucketrtn:
                keyrtn = key_check(module, s3, bucket, dirobj)
                if keyrtn is True:
                    module.exit_json(msg="Bucket %s and key %s already exists." % (bucket, obj), changed=False)
                else:
                    # setting valid object acls for the create_dirkey function
                    module.params['permission'] = obj_acl
                    create_dirkey(module, s3, bucket, dirobj)
            else:
                # only use valid bucket acls for the create_bucket function
                module.params['permission'] = bucket_acl
                created = create_bucket(module, s3, bucket, location)
                # only use valid object acls for the create_dirkey function
                module.params['permission'] = obj_acl
                create_dirkey(module, s3, bucket, dirobj)

    # Support for grabbing the time-expired URL for an object in S3/Walrus.
    if mode == 'geturl':
        if not bucket and not obj:
            module.fail_json(msg="Bucket and Object parameters must be set")

        keyrtn = key_check(module, s3, bucket, obj, version=version, validate=validate)
        if keyrtn:
            get_download_url(module, s3, bucket, obj, expiry)
        else:
            module.fail_json(msg="Key %s does not exist." % obj)

    if mode == 'getstr':
        if bucket and obj:
            keyrtn = key_check(module, s3, bucket, obj, version=version, validate=validate)
            if keyrtn:
                download_s3str(module, s3, bucket, obj, version=version)
            elif version is not None:
                module.fail_json(msg="Key %s with version id %s does not exist." % (obj, version))
            else:
                module.fail_json(msg="Key %s does not exist." % obj)

    module.exit_json(failed=False)


def get_s3_connection(module, aws_connect_kwargs, location, rgw, s3_url):
    if s3_url and rgw:  # TODO - test this
        rgw = urlparse(s3_url)
        s3 = boto3_conn(module,
                        conn_type='client',
                        resource='s3',
                        use_ssl=rgw.scheme == 'https',
                        region=location,
                        endpoint=s3_url,
                        **aws_connect_kwargs)
    elif is_fakes3(s3_url):  # DONE - I have tested this and works for me; is there a nicer way to generate the endpoint?
        fakes3 = urlparse(s3_url)
        session = boto3.session.Session()
        if fakes3.scheme == 'fakes3s':
            protocol = "https"
        else:
            protocol = "http"
        s3 = session.client(service_name='s3',
                            endpoint_url="%s://%s:%s" % (protocol, fakes3.hostname, to_text(fakes3.port)),
                            use_ssl=fakes3.scheme == 'fakes3s',
                            region_name=None,
                            **aws_connect_kwargs)
    elif is_walrus(s3_url):  # TODO - test this
        walrus = urlparse(s3_url).hostname
        s3 = boto3_conn(module,
                        conn_type='client',
                        resource='s3',
                        region=location,
                        endpoint=walrus,
                        **aws_connect_kwargs)

    else:
        aws_connect_kwargs['is_secure'] = True
        try:
            s3 = boto3_conn(module,
                            conn_type='client',
                            resource='s3',
                            use_ssl=aws_connect_kwargs.pop('is_secure'),
                            region=location,
                            **aws_connect_kwargs)
        except botocore.exceptions.ClientError as e:
            # use this as fallback because connect_to_region seems to fail in boto + non 'classic' aws accounts in some cases
            # are there cases when this should have a fallback here? TODO - test this.
            module.fail_json(msg="Failed while trying to connect to s3 (during get_s3_connection).",
                             exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))
    return s3

if __name__ == '__main__':
    main()
