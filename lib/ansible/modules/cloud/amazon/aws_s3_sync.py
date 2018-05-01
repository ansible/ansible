#!/usr/bin/python

# Copyright (c) 2018 Paul Arthur
# Copyright (c) 2016 Ted Timmons
# Copyright (c) 2016-2017 Red Hat, Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
module: aws_s3_sync
short_description: Efficiently sync files between S3 and a local directory
description:
     - Sync an entire directory tree at once.
version_added: "2.10"
options:
  direction:
    description:
      - Determines whether to pull from S3 to local storage or push from local storage to S3.
    type: str
    required: true
    choices: [ push, pull ]
  overwrite:
    description:
      - Determines whether to overwrite existing files or objects.
      - For C(different), the attributes set in I(diff_attributes) will be compared when deciding whether the sync candidates are the same.
    type: str
    required: false
    default: never
    choices: [ always, never, different, larger, newer ]
  diff_attributes:
    description:
      - A list of attributes to check when deciding whether sync candidates are
        different. Including C(e_tag) will calculate a local ETag based on the
        file contents. This requires MD5 support (unavailable on systems running
        in FIPS mode) and is not guaranteed to be the same ETag Amazon will use
        for the file once it's uploaded. See the notes about the ETag header at
        U(https://docs.aws.amazon.com/AmazonS3/latest/API/RESTCommonResponseHeaders.html).
    type: list
    default: [ e_tag ]
  bucket:
    description:
      - Target bucket.
    type: str
    required: true
  prefix:
    description:
      - Limits the affected objects to those whose keys match this prefix.
      - Added to local files when determining their keys.
    type: str
    required: false
  path:
    description:
      - Local directory path for synchronization.
    type: path
    required: true
  permission:
    description:
      - Canned ACL to apply to synced objects.
      - This only affects newly synced objects, it does not modify existing objects.
    type: str
    required: false
    choices: [ private, public-read, public-read-write, authenticated-read, aws-exec-read, bucket-owner-read, bucket-owner-full-control ]
  mime_types_map:
    description:
      - A dictionary mapping file suffixes to MIME types, used when guessing the MIME type of local files.
      - If I(mime_override) is enabled, this will replace the library's default mappings instead of adding to them.
    type: dict
    default: {}
  mime_encodings_map:
    description:
      - A dictionary mapping file suffixes to encoding types, used when guessing the MIME type of local files.
      - If C(mime_override) is enabled, this will replace the library's default maps instead of adding to them.
    type: dict
    default: {}
  mime_override:
    description:
      - Controls whether I(mime_types_map) and I(mime_encodings_map) are added to the system defaults or used to completely replace them.
    type: bool
    default: no
  mime_strict:
    description:
      - Disables detection of some common but non-standard MIME types. Has no effect if I(mime_override) is enabled.
    type: bool
    default: no
  patterns:
    description:
      - List of patterns to include. Only files with matching filenames will be synced.
    type: list
    required: false
    aliases: [ pattern ]
  excludes:
    description:
      - List of patterns to exclude. Can be used on its own or as a further constraint after I(patterns).
    type: list
    required: no
    aliases: [ exclude ]
  use_regex:
    description:
      - Treat I(patterns) and I(excludes) as Python regular expressions instead of shell globs.
    required: false
    type: bool
    default: no
  hidden:
    description:
      - Set this to true to include hidden files, otherwise they'll be ignored.
    type: bool
    default: no
  metadata:
    description:
      - A dictionary containing metadata for the uploaded objects.
    type: dict
    required: false
  delete:
    description:
      - Remove objects that exist in the destination but are not present in the source.
    required: false
    type: bool
    default: no
  directory_mode:
    description:
      - Mode to set on newly created local directories.
    required: false

requirements:
  - boto3 >= 1.4.4
  - botocore
  - dateutil

notes:
  - File attributes (e.g. I(mode) and I(owner)) are only applied to synced or
    added files and newly created directories. Files skipped due to the
    I(overwrite) setting will not be modified in any way.

author:
  - Ted Timmons (@tedder)
  - Paul Arthur (@flowerysong)

extends_documentation_fragment:
  - aws
  - ec2
  - files
'''

EXAMPLES = '''
- name: Upload to a bucket
  aws_s3_sync:
    direction: push
    bucket: example.com
    path: /srv/www/example.com

- name: Act more like s3_sync
  aws_s3_sync:
    direction: push
    bucket: example.com
    path: /srv/www/example.com
    overwrite: different
    diff_attributes:
      - last_modified
      - size

- name: Upload with more options
  aws_s3_sync:
    direction: push
    bucket: example.com
    path: /srv/www/example.com/awesomeapp
    mime_types_map:
      '.yml': application/text
      '.json': application/text
    prefix: awesomeapp
    overwrite: always
    permission: public-read
    metadata:
      server_side_encryption: AES256

- name: Download from a bucket
  aws_s3_sync:
    direction: pull
    bucket: example.com
    path: /srv/www/example.com
    includes:
      - '*.html'
      - '*.png'
    excludes: face*.png
    overwrite: different
    mode: '0640'
    directory_mode: '0750'
    owner: www-data
    group: www-data
'''

RETURN = '''
objects:
  description: a list of files and objects
  returned: always
  type: complex
  contains:
    key:
      description: The S3 object key
      returned: always
      type: str
      sample: foo
    path:
      description: The local file path
      returned: always
      type: str
      sample: /path/to/foo
    state:
      description: Action applied
      returned: always
      type: str
      sample:
        - unchanged
        - deleted
        - skipped
        - synced
        - added
    local:
      description: Initial local file attributes
      returned: When the file already existed locally
      type: complex
      contains:
        size:
          description: Size of the file in bytes
          returned: always
          type: int
        last_modified:
          description: Modification time of the file
          returned: always
          type: str
          sample: "2018-04-25T09:35:46+00:00"
        content_type:
          description: Mapped or guessed MIME type of the file
          returned: always
          type: str
          sample: application/octet-stream
        content_encoding:
          description: Mapped or guessed MIME encoding of the file
          returned: always
          type: str
          sample: bzip2
        e_tag:
          description: Calculated local ETag
          returned: When the object already existed in S3 and e_tag is included in diff_attributes
          type: str
          sample: '"fffcc0bc5495e11184419846975badc9"'
    s3:
      description: Initial S3 object attributes
      returned: When the object already existed in S3
      type: complex
      contains:
        size:
          description: Size of the file in bytes
          returned: always
          type: int
        last_modified:
          description: Modification time of the object
          returned: always
          type: str
          sample: "2018-04-24T15:57:34+00:00"
        e_tag:
          description: HTTP ETag of the object
          returned: always
          type: str
          sample: '"fffcc0bc5495e11184419846975badc9"'
        storage_class:
          description: Storage class of the object
          returned: always
          type: str
          sample: STANDARD
'''

import hashlib
import mimetypes
import os
import re
import time
import tempfile
import traceback

from copy import copy
from datetime import datetime
from fnmatch import fnmatch
from stat import ST_MTIME, ST_SIZE

from ansible.module_utils.aws.core import AnsibleAWSModule
from ansible.module_utils.aws.s3 import dict_to_s3_extra_args, calculate_etag, HAS_MD5
from ansible.module_utils.basic import missing_required_lib
from ansible.module_utils.ec2 import AWSRetry
from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict
from ansible.module_utils._text import to_bytes

HAS_DATEUTIL = True
HAS_DATEUTIL_EXC = None
try:
    from dateutil import tz
except ImportError:
    HAS_DATEUTIL = False
    HAS_DATEUTIL_EXC = traceback.format_exc()

try:
    from botocore.exceptions import BotoCoreError, ClientError
except ImportError:
    pass    # Handled by AnsibleAWSModule


class S3Syncer(object):
    def __init__(self, module):
        self.module = module
        self.check_mode = module.check_mode
        self.params = module.params
        self.changed = False

        params = self.params
        self.file_args = module._module.load_file_common_arguments(params)
        self.directory_args = copy(self.file_args)
        self.directory_args['mode'] = params['directory_mode']

        self.mode = params['direction']
        self.bucket = params['bucket']
        self.path = params['path']
        self.prefix = params['prefix']
        self.patterns = params['patterns']
        self.excludes = params['excludes']
        self.delete = params['delete']

        self.mimetypes = mimetypes.MimeTypes()
        if params['mime_override']:
            self.mimetypes.encodings_map = params['mime_encodings_map']
            self.mimetypes.types_map = ({}, params['mime_types_map'])
        else:
            self.mimetypes.encodings_map.update(params['mime_encodings_map'])
            self.mimetypes.types_map[1].update(params['mime_types_map'])

        self.s3 = module.client('s3')
        self.objects = []

    def _match_patterns(self, candidate, patterns):
        for pattern in patterns:
            if self.params['use_regex']:
                if re.compile(pattern).match(candidate):
                    return True
            elif fnmatch(candidate, pattern):
                return True
        return False

    def _match_all_patterns(self, candidate):
        if candidate.startswith('.') and not self.params['hidden']:
            return False
        if self.patterns and not self._match_patterns(candidate, self.patterns):
            return False
        if self.excludes and self._match_patterns(candidate, self.excludes):
            return False
        return True

    @AWSRetry.jittered_backoff()
    def _list_objects(self):
        paginator = self.s3.get_paginator('list_objects_v2')
        return paginator.paginate(Bucket=self.bucket, Prefix=self.prefix).build_full_result()

    def _new_object(self, key):
        new_object = {
            'key': key,
            'state': 'unchanged'
        }
        self.objects.append(new_object)
        return new_object

    def _lookup_object_by_key(self, key):
        for obj in self.objects:
            if obj['key'] == key:
                return obj
        return self._new_object(key)

    def _check_for_skip(self):
        for entry in self.objects:
            if 's3' in entry and 'local' in entry:
                if self.mode == 'push':
                    source = entry['local']
                    dest = entry['s3']
                else:
                    source = entry['s3']
                    dest = entry['local']

                strategy = self.params['overwrite']
                if strategy == 'never':
                    entry['state'] = 'skipped'
                elif strategy == 'different':
                    different = False
                    for attr in self.params['diff_attributes']:
                        if source.get(attr) != dest.get(attr):
                            different = True
                    if not different:
                        entry['state'] = 'skipped'
                elif strategy == 'larger':
                    if source['size'] <= dest['size']:
                        entry['state'] = 'skipped'
                elif strategy == 'newer':
                    if source['last_modified'] <= dest['last_modified']:
                        entry['state'] = 'skipped'

    def gather_local_files(self):
        for (dir_path, dirnames, filenames) in os.walk(self.path):
            for filename in filenames:
                path = os.path.join(dir_path, filename)

                if not self._match_all_patterns(filename):
                    continue

                rel_path = os.path.relpath(path, start=self.path)
                fstat = os.stat(path)

                content_type, content_encoding = self.mimetypes.guess_type(path, self.params['mime_strict'])

                # The guess might be None
                if not content_type:
                    content_type = 'application/octet-stream'

                entry = self._new_object(os.path.join(self.prefix, rel_path))
                entry.update({
                    'path': path,
                    'local': {
                        'content_type': content_type,
                        'content_encoding': content_encoding,
                        'last_modified': datetime.fromtimestamp(fstat[ST_MTIME], tz.tzutc()),
                        'size': fstat[ST_SIZE],
                    }
                })

    def gather_s3_files(self):
        try:
            s3_files = self._list_objects()
        except (BotoCoreError, ClientError) as e:
            self.module.fail_json_aws(e, msg="Couldn't list S3 objects in bucket %s with prefix %s" % (self.bucket, self.prefix))

        for s3_file in s3_files.get('Contents', []):
            entry = None

            filename = os.path.basename(s3_file['Key'])
            if not self._match_all_patterns(filename):
                continue

            entry = self._lookup_object_by_key(s3_file['Key'])

            if 'path' not in entry:
                path = s3_file['Key']
                if self.prefix:
                    path = path[len(self.prefix):].lstrip('/')
                entry['path'] = os.path.join(self.path, path)

            entry['s3'] = camel_dict_to_snake_dict(s3_file)
            entry['s3'].pop('key')

            # Calculate the local hash, if necessary
            if 'local' in entry and self.params['overwrite'] == 'different' and 'e_tag' in self.params['diff_attributes']:
                entry['local']['e_tag'] = calculate_etag(self.module, entry['path'], entry['s3']['e_tag'], self.s3, self.bucket, entry['key'], None)

    def upload_files(self):
        self._check_for_skip()
        for entry in self.objects:
            if entry['state'] == 'skipped' or 'local' not in entry:
                continue

            args = dict_to_s3_extra_args(self.params['metadata'])
            if 'ContentType' not in args:
                args['ContentType'] = entry['local']['content_type']
            if 'ContentEncoding' not in args and entry['local']['content_encoding']:
                args['ContentEncoding'] = entry['local']['content_encoding']
            if self.params['permission']:
                args['ACL'] = self.params['permission']

            if not self.check_mode:
                try:
                    self.s3.upload_file(entry['path'], self.bucket, entry['key'], ExtraArgs=args, Callback=None, Config=None)
                except (BotoCoreError, ClientError) as e:
                    self.module.fail_json_aws(e, msg="Failed to upload %s as %s" % (entry['path'], entry['key']))

            self.changed = True
            if 's3' in entry:
                entry['state'] = 'synced'
            else:
                entry['state'] = 'added'

    def download_files(self):
        self._check_for_skip()

        file_args = self.file_args
        dir_args = self.directory_args

        for entry in self.objects:
            if entry['state'] == 'skipped' or 's3' not in entry:
                continue

            if not self.check_mode:
                # Build a list of directory components to create
                new_directories = []
                current_dir = os.path.dirname(entry['path'])
                while not os.path.exists(to_bytes(current_dir, errors='surrogate_or_strict')):
                    current_dir, tail = os.path.split(current_dir)
                    new_directories.append(tail)

                # Create missing directories
                while new_directories:
                    current_dir = os.path.join(current_dir, new_directories.pop())
                    os.mkdir(to_bytes(current_dir, errors='surrogate_or_strict'))
                    dir_args['path'] = current_dir
                    self.module._module.set_fs_attributes_if_different(dir_args, True)

                if self.params['unsafe_writes']:
                    try:
                        self.s3.download_file(self.bucket, entry['key'], entry['path'])
                    except (BotoCoreError, ClientError) as e:
                        self.module.fail_json_aws(e, msg="Failed to download %s" % entry['key'])
                else:
                    tmp_file = tempfile.NamedTemporaryFile(prefix=b'.ansible_tmp', dir=to_bytes(current_dir, errors='surrogate_or_strict'), delete=False)
                    try:
                        self.s3.download_fileobj(self.bucket, entry['key'], tmp_file)
                    except (BotoCoreError, ClientError) as e:
                        os.unlink(to_bytes(tmp_file.name, errors='surrogate_or_strict'))
                        self.module.fail_json_aws(e, msg="Failed to download %s" % entry['key'])

                    tmp_file.close()

                    self.module._module.atomic_move(tmp_file.name, entry['path'])
                file_args['path'] = entry['path']
                self.module._module.set_fs_attributes_if_different(file_args, True)
                ts_datetime = entry['s3']['last_modified'].astimezone(tz.tzlocal())
                ts = time.mktime(ts_datetime.timetuple())
                os.utime(entry['path'], (ts, ts))

            self.changed = True
            if 'local' in entry:
                entry['state'] = 'synced'
            else:
                entry['state'] = 'added'

    def delete_local_files(self):
        for entry in self.objects:
            if 'local' in entry and 's3' not in entry:
                if not self.check_mode:
                    os.unlink(to_bytes(entry['path'], errors='surrogate_or_strict'))
                entry['state'] = 'deleted'
                self.changed = True

    def delete_s3_files(self):
        delete_keys = []
        for entry in self.objects:
            if 's3' in entry and 'local' not in entry:
                self.changed = True
                entry['state'] = 'deleted'
                delete_keys.append(entry['key'])

        if not self.check_mode:
            for i in range(0, len(delete_keys), 1000):
                try:
                    self.s3.delete_objects(Bucket=self.bucket, Delete={'Objects': [{'Key': key} for key in delete_keys[i:i + 1000]]})
                except (BotoCoreError, ClientError) as e:
                    self.module.fail_json_aws(e, msg="Bulk delete failed")


def main():
    argument_spec = dict(
        direction=dict(required=True, choices=['push', 'pull']),
        overwrite=dict(choices=['always', 'never', 'different', 'newer', 'larger'], default='never'),
        diff_attributes=dict(type='list', default=['e_tag']),
        bucket=dict(required=True),
        prefix=dict(default=''),
        path=dict(type='path', required=True),
        permission=dict(required=False, choices=[
            'private', 'public-read', 'public-read-write', 'authenticated-read',
            'aws-exec-read', 'bucket-owner-read', 'bucket-owner-full-control'
        ]),
        mime_encodings_map=dict(type='dict', default={}),
        mime_types_map=dict(type='dict', default={}),
        mime_override=dict(type='bool', default=False),
        mime_strict=dict(type='bool', default=False),
        patterns=dict(required=False, type='list', aliases=['pattern']),
        excludes=dict(required=False, type='list', aliases=['exclude']),
        hidden=dict(type='bool', default=False),
        use_regex=dict(type='bool', default=False),
        metadata=dict(type='dict', default={}),
        delete=dict(type='bool', default=False),
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        add_file_common_args=True,
        supports_check_mode=True,
    )

    if not HAS_DATEUTIL:
        module.fail_json(msg=missing_required_lib('dateutil'), exception=HAS_DATEUTIL_EXC)

    if module.params['overwrite'] == 'different' and 'e_tag' in module.params['diff_attributes'] and not HAS_MD5:
        module.fail_json(msg='Invalid diff_attributes: ETag calculation requires MD5 support, which is not available.')

    if not os.path.exists(to_bytes(module.params['path'], errors='surrogate_or_strict')):
        module.fail_json(msg="path not found: %s" % module.params['path'])

    syncer = S3Syncer(module)
    syncer.gather_local_files()
    syncer.gather_s3_files()
    if module.params['direction'] == 'push':
        syncer.upload_files()
        if module.params['delete']:
            syncer.delete_s3_files()
    else:
        syncer.download_files()
        if module.params['delete']:
            syncer.delete_local_files()

    module.exit_json(changed=syncer.changed, objects=syncer.objects)


if __name__ == '__main__':
    main()
