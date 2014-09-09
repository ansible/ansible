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

DOCUMENTATION = '''
---
module: s3
short_description: S3 module putting a file into S3.
description:
    - This module allows the user to dictate the presence of a given file in an S3 bucket. If or once the key (file) exists in the bucket, it returns a time-expired download URL. This module has a dependency on python-boto.
version_added: "1.1"
options:
  bucket:
    description:
      - Bucket name. 
    required: true
    default: null 
    aliases: []
  object:
    description:
      - Keyname of the object inside the bucket. Can be used to create "virtual directories", see examples.
    required: false
    default: null
    aliases: []
    version_added: "1.3"
  src:
    description:
      - The source file path when performing a PUT operation.
    required: false
    default: null
    aliases: []
    version_added: "1.3"
  dest:
    description:
      - The destination file path when downloading an object/key with a GET operation.
    required: false
    aliases: []
    version_added: "1.3"
  overwrite:
    description:
      - Force overwrite either locally on the filesystem or remotely with the object/key. Used with PUT and GET operations.
    required: false
    default: true
    version_added: "1.2"
  mode:
    description:
      - Switches the module behaviour between put (upload), get (download), geturl (return download url (Ansible 1.3+), getstr (download object as string (1.3+)), create (bucket) and delete (bucket). 
    required: true
    default: null
    aliases: []
  expiration:
    description:
      - Time limit (in seconds) for the URL generated and returned by S3/Walrus when performing a mode=put or mode=geturl operation. 
    required: false
    default: 600
    aliases: []
  s3_url:
    description:
        - "S3 URL endpoint. If not specified then the S3_URL environment variable is used, if that variable is defined. Ansible tries to guess if fakes3 (https://github.com/jubos/fake-s3) or Eucalyptus Walrus (https://github.com/eucalyptus/eucalyptus/wiki/Walrus) is used and configure connection accordingly. Current heuristic is: everything with scheme fakes3:// is fakes3, everything else not ending with amazonaws.com is Walrus."
    default: null
    aliases: [ S3_URL ]
  aws_secret_key:
    description:
      - AWS secret key. If not set then the value of the AWS_SECRET_KEY environment variable is used. 
    required: false
    default: null
    aliases: ['ec2_secret_key', 'secret_key']
  aws_access_key:
    description:
      - AWS access key. If not set then the value of the AWS_ACCESS_KEY environment variable is used.
    required: false
    default: null
    aliases: [ 'ec2_access_key', 'access_key' ]
  metadata:
    description:
      - Metadata for PUT operation, as a dictionary of 'key=value' and 'key=value,key=value'.
    required: false
    default: null
    version_added: "1.6"
  region:
    description:
     - "AWS region to create the bucket in. If not set then the value of the EC2_REGION and AWS_REGION environment variables are checked, followed by the aws_region and ec2_region settings in the Boto config file.  If none of those are set the region defaults to the S3 Location: US Standard.  Prior to ansible 1.8 this parameter could be specified but had no effect."
    required: false
    default: null
    version_added: "1.8"

requirements: [ "boto" ]
author: Lester Wade, Ralph Tice
'''

EXAMPLES = '''
# Simple PUT operation
- s3: bucket=mybucket object=/my/desired/key.txt src=/usr/local/myfile.txt mode=put
# Simple GET operation
- s3: bucket=mybucket object=/my/desired/key.txt dest=/usr/local/myfile.txt mode=get
# GET/download and overwrite local file (trust remote)
- s3: bucket=mybucket object=/my/desired/key.txt dest=/usr/local/myfile.txt mode=get 
# GET/download and do not overwrite local file (trust remote)
- s3: bucket=mybucket object=/my/desired/key.txt dest=/usr/local/myfile.txt mode=get force=false
# PUT/upload and overwrite remote file (trust local)
- s3: bucket=mybucket object=/my/desired/key.txt src=/usr/local/myfile.txt mode=put
# PUT/upload with metadata
- s3: bucket=mybucket object=/my/desired/key.txt src=/usr/local/myfile.txt mode=put metadata='Content-Encoding=gzip'
# PUT/upload with multiple metadata
- s3: bucket=mybucket object=/my/desired/key.txt src=/usr/local/myfile.txt mode=put metadata='Content-Encoding=gzip,Cache-Control=no-cache'
# PUT/upload and do not overwrite remote file (trust local)
- s3: bucket=mybucket object=/my/desired/key.txt src=/usr/local/myfile.txt mode=put force=false
# Download an object as a string to use else where in your playbook
- s3: bucket=mybucket object=/my/desired/key.txt src=/usr/local/myfile.txt mode=getstr
# Create an empty bucket
- s3: bucket=mybucket mode=create
# Create a bucket with key as directory
- s3: bucket=mybucket object=/my/directory/path mode=create
# Create an empty bucket in the EU region
- s3: bucket=mybucket mode=create region=eu-west-1
# Delete a bucket and all contents
- s3: bucket=mybucket mode=delete
'''

