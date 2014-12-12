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
module: gc_storage
version_added: "1.4"
short_description: This module manages objects/buckets in Google Cloud Storage. 
description:
    - This module allows users to manage their objects/buckets in Google Cloud Storage.  It allows upload and download operations and can set some canned permissions. It also allows retrieval of URLs for objects for use in playbooks, and retrieval of string contents of objects.  This module requires setting the default project in GCS prior to playbook usage.  See U(https://developers.google.com/storage/docs/reference/v1/apiversion1) for information about setting the default project.

options:
  bucket:
    description:
      - Bucket name. 
    required: true
    default: null 
    aliases: []
  object:
    description:
      - Keyname of the object inside the bucket. Can be also be used to create "virtual directories" (see examples).
    required: false
    default: null
    aliases: []
  src:
    description:
      - The source file path when performing a PUT operation.
    required: false
    default: null
    aliases: []
  dest:
    description:
      - The destination file path when downloading an object/key with a GET operation.
    required: false
    aliases: []
  force:
    description:
      - Forces an overwrite either locally on the filesystem or remotely with the object/key. Used with PUT and GET operations.
    required: false
    default: true
    aliases: [ 'overwrite' ]
  permission:
    description:
      - This option let's the user set the canned permissions on the object/bucket that are created. The permissions that can be set are 'private', 'public-read', 'authenticated-read'.
    required: false
    default: private 
  expiration:
    description:
      - Time limit (in seconds) for the URL generated and returned by GCA when performing a mode=put or mode=get_url operation. This url is only avaialbe when public-read is the acl for the object.
    required: false
    default: null
    aliases: []
  mode:
    description:
      - Switches the module behaviour between upload, download, get_url (return download url) , get_str (download object as string), create (bucket) and delete (bucket). 
    required: true
    default: null
    aliases: []
    choices: [ 'get', 'put', 'get_url', 'get_str', 'delete', 'create' ]
  gcs_secret_key:
    description:
      - GCS secret key. If not set then the value of the GCS_SECRET_KEY environment variable is used. 
    required: true
    default: null
  gcs_access_key:
    description:
      - GCS access key. If not set then the value of the GCS_ACCESS_KEY environment variable is used.
    required: true
    default: null

requirements: [ "boto 2.9+" ]

author: benno@ansible.com Note. Most of the code has been taken from the S3 module.

'''

EXAMPLES = '''
# upload some content
- gc_storage: bucket=mybucket object=key.txt src=/usr/local/myfile.txt mode=put permission=public-read

# download some content
- gc_storage: bucket=mybucket object=key.txt dest=/usr/local/myfile.txt mode=get

# Download an object as a string to use else where in your playbook
- gc_storage: bucket=mybucket object=key.txt mode=get_str

# Create an empty bucket
- gc_storage: bucket=mybucket mode=create

# Create a bucket with key as directory
- gc_storage: bucket=mybucket object=/my/directory/path mode=create

# Delete a bucket and all contents
- gc_storage: bucket=mybucket mode=delete
'''

import sys
import os
import urlparse
import hashlib

try:
    import boto
except ImportError:
    print "failed=True msg='boto 2.9+ required for this module'"
    sys.exit(1)

def grant_check(module, gs, obj):
    try:
        acp = obj.get_acl()
        if module.params.get('permission') == 'public-read':
            grant = [ x for x in acp.entries.entry_list if x.scope.type == 'AllUsers']
            if not grant:
                obj.set_acl('public-read')
                module.exit_json(changed=True, result="The objects permission as been set to public-read") 
        if module.params.get('permission') == 'authenticated-read':
            grant = [ x for x in acp.entries.entry_list if x.scope.type == 'AllAuthenticatedUsers']
            if not grant:
                obj.set_acl('authenticated-read')
                module.exit_json(changed=True, result="The objects permission as been set to authenticated-read") 
    except gs.provider.storage_response_error, e:
        module.fail_json(msg= str(e))
    return True

        

def key_check(module, gs, bucket, obj):
    try:
        bucket = gs.lookup(bucket)
        key_check = bucket.get_key(obj)
    except gs.provider.storage_response_error, e:
        module.fail_json(msg= str(e))
    if key_check:
        grant_check(module, gs, key_check)
        return True
    else:
        return False

def keysum(module, gs, bucket, obj):
    bucket = gs.lookup(bucket)
    key_check = bucket.get_key(obj)
    if not key_check:
        return None
    md5_remote = key_check.etag[1:-1]
    etag_multipart = '-' in md5_remote # Check for multipart, etag is not md5
    if etag_multipart is True:
        module.fail_json(msg="Files uploaded with multipart of gs are not supported with checksum, unable to compute checksum.")
    return md5_remote

def bucket_check(module, gs, bucket):
    try:
        result = gs.lookup(bucket)
    except gs.provider.storage_response_error, e:
        module.fail_json(msg= str(e))
    if result:
        grant_check(module, gs, result)
        return True
    else:
        return False

def create_bucket(module, gs, bucket):
    try:
        bucket = gs.create_bucket(bucket)
        bucket.set_acl(module.params.get('permission'))
    except gs.provider.storage_response_error, e:
        module.fail_json(msg= str(e))
    if bucket:
        return True

def delete_bucket(module, gs, bucket):
    try:
        bucket = gs.lookup(bucket)
        bucket_contents = bucket.list()
        for key in bucket_contents:
            bucket.delete_key(key.name)
        bucket.delete()
        return True
    except gs.provider.storage_response_error, e:
        module.fail_json(msg= str(e))

def delete_key(module, gs, bucket, obj):
    try:
        bucket = gs.lookup(bucket)
        bucket.delete_key(obj)
        module.exit_json(msg="Object deleted from bucket ", changed=True)
    except gs.provider.storage_response_error, e:
        module.fail_json(msg= str(e))
 
def create_dirkey(module, gs, bucket, obj):
    try:
        bucket = gs.lookup(bucket)
        key = bucket.new_key(obj)
        key.set_contents_from_string('')
        module.exit_json(msg="Virtual directory %s created in bucket %s" % (obj, bucket.name), changed=True)
    except gs.provider.storage_response_error, e:
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

def upload_gsfile(module, gs, bucket, obj, src, expiry):
    try:
        bucket = gs.lookup(bucket)
        key = bucket.new_key(obj)  
        key.set_contents_from_filename(src)
        key.set_acl(module.params.get('permission'))
        url = key.generate_url(expiry)
        module.exit_json(msg="PUT operation complete", url=url, changed=True)
    except gs.provider.storage_copy_error, e:
        module.fail_json(msg= str(e))

def download_gsfile(module, gs, bucket, obj, dest):
    try:
        bucket = gs.lookup(bucket)
        key = bucket.lookup(obj)
        key.get_contents_to_filename(dest)
        module.exit_json(msg="GET operation complete", changed=True)
    except gs.provider.storage_copy_error, e:
        module.fail_json(msg= str(e))

def download_gsstr(module, gs, bucket, obj):
    try:
        bucket = gs.lookup(bucket)
        key = bucket.lookup(obj)
        contents = key.get_contents_as_string()
        module.exit_json(msg="GET operation complete", contents=contents, changed=True)
    except gs.provider.storage_copy_error, e:
        module.fail_json(msg= str(e))

def get_download_url(module, gs, bucket, obj, expiry):
    try:
        bucket = gs.lookup(bucket)
        key = bucket.lookup(obj)
        url = key.generate_url(expiry)
        module.exit_json(msg="Download url:", url=url, expiration=expiry, changed=True)
    except gs.provider.storage_response_error, e:
        module.fail_json(msg= str(e))

def handle_get(module, gs, bucket, obj, overwrite, dest):
    md5_remote = keysum(module, gs, bucket, obj)
    md5_local = hashlib.md5(open(dest, 'rb').read()).hexdigest()
    if md5_local == md5_remote:
        module.exit_json(changed=False)
    if md5_local != md5_remote and not overwrite:
        module.exit_json(msg="WARNING: Checksums do not match. Use overwrite parameter to force download.", failed=True)
    else:
        download_gsfile(module, gs, bucket, obj, dest)

def handle_put(module, gs, bucket, obj, overwrite, src, expiration):
    # Lets check to see if bucket exists to get ground truth.
    bucket_rc = bucket_check(module, gs, bucket)
    key_rc    = key_check(module, gs, bucket, obj)

    # Lets check key state. Does it exist and if it does, compute the etag md5sum.
    if bucket_rc and key_rc:
        md5_remote = keysum(module, gs, bucket, obj)
        md5_local = hashlib.md5(open(src, 'rb').read()).hexdigest()
        if md5_local == md5_remote:
            module.exit_json(msg="Local and remote object are identical", changed=False)
        if md5_local != md5_remote and not overwrite:
            module.exit_json(msg="WARNING: Checksums do not match. Use overwrite parameter to force upload.", failed=True)
        else:
            upload_gsfile(module, gs, bucket, obj, src, expiration)
                                                                                                            
    if not bucket_rc:      
        create_bucket(module, gs, bucket)
        upload_gsfile(module, gs, bucket, obj, src, expiration)

    # If bucket exists but key doesn't, just upload.
    if bucket_rc and not key_rc:
            upload_gsfile(module, gs, bucket, obj, src, expiration)
    
def handle_delete(module, gs, bucket, obj):
    if bucket and not obj:
        if bucket_check(module, gs, bucket):
            module.exit_json(msg="Bucket %s and all keys have been deleted."%bucket, changed=delete_bucket(module, gs, bucket))
        else:
            module.exit_json(msg="Bucket does not exist.", changed=False)
    if bucket and obj:
        if bucket_check(module, gs, bucket):
            if key_check(module, gs, bucket, obj):
                module.exit_json(msg="Object has been deleted.", changed=delete_key(module, gs, bucket, obj))
            else:
                module.exit_json(msg="Object does not exists.", changed=False)
        else:
            module.exit_json(msg="Bucket does not exist.", changed=False)
    else:
        module.fail_json(msg="Bucket or Bucket & object  parameter is required.", failed=True)
 
def handle_create(module, gs, bucket, obj):
    if bucket and not obj: 
        if bucket_check(module, gs, bucket):
            module.exit_json(msg="Bucket already exists.", changed=False)
        else:
            module.exit_json(msg="Bucket created successfully", changed=create_bucket(module, gs, bucket))
    if bucket and obj:
        if obj.endswith('/'):
            dirobj = obj
        else:
            dirobj = obj + "/"

        if bucket_check(module, gs, bucket):
            if key_check(module, gs, bucket, dirobj):
                module.exit_json(msg="Bucket %s and key %s already exists."% (bucket, obj), changed=False)
            else:      
                create_dirkey(module, gs, bucket, dirobj)
        else:
            create_bucket(module, gs, bucket)
            create_dirkey(module, gs, bucket, dirobj)

def main():
    module = AnsibleModule(
        argument_spec = dict(
            bucket         = dict(required=True),
            object         = dict(default=None),
            src            = dict(default=None),
            dest           = dict(default=None),
            expiration     = dict(default=600, aliases=['expiry']),
            mode           = dict(choices=['get', 'put', 'delete', 'create', 'get_url', 'get_str'], required=True),
            permission     = dict(choices=['private', 'public-read', 'authenticated-read'], default='private'),
            gs_secret_key  = dict(no_log=True, required=True),
            gs_access_key  = dict(required=True),
            overwrite      = dict(default=True, type='bool', aliases=['force']),
        ),
    )

    bucket        = module.params.get('bucket')
    obj           = module.params.get('object')
    src           = module.params.get('src')
    dest          = module.params.get('dest')
    if dest:
        dest      = os.path.expanduser(dest)
    mode          = module.params.get('mode')
    expiry        = module.params.get('expiration')
    gs_secret_key = module.params.get('gs_secret_key')
    gs_access_key = module.params.get('gs_access_key')
    overwrite     = module.params.get('overwrite')

    if mode == 'put':
        if not src or not object:
            module.fail_json(msg="When using PUT, src, bucket, object are mandatory parameters")
    if mode == 'get':
        if not dest or not object:
            module.fail_json(msg="When using GET, dest, bucket, object are mandatory parameters")
    if obj:
        obj = os.path.expanduser(module.params['object'])

    try:
        gs = boto.connect_gs(gs_access_key, gs_secret_key)
    except boto.exception.NoAuthHandlerFound, e:
        module.fail_json(msg = str(e))
 
    if mode == 'get':
        if not bucket_check(module, gs, bucket) or not key_check(module, gs, bucket, obj):
            module.fail_json(msg="Target bucket/key cannot be found", failed=True)
        if not path_check(dest):
            download_gsfile(module, gs, bucket, obj, dest)
        else:
            handle_get(module, gs, bucket, obj, overwrite, dest)
        
    if mode == 'put':
        if not path_check(src):
            module.fail_json(msg="Local object for PUT does not exist", failed=True)
        handle_put(module, gs, bucket, obj, overwrite, src, expiry)

    # Support for deleting an object if we have both params.  
    if mode == 'delete':
        handle_delete(module, gs, bucket, obj)
    
    if mode == 'create':
        handle_create(module, gs, bucket, obj)
    
    if mode == 'get_url':
        if bucket and obj:
            if bucket_check(module, gs, bucket) and key_check(module, gs, bucket, obj):
                get_download_url(module, gs, bucket, obj, expiry)
            else:
                module.fail_json(msg="Key/Bucket does not exist", failed=True)
        else:
            module.fail_json(msg="Bucket and Object parameters must be set", failed=True)

    # --------------------------- Get the String contents of an Object -------------------------
    if mode == 'get_str':
        if bucket and obj:
            if bucket_check(module, gs, bucket) and key_check(module, gs, bucket, obj):
                download_gsstr(module, gs, bucket, obj)
            else:
                module.fail_json(msg="Key/Bucket does not exist", failed=True)
        else:
            module.fail_json(msg="Bucket and Object parameters must be set", failed=True)


# import module snippets
from ansible.module_utils.basic import *

main()
