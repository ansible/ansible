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

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['stableinterface'],
                    'supported_by': 'core'}


DOCUMENTATION = '''
---
module: aws_s3
short_description: manage objects in S3.
description:
    - This module allows the user to manage S3 buckets and the objects within them. Includes support for creating and
      deleting both objects and buckets, retrieving objects as files or strings and generating download links.
      This module has a dependency on boto3 and botocore.
notes:
   - In 2.4, this module has been renamed from C(s3) into M(aws_s3).
version_added: "1.1"
options:
  aws_access_key:
    description:
      - AWS access key id. If not set then the value of the AWS_ACCESS_KEY environment variable is used.
    aliases: [ 'ec2_access_key', 'access_key' ]
  aws_secret_key:
    description:
      - AWS secret key. If not set then the value of the AWS_SECRET_KEY environment variable is used.
    aliases: ['ec2_secret_key', 'secret_key']
  bucket:
    description:
      - Bucket name.
    required: true
  dest:
    description:
      - The destination file path when downloading an object/key with a GET operation.
    version_added: "1.3"
  encrypt:
    description:
      - When set for PUT mode, asks for server-side encryption.
    default: True
    version_added: "2.0"
  encryption_mode:
    description:
      - What encryption mode to use if C(encrypt) is set
    default: AES256
    choices:
      - AES256
      - aws:kms
    version_added: "2.7"
  expiration:
    description:
      - Time limit (in seconds) for the URL generated and returned by S3/Walrus when performing a mode=put or mode=geturl operation.
    default: 600
  headers:
    description:
      - Custom headers for PUT operation, as a dictionary of 'key=value' and 'key=value,key=value'.
    version_added: "2.0"
  marker:
    description:
      - Specifies the key to start with when using list mode. Object keys are returned in alphabetical order, starting with key after the marker in order.
    version_added: "2.0"
  max_keys:
    description:
      - Max number of results to return in list mode, set this if you want to retrieve fewer than the default 1000 keys.
    default: 1000
    version_added: "2.0"
  metadata:
    description:
      - Metadata for PUT operation, as a dictionary of 'key=value' and 'key=value,key=value'.
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
  permission:
    description:
      - This option lets the user set the canned permissions on the object/bucket that are created.
        The permissions that can be set are 'private', 'public-read', 'public-read-write', 'authenticated-read' for a bucket or
        'private', 'public-read', 'public-read-write', 'aws-exec-read', 'authenticated-read', 'bucket-owner-read',
        'bucket-owner-full-control' for an object. Multiple permissions can be specified as a list.
    default: private
    version_added: "2.0"
  prefix:
    description:
      - Limits the response to keys that begin with the specified prefix for list mode
    default: ""
    version_added: "2.0"
  version:
    description:
      - Version ID of the object inside the bucket. Can be used to get a specific version of a file if versioning is enabled in the target bucket.
    version_added: "2.0"
  overwrite:
    description:
      - Force overwrite either locally on the filesystem or remotely with the object/key. Used with PUT and GET operations.
        Boolean or one of [always, never, different], true is equal to 'always' and false is equal to 'never', new in 2.0.
        When this is set to 'different', the md5 sum of the local file is compared with the 'ETag' of the object/key in S3.
        The ETag may or may not be an MD5 digest of the object data. See the ETag response header here
        U(http://docs.aws.amazon.com/AmazonS3/latest/API/RESTCommonResponseHeaders.html)
    default: 'always'
    aliases: ['force']
    version_added: "1.2"
  region:
    description:
     - "AWS region to create the bucket in. If not set then the value of the AWS_REGION and EC2_REGION environment variables
       are checked, followed by the aws_region and ec2_region settings in the Boto config file. If none of those are set the
       region defaults to the S3 Location: US Standard. Prior to ansible 1.8 this parameter could be specified but had no effect."
    version_added: "1.8"
  retries:
    description:
     - On recoverable failure, how many times to retry before actually failing.
    default: 0
    version_added: "2.0"
  s3_url:
    description:
      - S3 URL endpoint for usage with Ceph, Eucalypus, fakes3, etc.  Otherwise assumes AWS
    aliases: [ S3_URL ]
  rgw:
    description:
      - Enable Ceph RGW S3 support. This option requires an explicit url via s3_url.
    default: false
    version_added: "2.2"
  src:
    description:
      - The source file path when performing a PUT operation.
    version_added: "1.3"
  ignore_nonexistent_bucket:
    description:
      - "Overrides initial bucket lookups in case bucket or iam policies are restrictive. Example: a user may have the
        GetObject permission but no other permissions. In this case using the option mode: get will fail without specifying
        ignore_nonexistent_bucket: True."
    version_added: "2.3"
  encryption_kms_key_id:
    description:
      - KMS key id to use when encrypting objects using C(aws:kms) encryption. Ignored if encryption is not C(aws:kms)
    version_added: "2.7"

requirements: [ "boto3", "botocore" ]
author:
    - "Lester Wade (@lwade)"
    - "Sloane Hertel (@s-hertel)"
extends_documentation_fragment:
    - aws
    - ec2
'''

