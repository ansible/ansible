#!/usr/bin/python
# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

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
  bucket:
    description:
      - Bucket name.
    required: true
    type: str
  dest:
    description:
      - The destination file path when downloading an object/key with a GET operation.
    version_added: "1.3"
    type: path
  encrypt:
    description:
      - When set for PUT mode, asks for server-side encryption.
    default: true
    version_added: "2.0"
    type: bool
  encryption_mode:
    description:
      - What encryption mode to use if I(encrypt=true).
    default: AES256
    choices:
      - AES256
      - aws:kms
    version_added: "2.7"
    type: str
  expiry:
    description:
      - Time limit (in seconds) for the URL generated and returned by S3/Walrus when performing a I(mode=put) or I(mode=geturl) operation.
    default: 600
    aliases: ['expiration']
    type: int
  headers:
    description:
      - Custom headers for PUT operation, as a dictionary of 'key=value' and 'key=value,key=value'.
    version_added: "2.0"
    type: dict
  marker:
    description:
      - Specifies the key to start with when using list mode. Object keys are returned in alphabetical order, starting with key after the marker in order.
    version_added: "2.0"
    type: str
  max_keys:
    description:
      - Max number of results to return in list mode, set this if you want to retrieve fewer than the default 1000 keys.
    default: 1000
    version_added: "2.0"
    type: int
  metadata:
    description:
      - Metadata for PUT operation, as a dictionary of 'key=value' and 'key=value,key=value'.
    version_added: "1.6"
    type: dict
  mode:
    description:
      - Switches the module behaviour between put (upload), get (download), geturl (return download url, Ansible 1.3+),
        getstr (download object as string (1.3+)), list (list keys, Ansible 2.0+), create (bucket), delete (bucket),
        and delobj (delete object, Ansible 2.0+).
    required: true
    choices: ['get', 'put', 'delete', 'create', 'geturl', 'getstr', 'delobj', 'list']
    type: str
  object:
    description:
      - Keyname of the object inside the bucket. Can be used to create "virtual directories", see examples.
    type: str
  permission:
    description:
      - This option lets the user set the canned permissions on the object/bucket that are created.
        The permissions that can be set are C(private), C(public-read), C(public-read-write), C(authenticated-read) for a bucket or
        C(private), C(public-read), C(public-read-write), C(aws-exec-read), C(authenticated-read), C(bucket-owner-read),
        C(bucket-owner-full-control) for an object. Multiple permissions can be specified as a list.
    default: ['private']
    version_added: "2.0"
    type: list
    elements: str
  prefix:
    description:
      - Limits the response to keys that begin with the specified prefix for list mode.
    default: ""
    version_added: "2.0"
    type: str
  version:
    description:
      - Version ID of the object inside the bucket. Can be used to get a specific version of a file if versioning is enabled in the target bucket.
    version_added: "2.0"
    type: str
  overwrite:
    description:
      - Force overwrite either locally on the filesystem or remotely with the object/key. Used with PUT and GET operations.
        Boolean or one of [always, never, different], true is equal to 'always' and false is equal to 'never', new in 2.0.
        When this is set to 'different', the md5 sum of the local file is compared with the 'ETag' of the object/key in S3.
        The ETag may or may not be an MD5 digest of the object data. See the ETag response header here
        U(https://docs.aws.amazon.com/AmazonS3/latest/API/RESTCommonResponseHeaders.html)
    default: 'always'
    aliases: ['force']
    version_added: "1.2"
    type: str
  retries:
    description:
     - On recoverable failure, how many times to retry before actually failing.
    default: 0
    version_added: "2.0"
    type: int
    aliases: ['retry']
  s3_url:
    description:
      - S3 URL endpoint for usage with Ceph, Eucalyptus and fakes3 etc. Otherwise assumes AWS.
    aliases: [ S3_URL ]
    type: str
  dualstack:
    description:
      - Enables Amazon S3 Dual-Stack Endpoints, allowing S3 communications using both IPv4 and IPv6.
      - Requires at least botocore version 1.4.45.
    type: bool
    default: false
    version_added: "2.7"
  rgw:
    description:
      - Enable Ceph RGW S3 support. This option requires an explicit url via I(s3_url).
    default: false
    version_added: "2.2"
    type: bool
  src:
    description:
      - The source file path when performing a PUT operation.
    version_added: "1.3"
    type: str
  ignore_nonexistent_bucket:
    description:
      - "Overrides initial bucket lookups in case bucket or iam policies are restrictive. Example: a user may have the
        GetObject permission but no other permissions. In this case using the option mode: get will fail without specifying
        I(ignore_nonexistent_bucket=true)."
    version_added: "2.3"
    type: bool
  encryption_kms_key_id:
    description:
      - KMS key id to use when encrypting objects using I(encrypting=aws:kms). Ignored if I(encryption) is not C(aws:kms)
    version_added: "2.7"
    type: str
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
  description: Message indicating the status of the operation.
  returned: always
  type: str
  sample: PUT operation complete
url:
  description: URL of the object.
  returned: (for put and geturl operations)
  type: str
  sample: https://my-bucket.s3.amazonaws.com/my-key.txt?AWSAccessKeyId=<access-key>&Expires=1506888865&Signature=<signature>
expiry:
  description: Number of seconds the presigned url is valid for.
  returned: (for geturl operation)
  type: int
  sample: 600
contents:
  description: Contents of the object as string.
  returned: (for getstr operation)
  type: str
  sample: "Hello, world!"
s3_keys:
  description: List of object keys.
  returned: (for list operation)
  type: list
  elements: str
  sample:
  - prefix1/
  - prefix1/key1
  - prefix1/key2
'''

import mimetypes
import os
from ansible.module_utils.six.moves.urllib.parse import urlparse
from ssl import SSLError
from ansible.module_utils.basic import to_text, to_native
from ansible.module_utils.aws.core import AnsibleAWSModule
from ansible.module_utils.aws.s3 import calculate_etag, HAS_MD5
from ansible.module_utils.ec2 import get_aws_connection_info, boto3_conn

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


def etag_compare(module, local_file, s3, bucket, obj, version=None):
    s3_etag = get_etag(s3, bucket, obj, version=version)
    local_etag = calculate_etag(module, local_file, s3_etag, s3, bucket, obj, version)

    return s3_etag == local_etag


def get_etag(s3, bucket, obj, version=None):
    if version:
        key_check = s3.head_object(Bucket=bucket, Key=obj, VersionId=version)
    else:
        key_check = s3.head_object(Bucket=bucket, Key=obj)
    if not key_check:
        return None
    return key_check['ETag']


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
        if module.params.get('permission'):
            # Wait for the bucket to exist before setting ACLs
            s3.get_waiter('bucket_exists').wait(Bucket=bucket)
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


def paginated_versioned_list_with_fallback(s3, **pagination_params):
    try:
        versioned_pg = s3.get_paginator('list_object_versions')
        for page in versioned_pg.paginate(**pagination_params):
            delete_markers = [{'Key': data['Key'], 'VersionId': data['VersionId']} for data in page.get('DeleteMarkers', [])]
            current_objects = [{'Key': data['Key'], 'VersionId': data['VersionId']} for data in page.get('Versions', [])]
            yield delete_markers + current_objects
    except botocore.exceptions.ClientError as e:
        if to_text(e.response['Error']['Code']) in IGNORE_S3_DROP_IN_EXCEPTIONS + ['AccessDenied']:
            for page in paginated_list(s3, **pagination_params):
                yield [{'Key': data['Key']} for data in page]


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
        for keys in paginated_versioned_list_with_fallback(s3, Bucket=bucket):
            if keys:
                s3.delete_objects(Bucket=bucket, Delete={'Objects': keys})
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

    optional_kwargs = {'ExtraArgs': {'VersionId': version}} if version else {}
    for x in range(0, retries + 1):
        try:
            s3.download_file(bucket, obj, dest, **optional_kwargs)
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
        if module.params['dualstack']:
            dualconf = botocore.client.Config(s3={'use_dualstack_endpoint': True})
            if 'config' in params:
                params['config'] = params['config'].merge(dualconf)
            else:
                params['config'] = dualconf
    return boto3_conn(**params)


def main():
    argument_spec = dict(
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
        dualstack=dict(default='no', type='bool'),
        rgw=dict(default='no', type='bool'),
        src=dict(),
        ignore_nonexistent_bucket=dict(default=False, type='bool'),
        encryption_kms_key_id=dict()
    )
    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=[['mode', 'put', ['src', 'object']],
                     ['mode', 'get', ['dest', 'object']],
                     ['mode', 'getstr', ['object']],
                     ['mode', 'geturl', ['object']]],
    )

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
    dualstack = module.params.get('dualstack')
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

    if overwrite == 'different' and not HAS_MD5:
        module.fail_json(msg='overwrite=different is unavailable: ETag calculation requires MD5 support')

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

    if dualstack and s3_url is not None and 'amazonaws.com' not in s3_url:
        module.fail_json(msg='dualstack only applies to AWS S3')

    if dualstack and not module.botocore_at_least('1.4.45'):
        module.fail_json(msg='dualstack requires botocore >= 1.4.45')

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

    if mode == 'get':
        keyrtn = key_check(module, s3, bucket, obj, version=version, validate=validate)
        if keyrtn is False:
            if version:
                module.fail_json(msg="Key %s with version id %s does not exist." % (obj, version))
            else:
                module.fail_json(msg="Key %s does not exist." % obj)

        if path_check(dest) and overwrite != 'always':
            if overwrite == 'never':
                module.exit_json(msg="Local object already exists and overwrite is disabled.", changed=False)
            if etag_compare(module, dest, s3, bucket, obj, version=version):
                module.exit_json(msg="Local and remote object are identical, ignoring. Use overwrite=always parameter to force.", changed=False)

        try:
            download_s3file(module, s3, bucket, obj, dest, retries, version=version)
        except Sigv4Required:
            s3 = get_s3_connection(module, aws_connect_kwargs, location, rgw, s3_url, sig_4=True)
            download_s3file(module, s3, bucket, obj, dest, retries, version=version)

    if mode == 'put':

        # if putting an object in a bucket yet to be created, acls for the bucket and/or the object may be specified
        # these were separated into the variables bucket_acl and object_acl above

        if not path_check(src):
            module.fail_json(msg="Local object for PUT does not exist")

        if bucketrtn:
            keyrtn = key_check(module, s3, bucket, obj, version=version, validate=validate)
        else:
            # If the bucket doesn't exist we should create it.
            # only use valid bucket acls for create_bucket function
            module.params['permission'] = bucket_acl
            create_bucket(module, s3, bucket, location)

        if keyrtn and overwrite != 'always':
            if overwrite == 'never' or etag_compare(module, src, s3, bucket, obj):
                # Return the download URL for the existing object
                get_download_url(module, s3, bucket, obj, expiry, changed=False)

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