import sys
import os
import urlparse
import hashlib

try:
    import boto
    from boto.s3.connection import Location
except ImportError:
    print "failed=True msg='boto required for this module'"
    sys.exit(1)

def key_check(module, s3, bucket, obj):
    try:
        bucket = s3.lookup(bucket)
        key_check = bucket.get_key(obj)
    except s3.provider.storage_response_error, e:
        module.fail_json(msg= str(e))
    if key_check:
        return True
    else:
        return False

def keysum(module, s3, bucket, obj):
    bucket = s3.lookup(bucket)
    key_check = bucket.get_key(obj)
    if not key_check:
        return None
    md5_remote = key_check.etag[1:-1]
    etag_multipart = '-' in md5_remote # Check for multipart, etag is not md5
    if etag_multipart is True:
        module.fail_json(msg="Files uploaded with multipart of s3 are not supported with checksum, unable to compute checksum.")
    return md5_remote

def bucket_check(module, s3, bucket):
    try:
        result = s3.lookup(bucket)
    except s3.provider.storage_response_error, e:
        module.fail_json(msg= str(e))
    if result:
        return True
    else:
        return False

def create_bucket(module, s3, bucket, location=Location.DEFAULT):
    try:
        bucket = s3.create_bucket(bucket, location=location)
    except s3.provider.storage_response_error, e:
        module.fail_json(msg= str(e))
    if bucket:
        return True

def delete_bucket(module, s3, bucket):
    try:
        bucket = s3.lookup(bucket)
        bucket_contents = bucket.list()
        bucket.delete_keys([key.name for key in bucket_contents])
        bucket.delete()
        return True
    except s3.provider.storage_response_error, e:
        module.fail_json(msg= str(e))

def delete_key(module, s3, bucket, obj):
    try:
        bucket = s3.lookup(bucket)
        bucket.delete_key(obj)
        module.exit_json(msg="Object deleted from bucket %s"%bucket, changed=True)
    except s3.provider.storage_response_error, e:
        module.fail_json(msg= str(e))
 
def create_dirkey(module, s3, bucket, obj):
    try:
        bucket = s3.lookup(bucket)
        key = bucket.new_key(obj)
        key.set_contents_from_string('')
        module.exit_json(msg="Virtual directory %s created in bucket %s" % (obj, bucket.name), changed=True)
    except s3.provider.storage_response_error, e:
        module.fail_json(msg= str(e))

def upload_file_check(src):
    if os.path.exists(src):
        file_exists is True
    else:
        file_exists is False
    if os.path.isdir(src):
        module.fail_json(msg="Specifying a directory is not a valid source for upload.", failed=True)
    return file_exists

def path_check(path):
    if os.path.exists(path):
        return True 
    else:
        return False

def upload_s3file(module, s3, bucket, obj, src, expiry, metadata):
    try:
        bucket = s3.lookup(bucket)
        key = bucket.new_key(obj)
        if metadata:
            for meta_key in metadata.keys():
                key.set_metadata(meta_key, metadata[meta_key])

        key.set_contents_from_filename(src)
        url = key.generate_url(expiry)
        module.exit_json(msg="PUT operation complete", url=url, changed=True)
    except s3.provider.storage_copy_error, e:
        module.fail_json(msg= str(e))

def download_s3file(module, s3, bucket, obj, dest):
    try:
        bucket = s3.lookup(bucket)
        key = bucket.lookup(obj)
        key.get_contents_to_filename(dest)
        module.exit_json(msg="GET operation complete", changed=True)
    except s3.provider.storage_copy_error, e:
        module.fail_json(msg= str(e))

def download_s3str(module, s3, bucket, obj):
    try:
        bucket = s3.lookup(bucket)
        key = bucket.lookup(obj)
        contents = key.get_contents_as_string()
        module.exit_json(msg="GET operation complete", contents=contents, changed=True)
    except s3.provider.storage_copy_error, e:
        module.fail_json(msg= str(e))

def get_download_url(module, s3, bucket, obj, expiry, changed=True):
    try:
        bucket = s3.lookup(bucket)
        key = bucket.lookup(obj)
        url = key.generate_url(expiry)
        module.exit_json(msg="Download url:", url=url, expiry=expiry, changed=changed)
    except s3.provider.storage_response_error, e:
        module.fail_json(msg= str(e))