EXAMPLES = '''
- name: Simple PUT operation
  aws_s3:
    bucket: mybucket
    object: /my/desired/key.txt
    src: /usr/local/myfile.txt
    mode: put

- name: Simple PUT operation in Ceph RGW S3
  aws_s3:
    bucket: mybucket
    object: /my/desired/key.txt
    src: /usr/local/myfile.txt
    mode: put
    rgw: true
    s3_url: "http://localhost:8000"

- name: Simple GET operation
  aws_s3:
    bucket: mybucket
    object: /my/desired/key.txt
    dest: /usr/local/myfile.txt
    mode: get

- name: Get a specific version of an object.
  aws_s3:
    bucket: mybucket
    object: /my/desired/key.txt
    version: 48c9ee5131af7a716edc22df9772aa6f
    dest: /usr/local/myfile.txt
    mode: get

- name: PUT/upload with metadata
  aws_s3:
    bucket: mybucket
    object: /my/desired/key.txt
    src: /usr/local/myfile.txt
    mode: put
    metadata: 'Content-Encoding=gzip,Cache-Control=no-cache'

- name: PUT/upload with custom headers
  aws_s3:
    bucket: mybucket
    object: /my/desired/key.txt
    src: /usr/local/myfile.txt
    mode: put
    headers: 'x-amz-grant-full-control=emailAddress=owner@example.com'

- name: List keys simple
  aws_s3:
    bucket: mybucket
    mode: list

- name: List keys all options
  aws_s3:
    bucket: mybucket
    mode: list
    prefix: /my/desired/
    marker: /my/desired/0023.txt
    max_keys: 472

- name: Create an empty bucket
  aws_s3:
    bucket: mybucket
    mode: create
    permission: public-read

- name: Create a bucket with key as directory, in the EU region
  aws_s3:
    bucket: mybucket
    object: /my/directory/path
    mode: create
    region: eu-west-1

- name: Delete a bucket and all contents
  aws_s3:
    bucket: mybucket
    mode: delete

- name: GET an object but don't download if the file checksums match. New in 2.0
  aws_s3:
    bucket: mybucket
    object: /my/desired/key.txt
    dest: /usr/local/myfile.txt
    mode: get
    overwrite: different

- name: Delete an object from a bucket
  aws_s3:
    bucket: mybucket
    object: /my/desired/key.txt
    mode: delobj
'''

RETURN = '''
msg:
  description: msg indicating the status of the operation
  returned: always
  type: string
  sample: PUT operation complete
url:
  description: url of the object
  returned: (for put and geturl operations)
  type: string
  sample: https://my-bucket.s3.amazonaws.com/my-key.txt?AWSAccessKeyId=<access-key>&Expires=1506888865&Signature=<signature>
expiry:
  description: number of seconds the presigned url is valid for
  returned: (for geturl operation)
  type: int
  sample: 600
contents:
  description: contents of the object as string
  returned: (for getstr operation)
  type: string
  sample: "Hello, world!"
s3_keys:
  description: list of object keys
  returned: (for list operation)
  type: list
  sample:
  - prefix1/
  - prefix1/key1
  - prefix1/key2
'''

import hashlib
import mimetypes
import os
from ansible.module_utils.six.moves.urllib.parse import urlparse
from ssl import SSLError
from ansible.module_utils.basic import to_text, to_native
from ansible.module_utils.aws.core import AnsibleAWSModule
from ansible.module_utils.ec2 import ec2_argument_spec, get_aws_connection_info, boto3_conn

try:
    import botocore
except ImportError:
    pass  # will be detected by imported AnsibleAWSModule

