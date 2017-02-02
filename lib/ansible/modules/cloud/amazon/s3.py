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
    - This module allows the user to manage S3 buckets and the objects within them. Includes support for creating and deleting both objects and buckets,
      retrieving objects as files or strings and generating download links. This module has a dependency on python-boto.
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
        getstr (download object as string (1.3+)), list (list keys, Ansible 2.0+), create (bucket), delete (bucket), and delobj (delete object, Ansible 2.0+).
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
        The permissions that can be set are 'private', 'public-read', 'public-read-write', 'authenticated-read'. Multiple permissions can be
        specified as a list.
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
     - >
       AWS region to create the bucket in. If not set then the value of the AWS_REGION and EC2_REGION environment variables are checked,
       followed by the aws_region and ec2_region settings in the Boto config file.  If none of those are set the region defaults to the
       S3 Location: US Standard.  Prior to ansible 1.8 this parameter could be specified but had no effect.
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
      - >
        Overrides initial bucket lookups in case bucket or iam policies are restrictive. Example: a user may have the GetObject permission but no other
        permissions. In this case using the option mode: get will fail without specifying ignore_nonexistent_bucket: True.
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

- name: GET an object but don't download if the file checksums match. New in 2.0
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

try:
    import boto
    import boto.ec2
    from boto.s3.connection import Location
    from boto.s3.connection import OrdinaryCallingFormat
    from boto.s3.connection import S3Connection
    from boto.s3.acl import CannedACLStrings
    HAS_BOTO = True
except ImportError:
    HAS_BOTO = False

def key_check(module, s3, bucket, obj, version=None, validate=True):
    try:
        bucket = s3.lookup(bucket, validate=validate)
        key_check = bucket.get_key(obj, version_id=version)
    except s3.provider.storage_response_error as e:
        if version is not None and e.status == 400: # If a specified version doesn't exist a 400 is returned.
            key_check = None
        else:
            module.fail_json(msg=str(e))
    if key_check:
        return True
    else:
        return False

def keysum(module, s3, bucket, obj, version=None, validate=True):
    bucket = s3.lookup(bucket, validate=validate)
    key_check = bucket.get_key(obj, version_id=version)
    if not key_check:
        return None
    md5_remote = key_check.etag[1:-1]
    etag_multipart = '-' in md5_remote # Check for multipart, etag is not md5
    if etag_multipart is True:
        module.fail_json(msg="Files uploaded with multipart of s3 are not supported with checksum, unable to compute checksum.")
    return md5_remote

def bucket_check(module, s3, bucket, validate=True):
    try:
        result = s3.lookup(bucket, validate=validate)
    except s3.provider.storage_response_error as e:
        module.fail_json(msg="Failed while looking up bucket (during bucket_check) %s: %s" % (bucket, e),
                exception=traceback.format_exc())
    return bool(result)

def create_bucket(module, s3, bucket, location=None):
    if module.check_mode:
        module.exit_json(msg="PUT operation skipped - running in check mode", changed=True)
    if location is None:
        location = Location.DEFAULT
    try:
        bucket = s3.create_bucket(bucket, location=location)
        for acl in module.params.get('permission'):
            bucket.set_acl(acl)
    except s3.provider.storage_response_error as e:
        module.fail_json(msg="Failed while creating bucket or setting acl (check that you have CreateBucket and PutBucketAcl permission) %s: %s" % (bucket, e),
                exception=traceback.format_exc())
    if bucket:
        return True

def get_bucket(module, s3, bucket):
    try:
        return s3.lookup(bucket)
    except s3.provider.storage_response_error as e:
        module.fail_json(msg="Failed while getting bucket %s: %s" % (bucket, e),
                exception=traceback.format_exc())

def list_keys(module, bucket_object, prefix, marker, max_keys):
    all_keys = bucket_object.get_all_keys(prefix=prefix, marker=marker, max_keys=max_keys)

    keys = [x.key for x in all_keys]

    module.exit_json(msg="LIST operation complete", s3_keys=keys)

