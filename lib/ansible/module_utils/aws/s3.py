# Copyright (c) 2018 Red Hat, Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

try:
    from botocore.exceptions import BotoCoreError, ClientError
except ImportError:
    pass    # Handled by the calling module

HAS_MD5 = True
try:
    from hashlib import md5
except ImportError:
    try:
        from md5 import md5
    except ImportError:
        HAS_MD5 = False


def calculate_etag(module, filename, etag, s3, bucket, obj, version=None):
    if not HAS_MD5:
        return None

    if '-' in etag:
        # Multi-part ETag; a hash of the hashes of each part.
        parts = int(etag[1:-1].split('-')[1])
        digests = []

        s3_kwargs = dict(
            Bucket=bucket,
            Key=obj,
        )
        if version:
            s3_kwargs['VersionId'] = version

        with open(filename, 'rb') as f:
            for part_num in range(1, parts + 1):
                s3_kwargs['PartNumber'] = part_num
                try:
                    head = s3.head_object(**s3_kwargs)
                except (BotoCoreError, ClientError) as e:
                    module.fail_json_aws(e, msg="Failed to get head object")
                digests.append(md5(f.read(int(head['ContentLength']))))

        digest_squared = md5(b''.join(m.digest() for m in digests))
        return '"{0}-{1}"'.format(digest_squared.hexdigest(), len(digests))
    else:  # Compute the MD5 sum normally
        return '"{0}"'.format(module.md5(filename))


def calculate_etag_content(module, content, etag, s3, bucket, obj, version=None):
    if not HAS_MD5:
        return None

    if '-' in etag:
        # Multi-part ETag; a hash of the hashes of each part.
        parts = int(etag[1:-1].split('-')[1])
        digests = []
        offset = 0

        s3_kwargs = dict(
            Bucket=bucket,
            Key=obj,
        )
        if version:
            s3_kwargs['VersionId'] = version

        for part_num in range(1, parts + 1):
            s3_kwargs['PartNumber'] = part_num
            try:
                head = s3.head_object(**s3_kwargs)
            except (BotoCoreError, ClientError) as e:
                module.fail_json_aws(e, msg="Failed to get head object")
            length = int(head['ContentLength'])
            digests.append(md5(content[offset:offset + length]))
            offset += length

        digest_squared = md5(b''.join(m.digest() for m in digests))
        return '"{0}-{1}"'.format(digest_squared.hexdigest(), len(digests))
    else:  # Compute the MD5 sum normally
        return '"{0}"'.format(md5(content).hexdigest())