IGNORE_S3_DROP_IN_EXCEPTIONS = ['XNotImplemented', 'NotImplemented']


class Sigv4Required(Exception):
    pass


def key_check(module, s3, bucket, obj, version=None, validate=True):
    exists = True
    try:
        if version:
            s3.head_object(Bucket=bucket, Key=obj, VersionId=version)
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
            module.fail_json_aws(e, msg="Failed while looking up object (during key check) %s." % obj)
    except botocore.exceptions.BotoCoreError as e:
        module.fail_json_aws(e, msg="Failed while looking up object (during key check) %s." % obj)
    return exists


def keysum_compare(module, local_file, s3, bucket, obj, version=None):
    s3_keysum = keysum(s3, bucket, obj, version=version)
    if '-' in s3_keysum:  # Check for multipart, ETag is not a proper MD5 sum
        parts = int(s3_keysum.split('-')[1])
        md5s = []

        with open(local_file, 'rb') as f:
            for part_num in range(1, parts + 1):
                # Get the part size for every part of the multipart uploaded object
                if version:
                    key_head = s3.head_object(Bucket=bucket, Key=obj, VersionId=version, PartNumber=part_num)
                else:
                    key_head = s3.head_object(Bucket=bucket, Key=obj, PartNumber=part_num)
                part_size = int(key_head['ContentLength'])
                data = f.read(part_size)
                hash = hashlib.md5(data)
                md5s.append(hash)

        digests = b''.join(m.digest() for m in md5s)
        digests_md5 = hashlib.md5(digests)
        local_keysum = '{0}-{1}'.format(digests_md5.hexdigest(), len(md5s))
    else:  # Compute the MD5 sum normally
        local_keysum = module.md5(local_file)

    return s3_keysum == local_keysum


def keysum(s3, bucket, obj, version=None):
    if version:
        key_check = s3.head_object(Bucket=bucket, Key=obj, VersionId=version)
    else:
        key_check = s3.head_object(Bucket=bucket, Key=obj)
    if not key_check:
        return None
    md5_remote = key_check['ETag'][1:-1]
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
            module.fail_json_aws(e, msg="Failed while looking up bucket (during bucket_check) %s." % bucket)
    except botocore.exceptions.EndpointConnectionError as e:
        module.fail_json_aws(e, msg="Invalid endpoint provided")
    except botocore.exceptions.BotoCoreError as e:
        module.fail_json_aws(e, msg="Failed while looking up bucket (during bucket_check) %s." % bucket)
    return exists


def create_bucket(module, s3, bucket, location=None):
    if module.check_mode:
        module.exit_json(msg="CREATE operation skipped - running in check mode", changed=True)
    configuration = {}
    if location not in ('us-east-1', None):
        configuration['LocationConstraint'] = location
    try:
        if len(configuration) > 0:
            s3.create_bucket(Bucket=bucket, CreateBucketConfiguration=configuration)
        else:
            s3.create_bucket(Bucket=bucket)
        for acl in module.params.get('permission'):
            s3.put_bucket_acl(ACL=acl, Bucket=bucket)
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] in IGNORE_S3_DROP_IN_EXCEPTIONS:
            module.warn("PutBucketAcl is not implemented by your storage provider. Set the permission parameters to the empty list to avoid this warning")
        else:
            module.fail_json_aws(e, msg="Failed while creating bucket or setting acl (check that you have CreateBucket and PutBucketAcl permission).")
    except botocore.exceptions.BotoCoreError as e:
        module.fail_json_aws(e, msg="Failed while creating bucket or setting acl (check that you have CreateBucket and PutBucketAcl permission).")

    if bucket:
        return True


def paginated_list(s3, **pagination_params):
    pg = s3.get_paginator('list_objects_v2')
    for page in pg.paginate(**pagination_params):
        yield [data['Key'] for data in page.get('Contents', [])]


def list_keys(module, s3, bucket, prefix, marker, max_keys):
    pagination_params = {'Bucket': bucket}
    for param_name, param_value in (('Prefix', prefix), ('StartAfter', marker), ('MaxKeys', max_keys)):
        pagination_params[param_name] = param_value
    try:
        keys = sum(paginated_list(s3, **pagination_params), [])
        module.exit_json(msg="LIST operation complete", s3_keys=keys)
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed while listing the keys in the bucket {0}".format(bucket))