def delete_bucket(module, s3, bucket):
    if module.check_mode:
        module.exit_json(msg="DELETE operation skipped - running in check mode", changed=True)
    try:
        bucket = s3.lookup(bucket, validate=False)
        bucket_contents = bucket.list()
        bucket.delete_keys([key.name for key in bucket_contents])
    except s3.provider.storage_response_error as e:
        if e.status == 404:
            # bucket doesn't appear to exist
            return False
        elif e.status == 403:
            # bucket appears to exist but user doesn't have list bucket permission; may still be able to delete bucket
            pass
        else:
            module.fail_json(msg=str(e), exception=traceback.format_exc())
    try:
        bucket.delete()
        return True
    except s3.provider.storage_response_error as e:
        if e.status == 403:
            module.exit_json(msg="Unable to complete DELETE operation. Check you have have s3:DeleteBucket "
                             "permission. Error: {0}.".format(e.message),
                             exception=traceback.format_exc())
        elif e.status == 409:
            module.exit_json(msg="Unable to complete DELETE operation. It appears there are contents in the "
                             "bucket that you don't have permission to delete. Error: {0}.".format(e.message),
                             exception=traceback.format_exc())
        else:
            module.fail_json(msg=str(e), exception=traceback.format_exc())

def delete_key(module, s3, bucket, obj, validate=True):
    if module.check_mode:
        module.exit_json(msg="DELETE operation skipped - running in check mode", changed=True)
    try:
        bucket = s3.lookup(bucket, validate=validate)
        bucket.delete_key(obj)
        module.exit_json(msg="Object deleted from bucket %s"%bucket, changed=True)
    except s3.provider.storage_response_error as e:
        module.fail_json(msg= str(e))

def create_dirkey(module, s3, bucket, obj, validate=True):
    if module.check_mode:
        module.exit_json(msg="PUT operation skipped - running in check mode", changed=True)
    try:
        bucket = s3.lookup(bucket, validate=validate)
        key = bucket.new_key(obj)
        key.set_contents_from_string('')
        module.exit_json(msg="Virtual directory %s created in bucket %s" % (obj, bucket.name), changed=True)
    except s3.provider.storage_response_error as e:
        module.fail_json(msg= str(e))

def path_check(path):
    if os.path.exists(path):
        return True
    else:
        return False


def upload_s3file(module, s3, bucket, obj, src, expiry, metadata, encrypt, headers, validate=True):
    if module.check_mode:
        module.exit_json(msg="PUT operation skipped - running in check mode", changed=True)
    try:
        bucket = s3.lookup(bucket, validate=validate)
        key = bucket.new_key(obj)
        if metadata:
            for meta_key in metadata.keys():
                key.set_metadata(meta_key, metadata[meta_key])

        key.set_contents_from_filename(src, encrypt_key=encrypt, headers=headers)
        for acl in module.params.get('permission'):
            key.set_acl(acl)
        url = key.generate_url(expiry)
        module.exit_json(msg="PUT operation complete", url=url, changed=True)
    except s3.provider.storage_copy_error as e:
        module.fail_json(msg= str(e))

def download_s3file(module, s3, bucket, obj, dest, retries, version=None, validate=True):
    if module.check_mode:
        module.exit_json(msg="GET operation skipped - running in check mode", changed=True)
    # retries is the number of loops; range/xrange needs to be one
    # more to get that count of loops.
    bucket = s3.lookup(bucket, validate=validate)
    key = bucket.get_key(obj, version_id=version)
    for x in range(0, retries + 1):
        try:
            key.get_contents_to_filename(dest)
            module.exit_json(msg="GET operation complete", changed=True)
        except s3.provider.storage_copy_error as e:
            module.fail_json(msg= str(e))
        except SSLError as e:
            # actually fail on last pass through the loop.
            if x >= retries:
                module.fail_json(msg="s3 download failed; %s" % e)
            # otherwise, try again, this may be a transient timeout.
            pass

