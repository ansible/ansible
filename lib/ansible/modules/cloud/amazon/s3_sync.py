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
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: s3_sync
short_description: Efficiently upload multiple files to S3
description:
     - The S3 module is great, but it is very slow for a large volume of files- even a dozen will be noticeable. In addition to speed, it handles globbing,
       inclusions/exclusions, mime types, expiration mapping, recursion, cache control and smart directory mapping.
version_added: "2.3"
options:
  mode:
    description:
    - sync direction.
    default: 'push'
    choices: [ push ]
  file_change_strategy:
    description:
    - Difference determination method to allow changes-only syncing. Unlike rsync, files are not patched- they are fully skipped or fully uploaded.
    - date_size will upload if file sizes don't match or if local file modified date is newer than s3's version
    - checksum will compare etag values based on s3's implementation of chunked md5s.
    - force will always upload all files.
    required: false
    default: 'date_size'
    choices: [ force, checksum, date_size ]
  bucket:
    description:
    - Bucket name.
    required: true
  key_prefix:
    description:
    - In addition to file path, prepend s3 path with this prefix. Module will add slash at end of prefix if necessary.
    required: false
  file_root:
    description:
    - File/directory path for synchronization. This is a local path.
    - This root path is scrubbed from the key name, so subdirectories will remain as keys.
    required: true
  permission:
    description:
    - Canned ACL to apply to synced files.
    - Changing this ACL only changes newly synced files, it does not trigger a full reupload.
    required: false
    choices: [ '', private, public-read, public-read-write, authenticated-read, aws-exec-read, bucket-owner-read, bucket-owner-full-control ]
  mime_map:
    description:
    - >
      Dict entry from extension to MIME type. This will override any default/sniffed MIME type.
      For example C({".txt": "application/text", ".yml": "application/text"})
    required: false
  include:
    description:
    - Shell pattern-style file matching.
    - Used before exclude to determine eligible files (for instance, only "*.gif")
    - For multiple patterns, comma-separate them.
    required: false
    default: "*"
  exclude:
    description:
    - Shell pattern-style file matching.
    - Used after include to remove files (for instance, skip "*.txt")
    - For multiple patterns, comma-separate them.
    required: false
    default: ".*"
  cache_control:
    description:
    - This is a string.
    - Cache-Control header set on uploaded objects.
    - Directives are separated by commas.
    required: false
    version_added: "2.4"
  delete:
    description:
    - Remove remote files that exist in bucket but are not present in the file root.
    required: false
    default: no
    version_added: "2.4"
    type: bool

requirements:
  - boto3 >= 1.4.4
  - botocore
  - python-dateutil

author: Ted Timmons (@tedder)
extends_documentation_fragment:
- aws
- ec2
'''

EXAMPLES = '''
- name: basic upload
  s3_sync:
    bucket: tedder
    file_root: roles/s3/files/

- name: all the options
  s3_sync:
    bucket: tedder
    file_root: roles/s3/files
    mime_map:
      .yml: application/text
      .json: application/text
    key_prefix: config_files/web
    file_change_strategy: force
    permission: public-read
    cache_control: "public, max-age=31536000"
    include: "*"
    exclude: "*.txt,.*"
'''

RETURN = '''
filelist_initial:
  description: file listing (dicts) from initial globbing
  returned: always
  type: list
  sample: [{
                "bytes": 151,
                "chopped_path": "policy.json",
                "fullpath": "roles/cf/files/policy.json",
                "modified_epoch": 1477416706
           }]
filelist_local_etag:
  description: file listing (dicts) including calculated local etag
  returned: always
  type: list
  sample: [{
                "bytes": 151,
                "chopped_path": "policy.json",
                "fullpath": "roles/cf/files/policy.json",
                "mime_type": "application/json",
                "modified_epoch": 1477416706,
                "s3_path": "s3sync/policy.json"
           }]
filelist_s3:
  description: file listing (dicts) including information about previously-uploaded versions
  returned: always
  type: list
  sample: [{
                "bytes": 151,
                "chopped_path": "policy.json",
                "fullpath": "roles/cf/files/policy.json",
                "mime_type": "application/json",
                "modified_epoch": 1477416706,
                "s3_path": "s3sync/policy.json"
           }]