def delete_bucket(module, s3, bucket):
    if module.check_mode:
        module.exit_json(msg="DELETE operation skipped - running in check mode", changed=True)
    try:
        exists = bucket_check(module, s3, bucket)
        if exists is False:
            return False
        # if there are contents then we need to delete them before we can delete the bucket
        for keys in paginated_list(s3, Bucket=bucket):
            formatted_keys = [{'Key': key} for key in keys]
            if formatted_keys:
                s3.delete_objects(Bucket=bucket, Delete={'Objects': formatted_keys})
        s3.delete_bucket(Bucket=bucket)
        return True
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed while deleting bucket %s." % bucket)


def delete_key(module, s3, bucket, obj):
    if module.check_mode:
        module.exit_json(msg="DELETE operation skipped - running in check mode", changed=True)
    try:
        s3.delete_object(Bucket=bucket, Key=obj)
        module.exit_json(msg="Object deleted from bucket %s." % (bucket), changed=True)
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed while trying to delete %s." % obj)


def create_dirkey(module, s3, bucket, obj, encrypt):
    if module.check_mode:
        module.exit_json(msg="PUT operation skipped - running in check mode", changed=True)
    try:
        params = {'Bucket': bucket, 'Key': obj, 'Body': b''}
        if encrypt:
            params['ServerSideEncryption'] = module.params['encryption_mode']
        if module.params['encryption_kms_key_id'] and module.params['encryption_mode'] == 'aws:kms':
            params['SSEKMSKeyId'] = module.params['encryption_kms_key_id']

        s3.put_object(**params)
        for acl in module.params.get('permission'):
            s3.put_object_acl(ACL=acl, Bucket=bucket, Key=obj)
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] in IGNORE_S3_DROP_IN_EXCEPTIONS:
            module.warn("PutObjectAcl is not implemented by your storage provider. Set the permissions parameters to the empty list to avoid this warning")
        else:
            module.fail_json_aws(e, msg="Failed while creating object %s." % obj)
    except botocore.exceptions.BotoCoreError as e:
        module.fail_json_aws(e, msg="Failed while creating object %s." % obj)
    module.exit_json(msg="Virtual directory %s created in bucket %s" % (obj, bucket), changed=True)


def path_check(path):
    if os.path.exists(path):
        return True
    else:
        return False


def option_in_extra_args(option):
    temp_option = option.replace('-', '').lower()

    allowed_extra_args = {'acl': 'ACL', 'cachecontrol': 'CacheControl', 'contentdisposition': 'ContentDisposition',
                          'contentencoding': 'ContentEncoding', 'contentlanguage': 'ContentLanguage',
                          'contenttype': 'ContentType', 'expires': 'Expires', 'grantfullcontrol': 'GrantFullControl',
                          'grantread': 'GrantRead', 'grantreadacp': 'GrantReadACP', 'grantwriteacp': 'GrantWriteACP',
                          'metadata': 'Metadata', 'requestpayer': 'RequestPayer', 'serversideencryption': 'ServerSideEncryption',
                          'storageclass': 'StorageClass', 'ssecustomeralgorithm': 'SSECustomerAlgorithm', 'ssecustomerkey': 'SSECustomerKey',
                          'ssecustomerkeymd5': 'SSECustomerKeyMD5', 'ssekmskeyid': 'SSEKMSKeyId', 'websiteredirectlocation': 'WebsiteRedirectLocation'}

    if temp_option in allowed_extra_args:
        return allowed_extra_args[temp_option]