def download_s3str(module, s3, bucket, obj, version=None, validate=True):
    if module.check_mode:
        module.exit_json(msg="GET operation skipped - running in check mode", changed=True)
    try:
        bucket = s3.lookup(bucket, validate=validate)
        key = bucket.get_key(obj, version_id=version)
        contents = key.get_contents_as_string()
        module.exit_json(msg="GET operation complete", contents=contents, changed=True)
    except s3.provider.storage_copy_error as e:
        module.fail_json(msg= str(e))

def get_download_url(module, s3, bucket, obj, expiry, changed=True, validate=True):
    try:
        bucket = s3.lookup(bucket, validate=validate)
        key = bucket.lookup(obj)
        url = key.generate_url(expiry)
        module.exit_json(msg="Download url:", url=url, expiry=expiry, changed=changed)
    except s3.provider.storage_response_error as e:
        module.fail_json(msg= str(e))

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
    argument_spec.update(dict(
        bucket                          = dict(required=True),
        dest                            = dict(default=None),
        encrypt                         = dict(default=True, type='bool'),
        expiry                          = dict(default=600, aliases=['expiration']),
        headers                         = dict(type='dict'),
        marker                          = dict(default=None),
        max_keys                        = dict(default=1000),
        metadata                        = dict(type='dict'),
        mode                            = dict(choices=['get', 'put', 'delete', 'create', 'geturl', 'getstr', 'delobj', 'list'], required=True),
        object                          = dict(),
        permission                      = dict(type='list', default=['private']),
        version                         = dict(default=None),
        overwrite                       = dict(aliases=['force'], default='always'),
        prefix                          = dict(default=None),
        retries                         = dict(aliases=['retry'], type='int', default=0),
        s3_url                          = dict(aliases=['S3_URL']),
        rgw                             = dict(default='no', type='bool'),
        src                             = dict(),
        ignore_nonexistent_bucket       = dict(default=False, type='bool')
        ),
    )
    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    if not HAS_BOTO:
        module.fail_json(msg='boto required for this module')

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

    for acl in module.params.get('permission'):
        if acl not in CannedACLStrings:
            module.fail_json(msg='Unknown permission specified: %s' % str(acl))

    if overwrite not in ['always', 'never', 'different']:
        if module.boolean(overwrite):
            overwrite = 'always'
        else:
            overwrite = 'never'

    region, ec2_url, aws_connect_kwargs = get_aws_connection_info(module)

    if region in ('us-east-1', '', None):
        # S3ism for the US Standard region
        location = Location.DEFAULT
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

    # bucket names with .'s in them need to use the calling_format option,
    # otherwise the connection will fail. See https://github.com/boto/boto/issues/2836
    # for more details.
    if '.' in bucket:
        aws_connect_kwargs['calling_format'] = OrdinaryCallingFormat()

    # Look at s3_url and tweak connection settings
    # if connecting to RGW, Walrus or fakes3
    try:
        s3 = get_s3_connection(aws_connect_kwargs, location, rgw, s3_url)

    except boto.exception.NoAuthHandlerFound as e:
        module.fail_json(msg='No Authentication Handler found: %s ' % str(e))
    except Exception as e:
        module.fail_json(msg='Failed to connect to S3: %s' % str(e))

    if s3 is None: # this should never happen
        module.fail_json(msg ='Unknown error, failed to create s3 connection, no information from boto.')

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
                module.fail_json(msg="Key %s with version id %s does not exist."% (obj, version))
            else:
                module.fail_json(msg="Key %s or source bucket %s does not exist."% (obj, bucket))

        # If the destination path doesn't exist or overwrite is True, no need to do the md5um etag check, so just download.
        pathrtn = path_check(dest)

        # Compare the remote MD5 sum of the object with the local dest md5sum, if it already exists.
        if pathrtn is True:
            md5_remote = keysum(module, s3, bucket, obj, version=version, validate=validate)
            md5_local = module.md5(dest)
            if md5_local == md5_remote:
                sum_matches = True
                if overwrite == 'always':
                    download_s3file(module, s3, bucket, obj, dest, retries, version=version, validate=validate)
                else:
                    module.exit_json(msg="Local and remote object are identical, ignoring. Use overwrite=always parameter to force.", changed=False)
            else:
                sum_matches = False

                if overwrite in ('always', 'different'):
                    download_s3file(module, s3, bucket, obj, dest, retries, version=version, validate=validate)
                else:
                    module.exit_json(msg="WARNING: Checksums do not match. Use overwrite parameter to force download.")
        else:
            download_s3file(module, s3, bucket, obj, dest, retries, version=version, validate=validate)


        # Firstly, if key_matches is TRUE and overwrite is not enabled, we EXIT with a helpful message.
        if sum_matches and overwrite == 'never':
            module.exit_json(msg="Local and remote object are identical, ignoring. Use overwrite parameter to force.", changed=False)

    # if our mode is a PUT operation (upload), go through the procedure as appropriate ...
    if mode == 'put':

        # Use this snippet to debug through conditionals:
        # module.exit_json(msg="Bucket return %s"%bucketrtn)

        # Lets check the src path.
        pathrtn = path_check(src)
        if not pathrtn:
            module.fail_json(msg="Local object for PUT does not exist")

        # Lets check to see if bucket exists to get ground truth.
        if bucketrtn:
            keyrtn = key_check(module, s3, bucket, obj)

        # Lets check key state. Does it exist and if it does, compute the etag md5sum.
        if bucketrtn and keyrtn:
            md5_remote = keysum(module, s3, bucket, obj)
            md5_local = module.md5(src)

            if md5_local == md5_remote:
                sum_matches = True
                if overwrite == 'always':
                    upload_s3file(module, s3, bucket, obj, src, expiry, metadata, encrypt, headers)
                else:
                    get_download_url(module, s3, bucket, obj, expiry, changed=False)
            else:
                sum_matches = False
                if overwrite in ('always', 'different'):
                    upload_s3file(module, s3, bucket, obj, src, expiry, metadata, encrypt, headers)
                else:
                    module.exit_json(msg="WARNING: Checksums do not match. Use overwrite parameter to force upload.")

        # If neither exist (based on bucket existence), we can create both.
        if pathrtn and not bucketrtn:
            create_bucket(module, s3, bucket, location)
            upload_s3file(module, s3, bucket, obj, src, expiry, metadata, encrypt, headers)

        # If bucket exists but key doesn't, just upload.
        if bucketrtn and pathrtn and not keyrtn:
            upload_s3file(module, s3, bucket, obj, src, expiry, metadata, encrypt, headers)

    # Delete an object from a bucket, not the entire bucket
    if mode == 'delobj':
        if obj is None:
            module.fail_json(msg="object parameter is required")
        if bucket:
            deletertn = delete_key(module, s3, bucket, obj, validate=validate)
            if deletertn is True:
                module.exit_json(msg="Object %s deleted from bucket %s." % (obj, bucket), changed=True)
        else:
            module.fail_json(msg="Bucket parameter is required.")


    # Delete an entire bucket, including all objects in the bucket
    if mode == 'delete':
        if bucket:
            deletertn = delete_bucket(module, s3, bucket)
            message = "Bucket {0} and all keys have been deleted.".format(bucket)
            module.exit_json(msg=message, changed=deletertn)
        else:
            module.fail_json(msg="Bucket parameter is required.")

    # Support for listing a set of keys
    if mode == 'list':
        bucket_object = get_bucket(module, s3, bucket)

        # If the bucket does not exist then bail out
        if bucket_object is None:
            module.fail_json(msg="Target bucket (%s) cannot be found"% bucket)

        list_keys(module, bucket_object, prefix, marker, max_keys)

    # Need to research how to create directories without "populating" a key, so this should just do bucket creation for now.
    # WE SHOULD ENABLE SOME WAY OF CREATING AN EMPTY KEY TO CREATE "DIRECTORY" STRUCTURE, AWS CONSOLE DOES THIS.
    if mode == 'create':
        if bucket and not obj:
            if bucketrtn:
                module.exit_json(msg="Bucket already exists.", changed=False)
            else:
                module.exit_json(msg="Bucket created successfully", changed=create_bucket(module, s3, bucket, location))
        if bucket and obj:
            if obj.endswith('/'):
                dirobj = obj
            else:
                dirobj = obj + "/"
            if bucketrtn:
                keyrtn = key_check(module, s3, bucket, dirobj)
                if keyrtn is True:
                    module.exit_json(msg="Bucket %s and key %s already exists."% (bucket, obj), changed=False)
                else:
                    create_dirkey(module, s3, bucket, dirobj)
            else:
                created = create_bucket(module, s3, bucket, location)
                create_dirkey(module, s3, bucket, dirobj)

    # Support for grabbing the time-expired URL for an object in S3/Walrus.
    if mode == 'geturl':
        if not bucket and not obj:
            module.fail_json(msg="Bucket and Object parameters must be set")

        keyrtn = key_check(module, s3, bucket, obj, validate=validate)
        if keyrtn:
            get_download_url(module, s3, bucket, obj, expiry, validate=validate)
        else:
            module.fail_json(msg="Key %s does not exist." % obj)

    if mode == 'getstr':
        if bucket and obj:
            keyrtn = key_check(module, s3, bucket, obj, version=version, validate=validate)
            if keyrtn:
                download_s3str(module, s3, bucket, obj, version=version, validate=validate)
            elif version is not None:
                module.fail_json(msg="Key %s with version id %s does not exist." % (obj, version))
            else:
                module.fail_json(msg="Key %s does not exist." % obj)

    module.exit_json(failed=False)