filelist_typed:
  description: file listing (dicts) with calculated or overridden mime types
  returned: always
  type: list
  sample: [{
                "bytes": 151,
                "chopped_path": "policy.json",
                "fullpath": "roles/cf/files/policy.json",
                "mime_type": "application/json",
                "modified_epoch": 1477416706
           }]
filelist_actionable:
  description: file listing (dicts) of files that will be uploaded after the strategy decision
  returned: always
  type: list
  sample: [{
                "bytes": 151,
                "chopped_path": "policy.json",
                "fullpath": "roles/cf/files/policy.json",
                "mime_type": "application/json",
                "modified_epoch": 1477931256,
                "s3_path": "s3sync/policy.json",
                "whysize": "151 / 151",
                "whytime": "1477931256 / 1477929260"
           }]
uploaded:
  description: file listing (dicts) of files that were actually uploaded
  returned: always
  type: list
  sample: [{
                "bytes": 151,
                "chopped_path": "policy.json",
                "fullpath": "roles/cf/files/policy.json",
                "s3_path": "s3sync/policy.json",
                "whysize": "151 / 151",
                "whytime": "1477931637 / 1477931489"
           }]

'''

import datetime
import fnmatch
import hashlib
import mimetypes
import os
import stat as osstat  # os.stat constants
import traceback

# import module snippets
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ec2 import camel_dict_to_snake_dict, ec2_argument_spec, boto3_conn, get_aws_connection_info, HAS_BOTO3, boto_exception
from ansible.module_utils._text import to_text

try:
    from dateutil import tz
    HAS_DATEUTIL = True
except ImportError:
    HAS_DATEUTIL = False

try:
    import botocore
except ImportError:
    # Handled by imported HAS_BOTO3
    pass


# the following function, calculate_multipart_etag, is from tlastowka
# on github and is used under its (compatible) GPL license. So this
# license applies to the following function.
# source: https://github.com/tlastowka/calculate_multipart_etag/blob/master/calculate_multipart_etag.py
#
# calculate_multipart_etag  Copyright (C) 2015
#      Tony Lastowka <tlastowka at gmail dot com>
#      https://github.com/tlastowka
#
#
# calculate_multipart_etag is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# calculate_multipart_etag is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with calculate_multipart_etag.  If not, see <http://www.gnu.org/licenses/>.

DEFAULT_CHUNK_SIZE = 5 * 1024 * 1024


def calculate_multipart_etag(source_path, chunk_size=DEFAULT_CHUNK_SIZE):
    """
    calculates a multipart upload etag for amazon s3

    Arguments:

    source_path -- The file to calculate the etag for
    chunk_size -- The chunk size to calculate for.
    """

    md5s = []

    with open(source_path, 'rb') as fp:
        while True:

            data = fp.read(chunk_size)

            if not data:
                break
            md5s.append(hashlib.md5(data))

    if len(md5s) == 1:
        new_etag = '"{0}"'.format(md5s[0].hexdigest())
    else:  # > 1
        digests = b"".join(m.digest() for m in md5s)

        new_md5 = hashlib.md5(digests)
        new_etag = '"{0}-{1}"'.format(new_md5.hexdigest(), len(md5s))

    return new_etag


def gather_files(fileroot, include=None, exclude=None):
    ret = []
    for (dirpath, dirnames, filenames) in os.walk(fileroot):
        for fn in filenames:
            fullpath = os.path.join(dirpath, fn)
            # include/exclude
            if include:
                found = False
                for x in include.split(','):
                    if fnmatch.fnmatch(fn, x):
                        found = True
                if not found:
                    # not on the include list, so we don't want it.
                    continue

            if exclude:
                found = False
                for x in exclude.split(','):
                    if fnmatch.fnmatch(fn, x):
                        found = True
                if found:
                    # skip it, even if previously included.
                    continue

            chopped_path = os.path.relpath(fullpath, start=fileroot)
            fstat = os.stat(fullpath)
            f_size = fstat[osstat.ST_SIZE]
            f_modified_epoch = fstat[osstat.ST_MTIME]
            ret.append({
                'fullpath': fullpath,
                'chopped_path': chopped_path,
                'modified_epoch': f_modified_epoch,
                'bytes': f_size,
            })
        # dirpath = path *to* the directory
        # dirnames = subdirs *in* our directory
        # filenames
    return ret


def calculate_s3_path(filelist, key_prefix=''):
    ret = []
    for fileentry in filelist:
        # don't modify the input dict
        retentry = fileentry.copy()
        retentry['s3_path'] = os.path.join(key_prefix, fileentry['chopped_path'])
        ret.append(retentry)
    return ret


def calculate_local_etag(filelist, key_prefix=''):
    '''Really, "calculate md5", but since AWS uses their own format, we'll just call
       it a "local etag". TODO optimization: only calculate if remote key exists.'''
    ret = []
    for fileentry in filelist:
        # don't modify the input dict
        retentry = fileentry.copy()
        retentry['local_etag'] = calculate_multipart_etag(fileentry['fullpath'])
        ret.append(retentry)
    return ret


def determine_mimetypes(filelist, override_map):
    ret = []
    for fileentry in filelist:
        retentry = fileentry.copy()
        localfile = fileentry['fullpath']

        # reminder: file extension is '.txt', not 'txt'.
        _, file_extension = os.path.splitext(localfile)
        if override_map and override_map.get(file_extension):
            # override? use it.
            retentry['mime_type'] = override_map[file_extension]
        else:
            # else sniff it
            retentry['mime_type'], retentry['encoding'] = mimetypes.guess_type(localfile, strict=False)

        # might be None or '' from one of the above. Not a great type but better than nothing.
        if not retentry['mime_type']:
            retentry['mime_type'] = 'application/octet-stream'

        ret.append(retentry)

    return ret


def head_s3(s3, bucket, s3keys):
    retkeys = []
    for entry in s3keys:
        retentry = entry.copy()
        # don't modify the input dict
        try:
            retentry['s3_head'] = s3.head_object(Bucket=bucket, Key=entry['s3_path'])
        except botocore.exceptions.ClientError as err:
            if (hasattr(err, 'response') and
                    'ResponseMetadata' in err.response and
                    'HTTPStatusCode' in err.response['ResponseMetadata'] and
                    str(err.response['ResponseMetadata']['HTTPStatusCode']) == '404'):
                pass
            else:
                raise Exception(err)
            # error_msg = boto_exception(err)
            # return {'error': error_msg}
        retkeys.append(retentry)
    return retkeys


def filter_list(s3, bucket, s3filelist, strategy):
    keeplist = list(s3filelist)

    for e in keeplist:
        e['_strategy'] = strategy

    # init/fetch info from S3 if we're going to use it for comparisons
    if not strategy == 'force':
        keeplist = head_s3(s3, bucket, s3filelist)

    # now actually run the strategies
    if strategy == 'checksum':
        for entry in keeplist:
            if entry.get('s3_head'):
                # since we have a remote s3 object, compare the values.
                if entry['s3_head']['ETag'] == entry['local_etag']:
                    # files match, so remove the entry
                    entry['skip_flag'] = True
                else:
                    # file etags don't match, keep the entry.
                    pass
            else:  # we don't have an etag, so we'll keep it.
                pass
    elif strategy == 'date_size':
        for entry in keeplist:
            if entry.get('s3_head'):
                # fstat = entry['stat']
                local_modified_epoch = entry['modified_epoch']
                local_size = entry['bytes']

                # py2's datetime doesn't have a timestamp() field, so we have to revert to something more awkward.
                # remote_modified_epoch = entry['s3_head']['LastModified'].timestamp()
                remote_modified_datetime = entry['s3_head']['LastModified']
                delta = (remote_modified_datetime - datetime.datetime(1970, 1, 1, tzinfo=tz.tzutc()))
                remote_modified_epoch = delta.seconds + (delta.days * 86400)

                remote_size = entry['s3_head']['ContentLength']

                entry['whytime'] = '{0} / {1}'.format(local_modified_epoch, remote_modified_epoch)
                entry['whysize'] = '{0} / {1}'.format(local_size, remote_size)

                if local_modified_epoch <= remote_modified_epoch and local_size == remote_size:
                    entry['skip_flag'] = True
            else:
                entry['why'] = "no s3_head"
    # else: probably 'force'. Basically we don't skip with any with other strategies.
    else:
        pass

    # prune 'please skip' entries, if any.
    return [x for x in keeplist if not x.get('skip_flag')]


def upload_files(s3, bucket, filelist, params):
    ret = []
    for entry in filelist:
        args = {
            'ContentType': entry['mime_type']
        }
        if params.get('permission'):
            args['ACL'] = params['permission']
        if params.get('cache_control'):
            args['CacheControl'] = params['cache_control']
        # if this fails exception is caught in main()
        s3.upload_file(entry['fullpath'], bucket, entry['s3_path'], ExtraArgs=args, Callback=None, Config=None)
        ret.append(entry)
    return ret


def remove_files(s3, sourcelist, params):
    bucket = params.get('bucket')
    key_prefix = params.get('key_prefix')
    paginator = s3.get_paginator('list_objects_v2')
    current_keys = set(x['Key'] for x in paginator.paginate(Bucket=bucket, Prefix=key_prefix).build_full_result().get('Contents', []))
    keep_keys = set(to_text(source_file['s3_path']) for source_file in sourcelist)
    delete_keys = list(current_keys - keep_keys)

    # can delete 1000 objects at a time
    groups_of_keys = [delete_keys[i:i + 1000] for i in range(0, len(delete_keys), 1000)]
    for keys in groups_of_keys:
        s3.delete_objects(Bucket=bucket, Delete={'Objects': [{'Key': key} for key in keys]})

    return delete_keys


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(dict(
        mode=dict(choices=['push'], default='push'),
        file_change_strategy=dict(choices=['force', 'date_size', 'checksum'], default='date_size'),
        bucket=dict(required=True),
        key_prefix=dict(required=False, default=''),
        file_root=dict(required=True, type='path'),
        permission=dict(required=False, choices=['private', 'public-read', 'public-read-write', 'authenticated-read',
                                                 'aws-exec-read', 'bucket-owner-read', 'bucket-owner-full-control']),
        retries=dict(required=False),
        mime_map=dict(required=False, type='dict'),
        exclude=dict(required=False, default=".*"),
        include=dict(required=False, default="*"),
        cache_control=dict(required=False, default=''),
        delete=dict(required=False, type='bool', default=False),
        # future options: encoding, metadata, storage_class, retries
    )
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
    )

    if not HAS_DATEUTIL:
        module.fail_json(msg='dateutil required for this module')

    if not HAS_BOTO3:
        module.fail_json(msg='boto3 required for this module')

    result = {}
    mode = module.params['mode']

    region, ec2_url, aws_connect_kwargs = get_aws_connection_info(module, boto3=True)
    if not region:
        module.fail_json(msg="Region must be specified")
    s3 = boto3_conn(module, conn_type='client', resource='s3', region=region, endpoint=ec2_url, **aws_connect_kwargs)

    if mode == 'push':
        try:
            result['filelist_initial'] = gather_files(module.params['file_root'], exclude=module.params['exclude'], include=module.params['include'])
            result['filelist_typed'] = determine_mimetypes(result['filelist_initial'], module.params.get('mime_map'))
            result['filelist_s3'] = calculate_s3_path(result['filelist_typed'], module.params['key_prefix'])
            result['filelist_local_etag'] = calculate_local_etag(result['filelist_s3'])
            result['filelist_actionable'] = filter_list(s3, module.params['bucket'], result['filelist_local_etag'], module.params['file_change_strategy'])
            result['uploads'] = upload_files(s3, module.params['bucket'], result['filelist_actionable'], module.params)

            if module.params['delete']:
                result['removed'] = remove_files(s3, result['filelist_local_etag'], module.params)

            # mark changed if we actually upload something.
            if result.get('uploads') or result.get('removed'):
                result['changed'] = True
            # result.update(filelist=actionable_filelist)
        except botocore.exceptions.ClientError as err:
            error_msg = boto_exception(err)
            module.fail_json(msg=error_msg, exception=traceback.format_exc(), **camel_dict_to_snake_dict(err.response))

    module.exit_json(**result)


if __name__ == '__main__':
    main()