def upload_s3file(module, s3, bucket, obj, src, expiry, metadata, encrypt, headers):
    if module.check_mode:
        module.exit_json(msg="PUT operation skipped - running in check mode", changed=True)
    try:
        extra = {}
        if encrypt:
            extra['ServerSideEncryption'] = module.params['encryption_mode']
        if module.params['encryption_kms_key_id'] and module.params['encryption_mode'] == 'aws:kms':
            extra['SSEKMSKeyId'] = module.params['encryption_kms_key_id']
        if metadata:
            extra['Metadata'] = {}

            # determine object metadata and extra arguments
            for option in metadata:
                extra_args_option = option_in_extra_args(option)
                if extra_args_option is not None:
                    extra[extra_args_option] = metadata[option]
                else:
                    extra['Metadata'][option] = metadata[option]

        if 'ContentType' not in extra:
            content_type = mimetypes.guess_type(src)[0]
            if content_type is None:
                # s3 default content type
                content_type = 'binary/octet-stream'
            extra['ContentType'] = content_type

        s3.upload_file(Filename=src, Bucket=bucket, Key=obj, ExtraArgs=extra)
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Unable to complete PUT operation.")
    try:
        for acl in module.params.get('permission'):
            s3.put_object_acl(ACL=acl, Bucket=bucket, Key=obj)
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] in IGNORE_S3_DROP_IN_EXCEPTIONS:
            module.warn("PutObjectAcl is not implemented by your storage provider. Set the permission parameters to the empty list to avoid this warning")
        else:
            module.fail_json_aws(e, msg="Unable to set object ACL")
    except botocore.exceptions.BotoCoreError as e:
        module.fail_json_aws(e, msg="Unable to set object ACL")
    try:
        url = s3.generate_presigned_url(ClientMethod='put_object',
                                        Params={'Bucket': bucket, 'Key': obj},
                                        ExpiresIn=expiry)
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Unable to generate presigned URL")
    module.exit_json(msg="PUT operation complete", url=url, changed=True)


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
        if e.response['Error']['Code'] == 'InvalidArgument' and 'require AWS Signature Version 4' in to_text(e):
            raise Sigv4Required()
        elif e.response['Error']['Code'] not in ("403", "404"):
            # AccessDenied errors may be triggered if 1) file does not exist or 2) file exists but
            # user does not have the s3:GetObject permission. 404 errors are handled by download_file().
            module.fail_json_aws(e, msg="Could not find the key %s." % obj)
    except botocore.exceptions.BotoCoreError as e:
        module.fail_json_aws(e, msg="Could not find the key %s." % obj)

    for x in range(0, retries + 1):
        try:
            s3.download_file(bucket, obj, dest)
            module.exit_json(msg="GET operation complete", changed=True)
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            # actually fail on last pass through the loop.
            if x >= retries:
                module.fail_json_aws(e, msg="Failed while downloading %s." % obj)
            # otherwise, try again, this may be a transient timeout.
        except SSLError as e:  # will ClientError catch SSLError?
            # actually fail on last pass through the loop.
            if x >= retries:
                module.fail_json_aws(e, msg="s3 download failed")
            # otherwise, try again, this may be a transient timeout.


def download_s3str(module, s3, bucket, obj, version=None, validate=True):
    if module.check_mode:
        module.exit_json(msg="GET operation skipped - running in check mode", changed=True)
    try:
        if version:
            contents = to_native(s3.get_object(Bucket=bucket, Key=obj, VersionId=version)["Body"].read())
        else:
            contents = to_native(s3.get_object(Bucket=bucket, Key=obj)["Body"].read())
        module.exit_json(msg="GET operation complete", contents=contents, changed=True)
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == 'InvalidArgument' and 'require AWS Signature Version 4' in to_text(e):
            raise Sigv4Required()
        else:
            module.fail_json_aws(e, msg="Failed while getting contents of object %s as a string." % obj)
    except botocore.exceptions.BotoCoreError as e:
        module.fail_json_aws(e, msg="Failed while getting contents of object %s as a string." % obj)


def get_download_url(module, s3, bucket, obj, expiry, changed=True):
    try:
        url = s3.generate_presigned_url(ClientMethod='get_object',
                                        Params={'Bucket': bucket, 'Key': obj},
                                        ExpiresIn=expiry)
        module.exit_json(msg="Download url:", url=url, expiry=expiry, changed=changed)
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed while getting download url.")


def is_fakes3(s3_url):
    """ Return True if s3_url has scheme fakes3:// """
    if s3_url is not None:
        return urlparse(s3_url).scheme in ('fakes3', 'fakes3s')
    else:
        return False