def get_s3_connection(aws_connect_kwargs, location, rgw, s3_url):
    if s3_url and rgw:
        rgw = urlparse(s3_url)
        # ensure none of the named arguments we will pass to boto.connect_s3
        # are already present in aws_connect_kwargs
        for kw in ['is_secure', 'host', 'port', 'calling_format']:
            try:
                del aws_connect_kwargs[kw]
            except KeyError:
                pass
        s3 = boto.connect_s3(
            is_secure=rgw.scheme == 'https',
            host=rgw.hostname,
            port=rgw.port,
            calling_format=OrdinaryCallingFormat(),
            **aws_connect_kwargs
        )
    elif is_fakes3(s3_url):
        fakes3 = urlparse(s3_url)
        # ensure none of the named arguments we will pass to S3Connection
        # are already present in aws_connect_kwargs
        for kw in ['is_secure', 'host', 'port', 'calling_format']:
            try:
                del aws_connect_kwargs[kw]
            except KeyError:
                pass
        s3 = S3Connection(
            is_secure=fakes3.scheme == 'fakes3s',
            host=fakes3.hostname,
            port=fakes3.port,
            calling_format=OrdinaryCallingFormat(),
            **aws_connect_kwargs
        )
    elif is_walrus(s3_url):
        walrus = urlparse(s3_url).hostname
        s3 = boto.connect_walrus(walrus, **aws_connect_kwargs)
    else:
        aws_connect_kwargs['is_secure'] = True
        try:
            s3 = connect_to_aws(boto.s3, location, **aws_connect_kwargs)
        except AnsibleAWSError:
            # use this as fallback because connect_to_region seems to fail in boto + non 'classic' aws accounts in some cases
            s3 = boto.connect_s3(**aws_connect_kwargs)
    return s3


# import module snippets
from ansible.module_utils.basic import *
from ansible.module_utils.ec2 import *

if __name__ == '__main__':
    main()