def is_fakes3(s3_url):
    """ Return True if s3_url has scheme fakes3:// """
    if s3_url is not None:
        return urlparse.urlparse(s3_url).scheme == 'fakes3'
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
    argument_spec.update(dict(
            bucket         = dict(required=True),
            object         = dict(),
            src            = dict(),
            dest           = dict(default=None),
            mode           = dict(choices=['get', 'put', 'delete', 'create', 'geturl', 'getstr'], required=True),
            expiry         = dict(default=600, aliases=['expiration']),
            s3_url         = dict(aliases=['S3_URL']),
            overwrite      = dict(aliases=['force'], default=True, type='bool'),
            metadata      = dict(type='dict'),
        ),
    )
    module = AnsibleModule(argument_spec=argument_spec)

    bucket = module.params.get('bucket')
    obj = module.params.get('object')
    src = module.params.get('src')
    if module.params.get('dest'):
        dest = os.path.expanduser(module.params.get('dest'))
    mode = module.params.get('mode')
    expiry = int(module.params['expiry'])
    s3_url = module.params.get('s3_url')
    overwrite = module.params.get('overwrite')
    metadata = module.params.get('metadata')

    ec2_url, aws_access_key, aws_secret_key, region = get_ec2_creds(module)

    if region in ('us-east-1', '', None):
        # S3ism for the US Standard region
        location = Location.DEFAULT
    else:
        # Boto uses symbolic names for locations but region strings will
        # actually work fine for everything except us-east-1 (US Standard)
        location = region

    if module.params.get('object'):
        obj = os.path.expanduser(module.params['object'])

    # allow eucarc environment variables to be used if ansible vars aren't set
    if not s3_url and 'S3_URL' in os.environ:
        s3_url = os.environ['S3_URL']

    # Look at s3_url and tweak connection settings
    # if connecting to Walrus or fakes3
    if is_fakes3(s3_url):
        try:
            fakes3 = urlparse.urlparse(s3_url)
            from boto.s3.connection import OrdinaryCallingFormat
            s3 = boto.connect_s3(
                aws_access_key,
                aws_secret_key,
                is_secure=False,
                host=fakes3.hostname,
                port=fakes3.port,
                calling_format=OrdinaryCallingFormat())
        except boto.exception.NoAuthHandlerFound, e:
            module.fail_json(msg = str(e))
    elif is_walrus(s3_url):
        try:
            walrus = urlparse.urlparse(s3_url).hostname
            s3 = boto.connect_walrus(walrus, aws_access_key, aws_secret_key)
        except boto.exception.NoAuthHandlerFound, e:
            module.fail_json(msg = str(e))
    else:
        try:
            s3 = boto.connect_s3(aws_access_key, aws_secret_key)
        except boto.exception.NoAuthHandlerFound, e:
            module.fail_json(msg = str(e))
 
    # If our mode is a GET operation (download), go through the procedure as appropriate ...
    if mode == 'get':
    
        # First, we check to see if the bucket exists, we get "bucket" returned.
        bucketrtn = bucket_check(module, s3, bucket)
        if bucketrtn is False:
            module.fail_json(msg="Target bucket cannot be found", failed=True)

        # Next, we check to see if the key in the bucket exists. If it exists, it also returns key_matches md5sum check.
        keyrtn = key_check(module, s3, bucket, obj)    
        if keyrtn is False:
            module.fail_json(msg="Target key cannot be found", failed=True)

        # If the destination path doesn't exist, no need to md5um etag check, so just download.
        pathrtn = path_check(dest)
        if pathrtn is False:
            download_s3file(module, s3, bucket, obj, dest)

        # Compare the remote MD5 sum of the object with the local dest md5sum, if it already exists. 
        if pathrtn is True:
            md5_remote = keysum(module, s3, bucket, obj)
            md5_local = hashlib.md5(open(dest, 'rb').read()).hexdigest()
            if md5_local == md5_remote:
                sum_matches = True
                if overwrite is True:
                    download_s3file(module, s3, bucket, obj, dest)
                else:
                    module.exit_json(msg="Local and remote object are identical, ignoring. Use overwrite parameter to force.", changed=False)
            else:
                sum_matches = False
                if overwrite is True:
                    download_s3file(module, s3, bucket, obj, dest)
                else:
                    module.fail_json(msg="WARNING: Checksums do not match. Use overwrite parameter to force download.", failed=True)
        
        # Firstly, if key_matches is TRUE and overwrite is not enabled, we EXIT with a helpful message. 
        if sum_matches is True and overwrite is False:
            module.exit_json(msg="Local and remote object are identical, ignoring. Use overwrite parameter to force.", changed=False)

        # At this point explicitly define the overwrite condition.
        if sum_matches is True and pathrtn is True and overwrite is True:
            download_s3file(module, s3, bucket, obj, dest)

        # If sum does not match but the destination exists, we 
               
    # if our mode is a PUT operation (upload), go through the procedure as appropriate ...        
    if mode == 'put':

        # Use this snippet to debug through conditionals:
#       module.exit_json(msg="Bucket return %s"%bucketrtn)
#       sys.exit(0)

        # Lets check the src path.
        pathrtn = path_check(src)
        if pathrtn is False:
            module.fail_json(msg="Local object for PUT does not exist", failed=True)
        
        # Lets check to see if bucket exists to get ground truth.
        bucketrtn = bucket_check(module, s3, bucket)
        if bucketrtn is True:
            keyrtn = key_check(module, s3, bucket, obj)

        # Lets check key state. Does it exist and if it does, compute the etag md5sum.
        if bucketrtn is True and keyrtn is True:
                md5_remote = keysum(module, s3, bucket, obj)
                md5_local = hashlib.md5(open(src, 'rb').read()).hexdigest()
                if md5_local == md5_remote:
                    sum_matches = True
                    if overwrite is True:
                        upload_s3file(module, s3, bucket, obj, src, expiry, metadata)
                    else:
                        get_download_url(module, s3, bucket, obj, expiry, changed=False)
                else:
                    sum_matches = False
                    if overwrite is True:
                        upload_s3file(module, s3, bucket, obj, src, expiry, metadata)
                    else:
                        module.exit_json(msg="WARNING: Checksums do not match. Use overwrite parameter to force upload.", failed=True)

        # If neither exist (based on bucket existence), we can create both.
        if bucketrtn is False and pathrtn is True:
            create_bucket(module, s3, bucket, location)
            upload_s3file(module, s3, bucket, obj, src, expiry, metadata)

        # If bucket exists but key doesn't, just upload.
        if bucketrtn is True and pathrtn is True and keyrtn is False:
            upload_s3file(module, s3, bucket, obj, src, expiry, metadata)

    # Support for deleting an object if we have both params.  
    if mode == 'delete':
        if bucket:
            bucketrtn = bucket_check(module, s3, bucket)
            if bucketrtn is True:
                deletertn = delete_bucket(module, s3, bucket)
                if deletertn is True:
                    module.exit_json(msg="Bucket %s and all keys have been deleted."%bucket, changed=True)
            else:
                module.fail_json(msg="Bucket does not exist.", changed=False)
        else:
            module.fail_json(msg="Bucket parameter is required.", failed=True)
 
    # Need to research how to create directories without "populating" a key, so this should just do bucket creation for now.
    # WE SHOULD ENABLE SOME WAY OF CREATING AN EMPTY KEY TO CREATE "DIRECTORY" STRUCTURE, AWS CONSOLE DOES THIS.
    if mode == 'create':
        if bucket and not obj: 
            bucketrtn = bucket_check(module, s3, bucket)
            if bucketrtn is True:
                module.exit_json(msg="Bucket already exists.", changed=False)
            else:
                module.exit_json(msg="Bucket created successfully", changed=create_bucket(module, s3, bucket, location))
        if bucket and obj:
            bucketrtn = bucket_check(module, s3, bucket)
            if obj.endswith('/'):
                dirobj = obj
            else:
                dirobj = obj + "/"
            if bucketrtn is True:
                keyrtn = key_check(module, s3, bucket, dirobj)
                if keyrtn is True: 
                    module.exit_json(msg="Bucket %s and key %s already exists."% (bucket, obj), changed=False)
                else:      
                    create_dirkey(module, s3, bucket, dirobj)
            if bucketrtn is False:
                created = create_bucket(module, s3, bucket, location)
                create_dirkey(module, s3, bucket, dirobj)

    # Support for grabbing the time-expired URL for an object in S3/Walrus.
    if mode == 'geturl':
        if bucket and obj:
            bucketrtn = bucket_check(module, s3, bucket)
            if bucketrtn is False:
                module.fail_json(msg="Bucket %s does not exist."%bucket, failed=True)
            else:
                keyrtn = key_check(module, s3, bucket, obj)
                if keyrtn is True:
                    get_download_url(module, s3, bucket, obj, expiry)
                else:
                    module.fail_json(msg="Key %s does not exist."%obj, failed=True)
        else:
            module.fail_json(msg="Bucket and Object parameters must be set", failed=True)

    if mode == 'getstr':
        if bucket and obj:
            bucketrtn = bucket_check(module, s3, bucket)
            if bucketrtn is False:
                module.fail_json(msg="Bucket %s does not exist."%bucket, failed=True)
            else:
                keyrtn = key_check(module, s3, bucket, obj)
                if keyrtn is True:
                    download_s3str(module, s3, bucket, obj)
                else:
                    module.fail_json(msg="Key %s does not exist."%obj, failed=True)

    module.exit_json(failed=False)

# import module snippets
from ansible.module_utils.basic import *
from ansible.module_utils.ec2 import *

main()