def get_s3_connection(module, aws_connect_kwargs, location, rgw, s3_url, sig_4=False):
    if s3_url and rgw:  # TODO - test this
        rgw = urlparse(s3_url)
        params = dict(module=module, conn_type='client', resource='s3', use_ssl=rgw.scheme == 'https', region=location, endpoint=s3_url, **aws_connect_kwargs)
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
        if module.params['mode'] == 'put' and module.params['encryption_mode'] == 'aws:kms':
            params['config'] = botocore.client.Config(signature_version='s3v4')
        elif module.params['mode'] in ('get', 'getstr') and sig_4:
            params['config'] = botocore.client.Config(signature_version='s3v4')
    return boto3_conn(**params)


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(
        dict(
            bucket=dict(required=True),
            dest=dict(default=None, type='path'),
            encrypt=dict(default=True, type='bool'),
            encryption_mode=dict(choices=['AES256', 'aws:kms'], default='AES256'),
            expiry=dict(default=600, type='int', aliases=['expiration']),
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
            ignore_nonexistent_bucket=dict(default=False, type='bool'),
            encryption_kms_key_id=dict()
        ),
    )
    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=[['mode', 'put', ['src', 'object']],
                     ['mode', 'get', ['dest', 'object']],
                     ['mode', 'getstr', ['object']],
                     ['mode', 'geturl', ['object']]],
    )

    if module._name == 's3':
        module.deprecate("The 's3' module is being renamed 'aws_s3'", version=2.7)

    bucket = module.params.get('bucket')
    encrypt = module.params.get('encrypt')
    expiry = module.params.get('expiry')
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

    object_canned_acl = ["private", "public-read", "public-read-write", "aws-exec-read", "authenticated-read", "bucket-owner-read", "bucket-owner-full-control"]
    bucket_canned_acl = ["private", "public-read", "public-read-write", "authenticated-read"]

    if overwrite not in ['always', 'never', 'different']:
        if module.boolean(overwrite):
            overwrite = 'always'
        else:
            overwrite = 'never'

    region, ec2_url, aws_connect_kwargs = get_aws_connection_info(module, boto3=True)

    if region in ('us-east-1', '', None):
        # default to US Standard region
        location = 'us-east-1'
    else:
        # Boto uses symbolic names for locations but region strings will
        # actually work fine for everything except us-east-1 (US Standard)
        location = region

    if module.params.get('object'):
        obj = module.params['object']
        # If there is a top level object, do nothing - if the object starts with /
        # remove the leading character to maintain compatibility with Ansible versions < 2.4
        if obj.startswith('/'):
            obj = obj[1:]

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
    if s3_url:
        for key in ['validate_certs', 'security_token', 'profile_name']:
            aws_connect_kwargs.pop(key, None)
    s3 = get_s3_connection(module, aws_connect_kwargs, location, rgw, s3_url)

    validate = not ignore_nonexistent_bucket

    # separate types of ACLs
    bucket_acl = [acl for acl in module.params.get('permission') if acl in bucket_canned_acl]
    object_acl = [acl for acl in module.params.get('permission') if acl in object_canned_acl]
    error_acl = [acl for acl in module.params.get('permission') if acl not in bucket_canned_acl and acl not in object_canned_acl]
    if error_acl:
        module.fail_json(msg='Unknown permission specified: %s' % error_acl)

    # First, we check to see if the bucket exists, we get "bucket" returned.
    bucketrtn = bucket_check(module, s3, bucket, validate=validate)

    if validate and mode not in ('create', 'put', 'delete') and not bucketrtn:
        module.fail_json(msg="Source bucket cannot be found.")

    # If our mode is a GET operation (download), go through the procedure as appropriate ...
    if mode == 'get':
        # Next, we check to see if the key in the bucket exists. If it exists, it also returns key_matches md5sum check.
        keyrtn = key_check(module, s3, bucket, obj, version=version, validate=validate)
        if keyrtn is False:
            if version:
                module.fail_json(msg="Key %s with version id %s does not exist." % (obj, version))
            else:
                module.fail_json(msg="Key %s does not exist." % obj)

        # If the destination path doesn't exist or overwrite is True, no need to do the md5sum ETag check, so just download.
        # Compare the remote MD5 sum of the object with the local dest md5sum, if it already exists.
        if path_check(dest):
            # Determine if the remote and local object are identical
            if keysum_compare(module, dest, s3, bucket, obj, version=version):
                sum_matches = True
                if overwrite == 'always':
                    try:
                        download_s3file(module, s3, bucket, obj, dest, retries, version=version)
                    except Sigv4Required:
                        s3 = get_s3_connection(module, aws_connect_kwargs, location, rgw, s3_url, sig_4=True)
                        download_s3file(module, s3, bucket, obj, dest, retries, version=version)
                else:
                    module.exit_json(msg="Local and remote object are identical, ignoring. Use overwrite=always parameter to force.", changed=False)
            else:
                sum_matches = False

                if overwrite in ('always', 'different'):
                    try:
                        download_s3file(module, s3, bucket, obj, dest, retries, version=version)
                    except Sigv4Required:
                        s3 = get_s3_connection(module, aws_connect_kwargs, location, rgw, s3_url, sig_4=True)
                        download_s3file(module, s3, bucket, obj, dest, retries, version=version)
                else:
                    module.exit_json(msg="WARNING: Checksums do not match. Use overwrite parameter to force download.")
        else:
            try:
                download_s3file(module, s3, bucket, obj, dest, retries, version=version)
            except Sigv4Required:
                s3 = get_s3_connection(module, aws_connect_kwargs, location, rgw, s3_url, sig_4=True)
                download_s3file(module, s3, bucket, obj, dest, retries, version=version)

    # if our mode is a PUT operation (upload), go through the procedure as appropriate ...
    if mode == 'put':

        # if putting an object in a bucket yet to be created, acls for the bucket and/or the object may be specified
        # these were separated into the variables bucket_acl and object_acl above

        # Lets check the src path.
        if not path_check(src):
            module.fail_json(msg="Local object for PUT does not exist")

        # Lets check to see if bucket exists to get ground truth.
        if bucketrtn:
            keyrtn = key_check(module, s3, bucket, obj, version=version, validate=validate)

        # Lets check key state. Does it exist and if it does, compute the ETag md5sum.
        if bucketrtn and keyrtn:
            # Compare the local and remote object
            if keysum_compare(module, src, s3, bucket, obj):
                sum_matches = True
                if overwrite == 'always':
                    # only use valid object acls for the upload_s3file function
                    module.params['permission'] = object_acl
                    upload_s3file(module, s3, bucket, obj, src, expiry, metadata, encrypt, headers)
                else:
                    get_download_url(module, s3, bucket, obj, expiry, changed=False)
            else:
                sum_matches = False
                if overwrite in ('always', 'different'):
                    # only use valid object acls for the upload_s3file function
                    module.params['permission'] = object_acl
                    upload_s3file(module, s3, bucket, obj, src, expiry, metadata, encrypt, headers)
                else:
                    module.exit_json(msg="WARNING: Checksums do not match. Use overwrite parameter to force upload.")

        # If neither exist (based on bucket existence), we can create both.
        if not bucketrtn:
            # only use valid bucket acls for create_bucket function
            module.params['permission'] = bucket_acl
            create_bucket(module, s3, bucket, location)
            # only use valid object acls for the upload_s3file function
            module.params['permission'] = object_acl
            upload_s3file(module, s3, bucket, obj, src, expiry, metadata, encrypt, headers)

        # If bucket exists but key doesn't, just upload.
        if bucketrtn and not keyrtn:
            # only use valid object acls for the upload_s3file function
            module.params['permission'] = object_acl
            upload_s3file(module, s3, bucket, obj, src, expiry, metadata, encrypt, headers)

    # Delete an object from a bucket, not the entire bucket
    if mode == 'delobj':
        if obj is None:
            module.fail_json(msg="object parameter is required")
        if bucket:
            deletertn = delete_key(module, s3, bucket, obj)
            if deletertn is True:
                module.exit_json(msg="Object deleted from bucket %s." % bucket, changed=True)
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
        # these were separated above into the variables bucket_acl and object_acl

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
                if key_check(module, s3, bucket, dirobj):
                    module.exit_json(msg="Bucket %s and key %s already exists." % (bucket, obj), changed=False)
                else:
                    # setting valid object acls for the create_dirkey function
                    module.params['permission'] = object_acl
                    create_dirkey(module, s3, bucket, dirobj, encrypt)
            else:
                # only use valid bucket acls for the create_bucket function
                module.params['permission'] = bucket_acl
                created = create_bucket(module, s3, bucket, location)
                # only use valid object acls for the create_dirkey function
                module.params['permission'] = object_acl
                create_dirkey(module, s3, bucket, dirobj, encrypt)

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
                try:
                    download_s3str(module, s3, bucket, obj, version=version)
                except Sigv4Required:
                    s3 = get_s3_connection(module, aws_connect_kwargs, location, rgw, s3_url, sig_4=True)
                    download_s3str(module, s3, bucket, obj, version=version)
            elif version is not None:
                module.fail_json(msg="Key %s with version id %s does not exist." % (obj, version))
            else:
                module.fail_json(msg="Key %s does not exist." % obj)

    module.exit_json(failed=False)


if __name__ == '__main__':
    main()
