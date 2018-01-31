#!/usr/bin/python
#
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: gc_storage
version_added: "1.4"
short_description: This module manages objects/buckets in Google Cloud Storage.
description:
    - This module allows users to manage their objects/buckets in Google Cloud Storage.  It allows upload and download operations and can set some
      canned permissions. It also allows retrieval of URLs for objects for use in playbooks, and retrieval of string contents of objects.  This module
      requires setting the default project in GCS prior to playbook usage.  See U(https://developers.google.com/storage/docs/reference/v1/apiversion1) for
      information about setting the default project.

options:
  bucket:
    description:
      - Bucket name.
    required: true
  object:
    description:
      - Keyname of the object inside the bucket. Can be also be used to create "virtual directories" (see examples).
    required: false
    default: null
  src:
    description:
      - The source file path when performing a PUT operation.
    required: false
    default: null
  dest:
    description:
      - The destination file path when downloading an object/key with a GET operation.
    required: false
  force:
    description:
      - Forces an overwrite either locally on the filesystem or remotely with the object/key. Used with PUT and GET operations.
    required: false
    default: true
    aliases: [ 'overwrite' ]
  permission:
    description:
      - This option let's the user set the canned permissions on the object/bucket that are created. The permissions that can be set are 'private',
        'public-read', 'authenticated-read'.
    required: false
    default: private
  headers:
    version_added: "2.0"
    description:
      - Headers to attach to object.
    required: false
    default: '{}'
  expiration:
    description:
      - Time limit (in seconds) for the URL generated and returned by GCA when performing a mode=put or mode=get_url operation. This url is only
        available when public-read is the acl for the object.
    required: false
    default: null
  mode:
    description:
      - Switches the module behaviour between upload, download, get_url (return download url) , get_str (download object as string), create (bucket) and
        delete (bucket).
    required: true
    default: null
    choices: [ 'get', 'put', 'get_url', 'get_str', 'delete', 'create' ]
  gs_secret_key:
    description:
      - GS secret key. If not set then the value of the GS_SECRET_ACCESS_KEY environment variable is used.
    required: true
    default: null
  gs_access_key:
    description:
      - GS access key. If not set then the value of the GS_ACCESS_KEY_ID environment variable is used.
    required: true
    default: null
  region:
    version_added: "2.4"
    description:
      - The gs region to use. If not defined then the value 'US' will be used. See U(https://cloud.google.com/storage/docs/bucket-locations)
    required: false
    default: 'US'
  versioning:
    version_added: "2.4"
    description:
      - Whether versioning is enabled or disabled (note that once versioning is enabled, it can only be suspended)
    required: false
    default: null
    choices: [ 'yes', 'no' ]

requirements:
    - "python >= 2.6"
    - "boto >= 2.9"

author: "Benno Joy (@bennojoy), extended by Lukas Beumer (@nitaco)"

'''

EXAMPLES = '''
- name: Upload some content
  gc_storage:
    bucket: mybucket
    object: key.txt
    src: /usr/local/myfile.txt
    mode: put
    permission: public-read

- name: Upload some headers
  gc_storage:
    bucket: mybucket
    object: key.txt
    src: /usr/local/myfile.txt
    headers: '{"Content-Encoding": "gzip"}'

- name: Download some content
  gc_storage:
    bucket: mybucket
    object: key.txt
    dest: /usr/local/myfile.txt
    mode: get

- name: Download an object as a string to use else where in your playbook
  gc_storage:
    bucket: mybucket
    object: key.txt
    mode: get_str

- name: Create an empty bucket
  gc_storage:
    bucket: mybucket
    mode: create

- name: Create a bucket with key as directory
  gc_storage:
    bucket: mybucket
    object: /my/directory/path
    mode: create

- name: Delete a bucket and all contents
  gc_storage:
    bucket: mybucket
    mode: delete

- name: Create a bucket with versioning enabled
  gc_storage:
    bucket: "mybucket"
    versioning: yes
    mode: create

- name: Create a bucket located in the eu
  gc_storage:
    bucket: "mybucket"
    region: "europe-west3"
    mode: create

'''

import os

try:
    import boto
    HAS_BOTO = True
except ImportError:
    HAS_BOTO = False

from ansible.module_utils.basic import AnsibleModule


def grant_check(module, gs, obj):
    try:
        acp = obj.get_acl()
        if module.params.get('permission') == 'public-read':
            grant = [x for x in acp.entries.entry_list if x.scope.type == 'AllUsers']
            if not grant:
                obj.set_acl('public-read')
                module.exit_json(changed=True, result="The objects permission as been set to public-read")
        if module.params.get('permission') == 'authenticated-read':
            grant = [x for x in acp.entries.entry_list if x.scope.type == 'AllAuthenticatedUsers']
            if not grant:
                obj.set_acl('authenticated-read')
                module.exit_json(changed=True, result="The objects permission as been set to authenticated-read")
    except gs.provider.storage_response_error as e:
        module.fail_json(msg=str(e))
    return True


def key_check(module, gs, bucket, obj):
    try:
        bucket = gs.lookup(bucket)
        key_check = bucket.get_key(obj)
    except gs.provider.storage_response_error as e:
        module.fail_json(msg=str(e))
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
    etag_multipart = '-' in md5_remote  # Check for multipart, etag is not md5
    if etag_multipart is True:
        module.fail_json(msg="Files uploaded with multipart of gs are not supported with checksum, unable to compute checksum.")
    return md5_remote


def bucket_check(module, gs, bucket):
    try:
        result = gs.lookup(bucket)
    except gs.provider.storage_response_error as e:
        module.fail_json(msg=str(e))
    if result:
        grant_check(module, gs, result)
        return True
    else:
        return False


def create_bucket(module, gs, bucket):
    try:
        bucket = gs.create_bucket(bucket, transform_headers(module.params.get('headers')), module.params.get('region'))
        bucket.set_acl(module.params.get('permission'))
        bucket.configure_versioning(module.params.get('versioning'))
    except gs.provider.storage_response_error as e:
        module.fail_json(msg=str(e))
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
    except gs.provider.storage_response_error as e:
        module.fail_json(msg=str(e))


def delete_key(module, gs, bucket, obj):
    try:
        bucket = gs.lookup(bucket)
        bucket.delete_key(obj)
        module.exit_json(msg="Object deleted from bucket ", changed=True)
    except gs.provider.storage_response_error as e:
        module.fail_json(msg=str(e))


def create_dirkey(module, gs, bucket, obj):
    try:
        bucket = gs.lookup(bucket)
        key = bucket.new_key(obj)
        key.set_contents_from_string('')
        module.exit_json(msg="Virtual directory %s created in bucket %s" % (obj, bucket.name), changed=True)
    except gs.provider.storage_response_error as e:
        module.fail_json(msg=str(e))


def path_check(path):
    if os.path.exists(path):
        return True
    else:
        return False


def transform_headers(headers):
    """
    Boto url-encodes values unless we convert the value to `str`, so doing
    this prevents 'max-age=100000' from being converted to "max-age%3D100000".

    :param headers: Headers to convert
    :type  headers: dict
    :rtype: dict

    """

    for key, value in headers.items():
        headers[key] = str(value)
    return headers


def upload_gsfile(module, gs, bucket, obj, src, expiry):
    try:
        bucket = gs.lookup(bucket)
        key = bucket.new_key(obj)
        key.set_contents_from_filename(
            filename=src,
            headers=transform_headers(module.params.get('headers'))
        )
        key.set_acl(module.params.get('permission'))
        url = key.generate_url(expiry)
        module.exit_json(msg="PUT operation complete", url=url, changed=True)
    except gs.provider.storage_copy_error as e:
        module.fail_json(msg=str(e))


def download_gsfile(module, gs, bucket, obj, dest):
    try:
        bucket = gs.lookup(bucket)
        key = bucket.lookup(obj)
        key.get_contents_to_filename(dest)
        module.exit_json(msg="GET operation complete", changed=True)
    except gs.provider.storage_copy_error as e:
        module.fail_json(msg=str(e))


def download_gsstr(module, gs, bucket, obj):
    try:
        bucket = gs.lookup(bucket)
        key = bucket.lookup(obj)
        contents = key.get_contents_as_string()
        module.exit_json(msg="GET operation complete", contents=contents, changed=True)
    except gs.provider.storage_copy_error as e:
        module.fail_json(msg=str(e))


def get_download_url(module, gs, bucket, obj, expiry):
    try:
        bucket = gs.lookup(bucket)
        key = bucket.lookup(obj)
        url = key.generate_url(expiry)
        module.exit_json(msg="Download url:", url=url, expiration=expiry, changed=True)
    except gs.provider.storage_response_error as e:
        module.fail_json(msg=str(e))


def handle_get(module, gs, bucket, obj, overwrite, dest):
    md5_remote = keysum(module, gs, bucket, obj)
    md5_local = module.md5(dest)
    if md5_local == md5_remote:
        module.exit_json(changed=False)
    if md5_local != md5_remote and not overwrite:
        module.exit_json(msg="WARNING: Checksums do not match. Use overwrite parameter to force download.", failed=True)
    else:
        download_gsfile(module, gs, bucket, obj, dest)


def handle_put(module, gs, bucket, obj, overwrite, src, expiration):
    # Lets check to see if bucket exists to get ground truth.
    bucket_rc = bucket_check(module, gs, bucket)
    key_rc = key_check(module, gs, bucket, obj)

    # Lets check key state. Does it exist and if it does, compute the etag md5sum.
    if bucket_rc and key_rc:
        md5_remote = keysum(module, gs, bucket, obj)
        md5_local = module.md5(src)
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
            module.exit_json(msg="Bucket %s and all keys have been deleted." % bucket, changed=delete_bucket(module, gs, bucket))
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
                module.exit_json(msg="Bucket %s and key %s already exists." % (bucket, obj), changed=False)
            else:
                create_dirkey(module, gs, bucket, dirobj)
        else:
            create_bucket(module, gs, bucket)
            create_dirkey(module, gs, bucket, dirobj)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            bucket=dict(required=True),
            object=dict(default=None, type='path'),
            src=dict(default=None),
            dest=dict(default=None, type='path'),
            expiration=dict(type='int', default=600, aliases=['expiry']),
            mode=dict(choices=['get', 'put', 'delete', 'create', 'get_url', 'get_str'], required=True),
            permission=dict(choices=['private', 'public-read', 'authenticated-read'], default='private'),
            headers=dict(type='dict', default={}),
            gs_secret_key=dict(no_log=True, required=True),
            gs_access_key=dict(required=True),
            overwrite=dict(default=True, type='bool', aliases=['force']),
            region=dict(default='US', type='str'),
            versioning=dict(default='no', type='bool')
        ),
    )

    if not HAS_BOTO:
        module.fail_json(msg='boto 2.9+ required for this module')

    bucket = module.params.get('bucket')
    obj = module.params.get('object')
    src = module.params.get('src')
    dest = module.params.get('dest')
    mode = module.params.get('mode')
    expiry = module.params.get('expiration')
    gs_secret_key = module.params.get('gs_secret_key')
    gs_access_key = module.params.get('gs_access_key')
    overwrite = module.params.get('overwrite')

    if mode == 'put':
        if not src or not object:
            module.fail_json(msg="When using PUT, src, bucket, object are mandatory parameters")
    if mode == 'get':
        if not dest or not object:
            module.fail_json(msg="When using GET, dest, bucket, object are mandatory parameters")

    try:
        gs = boto.connect_gs(gs_access_key, gs_secret_key)
    except boto.exception.NoAuthHandlerFound as e:
        module.fail_json(msg=str(e))

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


if __name__ == '__main__':
    main()
