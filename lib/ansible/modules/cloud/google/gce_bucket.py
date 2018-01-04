#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: gce_bucket
short_description: create, delete, upload, download operations on google storage buckets
description:
    - Create or delete google storage bucket.
      Upload or download objects to or from bucket.
      Update bucket policy.
version_added: "2.5"
author: Madhura Naniwadekar(@Madhura-CSI)
options:
  credentials_file:
    description:
      - Path to the JSON file associated with the service account email.
    default: null
    required: false
  service_account_email:
    description:
      - service account email
    required: false
    default: null
  project_id:
    description:
      - GCE project ID.
    required: false
    default: null
  service_account_permissions:
    description:
      - Service account permissions.
        See U(https://cloud.google.com/storage/docs/authentication#oauth-scopes) for possible permissions.
    required: false
    default: null
    choices: [
      "https://www.googleapis.com/auth/devstorage.read_only",
      "https://www.googleapis.com/auth/devstorage.read_write",
      "https://www.googleapis.com/auth/devstorage.full_control"
    ]
  bucket:
    description:
      - Name of google storage bucket.
    required: yes
  object:
    description:
      - Destination object name(on bucket) to be uploaded or downloaded. This may specify virtual directory structure
        inside google bucket. Required when mode is one of ['get', 'put', 'get_str', 'get_url'].
    required: yes
    default: null
  src:
    description:
      - The source file path when performing PUT operation.
    default: null
  dest:
    description:
      - The destination file path when performing GET operation.
    required: yes
  mode:
    description:
      - This indicates operation to be performed regarding google bucket.
    default: create
    choices: ['get', 'put', 'delete', 'create', 'get_url', 'get_str']
  permission:
    description:
      - Used to set the canned permissions(basic ACLs) on the object/bucket that are created.
    required: false
    default: private
    choices: ['private', 'public-read', 'authenticated-read']
  overwrite:
    description:
      - Used to overwrite existing object in bucket or on local file system. Used with GET and PUT operations.
    default: true
    aliases: ['force']
  region:
    description:
      - Region in which bucket will be created. This is not supported yet, all buckets are by default Multi-regional.
    required: no
  versioning:
    description:
      - Indicates whether versioning is enabled or disabled on bucket.
    default: false
  force_delete:
    description:
      - Indicates if user wants to delete bucket recursively(along with bucket objects). Used when mode is 'delete'.
    required: no
  policy_document:
    description:
      - Path to valid JSON IAM policy document, to attach to bucket. Used with CREATE operation.
    required: no
  expiration:
    description:
      - Time limit (in seconds) for the URL generated when mode=put or mode=get_url.
        This url is only available when public-read is the acl for the object.
    required: false
    default: null
    aliases: [ 'expiry' ]

requirements:
  - "python >= 2.7"
  - "google-cloud-storage >= 1.6.0"
  - "google-auth >= 1.2.0"
  - "google-api-core >= 0.1.1"
'''

EXAMPLES = '''
- name: Create New Bucket
  gce_bucket:
    bucket: testbucket
    mode: create
    versioning: yes
- name: Create bucket with authenticated-read ACL and directories
  gce_bucket:
    bucket: testbucket
    mode: create
    permission: authenticated-read
    object: x-dir/x-dir1
- name: Upload New Object
  gce_bucket:
    bucket: testbucket
    mode: put
    src: /tmp/x.txt
    object: x-dir/x.txt
- name: Download new object
  gce_bucket:
    bucket: testbucket
    mode: get
    dest: /home/centos/x.txt
    object: x-dir/x.txt
- name: Delete object
  gce_bucket:
    bucket: testbucket
    mode: delete
    object: x-dir/x-dir2/x.txt
- name: get file as string
  gce_bucket:
    bucket: testbucket
    mode: get_str
    object: x-dir/x-dir3/x.txt
- name: Get url for remote file
  gce_bucket:
    bucket: testbucket
    mode: get_url
    object: x-dir/x-dir3/x.txt
- name: Delete bucket forcefully
  gce_bucket:
    bucket: testbucket
    mode: delete
    force_delete: yes
- name: Create bucket with policy
  gce_bucket:
    bucket: testbucket
    mode: create
    policy_document: /home/centos/policy.json
'''

RETURN = '''
msg:
  description: Message displayed when bucket/object created/deleted/uploaded/downloaded.
               Compatible with modes ['get', 'put', 'create', 'delete']
  returned: always
  type: str
  sample:
      {
        "changed": true,
        "failed": false,
        "msg": "Bucket created successfully",
        "versioning": false
      }
versioning:
  description: If versioning is enabled on bucket. Returned with 'create' mode.
  returned: always
  type: bool
  sample:
      {
        "changed": true,
        "failed": false,
        "msg": "Bucket created successfully",
        "versioning": true
      }
url:
  description: Download URL(Signed) for bucket object when mode is 'get_url'. Also, returned when object is created.
  returned: on success
  type: str
  sample:
      {
        "changed": true,
        "failed": false,
        "msg": "PUT operation complete",
        "public_url": "https://storage.googleapis.com/testbucket/x-dir%2Fx.txt",
        "url": "https://storage.googleapis.com/testbucket/x-dir%2Fx.txt?Expires=600&GoogleAccessId=testproject.iam.gserviceaccount.com&Signature=testsign"
      }
public_url:
  description: Public URL to access bucket object. Returned with 'put' mode.
  returned: always
  type: str
  sample:
      {
        "changed": true,
        "failed": false,
        "msg": "PUT operation complete",
        "public_url": "https://storage.googleapis.com/testbucket/x-dir%2Fx.txt",
        "url": "https://storage.googleapis.com/testbucket/x-dir%2Fx.txt?Expires=600&GoogleAccessId=testproject.iam.gserviceaccount.com&Signature=testsign"
      }
contents:
  description: Returned when mode is 'get_str', value is bucket object content.
  returned: always
  type: str
  sample:
      {
        "changed": true,
        "contents": "123\n",
        "failed": false,
        "msg": "GET operation complete"
      }
expiration:
  description: Timeout for URL expiry. Returned with 'get_url' mode.
  returned: always
  type: str
  sample:
      {
        "changed": true,
        "expiration": 600,
        "failed": false,
        "url": "https://storage.googleapis.com/testbucket/x-dir%2Fx.txt?Expires=600&GoogleAccessId=testproject.iam.gserviceaccount.com&Signature=testsign"
      }
'''

import os
import base64
from ansible.module_utils.six import binary_type
import json
from ansible.module_utils.gcp import gcp_storage_connect, get_google_cloud_credentials
from ansible.module_utils.basic import AnsibleModule

try:
    from google.api_core import exceptions as gs_except
    HAS_GOOGLE_API_CORE = True
except ImportError:
    HAS_GOOGLE_API_CORE = False


def set_canned_permissions(module, gs, obj):
    try:
        # Fetch current ACL from cloud storage
        obj.acl.reload()
        current_acl_entities = list(obj.acl)
        if module.params.get('permission') == 'private':
            obj.acl.save_predefined('projectPrivate')
        if module.params.get('permission') == 'public-read':
            obj.acl.all().grant_read()
        elif module.params.get('permission') == 'authenticated-read':
            obj.acl.all_authenticated().grant_read()
        obj.acl.save()
    except Exception as e:
        module.fail_json(msg=str(e))
    if current_acl_entities != list(obj.acl):
        return obj, True
    return obj, False


def bucket_check(module, gs, bucket):
    # Return bucket object, if bucket exists. Else, fail.
    try:
        result = gs.get_bucket(bucket)
        return result
    except gs_except.NotFound as e:
        return None
    except Exception as e:
        module.fail_json(msg=str(e))


def keysum(module, gs, bucket_obj, obj):
    key_check = bucket_obj.get_blob(obj)
    if key_check is not None:
        return key_check.crc32c
    return None


def add_bucket_iam_member(module, bucket_obj, role, members):

    changed = False
    role_flag = 0
    policy = bucket_obj.get_iam_policy()
    for existing_role in policy:
        if role == existing_role:
            role_flag = 1
            break

    if role_flag == 1:
        existing_members = policy[role]
        if not sorted(list(existing_members)) == sorted(members):
            for member in list(existing_members):
                if member not in members:
                    policy[role].discard(member)
            for member in members:
                if member not in list(existing_members):
                    policy[role].add(member)
            changed = True
        else:
            return False
    else:
        for member in members:
            policy[role].add(member)
        changed = True
    if changed is True:
        try:
            bucket_obj.set_iam_policy(policy)
        except Exception as e:
            module.fail_json(msg=str(e))
    return changed


def create_bucket(module, gs, bucket):
    changed = False
    changed_for_new_create = False
    permission = module.params.get('permission')
    policy = module.params.get('policy_document')
    versioning = module.params.get('versioning')
    bucket_obj = bucket_check(module, gs, bucket)
    versioning_status = False
    if not bucket_obj:
        try:
            bucket_obj = gs.create_bucket(bucket)
            changed_for_new_create = True
        except Exception as e:
            module.fail_json(msg=str(e))
    if permission:
        bucket_obj, changed = set_canned_permissions(module, gs, bucket_obj)
    if not changed and changed_for_new_create:
        changed = True

    if policy:
        if not path_check(policy):
            module.fail_json(msg="IAM policy json file does not exist")
        try:
            with open(policy, 'r') as json_data:
                policy = json.load(json_data)
        except IOError as e:
            module.fail_json(msg="I/O error({0}): {1}".format(e.errno, e.strerror))
        # check if anything needs to be modified in existing policy
        changed_policy = 0
        for item in policy['bindings']:
            result = add_bucket_iam_member(module, bucket_obj, item['role'], item['members'])
            if result is True:
                changed_policy = changed_policy + 1
        if changed_policy > 0:
            changed = True
    versioning_status = bucket_obj.versioning_enabled
    if versioning is not None:
        if versioning and versioning_status is False:
            try:
                bucket_obj.versioning_enabled = versioning
                changed = True
                versioning_status = bucket_obj.versioning_enabled
                bucket_obj.update()
            except Exception as e:
                module.fail_json(msg=str(e))
        elif not versioning and versioning_status is True:
            try:
                bucket_obj.versioning_enabled = versioning
                changed = True
                versioning_status = bucket_obj.versioning_enabled
                bucket_obj.update()
            except Exception as e:
                module.fail_json(msg=str(e))
    return changed, versioning_status


def delete_bucket(module, bucket, force_delete):
    # Delete bucket objects, if bucket not empty
    if force_delete:
        try:
            bucket_blobs = bucket.list_blobs(versions=True)
            blobs_list = []
            for blob in list(bucket_blobs):
                blobs_list.append(blob)
            for blob in blobs_list:
                blob.delete()
        except gs_except.Forbidden:
            module.fail_json(msg="You don't have permission to delete bucket object '" + blob + "'")
        except Exception as e:
            module.fail_json(msg=str(e))
    try:
        bucket.delete(force=force_delete)
        return True
    except gs_except.Conflict:
        module.fail_json(msg="Cannot delete bucket '" + bucket.name + "' as it is not empty")
    except gs_except.Forbidden:
        module.fail_json(msg="You don't have permission to delete bucket '" + bucket.name + "'")
    except Exception as e:
        module.fail_json(msg=str(e))


def key_check(module, gs, bucket, obj):
    bucket = bucket_check(module, gs, bucket)
    try:
        # check if given object exists
        key_blob = bucket.blob(obj).exists()
    except gs_except.NotFound:
        module.fail_json(msg="Given object does not exist in bucket")
    if key_blob:
        if module.params.get('mode') != 'get':
            set_canned_permissions(module, gs, bucket.get_blob(obj))
        return True
    return False


def path_check(path):
    return os.path.exists(path)


def crc32c_for_local_file(filepath):
    import crcmod
    file_bytes = open(filepath, 'rb').read()
    crc32c = crcmod.predefined.Crc('crc-32c')
    crc32c.update(file_bytes)
    crc32c.crcValue
    crc32c = base64.b64encode(crc32c.digest())
    return crc32c


def create_bucket_folder(module, gs, bucket, obj):
    permission = module.params.get('permission')
    try:
        bucket = bucket_check(module, gs, bucket)
        key = bucket.blob(obj)
        key.upload_from_string('')
        if permission and permission != 'private':
            key_obj = set_canned_permissions(module, gs, key)
        module.exit_json(msg="Virtual directory %s created in bucket %s" % (obj, bucket.name), changed=True)
    except Exception as e:
        module.fail_json(msg=str(e))


def delete_object_blob(module, gs, bucket, obj):
    try:
        bucket = gs.get_bucket(bucket)
        blob = bucket.blob(obj)
        blob.delete()
        module.exit_json(msg="Object deleted from bucket.", changed=True)
    except gs_except.NotFound:
        module.fail_json(msg="Object '" + obj + "' not found in bucket '" + bucket.name + "'")
    except Exception as e:
        module.fail_json(msg=str(e))


def download_object_as_string(module, gs, bucket, obj):
    try:
        bucket = bucket_check(module, gs, bucket)
        blob = bucket.blob(obj)
        contents = blob.download_as_string()
        module.exit_json(msg="GET operation complete", contents=contents, changed=True)
    except gs_except.Forbidden:
        module.fail_json(msg="You don't have permission to access object '" + obj + "'")
    except Exception as e:
        module.fail_json(msg=str(e))


def get_download_url(module, gs, bucket, obj, expiry):
    try:
        bucket = bucket_check(module, gs, bucket)
        blob = bucket.blob(obj)
        url = blob.generate_signed_url(expiry)
        module.exit_json(url=url, expiration=expiry, changed=True)
    except gs_except.Forbidden:
        module.fail_json(msg="You don't have permission to generate url for object '" + obj + "'")
    except Exception as e:
        module.fail_json(msg=str(e))


def download_gs_object(module, gs, bucket, obj, dest):
    try:
        bucket = bucket_check(module, gs, bucket)
        key = bucket.get_blob(obj)
        key.download_to_filename(dest)
        module.exit_json(msg="GET operation complete", changed=True)
    except gs_except.NotFound:
        module.fail_json(msg="Object '" + obj + "' not found in bucket '" + bucket.name + "'")
    except Exception as e:
        module.fail_json(msg=str(e))


def get_operation(module, gs, bucket, obj, overwrite, dest):
    bucket_obj = bucket_check(module, gs, bucket)
    crc2c_remote = keysum(module, gs, bucket_obj, obj)
    crc2c_local = crc32c_for_local_file(dest)
    if crc2c_local == crc2c_remote:
        module.exit_json(msg="Remote and local objects are identical", changed=False)
    else:
        if not overwrite:
            module.exit_json(msg="WARNING: Checksums do not match. Use overwrite parameter to force download.", failed=True)
        else:
            download_gs_object(module, gs, bucket, obj, dest)


def upload_gs_object(module, gs, bucket, obj, src, expiry):
    permission = module.params.get('permission')
    try:
        bucket = bucket_check(module, gs, bucket)
        key = bucket.blob(obj)
        key.upload_from_filename(src)
        if permission and permission != 'private':
            set_canned_permissions(module, gs, key)
        url = key.generate_signed_url(expiry)
        public_url = key.public_url
        if isinstance(url, binary_type):
            url = url.decode('utf-8')
        module.exit_json(msg="PUT operation complete", url=url, changed=True, public_url=public_url)
    except gs_except.Forbidden:
        module.fail_json(msg="You don't have permission to create object '" + obj + "'")
    except Exception as e:
        module.fail_json(msg=str(e))


def put_operation(module, gs, bucket, obj, overwrite, src, expiration):
    # Lets check to see if bucket exists to get ground truth.
    bucket_obj = bucket_check(module, gs, bucket)
    if not bucket_obj:
        create_bucket(module, gs, bucket)
        upload_gs_object(module, gs, bucket, obj, src, expiration)
    else:
        key_obj = key_check(module, gs, bucket, obj)
        if key_obj:
            crc32c_remote = keysum(module, gs, bucket_obj, obj)
            crc32c_local = crc32c_for_local_file(src)
            if crc32c_remote == crc32c_local:
                module.exit_json(msg="Local and remote objects are identical", changed=False)
            else:
                if not overwrite:
                    module.exit_json(msg="WARNING: Checksums do not match. Use overwrite parameter to force upload.", failed=True)
                else:
                    upload_gs_object(module, gs, bucket, obj, src, expiration)
        else:
            upload_gs_object(module, gs, bucket, obj, src, expiration)


def delete_operation(module, gs, bucket, obj, force_delete):
    bucket_obj = bucket_check(module, gs, bucket)
    if bucket and not obj:
        if bucket_obj:
            module.exit_json(msg="Bucket %s and all keys have been deleted." % bucket, changed=delete_bucket(module, bucket_obj, force_delete))
        else:
            module.exit_json(msg="Bucket does not exist.", changed=False)
    if bucket and obj:
        if bucket_check(module, gs, bucket):
            if key_check(module, gs, bucket, obj):
                module.exit_json(msg="Object has been deleted.", changed=delete_object_blob(module, gs, bucket, obj))
            else:
                module.exit_json(msg="Object does not exist.", changed=False)
        else:
            module.exit_json(msg="Bucket does not exist.", changed=False)
    else:
        module.fail_json(msg="Bucket or Bucket & object  parameter is required.", failed=True)


def create_operation(module, gs, bucket, obj):

    changed = False
    if bucket:
        changed, versioning_status = create_bucket(module, gs, bucket)
        if not obj:
            if not changed:
                module.exit_json(msg="Bucket '" + bucket + "' already exists.", changed=False, versioning=versioning_status)
            module.exit_json(msg="Bucket created successfully", changed=changed, versioning=versioning_status)
        else:
            dirobj = obj if obj.endswith('/') else (obj + "/")

            if key_check(module, gs, bucket, dirobj):
                module.exit_json(msg="Bucket %s and key %s already exists." % (bucket, obj), changed=changed)
            else:
                create_bucket_folder(module, gs, bucket, dirobj)


def main():
    argument_spec = dict(
        credentials_file=dict(type='path'),
        service_account_email=dict(),
        service_account_permissions=dict(type='list'),
        project_id=dict(),
        bucket=dict(required=True),
        object=dict(default=None, type='path'),
        src=dict(default=None),
        dest=dict(default=None, type='path'),
        expiration=dict(type='int', default=600, aliases=['expiry']),
        mode=dict(choices=['get', 'put', 'delete', 'create', 'get_url', 'get_str'], required=True),
        permission=dict(choices=['private', 'public-read', 'authenticated-read'], default='private'),
        overwrite=dict(default=True, type='bool', aliases=['force']),
        region=dict(default='US', type='str'),
        versioning=dict(default='no', type='bool'),
        force_delete=dict(default='no', type='bool'),
        policy_document=dict(required=False, default=None, type='json')
    )
    module = AnsibleModule(
        argument_spec=argument_spec,
        required_if=[
            ['state', 'put', ['src', 'bucket', 'object']],
            ['state', 'get', ['dest', 'bucket', 'object']],
        ]
    )

    if not HAS_GOOGLE_API_CORE:
        module.fail_json(msg="Please install google-api-core to run this module.")

    bucket = module.params.get('bucket')
    obj = module.params.get('object')
    src = module.params.get('src')
    dest = module.params.get('dest')
    mode = module.params.get('mode')
    expiry = module.params.get('expiration')
    overwrite = module.params.get('overwrite')
    force_delete = module.params.get('force_delete')
    service_account_permissions = module.params.get('service_account_permissions')

    credentials, conn_params = get_google_cloud_credentials(module, service_account_permissions)
    project = conn_params.get('project_id', None)
    gs = gcp_storage_connect(module, credentials, conn_params, service_account_permissions)

    if mode == 'create':
        create_operation(module, gs, bucket, obj)

    if mode == 'delete':
        delete_operation(module, gs, bucket, obj, force_delete)

    if mode == 'get':
        if not bucket_check(module, gs, bucket):
            module.fail_json(msg="Target bucket cannot be found", failed=True)
        if not key_check(module, gs, bucket, obj):
            module.fail_json(msg="Target object/key cannot be found", failed=True)
        if not path_check(dest):
            download_gs_object(module, gs, bucket, obj, dest)
        else:
            get_operation(module, gs, bucket, obj, overwrite, dest)

    if mode == 'put':
        if not path_check(src):
            module.fail_json(msg="Local object for PUT does not exist", failed=True)
        put_operation(module, gs, bucket, obj, overwrite, src, expiry)

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
                download_object_as_string(module, gs, bucket, obj)
            else:
                module.fail_json(msg="Key/Bucket does not exist", failed=True)
        else:
            module.fail_json(msg="Bucket and Object parameters must be set", failed=True)


if __name__ == '__main__':
    main()
